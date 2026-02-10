# HeuristicsImageCritic Design Specification (Layer 1)

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-02
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

**HeuristicsImageCritic** is the first layer in the graduated critique pipeline. It performs CPU-only, ML-free quality checks to catch obvious failures (blur, wrong resolution, corruption) before loading any GPU models.

**Design Principle**: Fast rejection of bad images (<100ms) prevents wasting GPU time on obviously broken assets.

---

## 2. Architecture

### 2.1 Role in Graduated Pipeline

```
Generated Image
    ↓
┌─────────────────────────┐
│ Layer 1: Heuristics     │ <-- YOU ARE HERE
│ (CPU-only, no ML)       │
│ - Blur detection        │
│ - Composition checks    │
│ - Format validation     │
│ - Corruption detection  │
└──────────┬──────────────┘
           │
      ┌────┴────┐
   FAIL       PASS
      │         │
   REJECT    ┌──▼──────────────────────┐
             │ Layer 2: ImageReward    │
             │ (GPU, text-image align) │
             └─────────────────────────┘
```

**Key Constraint**: This MUST be a standalone adapter. Do NOT fold heuristics into ImageReward. The entire point of Layer 1 is catching failures without loading a 1 GB GPU model.

---

### 2.2 Class Structure

```python
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

        # Check 4: Transparency/corruption detection
        corruption_score, corruption_reason = self._check_corruption(image)
        # Also maps to artifacting
        if corruption_score < format_score:  # Take worst score
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
```

---

## 3. Heuristic Checks

### 3.1 Blur Detection (Readability)

Uses Laplacian variance to detect blur. Higher variance = sharper image.

```python
def _check_blur(self, image: np.ndarray) -> Tuple[float, str]:
    """Detect blur using Laplacian variance.

    Args:
        image: Image as numpy array (RGB)

    Returns:
        Tuple of (score, reason)
        Score 0.0-1.0 (higher = sharper)
    """
    import cv2

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
```

**Calibration Notes**:
- Typical sharp images: variance > 150
- Acceptable: variance > 100
- Blurry: variance < 100
- Very blurry: variance < 50

---

### 3.2 Composition Checks

Two sub-checks: center of mass and edge density.

#### 3.2.1 Center of Mass

```python
def _check_center_of_mass(self, image: np.ndarray) -> Tuple[float, str]:
    """Check if subject is centered using center of mass.

    Args:
        image: Image as numpy array (RGB)

    Returns:
        Tuple of (score, reason)
    """
    import cv2

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
```

#### 3.2.2 Edge Density

```python
def _check_edge_density(self, image: np.ndarray) -> Tuple[float, str]:
    """Check edge density (too low = overly smooth, too high = noisy artifacts).

    Args:
        image: Image as numpy array (RGB)

    Returns:
        Tuple of (score, reason)
    """
    import cv2

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
```

#### 3.2.3 Combined Composition Score

```python
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
```

---

### 3.3 Format Validation

Checks resolution, aspect ratio, and color space.

```python
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
```

---

### 3.4 Corruption Detection

Checks for transparency, uniformity, and file corruption indicators.

```python
def _check_corruption(self, image: np.ndarray) -> Tuple[float, str]:
    """Detect image corruption (transparency, uniformity, invalid data).

    Args:
        image: Image as numpy array (RGB)

    Returns:
        Tuple of (score, reason)
    """
    issues = []
    score = 1.0

    # Check for unexpected transparency (should be opaque RGB)
    # If image was loaded with alpha channel, it would have shape (H, W, 4)
    # Since we load as RGB, this is already handled by format check

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
```

---

## 4. Helper Methods

### 4.1 Image Loading

```python
def _load_image_from_bytes(self, image_bytes: bytes) -> np.ndarray:
    """Load image from bytes.

    Args:
        image_bytes: PNG/JPEG bytes

    Returns:
        Image as numpy array (RGB)

    Raises:
        ValueError: If image cannot be loaded
    """
    from PIL import Image
    import io

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        # Convert to RGB (removes alpha if present)
        pil_image = pil_image.convert('RGB')
        # Convert to numpy array
        image = np.array(pil_image)
        return image
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")
```

### 4.2 Dimension Creation

```python
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
```

### 4.3 Score Aggregation

```python
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
```

