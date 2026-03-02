"""Gate tests for WO-ENGINE-MANYSHOT-CONDITION-BLIND-001.

MCB-001..008 — get_condition_modifiers() wired into resolve_manyshot.
PHB p.97: Manyshot is a ranged attack action — all standard attack modifiers apply.
Pre-fix: resolve_manyshot read raw EF.ATTACK_BONUS + EF.AC, silently skipping conditions.
"""
import unittest.mock as mock

import pytest

from aidm.core.attack_resolver import resolve_manyshot, resolve_attack
from aidm.core.state import WorldState
from aidm.schemas.intents import ManyShotIntent
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers (adapted from test_engine_manyshot_gate.py)
# ---------------------------------------------------------------------------

def _ranged_weapon():
    return {
        "damage_dice": "1d8", "damage_bonus": 0, "damage_type": "piercing",
        "critical_multiplier": 3, "critical_range": 20,
        "weapon_type": "ranged", "range_increment": 60, "enhancement_bonus": 0,
    }


def _attacker(eid="archer", bab=6, conditions=None) -> dict:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50,
        EF.AC: 14,
        EF.ATTACK_BONUS: bab, EF.BAB: bab,
        EF.STR_MOD: 1, EF.DEX_MOD: 2,
        EF.DEFEATED: False, EF.DYING: False,
        EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: ["manyshot"],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FAVORED_ENEMIES: [],
        EF.DAMAGE_REDUCTIONS: [],
        EF.WEAPON: {"enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
        EF.ARMOR_TYPE: "none",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.NEGATIVE_LEVELS: 0,
    }


def _target(eid="goblin", hp=100, ac=5, dex_mod=2, conditions=None) -> dict:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp, EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEX_MOD: dex_mod,
        EF.DEFEATED: False, EF.DYING: False,
        EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.SAVE_FORT: 3, EF.CON_MOD: 2,
        EF.CREATURE_TYPE: "humanoid",
        EF.DAMAGE_REDUCTIONS: [],
        EF.ARMOR_TYPE: "none",
        EF.ARMOR_AC_BONUS: 0,
        EF.CLASS_LEVELS: {},
    }


def _world(attacker, target) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target},
        active_combat={
            "initiative_order": [attacker[EF.ENTITY_ID], target[EF.ENTITY_ID]],
            "deflect_arrows_used": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "cleave_used_this_turn": set(),
        },
    )


def _rng(d20=15, damage=4) -> mock.MagicMock:
    stream = mock.MagicMock()
    stream.randint.side_effect = [d20] + [damage] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _roll_event(events):
    return next((e for e in events if e.event_type == "attack_roll"), None)


# ---------------------------------------------------------------------------
# MCB-001: No conditions — result matches raw EF.ATTACK_BONUS (baseline)
# ---------------------------------------------------------------------------
def test_mcb_001_no_conditions_baseline():
    bab = 6
    a = _attacker(bab=bab)
    t = _target(ac=1)  # low AC → guaranteed hit
    ws = _world(a, t)
    intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                            weapon=_ranged_weapon(), within_30_feet=True)
    events = resolve_manyshot(intent, ws, _rng(d20=15), next_event_id=0, timestamp=0.0)
    ev = _roll_event(events)
    assert ev is not None, "Expected attack_roll event"
    # No conditions → attack_bonus = bab + manyshot_penalty(-4) = 6 + (-4) = 2
    assert ev.payload["attack_bonus"] == bab - 4, (
        f"Baseline: attack_bonus should be {bab - 4}, got {ev.payload['attack_bonus']}"
    )


# ---------------------------------------------------------------------------
# MCB-002: Attacker shaken → Manyshot attack roll has -2 applied (PHB p.309)
# ---------------------------------------------------------------------------
def test_mcb_002_shaken_attacker_minus2():
    bab = 6
    # shaken condition: attack_modifier = -2
    a = _attacker(bab=bab, conditions={"shaken": {}})
    t = _target(ac=1)
    ws = _world(a, t)
    intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                            weapon=_ranged_weapon(), within_30_feet=True)
    events = resolve_manyshot(intent, ws, _rng(d20=15), next_event_id=0, timestamp=0.0)
    ev = _roll_event(events)
    assert ev is not None, "Expected attack_roll event"
    # attack_bonus = bab + manyshot_penalty(-4) + shaken_penalty(-2) = 6 - 4 - 2 = 0
    expected = bab - 4 - 2
    assert ev.payload["attack_bonus"] == expected, (
        f"Shaken attacker: attack_bonus should be {expected} (bab-4-2), "
        f"got {ev.payload['attack_bonus']}"
    )


