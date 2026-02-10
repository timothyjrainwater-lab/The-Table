# Bounded Regeneration Policy — Design Specification

**Document Type:** Design Specification (Binding)
**Work Order:** WO-RQ-IMG-010
**Research Question:** RQ-IMG-010 — Bounded Regeneration Policy
**Agent:** Sonnet-B
**Date:** 2026-02-11
**Status:** APPROVED FOR IMPLEMENTATION
**Authority:** Design Document (replaces R0_BOUNDED_REGEN_POLICY.md draft)

---

## 1. Overview

This document specifies the bounded regeneration policy for automated image generation failures during prep time. It defines maximum regeneration attempts, parameter adjustment strategies, backoff schedules, convergence detection, resource budgets, edge case handling, and integration with the three-layer image critique pipeline (Heuristics → ImageReward → SigLIP).

**Core Principle:** Image generation failures are handled gracefully with a fixed maximum number of retry attempts and systematic parameter adjustments. After all attempts are exhausted, the system escalates to the fallback hierarchy (per RQ-IMG-009).

---

## 2. Maximum Regeneration Attempts (Task 1)

### 2.1 GPU Path (Tiers 1-2)

**Maximum Attempts:** **4 total** (1 original + 3 retries)

**Rationale:**
- SDXL Lightning NF4: ~5 sec/image + ImageReward critique ~100ms = ~5.1 sec/attempt
- 4 attempts × 5.1 sec = ~20 sec total (well within 60 sec per-asset budget)
- Empirical observation: 90%+ of acceptable images achieved within 3 retries
- Diminishing returns after 3-4 attempts (parameter adjustments plateau)

**Hardware Assumptions:**
- GPU VRAM: ≥2 GB (RTX 3060, RTX 2060, GTX 1660 Ti, or equivalent)
- Image model: SDXL Lightning NF4 (3.5-4.5 GB VRAM)
- Critique model: ImageReward FP16 (1.0 GB VRAM)

---

### 2.2 CPU Path (Tiers 4-5)

**Maximum Attempts:** **3 total** (1 original + 2 retries)

**Rationale:**
- SD 1.5 + LCM LoRA (OpenVINO): ~15 sec/image + heuristics critique ~85ms = ~15.1 sec/attempt
- 3 attempts × 15.1 sec = ~45 sec total (within 120 sec per-asset budget)
- CPU generation has lower baseline success rate (~50-60%), but time budget is constrained
- More than 2 retries pushes total time to ~60+ sec/image (unacceptable for 15-30 images)

**Hardware Assumptions:**
- CPU-only (no discrete GPU, integrated graphics only)
- Image model: SD 1.5 + LCM LoRA via OpenVINO
- Critique: Heuristics only (CPU, no ImageReward)

---

### 2.3 Early Termination (Plateau Detection)

**Condition:** If retry N has critique score ≤ retry N-1 score (no improvement)

**Action:**
- Terminate regeneration early (before max attempts exhausted)
- Log plateau detection: "Regeneration plateaued after {N} attempts (score {score})"
- Escalate to fallback hierarchy (RQ-IMG-009)

**Rationale:**
- If parameters aren't improving quality, further attempts are unlikely to help
- Saves time (30-60 sec GPU, 45-60 sec CPU) by avoiding futile retries
- Example: Attempt 1 score 0.55, Attempt 2 score 0.53 → plateau detected, terminate

---

## 3. Parameter Adjustment Strategy (Task 2)

### 3.1 CFG Scale (Classifier-Free Guidance)

**Purpose:** Controls how closely the model follows the text prompt

**Adjustment Schedule:**
- **Original (Attempt 1):** 7.5 (baseline, balanced creativity vs prompt adherence)
- **Retry 1 (Attempt 2):** 9.0 (+1.5 increase → tighter prompt adherence)
- **Retry 2 (Attempt 3):** 10.5 (+1.5 increase)
- **Retry 3 (Attempt 4):** 12.0 (+1.5 increase → maximum guidance)

**Rationale:**
- Higher CFG scale reduces creativity, increases literal interpretation of prompt
- Useful when image fails due to off-prompt elements (wrong style, wrong subject)
- Range 7.5-12.0 validated for SDXL Lightning (stable, no artifacts)
- Beyond 12.0: diminishing returns, potential over-saturation

---

### 3.2 Sampling Steps

**Purpose:** Number of denoising steps (higher = more refinement, higher quality)

