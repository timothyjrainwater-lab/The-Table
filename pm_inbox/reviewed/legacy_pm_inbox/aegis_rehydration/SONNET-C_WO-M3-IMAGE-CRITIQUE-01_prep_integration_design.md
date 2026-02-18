# Prep Pipeline Integration Design for Image Critique

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-01
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

This document defines how image critique integrates into the prep pipeline. It specifies:
- **When** critique occurs in the prep flow
- **How** failures trigger regeneration
- **What** retry limits and fallback strategies exist
- **Where** critique fits in the overall M3 architecture

**Key Constraint**: This design assumes the prep pipeline exists per WO-M3-PREP-01 (Sonnet B). If the actual prep pipeline differs, this integration design must be updated accordingly.

---

## 2. Prep Pipeline Flow (Assumed)

Based on the work order, the prep pipeline is expected to:

```
1. Load campaign data (NPCs, scenes, locations)
2. Generate assets (images, audio, grid data)
3. Validate assets (critique images, check audio quality)
4. Store validated assets in AssetStore
5. Build attribution ledger
```

**Image Critique Integration Point**: Between steps 2 and 4.

---

## 3. Image Generation + Critique Flow

### 3.1 High-Level Flow

```
┌─────────────────────────────────────────┐
│ Prep Pipeline: Generate NPC Portrait   │
└──────────────┬──────────────────────────┘
               │
               ▼
     ┌─────────────────┐
     │ Image Generator │ (SDXL Lightning)
     └────────┬────────┘
              │
              ▼
      [Generated Image Bytes]
              │
              ▼
     ┌──────────────────┐
     │ Image Critique   │ (Spark or CLIP)
     └────────┬─────────┘
              │
        ┌─────┴─────┐
        │           │
     PASS         FAIL
        │           │
        ▼           ▼
   [Save to   [Regenerate]
    AssetStore]    │
        │           └──> Adjust Parameters
        │                (CFG scale ↑, steps ↑, creativity ↓)
        │                     │
        │                     └──> Retry (max 3 attempts)
        │                               │
        │                         ┌─────┴─────┐
        │                         │           │
        │                      PASS         FAIL (all retries)
        │                         │           │
        │                         ▼           ▼
        └────────────────> [Save to    [Use placeholder
                            AssetStore]  or flag for manual review]
```

### 3.2 Detailed Algorithm

```python
def generate_and_validate_image(
    scene_description: str,
    semantic_key: str,
    rubric: CritiqueRubric,
    max_attempts: int = 4  # 1 original + 3 retries
) -> ImageResult:
    """Generate image with automatic quality validation.

    Args:
        scene_description: Text description of scene/NPC
        semantic_key: Asset identifier (e.g., "npc:theron:portrait")
        rubric: Quality thresholds
        max_attempts: Max generation attempts (1 + retries)

    Returns:
        ImageResult with status "generated" if passed, "placeholder" if failed
    """
    attempt_number = 0
    regeneration_attempts = []

    # Initial generation parameters
    cfg_scale = 7.5
    sampling_steps = 50
    creativity = 0.8

    while attempt_number < max_attempts:
        attempt_number += 1

        # 1. Generate image
        image_bytes = generate_image(
            prompt=scene_description,
            cfg_scale=cfg_scale,
            sampling_steps=sampling_steps,
            creativity=creativity
        )

        # 2. Critique image
        critique_result = critique_adapter.critique(
            image_bytes=image_bytes,
            rubric=rubric
        )

        # 3. Record attempt
        regeneration_attempt = RegenerationAttempt(
            attempt_number=attempt_number,
            cfg_scale=cfg_scale,
            sampling_steps=sampling_steps,
            creativity=creativity,
            critique_result=critique_result,
            generation_time_ms=<measured_time>
        )
        regeneration_attempts.append(regeneration_attempt)

        # 4. Check if passed
        if critique_result.passed:
            # SUCCESS: Save image
            asset_id = save_to_asset_store(image_bytes, semantic_key)
            return ImageResult(
                status="generated",
                asset_id=asset_id,
                path=f"assets/images/{semantic_key}.png",
                content_hash=hashlib.sha256(image_bytes).hexdigest()
            )

        # 5. Check if should retry
        if attempt_number >= max_attempts:
            # FAILURE: All attempts exhausted
            return ImageResult(
                status="placeholder",
                asset_id="",
                path="",
                content_hash="",
                error_message=f"Failed critique after {max_attempts} attempts: {critique_result.rejection_reason}"
            )

        # 6. Adjust parameters for next attempt
        cfg_scale, sampling_steps, creativity = adjust_parameters(
            attempt_number=attempt_number,
            previous_critique=critique_result
        )

    # Shouldn't reach here, but handle gracefully
    return ImageResult(
        status="error",
        asset_id="",
        path="",
        content_hash="",
        error_message="Unexpected error in generation loop"
    )
```

