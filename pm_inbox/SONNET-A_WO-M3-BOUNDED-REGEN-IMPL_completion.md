# Work Order Completion Report: WO-M3-BOUNDED-REGEN-IMPL

**Agent:** Sonnet-A
**Work Order:** WO-M3-BOUNDED-REGEN-IMPL (Bounded Regeneration Policy Implementation)
**Date:** 2026-02-11
**Status:** Implementation Phase Complete ✅

---

## 1. Executive Summary

Successfully implemented BoundedRegenerationPolicy module (Layer 1 of retry logic) based on approved design specification [docs/design/BOUNDED_REGENERATION_POLICY.md](../docs/design/BOUNDED_REGENERATION_POLICY.md).

**Core Achievement:** Pure-Python policy engine for image generation retry logic with hardware-specific budgets, convergence detection, and dimension-specific parameter adjustments.

**Implementation Status:** Complete and fully tested
- **Implementation:** [aidm/core/bounded_regeneration.py](../aidm/core/bounded_regeneration.py) (311 lines)
- **Tests:** [tests/test_bounded_regeneration.py](../tests/test_bounded_regeneration.py) (750 lines, 35 tests)
- **All tests passing:** 35/35 bounded regeneration tests
- **Total test suite:** 1931 tests passing (up from 1823 baseline)
- **Zero regressions:** All existing tests still pass

---

## 2. Acceptance Criteria Verification

### From WO-M3-BOUNDED-REGEN-IMPL:

- [x] **Implementation: aidm/core/bounded_regeneration.py**
  - BoundedRegenerationPolicy class implements should_retry, get_parameter_adjustments, detect_convergence ✅
  - GPU: 4 max attempts (1 original + 3 retries), 60s budget ✅
  - CPU: 3 max attempts (1 original + 2 retries), 120s budget ✅
  - Backoff schedules implemented per design spec ✅
  - Convergence detection with plateau threshold 0.02 ✅
  - Dimension-specific negative prompts ✅

- [x] **Tests: tests/test_bounded_regeneration.py**
  - Minimum 20 tests: **35 tests delivered** (exceeds requirement) ✅
  - GPU/CPU path tests ✅
  - Time budget tests ✅
  - Convergence/plateau detection tests ✅
  - Parameter adjustment tests ✅
  - Edge case tests ✅

- [x] **No modifications to locked infrastructure**
  - aidm/schemas/image_critique.py: UNCHANGED ✅
  - aidm/core/image_critique_adapter.py: UNCHANGED ✅
  - Frozen M0/M1/M2 code: UNCHANGED ✅
  - Total test suite: 1931 passing (no regressions) ✅

- [x] **Dependencies**
  - Pure Python implementation, no new dependencies ✅

---

## 3. Implementation Summary

### 3.1 BoundedRegenerationPolicy Class

**File:** [aidm/core/bounded_regeneration.py](../aidm/core/bounded_regeneration.py) (311 lines)

**Class Structure:**
```python
class BoundedRegenerationPolicy:
    """Policy for bounded image regeneration with parameter adjustments."""

    def __init__(
        self,
        max_attempts_gpu: int = 4,
        max_attempts_cpu: int = 3,
        time_budget_gpu_ms: int = 60_000,
        time_budget_cpu_ms: int = 120_000,
        plateau_threshold: float = 0.02,
        enable_plateau_detection: bool = True
    )

    def should_retry(
        self,
        attempt_number: int,
        hardware_tier: HardwareTier,
        elapsed_time_ms: int,
        critique_results: List[CritiqueResult]
    ) -> RegenerationDecision

    def get_parameter_adjustments(
        self,
        attempt_number: int,
        hardware_tier: HardwareTier,
        failed_dimensions: List[CritiqueDimension]
    ) -> Dict[str, Any]

    def _detect_plateau(
        self,
        critique_results: List[CritiqueResult]
    ) -> bool

    def detect_bad_prompt(
        self,
        critique_results: List[CritiqueResult]
    ) -> bool

    def calculate_time_remaining(
        self,
        hardware_tier: HardwareTier,
        elapsed_time_ms: int
    ) -> int
```

### 3.2 Hardware Tier Enum

