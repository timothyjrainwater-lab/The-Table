# Image Critique Adapters Design Document
**Work Order:** WO-M3-IMAGE-CRITIQUE-01
**Agent:** Sonnet-B
**Date:** 2026-02-11
**Status:** Design Specification (Implementation Deferred to M3 Execution)
**Authority:** R1 Technology Stack Validation (Section 2: Image Critique)

---

## Executive Summary

This document specifies the design for three image critique adapters that implement automated quality validation for AIDM-generated images during the prep phase. The design follows R1's graduated three-layer filtering approach, where images pass through progressively more sophisticated validation layers.

**Key Design Principles:**
- **Graduated filtering**: Fast CPU heuristics filter obvious failures before expensive GPU models
- **Separate adapters**: Each layer is an independent adapter following the ImageCritiqueAdapter protocol
- **Model specifications from R1**: ImageReward (1.0 GB FP16) and SigLIP (0.6 GB FP16)
- **Implementation deferred**: This is design-only; actual implementation happens during M3 execution

**Three Adapters:**
1. **HeuristicsImageCritic** (Layer 1: CPU, <100ms, 0 VRAM)
2. **ImageRewardCritiqueAdapter** (Layer 2: GPU, ~100ms, ~1.0 GB FP16)
3. **SigLIPCritiqueAdapter** (Layer 3: GPU, ~100ms, ~0.6 GB FP16)

---

## Background

### Existing Infrastructure

The image critique system has a complete schema layer and adapter protocol already implemented:

- **[aidm/schemas/image_critique.py](../../aidm/schemas/image_critique.py)** (337 lines)
  - 5 quality dimensions (readability, composition, artifacting, style adherence, identity match)
  - CritiqueResult, CritiqueRubric, CritiqueDimension, RegenerationAttempt contracts
  - Severity levels (CRITICAL, MAJOR, MINOR, ACCEPTABLE)

- **[aidm/core/image_critique_adapter.py](../../aidm/core/image_critique_adapter.py)** (226 lines)
  - ImageCritiqueAdapter protocol (runtime-checkable)
  - StubImageCritic (placeholder for testing)
  - create_image_critic() factory with registry pattern

- **[tests/test_image_critique.py](../../tests/test_image_critique.py)** (619 lines)
  - Comprehensive Tier-1 and Tier-2 tests
  - All tests passing

### R1 Model Selections

Per [R1 Technology Stack Validation](../pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md) Section 2 (lines 80-141):

- **Layer 1 (Heuristics)**: OpenCV-based checks (Laplacian variance, BRISQUE, saliency detection)
- **Layer 2 (ImageReward)**: THUDM/ImageReward (NeurIPS 2023), beats CLIP by 40% on text-image alignment
- **Layer 3 (SigLIP)**: Google SigLIP (2024-2025), CLIP successor with better calibration

**Performance Target:**
- Layer 1 alone: F1 0.60-0.65
- Layer 1 + 2: F1 0.80-0.85
- Layer 1 + 2 + 3: F1 0.85-0.90

---

## Layer 1: HeuristicsImageCritic (CPU)

### Purpose

Fast, CPU-only quality checks that filter obvious failures before invoking GPU models. Provides baseline quality assurance even on systems without GPU.

### Quality Dimensions Covered

| Dimension | Method | Metric | Threshold |
|-----------|--------|--------|-----------|
| **Readability** (DIM-01) | Laplacian variance | Edge sharpness | var > 100 |
| **Readability** (DIM-01) | Contrast ratio | Foreground/background separation | ratio > 3.0 |
| **Composition** (DIM-02) | Center-of-mass analysis | Subject centering | distance < 0.2 × width |
| **Composition** (DIM-02) | Bounding box area | Subject occupies frame | 0.4 < ratio < 0.7 |
| **Artifacting** (DIM-03) | BRISQUE score | Perceptual quality | score < 40 |
| **Identity Match** (DIM-05) | Perceptual hash (pHash) | Similarity to anchor | hamming distance < 10 |

**Dimensions NOT covered by Layer 1:**
- **Style Adherence** (DIM-04): Requires semantic understanding (deferred to Layer 2/3)

### Architecture

```python
class HeuristicsImageCritic:
    """CPU-only heuristic-based image critique adapter.

    Implements fast quality checks using OpenCV and image processing libraries.
    No GPU required. Suitable for minimum hardware tier (Tier 4-5).

    Based on R1 § Layer 1: Heuristics.
    """

    def __init__(self, rubric: Optional[CritiqueRubric] = None):
        """Initialize heuristics critic.

        Args:
            rubric: Quality thresholds (uses DEFAULT_CRITIQUE_RUBRIC if None)
        """
        self.rubric = rubric or DEFAULT_CRITIQUE_RUBRIC

        # Heuristic-specific thresholds (calibrated in M3)
        self.laplacian_threshold = 100.0
        self.contrast_threshold = 3.0
        self.brisque_threshold = 40.0
        self.centering_tolerance = 0.2
        self.area_ratio_range = (0.4, 0.7)
        self.phash_distance_threshold = 10

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Run heuristic quality checks on image.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds for pass/fail
            anchor_image_bytes: NPC anchor image for identity match (optional)
            style_reference_bytes: Ignored by Layer 1 (style requires semantic understanding)

        Returns:
            CritiqueResult with heuristic-based dimension scores
        """
        # Implementation deferred to M3
        pass
```

### Implementation Steps (Deferred to M3)

1. **Load image from bytes**
   - Decode image_bytes using PIL or OpenCV
   - Convert to RGB and grayscale representations

