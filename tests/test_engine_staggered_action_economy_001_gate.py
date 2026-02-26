"""Gate tests: ENGINE-STAGGERED-ACTION-ECONOMY-001

Staggered actor can only take a single move OR standard action per round.
Full-round actions blocked outright. PHB p.301.

WO-ENGINE-STAGGERED-ACTION-ECONOMY-001, Batch I (Dispatch #18).
"""

import pytest
from unittest.mock import MagicMock
from copy import deepcopy

from aidm.core.action_economy import ActionBudget
from aidm.core.play_loop import execute_turn
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import AttackIntent, Weapon, StepMoveIntent
from aidm.schemas.position import Position
from aidm.core.full_attack_resolver import FullAttackIntent
from aidm.schemas.intents import DelayIntent, StandIntent, MoveIntent


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(roll=15):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _make_turn_ctx(actor_id="hero"):
    ctx = MagicMock()
    ctx.actor_id = actor_id
    ctx.turn_index = 0
    ctx.actor_team = "players"
    return ctx


def _basic_world(actor_conditions=None, actor_id="hero", enemy_id=None):
    """Build a minimal WorldState with one actor."""
    actor = {
        EF.ENTITY_ID: actor_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 15,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: "players",
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: actor_conditions if actor_conditions is not None else {},
        EF.FEATS: [],
        EF.DEX_MOD: 1,
    }
    entities = {actor_id: actor}
    if enemy_id:
        entities[enemy_id] = {
            EF.ENTITY_ID: enemy_id,
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.AC: 12,
            EF.ATTACK_BONUS: 3,
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 5, "y": 5},  # Far away — no AoO on move
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
        }

    active_combat = {
        "initiative_order": [actor_id] + ([enemy_id] if enemy_id else []),
        "aoo_used_this_round": [],
        "aoo_count_this_round": {},
        "action_budget_actor": None,
        "action_budget": None,
    }
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat=active_combat,
    )


def _make_weapon():
    return Weapon(
        damage_dice="1d8",
        damage_bonus=2,
        damage_type="slashing",
        critical_range=20,
        critical_multiplier=2,
        weapon_type="one-handed",
        range_increment=0,
        enhancement_bonus=0,
    )


def _make_attack_intent(actor_id="hero", target_id="goblin"):
    return AttackIntent(
        attacker_id=actor_id,
        target_id=target_id,
        attack_bonus=5,
        weapon=_make_weapon(),
    )


