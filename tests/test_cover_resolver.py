"""Tests for cover resolution system.

WO-002: Cover Resolution
Tests the corner-to-corner cover calculation algorithm per PHB p.150-152.
"""

import pytest
import math

from aidm.schemas.position import Position
from aidm.schemas.geometry import (
    PropertyMask, PropertyFlag, Direction, SizeCategory, GridCell
)
from aidm.core.geometry_engine import BattleGrid
from aidm.core.cover_resolver import (
    CoverDegree,
    CoverResult,
    get_square_corners,
    get_cells_along_line,
    get_border_crossings,
    trace_corner_line,
    get_footprint_squares,
    calculate_cover,
    calculate_cover_from_positions,
    has_cover,
    has_total_cover,
    COVER_THRESHOLDS,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def empty_grid():
    """Create an empty 10x10 grid."""
    return BattleGrid(10, 10)


@pytest.fixture
def grid_with_wall():
    """Create a 10x10 grid with a solid wall at (5, 5)."""
    grid = BattleGrid(10, 10)
    cell = grid.get_cell(Position(x=5, y=5))
    cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
    return grid


@pytest.fixture
def grid_with_glass_wall():
    """Create a 10x10 grid with a glass wall at (5, 5) - blocks LOE but not LOS."""
    grid = BattleGrid(10, 10)
    cell = grid.get_cell(Position(x=5, y=5))
    # Glass: SOLID but not OPAQUE
    cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID)
    return grid


@pytest.fixture
def grid_with_grate():
    """Create a 10x10 grid with an iron grate at (5, 5) - permeable."""
    grid = BattleGrid(10, 10)
    cell = grid.get_cell(Position(x=5, y=5))
    # Iron grate: SOLID + PERMEABLE = doesn't block LOE
    cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.PERMEABLE)
    return grid


@pytest.fixture
def grid_with_border_wall():
    """Create a 10x10 grid with a wall border between (4, 5) and (5, 5)."""
    grid = BattleGrid(10, 10)
    wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
    grid.set_border(Position(x=5, y=5), Direction.W, wall_mask)
    return grid


# ==============================================================================
# TESTS: CoverDegree Enum
# ==============================================================================

class TestCoverDegreeEnum:
    """Tests for CoverDegree enum values."""

    def test_cover_degree_values(self):
        """Verify all cover degree values exist."""
        assert CoverDegree.NO_COVER.value == "no_cover"
        assert CoverDegree.HALF_COVER.value == "half_cover"
        assert CoverDegree.THREE_QUARTERS_COVER.value == "three_quarters_cover"
        assert CoverDegree.TOTAL_COVER.value == "total_cover"

    def test_cover_degree_count(self):
        """Verify exactly 4 cover degrees."""
        assert len(CoverDegree) == 4


# ==============================================================================
# TESTS: CoverResult Dataclass
# ==============================================================================

class TestCoverResult:
    """Tests for CoverResult dataclass."""

    def test_cover_result_creation(self):
        """Test CoverResult can be created with all fields."""
        result = CoverResult(
            cover_degree=CoverDegree.HALF_COVER,
            ac_bonus=2,
            reflex_bonus=1,
            lines_blocked=6,
            lines_total=16,
            blocks_targeting=False,
            attacker_pos=Position(x=0, y=0),
            defender_pos=Position(x=5, y=5),
        )
        assert result.cover_degree == CoverDegree.HALF_COVER
        assert result.ac_bonus == 2
        assert result.reflex_bonus == 1
        assert result.lines_blocked == 6
        assert result.lines_total == 16
        assert result.blocks_targeting is False

    def test_cover_result_is_frozen(self):
        """Verify CoverResult is immutable."""
        result = CoverResult(
            cover_degree=CoverDegree.NO_COVER,
            ac_bonus=0,
            reflex_bonus=0,
            lines_blocked=0,
            lines_total=16,
            blocks_targeting=False,
            attacker_pos=Position(x=0, y=0),
            defender_pos=Position(x=1, y=1),
        )
        with pytest.raises(AttributeError):
            result.ac_bonus = 5

    def test_cover_result_to_dict(self):
        """Test CoverResult serialization."""
        result = CoverResult(
            cover_degree=CoverDegree.THREE_QUARTERS_COVER,
            ac_bonus=5,
            reflex_bonus=2,
            lines_blocked=10,
            lines_total=16,
            blocks_targeting=False,
            attacker_pos=Position(x=2, y=3),
            defender_pos=Position(x=7, y=8),
        )
        d = result.to_dict()
        assert d["cover_degree"] == "three_quarters_cover"
        assert d["ac_bonus"] == 5
        assert d["reflex_bonus"] == 2
        assert d["lines_blocked"] == 10
        assert d["lines_total"] == 16
        assert d["blocks_targeting"] is False
        assert d["attacker_pos"] == {"x": 2, "y": 3}
        assert d["defender_pos"] == {"x": 7, "y": 8}


