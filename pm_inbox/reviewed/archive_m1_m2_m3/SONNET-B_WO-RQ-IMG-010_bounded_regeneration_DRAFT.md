# Work Order: WO-RQ-IMG-010 — Bounded Regeneration Policy Design

**Work Order ID:** WO-RQ-IMG-010
**Agent:** TBD (Agent B recommended)
**Milestone:** R0 Critical Research
**Priority:** 2 (Critical Path)
**Status:** DRAFT
**Research Question:** RQ-IMG-010 — Bounded Regeneration Policy
**Deliverable Type:** Design Documentation

---

## Objective

Design the bounded regeneration policy for automated image generation failures during prep time. This WO defines maximum regeneration attempts, parameter adjustment strategy between attempts, backoff schedule, convergence detection, resource budgets, and integration with the image critique pipeline.

**Core Questions:**
- How many regeneration attempts are allowed before giving up? (1 original + N retries — what is N?)
- What generation parameters are adjusted between attempts? (CFG scale, sampling steps, negative prompts, seed variation)
- What is the backoff schedule? (What changes on retry 1, retry 2, retry 3?)
- When is an image "good enough" vs "keep trying"? (Convergence detection based on critique scores)
- What is the resource budget per asset? (Time budget during prep, not just attempt count)
- How are edge cases handled? (Bad prompts, model consistently fails for certain subjects)

---

## Background

### Existing Infrastructure

**Image Critique System:**
- [aidm/schemas/image_critique.py](../aidm/schemas/image_critique.py) — `RegenerationAttempt` schema already exists (attempt_number, cfg_scale, sampling_steps, creativity, negative_prompt, critique_result, generation_time_ms)
- [aidm/core/image_critique_adapter.py](../aidm/core/image_critique_adapter.py) — Critique adapter protocol (HeuristicsImageCritic, ImageRewardCritiqueAdapter, SigLIPCritiqueAdapter)
- [docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md](../docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md) — Three-layer graduated filtering design (Heuristics → ImageReward → SigLIP)

**Prep Pipeline:**
- [aidm/core/prep_pipeline.py](../aidm/core/prep_pipeline.py) — Sequential model loading orchestrator (LLM → Image Gen → Music Gen → SFX Gen)
- [aidm/schemas/prep_pipeline.py](../aidm/schemas/prep_pipeline.py) — PrepPipelineConfig, GeneratedAsset schemas

**Research Foundation:**
- [docs/research/R0_BOUNDED_REGEN_POLICY.md](../docs/research/R0_BOUNDED_REGEN_POLICY.md) — Non-binding research draft on regeneration policy (max 3 retries, backoff strategy, time budget, fallback hierarchy)
- [docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md](../docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md) — Prep time budgets (≤30 min target for full campaign prep)

**Image Generation:**
- R1 Technology Stack Validation: SDXL Lightning NF4 (4-6 sec/image on GPU), SD 1.5 OpenVINO (8-20 sec/image on CPU)
- Expected image count per campaign: 15-30 images (NPC portraits, scenes, items)

---

## Scope

### IN SCOPE

1. **Maximum Regeneration Attempts**
   - Define N for "1 original + N retries" policy
   - Hardware-specific limits (GPU vs CPU)
   - Rationale for chosen limit (UX vs compute cost trade-off)

2. **Parameter Adjustment Strategy**
   - CFG scale adjustments (guidance scale increase for tighter prompt adherence)
   - Sampling steps adjustments (increase for higher quality)
   - Creativity/variation adjustments (decrease for more deterministic output)
   - Negative prompt additions (dimension-specific negative prompts for critique failures)
   - Seed variation (same seed vs new seed per retry)

3. **Backoff Schedule**
   - Parameter values for retry 1, retry 2, retry 3
   - Example: CFG scale 7.5 → 9.0 → 10.5 → 12.0
   - Example: Sampling steps 50 → 60 → 70 → 80
   - Example: Creativity 0.8 → 0.65 → 0.50 → 0.35

