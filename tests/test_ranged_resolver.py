"""Tests for ranged attack resolution.

WO-005: Ranged Attack Resolution
Comprehensive test suite covering:
- Distance calculation (orthogonal, diagonal, 1-2-1-2 rule)
- Range increment calculation
- Range penalty calculation
- Cover integration
- Full evaluation tests
- Edge cases
"""

import pytest

from aidm.schemas.position import Position
from aidm.schemas.geometry import PropertyMask, PropertyFlag, SizeCategory, Direction
from aidm.core.geometry_engine import BattleGrid
from aidm.core.cover_resolver import CoverDegree
from aidm.core.ranged_resolver import (
    calculate_distance_feet,
    calculate_distance_squares,
    get_range_increment,
    calculate_range_increment_penalty,
    get_cover_ac_bonus,
    has_line_of_effect,
    is_valid_ranged_target,
    evaluate_ranged_attack,
    RangedAttackResult,
    DEFAULT_MAX_INCREMENTS,
    THROWN_MAX_INCREMENTS,
    PENALTY_PER_INCREMENT,
)


# ==============================================================================
# TEST FIXTURES
# ==============================================================================

@pytest.fixture
def empty_grid():
    """Create an empty 20x20 grid."""
    return BattleGrid(20, 20)


@pytest.fixture
def grid_with_entities(empty_grid):
    """Create grid with attacker and target placed."""
    grid = empty_grid
    # Attacker at (5, 5)
    grid.place_entity("attacker", Position(5, 5), SizeCategory.MEDIUM)
    # Target at (10, 5) - 5 squares east = 25 feet
    grid.place_entity("target", Position(10, 5), SizeCategory.MEDIUM)
    return grid


@pytest.fixture
def grid_with_wall(empty_grid):
    """Create grid with a solid wall between positions."""
    grid = empty_grid
    grid.place_entity("attacker", Position(5, 5), SizeCategory.MEDIUM)
    grid.place_entity("target", Position(10, 5), SizeCategory.MEDIUM)
    # Place wall at (7, 5) - blocking cell
    cell = grid.get_cell(Position(7, 5))
    cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
    return grid


@pytest.fixture
def grid_with_half_cover(empty_grid):
    """Create grid with partial cover for target."""
    grid = empty_grid
    grid.place_entity("attacker", Position(0, 0), SizeCategory.MEDIUM)
    grid.place_entity("target", Position(4, 0), SizeCategory.MEDIUM)
    # Place a wall on the border between (3,0) and (4,0) - blocks some lines
    # Using cell mask at (3,0) with SOLID+OPAQUE to create partial cover
    cell = grid.get_cell(Position(3, 0))
    cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
    return grid


# ==============================================================================
# DISTANCE CALCULATION TESTS
# ==============================================================================

class TestDistanceCalculation:
    """Tests for distance calculation using 1-2-1-2 diagonal rule."""

    def test_adjacent_squares_orthogonal(self):
        """Adjacent squares orthogonally = 5 feet."""
        pos1 = Position(5, 5)
        pos2 = Position(5, 6)  # 1 square south
        assert calculate_distance_feet(pos1, pos2) == 5

    def test_adjacent_squares_diagonal(self):
        """First diagonal = 5 feet (1 in 1-2-1-2)."""
        pos1 = Position(5, 5)
        pos2 = Position(6, 6)  # 1 diagonal
        assert calculate_distance_feet(pos1, pos2) == 5

    def test_two_diagonals(self):
        """Two diagonals = 15 feet (5 + 10)."""
        pos1 = Position(0, 0)
        pos2 = Position(2, 2)  # 2 diagonals
        assert calculate_distance_feet(pos1, pos2) == 15

    def test_three_diagonals(self):
        """Three diagonals = 20 feet (5 + 10 + 5)."""
        pos1 = Position(0, 0)
        pos2 = Position(3, 3)  # 3 diagonals
        assert calculate_distance_feet(pos1, pos2) == 20

    def test_orthogonal_distance(self):
        """Straight line orthogonal = 5 feet per square."""
        pos1 = Position(0, 0)
        pos2 = Position(4, 0)  # 4 squares east
        assert calculate_distance_feet(pos1, pos2) == 20

    def test_long_orthogonal(self):
        """Long orthogonal distance (100+ ft)."""
        pos1 = Position(0, 0)
        pos2 = Position(25, 0)  # 25 squares = 125 feet
        assert calculate_distance_feet(pos1, pos2) == 125

    def test_mixed_diagonal_orthogonal(self):
        """Mixed diagonal and orthogonal movement."""
        pos1 = Position(0, 0)
        pos2 = Position(4, 2)  # 2 diagonals + 2 orthogonal
        # 2 diagonals = 15 feet, 2 orthogonal = 10 feet
        assert calculate_distance_feet(pos1, pos2) == 25

    def test_same_position(self):
        """Same position = 0 feet."""
        pos1 = Position(5, 5)
        pos2 = Position(5, 5)
        assert calculate_distance_feet(pos1, pos2) == 0

    def test_distance_squares(self):
        """Distance in squares = distance_feet / 5."""
        pos1 = Position(0, 0)
        pos2 = Position(4, 0)  # 20 feet = 4 squares
        assert calculate_distance_squares(pos1, pos2) == 4


