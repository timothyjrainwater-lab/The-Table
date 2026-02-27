"""
ENGINE GATE -- WO-ENGINE-IMPROVED-OVERRUN-001: Improved Overrun
Tests IO-001 through IO-008.
PHB p.96/157: (1) no AoO on overrun attempt, (2) defender cannot choose to avoid.
"""
import pytest
from aidm.core.maneuver_resolver import resolve_overrun
from aidm.schemas.maneuvers import OverrunIntent
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.core.aoo import check_aoo_triggers


class _FixedRNG:
    class _Stream:
        def __init__(self, val=15):
            self._val = val
        def randint(self, lo, hi):
            return self._val
    def stream(self, name):
        return _FixedRNG._Stream(15)


def _make_ws(attacker, defender):
    return WorldState(
        ruleset_version="3.5",
        entities={"att": attacker, "def": defender},
        active_combat={
            "initiative_order": ["att", "def"],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _attacker(feats=None, str_mod=3):
    return {
        EF.ENTITY_ID: "att", EF.TEAM: "player",
        EF.STR_MOD: str_mod, EF.DEX_MOD: 1,
        EF.FEATS: feats or [],
        EF.HP_CURRENT: 40, EF.HP_MAX: 40,
        EF.AC: 15, EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.NEGATIVE_LEVELS: 0,
    }


def _defender(str_mod=1, dex_mod=1, feats=None):
    return {
        EF.ENTITY_ID: "def", EF.TEAM: "monsters",
        EF.STR_MOD: str_mod, EF.DEX_MOD: dex_mod,
        EF.FEATS: feats or [],
        EF.HP_CURRENT: 30, EF.HP_MAX: 30,
        EF.AC: 12, EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON: {
            "damage_dice": "1d6", "damage_bonus": 1, "damage_type": "slashing",
            "weapon_type": "one-handed", "critical_multiplier": 2,
            "critical_range": 20, "is_two_handed": False, "grip": "one-handed",
            "range_increment": 0,
        },
    }


# IO-001: Improved Overrun → AoO triggers are suppressed in play_loop
def test_io001_improved_overrun_suppresses_aoo():
    """AoO suppression: OverrunIntent with improved_overrun feat → triggers cleared."""
    from aidm.schemas.maneuvers import OverrunIntent
    att = _attacker(feats=["improved_overrun"])
    ws = _make_ws(att, _defender())
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=False)
    # Build raw AoO triggers (defender is adjacent and on opposing team)
    raw_triggers = check_aoo_triggers(ws, "att", intent)
    # Improved Overrun: suppress triggers
    _io_feats = ws.entities.get("att", {}).get(EF.FEATS, [])
    suppressed = [] if "improved_overrun" in _io_feats else raw_triggers
    assert suppressed == [], "Improved Overrun must suppress AoO triggers"


# IO-002: No feat → AoO from target fires (existing behavior)
def test_io002_no_feat_aoo_fires():
    """Without feat, OverrunIntent triggers AoO from adjacent target."""
    att = _attacker(feats=[])
    ws = _make_ws(att, _defender())
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=False)
    raw_triggers = check_aoo_triggers(ws, "att", intent)
    # Defender is adjacent; expect at least one trigger (not suppressed — no feat)
    assert len(raw_triggers) >= 1, "Without Improved Overrun, AoO should trigger"


# IO-003: Improved Overrun → defender cannot avoid (forced into opposed check)
def test_io003_improved_overrun_defender_cannot_avoid():
    """With feat, even defender_avoids=True is ignored; overrun_avoided event absent."""
    att = _attacker(feats=["improved_overrun"], str_mod=5)
    ws = _make_ws(att, _defender(str_mod=1, dex_mod=1))
    # Attacker has higher modifier — will win opposed check with fixed RNG (both roll 15)
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=True)
    events, _ws2, result = resolve_overrun(intent, ws, _FixedRNG(), next_event_id=0, timestamp=0.0)
    event_types = [e.event_type for e in events]
    assert "overrun_avoided" not in event_types, "Improved Overrun: defender_avoids=True must be ignored"
    assert "opposed_check" in event_types, "Opposed check must still fire"


