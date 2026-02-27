"""
ENGINE GATE -- WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001
Tests IMB-001 through IMB-008.
PHB p.95-98: Improved Disarm / Grapple / Bull Rush / Trip / Sunder each grant
+4 to the attacker's opposed check modifier.
"""
from unittest.mock import MagicMock

from aidm.core.maneuver_resolver import (
    resolve_bull_rush,
    resolve_trip,
    resolve_sunder,
    resolve_disarm,
    resolve_grapple,
)
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, SunderIntent, DisarmIntent, GrappleIntent,
)
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng(val=15):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=val)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _entity(eid, feats=None, str_mod=2, bab=5, ac=10, dex_mod=0):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "player",
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: dex_mod,
        EF.FEATS: feats if feats is not None else [],
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30,
        EF.AC: ac,
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


# Medium size → special_size=0, standard_attack_size=0
# Bull rush baseline: STR(2) + special_size(0) = 2. With feat: 6.
# Trip baseline: STR(2) + special_size(0) = 2. With feat: 6.
# Sunder baseline: BAB(5) + STR(2) + std_size(0) = 7. With feat: 11.
# Disarm baseline: BAB(5) + STR(2) + special_size(0) + weapon_mod(0) = 7. With feat: 11.
# Grapple baseline: BAB(5) + STR(2) + special_size(0) = 7. With feat: 11.
_BULL_RUSH_BASELINE = 2
_TRIP_BASELINE = 2
_SUNDER_BASELINE = 7
_DISARM_BASELINE = 7
_GRAPPLE_BASELINE = 7


# ---------------------------------------------------------------------------
# IMB-001: Improved Disarm attacker → +4 applied at disarm check
# ---------------------------------------------------------------------------
def test_imb001_improved_disarm_plus4():
    """IMB-001: Improved Disarm → attacker_modifier in opposed_check is baseline+4."""
    att = _entity("att", feats=["improved_disarm"])
    tgt = _entity("tgt")
    ws = _ws(att, tgt)
    events, _, _ = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    oc = _get_ev(events, "opposed_check")
    assert oc is not None, "IMB-001: opposed_check event missing"
    assert oc.payload["attacker_modifier"] == _DISARM_BASELINE + 4, (
        f"IMB-001: attacker_modifier should be {_DISARM_BASELINE + 4}; "
        f"got {oc.payload['attacker_modifier']}")


