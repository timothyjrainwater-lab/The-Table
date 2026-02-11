"""Performance profiling framework for Box→Lens→Spark pipeline.

Validates latency targets specified in the execution plan and identifies
hot paths in the AIDM system.

WO-017: Performance Profiling Suite
"""

import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from aidm.schemas.testing import ScenarioConfig
from aidm.schemas.position import Position
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.lens_index import LensIndex, SourceTier
from aidm.core.rng_manager import RNGManager
from aidm.core.los_resolver import check_los
from aidm.core.cover_resolver import calculate_cover
from aidm.core.aoe_rasterizer import AoEShape, rasterize_burst, rasterize_cone


# ==============================================================================
# LATENCY TARGET — Defines acceptable performance thresholds
# ==============================================================================

@dataclass(frozen=True)
class LatencyTarget:
    """Defines acceptable latency thresholds for an operation.

    Latency targets are specified in milliseconds for p50, p95, and p99
    percentiles. Operations must meet all targets to pass validation.
    """

    name: str
    """Name of the operation being profiled."""

    p50_ms: float
    """50th percentile latency target in milliseconds."""

    p95_ms: float
    """95th percentile latency target in milliseconds."""

    p99_ms: float
    """99th percentile latency target in milliseconds."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
        }


# ==============================================================================
# LATENCY RESULT — Captures actual performance measurements
# ==============================================================================

@dataclass
class LatencyResult:
    """Captures actual latency measurements for an operation.

    Contains raw samples, computed percentiles, and pass/fail status
    against a LatencyTarget.
    """

    name: str
    """Name of the operation profiled."""

    samples: List[float]
    """Individual timing samples in milliseconds."""

    p50_ms: float
    """Computed 50th percentile latency."""

    p95_ms: float
    """Computed 95th percentile latency."""

    p99_ms: float
    """Computed 99th percentile latency."""

    meets_target: bool
    """Whether all targets were met."""

    target: Optional[LatencyTarget] = None
    """The target this was measured against."""

    min_ms: float = 0.0
    """Minimum sample value."""

    max_ms: float = 0.0
    """Maximum sample value."""

    mean_ms: float = 0.0
    """Arithmetic mean of samples."""

    iterations: int = 0
    """Number of iterations (including warmup)."""

    warmup_iterations: int = 0
    """Number of warmup iterations discarded."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "samples_count": len(self.samples),
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "mean_ms": self.mean_ms,
            "meets_target": self.meets_target,
            "target": self.target.to_dict() if self.target else None,
            "iterations": self.iterations,
            "warmup_iterations": self.warmup_iterations,
        }


# ==============================================================================
# DEFAULT LATENCY TARGETS — From execution plan
# ==============================================================================

DEFAULT_TARGETS = {
    "box_query": LatencyTarget(
        name="box_query",
        p50_ms=20.0,
        p95_ms=50.0,
        p99_ms=100.0,
    ),
    "lens_query": LatencyTarget(
        name="lens_query",
        p50_ms=10.0,
        p95_ms=20.0,
        p99_ms=50.0,
    ),
    "action_resolution": LatencyTarget(
        name="action_resolution",
        p50_ms=1500.0,   # 1.5s p50
        p95_ms=3000.0,   # 3s p95 (execution plan target)
        p99_ms=5000.0,   # 5s p99
    ),
    "full_round": LatencyTarget(
        name="full_round",
        p50_ms=5000.0,   # 5s p50
        p95_ms=10000.0,  # 10s p95
        p99_ms=15000.0,  # 15s p99
    ),
}


# ==============================================================================
# PERCENTILE CALCULATION — Statistical utilities
# ==============================================================================

def percentile(data: List[float], p: float) -> float:
    """Compute the p-th percentile of data.

    Uses linear interpolation between data points.

    Args:
        data: List of numeric values
        p: Percentile to compute (0-100)

    Returns:
        The computed percentile value
    """
    if not data:
        return 0.0

    sorted_data = sorted(data)
    n = len(sorted_data)

    if n == 1:
        return sorted_data[0]

    # Use linear interpolation
    k = (n - 1) * (p / 100.0)
    f = int(k)
    c = f + 1

    if c >= n:
        return sorted_data[-1]

    fraction = k - f
    return sorted_data[f] * (1 - fraction) + sorted_data[c] * fraction


