"""Tests for BoundedRegenerationPolicy (M3 Image Generation Retry Logic).

M3 IMPLEMENTATION TESTS
-----------------------
Tests bounded regeneration policy for automated image generation retries.
Validates attempt limits, time budgets, convergence detection, and parameter adjustments.

Based on approved design: docs/design/BOUNDED_REGENERATION_POLICY.md
"""

import pytest
from aidm.core.bounded_regeneration import (
    BoundedRegenerationPolicy,
    HardwareTier,
    RegenerationDecision,
)
from aidm.schemas.image_critique import (
    CritiqueResult,
    CritiqueDimension,
    DimensionType,
    SeverityLevel,
)


# =============================================================================
# Test Fixtures
# =============================================================================

def create_critique_result(
    passed: bool = False,
    overall_score: float = 0.50,
    overall_severity: SeverityLevel = SeverityLevel.MAJOR,
    failed_dimensions: list = None
) -> CritiqueResult:
    """Helper to create CritiqueResult for testing.

    Args:
        passed: Whether image passed critique
        overall_score: Overall quality score (0.0-1.0)
        overall_severity: Worst severity level
        failed_dimensions: List of (dimension_type, score) tuples for failed dims

    Returns:
        CritiqueResult instance
    """
    if failed_dimensions is None:
        failed_dimensions = [(DimensionType.READABILITY, 0.50)]

    dimensions = []
    for dim_type in DimensionType:
        # Check if this dimension failed
        failed_info = next((d for d in failed_dimensions if d[0] == dim_type), None)
        if failed_info:
            dim_type, score = failed_info
            severity = SeverityLevel.CRITICAL if score < 0.30 else SeverityLevel.MAJOR if score < 0.70 else SeverityLevel.MINOR
            dimensions.append(CritiqueDimension(
                dimension=dim_type,
                severity=severity,
                score=score,
                reason=f"Failed {dim_type.value}",
                measurement_method="test"
            ))
        else:
            # Dimension passed
            dimensions.append(CritiqueDimension(
                dimension=dim_type,
                severity=SeverityLevel.ACCEPTABLE,
                score=0.95,
                reason=f"Passed {dim_type.value}",
                measurement_method="test"
            ))

    # Sort dimensions by dimension type (required by schema)
    dimensions.sort(key=lambda d: d.dimension.value)

    return CritiqueResult(
        passed=passed,
        overall_severity=overall_severity,
        dimensions=dimensions,
        overall_score=overall_score,
        rejection_reason=None if passed else "Failed critique",
        critique_method="test"
    )


# =============================================================================
# Initialization Tests
# =============================================================================

def test_bounded_regeneration_policy_default_init():
    """BoundedRegenerationPolicy initializes with default parameters."""
    policy = BoundedRegenerationPolicy()
    assert policy.max_attempts_gpu == 4
    assert policy.max_attempts_cpu == 3
    assert policy.time_budget_gpu_ms == 60_000
    assert policy.time_budget_cpu_ms == 120_000
    assert policy.plateau_threshold == 0.02
    assert policy.enable_plateau_detection is True


def test_bounded_regeneration_policy_custom_init():
    """BoundedRegenerationPolicy initializes with custom parameters."""
    policy = BoundedRegenerationPolicy(
        max_attempts_gpu=5,
        max_attempts_cpu=4,
        time_budget_gpu_ms=90_000,
        time_budget_cpu_ms=180_000,
        plateau_threshold=0.05,
        enable_plateau_detection=False
    )
    assert policy.max_attempts_gpu == 5
    assert policy.max_attempts_cpu == 4
    assert policy.time_budget_gpu_ms == 90_000
    assert policy.time_budget_cpu_ms == 180_000
    assert policy.plateau_threshold == 0.05
    assert policy.enable_plateau_detection is False


# =============================================================================
# Max Attempts Tests (GPU)
# =============================================================================

def test_should_retry_gpu_attempt_1_fails():
    """GPU path attempt 1 fails → should retry (attempt 2)."""
    policy = BoundedRegenerationPolicy()
    critique_results = [create_critique_result(passed=False, overall_score=0.50)]

    decision = policy.should_retry(
        attempt_number=1,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=5000,
        critique_results=critique_results
    )

    assert decision.should_retry is True
    assert "Retrying" in decision.reason
    assert decision.parameter_adjustments is not None


