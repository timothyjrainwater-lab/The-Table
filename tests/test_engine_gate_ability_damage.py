"""Gate ENGINE-ABILITY-DAMAGE — WO-ENGINE-ABILITY-DAMAGE-001

Tests:
AD-01: get_effective_score returns base minus damage
AD-02: get_effective_score returns base minus drain (permanent)
AD-03: apply_ability_damage emits ability_damaged event
AD-04: apply_ability_damage drain emits ability_drained event
AD-05: CON drain to 0 triggers entity_defeated event
AD-06: heal_ability_damage heals up to amount (no over-heal)
AD-07: expire_ability_damage_regen heals 1 point per ability per call
AD-08: rest_resolver calls ability damage regen on overnight rest
AD-09: get_ability_modifier returns correct value from effective score
AD-10: AbilityDamageIntent roundtrips via parse_intent
"""

import unittest.mock as mock
from typing import Any, Dict
from copy import deepcopy

import pytest

from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import AbilityDamageIntent, parse_intent
from aidm.core.ability_damage_resolver import (
    get_effective_score, get_ability_modifier,
    apply_ability_damage, heal_ability_damage, expire_ability_damage_regen,
)
from aidm.schemas.intents import RestIntent
from aidm.core.rest_resolver import resolve_rest
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: str, str_score: int = 14, con_score: int = 12) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.LEVEL: 1,
        EF.AC: 10,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.CON_MOD: (con_score - 10) // 2,
        EF.STR_MOD: (str_score - 10) // 2,
        EF.DEX_MOD: 0,
        EF.SAVE_FORT: 2,
        EF.BASE_STATS: {
            "str_score": str_score,
            "dex_score": 10,
            "con_score": con_score,
            "int_score": 10,
            "wis_score": 10,
            "cha_score": 10,
        },
    }


def _world(entity: Dict[str, Any]) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={entity[EF.ENTITY_ID]: entity},
        active_combat=None,
    )


# ---------------------------------------------------------------------------
# AD-01: get_effective_score returns base minus temporary damage
# ---------------------------------------------------------------------------

def test_ad01_effective_score_minus_damage():
    e = _entity("hero")
    e[EF.STR_DAMAGE] = 4
    score = get_effective_score(e, "str")
    # base 14 - 4 damage = 10
    assert score == 10


# ---------------------------------------------------------------------------
# AD-02: get_effective_score returns base minus permanent drain
# ---------------------------------------------------------------------------

def test_ad02_effective_score_minus_drain():
    e = _entity("hero")
    e[EF.STR_DRAIN] = 6
    score = get_effective_score(e, "str")
    # base 14 - 6 drain = 8
    assert score == 8


# ---------------------------------------------------------------------------
# AD-03: apply_ability_damage emits ability_damaged event
# ---------------------------------------------------------------------------

def test_ad03_apply_ability_damage_event():
    e = _entity("hero")
    e, events = apply_ability_damage(
        e, "str", 3, False, "hero", "monster", next_event_id=10, timestamp=1.0
    )
    assert any(ev["event_type"] == "ability_damaged" for ev in events)
    dmg_ev = next(ev for ev in events if ev["event_type"] == "ability_damaged")
    assert dmg_ev["payload"]["ability"] == "str"
    assert dmg_ev["payload"]["amount"] == 3
    assert dmg_ev["payload"]["is_drain"] is False
    assert e.get(EF.STR_DAMAGE) == 3


# ---------------------------------------------------------------------------
# AD-04: apply_ability_damage drain emits ability_drained event
# ---------------------------------------------------------------------------

def test_ad04_apply_ability_drain_event():
    e = _entity("hero")
    e, events = apply_ability_damage(
        e, "wis", 2, True, "hero", "lich", next_event_id=5, timestamp=1.0
    )
    assert any(ev["event_type"] == "ability_drained" for ev in events)
    assert e.get(EF.WIS_DRAIN) == 2


