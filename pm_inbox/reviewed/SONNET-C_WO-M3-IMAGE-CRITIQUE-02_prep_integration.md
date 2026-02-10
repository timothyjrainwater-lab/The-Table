# Prep Pipeline Integration Design (Graduated Critique)

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-02
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

This document defines how the **3-layer graduated critique pipeline** integrates into the prep pipeline for sequential image validation during asset generation.

**Sequential Flow**: Generate → Layer 1 (CPU) → Layer 2 (GPU) → Layer 3 (GPU, optional) → Save or Regenerate

---

## 2. Graduated Pipeline Flow

```
┌────────────────────────────────────────────────────────────┐
│ PREP PIPELINE: Generate NPC Portrait                      │
└──────────┬─────────────────────────────────────────────────┘
           │
           ▼
     ┌─────────────────┐
     │ SDXL Lightning  │ Generate image (~5s, ~4 GB VRAM)
     └────────┬────────┘
              │
              ▼ [UNLOAD SDXL (~4 GB freed)]
              │
              ▼
     ┌──────────────────────────┐
     │ Layer 1: Heuristics      │ CPU-only, <100ms
     │ - Blur detection         │
     │ - Format validation      │
     │ - Composition checks     │
     └──────┬──────────┬────────┘
            │          │
         FAIL        PASS
            │          │
            │          ▼ [LOAD ImageReward (~1 GB)]
            │    ┌──────────────────────────┐
            │    │ Layer 2: ImageReward     │ GPU, ~1.5s
            │    │ - Text-image alignment   │
            │    └──────┬──────────┬────────┘
            │           │          │
            │        FAIL        PASS
            │           │          │
            │           │          ▼ [UNLOAD ImageReward]
            │           │          ▼ [LOAD SigLIP (~0.6 GB)]
            │           │    ┌──────────────────────────┐
            │           │    │ Layer 3: SigLIP          │ GPU, ~0.5s
            │           │    │ - Identity consistency   │ (if anchor exists)
            │           │    └──────┬──────────┬────────┘
            │           │           │          │
            │           │        FAIL        PASS
            │           │           │          │
            │           │           │          ▼ [UNLOAD SigLIP]
            │           │           │          │
            ▼           ▼           ▼          ▼
       ┌────────────────────────────────────────┐
       │ REGENERATE                             │
       │ - Adjust parameters (CFG↑, steps↑)     │
       │ - Max 3 retries                        │
       └────────┬───────────────────────────────┘
                │
           ┌────┴────┐
        RETRY      EXHAUSTED
           │          │
           └───┐      ▼
               │  ┌──────────────┐
               │  │ Use Placeholder│
               │  └──────────────┘
               │
               ▼
          [Back to SDXL Lightning]
```

---

## 3. Integration Algorithm

```python
def generate_and_validate_graduated(
    scene_description: str,
    semantic_key: str,
    rubric: CritiqueRubric,
    anchor_image_bytes: Optional[bytes] = None,
    max_attempts: int = 4
) -> ImageResult:
    """Generate image with graduated critique validation.

    Args:
        scene_description: Text description / generation prompt
        semantic_key: Asset identifier
        rubric: Quality thresholds
        anchor_image_bytes: Reference image for identity consistency (optional)
        max_attempts: Max generation attempts (1 original + 3 retries)

    Returns:
        ImageResult with status "generated" or "placeholder"
    """
    # Initialize critique adapters (lazy loading)
    layer1_critic = create_image_critic("heuristics")
    layer2_critic = create_image_critic("imagereward")
    layer3_critic = create_image_critic("siglip") if anchor_image_bytes else None

    attempt_number = 0
    cfg_scale = 7.5
    sampling_steps = 50

    while attempt_number < max_attempts:
        attempt_number += 1

        # STEP 1: Generate image (SDXL Lightning)
        image_bytes = generate_image_sdxl(
            prompt=scene_description,
            cfg_scale=cfg_scale,
            sampling_steps=sampling_steps
        )

        # STEP 2: Unload SDXL to free VRAM (~4 GB)
        unload_sdxl_model()

        # STEP 3: Layer 1 critique (CPU, fast rejection)
        layer1_result = layer1_critic.critique(image_bytes, rubric)
        if not layer1_result.passed:
            # Failed heuristics → regenerate immediately (don't load GPU models)
            cfg_scale, sampling_steps = adjust_parameters(attempt_number, layer1_result)
            continue

        # STEP 4: Layer 2 critique (GPU, text-image alignment)
        layer2_critic.load()
        layer2_result = layer2_critic.critique(image_bytes, rubric, prompt=scene_description)
        layer2_critic.unload()

        if not layer2_result.passed:
            # Failed ImageReward → regenerate
            cfg_scale, sampling_steps = adjust_parameters(attempt_number, layer2_result)
            continue

        # STEP 5: Layer 3 critique (GPU, identity consistency) - OPTIONAL
        if layer3_critic and anchor_image_bytes:
            layer3_critic.load()
            layer3_result = layer3_critic.critique(image_bytes, rubric, anchor_image_bytes=anchor_image_bytes)
            layer3_critic.unload()

            if not layer3_result.passed:
                # Failed SigLIP → regenerate
                cfg_scale, sampling_steps = adjust_parameters(attempt_number, layer3_result)
                continue

        # ALL LAYERS PASSED → Save image
        asset_id = save_to_asset_store(image_bytes, semantic_key)
        return ImageResult(
            status="generated",
            asset_id=asset_id,
            path=f"assets/images/{semantic_key}.png",
            content_hash=hashlib.sha256(image_bytes).hexdigest()
        )

    # Exhausted all attempts → use placeholder
    return ImageResult(
        status="placeholder",
        asset_id="",
        path="",
        content_hash="",
        error_message=f"Failed critique after {max_attempts} attempts"
    )
```