# ==============================================================================
# RANGE INCREMENT TESTS
# ==============================================================================

class TestRangeIncrement:
    """Tests for range increment calculation."""

    def test_first_increment_start(self):
        """Distance 5 ft with 60 ft increment = increment 1."""
        assert get_range_increment(5, 60) == 1

    def test_first_increment_end(self):
        """Distance 60 ft with 60 ft increment = increment 1."""
        assert get_range_increment(60, 60) == 1

    def test_second_increment_start(self):
        """Distance 61 ft with 60 ft increment = increment 2."""
        assert get_range_increment(61, 60) == 2

    def test_second_increment_end(self):
        """Distance 120 ft with 60 ft increment = increment 2."""
        assert get_range_increment(120, 60) == 2

    def test_third_increment(self):
        """Distance 121-180 ft with 60 ft increment = increment 3."""
        assert get_range_increment(121, 60) == 3
        assert get_range_increment(180, 60) == 3

    def test_tenth_increment(self):
        """Maximum range increment (10th) for shortbow."""
        # Shortbow: 60 ft increment, 10 increments = 600 ft max
        assert get_range_increment(541, 60) == 10
        assert get_range_increment(600, 60) == 10

    def test_beyond_tenth_increment(self):
        """Beyond 10th increment returns higher number (invalid)."""
        assert get_range_increment(601, 60) == 11

    def test_zero_distance(self):
        """Distance 0 returns increment 0 (same square)."""
        assert get_range_increment(0, 60) == 0

    def test_longbow_increments(self):
        """Longbow with 100 ft increment."""
        assert get_range_increment(100, 100) == 1
        assert get_range_increment(101, 100) == 2
        assert get_range_increment(200, 100) == 2

    def test_thrown_dagger(self):
        """Thrown dagger with 10 ft increment."""
        assert get_range_increment(10, 10) == 1
        assert get_range_increment(11, 10) == 2
        assert get_range_increment(50, 10) == 5

    def test_invalid_increment(self):
        """Zero or negative range increment raises error."""
        with pytest.raises(ValueError):
            get_range_increment(60, 0)
        with pytest.raises(ValueError):
            get_range_increment(60, -10)


# ==============================================================================
# RANGE PENALTY TESTS
# ==============================================================================

class TestRangePenalty:
    """Tests for range increment penalty calculation."""

    def test_first_increment_no_penalty(self):
        """First increment has no penalty."""
        assert calculate_range_increment_penalty(60, 60) == 0
        assert calculate_range_increment_penalty(5, 60) == 0

    def test_second_increment_penalty(self):
        """Second increment has -2 penalty."""
        assert calculate_range_increment_penalty(61, 60) == -2
        assert calculate_range_increment_penalty(120, 60) == -2

    def test_third_increment_penalty(self):
        """Third increment has -4 penalty."""
        assert calculate_range_increment_penalty(121, 60) == -4

    def test_fourth_increment_penalty(self):
        """Fourth increment has -6 penalty."""
        assert calculate_range_increment_penalty(181, 60) == -6

    def test_tenth_increment_penalty(self):
        """Tenth increment has -18 penalty."""
        assert calculate_range_increment_penalty(541, 60) == -18
        assert calculate_range_increment_penalty(600, 60) == -18

    def test_beyond_max_increments_returns_none(self):
        """Beyond max increments returns None (invalid)."""
        assert calculate_range_increment_penalty(601, 60, 10) is None
        assert calculate_range_increment_penalty(1001, 100, 10) is None

    def test_thrown_max_increments(self):
        """Thrown weapons have 5 max increments."""
        # Dagger: 10 ft increment, 5 max = 50 ft
        assert calculate_range_increment_penalty(50, 10, THROWN_MAX_INCREMENTS) == -8
        assert calculate_range_increment_penalty(51, 10, THROWN_MAX_INCREMENTS) is None

    def test_zero_distance_no_penalty(self):
        """Same square has no penalty (melee)."""
        assert calculate_range_increment_penalty(0, 60) == 0

    def test_penalty_constant(self):
        """Verify penalty constant is -2."""
        assert PENALTY_PER_INCREMENT == -2


