"""Tests for box_lens_bridge.py — Box-Lens integration layer.

WO-012: Box-Lens Bridge
Reference: WO-001 (BattleGrid), WO-007 (LensIndex)
"""

import pytest

from aidm.schemas.position import Position
from aidm.schemas.geometry import PropertyMask, PropertyFlag, SizeCategory, Direction
from aidm.core.geometry_engine import BattleGrid
from aidm.core.lens_index import LensIndex, SourceTier
from aidm.core.box_lens_bridge import BoxLensBridge, _infer_entity_class


# ==============================================================================
# HELPER FIXTURES
# ==============================================================================

@pytest.fixture
def empty_grid():
    """Create an empty 10x10 grid."""
    return BattleGrid(10, 10)


@pytest.fixture
def empty_lens():
    """Create an empty LensIndex."""
    return LensIndex()


@pytest.fixture
def bridge(empty_grid, empty_lens):
    """Create a bridge with empty grid and lens."""
    return BoxLensBridge(empty_grid, empty_lens)


@pytest.fixture
def populated_bridge():
    """Create a bridge with some entities already placed."""
    grid = BattleGrid(20, 20)
    lens = LensIndex()

    # Place some entities on the grid
    grid.place_entity("creature_fighter", Position(x=5, y=5), SizeCategory.MEDIUM)
    grid.place_entity("creature_ogre", Position(x=10, y=10), SizeCategory.LARGE)
    grid.place_entity("object_chest", Position(x=3, y=3), SizeCategory.SMALL)

    return BoxLensBridge(grid, lens)


# ==============================================================================
# CONSTRUCTION TESTS
# ==============================================================================

class TestConstruction:
    """Tests for BoxLensBridge construction."""

    def test_creates_with_grid_and_lens(self, empty_grid, empty_lens):
        """Bridge initializes with grid and lens."""
        bridge = BoxLensBridge(empty_grid, empty_lens)
        assert bridge.grid is empty_grid
        assert bridge.lens is empty_lens

    def test_grid_accessible(self, bridge):
        """Grid property returns the grid."""
        assert isinstance(bridge.grid, BattleGrid)

    def test_lens_accessible(self, bridge):
        """Lens property returns the lens."""
        assert isinstance(bridge.lens, LensIndex)


# ==============================================================================
# ENTITY CLASS MAPPING TESTS
# ==============================================================================

class TestEntityClassMapping:
    """Tests for _infer_entity_class helper."""

    def test_creature_prefix(self):
        """creature_ prefix maps to 'creature' class."""
        assert _infer_entity_class("creature_goblin") == "creature"
        assert _infer_entity_class("creature_dragon") == "creature"

    def test_object_prefix(self):
        """object_ prefix maps to 'object' class."""
        assert _infer_entity_class("object_chest") == "object"
        assert _infer_entity_class("object_door") == "object"

    def test_terrain_prefix(self):
        """terrain_ prefix maps to 'terrain' class."""
        assert _infer_entity_class("terrain_pillar") == "terrain"
        assert _infer_entity_class("terrain_wall") == "terrain"

    def test_unknown_prefix(self):
        """Unknown prefix maps to 'unknown' class."""
        assert _infer_entity_class("player_bob") == "unknown"
        assert _infer_entity_class("npc_merchant") == "unknown"
        assert _infer_entity_class("entity123") == "unknown"


# ==============================================================================
# ENTITY SYNC TESTS
# ==============================================================================

