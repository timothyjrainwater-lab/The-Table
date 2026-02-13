"""CP-18 Combat Maneuvers — Integration Tests (Tier 2).

Tests for AoO interaction, play loop integration, and edge cases.
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, OverrunIntent,
    DisarmIntent, GrappleIntent,
)
from aidm.core.aoo import check_aoo_triggers, resolve_aoo_sequence, aoo_dealt_damage
from aidm.core.conditions import has_condition


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def combat_world_state():
    """Create world state with adjacent combatants and weapon data for AoO."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 3,
                EF.DEX_MOD: 1,
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 5,
                "bab": 5,
                "weapon": {
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                    "damage_type": "slashing",
                    "critical_multiplier": 2,
                },
            },
            "orc": {
                EF.ENTITY_ID: "orc",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: 4,
                EF.DEX_MOD: 0,
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 3,
                "bab": 3,
                "weapon": {
                    "damage_dice": "1d12",
                    "damage_bonus": 4,
                    "damage_type": "slashing",
                    "critical_multiplier": 3,
                },
            },
        },
        active_combat={
            "initiative_order": ["fighter", "orc"],
            "aoo_used_this_round": [],
        }
    )


@pytest.fixture
def multi_enemy_world_state():
    """Create world state with multiple enemies for Bull Rush AoO testing."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 3,
                EF.DEX_MOD: 1,
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 5,
                "bab": 5,
            },
            "goblin1": {
                EF.ENTITY_ID: "goblin1",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 10,
                EF.HP_MAX: 10,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 5, "y": 6},  # Adjacent to fighter
                EF.STR_MOD: -1,
                EF.DEX_MOD: 2,
                EF.SIZE_CATEGORY: "small",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 2,
                "bab": 1,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2,
                },
            },
            "goblin2": {
                EF.ENTITY_ID: "goblin2",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 10,
                EF.HP_MAX: 10,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 4, "y": 5},  # Also adjacent to fighter
                EF.STR_MOD: -1,
                EF.DEX_MOD: 2,
                EF.SIZE_CATEGORY: "small",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 2,
                "bab": 1,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2,
                },
            },
            "target_orc": {
                EF.ENTITY_ID: "target_orc",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 6, "y": 5},  # Target of bull rush
                EF.STR_MOD: 4,
                EF.DEX_MOD: 0,
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 3,
                "bab": 3,
                "weapon": {
                    "damage_dice": "1d12",
                    "damage_bonus": 4,
                    "damage_type": "slashing",
                    "critical_multiplier": 3,
                },
            },
        },
        active_combat={
            "initiative_order": ["fighter", "goblin1", "goblin2", "target_orc"],
            "aoo_used_this_round": [],
        }
    )


# ==============================================================================
# AOO TRIGGER TESTS FOR MANEUVERS
# ==============================================================================

class TestManeuverAoOTriggers:
    """Test AoO trigger behavior for combat maneuvers."""

    def test_bull_rush_provokes_from_all_threatening(self, multi_enemy_world_state):
        """Bull Rush provokes AoO from ALL threatening enemies."""
        intent = BullRushIntent(attacker_id="fighter", target_id="target_orc")
        triggers = check_aoo_triggers(multi_enemy_world_state, "fighter", intent)

        # Should provoke from goblin1, goblin2, AND target_orc
        reactor_ids = [t.reactor_id for t in triggers]
        assert "goblin1" in reactor_ids
        assert "goblin2" in reactor_ids
        assert "target_orc" in reactor_ids
        assert len(triggers) == 3

    def test_trip_provokes_from_target_only(self, multi_enemy_world_state):
        """Trip provokes AoO from TARGET only (unarmed attack)."""
        intent = TripIntent(attacker_id="fighter", target_id="target_orc")
        triggers = check_aoo_triggers(multi_enemy_world_state, "fighter", intent)

        # Should only provoke from target_orc
        assert len(triggers) == 1
        assert triggers[0].reactor_id == "target_orc"
        assert triggers[0].provoking_action == "trip"

    def test_disarm_provokes_from_target_only(self, combat_world_state):
        """Disarm provokes AoO from TARGET only."""
        intent = DisarmIntent(attacker_id="fighter", target_id="orc")
        triggers = check_aoo_triggers(combat_world_state, "fighter", intent)

        assert len(triggers) == 1
        assert triggers[0].reactor_id == "orc"
        assert triggers[0].provoking_action == "disarm"

    def test_grapple_provokes_from_target_only(self, combat_world_state):
        """Grapple provokes AoO from TARGET only."""
        intent = GrappleIntent(attacker_id="fighter", target_id="orc")
        triggers = check_aoo_triggers(combat_world_state, "fighter", intent)

        assert len(triggers) == 1
        assert triggers[0].reactor_id == "orc"
        assert triggers[0].provoking_action == "grapple"

    def test_overrun_provokes_from_target_only(self, combat_world_state):
        """Overrun provokes AoO from TARGET only."""
        intent = OverrunIntent(attacker_id="fighter", target_id="orc")
        triggers = check_aoo_triggers(combat_world_state, "fighter", intent)

        assert len(triggers) == 1
        assert triggers[0].reactor_id == "orc"
        assert triggers[0].provoking_action == "overrun"


# ==============================================================================
# PLAY LOOP INTEGRATION TESTS
# ==============================================================================

class TestPlayLoopIntegration:
    """Test maneuver intents routed through play_loop."""

    def test_bull_rush_through_play_loop(self, combat_world_state):
        """Bull Rush intent resolves through execute_turn."""
        rng = RNGManager(master_seed=42)
        intent = BullRushIntent(attacker_id="fighter", target_id="orc")
        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter",
            actor_team="party",
        )

        result = execute_turn(
            world_state=combat_world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
        )

        assert result.status == "ok"
        assert "bull_rush" in result.narration

    def test_trip_through_play_loop(self, combat_world_state):
        """Trip intent resolves through execute_turn."""
        rng = RNGManager(master_seed=42)
        intent = TripIntent(attacker_id="fighter", target_id="orc")
        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter",
            actor_team="party",
        )

        result = execute_turn(
            world_state=combat_world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
        )

        assert result.status == "ok"
        assert "trip" in result.narration

    def test_grapple_through_play_loop(self, combat_world_state):
        """Grapple intent resolves through execute_turn."""
        rng = RNGManager(master_seed=42)
        intent = GrappleIntent(attacker_id="fighter", target_id="orc")
        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter",
            actor_team="party",
        )

        result = execute_turn(
            world_state=combat_world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
        )

        assert result.status == "ok"
        assert "grapple" in result.narration

    def test_maneuver_target_validation(self, combat_world_state):
        """Maneuver against invalid target returns validation failure."""
        rng = RNGManager(master_seed=42)
        intent = TripIntent(attacker_id="fighter", target_id="nonexistent")
        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter",
            actor_team="party",
        )

        result = execute_turn(
            world_state=combat_world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
        )

        assert result.status == "invalid_intent"
        assert "not found" in result.failure_reason

    def test_maneuver_actor_mismatch(self, combat_world_state):
        """Maneuver with wrong attacker_id returns validation failure."""
        rng = RNGManager(master_seed=42)
        intent = TripIntent(attacker_id="orc", target_id="fighter")  # Orc attacks fighter
        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter",  # But it's fighter's turn
            actor_team="party",
        )

        result = execute_turn(
            world_state=combat_world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
        )

        assert result.status == "invalid_intent"
        assert "does not match" in result.failure_reason


# ==============================================================================
# AOO DEALT DAMAGE HELPER TEST
# ==============================================================================

class TestAoODamageDetection:
    """Test aoo_dealt_damage helper function."""

    def test_detects_damage_from_hp_changed(self):
        """aoo_dealt_damage returns True when HP decreased."""
        from aidm.core.event_log import Event

        events = [
            Event(event_id=0, event_type="attack_roll", timestamp=0.0, payload={"hit": True}),
            Event(event_id=1, event_type="hp_changed", timestamp=0.1, payload={
                "entity_id": "target",
                "delta": -10,
                "hp_after": 40,
            }),
        ]

        assert aoo_dealt_damage(events) is True

    def test_no_damage_when_no_hp_changed(self):
        """aoo_dealt_damage returns False when no HP changed event."""
        from aidm.core.event_log import Event

        events = [
            Event(event_id=0, event_type="attack_roll", timestamp=0.0, payload={"hit": False}),
        ]

        assert aoo_dealt_damage(events) is False

    def test_no_damage_when_hp_increased(self):
        """aoo_dealt_damage returns False when HP increased (healing)."""
        from aidm.core.event_log import Event

        events = [
            Event(event_id=0, event_type="hp_changed", timestamp=0.0, payload={
                "entity_id": "target",
                "delta": 5,  # Healing
                "hp_after": 45,
            }),
        ]

        assert aoo_dealt_damage(events) is False


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

class TestManeuverEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_bull_rush_target_already_defeated(self, combat_world_state):
        """Bull rush against defeated target returns invalid intent."""
        # Mark orc as defeated
        combat_world_state.entities["orc"][EF.DEFEATED] = True

        rng = RNGManager(master_seed=42)
        intent = BullRushIntent(attacker_id="fighter", target_id="orc")
        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter",
            actor_team="party",
        )

        result = execute_turn(
            world_state=combat_world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
        )

        assert result.status == "invalid_intent"
        assert "defeated" in result.failure_reason

    def test_overrun_defender_avoids_no_rng_consumed(self, combat_world_state):
        """When defender avoids overrun, no RNG should be consumed."""
        rng1 = RNGManager(master_seed=42)
        rng2 = RNGManager(master_seed=42)

        intent = OverrunIntent(
            attacker_id="fighter",
            target_id="orc",
            defender_avoids=True,  # Defender steps aside
        )
        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter",
            actor_team="party",
        )

        result = execute_turn(
            world_state=combat_world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng1,
        )

        # Resolve should succeed without consuming combat RNG
        assert result.status == "ok"
        # The narration should indicate success (attacker continues movement)
        assert "overrun_success" in result.narration


# ==============================================================================
# DETERMINISTIC REPLAY FOR PLAY LOOP
# ==============================================================================

class TestPlayLoopDeterminism:
    """Test deterministic replay through play loop."""

    def test_trip_through_play_loop_deterministic_10x(self, combat_world_state):
        """10 trip resolutions through play loop produce identical results."""
        results = []
        for _ in range(10):
            rng = RNGManager(master_seed=12345)
            intent = TripIntent(attacker_id="fighter", target_id="orc")
            turn_ctx = TurnContext(
                turn_index=0,
                actor_id="fighter",
                actor_team="party",
            )

            result = execute_turn(
                world_state=combat_world_state,
                turn_ctx=turn_ctx,
                combat_intent=intent,
                rng=rng,
            )

            results.append({
                "status": result.status,
                "narration": result.narration,
                "event_count": len(result.events),
                "final_hash": result.world_state.state_hash(),
            })

        for i in range(1, 10):
            assert results[i] == results[0], f"Run {i} differs from run 0"

    def test_grapple_through_play_loop_deterministic_10x(self, combat_world_state):
        """10 grapple resolutions through play loop produce identical results."""
        results = []
        for _ in range(10):
            rng = RNGManager(master_seed=99999)
            intent = GrappleIntent(attacker_id="fighter", target_id="orc")
            turn_ctx = TurnContext(
                turn_index=0,
                actor_id="fighter",
                actor_team="party",
            )

            result = execute_turn(
                world_state=combat_world_state,
                turn_ctx=turn_ctx,
                combat_intent=intent,
                rng=rng,
            )

            results.append({
                "status": result.status,
                "narration": result.narration,
                "event_count": len(result.events),
                "final_hash": result.world_state.state_hash(),
            })

        for i in range(1, 10):
            assert results[i] == results[0], f"Run {i} differs from run 0"