```python
class HardwareTier(str, Enum):
    """Hardware tier classification for regeneration budgets."""
    GPU_TIER_1 = "gpu_tier_1"  # High-end GPU (RTX 3060+)
    GPU_TIER_2 = "gpu_tier_2"  # Mid-range GPU (RTX 2060, GTX 1660 Ti)
    CPU_TIER_4 = "cpu_tier_4"  # CPU-only (no discrete GPU)
    CPU_TIER_5 = "cpu_tier_5"  # CPU-only (low-end)
```

### 3.3 Regeneration Decision

```python
@dataclass
class RegenerationDecision:
    """Decision outcome from regeneration policy."""
    should_retry: bool
    reason: str
    parameter_adjustments: Optional[Dict[str, Any]] = None
    termination_reason: Optional[str] = None
```

### 3.4 Parameter Schedules

**GPU Path (SDXL Lightning NF4):**
```python
CFG_SCALE_SCHEDULE_GPU = [7.5, 9.0, 10.5, 12.0]  # Attempt 1-4
STEPS_SCHEDULE_GPU = [50, 60, 70, 80]
CREATIVITY_SCHEDULE = [0.8, 0.65, 0.50, 0.35]
```

**CPU Path (SD 1.5 + LCM LoRA):**
```python
CFG_SCALE_SCHEDULE_CPU = [7.5, 9.0, 10.5]  # Attempt 1-3
STEPS_SCHEDULE_CPU = [6, 8, 10]
CREATIVITY_SCHEDULE = [0.8, 0.65, 0.50]  # Same as GPU
```

### 3.5 Dimension-Specific Negative Prompts

```python
NEGATIVE_PROMPTS = {
    DimensionType.READABILITY: "blurry, out of focus, low contrast, muddy colors, washed out, faded",
    DimensionType.COMPOSITION: "off-center, cropped face, bad framing, excessive headroom, poor composition",
    DimensionType.ARTIFACTING: "malformed hands, extra fingers, asymmetric face, anatomical errors, distorted limbs, deformed",
    DimensionType.STYLE_ADHERENCE: "inconsistent style, wrong genre, mismatched aesthetic, modern elements, anachronistic",
    DimensionType.IDENTITY_MATCH: "different person, wrong species, incorrect features, altered appearance",
}
```

---

## 4. Test Coverage

### 4.1 Test File

**File:** [tests/test_bounded_regeneration.py](../tests/test_bounded_regeneration.py) (750 lines, 35 tests)

### 4.2 Test Categories

**Initialization (2 tests):**
- `test_bounded_regeneration_policy_default_init`: Default parameters
- `test_bounded_regeneration_policy_custom_init`: Custom parameters

**Max Attempts - GPU (4 tests):**
- `test_should_retry_gpu_attempt_1_fails`: Attempt 1 fails → retry
- `test_should_retry_gpu_attempt_2_fails`: Attempt 2 fails → retry
- `test_should_retry_gpu_attempt_3_fails`: Attempt 3 fails → retry (last retry)
- `test_should_retry_gpu_attempt_4_fails`: Attempt 4 fails → max exhausted

**Max Attempts - CPU (3 tests):**
- `test_should_retry_cpu_attempt_1_fails`: Attempt 1 fails → retry
- `test_should_retry_cpu_attempt_2_fails`: Attempt 2 fails → retry (last retry)
- `test_should_retry_cpu_attempt_3_fails`: Attempt 3 fails → max exhausted

**Time Budget (4 tests):**
- `test_should_retry_gpu_time_budget_exceeded`: GPU 60s budget exceeded
- `test_should_retry_cpu_time_budget_exceeded`: CPU 120s budget exceeded
- `test_calculate_time_remaining_gpu`: Remaining time calculation (GPU)
- `test_calculate_time_remaining_cpu`: Remaining time calculation (CPU)

**Convergence/Plateau Detection (5 tests):**
- `test_detect_plateau_no_improvement`: Score doesn't improve
- `test_detect_plateau_improvement_below_threshold`: Improvement < threshold
- `test_detect_plateau_improvement_above_threshold`: Improvement > threshold
- `test_should_retry_plateau_detected`: Plateau triggers early termination
- `test_should_retry_plateau_disabled`: Plateau detection can be disabled

**Image Passes Critique (1 test):**
- `test_should_retry_image_passes`: Passed image terminates retry

**Parameter Adjustments - GPU (4 tests):**
- `test_get_parameter_adjustments_gpu_attempt_1`: Baseline parameters
- `test_get_parameter_adjustments_gpu_attempt_2`: First retry
- `test_get_parameter_adjustments_gpu_attempt_3`: Second retry
- `test_get_parameter_adjustments_gpu_attempt_4`: Third retry (maximum)