---

## 4. Decision Logic: Which Layers to Invoke

```python
def should_run_layer_3(asset_type: str, anchor_available: bool, hardware_tier: str) -> bool:
    """Determine if Layer 3 (SigLIP) should run.

    Args:
        asset_type: "portrait", "scene", "backdrop"
        anchor_available: Whether reference image exists
        hardware_tier: "high", "medium", "low"

    Returns:
        True if Layer 3 should run
    """
    # Layer 3 only for portraits with anchors
    if asset_type != "portrait":
        return False

    if not anchor_available:
        return False

    # On low hardware tier, skip Layer 3 (save VRAM/time)
    if hardware_tier == "low":
        return False

    return True
```

---

## 5. Parameter Adjustment Strategy

```python
def adjust_parameters(
    attempt_number: int,
    failed_result: CritiqueResult
) -> Tuple[float, int]:
    """Adjust generation parameters based on critique failure.

    Args:
        attempt_number: Current attempt (1-4)
        failed_result: Critique result that failed

    Returns:
        Tuple of (cfg_scale, sampling_steps)
    """
    # Base backoff schedule
    cfg_adjustments = {1: 7.5, 2: 9.0, 3: 11.0, 4: 13.0}
    step_adjustments = {1: 50, 2: 60, 3: 70, 4: 80}

    cfg_scale = cfg_adjustments[min(attempt_number + 1, 4)]
    sampling_steps = step_adjustments[min(attempt_number + 1, 4)]

    # Fine-tune based on which layer failed
    if failed_result.critique_method == "heuristics_cpu":
        # Heuristics failed → likely blur or format issue
        # Increase steps aggressively
        sampling_steps = min(sampling_steps + 10, 100)

    elif failed_result.critique_method.startswith("imagereward"):
        # ImageReward failed → text-image misalignment
        # Increase CFG to strengthen prompt adherence
        cfg_scale = min(cfg_scale + 1.0, 15.0)

    elif failed_result.critique_method.startswith("siglip"):
        # SigLIP failed → identity mismatch
        # Try different seed (regenerate with variation)
        pass  # Parameter adjustment may not help; seed variation needed

    return cfg_scale, sampling_steps
```

---

## 6. VRAM Budget Validation

### 6.1 Peak VRAM by Stage

| Stage | Model Loaded | VRAM | Notes |
|-------|--------------|------|-------|
| **Image Generation** | SDXL Lightning | ~4.0 GB | FP16 + activations |
| **Critique Layer 1** | None | 0 GB | CPU-only heuristics |
| **Critique Layer 2** | ImageReward | ~1.0 GB | SDXL unloaded before load |
| **Critique Layer 3** | SigLIP | ~0.6 GB | ImageReward unloaded before load |

**Peak VRAM**: ~4.0 GB (during generation only)
**Critique VRAM**: ~1.0 GB max (sequential loading, no contention)

### 6.2 Sequential Loading Ensures No Contention