# ---------------------------------------------------------------------------
# MCB-003: Positive attack_modifier applied — proves additive wiring
# (Flanking +2 not implemented as a condition type; inject via mock to test wiring)
# ---------------------------------------------------------------------------
def test_mcb_003_positive_attack_modifier_applied():
    bab = 6
    a = _attacker(bab=bab)
    t = _target(ac=1)
    ws = _world(a, t)
    intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                            weapon=_ranged_weapon(), within_30_feet=True)
    from aidm.schemas.conditions import ConditionModifiers
    flanking_mods = ConditionModifiers(attack_modifier=2)
    no_mods = ConditionModifiers()
    with mock.patch("aidm.core.attack_resolver.get_condition_modifiers",
                    side_effect=[flanking_mods, no_mods]):
        events = resolve_manyshot(intent, ws, _rng(d20=15), next_event_id=0, timestamp=0.0)
    ev = _roll_event(events)
    assert ev is not None, "Expected attack_roll event"
    # attack_bonus = bab + manyshot_penalty(-4) + mock_modifier(+2) = 6 - 4 + 2 = 4
    expected = bab - 4 + 2
    assert ev.payload["attack_bonus"] == expected, (
        f"Positive modifier: attack_bonus should be {expected} (bab-4+2), "
        f"got {ev.payload['attack_bonus']}"
    )


# ---------------------------------------------------------------------------
# MCB-004: Target flat-footed → effective AC drops (loses DEX bonus)
# ---------------------------------------------------------------------------
def test_mcb_004_flat_footed_target_ac_drops():
    bab = 6
    dex_mod = 3  # flat-footed loses this DEX bonus
    raw_ac = 15   # base AC
    a = _attacker(bab=bab)
    t = _target(ac=raw_ac, dex_mod=dex_mod,
                conditions={"flat_footed": {}})
    ws = _world(a, t)
    intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                            weapon=_ranged_weapon(), within_30_feet=True)
    # d20=20 → guaranteed hit even against high AC
    events = resolve_manyshot(intent, ws, _rng(d20=20), next_event_id=0, timestamp=0.0)
    ev = _roll_event(events)
    assert ev is not None, "Expected attack_roll event"
    # Flat-footed: loses DEX → effective_ac = raw_ac - dex_mod = 15 - 3 = 12
    effective_ac_expected = raw_ac - dex_mod
    assert ev.payload["target_ac"] == effective_ac_expected, (
        f"Flat-footed target: effective AC should be {effective_ac_expected} "
        f"(raw {raw_ac} - dex_mod {dex_mod}), got {ev.payload['target_ac']}"
    )


# ---------------------------------------------------------------------------
# MCB-005: Target stunned → AC drops (ac_modifier + loses DEX)
# (Stunned: ac_modifier=-2 + loses_dex_to_ac=True, PHB p.312)
# ---------------------------------------------------------------------------
def test_mcb_005_stunned_target_ac_drops():
    dex_mod = 2
    raw_ac = 12
    a = _attacker(bab=6)
    t = _target(ac=raw_ac, dex_mod=dex_mod,
                conditions={"stunned": {}})
    ws = _world(a, t)
    intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                            weapon=_ranged_weapon(), within_30_feet=True)
    events = resolve_manyshot(intent, ws, _rng(d20=20), next_event_id=0, timestamp=0.0)
    ev = _roll_event(events)
    assert ev is not None, "Expected attack_roll event"
    # Stunned: ac_modifier=-2 + loses_dex_to_ac → effective_ac = raw_ac - 2 - dex_mod
    expected_ac = raw_ac - 2 - dex_mod
    assert ev.payload["target_ac"] == expected_ac, (
        f"Stunned target: effective AC should be {expected_ac} "
        f"(raw {raw_ac} - ac_mod 2 - dex_mod {dex_mod}), got {ev.payload['target_ac']}"
    )


