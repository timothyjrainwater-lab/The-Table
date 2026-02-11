"""Integration tests for performance profiling framework.

Validates execution plan latency targets:
- Box query <50ms p95
- Lens query <20ms p95
- Full action resolution <3s p95

Uses pre-configured scenarios from WO-016 fixtures.

WO-017: Performance Profiling Suite
"""

import pytest
from typing import List

from aidm.schemas.testing import ScenarioConfig
from aidm.schemas.position import Position
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.lens_index import LensIndex, SourceTier
from aidm.testing.performance_profiler import (
    PerformanceProfiler,
    LatencyTarget,
    LatencyResult,
    DEFAULT_TARGETS,
    create_profiler,
    quick_profile_box,
    quick_profile_lens,
    quick_profile_scenario,
    percentile,
    compute_percentiles,
)


# ==============================================================================
# TEST MARKERS
# ==============================================================================

pytestmark = pytest.mark.performance


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def profiler() -> PerformanceProfiler:
    """Create a fresh profiler with default targets."""
    return create_profiler(warmup_iterations=2)


@pytest.fixture
def small_grid() -> BattleGrid:
    """Create a small 20x20 grid for fast tests."""
    return BattleGrid(20, 20)


@pytest.fixture
def medium_grid() -> BattleGrid:
    """Create a medium 50x50 grid for realistic tests."""
    return BattleGrid(50, 50)


@pytest.fixture
def large_grid() -> BattleGrid:
    """Create a large 100x100 grid for stress tests."""
    return BattleGrid(100, 100)


@pytest.fixture
def populated_lens() -> LensIndex:
    """Create a LensIndex with some entities for realistic queries."""
    lens = LensIndex()

    for i in range(20):
        entity_id = f"entity_{i:02d}"
        lens.register_entity(entity_id, "creature", turn=0)
        lens.set_position(entity_id, Position(x=i * 2, y=i * 2), turn=0)
        lens.set_fact(entity_id, "hp", 50 + i, SourceTier.BOX, turn=0)
        lens.set_fact(entity_id, "ac", 12 + (i % 5), SourceTier.BOX, turn=0)
        lens.set_fact(entity_id, "name", f"Test Entity {i}", SourceTier.PLAYER, turn=0)

    return lens


# ==============================================================================
# TESTS: Percentile Calculation
# ==============================================================================

