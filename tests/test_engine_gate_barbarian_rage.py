"""ENGINE-BARBARIAN-RAGE Gate -- Barbarian Rage runtime (10 tests).

Gate: ENGINE-BARBARIAN-RAGE
Tests: BR-01 through BR-10
WO: WO-ENGINE-BARBARIAN-RAGE-001
"""

import pytest
from copy import deepcopy
from typing import Any, Dict

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.rage_resolver import (
    validate_rage,
    activate_rage,
    end_rage,
    tick_rage,
)


def _barbarian(eid="barbarian", level=1, con_mod=2, str_mod=3, rage_uses=1,
               rage_active=False, fatigued=False, rage_rounds=0):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: str_mod,
        EF.CON_MOD: con_mod,
        EF.DEX_MOD: 1,
        EF.BAB: level,
        EF.CLASS_LEVELS: {"barbarian": level},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.RAGE_USES_REMAINING: rage_uses,
        EF.RAGE_ACTIVE: rage_active,
        EF.RAGE_ROUNDS_REMAINING: rage_rounds,
        EF.FATIGUED: fatigued,
    }


def _fighter(eid="fighter"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"fighter": 3},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.RAGE_USES_REMAINING: 0,
        EF.RAGE_ACTIVE: False,
        EF.FATIGUED: False,
    }


def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
        },
    )


def test_br01_rage_activates():
    """BR-01: activate_rage emits rage_start, sets RAGE_ACTIVE=True, decrements uses."""
    barb = _barbarian(rage_uses=2)
    ws = _world({"barbarian": barb})
    events, ws2 = activate_rage("barbarian", ws, 0, 0.0)
    rage_evts = [e for e in events if e.event_type == "rage_start"]
    assert len(rage_evts) == 1, f"Expected rage_start, got: {[e.event_type for e in events]}"
    actor = ws2.entities["barbarian"]
    assert actor[EF.RAGE_ACTIVE] is True
    assert actor[EF.RAGE_USES_REMAINING] == 1


def test_br02_rage_bonuses_in_temp_mods():
    """BR-02: TEMPORARY_MODIFIERS has rage bonuses and AC penalty after activation."""
    barb = _barbarian(rage_uses=1)
    ws = _world({"barbarian": barb})
    _, ws2 = activate_rage("barbarian", ws, 0, 0.0)
    temp_mods = ws2.entities["barbarian"].get(EF.TEMPORARY_MODIFIERS, {})
    assert temp_mods.get("rage_str_bonus") == 4
    assert temp_mods.get("rage_con_bonus") == 4
    assert temp_mods.get("rage_will_bonus") == 2
    assert temp_mods.get("rage_ac_penalty") == -2


def test_br03_rage_rounds_decrement():
    """BR-03: tick_rage decrements RAGE_ROUNDS_REMAINING by 1 each call."""
    barb = _barbarian(rage_active=True, rage_rounds=3, rage_uses=0)
    ws = _world({"barbarian": barb})
    _, ws2 = tick_rage("barbarian", ws, 0, 0.0)
    rounds = ws2.entities["barbarian"].get(EF.RAGE_ROUNDS_REMAINING, 0)
    assert rounds == 2, f"Expected 2 rounds remaining, got {rounds}"


def test_br04_rage_end_fatigue():
    """BR-04: end_rage emits rage_end, sets FATIGUED=True, adds fatigue penalties."""
    barb = _barbarian(rage_active=True, rage_rounds=1, rage_uses=0)
    barb[EF.TEMPORARY_MODIFIERS] = {
        "rage_str_bonus": 4, "rage_con_bonus": 4,
        "rage_will_bonus": 2, "rage_ac_penalty": -2,
    }
    ws = _world({"barbarian": barb})
    events, ws2 = end_rage("barbarian", ws, 0, 0.0)
    actor = ws2.entities["barbarian"]
    assert actor[EF.RAGE_ACTIVE] is False
    assert actor[EF.FATIGUED] is True
    temp_mods = actor.get(EF.TEMPORARY_MODIFIERS, {})
    assert "rage_str_bonus" not in temp_mods
    assert temp_mods.get("fatigued_str_penalty") == -2
    assert temp_mods.get("fatigued_dex_penalty") == -2
    assert any(e.event_type == "rage_end" for e in events)


def test_br05_cannot_rage_while_raging():
    """BR-05: validate_rage returns already_raging when RAGE_ACTIVE is True."""
    barb = _barbarian(rage_active=True, rage_rounds=3, rage_uses=1)
    ws = _world({"barbarian": barb})
    reason = validate_rage(ws.entities["barbarian"], ws)
    assert reason == "already_raging", f"Got {reason!r}"


def test_br06_cannot_rage_while_fatigued():
    """BR-06: validate_rage returns already_fatigued when FATIGUED is True."""
    barb = _barbarian(fatigued=True, rage_uses=1)
    ws = _world({"barbarian": barb})
    reason = validate_rage(ws.entities["barbarian"], ws)
    assert reason == "already_fatigued", f"Got {reason!r}"


def test_br07_no_rage_uses():
    """BR-07: validate_rage returns no_rage_uses when RAGE_USES_REMAINING is 0."""
    barb = _barbarian(rage_uses=0)
    ws = _world({"barbarian": barb})
    reason = validate_rage(ws.entities["barbarian"], ws)
    assert reason == "no_rage_uses", f"Got {reason!r}"


def test_br08_not_a_barbarian():
    """BR-08: validate_rage returns not_a_barbarian for non-Barbarian entity."""
    fighter = _fighter()
    fighter[EF.RAGE_USES_REMAINING] = 1
    ws = _world({"fighter": fighter})
    reason = validate_rage(ws.entities["fighter"], ws)
    assert reason == "not_a_barbarian", f"Got {reason!r}"


def test_br09_rage_duration_con_mod():
    """BR-09: RAGE_ROUNDS_REMAINING = 3 + base CON modifier at activation."""
    barb = _barbarian(con_mod=3, rage_uses=1)
    ws = _world({"barbarian": barb})
    _, ws2 = activate_rage("barbarian", ws, 0, 0.0)
    rounds = ws2.entities["barbarian"].get(EF.RAGE_ROUNDS_REMAINING, 0)
    assert rounds == 6, f"Expected 6 (3+3), got {rounds}"

    barb2 = _barbarian(eid="barb2", con_mod=-5, rage_uses=1)
    ws3 = _world({"barb2": barb2})
    _, ws4 = activate_rage("barb2", ws3, 0, 0.0)
    rounds2 = ws4.entities["barb2"].get(EF.RAGE_ROUNDS_REMAINING, 0)
    assert rounds2 == 1, f"Expected min 1 round, got {rounds2}"


def test_br10_determinism():
    """BR-10: 10 replays of tick_rage produce identical results."""
    barb = _barbarian(rage_active=True, rage_rounds=3, rage_uses=0)
    ws = _world({"barbarian": barb})

    results = []
    for _ in range(10):
        ws_copy = deepcopy(ws)
        evts, ws2 = tick_rage("barbarian", ws_copy, 0, 0.0)
        results.append((
            [e.event_type for e in evts],
            ws2.entities["barbarian"].get(EF.RAGE_ROUNDS_REMAINING),
            ws2.entities["barbarian"].get(EF.RAGE_ACTIVE),
        ))

    first = results[0]
    for i, r in enumerate(results[1:], start=1):
        assert r == first, f"Replay {i} differs: {r} vs {first}"
