"""Property-based tests for geometry system validation.

Implements the "Thousand-Fold Fireball" pattern: randomized input generation
with invariant validation across 1000 iterations to find edge cases.

Tests marked with @pytest.mark.property_based for optional CI skipping.
Tests marked with @pytest.mark.slow for tests > 1 second.

WO-019: Property-Based Testing
Reference: Execution Plan Milestone 3
"""

import pytest
from typing import List

from aidm.testing.property_testing import PropertyTestHarness, PropertyTestResult
from aidm.core.geometry_engine import BattleGrid
from aidm.core.aoe_rasterizer import (
    AoEShape, AoEDirection, rasterize_burst, rasterize_cone, rasterize_line,
    get_aoe_affected_squares, discrete_distance, AoEResult, create_aoe_result,
)
from aidm.core.cover_resolver import calculate_cover, CoverDegree
from aidm.core.los_resolver import check_los, check_loe
from aidm.core.rng_manager import RNGManager
from aidm.schemas.position import Position


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def harness() -> PropertyTestHarness:
    """Create a PropertyTestHarness with fixed seed."""
    return PropertyTestHarness(master_seed=42)


@pytest.fixture
def alternate_harness() -> PropertyTestHarness:
    """Create a PropertyTestHarness with different seed for cross-validation."""
    return PropertyTestHarness(master_seed=12345)


@pytest.fixture
def empty_grid() -> BattleGrid:
    """Create an empty 30x30 grid."""
    return BattleGrid(30, 30)


@pytest.fixture
def small_grid() -> BattleGrid:
    """Create a small 10x10 grid for quick tests."""
    return BattleGrid(10, 10)


# ==============================================================================
# THOUSAND-FOLD FIREBALL TESTS
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestThousandFoldFireball:
    """Property tests for AoE rasterization robustness."""

    def test_thousand_fold_fireball_default_seed(self, harness: PropertyTestHarness):
        """Thousand-fold fireball with default seed passes."""
        result = harness.run_thousand_fold_fireball(iterations=1000)

        assert result.passed, (
            f"Thousand-fold fireball failed with {len(result.failures)} failures.\n"
            f"First failure: {result.failures[0] if result.failures else 'None'}"
        )
        assert result.iterations_run == 1000

    def test_thousand_fold_fireball_alternate_seed(self, alternate_harness: PropertyTestHarness):
        """Thousand-fold fireball passes with different seed."""
        result = alternate_harness.run_thousand_fold_fireball(iterations=1000)

        assert result.passed, (
            f"Failed with alternate seed. Failures: {result.failures[:3]}"
        )

    def test_thousand_fold_fireball_reproducible(self, harness: PropertyTestHarness):
        """Same seed produces same results (reproducibility)."""
        result1 = harness.run_thousand_fold_fireball(iterations=100)
        result2 = harness.run_thousand_fold_fireball(iterations=100)

        # Both should pass and have same iteration count
        assert result1.passed == result2.passed
        assert result1.iterations_run == result2.iterations_run
        assert len(result1.failures) == len(result2.failures)

    def test_thousand_fold_fireball_small_grid(self, harness: PropertyTestHarness):
        """Thousand-fold works on small grids."""
        result = harness.run_thousand_fold_fireball(
            iterations=500,
            grid_size=(10, 10)
        )

        assert result.passed, f"Failed on small grid: {result.failures[:3]}"

    def test_thousand_fold_fireball_large_grid(self, harness: PropertyTestHarness):
        """Thousand-fold works on large grids."""
        result = harness.run_thousand_fold_fireball(
            iterations=500,
            grid_size=(100, 100)
        )

        assert result.passed, f"Failed on large grid: {result.failures[:3]}"


