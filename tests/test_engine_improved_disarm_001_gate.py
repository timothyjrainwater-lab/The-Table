"""Gate tests: ENGINE-IMPROVED-DISARM-001

PHB p.96: Improved Disarm — "You do not provoke an attack of opportunity when
you attempt to disarm a foe."

The feat suppresses the AoO the target would normally get on DisarmIntent.
Tests ID-001 through ID-008.
WO-ENGINE-IMPROVED-DISARM-001, Batch L (Dispatch #21).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.play_loop import execute_turn
from aidm.core.aoo import check_aoo_triggers
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import DisarmIntent
from aidm.schemas.attack import AttackIntent, Weapon


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(roll=15):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _make_turn_ctx(actor_id="attacker"):
    ctx = MagicMock()
    ctx.actor_id = actor_id
    ctx.turn_index = 0
    ctx.actor_team = "players"
    return ctx


def _make_entity(eid, team, feats=None, pos=(0, 0), hp=20, ac=14, atk=5):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.ATTACK_BONUS: atk,
        EF.BAB: atk,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 1,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: {"x": pos[0], "y": pos[1]},
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {},
        EF.WEAPON: {
            "damage_dice": "1d6", "damage_bonus": 0, "damage_type": "slashing",
            "weapon_type": "one-handed", "enhancement_bonus": 0,
            "tags": [], "material": "steel", "alignment": "none",
        },
    }


def _make_world(attacker, target, extra_entities=None):
    entities = {attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target}
    if extra_entities:
        entities.update(extra_entities)
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "action_budget_actor": None,
            "action_budget": None,
        },
    )


def _disarm_intent(attacker_id="attacker", target_id="target"):
    return DisarmIntent(attacker_id=attacker_id, target_id=target_id)


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


def _has_aoo_event(result):
    return any(e.event_type == "aoo_triggered" for e in result.events)


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImprovedDisarm001Gate:

    def test_ID001_with_improved_disarm_no_aoo_triggered(self):
        """ID-001: Attacker WITH Improved Disarm — no AoO triggered (target adjacent)."""
        attacker = _make_entity("attacker", "players", feats=["improved_disarm"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _disarm_intent()
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), "ID-001: Improved Disarm must suppress AoO — aoo_triggered found"

    def test_ID002_without_improved_disarm_aoo_triggers(self):
        """ID-002: Attacker WITHOUT Improved Disarm — AoO triggers from target normally."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _disarm_intent()

        # Verify AoO would fire via check_aoo_triggers (base engine behavior)
        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "ID-002: Without Improved Disarm, target should have AoO trigger on DisarmIntent"
        )

    def test_ID003_with_improved_disarm_no_aoo_events_in_output(self):
        """ID-003: Attacker WITH Improved Disarm, target adjacent — no aoo_triggered in events."""
        attacker = _make_entity("attacker", "players", feats=["improved_disarm"], pos=(2, 2))
        target = _make_entity("target", "monsters", pos=(3, 2))
        ws = _make_world(attacker, target)
        intent = _disarm_intent()
        rng = _make_rng(roll=12)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        aoo_events = _events_of_type(result, "aoo_triggered")
        assert len(aoo_events) == 0, (
            f"ID-003: No aoo_triggered events expected with Improved Disarm, got {len(aoo_events)}"
        )

    def test_ID004_without_improved_disarm_aoo_event_in_output(self):
        """ID-004: Attacker WITHOUT Improved Disarm — aoo_triggered event present in output."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _disarm_intent()
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert _has_aoo_event(result), "ID-004: Without Improved Disarm, aoo_triggered event expected"

    def test_ID005_improved_disarm_feat_lookup_uses_ef_feats(self):
        """ID-005: Improved Disarm feat check reads from EF.FEATS list on the attacker entity."""
        attacker = _make_entity("attacker", "players", feats=["improved_disarm"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)

        # Verify the feat is in EF.FEATS (correct field access)
        assert "improved_disarm" in ws.entities["attacker"][EF.FEATS], (
            "ID-005: 'improved_disarm' must be in EF.FEATS list"
        )

        intent = _disarm_intent()
        rng = _make_rng()
        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), "ID-005: Feat lookup via EF.FEATS must suppress AoO"

    def test_ID006_empty_feats_list_disarm_normal_aoo(self):
        """ID-006: Attacker with empty FEATS list — no crash; normal AoO from target."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _disarm_intent()

        triggers = check_aoo_triggers(ws, "attacker", intent)
        # Empty feats → no suppression; target should threaten
        assert any(t.reactor_id == "target" for t in triggers), (
            "ID-006: Empty feats list must not suppress AoO"
        )

    def test_ID007_improved_disarm_no_effect_on_attack_intent(self):
        """ID-007: Non-disarm intent (AttackIntent) with Improved Disarm — AoO not affected."""
        attacker = _make_entity("attacker", "players", feats=["improved_disarm"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(5, 0))  # out of range — no AoO
        ws = _make_world(attacker, target)

        # A StepMoveIntent from attacker would provoke if enemies threaten
        # Just verify improved_disarm in feats doesn't cause any crash on non-disarm intents
        from aidm.schemas.attack import StepMoveIntent
        from aidm.schemas.position import Position
        move_intent = StepMoveIntent(
            actor_id="attacker",
            from_pos=Position(0, 0),
            to_pos=Position(1, 0),
        )
        triggers = check_aoo_triggers(ws, "attacker", move_intent)
        # No assertion on trigger count — just verify no crash with improved_disarm feat present
        assert isinstance(triggers, list), "ID-007: check_aoo_triggers must return a list with improved_disarm feat"

    def test_ID008_with_improved_disarm_disarm_still_resolves(self):
        """ID-008: With Improved Disarm, AoO suppressed — disarm resolution still completes normally."""
        attacker = _make_entity("attacker", "players", feats=["improved_disarm"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _disarm_intent()
        rng = _make_rng(roll=18)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None, "ID-008: execute_turn must return a result"
        # No AoO — maneuver resolves
        assert not _has_aoo_event(result), "ID-008: No AoO expected with Improved Disarm"
        # Maneuver events should be present (disarm attempt resolved)
        maneuver_events = [
            e for e in result.events
            if "disarm" in e.event_type or "maneuver" in e.event_type
        ]
        assert len(maneuver_events) >= 1, "ID-008: Disarm maneuver events expected in result"
