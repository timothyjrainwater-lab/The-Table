"""Tests for Combat Reflexes feat and multiple AoO tracking.

WO-011: Combat Reflexes + Multiple AoO
Comprehensive test suite covering:
- get_max_aoo calculation
- AoOTracker creation and serialization
- can_make_aoo logic
- record_aoo immutable updates
- reset_aoo_for_round
- check_aoo_trigger movement analysis
- AoOManager integration
- Integration with reach_resolver
"""

import pytest

from aidm.schemas.position import Position
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.combat_reflexes import (
    AoOTracker,
    AoOManager,
    get_max_aoo,
    can_make_aoo,
    record_aoo,
    reset_aoo_for_round,
    check_aoo_trigger,
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
    """Create grid with multiple entities for AoO testing."""
    grid = empty_grid
    # Fighter at (5, 5)
    grid.place_entity("fighter", Position(5, 5), SizeCategory.MEDIUM)
    # Enemy at (6, 5) - adjacent to fighter
    grid.place_entity("enemy1", Position(6, 5), SizeCategory.MEDIUM)
    # Another enemy at (10, 5) - not adjacent
    grid.place_entity("enemy2", Position(10, 5), SizeCategory.MEDIUM)
    return grid


@pytest.fixture
def basic_tracker():
    """Create a basic AoO tracker with 1 AoO."""
    return AoOTracker(entity_id="fighter", max_aoo_per_round=1)


@pytest.fixture
def combat_reflexes_tracker():
    """Create a tracker for entity with Combat Reflexes and +3 Dex."""
    return AoOTracker(
        entity_id="monk",
        max_aoo_per_round=4,  # 1 + 3 Dex
    )


# ==============================================================================
# GET_MAX_AOO TESTS
# ==============================================================================

class TestGetMaxAoO:
    """Tests for get_max_aoo function."""

    def test_without_feat_always_one(self):
        """Without Combat Reflexes, always returns 1."""
        assert get_max_aoo("fighter", has_combat_reflexes=False, dex_modifier=0) == 1
        assert get_max_aoo("fighter", has_combat_reflexes=False, dex_modifier=5) == 1
        assert get_max_aoo("fighter", has_combat_reflexes=False, dex_modifier=-2) == 1

    def test_with_feat_dex_zero(self):
        """With Combat Reflexes and Dex +0: 1 AoO (1 + 0)."""
        assert get_max_aoo("fighter", has_combat_reflexes=True, dex_modifier=0) == 1

    def test_with_feat_dex_plus_three(self):
        """With Combat Reflexes and Dex +3: 4 AoO (1 + 3)."""
        assert get_max_aoo("fighter", has_combat_reflexes=True, dex_modifier=3) == 4

    def test_with_feat_dex_plus_five(self):
        """With Combat Reflexes and Dex +5: 6 AoO (1 + 5)."""
        assert get_max_aoo("fighter", has_combat_reflexes=True, dex_modifier=5) == 6

    def test_with_feat_negative_dex_minimum_one(self):
        """With Combat Reflexes and negative Dex, minimum is 1."""
        assert get_max_aoo("fighter", has_combat_reflexes=True, dex_modifier=-1) == 1
        assert get_max_aoo("fighter", has_combat_reflexes=True, dex_modifier=-3) == 1

    def test_with_feat_high_dex(self):
        """With Combat Reflexes and very high Dex."""
        assert get_max_aoo("epic", has_combat_reflexes=True, dex_modifier=10) == 11


# ==============================================================================
# AOO TRACKER TESTS
# ==============================================================================

class TestAoOTracker:
    """Tests for AoOTracker dataclass."""

    def test_creation_with_defaults(self):
        """Create tracker with default values."""
        tracker = AoOTracker(entity_id="fighter")
        assert tracker.entity_id == "fighter"
        assert tracker.max_aoo_per_round == 1
        assert tracker.aoo_used_this_round == 0
        assert tracker.aoo_targets_this_round == frozenset()

    def test_creation_with_values(self):
        """Create tracker with specific values."""
        tracker = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=4,
            aoo_used_this_round=2,
            aoo_targets_this_round=frozenset({"enemy1", "enemy2"})
        )
        assert tracker.entity_id == "monk"
        assert tracker.max_aoo_per_round == 4
        assert tracker.aoo_used_this_round == 2
        assert "enemy1" in tracker.aoo_targets_this_round
        assert "enemy2" in tracker.aoo_targets_this_round

    def test_serialization_roundtrip(self):
        """Serialize and deserialize tracker."""
        original = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=4,
            aoo_used_this_round=2,
            aoo_targets_this_round=frozenset({"enemy1", "enemy2"})
        )
        data = original.to_dict()
        restored = AoOTracker.from_dict(data)

        assert restored.entity_id == original.entity_id
        assert restored.max_aoo_per_round == original.max_aoo_per_round
        assert restored.aoo_used_this_round == original.aoo_used_this_round
        assert restored.aoo_targets_this_round == original.aoo_targets_this_round

    def test_to_dict_format(self):
        """Verify to_dict output format."""
        tracker = AoOTracker(
            entity_id="fighter",
            max_aoo_per_round=1,
            aoo_used_this_round=1,
            aoo_targets_this_round=frozenset({"goblin"})
        )
        data = tracker.to_dict()

        assert data["entity_id"] == "fighter"
        assert data["max_aoo_per_round"] == 1
        assert data["aoo_used_this_round"] == 1
        assert "goblin" in data["aoo_targets_this_round"]

    def test_immutability(self):
        """Tracker is frozen (immutable)."""
        tracker = AoOTracker(entity_id="fighter")
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            tracker.aoo_used_this_round = 5


