# WO-M3-IMAGE-CRITIQUE-01: Image Critique Model Integration Documentation
**Agent:** Sonnet-B
**Date:** 2026-02-11
**Status:** COMPLETE
**Work Order Type:** Design Documentation (Implementation Deferred)

---

## Executive Summary

WO-M3-IMAGE-CRITIQUE-01 requested design documentation for image critique model integration into the prep pipeline. After investigation, I discovered that:

1. **Existing Infrastructure**: Complete schema layer, adapter protocol, and stub implementation already exist ([aidm/schemas/image_critique.py](../aidm/schemas/image_critique.py), [aidm/core/image_critique_adapter.py](../aidm/core/image_critique_adapter.py), 619 lines of tests)
2. **Outdated Model Selections**: Work order mentioned "Spark vision" and "CLIP", but R1 Technology Stack Validation supersedes these with ImageReward + SigLIP
3. **User Directive**: Create design documentation only (Option 1), matching current M3 design phase

**Deliverable**: [docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md](../docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md)

This design document specifies three image critique adapters following R1's graduated three-layer filtering approach:
- **Layer 1 (HeuristicsImageCritic)**: CPU-only heuristics, <100ms latency, F1 0.60-0.65
- **Layer 2 (ImageRewardCritiqueAdapter)**: GPU-accelerated text-image alignment, ~100ms latency, F1 0.80-0.85 (combined with Layer 1)
- **Layer 3 (SigLIPCritiqueAdapter)**: GPU-accelerated reference-based comparison, ~100ms latency, F1 0.85-0.90 (all layers combined)

---

## Work Order Analysis

### Original Request (Initial Interpretation)

The work order initially appeared to request:
- Document Spark vision model integration
- Design SparkCritiqueAdapter and CLIPCritiqueAdapter
- Document prep pipeline integration

### Findings (After Investigation)

**Existing Infrastructure (Pre-M3 Contracts)**:
- Complete schema layer: CritiqueResult, CritiqueRubric, CritiqueDimension, RegenerationAttempt
- Adapter protocol: ImageCritiqueAdapter (runtime-checkable)
- Stub implementation: StubImageCritic (configurable pass/fail)
- Comprehensive tests: 619 lines of Tier-1 and Tier-2 tests (all passing)

**Outdated Model Selections**:
- Work order mentioned "Spark vision" (text-to-vision LLM) and "CLIP" (ViT-B/32)
- R1 Technology Stack Validation (Section 2) supersedes these with:
  - **ImageReward** (THUDM, NeurIPS 2023): Beats CLIP by 40% on text-image alignment
  - **SigLIP** (Google 2024-2025): CLIP successor with better calibration
  - **Heuristics** (OpenCV-based): CPU-only baseline for graduated filtering

**User Directive (Option 1)**:
- Create design documentation only (no implementation)
- HeuristicsImageCritic as separate standalone adapter (Option A)
- Dependencies and implementation deferred to M3 execution phase

---

## Deliverable: Design Document

**Location**: [docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md](../docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md)

**Document Structure**:
1. Executive Summary (graduated filtering overview)
2. Background (existing infrastructure, R1 model selections)
3. Layer 1: HeuristicsImageCritic (CPU-only, OpenCV-based)
4. Layer 2: ImageRewardCritiqueAdapter (GPU, text-image alignment)
5. Layer 3: SigLIPCritiqueAdapter (GPU, reference-based comparison)
6. Graduated Filtering Orchestration (early rejection strategy)
7. Prep Pipeline Integration (critique call points, regeneration strategy)
8. Schema Extensions (PrepPipelineConfig, AssetSpec, GeneratedAsset)
9. Dependencies Summary (pip install tiers for different hardware)
10. Testing Strategy (deferred to M3)
11. Acceptance Criteria (implementation, testing, validation deferred)
12. Open Questions (threshold calibration, negative prompt strategy)
13. References (R1 reports, existing code)

---

## Layer 1: HeuristicsImageCritic (CPU)

### Purpose
Fast, CPU-only quality checks that filter obvious failures before invoking GPU models. Provides baseline quality assurance even on systems without GPU.