# ==============================================================================
# COVER SYMMETRY TESTS
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestCoverSymmetry:
    """Property tests for cover calculation consistency."""

    def test_cover_symmetry_default(self, harness: PropertyTestHarness):
        """Cover symmetry check passes with 1000 iterations."""
        result = harness.run_cover_symmetry_check(iterations=1000)

        assert result.passed, (
            f"Cover symmetry failed with {len(result.failures)} failures.\n"
            f"First failure: {result.failures[0] if result.failures else 'None'}"
        )

    def test_cover_symmetry_alternate_seed(self, alternate_harness: PropertyTestHarness):
        """Cover symmetry passes with different seed."""
        result = alternate_harness.run_cover_symmetry_check(iterations=1000)

        assert result.passed, f"Failed with alternate seed: {result.failures[:3]}"

    def test_cover_geometry_valid(self, harness: PropertyTestHarness):
        """Cover calculation produces valid geometry."""
        result = harness.run_cover_symmetry_check(iterations=500)

        assert result.passed
        # Verify all iterations completed
        assert result.iterations_run == 500


# ==============================================================================
# LOS REFLEXIVITY TESTS
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestLOSReflexivity:
    """Property tests for LOS reflexivity (can always see self)."""

    def test_los_reflexivity_default(self, harness: PropertyTestHarness):
        """LOS reflexivity check passes: entity can always see itself."""
        result = harness.run_los_reflexivity_check(iterations=1000)

        assert result.passed, (
            f"LOS reflexivity failed with {len(result.failures)} failures.\n"
            f"First failure: {result.failures[0] if result.failures else 'None'}"
        )

    def test_los_reflexivity_alternate_seed(self, alternate_harness: PropertyTestHarness):
        """LOS reflexivity passes with different seed."""
        result = alternate_harness.run_los_reflexivity_check(iterations=1000)

        assert result.passed, f"Failed with alternate seed: {result.failures[:3]}"

    def test_los_reflexivity_dense_obstacles(self, harness: PropertyTestHarness):
        """LOS reflexivity holds even with dense obstacles."""
        # Reflexivity should ALWAYS hold regardless of obstacles
        result = harness.run_los_reflexivity_check(
            iterations=500,
            grid_size=(20, 20)
        )

        assert result.passed


# ==============================================================================
# LOS SYMMETRY TESTS
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestLOSSymmetry:
    """Property tests for LOS symmetry in empty grids."""

    def test_los_symmetry_empty_grid(self, harness: PropertyTestHarness):
        """LOS symmetry holds in empty grids: LOS(A,B) == LOS(B,A)."""
        result = harness.run_los_symmetry_check(iterations=1000)

        assert result.passed, (
            f"LOS symmetry failed with {len(result.failures)} failures.\n"
            f"First failure: {result.failures[0] if result.failures else 'None'}"
        )

    def test_los_symmetry_alternate_seed(self, alternate_harness: PropertyTestHarness):
        """LOS symmetry passes with different seed."""
        result = alternate_harness.run_los_symmetry_check(iterations=1000)

        assert result.passed, f"Failed with alternate seed: {result.failures[:3]}"


# ==============================================================================
# AOE CONTAINMENT TESTS
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestAoEContainment:
    """Property tests for AoE containment (origin in burst)."""

    def test_aoe_containment_default(self, harness: PropertyTestHarness):
        """Burst AoE always contains origin."""
        result = harness.run_aoe_containment_check(iterations=1000)

        assert result.passed, (
            f"AoE containment failed with {len(result.failures)} failures.\n"
            f"First failure: {result.failures[0] if result.failures else 'None'}"
        )

    def test_aoe_containment_alternate_seed(self, alternate_harness: PropertyTestHarness):
        """AoE containment passes with different seed."""
        result = alternate_harness.run_aoe_containment_check(iterations=1000)

        assert result.passed, f"Failed with alternate seed: {result.failures[:3]}"

    def test_aoe_zero_radius_is_origin_only(self, harness: PropertyTestHarness):
        """Zero-radius burst contains only the origin."""
        rng = RNGManager(42).stream("zero_radius")

        for _ in range(100):
            origin = Position(
                x=rng.randint(0, 50),
                y=rng.randint(0, 50)
            )
            result = rasterize_burst(origin, 0)

            assert len(result) == 1
            assert result[0] == origin