**Parameter Adjustments - CPU (3 tests):**
- `test_get_parameter_adjustments_cpu_attempt_1`: Baseline parameters
- `test_get_parameter_adjustments_cpu_attempt_2`: First retry
- `test_get_parameter_adjustments_cpu_attempt_3`: Second retry (maximum for CPU)

**Dimension-Specific Negative Prompts (4 tests):**
- `test_negative_prompt_readability_failure`: Readability → blur-related prompts
- `test_negative_prompt_composition_failure`: Composition → framing-related prompts
- `test_negative_prompt_artifacting_failure`: Artifacting → anatomy-related prompts
- `test_negative_prompt_multiple_failures`: Multiple failures → concatenated prompts

**Bad Prompt Detection (3 tests):**
- `test_detect_bad_prompt_all_low_scores`: All scores < 0.30 → bad prompt
- `test_detect_bad_prompt_some_acceptable_scores`: Some scores OK → not bad prompt
- `test_detect_bad_prompt_empty_results`: No results → not bad prompt

**Edge Cases (2 tests):**
- `test_should_retry_no_critique_results`: No critique yet → proceed
- `test_parameter_adjustments_exceed_schedule_length`: Attempt number clamped

**Total:** 35 tests (exceeds 20 minimum requirement)

---

## 5. Design Compliance

### 5.1 Matches Approved Design Specification

**Blueprint:** [docs/design/BOUNDED_REGENERATION_POLICY.md](../docs/design/BOUNDED_REGENERATION_POLICY.md) (~620 lines)

**Compliance:** 100% ✅

All sections from design spec implemented exactly as specified:
- Section 2: Maximum regeneration attempts (GPU: 4, CPU: 3) → IMPLEMENTED
- Section 3: Parameter adjustment strategy (CFG, steps, creativity, negative prompts) → IMPLEMENTED
- Section 4: Backoff schedule tables → IMPLEMENTED
- Section 5: Convergence detection (plateau, time budget, max attempts) → IMPLEMENTED
- Section 6: Resource budget (GPU: 60s, CPU: 120s) → IMPLEMENTED
- Section 7: Edge case handling (bad prompts, model failure, hardware failure) → IMPLEMENTED

### 5.2 Integration Points

**Schema Compatibility:**
- Uses existing `CritiqueResult` schema (no modifications) ✅
- Uses existing `CritiqueDimension` schema (no modifications) ✅
- Uses existing `SeverityLevel` enum (no modifications) ✅
- Uses existing `DimensionType` enum (no modifications) ✅

**Hardware Tiers:**
- Introduced `HardwareTier` enum for GPU/CPU path selection
- GPU tiers (1-2): 4 attempts, 60s budget
- CPU tiers (4-5): 3 attempts, 120s budget

**Return Type:**
- Introduced `RegenerationDecision` dataclass for policy decisions
- Contains should_retry flag, reason, parameter_adjustments, termination_reason

---

## 6. Performance & Resource Budget

### 6.1 Time Budget Validation

**GPU Path (4 attempts):**
- Expected: ~26 sec (4 attempts × ~6.5 sec avg) + critique overhead
- Budget: 60 sec
- Utilization: ~43% ✅
- Headroom: ~34 sec for model loading, overhead, variance

**CPU Path (3 attempts):**
- Expected: ~53 sec (3 attempts × ~17.5 sec avg) + critique overhead
- Budget: 120 sec
- Utilization: ~44% ✅
- Headroom: ~67 sec for model loading, overhead, variance

### 6.2 Plateau Detection Benefits

**Time Saved (Early Termination):**
- GPU: ~13 sec (2 attempts saved if plateau detected at attempt 2)
- CPU: ~35 sec (1 attempt saved if plateau detected at attempt 2)

**Example:**
- Attempt 1: score 0.50 (failed)
- Attempt 2: score 0.50 (no improvement → plateau detected)
- Terminate early, save remaining attempts' time

---

## 7. Example Usage

### 7.1 Basic Usage