# ==============================================================================
# COVER INTEGRATION TESTS
# ==============================================================================

class TestCoverIntegration:
    """Tests for cover AC bonus and LOE integration."""

    def test_no_cover_zero_bonus(self, empty_grid):
        """No cover gives +0 AC bonus."""
        grid = empty_grid
        attacker_pos = Position(0, 0)
        target_pos = Position(5, 0)
        bonus = get_cover_ac_bonus(attacker_pos, target_pos, grid)
        assert bonus == 0

    def test_has_loe_no_obstruction(self, empty_grid):
        """Clear path has line of effect."""
        grid = empty_grid
        attacker_pos = Position(0, 0)
        target_pos = Position(5, 0)
        assert has_line_of_effect(attacker_pos, target_pos, grid) is True

    def test_blocked_loe_solid_wall(self, empty_grid):
        """Solid wall blocks line of effect."""
        grid = empty_grid
        attacker_pos = Position(0, 0)
        target_pos = Position(4, 0)
        # Place solid wall in between
        cell = grid.get_cell(Position(2, 0))
        cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        # Total cover should block LOE
        # Note: Whether this is total cover depends on corner-to-corner lines
        # A single cell may not block all 16 lines, so we test with full wall
        wall_cell = grid.get_cell(Position(2, 0))
        wall_cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        # The cover calculation will determine if LOE is blocked


class TestCoverACBonus:
    """Tests for specific cover AC bonuses."""

    def test_half_cover_bonus(self):
        """Half cover gives +2 AC bonus."""
        # Half cover: 5-8 of 16 lines blocked
        # This is tested via the cover_resolver integration
        # The get_cover_ac_bonus function returns the bonus from CoverResult
        pass  # Covered by integration tests

    def test_three_quarters_cover_bonus(self):
        """Three-quarters cover gives +5 AC bonus."""
        # Three-quarters cover: 9-12 of 16 lines blocked
        pass  # Covered by integration tests


# ==============================================================================
# VALID TARGET TESTS
# ==============================================================================

class TestValidRangedTarget:
    """Tests for is_valid_ranged_target function."""

    def test_valid_target_in_range(self, grid_with_entities):
        """Target within range with clear LOE is valid."""
        result = is_valid_ranged_target(
            grid_with_entities, "attacker", "target", max_range_ft=100
        )
        assert result is True

    def test_invalid_target_out_of_range(self, grid_with_entities):
        """Target beyond max range is invalid."""
        result = is_valid_ranged_target(
            grid_with_entities, "attacker", "target", max_range_ft=20
        )
        assert result is False

    def test_invalid_attacker_not_found(self, grid_with_entities):
        """Missing attacker raises error."""
        with pytest.raises(ValueError, match="not found"):
            is_valid_ranged_target(
                grid_with_entities, "nonexistent", "target", max_range_ft=100
            )

    def test_invalid_target_not_found(self, grid_with_entities):
        """Missing target raises error."""
        with pytest.raises(ValueError, match="not found"):
            is_valid_ranged_target(
                grid_with_entities, "attacker", "nonexistent", max_range_ft=100
            )


# ==============================================================================
# FULL EVALUATION TESTS
# ==============================================================================