---

## 4. Parameter Adjustment Strategy

### 4.1 Backoff Schedule

Each retry adjusts generation parameters to address critique failures:

| Attempt | CFG Scale | Sampling Steps | Creativity | Rationale |
|---------|-----------|----------------|------------|-----------|
| **1** (original) | 7.5 | 50 | 0.8 | Standard settings |
| **2** (retry 1) | 9.0 | 60 | 0.7 | ↑ guidance, ↓ variation |
| **3** (retry 2) | 11.0 | 70 | 0.5 | ↑↑ guidance, ↓↓ variation |
| **4** (retry 3) | 13.0 | 80 | 0.3 | Maximum guidance, minimal variation |

```python
def adjust_parameters(
    attempt_number: int,
    previous_critique: CritiqueResult
) -> Tuple[float, int, float]:
    """Adjust generation parameters based on critique failures.

    Args:
        attempt_number: Which attempt (2, 3, or 4)
        previous_critique: Previous attempt's critique result

    Returns:
        Tuple of (cfg_scale, sampling_steps, creativity)
    """
    # Base adjustments (conservative → strict)
    cfg_adjustments = {1: 7.5, 2: 9.0, 3: 11.0, 4: 13.0}
    step_adjustments = {1: 50, 2: 60, 3: 70, 4: 80}
    creativity_adjustments = {1: 0.8, 2: 0.7, 3: 0.5, 4: 0.3}

    cfg_scale = cfg_adjustments[attempt_number]
    sampling_steps = step_adjustments[attempt_number]
    creativity = creativity_adjustments[attempt_number]

    # TODO: Fine-tune based on specific failure types
    # Example: If artifact_dim failed → increase steps more aggressively
    # Example: If composition failed → adjust seed instead of parameters

    return cfg_scale, sampling_steps, creativity
```

### 4.2 Dimension-Specific Adjustments (Future)

```python
def adjust_parameters_smart(
    attempt_number: int,
    previous_critique: CritiqueResult
) -> Tuple[float, int, float]:
    """Smart parameter adjustment based on which dimensions failed.

    Future enhancement: Adjust different parameters for different failures.
    """
    cfg_scale, sampling_steps, creativity = adjust_parameters(attempt_number, previous_critique)

    # Check which dimensions failed
    failed_dims = [d for d in previous_critique.dimensions if d.severity in [SeverityLevel.CRITICAL, SeverityLevel.MAJOR]]

    for dim in failed_dims:
        if dim.dimension == DimensionType.ARTIFACTING:
            # Artifacts → increase sampling steps aggressively
            sampling_steps = min(sampling_steps + 20, 100)
        elif dim.dimension == DimensionType.COMPOSITION:
            # Composition → might be seed issue, not parameters
            # (Regenerate with different seed)
            pass
        elif dim.dimension == DimensionType.READABILITY:
            # Blur → increase steps, lower creativity
            sampling_steps = min(sampling_steps + 10, 100)
            creativity = max(creativity - 0.1, 0.1)

    return cfg_scale, sampling_steps, creativity
```

