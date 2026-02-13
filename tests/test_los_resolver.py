"""Tests for LOS/LOE resolution system.

WO-003: LOS/LOE Resolution
Tests cover:
- bresenham_3d algorithm (integer arithmetic, various directions)
- check_los (OPAQUE blocking, PERMEABLE exceptions, height occlusion)
- check_loe (SOLID blocking, PERMEABLE exceptions)
- Entity convenience functions
- Barrier truth table cases
- Edge cases (same cell, adjacent, out of bounds)
"""

import pytest

from aidm.schemas.position import Position
from aidm.schemas.geometry import (
    PropertyMask, PropertyFlag, Direction, SizeCategory, GridCell
)
from aidm.core.geometry_engine import BattleGrid
from aidm.core.los_resolver import (
    bresenham_3d,
    check_los,
    check_loe,
    check_los_between_entities,
    check_loe_between_entities,
    LOSResult,
    LOEResult,
    DEFAULT_ENTITY_HEIGHT,
)


# ==============================================================================
# BRESENHAM 3D TESTS
# ==============================================================================

class TestBresenham3D:
    """Tests for the 3D Bresenham line algorithm."""

    def test_horizontal_line_same_y_same_z(self):
        """Horizontal line along X axis."""
        result = bresenham_3d((0, 0, 0), (5, 0, 0))
        assert result == [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 0, 0), (5, 0, 0)]

    def test_horizontal_line_negative_direction(self):
        """Horizontal line along negative X axis."""
        result = bresenham_3d((5, 0, 0), (0, 0, 0))
        assert result == [(5, 0, 0), (4, 0, 0), (3, 0, 0), (2, 0, 0), (1, 0, 0), (0, 0, 0)]

    def test_vertical_line_same_x_same_z(self):
        """Vertical line along Y axis."""
        result = bresenham_3d((0, 0, 0), (0, 5, 0))
        assert result == [(0, 0, 0), (0, 1, 0), (0, 2, 0), (0, 3, 0), (0, 4, 0), (0, 5, 0)]

    def test_z_axis_line(self):
        """Line along Z axis only."""
        result = bresenham_3d((0, 0, 0), (0, 0, 5))
        assert result == [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (0, 0, 5)]

    def test_diagonal_line_2d_same_z(self):
        """Diagonal line in XY plane (same Z)."""
        result = bresenham_3d((0, 0, 0), (3, 3, 0))
        assert len(result) == 4  # 0,1,2,3
        assert result[0] == (0, 0, 0)
        assert result[-1] == (3, 3, 0)
        # All points should have z=0
        for x, y, z in result:
            assert z == 0

    def test_3d_diagonal(self):
        """True 3D diagonal line."""
        result = bresenham_3d((0, 0, 0), (3, 3, 3))
        assert result[0] == (0, 0, 0)
        assert result[-1] == (3, 3, 3)
        # Should have 4 points
        assert len(result) == 4

    def test_single_point_start_equals_end(self):
        """Single point when start == end."""
        result = bresenham_3d((5, 5, 5), (5, 5, 5))
        assert result == [(5, 5, 5)]

    def test_integer_arithmetic_only(self):
        """Verify all output coordinates are integers, no floats."""
        result = bresenham_3d((0, 0, 0), (7, 11, 5))
        for x, y, z in result:
            assert isinstance(x, int), f"x={x} is not int"
            assert isinstance(y, int), f"y={y} is not int"
            assert isinstance(z, int), f"z={z} is not int"

    def test_includes_start_and_end(self):
        """Both start and end points are included."""
        start = (1, 2, 3)
        end = (10, 8, 15)
        result = bresenham_3d(start, end)
        assert result[0] == start
        assert result[-1] == end

    def test_asymmetric_deltas(self):
        """Test with very different deltas to stress the algorithm."""
        result = bresenham_3d((0, 0, 0), (10, 2, 1))
        assert result[0] == (0, 0, 0)
        assert result[-1] == (10, 2, 1)
        # Should have 11 points (primary axis is X with delta 10)
        assert len(result) == 11


# ==============================================================================
# LOS TESTS
# ==============================================================================