# ---------------------------------------------------------------------------
# IMB-002: Improved Sunder attacker → +4 applied at sunder check
# ---------------------------------------------------------------------------
def test_imb002_improved_sunder_plus4():
    """IMB-002: Improved Sunder → attacker_modifier in opposed_check is baseline+4."""
    att = _entity("att", feats=["improved_sunder"])
    tgt = _entity("tgt")
    ws = _ws(att, tgt)
    events, _, _ = resolve_sunder(
        SunderIntent(attacker_id="att", target_id="tgt", target_item="weapon"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False,
    )
    oc = _get_ev(events, "opposed_check")
    assert oc is not None, "IMB-002: opposed_check event missing"
    assert oc.payload["attacker_modifier"] == _SUNDER_BASELINE + 4, (
        f"IMB-002: attacker_modifier should be {_SUNDER_BASELINE + 4}; "
        f"got {oc.payload['attacker_modifier']}")


# ---------------------------------------------------------------------------
# IMB-003: Improved Trip attacker → +4 applied at trip check
# ---------------------------------------------------------------------------
def test_imb003_improved_trip_plus4():
    """IMB-003: Improved Trip → attacker_modifier in opposed_check is baseline+4."""
    att = _entity("att", feats=["improved_trip"])
    tgt = _entity("tgt")
    ws = _ws(att, tgt)
    # d20=15 → touch attack hits (15+BAB=20 vs touch_ac=10), then opposed check
    events, _, _ = resolve_trip(
        TripIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False,
    )
    oc = _get_ev(events, "opposed_check")
    assert oc is not None, "IMB-003: opposed_check event missing (touch attack may have missed)"
    assert oc.payload["attacker_modifier"] == _TRIP_BASELINE + 4, (
        f"IMB-003: attacker_modifier should be {_TRIP_BASELINE + 4}; "
        f"got {oc.payload['attacker_modifier']}")


# ---------------------------------------------------------------------------
# IMB-004: Improved Grapple attacker → +4 applied at grapple check
# ---------------------------------------------------------------------------
def test_imb004_improved_grapple_plus4():
    """IMB-004: Improved Grapple → attacker_grapple_modifier in opposed_check is baseline+4."""
    att = _entity("att", feats=["improved_grapple"])
    tgt = _entity("tgt")
    ws = _ws(att, tgt)
    # d20=15: touch attack (15+BAB=20 vs touch_ac=10) hits, then grapple opposed check
    events, _, _ = resolve_grapple(
        GrappleIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    oc = _get_ev(events, "opposed_check")
    assert oc is not None, "IMB-004: opposed_check event missing (touch attack may have missed)"
    assert oc.payload["attacker_modifier"] == _GRAPPLE_BASELINE + 4, (
        f"IMB-004: attacker_modifier should be {_GRAPPLE_BASELINE + 4}; "
        f"got {oc.payload['attacker_modifier']}")


# ---------------------------------------------------------------------------
# IMB-005: Improved Bull Rush → +4 for follow-through bull rush (with charge)
# ---------------------------------------------------------------------------
def test_imb005_improved_bull_rush_with_charge_plus4():
    """IMB-005: Improved Bull Rush + is_charge=True → attacker_modifier = baseline+charge+4."""
    att = _entity("att", feats=["improved_bull_rush"])
    tgt = _entity("tgt")
    ws = _ws(att, tgt)
    # Charge bonus +2 applies; improved_bull_rush adds +4 on top
    events, _, _ = resolve_bull_rush(
        BullRushIntent(attacker_id="att", target_id="tgt", is_charge=True),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False,
    )
    oc = _get_ev(events, "opposed_check")
    assert oc is not None, "IMB-005: opposed_check event missing"
    # baseline=2, charge=+2, feat=+4 → 8
    assert oc.payload["attacker_modifier"] == _BULL_RUSH_BASELINE + 2 + 4, (
        f"IMB-005: charge bull rush attacker_modifier should be {_BULL_RUSH_BASELINE + 2 + 4}; "
        f"got {oc.payload['attacker_modifier']}")


# ---------------------------------------------------------------------------
# IMB-006: No improved feat → no bonus on any maneuver (regression guard)
# ---------------------------------------------------------------------------
def test_imb006_no_feat_no_bonus():
    """IMB-006: No improved feat → attacker_modifier is exactly baseline (no +4)."""
    att = _entity("att", feats=[])  # no improved maneuver feats
    tgt = _entity("tgt")
    ws = _ws(att, tgt)
    events, _, _ = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    oc = _get_ev(events, "opposed_check")
    assert oc is not None, "IMB-006: opposed_check event missing"
    assert oc.payload["attacker_modifier"] == _DISARM_BASELINE, (
        f"IMB-006: no feat → attacker_modifier should be {_DISARM_BASELINE} (no bonus); "
        f"got {oc.payload['attacker_modifier']}")


# ---------------------------------------------------------------------------
# IMB-007: Multiple improved feats held → each applies only to its own maneuver
# ---------------------------------------------------------------------------
def test_imb007_multiple_feats_isolated():
    """IMB-007: Attacker with improved_trip + improved_disarm doing a trip → +4 only (not +8)."""
    att = _entity("att", feats=["improved_trip", "improved_disarm"])
    tgt = _entity("tgt")
    ws = _ws(att, tgt)
    events, _, _ = resolve_trip(
        TripIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0,
        aoo_events=[], aoo_defeated=False,
    )
    oc = _get_ev(events, "opposed_check")
    assert oc is not None, "IMB-007: opposed_check event missing"
    # Only improved_trip applies to the trip check, not improved_disarm
    assert oc.payload["attacker_modifier"] == _TRIP_BASELINE + 4, (
        f"IMB-007: trip with 2 improved feats → only +4 (not +8); "
        f"got {oc.payload['attacker_modifier']}")


# ---------------------------------------------------------------------------
# IMB-008: +4 bonus appears in opposed_check event payload for all 5 maneuvers
# ---------------------------------------------------------------------------
def test_imb008_bonus_in_event_payload_all_5():
    """IMB-008: +4 bonus visible in opposed_check.attacker_modifier for all 5 maneuvers."""
    att = _entity("att", feats=[
        "improved_disarm", "improved_sunder", "improved_trip",
        "improved_grapple", "improved_bull_rush",
    ])
    tgt = _entity("tgt")
    ws = _ws(att, tgt)

    # Bull Rush
    ev_br, _, _ = resolve_bull_rush(
        BullRushIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0, aoo_events=[], aoo_defeated=False,
    )
    oc_br = _get_ev(ev_br, "opposed_check")
    assert oc_br is not None and oc_br.payload["attacker_modifier"] == _BULL_RUSH_BASELINE + 4, \
        f"IMB-008 BR: got {oc_br and oc_br.payload.get('attacker_modifier')}"

    # Trip
    ev_tr, _, _ = resolve_trip(
        TripIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0, aoo_events=[], aoo_defeated=False,
    )
    oc_tr = _get_ev(ev_tr, "opposed_check")
    assert oc_tr is not None and oc_tr.payload["attacker_modifier"] == _TRIP_BASELINE + 4, \
        f"IMB-008 TRIP: got {oc_tr and oc_tr.payload.get('attacker_modifier')}"

    # Sunder
    ev_su, _, _ = resolve_sunder(
        SunderIntent(attacker_id="att", target_id="tgt", target_item="weapon"),
        ws, _rng(15), 0, 0.0, aoo_events=[], aoo_defeated=False,
    )
    oc_su = _get_ev(ev_su, "opposed_check")
    assert oc_su is not None and oc_su.payload["attacker_modifier"] == _SUNDER_BASELINE + 4, \
        f"IMB-008 SUNDER: got {oc_su and oc_su.payload.get('attacker_modifier')}"

    # Disarm
    ev_di, _, _ = resolve_disarm(
        DisarmIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0, aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    oc_di = _get_ev(ev_di, "opposed_check")
    assert oc_di is not None and oc_di.payload["attacker_modifier"] == _DISARM_BASELINE + 4, \
        f"IMB-008 DISARM: got {oc_di and oc_di.payload.get('attacker_modifier')}"

    # Grapple
    ev_gr, _, _ = resolve_grapple(
        GrappleIntent(attacker_id="att", target_id="tgt"),
        ws, _rng(15), 0, 0.0, aoo_events=[], aoo_defeated=False, aoo_dealt_damage=False,
    )
    oc_gr = _get_ev(ev_gr, "opposed_check")
    assert oc_gr is not None and oc_gr.payload["attacker_modifier"] == _GRAPPLE_BASELINE + 4, \
        f"IMB-008 GRAPPLE: got {oc_gr and oc_gr.payload.get('attacker_modifier')}"
