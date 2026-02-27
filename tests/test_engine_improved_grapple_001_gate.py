"""Gate tests: ENGINE-IMPROVED-GRAPPLE-001

PHB p.96: Improved Grapple — "You do not provoke an attack of opportunity when
you attempt to grapple a foe."

The feat suppresses the AoO the target would normally get on GrappleIntent.
Tests IG-001 through IG-008.
WO-ENGINE-IMPROVED-GRAPPLE-001, Batch L (Dispatch #21).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.play_loop import execute_turn
from aidm.core.aoo import check_aoo_triggers
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import GrappleIntent


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


def _make_world(attacker, target):
    entities = {attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target}
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


def _grapple_intent(attacker_id="attacker", target_id="target"):
    return GrappleIntent(attacker_id=attacker_id, target_id=target_id)


def _has_aoo_event(result):
    return any(e.event_type == "aoo_triggered" for e in result.events)


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImprovedGrapple001Gate:

    def test_IG001_with_improved_grapple_no_aoo_triggered(self):
        """IG-001: Attacker WITH Improved Grapple — no AoO triggered (target adjacent)."""
        attacker = _make_entity("attacker", "players", feats=["improved_grapple"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _grapple_intent()
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), "IG-001: Improved Grapple must suppress AoO — aoo_triggered found"

    def test_IG002_without_improved_grapple_aoo_triggers(self):
        """IG-002: Attacker WITHOUT Improved Grapple — AoO triggers from target normally."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _grapple_intent()

        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "IG-002: Without Improved Grapple, target should have AoO trigger on GrappleIntent"
        )

    def test_IG003_with_improved_grapple_no_aoo_events_in_output(self):
        """IG-003: Attacker WITH Improved Grapple — no aoo_triggered events in output."""
        attacker = _make_entity("attacker", "players", feats=["improved_grapple"], pos=(2, 2))
        target = _make_entity("target", "monsters", pos=(3, 2))
        ws = _make_world(attacker, target)
        intent = _grapple_intent()
        rng = _make_rng(roll=12)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        aoo_events = _events_of_type(result, "aoo_triggered")
        assert len(aoo_events) == 0, (
            f"IG-003: No aoo_triggered events expected with Improved Grapple, got {len(aoo_events)}"
        )

    def test_IG004_without_improved_grapple_aoo_event_in_output(self):
        """IG-004: Attacker WITHOUT Improved Grapple — aoo_triggered event present in output."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _grapple_intent()
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert _has_aoo_event(result), "IG-004: Without Improved Grapple, aoo_triggered event expected"

    def test_IG005_improved_grapple_feat_lookup_uses_ef_feats(self):
        """IG-005: Improved Grapple feat check reads from EF.FEATS list on the attacker."""
        attacker = _make_entity("attacker", "players", feats=["improved_grapple"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)

        assert "improved_grapple" in ws.entities["attacker"][EF.FEATS], (
            "IG-005: 'improved_grapple' must be in EF.FEATS list"
        )

        intent = _grapple_intent()
        rng = _make_rng()
        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), "IG-005: Feat lookup via EF.FEATS must suppress AoO"

    def test_IG006_empty_feats_list_grapple_normal_aoo(self):
        """IG-006: Attacker with empty FEATS list — no crash; normal AoO from target."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _grapple_intent()

        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "IG-006: Empty feats list must not suppress AoO"
        )

    def test_IG007_improved_disarm_does_not_suppress_grapple_aoo(self):
        """IG-007: Attacker with improved_disarm (not improved_grapple) — GrappleIntent still provokes AoO."""
        attacker = _make_entity("attacker", "players", feats=["improved_disarm"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _grapple_intent()

        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "IG-007: improved_disarm must NOT suppress GrappleIntent AoO"
        )

    def test_IG008_with_improved_grapple_grapple_still_resolves(self):
        """IG-008: With Improved Grapple, AoO suppressed — grapple resolution still completes normally."""
        attacker = _make_entity("attacker", "players", feats=["improved_grapple"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _grapple_intent()
        rng = _make_rng(roll=18)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None, "IG-008: execute_turn must return a result"
        assert not _has_aoo_event(result), "IG-008: No AoO expected with Improved Grapple"
        maneuver_events = [
            e for e in result.events
            if "grapple" in e.event_type or "maneuver" in e.event_type
        ]
        assert len(maneuver_events) >= 1, "IG-008: Grapple maneuver events expected in result"