4. **Convergence Detection**
   - When to accept image as "good enough" (critique score threshold)
   - When to stop retrying (max attempts exhausted, time budget exceeded)
   - When to escalate to fallback (all attempts fail critique)

5. **Resource Budget**
   - Time budget per asset (GPU: 60 seconds, CPU: 120 seconds recommended)
   - Attempt budget based on time (GPU: 4 attempts in 60s, CPU: 2 attempts in 120s)
   - Total prep time impact (15-30 images × budget per image)

6. **Edge Case Handling**
   - Bad prompts: Prompt itself is malformed or contradictory (e.g., "dwarf elf hybrid")
   - Model failure: Model consistently fails for certain subjects (e.g., hands, complex scenes)
   - Hardware failure: GPU OOM, model loading failure
   - User abort: User manually cancels regeneration

7. **Integration with Image Critique Pipeline**
   - How critique scores drive retry decisions (CRITICAL/MAJOR failures trigger retry, ACCEPTABLE passes)
   - How dimension-specific failures inform parameter adjustments (artifacting → negative prompt "malformed hands")
   - Graduated filtering integration (Layer 1 fails → Layer 2, Layer 2 fails → Layer 3)

### OUT OF SCOPE

1. **Implementation**: This is design documentation only. No code changes to `prep_pipeline.py` or critique adapters.
2. **Critique Model Selection**: Critique models already selected by R1 (Heuristics, ImageReward, SigLIP). This WO focuses on regeneration policy only.
3. **Fallback Strategy**: Fallback hierarchy (placeholder images, shipped art pack) is covered by RQ-IMG-009 (separate WO).
4. **User Intervention**: User manually accepting/rejecting images is M1+ scope (Session Zero UX).
5. **Benchmarking**: Design only. Actual regeneration success rate testing happens in separate validation WO.

---

## Tasks

### Task 1: Define Maximum Regeneration Attempts

**Action:** Specify the maximum number of regeneration attempts per image asset.

**Subtasks:**
1. **GPU Path**: Define max attempts for GPU-based generation
   - Recommended: 3 retries (4 total attempts: original + 3 retries)
   - Rationale: 4 attempts × 5 sec/attempt = 20 sec, well within 60 sec budget
   - Trade-off: More attempts = higher chance of success, but diminishing returns after 3-4 attempts

2. **CPU Path**: Define max attempts for CPU-based generation
   - Recommended: 2 retries (3 total attempts: original + 2 retries)
   - Rationale: 3 attempts × 40 sec/attempt = 120 sec, at budget limit
   - Trade-off: Fewer attempts = lower success rate, but CPU users have stricter time constraints

3. **Early Termination**: Allow early termination if critique score plateaus
   - If retry N has same or worse critique score as retry N-1, consider terminating early
   - Prevents wasting time on images that won't improve with more attempts

**Output:**
- `MAX_ATTEMPTS.md` section specifying GPU (4 attempts) and CPU (3 attempts) limits
- Rationale for chosen limits (UX vs compute cost)
- Early termination logic (plateau detection)

---

### Task 2: Define Parameter Adjustment Strategy

**Action:** Specify how generation parameters are adjusted between retry attempts.

**Subtasks:**
1. **CFG Scale (Guidance Scale)**: How much to increase per retry
   - Original: 7.5 (baseline)
   - Retry 1: 9.0 (+1.5 increase → tighter prompt adherence)
   - Retry 2: 10.5 (+1.5 increase)
   - Retry 3: 12.0 (+1.5 increase → maximum guidance)
   - Rationale: Higher CFG = less creativity, more literal prompt interpretation

2. **Sampling Steps**: How many denoising steps per retry
   - Original: 50 steps (baseline for SDXL Lightning)
   - Retry 1: 60 steps (+10 → slightly higher quality)
   - Retry 2: 70 steps (+10)
   - Retry 3: 80 steps (+10 → maximum quality)
   - Rationale: More steps = higher quality, but diminishing returns after 80 steps