def test_should_retry_gpu_attempt_2_fails():
    """GPU path attempt 2 fails → should retry (attempt 3)."""
    policy = BoundedRegenerationPolicy()
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.55)
    ]

    decision = policy.should_retry(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=10000,
        critique_results=critique_results
    )

    assert decision.should_retry is True
    assert decision.parameter_adjustments is not None


def test_should_retry_gpu_attempt_3_fails():
    """GPU path attempt 3 fails → should retry (attempt 4, last attempt)."""
    policy = BoundedRegenerationPolicy()
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.55),
        create_critique_result(passed=False, overall_score=0.58)
    ]

    decision = policy.should_retry(
        attempt_number=3,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=15000,
        critique_results=critique_results
    )

    assert decision.should_retry is True
    assert decision.parameter_adjustments is not None


def test_should_retry_gpu_attempt_4_fails():
    """GPU path attempt 4 fails → no retry (max attempts exhausted)."""
    policy = BoundedRegenerationPolicy()
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.55),
        create_critique_result(passed=False, overall_score=0.58),
        create_critique_result(passed=False, overall_score=0.60)
    ]

    decision = policy.should_retry(
        attempt_number=4,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=20000,
        critique_results=critique_results
    )

    assert decision.should_retry is False
    assert "Maximum attempts" in decision.reason
    assert decision.termination_reason == "max_attempts_exhausted"


# =============================================================================
# Max Attempts Tests (CPU)
# =============================================================================

def test_should_retry_cpu_attempt_1_fails():
    """CPU path attempt 1 fails → should retry (attempt 2)."""
    policy = BoundedRegenerationPolicy()
    critique_results = [create_critique_result(passed=False, overall_score=0.50)]

    decision = policy.should_retry(
        attempt_number=1,
        hardware_tier=HardwareTier.CPU_TIER_4,
        elapsed_time_ms=15000,
        critique_results=critique_results
    )

    assert decision.should_retry is True
    assert decision.parameter_adjustments is not None


def test_should_retry_cpu_attempt_2_fails():
    """CPU path attempt 2 fails → should retry (attempt 3, last attempt)."""
    policy = BoundedRegenerationPolicy()
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.55)
    ]

    decision = policy.should_retry(
        attempt_number=2,
        hardware_tier=HardwareTier.CPU_TIER_4,
        elapsed_time_ms=30000,
        critique_results=critique_results
    )

    assert decision.should_retry is True
    assert decision.parameter_adjustments is not None


def test_should_retry_cpu_attempt_3_fails():
    """CPU path attempt 3 fails → no retry (max attempts exhausted)."""
    policy = BoundedRegenerationPolicy()
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.55),
        create_critique_result(passed=False, overall_score=0.58)
    ]

    decision = policy.should_retry(
        attempt_number=3,
        hardware_tier=HardwareTier.CPU_TIER_4,
        elapsed_time_ms=45000,
        critique_results=critique_results
    )

    assert decision.should_retry is False
    assert "Maximum attempts" in decision.reason
    assert decision.termination_reason == "max_attempts_exhausted"


# =============================================================================
# Time Budget Tests
# =============================================================================

def test_should_retry_gpu_time_budget_exceeded():
    """GPU path time budget exceeded → no retry."""
    policy = BoundedRegenerationPolicy()
    critique_results = [create_critique_result(passed=False, overall_score=0.50)]

    decision = policy.should_retry(
        attempt_number=1,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=65_000,  # Exceeds 60s budget
        critique_results=critique_results
    )

    assert decision.should_retry is False
    assert "Time budget" in decision.reason
    assert decision.termination_reason == "time_budget_exceeded"


def test_should_retry_cpu_time_budget_exceeded():
    """CPU path time budget exceeded → no retry."""
    policy = BoundedRegenerationPolicy()
    critique_results = [create_critique_result(passed=False, overall_score=0.50)]

    decision = policy.should_retry(
        attempt_number=1,
        hardware_tier=HardwareTier.CPU_TIER_4,
        elapsed_time_ms=125_000,  # Exceeds 120s budget
        critique_results=critique_results
    )

    assert decision.should_retry is False
    assert "Time budget" in decision.reason
    assert decision.termination_reason == "time_budget_exceeded"