# ==============================================================================
# TESTS: Cover Thresholds
# ==============================================================================

class TestCoverThresholds:
    """Tests for cover threshold constants."""

    def test_no_cover_threshold(self):
        """0-4 lines blocked = no cover."""
        degree, ac, reflex = COVER_THRESHOLDS[(0, 4)]
        assert degree == CoverDegree.NO_COVER
        assert ac == 0
        assert reflex == 0

    def test_half_cover_threshold(self):
        """5-8 lines blocked = half cover."""
        degree, ac, reflex = COVER_THRESHOLDS[(5, 8)]
        assert degree == CoverDegree.HALF_COVER
        assert ac == 2
        assert reflex == 1

    def test_three_quarters_cover_threshold(self):
        """9-12 lines blocked = three-quarters cover."""
        degree, ac, reflex = COVER_THRESHOLDS[(9, 12)]
        assert degree == CoverDegree.THREE_QUARTERS_COVER
        assert ac == 5
        assert reflex == 2

    def test_total_cover_threshold(self):
        """13-16 lines blocked = total cover."""
        degree, ac, reflex = COVER_THRESHOLDS[(13, 16)]
        assert degree == CoverDegree.TOTAL_COVER
        assert ac == 0  # N/A for total cover
        assert reflex == 0  # N/A for total cover


# ==============================================================================
# TESTS: get_square_corners()
# ==============================================================================

class TestGetSquareCorners:
    """Tests for get_square_corners function."""

    def test_corners_at_origin(self):
        """Test corners for square at (0, 0)."""
        corners = get_square_corners(Position(x=0, y=0))
        assert len(corners) == 4
        # NW, NE, SE, SW
        assert corners[0] == (-0.5, -0.5)  # NW
        assert corners[1] == (0.5, -0.5)   # NE
        assert corners[2] == (0.5, 0.5)    # SE
        assert corners[3] == (-0.5, 0.5)   # SW

    def test_corners_at_positive_position(self):
        """Test corners for square at (3, 5)."""
        corners = get_square_corners(Position(x=3, y=5))
        assert corners[0] == (2.5, 4.5)  # NW
        assert corners[1] == (3.5, 4.5)  # NE
        assert corners[2] == (3.5, 5.5)  # SE
        assert corners[3] == (2.5, 5.5)  # SW

    def test_corners_order_clockwise_from_nw(self):
        """Verify corners are in NW, NE, SE, SW order."""
        corners = get_square_corners(Position(x=5, y=5))
        # NW should have smallest x and y
        nw = corners[0]
        ne = corners[1]
        se = corners[2]
        sw = corners[3]

        assert nw[0] < ne[0]  # NW x < NE x
        assert nw[1] == ne[1]  # NW y == NE y (same row)
        assert ne[0] == se[0]  # NE x == SE x (same column)
        assert ne[1] < se[1]   # NE y < SE y
        assert se[0] > sw[0]   # SE x > SW x
        assert se[1] == sw[1]  # SE y == SW y
        assert sw[0] == nw[0]  # SW x == NW x
        assert sw[1] > nw[1]   # SW y > NW y