# ---------------------------------------------------------------------------
# MCB-006: Shaken attacker + flat-footed target → both deltas applied (canary)
# ---------------------------------------------------------------------------
def test_mcb_006_compound_shaken_attacker_flat_footed_target_canary():
    bab = 6
    dex_mod = 3
    raw_ac = 14
    a = _attacker(bab=bab, conditions={"shaken": {}})
    t = _target(ac=raw_ac, dex_mod=dex_mod,
                conditions={"flat_footed": {}})
    ws = _world(a, t)
    intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                            weapon=_ranged_weapon(), within_30_feet=True)
    events = resolve_manyshot(intent, ws, _rng(d20=15), next_event_id=0, timestamp=0.0)
    ev = _roll_event(events)
    assert ev is not None, "Expected attack_roll event"
    # Attacker: bab + (-4 manyshot) + (-2 shaken) = 6 - 6 = 0
    expected_bonus = bab - 4 - 2
    assert ev.payload["attack_bonus"] == expected_bonus, (
        f"MCB-006 CANARY: shaken attacker bonus should be {expected_bonus}, "
        f"got {ev.payload['attack_bonus']}"
    )
    # Target: flat-footed loses dex → effective_ac = raw_ac - dex_mod = 14 - 3 = 11
    expected_ac = raw_ac - dex_mod
    assert ev.payload["target_ac"] == expected_ac, (
        f"MCB-006 CANARY: flat-footed target AC should be {expected_ac} "
        f"(raw {raw_ac} - dex_mod {dex_mod}), got {ev.payload['target_ac']}"
    )


# ---------------------------------------------------------------------------
# MCB-007: Regression — resolve_attack still applies condition modifiers (parity)
# ---------------------------------------------------------------------------
def test_mcb_007_resolve_attack_condition_path_unaffected():
    from aidm.core.rng_manager import RNGManager
    bab = 6
    a = _attacker(bab=bab, conditions={"shaken": {}})
    t = _target(ac=1)
    # Add required fields for resolve_attack
    a[EF.DISARMED] = False
    a[EF.WEAPON_BROKEN] = False
    a[EF.INSPIRE_COURAGE_ACTIVE] = False
    a[EF.INSPIRE_COURAGE_BONUS] = 0
    a[EF.NEGATIVE_LEVELS] = 0
    t[EF.ARMOR_TYPE] = "none"
    t[EF.ARMOR_AC_BONUS] = 0
    t[EF.CLASS_LEVELS] = {}
    t[EF.CREATURE_TYPE] = "humanoid"
    ws = _world(a, t)
    ranged_weapon = Weapon(
        damage_dice="1d8", damage_bonus=0, damage_type="piercing",
        weapon_type="ranged", grip="one-handed", is_two_handed=False,
        range_increment=60, enhancement_bonus=0, critical_multiplier=3, critical_range=20,
    )
    intent = AttackIntent(attacker_id="archer", target_id="goblin",
                          attack_bonus=bab, weapon=ranged_weapon)
    events = resolve_attack(intent, ws, RNGManager(42), next_event_id=0, timestamp=0.0)
    roll_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(roll_events) >= 1, "resolve_attack must produce attack_roll event"
    ev = roll_events[0]
    # resolve_attack applies shaken -2 via condition_modifier field
    assert ev.payload.get("condition_modifier") == -2, (
        f"resolve_attack shaken modifier should be -2 in condition_modifier field, "
        f"got {ev.payload.get('condition_modifier')!r}"
    )


# ---------------------------------------------------------------------------
# MCB-008: Regression — no conditions → resolve_manyshot result identical to pre-fix
# ---------------------------------------------------------------------------
def test_mcb_008_no_conditions_no_spurious_delta():
    bab = 6
    raw_ac = 10
    a = _attacker(bab=bab)  # conditions={}
    t = _target(ac=raw_ac, dex_mod=0, conditions={})
    ws = _world(a, t)
    intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                            weapon=_ranged_weapon(), within_30_feet=True)
    events = resolve_manyshot(intent, ws, _rng(d20=15), next_event_id=0, timestamp=0.0)
    ev = _roll_event(events)
    assert ev is not None, "Expected attack_roll event"
    # No conditions → no delta introduced
    assert ev.payload["attack_bonus"] == bab - 4, (
        f"No conditions: attack_bonus should be exactly {bab - 4}, got {ev.payload['attack_bonus']}"
    )
    assert ev.payload["target_ac"] == raw_ac, (
        f"No conditions: target_ac should be exactly {raw_ac}, got {ev.payload['target_ac']}"
    )