3. **Creativity/Variation**: How much to reduce randomness per retry
   - Original: 0.8 (baseline variation)
   - Retry 1: 0.65 (-0.15 → less random)
   - Retry 2: 0.50 (-0.15)
   - Retry 3: 0.35 (-0.15 → minimal randomness)
   - Rationale: Lower creativity = more consistent output, closer to prompt

4. **Negative Prompt Additions**: Dimension-specific negative prompts
   - Artifacting failure → Add "malformed hands, extra fingers, asymmetric face, anatomical errors"
   - Readability failure → Add "blurry, out of focus, low contrast, muddy colors"
   - Composition failure → Add "off-center, cropped face, bad framing, excessive headroom"
   - Style failure → Add "inconsistent style, wrong genre, mismatched aesthetic"
   - Rationale: Targeted negative prompts address specific failure modes

5. **Seed Variation**: Same seed vs new seed per retry
   - Recommended: **New seed per retry** (allow model to explore different outputs)
   - Alternative: **Same seed + parameter changes** (isolate parameter effect)
   - Rationale: New seed increases diversity, higher chance of finding acceptable image

**Output:**
- `PARAMETER_ADJUSTMENT.md` section with backoff schedule table
- Rationale for each parameter adjustment
- Dimension-specific negative prompt mapping

---

### Task 3: Define Backoff Schedule Table

**Action:** Create a comprehensive backoff schedule table showing parameter values per attempt.

**Subtasks:**
1. **Create Table**: Define parameters for Original, Retry 1, Retry 2, Retry 3
   - Columns: Attempt Number, CFG Scale, Sampling Steps, Creativity, Negative Prompt Additions, Seed Strategy
   - Rows: Original, Retry 1, Retry 2, Retry 3

2. **Example Table**:
   | Attempt | CFG Scale | Steps | Creativity | Negative Prompt | Seed |
   |---------|-----------|-------|------------|-----------------|------|
   | Original | 7.5 | 50 | 0.8 | (empty) | Random |
   | Retry 1 | 9.0 | 60 | 0.65 | Dimension-specific | Random |
   | Retry 2 | 10.5 | 70 | 0.50 | Dimension-specific | Random |
   | Retry 3 | 12.0 | 80 | 0.35 | Dimension-specific | Random |

**Output:**
- `BACKOFF_SCHEDULE.md` section with backoff table
- Notes on parameter tuning (these values may need calibration in testing)

---

### Task 4: Define Convergence Detection

**Action:** Specify when to accept an image as "good enough" vs "keep trying."

**Subtasks:**
1. **Acceptance Threshold**: Critique score threshold for "good enough"
   - Recommended: Overall critique score ≥ 0.70 (per CritiqueRubric default)
   - ACCEPTABLE severity (no CRITICAL or MAJOR failures)
   - All critical dimensions pass (readability, artifacting)

2. **Plateau Detection**: When critique scores stop improving
   - If retry N score ≤ retry N-1 score, consider plateau detected
   - If 2 consecutive retries have no improvement, terminate early
   - Rationale: Further retries unlikely to improve quality

3. **Time Budget Exhaustion**: When time budget is exceeded
   - GPU: 60 seconds total per asset
   - CPU: 120 seconds total per asset
   - If time budget exceeded, terminate and escalate to fallback (RQ-IMG-009)

4. **Max Attempts Exhaustion**: When all retries are exhausted
   - GPU: After 4 attempts (original + 3 retries)
   - CPU: After 3 attempts (original + 2 retries)
   - Escalate to fallback if all attempts fail critique

**Output:**
- `CONVERGENCE_DETECTION.md` section with acceptance logic
- Plateau detection algorithm
- Time budget enforcement logic

---

### Task 5: Define Resource Budget

**Action:** Specify time budget per asset and total prep time impact.

**Subtasks:**
1. **Time Budget Per Asset**:
   - GPU: 60 seconds (allows 4 attempts at ~5 sec/attempt + critique overhead)
   - CPU: 120 seconds (allows 3 attempts at ~40 sec/attempt + critique overhead)
   - Rationale: Prep time budget ≤30 min for 15-30 images → ~60-120 sec/image