2. **DIM-01: Readability checks**
   - Laplacian variance (edge sharpness):
     ```python
     gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
     laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
     readability_score_1 = min(laplacian_var / 100.0, 1.0)
     ```
   - Contrast ratio (foreground/background separation):
     ```python
     fg_brightness = np.mean(np.percentile(image, [80, 90, 95, 100]))
     bg_brightness = np.mean(np.percentile(image, [0, 5, 10, 20]))
     contrast_ratio = fg_brightness / (bg_brightness + 1e-6)
     readability_score_2 = min(contrast_ratio / 3.0, 1.0)
     ```
   - Aggregate: `readability_score = (readability_score_1 + readability_score_2) / 2`

3. **DIM-02: Composition checks**
   - Center-of-mass analysis:
     ```python
     # Simple saliency detection (foreground mask)
     gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
     _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
     M = cv2.moments(thresh)
     cx = int(M['m10'] / (M['m00'] + 1e-6))
     cy = int(M['m01'] / (M['m00'] + 1e-6))
     img_center = (image.shape[1] / 2, image.shape[0] / 2)
     distance = np.sqrt((cx - img_center[0])**2 + (cy - img_center[1])**2)
     max_distance = image.shape[1] * 0.2
     composition_score_1 = 1.0 - min(distance / max_distance, 1.0)
     ```
   - Bounding box area ratio:
     ```python
     # Detect subject bounding box using contours
     contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
     largest_contour = max(contours, key=cv2.contourArea)
     x, y, w, h = cv2.boundingRect(largest_contour)
     subject_area = w * h
     image_area = image.shape[0] * image.shape[1]
     area_ratio = subject_area / image_area
     if 0.4 <= area_ratio <= 0.7:
         composition_score_2 = 1.0
     else:
         composition_score_2 = 0.5  # Partial credit
     ```
   - Aggregate: `composition_score = (composition_score_1 + composition_score_2) / 2`

4. **DIM-03: Artifacting checks (BRISQUE)**
   - BRISQUE (Blind/Referenceless Image Spatial Quality Evaluator):
     ```python
     import pyiqa
     brisque_metric = pyiqa.create_metric('brisque')
     brisque_score = brisque_metric(image_tensor).item()  # Lower is better
     # BRISQUE range: 0-100, threshold 40
     artifacting_score = 1.0 - min(brisque_score / 40.0, 1.0)
     ```

5. **DIM-05: Identity match (perceptual hash)**
   - Only if `anchor_image_bytes` provided:
     ```python
     import imagehash
     from PIL import Image

     anchor_img = Image.open(io.BytesIO(anchor_image_bytes))
     generated_img = Image.open(io.BytesIO(image_bytes))

     phash_anchor = imagehash.phash(anchor_img)
     phash_generated = imagehash.phash(generated_img)

     hamming_distance = phash_anchor - phash_generated  # 0 = identical, 64 = opposite
     identity_score = 1.0 - min(hamming_distance / 10.0, 1.0)
     ```
   - If no anchor provided: `identity_score = 1.0` (skip check)

6. **DIM-04: Style adherence (skipped)**
   - Heuristics cannot check style adherence (requires semantic understanding)
   - Set `style_score = None` (dimension not assessed by Layer 1)

7. **Aggregate and return CritiqueResult**
   - Determine `overall_severity` (worst severity across dimensions)
   - Determine `passed` (all assessed dimensions meet thresholds)
   - Return `CritiqueResult` with `critique_method="heuristics"`

### Dependencies

```python
# Layer 1 dependencies (CPU-only)
opencv-python>=4.8.0  # Laplacian, thresholding, contours
pillow>=10.0.0        # Image loading
numpy>=1.24.0         # Array operations
imagehash>=4.3.0      # Perceptual hashing for identity match
pyiqa>=0.1.12         # BRISQUE metric
```

### Performance Characteristics

- **Latency**: <100 ms (CPU)
- **Memory**: <200 MB (no model loading)
- **VRAM**: 0 GB
- **F1 Score**: 0.60-0.65 (per R1)
- **False Positive Rate**: 0.15-0.20 (may block acceptable images)
- **False Negative Rate**: 0.10-0.15 (may allow minor issues)

### Use Cases

- **Tier 4-5 Hardware**: Systems without GPU or with limited VRAM
- **Fast Pre-Filtering**: First-pass validation before GPU models (Layer 2/3)
- **Development/Testing**: Quick validation during local development

---

## Layer 2: ImageRewardCritiqueAdapter (GPU)

### Purpose

Text-image alignment scoring using ImageReward model (THUDM, NeurIPS 2023). Validates that generated images match the text prompt semantically. Provides 40% better alignment scoring than CLIP (per R1).

### Quality Dimensions Covered

| Dimension | Method | Metric | Threshold |
|-----------|--------|--------|-----------|
| **Style Adherence** (DIM-04) | Text-image alignment | ImageReward score | score > 0.7 |
| **Artifacting** (DIM-03) | Anomaly detection | Deviation from expected distribution | score > 0.7 |

**Note**: ImageReward is a **supplementary** layer. It does NOT replace Layer 1 heuristics; images should pass Layer 1 first, then be validated by Layer 2.

### Architecture