### Quality Dimensions Covered
- **DIM-01 (Readability)**: Laplacian variance (edge sharpness), contrast ratio
- **DIM-02 (Composition)**: Center-of-mass analysis, bounding box area ratio
- **DIM-03 (Artifacting)**: BRISQUE score (perceptual quality)
- **DIM-05 (Identity Match)**: Perceptual hash (pHash) similarity to anchor

### Architecture
```python
class HeuristicsImageCritic:
    def __init__(self, rubric: Optional[CritiqueRubric] = None):
        self.rubric = rubric or DEFAULT_CRITIQUE_RUBRIC
        self.laplacian_threshold = 100.0
        self.contrast_threshold = 3.0
        self.brisque_threshold = 40.0

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        # Implementation deferred to M3
        pass
```

### Dependencies
- opencv-python>=4.8.0
- pillow>=10.0.0
- numpy>=1.24.0
- imagehash>=4.3.0
- pyiqa>=0.1.12

### Performance Characteristics
- **Latency**: <100 ms (CPU)
- **Memory**: <200 MB
- **VRAM**: 0 GB
- **F1 Score**: 0.60-0.65

---

## Layer 2: ImageRewardCritiqueAdapter (GPU)

### Purpose
Text-image alignment scoring using ImageReward model (THUDM, NeurIPS 2023). Validates that generated images match the text prompt semantically. Provides 40% better alignment scoring than CLIP.

### Quality Dimensions Covered
- **DIM-04 (Style Adherence)**: Text-image alignment (semantic style matching)
- **DIM-03 (Artifacting)**: Anomaly detection (supplementary)

### Architecture
```python
class ImageRewardCritiqueAdapter:
    def __init__(
        self,
        model_path: str = "THUDM/ImageReward",
        device: str = "cuda",
        precision: str = "fp16",
        rubric: Optional[CritiqueRubric] = None
    ):
        self.model_path = model_path
        self.device = device
        self.precision = precision
        self.model = None  # Lazy-loaded

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        prompt: Optional[str] = None,
        **kwargs
    ) -> CritiqueResult:
        # Implementation deferred to M3
        pass
```

### Dependencies
- image-reward>=1.0
- torch>=2.0.0
- torchvision>=0.15.0
- pillow>=10.0.0

### Performance Characteristics
- **Latency**: ~100 ms (GPU), ~500 ms (CPU fallback)
- **Memory**: ~1.0 GB VRAM (FP16), ~2.0 GB VRAM (FP32)
- **Model Size**: ~1.0 GB (FP16)
- **F1 Score**: 0.80-0.85 (Layer 1 + Layer 2 combined)

---

## Layer 3: SigLIPCritiqueAdapter (GPU)

### Purpose
Reference-based image comparison using SigLIP (Google 2024-2025, CLIP successor). Validates that generated images match reference images (anchor portraits for identity, style references for campaign consistency). Better calibration than CLIP for similarity scoring.

### Quality Dimensions Covered
- **DIM-05 (Identity Match)**: Image-image similarity (anchor portrait matching)
- **DIM-04 (Style Adherence)**: Style reference comparison (campaign consistency)

### Architecture
```python
class SigLIPCritiqueAdapter:
    def __init__(
        self,
        model_name: str = "hf-hub:timm/ViT-SO400M-14-SigLIP-384",
        device: str = "cuda",
        precision: str = "fp16",
        rubric: Optional[CritiqueRubric] = None
    ):
        self.model_name = model_name
        self.device = device
        self.precision = precision
        self.model = None  # Lazy-loaded

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        # Implementation deferred to M3
        pass
```

### Dependencies
- open-clip-torch>=2.24.0
- torch>=2.0.0
- torchvision>=0.15.0
- pillow>=10.0.0

### Performance Characteristics
- **Latency**: ~100 ms (GPU), ~400 ms (CPU fallback)
- **Memory**: ~0.6 GB VRAM (FP16), ~1.2 GB VRAM (FP32)
- **Model Size**: ~0.6 GB (FP16)
- **F1 Score**: 0.85-0.90 (all layers combined)

---

## Graduated Filtering Orchestration

### Overview
The three layers work together as a **graduated filtering pipeline**, where each layer builds on the previous one:

1. **Layer 1 (Heuristics)** runs first on all images (fast, CPU-only)
2. **Layer 2 (ImageReward)** runs only on images that passed Layer 1 (GPU-accelerated)
3. **Layer 3 (SigLIP)** runs only on images that passed Layer 1+2 (GPU-accelerated, reference-based)

### Early Rejection Strategy
- **60-70% of bad images fail Layer 1** (heuristics) and never reach GPU models
- Saves ~200 ms per rejected image (avoids GPU inference)
- Reduces VRAM pressure (fewer images loaded into GPU memory)

### Hardware Tiers
- **Tier 1-2 (GPU, ≥2 GB VRAM)**: All 3 layers active → F1 0.85-0.90
- **Tier 3 (GPU, 1-2 GB VRAM)**: Layers 1+2 only (skip SigLIP) → F1 0.80-0.85
- **Tier 4-5 (CPU-only)**: Layer 1 only (heuristics) → F1 0.60-0.65

### Orchestration Function
```python
def critique_image_graduated(
    image_bytes: bytes,
    prompt: str,
    rubric: CritiqueRubric,
    anchor_image_bytes: Optional[bytes] = None,
    style_reference_bytes: Optional[bytes] = None,
    gpu_available: bool = True
) -> CritiqueResult:
    # Layer 1: Always runs (CPU-only)
    layer1_result = heuristics_critic.critique(...)
    if not layer1_result.passed:
        return layer1_result  # Early rejection

    # Layer 2: Only if GPU available
    if gpu_available:
        layer2_result = imagereward_critic.critique(...)
        if not layer2_result.passed:
            return merge_results([layer1_result, layer2_result])

    # Layer 3: Only if references provided
    if anchor_image_bytes or style_reference_bytes:
        layer3_result = siglip_critic.critique(...)
        return merge_results([layer1_result, layer2_result, layer3_result])

    return merge_results([layer1_result, layer2_result])
```

---

## Prep Pipeline Integration

### Integration Points
The image critique system integrates into the prep pipeline at the **image generation stage**, validating each generated image before storing it in the asset manifest.

### Critique Call Point
```python
# From prep_pipeline.py (aidm/core/prep_pipeline.py)

class PrepPipeline:
    def run(self) -> PrepPipelineResult:
        for model_config in self.config.model_sequence:
            self._load_model(model_config)

            for asset_spec in self._get_asset_specs(model_config):
                asset_bytes = self._generate_asset(model_config, asset_spec)

                # CRITIQUE INTEGRATION POINT
                if model_config.model_type == "image":
                    critique_result = self._critique_image(
                        image_bytes=asset_bytes,
                        prompt=asset_spec.prompt,
                        asset_spec=asset_spec
                    )

                    if not critique_result.passed:
                        asset_bytes = self._handle_critique_failure(
                            critique_result,
                            model_config,
                            asset_spec
                        )

                self._store_asset(asset_bytes, asset_spec, critique_result)

            self._unload_model(model_config)
```

### Regeneration Strategy (Bounded Retry Policy)
Per R1 recommendations and existing `RegenerationAttempt` schema:

**Bounded Retry Policy**:
1. **Max Attempts**: 4 total (1 original + 3 retries)
2. **Parameter Adjustments**: Increase CFG scale, sampling steps; decrease creativity
3. **Backoff Strategy**: Progressively stronger guidance on each retry
4. **Negative Prompt Additions**: Add dimension-specific negative prompts

**Parameter Progression**:
- **CFG Scale**: 7.5 → 9.0 → 10.5 → 12.0
- **Sampling Steps**: 50 → 60 → 70 → 80
- **Creativity**: 0.8 → 0.65 → 0.50 → 0.35
- **Negative Prompt**: Dimension-specific additions (e.g., "malformed hands, extra fingers" for artifacting failures)