### 4.4 Error Result Factory

```python
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
```

---

## 5. Performance Analysis

### 5.1 Timing Breakdown

| Operation | Time (CPU) | Notes |
|-----------|------------|-------|
| **Image load** | ~10ms | Pillow decode |
| **Blur detection** | ~20ms | Laplacian variance |
| **Center of mass** | ~15ms | Moments calculation |
| **Edge density** | ~25ms | Canny edge detection |
| **Format checks** | ~5ms | Shape/resolution checks |
| **Corruption checks** | ~10ms | Statistics (std dev, min/max) |
| **TOTAL** | **~85ms** | ✅ Under 100ms target |

### 5.2 Performance Optimization

```python
# Cache grayscale conversion (used by multiple checks)
def critique(self, image_bytes, rubric, **kwargs):
    # Load image once
    image = self._load_image_from_bytes(image_bytes)

    # Convert to grayscale once (cache for reuse)
    import cv2
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Pass grayscale to all checks that need it
    blur_score, blur_reason = self._check_blur_cached(gray)
    composition_score, composition_reason = self._check_composition_cached(gray, image)
    # ...
```

---

## 6. Calibration Strategy

### 6.1 Threshold Tuning

Heuristic thresholds must be calibrated on ground truth data:

```python
def calibrate_heuristics(
    ground_truth_images: List[Tuple[bytes, Dict[str, bool]]],  # (image_bytes, {dimension: should_pass})
    initial_thresholds: Dict[str, float]
) -> Dict[str, float]:
    """Calibrate heuristic thresholds.

    Args:
        ground_truth_images: List of (image_bytes, dimension_labels)
        initial_thresholds: Starting thresholds for each check

    Returns:
        Optimized thresholds
    """
    # Grid search over threshold ranges
    best_accuracy = {
        "blur": 0.0,
        "composition": 0.0,
        "format": 0.0
    }
    best_thresholds = initial_thresholds.copy()

    # Tune blur_threshold
    for blur_thresh in range(50, 200, 10):
        critic = HeuristicsImageCritic(blur_threshold=blur_thresh)
        correct = sum(
            1 for img_bytes, labels in ground_truth_images
            if (critic._check_blur(load_image(img_bytes))[0] >= 0.70) == labels["blur_pass"]
        )
        accuracy = correct / len(ground_truth_images)
        if accuracy > best_accuracy["blur"]:
            best_accuracy["blur"] = accuracy
            best_thresholds["blur_threshold"] = blur_thresh

    # Similar grid search for edge_density_min, edge_density_max, etc.

    return best_thresholds
```

### 6.2 Expected Accuracy

| Check | Expected Accuracy | Notes |
|-------|-------------------|-------|
| **Blur detection** | 90-95% | Laplacian variance is reliable |
| **Composition** | 70-80% | Center of mass is approximate |
| **Format validation** | 99%+ | Binary checks (resolution, aspect ratio) |
| **Corruption detection** | 85-90% | Catches extreme cases |

**Overall**: ~85-90% accuracy for rejecting obviously bad images.

---

## 7. Adapter Registry Integration