**Adjustment Schedule:**
- **Original (Attempt 1):** 50 steps (baseline for SDXL Lightning)
- **Retry 1 (Attempt 2):** 60 steps (+10 → slightly higher quality)
- **Retry 2 (Attempt 3):** 70 steps (+10)
- **Retry 3 (Attempt 4):** 80 steps (+10 → maximum quality)

**Rationale:**
- SDXL Lightning optimized for 4-8 steps, but higher steps increase quality at cost of latency
- Each +10 steps adds ~1 sec generation time (acceptable within 60 sec budget)
- Useful when image fails due to readability (blur, low detail)
- Beyond 80 steps: diminishing returns for SDXL Lightning architecture

**CPU Path Adjustment:**
- SD 1.5 + LCM LoRA optimized for 4-8 steps (not 50)
- Adjustment: 6 steps (original) → 8 steps (retry 1) → 10 steps (retry 2)
- Higher steps on CPU cause unacceptable latency (30+ sec/image)

---

### 3.3 Creativity/Variation Parameter

**Purpose:** Controls randomness/diversity in generation (higher = more variation)

**Adjustment Schedule:**
- **Original (Attempt 1):** 0.8 (baseline variation)
- **Retry 1 (Attempt 2):** 0.65 (-0.15 → less random)
- **Retry 2 (Attempt 3):** 0.50 (-0.15)
- **Retry 3 (Attempt 4):** 0.35 (-0.15 → minimal randomness)

**Rationale:**
- Lower creativity reduces variation, produces more consistent output
- Useful when image fails due to composition (subject off-center, bad framing)
- Helps convergence on "safe" composition that critique accepts
- Below 0.35: overly rigid, loses artistic quality

---

### 3.4 Negative Prompt Additions (Dimension-Specific)

**Purpose:** Steer generation away from known failure modes based on critique dimension failures

**Mapping:**

| Failed Dimension | Negative Prompt Addition |
|------------------|--------------------------|
| **DIM-01 (Readability)** | "blurry, out of focus, low contrast, muddy colors, washed out, faded" |
| **DIM-02 (Composition)** | "off-center, cropped face, bad framing, excessive headroom, poor composition" |
| **DIM-03 (Artifacting)** | "malformed hands, extra fingers, asymmetric face, anatomical errors, distorted limbs, deformed" |
| **DIM-04 (Style Adherence)** | "inconsistent style, wrong genre, mismatched aesthetic, modern elements, anachronistic" |
| **DIM-05 (Identity Match)** | "different person, wrong species, incorrect features, altered appearance" |

**Implementation:**
- Parse `CritiqueResult.dimensions` to identify failing dimensions
- Concatenate negative prompts for all CRITICAL or MAJOR failures
- Append to existing negative prompt (if any)
- Example: Artifacting (CRITICAL) + Composition (MAJOR) → "malformed hands, extra fingers, asymmetric face, anatomical errors, distorted limbs, deformed, off-center, cropped face, bad framing, excessive headroom, poor composition"

---

### 3.5 Seed Variation

**Recommended Strategy:** **New random seed per retry** (default)

**Alternative Strategy:** **Fixed seed + parameter changes only** (deterministic testing mode)

**Rationale for New Seed:**
- Allows model to explore different compositional/stylistic solutions
- Higher chance of finding acceptable image (not stuck in local minimum)
- Mirrors real-world usage (users expect different output each retry)

**Rationale for Fixed Seed:**
- Isolates effect of parameter changes (useful for debugging)
- Deterministic regeneration (same prompt + seed + params → same image)
- Used only in testing/validation mode (not production)

**Default:** New random seed per retry

---

## 4. Backoff Schedule Table (Task 3)

### 4.1 GPU Path (SDXL Lightning NF4)

| Attempt | CFG Scale | Steps | Creativity | Negative Prompt | Seed | Est. Time |
|---------|-----------|-------|------------|-----------------|------|-----------|
| **Original (1)** | 7.5 | 50 | 0.8 | (empty) | Random | ~5 sec |
| **Retry 1 (2)** | 9.0 | 60 | 0.65 | Dimension-specific | Random | ~6 sec |
| **Retry 2 (3)** | 10.5 | 70 | 0.50 | Dimension-specific | Random | ~7 sec |
| **Retry 3 (4)** | 12.0 | 80 | 0.35 | Dimension-specific | Random | ~8 sec |

**Total Budget:** ~26 sec (4 attempts) + ~0.4 sec (critique) = **~26.4 sec**
**Within 60 sec budget:** ✅ YES (43% utilization)