### Failure Handling
```python
def _handle_critique_failure(
    self,
    critique_result: CritiqueResult,
    model_config: ModelConfig,
    asset_spec: AssetSpec
) -> bytes:
    max_attempts = 4
    regeneration_log = []

    for attempt in range(2, max_attempts + 1):
        # Adjust parameters (backoff strategy)
        adjusted_cfg_scale = asset_spec.cfg_scale + (attempt - 1) * 1.5
        adjusted_steps = asset_spec.sampling_steps + (attempt - 1) * 10
        adjusted_creativity = asset_spec.creativity - (attempt - 1) * 0.15
        negative_prompt_addon = self._get_negative_prompt_for_dimension(
            critique_result.rejection_reason
        )

        # Regenerate and re-critique
        regenerated_bytes = self._generate_asset(...)
        retry_critique_result = self._critique_image(...)

        regeneration_log.append(RegenerationAttempt(...))

        if retry_critique_result.passed:
            return regenerated_bytes

    # All retries failed
    raise CritiqueFailureError(...)
```

---

## Schema Extensions

### PrepPipelineConfig Extensions
```python
@dataclass
class PrepPipelineConfig:
    campaign_id: str
    model_sequence: List[ModelConfig]
    artifact_dir: Path

    # NEW: Critique configuration
    critique_rubric: CritiqueRubric = field(default_factory=lambda: DEFAULT_CRITIQUE_RUBRIC)
    enable_graduated_filtering: bool = True
    max_regeneration_attempts: int = 4
    campaign_style_reference_path: Optional[Path] = None
```

### AssetSpec Extensions
```python
@dataclass
class AssetSpec:
    asset_id: str
    asset_type: str
    model_type: str
    model_name: str
    prompt: str

    # Generation parameters
    cfg_scale: float = 7.5
    sampling_steps: int = 50
    creativity: float = 0.8
    negative_prompt: str = ""

    # NEW: Critique-related parameters
    anchor_image_path: Optional[Path] = None
```

### GeneratedAsset Extensions
```python
@dataclass
class GeneratedAsset:
    asset_id: str
    asset_type: str
    file_path: str
    content_hash: str
    generation_timestamp: str
    model_type: str
    model_name: str
    prompt: str

    # NEW: Critique metadata
    critique_result: Optional[Dict[str, Any]] = None
    regeneration_attempts: int = 1
```

---

## Dependencies Summary

### Installation Tiers

```bash
# Tier 1-2 (GPU, full stack): All 3 layers
pip install -e ".[image-critique]"

# Tier 3 (GPU, limited VRAM): Layers 1+2 only (skip SigLIP)
pip install opencv-python pillow numpy imagehash pyiqa image-reward torch torchvision

# Tier 4-5 (CPU-only): Layer 1 only (heuristics)
pip install opencv-python pillow numpy imagehash pyiqa
```