# ---------------------------------------------------------------------------
# AD-05: CON drain to 0 triggers entity_defeated event
# ---------------------------------------------------------------------------

def test_ad05_con_drain_to_zero_defeats_entity():
    e = _entity("hero", con_score=8)  # CON 8 = effective score 8
    e, events = apply_ability_damage(
        e, "con", 8, True, "hero", "vampire", next_event_id=1, timestamp=1.0
    )
    # effective CON = 8 - 8 drain = 0 → defeated
    event_types = [ev["event_type"] for ev in events]
    assert "entity_defeated" in event_types
    assert e.get(EF.DEFEATED, False) is True


# ---------------------------------------------------------------------------
# AD-06: heal_ability_damage heals up to amount, no over-heal
# ---------------------------------------------------------------------------

def test_ad06_heal_ability_damage_clamps():
    e = _entity("hero")
    e[EF.STR_DAMAGE] = 3
    e, events = heal_ability_damage(e, "str", 10, "hero", next_event_id=1, timestamp=1.0)
    # Should only heal 3 (can't go below 0)
    assert e[EF.STR_DAMAGE] == 0
    assert events[0]["payload"]["amount_healed"] == 3
    assert events[0]["payload"]["remaining_damage"] == 0


# ---------------------------------------------------------------------------
# AD-07: expire_ability_damage_regen heals 1 point per ability per call
# ---------------------------------------------------------------------------

def test_ad07_regen_heals_one_per_ability():
    e = _entity("hero")
    e[EF.STR_DAMAGE] = 2
    e[EF.DEX_DAMAGE] = 5
    e[EF.CON_DAMAGE] = 1
    e, events = expire_ability_damage_regen(e, "hero", next_event_id=1, timestamp=1.0)
    assert e[EF.STR_DAMAGE] == 1
    assert e[EF.DEX_DAMAGE] == 4
    assert e[EF.CON_DAMAGE] == 0
    healed_abilities = [ev["payload"]["ability"] for ev in events if ev["event_type"] == "ability_damage_healed"]
    assert "str" in healed_abilities
    assert "dex" in healed_abilities
    assert "con" in healed_abilities


# ---------------------------------------------------------------------------
# AD-08: rest_resolver calls ability damage regen on overnight rest
# ---------------------------------------------------------------------------

def test_ad08_rest_heals_ability_damage():
    e = _entity("hero")
    e[EF.STR_DAMAGE] = 3
    ws = _world(e)
    result = resolve_rest(RestIntent(rest_type="overnight"), ws, "hero", next_event_id=0, timestamp=0.0)
    # After rest, ability damage should be 2 (healed 1)
    hero_after = result.world_state.entities["hero"]
    assert hero_after.get(EF.STR_DAMAGE, 0) == 2


# ---------------------------------------------------------------------------
# AD-09: get_ability_modifier returns correct modifier from effective score
# ---------------------------------------------------------------------------

def test_ad09_ability_modifier_from_effective():
    e = _entity("hero", str_score=16)  # base STR 16 → mod +3
    assert get_ability_modifier(e, "str") == 3

    e[EF.STR_DAMAGE] = 2  # effective 14 → mod +2
    assert get_ability_modifier(e, "str") == 2

    e[EF.STR_DRAIN] = 4  # effective 10 → mod 0
    assert get_ability_modifier(e, "str") == 0


# ---------------------------------------------------------------------------
# AD-10: AbilityDamageIntent roundtrips via parse_intent
# ---------------------------------------------------------------------------

def test_ad10_parse_intent_roundtrip():
    intent = AbilityDamageIntent(
        source_id="monster",
        target_id="hero",
        ability="str",
        amount=4,
        is_drain=True,
    )
    d = intent.to_dict()
    assert d["type"] == "ability_damage"
    parsed = parse_intent(d)
    assert isinstance(parsed, AbilityDamageIntent)
    assert parsed.ability == "str"
    assert parsed.amount == 4
    assert parsed.is_drain is True
    assert parsed.source_id == "monster"
    assert parsed.target_id == "hero"