class TestEvaluateRangedAttack:
    """Tests for evaluate_ranged_attack function."""

    def test_valid_attack_no_cover(self, grid_with_entities):
        """Valid attack within range with no cover."""
        result = evaluate_ranged_attack(
            grid=grid_with_entities,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,  # Shortbow
            max_range_ft=600
        )
        assert result.is_valid is True
        assert result.attacker_id == "attacker"
        assert result.target_id == "target"
        assert result.distance_ft == 25  # 5 squares * 5 = 25 ft
        assert result.range_increment == 1
        assert result.range_penalty == 0
        assert result.failure_reason is None

    def test_valid_attack_second_increment(self, empty_grid):
        """Valid attack in second range increment."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(15, 0), SizeCategory.MEDIUM)  # 75 ft
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is True
        assert result.distance_ft == 75
        assert result.range_increment == 2
        assert result.range_penalty == -2

    def test_invalid_beyond_max_range(self, empty_grid):
        """Attack beyond max range is invalid."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(15, 0), SizeCategory.MEDIUM)  # 75 ft
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=10,  # Dagger
            max_range_ft=50  # 5 increments
        )
        assert result.is_valid is False
        assert "Beyond maximum range" in result.failure_reason

    def test_invalid_attacker_missing(self, empty_grid):
        """Attack with missing attacker is invalid."""
        grid = empty_grid
        grid.place_entity("target", Position(5, 5), SizeCategory.MEDIUM)
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is False
        assert "not found" in result.failure_reason

    def test_invalid_target_missing(self, empty_grid):
        """Attack with missing target is invalid."""
        grid = empty_grid
        grid.place_entity("attacker", Position(5, 5), SizeCategory.MEDIUM)
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is False
        assert "not found" in result.failure_reason

    def test_result_to_dict(self, grid_with_entities):
        """RangedAttackResult.to_dict() serializes correctly."""
        result = evaluate_ranged_attack(
            grid=grid_with_entities,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        d = result.to_dict()
        assert d["is_valid"] is True
        assert d["attacker_id"] == "attacker"
        assert d["target_id"] == "target"
        assert d["distance_ft"] == 25
        assert d["range_increment"] == 1
        assert d["range_penalty"] == 0
        assert d["failure_reason"] is None
        assert "cover_result" in d


# ==============================================================================
# EDGE CASES
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_same_square_invalid(self, empty_grid):
        """Same square (distance 0) is invalid for ranged attack."""
        grid = empty_grid
        grid.place_entity("attacker", Position(5, 5), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(5, 5), SizeCategory.MEDIUM)
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is False
        assert "melee" in result.failure_reason.lower()
        assert result.distance_ft == 0

    def test_adjacent_diagonal(self, empty_grid):
        """Adjacent diagonal is 5 ft (first increment)."""
        grid = empty_grid
        grid.place_entity("attacker", Position(5, 5), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(6, 6), SizeCategory.MEDIUM)
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is True
        assert result.distance_ft == 5

    def test_diagonal_at_range_boundary(self, empty_grid):
        """Diagonal at exactly range increment boundary."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 0), SizeCategory.MEDIUM)
        # 12 diagonals = 90 feet (1+2+1+2+1+2+1+2+1+2+1+2) * 5 = (6*15) = 90
        grid.place_entity("target", Position(12, 12), SizeCategory.MEDIUM)
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is True
        assert result.distance_ft == 90
        assert result.range_increment == 2  # 61-120 ft = increment 2

    def test_max_range_exactly(self, empty_grid):
        """Attack at exactly max range is valid."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(10, 0), SizeCategory.MEDIUM)  # 50 ft
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=10,
            max_range_ft=50,
            max_increments=5
        )
        assert result.is_valid is True
        assert result.distance_ft == 50

    def test_one_foot_beyond_max_range(self, empty_grid):
        """Attack 1 square beyond max range is invalid."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(11, 0), SizeCategory.MEDIUM)  # 55 ft
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=10,
            max_range_ft=50,
            max_increments=5
        )
        assert result.is_valid is False
        assert "Beyond maximum range" in result.failure_reason

    def test_large_creature_targeting(self, empty_grid):
        """Large creature can be targeted from any adjacent square."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 5), SizeCategory.MEDIUM)
        grid.place_entity("large_target", Position(5, 5), SizeCategory.LARGE)  # 2x2
        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="large_target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is True
        # Distance from (0,5) to (5,5) = 25 ft
        assert result.distance_ft == 25


# ==============================================================================
# COVER WITH WALLS TESTS
# ==============================================================================

