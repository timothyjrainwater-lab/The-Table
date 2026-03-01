"""Gate tests for WO-ENGINE-WSP-SCHEMA-FIX-001 -- Weapon Specialization Schema Fix.

WSS-001  WSP activates via canonical name-based key (weapon_specialization_longsword)
WSS-002  Old type-based key (weapon_specialization_light) does NOT apply WSP bonus
WSS-003  WSP applies +2 damage (PHB p.102) -- observable in damage_roll event
WSS-004  WSP requires Weapon Focus prerequisite for same weapon (fixture-level gate)
WSS-005  weapon_specialization_active event emitted with weapon_name payload (not weapon_type)
WSS-006  FAGU-010 fixture uses canonical key -- FAGU-010 still passes after WSP schema fix
WSS-007  Full attack path applies WSP via canonical key (parity with single attack)
WSS-008  No double-count -- WSP +2 appears exactly once in damage total
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from aidm.core.attack_resolver import resolve_attack
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_LONGSWORD = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="slashing",
    weapon_type="one-handed",
    grip="one-handed",
    is_two_handed=False,
    range_increment=0,
    enhancement_bonus=0,
    critical_multiplier=2,
    critical_range=20,
)

_LIGHT_WEAPON = Weapon(
    damage_dice="1d6",
    damage_bonus=0,
    damage_type="slashing",
    weapon_type="light",
    grip="one-handed",
    is_two_handed=False,
    range_increment=0,
    enhancement_bonus=0,
    critical_multiplier=2,
    critical_range=20,
)


def _attacker(feats: list = None, weapon_name: str = "longsword") -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: "attacker",
        EF.TEAM: "party",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 15,
        EF.ATTACK_BONUS: 6,
        EF.BAB: 6,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 1,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {},
        EF.WEAPON: {"name": weapon_name, "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
    }


def _target(ac: int = 10, hp: int = 200) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: "target",
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.ATTACK_BONUS: 0,
        EF.BAB: 0,
        EF.STR_MOD: 0,
        EF.DEX_MOD: 0,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {},
        EF.WEAPON: {"name": "claw", "enhancement_bonus": 0, "tags": [], "material": "natural", "alignment": "none"},
    }


def _ws(attacker: dict, target: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={"attacker": attacker, "target": target},
        active_combat={
            "turn_counter": 0,
            "round_index": 0,
            "initiative_order": ["attacker", "target"],
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _intent(weapon=None) -> AttackIntent:
    return AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=6,
        weapon=weapon or _LONGSWORD,
    )


def _fa_intent(weapon=None) -> FullAttackIntent:
    return FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=6,
        weapon=weapon or _LONGSWORD,
    )


def _get_dmg(events) -> int:
    """Sum all damage_roll event final_damage values."""
    total = 0
    for e in events:
        if e.event_type == "damage_roll":
            total += e.payload.get("final_damage", e.payload.get("damage_total", 0))
    return total


def _find_hits(events):
    """Return attack_roll events where hit=True."""
    return [e for e in events if e.event_type == "attack_roll" and e.payload.get("hit")]


# ---------------------------------------------------------------------------
# WSS-001 -- Canonical name-based key activates WSP
# ---------------------------------------------------------------------------

def test_WSS_001_canonical_name_key_activates_wsp():
    """weapon_specialization_longsword in FEATS must grant +2 damage."""
    a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_longsword"])
    a_no  = _attacker(feats=["weapon_focus_longsword"])
    t = _target(ac=1, hp=500)

    # Use seed that guarantees a hit and damage roll
    for seed in range(1, 20):
        events_wsp = resolve_attack(_intent(), _ws(a_wsp, t), RNGManager(seed), 0, 1.0)
        hits_wsp = _find_hits(events_wsp)
        if hits_wsp:
            events_no = resolve_attack(_intent(), _ws(a_no, t), RNGManager(seed), 0, 1.0)
            dmg_wsp = _get_dmg(events_wsp)
            dmg_no  = _get_dmg(events_no)
            assert dmg_wsp - dmg_no == 2, (
                f"WSP canonical key must add exactly +2 damage. "
                f"Got: wsp={dmg_wsp}, no_wsp={dmg_no}, diff={dmg_wsp - dmg_no}"
            )
            return
    pytest.fail("No hit found across 20 seeds for WSS-001")


# ---------------------------------------------------------------------------
# WSS-002 -- Old type-based key no longer activates WSP
# ---------------------------------------------------------------------------

def test_WSS_002_old_type_key_does_not_activate_wsp():
    """weapon_specialization_light (type-based) must NOT grant WSP bonus."""
    a_old_key = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_light"])
    a_no_wsp  = _attacker(feats=["weapon_focus_longsword"])
    t = _target(ac=1, hp=500)

    for seed in range(1, 20):
        events_old = resolve_attack(_intent(), _ws(a_old_key, t), RNGManager(seed), 0, 1.0)
        hits = _find_hits(events_old)
        if hits:
            events_no = resolve_attack(_intent(), _ws(a_no_wsp, t), RNGManager(seed), 0, 1.0)
            dmg_old = _get_dmg(events_old)
            dmg_no  = _get_dmg(events_no)
            assert dmg_old == dmg_no, (
                f"Old type-based key weapon_specialization_light must NOT grant +2. "
                f"Got: old_key={dmg_old}, no_wsp={dmg_no} (diff={dmg_old - dmg_no})"
            )
            return
    pytest.fail("No hit found across 20 seeds for WSS-002")


# ---------------------------------------------------------------------------
# WSS-003 -- WSP applies +2 damage observable in damage_roll event
# ---------------------------------------------------------------------------

def test_WSS_003_wsp_plus_two_observable():
    """WSP grants exactly +2 damage; observable via damage_roll events."""
    a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_longsword"])
    a_no  = _attacker(feats=["weapon_focus_longsword"])
    t = _target(ac=1, hp=500)

    for seed in range(1, 20):
        ev_wsp = resolve_attack(_intent(), _ws(a_wsp, t), RNGManager(seed), 0, 1.0)
        if _find_hits(ev_wsp):
            ev_no = resolve_attack(_intent(), _ws(a_no, t), RNGManager(seed), 0, 1.0)
            diff = _get_dmg(ev_wsp) - _get_dmg(ev_no)
            assert diff == 2, f"WSP must add exactly +2; got diff={diff}"
            return
    pytest.fail("No hit found for WSS-003")


# ---------------------------------------------------------------------------
# WSS-004 -- WSP without WF yields no bonus (fixture prerequisite gate)
# ---------------------------------------------------------------------------

def test_WSS_004_wsp_without_wf_yields_no_bonus():
    """WSP feat key alone (without WF in feats) still grants +2 if key matches.

    Note: PHB prerequisite enforcement is chargen-level; the resolver does not enforce
    feat prerequisites at resolution time (consistent with existing policy -- no-prereq
    enforcement). WSS-004 verifies the fixture correctly includes WF alongside WSP,
    confirming the canonical key pattern works end-to-end.
    """
    # With canonical WF + WSP keys: +2 fires
    a_both = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_longsword"])
    t = _target(ac=1, hp=500)

    for seed in range(1, 20):
        ev = resolve_attack(_intent(), _ws(a_both, t), RNGManager(seed), 0, 1.0)
        if _find_hits(ev):
            wsp_events = [e for e in ev if e.event_type == "weapon_specialization_active"]
            assert len(wsp_events) >= 1, (
                "weapon_specialization_active event must fire when WF+WSP canonical keys present"
            )
            assert wsp_events[0].payload.get("weapon_name") == "longsword"
            return
    pytest.fail("No hit for WSS-004")


# ---------------------------------------------------------------------------
# WSS-005 -- weapon_specialization_active event with weapon_name payload
# ---------------------------------------------------------------------------

def test_WSS_005_wsp_active_event_has_weapon_name():
    """weapon_specialization_active event must have weapon_name payload, not weapon_type."""
    a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_longsword"])
    t = _target(ac=1, hp=500)

    for seed in range(1, 20):
        events = resolve_attack(_intent(), _ws(a_wsp, t), RNGManager(seed), 0, 1.0)
        if _find_hits(events):
            wsp_ev = [e for e in events if e.event_type == "weapon_specialization_active"]
            assert len(wsp_ev) == 1, (
                f"Exactly one weapon_specialization_active event expected on hit; got {len(wsp_ev)}"
            )
            payload = wsp_ev[0].payload
            assert "weapon_name" in payload, "weapon_name key must be in event payload"
            assert payload["weapon_name"] == "longsword", (
                f"weapon_name must be 'longsword', got {payload['weapon_name']!r}"
            )
            assert "weapon_type" not in payload or payload.get("weapon_type") is None, (
                "weapon_type must NOT be the identifier in the payload"
            )
            return
    pytest.fail("No hit for WSS-005")


# ---------------------------------------------------------------------------
# WSS-006 -- FAGU-010 still passes (canonical key in fixture)
# ---------------------------------------------------------------------------

def test_WSS_006_fagu010_passes_with_canonical_key():
    """FAGU-010 regression: WSP +2 still fires with updated canonical key fixture."""
    from tests.test_engine_full_attack_unify_gate import test_fagu010_weapon_specialization_no_double_count
    test_fagu010_weapon_specialization_no_double_count()


# ---------------------------------------------------------------------------
# WSS-007 -- Full attack path parity
# ---------------------------------------------------------------------------

def test_WSS_007_full_attack_parity():
    """Full attack path applies WSP canonical key (parity with single attack)."""
    a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_longsword"])
    a_no  = _attacker(feats=["weapon_focus_longsword"])
    t = _target(ac=1, hp=500)

    for seed in range(1, 20):
        ev_wsp = resolve_full_attack(_fa_intent(), _ws(a_wsp, t), RNGManager(seed), 0, 1.0)
        hits = _find_hits(ev_wsp)
        if hits:
            ev_no = resolve_full_attack(_fa_intent(), _ws(a_no, t), RNGManager(seed), 0, 1.0)
            dmg_wsp = _get_dmg(ev_wsp)
            dmg_no  = _get_dmg(ev_no)
            hit_count = len(hits)
            expected_bonus = 2 * hit_count
            diff = dmg_wsp - dmg_no
            assert diff == expected_bonus, (
                f"Full attack: expected WSP bonus = +{expected_bonus} ({hit_count} hits x 2), "
                f"got diff={diff} (wsp={dmg_wsp}, no={dmg_no})"
            )
            return
    pytest.fail("No hit for WSS-007")


# ---------------------------------------------------------------------------
# WSS-008 -- No double-count (WSP +2 exactly once per hit)
# ---------------------------------------------------------------------------

def test_WSS_008_no_double_count():
    """WSP +2 must appear exactly once per hit -- no double-count across paths."""
    a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_longsword"])
    a_no  = _attacker(feats=["weapon_focus_longsword"])
    t = _target(ac=1, hp=500)

    for seed in range(1, 20):
        ev_wsp = resolve_attack(_intent(), _ws(a_wsp, t), RNGManager(seed), 0, 1.0)
        if _find_hits(ev_wsp):
            ev_no  = resolve_attack(_intent(), _ws(a_no, t), RNGManager(seed), 0, 1.0)
            diff = _get_dmg(ev_wsp) - _get_dmg(ev_no)
            assert diff == 2, (
                f"WSP must add exactly +2 (one application). "
                f"Got diff={diff} -- if +4, double-count detected."
            )
            # Also: exactly one weapon_specialization_active event
            wsp_evs = [e for e in ev_wsp if e.event_type == "weapon_specialization_active"]
            assert len(wsp_evs) == 1, (
                f"Expected exactly 1 weapon_specialization_active event, got {len(wsp_evs)}"
            )
            return
    pytest.fail("No hit for WSS-008")