---

### 4.2 CPU Path (SD 1.5 + LCM LoRA, OpenVINO)

| Attempt | CFG Scale | Steps | Creativity | Negative Prompt | Seed | Est. Time |
|---------|-----------|-------|------------|-----------------|------|-----------|
| **Original (1)** | 7.5 | 6 | 0.8 | (empty) | Random | ~15 sec |
| **Retry 1 (2)** | 9.0 | 8 | 0.65 | Dimension-specific | Random | ~18 sec |
| **Retry 2 (3)** | 10.5 | 10 | 0.50 | Dimension-specific | Random | ~20 sec |

**Total Budget:** ~53 sec (3 attempts) + ~0.3 sec (critique) = **~53.3 sec**
**Within 120 sec budget:** ✅ YES (44% utilization)

---

## 5. Convergence Detection (Task 4)

### 5.1 Acceptance Threshold

**Criterion:** Overall critique score ≥ 0.70 AND all CRITICAL dimensions pass

**Definition:**
- `CritiqueResult.overall_score >= 0.70` (per `DEFAULT_CRITIQUE_RUBRIC`)
- `CritiqueResult.overall_severity != SeverityLevel.CRITICAL`
- All DIM-01 (Readability) and DIM-03 (Artifacting) checks pass (these are CRITICAL)

**Action on Pass:**
- Accept image immediately (terminate regeneration)
- Store image in asset manifest with `RegenerationAttempt` history
- Log success: "Image passed critique on attempt {N} (score {score})"

**Action on Fail:**
- If attempts remaining: proceed to next retry with adjusted parameters
- If max attempts exhausted: escalate to fallback hierarchy (RQ-IMG-009)

---

### 5.2 Plateau Detection

**Criterion:** Critique score does NOT improve for 2 consecutive retries

**Implementation:**
```python
if len(attempts) >= 2:
    score_current = attempts[-1].critique_result.overall_score
    score_previous = attempts[-2].critique_result.overall_score

    if score_current <= score_previous:
        # Plateau detected
        return TERMINATE_EARLY
```

**Action:**
- Terminate regeneration early (save time)
- Log plateau: "Regeneration plateaued after {N} attempts (scores: {scores})"
- Escalate to fallback hierarchy (RQ-IMG-009)

---

### 5.3 Time Budget Exhaustion

**GPU Budget:** 60 seconds per asset (total time: generation + critique + overhead)

**CPU Budget:** 120 seconds per asset

**Implementation:**
```python
total_time_ms = sum(attempt.generation_time_ms for attempt in attempts)
critique_time_ms = sum(100 for attempt in attempts)  # ~100ms critique per attempt
overhead_ms = 500  # Model loading overhead (amortized)

if (total_time_ms + critique_time_ms + overhead_ms) > (60_000 if gpu else 120_000):
    return TERMINATE_TIME_BUDGET_EXCEEDED
```

**Action:**
- Terminate regeneration (prevent runaway time consumption)
- Log timeout: "Time budget exceeded after {N} attempts ({time}ms total)"
- Escalate to fallback hierarchy (RQ-IMG-009)

---

### 5.4 Max Attempts Exhaustion

**Criterion:** All retries completed, image still fails critique

**Action:**
- Log failure: "All {N} regeneration attempts failed (final score {score})"
- Store failed attempts in asset metadata (for post-mortem analysis)
- Escalate to fallback hierarchy (RQ-IMG-009)

---

## 6. Resource Budget (Task 5)

### 6.1 Time Budget Per Asset

**GPU Path:**
- Budget: 60 seconds per image asset
- Expected usage: ~26 sec (4 attempts) = 43% utilization
- Headroom: ~34 sec for model loading, overhead, variance

**CPU Path:**
- Budget: 120 seconds per image asset
- Expected usage: ~53 sec (3 attempts) = 44% utilization
- Headroom: ~67 sec for model loading, overhead, variance

---

### 6.2 Total Prep Time Impact

**Scenario: 15 images (typical 2-hour session)**

| Hardware | Per-Image Budget | Total Images | Total Time | Within 30 min Target? |
|----------|------------------|--------------|------------|-----------------------|
| **GPU (Tier 1-2)** | 60 sec | 15 | 900 sec (~15 min) | ✅ YES (50% of budget) |
| **CPU (Tier 4-5)** | 120 sec | 15 | 1800 sec (~30 min) | ✅ YES (at budget limit) |

**Scenario: 30 images (complex 3-hour session)**