```python
class ImageRewardCritiqueAdapter:
    """GPU-accelerated text-image alignment critique using ImageReward.

    Uses THUDM/ImageReward (NeurIPS 2023) for semantic quality validation.
    Requires GPU with ~1.0 GB VRAM (FP16).

    Based on R1 § Layer 2: ImageReward.
    """

    def __init__(
        self,
        model_path: str = "THUDM/ImageReward",
        device: str = "cuda",
        precision: str = "fp16",
        rubric: Optional[CritiqueRubric] = None
    ):
        """Initialize ImageReward critic.

        Args:
            model_path: HuggingFace model identifier or local path
            device: Device for inference ("cuda" or "cpu")
            precision: Model precision ("fp16" or "fp32")
            rubric: Quality thresholds (uses DEFAULT_CRITIQUE_RUBRIC if None)
        """
        self.model_path = model_path
        self.device = device
        self.precision = precision
        self.rubric = rubric or DEFAULT_CRITIQUE_RUBRIC

        self.model = None  # Lazy-loaded in first critique() call
        self.preprocess = None

    def _load_model(self):
        """Load ImageReward model (lazy initialization)."""
        if self.model is not None:
            return  # Already loaded

        # Implementation deferred to M3
        # import ImageReward as RM
        # self.model = RM.load(self.model_path, device=self.device)
        pass

    def _unload_model(self):
        """Unload model to free VRAM."""
        if self.model is not None:
            del self.model
            self.model = None
            torch.cuda.empty_cache()

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None,
        prompt: Optional[str] = None
    ) -> CritiqueResult:
        """Run ImageReward quality checks on image.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds for pass/fail
            anchor_image_bytes: Ignored by Layer 2 (identity matching is Layer 1)
            style_reference_bytes: Ignored by Layer 2 (reference comparison is Layer 3)
            prompt: Text prompt used to generate image (REQUIRED for Layer 2)

        Returns:
            CritiqueResult with ImageReward-based dimension scores

        Raises:
            ValueError: If prompt is None (ImageReward requires text prompt)
        """
        # Implementation deferred to M3
        pass
```

### Implementation Steps (Deferred to M3)

1. **Load ImageReward model (lazy initialization)**
   ```python
   import ImageReward as RM

   if self.model is None:
       self.model = RM.load(self.model_path, device=self.device)
       if self.precision == "fp16":
           self.model = self.model.half()
   ```

2. **Decode image from bytes**
   ```python
   from PIL import Image
   import io

   image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
   ```

3. **Compute ImageReward score (text-image alignment)**
   ```python
   # ImageReward expects (image, prompt) pair
   score = self.model.score(prompt, image)  # Returns float in [-10, 10] range

   # Normalize to [0, 1] range (approximate, calibrate in M3)
   normalized_score = (score + 10) / 20.0
   normalized_score = max(0.0, min(normalized_score, 1.0))
   ```

4. **DIM-04: Style adherence scoring**
   - ImageReward score directly measures text-image alignment
   - High score → image matches prompt style semantically
   - `style_score = normalized_score`

5. **DIM-03: Artifacting detection (supplementary)**
   - ImageReward implicitly penalizes artifacts (they reduce alignment score)
   - Use same normalized score as proxy for artifact-free quality
   - `artifacting_score = normalized_score`

6. **Create CritiqueDimension entries**
   ```python
   dimensions = [
       CritiqueDimension(
           dimension=DimensionType.ARTIFACTING,
           severity=self._score_to_severity(artifacting_score, rubric.artifacting_threshold),
           score=artifacting_score,
           reason=f"ImageReward alignment score: {score:.2f} (normalized: {normalized_score:.2f})",
           measurement_method="imagereward"
       ),
       CritiqueDimension(
           dimension=DimensionType.STYLE_ADHERENCE,
           severity=self._score_to_severity(style_score, rubric.style_threshold),
           score=style_score,
           reason=f"ImageReward text-image alignment: {score:.2f}",
           measurement_method="imagereward"
       ),
   ]
   ```

7. **Return CritiqueResult**
   - `critique_method="imagereward"`
   - `overall_score = normalized_score`
   - `passed = (style_score >= rubric.style_threshold) and (artifacting_score >= rubric.artifacting_threshold)`

### Dependencies

```python
# Layer 2 dependencies (GPU-accelerated)
image-reward>=1.0       # THUDM/ImageReward model
torch>=2.0.0            # PyTorch for GPU inference
torchvision>=0.15.0     # Image preprocessing
pillow>=10.0.0          # Image loading
```

### Performance Characteristics

- **Latency**: ~100 ms (GPU), ~500 ms (CPU fallback, not recommended)
- **Memory**: ~1.0 GB VRAM (FP16), ~2.0 GB VRAM (FP32)
- **Model Size**: ~1.0 GB (FP16), ~2.0 GB (FP32)
- **F1 Score**: 0.80-0.85 (Layer 1 + Layer 2 combined, per R1)
- **False Positive Rate**: 0.08-0.12 (better than CLIP)
- **False Negative Rate**: 0.05-0.08

### Use Cases

- **Tier 1-3 Hardware**: Systems with GPU and ≥2 GB VRAM
- **Semantic Validation**: Check that image matches text prompt semantically
- **Style Adherence**: Validate fantasy vs sci-fi style matching

---

## Layer 3: SigLIPCritiqueAdapter (GPU)

### Purpose

Reference-based image comparison using SigLIP (Google 2024-2025, CLIP successor). Validates that generated images match reference images (anchor portraits for identity, style references for campaign consistency). Better calibration than CLIP for similarity scoring.

### Quality Dimensions Covered

| Dimension | Method | Metric | Threshold |
|-----------|--------|--------|-----------|
| **Identity Match** (DIM-05) | Image-image similarity | SigLIP embedding cosine similarity | similarity > 0.70 |
| **Style Adherence** (DIM-04) | Style reference comparison | SigLIP embedding cosine similarity | similarity > 0.65 |

**Note**: SigLIP is a **reference-based** layer. It only activates when `anchor_image_bytes` or `style_reference_bytes` is provided. Otherwise, it returns ACCEPTABLE (skip).

### Architecture