# ==============================================================================
# CAN_MAKE_AOO TESTS
# ==============================================================================

class TestCanMakeAoO:
    """Tests for can_make_aoo function."""

    def test_first_aoo_allowed(self, basic_tracker):
        """First AoO is allowed."""
        assert can_make_aoo(basic_tracker, "goblin") is True

    def test_second_aoo_blocked_no_feat(self):
        """Second AoO blocked without feat (max 1)."""
        tracker = AoOTracker(
            entity_id="fighter",
            max_aoo_per_round=1,
            aoo_used_this_round=1,
            aoo_targets_this_round=frozenset({"goblin"})
        )
        assert can_make_aoo(tracker, "orc") is False

    def test_second_aoo_allowed_with_feat(self):
        """Second AoO allowed with Combat Reflexes (max 3)."""
        tracker = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=3,
            aoo_used_this_round=1,
            aoo_targets_this_round=frozenset({"goblin"})
        )
        assert can_make_aoo(tracker, "orc") is True

    def test_same_target_blocked(self):
        """Cannot target same entity twice in same round."""
        tracker = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=4,
            aoo_used_this_round=1,
            aoo_targets_this_round=frozenset({"goblin"})
        )
        assert can_make_aoo(tracker, "goblin") is False

    def test_different_target_allowed(self):
        """Can target different entity even after AoO."""
        tracker = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=4,
            aoo_used_this_round=1,
            aoo_targets_this_round=frozenset({"goblin"})
        )
        assert can_make_aoo(tracker, "orc") is True

    def test_max_exhausted(self, combat_reflexes_tracker):
        """Cannot make AoO when max exhausted."""
        tracker = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=4,
            aoo_used_this_round=4,
            aoo_targets_this_round=frozenset({"a", "b", "c", "d"})
        )
        assert can_make_aoo(tracker, "new_target") is False


# ==============================================================================
# RECORD_AOO TESTS
# ==============================================================================