def test_calculate_time_remaining_gpu():
    """Calculate remaining time for GPU path."""
    policy = BoundedRegenerationPolicy()

    # 20s elapsed, 40s remaining
    remaining = policy.calculate_time_remaining(
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=20_000
    )
    assert remaining == 40_000

    # Budget exceeded
    remaining = policy.calculate_time_remaining(
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=70_000
    )
    assert remaining == 0


def test_calculate_time_remaining_cpu():
    """Calculate remaining time for CPU path."""
    policy = BoundedRegenerationPolicy()

    # 60s elapsed, 60s remaining
    remaining = policy.calculate_time_remaining(
        hardware_tier=HardwareTier.CPU_TIER_4,
        elapsed_time_ms=60_000
    )
    assert remaining == 60_000

    # Budget exceeded
    remaining = policy.calculate_time_remaining(
        hardware_tier=HardwareTier.CPU_TIER_4,
        elapsed_time_ms=130_000
    )
    assert remaining == 0


# =============================================================================
# Convergence/Plateau Detection Tests
# =============================================================================

def test_detect_plateau_no_improvement():
    """Plateau detected when score doesn't improve."""
    policy = BoundedRegenerationPolicy(plateau_threshold=0.02)
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.50)  # No improvement
    ]

    plateau = policy._detect_plateau(critique_results)
    assert plateau is True


def test_detect_plateau_improvement_below_threshold():
    """Plateau detected when improvement is below threshold."""
    policy = BoundedRegenerationPolicy(plateau_threshold=0.02)
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.51)  # Delta = 0.01 < 0.02
    ]

    plateau = policy._detect_plateau(critique_results)
    assert plateau is True


def test_detect_plateau_improvement_above_threshold():
    """No plateau when improvement is above threshold."""
    policy = BoundedRegenerationPolicy(plateau_threshold=0.02)
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.55)  # Delta = 0.05 > 0.02
    ]

    plateau = policy._detect_plateau(critique_results)
    assert plateau is False


def test_should_retry_plateau_detected():
    """Plateau detection triggers early termination."""
    policy = BoundedRegenerationPolicy(enable_plateau_detection=True, plateau_threshold=0.02)
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.50)  # Plateau
    ]

    decision = policy.should_retry(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=10000,
        critique_results=critique_results
    )

    assert decision.should_retry is False
    assert "plateau" in decision.reason.lower()
    assert decision.termination_reason == "plateau_detected"


def test_should_retry_plateau_disabled():
    """Plateau detection disabled → continue retrying."""
    policy = BoundedRegenerationPolicy(enable_plateau_detection=False)
    critique_results = [
        create_critique_result(passed=False, overall_score=0.50),
        create_critique_result(passed=False, overall_score=0.50)  # Would be plateau if enabled
    ]

    decision = policy.should_retry(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=10000,
        critique_results=critique_results
    )

    assert decision.should_retry is True  # Plateau disabled, so retry


# =============================================================================
# Image Passes Critique Tests
# =============================================================================

def test_should_retry_image_passes():
    """Image passes critique → no retry."""
    policy = BoundedRegenerationPolicy()
    critique_results = [create_critique_result(passed=True, overall_score=0.85)]

    decision = policy.should_retry(
        attempt_number=1,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=5000,
        critique_results=critique_results
    )

    assert decision.should_retry is False
    assert "passed critique" in decision.reason.lower()
    assert decision.termination_reason == "passed_critique"


# =============================================================================
# Parameter Adjustment Tests (GPU)
# =============================================================================

def test_get_parameter_adjustments_gpu_attempt_1():
    """GPU attempt 1 → baseline parameters."""
    policy = BoundedRegenerationPolicy()
    failed_dims = [
        CritiqueDimension(
            dimension=DimensionType.READABILITY,
            severity=SeverityLevel.MAJOR,
            score=0.50,
            reason="Blurry",
            measurement_method="test"
        )
    ]

    adjustments = policy.get_parameter_adjustments(
        attempt_number=1,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=failed_dims
    )

    assert adjustments["cfg_scale"] == 7.5
    assert adjustments["sampling_steps"] == 50
    assert adjustments["creativity"] == 0.8
    assert "blurry" in adjustments["negative_prompt"].lower()


