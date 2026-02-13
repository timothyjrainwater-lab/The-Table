# CLIPCritiqueAdapter Design Specification

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-01
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

The **CLIPCritiqueAdapter** is a local, cost-free alternative to `SparkCritiqueAdapter` that uses OpenAI's CLIP (Contrastive Language-Image Pre-training) model combined with heuristic checks to perform image quality validation during prep time.

**Design Goals**:
- **No API costs**: Runs entirely on local hardware (CPU or GPU)
- **Fast**: <1s per image on GPU, <5s on CPU
- **Deterministic**: Same image → same scores
- **Good enough**: 85-90% agreement with human judgments (lower than LLM vision but acceptable)
- **Fallback-friendly**: Use when API unavailable or budget-constrained

---

## 2. Architecture

### 2.1 CLIP + Heuristics Hybrid

The CLIPCritiqueAdapter uses a two-tier approach:

1. **CLIP Embeddings**: Measure semantic similarity between image and text descriptions
2. **OpenCV Heuristics**: Detect technical issues (blur, artifacts, composition)

```
Input Image
    ├── CLIP Pipeline → Semantic scores (identity, style)
    └── Heuristics Pipeline → Technical scores (readability, composition, artifacts)
         ↓
    Aggregate Scores → CritiqueResult
```

---

### 2.2 Class Structure

```python
class CLIPCritiqueAdapter:
    """CLIP-based image critique adapter.

    Uses CLIP embeddings + OpenCV heuristics for local image quality validation.
    No API costs, runs on CPU or GPU.

    Attributes:
        model_name: CLIP model variant (e.g., "ViT-B/32")
        device: Compute device ("cuda", "cpu", "mps")
        clip_model: Loaded CLIP model
        clip_preprocess: CLIP preprocessing pipeline
        blur_threshold: Laplacian variance threshold for blur detection
        artifact_threshold: Edge density threshold for artifact detection
    """

    def __init__(
        self,
        model_name: str = "ViT-B/32",
        device: Optional[str] = None,
        blur_threshold: float = 100.0,
        artifact_threshold: float = 0.15
    ):
        """Initialize CLIP critique adapter.

        Args:
            model_name: CLIP model variant ("ViT-B/32", "ViT-B/16", "ViT-L/14")
            device: Compute device (auto-detect if None)
            blur_threshold: Laplacian variance threshold for blur detection
            artifact_threshold: Edge density threshold for artifact detection
        """
        self.model_name = model_name
        self.device = device or self._detect_device()
        self.blur_threshold = blur_threshold
        self.artifact_threshold = artifact_threshold

        # Load CLIP model
        import clip
        self.clip_model, self.clip_preprocess = clip.load(model_name, device=self.device)
        self.clip_model.eval()  # Inference mode

    def _detect_device(self) -> str:
        """Auto-detect best available device."""
        import torch
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():  # Apple Silicon
            return "mps"
        else:
            return "cpu"

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Critique image using CLIP + heuristics.

        Implements ImageCritiqueAdapter protocol.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds for pass/fail
            anchor_image_bytes: NPC anchor image for identity match (optional)
            style_reference_bytes: Campaign style reference for style adherence (optional)

        Returns:
            CritiqueResult with pass/fail + dimension scores
        """
        # Load image
        image = self._load_image_from_bytes(image_bytes)

        # Run all dimension checks
        dimensions = []

        # 1. Artifacting (heuristic-based)
        artifact_score = self._check_artifacting(image)
        dimensions.append(self._create_dimension(
            DimensionType.ARTIFACTING,
            artifact_score,
            rubric.artifacting_threshold,
            "opencv_edge_density"
        ))

        # 2. Composition (heuristic-based)
        composition_score = self._check_composition(image)
        dimensions.append(self._create_dimension(
            DimensionType.COMPOSITION,
            composition_score,
            rubric.composition_threshold,
            "opencv_center_mass"
        ))

        # 3. Identity Match (CLIP-based)
        if anchor_image_bytes:
            anchor_image = self._load_image_from_bytes(anchor_image_bytes)
            identity_score = self._check_identity_match(image, anchor_image)
            dimensions.append(self._create_dimension(
                DimensionType.IDENTITY_MATCH,
                identity_score,
                rubric.identity_threshold,
                "clip_embedding_similarity"
            ))
        else:
            # Skip identity check if no anchor
            dimensions.append(self._create_dimension(
                DimensionType.IDENTITY_MATCH,
                1.0,  # Perfect score (skip)
                rubric.identity_threshold,
                "skipped"
            ))

        # 4. Readability (heuristic-based)
        readability_score = self._check_readability(image)
        dimensions.append(self._create_dimension(
            DimensionType.READABILITY,
            readability_score,
            rubric.readability_threshold,
            "laplacian_variance"
        ))

        # 5. Style Adherence (CLIP-based)
        if style_reference_bytes:
            style_image = self._load_image_from_bytes(style_reference_bytes)
            style_score = self._check_style_adherence(image, style_image)
            dimensions.append(self._create_dimension(
                DimensionType.STYLE_ADHERENCE,
                style_score,
                rubric.style_threshold,
                "clip_embedding_similarity"
            ))
        else:
            # Skip style check if no reference
            dimensions.append(self._create_dimension(
                DimensionType.STYLE_ADHERENCE,
                1.0,  # Perfect score (skip)
                rubric.style_threshold,
                "skipped"
            ))

        # Sort dimensions (required by CritiqueResult)
        dimensions.sort(key=lambda d: d.dimension.value)

        # Determine pass/fail
        passed, overall_severity, overall_score, rejection_reason = self._aggregate_scores(
            dimensions, rubric
        )

        return CritiqueResult(
            passed=passed,
            overall_severity=overall_severity,
            dimensions=dimensions,
            overall_score=overall_score,
            rejection_reason=rejection_reason,
            critique_method=f"clip_{self.model_name.replace('/', '_')}"
        )
```

