"""Heuristics-based image critique adapter (Layer 1).

M3 IMPLEMENTATION: HeuristicsImageCritic
----------------------------------------
CPU-only, ML-free quality checks for fast rejection of bad images.
No GPU models, no VRAM usage. Target: <100ms per image.

This is Layer 1 of the graduated critique pipeline. It catches obvious failures
(blur, wrong resolution, corruption) before loading expensive GPU models.

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_heuristics_design.md

Architecture:
    - 5 heuristic checks: blur, composition, format, corruption, color distribution
    - Uses OpenCV + Pillow for image analysis
    - Maps checks to CritiqueDimension types
    - Implements ImageCritiqueAdapter protocol
"""

from typing import Optional, Tuple, List
import io
import numpy as np
from PIL import Image
import cv2

from aidm.schemas.image_critique import (
    CritiqueResult,
    CritiqueRubric,
    CritiqueDimension,
    DimensionType,
    SeverityLevel,
)


class HeuristicsImageCritic:
    """Layer 1: CPU-only heuristic quality checks.

    Catches obvious failures (blur, wrong resolution, corruption) before
    loading GPU models. No machine learning models, no VRAM usage.

    Implements ImageCritiqueAdapter protocol.

    Attributes:
        blur_threshold: Laplacian variance threshold for blur detection (default: 100.0)
        min_resolution: Minimum acceptable resolution in pixels (default: 512)
        max_resolution: Maximum acceptable resolution in pixels (default: 2048)
        aspect_ratio_tolerance: Acceptable deviation from 1:1 (default: 0.15)
        edge_density_min: Minimum edge density (too smooth = artifact) (default: 0.05)
        edge_density_max: Maximum edge density (too noisy = artifact) (default: 0.25)
    """

    def __init__(
        self,
        blur_threshold: float = 100.0,
        min_resolution: int = 512,
        max_resolution: int = 2048,
        aspect_ratio_tolerance: float = 0.15,
        edge_density_min: float = 0.05,
        edge_density_max: float = 0.25
    ):
        """Initialize heuristics critic.

        Args:
            blur_threshold: Laplacian variance threshold (higher = sharper)
            min_resolution: Minimum acceptable width/height
            max_resolution: Maximum acceptable width/height
            aspect_ratio_tolerance: Max deviation from 1:1 aspect ratio
            edge_density_min: Minimum edge density (rejects overly smooth)
            edge_density_max: Maximum edge density (rejects overly noisy)
        """
        self.blur_threshold = blur_threshold
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        self.aspect_ratio_tolerance = aspect_ratio_tolerance
        self.edge_density_min = edge_density_min
        self.edge_density_max = edge_density_max

    def load(self):
        """Load resources (no-op for CPU-only heuristics).

        Required by ImageCritiqueAdapter protocol but not needed for heuristics.
        """
        pass

    def unload(self):
        """Unload resources (no-op for CPU-only heuristics).

        Required by ImageCritiqueAdapter protocol but not needed for heuristics.
        """
        pass

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Perform heuristic quality checks.

        Implements ImageCritiqueAdapter protocol.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds (used for overall scoring)
            anchor_image_bytes: Ignored by heuristics (Layer 3 handles this)
            style_reference_bytes: Ignored by heuristics

        Returns:
            CritiqueResult with pass/fail + dimension scores
        """
        # Load image
        try:
            image = self._load_image_from_bytes(image_bytes)
        except Exception as e:
            return self._create_error_result(f"Image load failed: {e}")

        # Run all heuristic checks
        dimensions = []

        # Check 1: Readability (blur detection)
        blur_score, blur_reason = self._check_blur(image)
        dimensions.append(self._create_dimension(
            DimensionType.READABILITY,
            blur_score,
            rubric.readability_threshold,
            blur_reason,
            "laplacian_variance"
        ))

        # Check 2: Composition (center of mass, edge density)
        composition_score, composition_reason = self._check_composition(image)
        dimensions.append(self._create_dimension(
            DimensionType.COMPOSITION,
            composition_score,
            rubric.composition_threshold,
            composition_reason,
            "center_mass_edge_density"
        ))

        # Check 3: Format validation (resolution, aspect ratio, color space)
        format_score, format_reason = self._check_format(image)
        # Map format check to artifacting dimension (corruption = artifact)
        dimensions.append(self._create_dimension(
            DimensionType.ARTIFACTING,
            format_score,
            rubric.artifacting_threshold,
            format_reason,
            "format_validation"
        ))

        # Check 4: Corruption detection (transparency, uniformity)
        corruption_score, corruption_reason = self._check_corruption(image)
        # Also maps to artifacting - take worst score
        if corruption_score < format_score:
            dimensions[-1] = self._create_dimension(
                DimensionType.ARTIFACTING,
                corruption_score,
                rubric.artifacting_threshold,
                corruption_reason,
                "corruption_detection"
            )

        # Heuristics cannot check identity or style (requires ML models)
        # Set these to 1.0 (skip) so they don't fail overall score
        dimensions.append(self._create_dimension(
            DimensionType.IDENTITY_MATCH,
            1.0,
            rubric.identity_threshold,
            "Heuristics cannot check identity (requires Layer 3)",
            "skipped"
        ))

        dimensions.append(self._create_dimension(
            DimensionType.STYLE_ADHERENCE,
            1.0,
            rubric.style_threshold,
            "Heuristics cannot check style (requires Layer 2/3)",
            "skipped"
        ))

        # Sort dimensions (required by CritiqueResult)
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
            critique_method="heuristics_cpu"
        )

    def _load_image_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Load image from bytes.

        Args:
            image_bytes: PNG/JPEG bytes

        Returns:
            Image as numpy array (RGB)

        Raises:
            ValueError: If image cannot be loaded
        """
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            # Convert to RGB (removes alpha if present)
            pil_image = pil_image.convert('RGB')
            # Convert to numpy array
            image = np.array(pil_image)
            return image
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")

    def _check_blur(self, image: np.ndarray) -> Tuple[float, str]:
        """Detect blur using Laplacian variance.

        Args:
            image: Image as numpy array (RGB)

        Returns:
            Tuple of (score, reason)
            Score 0.0-1.0 (higher = sharper)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Compute Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # Map variance to score
        # variance < 50: very blurry → score 0.30
        # variance < 100: blurry → score 0.60
        # variance >= 100: sharp → score 0.95
        if variance < 50:
            score = 0.30
            reason = f"Very blurry (Laplacian variance: {variance:.1f}, threshold: 50)"
        elif variance < self.blur_threshold:
            score = 0.60
            reason = f"Slightly blurry (Laplacian variance: {variance:.1f}, threshold: {self.blur_threshold})"
        else:
            score = 0.95
            reason = f"Sharp (Laplacian variance: {variance:.1f})"

        return score, reason

    def _check_center_of_mass(self, image: np.ndarray) -> Tuple[float, str]:
        """Check if subject is centered using center of mass.

        Args:
            image: Image as numpy array (RGB)

        Returns:
            Tuple of (score, reason)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Threshold to isolate subject
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # Compute center of mass
        M = cv2.moments(thresh)
        if M["m00"] == 0:
            return 0.50, "Cannot determine center of mass (uniform image)"

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # Image center
        img_h, img_w = image.shape[:2]
        img_cx = img_w / 2
        img_cy = img_h / 2

        # Distance from center (normalized)
        dist_x = abs(cx - img_cx) / img_w
        dist_y = abs(cy - img_cy) / img_h
        dist = (dist_x + dist_y) / 2

        # Map distance to score
        if dist < 0.10:
            score = 0.95
            reason = f"Well-centered (offset: {dist:.2%})"
        elif dist < 0.20:
            score = 0.85
            reason = f"Slightly off-center (offset: {dist:.2%})"
        elif dist < 0.30:
            score = 0.70
            reason = f"Off-center (offset: {dist:.2%})"
        else:
            score = 0.50
            reason = f"Poorly centered (offset: {dist:.2%})"

        return score, reason

    def _check_edge_density(self, image: np.ndarray) -> Tuple[float, str]:
        """Check edge density (too low = overly smooth, too high = noisy artifacts).

        Args:
            image: Image as numpy array (RGB)

        Returns:
            Tuple of (score, reason)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Detect edges using Canny
        edges = cv2.Canny(gray, threshold1=50, threshold2=150)

        # Compute edge density
        edge_density = np.sum(edges > 0) / edges.size

        # Map edge density to score
        if edge_density < self.edge_density_min:
            score = 0.60
            reason = f"Too smooth (edge density: {edge_density:.3f}, min: {self.edge_density_min})"
        elif edge_density > self.edge_density_max:
            score = 0.50
            reason = f"Too noisy (edge density: {edge_density:.3f}, max: {self.edge_density_max})"
        else:
            score = 0.90
            reason = f"Normal edge density ({edge_density:.3f})"

        return score, reason

    def _check_composition(self, image: np.ndarray) -> Tuple[float, str]:
        """Check composition (center of mass + edge density).

        Args:
            image: Image as numpy array (RGB)

        Returns:
            Tuple of (score, reason)
        """
        center_score, center_reason = self._check_center_of_mass(image)
        edge_score, edge_reason = self._check_edge_density(image)

        # Average the two scores
        score = (center_score + edge_score) / 2

        # Combine reasons
        reason = f"Center: {center_reason}; Edges: {edge_reason}"

        return score, reason

    def _check_format(self, image: np.ndarray) -> Tuple[float, str]:
        """Validate image format (resolution, aspect ratio, color space).

        Args:
            image: Image as numpy array (RGB)

        Returns:
            Tuple of (score, reason)
        """
        issues = []
        score = 1.0  # Start perfect, deduct for issues

        # Check resolution
        h, w = image.shape[:2]
        if w < self.min_resolution or h < self.min_resolution:
            issues.append(f"Resolution too low ({w}x{h}, min: {self.min_resolution})")
            score -= 0.4
        elif w > self.max_resolution or h > self.max_resolution:
            issues.append(f"Resolution too high ({w}x{h}, max: {self.max_resolution})")
            score -= 0.2

        # Check aspect ratio (should be close to square for portraits)
        aspect_ratio = w / h
        deviation = abs(aspect_ratio - 1.0)
        if deviation > self.aspect_ratio_tolerance:
            issues.append(f"Aspect ratio off (ratio: {aspect_ratio:.2f}, expected: 1.0 ± {self.aspect_ratio_tolerance})")
            score -= 0.3

        # Check color space (should be RGB)
        if len(image.shape) != 3 or image.shape[2] != 3:
            issues.append(f"Invalid color space (expected RGB, got shape: {image.shape})")
            score -= 0.5

        # Ensure score stays in [0.0, 1.0]
        score = max(score, 0.0)

        if issues:
            reason = "; ".join(issues)
        else:
            reason = f"Valid format ({w}x{h}, aspect ratio: {aspect_ratio:.2f})"

        return score, reason

    def _check_corruption(self, image: np.ndarray) -> Tuple[float, str]:
        """Detect image corruption (transparency, uniformity, invalid data).

        Args:
            image: Image as numpy array (RGB)

        Returns:
            Tuple of (score, reason)
        """
        issues = []
        score = 1.0

        # Check for uniformity (completely black, white, or single color)
        std_dev = np.std(image)
        if std_dev < 5.0:  # Very low variation
            issues.append(f"Uniformly colored (std dev: {std_dev:.2f})")
            score -= 0.6

        # Check for extreme values (overflow/underflow)
        if np.any(image == 0) and np.all(image <= 10):
            issues.append("Image is mostly black (possible corruption)")
            score -= 0.5
        elif np.any(image == 255) and np.all(image >= 245):
            issues.append("Image is mostly white (possible corruption)")
            score -= 0.5

        # Ensure score stays in [0.0, 1.0]
        score = max(score, 0.0)

        if issues:
            reason = "; ".join(issues)
        else:
            reason = "No corruption detected"

        return score, reason

    def _create_dimension(
        self,
        dimension_type: DimensionType,
        score: float,
        threshold: float,
        reason: str,
        measurement_method: str
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
            measurement_method=measurement_method
        )

    def _aggregate_scores(
        self,
        dimensions: List[CritiqueDimension],
        rubric: CritiqueRubric
    ) -> Tuple[bool, SeverityLevel, float, Optional[str]]:
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
                min(d.score for d in dimensions if d.score < 1.0),  # Ignore skipped dimensions
                f"Critical failures: {', '.join(d.dimension.value for d in critical_failures)}"
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
                f"Failed thresholds: {', '.join(failures)}"
            )
        else:
            return (
                True,
                SeverityLevel.ACCEPTABLE,
                overall_score,
                None
            )

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
            critique_method="heuristics_error"
        )