class TestRecordAoO:
    """Tests for record_aoo function."""

    def test_increments_counter(self, basic_tracker):
        """Recording AoO increments the counter."""
        new_tracker = record_aoo(basic_tracker, "goblin")
        assert new_tracker.aoo_used_this_round == 1
        assert basic_tracker.aoo_used_this_round == 0  # Original unchanged

    def test_adds_target_to_set(self, basic_tracker):
        """Recording AoO adds target to set."""
        new_tracker = record_aoo(basic_tracker, "goblin")
        assert "goblin" in new_tracker.aoo_targets_this_round
        assert "goblin" not in basic_tracker.aoo_targets_this_round

    def test_returns_new_tracker(self, basic_tracker):
        """Returns new tracker instance (immutable)."""
        new_tracker = record_aoo(basic_tracker, "goblin")
        assert new_tracker is not basic_tracker

    def test_preserves_entity_id(self, basic_tracker):
        """Entity ID is preserved."""
        new_tracker = record_aoo(basic_tracker, "goblin")
        assert new_tracker.entity_id == basic_tracker.entity_id

    def test_preserves_max_aoo(self, combat_reflexes_tracker):
        """Max AoO is preserved."""
        new_tracker = record_aoo(combat_reflexes_tracker, "goblin")
        assert new_tracker.max_aoo_per_round == combat_reflexes_tracker.max_aoo_per_round

    def test_multiple_recordings(self, combat_reflexes_tracker):
        """Multiple recordings work correctly."""
        t1 = record_aoo(combat_reflexes_tracker, "goblin")
        t2 = record_aoo(t1, "orc")
        t3 = record_aoo(t2, "bugbear")

        assert t3.aoo_used_this_round == 3
        assert "goblin" in t3.aoo_targets_this_round
        assert "orc" in t3.aoo_targets_this_round
        assert "bugbear" in t3.aoo_targets_this_round


# ==============================================================================
# RESET_AOO_FOR_ROUND TESTS
# ==============================================================================

class TestResetAoOForRound:
    """Tests for reset_aoo_for_round function."""

    def test_clears_counter(self):
        """Resets aoo_used_this_round to 0."""
        tracker = AoOTracker(
            entity_id="fighter",
            max_aoo_per_round=1,
            aoo_used_this_round=1,
            aoo_targets_this_round=frozenset({"goblin"})
        )
        new_tracker = reset_aoo_for_round(tracker)
        assert new_tracker.aoo_used_this_round == 0

    def test_clears_target_set(self):
        """Clears the target set."""
        tracker = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=4,
            aoo_used_this_round=3,
            aoo_targets_this_round=frozenset({"a", "b", "c"})
        )
        new_tracker = reset_aoo_for_round(tracker)
        assert new_tracker.aoo_targets_this_round == frozenset()

    def test_returns_new_tracker(self, basic_tracker):
        """Returns new tracker instance."""
        new_tracker = reset_aoo_for_round(basic_tracker)
        assert new_tracker is not basic_tracker

    def test_preserves_entity_id(self, basic_tracker):
        """Preserves entity ID."""
        new_tracker = reset_aoo_for_round(basic_tracker)
        assert new_tracker.entity_id == basic_tracker.entity_id

    def test_preserves_max_aoo(self, combat_reflexes_tracker):
        """Preserves max_aoo_per_round."""
        tracker = AoOTracker(
            entity_id="monk",
            max_aoo_per_round=4,
            aoo_used_this_round=4,
            aoo_targets_this_round=frozenset({"a", "b", "c", "d"})
        )
        new_tracker = reset_aoo_for_round(tracker)
        assert new_tracker.max_aoo_per_round == 4


# ==============================================================================
# CHECK_AOO_TRIGGER TESTS
# ==============================================================================