def test_get_parameter_adjustments_gpu_attempt_2():
    """GPU attempt 2 → first retry adjustments."""
    policy = BoundedRegenerationPolicy()
    adjustments = policy.get_parameter_adjustments(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=[]
    )

    assert adjustments["cfg_scale"] == 9.0
    assert adjustments["sampling_steps"] == 60
    assert adjustments["creativity"] == 0.65


def test_get_parameter_adjustments_gpu_attempt_3():
    """GPU attempt 3 → second retry adjustments."""
    policy = BoundedRegenerationPolicy()
    adjustments = policy.get_parameter_adjustments(
        attempt_number=3,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=[]
    )

    assert adjustments["cfg_scale"] == 10.5
    assert adjustments["sampling_steps"] == 70
    assert adjustments["creativity"] == 0.50


def test_get_parameter_adjustments_gpu_attempt_4():
    """GPU attempt 4 → third retry adjustments (maximum)."""
    policy = BoundedRegenerationPolicy()
    adjustments = policy.get_parameter_adjustments(
        attempt_number=4,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=[]
    )

    assert adjustments["cfg_scale"] == 12.0
    assert adjustments["sampling_steps"] == 80
    assert adjustments["creativity"] == 0.35


# =============================================================================
# Parameter Adjustment Tests (CPU)
# =============================================================================

def test_get_parameter_adjustments_cpu_attempt_1():
    """CPU attempt 1 → baseline parameters."""
    policy = BoundedRegenerationPolicy()
    adjustments = policy.get_parameter_adjustments(
        attempt_number=1,
        hardware_tier=HardwareTier.CPU_TIER_4,
        failed_dimensions=[]
    )

    assert adjustments["cfg_scale"] == 7.5
    assert adjustments["sampling_steps"] == 6
    assert adjustments["creativity"] == 0.8


def test_get_parameter_adjustments_cpu_attempt_2():
    """CPU attempt 2 → first retry adjustments."""
    policy = BoundedRegenerationPolicy()
    adjustments = policy.get_parameter_adjustments(
        attempt_number=2,
        hardware_tier=HardwareTier.CPU_TIER_4,
        failed_dimensions=[]
    )

    assert adjustments["cfg_scale"] == 9.0
    assert adjustments["sampling_steps"] == 8
    assert adjustments["creativity"] == 0.65


def test_get_parameter_adjustments_cpu_attempt_3():
    """CPU attempt 3 → second retry adjustments (maximum for CPU)."""
    policy = BoundedRegenerationPolicy()
    adjustments = policy.get_parameter_adjustments(
        attempt_number=3,
        hardware_tier=HardwareTier.CPU_TIER_4,
        failed_dimensions=[]
    )

    assert adjustments["cfg_scale"] == 10.5
    assert adjustments["sampling_steps"] == 10
    assert adjustments["creativity"] == 0.50


# =============================================================================
# Dimension-Specific Negative Prompts Tests
# =============================================================================

def test_negative_prompt_readability_failure():
    """Readability failure → adds blur-related negative prompts."""
    policy = BoundedRegenerationPolicy()
    failed_dims = [
        CritiqueDimension(
            dimension=DimensionType.READABILITY,
            severity=SeverityLevel.CRITICAL,
            score=0.30,
            reason="Very blurry",
            measurement_method="test"
        )
    ]

    adjustments = policy.get_parameter_adjustments(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=failed_dims
    )

    negative_prompt = adjustments["negative_prompt"].lower()
    assert "blurry" in negative_prompt
    assert "out of focus" in negative_prompt