```python
class SigLIPCritiqueAdapter:
    """GPU-accelerated reference-based critique using SigLIP.

    Uses Google SigLIP (CLIP successor, 2024-2025) for image-image similarity.
    Requires GPU with ~0.6 GB VRAM (FP16).

    Based on R1 § Layer 3: SigLIP.
    """

    def __init__(
        self,
        model_name: str = "hf-hub:timm/ViT-SO400M-14-SigLIP-384",
        device: str = "cuda",
        precision: str = "fp16",
        rubric: Optional[CritiqueRubric] = None
    ):
        """Initialize SigLIP critic.

        Args:
            model_name: Open-CLIP model name for SigLIP
            device: Device for inference ("cuda" or "cpu")
            precision: Model precision ("fp16" or "fp32")
            rubric: Quality thresholds (uses DEFAULT_CRITIQUE_RUBRIC if None)
        """
        self.model_name = model_name
        self.device = device
        self.precision = precision
        self.rubric = rubric or DEFAULT_CRITIQUE_RUBRIC

        self.model = None  # Lazy-loaded in first critique() call
        self.preprocess = None
        self.tokenizer = None

    def _load_model(self):
        """Load SigLIP model (lazy initialization)."""
        if self.model is not None:
            return  # Already loaded

        # Implementation deferred to M3
        # import open_clip
        # self.model, _, self.preprocess = open_clip.create_model_and_transforms(self.model_name)
        # self.model = self.model.to(self.device)
        # if self.precision == "fp16":
        #     self.model = self.model.half()
        pass

    def _unload_model(self):
        """Unload model to free VRAM."""
        if self.model is not None:
            del self.model
            del self.preprocess
            self.model = None
            self.preprocess = None
            torch.cuda.empty_cache()

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Run SigLIP reference-based quality checks on image.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds for pass/fail
            anchor_image_bytes: NPC anchor image for identity match (optional)
            style_reference_bytes: Campaign style reference for style adherence (optional)

        Returns:
            CritiqueResult with SigLIP-based dimension scores

        Note:
            If neither anchor_image_bytes nor style_reference_bytes is provided,
            this layer returns ACCEPTABLE (no reference-based checks to perform).
        """
        # Implementation deferred to M3
        pass
```

### Implementation Steps (Deferred to M3)

1. **Load SigLIP model (lazy initialization)**
   ```python
   import open_clip
   import torch

   if self.model is None:
       self.model, _, self.preprocess = open_clip.create_model_and_transforms(self.model_name)
       self.model = self.model.to(self.device)
       if self.precision == "fp16":
           self.model = self.model.half()
   ```

2. **Decode images from bytes**
   ```python
   from PIL import Image
   import io

   generated_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

   if anchor_image_bytes:
       anchor_img = Image.open(io.BytesIO(anchor_image_bytes)).convert("RGB")
   else:
       anchor_img = None

   if style_reference_bytes:
       style_img = Image.open(io.BytesIO(style_reference_bytes)).convert("RGB")
   else:
       style_img = None
   ```

3. **Compute SigLIP embeddings**
   ```python
   with torch.no_grad():
       generated_tensor = self.preprocess(generated_img).unsqueeze(0).to(self.device)
       if self.precision == "fp16":
           generated_tensor = generated_tensor.half()

       generated_embedding = self.model.encode_image(generated_tensor)
       generated_embedding = generated_embedding / generated_embedding.norm(dim=-1, keepdim=True)
   ```

4. **DIM-05: Identity match (if anchor provided)**
   ```python
   if anchor_img is not None:
       anchor_tensor = self.preprocess(anchor_img).unsqueeze(0).to(self.device)
       if self.precision == "fp16":
           anchor_tensor = anchor_tensor.half()

       anchor_embedding = self.model.encode_image(anchor_tensor)
       anchor_embedding = anchor_embedding / anchor_embedding.norm(dim=-1, keepdim=True)

       identity_similarity = (generated_embedding @ anchor_embedding.T).item()  # Cosine similarity
       identity_score = identity_similarity  # Already in [0, 1] range (normalized embeddings)
   else:
       identity_score = 1.0  # Skip check (no anchor provided)
       identity_similarity = None
   ```

5. **DIM-04: Style adherence (if style reference provided)**
   ```python
   if style_img is not None:
       style_tensor = self.preprocess(style_img).unsqueeze(0).to(self.device)
       if self.precision == "fp16":
           style_tensor = style_tensor.half()

       style_embedding = self.model.encode_image(style_tensor)
       style_embedding = style_embedding / style_embedding.norm(dim=-1, keepdim=True)

       style_similarity = (generated_embedding @ style_embedding.T).item()
       style_score = style_similarity
   else:
       style_score = 1.0  # Skip check (no style reference provided)
       style_similarity = None
   ```

6. **Create CritiqueDimension entries**
   ```python
   dimensions = []

   if anchor_img is not None:
       dimensions.append(CritiqueDimension(
           dimension=DimensionType.IDENTITY_MATCH,
           severity=self._score_to_severity(identity_score, rubric.identity_threshold),
           score=identity_score,
           reason=f"SigLIP anchor similarity: {identity_similarity:.3f}",
           measurement_method="siglip_embedding_similarity"
       ))

   if style_img is not None:
       dimensions.append(CritiqueDimension(
           dimension=DimensionType.STYLE_ADHERENCE,
           severity=self._score_to_severity(style_score, rubric.style_threshold),
           score=style_score,
           reason=f"SigLIP style reference similarity: {style_similarity:.3f}",
           measurement_method="siglip_embedding_similarity"
       ))
   ```

7. **Return CritiqueResult**
   - If no references provided: return ACCEPTABLE (no checks to perform)
   - Otherwise: aggregate dimension scores and return result
   - `critique_method="siglip"`

### Dependencies

```python
# Layer 3 dependencies (GPU-accelerated)
open-clip-torch>=2.24.0   # SigLIP model via Open-CLIP
torch>=2.0.0              # PyTorch for GPU inference
torchvision>=0.15.0       # Image preprocessing
pillow>=10.0.0            # Image loading
```

### Performance Characteristics

