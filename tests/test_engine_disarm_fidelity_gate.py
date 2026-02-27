"""Gate tests: WO-ENGINE-DISARM-FIDELITY-001

ENGINE-DISARM-FIDELITY: Counter-disarm threshold removed (any failure allows
counter per PHB p.155). Size modifier verification.

DSFX-001 – DSFX-008 (8 tests)
"""
from unittest.mock import MagicMock

import pytest

from aidm.core.maneuver_resolver import resolve_disarm
from aidm.schemas.maneuvers import DisarmIntent
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# RNG helpers
# ---------------------------------------------------------------------------

class _SeqRNG:
    """Sequential RNG: returns values from a list, cycling."""
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


def _seq_rng(*values):
    return _SeqRNG(values)


def _rng(val=15):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=val)
    rng.stream = MagicMock(return_value=stream)
    return rng


# ---------------------------------------------------------------------------
# Entity / WorldState helpers
# ---------------------------------------------------------------------------

def _entity(eid, feats=None, bab=5, str_mod=2, size="medium"):
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
        EF.SIZE_CATEGORY: size,
        EF.STABILITY_BONUS: 0,
        EF.POSITION: {"x": 0, "y": 0},
        EF.DISARMED: False,
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


def _intent(att_id="att", tgt_id="def"):
    return DisarmIntent(attacker_id=att_id, target_id=tgt_id)


def _get_ev(events, etype):
    return [e for e in events if e.event_type == etype]


# ---------------------------------------------------------------------------
# DSFX-001: Disarm fails by margin=1 → counter-disarm allowed (was blocked)
# ---------------------------------------------------------------------------