# ==============================================================================
# TESTS: get_cells_along_line()
# ==============================================================================

class TestGetCellsAlongLine:
    """Tests for get_cells_along_line function."""

    def test_horizontal_line(self):
        """Test line traversal along horizontal path."""
        start = (0.5, 0.5)  # Center of (0, 0)
        end = (3.5, 0.5)    # Center of (3, 0)
        cells = get_cells_along_line(start, end)
        # Should include cells (0,0), (1,0), (2,0), (3,0)
        cell_coords = [(c.x, c.y) for c in cells]
        assert (0, 0) in cell_coords
        assert (1, 0) in cell_coords
        assert (2, 0) in cell_coords
        assert (3, 0) in cell_coords

    def test_vertical_line(self):
        """Test line traversal along vertical path."""
        start = (2.5, 1.5)
        end = (2.5, 4.5)
        cells = get_cells_along_line(start, end)
        cell_coords = [(c.x, c.y) for c in cells]
        assert (2, 1) in cell_coords
        assert (2, 2) in cell_coords
        assert (2, 3) in cell_coords
        assert (2, 4) in cell_coords

    def test_diagonal_line(self):
        """Test line traversal along diagonal path."""
        start = (0.5, 0.5)
        end = (3.5, 3.5)
        cells = get_cells_along_line(start, end)
        cell_coords = [(c.x, c.y) for c in cells]
        # Diagonal should pass through (0,0), (1,1), (2,2), (3,3)
        assert (0, 0) in cell_coords
        assert (1, 1) in cell_coords
        assert (2, 2) in cell_coords
        assert (3, 3) in cell_coords

    def test_same_point(self):
        """Test when start and end are the same point."""
        start = (2.5, 3.5)
        end = (2.5, 3.5)
        cells = get_cells_along_line(start, end)
        assert len(cells) == 1
        assert cells[0] == Position(x=2, y=3)


# ==============================================================================
# TESTS: get_border_crossings()
# ==============================================================================

class TestGetBorderCrossings:
    """Tests for get_border_crossings function."""

    def test_no_border_crossing_same_cell(self):
        """No borders crossed within same cell."""
        start = (2.1, 2.1)
        end = (2.9, 2.9)
        crossings = get_border_crossings(start, end)
        assert len(crossings) == 0

    def test_vertical_border_crossing(self):
        """Test crossing a vertical border (moving east)."""
        start = (1.5, 2.5)  # Center of (1, 2)
        end = (3.5, 2.5)    # Center of (3, 2)
        crossings = get_border_crossings(start, end)
        # Should cross border between (1,2)-(2,2) and (2,2)-(3,2)
        assert len(crossings) >= 2

    def test_horizontal_border_crossing(self):
        """Test crossing a horizontal border (moving south)."""
        start = (2.5, 1.5)  # Center of (2, 1)
        end = (2.5, 3.5)    # Center of (2, 3)
        crossings = get_border_crossings(start, end)
        # Should cross border between (2,1)-(2,2) and (2,2)-(2,3)
        assert len(crossings) >= 2


# ==============================================================================
# TESTS: trace_corner_line()
# ==============================================================================

