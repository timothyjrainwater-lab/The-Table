"""Spark Adapter: Abstract interface for LLM model loading and selection

This module defines the SparkAdapter abstract base class which provides
hardware-aware model loading and tier-based model selection.

BOUNDARY LAW (BL-001, BL-002): This module must NEVER import from aidm.core
or aidm.narration. SPARK is a pure text generation layer with no access to
game state, RNG, or guardrail internals. If you add such imports,
test_boundary_law.py BL-001/BL-002 will fail.

BOUNDARY LAW (BL-013, BL-016): SparkRequest and SparkResponse validate
schema invariants at construction. Invalid requests/responses fail fast.

Reference: docs/design/SPARK_ADAPTER_ARCHITECTURE.md (Section 2)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

from aidm.spark.model_registry import HardwareTier, ModelProfile
from aidm.spark.spark_failure import SparkFailureMode


# ============================================================================
# Canonical Request/Response (SPARK_PROVIDER_CONTRACT.md §2)
# ============================================================================


class FinishReason(str, Enum):
    """Why generation stopped (SPARK_PROVIDER_CONTRACT.md §2.2)."""
    COMPLETED = "completed"
    LENGTH_LIMIT = "length_limit"
    STOP_SEQUENCE = "stop_sequence"
    ERROR = "error"


@dataclass
class SparkRequest:
    """Canonical request from AIDM to SPARK (§2.1).

    Attributes:
        prompt: Text prompt (REQUIRED, non-empty)
        temperature: Sampling temperature 0.0-2.0 (REQUIRED)
        max_tokens: Maximum response tokens (REQUIRED, positive)
        stop_sequences: Token sequences that halt generation
        context_window: Override default context window
        streaming: Enable streaming response
        json_mode: Request structured JSON output
        seed: RNG seed for reproducibility
        metadata: Provider-specific parameters
    """
    prompt: str
    temperature: float
    max_tokens: int
    stop_sequences: List[str] = field(default_factory=list)
    context_window: Optional[int] = None
    streaming: bool = False
    json_mode: bool = False
    seed: Optional[int] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        if not self.prompt:
            raise ValueError("prompt MUST be non-empty string")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"temperature MUST be in [0.0, 2.0], got {self.temperature}")
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens MUST be positive, got {self.max_tokens}")


@dataclass
class SparkResponse:
    """Canonical response from SPARK to AIDM (§2.2).

    Attributes:
        text: Generated text output (REQUIRED)
        finish_reason: Why generation stopped (REQUIRED)
        tokens_used: Total tokens consumed (REQUIRED, non-negative)
        provider_metadata: Provider-specific info
        error: Error message if generation failed
        degraded: True when template narration substituted for model output (BURST-002)
        failure_mode: SparkFailureMode classifying the failure, or None (BURST-002)
        fallback_used: True when template narration was substituted (BURST-002)
    """
    text: str
    finish_reason: FinishReason
    tokens_used: int
    provider_metadata: Optional[dict] = None
    error: Optional[str] = None
    degraded: bool = False
    failure_mode: Optional[SparkFailureMode] = None
    fallback_used: bool = False

    def __post_init__(self):
        if self.finish_reason == FinishReason.ERROR and not self.error:
            raise ValueError("error field MUST be populated when finish_reason is 'error'")
        if self.tokens_used < 0:
            raise ValueError(f"tokens_used MUST be non-negative, got {self.tokens_used}")


# ============================================================================
# Exceptions
# ============================================================================


class SparkAdapterError(Exception):
    """Base exception for Spark Adapter errors."""
    pass


class ModelLoadError(SparkAdapterError):
    """Raised when model cannot be loaded."""
    pass


class InsufficientResourcesError(SparkAdapterError):
    """Raised when hardware requirements not met."""
    pass


class NoSuitableModelError(SparkAdapterError):
    """Raised when no model fits hardware tier."""
    pass


class NoFallbackAvailableError(SparkAdapterError):
    """Raised when no fallback model exists."""
    pass


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class LoadedModel:
    """Loaded model instance with inference interface.

    Attributes:
        model_id: Model identifier
        profile: Model profile from registry
        inference_engine: Runtime-specific inference engine (provider-dependent)
        device: Device where model is loaded ("cuda", "cpu", "mps")
        memory_usage_mb: Estimated memory usage in megabytes
    """
    model_id: str
    profile: ModelProfile
    inference_engine: Any
    device: str
    memory_usage_mb: float


@dataclass
class CompatibilityReport:
    """Model compatibility check result.

    Attributes:
        model_id: Model identifier
        is_compatible: Whether model is compatible with current hardware
        vram_required_gb: VRAM required by model
        vram_available_gb: VRAM available on system
        ram_required_gb: System RAM required by model
        ram_available_gb: System RAM available
        compatibility_issues: List of reasons if not compatible
        offload_recommended: Whether CPU offload is recommended
    """
    model_id: str
    is_compatible: bool
    vram_required_gb: float
    vram_available_gb: float
    ram_required_gb: float
    ram_available_gb: float
    compatibility_issues: List[str]
    offload_recommended: bool = False


# ============================================================================
# SparkAdapter Interface
# ============================================================================


class SparkAdapter(ABC):
    """Abstract interface for LLM model loading and selection.

    The Spark Adapter provides a hardware-aware model loading interface
    that selects models based on detected hardware tier and falls back
    gracefully when resources are insufficient.

    Implementations:
    - LlamaCppAdapter: llama.cpp backend (GGUF models)
    - TransformersAdapter: Hugging Face Transformers backend (future)

    Example usage:
        adapter = LlamaCppAdapter(registry=model_registry)
        hardware_tier = detect_hardware_tier()
        model_id = adapter.select_model_for_tier(hardware_tier)
        loaded_model = adapter.load_model(model_id)
    """

    @abstractmethod
    def load_model(self, model_id: str) -> LoadedModel:
        """Load model by ID from model registry.

        This method loads a model specified by its ID, initializing the
        inference engine and allocating resources.

        Args:
            model_id: Model identifier (e.g., "mistral-7b-instruct-4bit")

        Returns:
            LoadedModel instance with inference interface

        Raises:
            ModelLoadError: If model cannot be loaded
            InsufficientResourcesError: If hardware requirements not met
        """
        raise NotImplementedError

    @abstractmethod
    def unload_model(self, loaded_model: LoadedModel) -> None:
        """Unload model and free resources.

        Args:
            loaded_model: Loaded model instance to unload
        """
        raise NotImplementedError

    @abstractmethod
    def select_model_for_tier(self, hardware_tier: HardwareTier) -> str:
        """Select appropriate model ID for detected hardware tier.

        This method uses tier-based selection rules to choose the best
        model for the available hardware.

        Args:
            hardware_tier: Detected hardware tier (HIGH/MEDIUM/LOW/FALLBACK)

        Returns:
            model_id: Best model for this hardware tier

        Raises:
            NoSuitableModelError: If no model fits hardware tier
        """
        raise NotImplementedError

    @abstractmethod
    def get_fallback_model(self, failed_model_id: str) -> str:
        """Get fallback model ID if primary model fails to load.

        This method returns the next model in the fallback chain to try
        if the primary model fails to load or runs out of resources.

        Args:
            failed_model_id: Model that failed to load

        Returns:
            fallback_model_id: Smaller model to try next

        Raises:
            NoFallbackAvailableError: If no fallback exists
        """
        raise NotImplementedError

    @abstractmethod
    def check_model_compatibility(self, model_id: str) -> CompatibilityReport:
        """Check if model is compatible with current hardware.

        This method checks whether a model's hardware requirements
        (VRAM, RAM, etc.) can be satisfied by the current system.

        Args:
            model_id: Model to check

        Returns:
            CompatibilityReport with VRAM requirements, context window, etc.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_text(
        self,
        loaded_model: LoadedModel,
        prompt: str,
        temperature: float = 0.8,
        max_tokens: int = 150,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Generate text using loaded model.

        This method generates text from a prompt using the loaded model's
        inference engine.

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
        raise NotImplementedError

    def generate(self, request: SparkRequest, loaded_model: Optional[LoadedModel] = None,
                 call_type: Optional[str] = None,
                 profiler: Optional[Any] = None,
                 sensor_fn: Optional[Any] = None) -> SparkResponse:
        """Generate text from canonical request (SPARK_PROVIDER_CONTRACT.md §7.1).

        Default implementation delegates to generate_text() for backward
        compatibility with existing adapters.

        Adds TTFT measurement (BURST-002 §3.6), per-call timeout enforcement,
        and graceful degradation to template narration on failure.

        Args:
            request: Canonical SPARK request
            loaded_model: Loaded model instance (optional for backward compat)
            call_type: SparkCallType string for SLA lookup and template narration
            profiler: Optional callable(bucket, record_dict) for TTFT recording
            sensor_fn: Optional callable(event_name, **kwargs) for sensor events

        Returns:
            Canonical SPARK response (may be degraded with template narration)
        """
        import time
        from aidm.spark.spark_failure import SparkFailure, SparkFailureMode
        from aidm.spark.spark_sla import SPARK_SLA_PER_CALL, TEMPLATE_NARRATION

        # Resolve timeout for this call type
        timeout_s: Optional[float] = None
        if call_type and call_type in SPARK_SLA_PER_CALL:
            timeout_s = SPARK_SLA_PER_CALL[call_type]["timeout_s"]

        # Bridge to legacy generate_text() for existing adapters
        effective_model = loaded_model or getattr(self, '_current_model', None)

        t_call_start = time.perf_counter()
        t_first_token: float = t_call_start  # default: no streaming; first token = call start

        try:
            text = self.generate_text(
                loaded_model=effective_model,
                prompt=request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stop_sequences=request.stop_sequences or None,
            )
            t_first_token = time.perf_counter()  # non-streaming: approximate
            t_complete = time.perf_counter()

            ttft_s = t_first_token - t_call_start
            inference_s = t_complete - t_call_start

            # Timeout enforcement (post-call check for non-streaming adapters)
            if timeout_s is not None and inference_s > timeout_s:
                raise SparkFailure(
                    SparkFailureMode.INFERENCE_TIMEOUT,
                    f"Inference took {inference_s:.2f}s, exceeded timeout {timeout_s:.2f}s",
                )

            # Record TTFT to profiler bucket if provided
            if profiler is not None:
                model_id = effective_model.model_id if effective_model else "unknown"
                profiler("spark_call", {
                    "call_type": call_type or "UNKNOWN",
                    "ttft_s": ttft_s,
                    "inference_s": inference_s,
                    "model_id": model_id,
                    "degraded": False,
                })

            return SparkResponse(
                text=text,
                finish_reason=FinishReason.COMPLETED,
                tokens_used=0,  # Unknown from legacy interface
            )

        except SparkFailure as sf:
            t_complete = time.perf_counter()
            inference_s = t_complete - t_call_start

            # Build degraded template response
            template_text = TEMPLATE_NARRATION.get(call_type or "", "") if call_type else ""
            if not template_text:
                template_text = "Narration unavailable."

            # Emit sensor event
            if sensor_fn is not None:
                sensor_fn("SPARK_DEGRADED", failure_mode=sf.mode, call_type=call_type)

            # Record TTFT to profiler bucket (degraded=True)
            if profiler is not None:
                model_id = effective_model.model_id if effective_model else "unknown"
                profiler("spark_call", {
                    "call_type": call_type or "UNKNOWN",
                    "ttft_s": t_first_token - t_call_start,
                    "inference_s": inference_s,
                    "model_id": model_id,
                    "degraded": True,
                })

            return SparkResponse(
                text=template_text,
                finish_reason=FinishReason.ERROR,
                tokens_used=0,
                error=str(sf),
                degraded=True,
                failure_mode=sf.mode,
                fallback_used=True,
            )

        except Exception as e:
            t_complete = time.perf_counter()
            inference_s = t_complete - t_call_start

            return SparkResponse(
                text="",
                finish_reason=FinishReason.ERROR,
                tokens_used=0,
                error=str(e),
            )

    def load_model_with_fallback(
        self,
        model_id: str,
        max_fallback_attempts: int = 3,
    ) -> LoadedModel:
        """Load model with automatic fallback on failure.

        This method attempts to load a model, and if it fails, tries
        fallback models until one succeeds or all fail.

        Args:
            model_id: Initial model ID to try
            max_fallback_attempts: Maximum number of fallback attempts

        Returns:
            LoadedModel instance

        Raises:
            ModelLoadError: If all models (including fallbacks) fail
        """
        current_id = model_id
        attempts = 0

        while attempts < max_fallback_attempts:
            try:
                return self.load_model(current_id)
            except (ModelLoadError, InsufficientResourcesError) as e:
                attempts += 1

                try:
                    fallback_id = self.get_fallback_model(current_id)
                    current_id = fallback_id
                except NoFallbackAvailableError:
                    raise ModelLoadError(
                        f"Failed to load model '{model_id}' and no fallback available"
                    ) from e

        raise ModelLoadError(
            f"Failed to load model '{model_id}' after {attempts} fallback attempts"
        )

    def get_loaded_model_info(self, loaded_model: LoadedModel) -> dict:
        """Get information about loaded model.

        Args:
            loaded_model: Loaded model instance

        Returns:
            Dictionary with model information
        """
        return {
            "model_id": loaded_model.model_id,
            "model_name": loaded_model.profile.name,
            "tier": loaded_model.profile.tier.value,
            "device": loaded_model.device,
            "memory_usage_mb": loaded_model.memory_usage_mb,
            "backend": loaded_model.profile.backend,
            "quantization": loaded_model.profile.quantization,
            "max_tokens": loaded_model.profile.max_tokens,
            "max_context_window": loaded_model.profile.max_context_window,
        }