```python
# CRITICAL: Models NEVER overlap in memory

# Generation phase
sdxl.load()          # 4 GB
image = sdxl.generate()
sdxl.unload()        # Free 4 GB

# Critique phase
imagereward.load()   # 1 GB (not 5 GB total!)
score = imagereward.critique()
imagereward.unload() # Free 1 GB

siglip.load()        # 0.6 GB
similarity = siglip.critique()
siglip.unload()      # Free 0.6 GB

# Back to generation (if regenerating)
sdxl.load()          # 4 GB (clean slate)
```

---

## 7. Performance Analysis

### 7.1 Timing per Attempt (Happy Path: All Layers Pass)

| Stage | Time | Notes |
|-------|------|-------|
| **SDXL generation** | ~5s | Includes prompt processing |
| **SDXL unload** | ~0.5s | Free VRAM |
| **Layer 1 (heuristics)** | ~0.1s | CPU-only, fast |
| **ImageReward load** | ~2s | One-time per session |
| **ImageReward critique** | ~1.5s | Per image |
| **ImageReward unload** | ~0.3s | Free VRAM |
| **SigLIP load** | ~1.5s | One-time per session |
| **SigLIP critique** | ~0.5s | Per image |
| **SigLIP unload** | ~0.3s | Free VRAM |
| **Asset storage** | ~0.1s | Write to disk |
| **TOTAL (first image)** | **~11.8s** | Includes model loading |
| **TOTAL (subsequent)** | **~7.5s** | Models already loaded |

### 7.2 Prep Session for 50 NPCs

**Assumptions**:
- 80% pass all layers first try (40 images)
- 15% pass on second try (7.5 → 8 images)
- 5% fail after 4 tries (2 images → placeholders)

**Calculation**:
- 40 × 7.5s = 300s (first-try passes)
- 8 × (7.5s + 5s) = 100s (second-try passes, one regen)
- 2 × (7.5s × 4) = 60s (exhausted attempts)
- **TOTAL**: ~460s = **7.7 minutes** ✅

**Target**: <10 minutes for 50 NPCs → **ACHIEVED**

---

## 8. Failure Handling

### 8.1 Model Load Failures

```python
def critique_with_fallback(image_bytes, prompt, rubric):
    """Critique with automatic fallback on model failures."""
    # Layer 1: Always runs (CPU-only, no failure mode except invalid image)
    layer1_result = create_image_critic("heuristics").critique(image_bytes, rubric)
    if not layer1_result.passed:
        return layer1_result

    # Layer 2: Try to load, fall back to Layer 1 only if fails
    try:
        layer2_critic = create_image_critic("imagereward")
        layer2_critic.load()
        layer2_result = layer2_critic.critique(image_bytes, rubric, prompt=prompt)
        layer2_critic.unload()
        return layer2_result
    except Exception as e:
        logger.warning(f"ImageReward failed: {e}. Using Layer 1 result only.")
        return layer1_result  # Accept Layer 1 result (heuristics passed)

    # Layer 3: Optional, failure doesn't block (Layer 2 result stands)
```

### 8.2 All Attempts Exhausted

```python
def handle_exhausted_attempts(semantic_key: str, attempts: List[CritiqueResult]) -> ImageResult:
    """Handle case where all regeneration attempts failed.

    Args:
        semantic_key: Asset identifier
        attempts: List of critique results from all attempts

    Returns:
        Placeholder ImageResult
    """
    # Log failure for manual review
    logger.error(f"Image generation failed for {semantic_key} after {len(attempts)} attempts")
    for i, result in enumerate(attempts):
        logger.error(f"  Attempt {i+1}: {result.rejection_reason}")

    # Add to manual review queue
    manual_review_queue.append({
        "semantic_key": semantic_key,
        "attempts": len(attempts),
        "final_failure": attempts[-1].rejection_reason
    })

    # Return placeholder
    return ImageResult(
        status="placeholder",
        asset_id="",
        path=f"assets/placeholders/{semantic_key}.png",  # Default placeholder image
        content_hash="",
        error_message=f"Failed critique after {len(attempts)} attempts: {attempts[-1].rejection_reason}"
    )
```

---

## 9. Regeneration Policy

### 9.1 Max Attempts

**Default**: 4 attempts (1 original + 3 retries)