```python
from aidm.core.bounded_regeneration import BoundedRegenerationPolicy, HardwareTier
from aidm.schemas.image_critique import CritiqueResult

policy = BoundedRegenerationPolicy()

# After each generation attempt + critique:
decision = policy.should_retry(
    attempt_number=2,
    hardware_tier=HardwareTier.GPU_TIER_1,
    elapsed_time_ms=10_000,
    critique_results=[result1, result2]
)

if decision.should_retry:
    # Apply parameter adjustments for next attempt
    adjustments = decision.parameter_adjustments
    cfg_scale = adjustments["cfg_scale"]
    steps = adjustments["sampling_steps"]
    creativity = adjustments["creativity"]
    negative_prompt = adjustments["negative_prompt"]
    # Generate with adjusted parameters...
else:
    # Terminate regeneration
    print(f"Termination reason: {decision.termination_reason}")
    print(f"Reason: {decision.reason}")
```

### 7.2 Custom Configuration

```python
policy = BoundedRegenerationPolicy(
    max_attempts_gpu=5,  # Allow 5 attempts instead of 4
    time_budget_gpu_ms=90_000,  # 90s budget instead of 60s
    plateau_threshold=0.05,  # Less sensitive plateau detection
    enable_plateau_detection=False  # Disable early termination
)
```

### 7.3 Integration with Prep Pipeline

```python
# Pseudocode for prep pipeline integration:

def generate_asset_with_retry(prompt, hardware_tier):
    policy = BoundedRegenerationPolicy()
    critique_results = []
    attempt = 1
    start_time = time.time()

    while True:
        # Get parameter adjustments for current attempt
        if attempt == 1:
            params = get_default_params()
        else:
            params = policy.get_parameter_adjustments(
                attempt_number=attempt,
                hardware_tier=hardware_tier,
                failed_dimensions=get_failed_dimensions(critique_results[-1])
            )

        # Generate image with adjusted parameters
        image_bytes = generate_image(prompt, **params)

        # Critique image
        critique_result = critique_image(image_bytes)
        critique_results.append(critique_result)

        # Check if should retry
        elapsed_ms = (time.time() - start_time) * 1000
        decision = policy.should_retry(
            attempt_number=attempt,
            hardware_tier=hardware_tier,
            elapsed_time_ms=elapsed_ms,
            critique_results=critique_results
        )

        if not decision.should_retry:
            # Termination condition met
            if decision.termination_reason == "passed_critique":
                return image_bytes  # Success
            else:
                # Escalate to fallback (RQ-IMG-009)
                return fallback_image(decision.termination_reason)

        attempt += 1
```

---

## 8. Test Results

### 8.1 All Tests Passing

**BoundedRegenerationPolicy tests:**
```
tests/test_bounded_regeneration.py::35 tests
============================= 35 passed in 0.09s ==============================
```

**Full test suite:**
```
======================== 1931 tests collected in 0.74s ========================
===================== 1931 passed, 43 warnings in 10.57s ======================
```

### 8.2 No Regressions

- Original test suite: 1823 tests (all passing before this WO)
- New test suite: 1931 tests (1823 + 35 + 73 other new tests from concurrent work)
- All 1931 tests passing ✅
- No modifications to frozen M0/M1/M2 code
- No modifications to locked protocols/schemas

---

## 9. Code Quality

### 9.1 Type Hints

Full type coverage:
```python
def should_retry(
    self,
    attempt_number: int,
    hardware_tier: HardwareTier,
    elapsed_time_ms: int,
    critique_results: List[CritiqueResult]
) -> RegenerationDecision:
```

### 9.2 Docstrings

All classes and methods documented:
- Class docstring with attributes
- Method docstrings with Args/Returns
- Helper method docstrings
- Enum value documentation

### 9.3 Error Handling

No exceptions raised during normal operation:
- All decision logic returns RegenerationDecision (never raises)
- Edge cases handled gracefully (empty results, out-of-range attempts, etc.)
- Time budget enforcement prevents runaway retries

---

## 10. Design Decisions & Trade-Offs

### 10.1 Key Design Decisions

| Decision | Trade-Off | Chosen Approach | Rationale |
|----------|-----------|-----------------|-----------|
| **Max Attempts** | More attempts = higher success rate vs longer time | GPU 4, CPU 3 | Diminishing returns after 3-4 attempts (per design spec § 2) |
| **Seed Strategy** | Fixed seed (deterministic) vs random seed (diverse) | Random seed | Higher chance of finding acceptable image (not stuck in local minimum) |
| **Plateau Detection** | Early termination (save time) vs exhaust all attempts | Enable plateau detection (default: True) | Prevents futile retries when score plateaus (saves 30-60 sec) |
| **CPU Budget** | Tighter budget (faster prep) vs more attempts (higher quality) | 120 sec (3 attempts) | At 30 min prep limit for 15 images (per design spec § 6.2) |

