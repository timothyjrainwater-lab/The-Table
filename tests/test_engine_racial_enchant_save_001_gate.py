"""
Gate tests: ENGINE-RACIAL-ENCHANT-SAVE-001
WO-ENGINE-RACIAL-ENCHANT-SAVE-001

PHB p.14 (Elf): Immunity to magic sleep effects, +2 racial bonus on saving throws
against enchantment spells or effects.
PHB p.18 (Half-Elf): Same immunities.

Tests RAES-001 through RAES-008.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from copy import deepcopy

from aidm.core.save_resolver import get_save_bonus, SaveType
from aidm.core.play_loop import _create_target_stats, _resolve_spell_cast
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.spell_resolver import SpellCastIntent
from aidm.schemas.spell_definitions import SPELL_REGISTRY
from aidm.core.spell_resolver import SpellDefinition, SpellTarget, SpellEffect, SaveEffect, DamageType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_world_state(entities):
    return WorldState(ruleset_version="3.5", entities=entities)


def _base_entity(entity_id="ent", hp=20, will_save=2, race=None):
    e = {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 12,
        EF.TEAM: "party",
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: will_save,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
    }
    if race:
        e[EF.RACE] = race
    return e


def _elf_entity(entity_id="elf", will_save=2):
    e = _base_entity(entity_id, will_save=will_save, race="elf")
    e[EF.IMMUNE_SLEEP] = True
    e[EF.SAVE_BONUS_ENCHANTMENT] = 2
    return e


def _half_elf_entity(entity_id="half_elf", will_save=2):
    e = _base_entity(entity_id, will_save=will_save, race="half_elf")
    e[EF.IMMUNE_SLEEP] = True
    e[EF.SAVE_BONUS_ENCHANTMENT] = 2
    return e


def _human_entity(entity_id="human", will_save=2):
    return _base_entity(entity_id, will_save=will_save, race="human")


def _caster_entity(entity_id="caster", caster_level=5):
    e = {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.TEAM: "party",
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 4,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CASTER_LEVEL: caster_level,
        EF.SPELL_SLOTS: {1: 3, 2: 2},
        EF.SPELLS_PREPARED: {1: ["_test_sleep"], 2: []},
        EF.CONDITIONS: {},
        EF.CHA_MOD: 3,
    }
    return e


# Register a test enchantment spell with conditions_on_fail=("unconscious",)
_TEST_SLEEP_SPELL = SpellDefinition(
    spell_id="_test_sleep",
    name="Test Sleep",
    level=1,
    school="enchantment",
    target_type=SpellTarget.SINGLE,
    range_ft=100,
    effect_type=SpellEffect.DEBUFF,
    damage_dice=None,
    damage_type=None,
    save_type=None,   # no save — all targets affected
    save_effect=SaveEffect.NONE,
    duration_rounds=10,
    conditions_on_fail=("unconscious",),
    rule_citations=("PHB p.280",),
    has_somatic=True,
    has_verbal=True,
)

_TEST_FIREBALL_SPELL = SpellDefinition(
    spell_id="_test_fireball",
    name="Test Fireball",
    level=3,
    school="evocation",
    target_type=SpellTarget.SINGLE,
    range_ft=400,
    effect_type=SpellEffect.DEBUFF,
    damage_dice=None,
    damage_type=None,
    save_type=None,
    save_effect=SaveEffect.NONE,
    duration_rounds=10,
    conditions_on_fail=("shaken",),
    rule_citations=(),
    has_somatic=True,
    has_verbal=True,
)

# Patch test spells into SPELL_REGISTRY for duration of tests
SPELL_REGISTRY["_test_sleep"] = _TEST_SLEEP_SPELL
SPELL_REGISTRY["_test_fireball"] = _TEST_FIREBALL_SPELL


# ---------------------------------------------------------------------------
# RAES-001: Elf gets +2 enchantment save bonus (Will) vs. non-elf
# ---------------------------------------------------------------------------

def test_raes_001_elf_enchantment_save_bonus():
    """RAES-001: Elf will_save vs enchantment is +2 higher than non-elf (same base will_save=2)."""
    elf = _elf_entity(will_save=2)
    human = _human_entity(will_save=2)

    ws_elf = _make_world_state({"elf": elf})
    ws_human = _make_world_state({"human": human})

    bonus_elf = get_save_bonus(ws_elf, "elf", SaveType.WILL, school="enchantment")
    bonus_human = get_save_bonus(ws_human, "human", SaveType.WILL, school="enchantment")

    assert bonus_elf == bonus_human + 2, (
        f"Elf enchantment will bonus should be +2 vs human: elf={bonus_elf}, human={bonus_human}"
    )


# ---------------------------------------------------------------------------
# RAES-002: Half-elf gets +2 enchantment save bonus
# ---------------------------------------------------------------------------

def test_raes_002_half_elf_enchantment_save_bonus():
    """RAES-002: Half-elf gets +2 enchantment Will save bonus."""
    half_elf = _half_elf_entity(will_save=2)
    human = _human_entity(will_save=2)

    ws_he = _make_world_state({"half_elf": half_elf})
    ws_h = _make_world_state({"human": human})

    bonus_he = get_save_bonus(ws_he, "half_elf", SaveType.WILL, school="enchantment")
    bonus_h = get_save_bonus(ws_h, "human", SaveType.WILL, school="enchantment")

    assert bonus_he == bonus_h + 2, (
        f"Half-elf enchantment will bonus should be +2 vs human: he={bonus_he}, human={bonus_h}"
    )


# ---------------------------------------------------------------------------
# RAES-003: Non-elf gets +0 enchantment save bonus
# ---------------------------------------------------------------------------

def test_raes_003_non_elf_no_enchantment_bonus():
    """RAES-003: Human entity with no SAVE_BONUS_ENCHANTMENT gets +0 bonus."""
    human = _human_entity(will_save=3)
    ws = _make_world_state({"human": human})

    bonus = get_save_bonus(ws, "human", SaveType.WILL, school="enchantment")

    assert bonus == 3, f"Human base will=3 + no enchantment bonus = 3, got {bonus}"


# ---------------------------------------------------------------------------
# RAES-004: Enchantment save stacks with other bonuses (Iron Will)
# ---------------------------------------------------------------------------

def test_raes_004_enchantment_bonus_stacks_with_iron_will():
    """RAES-004: Elf enchantment save bonus stacks with Iron Will feat (+2)."""
    elf = _elf_entity(will_save=2)
    elf[EF.FEATS] = ["iron_will"]

    ws = _make_world_state({"elf": elf})
    bonus = get_save_bonus(ws, "elf", SaveType.WILL, school="enchantment")

    # will_save=2 + iron_will=2 + enchantment=2 = 6
    assert bonus == 6, f"Elf with iron_will vs enchantment: expected 6, got {bonus}"


# ---------------------------------------------------------------------------
# RAES-005: Non-enchantment spell: elf gets NO bonus from SAVE_BONUS_ENCHANTMENT
# ---------------------------------------------------------------------------

def test_raes_005_non_enchantment_no_racial_bonus():
    """RAES-005: Elf SAVE_BONUS_ENCHANTMENT does NOT apply to non-enchantment spells."""
    elf = _elf_entity(will_save=2)
    human = _human_entity(will_save=2)

    ws_elf = _make_world_state({"elf": elf})
    ws_human = _make_world_state({"human": human})

    # school="evocation" — no enchantment bonus
    bonus_elf = get_save_bonus(ws_elf, "elf", SaveType.WILL, school="evocation")
    bonus_human = get_save_bonus(ws_human, "human", SaveType.WILL, school="evocation")

    assert bonus_elf == bonus_human, (
        f"Elf vs evocation should equal human (no school bonus): elf={bonus_elf}, human={bonus_human}"
    )


# ---------------------------------------------------------------------------
# RAES-006: Elf is immune to sleep spell — sleep_immunity event, no condition
# ---------------------------------------------------------------------------

def test_raes_006_elf_immune_to_sleep():
    """RAES-006: Elf gets sleep_immunity event and no 'unconscious' condition applied."""
    rng = RNGManager(master_seed=42)
    caster = _caster_entity("caster")
    target = _elf_entity("elf_target")
    target[EF.POSITION] = {"x": 1, "y": 0}

    ws = _make_world_state({"caster": caster, "elf_target": target})

    intent = SpellCastIntent(
        caster_id="caster",
        spell_id="_test_sleep",
        target_entity_id="elf_target",
    )

    events, updated_ws, _narration = _resolve_spell_cast(
        intent=intent,
        world_state=ws,
        rng=rng,
        grid=None,
        next_event_id=1,
        timestamp=0.0,
        turn_index=1,
    )

    event_types = [e.event_type for e in events]
    elf_conditions = updated_ws.entities.get("elf_target", {}).get(EF.CONDITIONS, {})

    assert "sleep_immunity" in event_types, (
        f"Expected sleep_immunity event for elf, got: {event_types}"
    )
    assert "unconscious" not in elf_conditions, (
        f"Elf should NOT get unconscious condition, but got: {elf_conditions}"
    )


# ---------------------------------------------------------------------------
# RAES-007: Half-elf is immune to sleep spell
# ---------------------------------------------------------------------------

def test_raes_007_half_elf_immune_to_sleep():
    """RAES-007: Half-elf gets sleep_immunity event and no 'unconscious' condition."""
    rng = RNGManager(master_seed=42)
    caster = _caster_entity("caster")
    target = _half_elf_entity("half_elf_target")
    target[EF.POSITION] = {"x": 1, "y": 0}

    ws = _make_world_state({"caster": caster, "half_elf_target": target})

    intent = SpellCastIntent(
        caster_id="caster",
        spell_id="_test_sleep",
        target_entity_id="half_elf_target",
    )

    events, updated_ws, _narration = _resolve_spell_cast(
        intent=intent,
        world_state=ws,
        rng=rng,
        grid=None,
        next_event_id=1,
        timestamp=0.0,
        turn_index=1,
    )

    event_types = [e.event_type for e in events]
    conditions = updated_ws.entities.get("half_elf_target", {}).get(EF.CONDITIONS, {})

    assert "sleep_immunity" in event_types, (
        f"Expected sleep_immunity event for half-elf, got: {event_types}"
    )
    assert "unconscious" not in conditions, (
        f"Half-elf should NOT get unconscious condition"
    )


# ---------------------------------------------------------------------------
# RAES-008: Non-elf IS affected by sleep spell (no immunity)
# ---------------------------------------------------------------------------

def test_raes_008_non_elf_affected_by_sleep():
    """RAES-008: Human entity receives 'unconscious' condition from sleep spell."""
    rng = RNGManager(master_seed=42)
    caster = _caster_entity("caster")
    target = _human_entity("human_target")
    target[EF.POSITION] = {"x": 1, "y": 0}
    # Ensure no IMMUNE_SLEEP flag
    target.pop(EF.IMMUNE_SLEEP, None)

    ws = _make_world_state({"caster": caster, "human_target": target})

    intent = SpellCastIntent(
        caster_id="caster",
        spell_id="_test_sleep",
        target_entity_id="human_target",
    )

    events, updated_ws, _narration = _resolve_spell_cast(
        intent=intent,
        world_state=ws,
        rng=rng,
        grid=None,
        next_event_id=1,
        timestamp=0.0,
        turn_index=1,
    )

    event_types = [e.event_type for e in events]
    conditions = updated_ws.entities.get("human_target", {}).get(EF.CONDITIONS, {})

    assert "sleep_immunity" not in event_types, (
        f"Human should NOT get sleep_immunity event"
    )
    assert "unconscious" in conditions, (
        f"Human should get unconscious condition, got conditions: {conditions}"
    )
