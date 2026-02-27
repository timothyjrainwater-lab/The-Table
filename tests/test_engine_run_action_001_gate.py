"""Gate tests: ENGINE-RUN-ACTION-001

Run action (PHB p.144):
- Full-round action: moves at ×4 base speed.
- Applies RUNNING condition (loses DEX to AC until start of next turn).
- Staggered actors cannot run (full-round blocked).

WO-ENGINE-RUN-ACTION-001, Batch J (Dispatch #19).
"""

import pytest
from copy import deepcopy
from unittest.mock import MagicMock

from aidm.core.play_loop import execute_turn
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RunIntent
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.conditions import create_staggered_condition
from aidm.core.full_attack_resolver import FullAttackIntent


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


def _basic_world(actor_id="hero", conditions=None, base_speed=None, enemy_id=None):
    actor = {
        EF.ENTITY_ID: actor_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 15,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: "players",
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: [],
        EF.DEX_MOD: 3,
    }
    if base_speed is not None:
        actor[EF.BASE_SPEED] = base_speed
    entities = {actor_id: actor}
    if enemy_id:
        entities[enemy_id] = {
            EF.ENTITY_ID: enemy_id,
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.AC: 12,
            EF.ATTACK_BONUS: 3,
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 1, "y": 0},  # Adjacent for attack testing
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 1,
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
        damage_dice="1d8", damage_bonus=0, damage_type="slashing",
        critical_range=20, critical_multiplier=2, weapon_type="one-handed",
        range_increment=0, enhancement_bonus=0,
    )


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineRunAction001Gate:

    def test_RN001_run_speed_30_moves_120ft_running_condition_applied(self):
        """RN-001: Actor with speed 30 takes RunIntent — moves 120 ft (×4); RUNNING condition applied."""
        ws = _basic_world(base_speed=30)
        intent = RunIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result.status != "action_denied", "RunIntent should not be denied on fresh budget"

        # entity_moved event with distance_ft=120
        moved_events = _events_of_type(result, "entity_moved")
        assert any(e.payload.get("distance_ft") == 120 for e in moved_events), \
            f"Expected entity_moved with distance_ft=120, got: {[e.payload for e in moved_events]}"

        # RUNNING condition applied
        actor_conds = result.world_state.entities.get("hero", {}).get(EF.CONDITIONS, {})
        assert "running" in actor_conds, "RUNNING condition must be applied after RunIntent"

        # condition_applied event
        cond_applied = _events_of_type(result, "condition_applied")
        assert any(e.payload.get("condition") == "running" for e in cond_applied), \
            "condition_applied event for 'running' must be emitted"

    def test_RN002_running_condition_loses_dex_to_ac(self):
        """RN-002: Actor with RUNNING condition is attacked — RUNNING.loses_dex_to_ac is True."""
        from aidm.schemas.conditions import create_running_condition
        # Verify RUNNING condition has loses_dex_to_ac=True
        cond = create_running_condition(source="test", applied_at_event_id=0)
        assert cond.modifiers.loses_dex_to_ac is True, \
            "RUNNING condition must set loses_dex_to_ac=True (PHB p.144)"

        # Also verify it appears correctly in entity state after RunIntent
        ws = _basic_world(base_speed=30)
        intent = RunIntent(actor_id="hero")
        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=_make_rng(),
        )
        actor_conds = result.world_state.entities.get("hero", {}).get(EF.CONDITIONS, {})
        assert "running" in actor_conds
        running_dict = actor_conds["running"]
        mods = running_dict.get("modifiers", {})
        assert mods.get("loses_dex_to_ac") is True, \
            "RUNNING condition dict must have loses_dex_to_ac=True"

    def test_RN003_running_condition_cleared_next_turn(self):
        """RN-003: Actor with RUNNING condition starts next turn — RUNNING cleared."""
        from aidm.schemas.conditions import create_running_condition
        # Pre-apply RUNNING condition
        cond_dict = create_running_condition(source="run_action", applied_at_event_id=0).to_dict()
        ws = _basic_world(base_speed=30, conditions={"running": cond_dict})

        # Execute a fresh turn (anything — RunIntent or an attack, budget clears differently)
        # Just pass None intent to trigger turn_start expiry
        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=None,
            rng=_make_rng(),
        )
        actor_conds = result.world_state.entities.get("hero", {}).get(EF.CONDITIONS, {})
        assert "running" not in actor_conds, \
            "RUNNING must be cleared at start of actor's next turn"

        # condition_removed event for running
        removed = _events_of_type(result, "condition_removed")
        assert any(e.payload.get("condition") == "running" for e in removed), \
            "condition_removed event for 'running' must be emitted at turn start"

    def test_RN004_staggered_run_denied(self):
        """RN-004: Staggered actor attempts RunIntent — denied (full-round blocked by staggered guard)."""
        staggered_cond = create_staggered_condition(source="test", applied_at_event_id=0).to_dict()
        ws = _basic_world(conditions={"staggered": staggered_cond})
        intent = RunIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        denied = _events_of_type(result, "ACTION_DENIED")
        assert len(denied) >= 1, "Staggered actor must not be able to run"
        reasons = [e.payload.get("reason") for e in denied]
        assert "staggered_no_full_round" in reasons, \
            f"Expected staggered_no_full_round, got: {reasons}"
        assert result.status == "action_denied"

    def test_RN005_run_blocked_if_standard_already_used(self):
        """RN-005: Actor uses RunIntent after standard action — denied (full-round blocked)."""
        from aidm.core.action_economy import ActionBudget
        budget = ActionBudget.fresh()
        budget.standard_used = True

        ws = _basic_world()
        # Inject pre-used budget
        ac = deepcopy(ws.active_combat)
        ac["action_budget_actor"] = "hero"
        ac["action_budget"] = budget.to_dict()
        ws = WorldState(
            ruleset_version=ws.ruleset_version,
            entities=ws.entities,
            active_combat=ac,
        )
        intent = RunIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        denied = _events_of_type(result, "ACTION_DENIED")
        assert len(denied) >= 1, "RunIntent (full-round) must be denied if standard already used"
        assert result.status == "action_denied"

    def test_RN006_run_fresh_budget_full_round_consumed(self):
        """RN-006: Actor uses RunIntent on fresh budget — full_round consumed; no remaining standard/move."""
        from aidm.core.action_economy import ActionBudget
        ws = _basic_world()
        intent = RunIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result.status != "action_denied", "Run on fresh budget must succeed"

        budget_raw = result.world_state.active_combat.get("action_budget")
        assert budget_raw is not None
        budget = ActionBudget.from_dict(budget_raw)
        assert budget.full_round_used is True, "full_round slot must be consumed"
        # standard and move should also be locked (full_round consumes both)
        assert not budget.can_use("standard"), "standard must not be available after full-round"
        assert not budget.can_use("move"), "move must not be available after full-round"

    def test_RN007_non_running_actor_normal_ac(self):
        """RN-007: Non-running actor attacked — normal AC; no RUNNING penalty."""
        from aidm.schemas.conditions import create_running_condition
        # Verify normal actor has no RUNNING
        ws = _basic_world()
        actor_conds = ws.entities["hero"].get(EF.CONDITIONS, {})
        assert "running" not in actor_conds, "Fresh actor must not have RUNNING condition"

        # Verify condition factory: non-running has no loses_dex_to_ac from running
        from aidm.core.conditions import get_condition_modifiers
        mods = get_condition_modifiers(ws, "hero")
        # loses_dex_to_ac should be False for a fresh actor with no RUNNING
        assert mods.loses_dex_to_ac is False, \
            "Non-running actor must not have loses_dex_to_ac set"

    def test_RN008_no_base_speed_defaults_to_30(self):
        """RN-008: Actor with no BASE_SPEED field defaults to 30 ft; moves 120 ft; no crash."""
        ws = _basic_world()  # No BASE_SPEED set
        assert EF.BASE_SPEED not in ws.entities["hero"], "Test setup: BASE_SPEED must be absent"

        intent = RunIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None, "Must not crash when BASE_SPEED absent"
        assert result.status != "action_denied"

        moved_events = _events_of_type(result, "entity_moved")
        assert any(e.payload.get("distance_ft") == 120 for e in moved_events), \
            f"Default speed 30 → 120 ft run. Got: {[e.payload for e in moved_events]}"