def _make_step_move_intent(actor_id="hero"):
    return StandIntent(actor_id=actor_id)  # Stand on a non-prone actor = move action, no AoO


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestStaggeredActionEconomy001Gate:

    def test_SA001_staggered_standard_resolves_move_locked(self):
        """SA-001: Staggered actor takes standard action — standard resolves; move locked afterward."""
        ws = _basic_world(
            actor_conditions={"staggered": {}},
            actor_id="hero",
            enemy_id="goblin",
        )
        intent = _make_attack_intent("hero", "goblin")
        rng = _make_rng(roll=18)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        # Standard action should proceed (not denied)
        denied = _events_of_type(result, "ACTION_DENIED")
        assert len(denied) == 0, f"Standard action denied unexpectedly: {denied}"

        # Now try to also take a move action — move slot should be locked
        ws2 = result.world_state
        move_intent = _make_step_move_intent("hero")
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws2,
            combat_intent=move_intent,
            rng=rng,
        )
        denied2 = _events_of_type(result2, "ACTION_DENIED")
        assert len(denied2) >= 1, "Move after standard should be denied for staggered actor"

    def test_SA002_staggered_move_resolves_standard_locked(self):
        """SA-002: Staggered actor takes move action — move resolves; standard locked afterward."""
        ws = _basic_world(
            actor_conditions={"staggered": {}},
            actor_id="hero",
        )
        move_intent = _make_step_move_intent("hero")
        rng = _make_rng(roll=12)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=move_intent,
            rng=rng,
        )
        denied = _events_of_type(result, "ACTION_DENIED")
        assert len(denied) == 0, f"Move action denied unexpectedly: {denied}"

        # Second call — standard should now be denied
        ws2 = result.world_state
        # Add enemy to ws2 so attack has a target
        entities2 = deepcopy(ws2.entities)
        entities2["goblin"] = {
            EF.ENTITY_ID: "goblin",
            EF.HP_CURRENT: 15,
            EF.HP_MAX: 15,
            EF.AC: 12,
            EF.ATTACK_BONUS: 2,
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 5, "y": 5},
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
        }
        ws2_with_enemy = WorldState(
            ruleset_version=ws2.ruleset_version,
            entities=entities2,
            active_combat=ws2.active_combat,
        )
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws2_with_enemy,
            combat_intent=_make_attack_intent("hero", "goblin"),
            rng=rng,
        )
        denied2 = _events_of_type(result2, "ACTION_DENIED")
        assert len(denied2) >= 1, "Standard after move should be denied for staggered actor"

    def test_SA003_staggered_full_round_denied(self):
        """SA-003: Staggered actor attempts full-round action — denied with staggered_no_full_round."""
        ws = _basic_world(
            actor_conditions={"staggered": {}},
            actor_id="hero",
            enemy_id="goblin",
        )
        rng = _make_rng(roll=18)
        full_intent = FullAttackIntent(
            attacker_id="hero",
            target_id="goblin",
            base_attack_bonus=5,
            weapon=_make_weapon(),
        )

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=full_intent,
            rng=rng,
        )
        denied = _events_of_type(result, "ACTION_DENIED")
        assert len(denied) >= 1, "Full-round should be denied for staggered actor"
        reasons = [e.payload.get("reason") for e in denied]
        assert "staggered_no_full_round" in reasons, \
            f"Expected staggered_no_full_round reason, got: {reasons}"
        assert result.status == "action_denied"

    def test_SA004_staggered_second_action_after_standard_denied(self):
        """SA-004: Staggered actor attempts second standard after standard — denied."""
        ws = _basic_world(
            actor_conditions={"staggered": {}},
            actor_id="hero",
            enemy_id="goblin",
        )
        intent = _make_attack_intent("hero", "goblin")
        rng = _make_rng(roll=18)

        # First standard (attack)
        result1 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result1.status != "action_denied", "First standard should not be denied"

        # Second standard — should be denied (move locked → can't take another standard)
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=result1.world_state,
            combat_intent=intent,
            rng=rng,
        )
        denied = _events_of_type(result2, "ACTION_DENIED")
        assert len(denied) >= 1, "Second standard should be denied for staggered actor"

    def test_SA005_staggered_second_action_after_move_denied(self):
        """SA-005: Staggered actor attempts standard after move — denied."""
        ws = _basic_world(
            actor_conditions={"staggered": {}},
            actor_id="hero",
        )
        move_intent = _make_step_move_intent("hero")
        rng = _make_rng(roll=12)

        result1 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=move_intent,
            rng=rng,
        )
        assert result1.status != "action_denied", "First move should not be denied"

        # Standard after move — denied
        entities2 = deepcopy(result1.world_state.entities)
        entities2["goblin"] = {
            EF.ENTITY_ID: "goblin",
            EF.HP_CURRENT: 15,
            EF.HP_MAX: 15,
            EF.AC: 12,
            EF.ATTACK_BONUS: 2,
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 5, "y": 5},
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
        }
        ws2 = WorldState(
            ruleset_version=result1.world_state.ruleset_version,
            entities=entities2,
            active_combat=result1.world_state.active_combat,
        )
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws2,
            combat_intent=_make_attack_intent("hero", "goblin"),
            rng=rng,
        )
        denied = _events_of_type(result2, "ACTION_DENIED")
        assert len(denied) >= 1, "Standard after move denied for staggered"

    def test_SA006_non_staggered_full_budget(self):
        """SA-006: Non-staggered actor; standard + move both available; no restriction."""
        ws = _basic_world(
            actor_conditions={},  # NOT staggered
            actor_id="hero",
            enemy_id="goblin",
        )
        rng = _make_rng(roll=18)

        # Standard should succeed
        result1 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=_make_attack_intent("hero", "goblin"),
            rng=rng,
        )
        assert result1.status != "action_denied"

        # Move should also succeed (non-staggered has full budget)
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=result1.world_state,
            combat_intent=_make_step_move_intent("hero"),
            rng=rng,
        )
        denied = _events_of_type(result2, "ACTION_DENIED")
        assert len(denied) == 0, "Non-staggered actor should be able to move after standard"

    def test_SA007_staggered_free_action_not_restricted(self):
        """SA-007: Staggered actor takes StandIntent (move action) — no crash, staggered applies to move."""
        # Staggered only restricts move/standard — test that StandIntent (move) works for first action
        ws = _basic_world(
            actor_conditions={"staggered": {}, "prone": {}},
            actor_id="hero",
        )
        intent = StandIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        # Stand (move action) as first action should resolve, not be denied for full_round
        assert result is not None
        staggered_denied = [
            e for e in result.events
            if e.event_type == "ACTION_DENIED"
            and e.payload.get("reason") == "staggered_no_full_round"
        ]
        assert len(staggered_denied) == 0, "Stand (move action) should not trigger staggered_no_full_round denial"

    def test_SA008_staggered_cleared_mid_turn_no_crash(self):
        """SA-008: Actor not staggered (condition cleared) — full budget available, no crash."""
        ws = _basic_world(
            actor_conditions={},  # Already cleared
            actor_id="hero",
            enemy_id="goblin",
        )
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=_make_attack_intent("hero", "goblin"),
            rng=rng,
        )
        assert result is not None, "execute_turn must not crash"
        # No staggered restriction with empty conditions
        staggered_denials = [
            e for e in result.events
            if e.event_type == "ACTION_DENIED" and "staggered" in str(e.payload.get("reason", ""))
        ]
        assert len(staggered_denials) == 0, "No staggered denials when condition cleared"