2. **Total Prep Time Impact**:
   - GPU: 15 images × 60 sec = 15 min (well within ≤30 min target)
   - CPU: 15 images × 120 sec = 30 min (at budget limit)
   - Worst case (30 images, CPU): 30 × 120 sec = 60 min (exceeds budget, need optimization)

3. **Optimization Strategies**:
   - Parallel generation for independent assets (not part of this WO, but noted)
   - Skip regeneration for non-critical assets (backgrounds, decorative items)
   - User-configurable time budget (Session Zero setting)

**Output:**
- `RESOURCE_BUDGET.md` section with time budget breakdown
- Total prep time impact analysis
- Optimization notes for future work

---

### Task 6: Define Edge Case Handling

**Action:** Specify how to handle edge cases where regeneration policy fails.

**Subtasks:**
1. **Bad Prompts**: Prompt is malformed or contradictory
   - Detection: Critique consistently fails across all attempts (all retries score <0.30)
   - Action: Flag prompt as problematic, log for review, escalate to fallback
   - Example: "dwarf elf hybrid" (contradictory species), "invisible portrait" (impossible request)

2. **Model Failure**: Model consistently fails for certain subjects
   - Detection: Specific subject type (hands, complex scenes) fails 80%+ of the time
   - Action: Flag subject type, use fallback for that asset, log for model improvement
   - Example: Hands with >5 fingers, asymmetric faces, complex multi-character scenes

3. **Hardware Failure**: GPU OOM, model loading failure
   - Detection: Exception during model loading or generation
   - Action: Fallback to CPU mode (if available), or escalate to placeholder (RQ-IMG-009)
   - Example: CUDA OOM error, model file corrupted

4. **User Abort**: User manually cancels regeneration
   - Detection: User interrupt signal (Ctrl+C, UI cancel button)
   - Action: Terminate regeneration, save partial results, allow user to retry later
   - Note: User intervention is M1+ scope (Session Zero UX), but design should accommodate future abort feature

**Output:**
- `EDGE_CASES.md` section with edge case handling logic
- Detection heuristics for each edge case
- Action/fallback for each edge case

---

### Task 7: Define Integration with Image Critique Pipeline

**Action:** Specify how regeneration policy integrates with three-layer graduated filtering (Heuristics → ImageReward → SigLIP).

**Subtasks:**
1. **Critique Score Driving Retry Decisions**:
   - CRITICAL failure (DIM-01 readability, DIM-03 artifacting) → Immediate retry with adjusted parameters
   - MAJOR failure (DIM-02 composition, DIM-04 style) → Retry with adjusted parameters
   - MINOR failure (low score but no critical issues) → Accept (no retry)
   - ACCEPTABLE → Accept immediately (no retry)

2. **Dimension-Specific Parameter Adjustments**:
   - DIM-01 (Readability) failure → Increase sampling steps, add negative prompt "blurry, low contrast"
   - DIM-02 (Composition) failure → Increase CFG scale, add negative prompt "off-center, bad framing"
   - DIM-03 (Artifacting) failure → Add negative prompt "malformed hands, asymmetric face, anatomical errors"
   - DIM-04 (Style) failure → Increase CFG scale (tighter prompt adherence), add negative prompt "inconsistent style"
   - DIM-05 (Identity) failure → Increase CFG scale (match anchor image better)

3. **Graduated Filtering Integration**:
   - Layer 1 (Heuristics) fails → Retry without loading GPU models (fast rejection)
   - Layer 2 (ImageReward) fails → Retry with adjusted parameters, re-run Layer 1 + Layer 2
   - Layer 3 (SigLIP) fails → Retry with adjusted parameters, re-run all three layers
   - Rationale: Early rejection saves GPU compute (graduated filtering optimization)

