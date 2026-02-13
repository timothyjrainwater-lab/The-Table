"""Tests for geometry engine (WO-001: Box Geometric Engine Core).

Comprehensive test coverage for:
- PropertyMask: Flag operations, barrier truth table, immutability
- Direction: Cardinal directions, opposite(), delta()
- CellState: FSM states
- SizeCategory: D&D 3.5e sizes, footprint()
- GridCell: Construction, serialization
- BattleGrid: Cell access, border reciprocity, entity tracking
- from_terrain_map: Terrain conversion
"""

import pytest
from copy import deepcopy

from aidm.schemas.position import Position
from aidm.schemas.geometry import (
    PropertyMask, PropertyFlag, Direction, CellState, SizeCategory, GridCell
)
from aidm.core.geometry_engine import BattleGrid, from_terrain_map


# ==============================================================================
# PROPERTY MASK TESTS
# ==============================================================================

class TestPropertyMask:
    """Tests for PropertyMask bitmask operations."""

    def test_default_mask_is_empty(self):
        """Default PropertyMask has no flags set."""
        mask = PropertyMask()
        assert mask.to_int() == 0
        assert not mask.has_flag(PropertyFlag.SOLID)
        assert not mask.has_flag(PropertyFlag.OPAQUE)

    def test_set_flag_returns_new_instance(self):
        """set_flag() returns new instance, original unchanged."""
        original = PropertyMask()
        modified = original.set_flag(PropertyFlag.SOLID)

        assert original.to_int() == 0
        assert modified.to_int() == PropertyFlag.SOLID
        assert original is not modified

    def test_clear_flag_returns_new_instance(self):
        """clear_flag() returns new instance, original unchanged."""
        original = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        modified = original.clear_flag(PropertyFlag.SOLID)

        assert original.has_flag(PropertyFlag.SOLID)
        assert not modified.has_flag(PropertyFlag.SOLID)
        assert modified.has_flag(PropertyFlag.OPAQUE)
        assert original is not modified

    def test_set_get_clear_roundtrip(self):
        """Set, get, and clear flag round-trip."""
        mask = PropertyMask()
        assert not mask.has_flag(PropertyFlag.DIFFICULT)

        mask = mask.set_flag(PropertyFlag.DIFFICULT)
        assert mask.has_flag(PropertyFlag.DIFFICULT)

        mask = mask.clear_flag(PropertyFlag.DIFFICULT)
        assert not mask.has_flag(PropertyFlag.DIFFICULT)

    def test_multiple_flags_via_chaining(self):
        """Combine multiple flags via chained set_flag() calls."""
        mask = PropertyMask()
        mask = mask.set_flag(PropertyFlag.SOLID)
        mask = mask.set_flag(PropertyFlag.OPAQUE)
        mask = mask.set_flag(PropertyFlag.HAZARDOUS)

        assert mask.has_flag(PropertyFlag.SOLID)
        assert mask.has_flag(PropertyFlag.OPAQUE)
        assert mask.has_flag(PropertyFlag.HAZARDOUS)
        assert not mask.has_flag(PropertyFlag.PERMEABLE)

    def test_to_int_from_int_roundtrip(self):
        """to_int() / from_int() round-trip."""
        original = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        value = original.to_int()
        restored = PropertyMask.from_int(value)

        assert restored.has_flag(PropertyFlag.SOLID)
        assert restored.has_flag(PropertyFlag.OPAQUE)
        assert restored.to_int() == original.to_int()

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict() / from_dict() serialization round-trip."""
        original = PropertyMask().set_flag(PropertyFlag.DIFFICULT).set_flag(PropertyFlag.HAZARDOUS)
        data = original.to_dict()
        restored = PropertyMask.from_dict(data)

        assert restored.to_int() == original.to_int()

    # Barrier truth table tests (from RQ-BOX-001 Finding 4)

    def test_barrier_stone_wall(self):
        """Stone wall: SOLID + OPAQUE → blocks_los=True, blocks_loe=True."""
        mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
        assert mask.blocks_los() is True
        assert mask.blocks_loe() is True

    def test_barrier_glass_wall(self):
        """Glass wall: SOLID only → blocks_los=False, blocks_loe=True."""
        mask = PropertyMask().set_flag(PropertyFlag.SOLID)
        assert mask.blocks_los() is False
        assert mask.blocks_loe() is True

    def test_barrier_magical_darkness(self):
        """Magical darkness: OPAQUE + PERMEABLE → blocks_los=False, blocks_loe=False.

        Magical darkness does not block geometric LOS because PERMEABLE is set.
        The concealment effect is handled separately.
        """
        mask = PropertyMask().set_flag(PropertyFlag.OPAQUE).set_flag(PropertyFlag.PERMEABLE)
        assert mask.blocks_los() is False
        assert mask.blocks_loe() is False

    def test_barrier_iron_grate(self):
        """Iron grate: SOLID + PERMEABLE → blocks_los=False, blocks_loe=False."""
        mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.PERMEABLE)
        assert mask.blocks_los() is False
        assert mask.blocks_loe() is False


# ==============================================================================
# DIRECTION TESTS
# ==============================================================================

class TestDirection:
    """Tests for Direction enum."""

    def test_all_four_directions_exist(self):
        """All four cardinal directions exist."""
        assert Direction.N is not None
        assert Direction.E is not None
        assert Direction.S is not None
        assert Direction.W is not None

    def test_opposite_north_south(self):
        """N.opposite() → S and S.opposite() → N."""
        assert Direction.N.opposite() == Direction.S
        assert Direction.S.opposite() == Direction.N

    def test_opposite_east_west(self):
        """E.opposite() → W and W.opposite() → E."""
        assert Direction.E.opposite() == Direction.W
        assert Direction.W.opposite() == Direction.E

    def test_delta_north(self):
        """N.delta() → (0, -1) (Y decreases going north)."""
        assert Direction.N.delta() == (0, -1)

    def test_delta_east(self):
        """E.delta() → (1, 0)."""
        assert Direction.E.delta() == (1, 0)

    def test_delta_south(self):
        """S.delta() → (0, 1)."""
        assert Direction.S.delta() == (0, 1)

    def test_delta_west(self):
        """W.delta() → (-1, 0)."""
        assert Direction.W.delta() == (-1, 0)


# ==============================================================================
# CELL STATE TESTS
# ==============================================================================

class TestCellState:
    """Tests for CellState FSM enum."""

    def test_all_four_states_exist(self):
        """All four FSM states exist."""
        assert CellState.INTACT is not None
        assert CellState.DAMAGED is not None
        assert CellState.BROKEN is not None
        assert CellState.DESTROYED is not None

    def test_states_are_distinct(self):
        """All states have distinct values."""
        states = [CellState.INTACT, CellState.DAMAGED, CellState.BROKEN, CellState.DESTROYED]
        values = [s.value for s in states]
        assert len(set(values)) == 4


# ==============================================================================
# SIZE CATEGORY TESTS
# ==============================================================================

class TestSizeCategory:
    """Tests for SizeCategory enum."""

    def test_all_nine_sizes_exist(self):
        """All nine D&D 3.5e size categories exist."""
        assert SizeCategory.FINE is not None
        assert SizeCategory.DIMINUTIVE is not None
        assert SizeCategory.TINY is not None
        assert SizeCategory.SMALL is not None
        assert SizeCategory.MEDIUM is not None
        assert SizeCategory.LARGE is not None
        assert SizeCategory.HUGE is not None
        assert SizeCategory.GARGANTUAN is not None
        assert SizeCategory.COLOSSAL is not None

    def test_footprint_fine_through_medium(self):
        """Fine through Medium occupy 1 square."""
        assert SizeCategory.FINE.footprint() == 1
        assert SizeCategory.DIMINUTIVE.footprint() == 1
        assert SizeCategory.TINY.footprint() == 1
        assert SizeCategory.SMALL.footprint() == 1
        assert SizeCategory.MEDIUM.footprint() == 1

    def test_footprint_large(self):
        """Large occupies 4 squares (2x2)."""
        assert SizeCategory.LARGE.footprint() == 4
        assert SizeCategory.LARGE.grid_size() == 2

    def test_footprint_huge(self):
        """Huge occupies 9 squares (3x3)."""
        assert SizeCategory.HUGE.footprint() == 9
        assert SizeCategory.HUGE.grid_size() == 3

    def test_footprint_gargantuan(self):
        """Gargantuan occupies 16 squares (4x4)."""
        assert SizeCategory.GARGANTUAN.footprint() == 16
        assert SizeCategory.GARGANTUAN.grid_size() == 4

    def test_footprint_colossal(self):
        """Colossal occupies 25 squares (5x5)."""
        assert SizeCategory.COLOSSAL.footprint() == 25
        assert SizeCategory.COLOSSAL.grid_size() == 5


# ==============================================================================
# GRID CELL TESTS
# ==============================================================================

class TestGridCell:
    """Tests for GridCell data structure."""

    def test_construction_with_defaults(self):
        """GridCell construction with default values."""
        pos = Position(x=5, y=10)
        cell = GridCell(position=pos)

        assert cell.position == pos
        assert cell.cell_mask.to_int() == 0
        assert cell.border_masks == {}
        assert cell.elevation == 0
        assert cell.height == 0
        assert cell.state == CellState.INTACT
        assert cell.occupant_ids == []

    def test_to_dict_from_dict_roundtrip(self):
        """GridCell serialization round-trip."""
        pos = Position(x=3, y=7)
        mask = PropertyMask().set_flag(PropertyFlag.SOLID)
        cell = GridCell(
            position=pos,
            cell_mask=mask,
            border_masks={Direction.N: PropertyMask().set_flag(PropertyFlag.OPAQUE)},
            elevation=10,
            height=5,
            state=CellState.DAMAGED,
            occupant_ids=["goblin_1", "goblin_2"],
        )

        data = cell.to_dict()
        restored = GridCell.from_dict(data)

        assert restored.position == pos
        assert restored.cell_mask.has_flag(PropertyFlag.SOLID)
        assert Direction.N in restored.border_masks
        assert restored.border_masks[Direction.N].has_flag(PropertyFlag.OPAQUE)
        assert restored.elevation == 10
        assert restored.height == 5
        assert restored.state == CellState.DAMAGED
        assert restored.occupant_ids == ["goblin_1", "goblin_2"]

    def test_border_masks_stored_per_direction(self):
        """Border masks correctly stored per direction."""
        cell = GridCell(position=Position(x=0, y=0))
        cell.border_masks[Direction.N] = PropertyMask().set_flag(PropertyFlag.SOLID)
        cell.border_masks[Direction.E] = PropertyMask().set_flag(PropertyFlag.OPAQUE)

        assert cell.get_border_mask(Direction.N).has_flag(PropertyFlag.SOLID)
        assert cell.get_border_mask(Direction.E).has_flag(PropertyFlag.OPAQUE)
        assert cell.get_border_mask(Direction.S).to_int() == 0  # Not set


# ==============================================================================
# BATTLE GRID TESTS
# ==============================================================================

class TestBattleGrid:
    """Tests for BattleGrid data structure."""

    def test_construction_with_dimensions(self):
        """BattleGrid construction with width and height."""
        grid = BattleGrid(20, 15)
        assert grid.width == 20
        assert grid.height == 15

    def test_in_bounds_valid_positions(self):
        """in_bounds() returns True for valid positions."""
        grid = BattleGrid(10, 10)
        assert grid.in_bounds(Position(x=0, y=0)) is True
        assert grid.in_bounds(Position(x=9, y=9)) is True
        assert grid.in_bounds(Position(x=5, y=5)) is True

    def test_in_bounds_invalid_positions(self):
        """in_bounds() returns False for out-of-bounds positions."""
        grid = BattleGrid(10, 10)
        assert grid.in_bounds(Position(x=-1, y=0)) is False
        assert grid.in_bounds(Position(x=0, y=-1)) is False
        assert grid.in_bounds(Position(x=10, y=0)) is False
        assert grid.in_bounds(Position(x=0, y=10)) is False
        assert grid.in_bounds(Position(x=100, y=100)) is False

    def test_get_cell_set_cell_roundtrip(self):
        """get_cell() / set_cell() round-trip."""
        grid = BattleGrid(10, 10)
        pos = Position(x=3, y=4)

        original_cell = grid.get_cell(pos)
        assert original_cell.position == pos

        new_cell = GridCell(
            position=pos,
            cell_mask=PropertyMask().set_flag(PropertyFlag.SOLID),
            elevation=20,
        )
        grid.set_cell(pos, new_cell)

        retrieved = grid.get_cell(pos)
        assert retrieved.cell_mask.has_flag(PropertyFlag.SOLID)
        assert retrieved.elevation == 20

    def test_get_cell_out_of_bounds_raises(self):
        """get_cell() raises IndexError for out-of-bounds."""
        grid = BattleGrid(10, 10)
        with pytest.raises(IndexError):
            grid.get_cell(Position(x=10, y=0))

    def test_get_neighbors_center_cell(self):
        """get_neighbors() returns 8 neighbors for center cell."""
        grid = BattleGrid(10, 10)
        neighbors = grid.get_neighbors(Position(x=5, y=5))

        assert len(neighbors) == 8
        expected = [
            Position(4, 4), Position(5, 4), Position(6, 4),
            Position(4, 5),                 Position(6, 5),
            Position(4, 6), Position(5, 6), Position(6, 6),
        ]
        for exp in expected:
            assert exp in neighbors

    def test_get_neighbors_corner_cell(self):
        """get_neighbors() returns 3 neighbors for corner cell."""
        grid = BattleGrid(10, 10)
        neighbors = grid.get_neighbors(Position(x=0, y=0))

        assert len(neighbors) == 3
        assert Position(1, 0) in neighbors
        assert Position(0, 1) in neighbors
        assert Position(1, 1) in neighbors

    def test_get_neighbors_edge_cell(self):
        """get_neighbors() returns 5 neighbors for edge cell."""
        grid = BattleGrid(10, 10)
        neighbors = grid.get_neighbors(Position(x=5, y=0))  # Top edge

        assert len(neighbors) == 5

    # Border reciprocity tests

    def test_border_reciprocity_north_south(self):
        """Setting N border on (3,5) also sets S border on (3,4)."""
        grid = BattleGrid(10, 10)
        pos = Position(x=3, y=5)
        north_neighbor = Position(x=3, y=4)

        mask = PropertyMask().set_flag(PropertyFlag.SOLID)
        grid.set_border(pos, Direction.N, mask)

        # Check local border
        assert grid.get_border(pos, Direction.N).has_flag(PropertyFlag.SOLID)
        # Check reciprocal border
        assert grid.get_border(north_neighbor, Direction.S).has_flag(PropertyFlag.SOLID)

    def test_border_reciprocity_east_west(self):
        """Setting E border also sets W border on eastern neighbor."""
        grid = BattleGrid(10, 10)
        pos = Position(x=3, y=5)
        east_neighbor = Position(x=4, y=5)

        mask = PropertyMask().set_flag(PropertyFlag.OPAQUE)
        grid.set_border(pos, Direction.E, mask)

        assert grid.get_border(pos, Direction.E).has_flag(PropertyFlag.OPAQUE)
        assert grid.get_border(east_neighbor, Direction.W).has_flag(PropertyFlag.OPAQUE)

    def test_border_at_grid_edge_no_crash(self):
        """Setting border at grid edge (no neighbor) doesn't crash."""
        grid = BattleGrid(10, 10)
        pos = Position(x=0, y=0)

        # Setting N border at top edge (no neighbor to north)
        mask = PropertyMask().set_flag(PropertyFlag.SOLID)
        grid.set_border(pos, Direction.N, mask)

        # Should set local border without crashing
        assert grid.get_border(pos, Direction.N).has_flag(PropertyFlag.SOLID)