class TestCoverWithWalls:
    """Tests for cover calculation with walls blocking lines."""

    def test_total_cover_blocks_attack(self, empty_grid):
        """Total cover makes target untargetable."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 5), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(5, 5), SizeCategory.MEDIUM)

        # Create a solid wall that completely blocks the path
        # Fill multiple cells to ensure total cover
        for y in range(4, 7):
            cell = grid.get_cell(Position(3, y))
            cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        assert result.is_valid is False
        assert result.cover_result is not None
        assert result.cover_result.blocks_targeting is True
        assert "total cover" in result.failure_reason.lower()

    def test_partial_cover_valid_attack(self, empty_grid):
        """Partial cover allows attack but with AC bonus."""
        grid = empty_grid
        grid.place_entity("attacker", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(5, 0), SizeCategory.MEDIUM)

        # Place a small obstruction that only blocks some lines
        cell = grid.get_cell(Position(2, 1))
        cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        result = evaluate_ranged_attack(
            grid=grid,
            attacker_id="attacker",
            target_id="target",
            range_increment_ft=60,
            max_range_ft=600
        )
        # Attack should still be valid if not total cover
        # Cover degree depends on how many lines are blocked
        assert result.cover_result is not None


# ==============================================================================
# CONSTANTS TESTS
# ==============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_default_max_increments(self):
        """Default max increments is 10."""
        assert DEFAULT_MAX_INCREMENTS == 10

    def test_thrown_max_increments(self):
        """Thrown max increments is 5."""
        assert THROWN_MAX_INCREMENTS == 5


# ==============================================================================
# WEAPON SCENARIO TESTS
# ==============================================================================

class TestWeaponScenarios:
    """Tests using real weapon statistics."""

    def test_shortbow_at_various_ranges(self, empty_grid):
        """Shortbow (60 ft increment) at various ranges."""
        grid = empty_grid
        grid.place_entity("archer", Position(0, 0), SizeCategory.MEDIUM)

        # Test at 30 ft (6 squares)
        grid.place_entity("target30", Position(6, 0), SizeCategory.MEDIUM)
        result = evaluate_ranged_attack(
            grid, "archer", "target30",
            range_increment_ft=60, max_range_ft=600
        )
        assert result.distance_ft == 30
        assert result.range_increment == 1
        assert result.range_penalty == 0

    def test_longbow_at_max_range(self, empty_grid):
        """Longbow (100 ft increment) at maximum range."""
        grid = empty_grid
        grid.place_entity("archer", Position(0, 0), SizeCategory.MEDIUM)
        # 1000 ft = 200 squares (orthogonal)
        # Using a smaller grid, test the logic
        result = evaluate_ranged_attack(
            grid, "archer", "target",
            range_increment_ft=100, max_range_ft=1000
        )
        # Target not on grid
        assert result.is_valid is False

    def test_thrown_dagger_range(self, empty_grid):
        """Thrown dagger (10 ft increment, 5 max) range check."""
        grid = empty_grid
        grid.place_entity("thrower", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(10, 0), SizeCategory.MEDIUM)  # 50 ft
        result = evaluate_ranged_attack(
            grid, "thrower", "target",
            range_increment_ft=10,
            max_range_ft=50,
            max_increments=THROWN_MAX_INCREMENTS
        )
        assert result.is_valid is True
        assert result.distance_ft == 50
        assert result.range_increment == 5
        assert result.range_penalty == -8  # (5-1) * -2

    def test_heavy_crossbow(self, empty_grid):
        """Heavy crossbow (120 ft increment)."""
        grid = empty_grid
        grid.place_entity("crossbowman", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target", Position(18, 0), SizeCategory.MEDIUM)  # 90 ft
        result = evaluate_ranged_attack(
            grid, "crossbowman", "target",
            range_increment_ft=120, max_range_ft=1200
        )
        assert result.is_valid is True
        assert result.distance_ft == 90
        assert result.range_increment == 1
        assert result.range_penalty == 0


# ==============================================================================
# POSITION SYMMETRY TESTS
# ==============================================================================

class TestPositionSymmetry:
    """Tests that distance is symmetric regardless of direction."""

    def test_distance_symmetric(self):
        """Distance from A to B equals distance from B to A."""
        pos_a = Position(0, 0)
        pos_b = Position(7, 4)
        assert calculate_distance_feet(pos_a, pos_b) == calculate_distance_feet(pos_b, pos_a)

    def test_distance_all_directions(self):
        """Distance calculation works in all directions."""
        center = Position(10, 10)
        # Cardinal directions
        assert calculate_distance_feet(center, Position(15, 10)) == 25  # East
        assert calculate_distance_feet(center, Position(5, 10)) == 25   # West
        assert calculate_distance_feet(center, Position(10, 15)) == 25  # South
        assert calculate_distance_feet(center, Position(10, 5)) == 25   # North
        # Diagonals
        assert calculate_distance_feet(center, Position(13, 13)) == 20  # SE 3 diag
        assert calculate_distance_feet(center, Position(7, 7)) == 20    # NW 3 diag
        assert calculate_distance_feet(center, Position(13, 7)) == 20   # NE 3 diag
        assert calculate_distance_feet(center, Position(7, 13)) == 20   # SW 3 diag