class TestCheckAoOTrigger:
    """Tests for check_aoo_trigger function."""

    def test_leaving_threatened_square_triggers(self):
        """Leaving a threatened square triggers AoO."""
        # Fighter at (5,5), enemy moving from (5,6) to (5,7)
        result = check_aoo_trigger(
            mover_id="enemy",
            from_pos=Position(5, 6),  # Adjacent to fighter
            to_pos=Position(5, 7),     # Moving away
            threatener_id="fighter",
            threatener_pos=Position(5, 5),
            reach_ft=5
        )
        assert result is True

    def test_moving_within_threatened_doesnt_trigger(self):
        """Moving within threatened area doesn't trigger (already in threat)."""
        # This is actually still leaving a threatened square, so it DOES trigger
        # PHB clarification: leaving ANY threatened square triggers
        result = check_aoo_trigger(
            mover_id="enemy",
            from_pos=Position(5, 6),   # Adjacent to fighter
            to_pos=Position(6, 6),      # Still adjacent
            threatener_id="fighter",
            threatener_pos=Position(5, 5),
            reach_ft=5
        )
        # This actually triggers because they left the original threatened square
        assert result is True

    def test_entering_threatened_doesnt_trigger(self):
        """Moving INTO a threatened area doesn't trigger."""
        result = check_aoo_trigger(
            mover_id="enemy",
            from_pos=Position(10, 10),  # Far away
            to_pos=Position(5, 6),       # Now adjacent to fighter
            threatener_id="fighter",
            threatener_pos=Position(5, 5),
            reach_ft=5
        )
        assert result is False

    def test_already_outside_doesnt_trigger(self):
        """Moving outside threat range doesn't trigger."""
        result = check_aoo_trigger(
            mover_id="enemy",
            from_pos=Position(10, 10),  # Not threatened
            to_pos=Position(10, 11),     # Still not threatened
            threatener_id="fighter",
            threatener_pos=Position(5, 5),
            reach_ft=5
        )
        assert result is False

    def test_ten_foot_reach_triggers_at_distance_two(self):
        """10ft reach triggers when leaving distance 2."""
        # Large creature or reach weapon with 10ft
        result = check_aoo_trigger(
            mover_id="enemy",
            from_pos=Position(7, 5),  # 2 squares away = 10ft
            to_pos=Position(8, 5),     # Moving further away
            threatener_id="ogre",
            threatener_pos=Position(5, 5),
            reach_ft=10
        )
        assert result is True

    def test_ten_foot_reach_at_distance_one(self):
        """10ft reach: check adjacent (distance 1)."""
        result = check_aoo_trigger(
            mover_id="enemy",
            from_pos=Position(6, 5),  # 1 square away = 5ft (within 10ft)
            to_pos=Position(7, 5),     # Moving away
            threatener_id="ogre",
            threatener_pos=Position(5, 5),
            reach_ft=10
        )
        # Adjacent is within 10ft reach, so leaving triggers
        assert result is True


# ==============================================================================
# AOO MANAGER TESTS
# ==============================================================================