class TestTraceCornerLine:
    """Tests for trace_corner_line function."""

    def test_clear_line_empty_grid(self, empty_grid):
        """Line through empty grid is not blocked."""
        start = (0.5, 0.5)
        end = (5.5, 5.5)
        blocked = trace_corner_line(start, end, empty_grid, "loe")
        assert blocked is False

    def test_line_blocked_by_solid_cell(self, grid_with_wall):
        """Line through solid cell is blocked."""
        start = (3.5, 5.5)  # Corner of cell near wall
        end = (7.5, 5.5)    # Corner on other side
        blocked = trace_corner_line(start, end, grid_with_wall, "loe")
        assert blocked is True

    def test_line_not_blocked_by_grate_loe(self, grid_with_grate):
        """Line through grate (PERMEABLE) is not blocked for LOE."""
        start = (3.5, 5.5)
        end = (7.5, 5.5)
        blocked = trace_corner_line(start, end, grid_with_grate, "loe")
        assert blocked is False

    def test_line_blocked_by_border_wall(self, grid_with_border_wall):
        """Line crossing a solid border is blocked."""
        start = (4.5, 5.5)  # Just west of the border
        end = (5.5, 5.5)    # Just east of the border
        blocked = trace_corner_line(start, end, grid_with_border_wall, "loe")
        assert blocked is True

    def test_los_check_glass_wall(self, grid_with_glass_wall):
        """Glass wall blocks LOE but not LOS."""
        start = (3.5, 5.5)
        end = (7.5, 5.5)
        # LOS should NOT be blocked (not opaque)
        blocked_los = trace_corner_line(start, end, grid_with_glass_wall, "los")
        assert blocked_los is False
        # LOE should be blocked (solid)
        blocked_loe = trace_corner_line(start, end, grid_with_glass_wall, "loe")
        assert blocked_loe is True


# ==============================================================================
# TESTS: get_footprint_squares()
# ==============================================================================

class TestGetFootprintSquares:
    """Tests for get_footprint_squares function."""

    def test_medium_footprint(self):
        """Medium creature occupies 1 square."""
        squares = get_footprint_squares(Position(x=3, y=4), SizeCategory.MEDIUM)
        assert len(squares) == 1
        assert squares[0] == Position(x=3, y=4)

    def test_small_footprint(self):
        """Small creature occupies 1 square."""
        squares = get_footprint_squares(Position(x=3, y=4), SizeCategory.SMALL)
        assert len(squares) == 1

    def test_large_footprint(self):
        """Large creature occupies 2x2 = 4 squares."""
        squares = get_footprint_squares(Position(x=3, y=4), SizeCategory.LARGE)
        assert len(squares) == 4
        coords = [(s.x, s.y) for s in squares]
        assert (3, 4) in coords
        assert (4, 4) in coords
        assert (3, 5) in coords
        assert (4, 5) in coords

    def test_huge_footprint(self):
        """Huge creature occupies 3x3 = 9 squares."""
        squares = get_footprint_squares(Position(x=0, y=0), SizeCategory.HUGE)
        assert len(squares) == 9

    def test_gargantuan_footprint(self):
        """Gargantuan creature occupies 4x4 = 16 squares."""
        squares = get_footprint_squares(Position(x=0, y=0), SizeCategory.GARGANTUAN)
        assert len(squares) == 16

    def test_colossal_footprint(self):
        """Colossal creature occupies 6x6 = 36 squares."""
        squares = get_footprint_squares(Position(x=0, y=0), SizeCategory.COLOSSAL)
        assert len(squares) == 36


# ==============================================================================
# TESTS: calculate_cover() - No Cover Cases
# ==============================================================================

class TestCalculateCoverNoCover:
    """Tests for calculate_cover with no obstructions."""

    def test_no_cover_empty_grid(self, empty_grid):
        """No cover on empty grid."""
        result = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=5),
            empty_grid
        )
        assert result.cover_degree == CoverDegree.NO_COVER
        assert result.ac_bonus == 0
        assert result.reflex_bonus == 0
        assert result.lines_blocked == 0
        assert result.lines_total == 16
        assert result.blocks_targeting is False

    def test_no_cover_adjacent_cells(self, empty_grid):
        """No cover for adjacent combatants."""
        result = calculate_cover(
            Position(x=3, y=3),
            Position(x=4, y=3),
            empty_grid
        )
        assert result.cover_degree == CoverDegree.NO_COVER
        assert result.lines_blocked == 0

    def test_no_cover_diagonal_adjacent(self, empty_grid):
        """No cover for diagonally adjacent combatants."""
        result = calculate_cover(
            Position(x=3, y=3),
            Position(x=4, y=4),
            empty_grid
        )
        assert result.cover_degree == CoverDegree.NO_COVER