class TestPercentileCalculation:
    """Test statistical utilities."""

    def test_percentile_empty_list(self):
        """Empty list returns 0."""
        assert percentile([], 50) == 0.0

    def test_percentile_single_value(self):
        """Single value returns that value for all percentiles."""
        assert percentile([42.0], 0) == 42.0
        assert percentile([42.0], 50) == 42.0
        assert percentile([42.0], 100) == 42.0

    def test_percentile_p50_odd_count(self):
        """P50 of odd-count list is the median."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert percentile(data, 50) == 3.0

    def test_percentile_p50_even_count(self):
        """P50 of even-count list interpolates."""
        data = [1.0, 2.0, 3.0, 4.0]
        result = percentile(data, 50)
        assert 2.0 <= result <= 3.0

    def test_percentile_p95(self):
        """P95 is near top of range."""
        data = list(range(1, 101))  # 1-100
        p95 = percentile([float(x) for x in data], 95)
        assert 94.0 <= p95 <= 96.0

    def test_compute_percentiles(self):
        """compute_percentiles returns all three percentiles."""
        data = list(range(1, 101))
        data_float = [float(x) for x in data]
        p50, p95, p99 = compute_percentiles(data_float)

        assert 49.0 <= p50 <= 51.0
        assert 94.0 <= p95 <= 96.0
        assert 98.0 <= p99 <= 100.0

    def test_compute_percentiles_empty(self):
        """Empty list returns zeros."""
        p50, p95, p99 = compute_percentiles([])
        assert p50 == 0.0
        assert p95 == 0.0
        assert p99 == 0.0


# ==============================================================================
# TESTS: LatencyTarget
# ==============================================================================

class TestLatencyTarget:
    """Test LatencyTarget dataclass."""

    def test_create_target(self):
        """Can create a latency target."""
        target = LatencyTarget(
            name="test_op",
            p50_ms=10.0,
            p95_ms=50.0,
            p99_ms=100.0,
        )
        assert target.name == "test_op"
        assert target.p50_ms == 10.0
        assert target.p95_ms == 50.0
        assert target.p99_ms == 100.0

    def test_target_is_frozen(self):
        """LatencyTarget is immutable."""
        target = LatencyTarget(
            name="frozen_test",
            p50_ms=10.0,
            p95_ms=50.0,
            p99_ms=100.0,
        )
        with pytest.raises(AttributeError):
            target.p50_ms = 20.0

    def test_target_to_dict(self):
        """LatencyTarget serializes to dict."""
        target = LatencyTarget(
            name="serialize_test",
            p50_ms=10.0,
            p95_ms=50.0,
            p99_ms=100.0,
        )
        d = target.to_dict()
        assert d["name"] == "serialize_test"
        assert d["p50_ms"] == 10.0


# ==============================================================================
# TESTS: Default Targets
# ==============================================================================

class TestDefaultTargets:
    """Test that default targets are properly defined."""

    def test_box_query_target_exists(self):
        """box_query target is defined."""
        assert "box_query" in DEFAULT_TARGETS
        assert DEFAULT_TARGETS["box_query"].p95_ms == 50.0

    def test_lens_query_target_exists(self):
        """lens_query target is defined."""
        assert "lens_query" in DEFAULT_TARGETS
        assert DEFAULT_TARGETS["lens_query"].p95_ms == 20.0

    def test_action_resolution_target_exists(self):
        """action_resolution target is defined."""
        assert "action_resolution" in DEFAULT_TARGETS
        assert DEFAULT_TARGETS["action_resolution"].p95_ms == 3000.0

    def test_full_round_target_exists(self):
        """full_round target is defined."""
        assert "full_round" in DEFAULT_TARGETS


# ==============================================================================
# TESTS: PerformanceProfiler Basic
# ==============================================================================

class TestPerformanceProfilerBasic:
    """Test basic profiler functionality."""

    def test_create_profiler_default(self):
        """Can create profiler with defaults."""
        profiler = create_profiler()
        assert profiler is not None
        assert profiler.get_target("box_query") is not None

    def test_create_profiler_custom_warmup(self):
        """Can create profiler with custom warmup."""
        profiler = create_profiler(warmup_iterations=5)
        assert profiler._warmup_iterations == 5

    def test_add_custom_target(self, profiler: PerformanceProfiler):
        """Can add custom targets."""
        custom = LatencyTarget(
            name="custom_op",
            p50_ms=5.0,
            p95_ms=10.0,
            p99_ms=20.0,
        )
        profiler.add_target(custom)
        assert profiler.get_target("custom_op") == custom

    def test_clear_results(self, profiler: PerformanceProfiler, small_grid: BattleGrid):
        """Can clear profiling results."""
        profiler.profile_box_query(small_grid, iterations=5)
        assert len(profiler.get_results()) == 1

        profiler.clear_results()
        assert len(profiler.get_results()) == 0


# ==============================================================================
# TESTS: Box Query Profiling
# ==============================================================================

class TestBoxQueryProfiling:
    """Test Box layer profiling."""

    def test_profile_box_query_runs(self, profiler: PerformanceProfiler, small_grid: BattleGrid):
        """Box query profiling runs successfully."""
        result = profiler.profile_box_query(small_grid, iterations=10)

        assert result.name == "box_query"
        assert len(result.samples) == 10
        assert result.p50_ms > 0
        assert result.p95_ms >= result.p50_ms
        assert result.p99_ms >= result.p95_ms

    def test_box_query_result_stored(self, profiler: PerformanceProfiler, small_grid: BattleGrid):
        """Box query result is stored in profiler."""
        profiler.profile_box_query(small_grid, iterations=5)
        results = profiler.get_results()
        assert len(results) == 1
        assert results[0].name == "box_query"

    def test_box_query_meets_target_small_grid(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """Box query meets p95 < 50ms target on small grid."""
        result = profiler.profile_box_query(small_grid, iterations=20)

        # Should easily meet target on small grid
        assert result.p95_ms < 50.0, f"p95 was {result.p95_ms}ms, target is 50ms"

    def test_box_query_meets_target_medium_grid(
        self,
        profiler: PerformanceProfiler,
        medium_grid: BattleGrid,
    ):
        """Box query meets p95 < 50ms target on medium grid."""
        result = profiler.profile_box_query(medium_grid, iterations=20)

        assert result.p95_ms < 50.0, f"p95 was {result.p95_ms}ms, target is 50ms"

    def test_quick_profile_box(self, small_grid: BattleGrid):
        """quick_profile_box convenience function works."""
        result = quick_profile_box(small_grid, iterations=10)
        assert result.name == "box_query"
        assert len(result.samples) == 10


# ==============================================================================
# TESTS: Lens Query Profiling
# ==============================================================================

class TestLensQueryProfiling:
    """Test Lens layer profiling."""

    def test_profile_lens_query_runs(
        self,
        profiler: PerformanceProfiler,
        populated_lens: LensIndex,
    ):
        """Lens query profiling runs successfully."""
        result = profiler.profile_lens_query(populated_lens, iterations=10)

        assert result.name == "lens_query"
        assert len(result.samples) == 10
        assert result.p50_ms > 0

    def test_lens_query_meets_target(
        self,
        profiler: PerformanceProfiler,
        populated_lens: LensIndex,
    ):
        """Lens query meets p95 < 20ms target."""
        result = profiler.profile_lens_query(populated_lens, iterations=30)

        assert result.p95_ms < 20.0, f"p95 was {result.p95_ms}ms, target is 20ms"

    def test_quick_profile_lens(self, populated_lens: LensIndex):
        """quick_profile_lens convenience function works."""
        result = quick_profile_lens(populated_lens, iterations=10)
        assert result.name == "lens_query"


# ==============================================================================
# TESTS: Action Resolution Profiling
# ==============================================================================

class TestActionResolutionProfiling:
    """Test action resolution profiling."""

    def test_profile_action_resolution_runs(
        self,
        profiler: PerformanceProfiler,
        tavern_scenario: ScenarioConfig,
    ):
        """Action resolution profiling runs successfully."""
        result = profiler.profile_action_resolution(tavern_scenario, iterations=3)

        assert result.name == "action_resolution"
        assert len(result.samples) == 3

    def test_action_resolution_meets_target_tavern(
        self,
        profiler: PerformanceProfiler,
        tavern_scenario: ScenarioConfig,
    ):
        """Action resolution meets p95 < 3s target (tavern scenario)."""
        result = profiler.profile_action_resolution(tavern_scenario, iterations=5)

        assert result.p95_ms < 3000.0, f"p95 was {result.p95_ms}ms, target is 3000ms"

    def test_action_resolution_meets_target_dungeon(
        self,
        profiler: PerformanceProfiler,
        dungeon_scenario: ScenarioConfig,
    ):
        """Action resolution meets p95 < 3s target (dungeon scenario)."""
        result = profiler.profile_action_resolution(dungeon_scenario, iterations=5)

        assert result.p95_ms < 3000.0, f"p95 was {result.p95_ms}ms, target is 3000ms"


# ==============================================================================
# TESTS: Full Round Profiling
# ==============================================================================

class TestFullRoundProfiling:
    """Test full round profiling."""

    def test_profile_full_round_runs(
        self,
        profiler: PerformanceProfiler,
        tavern_scenario: ScenarioConfig,
    ):
        """Full round profiling runs successfully."""
        result = profiler.profile_full_round(tavern_scenario, iterations=3)

        assert result.name == "full_round"
        assert len(result.samples) == 3

    def test_full_round_tavern_completes(
        self,
        profiler: PerformanceProfiler,
        tavern_scenario: ScenarioConfig,
    ):
        """Full round completes within reasonable time (tavern)."""
        result = profiler.profile_full_round(tavern_scenario, iterations=3)

        # Full round should complete within 10 seconds p95
        assert result.p95_ms < 10000.0, f"p95 was {result.p95_ms}ms"

    def test_quick_profile_scenario(self, tavern_scenario: ScenarioConfig):
        """quick_profile_scenario convenience function works."""
        result = quick_profile_scenario(tavern_scenario, "full_round", iterations=2)
        assert result.name == "full_round"


# ==============================================================================
# TESTS: Report Generation
# ==============================================================================

class TestReportGeneration:
    """Test report generation."""

    def test_generate_empty_report(self, profiler: PerformanceProfiler):
        """Can generate report with no results."""
        report = profiler.generate_report()
        assert "PERFORMANCE PROFILING REPORT" in report
        assert "Operations Profiled: 0" in report

    def test_generate_report_with_results(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
        populated_lens: LensIndex,
    ):
        """Can generate report with results."""
        profiler.profile_box_query(small_grid, iterations=10)
        profiler.profile_lens_query(populated_lens, iterations=10)

        report = profiler.generate_report()

        assert "Operations Profiled: 2" in report
        assert "box_query" in report
        assert "lens_query" in report
        assert "p50:" in report
        assert "p95:" in report
        assert "p99:" in report

    def test_report_shows_pass_fail(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """Report shows pass/fail status."""
        profiler.profile_box_query(small_grid, iterations=10)
        report = profiler.generate_report()

        assert "[PASS]" in report or "[FAIL]" in report

    def test_report_shows_target_comparison(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """Report shows target comparisons."""
        profiler.profile_box_query(small_grid, iterations=10)
        report = profiler.generate_report()

        assert "Target Latencies" in report
        assert "OK" in report or "EXCEEDED" in report


# ==============================================================================
# TESTS: Custom Operation Profiling
# ==============================================================================

class TestCustomOperationProfiling:
    """Test custom operation profiling."""

    def test_profile_custom_operation(self, profiler: PerformanceProfiler):
        """Can profile a custom operation."""
        call_count = 0

        def custom_op():
            nonlocal call_count
            call_count += 1
            # Simulate work
            _ = sum(range(100))

        result = profiler.profile_custom("custom_sum", custom_op, iterations=20)

        assert result.name == "custom_sum"
        assert len(result.samples) == 20
        # Warmup + iterations
        assert call_count >= 20

    def test_profile_custom_with_target(self, profiler: PerformanceProfiler):
        """Custom operation can have a target."""
        target = LatencyTarget(
            name="fast_op",
            p50_ms=1.0,
            p95_ms=5.0,
            p99_ms=10.0,
        )

        def fast_op():
            pass

        result = profiler.profile_custom("fast_op", fast_op, iterations=50, target=target)

        assert result.target == target
        assert result.meets_target  # Empty function should pass


# ==============================================================================
# TESTS: Multiple Scenarios
# ==============================================================================

class TestMultipleScenarios:
    """Test profiling across different scenarios."""

    def test_profile_all_scenarios(
        self,
        profiler: PerformanceProfiler,
        tavern_scenario: ScenarioConfig,
        dungeon_scenario: ScenarioConfig,
        field_battle_scenario: ScenarioConfig,
        boss_fight_scenario: ScenarioConfig,
    ):
        """Can profile across all scenarios."""
        scenarios = [
            ("tavern", tavern_scenario),
            ("dungeon", dungeon_scenario),
            ("field", field_battle_scenario),
            ("boss", boss_fight_scenario),
        ]

        results = []
        for name, scenario in scenarios:
            result = profiler.profile_action_resolution(scenario, iterations=2)
            results.append((name, result))

        # All should complete successfully
        for name, result in results:
            assert len(result.samples) == 2, f"{name} failed to collect samples"

    def test_all_scenarios_meet_action_target(
        self,
        profiler: PerformanceProfiler,
        tavern_scenario: ScenarioConfig,
        dungeon_scenario: ScenarioConfig,
        field_battle_scenario: ScenarioConfig,
        boss_fight_scenario: ScenarioConfig,
    ):
        """All scenarios meet action resolution target."""
        scenarios = [
            ("tavern", tavern_scenario),
            ("dungeon", dungeon_scenario),
            ("field", field_battle_scenario),
            ("boss", boss_fight_scenario),
        ]

        for name, scenario in scenarios:
            result = profiler.profile_action_resolution(scenario, iterations=5)
            assert result.p95_ms < 3000.0, (
                f"{name} scenario p95 was {result.p95_ms}ms, target is 3000ms"
            )


# ==============================================================================
# TESTS: Statistical Validity
# ==============================================================================

class TestStatisticalValidity:
    """Test statistical properties of profiling."""

    def test_samples_are_positive(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """All samples should be positive."""
        result = profiler.profile_box_query(small_grid, iterations=20)

        for sample in result.samples:
            assert sample > 0, "Sample should be positive"

    def test_percentile_ordering(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """Percentiles should be in order: p50 <= p95 <= p99."""
        result = profiler.profile_box_query(small_grid, iterations=30)

        assert result.p50_ms <= result.p95_ms
        assert result.p95_ms <= result.p99_ms

    def test_min_max_bounds(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """Min/max should bound all samples."""
        result = profiler.profile_box_query(small_grid, iterations=30)

        assert result.min_ms <= result.p50_ms
        assert result.p99_ms <= result.max_ms

    def test_mean_is_reasonable(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """Mean should be between min and max."""
        result = profiler.profile_box_query(small_grid, iterations=30)

        assert result.min_ms <= result.mean_ms <= result.max_ms


# ==============================================================================
# TESTS: Result Serialization
# ==============================================================================

class TestResultSerialization:
    """Test LatencyResult serialization."""

    def test_result_to_dict(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """LatencyResult serializes to dict."""
        result = profiler.profile_box_query(small_grid, iterations=10)
        d = result.to_dict()

        assert d["name"] == "box_query"
        assert "p50_ms" in d
        assert "p95_ms" in d
        assert "p99_ms" in d
        assert "meets_target" in d
        assert d["samples_count"] == 10

    def test_result_includes_target(
        self,
        profiler: PerformanceProfiler,
        small_grid: BattleGrid,
    ):
        """Result includes target in serialization."""
        result = profiler.profile_box_query(small_grid, iterations=10)
        d = result.to_dict()

        assert d["target"] is not None
        assert d["target"]["name"] == "box_query"