class TestEntitySync:
    """Tests for sync_entity_to_lens."""

    def test_sync_stores_position(self, populated_bridge):
        """sync_entity_to_lens stores position in Lens."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("creature_fighter", turn=1)

        pos = bridge.lens.get_position("creature_fighter")
        assert pos is not None
        assert pos == Position(x=5, y=5)

    def test_sync_stores_size(self, populated_bridge):
        """sync_entity_to_lens stores size in Lens."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("creature_fighter", turn=1)

        size = bridge.get_entity_size("creature_fighter")
        assert size == SizeCategory.MEDIUM

    def test_sync_uses_box_tier(self, populated_bridge):
        """Synced facts have BOX tier authority."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("creature_fighter", turn=1)

        fact = bridge.lens.get_fact("creature_fighter", "size")
        assert fact is not None
        assert fact.source_tier == SourceTier.BOX

    def test_sync_returns_false_for_unknown_entity(self, bridge):
        """sync_entity_to_lens returns False for entity not in grid."""
        result = bridge.sync_entity_to_lens("creature_unknown", turn=1)
        assert result is False

    def test_sync_returns_true_for_known_entity(self, populated_bridge):
        """sync_entity_to_lens returns True for entity in grid."""
        result = populated_bridge.sync_entity_to_lens("creature_fighter", turn=1)
        assert result is True

    def test_sync_all_entities_handles_multiple(self, populated_bridge):
        """sync_all_entities syncs all grid entities."""
        count = populated_bridge.sync_all_entities(turn=1)
        assert count == 3  # fighter, ogre, chest

        # Verify all are synced
        assert populated_bridge.lens.get_position("creature_fighter") is not None
        assert populated_bridge.lens.get_position("creature_ogre") is not None
        assert populated_bridge.lens.get_position("object_chest") is not None

    def test_sync_creates_entity_in_lens(self, populated_bridge):
        """sync_entity_to_lens creates entity profile in Lens."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("creature_fighter", turn=1)

        profile = bridge.lens.get_entity("creature_fighter")
        assert profile is not None
        assert profile.entity_class == "creature"

    def test_sync_infers_object_class(self, populated_bridge):
        """sync_entity_to_lens infers 'object' class from prefix."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("object_chest", turn=1)

        profile = bridge.lens.get_entity("object_chest")
        assert profile.entity_class == "object"


# ==============================================================================
# CELL SYNC TESTS
# ==============================================================================

class TestCellSync:
    """Tests for sync_cell_to_lens."""

    def test_sync_stores_mask(self, bridge):
        """sync_cell_to_lens stores cell_mask in Lens."""
        # Set up a cell with properties
        pos = Position(x=3, y=3)
        cell = bridge.grid.get_cell(pos)
        cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID)

        bridge.sync_cell_to_lens(pos, turn=1)

        mask = bridge.get_cell_properties(pos)
        assert mask is not None
        assert mask.has_flag(PropertyFlag.SOLID)

    def test_sync_stores_elevation(self, bridge):
        """sync_cell_to_lens stores elevation in Lens."""
        pos = Position(x=3, y=3)
        cell = bridge.grid.get_cell(pos)
        cell.elevation = 10

        bridge.sync_cell_to_lens(pos, turn=1)

        cell_entity_id = f"cell_{pos.x}_{pos.y}"
        fact = bridge.lens.get_fact(cell_entity_id, "elevation")
        assert fact is not None
        assert fact.value == 10

    def test_sync_stores_border_masks(self, bridge):
        """sync_cell_to_lens stores border_masks in Lens."""
        pos = Position(x=3, y=3)
        cell = bridge.grid.get_cell(pos)
        cell.border_masks[Direction.N] = PropertyMask().set_flag(PropertyFlag.OPAQUE)

        bridge.sync_cell_to_lens(pos, turn=1)

        cell_entity_id = f"cell_{pos.x}_{pos.y}"
        fact = bridge.lens.get_fact(cell_entity_id, "border_masks")
        assert fact is not None
        assert "north" in fact.value

    def test_sync_returns_false_out_of_bounds(self, bridge):
        """sync_cell_to_lens returns False for out-of-bounds position."""
        pos = Position(x=100, y=100)
        result = bridge.sync_cell_to_lens(pos, turn=1)
        assert result is False

    def test_sync_grid_to_lens_handles_full_grid(self, bridge):
        """sync_grid_to_lens syncs all cells."""
        # 10x10 grid = 100 cells
        count = bridge.sync_grid_to_lens(turn=1)
        assert count == 100


# ==============================================================================
# QUERY TESTS
# ==============================================================================

class TestQueries:
    """Tests for Lens query functions."""

    def test_get_entity_size_returns_correct(self, populated_bridge):
        """get_entity_size returns correct SizeCategory."""
        populated_bridge.sync_all_entities(turn=1)

        assert populated_bridge.get_entity_size("creature_fighter") == SizeCategory.MEDIUM
        assert populated_bridge.get_entity_size("creature_ogre") == SizeCategory.LARGE
        assert populated_bridge.get_entity_size("object_chest") == SizeCategory.SMALL

    def test_get_entity_size_returns_none_for_unknown(self, bridge):
        """get_entity_size returns None for unknown entity."""
        assert bridge.get_entity_size("creature_unknown") is None

    def test_get_entity_position_returns_correct(self, populated_bridge):
        """get_entity_position returns correct Position."""
        populated_bridge.sync_all_entities(turn=1)

        pos = populated_bridge.get_entity_position("creature_fighter")
        assert pos == Position(x=5, y=5)

    def test_get_entity_position_returns_none_for_unknown(self, bridge):
        """get_entity_position returns None for unknown entity."""
        assert bridge.get_entity_position("creature_unknown") is None

    def test_get_entities_in_area_uses_lens(self, populated_bridge):
        """get_entities_in_area uses Lens spatial index."""
        populated_bridge.sync_all_entities(turn=1)

        # Query positions that include fighter
        positions = [Position(x=5, y=5), Position(x=6, y=6)]
        entities = populated_bridge.get_entities_in_area(positions)

        assert "creature_fighter" in entities

    def test_get_entities_in_area_deduplicates(self, populated_bridge):
        """get_entities_in_area returns deduplicated list."""
        populated_bridge.sync_all_entities(turn=1)

        # Large creature at (10,10) occupies multiple squares
        # Query multiple positions in its footprint
        positions = [
            Position(x=10, y=10),
            Position(x=11, y=10),
            Position(x=10, y=11),
            Position(x=11, y=11),
        ]
        entities = populated_bridge.get_entities_in_area(positions)

        # Should only appear once
        ogre_count = entities.count("creature_ogre")
        # Note: Large creature only has position at anchor, not all squares in Lens
        # So it should appear at most once
        assert ogre_count <= 1

    def test_get_cell_properties_returns_mask(self, bridge):
        """get_cell_properties returns PropertyMask."""
        pos = Position(x=5, y=5)
        cell = bridge.grid.get_cell(pos)
        cell.cell_mask = PropertyMask().set_flag(PropertyFlag.DIFFICULT)

        bridge.sync_cell_to_lens(pos, turn=1)

        mask = bridge.get_cell_properties(pos)
        assert mask is not None
        assert mask.has_flag(PropertyFlag.DIFFICULT)

    def test_get_cell_properties_returns_none_for_unsynced(self, bridge):
        """get_cell_properties returns None for unsynced cell."""
        pos = Position(x=5, y=5)
        # Don't sync the cell
        mask = bridge.get_cell_properties(pos)
        assert mask is None


# ==============================================================================
# VALIDATION TESTS
# ==============================================================================

class TestValidation:
    """Tests for validate_consistency."""

    def test_consistent_state_returns_empty(self, populated_bridge):
        """Consistent state returns empty error list."""
        populated_bridge.sync_all_entities(turn=1)
        errors = populated_bridge.validate_consistency(turn=1)
        assert errors == []

    def test_missing_entity_in_lens_detected(self, populated_bridge):
        """Missing entity in Lens is detected."""
        # Don't sync entities - Lens is empty
        errors = populated_bridge.validate_consistency(turn=1)

        # Should have errors for all 3 entities
        assert len(errors) == 3
        assert any("creature_fighter" in e and "not in Lens" in e for e in errors)

    def test_position_mismatch_detected(self, populated_bridge):
        """Position mismatch is detected."""
        bridge = populated_bridge
        bridge.sync_all_entities(turn=1)

        # Manually change position in Lens
        bridge.lens.set_position("creature_fighter", Position(x=99, y=99), turn=2)

        errors = bridge.validate_consistency(turn=2)
        assert any("Position mismatch" in e and "creature_fighter" in e for e in errors)

    def test_size_mismatch_detected(self, populated_bridge):
        """Size mismatch is detected."""
        bridge = populated_bridge
        bridge.sync_all_entities(turn=1)

        # Manually change size in Lens
        bridge.lens.set_fact(
            entity_id="creature_fighter",
            attribute="size",
            value="large",  # Was medium
            source_tier=SourceTier.BOX,
            turn=2,
        )

        errors = bridge.validate_consistency(turn=2)
        assert any("Size mismatch" in e and "creature_fighter" in e for e in errors)

    def test_entity_in_lens_not_grid_detected(self):
        """Entity in Lens but not Grid is detected."""
        grid = BattleGrid(10, 10)
        lens = LensIndex()

        # Register entity in Lens but not Grid
        lens.register_entity("creature_ghost", "creature", turn=1)

        bridge = BoxLensBridge(grid, lens)
        errors = bridge.validate_consistency(turn=1)

        assert any("creature_ghost" in e and "not in Grid" in e for e in errors)

    def test_terrain_entities_excluded_from_grid_check(self):
        """Terrain entities in Lens don't need to exist in Grid."""
        grid = BattleGrid(10, 10)
        lens = LensIndex()

        # Register terrain entity in Lens (cells are terrain)
        lens.register_entity("cell_5_5", "terrain", turn=1)

        bridge = BoxLensBridge(grid, lens)
        errors = bridge.validate_consistency(turn=1)

        # Should not report cell_5_5 as missing from Grid
        assert not any("cell_5_5" in e for e in errors)


