# ImageRewardCritiqueAdapter Design Specification (Layer 2)

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-02
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

**ImageRewardCritiqueAdapter** is Layer 2 in the graduated critique pipeline. It uses the ImageReward model (NeurIPS 2023) to score text-image alignment—how well a generated image matches its generation prompt.

**Key Advantage**: ImageReward outperforms CLIP by 40% on human preference benchmarks for image quality assessment.

**Model Details**:
- **Paper**: "ImageReward: Learning and Evaluating Human Preferences for Text-to-Image Generation" (NeurIPS 2023)
- **License**: MIT
- **Size**: ~1.0 GB FP16
- **VRAM**: ~1.0 GB peak during inference
- **Performance**: <2s per image on GPU

---

## 2. Architecture

### 2.1 Role in Graduated Pipeline

```
Generated Image + Prompt
    ↓
┌──────────────────────────┐
│ Layer 1: Heuristics      │
│ (passed)                 │
└───────────┬──────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ Layer 2: ImageReward            │ <-- YOU ARE HERE
│ (text-image alignment scoring)  │
│ - Load ImageReward model        │
│ - Score image vs prompt         │
│ - Map score to dimensions       │
│ - Unload model                  │
└──────────┬──────────────────────┘
           │
      ┌────┴────┐
   FAIL       PASS
      │         │
   REJECT    ┌──▼──────────────────┐
             │ Layer 3: SigLIP     │
             │ (optional)          │
             └─────────────────────┘
```

**Sequential Loading**: ImageReward loads AFTER SDXL Lightning unloads (~4 GB freed) → ImageReward loads (~1 GB used) → no VRAM contention.

---

## 3. Class Structure

```python
class ImageRewardCritiqueAdapter:
    """Layer 2: Text-image alignment scoring using ImageReward.

    Implements ImageCritiqueAdapter protocol.

    Attributes:
        model_name: ImageReward model variant (default: "ImageReward-v1.0")
        device: Compute device ("cuda", "cpu", "mps")
        dtype: Model precision (torch.float16 for efficiency)
        alignment_threshold: Score threshold for text-image alignment (default: 0.0)
        model: Loaded ImageReward model (None until load() called)
    """

    def __init__(
        self,
        model_name: str = "ImageReward-v1.0",
        device: Optional[str] = None,
        dtype: torch.dtype = torch.float16,
        alignment_threshold: float = 0.0
    ):
        """Initialize ImageReward critique adapter.

        Args:
            model_name: ImageReward model variant
            device: Compute device (auto-detect if None)
            dtype: Model precision (float16 recommended)
            alignment_threshold: Score threshold for pass/fail
        """
        self.model_name = model_name
        self.device = device or self._detect_device()
        self.dtype = dtype
        self.alignment_threshold = alignment_threshold
        self.model = None  # Lazy loading

    def load(self):
        """Load ImageReward model into memory."""
        import ImageReward as RM
        self.model = RM.load(self.model_name, device=self.device, dtype=self.dtype)

    def unload(self):
        """Unload model and free VRAM."""
        if self.model is not None:
            del self.model
            self.model = None
            torch.cuda.empty_cache()  # Free VRAM

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        prompt: Optional[str] = None,
        **kwargs
    ) -> CritiqueResult:
        """Score text-image alignment.

        Args:
            image_bytes: Generated image
            rubric: Quality thresholds
            prompt: Generation prompt (REQUIRED for ImageReward)
            **kwargs: Ignored

        Returns:
            CritiqueResult with alignment score
        """
        if prompt is None:
            return self._create_error_result("ImageReward requires generation prompt")

        # Load model if not loaded
        if self.model is None:
            self.load()

        # Load image
        image = self._load_image_from_bytes(image_bytes)

        # Score text-image alignment
        try:
            score = self.model.score(prompt, image)  # Returns float
        except Exception as e:
            return self._create_error_result(f"ImageReward scoring failed: {e}")

        # Map ImageReward score to CritiqueResult
        return self._map_score_to_result(score, rubric)
```

---

## 4. Score Mapping

### 4.1 ImageReward Score Range

ImageReward returns a **single float score** (typically -1.0 to +2.0):
- **High score** (>0.5): Image matches prompt well
- **Medium score** (0.0 to 0.5): Acceptable match
- **Low score** (<0.0): Poor match

### 4.2 Mapping to CritiqueResult Dimensions