**Output:**
- `CRITIQUE_INTEGRATION.md` section with retry decision logic
- Dimension-specific parameter adjustment table
- Graduated filtering retry flow diagram

---

## Deliverables

1. **Design Document:** `docs/design/BOUNDED_REGENERATION_POLICY.md` (150-250 lines)
   - Maximum regeneration attempts (GPU: 4, CPU: 3)
   - Parameter adjustment strategy (CFG scale, steps, creativity, negative prompts)
   - Backoff schedule table (parameter values per retry)
   - Convergence detection (acceptance threshold, plateau detection, time budget)
   - Resource budget (time per asset, total prep time impact)
   - Edge case handling (bad prompts, model failure, hardware failure, user abort)
   - Critique integration (dimension-specific adjustments, graduated filtering)

2. **Backoff Schedule Table:** Comprehensive table showing parameter progression
   - Original, Retry 1, Retry 2, Retry 3 parameter values
   - Dimension-specific negative prompt additions

3. **Integration Notes:** Reference existing schema fields that support regeneration policy
   - `RegenerationAttempt` schema (aidm/schemas/image_critique.py) — Already exists, no changes needed
   - `PrepPipelineConfig` extensions — Note where critique_rubric and max_regeneration_attempts should be added

---

## Acceptance Criteria

1. ✅ **Design document complete** with all seven task sections (max attempts, parameters, backoff, convergence, budget, edge cases, integration)
2. ✅ **Backoff schedule table** with parameter values for Original, Retry 1, Retry 2, Retry 3
3. ✅ **Time budget analysis** showing GPU (15 min for 15 images) and CPU (30 min for 15 images) prep time
4. ✅ **Edge case handling** specified for bad prompts, model failure, hardware failure, user abort
5. ✅ **Critique integration** shows how dimension-specific failures drive parameter adjustments
6. ✅ **Integration notes** reference `RegenerationAttempt` schema and prep pipeline config extensions

---

## Dependencies

**Depends On:**
- RQ-IMG-001 (Image Critique Model Selection) — R1-ANSWERED (Heuristics + ImageReward + SigLIP)
- WO-M3-IMAGE-CRITIQUE-01 (Image Critique Design) — COMPLETE (three-layer graduated filtering design)
- WO-M3-PREP-01 (Prep Pipeline Prototype) — COMPLETE (sequential model loading)

**Blocks:**
- RQ-IMG-009 (Image Generation Failure Fallback) — Fallback policy depends on regeneration policy defining "all attempts exhausted"
- WO-M3-PREP-CRITIQUE-INTEGRATION (implementation) — Cannot implement regeneration without policy definition

**Related:**
- R0_BOUNDED_REGEN_POLICY.md (non-binding research draft) — Foundation for this design
- R0_PREP_PIPELINE_TIMING_STUDY.md (prep time budgets) — Informs time budget allocation

---

## Stop Conditions

**STOP and report if:**
1. **Existing design found**: A complete bounded regeneration policy already exists in `docs/design/` or `pm_inbox/reviewed/`
2. **Critique models changed**: R1 Technology Stack Validation is revised and critique models are replaced
3. **Scope overlap**: Another WO overlaps significantly with this work (e.g., prep pipeline integration already includes regeneration policy)
4. **Dependency on RQ-IMG-009**: If fallback strategy is needed to complete regeneration policy, flag dependency

---

## Notes for Agent

**Recommended Agent:** Agent B (Image & Asset Generation Architect)

**Key Considerations:**
- This is a **design WO**, not an implementation WO. Output is documentation, not code.
- Focus on **prep-time constraints** (≤30 min total prep budget for 15-30 images).
- Prioritize **GPU path** (majority of users), but provide **CPU fallback** path.
- Use R0_BOUNDED_REGEN_POLICY.md as research foundation, but make binding design decisions.
- Reference `RegenerationAttempt` schema (already exists) to ensure design aligns with existing contracts.

**Estimated Effort:** 3-5 hours (review existing research, draft design document, create backoff schedule table)

---

**END OF WORK ORDER DRAFT**
