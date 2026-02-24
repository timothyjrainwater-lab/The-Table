"""ENGINE-NATURAL-ATTACK Gate — Natural Attack Resolution v1 (10 tests).

Gate: ENGINE-NATURAL-ATTACK
Tests: NA-01 through NA-10
WO: WO-ENGINE-NATURAL-ATTACK-001
"""

import pytest
from copy import deepcopy
from unittest import mock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import Weapon
from aidm.schemas.intents import NaturalAttackIntent, WildShapeIntent
from aidm.core.natural_attack_resolver import (
    validate_natural_attack,
    resolve_natural_attack,
    _build_weapon_from_natural_attack,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WOLF_ATTACKS = [{"name": "bite", "damage": "1d6", "damage_type": "piercing"}]
BEAR_ATTACKS = [
    {"name": "claw", "damage": "1d4", "damage_type": "slashing"},
    {"name": "bite", "damage": "1d6", "damage_type": "piercing"},
]


def _druid_wolf(eid="druid"):
    """Druid already transformed into wolf form."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 1,
        EF.DEX_MOD: 2,
        EF.CON_MOD: 2,
        EF.BAB: 2,
        EF.ATTACK_BONUS: 3,
        EF.CLASS_LEVELS: {"druid": 5},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.WILD_SHAPE_ACTIVE: True,
        EF.WILD_SHAPE_FORM: "wolf",
        EF.WILD_SHAPE_USES_REMAINING: 0,
        EF.WILD_SHAPE_SAVED_STATS: {"str_mod": 1, "dex_mod": 2, "con_mod": 2, "ac": 14},
        EF.WILD_SHAPE_HOURS_REMAINING: 5,
        EF.EQUIPMENT_MELDED: True,
        EF.NATURAL_ATTACKS: WOLF_ATTACKS,
        EF.SIZE_CATEGORY: "medium",
    }


def _druid_bear(eid="druid"):
    """Druid transformed into black bear."""
    e = _druid_wolf(eid)
    e[EF.WILD_SHAPE_FORM] = "black_bear"
    e[EF.NATURAL_ATTACKS] = BEAR_ATTACKS
    return e


def _goblin(eid="goblin"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 15,
        EF.HP_MAX: 15,
        EF.AC: 13,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 1, "y": 0},
    }


def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "cleave_used_this_turn": set(),
        },
    )


def _mock_rng(rolls):
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [10] * 200
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ===========================================================================
# NA-01: Bite attack emits attack_roll event
# ===========================================================================

def test_na01_bite_emits_attack_roll():
    """NA-01: resolve_natural_attack emits attack_roll event for wolf bite."""
    druid = _druid_wolf()
    goblin = _goblin()
    ws = _world({"druid": druid, "goblin": goblin})
    intent = NaturalAttackIntent(
        attacker_id="druid",
        target_id="goblin",
        attack_name="bite",
        attack_bonus=3,
    )
    rng = _mock_rng([15, 4])  # d20=15 (hit), damage=4

    events, _ = resolve_natural_attack(intent, ws, rng, 0, 0.0)

    evt_types = [e.event_type for e in events]
    assert "attack_roll" in evt_types, f"Expected attack_roll, got {evt_types}"


# ===========================================================================
# NA-02: Hit produces damage_roll and hp_changed
# ===========================================================================

def test_na02_hit_produces_damage_and_hp():
    """NA-02: A hitting natural attack emits damage_roll and hp_changed."""
    druid = _druid_wolf()
    goblin = _goblin()
    ws = _world({"druid": druid, "goblin": goblin})
    intent = NaturalAttackIntent(
        attacker_id="druid",
        target_id="goblin",
        attack_name="bite",
        attack_bonus=10,  # guaranteed hit
    )
    rng = _mock_rng([15, 4])

    events, _ = resolve_natural_attack(intent, ws, rng, 0, 0.0)

    evt_types = [e.event_type for e in events]
    assert "damage_roll" in evt_types, f"Expected damage_roll, got {evt_types}"
    assert "hp_changed" in evt_types, f"Expected hp_changed, got {evt_types}"


# ===========================================================================
# NA-03: EQUIPMENT_MELDED does NOT block natural attacks
# ===========================================================================

def test_na03_equipment_melded_does_not_block():
    """NA-03: Natural attack succeeds even when EQUIPMENT_MELDED=True."""
    druid = _druid_wolf()
    assert druid[EF.EQUIPMENT_MELDED] is True  # confirm precondition
    goblin = _goblin()
    ws = _world({"druid": druid, "goblin": goblin})
    intent = NaturalAttackIntent(
        attacker_id="druid",
        target_id="goblin",
        attack_name="bite",
        attack_bonus=10,
    )
    rng = _mock_rng([15, 4])

    events, _ = resolve_natural_attack(intent, ws, rng, 0, 0.0)

    failed = [e for e in events if e.event_type == "intent_validation_failed"]
    melded_blocks = [e for e in failed if e.payload.get("reason") == "equipment_melded"]
    assert len(melded_blocks) == 0, "Natural attack should not be blocked by equipment_melded"
    assert any(e.event_type == "attack_roll" for e in events)


# ===========================================================================
# NA-04: Miss produces no damage
# ===========================================================================

def test_na04_miss_produces_no_damage():
    """NA-04: A missing natural attack emits attack_roll but no damage_roll."""
    druid = _druid_wolf()
    goblin = _goblin()
    ws = _world({"druid": druid, "goblin": goblin})
    intent = NaturalAttackIntent(
        attacker_id="druid",
        target_id="goblin",
        attack_name="bite",
        attack_bonus=-10,  # guaranteed miss
    )
    rng = _mock_rng([1, 4])  # natural 1 = guaranteed miss

    events, _ = resolve_natural_attack(intent, ws, rng, 0, 0.0)

    evt_types = [e.event_type for e in events]
    assert "attack_roll" in evt_types
    assert "damage_roll" not in evt_types, f"Miss should not produce damage_roll, got {evt_types}"


# ===========================================================================
# NA-05: Unknown attack name returns validation failure
# ===========================================================================

def test_na05_unknown_attack_name_fails():
    """NA-05: validate_natural_attack returns unknown_natural_attack for unlisted name."""
    druid = _druid_wolf()
    ws = _world({"druid": druid, "goblin": _goblin()})

    reason = validate_natural_attack(druid, "slam", "goblin", ws)
    assert reason == "unknown_natural_attack", f"Got {reason!r}"


# ===========================================================================
# NA-06: No natural attacks returns validation failure
# ===========================================================================

def test_na06_no_natural_attacks_fails():
    """NA-06: validate_natural_attack returns no_natural_attacks when list is empty."""
    druid = _druid_wolf()
    druid[EF.NATURAL_ATTACKS] = []
    ws = _world({"druid": druid, "goblin": _goblin()})

    reason = validate_natural_attack(druid, "bite", "goblin", ws)
    assert reason == "no_natural_attacks", f"Got {reason!r}"


# ===========================================================================
# NA-07: Multi-attack — bear has claw and bite
# ===========================================================================

def test_na07_bear_claw_attack():
    """NA-07: Black bear claw attack resolves independently from bite."""
    druid = _druid_bear()
    goblin = _goblin()
    ws = _world({"druid": druid, "goblin": goblin})
    intent = NaturalAttackIntent(
        attacker_id="druid",
        target_id="goblin",
        attack_name="claw",
        attack_bonus=10,
    )
    rng = _mock_rng([12, 3])

    events, _ = resolve_natural_attack(intent, ws, rng, 0, 0.0)

    assert any(e.event_type == "attack_roll" for e in events)
    # Confirm the damage type on the damage_roll is slashing (claw)
    dmg_events = [e for e in events if e.event_type == "damage_roll"]
    if dmg_events:
        assert dmg_events[0].payload.get("damage_type") == "slashing", \
            f"Expected slashing damage for claw, got {dmg_events[0].payload.get('damage_type')}"


# ===========================================================================
# NA-08: weapon_type is 'natural' on constructed Weapon
# ===========================================================================

def test_na08_weapon_type_is_natural():
    """NA-08: _build_weapon_from_natural_attack produces weapon_type='natural'."""
    attack_dict = {"name": "bite", "damage": "1d6", "damage_type": "piercing"}
    weapon = _build_weapon_from_natural_attack(attack_dict)
    assert weapon.weapon_type == "natural", f"Expected 'natural', got {weapon.weapon_type!r}"


# ===========================================================================
# NA-09: Defeated target returns validation failure
# ===========================================================================

def test_na09_defeated_target_fails():
    """NA-09: validate_natural_attack returns target_already_defeated for defeated targets."""
    druid = _druid_wolf()
    goblin = _goblin()
    goblin[EF.DEFEATED] = True
    ws = _world({"druid": druid, "goblin": goblin})

    reason = validate_natural_attack(druid, "bite", "goblin", ws)
    assert reason == "target_already_defeated", f"Got {reason!r}"


# ===========================================================================
# NA-10: World state entity HP is unchanged (caller applies events)
# ===========================================================================

def test_na10_world_state_unchanged():
    """NA-10: resolve_natural_attack returns original world_state; HP changes not applied."""
    druid = _druid_wolf()
    goblin = _goblin()
    orig_hp = goblin[EF.HP_CURRENT]
    ws = _world({"druid": druid, "goblin": goblin})
    intent = NaturalAttackIntent(
        attacker_id="druid",
        target_id="goblin",
        attack_name="bite",
        attack_bonus=10,
    )
    rng = _mock_rng([15, 4])

    events, ws2 = resolve_natural_attack(intent, ws, rng, 0, 0.0)

    # Resolver returns original ws, not mutated
    assert ws2.entities["goblin"][EF.HP_CURRENT] == orig_hp, \
        "resolve_natural_attack should not mutate world_state HP"