# ==============================================================================
# LARGE CREATURE TESTS
# ==============================================================================

class TestLargeCreatures:
    """Tests for multi-square creature handling."""

    def test_large_2x2_syncs_correctly(self, populated_bridge):
        """Large (2x2) creature syncs correctly."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("creature_ogre", turn=1)

        # Position should be top-left anchor
        pos = bridge.get_entity_position("creature_ogre")
        assert pos == Position(x=10, y=10)

        # Size should be Large
        size = bridge.get_entity_size("creature_ogre")
        assert size == SizeCategory.LARGE

    def test_huge_3x3_syncs_correctly(self):
        """Huge (3x3) creature syncs correctly."""
        grid = BattleGrid(20, 20)
        lens = LensIndex()
        grid.place_entity("creature_giant", Position(x=5, y=5), SizeCategory.HUGE)

        bridge = BoxLensBridge(grid, lens)
        bridge.sync_entity_to_lens("creature_giant", turn=1)

        pos = bridge.get_entity_position("creature_giant")
        assert pos == Position(x=5, y=5)

        size = bridge.get_entity_size("creature_giant")
        assert size == SizeCategory.HUGE

    def test_position_is_top_left_anchor(self):
        """Position in Lens is the top-left anchor for all sizes."""
        grid = BattleGrid(30, 30)
        lens = LensIndex()

        # Place various sized creatures
        grid.place_entity("creature_human", Position(x=5, y=5), SizeCategory.MEDIUM)
        grid.place_entity("creature_ogre", Position(x=10, y=10), SizeCategory.LARGE)
        grid.place_entity("creature_dragon", Position(x=15, y=15), SizeCategory.HUGE)
        grid.place_entity("creature_titan", Position(x=20, y=20), SizeCategory.GARGANTUAN)

        bridge = BoxLensBridge(grid, lens)
        bridge.sync_all_entities(turn=1)

        # All should have their anchor positions
        assert bridge.get_entity_position("creature_human") == Position(x=5, y=5)
        assert bridge.get_entity_position("creature_ogre") == Position(x=10, y=10)
        assert bridge.get_entity_position("creature_dragon") == Position(x=15, y=15)
        assert bridge.get_entity_position("creature_titan") == Position(x=20, y=20)


# ==============================================================================
# ROUND-TRIP TESTS
# ==============================================================================

class TestRoundTrip:
    """Tests for sync-query round trips."""

    def test_sync_query_matches(self, populated_bridge):
        """Synced data can be queried back correctly."""
        bridge = populated_bridge
        bridge.sync_all_entities(turn=1)

        # Query should match grid
        for entity_id, (grid_pos, grid_size) in bridge.grid._entities.items():
            lens_pos = bridge.get_entity_position(entity_id)
            lens_size = bridge.get_entity_size(entity_id)

            assert lens_pos == grid_pos
            assert lens_size == grid_size

    def test_multiple_syncs_update_correctly(self):
        """Multiple syncs update facts correctly."""
        grid = BattleGrid(20, 20)
        lens = LensIndex()
        bridge = BoxLensBridge(grid, lens)

        # Place and sync
        grid.place_entity("creature_test", Position(x=5, y=5), SizeCategory.MEDIUM)
        bridge.sync_entity_to_lens("creature_test", turn=1)

        assert bridge.get_entity_position("creature_test") == Position(x=5, y=5)

        # Move and re-sync
        grid.move_entity("creature_test", Position(x=10, y=10))
        bridge.sync_entity_to_lens("creature_test", turn=2)

        # Should reflect new position
        assert bridge.get_entity_position("creature_test") == Position(x=10, y=10)


# ==============================================================================
# SNAPSHOT TESTS
# ==============================================================================

class TestSnapshot:
    """Tests for snapshot functionality."""

    def test_creates_independent_copy(self, populated_bridge):
        """snapshot creates independent copy."""
        bridge = populated_bridge
        bridge.sync_all_entities(turn=1)

        snapshot = bridge.snapshot()

        # Should be different objects
        assert snapshot is not bridge
        assert snapshot.grid is not bridge.grid
        assert snapshot.lens is not bridge.lens

    def test_mutations_dont_affect_original(self, populated_bridge):
        """Mutations to snapshot don't affect original."""
        bridge = populated_bridge
        bridge.sync_all_entities(turn=1)

        snapshot = bridge.snapshot()

        # Modify snapshot's grid
        snapshot.grid.place_entity("creature_new", Position(x=15, y=15), SizeCategory.MEDIUM)

        # Original should not have the new entity
        assert "creature_new" not in bridge.grid._entities

    def test_original_mutations_dont_affect_snapshot(self, populated_bridge):
        """Mutations to original don't affect snapshot."""
        bridge = populated_bridge
        bridge.sync_all_entities(turn=1)

        snapshot = bridge.snapshot()

        # Move entity in original
        bridge.grid.move_entity("creature_fighter", Position(x=8, y=8))
        bridge.sync_entity_to_lens("creature_fighter", turn=2)

        # Snapshot should still have old position
        snapshot_pos = snapshot.get_entity_position("creature_fighter")
        assert snapshot_pos == Position(x=5, y=5)


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_grid(self):
        """Empty grid syncs correctly."""
        grid = BattleGrid(10, 10)
        lens = LensIndex()
        bridge = BoxLensBridge(grid, lens)

        count = bridge.sync_all_entities(turn=1)
        assert count == 0

        errors = bridge.validate_consistency(turn=1)
        assert errors == []

    def test_entity_not_in_grid(self, bridge):
        """Querying entity not in grid returns None."""
        assert bridge.get_entity_position("creature_nonexistent") is None
        assert bridge.get_entity_size("creature_nonexistent") is None

    def test_cell_out_of_bounds(self, bridge):
        """Syncing out-of-bounds cell returns False."""
        result = bridge.sync_cell_to_lens(Position(x=1000, y=1000), turn=1)
        assert result is False

    def test_empty_positions_list(self, bridge):
        """get_entities_in_area with empty list returns empty."""
        entities = bridge.get_entities_in_area([])
        assert entities == []

    def test_sync_after_entity_removal(self):
        """Syncing after entity removal works correctly."""
        grid = BattleGrid(20, 20)
        lens = LensIndex()
        bridge = BoxLensBridge(grid, lens)

        # Place, sync, remove
        grid.place_entity("creature_temp", Position(x=5, y=5), SizeCategory.MEDIUM)
        bridge.sync_entity_to_lens("creature_temp", turn=1)

        grid.remove_entity("creature_temp")

        # Sync should return False now
        result = bridge.sync_entity_to_lens("creature_temp", turn=2)
        assert result is False

        # Validation should detect inconsistency
        errors = bridge.validate_consistency(turn=2)
        assert any("creature_temp" in e and "not in Grid" in e for e in errors)