---

## 5. Integration with Prep Orchestrator

### 5.1 Assumed Prep Pipeline Interface

```python
class PrepOrchestrator:
    """Coordinates all prep-time asset generation.

    Assumed interface based on WO-M3-PREP-01.
    """

    def __init__(
        self,
        image_generator: ImageAdapter,
        image_critic: ImageCritiqueAdapter,
        audio_generator: AudioAdapter,
        asset_store: AssetStore
    ):
        self.image_generator = image_generator
        self.image_critic = image_critic
        self.audio_generator = audio_generator
        self.asset_store = asset_store

    def prepare_campaign_assets(self, campaign_data: Dict[str, Any]) -> PrepResult:
        """Generate and validate all campaign assets.

        Args:
            campaign_data: Campaign definition (NPCs, scenes, encounters)

        Returns:
            PrepResult with generated assets and validation results
        """
        results = []

        # Generate NPC portraits
        for npc in campaign_data["npcs"]:
            image_result = self._generate_npc_portrait(npc)
            results.append(image_result)

        # Generate scene illustrations
        for scene in campaign_data["scenes"]:
            image_result = self._generate_scene_illustration(scene)
            results.append(image_result)

        # Generate audio assets (out of scope for this design)
        # ...

        return PrepResult(
            image_results=results,
            # audio_results=...,
            # attribution_ledger=...
        )

    def _generate_npc_portrait(self, npc: Dict[str, Any]) -> ImageResult:
        """Generate NPC portrait with critique validation."""
        scene_description = npc["description"]
        semantic_key = f"npc:{npc['id']}:portrait"

        return generate_and_validate_image(
            scene_description=scene_description,
            semantic_key=semantic_key,
            rubric=DEFAULT_CRITIQUE_RUBRIC,
            max_attempts=4
        )
```

### 5.2 Critique Adapter Selection

The prep orchestrator should support pluggable critique adapters:

```python
def create_prep_orchestrator(
    critique_backend: str = "clip",  # Default to CLIP (free, fast)
    **critique_kwargs
) -> PrepOrchestrator:
    """Create prep orchestrator with specified critique backend.

    Args:
        critique_backend: "clip" or "spark"
        **critique_kwargs: Backend-specific configuration

    Returns:
        PrepOrchestrator instance
    """
    # Create critique adapter
    if critique_backend == "spark":
        critic = create_image_critic("spark", **critique_kwargs)
    elif critique_backend == "clip":
        critic = create_image_critic("clip", **critique_kwargs)
    else:
        raise ValueError(f"Unknown critique backend: {critique_backend}")

    # Create orchestrator
    return PrepOrchestrator(
        image_generator=create_image_adapter("sdxl_lightning"),
        image_critic=critic,
        audio_generator=create_audio_adapter("stub"),
        asset_store=AssetStore(base_path="assets/")
    )
```

---

## 6. Error Handling & Fallbacks

### 6.1 Critique Failure Modes

| Error | Handling | Rationale |
|-------|----------|-----------|
| **Critique model unavailable** | Fall back to stub critic (auto-pass) | Prep should not block on critique |
| **All retries exhausted** | Use placeholder asset | Manual review post-prep |
| **Image generator fails** | Skip asset, log error | Prep continues with remaining assets |
| **Asset store write fails** | Retry 3×, then fail prep | Data integrity critical |

```python
def generate_and_validate_image_safe(
    scene_description: str,
    semantic_key: str,
    rubric: CritiqueRubric,
    max_attempts: int = 4
) -> ImageResult:
    """Safe wrapper that handles critique failures.

    Returns:
        ImageResult (never raises exceptions)
    """
    try:
        return generate_and_validate_image(
            scene_description, semantic_key, rubric, max_attempts
        )
    except CritiqueAdapterError as e:
        # Critique failed → fall back to stub critic (auto-pass)
        logger.warning(f"Critique failed for {semantic_key}: {e}. Using stub critic.")
        stub_critic = StubImageCritic(always_pass=True)
        # ... retry with stub
    except ImageGeneratorError as e:
        # Generation failed → return error result
        return ImageResult(
            status="error",
            asset_id="",
            path="",
            content_hash="",
            error_message=f"Image generation failed: {e}"
        )
```

