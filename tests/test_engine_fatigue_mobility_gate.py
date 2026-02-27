"""Gate tests: WO-ENGINE-FATIGUE-MOBILITY-001

ENGINE-FATIGUE-MOBILITY: Fatigued/exhausted entities cannot charge or run.
PHB p.308: "A fatigued character can neither run nor charge."

FMOB-001 – FMOB-008 (8 tests)
"""
import unittest.mock as mock
from copy import deepcopy

import pytest

from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.rage_resolver import activate_rage, end_rage
from aidm.core.state import WorldState
from aidm.schemas.intents import ChargeIntent, RunIntent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEAPON_LONGSWORD = {
    "damage_dice": "1d8",
    "damage_bonus": 0,
    "critical_range": 19,
    "critical_multiplier": 2,
    "grip": "one-handed",
    "damage_type": "slashing",
    "weapon_type": "one-handed",
    "range_increment": 0,
    "is_two_handed": False,
}


def _entity(
    eid, team="player", hp=30, hp_max=30, ac=10, attack_bonus=5,
    feats=None, fatigued=False, conditions=None, pos=None, str_mod=2,
):
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: ac,
        EF.ATTACK_BONUS: attack_bonus,
        EF.BAB: attack_bonus,
        "bab": attack_bonus,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: feats if feats is not None else [],
        EF.POSITION: pos if pos is not None else {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FATIGUED: fatigued,
        EF.TEMPORARY_MODIFIERS: {},
        EF.BASE_SPEED: 30,
        EF.WEAPON: WEAPON_LONGSWORD,
    }
    return e


def _world(att, tgt):
    return WorldState(
        ruleset_version="3.5e",
        entities={att[EF.ENTITY_ID]: att, tgt[EF.ENTITY_ID]: tgt},
        active_combat={"initiative_order": [att[EF.ENTITY_ID], tgt[EF.ENTITY_ID]]},
    )


def _ctx(actor_id="hero"):
    return TurnContext(turn_index=0, actor_id=actor_id, actor_team="party")


def _rng(val=15):
    stream = mock.MagicMock()
    stream.randint = mock.MagicMock(return_value=val)
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _get_ev(events, etype):
    return [e for e in events if e.event_type == etype]


# ---------------------------------------------------------------------------
# FMOB-001: Fatigued entity attempts ChargeIntent → blocked
# ---------------------------------------------------------------------------

def test_fmob_001_fatigued_charge_blocked():
    """FMOB-001: Fatigued entity attempts ChargeIntent → intent rejected, event emitted."""
    att = _entity("hero", fatigued=True, pos={"x": 0, "y": 0})
    tgt = _entity("goblin", team="monsters", pos={"x": 2, "y": 0})
    ws = _world(att, tgt)
    intent = ChargeIntent(attacker_id="hero", target_id="goblin", weapon=WEAPON_LONGSWORD, path_clear=True)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=_rng())
    blocked = _get_ev(result.events, "charge_blocked_fatigued")
    assert len(blocked) >= 1
    assert blocked[0].payload["reason"] == "fatigued"
    assert result.narration == "charge_blocked_fatigued"


# ---------------------------------------------------------------------------
# FMOB-002: Non-fatigued entity attempts ChargeIntent → allowed (control)
# ---------------------------------------------------------------------------

def test_fmob_002_non_fatigued_charge_allowed():
    """FMOB-002: Non-fatigued entity attempts ChargeIntent → charge proceeds normally."""
    att = _entity("hero", fatigued=False, pos={"x": 0, "y": 0})
    tgt = _entity("goblin", team="monsters", pos={"x": 2, "y": 0})
    ws = _world(att, tgt)
    intent = ChargeIntent(attacker_id="hero", target_id="goblin", weapon=WEAPON_LONGSWORD, path_clear=True)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=_rng())
    blocked = _get_ev(result.events, "charge_blocked_fatigued")
    assert len(blocked) == 0
    assert result.narration != "charge_blocked_fatigued"


# ---------------------------------------------------------------------------
# FMOB-003: Fatigued entity attempts RunIntent → blocked
# ---------------------------------------------------------------------------

def test_fmob_003_fatigued_run_blocked():
    """FMOB-003: Fatigued entity attempts RunIntent → intent rejected, event emitted."""
    att = _entity("hero", fatigued=True)
    tgt = _entity("goblin", team="monsters", pos={"x": 5, "y": 0})
    ws = _world(att, tgt)
    intent = RunIntent(actor_id="hero")
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=_rng())
    blocked = _get_ev(result.events, "run_blocked_fatigued")
    assert len(blocked) >= 1
    assert blocked[0].payload["reason"] == "fatigued"
    assert result.narration == "run_blocked_fatigued"


# ---------------------------------------------------------------------------
# FMOB-004: Non-fatigued entity attempts RunIntent → allowed (control)
# ---------------------------------------------------------------------------

