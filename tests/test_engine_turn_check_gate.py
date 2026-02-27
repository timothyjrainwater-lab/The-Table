"""ENGINE-TURN-CHECK Gate -- WO-ENGINE-TURN-CHECK-001: Turn check formula fix (6 tests).

Gate: ENGINE-TURN-CHECK
Tests: TURN-001 through TURN-006
WO: WO-ENGINE-TURN-CHECK-001 (Batch U WO2)
Source finding: FINDING-AUDIT-TURN-CHECK-001 (AUDIT-WO-004, HIGH)

PHB p.159: Turning check = 1d20 + CHA_mod only.
Cleric level is NOT part of the check roll.
HP budget (2d6×10) is a separate roll — unchanged.
"""

import unittest.mock as mock

from aidm.core.turn_undead_resolver import apply_turn_undead_events, resolve_turn_undead
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import TurnUndeadIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng_fixed(*rolls):
    """Stateful mock RNG: returns rolls in order from combat stream."""
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [3] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _cleric(eid="cleric1", level=5, cha_mod=2, uses=3, feats=None):
    entity = {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.LEVEL: level,
        EF.CHA_MOD: cha_mod,
        EF.TURN_UNDEAD_USES: uses,
        EF.TURN_UNDEAD_USES_MAX: uses,
        EF.CLASS_LEVELS: {"cleric": level},
        "class_features": {},
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
    }
    return entity


def _undead(eid, hd, hp_max=None):
    hp_max = hp_max if hp_max is not None else hd * 5
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp_max,
        EF.HP_MAX: hp_max,
        EF.AC: 12,
        EF.HD_COUNT: hd,
        EF.IS_UNDEAD: True,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
    }


def _world(*entities):
    return WorldState(
        ruleset_version="3.5e",
        entities={e[EF.ENTITY_ID]: e for e in entities},
        active_combat={"initiative_order": [e[EF.ENTITY_ID] for e in entities]},
    )


# ---------------------------------------------------------------------------
# TURN-001: Check result is in [1+CHA_mod, 20+CHA_mod], not old 2d6 range
# ---------------------------------------------------------------------------

def test_turn001_check_result_uses_d20():
    """TURN-001: Turn check = d20 + CHA_mod; result is in [1+cha, 20+cha] not [2+cha+lvl, 12+cha+lvl]."""
    cleric = _cleric(level=5, cha_mod=2, uses=3)
    ws = _world(cleric)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=[])
    # d20=10 → expected result = 10+2=12
    # Old formula: 10+5+2=17 (d1=10, d2=0? No — old was 2d6; 10 is outside 1d6 range anyway)
    # Using a d20=10 roll: new result=12, old result would be impossible from 2d6
    rng = _rng_fixed(10, 3, 3)  # turn check d20=10, budget d6s: 3,3

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    tc_ev = next((e for e in events if e.event_type == "turning_check_rolled"), None)
    assert tc_ev is not None, "turning_check_rolled event must be emitted"
    result = tc_ev.payload["roll_result"]
    assert result == 12, f"Expected d20(10)+cha_mod(2)=12, got {result}"
    # Sanity: result is in valid d20+cha range
    cha_mod = 2
    assert 1 + cha_mod <= result <= 20 + cha_mod, (
        f"result {result} outside [1+cha, 20+cha] = [{1+cha_mod}, {20+cha_mod}]"
    )


# ---------------------------------------------------------------------------
# TURN-002: Cleric level NOT included in turn check (formula inspection)
# ---------------------------------------------------------------------------

def test_turn002_check_excludes_cleric_level():
    """TURN-002: High cleric level does NOT inflate the turning check roll.

    Cleric L10, CHA_mod=0: d20=5 → expected roll_result=5, not 5+10=15.
    """
    cleric = _cleric(level=10, cha_mod=0, uses=3)
    ws = _world(cleric)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=[])
    rng = _rng_fixed(5, 3, 3)  # d20=5, budget dice 3+3

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    tc_ev = next((e for e in events if e.event_type == "turning_check_rolled"), None)
    assert tc_ev is not None
    assert tc_ev.payload["roll_result"] == 5, (
        f"Expected d20(5)+cha_mod(0)=5 (no cleric_level), got {tc_ev.payload['roll_result']}"
    )
    # Explicitly verify it is NOT 5+10=15
    assert tc_ev.payload["roll_result"] != 15, (
        "roll_result must not include cleric_level (old 2d6+level formula)"
    )


