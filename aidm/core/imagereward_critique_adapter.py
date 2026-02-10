"""ImageReward critique adapter for AIDM immersion pipeline.

M3 IMPLEMENTATION (LAYER 2)
---------------------------
This module implements Layer 2 of the graduated image critique pipeline using
the ImageReward model (NeurIPS 2023) for text-image alignment scoring.

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_imagereward_design.md

Layer 2 runs AFTER Layer 1 (HeuristicsImageCritic) passes. Provides semantic
quality validation using learned text-image alignment model.

Performance:
- Model load: ~4s (1.0 GB VRAM for FP16)
- Inference: ~1.6s per image (GPU)
- Total: ~5.6s first call, ~1.6s subsequent calls

ImageReward model:
- Source: https://github.com/THUDM/ImageReward
- Paper: NeurIPS 2023 (ImageReward: Learning and Evaluating Human Preferences)
- License: MIT
- Model size: ~1.0 GB (FP16)
- Score range: [-1.0, +2.0] (normalized to [0.0, 1.0])
"""

from typing import Optional
import numpy as np
from aidm.schemas.image_critique import (
    CritiqueResult,
    CritiqueRubric,
    CritiqueDimension,
    DimensionType,
    SeverityLevel,
)


class ImageRewardCritiqueAdapter:
    """Layer 2: ImageReward text-image alignment scoring.

    Uses ImageReward model to validate semantic quality and text-image alignment.
    Runs AFTER Layer 1 heuristics pass. Requires GPU for reasonable performance.

    Implements ImageCritiqueAdapter protocol.

    Attributes:
        model_name: ImageReward model identifier (default: "ImageReward-v1.0")
        device: Compute device ("cuda", "mps", or "cpu")
        dtype: Model precision (torch.float16 recommended for efficiency)
        alignment_threshold: Minimum alignment score for IDENTITY_MATCH dimension
        model: Loaded ImageReward model (None until load() called)
    """

    def __init__(
        self,
        model_name: str = "ImageReward-v1.0",
        device: Optional[str] = None,
        alignment_threshold: float = 0.0,
    ):
        """Initialize ImageReward critic.

        Args:
            model_name: ImageReward model identifier
            device: Compute device (None = auto-detect: cuda > mps > cpu)
            alignment_threshold: Minimum alignment score for IDENTITY_MATCH
        """
        self.model_name = model_name
        self.alignment_threshold = alignment_threshold
        self.model = None
        self._dtype = None  # Will be set when torch is imported

        # Auto-detect device if not specified
        if device is None:
            # Lazy import torch
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device

    def load(self):
        """Load ImageReward model into VRAM.

        This is called automatically on first critique() if not already loaded.
        Can also be called explicitly to preload the model.

        Model load time: ~4 seconds (1.0 GB VRAM for FP16).
        """
        if self.model is not None:
            return  # Already loaded

        # Lazy import dependencies
        import torch
        import ImageReward as RM

        # Set dtype if not already set
        if self._dtype is None:
            self._dtype = torch.float16

        # Load model
        self.model = RM.load(
            name=self.model_name,
            device=self.device,
            download_root=None,  # Use default cache
            med_config=None,     # Use default config
        )

        # Convert to FP16 if using CUDA
        if self.device == "cuda" and self._dtype == torch.float16:
            self.model = self.model.half()

    def unload(self):
        """Unload ImageReward model from VRAM.

        Frees ~1.0 GB VRAM (FP16). Call this after critique pipeline completes
        to free VRAM for other models (e.g., SDXL).
        """
        if self.model is not None:
            del self.model
            self.model = None

            # Clear CUDA cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        prompt: Optional[str] = None,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None,
    ) -> CritiqueResult:
        """Perform ImageReward text-image alignment scoring.

        Implements ImageCritiqueAdapter protocol.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds (used for overall scoring)
            prompt: Text prompt used to generate image (REQUIRED)
            anchor_image_bytes: Ignored by ImageReward (Layer 3 handles this)
            style_reference_bytes: Ignored by ImageReward (Layer 3 handles this)

        Returns:
            CritiqueResult with pass/fail + dimension scores

        Raises:
            ValueError: If prompt is None (ImageReward requires prompt)
        """
        # Validate prompt requirement
        if prompt is None:
            return self._create_error_result(
                "ImageReward requires prompt parameter (text used to generate image)"
            )

        # Lazy load model if not already loaded
        if self.model is None:
            try:
                self.load()
            except Exception as e:
                return self._create_error_result(f"Model load failed: {e}")

        # Score image using ImageReward
        try:
            score = self._score_image(image_bytes, prompt)
        except Exception as e:
            return self._create_error_result(f"ImageReward scoring failed: {e}")

        # Normalize score from [-1.0, +2.0] to [0.0, 1.0]
        normalized_score = self._normalize_score(score)

        # Create dimensions
        dimensions = []

        # Skip Layer 1 dimensions (handled by HeuristicsImageCritic)
        dimensions.append(
            self._create_dimension(
                DimensionType.ARTIFACTING,
                1.0,
                rubric.artifacting_threshold,
                "ImageReward cannot check artifacts (requires Layer 1)",
                "skipped",
            )
        )

        dimensions.append(
            self._create_dimension(
                DimensionType.COMPOSITION,
                1.0,
                rubric.composition_threshold,
                "ImageReward cannot check composition (requires Layer 1)",
                "skipped",
            )
        )

        dimensions.append(
            self._create_dimension(
                DimensionType.READABILITY,
                1.0,
                rubric.readability_threshold,
                "ImageReward cannot check readability (requires Layer 1)",
                "skipped",
            )
        )

        # ImageReward dimensions (text-image alignment)
        # Use same score for both IDENTITY_MATCH and STYLE_ADHERENCE
        dimensions.append(
            self._create_dimension(
                DimensionType.IDENTITY_MATCH,
                normalized_score,
                rubric.identity_threshold,
                f"Text-image alignment score: {score:.3f} (normalized: {normalized_score:.3f})",
                "imagereward_alignment",
            )
        )

        dimensions.append(
            self._create_dimension(
                DimensionType.STYLE_ADHERENCE,
                normalized_score,
                rubric.style_threshold,
                f"Text-image alignment score: {score:.3f} (normalized: {normalized_score:.3f})",
                "imagereward_alignment",
            )
        )

        # Sort dimensions (required by CritiqueResult schema)
        dimensions.sort(key=lambda d: d.dimension.value)

        # Aggregate scores
        passed, overall_severity, overall_score, rejection_reason = self._aggregate_scores(
            dimensions, rubric
        )

        return CritiqueResult(
            passed=passed,
            overall_severity=overall_severity,
            dimensions=dimensions,
            overall_score=overall_score,
            rejection_reason=rejection_reason,
            critique_method="imagereward_gpu",
        )

    def _score_image(self, image_bytes: bytes, prompt: str) -> float:
        """Score image using ImageReward model.

        Args:
            image_bytes: Image as PNG/JPEG bytes
            prompt: Text prompt used to generate image

        Returns:
            Raw ImageReward score (range: [-1.0, +2.0])

        Raises:
            ValueError: If image cannot be loaded
        """
        from PIL import Image
        import io

        # Load image
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            pil_image = pil_image.convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")

        # Score with ImageReward
        # ImageReward.score() expects: prompt (str), image (PIL.Image)
        score = self.model.score(prompt, pil_image)

        # ImageReward returns numpy scalar or float
        if isinstance(score, np.ndarray):
            score = float(score.item())
        else:
            score = float(score)

        return score

    def _normalize_score(self, score: float) -> float:
        """Normalize ImageReward score to [0.0, 1.0].

        ImageReward returns scores in range [-1.0, +2.0].
        We normalize to [0.0, 1.0] using: (score + 1.0) / 3.0

        Args:
            score: Raw ImageReward score

        Returns:
            Normalized score in [0.0, 1.0]
        """
        normalized = (score + 1.0) / 3.0
        # Clip to ensure [0.0, 1.0] (handle edge cases)
        normalized = np.clip(normalized, 0.0, 1.0)
        return float(normalized)

    def _create_dimension(
        self,
        dimension_type: DimensionType,
        score: float,
        threshold: float,
        reason: str,
        measurement_method: str,
    ) -> CritiqueDimension:
        """Create CritiqueDimension from score.

        Args:
            dimension_type: Which dimension
            score: Numeric score (0.0-1.0)
            threshold: Pass/fail threshold
            reason: Human-readable explanation
            measurement_method: How score was computed

        Returns:
            CritiqueDimension with severity assigned
        """
        # Assign severity based on score
        if score >= 0.90:
            severity = SeverityLevel.ACCEPTABLE
        elif score >= threshold:
            severity = SeverityLevel.ACCEPTABLE
        elif score >= 0.50:
            severity = SeverityLevel.MINOR
        elif score >= 0.30:
            severity = SeverityLevel.MAJOR
        else:
            severity = SeverityLevel.CRITICAL

        return CritiqueDimension(
            dimension=dimension_type,
            severity=severity,
            score=score,
            reason=reason,
            measurement_method=measurement_method,
        )

    def _aggregate_scores(
        self,
        dimensions: list[CritiqueDimension],
        rubric: CritiqueRubric,
    ) -> tuple[bool, SeverityLevel, float, Optional[str]]:
        """Aggregate dimension scores into overall result.

        Args:
            dimensions: List of dimension results
            rubric: Quality thresholds

        Returns:
            Tuple of (passed, overall_severity, overall_score, rejection_reason)
        """
        # Check for CRITICAL failures (auto-reject)
        critical_failures = [d for d in dimensions if d.severity == SeverityLevel.CRITICAL]
        if critical_failures:
            return (
                False,
                SeverityLevel.CRITICAL,
                min(d.score for d in dimensions if d.score < 1.0),
                f"Critical failures: {', '.join(d.dimension.value for d in critical_failures)}",
            )

        # Compute overall score (average of non-skipped dimensions)
        scored_dimensions = [d for d in dimensions if d.score < 1.0]
        if scored_dimensions:
            overall_score = sum(d.score for d in scored_dimensions) / len(scored_dimensions)
        else:
            overall_score = 1.0  # All dimensions skipped

        # Check threshold failures
        threshold_map = {
            DimensionType.ARTIFACTING: rubric.artifacting_threshold,
            DimensionType.COMPOSITION: rubric.composition_threshold,
            DimensionType.IDENTITY_MATCH: rubric.identity_threshold,
            DimensionType.READABILITY: rubric.readability_threshold,
            DimensionType.STYLE_ADHERENCE: rubric.style_threshold,
        }

        failures = []
        worst_severity = SeverityLevel.ACCEPTABLE

        for dim in dimensions:
            if dim.score >= 1.0:  # Skipped dimension
                continue
            threshold = threshold_map[dim.dimension]
            if dim.score < threshold:
                failures.append(dim.dimension.value)
                if dim.severity == SeverityLevel.MAJOR:
                    worst_severity = SeverityLevel.MAJOR
                elif dim.severity == SeverityLevel.MINOR and worst_severity == SeverityLevel.ACCEPTABLE:
                    worst_severity = SeverityLevel.MINOR

        if failures:
            return (
                False,
                worst_severity,
                overall_score,
                f"Failed thresholds: {', '.join(failures)}",
            )
        else:
            return (True, SeverityLevel.ACCEPTABLE, overall_score, None)

    def _create_error_result(self, error_message: str) -> CritiqueResult:
        """Create error CritiqueResult.

        Args:
            error_message: Error description

        Returns:
            CritiqueResult with passed=False and error information
        """
        return CritiqueResult(
            passed=False,
            overall_severity=SeverityLevel.CRITICAL,
            dimensions=[],
            overall_score=0.0,
            rejection_reason=error_message,
            critique_method="imagereward_error",
        )
