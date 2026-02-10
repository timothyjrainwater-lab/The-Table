"""Image critique adapter protocol for AIDM immersion pipeline.

PRE-M3 CONTRACT (NON-OPERATIONAL)
---------------------------------
This module defines the adapter protocol for automated image quality validation.
Implementation deferred to M3 (Immersion Layer integration).

CURRENT STATUS: Protocol + stub only, no actual critique implementation
R0 SOURCE: R0_IMAGE_CRITIQUE_FEASIBILITY.md (advisory, non-binding)
AUTHORITY: NON-BINDING until formal R0 approval + M3 integration

Design follows existing adapter pattern (STTAdapter, TTSAdapter, ImageAdapter).
Stub implementation returns placeholder results for testing.

---

This module provides:
- ImageCritiqueAdapter: Protocol for critique implementations
- StubImageCritic: Stub implementation for testing
- create_image_critic: Factory function for adapter creation

NO ACTUAL MODELS OR CRITIQUE LOGIC IMPLEMENTED.
All runtime wiring deferred to M3.
"""

from typing import Protocol, runtime_checkable, Optional, Dict, Any
from aidm.schemas.image_critique import (
    CritiqueResult,
    CritiqueRubric,
    CritiqueDimension,
    DimensionType,
    SeverityLevel,
    DEFAULT_CRITIQUE_RUBRIC,
)

# Lazy imports for optional dependencies
def _import_heuristics_critic():
    """Lazy import HeuristicsImageCritic to avoid dependency issues."""
    from aidm.core.heuristics_image_critic import HeuristicsImageCritic
    return HeuristicsImageCritic


def _import_imagereward_critic():
    """Lazy import ImageRewardCritiqueAdapter to avoid dependency issues."""
    from aidm.core.imagereward_critique_adapter import ImageRewardCritiqueAdapter
    return ImageRewardCritiqueAdapter


def _import_graduated_orchestrator():
    """Lazy import GraduatedCritiqueOrchestrator to avoid dependency issues."""
    from aidm.core.graduated_critique_orchestrator import GraduatedCritiqueOrchestrator
    return GraduatedCritiqueOrchestrator


@runtime_checkable
class ImageCritiqueAdapter(Protocol):
    """Protocol for automated image quality validation.

    Implementations must provide critique() method that validates image quality
    across multiple dimensions (readability, composition, artifacting, style, identity).

    Based on R0_IMAGE_CRITIQUE_FEASIBILITY.md § Recommended Approach (Hybrid).

    Future implementations:
    - HeuristicsImageCritic: OpenCV-based heuristics (CPU-only)
    - CLIPImageCritic: Heuristics + CLIP embeddings (GPU)
    - HybridImageCritic: Auto-detect GPU, use CLIP if available else heuristics

    All implementations must be deterministic for same inputs.
    """

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Validate image quality against rubric.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds for pass/fail
            anchor_image_bytes: NPC anchor image for identity match (optional)
            style_reference_bytes: Campaign style reference for style adherence (optional)

        Returns:
            CritiqueResult with pass/fail + dimension scores

        Raises:
            ValueError: If image_bytes is invalid (not a valid image format)
        """
        ...


class StubImageCritic:
    """Stub image critique adapter for testing.

    Always returns ACCEPTABLE (pass) with placeholder scores.
    No actual image analysis performed.

    Used for testing contract behavior without model dependencies.
    """

    def __init__(self, always_pass: bool = True, placeholder_score: float = 0.85):
        """Initialize stub critic.

        Args:
            always_pass: If True, always return passed=True. If False, always fail.
            placeholder_score: Score to use for all dimensions (0.0-1.0)
        """
        if not (0.0 <= placeholder_score <= 1.0):
            raise ValueError(f"StubImageCritic placeholder_score must be in [0.0, 1.0], got {placeholder_score}")
        self.always_pass = always_pass
        self.placeholder_score = placeholder_score

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Return placeholder critique result.

        Args:
            image_bytes: Generated image (not analyzed, just validated as bytes)
            rubric: Quality thresholds (used to determine pass/fail)
            anchor_image_bytes: Ignored by stub
            style_reference_bytes: Ignored by stub

        Returns:
            CritiqueResult with placeholder scores

        Raises:
            ValueError: If image_bytes is empty
        """
        if not image_bytes:
            raise ValueError("StubImageCritic requires non-empty image_bytes")

        # Determine pass/fail based on stub configuration
        if self.always_pass:
            severity = SeverityLevel.ACCEPTABLE
            passed = True
            rejection_reason = None
        else:
            severity = SeverityLevel.MAJOR
            passed = False
            rejection_reason = "Stub critic configured to always fail"

        # Create placeholder dimensions (sorted by dimension type)
        dimensions = [
            CritiqueDimension(
                dimension=DimensionType.ARTIFACTING,
                severity=severity,
                score=self.placeholder_score,
                reason="Stub: no actual artifact detection",
                measurement_method="stub"
            ),
            CritiqueDimension(
                dimension=DimensionType.COMPOSITION,
                severity=severity,
                score=self.placeholder_score,
                reason="Stub: no actual composition analysis",
                measurement_method="stub"
            ),
            CritiqueDimension(
                dimension=DimensionType.IDENTITY_MATCH,
                severity=severity if anchor_image_bytes else SeverityLevel.ACCEPTABLE,
                score=self.placeholder_score if anchor_image_bytes else 1.0,
                reason="Stub: no actual identity matching" if anchor_image_bytes else "No anchor provided (skip identity check)",
                measurement_method="stub"
            ),
            CritiqueDimension(
                dimension=DimensionType.READABILITY,
                severity=severity,
                score=self.placeholder_score,
                reason="Stub: no actual readability analysis",
                measurement_method="stub"
            ),
            CritiqueDimension(
                dimension=DimensionType.STYLE_ADHERENCE,
                severity=severity if style_reference_bytes else SeverityLevel.ACCEPTABLE,
                score=self.placeholder_score if style_reference_bytes else 1.0,
                reason="Stub: no actual style matching" if style_reference_bytes else "No style reference provided (skip style check)",
                measurement_method="stub"
            ),
        ]

        return CritiqueResult(
            passed=passed,
            overall_severity=severity,
            dimensions=dimensions,
            overall_score=self.placeholder_score if passed else (self.placeholder_score - 0.2),
            rejection_reason=rejection_reason,
            critique_method="stub"
        )