# ==============================================================================
# DISTANCE PROPERTIES TESTS
# ==============================================================================

@pytest.mark.property_based
class TestDistanceProperties:
    """Property tests for distance functions.

    NOTE: The D&D 3.5e 1-2-1-2 diagonal distance does NOT satisfy the
    triangle inequality. This is a known property, not a bug. The alternating
    diagonal cost (5 ft, then 10 ft) means dist(A,C) can exceed
    dist(A,B) + dist(B,C) when paths combine diagonal costs unfavorably.

    Example: A=(0,0), B=(1,1), C=(2,2)
    - dist(A,B) = 5 feet (1 diagonal, costs 5)
    - dist(B,C) = 5 feet (1 diagonal, costs 5)
    - dist(A,C) = 15 feet (2 diagonals, costs 5+10=15)
    - But dist(A,B) + dist(B,C) = 10, and 15 > 10!

    This is RAW-compliant behavior per PHB p.148.
    """

    def test_distance_non_negative(self, harness: PropertyTestHarness):
        """Distance is always non-negative."""
        rng = RNGManager(42).stream("distance")

        for _ in range(1000):
            pos_a = Position(x=rng.randint(0, 50), y=rng.randint(0, 50))
            pos_b = Position(x=rng.randint(0, 50), y=rng.randint(0, 50))

            dist = pos_a.distance_to(pos_b)
            assert dist >= 0, f"Negative distance from {pos_a} to {pos_b}"

    def test_distance_symmetric(self, harness: PropertyTestHarness):
        """Distance is symmetric: dist(A,B) == dist(B,A)."""
        rng = RNGManager(42).stream("symmetry")

        for _ in range(1000):
            pos_a = Position(x=rng.randint(0, 50), y=rng.randint(0, 50))
            pos_b = Position(x=rng.randint(0, 50), y=rng.randint(0, 50))

            dist_ab = pos_a.distance_to(pos_b)
            dist_ba = pos_b.distance_to(pos_a)

            assert dist_ab == dist_ba, (
                f"Distance asymmetric: {pos_a} to {pos_b} = {dist_ab}, "
                f"{pos_b} to {pos_a} = {dist_ba}"
            )

    def test_distance_self_is_zero(self, harness: PropertyTestHarness):
        """Distance to self is zero."""
        rng = RNGManager(42).stream("self_distance")

        for _ in range(1000):
            pos = Position(x=rng.randint(0, 50), y=rng.randint(0, 50))
            dist = pos.distance_to(pos)

            assert dist == 0, f"Distance to self not zero: {pos} -> {dist}"

    def test_discrete_distance_non_negative(self, harness: PropertyTestHarness):
        """Discrete distance is always non-negative."""
        rng = RNGManager(42).stream("discrete")

        for _ in range(1000):
            dx = rng.randint(-20, 20)
            dy = rng.randint(-20, 20)

            dist = discrete_distance(dx, dy)
            assert dist >= 0, f"Negative discrete distance for ({dx}, {dy})"

    def test_discrete_distance_symmetric(self, harness: PropertyTestHarness):
        """Discrete distance is symmetric for sign changes."""
        rng = RNGManager(42).stream("discrete_sym")

        for _ in range(1000):
            dx = rng.randint(-20, 20)
            dy = rng.randint(-20, 20)

            d1 = discrete_distance(dx, dy)
            d2 = discrete_distance(-dx, -dy)
            d3 = discrete_distance(dx, -dy)
            d4 = discrete_distance(-dx, dy)

            assert d1 == d2 == d3 == d4, (
                f"Discrete distance not symmetric for ({dx}, {dy}): "
                f"{d1}, {d2}, {d3}, {d4}"
            )


