"""Gate tests: ENGINE-WEAPON-SPECIALIZATION — WO-ENGINE-WEAPON-SPECIALIZATION-001.

Tests:
WSP-001: weapon_specialization_one-handed + matching weapon → +2 to damage roll
WSP-002: weapon_specialization_one-handed + two-handed weapon → no bonus (type mismatch)
WSP-003: Full attack — all iterative hits get +2 damage
WSP-004: Crit confirms: +2 damage bonus included in crit multiplier (pre-crit site)
WSP-005: Weapon Focus + Weapon Specialization on same weapon_type → +1 attack AND +2 damage
WSP-006: No Weapon Specialization feat → no damage bonus (regression guard)
WSP-007: weapon_specialization_two-handed → +2 damage with two-handed weapon
WSP-008: After WSP commit — WFC regression guard: Weapon Focus +1 attack still applies

Insertion sites:
  attack_resolver.py: _wsp_bonus applied to base_damage (pre-crit, multiplied on crits)
  full_attack_resolver.py: resolve_single_attack_with_critical() — same site, attacker_feats param
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.attack_resolver import resolve_attack
from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Weapons
# ---------------------------------------------------------------------------

ONE_HANDED_WEAPON = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=20,
    is_two_handed=False,
    grip="one-handed",
    weapon_type="one-handed",
    range_increment=0,
    enhancement_bonus=0,
)

TWO_HANDED_WEAPON = Weapon(
    damage_dice="1d10",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=20,
    is_two_handed=True,
    grip="two-handed",
    weapon_type="two-handed",
    range_increment=0,
    enhancement_bonus=0,
)

# Critical-range weapon for WSP-004
CRIT_WEAPON = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=20,
    is_two_handed=False,
    grip="one-handed",
    weapon_type="one-handed",
    range_increment=0,
    enhancement_bonus=0,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attacker(
    eid: str = "fighter",
    feats: list = None,
    bab: int = 5,
    str_mod: int = 2,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 15,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: str_mod,
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
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {"fighter": 5},
        EF.WEAPON: {"enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
    }


def _target(eid: str = "goblin", hp: int = 30, ac: int = 10) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.DAMAGE_REDUCTIONS: [],
        EF.SAVE_FORT: 3,
        EF.CON_MOD: 2,
        EF.CREATURE_TYPE: "humanoid",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.CLASS_LEVELS: {},
        EF.DEX_MOD: 1,
    }


def _world(attacker: dict, target: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target},
        active_combat={"initiative_order": [attacker[EF.ENTITY_ID], target[EF.ENTITY_ID]]},
    )


def _rng_hit(attack_roll: int = 15, damage_roll: int = 3):
    """RNG that hits. Returns attack_roll for d20, damage_roll for damage."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [attack_roll, damage_roll] + [damage_roll] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _rng_crit(d20: int = 20, confirm_d20: int = 15, damage_roll: int = 3):
    """RNG that threatens and confirms a crit."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [d20, confirm_d20, damage_roll] + [damage_roll] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _intent(attacker_id: str, target_id: str, weapon: Weapon, attack_bonus: int = 10) -> AttackIntent:
    return AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        attack_bonus=attack_bonus,
        weapon=weapon,
        power_attack_penalty=0,
    )


def _get_damage_total(events) -> int:
    """Extract pre-DR damage_total from damage_roll event."""
    for e in events:
        if e.event_type == "damage_roll":
            return e.payload.get("damage_total", 0)
    return 0


def _get_base_damage(events) -> int:
    """Extract base_damage (pre-multiplier) from damage_roll event."""
    for e in events:
        if e.event_type == "damage_roll":
            return e.payload.get("base_damage", 0)
    return 0


# ---------------------------------------------------------------------------
# WSP-001: weapon_specialization_one-handed + matching weapon → +2 damage
# ---------------------------------------------------------------------------

def test_wsp001_one_handed_wsp_adds_two_damage():
    """WSP-001: weapon_specialization_one-handed + one-handed weapon → damage total +2 vs baseline."""
    a_with = _attacker(feats=["weapon_specialization_one-handed"], str_mod=0)
    a_without = _attacker(eid="fighter2", feats=[], str_mod=0)
    t = _target()

    ws_with = _world(a_with, t)
    ws_without = _world(a_without, t)

    events_with = resolve_attack(_intent("fighter", "goblin", ONE_HANDED_WEAPON), ws_with, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)
    events_without = resolve_attack(_intent("fighter2", "goblin", ONE_HANDED_WEAPON), ws_without, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)

    dmg_with = _get_damage_total(events_with)
    dmg_without = _get_damage_total(events_without)

    assert dmg_with == dmg_without + 2, (
        f"weapon_specialization_one-handed should add +2 to damage; "
        f"got {dmg_with} (with WSP) vs {dmg_without} (without WSP)"
    )


# ---------------------------------------------------------------------------
# WSP-002: weapon_specialization_one-handed + two-handed weapon → no bonus
# ---------------------------------------------------------------------------

def test_wsp002_type_mismatch_no_bonus():
    """WSP-002: weapon_specialization_one-handed but using two-handed weapon → no WSP bonus."""
    a_mismatch = _attacker(feats=["weapon_specialization_one-handed"], str_mod=0)
    a_baseline = _attacker(eid="fighter2", feats=[], str_mod=0)
    t = _target()

    ws_mismatch = _world(a_mismatch, t)
    ws_baseline = _world(a_baseline, t)

    events_mismatch = resolve_attack(_intent("fighter", "goblin", TWO_HANDED_WEAPON), ws_mismatch, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)
    events_baseline = resolve_attack(_intent("fighter2", "goblin", TWO_HANDED_WEAPON), ws_baseline, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)

    dmg_mismatch = _get_damage_total(events_mismatch)
    dmg_baseline = _get_damage_total(events_baseline)

    assert dmg_mismatch == dmg_baseline, (
        f"weapon_specialization_one-handed should NOT apply to two-handed weapon; "
        f"got {dmg_mismatch} (mismatch) vs {dmg_baseline} (baseline)"
    )


# ---------------------------------------------------------------------------
# WSP-003: Full attack — all hits get +2 damage
# ---------------------------------------------------------------------------

def test_wsp003_full_attack_all_hits_get_bonus():
    """WSP-003: Full attack with weapon_specialization_one-handed → all hits have +2 damage."""
    a = _attacker(feats=["weapon_specialization_one-handed"], str_mod=0, bab=11)
    t = _target(hp=200, ac=5)  # Low AC to ensure hits; high HP to survive multiple attacks
    ws = _world(a, t)

    fa_intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        weapon=ONE_HANDED_WEAPON,
        base_attack_bonus=11,
        power_attack_penalty=0,
    )

    # d20=15 → all iteratives hit AC5; damage=3 → damage_total=3+2=5 per hit with WSP
    events_with = resolve_full_attack(fa_intent, ws, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)

    a_no = _attacker(eid="fighter2", feats=[], str_mod=0, bab=11)
    ws_no = _world(a_no, t)
    fa_no = FullAttackIntent(
        attacker_id="fighter2",
        target_id="goblin",
        weapon=ONE_HANDED_WEAPON,
        base_attack_bonus=11,
        power_attack_penalty=0,
    )
    events_no = resolve_full_attack(fa_no, ws_no, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)

    damage_with = [e.payload.get("damage_total", 0) for e in events_with if e.event_type == "damage_roll"]
    damage_no = [e.payload.get("damage_total", 0) for e in events_no if e.event_type == "damage_roll"]

    assert len(damage_with) >= 1 and len(damage_with) == len(damage_no), (
        f"Should have same hit count; got {damage_with} vs {damage_no}"
    )
    for i, (dw, dn) in enumerate(zip(damage_with, damage_no)):
        assert dw == dn + 2, (
            f"Hit {i}: WSP should give +2 damage; got {dw} vs {dn}"
        )


# ---------------------------------------------------------------------------
# WSP-004: Crit: +2 bonus is multiplied (pre-crit site)
# ---------------------------------------------------------------------------

def test_wsp004_crit_multiplies_wsp_bonus():
    """WSP-004: Weapon Specialization +2 is pre-crit (multiplied by crit multiplier).

    With crit_mult=2: (base_dice + wsp_bonus) × 2.
    Baseline without WSP: base_dice × 2.
    Delta = wsp_bonus × 2 = 4.
    """
    # STR=0 so damage is only dice roll + WSP
    a_with = _attacker(feats=["weapon_specialization_one-handed"], str_mod=0)
    a_without = _attacker(eid="fighter2", feats=[], str_mod=0)
    t = _target()

    ws_with = _world(a_with, t)
    ws_without = _world(a_without, t)

    # d20=20 (natural 20 → threat), confirm=15 → hits AC10 (confirm total = 15+10=25 ≥ 10); damage=3
    events_with = resolve_attack(_intent("fighter", "goblin", CRIT_WEAPON), ws_with, _rng_crit(20, 15, 3), next_event_id=0, timestamp=0.0)
    events_without = resolve_attack(_intent("fighter2", "goblin", CRIT_WEAPON), ws_without, _rng_crit(20, 15, 3), next_event_id=0, timestamp=0.0)

    # Verify crits fired in both
    crit_with = any(e.event_type == "attack_roll" and e.payload.get("is_critical") for e in events_with)
    crit_without = any(e.event_type == "attack_roll" and e.payload.get("is_critical") for e in events_without)
    assert crit_with and crit_without, "Both should have confirmed crits"

    dmg_with = _get_damage_total(events_with)
    dmg_without = _get_damage_total(events_without)

    # Expected delta: wsp_bonus × crit_mult = 2 × 2 = 4
    assert dmg_with == dmg_without + 4, (
        f"On crit (×2), WSP +2 bonus should contribute +4 total; "
        f"got {dmg_with} (with WSP) vs {dmg_without} (without WSP)"
    )


# ---------------------------------------------------------------------------
# WSP-005: WF + WSP on same type → +1 attack AND +2 damage (both active)
# ---------------------------------------------------------------------------

def test_wsp005_wf_and_wsp_stack():
    """WSP-005: weapon_focus_one-handed + weapon_specialization_one-handed → +1 attack AND +2 damage."""
    a_both = _attacker(feats=["weapon_focus_one-handed", "weapon_specialization_one-handed"], str_mod=0)
    a_neither = _attacker(eid="fighter2", feats=[], str_mod=0)
    t = _target()

    ws_both = _world(a_both, t)
    ws_neither = _world(a_neither, t)

    events_both = resolve_attack(_intent("fighter", "goblin", ONE_HANDED_WEAPON, attack_bonus=5), ws_both, _rng_hit(10, 3), next_event_id=0, timestamp=0.0)
    events_neither = resolve_attack(_intent("fighter2", "goblin", ONE_HANDED_WEAPON, attack_bonus=5), ws_neither, _rng_hit(10, 3), next_event_id=0, timestamp=0.0)

    atk_both = next((e.payload["total"] for e in events_both if e.event_type == "attack_roll"), None)
    atk_neither = next((e.payload["total"] for e in events_neither if e.event_type == "attack_roll"), None)
    assert atk_both == atk_neither + 1, (
        f"WF should add +1 to attack; got {atk_both} vs {atk_neither}"
    )

    dmg_both = _get_damage_total(events_both)
    dmg_neither = _get_damage_total(events_neither)
    assert dmg_both == dmg_neither + 2, (
        f"WSP should add +2 to damage; got {dmg_both} vs {dmg_neither}"
    )


# ---------------------------------------------------------------------------
# WSP-006: No WSP feat → no damage bonus (regression guard)
# ---------------------------------------------------------------------------

def test_wsp006_no_feat_no_bonus():
    """WSP-006: Attacker without weapon_specialization feat → damage unchanged (regression guard)."""
    a = _attacker(feats=[])
    t = _target()
    ws = _world(a, t)

    events = resolve_attack(_intent("fighter", "goblin", ONE_HANDED_WEAPON), ws, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)

    # Verify no WSP bonus by checking there's no extra damage (no WSP event pattern to check)
    # Instead: check that the damage total matches expected base (dice=3 + STR=2 = 5)
    dmg = _get_damage_total(events)
    # dice=3 + str_mod=2 = 5 base damage
    assert dmg == 5, (
        f"No WSP feat → damage should be 3 (dice) + 2 (STR) = 5; got {dmg}"
    )


# ---------------------------------------------------------------------------
# WSP-007: weapon_specialization_two-handed → +2 damage with two-handed weapon
# ---------------------------------------------------------------------------

def test_wsp007_two_handed_specialization():
    """WSP-007: weapon_specialization_two-handed + two-handed weapon → +2 damage."""
    a_with = _attacker(feats=["weapon_specialization_two-handed"], str_mod=0)
    a_without = _attacker(eid="fighter2", feats=[], str_mod=0)
    t = _target()

    ws_with = _world(a_with, t)
    ws_without = _world(a_without, t)

    events_with = resolve_attack(_intent("fighter", "goblin", TWO_HANDED_WEAPON), ws_with, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)
    events_without = resolve_attack(_intent("fighter2", "goblin", TWO_HANDED_WEAPON), ws_without, _rng_hit(15, 3), next_event_id=0, timestamp=0.0)

    dmg_with = _get_damage_total(events_with)
    dmg_without = _get_damage_total(events_without)

    assert dmg_with == dmg_without + 2, (
        f"weapon_specialization_two-handed should add +2 to two-handed damage; "
        f"got {dmg_with} vs {dmg_without}"
    )


# ---------------------------------------------------------------------------
# WSP-008: WFC regression guard — Weapon Focus +1 attack still applies after WSP commit
# ---------------------------------------------------------------------------

def test_wsp008_wfc_regression_weapon_focus_unaffected():
    """WSP-008: After WSP, Weapon Focus +1 attack still correctly fires (WO3 unaffected)."""
    a_wf = _attacker(feats=["weapon_focus_one-handed"])
    a_baseline = _attacker(eid="fighter2", feats=[])
    t = _target()

    ws_wf = _world(a_wf, t)
    ws_baseline = _world(a_baseline, t)

    events_wf = resolve_attack(_intent("fighter", "goblin", ONE_HANDED_WEAPON, attack_bonus=5), ws_wf, _rng_hit(10, 3), next_event_id=0, timestamp=0.0)
    events_baseline = resolve_attack(_intent("fighter2", "goblin", ONE_HANDED_WEAPON, attack_bonus=5), ws_baseline, _rng_hit(10, 3), next_event_id=0, timestamp=0.0)

    atk_wf = next((e.payload["total"] for e in events_wf if e.event_type == "attack_roll"), None)
    atk_baseline = next((e.payload["total"] for e in events_baseline if e.event_type == "attack_roll"), None)

    assert atk_wf == atk_baseline + 1, (
        f"WFC regression: weapon_focus_one-handed should still give +1 attack after WSP commit; "
        f"got {atk_wf} vs {atk_baseline}"
    )

    # Also verify weapon_focus_active event still fires
    wf_events = [e for e in events_wf if e.event_type == "weapon_focus_active"]
    assert len(wf_events) >= 1, (
        "weapon_focus_active event should still be emitted; WO3 must be unaffected by WO4"
    )