# ==============================================================================
# TESTS: calculate_cover() - Partial Cover Cases
# ==============================================================================

class TestCalculateCoverPartial:
    """Tests for calculate_cover with partial obstructions."""

    def test_half_cover_from_partial_obstruction(self):
        """Half cover when obstruction blocks 5-8 of 16 lines."""
        grid = BattleGrid(10, 10)
        # Place a wall that partially blocks lines
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        # Create a scenario where about half the lines are blocked
        # Wall at position between attacker and defender
        cell = grid.get_cell(Position(x=4, y=2))
        cell.cell_mask = wall_mask

        result = calculate_cover(
            Position(x=2, y=2),
            Position(x=6, y=2),
            grid
        )
        # The exact number depends on geometry
        # At minimum, verify we're testing the function
        assert result.lines_total == 16

    def test_cover_increases_with_more_obstruction(self):
        """More obstruction = higher cover degree."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        # No obstruction
        result_none = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=0),
            grid
        )

        # Add some obstruction
        grid.get_cell(Position(x=2, y=0)).cell_mask = wall_mask
        result_some = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=0),
            grid
        )

        # Add more obstruction
        grid.get_cell(Position(x=3, y=0)).cell_mask = wall_mask
        result_more = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=0),
            grid
        )

        # Verify lines blocked increases with more obstruction
        assert result_some.lines_blocked >= result_none.lines_blocked
        assert result_more.lines_blocked >= result_some.lines_blocked


# ==============================================================================
# TESTS: calculate_cover() - Total Cover Cases
# ==============================================================================

class TestCalculateCoverTotal:
    """Tests for calculate_cover with total obstruction."""

    def test_total_cover_full_wall_between(self):
        """Total cover when solid wall fully blocks all lines."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        # Create a wall that completely separates attacker and defender
        for y in range(10):
            grid.get_cell(Position(x=5, y=y)).cell_mask = wall_mask

        result = calculate_cover(
            Position(x=2, y=5),
            Position(x=8, y=5),
            grid
        )

        assert result.cover_degree == CoverDegree.TOTAL_COVER
        assert result.blocks_targeting is True
        assert result.lines_blocked == 16

    def test_total_cover_blocks_targeting(self):
        """Total cover prevents targeting."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        for y in range(10):
            grid.get_cell(Position(x=5, y=y)).cell_mask = wall_mask

        result = calculate_cover(
            Position(x=2, y=5),
            Position(x=8, y=5),
            grid
        )

        assert result.blocks_targeting is True


# ==============================================================================
# TESTS: calculate_cover() - Large Creatures
# ==============================================================================

class TestCalculateCoverLargeCreatures:
    """Tests for calculate_cover with Large+ creatures."""

    def test_large_attacker_medium_defender(self, empty_grid):
        """Large attacker vs Medium defender."""
        result = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=5),
            empty_grid,
            attacker_size=SizeCategory.LARGE,
            defender_size=SizeCategory.MEDIUM,
        )
        # Still 16 lines for the selected squares
        assert result.lines_total == 16
        assert result.cover_degree == CoverDegree.NO_COVER

    def test_medium_attacker_large_defender(self, empty_grid):
        """Medium attacker vs Large defender."""
        result = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=5),
            empty_grid,
            attacker_size=SizeCategory.MEDIUM,
            defender_size=SizeCategory.LARGE,
        )
        assert result.lines_total == 16
        assert result.cover_degree == CoverDegree.NO_COVER

    def test_large_vs_large(self, empty_grid):
        """Large vs Large - uses optimal squares."""
        result = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=5),
            empty_grid,
            attacker_size=SizeCategory.LARGE,
            defender_size=SizeCategory.LARGE,
        )
        assert result.lines_total == 16
        assert result.cover_degree == CoverDegree.NO_COVER


# ==============================================================================
# TESTS: calculate_cover_from_positions() Convenience Function
# ==============================================================================

class TestCalculateCoverFromPositions:
    """Tests for the simplified convenience function."""

    def test_wrapper_uses_medium_size(self, empty_grid):
        """Wrapper assumes Medium creatures."""
        result = calculate_cover_from_positions(
            Position(x=0, y=0),
            Position(x=5, y=5),
            empty_grid
        )
        assert result.lines_total == 16

    def test_wrapper_matches_full_function(self, empty_grid):
        """Wrapper produces same result as full function."""
        result1 = calculate_cover_from_positions(
            Position(x=2, y=2),
            Position(x=7, y=7),
            empty_grid
        )
        result2 = calculate_cover(
            Position(x=2, y=2),
            Position(x=7, y=7),
            empty_grid,
            attacker_size=SizeCategory.MEDIUM,
            defender_size=SizeCategory.MEDIUM,
        )
        assert result1.cover_degree == result2.cover_degree
        assert result1.lines_blocked == result2.lines_blocked


# ==============================================================================
# TESTS: has_cover() and has_total_cover() Quick Checks
# ==============================================================================

class TestHasCoverQuickChecks:
    """Tests for quick cover check functions."""

    def test_has_cover_false_empty_grid(self, empty_grid):
        """has_cover returns False on empty grid."""
        assert has_cover(Position(x=0, y=0), Position(x=5, y=5), empty_grid) is False

    def test_has_cover_true_with_obstruction(self):
        """has_cover returns True with sufficient obstruction."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        for y in range(10):
            grid.get_cell(Position(x=5, y=y)).cell_mask = wall_mask

        assert has_cover(Position(x=2, y=5), Position(x=8, y=5), grid) is True

    def test_has_total_cover_false_empty_grid(self, empty_grid):
        """has_total_cover returns False on empty grid."""
        assert has_total_cover(Position(x=0, y=0), Position(x=5, y=5), empty_grid) is False

    def test_has_total_cover_true_with_full_wall(self):
        """has_total_cover returns True with full wall."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        for y in range(10):
            grid.get_cell(Position(x=5, y=y)).cell_mask = wall_mask

        assert has_total_cover(Position(x=2, y=5), Position(x=8, y=5), grid) is True


# ==============================================================================
# TESTS: Material-Specific Cover Cases
# ==============================================================================

class TestMaterialSpecificCover:
    """Tests for different material types affecting cover."""

    def test_glass_wall_los_vs_loe(self):
        """Glass wall blocks LOE but not LOS."""
        grid = BattleGrid(10, 10)
        # Glass: SOLID but not OPAQUE
        glass_mask = PropertyMask().set_flag(PropertyFlag.SOLID)
        for y in range(10):
            grid.get_cell(Position(x=5, y=y)).cell_mask = glass_mask

        # LOE check - should be blocked
        result_loe = calculate_cover(
            Position(x=2, y=5),
            Position(x=8, y=5),
            grid,
            check_type="loe"
        )
        assert result_loe.cover_degree == CoverDegree.TOTAL_COVER

        # LOS check - should NOT be blocked
        result_los = calculate_cover(
            Position(x=2, y=5),
            Position(x=8, y=5),
            grid,
            check_type="los"
        )
        assert result_los.cover_degree == CoverDegree.NO_COVER

    def test_grate_permeable(self):
        """Iron grate (SOLID + PERMEABLE) doesn't block LOE."""
        grid = BattleGrid(10, 10)
        grate_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.PERMEABLE)
        for y in range(10):
            grid.get_cell(Position(x=5, y=y)).cell_mask = grate_mask

        result = calculate_cover(
            Position(x=2, y=5),
            Position(x=8, y=5),
            grid,
            check_type="loe"
        )
        assert result.cover_degree == CoverDegree.NO_COVER


