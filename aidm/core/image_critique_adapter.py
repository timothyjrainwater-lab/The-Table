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
}


def create_image_critic(backend: str = "stub", **kwargs) -> ImageCritiqueAdapter:
    """Factory function for image critique adapters.

    Args:
        backend: Adapter backend name ("stub" only for now)
        **kwargs: Backend-specific configuration

    Returns:
        ImageCritiqueAdapter instance

    Raises:
        ValueError: If backend unknown

    Examples:
        # Always pass (default)
        critic = create_image_critic("stub")

        # Always fail
        critic = create_image_critic("stub", always_pass=False)

        # Custom placeholder score
        critic = create_image_critic("stub", placeholder_score=0.75)

        # Future: Heuristics-only (CPU)
        # critic = create_image_critic("heuristics")

        # Future: CLIP + heuristics (GPU)
        # critic = create_image_critic("clip", device="cuda")

        # Future: Hybrid (auto-detect GPU)
        # critic = create_image_critic("hybrid")
    """
    if backend not in _IMAGE_CRITIC_REGISTRY:
        available = ", ".join(sorted(_IMAGE_CRITIC_REGISTRY.keys()))
        raise ValueError(f"Unknown image critic backend '{backend}'. Available: {available}")

    adapter_class = _IMAGE_CRITIC_REGISTRY[backend]
    return adapter_class(**kwargs)