```python
# In aidm/core/image_critique_adapter.py

_IMAGE_CRITIC_REGISTRY["heuristics"] = HeuristicsImageCritic

def create_image_critic(backend: str = "stub", **kwargs) -> ImageCritiqueAdapter:
    """Factory function for image critique adapters.

    Examples:
        # Heuristics with defaults
        critic = create_image_critic("heuristics")

        # Heuristics with custom thresholds
        critic = create_image_critic(
            "heuristics",
            blur_threshold=120.0,
            min_resolution=768,
            edge_density_min=0.08
        )
    """
    if backend not in _IMAGE_CRITIC_REGISTRY:
        raise ValueError(f"Unknown image critic backend '{backend}'")

    adapter_class = _IMAGE_CRITIC_REGISTRY[backend]
    return adapter_class(**kwargs)
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
def test_heuristics_critic_sharp_image_passes():
    """HeuristicsImageCritic passes sharp, well-composed image."""
    critic = HeuristicsImageCritic()

    result = critic.critique(
        image_bytes=SHARP_CENTERED_PNG,
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )

    assert result.passed is True
    readability_dim = [d for d in result.dimensions if d.dimension == DimensionType.READABILITY][0]
    assert readability_dim.score >= 0.90


def test_heuristics_critic_blurry_image_fails():
    """HeuristicsImageCritic rejects blurry image."""
    critic = HeuristicsImageCritic(blur_threshold=100.0)

    result = critic.critique(
        image_bytes=BLURRY_PNG,
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )

    assert result.passed is False
    readability_dim = [d for d in result.dimensions if d.dimension == DimensionType.READABILITY][0]
    assert readability_dim.score < 0.70
    assert "blurry" in readability_dim.reason.lower()


def test_heuristics_critic_wrong_resolution_fails():
    """HeuristicsImageCritic rejects image with wrong resolution."""
    critic = HeuristicsImageCritic(min_resolution=512)

    result = critic.critique(
        image_bytes=LOW_RES_PNG_256x256,
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )

    assert result.passed is False
    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert "resolution too low" in artifact_dim.reason.lower()


def test_heuristics_critic_performance_under_100ms():
    """HeuristicsImageCritic completes in under 100ms."""
    import time
    critic = HeuristicsImageCritic()

    start = time.time()
    result = critic.critique(
        image_bytes=VALID_PNG_512x512,
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )
    elapsed = time.time() - start

    assert elapsed < 0.100  # 100ms
```

---

## 9. Dependencies

### 9.1 Python Packages

```toml
[tool.poetry.dependencies]
opencv-python = "^4.8.0"   # OpenCV for heuristics
Pillow = "^10.0.0"         # Image loading
numpy = "^1.24.0"          # Array operations
```

**No ML models, no GPU, no VRAM.**

---

## 10. Limitations

### 10.1 What Heuristics Cannot Do

| Cannot Detect | Why | Alternative |
|---------------|-----|-------------|
| **Anatomy errors** (6 fingers) | No semantic understanding | Layer 2 (ImageReward) |
| **Style mismatch** | No learned style representation | Layer 3 (SigLIP) |
| **Text-image alignment** | No prompt analysis | Layer 2 (ImageReward) |
| **Identity consistency** | No reference comparison | Layer 3 (SigLIP) |

**Heuristics are Layer 1 only**: Fast rejection of obvious failures. Layers 2 and 3 handle semantic quality.

---

## 11. Gap Analysis

### What Exists:
✅ `ImageCritiqueAdapter` protocol
✅ `CritiqueResult` schemas
✅ Test infrastructure

### What's Missing:
❌ `HeuristicsImageCritic` implementation
❌ OpenCV/Pillow integration
❌ Calibration data for threshold tuning

### Implementation Checklist:
1. ✅ Design complete (this document)
2. ❌ Implement `HeuristicsImageCritic` class
3. ❌ Add OpenCV/Pillow dependencies
4. ❌ Write unit tests (blur, composition, format, corruption)
5. ❌ Calibrate thresholds on ground truth images
6. ❌ Profile performance (verify <100ms target)

---

## 12. Integration with Graduated Pipeline

### 12.1 Sequential Flow

```python
def critique_graduated(
    image_bytes: bytes,
    generation_prompt: str,
    rubric: CritiqueRubric
) -> CritiqueResult:
    """Run graduated critique pipeline.

    Args:
        image_bytes: Generated image
        generation_prompt: Text prompt used to generate image
        rubric: Quality thresholds

    Returns:
        CritiqueResult from first failing layer or final layer
    """
    # Layer 1: Heuristics (always runs, CPU-only)
    heuristics_critic = create_image_critic("heuristics")
    layer1_result = heuristics_critic.critique(image_bytes, rubric)

    if not layer1_result.passed:
        # Failed Layer 1 → reject immediately (don't load GPU models)
        return layer1_result

    # Layer 2: ImageReward (GPU, text-image alignment)
    imagereward_critic = create_image_critic("imagereward")
    layer2_result = imagereward_critic.critique(image_bytes, rubric, prompt=generation_prompt)

    if not layer2_result.passed:
        # Failed Layer 2 → reject (don't run Layer 3)
        return layer2_result

    # Layer 3: SigLIP (optional, reference comparison)
    # Only run if reference images exist
    # (Implementation detail for Layer 3 design doc)

    return layer2_result  # Passed all layers
```

---

**END OF SPECIFICATION**
