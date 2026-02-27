"""
ENGINE GATE -- WO-ENGINE-IDC-001: Improved Disarm Counter
Tests IDC-001 through IDC-008.
PHB p.155: Attacker loses disarm by 10+ → defender may attempt counter-disarm.
PHB p.96: Improved Disarm suppresses the counter-disarm attempt.
Margin is computed from totals (not raw d20 rolls).
"""
from unittest.mock import MagicMock

from aidm.core.maneuver_resolver import resolve_disarm
from aidm.schemas.maneuvers import DisarmIntent
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# RNG helpers
# ---------------------------------------------------------------------------

class _SeqRNG:
    """Sequential RNG: returns values from list cycling."""
    def __init__(self, values):
        self._vals = list(values)
        self._idx = 0

    class _Stream:
        def __init__(self, parent):
            self._p = parent
        def randint(self, lo, hi):
            val = self._p._vals[self._p._idx % len(self._p._vals)]
            self._p._idx += 1
            return val

    def stream(self, name):
        return _SeqRNG._Stream(self)


def _rng(val=15):
    """Constant-value RNG: all d20 rolls return val."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=val)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _seq_rng(*values):
    return _SeqRNG(values)


# ---------------------------------------------------------------------------
# Entity / WorldState helpers
# ---------------------------------------------------------------------------

def _entity(eid, feats=None, bab=5, str_mod=2):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "player",
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.FEATS: feats if feats is not None else [],
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30,
        EF.AC: 10,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.SIZE_CATEGORY: "medium",
        EF.STABILITY_BONUS: 0,
        EF.POSITION: {"x": 0, "y": 0},
        EF.WEAPON: {"damage_dice": "1d8", "damage_bonus": 0, "damage_type": "slashing",
                    "weapon_type": "one-handed"},
    }


def _ws(att, tgt):
    return WorldState(
        ruleset_version="3.5",
        entities={att[EF.ENTITY_ID]: att, tgt[EF.ENTITY_ID]: tgt},
        active_combat={
            "initiative_order": [att[EF.ENTITY_ID], tgt[EF.ENTITY_ID]],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _get_ev(events, etype):
    for e in events:
        if e.event_type == etype:
            return e
    return None


# ---------------------------------------------------------------------------
# Modifier reference (medium size → 0, one-handed → 0)
# IDC tests use:
#   HIGH_MOD = BAB(5) + STR(5) = 10   (defender in fail-by-10+ tests)
#   LOW_MOD  = BAB(0) + STR(0) = 0    (attacker in fail-by-10+ tests)
#   EQ_MOD   = BAB(5) + STR(2) = 7    (equal modifiers for tie → fail < 10)
# ---------------------------------------------------------------------------
_LOW_MOD = 0     # att: bab=0, str_mod=0
_HIGH_MOD = 10   # def: bab=5, str_mod=5
_EQ_MOD = 7      # both: bab=5, str_mod=2


# ---------------------------------------------------------------------------
# IDC-001: Disarm succeeds → no counter events at all
# ---------------------------------------------------------------------------
def test_idc001_disarm_success_no_counter():
    """IDC-001: Attacker wins disarm → no disarm_failure, no counter events."""
    # att modifier = 11 (bab=5, str=6), def modifier = 5 (bab=5, str=0)
    # With roll=15: att_total=26, def_total=20 → attacker wins
    att = _entity("att", bab=5, str_mod=6)
    tgt = _entity("tgt", bab=5, str_mod=0)
    ws = _ws(att, tgt)
    events, _, result = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    assert result.success, "IDC-001: disarm should succeed"
    fail_ev = _get_ev(events, "disarm_failure")
    assert fail_ev is None, "IDC-001: no disarm_failure event expected on success"
    counter_ev = _get_ev(events, "counter_disarm_suppressed")
    assert counter_ev is None, "IDC-001: no counter_disarm_suppressed on success"


# ---------------------------------------------------------------------------
# IDC-002: Disarm fails by < 10 → counter-disarm now allowed (PHB p.155)
# Updated by WO-ENGINE-DISARM-FIDELITY-001: any failure allows counter.
# ---------------------------------------------------------------------------
def test_idc002_fail_lt10_counter_allowed():
    """IDC-002: Disarm fails by < 10 → counter_disarm_allowed=True (PHB p.155)."""
    # SeqRNG: att_roll=10, def_roll=15 → att_total=17, def_total=22 → margin=5
    # WO-ENGINE-DISARM-FIDELITY-001: any failure allows counter-disarm
    att = _entity("att", bab=5, str_mod=2)
    tgt = _entity("tgt", bab=5, str_mod=2)
    ws = _ws(att, tgt)
    events, _, result = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _seq_rng(10, 15, 10, 10), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    assert not result.success, "IDC-002: disarm should fail"
    fail_ev = _get_ev(events, "disarm_failure")
    assert fail_ev is not None, "IDC-002: disarm_failure event missing"
    assert fail_ev.payload["counter_disarm_allowed"] is True, (
        f"IDC-002: counter_disarm_allowed should be True per PHB p.155; "
        f"got {fail_ev.payload['counter_disarm_allowed']}")


# ---------------------------------------------------------------------------
# IDC-003: Disarm fails by >= 10, no Improved Disarm → counter opposed_check rolled
# ---------------------------------------------------------------------------
def test_idc003_fail_ge10_counter_rolled():
    """IDC-003: Fails by >= 10 without Improved Disarm → opposed_check with is_counter_disarm."""
    # att modifier=0 (bab=0, str=0), def modifier=10 (bab=5, str=5)
    # Roll=15: att_total=15, def_total=25, margin=10 → counter triggered
    att = _entity("att", feats=[], bab=0, str_mod=0)
    tgt = _entity("tgt", bab=5, str_mod=5)
    ws = _ws(att, tgt)
    events, _, result = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    assert not result.success, "IDC-003: disarm should fail"
    fail_ev = _get_ev(events, "disarm_failure")
    assert fail_ev is not None and fail_ev.payload["counter_disarm_allowed"] is True, (
        "IDC-003: counter_disarm_allowed should be True")
    # Counter opposed_check event
    counter_oc = None
    for e in events:
        if e.event_type == "opposed_check" and e.payload.get("is_counter_disarm"):
            counter_oc = e
            break
    assert counter_oc is not None, "IDC-003: opposed_check(is_counter_disarm=True) missing"
    assert counter_oc.payload["original_attacker"] == "att", \
        f"IDC-003: original_attacker should be 'att'; got {counter_oc.payload.get('original_attacker')}"
    assert counter_oc.payload["counter_attacker"] == "tgt", \
        f"IDC-003: counter_attacker should be 'tgt'; got {counter_oc.payload.get('counter_attacker')}"


# ---------------------------------------------------------------------------
# IDC-004: Disarm fails by >= 10, HAS Improved Disarm → counter suppressed
# ---------------------------------------------------------------------------
def test_idc004_improved_disarm_suppresses_counter():
    """IDC-004: Fails by >= 10 WITH Improved Disarm → counter_disarm_suppressed, no counter roll."""
    # att: improved_disarm → +4 applied at check, so modifier=0+4=4
    # def: modifier=14 (bab=5, str=9) → margin = (15+14)-(15+4) = 29-19=10 → counter triggered
    # BUT improved_disarm suppresses it
    att = _entity("att", feats=["improved_disarm"], bab=0, str_mod=0)
    tgt = _entity("tgt", bab=5, str_mod=9)
    ws = _ws(att, tgt)
    events, _, result = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    assert not result.success, "IDC-004: disarm should fail"
    supp_ev = _get_ev(events, "counter_disarm_suppressed")
    assert supp_ev is not None, "IDC-004: counter_disarm_suppressed event missing"
    # No counter opposed_check should follow
    counter_oc = None
    for e in events:
        if e.event_type == "opposed_check" and e.payload.get("is_counter_disarm"):
            counter_oc = e
            break
    assert counter_oc is None, "IDC-004: counter opposed_check should NOT appear when suppressed"


# ---------------------------------------------------------------------------
# IDC-005: Counter wins → counter_disarm_success event, attacker marked DISARMED
# ---------------------------------------------------------------------------
def test_idc005_counter_disarm_wins():
    """IDC-005: Counter-disarm succeeds → counter_disarm_success emitted, attacker DISARMED."""
    # att modifier=0, def modifier=10: disarm fails by 10, counter rolls
    # With roll=15: counter_att(def_mod=10)_total=25, counter_def(att_mod=0)_total=15 → counter wins
    att = _entity("att", feats=[], bab=0, str_mod=0)
    tgt = _entity("tgt", bab=5, str_mod=5)
    ws = _ws(att, tgt)
    events, updated_ws, result = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    success_ev = _get_ev(events, "counter_disarm_success")
    assert success_ev is not None, "IDC-005: counter_disarm_success event missing"
    assert success_ev.payload["counter_attacker"] == "tgt", \
        f"IDC-005: counter_attacker should be 'tgt'; got {success_ev.payload.get('counter_attacker')}"
    assert success_ev.payload["target_id"] == "att", \
        f"IDC-005: target_id should be 'att'; got {success_ev.payload.get('target_id')}"
    assert success_ev.payload["weapon_dropped"] is True, \
        "IDC-005: weapon_dropped should be True"
    assert updated_ws.entities["att"].get(EF.DISARMED) is True, \
        "IDC-005: attacker should be marked DISARMED in updated world_state"


# ---------------------------------------------------------------------------
# IDC-006: Counter fails → counter_disarm_failure event, attacker NOT disarmed
# ---------------------------------------------------------------------------
def test_idc006_counter_disarm_fails():
    """IDC-006: Counter-disarm fails → counter_disarm_failure emitted, attacker not disarmed."""
    # SeqRNG: disarm check: att_roll=5, def_roll=15 (margin=10, counter triggered)
    # counter check: counter_att_roll=8, counter_def_roll=10 (tie favors defender → counter fails)
    # att modifier = def modifier = 7 (bab=5, str=2) for equal modifiers
    att = _entity("att", feats=[], bab=5, str_mod=2)
    tgt = _entity("tgt", bab=5, str_mod=2)
    ws = _ws(att, tgt)
    events, updated_ws, result = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _seq_rng(5, 15, 8, 10), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    fail_ev = _get_ev(events, "counter_disarm_failure")
    assert fail_ev is not None, "IDC-006: counter_disarm_failure event missing"
    assert fail_ev.payload["counter_attacker"] == "tgt", \
        f"IDC-006: counter_attacker should be 'tgt'; got {fail_ev.payload.get('counter_attacker')}"
    assert updated_ws.entities["att"].get(EF.DISARMED) is not True, \
        "IDC-006: attacker should NOT be disarmed when counter fails"


# ---------------------------------------------------------------------------
# IDC-007: disarm_failure.margin = defender_total - attacker_total (not raw rolls)
# ---------------------------------------------------------------------------
def test_idc007_margin_uses_totals():
    """IDC-007: disarm_failure.margin is computed from modifier totals, not raw d20 rolls."""
    # SeqRNG: att_roll=5, def_roll=10
    # att: bab=1, str=2 → modifier=3; def: bab=5, str=2 → modifier=7
    # att_total=8, def_total=17 → total_margin=9
    # OLD (buggy) raw_margin = def_roll - att_roll = 10-5=5 (different from 9)
    att = _entity("att", bab=1, str_mod=2)
    tgt = _entity("tgt", bab=5, str_mod=2)
    ws = _ws(att, tgt)
    events, _, _ = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _seq_rng(5, 10), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    fail_ev = _get_ev(events, "disarm_failure")
    assert fail_ev is not None, "IDC-007: disarm_failure event missing"
    assert fail_ev.payload["margin"] == 9, (
        f"IDC-007: margin should be 9 (totals: 17-8); "
        f"got {fail_ev.payload['margin']} (old buggy raw would be 5)")


# ---------------------------------------------------------------------------
# IDC-008: counter_disarm_suppressed payload fields
# ---------------------------------------------------------------------------
def test_idc008_suppressed_event_payload():
    """IDC-008: counter_disarm_suppressed has actor_id=attacker_id and feat='improved_disarm'."""
    # Same setup as IDC-004
    att = _entity("att", feats=["improved_disarm"], bab=0, str_mod=0)
    tgt = _entity("tgt", bab=5, str_mod=9)
    ws = _ws(att, tgt)
    events, _, _ = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    supp_ev = _get_ev(events, "counter_disarm_suppressed")
    assert supp_ev is not None, "IDC-008: counter_disarm_suppressed event missing"
    assert supp_ev.payload["actor_id"] == "att", (
        f"IDC-008: actor_id should be 'att'; got {supp_ev.payload.get('actor_id')}")
    assert supp_ev.payload["feat"] == "improved_disarm", (
        f"IDC-008: feat should be 'improved_disarm'; got {supp_ev.payload.get('feat')}")