# ---------------------------------------------------------------------------
# TURN-003: HP budget (2d6×10) is UNCHANGED — regression guard
# ---------------------------------------------------------------------------

def test_turn003_hp_budget_formula_unchanged():
    """TURN-003: HP budget roll (2d6×10) is independent of the turn check fix."""
    cleric = _cleric(level=5, cha_mod=2, uses=3)
    ws = _world(cleric)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=[])
    # turn check d20=10 → check=12; budget d6s: 4+2 → (4+2)*10=60
    rng = _rng_fixed(10, 4, 2)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    tc_ev = next((e for e in events if e.event_type == "turning_check_rolled"), None)
    assert tc_ev is not None
    assert tc_ev.payload["hp_budget"] == 60, (
        f"Expected hp_budget=(4+2)*10=60, got {tc_ev.payload['hp_budget']}"
    )


# ---------------------------------------------------------------------------
# TURN-004: Correct Table 8-1 lookup with fixed check formula
# ---------------------------------------------------------------------------

def test_turn004_table_lookup_cleric_l5_cha2():
    """TURN-004: Cleric L5 CHA+2, d20=15 → check=17; HD-5 undead turned (not destroyed: 5 > 5-4=1)."""
    cleric = _cleric(level=5, cha_mod=2, uses=3)
    hd5 = _undead("ghoul", hd=5, hp_max=25)
    ws = _world(cleric, hd5)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["ghoul"])
    # d20=15 → check=17; budget d6s: 3+3 → 60. HD 5 ≤ 17, fits budget → turned
    rng = _rng_fixed(15, 3, 3)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    tc_ev = next((e for e in events if e.event_type == "turning_check_rolled"), None)
    assert tc_ev is not None
    assert tc_ev.payload["roll_result"] == 17  # 15+2

    turned_ev = next((e for e in events if e.event_type == "undead_turned"), None)
    assert turned_ev is not None, (
        f"HD-5 undead should be turned (check=17 ≥ hd=5); events: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# TURN-005: Improved Turning still applies correctly after check formula fix
# ---------------------------------------------------------------------------

def test_turn005_improved_turning_regression():
    """TURN-005: Improved Turning — effective_level+=1 before table lookup — still correct post-fix."""
    # Cleric L3 + Improved Turning → effective_level=4
    # d20=10 → check=10+0=10; HD-4 undead: ≤ 4-4=0? NO; ≤ check 10? YES → turned
    cleric = _cleric(level=3, cha_mod=0, uses=3, feats=["improved_turning"])
    hd4 = _undead("wraith", hd=4, hp_max=20)
    ws = _world(cleric, hd4)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["wraith"])
    rng = _rng_fixed(10, 3, 3)  # d20=10 → check=10, budget=60

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    itn_ev = next((e for e in events if e.event_type == "improved_turning_active"), None)
    assert itn_ev is not None, "improved_turning_active must fire"
    assert itn_ev.payload["effective_level"] == 4  # 3+1

    turned_ev = next((e for e in events if e.event_type == "undead_turned"), None)
    assert turned_ev is not None, (
        f"HD-4 undead should be turned (effective_level=4, check=10); events: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# TURN-006: Uses decremented even when check produces no affected undead
# ---------------------------------------------------------------------------

def test_turn006_uses_decremented_regardless_of_check_outcome():
    """TURN-006: Turn uses always decremented — not conditional on check outcome.

    d20=1 → check=1; HD-5 undead → unaffected (5 > 1). Uses still spent.
    """
    cleric = _cleric(level=5, cha_mod=0, uses=3)
    hd5 = _undead("wight", hd=5, hp_max=25)
    ws = _world(cleric, hd5)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["wight"])
    rng = _rng_fixed(1, 3, 3)  # d20=1 → check=1; HD 5 > 1 → unaffected

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    # No undead affected
    assert not any(
        e.event_type in ("undead_turned", "undead_destroyed") for e in events
    ), "No undead should be affected when check=1 vs HD=5"

    # Uses still spent
    use_ev = next((e for e in events if e.event_type == "turn_undead_use_spent"), None)
    assert use_ev is not None, "turn_undead_use_spent must fire even with no targets affected"
    assert use_ev.payload["uses_remaining"] == 2, (
        f"Expected uses_remaining=2 (3-1), got {use_ev.payload['uses_remaining']}"
    )