# Adapter registry (matches STT/TTS pattern)
_IMAGE_CRITIC_REGISTRY: Dict[str, Any] = {
    "stub": StubImageCritic,
    "heuristics": _import_heuristics_critic,  # Lazy import
    "imagereward": _import_imagereward_critic,  # Lazy import
    "graduated": _import_graduated_orchestrator,  # Lazy import
}


def create_image_critic(backend: str = "stub", **kwargs) -> ImageCritiqueAdapter:
    """Factory function for image critique adapters.

    Args:
        backend: Adapter backend name ("stub", "heuristics", "imagereward", or "graduated")
        **kwargs: Backend-specific configuration

    Returns:
        ImageCritiqueAdapter instance

    Raises:
        ValueError: If backend unknown

    Examples:
        # Always pass (default stub)
        critic = create_image_critic("stub")

        # Always fail
        critic = create_image_critic("stub", always_pass=False)

        # Custom placeholder score
        critic = create_image_critic("stub", placeholder_score=0.75)

        # Heuristics-only (CPU, M3 Layer 1)
        critic = create_image_critic("heuristics")

        # Heuristics with custom thresholds
        critic = create_image_critic(
            "heuristics",
            blur_threshold=120.0,
            min_resolution=768,
            edge_density_min=0.08
        )

        # Graduated pipeline (all layers)
        critic = create_image_critic(
            "graduated",
            layer1_backend="heuristics",
            layer2_backend="imagereward",
            layer3_backend="siglip"
        )

        # Graduated pipeline (CPU-only, L1 only)
        critic = create_image_critic(
            "graduated",
            layer1_backend="heuristics",
            layer2_backend=None,
            layer3_backend=None
        )
    """
    if backend not in _IMAGE_CRITIC_REGISTRY:
        available = ", ".join(sorted(_IMAGE_CRITIC_REGISTRY.keys()))
        raise ValueError(f"Unknown image critic backend '{backend}'. Available: {available}")

    # Special handling for "graduated" backend (creates sub-adapters)
    if backend == "graduated":
        layer1_backend = kwargs.pop("layer1_backend", "heuristics")
        layer2_backend = kwargs.pop("layer2_backend", None)
        layer3_backend = kwargs.pop("layer3_backend", None)

        # Create layer adapters recursively
        layer1 = create_image_critic(layer1_backend, **kwargs.get("layer1_kwargs", {}))
        layer2 = create_image_critic(layer2_backend, **kwargs.get("layer2_kwargs", {})) if layer2_backend else None
        layer3 = create_image_critic(layer3_backend, **kwargs.get("layer3_kwargs", {})) if layer3_backend else None

        # Get orchestrator class
        adapter_class_or_factory = _IMAGE_CRITIC_REGISTRY[backend]
        if callable(adapter_class_or_factory) and not isinstance(adapter_class_or_factory, type):
            adapter_class = adapter_class_or_factory()
        else:
            adapter_class = adapter_class_or_factory

        return adapter_class(layer1=layer1, layer2=layer2, layer3=layer3)

    # Standard adapter creation
    adapter_class_or_factory = _IMAGE_CRITIC_REGISTRY[backend]

    # Handle lazy imports (callables that return the class)
    if callable(adapter_class_or_factory) and not isinstance(adapter_class_or_factory, type):
        adapter_class = adapter_class_or_factory()
    else:
        adapter_class = adapter_class_or_factory

    return adapter_class(**kwargs)