### pyproject.toml Addition
```toml
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

---

## Acceptance Criteria Status

Per WO-M3-IMAGE-CRITIQUE-01:

### ✅ Design Documentation Complete
- [x] HeuristicsImageCritic design (Layer 1 CPU)
- [x] ImageRewardCritiqueAdapter design (Layer 2 GPU)
- [x] SigLIPCritiqueAdapter design (Layer 3 GPU)
- [x] Graduated filtering orchestration logic
- [x] Prep pipeline integration points
- [x] Regeneration strategy (bounded retry policy)
- [x] Schema extensions (PrepPipelineConfig, AssetSpec, GeneratedAsset)
- [x] Dependencies summary (installation tiers)
- [x] Testing strategy (deferred to M3)
- [x] References to R1 reports and existing code

### ⏳ Implementation (DEFERRED to M3 Execution)
- [ ] Implement HeuristicsImageCritic adapter
- [ ] Implement ImageRewardCritiqueAdapter adapter
- [ ] Implement SigLIPCritiqueAdapter adapter
- [ ] Integrate into prep pipeline (aidm/core/prep_pipeline.py)
- [ ] Add critique configuration to PrepPipelineConfig schema
- [ ] Create test dataset (100+ positive, 100+ negative examples)
- [ ] Write unit tests for each adapter
- [ ] Write integration tests for graduated filtering
- [ ] Benchmark F1 scores and latency
- [ ] Calibrate heuristic thresholds

---

## Open Questions (For M3 Execution)

1. **Heuristic Threshold Calibration**: What are the optimal thresholds for Laplacian variance, contrast ratio, BRISQUE, etc.?
   - **Resolution Plan**: Calibrate using test dataset in M3 (requires human-annotated examples)

2. **Negative Prompt Strategy**: How effective are negative prompt additions for regeneration?
   - **Resolution Plan**: A/B test with and without negative prompt additions in M3

3. **ImageReward Score Normalization**: ImageReward returns [-10, 10] range; how to map to [0, 1]?
   - **Resolution Plan**: Empirical calibration using test dataset (measure actual score distribution)

4. **SigLIP Similarity Thresholds**: What cosine similarity threshold constitutes "identity match" vs "different subject"?
   - **Resolution Plan**: Empirical calibration using NPC portrait regeneration examples

5. **GPU Memory Management**: How to handle VRAM exhaustion when loading multiple models?
   - **Resolution Plan**: Sequential loading/unloading in prep pipeline (already implemented in prep_pipeline.py)

---

## Files Created

1. **[docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md](../docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md)** (Full design specification, ~900 lines)

---

## Files Referenced

1. **[aidm/schemas/image_critique.py](../aidm/schemas/image_critique.py)** (337 lines) - Existing schema layer
2. **[aidm/core/image_critique_adapter.py](../aidm/core/image_critique_adapter.py)** (226 lines) - Existing adapter protocol
3. **[tests/test_image_critique.py](../tests/test_image_critique.py)** (619 lines) - Existing test coverage
4. **[aidm/core/prep_pipeline.py](../aidm/core/prep_pipeline.py)** (549 lines) - Prep pipeline implementation
5. **[aidm/schemas/prep_pipeline.py](../aidm/schemas/prep_pipeline.py)** (394 lines) - Prep pipeline schemas
6. **[docs/R1_IMAGE_QUALITY_DIMENSIONS.md](../docs/R1_IMAGE_QUALITY_DIMENSIONS.md)** (449 lines) - Quality dimension taxonomy
7. **[pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md](../pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md)** (Section 2) - R1 model selections
8. **[docs/research/R0_IMAGE_CRITIQUE_FEASIBILITY.md](../docs/research/R0_IMAGE_CRITIQUE_FEASIBILITY.md)** - R0 feasibility with R1 revision

---

## Compliance Notes

### Agent Communication Protocol
- **READ-ONLY Mode**: No production code modifications made (design documentation only)
- **No Schema Changes**: Documented schema extensions, but no actual schema modifications
- **No Silent Decisions**: All design choices documented with R1 citations
- **Reporting Line**: PM (Aegis) → Agent D (Governance)

### Hard Constraints Observed
- ❌ NO pipeline implementation without authorization (deferred to M3 execution)
- ❌ NO schema amendments (documented extensions only, no code changes)
- ❌ NO silent decisions (all choices traceable to R1 report)

---

## Next Steps (For M3 Execution)

1. **Implement HeuristicsImageCritic adapter** following design spec
2. **Implement ImageRewardCritiqueAdapter** following design spec
3. **Implement SigLIPCritiqueAdapter** following design spec
4. **Integrate into prep pipeline** (add critique calls to PrepPipeline.run())
5. **Create test dataset** (100+ positive, 100+ negative examples with human labels)
6. **Write comprehensive tests** (unit, integration, performance)
7. **Calibrate thresholds** using test dataset
8. **Benchmark F1 scores** (validate 0.85-0.90 target for all layers combined)
9. **Validate regeneration strategy** (bounded retry works correctly)
10. **Update PROJECT_STATE_DIGEST.md** with implementation completion

---

## Deliverable Summary

**Work Order**: WO-M3-IMAGE-CRITIQUE-01
**Deliverable**: Design documentation for three-layer graduated filtering image critique system
**Status**: ✅ COMPLETE (design phase)
**Implementation Status**: ⏳ DEFERRED to M3 execution
**Location**: [docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md](../docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md)

**Design Quality**:
- Follows R1 Technology Stack Validation (Section 2: Image Critique)
- Integrates with existing infrastructure (schemas, protocol, tests)
- Specifies all three adapters with implementation pseudocode
- Documents graduated filtering orchestration
- Documents prep pipeline integration points
- Documents regeneration strategy (bounded retry policy)
- Provides dependency installation tiers for hardware compatibility

**Ready for M3 Execution**: Yes (design is complete and unambiguous)

---

**Agent:** Sonnet-B
**Date:** 2026-02-11
**Status:** WO-M3-IMAGE-CRITIQUE-01 COMPLETE (design phase)
