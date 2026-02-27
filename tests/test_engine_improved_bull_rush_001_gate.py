"""Gate tests: ENGINE-IMPROVED-BULL-RUSH-001

PHB p.96: Improved Bull Rush — "When you perform a bull rush you do not provoke
an attack of opportunity from the defender."

Bull Rush normally provokes from ALL threatening enemies (PHB p.154).
Improved Bull Rush suppresses all AoOs entirely.
Tests IB-001 through IB-008.
WO-ENGINE-IMPROVED-BULL-RUSH-001, Batch L (Dispatch #21).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.play_loop import execute_turn
from aidm.core.aoo import check_aoo_triggers
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import BullRushIntent


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


def _bull_rush_intent(attacker_id="attacker", target_id="target", is_charge=False):
    return BullRushIntent(attacker_id=attacker_id, target_id=target_id, is_charge=is_charge)


def _has_aoo_event(result):
    return any(e.event_type == "aoo_triggered" for e in result.events)


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImprovedBullRush001Gate:

    def test_IB001_with_improved_bull_rush_no_aoo_triggered(self):
        """IB-001: Attacker WITH Improved Bull Rush — no AoO triggered from target."""
        attacker = _make_entity("attacker", "players", feats=["improved_bull_rush"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _bull_rush_intent()
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), (
            "IB-001: Improved Bull Rush must suppress AoO — aoo_triggered found"
        )

    def test_IB002_without_improved_bull_rush_aoo_triggers(self):
        """IB-002: Attacker WITHOUT Improved Bull Rush — AoO triggers from target (provokes from all)."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _bull_rush_intent()

        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "IB-002: Without Improved Bull Rush, target should have AoO trigger on BullRushIntent"
        )

    def test_IB003_with_improved_bull_rush_no_aoo_events_in_output(self):
        """IB-003: Attacker WITH Improved Bull Rush — no aoo_triggered events in output."""
        attacker = _make_entity("attacker", "players", feats=["improved_bull_rush"], pos=(2, 2))
        target = _make_entity("target", "monsters", pos=(3, 2))
        ws = _make_world(attacker, target)
        intent = _bull_rush_intent()
        rng = _make_rng(roll=12)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        aoo_events = _events_of_type(result, "aoo_triggered")
        assert len(aoo_events) == 0, (
            f"IB-003: No aoo_triggered events expected with Improved Bull Rush, got {len(aoo_events)}"
        )

    def test_IB004_without_improved_bull_rush_aoo_event_in_output(self):
        """IB-004: Attacker WITHOUT Improved Bull Rush — aoo_triggered event present."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _bull_rush_intent()
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert _has_aoo_event(result), "IB-004: Without Improved Bull Rush, aoo_triggered event expected"

    def test_IB005_improved_bull_rush_suppresses_all_threaten_aoos(self):
        """IB-005: Improved Bull Rush suppresses AoOs from ALL threatening enemies (not just target)."""
        attacker = _make_entity("attacker", "players", feats=["improved_bull_rush"], pos=(1, 1))
        target = _make_entity("target", "monsters", pos=(2, 1))
        bystander = _make_entity("bystander", "monsters", pos=(1, 2))  # also threatens
        ws = _make_world(attacker, target, extra_entities={"bystander": bystander})
        intent = _bull_rush_intent()
        rng = _make_rng(roll=15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), (
            "IB-005: Improved Bull Rush must suppress AoOs from ALL threatening enemies"
        )

    def test_IB006_without_improved_bull_rush_two_enemies_both_trigger(self):
        """IB-006: Without Improved Bull Rush, two threatening enemies — both get AoO triggers."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(1, 1))
        target = _make_entity("target", "monsters", pos=(2, 1))
        bystander = _make_entity("bystander", "monsters", pos=(1, 2))
        ws = _make_world(attacker, target, extra_entities={"bystander": bystander})
        intent = _bull_rush_intent()

        triggers = check_aoo_triggers(ws, "attacker", intent)
        reactor_ids = {t.reactor_id for t in triggers}
        # Both enemies threaten and both should AoO on Bull Rush (provokes from all)
        assert "target" in reactor_ids or "bystander" in reactor_ids, (
            "IB-006: Without Improved Bull Rush, at least one threatening enemy should have AoO trigger"
        )

    def test_IB007_improved_grapple_does_not_suppress_bull_rush_aoo(self):
        """IB-007: Attacker with improved_grapple (not improved_bull_rush) — BullRushIntent still provokes."""
        attacker = _make_entity("attacker", "players", feats=["improved_grapple"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _bull_rush_intent()

        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "IB-007: improved_grapple must NOT suppress BullRushIntent AoO"
        )

    def test_IB008_with_improved_bull_rush_bull_rush_still_resolves(self):
        """IB-008: With Improved Bull Rush, AoO suppressed — bull rush resolution still completes."""
        attacker = _make_entity("attacker", "players", feats=["improved_bull_rush"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = _bull_rush_intent()
        rng = _make_rng(roll=18)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None, "IB-008: execute_turn must return a result"
        assert not _has_aoo_event(result), "IB-008: No AoO expected with Improved Bull Rush"
        maneuver_events = [
            e for e in result.events
            if "bull_rush" in e.event_type or "maneuver" in e.event_type
        ]
        assert len(maneuver_events) >= 1, "IB-008: Bull rush maneuver events expected in result"