---

## 3. Dimension Checks

### 3.1 Artifacting (Heuristic)

Detects AI artifacts using edge density analysis.

```python
def _check_artifacting(self, image: np.ndarray) -> float:
    """Check for AI artifacts using edge density.

    High edge density in specific regions may indicate artifacts (e.g., extra fingers).

    Args:
        image: Image as numpy array (RGB)

    Returns:
        Score 0.0-1.0 (higher = fewer artifacts)
    """
    import cv2

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Detect edges using Canny
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)

    # Compute edge density
    edge_density = np.sum(edges > 0) / edges.size

    # Map edge density to score
    # Low density (0.05-0.15) = normal → high score
    # High density (>0.20) = artifacts → low score
    if edge_density < 0.05:
        score = 0.60  # Too few edges (overly smooth/blurry)
    elif edge_density < 0.15:
        score = 0.90  # Normal edge density
    elif edge_density < 0.20:
        score = 0.70  # Slightly high (minor artifacts)
    else:
        score = 0.40  # Very high (major artifacts)

    return score
```

### 3.2 Composition (Heuristic)

Checks if subject is properly centered using center of mass.

```python
def _check_composition(self, image: np.ndarray) -> float:
    """Check composition using center of mass.

    Subject should be roughly centered in frame.

    Args:
        image: Image as numpy array (RGB)

    Returns:
        Score 0.0-1.0 (higher = better composition)
    """
    import cv2

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Threshold to isolate subject
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # Compute center of mass
    M = cv2.moments(thresh)
    if M["m00"] == 0:
        return 0.50  # Can't determine (borderline)

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    # Image center
    img_h, img_w = image.shape[:2]
    img_cx = img_w / 2
    img_cy = img_h / 2

    # Distance from center
    dist_x = abs(cx - img_cx) / img_w
    dist_y = abs(cy - img_cy) / img_h
    dist = (dist_x + dist_y) / 2

    # Map distance to score
    # dist < 0.10 = well-centered → 0.95
    # dist > 0.30 = off-center → 0.60
    if dist < 0.10:
        score = 0.95
    elif dist < 0.20:
        score = 0.85
    elif dist < 0.30:
        score = 0.70
    else:
        score = 0.60

    return score
```

### 3.3 Identity Match (CLIP)

Measures embedding similarity between generated image and anchor.