class TestCheckLOS:
    """Tests for line of sight checking."""

    def test_clear_los_across_empty_grid(self):
        """LOS is clear across empty grid."""
        grid = BattleGrid(10, 10)
        observer = Position(x=0, y=0)
        target = Position(x=5, y=5)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is True
        assert result.blocking_position is None
        assert result.blocking_reason is None

    def test_los_blocked_by_opaque_cell(self):
        """LOS blocked by OPAQUE cell in the path."""
        grid = BattleGrid(10, 10)

        # Place opaque wall in the middle
        wall_pos = Position(x=2, y=2)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.cell_mask = PropertyMask().set_flag(PropertyFlag.OPAQUE)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=5)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_position == wall_pos
        assert result.blocking_reason == "cell_opaque"

    def test_los_blocked_by_opaque_border(self):
        """LOS blocked by OPAQUE border."""
        grid = BattleGrid(10, 10)

        # Place opaque border on the east side of cell (0, 0)
        opaque_mask = PropertyMask().set_flag(PropertyFlag.OPAQUE)
        grid.set_border(Position(x=0, y=0), Direction.E, opaque_mask)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_reason == "border_opaque"

    def test_los_not_blocked_by_solid_only_cell(self):
        """LOS NOT blocked by SOLID-only cell (glass wall case)."""
        grid = BattleGrid(10, 10)

        # Place glass wall (SOLID but not OPAQUE)
        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is True

    def test_los_not_blocked_by_opaque_permeable_cell(self):
        """LOS NOT blocked by OPAQUE + PERMEABLE cell (magical darkness)."""
        grid = BattleGrid(10, 10)

        # Place magical darkness (OPAQUE + PERMEABLE)
        dark_pos = Position(x=2, y=0)
        dark_cell = grid.get_cell(dark_pos)
        dark_cell.cell_mask = (
            PropertyMask()
            .set_flag(PropertyFlag.OPAQUE)
            .set_flag(PropertyFlag.PERMEABLE)
        )

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_los(grid, observer, 5, target, 5)

        # PERMEABLE overrides OPAQUE for geometric LOS
        assert result.is_clear is True

    def test_height_occlusion_short_observer_behind_tall_wall(self):
        """Height occlusion: short observer cannot see over tall wall."""
        grid = BattleGrid(10, 10)

        # Create a tall wall (10 feet high) in the middle
        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.height = 10  # 10 feet tall

        # Observer at 5 feet, target at 5 feet, wall at 10 feet
        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_position == wall_pos
        assert result.blocking_reason == "height_occlusion"

    def test_height_clear_tall_observer_over_short_wall(self):
        """Height clear: tall observer can see over short wall."""
        grid = BattleGrid(10, 10)

        # Create a short wall (3 feet high) in the middle
        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.height = 3  # 3 feet tall

        # Observer at 10 feet (tall creature), target at 10 feet
        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_los(grid, observer, 10, target, 10)

        assert result.is_clear is True

    def test_elevation_difference_affects_los(self):
        """Elevation differences affect LOS calculation."""
        grid = BattleGrid(10, 10)

        # Observer on raised platform (elevation 10)
        observer_pos = Position(x=0, y=0)
        observer_cell = grid.get_cell(observer_pos)
        observer_cell.elevation = 10

        # Wall in middle at ground level with height 8
        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.elevation = 0
        wall_cell.height = 8

        # Target at ground level
        target = Position(x=5, y=0)

        # Observer at elevation 10 + height 5 = Z=15
        # Wall top is at elevation 0 + height 8 = Z=8
        # Observer should see over the wall
        result = check_los(grid, observer_pos, 5, target, 5)

        assert result.is_clear is True


# ==============================================================================
# LOE TESTS
# ==============================================================================