### 10.2 Implementation Choices

**Attempt Number Indexing:**
- Design spec uses 1-based attempt numbering (Attempt 1 = original, Attempt 2-4 = retries)
- Implementation uses 0-based indexing for schedule arrays
- Conversion: `idx = attempt_number - 1`
- Test coverage confirms correct mapping

**Hardware Tier Enum:**
- Explicit enum instead of boolean GPU flag
- Allows for future expansion (GPU Tier 3, CPU Tier 6, etc.)
- Clear separation between GPU (Tier 1-2) and CPU (Tier 4-5)

**Negative Prompt Concatenation:**
- Multiple failed dimensions → concatenate all negative prompts
- Delimiter: ", " (comma-space)
- Example: "blurry, out of focus, off-center, bad framing" (Readability + Composition failures)

---

## 11. Future Work (M3+ Integration)

### 11.1 Prep Pipeline Integration

**Next Steps:**
- Integrate BoundedRegenerationPolicy into `aidm/core/prep_pipeline.py`
- Wire up to image generation loop
- Add logging for regeneration attempts (attempt number, score, parameters, termination reason)
- Store RegenerationAttempt history in asset metadata

### 11.2 Calibration (Post-M3)

**Threshold Tuning:**
- Current thresholds: Design spec defaults
- Calibration needed: Real prep pipeline images
- Method: Grid search over threshold ranges
- Target: Optimize accuracy on ground truth data

### 11.3 User Configuration (Session Zero UX, M1+)

**Recommended Extensions:**
```python
# Allow user to configure via CLI flags or config file
user_config = PrepPipelineConfig(
    max_regeneration_attempts_gpu=5,  # User wants higher quality
    time_budget_per_asset_ms_gpu=90_000,  # Willing to wait longer
    enable_plateau_detection=False  # Exhaust all attempts
)
```

---

## 12. Deliverables Summary

### 12.1 Files Created

**Implementation:**
- ✅ [aidm/core/bounded_regeneration.py](../aidm/core/bounded_regeneration.py) (311 lines) - NEW

**Tests:**
- ✅ [tests/test_bounded_regeneration.py](../tests/test_bounded_regeneration.py) (750 lines, 35 tests) - NEW

**Completion report:**
- ✅ [pm_inbox/SONNET-A_WO-M3-BOUNDED-REGEN-IMPL_completion.md](../pm_inbox/SONNET-A_WO-M3-BOUNDED-REGEN-IMPL_completion.md) - THIS FILE

### 12.2 Lines of Code

- Implementation: 311 lines
- Tests: 750 lines
- **Total new code: 1061 lines**

### 12.3 Test Coverage

- New tests: 35
- Total test suite: 1931 tests (all passing)
- Test categories: Initialization, max attempts (GPU/CPU), time budget, convergence, parameter adjustments, negative prompts, bad prompt detection, edge cases

---

## 13. Conclusion

### 13.1 Work Order Complete ✅

All deliverables from WO-M3-BOUNDED-REGEN-IMPL are complete and verified:

- [x] Implementation: BoundedRegenerationPolicy class (311 lines)
- [x] GPU: 4 max attempts, 60s budget
- [x] CPU: 3 max attempts, 120s budget
- [x] Convergence detection (plateau threshold 0.02)
- [x] Parameter adjustments (CFG, steps, creativity, negative prompts)
- [x] Dimension-specific negative prompt additions
- [x] Tests: 35 comprehensive tests (750 lines)
- [x] Total suite: 1931 tests passing ✅
- [x] No regressions: All existing tests still pass ✅
- [x] Zero new dependencies (pure Python)

### 13.2 Ready for PM Approval

**Status:** Implementation complete, awaiting PM (Opus) review.

**Next Step:** PM to review and move to reviewed/ if approved.

**Blockers:** None

**Dependencies:** None (standalone module, integrates with existing schemas)

---

**END OF COMPLETION REPORT**

**Agent:** Sonnet-A
**Date:** 2026-02-11
**Deliverables:** Implementation (311 lines) + Tests (750 lines, 35 tests)
**Status:** ✅ Implementation Phase Complete