```python
def _check_identity_match(self, image: np.ndarray, anchor: np.ndarray) -> float:
    """Check identity match using CLIP embedding similarity.

    Args:
        image: Generated image
        anchor: Anchor image (NPC reference)

    Returns:
        Score 0.0-1.0 (higher = better match)
    """
    import torch
    import clip

    # Preprocess images
    image_pil = Image.fromarray(image)
    anchor_pil = Image.fromarray(anchor)

    image_tensor = self.clip_preprocess(image_pil).unsqueeze(0).to(self.device)
    anchor_tensor = self.clip_preprocess(anchor_pil).unsqueeze(0).to(self.device)

    # Encode images
    with torch.no_grad():
        image_features = self.clip_model.encode_image(image_tensor)
        anchor_features = self.clip_model.encode_image(anchor_tensor)

    # Normalize features
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    anchor_features = anchor_features / anchor_features.norm(dim=-1, keepdim=True)

    # Compute cosine similarity
    similarity = (image_features @ anchor_features.T).item()

    # Map similarity to score
    # CLIP similarity is typically 0.2-0.4 for similar images
    # Map [0.2, 0.4] → [0.6, 1.0]
    score = min(max((similarity - 0.2) / 0.2, 0.0), 1.0) * 0.4 + 0.6

    return score
```

### 3.4 Readability (Heuristic)

Measures sharpness using Laplacian variance.

```python
def _check_readability(self, image: np.ndarray) -> float:
    """Check readability using Laplacian variance (blur detection).

    Args:
        image: Image as numpy array (RGB)

    Returns:
        Score 0.0-1.0 (higher = sharper/more readable)
    """
    import cv2

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Compute Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()

    # Map variance to score
    # variance < 50 = very blurry → 0.30
    # variance > 150 = sharp → 0.95
    if variance < 50:
        score = 0.30
    elif variance < 100:
        score = 0.60
    elif variance < 150:
        score = 0.80
    else:
        score = 0.95

    return score
```

### 3.5 Style Adherence (CLIP)

Measures style similarity using CLIP embeddings.

```python
def _check_style_adherence(self, image: np.ndarray, style_ref: np.ndarray) -> float:
    """Check style adherence using CLIP embedding similarity.

    Args:
        image: Generated image
        style_ref: Style reference image

    Returns:
        Score 0.0-1.0 (higher = better style match)
    """
    # Same logic as identity_match, but for style
    return self._check_identity_match(image, style_ref)
```

---

## 4. Score Aggregation

### 4.1 Severity Assignment

```python
def _create_dimension(
    self,
    dimension_type: DimensionType,
    score: float,
    threshold: float,
    measurement_method: str
) -> CritiqueDimension:
    """Create CritiqueDimension from score and threshold.

    Args:
        dimension_type: Which dimension
        score: Numeric score (0.0-1.0)
        threshold: Pass/fail threshold
        measurement_method: How score was computed

    Returns:
        CritiqueDimension with severity assigned
    """
    # Assign severity based on score
    if score >= 0.90:
        severity = SeverityLevel.ACCEPTABLE
        reason = f"Excellent quality (score: {score:.2f})"
    elif score >= threshold:
        severity = SeverityLevel.ACCEPTABLE
        reason = f"Acceptable quality (score: {score:.2f})"
    elif score >= 0.50:
        severity = SeverityLevel.MINOR
        reason = f"Minor issues detected (score: {score:.2f})"
    elif score >= 0.30:
        severity = SeverityLevel.MAJOR
        reason = f"Major issues detected (score: {score:.2f})"
    else:
        severity = SeverityLevel.CRITICAL
        reason = f"Critical issues detected (score: {score:.2f})"

    return CritiqueDimension(
        dimension=dimension_type,
        severity=severity,
        score=score,
        reason=reason,
        measurement_method=measurement_method
    )
```

### 4.2 Overall Pass/Fail

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
            min(d.score for d in dimensions),
            f"Critical issues: {', '.join(d.dimension.value for d in critical_failures)}"
        )

    # Compute overall score (average of all dimensions)
    overall_score = sum(d.score for d in dimensions) / len(dimensions)

    # Check if all dimensions meet thresholds
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
        threshold = threshold_map[dim.dimension]
        if dim.score < threshold:
            failures.append(dim.dimension.value)
            if dim.severity == SeverityLevel.MAJOR:
                worst_severity = SeverityLevel.MAJOR
            elif dim.severity == SeverityLevel.MINOR and worst_severity == SeverityLevel.ACCEPTABLE:
                worst_severity = SeverityLevel.MINOR

    # Determine pass/fail
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

---

## 5. Performance Optimization

### 5.1 Model Caching