### 6.2 Manual Review Queue

Failed images should be flagged for manual review:

```python
@dataclass
class ManualReviewItem:
    """Item requiring manual review after prep."""
    semantic_key: str
    scene_description: str
    attempts: List[RegenerationAttempt]
    final_critique: CritiqueResult
    reason: str

class PrepOrchestrator:
    def __init__(self, ...):
        self.manual_review_queue = []

    def _generate_npc_portrait(self, npc: Dict[str, Any]) -> ImageResult:
        """Generate NPC portrait with manual review queue."""
        result = generate_and_validate_image(...)

        if result.status == "placeholder":
            # Add to manual review queue
            self.manual_review_queue.append(ManualReviewItem(
                semantic_key=f"npc:{npc['id']}:portrait",
                scene_description=npc["description"],
                attempts=<regeneration_attempts>,
                final_critique=<last_critique_result>,
                reason="Failed after 4 attempts"
            ))

        return result
```

---

## 7. Performance Considerations

### 7.1 Timing Budget

**Target**: Prep for 50-NPC campaign should complete in < 30 minutes on consumer hardware.

| Stage | Time per Image | 50 Images Total |
|-------|----------------|-----------------|
| **Generation** (SDXL Lightning) | ~5s | ~4 min |
| **Critique** (CLIP, GPU) | ~0.5s | ~25s |
| **Critique** (Spark, API) | ~3s | ~2.5 min |
| **Regeneration** (worst case: 3 retries × 50% of images) | ~15s × 25 | ~6 min |
| **Asset storage** | ~0.1s | ~5s |
| **TOTAL** (CLIP) | | **~11 min** ✅ |
| **TOTAL** (Spark) | | **~13 min** ✅ |

**Optimization**: Run image generation + critique in parallel (batch process).

### 7.2 Parallel Processing

```python
import concurrent.futures

def prepare_campaign_assets_parallel(
    self,
    campaign_data: Dict[str, Any]
) -> PrepResult:
    """Generate assets in parallel."""
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all NPC portrait jobs
        futures = []
        for npc in campaign_data["npcs"]:
            future = executor.submit(self._generate_npc_portrait, npc)
            futures.append(future)

        # Wait for all to complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    return PrepResult(image_results=results)
```

---

## 8. Monitoring & Logging

### 8.1 Prep Report Format

```python
@dataclass
class PrepReport:
    """Summary of prep pipeline execution."""
    total_assets_requested: int
    assets_generated: int
    assets_failed: int
    assets_placeholder: int
    total_critique_passes: int
    total_critique_failures: int
    total_regenerations: int
    total_time_seconds: float
    manual_review_items: List[ManualReviewItem]
    critique_backend: str
    total_cost_usd: float  # If using Spark

def generate_prep_report(prep_result: PrepResult) -> PrepReport:
    """Generate human-readable prep report."""
    # ... aggregate stats from prep_result
    return PrepReport(...)
```

### 8.2 Logging Example

