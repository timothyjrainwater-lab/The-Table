"""Gate tests — SRSP-AE-001 through SRSP-AE-004
WO-AE-WO1: Spell save descriptor always "spell" — racial bonuses (halfling, dwarf) fire for all spells.
PHB p.176 (spell saves use standard saving throw mechanics including all modifiers).
Fix: play_loop._create_target_stats(): _save_descriptor = "spell" (unconditional).
"""

import pytest
from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


def _ws(entity: dict) -> WorldState:
    ws = WorldState(ruleset_version="3.5", entities={entity[EF.ENTITY_ID]: entity}, active_combat=None)
    return ws


def _base_entity(entity_id: str = "target") -> dict:
    return {
        EF.ENTITY_ID: entity_id,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 1,
        EF.FEATS: [],
        EF.CLASS_LEVELS: {},
        EF.RACE: "human",
        EF.RACIAL_SAVE_BONUS: 0,
        EF.SAVE_BONUS_POISON: 0,
        EF.SAVE_BONUS_SPELLS: 0,
        EF.SAVE_BONUS_ENCHANTMENT: 0,
        EF.CONDITIONS: [],
        EF.TEAM: "players",
    }


def test_srsp_ae_001_dwarf_spell_bonus_fires_with_empty_school():
    """SRSP-AE-001: Dwarf +2 vs spells fires when save_descriptor='spell' and school='' (empty).
    Before fix: _save_descriptor was '' when school was '' → racial spell bonus missed.
    After fix: _save_descriptor is always 'spell' for spell saves.
    """
    entity = _base_entity()
    entity[EF.RACE] = "dwarf"
    entity[EF.SAVE_BONUS_SPELLS] = 2  # Dwarf racial spell save bonus
    ws = _ws(entity)

    # save_descriptor="spell" with empty school → racial spell bonus should fire
    bonus_with = get_save_bonus(ws, "target", SaveType.WILL, save_descriptor="spell", school="")
    # save_descriptor="" → racial spell bonus should NOT fire
    bonus_without = get_save_bonus(ws, "target", SaveType.WILL, save_descriptor="", school="")

    assert bonus_with == bonus_without + 2, (
        f"Dwarf spell bonus (+2) should fire when save_descriptor='spell' regardless of school. "
        f"With: {bonus_with}, Without: {bonus_without}"
    )


def test_srsp_ae_002_halfling_all_saves_unaffected_by_descriptor():
    """SRSP-AE-002: Halfling +1 all saves fires regardless of save_descriptor (not school-gated)."""
    entity = _base_entity()
    entity[EF.RACE] = "halfling"
    entity[EF.RACIAL_SAVE_BONUS] = 1  # halfling +1 all saves
    ws = _ws(entity)

    bonus_spell = get_save_bonus(ws, "target", SaveType.FORT, save_descriptor="spell", school="")
    bonus_empty = get_save_bonus(ws, "target", SaveType.FORT, save_descriptor="", school="")

    # Halfling bonus fires for both — it's a blanket bonus, not descriptor-gated
    assert bonus_spell == bonus_empty, (
        f"Halfling all-saves +1 should not depend on descriptor. spell={bonus_spell}, empty={bonus_empty}"
    )
    assert bonus_spell == entity[EF.SAVE_FORT] + 1


def test_srsp_ae_003_dwarf_spell_bonus_with_school_set():
    """SRSP-AE-003: Dwarf +2 vs spells fires when save_descriptor='spell' and school='evocation'."""
    entity = _base_entity()
    entity[EF.RACE] = "dwarf"
    entity[EF.SAVE_BONUS_SPELLS] = 2
    ws = _ws(entity)

    bonus = get_save_bonus(ws, "target", SaveType.WILL, save_descriptor="spell", school="evocation")
    base = entity[EF.SAVE_WILL]

    assert bonus == base + 2, f"Dwarf +2 vs spells should fire when school='evocation'. Got {bonus}, expected {base + 2}"


def test_srsp_ae_004_non_spell_save_no_spell_bonus():
    """SRSP-AE-004: Dwarf spell bonus does NOT fire for non-spell saves (descriptor != 'spell')."""
    entity = _base_entity()
    entity[EF.RACE] = "dwarf"
    entity[EF.SAVE_BONUS_SPELLS] = 2
    ws = _ws(entity)

    # poison save — should NOT get the spell bonus
    bonus = get_save_bonus(ws, "target", SaveType.FORT, save_descriptor="poison", school="")
    base = entity[EF.SAVE_FORT]

    assert bonus == base, (
        f"Dwarf spell bonus should NOT fire for poison save. Got {bonus}, expected {base}"
    )