# ==============================================================================
# ENTITY TRACKING TESTS
# ==============================================================================

class TestEntityTracking:
    """Tests for entity spatial tracking."""

    def test_place_entity_get_position_roundtrip(self):
        """place_entity() + get_entity_position() round-trip."""
        grid = BattleGrid(20, 20)
        pos = Position(x=5, y=10)

        grid.place_entity("fighter_1", pos, SizeCategory.MEDIUM)
        result = grid.get_entity_position("fighter_1")

        assert result == pos

    def test_place_entity_adds_to_occupant_ids(self):
        """place_entity() adds entity_id to cell's occupant_ids."""
        grid = BattleGrid(20, 20)
        pos = Position(x=5, y=10)

        grid.place_entity("goblin_1", pos, SizeCategory.SMALL)

        occupants = grid.get_occupants(pos)
        assert "goblin_1" in occupants

    def test_large_creature_occupies_four_cells(self):
        """Large creature (2x2) occupies all 4 cells."""
        grid = BattleGrid(20, 20)
        pos = Position(x=5, y=5)

        grid.place_entity("ogre", pos, SizeCategory.LARGE)

        # Check all 4 cells
        assert "ogre" in grid.get_occupants(Position(5, 5))
        assert "ogre" in grid.get_occupants(Position(6, 5))
        assert "ogre" in grid.get_occupants(Position(5, 6))
        assert "ogre" in grid.get_occupants(Position(6, 6))

    def test_huge_creature_occupies_nine_cells(self):
        """Huge creature (3x3) occupies all 9 cells."""
        grid = BattleGrid(20, 20)
        pos = Position(x=5, y=5)

        grid.place_entity("giant", pos, SizeCategory.HUGE)

        # Check all 9 cells
        for dx in range(3):
            for dy in range(3):
                assert "giant" in grid.get_occupants(Position(5 + dx, 5 + dy))

    def test_remove_entity_cleans_all_cells(self):
        """remove_entity() cleans all occupied cells."""
        grid = BattleGrid(20, 20)
        pos = Position(x=5, y=5)

        grid.place_entity("ogre", pos, SizeCategory.LARGE)
        grid.remove_entity("ogre")

        # All 4 cells should be empty
        assert "ogre" not in grid.get_occupants(Position(5, 5))
        assert "ogre" not in grid.get_occupants(Position(6, 5))
        assert "ogre" not in grid.get_occupants(Position(5, 6))
        assert "ogre" not in grid.get_occupants(Position(6, 6))
        assert grid.get_entity_position("ogre") is None

    def test_move_entity_updates_cells(self):
        """move_entity() updates old and new cells."""
        grid = BattleGrid(20, 20)
        old_pos = Position(x=5, y=5)
        new_pos = Position(x=10, y=10)

        grid.place_entity("fighter", old_pos, SizeCategory.MEDIUM)
        grid.move_entity("fighter", new_pos)

        assert "fighter" not in grid.get_occupants(old_pos)
        assert "fighter" in grid.get_occupants(new_pos)
        assert grid.get_entity_position("fighter") == new_pos

    def test_get_entities_in_area_returns_correct_set(self):
        """get_entities_in_area() returns correct entity set."""
        grid = BattleGrid(20, 20)
        grid.place_entity("goblin_1", Position(5, 5), SizeCategory.SMALL)
        grid.place_entity("goblin_2", Position(6, 5), SizeCategory.SMALL)
        grid.place_entity("fighter", Position(10, 10), SizeCategory.MEDIUM)

        area = [Position(5, 5), Position(6, 5), Position(7, 5)]
        entities = grid.get_entities_in_area(area)

        assert "goblin_1" in entities
        assert "goblin_2" in entities
        assert "fighter" not in entities

    def test_get_entities_in_area_deduplicates(self):
        """get_entities_in_area() deduplicates Large creature."""
        grid = BattleGrid(20, 20)
        grid.place_entity("ogre", Position(5, 5), SizeCategory.LARGE)

        # Area overlaps multiple cells the ogre occupies
        area = [Position(5, 5), Position(6, 5), Position(5, 6), Position(6, 6)]
        entities = grid.get_entities_in_area(area)

        # Ogre should appear only once
        assert entities.count("ogre") == 1

    def test_place_entity_out_of_bounds_raises(self):
        """Placing entity out of bounds raises ValueError."""
        grid = BattleGrid(10, 10)

        with pytest.raises(ValueError):
            grid.place_entity("ogre", Position(9, 9), SizeCategory.LARGE)  # 2x2 would exceed

    def test_remove_nonexistent_entity_raises(self):
        """Removing nonexistent entity raises KeyError."""
        grid = BattleGrid(10, 10)

        with pytest.raises(KeyError):
            grid.remove_entity("nonexistent")