- **Latency**: ~100 ms (GPU), ~400 ms (CPU fallback, not recommended)
- **Memory**: ~0.6 GB VRAM (FP16), ~1.2 GB VRAM (FP32)
- **Model Size**: ~0.6 GB (FP16), ~1.2 GB (FP32)
- **F1 Score**: 0.85-0.90 (Layer 1 + Layer 2 + Layer 3 combined, per R1)
- **False Positive Rate**: 0.05-0.08
- **False Negative Rate**: 0.03-0.05

### Use Cases

- **Tier 1-2 Hardware**: Systems with GPU and ≥1.5 GB VRAM
- **NPC Identity Continuity**: Validate regenerated portraits match anchor image
- **Campaign Style Consistency**: Validate images match campaign style reference

---

## Graduated Filtering Orchestration

### Overview

The three layers are designed to work together as a **graduated filtering pipeline**, where each layer builds on the previous one:

1. **Layer 1 (Heuristics)** runs first on all images (fast, CPU-only)
2. **Layer 2 (ImageReward)** runs only on images that passed Layer 1 (GPU-accelerated)
3. **Layer 3 (SigLIP)** runs only on images that passed Layer 1+2 (GPU-accelerated, reference-based)

### Orchestration Logic

```python
def critique_image_graduated(
    image_bytes: bytes,
    prompt: str,
    rubric: CritiqueRubric,
    anchor_image_bytes: Optional[bytes] = None,
    style_reference_bytes: Optional[bytes] = None,
    gpu_available: bool = True
) -> CritiqueResult:
    """Run graduated filtering critique on image.

    Args:
        image_bytes: Generated image (PNG/JPEG bytes)
        prompt: Text prompt used to generate image
        rubric: Quality thresholds for pass/fail
        anchor_image_bytes: NPC anchor image for identity match (optional)
        style_reference_bytes: Campaign style reference (optional)
        gpu_available: Whether GPU is available for Layers 2-3

    Returns:
        CritiqueResult aggregated across all applicable layers

    Raises:
        ValueError: If image fails any layer
    """
    # Layer 1: Heuristics (always runs, CPU-only)
    heuristics_critic = create_image_critic("heuristics", rubric=rubric)
    layer1_result = heuristics_critic.critique(
        image_bytes,
        rubric,
        anchor_image_bytes=anchor_image_bytes,
        style_reference_bytes=None  # Layer 1 doesn't check style
    )

    if not layer1_result.passed:
        # Early rejection: failed heuristics (most common case)
        return layer1_result

    # Layer 2: ImageReward (only if GPU available and Layer 1 passed)
    if not gpu_available:
        # CPU-only mode: return Layer 1 result
        return layer1_result

    imagereward_critic = create_image_critic("imagereward", device="cuda", precision="fp16", rubric=rubric)
    layer2_result = imagereward_critic.critique(
        image_bytes,
        rubric,
        prompt=prompt
    )

    if not layer2_result.passed:
        # Rejection: failed semantic alignment
        return _merge_critique_results([layer1_result, layer2_result])

    # Layer 3: SigLIP (only if references provided and Layer 1+2 passed)
    if anchor_image_bytes is None and style_reference_bytes is None:
        # No references to compare: return Layer 1+2 result
        return _merge_critique_results([layer1_result, layer2_result])

    siglip_critic = create_image_critic("siglip", device="cuda", precision="fp16", rubric=rubric)
    layer3_result = siglip_critic.critique(
        image_bytes,
        rubric,
        anchor_image_bytes=anchor_image_bytes,
        style_reference_bytes=style_reference_bytes
    )

    # Return merged result from all 3 layers
    return _merge_critique_results([layer1_result, layer2_result, layer3_result])


def _merge_critique_results(results: List[CritiqueResult]) -> CritiqueResult:
    """Merge multiple CritiqueResults into a single aggregate result.

    Args:
        results: List of CritiqueResults from different layers

    Returns:
        CritiqueResult with merged dimensions and aggregate scores
    """
    # Collect all dimensions (deduplicate by dimension type, keep best score)
    dimension_map = {}
    for result in results:
        for dim in result.dimensions:
            if dim.dimension not in dimension_map or dim.score > dimension_map[dim.dimension].score:
                dimension_map[dim.dimension] = dim

    # Sort dimensions by type (deterministic ordering)
    merged_dimensions = sorted(dimension_map.values(), key=lambda d: d.dimension.value)

    # Aggregate overall score (weighted average)
    overall_score = sum(d.score for d in merged_dimensions) / len(merged_dimensions)

    # Determine worst severity
    severity_order = [SeverityLevel.ACCEPTABLE, SeverityLevel.MINOR, SeverityLevel.MAJOR, SeverityLevel.CRITICAL]
    overall_severity = max((d.severity for d in merged_dimensions), key=lambda s: severity_order.index(s))

    # Determine pass/fail (all dimensions must pass)
    passed = all(d.severity == SeverityLevel.ACCEPTABLE for d in merged_dimensions)

    # Rejection reason (from worst-severity dimension)
    if not passed:
        worst_dim = max(merged_dimensions, key=lambda d: severity_order.index(d.severity))
        rejection_reason = f"{worst_dim.dimension.value}: {worst_dim.reason}"
    else:
        rejection_reason = None

    return CritiqueResult(
        passed=passed,
        overall_severity=overall_severity,
        dimensions=merged_dimensions,
        overall_score=overall_score,
        rejection_reason=rejection_reason,
        critique_method="graduated_filtering"
    )
```

### Performance Optimization

**Early Rejection Strategy:**
- 60-70% of bad images fail Layer 1 (heuristics) and never reach GPU models
- Saves ~200 ms per rejected image (avoids GPU inference)
- Reduces VRAM pressure (fewer images loaded into GPU memory)