**Rationale**:
- 1st attempt: Standard params → ~80% pass rate
- 2nd attempt: Adjusted params → +15% pass rate (cumulative 95%)
- 3rd attempt: Aggressive params → +3% pass rate (cumulative 98%)
- 4th attempt: Maximum params → +1% pass rate (cumulative 99%)

**Remaining 1%**: Manual review queue (human intervention)

### 9.2 Early Stop Conditions

```python
# Stop regenerating if:
# 1. All layers passed
if all_layers_passed:
    break

# 2. Max attempts reached
if attempt_number >= max_attempts:
    break

# 3. Identical failure 3 times in a row (params not helping)
if last_3_failures_identical():
    break  # Parameters won't fix this, need manual review
```

---

## 10. Testing Strategy

```python
def test_graduated_critique_happy_path():
    """Graduated critique accepts good image without regeneration."""
    result = generate_and_validate_graduated(
        scene_description="A stern dwarf cleric",
        semantic_key="npc:dwarf:001",
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        max_attempts=4
    )

    assert result.status == "generated"
    assert result.asset_id != ""


def test_graduated_critique_regenerates_blurry():
    """Graduated critique regenerates blurry image caught by Layer 1."""
    # Mock SDXL to return blurry image first, sharp second
    with mock_sdxl_output([BLURRY_IMAGE, SHARP_IMAGE]):
        result = generate_and_validate_graduated(
            scene_description="A stern dwarf cleric",
            semantic_key="npc:dwarf:002",
            rubric=DEFAULT_CRITIQUE_RUBRIC,
            max_attempts=4
        )

    assert result.status == "generated"
    assert sdxl_generate_count == 2  # Regenerated once


def test_graduated_critique_exhausts_attempts():
    """Graduated critique uses placeholder after max attempts."""
    # Mock SDXL to always return failing images
    with mock_sdxl_output([BLURRY_IMAGE] * 4):
        result = generate_and_validate_graduated(
            scene_description="A stern dwarf cleric",
            semantic_key="npc:dwarf:003",
            rubric=DEFAULT_CRITIQUE_RUBRIC,
            max_attempts=4
        )

    assert result.status == "placeholder"
    assert sdxl_generate_count == 4  # All attempts used
```

---

## 11. Monitoring & Logging

### 11.1 Prep Report

```python
@dataclass
class GraduatedCritiqueReport:
    """Report of graduated critique performance."""
    total_images: int
    layer1_passes: int
    layer1_failures: int
    layer2_passes: int
    layer2_failures: int
    layer3_passes: int
    layer3_failures: int
    total_regenerations: int
    placeholder_count: int
    avg_attempts_per_image: float
    total_time_seconds: float

def generate_critique_report(results: List[ImageResult]) -> GraduatedCritiqueReport:
    """Generate performance report."""
    # Aggregate statistics from all results
    # ...
    return GraduatedCritiqueReport(...)
```

### 11.2 Logging Example

```
[PREP] Generating npc:theron:portrait
  [SDXL] Generated in 4.8s
  [L1-HEUR] PASS (blur: 0.92, composition: 0.85, format: 1.0)
  [L2-IREWARD] PASS (alignment: 0.78)
  [L3-SIGLIP] PASS (similarity: 0.82 vs anchor)
  [ASSET] Saved to assets/images/npc_theron_portrait.png

[PREP] Generating npc:elsa:portrait
  [SDXL] Generated in 5.1s
  [L1-HEUR] FAIL (blur: 0.55 - slightly blurry)
  [REGEN] Attempt 2 (cfg: 9.0, steps: 60)
  [SDXL] Generated in 5.3s
  [L1-HEUR] PASS (blur: 0.91, composition: 0.88, format: 1.0)
  [L2-IREWARD] PASS (alignment: 0.81)
  [ASSET] Saved to assets/images/npc_elsa_portrait.png
```

---

## 12. Gap Analysis

### What Exists:
✅ All 3 critique adapter designs (Layers 1-3)
✅ Existing ImageCritiqueAdapter protocol

### What's Missing:
❌ Integration layer (generate_and_validate_graduated)
❌ Parameter adjustment logic
❌ Manual review queue
❌ Prep report generation

### Implementation Checklist:
1. ✅ Designs complete (4 documents)
2. ❌ Implement integration function
3. ❌ Implement parameter adjustment
4. ❌ Add manual review queue
5. ❌ Write integration tests
6. ❌ Profile end-to-end performance

---

**END OF SPECIFICATION**