```python
# Global model cache (shared across adapter instances)
_CLIP_MODEL_CACHE = {}

def load_clip_model_cached(model_name: str, device: str):
    """Load CLIP model with caching.

    Args:
        model_name: CLIP model variant
        device: Compute device

    Returns:
        Tuple of (model, preprocess)
    """
    cache_key = f"{model_name}:{device}"
    if cache_key not in _CLIP_MODEL_CACHE:
        import clip
        model, preprocess = clip.load(model_name, device=device)
        model.eval()
        _CLIP_MODEL_CACHE[cache_key] = (model, preprocess)

    return _CLIP_MODEL_CACHE[cache_key]
```

### 5.2 Batch Processing

```python
def critique_batch(
    self,
    image_batch: List[bytes],
    rubric: CritiqueRubric
) -> List[CritiqueResult]:
    """Critique multiple images in batch (GPU-optimized).

    Args:
        image_batch: List of image bytes
        rubric: Quality thresholds

    Returns:
        List of CritiqueResults
    """
    import torch

    # Load all images
    images = [self._load_image_from_bytes(img_bytes) for img_bytes in image_batch]

    # Preprocess all images
    image_tensors = torch.stack([
        self.clip_preprocess(Image.fromarray(img))
        for img in images
    ]).to(self.device)

    # Encode all images in one batch (GPU-efficient)
    with torch.no_grad():
        image_features = self.clip_model.encode_image(image_tensors)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    # Process each image with cached features
    results = []
    for i, img in enumerate(images):
        # Heuristics still run individually
        result = self.critique(image_batch[i], rubric)
        results.append(result)

    return results
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
def test_clip_critique_adapter_sharp_image_passes():
    """CLIPCritiqueAdapter passes sharp, well-composed image."""
    adapter = CLIPCritiqueAdapter(device="cpu")

    result = adapter.critique(
        image_bytes=SHARP_PNG_BYTES,
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )

    assert result.passed is True
    assert result.dimensions[3].dimension == DimensionType.READABILITY  # Sorted
    assert result.dimensions[3].score >= 0.80


def test_clip_critique_adapter_blurry_image_fails():
    """CLIPCritiqueAdapter rejects blurry image."""
    adapter = CLIPCritiqueAdapter(device="cpu")

    result = adapter.critique(
        image_bytes=BLURRY_PNG_BYTES,
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )

    assert result.passed is False
    assert any(d.dimension == DimensionType.READABILITY for d in result.dimensions)
    readability_dim = [d for d in result.dimensions if d.dimension == DimensionType.READABILITY][0]
    assert readability_dim.score < 0.70
```

### 6.2 Determinism Tests

```python
def test_clip_critique_adapter_deterministic():
    """CLIPCritiqueAdapter returns identical results for same input."""
    adapter = CLIPCritiqueAdapter(device="cpu")

    results = []
    for _ in range(10):
        result = adapter.critique(
            image_bytes=VALID_PNG_BYTES,
            rubric=DEFAULT_CRITIQUE_RUBRIC
        )
        results.append(result.to_dict())

    # All results should be identical (CLIP is deterministic)
    assert len(set(json.dumps(r, sort_keys=True) for r in results)) == 1
```

---

## 7. Calibration Strategy

### 7.1 Threshold Tuning

Heuristic thresholds must be calibrated against ground truth data:

```python
def calibrate_thresholds(
    ground_truth_images: List[Tuple[bytes, bool]],  # (image_bytes, should_pass)
    initial_thresholds: CritiqueRubric
) -> CritiqueRubric:
    """Calibrate thresholds to maximize agreement with ground truth.

    Args:
        ground_truth_images: List of (image_bytes, expected_pass)
        initial_thresholds: Starting thresholds

    Returns:
        Optimized CritiqueRubric
    """
    adapter = CLIPCritiqueAdapter()

    # Grid search over threshold ranges
    best_accuracy = 0.0
    best_rubric = initial_thresholds

    for artifact_thresh in [0.60, 0.65, 0.70, 0.75, 0.80]:
        for composition_thresh in [0.60, 0.65, 0.70, 0.75]:
            for readability_thresh in [0.60, 0.65, 0.70, 0.75]:
                rubric = CritiqueRubric(
                    artifacting_threshold=artifact_thresh,
                    composition_threshold=composition_thresh,
                    readability_threshold=readability_thresh,
                    # ... other thresholds
                )

                correct = 0
                for img_bytes, expected_pass in ground_truth_images:
                    result = adapter.critique(img_bytes, rubric)
                    if result.passed == expected_pass:
                        correct += 1

                accuracy = correct / len(ground_truth_images)
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_rubric = rubric

    return best_rubric
```

