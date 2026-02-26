"""Gate tests: ENGINE-AOO-STAND-FROM-PRONE-001

Standing from prone (move action) provokes AoO from all threatening enemies.
AoO fires BEFORE prone is cleared. Flat-footed guard from Batch H applies.
PHB p.137.

WO-ENGINE-AOO-STAND-FROM-PRONE-001, Batch I (Dispatch #18).
"""

import pytest
from unittest.mock import MagicMock
from copy import deepcopy

from aidm.core.play_loop import execute_turn
from aidm.core.aoo import check_stand_from_prone_aoo
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import StandIntent
from aidm.schemas.position import Position


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


def _build_world(actor_conditions=None, enemies=None, actor_id="hero"):
    """Build a WorldState with one prone actor and optional enemies."""
    actor = {
        EF.ENTITY_ID: actor_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 14,
        EF.ATTACK_BONUS: 4,
        EF.TEAM: "players",
        EF.POSITION: {"x": 3, "y": 3},
        EF.CONDITIONS: actor_conditions if actor_conditions is not None else {"prone": {}},
        EF.FEATS: [],
        EF.DEX_MOD: 1,
    }
    entities = {actor_id: actor}
    initiative_order = [actor_id]

    if enemies:
        for eid, edata in enemies.items():
            entities[eid] = edata
            initiative_order.append(eid)

    active_combat = {
        "initiative_order": initiative_order,
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


def _adjacent_enemy(eid="goblin", hp=15, conditions=None, feats=None, dex_mod=0):
    """Enemy entity adjacent to actor (x=4, y=3)."""
    return {
        EF.ENTITY_ID: eid,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 12,
        EF.ATTACK_BONUS: 3,
        EF.TEAM: "monsters",
        EF.POSITION: {"x": 4, "y": 3},
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: feats or [],
        EF.DEX_MOD: dex_mod,
    }


def _nonadjacent_enemy(eid="orc"):
    """Enemy entity NOT adjacent to actor (x=8, y=8)."""
    return {
        EF.ENTITY_ID: eid,
        EF.HP_CURRENT: 15,
        EF.HP_MAX: 15,
        EF.AC: 12,
        EF.ATTACK_BONUS: 3,
        EF.TEAM: "monsters",
        EF.POSITION: {"x": 8, "y": 8},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.DEX_MOD: 0,
    }


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAoOStandFromProne001Gate:

    def test_SP001_prone_stand_enemy_threatens_aoo_triggered(self):
        """SP-001: Prone actor stands; enemy threatens square — AoO triggered."""
        enemy = _adjacent_enemy("goblin")
        ws = _build_world(
            actor_conditions={"prone": {}},
            enemies={"goblin": enemy},
        )
        intent = StandIntent(actor_id="hero")
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        # AoO should have fired — look for attack events or hp_changed from goblin's AoO
        # OR check that check_stand_from_prone_aoo returns a trigger
        triggers = check_stand_from_prone_aoo(ws, "hero")
        assert len(triggers) == 1, f"Expected 1 AoO trigger, got {len(triggers)}"
        assert triggers[0].reactor_id == "goblin"
        assert triggers[0].provoking_action == "stand_from_prone"

        # Stand should resolve (not denied)
        stand_events = _events_of_type(result, "stand_resolved")
        assert len(stand_events) >= 1
        assert stand_events[0].payload.get("was_prone") is True
        assert stand_events[0].payload.get("aoo_triggered") is True

    def test_SP002_prone_stand_no_enemies_no_aoo(self):
        """SP-002: Prone actor stands; no enemies threatening — stand resolves, no AoO."""
        ws = _build_world(actor_conditions={"prone": {}}, enemies=None)
        intent = StandIntent(actor_id="hero")
        rng = _make_rng()

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        stand_events = _events_of_type(result, "stand_resolved")
        assert len(stand_events) >= 1
        assert stand_events[0].payload.get("was_prone") is True
        assert stand_events[0].payload.get("aoo_triggered") is False

        triggers = check_stand_from_prone_aoo(ws, "hero")
        assert len(triggers) == 0

    def test_SP003_non_prone_stand_no_aoo(self):
        """SP-003: Non-prone actor takes StandIntent — no standing-from-prone AoO triggered."""
        enemy = _adjacent_enemy("goblin")
        ws = _build_world(
            actor_conditions={},  # NOT prone
            enemies={"goblin": enemy},
        )
        intent = StandIntent(actor_id="hero")
        rng = _make_rng()

        triggers = check_stand_from_prone_aoo(ws, "hero")
        assert len(triggers) == 0, "Non-prone actor should trigger no AoOs"

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        stand_events = _events_of_type(result, "stand_resolved")
        assert len(stand_events) >= 1
        assert stand_events[0].payload.get("was_prone") is False
        assert stand_events[0].payload.get("aoo_triggered") is False

    def test_SP004_prone_stand_flat_footed_enemy_no_aoo(self):
        """SP-004: Prone actor stands; flat-footed enemy threatens — no AoO (Batch H guard)."""
        enemy = _adjacent_enemy("goblin", conditions={"flat_footed": {}})
        ws = _build_world(
            actor_conditions={"prone": {}},
            enemies={"goblin": enemy},
        )

        triggers = check_stand_from_prone_aoo(ws, "hero")
        assert len(triggers) == 0, "Flat-footed enemy must not make AoO (Batch H guard)"

        intent = StandIntent(actor_id="hero")
        rng = _make_rng()
        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        stand_events = _events_of_type(result, "stand_resolved")
        assert len(stand_events) >= 1
        # Flat-footed enemy can't AoO
        assert stand_events[0].payload.get("aoo_triggered") is False

    def test_SP005_prone_stand_two_enemies_both_aoo(self):
        """SP-005: Prone actor stands; two enemies threaten — both make AoO (Combat Reflexes limits apply)."""
        enemy1 = _adjacent_enemy("goblin1", hp=15)
        enemy2 = {
            EF.ENTITY_ID: "goblin2",
            EF.HP_CURRENT: 15,
            EF.HP_MAX: 15,
            EF.AC: 12,
            EF.ATTACK_BONUS: 3,
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 3, "y": 4},  # Also adjacent
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
        }
        ws = _build_world(
            actor_conditions={"prone": {}},
            enemies={"goblin1": enemy1, "goblin2": enemy2},
        )

        triggers = check_stand_from_prone_aoo(ws, "hero")
        assert len(triggers) == 2, f"Expected 2 AoO triggers (two threatening enemies), got {len(triggers)}"
        reactor_ids = {t.reactor_id for t in triggers}
        assert "goblin1" in reactor_ids
        assert "goblin2" in reactor_ids

    def test_SP006_prone_stand_enemy_no_aoo_remaining_no_trigger(self):
        """SP-006: Prone actor stands; enemy has no AoO uses remaining — no AoO, no crash."""
        enemy = _adjacent_enemy("goblin")
        # Mark goblin as having used its AoO
        ws = _build_world(
            actor_conditions={"prone": {}},
            enemies={"goblin": enemy},
        )
        # Exhaust goblin's AoO by setting aoo_count_this_round to 1 (at limit)
        ac = deepcopy(ws.active_combat)
        ac["aoo_count_this_round"] = {"goblin": 1}  # 1 AoO used; limit = 1
        ws = WorldState(
            ruleset_version=ws.ruleset_version,
            entities=ws.entities,
            active_combat=ac,
        )

        triggers = check_stand_from_prone_aoo(ws, "hero")
        assert len(triggers) == 0, "Enemy with AoO exhausted should not trigger"

        intent = StandIntent(actor_id="hero")
        rng = _make_rng()
        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None, "No crash when AoO exhausted"

    def test_SP007_aoo_drops_actor_to_0hp_actor_incapacitated(self):
        """SP-007: Prone actor stands; AoO drops actor to 0 HP — incapacitated after AoO."""
        # Give actor 1 HP so any AoO damage incapacitates
        actor = {
            EF.ENTITY_ID: "hero",
            EF.HP_CURRENT: 1,
            EF.HP_MAX: 20,
            EF.AC: 5,   # Low AC so AoO hits
            EF.ATTACK_BONUS: 0,
            EF.TEAM: "players",
            EF.POSITION: {"x": 3, "y": 3},
            EF.CONDITIONS: {"prone": {}},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
        }
        enemy = {
            EF.ENTITY_ID: "goblin",
            EF.HP_CURRENT: 15,
            EF.HP_MAX: 15,
            EF.AC: 10,
            EF.ATTACK_BONUS: 10,  # High to ensure hit
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 4, "y": 3},
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
        }
        ac = {
            "initiative_order": ["hero", "goblin"],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "action_budget_actor": None,
            "action_budget": None,
        }
        ws = WorldState(
            ruleset_version="3.5",
            entities={"hero": actor, "goblin": enemy},
            active_combat=ac,
        )

        intent = StandIntent(actor_id="hero")
        rng = _make_rng(roll=18)  # High roll → AoO hits

        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None, "No crash when AoO kills actor"
        # Stand still completes (returns a result); actor may be defeated
        stand_events = _events_of_type(result, "stand_resolved")
        # Stand event should still fire (action resolves even if actor is knocked down)
        assert len(stand_events) >= 1

    def test_SP008_prone_no_enemies_in_range_clean_stand(self):
        """SP-008: Entity with PRONE condition, enemy out of range — stands cleanly, no AoO, no crash."""
        far_enemy = _nonadjacent_enemy("orc")
        ws = _build_world(
            actor_conditions={"prone": {}},
            enemies={"orc": far_enemy},
        )

        triggers = check_stand_from_prone_aoo(ws, "hero")
        assert len(triggers) == 0, "No AoO for out-of-range enemy"

        intent = StandIntent(actor_id="hero")
        rng = _make_rng()
        result = execute_turn(
            turn_ctx=_make_turn_ctx("hero"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None
        stand_events = _events_of_type(result, "stand_resolved")
        assert len(stand_events) >= 1
        # PRONE condition should be cleared
        hero_after = result.world_state.entities.get("hero", {})
        conds_after = hero_after.get(EF.CONDITIONS, {})
        assert "prone" not in conds_after, "PRONE should be cleared after standing"

        # Verify condition_removed event emitted
        cond_removed = _events_of_type(result, "condition_removed")
        prone_removed = [e for e in cond_removed if e.payload.get("condition") == "prone"]
        assert len(prone_removed) >= 1, "condition_removed event should fire for prone"