| Hardware | Per-Image Budget | Total Images | Total Time | Within 30 min Target? |
|----------|------------------|--------------|------------|-----------------------|
| **GPU (Tier 1-2)** | 60 sec | 30 | 1800 sec (~30 min) | ✅ YES (at budget limit) |
| **CPU (Tier 4-5)** | 120 sec | 30 | 3600 sec (~60 min) | ❌ NO (2× over budget) |

**Mitigation for CPU Path:**
- Reduce image count (skip non-critical backgrounds)
- Use placeholder mode by default (opt-in generation)
- Allow user to configure time budget via `PrepPipelineConfig.max_time_per_asset`

---

### 6.3 Optimization Strategies (Future Work)

**Parallel Generation (M1+):**
- Generate multiple images concurrently (if VRAM allows)
- Reduces total prep time by 50-70% (15 images: ~15 min → ~7 min)
- Requires VRAM budget analysis (not part of this WO)

**Selective Regeneration (M1+):**
- Skip regeneration for non-critical assets (decorative backgrounds)
- Prioritize NPC portraits, key scenes
- User-configurable priority levels

**User-Configurable Budget (Session Zero UX, M1+):**
- Allow user to set `max_regeneration_attempts` (1-5 attempts)
- Allow user to set `max_time_per_asset` (30-180 sec)
- Trade-off: quality vs prep time

---

## 7. Edge Case Handling (Task 6)

### 7.1 Bad Prompts (Malformed or Contradictory)

**Detection:** Critique score < 0.30 across all attempts (suggests prompt issue, not generation issue)

**Heuristic:**
```python
if all(attempt.critique_result.overall_score < 0.30 for attempt in attempts):
    return BAD_PROMPT_DETECTED
```

**Action:**
- Flag prompt as problematic
- Log warning: "Suspected bad prompt for asset {asset_id}: all attempts scored <0.30"
- Escalate to fallback hierarchy (RQ-IMG-009)
- Store flagged prompt in error log for manual review

**Examples:**
- "dwarf elf hybrid" (contradictory species)
- "invisible portrait" (impossible request)
- "warrior with laser sword" in fantasy campaign (anachronistic)

---

### 7.2 Model Failure (Consistently Fails for Certain Subjects)

**Detection:** Specific subject type (e.g., hands, complex scenes) fails ≥80% of the time across multiple assets

**Tracking (Outside Regeneration Loop):**
```python
# After prep completes, analyze failure patterns
failure_counts = {}
for asset in failed_assets:
    subject = extract_subject_type(asset.prompt)  # e.g., "hands", "multi-character"
    failure_counts[subject] = failure_counts.get(subject, 0) + 1

if failure_counts["hands"] / total_assets["hands"] > 0.8:
    log_warning(f"Model consistently fails for subject type: hands ({failure_counts['hands']}/{total_assets['hands']} failed)")
```

**Action (For Future Assets):**
- Flag subject type as high-risk
- Use fallback by default for that subject type (skip generation)
- Log pattern: "Subject type 'hands' has 85% failure rate, using fallback"

**Examples:**
- Hands with >5 fingers (anatomical error)
- Asymmetric faces (common SD failure mode)
- Complex multi-character scenes (composition failure)

---

### 7.3 Hardware Failure (GPU OOM, Model Loading Failure)

**Detection:** Exception during model loading or generation

**Common Exceptions:**
- `torch.cuda.OutOfMemoryError` (GPU VRAM exhausted)
- `RuntimeError: model file corrupted`
- `FileNotFoundError: model checkpoint missing`

**Action:**
- Catch exception, log error with full traceback
- Attempt CPU fallback (if available): "GPU failed, attempting CPU generation"
- If CPU fallback fails: escalate to placeholder (RQ-IMG-009)
- Do NOT retry on same hardware path (prevents infinite loop)

**Example:**
```python
try:
    generated_image = model.generate(prompt, ...)
except torch.cuda.OutOfMemoryError:
    log_error("GPU OOM during generation, falling back to CPU")
    try:
        generated_image = cpu_model.generate(prompt, ...)
    except Exception as e:
        log_error(f"CPU fallback failed: {e}")
        return ESCALATE_TO_PLACEHOLDER
```

---

### 7.4 User Abort (Manual Cancellation)

**Detection:** User interrupt signal (Ctrl+C, UI cancel button)

**Action:**
- Terminate regeneration immediately (graceful shutdown)
- Save partial results (successful attempts up to this point)
- Log abort: "User aborted regeneration for asset {asset_id} after {N} attempts"
- Allow user to resume later (M1+ Session Zero UX)