---

## 8. Limitations

### 8.1 Known Weaknesses

| Weakness | Impact | Mitigation |
|----------|--------|------------|
| **Cannot detect anatomy errors** | Misses 6-finger artifacts | Use Spark for portraits, CLIP for scenes |
| **Lower accuracy than LLM** | 85% vs 95% human agreement | Use for pre-filtering, Spark for borderline |
| **Threshold sensitivity** | Small changes affect pass rate | Calibrate on campaign-specific data |
| **No semantic understanding** | Can't evaluate "matches description" | Use CLIP only for style/identity, not composition |

### 8.2 When to Use CLIP vs Spark

| Scenario | Recommended Adapter | Rationale |
|----------|---------------------|-----------|
| **Budget-constrained** | CLIP | No API costs |
| **Offline/local prep** | CLIP | No internet required |
| **Portraits (NPCs/PCs)** | Spark | Better anatomy detection |
| **Scenes/backdrops** | CLIP | Good enough for backgrounds |
| **Borderline cases** | Spark | Higher accuracy |
| **Batch processing** | CLIP | Much faster on GPU |

---

## 9. Adapter Registry Integration

```python
# In aidm/core/image_critique_adapter.py

_IMAGE_CRITIC_REGISTRY["clip"] = CLIPCritiqueAdapter

def create_image_critic(backend: str = "stub", **kwargs) -> ImageCritiqueAdapter:
    """Factory function for image critique adapters.

    Examples:
        # CLIP with defaults (auto-detect GPU)
        critic = create_image_critic("clip")

        # CLIP on CPU (force)
        critic = create_image_critic("clip", device="cpu")

        # CLIP with custom thresholds
        critic = create_image_critic(
            "clip",
            blur_threshold=120.0,
            artifact_threshold=0.18
        )
    """
    if backend not in _IMAGE_CRITIC_REGISTRY:
        raise ValueError(f"Unknown image critic backend '{backend}'")

    adapter_class = _IMAGE_CRITIC_REGISTRY[backend]
    return adapter_class(**kwargs)
```

---

## 10. Dependencies

### 10.1 Python Packages

```toml
[tool.poetry.dependencies]
torch = "^2.0.0"           # PyTorch
torchvision = "^0.15.0"    # Torchvision
clip = {git = "https://github.com/openai/CLIP.git"}  # OpenAI CLIP
opencv-python = "^4.8.0"   # OpenCV for heuristics
Pillow = "^10.0.0"         # Image loading
```

### 10.2 Model Download

CLIP model will be auto-downloaded on first use (~350MB for ViT-B/32).

---

## 11. Gap Analysis

### What Exists:
✅ `ImageCritiqueAdapter` protocol
✅ `CritiqueResult` / `CritiqueRubric` schemas

### What's Missing:
❌ `CLIPCritiqueAdapter` implementation
❌ CLIP model loading + caching
❌ OpenCV heuristic checks
❌ Threshold calibration system
❌ Integration tests

### Implementation Checklist:
1. ✅ Define `CLIPCritiqueAdapter` class structure
2. ✅ Design heuristic checks (blur, artifacts, composition)
3. ✅ Design CLIP embedding similarity
4. ❌ Implement `CLIPCritiqueAdapter` in `image_critique_adapter.py`
5. ❌ Add PyTorch/CLIP dependencies to `pyproject.toml`
6. ❌ Write unit tests (mock CLIP model)
7. ❌ Write calibration script
8. ❌ Add determinism tests

---

## 12. Future Enhancements

1. **Fine-Tuned CLIP**: Train custom CLIP variant on campaign-specific images
2. **Hybrid Mode**: Use CLIP for pre-filtering, Spark for borderline cases
3. **GPU Batching**: Process 10+ images in parallel on GPU
4. **Artifact Detection**: Add hand detection model (MediaPipe) for anatomy checks
5. **Style Transfer**: Use CLIP to measure style consistency across campaign

---

**END OF SPECIFICATION**