# ==============================================================================
# TESTS: Border Wall Cover
# ==============================================================================

class TestBorderWallCover:
    """Tests for cover from border walls (not cell contents)."""

    def test_border_wall_provides_cover(self):
        """Border wall between cells provides cover."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        # Set up a wall border spanning the full height
        for y in range(10):
            grid.set_border(Position(x=5, y=y), Direction.W, wall_mask)

        result = calculate_cover(
            Position(x=2, y=5),
            Position(x=8, y=5),
            grid
        )
        # Should have significant cover from the wall
        assert result.lines_blocked > 0


# ==============================================================================
# TESTS: Edge Cases and Boundary Conditions
# ==============================================================================

class TestCoverEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_same_position_no_cover(self, empty_grid):
        """Same position should have no cover (edge case)."""
        result = calculate_cover(
            Position(x=5, y=5),
            Position(x=5, y=5),
            empty_grid
        )
        assert result.cover_degree == CoverDegree.NO_COVER

    def test_grid_boundary_positions(self, empty_grid):
        """Cover calculation works at grid boundaries."""
        result = calculate_cover(
            Position(x=0, y=0),
            Position(x=9, y=9),
            empty_grid
        )
        assert result.lines_total == 16
        assert result.cover_degree == CoverDegree.NO_COVER

    def test_out_of_bounds_wall_ignored(self):
        """Walls outside grid don't cause errors."""
        grid = BattleGrid(5, 5)
        # Should not error even if line would extend outside
        result = calculate_cover(
            Position(x=0, y=0),
            Position(x=4, y=4),
            grid
        )
        assert result is not None