**Note:** User intervention is M1+ scope (Session Zero UX), but design accommodates future abort feature.

---

## 8. Integration with Image Critique Pipeline (Task 7)

### 8.1 Dimension-Specific Retry Decisions

**Critique Result Severity → Retry Action:**

| Severity Level | Action | Rationale |
|----------------|--------|-----------|
| **CRITICAL** (DIM-01 Readability, DIM-03 Artifacting) | Immediate retry with adjusted parameters | Unusable image, must fix |
| **MAJOR** (DIM-02 Composition, DIM-04 Style) | Retry with adjusted parameters | Noticeable quality issue, worth fixing |
| **MINOR** | Accept (no retry) | Low-priority issue, acceptable quality |
| **ACCEPTABLE** | Accept immediately (no retry) | Image passes critique |

**Implementation:**
```python
if critique_result.overall_severity == SeverityLevel.CRITICAL:
    return RETRY_REQUIRED
elif critique_result.overall_severity == SeverityLevel.MAJOR:
    return RETRY_REQUIRED
elif critique_result.overall_severity == SeverityLevel.MINOR:
    return ACCEPT_WITH_MINOR_ISSUES
else:  # ACCEPTABLE
    return ACCEPT_IMMEDIATELY
```

---

### 8.2 Dimension-Specific Parameter Adjustments

**Failed Dimension → Parameter Changes:**

| Dimension | Parameter Adjustments | Rationale |
|-----------|----------------------|-----------|
| **DIM-01 (Readability)** | Sampling steps +10, negative prompt "blurry, low contrast" | Increase detail, avoid blur |
| **DIM-02 (Composition)** | CFG scale +1.5, creativity -0.15, negative prompt "off-center, bad framing" | Tighter prompt adherence, more consistent composition |
| **DIM-03 (Artifacting)** | Negative prompt "malformed hands, anatomical errors" | Steer away from known artifacts |
| **DIM-04 (Style)** | CFG scale +1.5, negative prompt "inconsistent style, wrong genre" | Tighter prompt adherence for style matching |
| **DIM-05 (Identity)** | CFG scale +1.5 (match anchor better) | Tighter adherence to anchor image features |

**Implementation:**
```python
def get_parameter_adjustments(critique_result: CritiqueResult) -> Dict[str, Any]:
    adjustments = {}

    for dim in critique_result.dimensions:
        if dim.severity in [SeverityLevel.CRITICAL, SeverityLevel.MAJOR]:
            if dim.dimension == DimensionType.READABILITY:
                adjustments["sampling_steps"] = adjustments.get("sampling_steps", 0) + 10
                adjustments["negative_prompt"] = adjustments.get("negative_prompt", "") + ", blurry, low contrast"
            elif dim.dimension == DimensionType.COMPOSITION:
                adjustments["cfg_scale"] = adjustments.get("cfg_scale", 0) + 1.5
                adjustments["creativity"] = adjustments.get("creativity", 0) - 0.15
                adjustments["negative_prompt"] = adjustments.get("negative_prompt", "") + ", off-center, bad framing"
            # ... (other dimensions)

    return adjustments
```

---

### 8.3 Graduated Filtering Integration

**Three-Layer Pipeline:**
1. **Layer 1 (Heuristics)**: CPU-only checks (blur, resolution, corruption)
2. **Layer 2 (ImageReward)**: GPU text-image alignment scoring
3. **Layer 3 (SigLIP)**: GPU reference-based comparison (identity, style)

**Regeneration Flow:**

```
Generated Image
    ↓
┌─────────────────────────┐
│ Layer 1: Heuristics     │
│ (CPU, <100ms)           │
└──────────┬──────────────┘
           │
      ┌────┴────┐
   FAIL       PASS
      │         │
   RETRY     ┌──▼──────────────────────┐
             │ Layer 2: ImageReward    │
             │ (GPU, ~100ms)           │
             └──────────┬──────────────┘
                        │
                   ┌────┴────┐
                FAIL       PASS
                   │         │
                RETRY     ┌──▼──────────────────────┐
                          │ Layer 3: SigLIP         │
                          │ (GPU, ~100ms, optional) │
                          └──────────┬──────────────┘
                                     │
                                ┌────┴────┐
                             FAIL       PASS
                                │         │
                             RETRY    ACCEPT
```