def compute_percentiles(samples: List[float]) -> Tuple[float, float, float]:
    """Compute p50, p95, and p99 percentiles.

    Args:
        samples: List of timing samples

    Returns:
        Tuple of (p50, p95, p99)
    """
    if not samples:
        return 0.0, 0.0, 0.0

    return (
        percentile(samples, 50),
        percentile(samples, 95),
        percentile(samples, 99),
    )


# ==============================================================================
# PERFORMANCE PROFILER — Main profiling system
# ==============================================================================

class PerformanceProfiler:
    """Profiles specific operations and validates against latency targets.

    Uses time.perf_counter_ns() for high-precision timing. Supports
    warm-up iterations to avoid cold-start effects and statistical
    analysis of results.
    """

    def __init__(
        self,
        targets: Optional[Dict[str, LatencyTarget]] = None,
        warmup_iterations: int = 3,
    ):
        """Initialize the profiler.

        Args:
            targets: Custom latency targets (defaults to DEFAULT_TARGETS)
            warmup_iterations: Number of warmup runs to discard
        """
        self._targets = targets or DEFAULT_TARGETS.copy()
        self._warmup_iterations = warmup_iterations
        self._results: List[LatencyResult] = []

    def get_target(self, name: str) -> Optional[LatencyTarget]:
        """Get a latency target by name.

        Args:
            name: Target name

        Returns:
            LatencyTarget or None
        """
        return self._targets.get(name)

    def add_target(self, target: LatencyTarget) -> None:
        """Add or update a latency target.

        Args:
            target: Target to add
        """
        self._targets[target.name] = target

    def clear_results(self) -> None:
        """Clear all profiling results."""
        self._results.clear()

    def get_results(self) -> List[LatencyResult]:
        """Get all profiling results.

        Returns:
            List of LatencyResult
        """
        return list(self._results)

    # ==========================================================================
    # LOW-LEVEL TIMING
    # ==========================================================================

    def _time_operation(
        self,
        operation: Callable[[], Any],
        iterations: int,
        warmup: Optional[int] = None,
    ) -> List[float]:
        """Time an operation over multiple iterations.

        Args:
            operation: Callable to time
            iterations: Number of timed iterations
            warmup: Number of warmup iterations (uses default if None)

        Returns:
            List of timing samples in milliseconds
        """
        if warmup is None:
            warmup = self._warmup_iterations

        # Warmup runs (discarded)
        for _ in range(warmup):
            operation()

        # Timed runs
        samples = []
        for _ in range(iterations):
            start = time.perf_counter_ns()
            operation()
            end = time.perf_counter_ns()
            samples.append((end - start) / 1_000_000)  # Convert to ms

        return samples

    def _create_result(
        self,
        name: str,
        samples: List[float],
        iterations: int,
        warmup: int,
    ) -> LatencyResult:
        """Create a LatencyResult from samples.

        Args:
            name: Operation name
            samples: Timing samples
            iterations: Total iterations
            warmup: Warmup iterations

        Returns:
            LatencyResult
        """
        p50, p95, p99 = compute_percentiles(samples)
        target = self._targets.get(name)

        meets_target = True
        if target:
            meets_target = (
                p50 <= target.p50_ms and
                p95 <= target.p95_ms and
                p99 <= target.p99_ms
            )

        result = LatencyResult(
            name=name,
            samples=samples,
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=p99,
            meets_target=meets_target,
            target=target,
            min_ms=min(samples) if samples else 0.0,
            max_ms=max(samples) if samples else 0.0,
            mean_ms=statistics.mean(samples) if samples else 0.0,
            iterations=iterations + warmup,
            warmup_iterations=warmup,
        )

        self._results.append(result)
        return result

    # ==========================================================================
    # BOX QUERY PROFILING
    # ==========================================================================

    def profile_box_query(
        self,
        grid: BattleGrid,
        iterations: int = 100,
    ) -> LatencyResult:
        """Profile Box layer query operations.

        Tests a mix of common Box operations:
        - Cell access (get_cell)
        - LOS checks
        - Cover calculations
        - AoE rasterization

        Args:
            grid: BattleGrid to test against
            iterations: Number of iterations

        Returns:
            LatencyResult for box_query
        """
        # Setup test positions
        center = Position(x=grid.width // 2, y=grid.height // 2)
        corner = Position(x=0, y=0)
        far_corner = Position(x=grid.width - 1, y=grid.height - 1)

        # Place some entities for realistic queries
        grid.place_entity("test_entity_1", center, SizeCategory.MEDIUM)
        grid.place_entity("test_entity_2", corner, SizeCategory.MEDIUM)

        def box_operation():
            # Cell access (multiple)
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    pos = Position(x=center.x + dx, y=center.y + dy)
                    if grid.in_bounds(pos):
                        grid.get_cell(pos)

            # LOS check
            check_los(grid, corner, 5, far_corner, 5)

            # Cover calculation
            calculate_cover(corner, center, grid)

            # AoE rasterization
            rasterize_burst(center, 20)

        samples = self._time_operation(box_operation, iterations)

        # Cleanup
        grid.remove_entity("test_entity_1")
        grid.remove_entity("test_entity_2")

        return self._create_result(
            "box_query",
            samples,
            iterations,
            self._warmup_iterations,
        )

    # ==========================================================================
    # LENS QUERY PROFILING
    # ==========================================================================

    def profile_lens_query(
        self,
        lens: LensIndex,
        iterations: int = 100,
    ) -> LatencyResult:
        """Profile Lens layer query operations.

        Tests a mix of common Lens operations:
        - Entity registration
        - Fact setting/getting
        - Spatial queries
        - Authority resolution

        Args:
            lens: LensIndex to test against
            iterations: Number of iterations

        Returns:
            LatencyResult for lens_query
        """
        # Setup test entities
        test_entities = []
        for i in range(10):
            entity_id = f"lens_test_{i}"
            test_entities.append(entity_id)
            lens.register_entity(entity_id, "creature", turn=0)
            lens.set_position(entity_id, Position(x=i * 2, y=i * 2), turn=0)
            lens.set_fact(entity_id, "hp", 50, SourceTier.BOX, turn=0)
            lens.set_fact(entity_id, "ac", 15, SourceTier.BOX, turn=0)

        center = Position(x=10, y=10)

        def lens_operation():
            # Entity lookups
            for eid in test_entities[:5]:
                lens.get_entity(eid)

            # Fact queries
            for eid in test_entities[:5]:
                lens.get_fact(eid, "hp")
                lens.get_fact(eid, "ac")

            # Spatial queries
            lens.get_entities_in_radius(center, 50)
            lens.get_entities_at(Position(x=4, y=4))

            # Authority resolution checks
            for eid in test_entities[:3]:
                lens.resolve_conflict(eid, "hp", 40, SourceTier.SPARK, turn=1)

        samples = self._time_operation(lens_operation, iterations)

        # Cleanup
        for eid in test_entities:
            lens.remove_entity(eid)

        return self._create_result(
            "lens_query",
            samples,
            iterations,
            self._warmup_iterations,
        )

    # ==========================================================================
    # ACTION RESOLUTION PROFILING
    # ==========================================================================

    def profile_action_resolution(
        self,
        scenario: ScenarioConfig,
        iterations: int = 20,
    ) -> LatencyResult:
        """Profile a single combat action resolution.

        Runs a single turn with AI-selected action and measures time.

        Args:
            scenario: ScenarioConfig to use
            iterations: Number of iterations

        Returns:
            LatencyResult for action_resolution
        """
        from aidm.testing.scenario_runner import ScenarioRunner, SimpleAIPolicy
        from aidm.schemas.attack import AttackIntent, Weapon
        from aidm.schemas.entity_fields import EF
        from aidm.core.play_loop import execute_turn, TurnContext

        samples = []

        # Need fresh runner for each iteration to get consistent state
        for _ in range(self._warmup_iterations + iterations):
            runner = ScenarioRunner()
            runner._initialize_scenario(scenario)

            # Get first actor
            world_state = runner._world_state
            if world_state.active_combat is None:
                samples.append(0.0)
                continue

            init_order = world_state.active_combat.get("initiative_order", [])
            if not init_order:
                samples.append(0.0)
                continue

            actor_id = init_order[0]
            entity = world_state.entities.get(actor_id)
            if entity is None:
                samples.append(0.0)
                continue

            actor_team = entity.get(EF.TEAM, "unknown")
            target_id = SimpleAIPolicy.select_target(actor_id, actor_team, world_state)

            if target_id is None:
                samples.append(0.0)
                continue

            # Build attack intent
            attacks = entity.get("attacks", [])
            if attacks:
                attack_config = attacks[0]
                weapon = Weapon(
                    damage_dice=attack_config.get("damage_dice", "1d6"),
                    damage_bonus=attack_config.get("damage_bonus", 0),
                    damage_type=attack_config.get("damage_type", "slashing"),
                )
                attack_bonus = attack_config.get("attack_bonus", 0)
            else:
                weapon = Weapon(
                    damage_dice="1d3",
                    damage_bonus=entity.get(EF.STR_MOD, 0),
                    damage_type="bludgeoning",
                )
                attack_bonus = entity.get(EF.BAB, 0) + entity.get(EF.STR_MOD, 0)

            intent = AttackIntent(
                attacker_id=actor_id,
                target_id=target_id,
                attack_bonus=attack_bonus,
                weapon=weapon,
            )

            turn_ctx = TurnContext(
                turn_index=0,
                actor_id=actor_id,
                actor_team=actor_team,
            )

            # Time the action
            start = time.perf_counter_ns()
            execute_turn(
                world_state=world_state,
                turn_ctx=turn_ctx,
                combat_intent=intent,
                rng=runner._rng,
                next_event_id=0,
                timestamp=0.0,
            )
            end = time.perf_counter_ns()

            samples.append((end - start) / 1_000_000)

        # Discard warmup
        measured_samples = samples[self._warmup_iterations:]

        return self._create_result(
            "action_resolution",
            measured_samples,
            iterations,
            self._warmup_iterations,
        )

    # ==========================================================================
    # FULL ROUND PROFILING
    # ==========================================================================

    def profile_full_round(
        self,
        scenario: ScenarioConfig,
        iterations: int = 10,
    ) -> LatencyResult:
        """Profile a full combat round.

        Runs one complete combat round with all actors taking turns.

        Args:
            scenario: ScenarioConfig to use
            iterations: Number of iterations

        Returns:
            LatencyResult for full_round
        """
        from aidm.testing.scenario_runner import ScenarioRunner

        samples = []

        for _ in range(self._warmup_iterations + iterations):
            runner = ScenarioRunner()
            runner._initialize_scenario(scenario)

            # Time single round execution
            start = time.perf_counter_ns()
            runner._execute_round(1)
            end = time.perf_counter_ns()

            samples.append((end - start) / 1_000_000)

        # Discard warmup
        measured_samples = samples[self._warmup_iterations:]

        return self._create_result(
            "full_round",
            measured_samples,
            iterations,
            self._warmup_iterations,
        )

    # ==========================================================================
    # CUSTOM OPERATION PROFILING
    # ==========================================================================

    def profile_custom(
        self,
        name: str,
        operation: Callable[[], Any],
        iterations: int = 100,
        target: Optional[LatencyTarget] = None,
    ) -> LatencyResult:
        """Profile a custom operation.

        Args:
            name: Name for this profile
            operation: Callable to profile
            iterations: Number of iterations
            target: Optional custom target (will be added to targets)

        Returns:
            LatencyResult
        """
        if target:
            self._targets[name] = target

        samples = self._time_operation(operation, iterations)

        return self._create_result(
            name,
            samples,
            iterations,
            self._warmup_iterations,
        )

    # ==========================================================================
    # REPORT GENERATION
    # ==========================================================================

    def generate_report(self, results: Optional[List[LatencyResult]] = None) -> str:
        """Generate a human-readable performance report.

        Args:
            results: Results to report (uses stored results if None)

        Returns:
            Formatted report string
        """
        if results is None:
            results = self._results

        lines = []
        lines.append("=" * 72)
        lines.append("PERFORMANCE PROFILING REPORT")
        lines.append("=" * 72)
        lines.append("")

        all_pass = True
        for result in results:
            all_pass = all_pass and result.meets_target

        status = "PASS" if all_pass else "FAIL"
        lines.append(f"Overall Status: {status}")
        lines.append(f"Operations Profiled: {len(results)}")
        lines.append("")

        for result in results:
            lines.append("-" * 72)
            lines.append(f"Operation: {result.name}")
            lines.append("-" * 72)

            status_marker = "[PASS]" if result.meets_target else "[FAIL]"
            lines.append(f"Status: {status_marker}")
            lines.append(f"Iterations: {result.iterations} (warmup: {result.warmup_iterations})")
            lines.append("")

            # Actual measurements
            lines.append("Measured Latencies (ms):")
            lines.append(f"  p50:  {result.p50_ms:8.3f}")
            lines.append(f"  p95:  {result.p95_ms:8.3f}")
            lines.append(f"  p99:  {result.p99_ms:8.3f}")
            lines.append(f"  min:  {result.min_ms:8.3f}")
            lines.append(f"  max:  {result.max_ms:8.3f}")
            lines.append(f"  mean: {result.mean_ms:8.3f}")
            lines.append("")

            # Targets
            if result.target:
                lines.append("Target Latencies (ms):")
                lines.append(f"  p50:  {result.target.p50_ms:8.3f}  {'OK' if result.p50_ms <= result.target.p50_ms else 'EXCEEDED'}")
                lines.append(f"  p95:  {result.target.p95_ms:8.3f}  {'OK' if result.p95_ms <= result.target.p95_ms else 'EXCEEDED'}")
                lines.append(f"  p99:  {result.target.p99_ms:8.3f}  {'OK' if result.p99_ms <= result.target.p99_ms else 'EXCEEDED'}")
            else:
                lines.append("No target defined for this operation.")

            lines.append("")

        lines.append("=" * 72)
        lines.append(f"END OF REPORT")
        lines.append("=" * 72)

        return "\n".join(lines)


# ==============================================================================
# CONVENIENCE FACTORY
# ==============================================================================

def create_profiler(
    warmup_iterations: int = 3,
    custom_targets: Optional[Dict[str, LatencyTarget]] = None,
) -> PerformanceProfiler:
    """Factory function to create a PerformanceProfiler.

    Args:
        warmup_iterations: Number of warmup runs
        custom_targets: Custom latency targets (merged with defaults)

    Returns:
        Configured PerformanceProfiler
    """
    targets = DEFAULT_TARGETS.copy()
    if custom_targets:
        targets.update(custom_targets)

    return PerformanceProfiler(
        targets=targets,
        warmup_iterations=warmup_iterations,
    )


# ==============================================================================
# QUICK PROFILE FUNCTIONS
# ==============================================================================

def quick_profile_box(grid: BattleGrid, iterations: int = 50) -> LatencyResult:
    """Quick Box query profile with defaults.

    Args:
        grid: BattleGrid to test
        iterations: Number of iterations

    Returns:
        LatencyResult
    """
    profiler = create_profiler()
    return profiler.profile_box_query(grid, iterations)


def quick_profile_lens(lens: LensIndex, iterations: int = 50) -> LatencyResult:
    """Quick Lens query profile with defaults.

    Args:
        lens: LensIndex to test
        iterations: Number of iterations

    Returns:
        LatencyResult
    """
    profiler = create_profiler()
    return profiler.profile_lens_query(lens, iterations)


def quick_profile_scenario(
    scenario: ScenarioConfig,
    profile_type: str = "full_round",
    iterations: int = 5,
) -> LatencyResult:
    """Quick scenario profile with defaults.

    Args:
        scenario: ScenarioConfig to test
        profile_type: "action_resolution" or "full_round"
        iterations: Number of iterations

    Returns:
        LatencyResult
    """
    profiler = create_profiler()

    if profile_type == "action_resolution":
        return profiler.profile_action_resolution(scenario, iterations)
    else:
        return profiler.profile_full_round(scenario, iterations)
