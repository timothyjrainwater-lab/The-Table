"""LLM model configuration and selection based on hardware tier.

Selects appropriate model size and offload strategy based on detected
hardware capabilities. Integrates with Spark Adapter Architecture by
reading from models.yaml registry.

Supports 14B, 7B, and 3B model tiers with automatic CPU offload when
VRAM is insufficient.

Usage:
    from aidm.core.hardware_detector import detect_hardware
    from aidm.core.model_selector import ModelSelector

    capabilities = detect_hardware()
    selector = ModelSelector()
    config = selector.select_model(capabilities)

    # Load model with selected config (via Spark Adapter)
    spark_adapter.load_model(config.model_name)

Reference:
- SPARK_ADAPTER_ARCHITECTURE.md: Spark model loading system
- SPARK_PROVIDER_CONTRACT.md: Spark provider interface
"""

import logging
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

from aidm.schemas.hardware_capability import (
    HardwareCapabilities,
    HardwareTier,
)

# NOTE: Model registry data is consumed from models.yaml at runtime.
# BL-004: Box must NOT import from Spark. Spark registers itself at
# runtime wiring, not via static import in core/.
# (Violation fixed 2026-02-13 per WO-AUDIT-004)

# Configure logging
logger = logging.getLogger(__name__)

# Default models.yaml location (relative to project root)
DEFAULT_MODEL_REGISTRY_PATH = Path(__file__).parent.parent.parent / "config" / "models.yaml"


class ModelSize(Enum):
    """LLM model size categories."""

    LARGE_14B = "14B"   # 14 billion parameters
    MEDIUM_7B = "7B"    # 7 billion parameters
    SMALL_3B = "3B"     # 3 billion parameters


@dataclass
class ModelConfig:
    """Configuration for LLM model loading.

    Attributes:
        model_name: Model identifier (e.g., "qwen-14b-chat")
        model_size: Parameter count (14B, 7B, 3B)
        model_path: Path to model weights (optional, for local models)
        enable_offload: Whether to enable CPU offload
        offload_layers: Number of layers to offload to CPU (0 = auto)
        max_context_length: Maximum context window size
        device_map: Device mapping strategy ("auto", "balanced", "sequential")
        load_in_8bit: Whether to use 8-bit quantization
        load_in_4bit: Whether to use 4-bit quantization
        torch_dtype: PyTorch dtype for model weights
        trust_remote_code: Whether to trust remote code execution
    """

    model_name: str
    model_size: ModelSize
    model_path: Optional[str] = None
    enable_offload: bool = False
    offload_layers: int = 0  # 0 = auto-determine
    max_context_length: int = 8192
    device_map: str = "auto"
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    torch_dtype: str = "auto"  # "auto", "float16", "bfloat16", "float32"
    trust_remote_code: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "model_name": self.model_name,
            "model_size": self.model_size.value,
            "model_path": self.model_path,
            "enable_offload": self.enable_offload,
            "offload_layers": self.offload_layers,
            "max_context_length": self.max_context_length,
            "device_map": self.device_map,
            "load_in_8bit": self.load_in_8bit,
            "load_in_4bit": self.load_in_4bit,
            "torch_dtype": self.torch_dtype,
            "trust_remote_code": self.trust_remote_code,
        }


@dataclass
class ModelSelectionResult:
    """Result of model selection process.

    Attributes:
        config: Selected model configuration
        warnings: Any warnings about the selection
        fallback_applied: Whether fallback to smaller model was applied
        reason: Human-readable reason for model selection
    """

    config: ModelConfig
    warnings: List[str] = field(default_factory=list)
    fallback_applied: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "config": self.config.to_dict(),
            "warnings": self.warnings,
            "fallback_applied": self.fallback_applied,
            "reason": self.reason,
        }