def test_dsfx_001_margin_1_counter_allowed():
    """DSFX-001: Attacker fails by 1 → counter-disarm attempt occurs."""
    # Attacker: BAB 5 + STR 2 = 7
    # Defender: BAB 5 + STR 3 = 8  (margin = 1)
    # Attacker rolls 10, defender rolls 10 → totals: 17 vs 18 → margin 1
    att = _entity("att", bab=5, str_mod=2)
    tgt = _entity("def", bab=5, str_mod=3)
    ws = _ws(att, tgt)
    # Rolls: attacker=10, defender=10 (opposed check), then counter-disarm=10, counter-def=10
    rng = _seq_rng(10, 10, 10, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    # Disarm must fail (attacker total 17 < defender total 18)
    fail_evs = _get_ev(events, "disarm_failure")
    assert len(fail_evs) == 1
    assert fail_evs[0].payload["counter_disarm_allowed"] is True
    # Counter-disarm opposed check must be attempted
    counter_checks = [e for e in events if e.event_type == "opposed_check"
                      and e.payload.get("is_counter_disarm")]
    assert len(counter_checks) >= 1


# ---------------------------------------------------------------------------
# DSFX-002: Disarm fails by margin=5 → counter-disarm allowed (was blocked)
# ---------------------------------------------------------------------------

def test_dsfx_002_margin_5_counter_allowed():
    """DSFX-002: Attacker fails by 5 → counter-disarm allowed."""
    # Attacker: BAB 2 + STR 0 = 2, roll 10 → total 12
    # Defender: BAB 5 + STR 2 = 7, roll 10 → total 17 → margin 5
    att = _entity("att", bab=2, str_mod=0)
    tgt = _entity("def", bab=5, str_mod=2)
    ws = _ws(att, tgt)
    rng = _seq_rng(10, 10, 10, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    fail_evs = _get_ev(events, "disarm_failure")
    assert len(fail_evs) == 1
    assert fail_evs[0].payload["counter_disarm_allowed"] is True
    counter_checks = [e for e in events if e.event_type == "opposed_check"
                      and e.payload.get("is_counter_disarm")]
    assert len(counter_checks) >= 1


# ---------------------------------------------------------------------------
# DSFX-003: Disarm fails by margin=9 → counter-disarm allowed (boundary)
# ---------------------------------------------------------------------------

def test_dsfx_003_margin_9_counter_allowed():
    """DSFX-003: Attacker fails by 9 → counter-disarm (was blocked at < 10, boundary test)."""
    # Attacker: BAB 0 + STR 0 = 0, roll 10 → total 10
    # Defender: BAB 9 + STR 0 = 9, roll 10 → total 19 → margin 9
    att = _entity("att", bab=0, str_mod=0)
    tgt = _entity("def", bab=9, str_mod=0)
    ws = _ws(att, tgt)
    rng = _seq_rng(10, 10, 10, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    fail_evs = _get_ev(events, "disarm_failure")
    assert len(fail_evs) == 1
    assert fail_evs[0].payload["counter_disarm_allowed"] is True
    assert fail_evs[0].payload["margin"] == 9
    counter_checks = [e for e in events if e.event_type == "opposed_check"
                      and e.payload.get("is_counter_disarm")]
    assert len(counter_checks) >= 1


# ---------------------------------------------------------------------------
# DSFX-004: Disarm fails by margin=10 → counter-disarm allowed (was already allowed)
# ---------------------------------------------------------------------------

def test_dsfx_004_margin_10_counter_allowed():
    """DSFX-004: Attacker fails by 10 → counter-disarm (was already allowed)."""
    # Attacker: BAB 0 + STR 0 = 0, roll 10 → total 10
    # Defender: BAB 10 + STR 0 = 10, roll 10 → total 20 → margin 10
    att = _entity("att", bab=0, str_mod=0)
    tgt = _entity("def", bab=10, str_mod=0)
    ws = _ws(att, tgt)
    rng = _seq_rng(10, 10, 10, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    fail_evs = _get_ev(events, "disarm_failure")
    assert len(fail_evs) == 1
    assert fail_evs[0].payload["counter_disarm_allowed"] is True
    assert fail_evs[0].payload["margin"] == 10


# ---------------------------------------------------------------------------
# DSFX-005: Disarm succeeds → no counter-disarm (control)
# ---------------------------------------------------------------------------

def test_dsfx_005_success_no_counter():
    """DSFX-005: Disarm succeeds → no counter-disarm triggered."""
    # Attacker: BAB 10 + STR 3 = 13, roll 15 → total 28
    # Defender: BAB 5 + STR 2 = 7, roll 10 → total 17
    att = _entity("att", bab=10, str_mod=3)
    tgt = _entity("def", bab=5, str_mod=2)
    ws = _ws(att, tgt)
    rng = _seq_rng(15, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    assert result.success is True
    counter_checks = [e for e in events if e.event_type == "opposed_check"
                      and e.payload.get("is_counter_disarm")]
    assert len(counter_checks) == 0


# ---------------------------------------------------------------------------
# DSFX-006: Medium vs Large → Large gets +4 size bonus
# ---------------------------------------------------------------------------

def test_dsfx_006_medium_vs_large_size_bonus():
    """DSFX-006: Medium vs Large disarm → Large gets +4 size modifier."""
    # Both BAB 5, STR 2 (base mod 7). Large defender gets +4 size → mod 11.
    # Both roll 10: attacker total 17, defender total 21.
    att = _entity("att", bab=5, str_mod=2, size="medium")
    tgt = _entity("def", bab=5, str_mod=2, size="large")
    ws = _ws(att, tgt)
    rng = _seq_rng(10, 10, 10, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    # Attacker should fail (17 vs 21)
    assert result.success is False
    # Check the opposed check event for modifier values
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first_check = checks[0]
    # Defender total should be 4 higher due to size
    assert first_check.payload["defender_total"] - first_check.payload["attacker_total"] == 4


# ---------------------------------------------------------------------------
# DSFX-007: Medium vs Medium → no size bonus
# ---------------------------------------------------------------------------

def test_dsfx_007_medium_vs_medium_no_bonus():
    """DSFX-007: Medium vs Medium disarm → no size bonus (same size)."""
    # Both BAB 5, STR 2. Both medium → both size mod 0.
    att = _entity("att", bab=5, str_mod=2, size="medium")
    tgt = _entity("def", bab=5, str_mod=2, size="medium")
    ws = _ws(att, tgt)
    rng = _seq_rng(10, 10, 10, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    # Same rolls + same modifiers = tie. Check who wins ties.
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first_check = checks[0]
    # Totals should be equal (both mod 7, both roll 10 = 17)
    assert first_check.payload["attacker_total"] == first_check.payload["defender_total"]


# ---------------------------------------------------------------------------
# DSFX-008: Small vs Large → Large gets +8 size bonus (2 steps)
# ---------------------------------------------------------------------------

def test_dsfx_008_small_vs_large_size_bonus():
    """DSFX-008: Small vs Large disarm → Large gets +8 bonus (2 size steps)."""
    # Small attacker: BAB 5 + STR 2 + size(-4) = 3, roll 10 → total 13
    # Large defender: BAB 5 + STR 2 + size(+4) = 11, roll 10 → total 21
    att = _entity("att", bab=5, str_mod=2, size="small")
    tgt = _entity("def", bab=5, str_mod=2, size="large")
    ws = _ws(att, tgt)
    rng = _seq_rng(10, 10, 10, 10)
    events, _, result = resolve_disarm(_intent(), ws, rng, next_event_id=1, timestamp=1.0)
    assert result.success is False
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first_check = checks[0]
    # Net difference = 8 (Large +4, Small -4 → relative +8)
    assert first_check.payload["defender_total"] - first_check.payload["attacker_total"] == 8