```python
def _map_score_to_result(
    self,
    imagereward_score: float,
    rubric: CritiqueRubric
) -> CritiqueResult:
    """Map ImageReward score to CritiqueResult.

    Args:
        imagereward_score: Raw ImageReward score (-1.0 to +2.0)
        rubric: Quality thresholds

    Returns:
        CritiqueResult with dimensions populated
    """
    # Normalize ImageReward score to [0.0, 1.0]
    # Empirical range: -1.0 (poor) to +2.0 (excellent)
    # Map: -1.0 → 0.0, 0.0 → 0.33, 1.0 → 0.67, 2.0 → 1.0
    normalized_score = (imagereward_score + 1.0) / 3.0
    normalized_score = np.clip(normalized_score, 0.0, 1.0)

    dimensions = []

    # ImageReward primarily measures identity_match (prompt alignment)
    dimensions.append(CritiqueDimension(
        dimension=DimensionType.IDENTITY_MATCH,
        severity=self._score_to_severity(normalized_score, rubric.identity_threshold),
        score=normalized_score,
        reason=f"Text-image alignment (ImageReward score: {imagereward_score:.2f})",
        measurement_method="imagereward_v1"
    ))

    # ImageReward also captures style_adherence (aesthetic quality)
    dimensions.append(CritiqueDimension(
        dimension=DimensionType.STYLE_ADHERENCE,
        severity=self._score_to_severity(normalized_score, rubric.style_threshold),
        score=normalized_score,
        reason=f"Aesthetic quality (ImageReward score: {imagereward_score:.2f})",
        measurement_method="imagereward_v1"
    ))

    # Skip dimensions that ImageReward doesn't measure
    dimensions.append(CritiqueDimension(
        dimension=DimensionType.ARTIFACTING,
        severity=SeverityLevel.ACCEPTABLE,
        score=1.0,
        reason="ImageReward does not measure artifacts (use Layer 1 heuristics)",
        measurement_method="skipped"
    ))

    dimensions.append(CritiqueDimension(
        dimension=DimensionType.COMPOSITION,
        severity=SeverityLevel.ACCEPTABLE,
        score=1.0,
        reason="ImageReward does not measure composition (use Layer 1 heuristics)",
        measurement_method="skipped"
    ))

    dimensions.append(CritiqueDimension(
        dimension=DimensionType.READABILITY,
        severity=SeverityLevel.ACCEPTABLE,
        score=1.0,
        reason="ImageReward does not measure readability (use Layer 1 heuristics)",
        measurement_method="skipped"
    ))

    # Sort dimensions
    dimensions.sort(key=lambda d: d.dimension.value)

    # Determine pass/fail
    passed = normalized_score >= self.alignment_threshold

    return CritiqueResult(
        passed=passed,
        overall_severity=self._score_to_severity(normalized_score, self.alignment_threshold),
        dimensions=dimensions,
        overall_score=normalized_score,
        rejection_reason=None if passed else f"Low text-image alignment (score: {imagereward_score:.2f})",
        critique_method="imagereward_v1"
    )
```

---

## 5. Threshold Calibration

### 5.1 Calibration Strategy

```python
def calibrate_threshold(
    ground_truth_pairs: List[Tuple[bytes, str, bool]],  # (image, prompt, should_pass)
    candidate_thresholds: List[float]
) -> float:
    """Calibrate alignment_threshold on ground truth data.

    Args:
        ground_truth_pairs: List of (image_bytes, prompt, expected_pass)
        candidate_thresholds: Thresholds to test (e.g., [-0.5, 0.0, 0.5, 1.0])

    Returns:
        Best threshold (highest F1 score)
    """
    critic = ImageRewardCritiqueAdapter()
    critic.load()

    best_f1 = 0.0
    best_threshold = 0.0

    for threshold in candidate_thresholds:
        critic.alignment_threshold = threshold

        true_positives = 0
        false_positives = 0
        false_negatives = 0

        for img_bytes, prompt, should_pass in ground_truth_pairs:
            result = critic.critique(img_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt=prompt)
            if result.passed and should_pass:
                true_positives += 1
            elif result.passed and not should_pass:
                false_positives += 1
            elif not result.passed and should_pass:
                false_negatives += 1

        # Compute F1 score
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    critic.unload()
    return best_threshold
```

### 5.2 Expected Threshold