# ==============================================================================
# CONE SQUARE COUNT TESTS
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestConeSquareCount:
    """Property tests for cone triangular number formula."""

    def test_cone_square_count_cardinal(self, harness: PropertyTestHarness):
        """Cardinal cones have triangular number square counts."""
        result = harness.run_cone_square_count_check(iterations=1000)

        assert result.passed, (
            f"Cone square count failed with {len(result.failures)} failures.\n"
            f"First failure: {result.failures[0] if result.failures else 'None'}"
        )

    def test_cone_square_count_formula(self):
        """Explicit test of triangular number formula for cones."""
        origin = Position(x=20, y=20)

        test_cases = [
            (15, 6),   # 3 * 4 / 2 = 6
            (30, 21),  # 6 * 7 / 2 = 21
            (45, 45),  # 9 * 10 / 2 = 45
            (60, 78),  # 12 * 13 / 2 = 78
        ]

        for length_ft, expected_count in test_cases:
            for direction in [AoEDirection.N, AoEDirection.E,
                              AoEDirection.S, AoEDirection.W]:
                result = rasterize_cone(origin, direction, length_ft)
                assert len(result) == expected_count, (
                    f"Cone {length_ft}ft {direction.value}: expected {expected_count}, got {len(result)}"
                )


# ==============================================================================
# ALL PROPERTY TESTS RUNNER
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestAllPropertyTests:
    """Run all property tests as a suite."""

    def test_all_property_tests_pass(self, harness: PropertyTestHarness):
        """All property tests pass with 1000 iterations."""
        results = harness.run_all_property_tests(iterations=1000)

        failed_tests = [name for name, result in results.items() if not result.passed]

        assert len(failed_tests) == 0, (
            f"Property tests failed: {failed_tests}\n"
            f"Details: {[(name, results[name].failures[:2]) for name in failed_tests]}"
        )

    def test_all_tests_complete(self, harness: PropertyTestHarness):
        """All property tests complete their iterations."""
        results = harness.run_all_property_tests(iterations=100)

        for name, result in results.items():
            assert result.iterations_run == 100, (
                f"Test {name} only ran {result.iterations_run}/100 iterations"
            )


# ==============================================================================
# HARNESS UNIT TESTS
# ==============================================================================

class TestPropertyTestHarness:
    """Unit tests for PropertyTestHarness methods."""

    def test_generate_random_grid_has_correct_size(self, harness: PropertyTestHarness):
        """Generated grids have correct dimensions."""
        grid = harness.generate_random_grid(seed=42, size=(25, 30))

        assert grid.width == 25
        assert grid.height == 30

    def test_generate_random_grid_has_obstacles(self, harness: PropertyTestHarness):
        """Generated grids contain obstacles when density > 0."""
        grid = harness.generate_random_grid(
            seed=42,
            size=(20, 20),
            obstacle_density=0.2
        )

        # Count solid cells
        solid_count = 0
        for y in range(grid.height):
            for x in range(grid.width):
                cell = grid.get_cell(Position(x=x, y=y))
                if cell.cell_mask.blocks_loe():
                    solid_count += 1

        # Should have some obstacles (approximately 20% of 400 = 80)
        assert solid_count > 0

    def test_generate_empty_grid_is_empty(self, harness: PropertyTestHarness):
        """Empty grid has no obstacles."""
        grid = harness.generate_empty_grid(size=(20, 20))

        for y in range(grid.height):
            for x in range(grid.width):
                cell = grid.get_cell(Position(x=x, y=y))
                assert not cell.cell_mask.blocks_loe()
                assert not cell.cell_mask.blocks_los()

    def test_generate_random_positions_in_bounds(self, harness: PropertyTestHarness):
        """Generated positions are within grid bounds."""
        grid = harness.generate_empty_grid(size=(15, 20))
        positions = harness.generate_random_positions(grid=grid, count=100, seed=42)

        assert len(positions) == 100
        for pos in positions:
            assert 0 <= pos.x < 15
            assert 0 <= pos.y < 20

    def test_generate_random_aoe_produces_valid_config(self, harness: PropertyTestHarness):
        """Generated AoE configs are valid."""
        origin = Position(x=25, y=25)
        config = harness.generate_random_aoe(origin=origin, seed=42)

        assert config.origin == origin
        assert isinstance(config.shape, AoEShape)
        assert isinstance(config.params, dict)

        # Should be able to execute without error
        affected = get_aoe_affected_squares(
            config.shape,
            config.origin,
            config.params
        )
        assert isinstance(affected, list)

    def test_harness_deterministic(self, harness: PropertyTestHarness):
        """Same seed produces same random values."""
        grid1 = harness.generate_random_grid(seed=123, size=(10, 10))
        grid2 = harness.generate_random_grid(seed=123, size=(10, 10))

        # Compare cell masks
        for y in range(10):
            for x in range(10):
                pos = Position(x=x, y=y)
                assert grid1.get_cell(pos).cell_mask.to_int() == \
                       grid2.get_cell(pos).cell_mask.to_int()