def test_fmob_004_non_fatigued_run_allowed():
    """FMOB-004: Non-fatigued entity attempts RunIntent → run proceeds normally."""
    att = _entity("hero", fatigued=False)
    tgt = _entity("goblin", team="monsters", pos={"x": 5, "y": 0})
    ws = _world(att, tgt)
    intent = RunIntent(actor_id="hero")
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=_rng())
    blocked = _get_ev(result.events, "run_blocked_fatigued")
    assert len(blocked) == 0
    assert result.narration != "run_blocked_fatigued"


# ---------------------------------------------------------------------------
# FMOB-005: Exhausted entity attempts ChargeIntent → blocked
# ---------------------------------------------------------------------------

def test_fmob_005_exhausted_charge_blocked():
    """FMOB-005: Exhausted entity attempts ChargeIntent → intent rejected."""
    att = _entity("hero", fatigued=False, conditions={"exhausted": {"source": "test"}},
                  pos={"x": 0, "y": 0})
    tgt = _entity("goblin", team="monsters", pos={"x": 2, "y": 0})
    ws = _world(att, tgt)
    intent = ChargeIntent(attacker_id="hero", target_id="goblin", weapon=WEAPON_LONGSWORD, path_clear=True)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=_rng())
    blocked = _get_ev(result.events, "charge_blocked_fatigued")
    assert len(blocked) >= 1
    assert blocked[0].payload["reason"] == "exhausted"


# ---------------------------------------------------------------------------
# FMOB-006: Exhausted entity attempts RunIntent → blocked
# ---------------------------------------------------------------------------

def test_fmob_006_exhausted_run_blocked():
    """FMOB-006: Exhausted entity attempts RunIntent → intent rejected."""
    att = _entity("hero", fatigued=False, conditions={"exhausted": {"source": "test"}})
    tgt = _entity("goblin", team="monsters", pos={"x": 5, "y": 0})
    ws = _world(att, tgt)
    intent = RunIntent(actor_id="hero")
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=_rng())
    blocked = _get_ev(result.events, "run_blocked_fatigued")
    assert len(blocked) >= 1
    assert blocked[0].payload["reason"] == "exhausted"


# ---------------------------------------------------------------------------
# FMOB-007: Integration — rage enter → rage exit → fatigued → charge blocked
# ---------------------------------------------------------------------------

def test_fmob_007_rage_fatigue_integration():
    """FMOB-007: Barbarian rages, exits rage → fatigued → charge blocked."""
    barb = _entity("hero", pos={"x": 0, "y": 0})
    barb[EF.CLASS_LEVELS] = {"barbarian": 5}
    barb[EF.CON_MOD] = 2
    barb[EF.RAGE_ACTIVE] = False
    barb[EF.RAGE_USES_REMAINING] = 2
    barb[EF.RAGE_ROUNDS_REMAINING] = 0
    tgt = _entity("goblin", team="monsters", pos={"x": 2, "y": 0})
    ws = _world(barb, tgt)

    # Enter rage
    _, ws_raged = activate_rage("hero", ws, next_event_id=1, timestamp=1.0)
    # Exit rage → fatigued
    _, ws_fatigued = end_rage("hero", ws_raged, next_event_id=10, timestamp=2.0)
    assert ws_fatigued.entities["hero"][EF.FATIGUED] is True

    # Now attempt charge — should be blocked
    intent = ChargeIntent(attacker_id="hero", target_id="goblin", weapon=WEAPON_LONGSWORD, path_clear=True)
    result = execute_turn(ws_fatigued, _ctx(), combat_intent=intent, rng=_rng())
    blocked = _get_ev(result.events, "charge_blocked_fatigued")
    assert len(blocked) >= 1


# ---------------------------------------------------------------------------
# FMOB-008: After fatigue clears → charge and run re-allowed
# ---------------------------------------------------------------------------

def test_fmob_008_fatigue_cleared_charge_run_allowed():
    """FMOB-008: After fatigue clears, charge and run are re-allowed."""
    att = _entity("hero", fatigued=True, pos={"x": 0, "y": 0})
    tgt = _entity("goblin", team="monsters", pos={"x": 2, "y": 0})
    ws = _world(att, tgt)

    # First confirm charge is blocked while fatigued
    intent_charge = ChargeIntent(attacker_id="hero", target_id="goblin", weapon=WEAPON_LONGSWORD, path_clear=True)
    result1 = execute_turn(ws, _ctx(), combat_intent=intent_charge, rng=_rng())
    assert len(_get_ev(result1.events, "charge_blocked_fatigued")) >= 1

    # Clear fatigue
    entities = deepcopy(ws.entities)
    entities["hero"][EF.FATIGUED] = False
    ws_clear = WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat=ws.active_combat,
    )

    # Charge now succeeds
    result2 = execute_turn(ws_clear, _ctx(), combat_intent=intent_charge, rng=_rng())
    assert len(_get_ev(result2.events, "charge_blocked_fatigued")) == 0

    # Run also succeeds
    intent_run = RunIntent(actor_id="hero")
    result3 = execute_turn(ws_clear, _ctx(), combat_intent=intent_run, rng=_rng())
    assert len(_get_ev(result3.events, "run_blocked_fatigued")) == 0