class ModelSelector:
    """Selects appropriate LLM model based on hardware capabilities.

    Implements tier-based model selection integrated with Spark Adapter
    Architecture. Reads model registry from models.yaml and selects
    appropriate model based on detected hardware tier.

    Tier selection logic:
    - HIGH tier (≥8 GB VRAM): 14B models, no offload
    - MEDIUM tier (6-8 GB VRAM): 7B models, no offload
    - FALLBACK tier (<6 GB VRAM or CPU-only): 3B models or offload enabled

    Attributes:
        _model_registry: Parsed models.yaml registry
        _registry_path: Path to models.yaml file
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize model selector with model registry.

        Args:
            registry_path: Path to models.yaml (None = use default)
        """
        self._registry_path = registry_path or DEFAULT_MODEL_REGISTRY_PATH
        self._model_registry = self._load_model_registry()

    def _load_model_registry(self) -> Dict[str, Any]:
        """Load model registry from models.yaml.

        Returns:
            Parsed model registry dictionary

        Raises:
            FileNotFoundError: If models.yaml not found
            yaml.YAMLError: If models.yaml is invalid
        """
        if not self._registry_path.exists():
            logger.error(f"Model registry not found: {self._registry_path}")
            logger.warning("Falling back to minimal hardcoded registry")
            return self._build_fallback_registry()

        try:
            with open(self._registry_path, "r", encoding="utf-8") as f:
                registry = yaml.safe_load(f)
            logger.info(f"Model registry loaded from {self._registry_path}")
            return registry
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse models.yaml: {e}")
            logger.warning("Falling back to minimal hardcoded registry")
            return self._build_fallback_registry()
        except Exception as e:
            logger.error(f"Unexpected error loading model registry: {e}")
            return self._build_fallback_registry()

    def _build_fallback_registry(self) -> Dict[str, Any]:
        """Build minimal fallback registry when models.yaml unavailable.

        Returns only template-narration (no hardcoded model names).

        Returns:
            Minimal registry with template narration only
        """
        logger.info("Using fallback registry (template narration only)")
        return {
            "spark": {
                "default": "template-narration",
                "models": [
                    {
                        "id": "template-narration",
                        "name": "Template Narration",
                        "tier": "FALLBACK",
                        "min_vram_gb": 0.0,
                        "fallback_model": None,
                    },
                ],
            },
            "tier_selection": {
                "HIGH": {"preferred_model": "template-narration"},
                "MEDIUM": {"preferred_model": "template-narration"},
                "FALLBACK": {"preferred_model": "template-narration"},
            },
        }

    def _get_models_by_tier(self, tier: HardwareTier) -> List[Dict[str, Any]]:
        """Get all models for a specific tier.

        Args:
            tier: Hardware tier

        Returns:
            List of model entries matching tier
        """
        tier_name = tier.value.upper()
        models = self._model_registry.get("spark", {}).get("models", [])
        return [m for m in models if m.get("tier", "").upper() == tier_name]

    def _get_preferred_model_id(self, tier: HardwareTier) -> str:
        """Get preferred model ID for hardware tier.

        Args:
            tier: Hardware tier

        Returns:
            Model ID from tier_selection rules
        """
        tier_name = tier.value.upper()
        tier_rules = self._model_registry.get("tier_selection", {})
        tier_config = tier_rules.get(tier_name, {})
        return tier_config.get("preferred_model", "template-narration")

    def _get_model_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Find model entry by ID.

        Args:
            model_id: Model identifier

        Returns:
            Model entry dict or None if not found
        """
        models = self._model_registry.get("spark", {}).get("models", [])
        for model in models:
            if model.get("id") == model_id:
                return model
        return None

    def select_model(
        self,
        capabilities: HardwareCapabilities,
        preferred_model: Optional[str] = None,
    ) -> ModelSelectionResult:
        """Select appropriate model based on hardware capabilities.

        Reads models.yaml to determine preferred model for detected tier,
        validates hardware compatibility, and configures offload if needed.

        Args:
            capabilities: Detected hardware capabilities
            preferred_model: Optional preferred model name (overrides auto-selection)

        Returns:
            ModelSelectionResult with selected configuration and warnings
        """
        logger.info(
            f"Selecting model for tier: {capabilities.tier.value}, "
            f"has_gpu={capabilities.has_gpu}, requires_offload={capabilities.requires_offload}"
        )

        warnings = []

        # Handle preferred model override
        if preferred_model:
            return self._select_preferred_model(
                preferred_model, capabilities, warnings
            )

        # Get preferred model for detected tier from models.yaml
        model_id = self._get_preferred_model_id(capabilities.tier)
        model_entry = self._get_model_by_id(model_id)

        if not model_entry:
            warnings.append(
                f"Preferred model '{model_id}' not found in registry. "
                "Falling back to template narration."
            )
            return self._select_template_narration(warnings)

        # Build model configuration based on tier
        if capabilities.tier == HardwareTier.HIGH:
            return self._select_high_tier_model(model_entry, capabilities, warnings)
        elif capabilities.tier == HardwareTier.MEDIUM:
            return self._select_medium_tier_model(model_entry, capabilities, warnings)
        elif capabilities.tier == HardwareTier.FALLBACK:
            return self._select_fallback_tier_model(model_entry, capabilities, warnings)
        else:
            # Unknown tier: default to fallback
            warnings.append(
                f"Unknown hardware tier: {capabilities.tier}. "
                "Defaulting to fallback model."
            )
            return self._select_fallback_tier_model(model_entry, capabilities, warnings)

    def _select_high_tier_model(
        self, model_entry: Dict[str, Any], capabilities: HardwareCapabilities, warnings: List[str]
    ) -> ModelSelectionResult:
        """Select model for HIGH tier (≥8 GB VRAM).

        Args:
            model_entry: Model entry from models.yaml
            capabilities: Hardware capabilities
            warnings: Warnings list to append to

        Returns:
            ModelSelectionResult with 14B model config
        """
        model_id = model_entry.get("id", "unknown")
        model_path = model_entry.get("path")
        max_context_window = model_entry.get("max_context_window", 8192)
        presets = model_entry.get("presets", {}).get("narration", {})

        config = ModelConfig(
            model_name=model_id,
            model_size=ModelSize.LARGE_14B,
            model_path=model_path,
            enable_offload=False,
            offload_layers=0,
            max_context_length=max_context_window,
            device_map="auto",
            load_in_8bit=False,
            load_in_4bit=False,
            torch_dtype="auto",
        )

        vram_gb = capabilities.gpu_info.vram_total_gb if capabilities.gpu_info else 0
        return ModelSelectionResult(
            config=config,
            warnings=warnings,
            fallback_applied=False,
            reason=f"High-tier hardware detected ({vram_gb:.1f}GB VRAM). "
            f"Loading 14B model ({model_id}) without offload.",
        )

    def _select_medium_tier_model(
        self, model_entry: Dict[str, Any], capabilities: HardwareCapabilities, warnings: List[str]
    ) -> ModelSelectionResult:
        """Select model for MEDIUM tier (6-8 GB VRAM).

        Args:
            model_entry: Model entry from models.yaml
            capabilities: Hardware capabilities
            warnings: Warnings list to append to

        Returns:
            ModelSelectionResult with 7B model config
        """
        model_id = model_entry.get("id", "unknown")
        model_path = model_entry.get("path")
        max_context_window = model_entry.get("max_context_window", 8192)

        # Check if VRAM is marginal (close to 6GB threshold)
        vram_gb = capabilities.gpu_info.vram_available_gb if capabilities.gpu_info else 0
        marginal_vram = vram_gb < 7.0

        if marginal_vram:
            warnings.append(
                f"VRAM ({vram_gb:.1f}GB) is marginal for 7B models. "
                "Consider enabling 8-bit quantization if OOM errors occur."
            )

        config = ModelConfig(
            model_name=model_id,
            model_size=ModelSize.MEDIUM_7B,
            model_path=model_path,
            enable_offload=False,
            offload_layers=0,
            max_context_length=max_context_window,
            device_map="auto",
            load_in_8bit=False,  # Enable if marginal VRAM
            load_in_4bit=False,
            torch_dtype="auto",
        )

        return ModelSelectionResult(
            config=config,
            warnings=warnings,
            fallback_applied=False,
            reason=f"Medium-tier hardware detected ({vram_gb:.1f}GB VRAM). "
            f"Loading 7B model ({model_id}) without offload.",
        )

    def _select_fallback_tier_model(
        self, model_entry: Dict[str, Any], capabilities: HardwareCapabilities, warnings: List[str]
    ) -> ModelSelectionResult:
        """Select model for FALLBACK tier (<6 GB VRAM or CPU-only).

        Args:
            model_entry: Model entry from models.yaml
            capabilities: Hardware capabilities
            warnings: Warnings list to append to

        Returns:
            ModelSelectionResult with 3B model config or offloaded 7B
        """
        model_id = model_entry.get("id", "unknown")

        # Template narration fallback (no model loading)
        if model_id == "template-narration":
            return self._select_template_narration(warnings)

        model_path = model_entry.get("path")
        max_context_window = model_entry.get("max_context_window", 4096)
        offload_config = model_entry.get("offload_config", {})

        # Determine if we have marginal GPU or CPU-only
        has_marginal_gpu = (
            capabilities.gpu_info is not None
            and capabilities.gpu_info.vram_total_mb >= 3072  # ≥3 GB
        )

        if has_marginal_gpu:
            # Marginal GPU: Use 3B model with possible offload
            warnings.append(
                f"GPU VRAM ({capabilities.gpu_info.vram_total_gb:.1f}GB) insufficient for larger models. "
                "Using 3B model with CPU offload enabled."
            )

            config = ModelConfig(
                model_name=model_id,
                model_size=ModelSize.SMALL_3B,
                model_path=model_path,
                enable_offload=True,
                offload_layers=0,  # Auto-determine
                max_context_length=max_context_window,
                device_map="auto",
                load_in_8bit=True,  # Use quantization to reduce VRAM
                load_in_4bit=False,
                torch_dtype="auto",
            )

            reason = (
                f"Fallback tier with marginal GPU ({capabilities.gpu_info.vram_total_gb:.1f}GB VRAM). "
                f"Loading 3B model ({model_id}) with CPU offload and 8-bit quantization."
            )
        else:
            # CPU-only: Use 3B model with full CPU offload
            warnings.append(
                "No GPU detected. Using 3B model with full CPU offload. "
                "Inference will be slower than GPU-accelerated."
            )

            config = ModelConfig(
                model_name=model_id,
                model_size=ModelSize.SMALL_3B,
                model_path=model_path,
                enable_offload=True,
                offload_layers=999,  # Offload all layers to CPU
                max_context_length=max_context_window,
                device_map="cpu",  # Force CPU device
                load_in_8bit=False,  # No quantization for CPU
                load_in_4bit=False,
                torch_dtype="float32",  # CPU uses float32
            )

            reason = (
                f"CPU-only fallback. Loading 3B model ({model_id}) with full CPU offload. "
                "Inference latency will be significantly higher than GPU."
            )

        return ModelSelectionResult(
            config=config,
            warnings=warnings,
            fallback_applied=True,
            reason=reason,
        )

    def _select_template_narration(self, warnings: List[str]) -> ModelSelectionResult:
        """Select template narration fallback (no LLM model).

        Args:
            warnings: Warnings list to append to

        Returns:
            ModelSelectionResult with template narration config
        """
        warnings.append(
            "No suitable LLM model for hardware. Falling back to template-based narration (M0)."
        )

        config = ModelConfig(
            model_name="template-narration",
            model_size=ModelSize.SMALL_3B,  # Placeholder
            model_path=None,
            enable_offload=False,
            offload_layers=0,
            max_context_length=0,
            device_map="cpu",
            load_in_8bit=False,
            load_in_4bit=False,
            torch_dtype="float32",
        )

        return ModelSelectionResult(
            config=config,
            warnings=warnings,
            fallback_applied=True,
            reason="Ultimate fallback: Using M0 template-based narration (no model loading required).",
        )

    def _select_preferred_model(
        self,
        preferred_model: str,
        capabilities: HardwareCapabilities,
        warnings: List[str],
    ) -> ModelSelectionResult:
        """Select user-specified preferred model with hardware validation.

        Args:
            preferred_model: User-requested model ID
            capabilities: Hardware capabilities
            warnings: Warnings list to append to

        Returns:
            ModelSelectionResult with preferred model if compatible, else fallback
        """
        # Look up model in registry
        model_entry = self._get_model_by_id(preferred_model)

        if not model_entry:
            warnings.append(
                f"Preferred model '{preferred_model}' not found in registry. "
                "Falling back to auto-selection."
            )
            return self.select_model(capabilities, preferred_model=None)

        # Check hardware compatibility
        min_vram_gb = model_entry.get("min_vram_gb", 0.0)
        vram_available_gb = (
            capabilities.gpu_info.vram_available_gb if capabilities.gpu_info else 0.0
        )

        if vram_available_gb < min_vram_gb:
            warnings.append(
                f"Preferred model '{preferred_model}' requires {min_vram_gb:.1f}GB VRAM, "
                f"but only {vram_available_gb:.1f}GB available. "
                "Attempting to load with CPU offload."
            )

            # Attempt to load with offload
            model_id = model_entry.get("id", "unknown")
            model_path = model_entry.get("path")
            max_context_window = model_entry.get("max_context_window", 8192)

            config = ModelConfig(
                model_name=model_id,
                model_size=ModelSize.MEDIUM_7B,  # Assume 7B if preferred override
                model_path=model_path,
                enable_offload=True,
                offload_layers=0,  # Auto-determine
                max_context_length=max_context_window,
                device_map="auto",
                load_in_8bit=True,
                load_in_4bit=False,
                torch_dtype="auto",
            )

            return ModelSelectionResult(
                config=config,
                warnings=warnings,
                fallback_applied=True,
                reason=f"Attempting to load preferred model '{preferred_model}' "
                "with CPU offload and 8-bit quantization. May fail if VRAM insufficient.",
            )

        # Model is compatible - load without offload
        logger.info(f"Using preferred model: {preferred_model}")
        model_id = model_entry.get("id", "unknown")
        model_path = model_entry.get("path")
        model_tier = model_entry.get("tier", "MEDIUM")
        max_context_window = model_entry.get("max_context_window", 8192)

        # Determine model size from tier
        if model_tier == "HIGH":
            model_size = ModelSize.LARGE_14B
        elif model_tier == "MEDIUM":
            model_size = ModelSize.MEDIUM_7B
        else:
            model_size = ModelSize.SMALL_3B

        config = ModelConfig(
            model_name=model_id,
            model_size=model_size,
            model_path=model_path,
            enable_offload=False,
            offload_layers=0,
            max_context_length=max_context_window,
            device_map="auto",
            load_in_8bit=False,
            load_in_4bit=False,
            torch_dtype="auto",
        )

        return ModelSelectionResult(
            config=config,
            warnings=warnings,
            fallback_applied=False,
            reason=f"User requested model '{preferred_model}' is compatible with hardware. Loading without offload.",
        )


# ═══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════


def select_model_for_hardware(
    capabilities: HardwareCapabilities,
) -> ModelSelectionResult:
    """Convenience function to select model for detected hardware.

    Args:
        capabilities: Detected hardware capabilities

    Returns:
        ModelSelectionResult with selected model config
    """
    selector = ModelSelector()
    return selector.select_model(capabilities)