class TestAoOManager:
    """Tests for AoOManager class."""

    def test_register_entity_creates_tracker(self):
        """Register entity creates a tracker."""
        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=2)

        tracker = manager.get_tracker("fighter")
        assert tracker is not None
        assert tracker.entity_id == "fighter"
        assert tracker.max_aoo_per_round == 1

    def test_register_entity_with_combat_reflexes(self):
        """Register entity with Combat Reflexes calculates max correctly."""
        manager = AoOManager()
        manager.register_entity("monk", has_combat_reflexes=True, dex_modifier=3)

        tracker = manager.get_tracker("monk")
        assert tracker is not None
        assert tracker.max_aoo_per_round == 4  # 1 + 3

    def test_get_tracker_unknown_entity(self):
        """Get tracker for unknown entity returns None."""
        manager = AoOManager()
        assert manager.get_tracker("unknown") is None

    def test_start_new_round_resets_all(self):
        """Start new round resets all trackers."""
        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)
        manager.register_entity("monk", has_combat_reflexes=True, dex_modifier=3)

        # Use some AoO
        manager.attempt_aoo("fighter", "goblin")
        manager.attempt_aoo("monk", "orc")

        # Verify used
        assert manager.get_tracker("fighter").aoo_used_this_round == 1
        assert manager.get_tracker("monk").aoo_used_this_round == 1

        # Reset round
        manager.start_new_round()

        # Verify reset
        assert manager.get_tracker("fighter").aoo_used_this_round == 0
        assert manager.get_tracker("monk").aoo_used_this_round == 0
        assert len(manager.get_tracker("fighter").aoo_targets_this_round) == 0
        assert len(manager.get_tracker("monk").aoo_targets_this_round) == 0

    def test_attempt_aoo_succeeds_and_records(self):
        """Attempt AoO succeeds and records usage."""
        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)

        result = manager.attempt_aoo("fighter", "goblin")

        assert result is True
        tracker = manager.get_tracker("fighter")
        assert tracker.aoo_used_this_round == 1
        assert "goblin" in tracker.aoo_targets_this_round

    def test_attempt_aoo_fails_when_exhausted(self):
        """Attempt AoO fails when max exhausted."""
        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)

        # Use the one AoO
        manager.attempt_aoo("fighter", "goblin")

        # Second attempt fails
        result = manager.attempt_aoo("fighter", "orc")
        assert result is False

    def test_attempt_aoo_fails_on_same_target(self):
        """Attempt AoO fails against same target."""
        manager = AoOManager()
        manager.register_entity("monk", has_combat_reflexes=True, dex_modifier=3)

        manager.attempt_aoo("monk", "goblin")

        # Second attempt against same target fails
        result = manager.attempt_aoo("monk", "goblin")
        assert result is False

    def test_attempt_aoo_unknown_attacker(self):
        """Attempt AoO with unknown attacker fails."""
        manager = AoOManager()
        result = manager.attempt_aoo("unknown", "goblin")
        assert result is False

    def test_check_triggers_for_movement(self, empty_grid):
        """Check triggers returns eligible entities."""
        grid = empty_grid
        grid.place_entity("fighter", Position(5, 5), SizeCategory.MEDIUM)
        grid.place_entity("enemy", Position(6, 5), SizeCategory.MEDIUM)

        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)

        # Enemy moves away from fighter
        eligible = manager.check_triggers_for_movement(
            mover_id="enemy",
            from_pos=Position(6, 5),  # Adjacent to fighter
            to_pos=Position(7, 5),     # Moving away
            grid=grid
        )

        assert "fighter" in eligible

    def test_check_triggers_excludes_exhausted(self, empty_grid):
        """Check triggers excludes entities that used their AoO."""
        grid = empty_grid
        grid.place_entity("fighter", Position(5, 5), SizeCategory.MEDIUM)
        grid.place_entity("enemy", Position(6, 5), SizeCategory.MEDIUM)

        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)

        # Fighter already used AoO
        manager.attempt_aoo("fighter", "other_enemy")

        # Enemy moves away
        eligible = manager.check_triggers_for_movement(
            mover_id="enemy",
            from_pos=Position(6, 5),
            to_pos=Position(7, 5),
            grid=grid
        )

        assert "fighter" not in eligible

    def test_serialization_roundtrip(self):
        """Manager serializes and deserializes correctly."""
        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)
        manager.register_entity("monk", has_combat_reflexes=True, dex_modifier=3)
        manager.attempt_aoo("fighter", "goblin")

        data = manager.to_dict()
        restored = AoOManager.from_dict(data)

        assert restored.get_tracker("fighter").aoo_used_this_round == 1
        assert restored.get_tracker("monk").max_aoo_per_round == 4


# ==============================================================================
# INTEGRATION WITH REACH TESTS
# ==============================================================================

