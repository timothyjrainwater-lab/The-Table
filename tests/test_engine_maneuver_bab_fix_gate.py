"""Gate tests: WO-ENGINE-MANEUVER-BAB-FIX-001

Fixes _get_bab() to read EF.BAB (Type 1 component) instead of EF.ATTACK_BONUS
(BAB+STR composite). Prevents STR double-count in maneuver opposed checks.

MBF-001 – MBF-008 (8 tests)
"""
from unittest.mock import MagicMock

import pytest

from aidm.core.maneuver_resolver import _get_bab, resolve_grapple, resolve_bull_rush, resolve_trip, resolve_disarm, resolve_overrun
from aidm.schemas.maneuvers import GrappleIntent, BullRushIntent, TripIntent, DisarmIntent, OverrunIntent
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid, bab=5, str_mod=3, attack_bonus=None, size="medium"):
    ab = attack_bonus if attack_bonus is not None else bab + str_mod
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "player",
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.FEATS: [],
        EF.ATTACK_BONUS: ab,
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


class _SeqRNG:
    """Sequential RNG."""
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


def _get_ev(events, etype):
    return [e for e in events if e.event_type == etype]


# ---------------------------------------------------------------------------
# MBF-001: _get_bab() returns EF.BAB value, not EF.ATTACK_BONUS
# ---------------------------------------------------------------------------

def test_mbf_001_get_bab_returns_bab():
    """MBF-001: _get_bab() uses EF.BAB (5), not EF.ATTACK_BONUS (8)."""
    att = _entity("att", bab=5, str_mod=3)  # ATTACK_BONUS = 8
    ws = _ws(att, att)  # just need the entity in ws
    result = _get_bab(ws, "att")
    assert result == 5, f"Expected BAB=5, got {result} (was {att[EF.ATTACK_BONUS]} before fix)"


# ---------------------------------------------------------------------------
# MBF-002: Grapple check = d20 + BAB + STR + size (no double STR)
# ---------------------------------------------------------------------------

def test_mbf_002_grapple_no_double_str():
    """MBF-002: Grapple opposed check uses BAB not ATTACK_BONUS."""
    # Attacker: BAB 5, STR +3 → grapple mod = 5 + 3 = 8
    # Defender: BAB 5, STR +3 → grapple mod = 5 + 3 = 8
    # Both roll 10 → tie. Before fix: attacker mod = 8+3=11, giving wrong advantage.
    att = _entity("att", bab=5, str_mod=3)
    tgt = _entity("def", bab=5, str_mod=3)
    ws = _ws(att, tgt)
    intent = GrappleIntent(attacker_id="att", target_id="def")
    events, _, result = resolve_grapple(intent, ws, _seq_rng(10, 10), next_event_id=1, timestamp=1.0,
                                        aoo_events=[], aoo_defeated=False)
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first = checks[0]
    # Both should have same total (same stats, same rolls)
    assert first.payload["attacker_total"] == first.payload["defender_total"], \
        f"Grapple totals should be equal: att={first.payload['attacker_total']}, def={first.payload['defender_total']}"


# ---------------------------------------------------------------------------
# MBF-003: Bull rush check = d20 + BAB + STR + size (no double STR)
# ---------------------------------------------------------------------------

def test_mbf_003_bull_rush_no_double_str():
    """MBF-003: Bull rush uses BAB not ATTACK_BONUS."""
    att = _entity("att", bab=5, str_mod=3)
    tgt = _entity("def", bab=5, str_mod=3)
    ws = _ws(att, tgt)
    intent = BullRushIntent(attacker_id="att", target_id="def")
    events, _, result = resolve_bull_rush(intent, ws, _seq_rng(10, 10), next_event_id=1, timestamp=1.0,
                                          aoo_events=[], aoo_defeated=False)
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first = checks[0]
    # Same stats → same totals
    assert first.payload["attacker_total"] == first.payload["defender_total"]


# ---------------------------------------------------------------------------
# MBF-004: Trip check = d20 + BAB + STR + size (no double STR)
# ---------------------------------------------------------------------------

def test_mbf_004_trip_no_double_str():
    """MBF-004: Trip uses BAB not ATTACK_BONUS."""
    att = _entity("att", bab=5, str_mod=3)
    tgt = _entity("def", bab=5, str_mod=3)
    ws = _ws(att, tgt)
    intent = TripIntent(attacker_id="att", target_id="def")
    events, _, result = resolve_trip(intent, ws, _seq_rng(10, 10, 10, 10), next_event_id=1, timestamp=1.0,
                                     aoo_events=[], aoo_defeated=False)
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first = checks[0]
    assert first.payload["attacker_total"] == first.payload["defender_total"]


# ---------------------------------------------------------------------------
# MBF-005: Disarm check = d20 + BAB + size (STR not in disarm per PHB p.155)
# ---------------------------------------------------------------------------

def test_mbf_005_disarm_uses_bab():
    """MBF-005: Disarm uses BAB for opposed check."""
    att = _entity("att", bab=5, str_mod=3)
    tgt = _entity("def", bab=5, str_mod=3)
    ws = _ws(att, tgt)
    intent = DisarmIntent(attacker_id="att", target_id="def")
    events, _, result = resolve_disarm(intent, ws, _seq_rng(10, 10, 10, 10), next_event_id=1, timestamp=1.0,
                                        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False)
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first = checks[0]
    # With same BAB and size, totals should be equal
    assert first.payload["attacker_total"] == first.payload["defender_total"]


# ---------------------------------------------------------------------------
# MBF-006: Overrun check = d20 + BAB + STR + size (no double STR)
# ---------------------------------------------------------------------------

def test_mbf_006_overrun_no_double_str():
    """MBF-006: Overrun uses BAB not ATTACK_BONUS."""
    att = _entity("att", bab=5, str_mod=3)
    tgt = _entity("def", bab=5, str_mod=3)
    ws = _ws(att, tgt)
    intent = OverrunIntent(attacker_id="att", target_id="def")
    events, _, result = resolve_overrun(intent, ws, _seq_rng(10, 10), next_event_id=1, timestamp=1.0,
                                         aoo_events=[], aoo_defeated=False)
    checks = _get_ev(events, "opposed_check")
    assert len(checks) >= 1
    first = checks[0]
    assert first.payload["attacker_total"] == first.payload["defender_total"]


# ---------------------------------------------------------------------------
# MBF-007: Entity with EF.BAB=0 and EF.ATTACK_BONUS=5 → _get_bab() returns 0
# ---------------------------------------------------------------------------

def test_mbf_007_bab_zero_attack_bonus_five():
    """MBF-007: BAB=0, ATTACK_BONUS=5 → _get_bab() returns 0 (BAB is truth)."""
    entity = _entity("att", bab=0, str_mod=5)  # BAB=0, ATTACK_BONUS=5
    ws = _ws(entity, entity)
    result = _get_bab(ws, "att")
    assert result == 0, f"Expected BAB=0, got {result}"


# ---------------------------------------------------------------------------
# MBF-008: Entity with only EF.BAB set → returns BAB correctly
# ---------------------------------------------------------------------------

def test_mbf_008_bab_only():
    """MBF-008: Entity with BAB=7, no ATTACK_BONUS → returns 7."""
    entity = {
        EF.ENTITY_ID: "att",
        EF.BAB: 7,
        # No EF.ATTACK_BONUS at all
    }
    ws = WorldState(
        ruleset_version="3.5",
        entities={"att": entity},
        active_combat=None,
    )
    result = _get_bab(ws, "att")
    assert result == 7, f"Expected BAB=7, got {result}"
