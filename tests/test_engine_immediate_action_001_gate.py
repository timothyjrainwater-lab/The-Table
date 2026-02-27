"""Gate tests: ENGINE-IMMEDIATE-ACTION-001

Immediate action slot in ActionBudget. PHB p.127:
- Once per round.
- Cannot use if swift already used this turn.
- Using immediate burns NEXT TURN's swift slot (pending_swift_burn).

WO-ENGINE-IMMEDIATE-ACTION-001, Batch J (Dispatch #19).
"""

import pytest
from copy import deepcopy
from unittest.mock import MagicMock

from aidm.core.action_economy import ActionBudget
from aidm.core.play_loop import execute_turn
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import ImmediateActionIntent


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(roll=10):
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


def _basic_world(actor_id="hero", budget=None):
    """Build minimal WorldState with one actor and optional pre-set budget."""
    actor = {
        EF.ENTITY_ID: actor_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 15,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: "players",
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.DEX_MOD: 1,
    }
    active_combat = {
        "initiative_order": [actor_id],
        "aoo_used_this_round": [],
        "aoo_count_this_round": {},
        "action_budget_actor": actor_id if budget else None,
        "action_budget": budget.to_dict() if budget else None,
        "pending_swift_burn": False,
    }
    return WorldState(
        ruleset_version="3.5",
        entities={actor_id: actor},
        active_combat=active_combat,
    )


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineImmediateAction001Gate:

    def test_IA001_immediate_action_consumed(self):
        """IA-001: Actor takes immediate action — immediate_used set; action consumed."""
        ws = _basic_world()
        intent = ImmediateActionIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result.status != "action_denied", f"Immediate action denied unexpectedly"
        # Budget should have immediate_used=True
        budget_raw = result.world_state.active_combat.get("action_budget")
        assert budget_raw is not None
        budget = ActionBudget.from_dict(budget_raw)
        assert budget.immediate_used is True

    def test_IA002_second_immediate_denied(self):
        """IA-002: Actor attempts second immediate action same turn — denied."""
        budget = ActionBudget.fresh()
        budget.immediate_used = True
        ws = _basic_world(budget=budget)
        intent = ImmediateActionIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        denied = _events_of_type(result, "ACTION_DENIED")
        assert len(denied) >= 1, "Second immediate action should be denied"
        assert result.status == "action_denied"

    def test_IA003_swift_used_blocks_immediate(self):
        """IA-003: Actor uses swift action then tries immediate — denied (PHB p.127)."""
        budget = ActionBudget.fresh()
        budget.swift_used = True
        ws = _basic_world(budget=budget)
        intent = ImmediateActionIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        denied = _events_of_type(result, "ACTION_DENIED")
        assert len(denied) >= 1, "Immediate denied when swift already used"
        assert result.status == "action_denied"

    def test_IA004_immediate_burns_next_swift(self):
        """IA-004: Actor uses immediate action; next turn's swift slot pre-burned."""
        ws = _basic_world()
        intent = ImmediateActionIntent(actor_id="hero")
        rng = _make_rng()

        result1 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result1.status != "action_denied"
        # pending_swift_burn should be set in active_combat
        pending = result1.world_state.active_combat.get("pending_swift_burn")
        assert pending is True, "pending_swift_burn must be True after immediate action"

        # Next turn: fresh budget but pending_swift_burn causes swift pre-burn
        # Simulate turn change by clearing action_budget_actor
        ac_next = deepcopy(result1.world_state.active_combat)
        ac_next["action_budget_actor"] = None  # Force fresh budget next turn
        ac_next["action_budget"] = None
        ws2 = WorldState(
            ruleset_version=result1.world_state.ruleset_version,
            entities=result1.world_state.entities,
            active_combat=ac_next,
        )

        # Try to take swift action on "next turn"
        from aidm.schemas.intents import RageIntent
        # Use immediate as a proxy for swift (RageIntent is a standard, not swift).
        # The easiest way to test swift_used is check ActionBudget after budget init.
        # We verify via a second ImmediateActionIntent (swift blocked → immediate blocked).
        intent2 = ImmediateActionIntent(actor_id="hero")
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws2,
            combat_intent=intent2,
            rng=rng,
        )
        # pending_swift_burn pre-burned swift → immediate should be denied
        denied = _events_of_type(result2, "ACTION_DENIED")
        assert len(denied) >= 1, "Immediate should be denied when swift pre-burned from prior immediate"

    def test_IA005_immediate_does_not_affect_standard(self):
        """IA-005: Actor uses immediate action; standard action unaffected."""
        ws = _basic_world()
        from aidm.schemas.attack import AttackIntent, Weapon
        actor = {
            EF.ENTITY_ID: "hero",
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.AC: 15,
            EF.ATTACK_BONUS: 5,
            EF.TEAM: "players",
            EF.POSITION: {"x": 0, "y": 0},
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 1,
        }
        enemy = {
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
        ws = WorldState(
            ruleset_version="3.5",
            entities={"hero": actor, "goblin": enemy},
            active_combat={
                "initiative_order": ["hero", "goblin"],
                "aoo_used_this_round": [],
                "aoo_count_this_round": {},
                "action_budget_actor": None,
                "action_budget": None,
                "pending_swift_burn": False,
            },
        )
        rng = _make_rng(roll=18)

        # Take immediate first
        result1 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=ImmediateActionIntent(actor_id="hero"),
            rng=rng,
        )
        assert result1.status != "action_denied", "Immediate should succeed"

        # Standard action (attack) should still be available
        weapon = Weapon(
            damage_dice="1d8", damage_bonus=2, damage_type="slashing",
            critical_range=20, critical_multiplier=2, weapon_type="one-handed",
            range_increment=0, enhancement_bonus=0,
        )
        attack_intent = AttackIntent(
            attacker_id="hero", target_id="goblin", attack_bonus=5, weapon=weapon,
        )
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=result1.world_state,
            combat_intent=attack_intent,
            rng=rng,
        )
        denied = _events_of_type(result2, "ACTION_DENIED")
        assert len(denied) == 0, "Standard action should not be denied after immediate"

    def test_IA006_pending_swift_burn_cleared_second_turn(self):
        """IA-006: After second turn passes with no immediate, swift available again."""
        ws = _basic_world()
        intent = ImmediateActionIntent(actor_id="hero")
        rng = _make_rng()

        result1 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result1.world_state.active_combat.get("pending_swift_burn") is True

        # First "next turn" — swift is pre-burned
        ac2 = deepcopy(result1.world_state.active_combat)
        ac2["action_budget_actor"] = None
        ac2["action_budget"] = None
        ws2 = WorldState(
            ruleset_version=result1.world_state.ruleset_version,
            entities=result1.world_state.entities,
            active_combat=ac2,
        )
        # On this turn, taking an immediate will consume pending_swift_burn check
        # and try to deny via swift_used. BUT if we don't take immediate,
        # pending_swift_burn gets cleared. Take a no-op immediate to trigger the init:
        # Actually taking a non-immediate is fine — the swift burn happens at budget init.
        # Use ImmediateActionIntent to trigger budget init with pending_swift_burn.
        result2 = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws2,
            combat_intent=ImmediateActionIntent(actor_id="hero"),
            rng=rng,
        )
        # ImmediateActionIntent denied because swift pre-burned
        # That's OK. Now pending_swift_burn should be cleared in result2's world_state.
        pending2 = result2.world_state.active_combat.get("pending_swift_burn")
        assert pending2 is False or pending2 is None, \
            "pending_swift_burn should be cleared after being consumed"

    def test_IA007_no_immediate_taken_slot_available(self):
        """IA-007: Actor with no immediate action taken this turn — immediate slot available."""
        budget = ActionBudget.fresh()
        assert budget.immediate_used is False
        assert budget.can_use("immediate") is True

    def test_IA008_fresh_budget_immediate_false(self):
        """IA-008: Fresh ActionBudget has immediate_used=False."""
        budget = ActionBudget.fresh()
        assert budget.immediate_used is False

        # Serialization round-trip
        budget_dict = budget.to_dict()
        assert "immediate_used" in budget_dict
        assert budget_dict["immediate_used"] is False

        restored = ActionBudget.from_dict(budget_dict)
        assert restored.immediate_used is False