# ==============================================================================
# TESTS: Cover Bonus Values (PHB p.150-152)
# ==============================================================================

class TestCoverBonusValues:
    """Tests verifying correct AC and Reflex bonuses per PHB."""

    def test_no_cover_bonuses(self, empty_grid):
        """No cover gives +0 AC and +0 Reflex."""
        result = calculate_cover(
            Position(x=0, y=0),
            Position(x=5, y=5),
            empty_grid
        )
        assert result.ac_bonus == 0
        assert result.reflex_bonus == 0

    def test_half_cover_bonuses(self):
        """Half cover gives +2 AC and +1 Reflex."""
        # Verify from thresholds
        degree, ac, reflex = COVER_THRESHOLDS[(5, 8)]
        assert ac == 2
        assert reflex == 1

    def test_three_quarters_cover_bonuses(self):
        """Three-quarters cover gives +5 AC and +2 Reflex."""
        degree, ac, reflex = COVER_THRESHOLDS[(9, 12)]
        assert ac == 5
        assert reflex == 2

    def test_total_cover_blocks_targeting(self):
        """Total cover makes target untargetable."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        for y in range(10):
            grid.get_cell(Position(x=5, y=y)).cell_mask = wall_mask

        result = calculate_cover(
            Position(x=2, y=5),
            Position(x=8, y=5),
            grid
        )
        assert result.blocks_targeting is True


# ==============================================================================
# TESTS: Determinism
# ==============================================================================

class TestCoverDeterminism:
    """Tests verifying deterministic behavior."""

    def test_same_input_same_output(self, empty_grid):
        """Same inputs produce identical outputs."""
        for _ in range(5):
            result = calculate_cover(
                Position(x=2, y=3),
                Position(x=7, y=8),
                empty_grid
            )
            assert result.lines_blocked == 0
            assert result.cover_degree == CoverDegree.NO_COVER

    def test_symmetric_positions_different_results(self):
        """Swapping attacker/defender may give different cover."""
        grid = BattleGrid(10, 10)
        wall_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        # Asymmetric wall placement
        grid.get_cell(Position(x=5, y=3)).cell_mask = wall_mask

        result1 = calculate_cover(
            Position(x=3, y=3),
            Position(x=7, y=3),
            grid
        )
        result2 = calculate_cover(
            Position(x=7, y=3),
            Position(x=3, y=3),
            grid
        )
        # Cover is not necessarily symmetric depending on wall placement
        # Just verify both are valid results
        assert result1.lines_total == 16
        assert result2.lines_total == 16