**Lazy Model Loading:**
- Models are loaded only when first needed (lazy initialization)
- Models can be unloaded after critique to free VRAM
- Prep pipeline can orchestrate sequential loading/unloading

**Hardware Tiers:**
- **Tier 1-2 (GPU, ≥2 GB VRAM)**: All 3 layers active → F1 0.85-0.90
- **Tier 3 (GPU, 1-2 GB VRAM)**: Layers 1+2 only (skip SigLIP) → F1 0.80-0.85
- **Tier 4-5 (CPU-only)**: Layer 1 only (heuristics) → F1 0.60-0.65

---

## Prep Pipeline Integration

### Integration Points

The image critique system integrates into the prep pipeline at the **image generation stage**, validating each generated image before storing it in the asset manifest.

### Prep Pipeline Flow (with Critique)

```python
# From prep_pipeline.py (aidm/core/prep_pipeline.py)

class PrepPipeline:
    def run(self) -> PrepPipelineResult:
        """Run prep pipeline with image critique validation."""
        for model_config in self.config.model_sequence:
            # Load model
            self._load_model(model_config)

            # Generate assets
            for asset_spec in self._get_asset_specs(model_config):
                # Generate asset (e.g., NPC portrait)
                asset_bytes = self._generate_asset(model_config, asset_spec)

                # CRITIQUE INTEGRATION POINT
                if model_config.model_type == "image":
                    critique_result = self._critique_image(
                        image_bytes=asset_bytes,
                        prompt=asset_spec.prompt,
                        asset_spec=asset_spec
                    )

                    if not critique_result.passed:
                        # Handle failure (see Regeneration Strategy)
                        asset_bytes = self._handle_critique_failure(
                            critique_result,
                            model_config,
                            asset_spec
                        )

                # Store validated asset
                self._store_asset(asset_bytes, asset_spec, critique_result)

            # Unload model
            self._unload_model(model_config)

        return self._build_result()
```

### Critique Call Signature

```python
def _critique_image(
    self,
    image_bytes: bytes,
    prompt: str,
    asset_spec: AssetSpec
) -> CritiqueResult:
    """Run graduated filtering critique on generated image.

    Args:
        image_bytes: Generated image (PNG/JPEG bytes)
        prompt: Text prompt used to generate image
        asset_spec: Asset specification with metadata (anchor, style reference)

    Returns:
        CritiqueResult from graduated filtering
    """
    # Determine if GPU available
    gpu_available = torch.cuda.is_available()

    # Extract references from asset_spec
    anchor_image_bytes = asset_spec.anchor_image if hasattr(asset_spec, 'anchor_image') else None
    style_reference_bytes = self.campaign_style_reference  # From CampaignDescriptor

    # Run graduated filtering
    return critique_image_graduated(
        image_bytes=image_bytes,
        prompt=prompt,
        rubric=self.config.critique_rubric,  # From PrepPipelineConfig
        anchor_image_bytes=anchor_image_bytes,
        style_reference_bytes=style_reference_bytes,
        gpu_available=gpu_available
    )
```

### Regeneration Strategy (Bounded Retry Policy)

Per R1 recommendations and existing `RegenerationAttempt` schema:

**Bounded Retry Policy:**
1. **Max Attempts**: 4 total (1 original + 3 retries)
2. **Parameter Adjustments**: Increase CFG scale, sampling steps; decrease creativity
3. **Backoff Strategy**: Progressively stronger guidance on each retry

```python
def _handle_critique_failure(
    self,
    critique_result: CritiqueResult,
    model_config: ModelConfig,
    asset_spec: AssetSpec
) -> bytes:
    """Handle critique failure with bounded regeneration.

    Args:
        critique_result: Failed critique result
        model_config: Current model configuration
        asset_spec: Asset specification with generation parameters

    Returns:
        Validated image bytes (or raises if all retries fail)

    Raises:
        CritiqueFailureError: If all 4 attempts fail critique
    """
    max_attempts = 4
    attempt = 1
    regeneration_log = []

    # Record first attempt failure
    regeneration_log.append(RegenerationAttempt(
        attempt_number=attempt,
        cfg_scale=asset_spec.cfg_scale,
        sampling_steps=asset_spec.sampling_steps,
        creativity=asset_spec.creativity,
        critique_result=critique_result,
        generation_time_ms=None  # Not tracked for first attempt
    ))

    # Retry up to 3 times (attempts 2, 3, 4)
    while attempt < max_attempts:
        attempt += 1

        # Adjust generation parameters (backoff strategy)
        adjusted_cfg_scale = asset_spec.cfg_scale + (attempt - 1) * 1.5  # 7.5 → 9.0 → 10.5 → 12.0
        adjusted_steps = asset_spec.sampling_steps + (attempt - 1) * 10   # 50 → 60 → 70 → 80
        adjusted_creativity = asset_spec.creativity - (attempt - 1) * 0.15  # 0.8 → 0.65 → 0.50 → 0.35
        negative_prompt_addon = self._get_negative_prompt_for_dimension(critique_result.rejection_reason)

        # Regenerate with adjusted parameters
        start_time = time.time()
        regenerated_bytes = self._generate_asset(
            model_config,
            asset_spec,
            cfg_scale=adjusted_cfg_scale,
            sampling_steps=adjusted_steps,
            creativity=adjusted_creativity,
            negative_prompt_addon=negative_prompt_addon
        )
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Re-critique regenerated image
        retry_critique_result = self._critique_image(
            image_bytes=regenerated_bytes,
            prompt=asset_spec.prompt,
            asset_spec=asset_spec
        )

        # Record regeneration attempt
        regeneration_log.append(RegenerationAttempt(
            attempt_number=attempt,
            cfg_scale=adjusted_cfg_scale,
            sampling_steps=adjusted_steps,
            creativity=adjusted_creativity,
            negative_prompt=negative_prompt_addon,
            critique_result=retry_critique_result,
            generation_time_ms=generation_time_ms
        ))

        if retry_critique_result.passed:
            # Success: return validated image
            self._log_regeneration_success(asset_spec, regeneration_log)
            return regenerated_bytes

    # All retries failed: raise error
    self._log_regeneration_failure(asset_spec, regeneration_log)
    raise CritiqueFailureError(
        f"Asset {asset_spec.asset_id} failed critique after {max_attempts} attempts",
        regeneration_log=regeneration_log
    )


def _get_negative_prompt_for_dimension(self, rejection_reason: str) -> str:
    """Get negative prompt addon based on critique failure dimension.

    Args:
        rejection_reason: Rejection reason from CritiqueResult

    Returns:
        Negative prompt addon to avoid specific failure mode
    """
    # Map dimension failures to negative prompt additions
    if "artifacting" in rejection_reason.lower():
        return "malformed hands, extra fingers, asymmetric face, anatomical errors, artifacts"
    elif "readability" in rejection_reason.lower():
        return "blurry, out of focus, low contrast, muddy colors"
    elif "composition" in rejection_reason.lower():
        return "off-center, cropped face, bad framing, excessive headroom"
    elif "style" in rejection_reason.lower():
        return "inconsistent style, wrong genre, mismatched aesthetic"
    else:
        return "low quality, bad anatomy, poorly composed"
```