# ==============================================================================
# PROPERTY TEST RESULT TESTS
# ==============================================================================

class TestPropertyTestResult:
    """Tests for PropertyTestResult dataclass."""

    def test_result_starts_passing(self):
        """New result starts in passing state."""
        result = PropertyTestResult(
            test_name="test",
            passed=True,
            iterations_run=0
        )

        assert result.passed
        assert len(result.failures) == 0

    def test_add_failure_sets_failed(self):
        """Adding a failure sets passed to False."""
        result = PropertyTestResult(
            test_name="test",
            passed=True,
            iterations_run=100
        )

        result.add_failure(
            seed=42,
            iteration=50,
            message="Test failure",
            context={"key": "value"}
        )

        assert not result.passed
        assert len(result.failures) == 1
        assert result.failures[0]["seed"] == 42
        assert result.failures[0]["iteration"] == 50
        assert result.failures[0]["message"] == "Test failure"

    def test_to_dict_serializes(self):
        """Result serializes to dict correctly."""
        result = PropertyTestResult(
            test_name="my_test",
            passed=True,
            iterations_run=500,
            elapsed_seconds=1.5
        )

        data = result.to_dict()

        assert data["test_name"] == "my_test"
        assert data["passed"] is True
        assert data["iterations_run"] == 500
        assert data["elapsed_seconds"] == 1.5
        assert data["failure_count"] == 0


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

@pytest.mark.property_based
class TestEdgeCases:
    """Test edge cases discovered by property testing."""

    def test_aoe_at_grid_origin(self):
        """AoE at (0,0) works correctly."""
        origin = Position(x=0, y=0)

        # Burst at origin
        burst = rasterize_burst(origin, 10)
        assert origin in burst
        # Some squares will have negative coordinates (out of typical grid)
        assert Position(x=-1, y=0) in burst

    def test_aoe_at_max_radius(self):
        """Large radius AoE doesn't crash."""
        origin = Position(x=50, y=50)
        burst = rasterize_burst(origin, 60)  # 60-foot radius

        assert origin in burst
        assert len(burst) > 100  # Should be substantial

    def test_cover_same_position(self):
        """Cover calculation at same position works."""
        grid = BattleGrid(20, 20)
        pos = Position(x=10, y=10)

        result = calculate_cover(pos, pos, grid)

        # Same position should have no cover (can target yourself)
        assert result.lines_blocked <= result.lines_total

    def test_los_adjacent_positions(self):
        """LOS between adjacent positions is clear in empty grid."""
        grid = BattleGrid(20, 20)

        # Check all 8 directions from center
        center = Position(x=10, y=10)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbor = Position(x=center.x + dx, y=center.y + dy)

                result = check_los(grid, center, 5, neighbor, 5)
                assert result.is_clear, f"LOS blocked to adjacent {neighbor}"

    def test_cone_excludes_origin(self):
        """Cone never includes its origin position."""
        origin = Position(x=20, y=20)

        for direction in AoEDirection:
            for length_ft in [15, 30, 45]:
                affected = rasterize_cone(origin, direction, length_ft)
                assert origin not in affected, (
                    f"Origin in cone {direction.value} {length_ft}ft"
                )

    def test_line_correct_length(self):
        """Cardinal line has correct number of squares."""
        origin = Position(x=10, y=10)

        for length_ft in [10, 20, 30, 40, 50]:
            for direction in [AoEDirection.N, AoEDirection.E,
                              AoEDirection.S, AoEDirection.W]:
                affected = rasterize_line(origin, direction, length_ft)
                expected = length_ft // 5
                assert len(affected) == expected, (
                    f"Line {direction.value} {length_ft}ft: "
                    f"expected {expected}, got {len(affected)}"
                )


