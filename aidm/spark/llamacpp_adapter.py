"""LlamaCpp Adapter: llama.cpp backend implementation for Spark

This module provides a concrete implementation of SparkAdapter using
the llama-cpp-python library for GGUF model loading and inference.

Reference: docs/design/SPARK_ADAPTER_ARCHITECTURE.md (Section 2)
"""

import logging
from pathlib import Path
from typing import List, Optional

from aidm.spark.model_registry import HardwareTier, ModelProfile, ModelRegistry, TierName
from aidm.spark.spark_adapter import (
    SparkAdapter,
    SparkRequest,
    SparkResponse,
    FinishReason,
    LoadedModel,
    CompatibilityReport,
    ModelLoadError,
    InsufficientResourcesError,
    NoSuitableModelError,
    NoFallbackAvailableError,
)

logger = logging.getLogger(__name__)


class LlamaCppAdapter(SparkAdapter):
    """LlamaCpp backend implementation for Spark Adapter.

    This adapter uses llama-cpp-python to load GGUF models and perform
    inference. It supports GPU acceleration, CPU offloading, and automatic
    fallback to smaller models when resources are insufficient.

    Example usage:
        registry = ModelRegistry.load_from_file("config/models.yaml")
        adapter = LlamaCppAdapter(registry=registry, models_dir="models/")
        hardware_tier = detect_hardware_tier()
        model_id = adapter.select_model_for_tier(hardware_tier)
        loaded_model = adapter.load_model(model_id)
        text = adapter.generate_text(loaded_model, "Once upon a time...")
    """

    def __init__(
        self,
        registry: ModelRegistry,
        models_dir: str = "models/",
        enable_gpu: bool = True,
    ):
        """Initialize LlamaCpp adapter.

        Args:
            registry: Model registry instance
            models_dir: Base directory for model files
            enable_gpu: Whether to enable GPU acceleration
        """
        self.registry = registry
        self.models_dir = Path(models_dir)
        self.enable_gpu = enable_gpu
        self._llama_cpp_available = self._check_llama_cpp_available()

    def _check_llama_cpp_available(self) -> bool:
        """Check if llama-cpp-python is installed.

        Returns:
            True if llama-cpp-python is available
        """
        try:
            import llama_cpp  # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )
            return False

    def load_model(self, model_id: str) -> LoadedModel:
        """Load model by ID from model registry.

        Args:
            model_id: Model identifier (e.g., "mistral-7b-instruct-4bit")

        Returns:
            LoadedModel instance with inference interface

        Raises:
            ModelLoadError: If model cannot be loaded
            InsufficientResourcesError: If hardware requirements not met
        """
        # Get model profile
        profile = self.registry.get_model_by_id(model_id)
        if profile is None:
            raise ModelLoadError(f"Model not found in registry: {model_id}")

        # Handle template-narration fallback (no model loading)
        # Template narration works WITHOUT llama-cpp-python
        if profile.backend == "template":
            return LoadedModel(
                model_id=model_id,
                profile=profile,
                inference_engine=None,
                device="cpu",
                memory_usage_mb=0.0,
            )

        # For LLM models, llama-cpp-python is required
        if not self._llama_cpp_available:
            raise ModelLoadError(
                "llama-cpp-python not installed. Cannot load LLM models. "
                "Install with: pip install llama-cpp-python"
            )
        if profile.backend == "template":
            return LoadedModel(
                model_id=model_id,
                profile=profile,
                inference_engine=None,
                device="cpu",
                memory_usage_mb=0.0,
            )

        # Check compatibility
        compat_report = self.check_model_compatibility(model_id)
        if not compat_report.is_compatible:
            raise InsufficientResourcesError(
                f"Model '{model_id}' requires {compat_report.vram_required_gb:.1f} GB VRAM, "
                f"but only {compat_report.vram_available_gb:.1f} GB available. "
                f"Issues: {', '.join(compat_report.compatibility_issues)}"
            )

        # Resolve model path
        if profile.path is None:
            raise ModelLoadError(f"Model '{model_id}' has no path specified")

        model_path = self.models_dir / profile.path
        if not model_path.exists():
            raise ModelLoadError(
                f"Model file not found: {model_path}\n"
                f"Download models separately (see docs/INSTALLATION.md)"
            )

        # Load model using llama-cpp-python
        try:
            from llama_cpp import Llama

            # Determine GPU layers
            n_gpu_layers = self._calculate_gpu_layers(profile, compat_report)

            # Load model
            logger.info(
                f"Loading model '{model_id}' from {model_path} "
                f"(n_gpu_layers={n_gpu_layers})"
            )

            llm = Llama(
                model_path=str(model_path),
                n_ctx=profile.max_context_window or 8192,
                n_gpu_layers=n_gpu_layers if self.enable_gpu else 0,
                n_batch=512,
                n_threads=None,  # Auto-detect
                use_mlock=True,
                use_mmap=True,
                verbose=False,
            )

            # Estimate memory usage (rough approximation)
            memory_usage_mb = profile.min_vram_gb * 1024 if n_gpu_layers > 0 else profile.min_ram_gb * 1024

            device = "cuda" if n_gpu_layers > 0 else "cpu"

            logger.info(
                f"Model '{model_id}' loaded successfully on {device} "
                f"(~{memory_usage_mb:.0f} MB)"
            )

            return LoadedModel(
                model_id=model_id,
                profile=profile,
                inference_engine=llm,
                device=device,
                memory_usage_mb=memory_usage_mb,
            )

        except Exception as e:
            raise ModelLoadError(f"Failed to load model '{model_id}': {e}") from e

    def unload_model(self, loaded_model: LoadedModel) -> None:
        """Unload model and free resources.

        Args:
            loaded_model: Loaded model instance to unload
        """
        if loaded_model.inference_engine is not None:
            # llama-cpp-python models are freed automatically when deleted
            del loaded_model.inference_engine
            logger.info(f"Model '{loaded_model.model_id}' unloaded")

    def select_model_for_tier(self, hardware_tier: HardwareTier) -> str:
        """Select appropriate model ID for detected hardware tier.

        Args:
            hardware_tier: Detected hardware tier

        Returns:
            model_id: Best model for this hardware tier

        Raises:
            NoSuitableModelError: If no model fits hardware tier
        """
        tier_rule = self.registry.get_tier_rule(hardware_tier.tier_name)

        if tier_rule is None:
            # Fallback to lowest tier
            logger.warning(
                f"No tier rule for {hardware_tier.tier_name}, using FALLBACK tier"
            )
            tier_rule = self.registry.get_tier_rule(TierName.FALLBACK)
            if tier_rule is None:
                raise NoSuitableModelError("No fallback tier rule found")

        # Try preferred model first
        model_id = tier_rule.preferred_model

        # Check if preferred model is compatible
        compat_report = self.check_model_compatibility(model_id)
        if compat_report.is_compatible:
            logger.info(
                f"Selected model '{model_id}' for tier {hardware_tier.tier_name}"
            )
            return model_id

        # Try alternatives
        for alt_model_id in tier_rule.alternatives:
            compat_report = self.check_model_compatibility(alt_model_id)
            if compat_report.is_compatible:
                logger.info(
                    f"Selected alternative model '{alt_model_id}' "
                    f"for tier {hardware_tier.tier_name}"
                )
                return alt_model_id

        # No compatible model found, try fallback chain
        fallback_id = self.get_fallback_model(model_id)
        logger.warning(
            f"No compatible model for tier {hardware_tier.tier_name}, "
            f"falling back to '{fallback_id}'"
        )
        return fallback_id

    def get_fallback_model(self, failed_model_id: str) -> str:
        """Get fallback model ID if primary model fails to load.

        Args:
            failed_model_id: Model that failed to load

        Returns:
            fallback_model_id: Smaller model to try next

        Raises:
            NoFallbackAvailableError: If no fallback exists
        """
        profile = self.registry.get_model_by_id(failed_model_id)
        if profile is None:
            raise NoFallbackAvailableError(
                f"Model '{failed_model_id}' not found in registry"
            )

        if profile.fallback_model is None:
            raise NoFallbackAvailableError(
                f"Model '{failed_model_id}' has no fallback model"
            )

        return profile.fallback_model

    def check_model_compatibility(self, model_id: str) -> CompatibilityReport:
        """Check if model is compatible with current hardware.

        Args:
            model_id: Model to check

        Returns:
            CompatibilityReport with VRAM requirements, issues, etc.
        """
        profile = self.registry.get_model_by_id(model_id)
        if profile is None:
            return CompatibilityReport(
                model_id=model_id,
                is_compatible=False,
                vram_required_gb=0.0,
                vram_available_gb=0.0,
                ram_required_gb=0.0,
                ram_available_gb=0.0,
                compatibility_issues=["Model not found in registry"],
            )

        # Template narration is always compatible
        if profile.backend == "template":
            return CompatibilityReport(
                model_id=model_id,
                is_compatible=True,
                vram_required_gb=0.0,
                vram_available_gb=0.0,
                ram_required_gb=0.0,
                ram_available_gb=0.0,
                compatibility_issues=[],
            )

        # Detect available resources
        # TODO: Integrate with Agent B hardware detection
        # For now, use conservative estimates
        vram_available = self._get_available_vram_gb()
        ram_available = self._get_available_ram_gb()

        issues = []
        is_compatible = True
        offload_recommended = False

        # Check VRAM requirement
        if profile.min_vram_gb > vram_available:
            if profile.min_vram_gb * 0.5 <= vram_available:
                # Partial offload possible
                offload_recommended = True
                logger.info(
                    f"Model '{model_id}' requires {profile.min_vram_gb:.1f} GB VRAM, "
                    f"but only {vram_available:.1f} GB available. CPU offload recommended."
                )
            else:
                # Insufficient even with offload
                is_compatible = False
                issues.append(
                    f"Insufficient VRAM: requires {profile.min_vram_gb:.1f} GB, "
                    f"available {vram_available:.1f} GB"
                )

        # Check RAM requirement
        if profile.min_ram_gb > ram_available:
            is_compatible = False
            issues.append(
                f"Insufficient RAM: requires {profile.min_ram_gb:.1f} GB, "
                f"available {ram_available:.1f} GB"
            )

        # Check model file exists
        if profile.path is not None:
            model_path = self.models_dir / profile.path
            if not model_path.exists():
                is_compatible = False
                issues.append(f"Model file not found: {model_path}")

        return CompatibilityReport(
            model_id=model_id,
            is_compatible=is_compatible,
            vram_required_gb=profile.min_vram_gb,
            vram_available_gb=vram_available,
            ram_required_gb=profile.min_ram_gb,
            ram_available_gb=ram_available,
            compatibility_issues=issues,
            offload_recommended=offload_recommended,
        )

    def generate_text(
        self,
        loaded_model: LoadedModel,
        prompt: str,
        temperature: float = 0.8,
        max_tokens: int = 150,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Generate text using loaded model.

        Args:
            loaded_model: Loaded model instance
            prompt: Input prompt text
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stop_sequences: Optional list of stop sequences

        Returns:
            Generated text string

        Raises:
            ModelLoadError: If model not properly loaded
        """
        if loaded_model.inference_engine is None:
            raise ModelLoadError(
                f"Model '{loaded_model.model_id}' not properly loaded "
                f"(inference engine is None)"
            )

        try:
            output = loaded_model.inference_engine(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop_sequences or [],
                echo=False,
            )

            # Extract generated text
            if isinstance(output, dict) and 'choices' in output:
                text = output['choices'][0]['text']
            else:
                text = str(output)

            return text.strip()

        except Exception as e:
            raise ModelLoadError(
                f"Failed to generate text with model '{loaded_model.model_id}': {e}"
            ) from e

    def generate(self, request: SparkRequest, loaded_model: LoadedModel = None) -> SparkResponse:
        """Generate text from canonical SparkRequest (SPARK_PROVIDER_CONTRACT.md §7.1).

        Full implementation with accurate token counts, finish reason tracking,
        stop sequence enforcement, seed forwarding, and json_mode support.

        Args:
            request: Canonical SPARK request
            loaded_model: Loaded model instance

        Returns:
            Canonical SPARK response with full field fidelity
        """
        # Template model handling: no inference engine loaded
        if loaded_model is None or loaded_model.inference_engine is None:
            return SparkResponse(
                text="",
                finish_reason=FinishReason.ERROR,
                tokens_used=0,
                error="No inference engine loaded — use template fallback",
            )

        try:
            # Build llama-cpp kwargs
            kwargs = {
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "echo": False,
            }

            # Stop sequence enforcement
            if request.stop_sequences:
                kwargs["stop"] = request.stop_sequences

            # Seed forwarding for reproducibility
            if request.seed is not None:
                kwargs["seed"] = request.seed

            # json_mode flag
            if request.json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            # Call llama-cpp inference engine
            output = loaded_model.inference_engine(request.prompt, **kwargs)

            # Extract text from response
            if isinstance(output, dict) and "choices" in output:
                text = output["choices"][0]["text"]
            else:
                text = str(output)

            text = text.strip()

            # Extract token usage from response
            prompt_tokens = 0
            completion_tokens = 0
            if isinstance(output, dict) and "usage" in output:
                usage = output["usage"]
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

            tokens_used = prompt_tokens + completion_tokens

            # Determine finish reason
            finish_reason = FinishReason.COMPLETED

            # Check LENGTH_LIMIT: completion_tokens >= max_tokens
            if completion_tokens >= request.max_tokens:
                finish_reason = FinishReason.LENGTH_LIMIT

            # Check STOP_SEQUENCE: output ends with a stop sequence
            # Only check if not already LENGTH_LIMIT (length takes priority)
            if finish_reason != FinishReason.LENGTH_LIMIT and request.stop_sequences:
                for seq in request.stop_sequences:
                    if text.endswith(seq):
                        finish_reason = FinishReason.STOP_SEQUENCE
                        break
                    # Also check the raw (untrimmed) text from the response
                    if isinstance(output, dict) and "choices" in output:
                        raw_text = output["choices"][0].get("text", "")
                        if raw_text.endswith(seq):
                            finish_reason = FinishReason.STOP_SEQUENCE
                            break

            # Provider metadata
            provider_metadata = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "model_id": loaded_model.model_id,
            }

            return SparkResponse(
                text=text,
                finish_reason=finish_reason,
                tokens_used=tokens_used,
                provider_metadata=provider_metadata,
            )

        except Exception as e:
            return SparkResponse(
                text="",
                finish_reason=FinishReason.ERROR,
                tokens_used=0,
                error=str(e),
                provider_metadata={"model_id": loaded_model.model_id},
            )

    def _calculate_gpu_layers(
        self,
        profile: ModelProfile,
        compat_report: CompatibilityReport,
    ) -> int:
        """Calculate number of GPU layers based on available resources.

        Args:
            profile: Model profile
            compat_report: Compatibility report

        Returns:
            Number of layers to load on GPU
        """
        if not self.enable_gpu:
            return 0

        if compat_report.offload_recommended:
            # Use offload config if available
            if profile.offload_config is not None:
                return profile.offload_config.get('min_gpu_layers', 8)
            else:
                # Conservative default
                return 8

        # Full GPU loading
        return -1  # -1 means all layers on GPU

    def _get_available_vram_gb(self) -> float:
        """Get available VRAM in gigabytes.

        This is a placeholder. In production, this would integrate
        with Agent B hardware detection system.

        Returns:
            Available VRAM in GB
        """
        # TODO: Integrate with Agent B hardware detection
        # For now, return conservative estimate
        try:
            import torch
            if torch.cuda.is_available():
                # Get VRAM from first GPU
                props = torch.cuda.get_device_properties(0)
                total_vram_gb = props.total_memory / (1024 ** 3)
                # Assume 80% is available
                return total_vram_gb * 0.8
        except ImportError:
            pass

        # No GPU detected or torch not available
        return 0.0

    def _get_available_ram_gb(self) -> float:
        """Get available system RAM in gigabytes.

        This is a placeholder. In production, this would integrate
        with Agent B hardware detection system.

        Returns:
            Available RAM in GB
        """
        # TODO: Integrate with Agent B hardware detection
        # For now, return conservative estimate
        import psutil
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
