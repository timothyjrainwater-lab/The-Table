# Gate tests: ENGINE-UNCANNY-DODGE -- WO-ENGINE-UNCANNY-DODGE-001
# PHB p.51 Rogue, p.47 Ranger, p.26 Barbarian
# Retain DEX bonus to AC when flat-footed.
# Exception: immobilized conditions still deny DEX.

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.attack_resolver import resolve_attack
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.conditions import ConditionType
from aidm.schemas.entity_fields import EF


def _weapon():
    return Weapon(
        damage_dice="1d6", damage_bonus=0, damage_type="slashing",
        critical_multiplier=2, critical_range=20, is_two_handed=False,
        grip="one-handed", weapon_type="one-handed",
        range_increment=0, enhancement_bonus=0,
    )

def _attacker(eid="attacker"):
    return {
        EF.ENTITY_ID: eid, EF.TEAM: "monsters",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: 10,
        EF.ATTACK_BONUS: 5, EF.BAB: 5, EF.STR_MOD: 2, EF.DEX_MOD: 0,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0}, EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False, EF.FAVORED_ENEMIES: [],
        EF.WEAPON: {"enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
        EF.CLASS_LEVELS: {},
    }


def _target(eid="defender", dex_mod=3, ac=10, class_levels=None, conditions=None):
    return {
        EF.ENTITY_ID: eid, EF.TEAM: "party",
        EF.HP_CURRENT: 40, EF.HP_MAX: 40, EF.AC: ac, EF.DEX_MOD: dex_mod,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: [], EF.POSITION: {"x": 1, "y": 0}, EF.SIZE_CATEGORY: "medium",
        EF.DAMAGE_REDUCTIONS: [], EF.SAVE_FORT: 3, EF.CON_MOD: 1,
        EF.CREATURE_TYPE: "humanoid", EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.CLASS_LEVELS: class_levels if class_levels is not None else {},
    }

def _flat_footed_cond():
    return {
        "condition_type": ConditionType.FLAT_FOOTED.value, "source": "combat_start",
        "modifiers": {
            "ac_modifier": 0, "ac_modifier_melee": 0, "ac_modifier_ranged": 0,
            "attack_modifier": 0, "damage_modifier": 0, "dex_modifier": 0,
            "fort_save_modifier": 0, "ref_save_modifier": 0, "will_save_modifier": 0,
            "movement_prohibited": False, "actions_prohibited": False,
            "standing_triggers_aoo": False, "auto_hit_if_helpless": False,
            "loses_dex_to_ac": True,
        },
        "applied_at_event_id": 0, "duration_rounds": None,
        "notes": "Flat-footed: loses Dex bonus to AC",
    }


def _paralyzed_cond():
    return {
        "condition_type": ConditionType.PARALYZED.value, "source": "spell",
        "modifiers": {
            "ac_modifier": 0, "ac_modifier_melee": 0, "ac_modifier_ranged": 0,
            "attack_modifier": 0, "damage_modifier": 0, "dex_modifier": 0,
            "fort_save_modifier": 0, "ref_save_modifier": 0, "will_save_modifier": 0,
            "movement_prohibited": True, "actions_prohibited": True,
            "standing_triggers_aoo": False, "auto_hit_if_helpless": True,
            "loses_dex_to_ac": True,
        },
        "applied_at_event_id": 0, "duration_rounds": None,
        "notes": "Paralyzed: loses Dex to AC, auto-hit for melee",
    }

def _world(attacker, target):
    return WorldState(
        ruleset_version="3.5e",
        entities={attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target},
        active_combat={
            "initiative_order": [attacker[EF.ENTITY_ID], target[EF.ENTITY_ID]],
            "aoo_used_this_round": [], "flat_footed_actors": [], "feint_flat_footed": [],
        },
    )


def _rng(attack_roll=15, damage_roll=3):
    stream = mock.MagicMock()
    stream.randint.side_effect = [attack_roll, damage_roll] + [damage_roll] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _intent(attacker_id="attacker", target_id="defender"):
    return AttackIntent(
        attacker_id=attacker_id, target_id=target_id,
        attack_bonus=5, weapon=_weapon(), power_attack_penalty=0,
    )


def _dex_penalty(events):
    for e in events:
        if e.event_type == "attack_roll":
            return e.payload.get("dex_penalty", 0)
    return 0

# UD-001: Rogue 2 flat-footed -> retains DEX
def test_ud001_rogue_lv2_flat_footed_retains_dex():
    t = _target(dex_mod=3, class_levels={"rogue": 2},
                conditions={"flat_footed": _flat_footed_cond()})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == 0, "UD-001: Rogue2 flat-footed should retain DEX, got %d" % p


# UD-002: Rogue 1 flat-footed -> DEX denied
def test_ud002_rogue_lv1_flat_footed_denies_dex():
    t = _target(dex_mod=3, class_levels={"rogue": 1},
                conditions={"flat_footed": _flat_footed_cond()})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == -3, "UD-002: Rogue1 flat-footed should lose DEX (-3), got %d" % p


# UD-003: Ranger 4 flat-footed -> retains DEX
def test_ud003_ranger_lv4_flat_footed_retains_dex():
    t = _target(dex_mod=4, class_levels={"ranger": 4},
                conditions={"flat_footed": _flat_footed_cond()})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == 0, "UD-003: Ranger4 flat-footed should retain DEX, got %d" % p


# UD-004: Ranger 3 flat-footed -> DEX denied
def test_ud004_ranger_lv3_flat_footed_denies_dex():
    t = _target(dex_mod=4, class_levels={"ranger": 3},
                conditions={"flat_footed": _flat_footed_cond()})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == -4, "UD-004: Ranger3 flat-footed should lose DEX (-4), got %d" % p

# UD-005: Barbarian 2 flat-footed -> retains DEX
def test_ud005_barbarian_lv2_flat_footed_retains_dex():
    t = _target(dex_mod=2, class_levels={"barbarian": 2},
                conditions={"flat_footed": _flat_footed_cond()})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == 0, "UD-005: Barb2 flat-footed should retain DEX, got %d" % p


# UD-006: Wizard flat-footed -> DEX denied (regression)
def test_ud006_wizard_flat_footed_denies_dex():
    t = _target(dex_mod=2, class_levels={"wizard": 5},
                conditions={"flat_footed": _flat_footed_cond()})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == -2, "UD-006: Wizard flat-footed should lose DEX (-2), got %d" % p


# UD-007: Rogue 2 paralyzed -> DEX still denied (immobilized exception)
def test_ud007_rogue_lv2_paralyzed_denies_dex():
    t = _target(dex_mod=3, class_levels={"rogue": 2},
                conditions={"paralyzed": _paralyzed_cond()})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == -3, "UD-007: Rogue2 paralyzed should still lose DEX (-3), got %d" % p


# UD-008: Rogue 2 not flat-footed -> DEX normal
def test_ud008_rogue_lv2_not_flat_footed_dex_normal():
    t = _target(dex_mod=3, class_levels={"rogue": 2}, conditions={})
    events = resolve_attack(_intent(), _world(_attacker(), t), _rng(15), 0, 0.0)
    p = _dex_penalty(events)
    assert p == 0, "UD-008: Rogue2 not flat-footed should have dex_penalty=0, got %d" % p
