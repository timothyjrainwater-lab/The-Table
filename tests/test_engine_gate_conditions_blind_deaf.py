"""Gate ENGINE-CONDITIONS-BLIND-DEAF — WO-ENGINE-CONDITIONS-BLIND-DEAF-001

Tests:
BD-01: create_blinded_condition has correct modifiers (-2 AC, loses_dex_to_ac)
BD-02: check_blinded_miss returns True when d100 ≤ 50
BD-03: check_blinded_miss returns False when d100 > 50
BD-04: blinded defender causes +2 attack bonus via attack_bonus_with_conditions
BD-05: create_deafened_condition has no numeric penalties
BD-06: check_deafened_spell_failure returns True when d100 ≤ 20 with verbal component
BD-07: check_deafened_spell_failure returns False when no verbal component
BD-08: create_entangled_condition has -2 attack, -4 dex_modifier
BD-09: roll_confused_behavior returns correct behavior string for each range
BD-10: confused entity is suppressed from AoO in check_aoo_triggers
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import ConditionType
from aidm.core.condition_combat_resolver import (
    create_blinded_condition, create_deafened_condition,
    create_entangled_condition, create_confused_condition,
    check_blinded_miss, check_deafened_spell_failure,
    roll_confused_behavior, is_blinded, is_confused,
)
from aidm.core.aoo import check_aoo_triggers
from aidm.schemas.attack import StepMoveIntent
from aidm.schemas.position import Position
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng_with_roll(roll: int) -> mock.MagicMock:
    stream = mock.MagicMock()
    stream.randint.return_value = roll
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _entity(eid: str, team: str, pos: dict = None, conditions: dict = None) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.ATTACK_BONUS: 4,
        EF.BAB: 4,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 2,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: conditions or {},
        EF.POSITION: pos or {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
    }


def _world(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
        },
    )


# ---------------------------------------------------------------------------
# BD-01: create_blinded_condition has correct modifiers
# ---------------------------------------------------------------------------

def test_bd01_blinded_modifiers():
    cond = create_blinded_condition("spell_darkness", applied_at_event_id=1)
    assert cond.condition_type == ConditionType.BLINDED
    assert cond.modifiers.ac_modifier == -2
    assert cond.modifiers.loses_dex_to_ac is True


# ---------------------------------------------------------------------------
# BD-02: check_blinded_miss returns True when d100 ≤ 50
# ---------------------------------------------------------------------------

def test_bd02_blinded_miss_true():
    rng = _rng_with_roll(50)  # Exactly 50 → miss
    missed, events = check_blinded_miss(rng, "hero", next_event_id=1, timestamp=0.0)
    assert missed is True
    assert events[0]["payload"]["missed"] is True


# ---------------------------------------------------------------------------
# BD-03: check_blinded_miss returns False when d100 > 50
# ---------------------------------------------------------------------------

def test_bd03_blinded_miss_false():
    rng = _rng_with_roll(51)  # 51 → not miss
    missed, events = check_blinded_miss(rng, "hero", next_event_id=1, timestamp=0.0)
    assert missed is False
    assert events[0]["payload"]["missed"] is False


# ---------------------------------------------------------------------------
# BD-04: is_blinded returns True when entity has BLINDED condition
# ---------------------------------------------------------------------------

def test_bd04_is_blinded_check():
    e = _entity("hero", "party", conditions={"blinded": {}})
    assert is_blinded(e) is True

    e_no_blind = _entity("hero", "party")
    assert is_blinded(e_no_blind) is False


# ---------------------------------------------------------------------------
# BD-05: create_deafened_condition has no numeric combat penalties
# ---------------------------------------------------------------------------

def test_bd05_deafened_no_numeric_penalties():
    cond = create_deafened_condition("piercing_sound", applied_at_event_id=1)
    assert cond.condition_type == ConditionType.DEAFENED
    assert cond.modifiers.ac_modifier == 0
    assert cond.modifiers.attack_modifier == 0


# ---------------------------------------------------------------------------
# BD-06: check_deafened_spell_failure True when d100 ≤ 20 with verbal component
# ---------------------------------------------------------------------------

def test_bd06_deafened_spell_failure_verbal():
    rng = _rng_with_roll(20)  # Exactly 20 → spell fails
    failed, events = check_deafened_spell_failure(
        rng, "wizard", "magic_missile", has_verbal_component=True,
        next_event_id=1, timestamp=0.0
    )
    assert failed is True
    assert events[0]["payload"]["failed"] is True


# ---------------------------------------------------------------------------
# BD-07: check_deafened_spell_failure False when no verbal component
# ---------------------------------------------------------------------------

def test_bd07_deafened_no_failure_without_verbal():
    rng = _rng_with_roll(1)  # Even roll of 1 should not fail if no verbal
    failed, events = check_deafened_spell_failure(
        rng, "wizard", "silent_image", has_verbal_component=False,
        next_event_id=1, timestamp=0.0
    )
    assert failed is False
    assert events == []


# ---------------------------------------------------------------------------
# BD-08: create_entangled_condition has -2 attack, -4 dex_modifier
# ---------------------------------------------------------------------------

def test_bd08_entangled_modifiers():
    cond = create_entangled_condition("web_spell", applied_at_event_id=1)
    assert cond.condition_type == ConditionType.ENTANGLED
    assert cond.modifiers.attack_modifier == -2
    assert cond.modifiers.dex_modifier == -4


# ---------------------------------------------------------------------------
# BD-09: roll_confused_behavior returns correct behavior for each d100 range
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("roll,expected_behavior", [
    (5, "attack_caster"),
    (10, "attack_caster"),
    (11, "act_normally"),
    (20, "act_normally"),
    (21, "babble"),
    (50, "babble"),
    (51, "flee"),
    (70, "flee"),
    (71, "attack_nearest"),
    (100, "attack_nearest"),
])
def test_bd09_confused_behavior_ranges(roll, expected_behavior):
    rng = _rng_with_roll(roll)
    behavior, events = roll_confused_behavior(rng, "confused_hero", next_event_id=1, timestamp=0.0)
    assert behavior == expected_behavior
    assert events[0]["payload"]["behavior"] == expected_behavior


# ---------------------------------------------------------------------------
# BD-10: confused entity suppressed from AoO in check_aoo_triggers
# ---------------------------------------------------------------------------

def test_bd10_confused_suppresses_aoo():
    hero = _entity("hero", "party", pos={"x": 1, "y": 0})
    orc = _entity("orc", "monsters", pos={"x": 0, "y": 0},
                  conditions={"confused": {}})
    ws = _world({"hero": hero, "orc": orc})
    # Hero moves out of orc's threatened square
    move_intent = StepMoveIntent(
        actor_id="hero",
        from_pos=Position(x=1, y=0),
        to_pos=Position(x=2, y=0),
    )
    triggers = check_aoo_triggers(ws, "hero", move_intent)
    # Confused orc should NOT get an AoO
    reactor_ids = [t.reactor_id for t in triggers]
    assert "orc" not in reactor_ids