class TestReachIntegration:
    """Tests for integration with reach_resolver."""

    def test_five_foot_reach_adjacent(self, empty_grid):
        """5ft reach triggers when leaving adjacent square."""
        grid = empty_grid
        grid.place_entity("fighter", Position(5, 5), SizeCategory.MEDIUM)
        grid.place_entity("goblin", Position(6, 5), SizeCategory.MEDIUM)

        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)

        eligible = manager.check_triggers_for_movement(
            mover_id="goblin",
            from_pos=Position(6, 5),
            to_pos=Position(7, 5),
            grid=grid,
            reach_by_entity={"fighter": 5}
        )

        assert "fighter" in eligible

    def test_ten_foot_reach_distance_two(self, empty_grid):
        """10ft reach triggers when leaving distance 2."""
        grid = empty_grid
        grid.place_entity("ogre", Position(5, 5), SizeCategory.LARGE)
        grid.place_entity("goblin", Position(8, 5), SizeCategory.MEDIUM)

        manager = AoOManager()
        manager.register_entity("ogre", has_combat_reflexes=False, dex_modifier=0)

        eligible = manager.check_triggers_for_movement(
            mover_id="goblin",
            from_pos=Position(8, 5),  # 2 squares from ogre's closest square
            to_pos=Position(9, 5),
            grid=grid,
            reach_by_entity={"ogre": 10},
            size_by_entity={"ogre": SizeCategory.LARGE}
        )

        assert "ogre" in eligible

    def test_large_creature_threatens_from_all_squares(self, empty_grid):
        """Large creature threatens from all occupied squares."""
        grid = empty_grid
        # Large creature at (5,5) occupies (5,5), (6,5), (5,6), (6,6)
        grid.place_entity("ogre", Position(5, 5), SizeCategory.LARGE)
        # Goblin at (4,5) - adjacent to ogre's (5,5)
        grid.place_entity("goblin", Position(4, 5), SizeCategory.MEDIUM)

        manager = AoOManager()
        manager.register_entity("ogre", has_combat_reflexes=False, dex_modifier=0)

        eligible = manager.check_triggers_for_movement(
            mover_id="goblin",
            from_pos=Position(4, 5),
            to_pos=Position(3, 5),  # Moving away
            grid=grid,
            reach_by_entity={"ogre": 10},
            size_by_entity={"ogre": SizeCategory.LARGE}
        )

        assert "ogre" in eligible


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_mover_not_in_trigger_list(self, empty_grid):
        """Mover is never in their own trigger list."""
        grid = empty_grid
        grid.place_entity("fighter", Position(5, 5), SizeCategory.MEDIUM)

        manager = AoOManager()
        manager.register_entity("fighter", has_combat_reflexes=False, dex_modifier=0)

        eligible = manager.check_triggers_for_movement(
            mover_id="fighter",
            from_pos=Position(5, 5),
            to_pos=Position(5, 6),
            grid=grid
        )

        assert "fighter" not in eligible

    def test_empty_manager(self):
        """Empty manager handles operations gracefully."""
        manager = AoOManager()

        assert manager.get_tracker("nobody") is None
        assert manager.attempt_aoo("nobody", "target") is False

        # start_new_round on empty manager is fine
        manager.start_new_round()

    def test_combat_reflexes_high_dex_scenario(self):
        """Combat Reflexes with high Dex can make many AoO."""
        manager = AoOManager()
        manager.register_entity("monk", has_combat_reflexes=True, dex_modifier=5)

        targets = ["g1", "g2", "g3", "g4", "g5", "g6"]
        for i, target in enumerate(targets):
            result = manager.attempt_aoo("monk", target)
            if i < 6:  # 1 + 5 = 6 max
                assert result is True
            else:
                assert result is False

        tracker = manager.get_tracker("monk")
        assert tracker.aoo_used_this_round == 6

    def test_multiple_entities_same_trigger(self, empty_grid):
        """Multiple entities can AoO same movement."""
        grid = empty_grid
        grid.place_entity("fighter1", Position(4, 5), SizeCategory.MEDIUM)
        grid.place_entity("fighter2", Position(6, 5), SizeCategory.MEDIUM)
        grid.place_entity("goblin", Position(5, 5), SizeCategory.MEDIUM)

        manager = AoOManager()
        manager.register_entity("fighter1", has_combat_reflexes=False, dex_modifier=0)
        manager.register_entity("fighter2", has_combat_reflexes=False, dex_modifier=0)

        eligible = manager.check_triggers_for_movement(
            mover_id="goblin",
            from_pos=Position(5, 5),
            to_pos=Position(5, 6),
            grid=grid
        )

        assert "fighter1" in eligible
        assert "fighter2" in eligible