class TestCheckLOE:
    """Tests for line of effect checking."""

    def test_clear_loe_across_empty_grid(self):
        """LOE is clear across empty grid."""
        grid = BattleGrid(10, 10)
        observer = Position(x=0, y=0)
        target = Position(x=5, y=5)

        result = check_loe(grid, observer, 5, target, 5)

        assert result.is_clear is True
        assert result.blocking_position is None
        assert result.blocking_reason is None

    def test_loe_blocked_by_solid_cell(self):
        """LOE blocked by SOLID cell in the path."""
        grid = BattleGrid(10, 10)

        # Place solid wall in the middle
        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_loe(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_position == wall_pos
        assert result.blocking_reason == "cell_solid"

    def test_loe_blocked_by_solid_border(self):
        """LOE blocked by SOLID border."""
        grid = BattleGrid(10, 10)

        # Place solid border on the east side of cell (0, 0)
        solid_mask = PropertyMask().set_flag(PropertyFlag.SOLID)
        grid.set_border(Position(x=0, y=0), Direction.E, solid_mask)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_loe(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_reason == "border_solid"

    def test_loe_not_blocked_by_opaque_only_cell(self):
        """LOE NOT blocked by OPAQUE-only cell."""
        grid = BattleGrid(10, 10)

        # Place magical darkness (OPAQUE but not SOLID)
        dark_pos = Position(x=2, y=0)
        dark_cell = grid.get_cell(dark_pos)
        dark_cell.cell_mask = PropertyMask().set_flag(PropertyFlag.OPAQUE)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_loe(grid, observer, 5, target, 5)

        # OPAQUE alone doesn't block LOE
        assert result.is_clear is True

    def test_loe_not_blocked_by_solid_permeable(self):
        """LOE NOT blocked by SOLID + PERMEABLE (iron grate)."""
        grid = BattleGrid(10, 10)

        # Place iron grate (SOLID + PERMEABLE)
        grate_pos = Position(x=2, y=0)
        grate_cell = grid.get_cell(grate_pos)
        grate_cell.cell_mask = (
            PropertyMask()
            .set_flag(PropertyFlag.SOLID)
            .set_flag(PropertyFlag.PERMEABLE)
        )

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_loe(grid, observer, 5, target, 5)

        # PERMEABLE overrides SOLID for LOE
        assert result.is_clear is True

    def test_loe_blocked_through_glass_wall(self):
        """LOE blocked by glass wall (SOLID, not OPAQUE)."""
        grid = BattleGrid(10, 10)

        # Place glass wall (SOLID only)
        glass_pos = Position(x=2, y=0)
        glass_cell = grid.get_cell(glass_pos)
        glass_cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        result = check_loe(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_position == glass_pos
        assert result.blocking_reason == "cell_solid"


# ==============================================================================
# BARRIER TRUTH TABLE TESTS
# ==============================================================================

class TestBarrierTruthTable:
    """Tests for the barrier truth table from RQ-BOX-001 Finding 4.

    | Barrier      | SOLID | OPAQUE | PERMEABLE | blocks_los | blocks_loe |
    |-------------|-------|--------|-----------|------------|------------|
    | Stone Wall  |   1   |   1    |     0     |    True    |    True    |
    | Glass Wall  |   1   |   0    |     0     |   False    |    True    |
    | Magic Dark  |   0   |   1    |     1     |   False    |   False    |
    | Iron Grate  |   1   |   0    |     1     |   False    |   False    |
    """

    def test_stone_wall_blocks_both(self):
        """Stone wall (SOLID + OPAQUE) blocks both LOS and LOE."""
        grid = BattleGrid(10, 10)

        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.cell_mask = (
            PropertyMask()
            .set_flag(PropertyFlag.SOLID)
            .set_flag(PropertyFlag.OPAQUE)
        )

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        los_result = check_los(grid, observer, 5, target, 5)
        loe_result = check_loe(grid, observer, 5, target, 5)

        assert los_result.is_clear is False
        assert loe_result.is_clear is False

    def test_glass_wall_blocks_loe_only(self):
        """Glass wall (SOLID only) blocks LOE but not LOS."""
        grid = BattleGrid(10, 10)

        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID)

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        los_result = check_los(grid, observer, 5, target, 5)
        loe_result = check_loe(grid, observer, 5, target, 5)

        assert los_result.is_clear is True
        assert loe_result.is_clear is False

    def test_magical_darkness_blocks_neither(self):
        """Magical darkness (OPAQUE + PERMEABLE) blocks neither LOS nor LOE."""
        grid = BattleGrid(10, 10)

        dark_pos = Position(x=2, y=0)
        dark_cell = grid.get_cell(dark_pos)
        dark_cell.cell_mask = (
            PropertyMask()
            .set_flag(PropertyFlag.OPAQUE)
            .set_flag(PropertyFlag.PERMEABLE)
        )

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        los_result = check_los(grid, observer, 5, target, 5)
        loe_result = check_loe(grid, observer, 5, target, 5)

        assert los_result.is_clear is True
        assert loe_result.is_clear is True

    def test_iron_grate_blocks_neither(self):
        """Iron grate (SOLID + PERMEABLE) blocks neither LOS nor LOE."""
        grid = BattleGrid(10, 10)

        grate_pos = Position(x=2, y=0)
        grate_cell = grid.get_cell(grate_pos)
        grate_cell.cell_mask = (
            PropertyMask()
            .set_flag(PropertyFlag.SOLID)
            .set_flag(PropertyFlag.PERMEABLE)
        )

        observer = Position(x=0, y=0)
        target = Position(x=5, y=0)

        los_result = check_los(grid, observer, 5, target, 5)
        loe_result = check_loe(grid, observer, 5, target, 5)

        assert los_result.is_clear is True
        assert loe_result.is_clear is True


# ==============================================================================
# ENTITY CONVENIENCE FUNCTION TESTS
# ==============================================================================

class TestEntityConvenienceFunctions:
    """Tests for entity-based LOS/LOE functions."""

    def test_check_los_between_entities(self):
        """check_los_between_entities with placed entities."""
        grid = BattleGrid(10, 10)

        # Place two entities
        grid.place_entity("entity_a", Position(x=0, y=0), SizeCategory.MEDIUM)
        grid.place_entity("entity_b", Position(x=5, y=5), SizeCategory.MEDIUM)

        result = check_los_between_entities(grid, "entity_a", "entity_b")

        assert result.is_clear is True
        assert result.observer_pos == Position(x=0, y=0)
        assert result.target_pos == Position(x=5, y=5)

    def test_check_loe_between_entities(self):
        """check_loe_between_entities with placed entities."""
        grid = BattleGrid(10, 10)

        grid.place_entity("entity_a", Position(x=0, y=0), SizeCategory.MEDIUM)
        grid.place_entity("entity_b", Position(x=5, y=5), SizeCategory.MEDIUM)

        result = check_loe_between_entities(grid, "entity_a", "entity_b")

        assert result.is_clear is True
        assert result.observer_pos == Position(x=0, y=0)
        assert result.target_pos == Position(x=5, y=5)

    def test_entity_los_blocked_by_wall(self):
        """Entity LOS blocked by wall between them."""
        grid = BattleGrid(10, 10)

        grid.place_entity("entity_a", Position(x=0, y=0), SizeCategory.MEDIUM)
        grid.place_entity("entity_b", Position(x=5, y=0), SizeCategory.MEDIUM)

        # Place wall between them
        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.cell_mask = (
            PropertyMask()
            .set_flag(PropertyFlag.SOLID)
            .set_flag(PropertyFlag.OPAQUE)
        )

        result = check_los_between_entities(grid, "entity_a", "entity_b")

        assert result.is_clear is False
        assert result.blocking_position == wall_pos

    def test_entity_not_found_raises_error(self):
        """KeyError raised when entity not found."""
        grid = BattleGrid(10, 10)
        grid.place_entity("entity_a", Position(x=0, y=0), SizeCategory.MEDIUM)

        with pytest.raises(KeyError, match="entity_b"):
            check_los_between_entities(grid, "entity_a", "entity_b")

        with pytest.raises(KeyError, match="nonexistent"):
            check_loe_between_entities(grid, "nonexistent", "entity_a")

    def test_default_entity_height(self):
        """Entities use default height of 5 feet."""
        assert DEFAULT_ENTITY_HEIGHT == 5


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_adjacent_cells_distance_1(self):
        """Adjacent cells (distance 1) have clear LOS."""
        grid = BattleGrid(10, 10)
        observer = Position(x=0, y=0)
        target = Position(x=1, y=0)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is True

    def test_same_cell_distance_0(self):
        """Same cell (distance 0) has clear LOS."""
        grid = BattleGrid(10, 10)
        observer = Position(x=5, y=5)
        target = Position(x=5, y=5)

        los_result = check_los(grid, observer, 5, target, 5)
        loe_result = check_loe(grid, observer, 5, target, 5)

        assert los_result.is_clear is True
        assert loe_result.is_clear is True

    def test_out_of_bounds_observer(self):
        """Out of bounds observer returns blocked result."""
        grid = BattleGrid(10, 10)
        observer = Position(x=15, y=15)  # Out of bounds
        target = Position(x=5, y=5)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_reason == "out_of_bounds"

    def test_out_of_bounds_target(self):
        """Out of bounds target returns blocked result."""
        grid = BattleGrid(10, 10)
        observer = Position(x=5, y=5)
        target = Position(x=15, y=15)  # Out of bounds

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_reason == "out_of_bounds"

    def test_diagonal_los_clear(self):
        """Diagonal LOS is clear across empty grid."""
        grid = BattleGrid(10, 10)
        observer = Position(x=0, y=0)
        target = Position(x=9, y=9)

        result = check_los(grid, observer, 5, target, 5)

        assert result.is_clear is True

    def test_negative_elevation(self):
        """Negative elevation (pit) handled correctly."""
        grid = BattleGrid(10, 10)

        # Observer in pit
        observer_pos = Position(x=0, y=0)
        observer_cell = grid.get_cell(observer_pos)
        observer_cell.elevation = -10

        # Wall at ground level
        wall_pos = Position(x=2, y=0)
        wall_cell = grid.get_cell(wall_pos)
        wall_cell.elevation = 0
        wall_cell.height = 5

        target = Position(x=5, y=0)

        # Observer at -10 + 5 = -5, wall from 0 to 5
        # Ray should be blocked
        result = check_los(grid, observer_pos, 5, target, 5)

        assert result.is_clear is False
        assert result.blocking_reason == "height_occlusion"


# ==============================================================================
# RESULT SERIALIZATION TESTS
# ==============================================================================

class TestResultSerialization:
    """Tests for result dataclass serialization."""

    def test_los_result_to_dict_clear(self):
        """LOSResult.to_dict() works for clear result."""
        result = LOSResult(
            is_clear=True,
            blocking_position=None,
            blocking_reason=None,
            observer_pos=Position(x=0, y=0),
            target_pos=Position(x=5, y=5),
        )

        d = result.to_dict()

        assert d["is_clear"] is True
        assert d["blocking_position"] is None
        assert d["blocking_reason"] is None
        assert d["observer_pos"] == {"x": 0, "y": 0}
        assert d["target_pos"] == {"x": 5, "y": 5}

    def test_los_result_to_dict_blocked(self):
        """LOSResult.to_dict() works for blocked result."""
        result = LOSResult(
            is_clear=False,
            blocking_position=Position(x=2, y=2),
            blocking_reason="cell_opaque",
            observer_pos=Position(x=0, y=0),
            target_pos=Position(x=5, y=5),
        )

        d = result.to_dict()

        assert d["is_clear"] is False
        assert d["blocking_position"] == {"x": 2, "y": 2}
        assert d["blocking_reason"] == "cell_opaque"

    def test_loe_result_to_dict(self):
        """LOEResult.to_dict() works correctly."""
        result = LOEResult(
            is_clear=False,
            blocking_position=Position(x=3, y=3),
            blocking_reason="cell_solid",
            observer_pos=Position(x=0, y=0),
            target_pos=Position(x=5, y=5),
        )

        d = result.to_dict()

        assert d["is_clear"] is False
        assert d["blocking_position"] == {"x": 3, "y": 3}
        assert d["blocking_reason"] == "cell_solid"

    def test_result_is_frozen(self):
        """Result dataclasses are frozen (immutable)."""
        result = LOSResult(
            is_clear=True,
            blocking_position=None,
            blocking_reason=None,
            observer_pos=Position(x=0, y=0),
            target_pos=Position(x=5, y=5),
        )

        with pytest.raises(AttributeError):
            result.is_clear = False