def test_negative_prompt_composition_failure():
    """Composition failure → adds framing-related negative prompts."""
    policy = BoundedRegenerationPolicy()
    failed_dims = [
        CritiqueDimension(
            dimension=DimensionType.COMPOSITION,
            severity=SeverityLevel.MAJOR,
            score=0.50,
            reason="Off-center",
            measurement_method="test"
        )
    ]

    adjustments = policy.get_parameter_adjustments(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=failed_dims
    )

    negative_prompt = adjustments["negative_prompt"].lower()
    assert "off-center" in negative_prompt
    assert "bad framing" in negative_prompt


def test_negative_prompt_artifacting_failure():
    """Artifacting failure → adds anatomical error negative prompts."""
    policy = BoundedRegenerationPolicy()
    failed_dims = [
        CritiqueDimension(
            dimension=DimensionType.ARTIFACTING,
            severity=SeverityLevel.CRITICAL,
            score=0.25,
            reason="Malformed hands",
            measurement_method="test"
        )
    ]

    adjustments = policy.get_parameter_adjustments(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=failed_dims
    )

    negative_prompt = adjustments["negative_prompt"].lower()
    assert "malformed hands" in negative_prompt
    assert "extra fingers" in negative_prompt


def test_negative_prompt_multiple_failures():
    """Multiple dimension failures → concatenates negative prompts."""
    policy = BoundedRegenerationPolicy()
    failed_dims = [
        CritiqueDimension(
            dimension=DimensionType.READABILITY,
            severity=SeverityLevel.MAJOR,
            score=0.50,
            reason="Blurry",
            measurement_method="test"
        ),
        CritiqueDimension(
            dimension=DimensionType.COMPOSITION,
            severity=SeverityLevel.MAJOR,
            score=0.55,
            reason="Off-center",
            measurement_method="test"
        )
    ]

    adjustments = policy.get_parameter_adjustments(
        attempt_number=2,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=failed_dims
    )

    negative_prompt = adjustments["negative_prompt"].lower()
    assert "blurry" in negative_prompt
    assert "off-center" in negative_prompt


# =============================================================================
# Bad Prompt Detection Tests
# =============================================================================

def test_detect_bad_prompt_all_low_scores():
    """All attempts scored < 0.30 → bad prompt detected."""
    policy = BoundedRegenerationPolicy()
    critique_results = [
        create_critique_result(passed=False, overall_score=0.25),
        create_critique_result(passed=False, overall_score=0.28),
        create_critique_result(passed=False, overall_score=0.22)
    ]

    is_bad_prompt = policy.detect_bad_prompt(critique_results)
    assert is_bad_prompt is True


def test_detect_bad_prompt_some_acceptable_scores():
    """Some attempts scored >= 0.30 → no bad prompt."""
    policy = BoundedRegenerationPolicy()
    critique_results = [
        create_critique_result(passed=False, overall_score=0.25),
        create_critique_result(passed=False, overall_score=0.50),  # Above threshold
        create_critique_result(passed=False, overall_score=0.28)
    ]

    is_bad_prompt = policy.detect_bad_prompt(critique_results)
    assert is_bad_prompt is False


def test_detect_bad_prompt_empty_results():
    """No critique results → no bad prompt detected."""
    policy = BoundedRegenerationPolicy()
    is_bad_prompt = policy.detect_bad_prompt([])
    assert is_bad_prompt is False


# =============================================================================
# Edge Case Tests
# =============================================================================

def test_should_retry_no_critique_results():
    """No critique results yet → proceed with generation."""
    policy = BoundedRegenerationPolicy()

    decision = policy.should_retry(
        attempt_number=1,
        hardware_tier=HardwareTier.GPU_TIER_1,
        elapsed_time_ms=0,
        critique_results=[]
    )

    assert decision.should_retry is True
    assert "No critique results" in decision.reason


def test_parameter_adjustments_exceed_schedule_length():
    """Attempt number exceeds schedule → uses last schedule value."""
    policy = BoundedRegenerationPolicy()

    # GPU schedule has 4 values, but attempt 10 should clamp to index 3
    adjustments = policy.get_parameter_adjustments(
        attempt_number=10,
        hardware_tier=HardwareTier.GPU_TIER_1,
        failed_dimensions=[]
    )

    assert adjustments["cfg_scale"] == 12.0  # Last value in GPU schedule
    assert adjustments["sampling_steps"] == 80
    assert adjustments["creativity"] == 0.35