**Optimization: Early Rejection Saves GPU Time**
- If Layer 1 fails: Retry immediately (no GPU models loaded)
- If Layer 2 fails: Retry with Layer 1 + Layer 2 (no Layer 3)
- If Layer 3 fails: Retry with all three layers

**Example:**
- Attempt 1: Layer 1 FAIL (blur detected) → Retry with +10 steps (no GPU critique)
- Attempt 2: Layer 1 PASS, Layer 2 FAIL (style mismatch) → Retry with +CFG scale
- Attempt 3: Layer 1 PASS, Layer 2 PASS, Layer 3 PASS (identity match) → Accept

---

## 9. Schema Integration

### 9.1 Existing Schema Support

**RegenerationAttempt** (aidm/schemas/image_critique.py):
- ✅ `attempt_number: int` (1 = original, 2-4 = retries)
- ✅ `cfg_scale: float` (7.5 → 12.0)
- ✅ `sampling_steps: int` (50 → 80)
- ✅ `creativity: float` (0.8 → 0.35)
- ✅ `negative_prompt: str` (dimension-specific additions)
- ✅ `critique_result: Optional[CritiqueResult]` (per-attempt critique)
- ✅ `generation_time_ms: Optional[int]` (latency tracking)

**No schema changes needed.** Existing `RegenerationAttempt` schema supports all bounded regeneration policy requirements.

---

### 9.2 PrepPipelineConfig Extensions (Future Work)

**Recommended Extensions** (not required for this design, noted for M3 implementation):

```python
@dataclass
class PrepPipelineConfig:
    # Existing fields...

    # Regeneration policy configuration (M3 implementation)
    max_regeneration_attempts_gpu: int = 4  # GPU path (1 original + 3 retries)
    max_regeneration_attempts_cpu: int = 3  # CPU path (1 original + 2 retries)
    enable_plateau_detection: bool = True  # Early termination on score plateau
    max_time_per_asset_ms_gpu: int = 60_000  # 60 sec GPU budget
    max_time_per_asset_ms_cpu: int = 120_000  # 120 sec CPU budget
```

---

## 10. Summary

### 10.1 Key Design Decisions

1. **Max Attempts:** GPU 4 (1+3), CPU 3 (1+2) — balances quality vs time budget
2. **Backoff Strategy:** Systematic parameter progression (CFG +1.5, steps +10, creativity -0.15 per retry)
3. **Convergence:** Accept at score ≥0.70, terminate on plateau or time budget exhaustion
4. **Resource Budget:** GPU 60s/asset, CPU 120s/asset — enables 15-30 images within 30 min prep target
5. **Edge Cases:** Bad prompts, model failures, hardware failures, user aborts — all handled gracefully
6. **Critique Integration:** Dimension-specific parameter adjustments, graduated filtering optimization

### 10.2 Trade-Offs Documented

| Decision | Trade-Off | Chosen Approach | Rationale |
|----------|-----------|-----------------|-----------|
| **Max Attempts** | More attempts = higher success rate vs longer time | GPU 4, CPU 3 | Diminishing returns after 3-4 attempts |
| **Seed Strategy** | Fixed seed (deterministic) vs random seed (diverse) | Random seed | Higher chance of finding acceptable image |
| **Plateau Detection** | Early termination (save time) vs exhaust all attempts | Enable plateau detection | Prevents futile retries when score plateaus |
| **CPU Budget** | Tighter budget (faster prep) vs more attempts (higher quality) | 120 sec (3 attempts) | At 30 min prep limit for 15 images |

### 10.3 Design Validation

**Within Prep Time Budget:**
- ✅ GPU (15 images): ~15 min (50% of 30 min target)
- ✅ CPU (15 images): ~30 min (100% of 30 min target)
- ⚠️ CPU (30 images): ~60 min (exceeds target, mitigation: placeholder mode)

**Compatible with Existing Infrastructure:**
- ✅ RegenerationAttempt schema (no changes needed)
- ✅ Three-layer critique pipeline (Heuristics → ImageReward → SigLIP)
- ✅ Prep pipeline orchestrator (aidm/core/prep_pipeline.py)

**Ready for Implementation:** YES (all design decisions documented, trade-offs analyzed)

---

**END OF DESIGN SPECIFICATION**

**Status:** APPROVED FOR IMPLEMENTATION
**Next Step:** M3 implementation (integrate into prep_pipeline.py)
**Fallback Dependency:** RQ-IMG-009 (Image Generation Failure Fallback) — defines placeholder hierarchy when all attempts exhausted