Based on ImageReward paper:
- **Threshold = 0.0**: Balanced (recommended starting point)
- **Threshold = -0.5**: More lenient (fewer false rejections)
- **Threshold = 0.5**: Stricter (fewer false acceptances)

---

## 6. Error Handling

### 6.1 Fallback on Model Load Failure

```python
def critique(self, image_bytes, rubric, prompt=None, **kwargs):
    """Critique with fallback to heuristics if model fails."""
    try:
        if self.model is None:
            self.load()
    except Exception as e:
        # Model failed to load → fall back to Layer 1 (heuristics)
        logger.warning(f"ImageReward failed to load: {e}. Falling back to heuristics.")
        heuristics_critic = create_image_critic("heuristics")
        return heuristics_critic.critique(image_bytes, rubric)

    # Continue with ImageReward scoring...
```

---

## 7. Performance Analysis

### 7.1 Timing Breakdown

| Operation | Time (GPU) | Notes |
|-----------|------------|-------|
| **Model load** (first time) | ~3s | One-time cost per prep session |
| **Image preprocessing** | ~50ms | Resize, normalize |
| **Model inference** | ~1.5s | Forward pass through BLIP backbone |
| **TOTAL per image** | **~1.6s** | ✅ Under 2s target |

### 7.2 VRAM Usage

| Stage | VRAM | Notes |
|-------|------|-------|
| **Model weights** | ~1.0 GB | FP16 precision |
| **Activations** | ~0.2 GB | During inference |
| **Peak** | **~1.2 GB** | Well under 4 GB budget |

---

## 8. Testing Strategy

```python
def test_imagereward_critic_aligned_image_passes():
    """ImageRewardCritiqueAdapter passes well-aligned image."""
    critic = create_image_critic("imagereward")
    critic.load()

    result = critic.critique(
        image_bytes=DWARF_CLERIC_IMAGE,
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        prompt="A stern dwarf cleric with a gray beard"
    )

    assert result.passed is True
    identity_dim = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH][0]
    assert identity_dim.score >= 0.60

    critic.unload()


def test_imagereward_critic_misaligned_image_fails():
    """ImageRewardCritiqueAdapter rejects misaligned image."""
    critic = create_image_critic("imagereward", alignment_threshold=0.0)
    critic.load()

    result = critic.critique(
        image_bytes=DWARF_CLERIC_IMAGE,
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        prompt="A young elf wizard with blonde hair"  # Mismatched prompt
    )

    assert result.passed is False
    assert "low text-image alignment" in result.rejection_reason.lower()

    critic.unload()
```

---

## 9. Dependencies

```toml
[tool.poetry.dependencies]
image-reward = {git = "https://github.com/THUDM/ImageReward.git"}  # MIT license
torch = "^2.0.0"
torchvision = "^0.15.0"
Pillow = "^10.0.0"
```

---

## 10. Integration with Graduated Pipeline

```python
def critique_layer_1_and_2(
    image_bytes: bytes,
    generation_prompt: str,
    rubric: CritiqueRubric
) -> CritiqueResult:
    """Run Layers 1 and 2 sequentially.

    Args:
        image_bytes: Generated image
        generation_prompt: Prompt used to generate image
        rubric: Quality thresholds

    Returns:
        CritiqueResult from first failing layer or Layer 2
    """
    # Layer 1: Heuristics (CPU, fast rejection)
    layer1_critic = create_image_critic("heuristics")
    layer1_result = layer1_critic.critique(image_bytes, rubric)

    if not layer1_result.passed:
        return layer1_result  # Reject without loading GPU model

    # Layer 2: ImageReward (GPU, text-image alignment)
    layer2_critic = create_image_critic("imagereward")
    layer2_critic.load()
    layer2_result = layer2_critic.critique(image_bytes, rubric, prompt=generation_prompt)
    layer2_critic.unload()

    return layer2_result
```

---

## 11. Gap Analysis

### What Exists:
✅ ImageCritiqueAdapter protocol
✅ CritiqueResult schemas

### What's Missing:
❌ ImageRewardCritiqueAdapter implementation
❌ image-reward dependency
❌ Threshold calibration data

### Implementation Checklist:
1. ✅ Design complete
2. ❌ Add image-reward to pyproject.toml
3. ❌ Implement ImageRewardCritiqueAdapter
4. ❌ Calibrate alignment_threshold on ground truth
5. ❌ Write tests (model loading, scoring, fallback)
6. ❌ Profile VRAM usage and performance

---

**END OF SPECIFICATION**