# ==============================================================================
# BOX TIER AUTHORITY TESTS
# ==============================================================================

class TestBoxTierAuthority:
    """Tests for BOX tier authority enforcement."""

    def test_position_fact_is_box_tier(self, populated_bridge):
        """Position facts are stored with BOX tier."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("creature_fighter", turn=1)

        fact = bridge.lens.get_fact("creature_fighter", "position")
        assert fact is not None
        assert fact.source_tier == SourceTier.BOX

    def test_size_fact_is_box_tier(self, populated_bridge):
        """Size facts are stored with BOX tier."""
        bridge = populated_bridge
        bridge.sync_entity_to_lens("creature_fighter", turn=1)

        fact = bridge.lens.get_fact("creature_fighter", "size")
        assert fact.source_tier == SourceTier.BOX

    def test_cell_mask_fact_is_box_tier(self, bridge):
        """Cell mask facts are stored with BOX tier."""
        pos = Position(x=5, y=5)
        bridge.sync_cell_to_lens(pos, turn=1)

        cell_entity_id = f"cell_{pos.x}_{pos.y}"
        fact = bridge.lens.get_fact(cell_entity_id, "cell_mask")
        assert fact.source_tier == SourceTier.BOX

    def test_box_overrides_spark(self, populated_bridge):
        """BOX tier facts override SPARK tier."""
        bridge = populated_bridge

        # First set a SPARK-tier size
        bridge.lens.register_entity("creature_fighter", "creature", turn=0)
        bridge.lens.set_fact(
            entity_id="creature_fighter",
            attribute="size",
            value="large",
            source_tier=SourceTier.SPARK,
            turn=1,
        )

        # Now sync from grid (BOX tier)
        bridge.sync_entity_to_lens("creature_fighter", turn=2)

        # BOX should have overridden SPARK
        size = bridge.get_entity_size("creature_fighter")
        assert size == SizeCategory.MEDIUM  # Grid has Medium, not Large