### Asset Storage with Critique Metadata

```python
def _store_asset(
    self,
    asset_bytes: bytes,
    asset_spec: AssetSpec,
    critique_result: CritiqueResult
) -> None:
    """Store validated asset with critique metadata.

    Args:
        asset_bytes: Validated asset bytes
        asset_spec: Asset specification
        critique_result: Passing critique result
    """
    # Compute SHA256 hash
    content_hash = hashlib.sha256(asset_bytes).hexdigest()

    # Determine file path (deterministic)
    asset_path = self.artifact_dir / asset_spec.asset_type / f"{asset_spec.asset_id}.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)

    # Write asset to disk
    asset_path.write_bytes(asset_bytes)

    # Create GeneratedAsset record
    asset = GeneratedAsset(
        asset_id=asset_spec.asset_id,
        asset_type=asset_spec.asset_type,
        file_path=str(asset_path.relative_to(self.artifact_dir)),
        content_hash=content_hash,
        generation_timestamp=datetime.now(timezone.utc).isoformat(),
        model_type=asset_spec.model_type,
        model_name=asset_spec.model_name,
        prompt=asset_spec.prompt,
        critique_result=critique_result.to_dict()  # Embed critique metadata
    )

    # Add to manifest
    self.manifest.add_asset(asset)
```

---

## Schema Extensions

### PrepPipelineConfig Extensions

```python
# In aidm/schemas/prep_pipeline.py

@dataclass
class PrepPipelineConfig:
    """Prep pipeline configuration (EXTENDED for critique)."""

    campaign_id: str
    model_sequence: List[ModelConfig]
    artifact_dir: Path

    # NEW: Critique configuration
    critique_rubric: CritiqueRubric = field(default_factory=lambda: DEFAULT_CRITIQUE_RUBRIC)
    enable_graduated_filtering: bool = True  # If False, use heuristics only
    max_regeneration_attempts: int = 4

    # NEW: Style reference for campaign-wide style adherence
    campaign_style_reference_path: Optional[Path] = None
```

### AssetSpec Extensions

```python
# In aidm/schemas/prep_pipeline.py (or new asset_spec.py)

@dataclass
class AssetSpec:
    """Asset generation specification (EXTENDED for critique)."""

    asset_id: str
    asset_type: str  # "npc_portrait", "scene_background", etc.
    model_type: str
    model_name: str
    prompt: str

    # Generation parameters
    cfg_scale: float = 7.5
    sampling_steps: int = 50
    creativity: float = 0.8
    negative_prompt: str = ""

    # NEW: Critique-related parameters
    anchor_image_path: Optional[Path] = None  # For identity match (NPC portrait regeneration)
```

### GeneratedAsset Extensions

```python
# In aidm/schemas/prep_pipeline.py

@dataclass
class GeneratedAsset:
    """Generated asset record (EXTENDED for critique metadata)."""

    asset_id: str
    asset_type: str
    file_path: str
    content_hash: str
    generation_timestamp: str
    model_type: str
    model_name: str
    prompt: str

    # NEW: Critique metadata
    critique_result: Optional[Dict[str, Any]] = None  # CritiqueResult.to_dict()
    regeneration_attempts: int = 1  # How many attempts before passing
```

---

## Dependencies Summary

### All Layers Combined

```toml
# pyproject.toml additions for image critique

[project.optional-dependencies]
image-critique = [
    # Layer 1 (Heuristics - CPU-only)
    "opencv-python>=4.8.0",
    "pillow>=10.0.0",
    "numpy>=1.24.0",
    "imagehash>=4.3.0",
    "pyiqa>=0.1.12",

    # Layer 2 (ImageReward - GPU-accelerated)
    "image-reward>=1.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0",

    # Layer 3 (SigLIP - GPU-accelerated)
    "open-clip-torch>=2.24.0",
]
```

### Installation Tiers

```bash
# Tier 1-2 (GPU, full stack): All 3 layers
pip install -e ".[image-critique]"

# Tier 3 (GPU, limited VRAM): Layers 1+2 only (skip SigLIP)
pip install opencv-python pillow numpy imagehash pyiqa image-reward torch torchvision

# Tier 4-5 (CPU-only): Layer 1 only (heuristics)
pip install opencv-python pillow numpy imagehash pyiqa
```