```
[PREP] Starting prep for campaign "Lost Mines of Phandelver"
[PREP] Generating 50 NPC portraits, 10 scene illustrations
[PREP] Using CLIP critique adapter (ViT-B/32, device=cuda)

[IMAGE] Generating npc:theron:portrait (attempt 1/4)
[IMAGE]   Generated in 4.8s
[CRITIQUE]   PASS (overall_score=0.82, readability=0.85, composition=0.78)
[IMAGE]   Saved to assets/images/npc_theron_portrait.png

[IMAGE] Generating npc:elsa:portrait (attempt 1/4)
[IMAGE]   Generated in 5.1s
[CRITIQUE]   FAIL (overall_score=0.62, artifacting=0.45 [MAJOR: extra finger])
[IMAGE]   Regenerating with adjusted parameters (cfg=9.0, steps=60)
[IMAGE] Generating npc:elsa:portrait (attempt 2/4)
[IMAGE]   Generated in 6.2s
[CRITIQUE]   PASS (overall_score=0.76, artifacting=0.72)
[IMAGE]   Saved to assets/images/npc_elsa_portrait.png

...

[PREP] Prep complete in 11m 32s
[PREP]   Total: 60 images requested
[PREP]   Generated: 58 (96.7%)
[PREP]   Failed: 0
[PREP]   Placeholder: 2 (3.3%)
[PREP]   Critique passes: 47 (first attempt)
[PREP]   Critique failures: 13 (required regeneration)
[PREP]   Total regenerations: 18
[PREP]   Manual review queue: 2 items
[PREP] See manual review queue for failed assets.
```

---

## 9. Testing Strategy

### 9.1 Integration Tests

```python
def test_prep_orchestrator_generates_valid_npc_portrait():
    """PrepOrchestrator generates and validates NPC portrait."""
    orchestrator = create_prep_orchestrator(critique_backend="stub")

    campaign_data = {
        "npcs": [
            {
                "id": "theron",
                "description": "A stern dwarf cleric with a gray beard"
            }
        ]
    }

    result = orchestrator.prepare_campaign_assets(campaign_data)

    assert len(result.image_results) == 1
    assert result.image_results[0].status == "generated"
    assert result.image_results[0].asset_id != ""


def test_prep_orchestrator_retries_on_critique_failure():
    """PrepOrchestrator retries generation when critique fails."""
    # Mock critique to fail first 2 attempts, pass on 3rd
    mock_critic = MockImageCritic(fail_first_n=2)
    orchestrator = PrepOrchestrator(
        image_generator=StubImageAdapter(),
        image_critic=mock_critic,
        asset_store=AssetStore(base_path="/tmp/assets")
    )

    campaign_data = {
        "npcs": [{"id": "test", "description": "Test NPC"}]
    }

    result = orchestrator.prepare_campaign_assets(campaign_data)

    assert mock_critic.critique_count == 3  # 1 original + 2 retries
    assert result.image_results[0].status == "generated"
```

---

## 10. Gap Analysis

### What Exists:
✅ Image critique contracts (CritiqueResult, CritiqueRubric)
✅ Stub critique adapter
✅ Image generation adapter protocol

### What's Missing:
❌ Prep orchestrator (WO-M3-PREP-01, Sonnet B)
❌ generate_and_validate_image() function
❌ Parameter adjustment logic
❌ Manual review queue system
❌ Prep report generation
❌ Integration tests

### Implementation Checklist:
1. ❌ Wait for WO-M3-PREP-01 completion (Sonnet B)
2. ❌ Implement generate_and_validate_image() in prep orchestrator
3. ❌ Add parameter adjustment strategies
4. ❌ Add manual review queue
5. ❌ Write integration tests (prep → critique → regeneration)
6. ❌ Add prep report generation
7. ❌ Test parallel asset generation

---

## 11. Dependencies

### On WO-M3-PREP-01:
- PrepOrchestrator class structure
- ImageGenerator integration
- AssetStore implementation
- Campaign data schema

### On This Work Order:
- SparkCritiqueAdapter (if using Spark)
- CLIPCritiqueAdapter (if using CLIP)
- StubImageCritic (already exists)

---

## 12. Future Enhancements

1. **Smart Retry Logic**: Use ML to predict which parameters to adjust based on failure type
2. **A/B Testing**: Generate 2 variants in parallel, choose best
3. **Incremental Prep**: Only regenerate assets that changed since last prep
4. **Caching**: Cache critiques by image hash to avoid re-processing
5. **Parallel Critique**: Critique multiple images concurrently on GPU

---

**END OF SPECIFICATION**