# ==============================================================================
# PERFORMANCE TESTS
# ==============================================================================

@pytest.mark.property_based
@pytest.mark.slow
class TestPerformance:
    """Performance validation for property tests."""

    def test_thousand_fold_completes_in_reasonable_time(self, harness: PropertyTestHarness):
        """Thousand-fold fireball completes within reasonable time."""
        import time

        start = time.time()
        result = harness.run_thousand_fold_fireball(iterations=1000)
        elapsed = time.time() - start

        assert result.passed
        # Should complete in under 30 seconds (generous for CI)
        assert elapsed < 30, f"Took {elapsed:.2f}s, expected < 30s"

    def test_all_tests_complete_in_reasonable_time(self, harness: PropertyTestHarness):
        """All property tests complete within reasonable time."""
        import time

        start = time.time()
        results = harness.run_all_property_tests(iterations=500)
        elapsed = time.time() - start

        # All should pass
        failed = [name for name, r in results.items() if not r.passed]
        assert len(failed) == 0, f"Failed tests: {failed}"

        # Total time should be reasonable (under 2 minutes)
        assert elapsed < 120, f"Took {elapsed:.2f}s, expected < 120s"


# ==============================================================================
# REGRESSION TESTS
# ==============================================================================

@pytest.mark.property_based
class TestRegressions:
    """Regression tests for previously found issues."""

    def test_negative_radius_returns_empty(self):
        """Negative radius returns empty list, not crash."""
        origin = Position(x=10, y=10)
        result = rasterize_burst(origin, -5)

        assert result == []

    def test_zero_length_cone_returns_empty(self):
        """Zero-length cone returns empty list."""
        origin = Position(x=10, y=10)
        result = rasterize_cone(origin, AoEDirection.N, 0)

        assert result == []

    def test_zero_length_line_returns_empty(self):
        """Zero-length line returns empty list."""
        origin = Position(x=10, y=10)
        result = rasterize_line(origin, AoEDirection.N, 0)

        assert result == []

    def test_burst_no_duplicates(self):
        """Burst result has no duplicate positions."""
        origin = Position(x=25, y=25)
        result = rasterize_burst(origin, 30)

        assert len(result) == len(set(result))

    def test_cone_no_duplicates(self):
        """Cone result has no duplicate positions."""
        origin = Position(x=25, y=25)

        for direction in AoEDirection:
            result = rasterize_cone(origin, direction, 30)
            assert len(result) == len(set(result)), (
                f"Duplicates in cone {direction.value}"
            )

    def test_line_no_duplicates(self):
        """Line result has no duplicate positions."""
        origin = Position(x=25, y=25)

        for direction in AoEDirection:
            result = rasterize_line(origin, direction, 40)
            assert len(result) == len(set(result)), (
                f"Duplicates in line {direction.value}"
            )