---

## Testing Strategy (Deferred to M3)

### Test Coverage Plan

1. **Unit Tests (Tier-1)**: Each adapter independently
   - HeuristicsImageCritic: Test each heuristic dimension
   - ImageRewardCritiqueAdapter: Mock ImageReward model, test scoring logic
   - SigLIPCritiqueAdapter: Mock SigLIP model, test similarity computation

2. **Integration Tests (Tier-2)**: Graduated filtering orchestration
   - Test early rejection (Layer 1 fails, Layers 2-3 skipped)
   - Test pass-through (Layer 1 passes, Layer 2 runs)
   - Test reference-based activation (Layer 3 only runs if references provided)

3. **Prep Pipeline Tests (Tier-2)**: End-to-end with critique
   - Test successful generation (all images pass critique)
   - Test regeneration (image fails, retries with adjusted parameters)
   - Test exhaustion (all 4 attempts fail, raise error)

4. **Performance Tests (Tier-3)**: Latency benchmarks
   - Measure Layer 1 latency (CPU): <100 ms target
   - Measure Layer 2 latency (GPU): ~100 ms target
   - Measure Layer 3 latency (GPU): ~100 ms target

### Test Dataset

Per [R1_IMAGE_QUALITY_DIMENSIONS.md](../R1_IMAGE_QUALITY_DIMENSIONS.md):
- **Positive Set**: 100+ "good" AIDM-style portraits (readable, anatomically correct, well-composed)
- **Negative Set**: 100+ "bad" portraits (blurry, malformed hands, poor composition)
- **Ground Truth Labels**: Human-annotated binary labels (pass/fail per dimension)

**Test dataset creation deferred to M3.**

---

## Acceptance Criteria (For M3 Implementation)

Per WO-M3-IMAGE-CRITIQUE-01:

1. ✅ **Design Documentation Complete**
   - [x] HeuristicsImageCritic design (Layer 1 CPU)
   - [x] ImageRewardCritiqueAdapter design (Layer 2 GPU)
   - [x] SigLIPCritiqueAdapter design (Layer 3 GPU)
   - [x] Graduated filtering orchestration logic
   - [x] Prep pipeline integration points
   - [x] Regeneration strategy (bounded retry policy)

2. ⏳ **Implementation** (DEFERRED to M3 execution)
   - [ ] Implement HeuristicsImageCritic adapter
   - [ ] Implement ImageRewardCritiqueAdapter adapter
   - [ ] Implement SigLIPCritiqueAdapter adapter
   - [ ] Integrate into prep pipeline (aidm/core/prep_pipeline.py)
   - [ ] Add critique configuration to PrepPipelineConfig schema

3. ⏳ **Testing** (DEFERRED to M3 execution)
   - [ ] Write unit tests for each adapter
   - [ ] Write integration tests for graduated filtering
   - [ ] Write prep pipeline integration tests
   - [ ] Create test dataset (100+ positive, 100+ negative examples)

4. ⏳ **Validation** (DEFERRED to M3 execution)
   - [ ] Benchmark F1 scores (0.60-0.65 Layer 1, 0.80-0.85 Layer 1+2, 0.85-0.90 Layer 1+2+3)
   - [ ] Benchmark latency (<100 ms Layer 1, ~100 ms Layers 2-3)
   - [ ] Validate regeneration strategy (bounded retry works correctly)

---

## Open Questions (For M3 Execution)

1. **Heuristic Threshold Calibration**: What are the optimal thresholds for Laplacian variance, contrast ratio, BRISQUE, etc.?
   - **Resolution**: Calibrate using test dataset in M3 (requires human-annotated examples)

2. **Negative Prompt Strategy**: How effective are negative prompt additions for regeneration?
   - **Resolution**: A/B test with and without negative prompt additions in M3

3. **ImageReward Score Normalization**: ImageReward returns [-10, 10] range; how to map to [0, 1]?
   - **Resolution**: Empirical calibration using test dataset (measure actual score distribution)

4. **SigLIP Similarity Thresholds**: What cosine similarity threshold constitutes "identity match" vs "different subject"?
   - **Resolution**: Empirical calibration using NPC portrait regeneration examples

5. **GPU Memory Management**: How to handle VRAM exhaustion when loading multiple models?
   - **Resolution**: Sequential loading/unloading in prep pipeline (already implemented in prep_pipeline.py)

---

## References

- [R1 Technology Stack Validation](../pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md) (Section 2: Image Critique)
- [R1 Image Quality Dimensions](../R1_IMAGE_QUALITY_DIMENSIONS.md) (5 dimensions taxonomy)
- [R0 Image Critique Feasibility](../research/R0_IMAGE_CRITIQUE_FEASIBILITY.md) (R1 revision appended)
- [Existing Schema: image_critique.py](../../aidm/schemas/image_critique.py) (337 lines, complete multi-dimensional rubric)
- [Existing Adapter: image_critique_adapter.py](../../aidm/core/image_critique_adapter.py) (226 lines, protocol + stub)
- [Existing Tests: test_image_critique.py](../../tests/test_image_critique.py) (619 lines, comprehensive coverage)
- [Prep Pipeline Implementation](../../aidm/core/prep_pipeline.py) (549 lines, sequential model loading)
- [Prep Pipeline Schemas](../../aidm/schemas/prep_pipeline.py) (394 lines, CampaignDescriptor, PrepPipelineConfig, PrepAssetManifest)

---

**END OF DESIGN DOCUMENT**

**Status:** Design complete, implementation deferred to M3 execution phase
**Dependencies:** image-reward>=1.0, open-clip-torch>=2.24, pyiqa>=0.1.12, opencv-python>=4.8.0
**Next Phase:** M3 execution (implement adapters, integrate into prep pipeline, validate with test dataset)
