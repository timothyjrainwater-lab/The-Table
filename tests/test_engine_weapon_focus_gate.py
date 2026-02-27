"""Gate tests: ENGINE-WEAPON-FOCUS — WO-ENGINE-WEAPON-FOCUS-001.

Tests:
WFC-001: weapon_focus_light + light weapon → +1 to attack roll total
WFC-002: weapon_focus_one-handed + two-handed weapon → no bonus (type mismatch)
WFC-003: Full attack (FullAttackIntent) — iterative attacks get +1 (both resolvers covered)
WFC-004: weapon_focus_two-handed → +1 with two-handed weapon
WFC-005: weapon_focus_ranged → +1 with ranged weapon
WFC-006: No Weapon Focus feat → no attack bonus (regression guard)
WFC-007: weapon_focus_natural → +1 with natural attacks
WFC-008: weapon_focus_active event emitted in attack sequence when feat active

Insertion sites:
  attack_resolver.py: _wf_bonus before attack_bonus_with_conditions, event emitted
  full_attack_resolver.py: _wf_bonus before adjusted_attack_bonus per iterative attack
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

LIGHT_WEAPON = Weapon(
    damage_dice="1d6",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=20,
    is_two_handed=False,
    grip="one-handed",
    weapon_type="light",
    range_increment=0,
    enhancement_bonus=0,
)

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

RANGED_WEAPON = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="piercing",
    critical_multiplier=3,
    critical_range=20,
    is_two_handed=True,
    grip="two-handed",
    weapon_type="ranged",
    range_increment=30,
    enhancement_bonus=0,
)

NATURAL_WEAPON = Weapon(
    damage_dice="1d6",
    damage_bonus=0,
    damage_type="piercing",
    critical_multiplier=2,
    critical_range=20,
    is_two_handed=False,
    grip="one-handed",
    weapon_type="natural",
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
    weapon_override: dict = None,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 15,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
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
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {"fighter": 5},
        EF.WEAPON: weapon_override or {"enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
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


def _rng(attack_roll: int = 15, damage_roll: int = 3):
    stream = mock.MagicMock()
    stream.randint.side_effect = [attack_roll, damage_roll] + [damage_roll] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _intent(
    attacker_id: str,
    target_id: str,
    weapon: Weapon,
    attack_bonus: int = 5,
) -> AttackIntent:
    return AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        attack_bonus=attack_bonus,
        weapon=weapon,
        power_attack_penalty=0,
    )


def _get_attack_total(events) -> int:
    """Extract total (d20 + bonus) from attack_roll event."""
    for e in events:
        if e.event_type == "attack_roll":
            return e.payload["total"]
    return None


# ---------------------------------------------------------------------------
# WFC-001: weapon_focus_light + light weapon → +1 attack total
# ---------------------------------------------------------------------------

def test_wfc001_light_weapon_focus_adds_one_attack():
    """WFC-001: weapon_focus_light feat + light weapon → attack total +1 vs no-feat baseline."""
    a_with = _attacker(feats=["weapon_focus_light"])
    a_without = _attacker(eid="fighter2", feats=[])
    t = _target()

    ws_with = _world(a_with, t)
    ws_without = _world(a_without, t)

    # Same d20=15 for both
    events_with = resolve_attack(_intent("fighter", "goblin", LIGHT_WEAPON), ws_with, _rng(15, 3), next_event_id=0, timestamp=0.0)
    events_without = resolve_attack(_intent("fighter2", "goblin", LIGHT_WEAPON), ws_without, _rng(15, 3), next_event_id=0, timestamp=0.0)

    total_with = _get_attack_total(events_with)
    total_without = _get_attack_total(events_without)

    assert total_with == total_without + 1, (
        f"weapon_focus_light should add +1 to attack total; "
        f"got {total_with} (with WF) vs {total_without} (without WF)"
    )


# ---------------------------------------------------------------------------
# WFC-002: weapon_focus_one-handed + two-handed weapon → no bonus
# ---------------------------------------------------------------------------

def test_wfc002_type_mismatch_no_bonus():
    """WFC-002: weapon_focus_one-handed but using two-handed weapon → no WF bonus."""
    a_mismatch = _attacker(feats=["weapon_focus_one-handed"])
    a_baseline = _attacker(eid="fighter2", feats=[])
    t = _target()

    ws_mismatch = _world(a_mismatch, t)
    ws_baseline = _world(a_baseline, t)

    events_mismatch = resolve_attack(_intent("fighter", "goblin", TWO_HANDED_WEAPON), ws_mismatch, _rng(15, 3), next_event_id=0, timestamp=0.0)
    events_baseline = resolve_attack(_intent("fighter2", "goblin", TWO_HANDED_WEAPON), ws_baseline, _rng(15, 3), next_event_id=0, timestamp=0.0)

    total_mismatch = _get_attack_total(events_mismatch)
    total_baseline = _get_attack_total(events_baseline)

    assert total_mismatch == total_baseline, (
        f"weapon_focus_one-handed should NOT apply to two-handed weapon; "
        f"got {total_mismatch} (mismatch) vs {total_baseline} (baseline)"
    )


# ---------------------------------------------------------------------------
# WFC-003: Full attack — all iterative attacks get +1
# ---------------------------------------------------------------------------

def test_wfc003_full_attack_all_iteratives_get_bonus():
    """WFC-003: Full attack with weapon_focus_one-handed → all iterative attack totals +1."""
    a = _attacker(feats=["weapon_focus_one-handed"], bab=11)  # BAB 11 → 3 attacks
    t = _target(hp=100, ac=30)  # High AC to force misses so all iteratives run
    ws = _world(a, t)

    fa_intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        weapon=ONE_HANDED_WEAPON,
        base_attack_bonus=11,
        power_attack_penalty=0,
    )

    # d20=5 for all attacks → miss vs AC=30 regardless (5+bonus < 30), so all 3 run
    events_with = resolve_full_attack(fa_intent, ws, _rng(5, 3), next_event_id=0, timestamp=0.0)

    # Baseline: same setup, no feat
    a_no = _attacker(eid="fighter2", feats=[], bab=11)
    ws_no = _world(a_no, t)
    fa_no = FullAttackIntent(
        attacker_id="fighter2",
        target_id="goblin",
        weapon=ONE_HANDED_WEAPON,
        base_attack_bonus=11,
        power_attack_penalty=0,
    )
    events_no = resolve_full_attack(fa_no, ws_no, _rng(5, 3), next_event_id=0, timestamp=0.0)

    atk_with = [e.payload["total"] for e in events_with if e.event_type == "attack_roll"]
    atk_no = [e.payload["total"] for e in events_no if e.event_type == "attack_roll"]

    assert len(atk_with) == len(atk_no) >= 2, f"Should have same iterative count; got {atk_with} vs {atk_no}"
    for i, (tw, tn) in enumerate(zip(atk_with, atk_no)):
        assert tw == tn + 1, (
            f"Attack {i}: WF should give +1; got {tw} vs {tn}"
        )


# ---------------------------------------------------------------------------
# WFC-004: weapon_focus_two-handed → +1 with two-handed weapon
# ---------------------------------------------------------------------------

def test_wfc004_two_handed_weapon_focus():
    """WFC-004: weapon_focus_two-handed + two-handed weapon → +1 attack."""
    a_with = _attacker(feats=["weapon_focus_two-handed"])
    a_without = _attacker(eid="fighter2", feats=[])
    t = _target()

    ws_with = _world(a_with, t)
    ws_without = _world(a_without, t)

    events_with = resolve_attack(_intent("fighter", "goblin", TWO_HANDED_WEAPON), ws_with, _rng(15, 3), next_event_id=0, timestamp=0.0)
    events_without = resolve_attack(_intent("fighter2", "goblin", TWO_HANDED_WEAPON), ws_without, _rng(15, 3), next_event_id=0, timestamp=0.0)

    assert _get_attack_total(events_with) == _get_attack_total(events_without) + 1, (
        "weapon_focus_two-handed should add +1 to two-handed attack total"
    )


# ---------------------------------------------------------------------------
# WFC-005: weapon_focus_ranged → +1 with ranged weapon
# ---------------------------------------------------------------------------

def test_wfc005_ranged_weapon_focus():
    """WFC-005: weapon_focus_ranged + ranged weapon → +1 attack."""
    a_with = _attacker(feats=["weapon_focus_ranged"])
    a_without = _attacker(eid="fighter2", feats=[])
    # Target is same tile — close range, no range penalty
    t = _target()

    ws_with = _world(a_with, t)
    ws_without = _world(a_without, t)

    events_with = resolve_attack(_intent("fighter", "goblin", RANGED_WEAPON), ws_with, _rng(15, 3), next_event_id=0, timestamp=0.0)
    events_without = resolve_attack(_intent("fighter2", "goblin", RANGED_WEAPON), ws_without, _rng(15, 3), next_event_id=0, timestamp=0.0)

    assert _get_attack_total(events_with) == _get_attack_total(events_without) + 1, (
        "weapon_focus_ranged should add +1 to ranged attack total"
    )


# ---------------------------------------------------------------------------
# WFC-006: No Weapon Focus feat → no attack bonus (regression guard)
# ---------------------------------------------------------------------------

def test_wfc006_no_feat_no_bonus():
    """WFC-006: Attacker without any weapon_focus feat → attack total unmodified."""
    a = _attacker(feats=[])  # No WF feat
    t = _target()
    ws = _world(a, t)

    events = resolve_attack(_intent("fighter", "goblin", ONE_HANDED_WEAPON, attack_bonus=5), ws, _rng(15, 3), next_event_id=0, timestamp=0.0)

    total = _get_attack_total(events)
    # d20=15 + BAB5 + STR2 (included in intent.attack_bonus=5) = 20 (no WF)
    # We check no weapon_focus_active event fired
    wf_events = [e for e in events if e.event_type == "weapon_focus_active"]
    assert len(wf_events) == 0, (
        f"No weapon_focus feat → no weapon_focus_active event; got: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# WFC-007: weapon_focus_natural → +1 with natural attacks
# ---------------------------------------------------------------------------

def test_wfc007_natural_weapon_focus():
    """WFC-007: weapon_focus_natural + natural weapon → +1 attack."""
    a_with = _attacker(feats=["weapon_focus_natural"])
    a_without = _attacker(eid="fighter2", feats=[])
    t = _target()

    ws_with = _world(a_with, t)
    ws_without = _world(a_without, t)

    events_with = resolve_attack(_intent("fighter", "goblin", NATURAL_WEAPON), ws_with, _rng(15, 3), next_event_id=0, timestamp=0.0)
    events_without = resolve_attack(_intent("fighter2", "goblin", NATURAL_WEAPON), ws_without, _rng(15, 3), next_event_id=0, timestamp=0.0)

    assert _get_attack_total(events_with) == _get_attack_total(events_without) + 1, (
        "weapon_focus_natural should add +1 to natural attack total"
    )


# ---------------------------------------------------------------------------
# WFC-008: weapon_focus_active event emitted when feat active
# ---------------------------------------------------------------------------

def test_wfc008_event_emitted_when_feat_active():
    """WFC-008: weapon_focus_active event emitted in attack sequence when feat is active."""
    a = _attacker(feats=["weapon_focus_light"])
    t = _target()
    ws = _world(a, t)

    events = resolve_attack(_intent("fighter", "goblin", LIGHT_WEAPON), ws, _rng(15, 3), next_event_id=0, timestamp=0.0)

    wf_events = [e for e in events if e.event_type == "weapon_focus_active"]
    assert len(wf_events) >= 1, (
        f"weapon_focus_active event should fire when feat active; got: {[e.event_type for e in events]}"
    )
    assert wf_events[0].payload.get("weapon_type") == "light", (
        f"Event payload should include weapon_type='light'; got: {wf_events[0].payload}"
    )