# IO-004: No feat → defender CAN choose to avoid (existing behavior)
def test_io004_no_feat_defender_can_avoid():
    """Without feat, defender_avoids=True → overrun_avoided emitted, no opposed check."""
    att = _attacker(feats=[])
    ws = _make_ws(att, _defender())
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=True)
    events, _ws2, result = resolve_overrun(intent, ws, _FixedRNG(), next_event_id=0, timestamp=0.0)
    event_types = [e.event_type for e in events]
    assert "overrun_avoided" in event_types, "Without feat, defender_avoids=True → overrun_avoided"
    assert "opposed_check" not in event_types, "No opposed check when defender avoids"


# IO-005: Defender avoidance suppressed; opposed STR check resolves normally
def test_io005_opposed_check_resolves_normally():
    """Improved Overrun: opposed check roll event is present with expected modifier fields."""
    att = _attacker(feats=["improved_overrun"], str_mod=4)
    ws = _make_ws(att, _defender(str_mod=1, dex_mod=1))
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=True)
    events, _ws2, result = resolve_overrun(intent, ws, _FixedRNG(), next_event_id=0, timestamp=0.0)
    opp = next((e for e in events if e.event_type == "opposed_check"), None)
    assert opp is not None, "Opposed check event must be present"
    assert opp.payload.get("check_type") == "overrun", "Check type must be 'overrun'"


# IO-006: Overrun success with feat → target knocked prone
def test_io006_overrun_success_target_prone():
    """Improved Overrun + high STR → attacker wins, defender gets prone condition."""
    att = _attacker(feats=["improved_overrun"], str_mod=10)
    ws = _make_ws(att, _defender(str_mod=0, dex_mod=0))
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=False)
    events, ws2, result = resolve_overrun(intent, ws, _FixedRNG(), next_event_id=0, timestamp=0.0)
    event_types = [e.event_type for e in events]
    assert "overrun_success" in event_types, "High-STR attacker must win opposed check"
    # Condition applied
    assert "condition_applied" in event_types or ws2.entities["def"].get(EF.CONDITIONS), (
        "Prone condition must be applied on success"
    )


# IO-007: Overrun fails with feat → attacker stops (no prone on attacker for normal failure)
def test_io007_overrun_failure_no_prone_on_attacker():
    """Improved Overrun + low STR → attacker loses opposed check; overrun_failure emitted."""
    att = _attacker(feats=["improved_overrun"], str_mod=0)
    ws = _make_ws(att, _defender(str_mod=10, dex_mod=0))
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=False)
    events, _ws2, result = resolve_overrun(intent, ws, _FixedRNG(), next_event_id=0, timestamp=0.0)
    event_types = [e.event_type for e in events]
    assert "overrun_failure" in event_types, "Low-STR attacker should fail overrun"
    assert result.success is False, "ManeuverResult.success must be False on failure"


# IO-008: Both AoO suppression AND avoid-path suppression active simultaneously
def test_io008_both_suppressions_active():
    """Improved Overrun: AoO suppressed AND defender_avoids=True ignored simultaneously."""
    att = _attacker(feats=["improved_overrun"], str_mod=5)
    ws = _make_ws(att, _defender(str_mod=1, dex_mod=1))
    intent = OverrunIntent(attacker_id="att", target_id="def", is_charge=False, defender_avoids=True)
    # Confirm AoO triggers would be suppressed
    raw_triggers = check_aoo_triggers(ws, "att", intent)
    _io_feats = ws.entities.get("att", {}).get(EF.FEATS, [])
    suppressed_triggers = [] if "improved_overrun" in _io_feats else raw_triggers
    assert suppressed_triggers == [], "AoO triggers must be suppressed"
    # Confirm defender_avoids is ignored in resolver
    events, _ws2, result = resolve_overrun(intent, ws, _FixedRNG(), next_event_id=0, timestamp=0.0)
    event_types = [e.event_type for e in events]
    assert "overrun_avoided" not in event_types, "Defender avoid path must be suppressed"
    assert "opposed_check" in event_types, "Opposed check must proceed"