# ==============================================================================
# SNAPSHOT TESTS
# ==============================================================================

class TestSnapshot:
    """Tests for BattleGrid snapshot."""

    def test_snapshot_produces_independent_copy(self):
        """snapshot() produces independent copy."""
        grid = BattleGrid(10, 10)
        grid.place_entity("fighter", Position(5, 5), SizeCategory.MEDIUM)

        snapshot = grid.snapshot()

        # Both have the entity
        assert grid.get_entity_position("fighter") == Position(5, 5)
        assert snapshot.get_entity_position("fighter") == Position(5, 5)

    def test_modifying_snapshot_cell_does_not_affect_original(self):
        """Modifying snapshot's cell doesn't affect original."""
        grid = BattleGrid(10, 10)
        pos = Position(x=5, y=5)
        grid.get_cell(pos).elevation = 10

        snapshot = grid.snapshot()
        snapshot.get_cell(pos).elevation = 100

        assert grid.get_cell(pos).elevation == 10
        assert snapshot.get_cell(pos).elevation == 100

    def test_modifying_original_cell_does_not_affect_snapshot(self):
        """Modifying original's cell doesn't affect snapshot."""
        grid = BattleGrid(10, 10)
        pos = Position(x=5, y=5)

        snapshot = grid.snapshot()
        grid.get_cell(pos).elevation = 50

        assert grid.get_cell(pos).elevation == 50
        assert snapshot.get_cell(pos).elevation == 0

    def test_entity_tracking_independent_in_snapshot(self):
        """Entity tracking is independent in snapshot."""
        grid = BattleGrid(10, 10)
        grid.place_entity("fighter", Position(5, 5), SizeCategory.MEDIUM)

        snapshot = grid.snapshot()
        snapshot.move_entity("fighter", Position(7, 7))

        assert grid.get_entity_position("fighter") == Position(5, 5)
        assert snapshot.get_entity_position("fighter") == Position(7, 7)


