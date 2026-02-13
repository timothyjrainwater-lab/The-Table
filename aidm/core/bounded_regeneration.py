"""Bounded Regeneration Policy for automated image generation retries.

M3 IMPLEMENTATION: BoundedRegenerationPolicy
---------------------------------------------
Controls retry logic when image generation fails quality checks.
Implements parameter adjustment strategies, convergence detection, and resource budgets.

Based on approved design: docs/design/BOUNDED_REGENERATION_POLICY.md

Architecture:
    - GPU path: 4 max attempts (1 original + 3 retries), 60s budget
    - CPU path: 3 max attempts (1 original + 2 retries), 120s budget
    - Backoff: Systematic parameter progression (CFG, steps, creativity)
    - Convergence: Plateau detection (stop if scores don't improve)
    - Dimension-specific negative prompt additions
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from aidm.schemas.image_critique import (
    CritiqueResult,
    DimensionType,
    SeverityLevel,
)


class HardwareTier(str, Enum):
    """Hardware tier classification for regeneration budgets.

    Based on docs/design/BOUNDED_REGENERATION_POLICY.md § 2.1-2.2
    """
    GPU_TIER_1 = "gpu_tier_1"  # High-end GPU (RTX 3060+)
    GPU_TIER_2 = "gpu_tier_2"  # Mid-range GPU (RTX 2060, GTX 1660 Ti)
    CPU_TIER_4 = "cpu_tier_4"  # CPU-only (no discrete GPU)
    CPU_TIER_5 = "cpu_tier_5"  # CPU-only (low-end)


@dataclass
class RegenerationDecision:
    """Decision outcome from regeneration policy.

    Attributes:
        should_retry: Whether to retry generation
        reason: Human-readable reason for decision
        parameter_adjustments: Suggested parameter changes for next attempt
        termination_reason: Why regeneration terminated (if should_retry=False)
    """
    should_retry: bool
    reason: str
    parameter_adjustments: Optional[Dict[str, Any]] = None
    termination_reason: Optional[str] = None


class BoundedRegenerationPolicy:
    """Policy for bounded image regeneration with parameter adjustments.

    Implements systematic retry logic with:
    - Hardware-specific attempt limits (GPU: 4, CPU: 3)
    - Time budget enforcement (GPU: 60s, CPU: 120s)
    - Convergence detection (plateau in scores)
    - Dimension-specific parameter adjustments
    - Negative prompt additions based on failed dimensions

    Based on approved design: docs/design/BOUNDED_REGENERATION_POLICY.md

    Attributes:
        max_attempts_gpu: Maximum attempts for GPU path (default: 4)
        max_attempts_cpu: Maximum attempts for CPU path (default: 3)
        time_budget_gpu_ms: Time budget for GPU in milliseconds (default: 60000)
        time_budget_cpu_ms: Time budget for CPU in milliseconds (default: 120000)
        plateau_threshold: Score delta threshold for plateau detection (default: 0.02)
        enable_plateau_detection: Whether to enable early termination on plateau (default: True)
    """

    # Parameter adjustment schedules (from design spec § 3)
    CFG_SCALE_SCHEDULE_GPU = [7.5, 9.0, 10.5, 12.0]  # Original, Retry 1, 2, 3
    STEPS_SCHEDULE_GPU = [50, 60, 70, 80]
    CREATIVITY_SCHEDULE = [0.8, 0.65, 0.50, 0.35]

    CFG_SCALE_SCHEDULE_CPU = [7.5, 9.0, 10.5]  # Original, Retry 1, 2
    STEPS_SCHEDULE_CPU = [6, 8, 10]

    # Dimension-specific negative prompts (from design spec § 3.4)
    NEGATIVE_PROMPTS = {
        DimensionType.READABILITY: "blurry, out of focus, low contrast, muddy colors, washed out, faded",
        DimensionType.COMPOSITION: "off-center, cropped face, bad framing, excessive headroom, poor composition",
        DimensionType.ARTIFACTING: "malformed hands, extra fingers, asymmetric face, anatomical errors, distorted limbs, deformed",
        DimensionType.STYLE_ADHERENCE: "inconsistent style, wrong genre, mismatched aesthetic, modern elements, anachronistic",
        DimensionType.IDENTITY_MATCH: "different person, wrong species, incorrect features, altered appearance",
    }

    def __init__(
        self,
        max_attempts_gpu: int = 4,
        max_attempts_cpu: int = 3,
        time_budget_gpu_ms: int = 60_000,
        time_budget_cpu_ms: int = 120_000,
        plateau_threshold: float = 0.02,
        enable_plateau_detection: bool = True
    ):
        """Initialize bounded regeneration policy.

        Args:
            max_attempts_gpu: Maximum regeneration attempts for GPU path
            max_attempts_cpu: Maximum regeneration attempts for CPU path
            time_budget_gpu_ms: Time budget for GPU in milliseconds
            time_budget_cpu_ms: Time budget for CPU in milliseconds
            plateau_threshold: Score delta threshold for plateau detection
            enable_plateau_detection: Whether to enable early termination on plateau
        """
        self.max_attempts_gpu = max_attempts_gpu
        self.max_attempts_cpu = max_attempts_cpu
        self.time_budget_gpu_ms = time_budget_gpu_ms
        self.time_budget_cpu_ms = time_budget_cpu_ms
        self.plateau_threshold = plateau_threshold
        self.enable_plateau_detection = enable_plateau_detection

    def should_retry(
        self,
        attempt_number: int,
        hardware_tier: HardwareTier,
        elapsed_time_ms: int,
        critique_results: List[CritiqueResult]
    ) -> RegenerationDecision:
        """Determine whether to retry generation.

        Checks:
        1. Max attempts exhausted?
        2. Time budget exceeded?
        3. Convergence/plateau detected?
        4. Image passed critique?

        Args:
            attempt_number: Current attempt number (1-based)
            hardware_tier: Hardware tier (GPU or CPU)
            elapsed_time_ms: Total elapsed time in milliseconds
            critique_results: List of critique results from all attempts so far

        Returns:
            RegenerationDecision with should_retry flag and parameter adjustments
        """
        # Determine max attempts for this hardware tier
        is_gpu = hardware_tier in [HardwareTier.GPU_TIER_1, HardwareTier.GPU_TIER_2]
        max_attempts = self.max_attempts_gpu if is_gpu else self.max_attempts_cpu
        time_budget_ms = self.time_budget_gpu_ms if is_gpu else self.time_budget_cpu_ms

        # Check 1: Max attempts exhausted
        if attempt_number >= max_attempts:
            return RegenerationDecision(
                should_retry=False,
                reason=f"Maximum attempts ({max_attempts}) exhausted",
                termination_reason="max_attempts_exhausted"
            )

        # Check 2: Time budget exceeded
        if elapsed_time_ms >= time_budget_ms:
            return RegenerationDecision(
                should_retry=False,
                reason=f"Time budget ({time_budget_ms}ms) exceeded (elapsed: {elapsed_time_ms}ms)",
                termination_reason="time_budget_exceeded"
            )

        # Get latest critique result
        if not critique_results:
            # No critique yet, proceed with generation
            return RegenerationDecision(
                should_retry=True,
                reason="No critique results yet, proceeding with generation",
                parameter_adjustments=None
            )

        latest_result = critique_results[-1]

        # Check 3: Image passed critique
        if latest_result.passed:
            return RegenerationDecision(
                should_retry=False,
                reason=f"Image passed critique (score: {latest_result.overall_score:.2f})",
                termination_reason="passed_critique"
            )

        # Check 4: Plateau detection (if enabled and we have multiple attempts)
        if self.enable_plateau_detection and len(critique_results) >= 2:
            if self._detect_plateau(critique_results):
                return RegenerationDecision(
                    should_retry=False,
                    reason=f"Score plateau detected (no improvement in last 2 attempts)",
                    termination_reason="plateau_detected"
                )

        # Retry with adjusted parameters
        parameter_adjustments = self.get_parameter_adjustments(
            attempt_number=attempt_number,
            hardware_tier=hardware_tier,
            failed_dimensions=[d for d in latest_result.dimensions if d.severity in [SeverityLevel.CRITICAL, SeverityLevel.MAJOR]]
        )

        return RegenerationDecision(
            should_retry=True,
            reason=f"Retrying with adjusted parameters (attempt {attempt_number + 1}/{max_attempts})",
            parameter_adjustments=parameter_adjustments
        )

    def get_parameter_adjustments(
        self,
        attempt_number: int,
        hardware_tier: HardwareTier,
        failed_dimensions: List[Any]
    ) -> Dict[str, Any]:
        """Get parameter adjustments for next retry attempt.

        Implements backoff strategy from design spec § 3-4.

        Args:
            attempt_number: Current attempt number (1-based)
            hardware_tier: Hardware tier (GPU or CPU)
            failed_dimensions: List of CritiqueDimension objects that failed

        Returns:
            Dict with parameter adjustments (cfg_scale, sampling_steps, creativity, negative_prompt)
        """
        is_gpu = hardware_tier in [HardwareTier.GPU_TIER_1, HardwareTier.GPU_TIER_2]

        # Get schedules based on hardware
        if is_gpu:
            cfg_schedule = self.CFG_SCALE_SCHEDULE_GPU
            steps_schedule = self.STEPS_SCHEDULE_GPU
        else:
            cfg_schedule = self.CFG_SCALE_SCHEDULE_CPU
            steps_schedule = self.STEPS_SCHEDULE_CPU

        # Convert attempt_number (1-based) to index (0-based)
        # Attempt 1 = index 0, Attempt 2 = index 1, etc.
        idx = min(attempt_number - 1, len(cfg_schedule) - 1)

        adjustments = {
            "cfg_scale": cfg_schedule[idx],
            "sampling_steps": steps_schedule[idx],
            "creativity": self.CREATIVITY_SCHEDULE[idx],
            "seed": None,  # Random seed (new seed per retry)
        }

        # Build negative prompt from failed dimensions
        negative_prompt_parts = []
        for dim in failed_dimensions:
            if hasattr(dim, 'dimension') and dim.dimension in self.NEGATIVE_PROMPTS:
                negative_prompt_parts.append(self.NEGATIVE_PROMPTS[dim.dimension])

        adjustments["negative_prompt"] = ", ".join(negative_prompt_parts) if negative_prompt_parts else ""

        return adjustments

    def _detect_plateau(self, critique_results: List[CritiqueResult]) -> bool:
        """Detect if scores have plateaued (no improvement).

        Plateau definition (from design spec § 5.2):
        - Score does NOT improve for 2 consecutive attempts
        - Delta < plateau_threshold (default: 0.02)

        Args:
            critique_results: List of critique results from all attempts

        Returns:
            True if plateau detected, False otherwise
        """
        if len(critique_results) < 2:
            return False

        # Get last two scores
        score_current = critique_results[-1].overall_score
        score_previous = critique_results[-2].overall_score

        # Plateau if current score <= previous score OR delta < threshold
        delta = score_current - score_previous

        return delta <= self.plateau_threshold

    def detect_bad_prompt(self, critique_results: List[CritiqueResult]) -> bool:
        """Detect if prompt is likely malformed or contradictory.

        Heuristic (from design spec § 7.1):
        - All attempts scored < 0.30 (suggests prompt issue, not generation issue)

        Args:
            critique_results: List of critique results from all attempts

        Returns:
            True if bad prompt detected, False otherwise
        """
        if not critique_results:
            return False

        # Check if all attempts scored < 0.30
        return all(result.overall_score < 0.30 for result in critique_results)

    def calculate_time_remaining(
        self,
        hardware_tier: HardwareTier,
        elapsed_time_ms: int
    ) -> int:
        """Calculate remaining time budget in milliseconds.

        Args:
            hardware_tier: Hardware tier (GPU or CPU)
            elapsed_time_ms: Total elapsed time in milliseconds

        Returns:
            Remaining time in milliseconds (0 if budget exceeded)
        """
        is_gpu = hardware_tier in [HardwareTier.GPU_TIER_1, HardwareTier.GPU_TIER_2]
        time_budget_ms = self.time_budget_gpu_ms if is_gpu else self.time_budget_cpu_ms

        remaining = time_budget_ms - elapsed_time_ms
        return max(0, remaining)