# ==============================================================================
# FROM_TERRAIN_MAP CONVERSION TESTS
# ==============================================================================

class TestFromTerrainMap:
    """Tests for from_terrain_map() factory."""

    def test_empty_terrain_map_produces_minimal_grid(self):
        """Empty terrain_map produces 1x1 empty grid."""
        grid = from_terrain_map({}, {})
        assert grid.width == 1
        assert grid.height == 1

    def test_wall_smooth_tag_sets_solid_opaque(self):
        """WALL_SMOOTH terrain tag → SOLID + OPAQUE on cell_mask."""
        terrain_map = {
            "5,5": {
                "position": {"x": 5, "y": 5},
                "terrain_tags": ["wall_smooth"],
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(5, 5))
        assert cell.cell_mask.has_flag(PropertyFlag.SOLID)
        assert cell.cell_mask.has_flag(PropertyFlag.OPAQUE)

    def test_wall_rough_tag_sets_solid_opaque(self):
        """WALL_ROUGH terrain tag → SOLID + OPAQUE on cell_mask."""
        terrain_map = {
            "3,4": {
                "position": {"x": 3, "y": 4},
                "terrain_tags": ["wall_rough"],
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(3, 4))
        assert cell.cell_mask.has_flag(PropertyFlag.SOLID)
        assert cell.cell_mask.has_flag(PropertyFlag.OPAQUE)

    def test_blocking_solid_tag_sets_solid_opaque(self):
        """blocking_solid terrain tag → SOLID + OPAQUE."""
        terrain_map = {
            "2,2": {
                "position": {"x": 2, "y": 2},
                "terrain_tags": ["blocking_solid"],
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(2, 2))
        assert cell.cell_mask.has_flag(PropertyFlag.SOLID)
        assert cell.cell_mask.has_flag(PropertyFlag.OPAQUE)

    def test_difficult_terrain_sets_difficult_flag(self):
        """DIFFICULT_TERRAIN → DIFFICULT flag."""
        terrain_map = {
            "1,1": {
                "position": {"x": 1, "y": 1},
                "terrain_tags": ["difficult_terrain"],
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(1, 1))
        assert cell.cell_mask.has_flag(PropertyFlag.DIFFICULT)

    def test_deep_water_sets_difficult_and_hazardous(self):
        """DEEP_WATER → DIFFICULT + HAZARDOUS."""
        terrain_map = {
            "0,0": {
                "position": {"x": 0, "y": 0},
                "terrain_tags": ["deep_water"],
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(0, 0))
        assert cell.cell_mask.has_flag(PropertyFlag.DIFFICULT)
        assert cell.cell_mask.has_flag(PropertyFlag.HAZARDOUS)

    def test_shallow_water_sets_difficult(self):
        """shallow_water → DIFFICULT only."""
        terrain_map = {
            "0,0": {
                "position": {"x": 0, "y": 0},
                "terrain_tags": ["shallow_water"],
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(0, 0))
        assert cell.cell_mask.has_flag(PropertyFlag.DIFFICULT)
        assert not cell.cell_mask.has_flag(PropertyFlag.HAZARDOUS)

    def test_pit_sets_hazardous(self):
        """is_pit → HAZARDOUS."""
        terrain_map = {
            "4,4": {
                "position": {"x": 4, "y": 4},
                "is_pit": True,
                "pit_depth": 20,
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(4, 4))
        assert cell.cell_mask.has_flag(PropertyFlag.HAZARDOUS)

    def test_ledge_sets_hazardous(self):
        """is_ledge → HAZARDOUS."""
        terrain_map = {
            "3,3": {
                "position": {"x": 3, "y": 3},
                "is_ledge": True,
                "ledge_drop": 15,
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(3, 3))
        assert cell.cell_mask.has_flag(PropertyFlag.HAZARDOUS)

    def test_elevation_preserved_from_terrain_cell(self):
        """Elevation preserved from TerrainCell."""
        terrain_map = {
            "5,5": {
                "position": {"x": 5, "y": 5},
                "elevation": 30,
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(5, 5))
        assert cell.elevation == 30

    def test_total_cover_sets_solid_opaque(self):
        """cover_type == 'total' → SOLID + OPAQUE."""
        terrain_map = {
            "7,7": {
                "position": {"x": 7, "y": 7},
                "cover_type": "total",
            }
        }
        grid = from_terrain_map(terrain_map, {})

        cell = grid.get_cell(Position(7, 7))
        assert cell.cell_mask.has_flag(PropertyFlag.SOLID)
        assert cell.cell_mask.has_flag(PropertyFlag.OPAQUE)

    def test_entity_positions_populated(self):
        """Entity positions populated from entities dict."""
        terrain_map = {
            "5,5": {"position": {"x": 5, "y": 5}},
        }
        entities = {
            "fighter_1": {"position": {"x": 5, "y": 5}},
            "goblin_1": {"position": {"x": 3, "y": 3}},
        }
        grid = from_terrain_map(terrain_map, entities)

        assert grid.get_entity_position("fighter_1") == Position(5, 5)
        # goblin_1 is at (3,3) which may be in bounds depending on grid size
        # Grid size is max(5,3)+1=6, so (3,3) is in bounds
        assert grid.get_entity_position("goblin_1") == Position(3, 3)


# ==============================================================================
# SCALE TESTS
# ==============================================================================

class TestScale:
    """Scale tests for large grids."""

    def test_100x100_grid_creates_successfully(self):
        """BattleGrid(100, 100) creates successfully (10,000 cells)."""
        grid = BattleGrid(100, 100)
        assert grid.width == 100
        assert grid.height == 100

    def test_cell_access_at_99_99(self):
        """Cell access at (99, 99) works."""
        grid = BattleGrid(100, 100)
        cell = grid.get_cell(Position(99, 99))
        assert cell.position == Position(99, 99)

        # Modify and verify
        cell.elevation = 42
        assert grid.get_cell(Position(99, 99)).elevation == 42

    def test_large_grid_entity_tracking(self):
        """Entity tracking works on large grid."""
        grid = BattleGrid(100, 100)

        # Place entities at various locations
        grid.place_entity("dragon", Position(90, 90), SizeCategory.GARGANTUAN)

        # Verify all 16 cells (4x4) are occupied
        for dx in range(4):
            for dy in range(4):
                assert "dragon" in grid.get_occupants(Position(90 + dx, 90 + dy))
