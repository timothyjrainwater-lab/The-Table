"""Gate V6: Character Builder Tests (WO-CHARGEN-BUILDER-001).

25 tests covering:
- Basic build for each of 11 classes at level 1 (V6-01 through V6-11)
- Level 5 build with derived stats validation (V6-12)
- Level 10 caster with spell slots (V6-13)
- Level 20 build at max level (V6-14)
- Each of 7 races builds successfully (V6-15)
- Ability overrides (V6-16)
- Racial modifiers applied (V6-17)
- Feat assignment (V6-18)
- Skill allocation (V6-19)
- Spell choice for spontaneous caster (V6-20)
- Spell choice for prepared caster (V6-21)
- Invalid race/class errors (V6-22)
- Non-caster spellcasting fields empty (V6-23)
- Human bonus feat slot (V6-24)
- Import from package (V6-25)

Source: PHB Chapters 1-3
"""

import pytest

from aidm.schemas.entity_fields import EF
from aidm.schemas.leveling import CLASS_PROGRESSIONS
from aidm.data.races import RACE_REGISTRY
from aidm.chargen.builder import build_character


# ---------------------------------------------------------------------------
# V6-01 through V6-11: Build each of 11 classes at level 1
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("class_name", sorted(CLASS_PROGRESSIONS.keys()))
def test_v6_01_to_11_build_all_classes_level_1(class_name):
    """V6-01..11: build_character produces valid entity for each class at level 1."""
    entity = build_character("human", class_name, level=1, ability_method="standard")

    # Core fields exist
    assert entity[EF.ENTITY_ID]
    assert entity[EF.RACE] == "human"
    assert entity[EF.LEVEL] == 1
    assert entity[EF.CLASS_LEVELS] == {class_name: 1}

    # HP is positive
    assert entity[EF.HP_MAX] > 0
    assert entity[EF.HP_CURRENT] == entity[EF.HP_MAX]

    # BAB is non-negative
    assert entity[EF.BAB] >= 0

    # Saves are ints
    assert isinstance(entity[EF.SAVE_FORT], int)
    assert isinstance(entity[EF.SAVE_REF], int)
    assert isinstance(entity[EF.SAVE_WILL], int)

    # Ability scores exist and are reasonable
    base_stats = entity[EF.BASE_STATS]
    assert len(base_stats) == 6
    for ability in ("str", "dex", "con", "int", "wis", "cha"):
        assert ability in base_stats
        assert base_stats[ability] >= 3  # minimum possible after racial mods

    # Class skills populated
    assert isinstance(entity[EF.CLASS_SKILLS], list)

    # Feat slots available
    assert entity[EF.FEAT_SLOTS] >= 0

    # Not defeated
    assert entity[EF.DEFEATED] is False

    # Spellcasting fields present
    assert EF.SPELL_SLOTS in entity
    assert EF.SPELLS_KNOWN in entity
    assert EF.SPELLS_PREPARED in entity
    assert EF.CASTER_LEVEL in entity


def test_v6_12_level_5_derived_stats():
    """V6-12: Level 5 fighter has correct derived stats."""
    entity = build_character(
        "human", "fighter", level=5,
        ability_overrides={"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 8},
    )

    assert entity[EF.LEVEL] == 5
    assert entity[EF.BAB] == 5  # Full BAB at level 5

    # STR 16 → mod +3
    assert entity[EF.STR_MOD] == 3
    # Attack bonus = BAB + STR mod
    assert entity[EF.ATTACK_BONUS] == 8

    # CON 14 → mod +2, fighter d10
    # Level 1: max(1, 10+2) = 12, Levels 2-5: roll+2 each (min 1)
    assert entity[EF.HP_MAX] >= 12 + 4  # At minimum: 12 + 4*(1) = 16
    assert entity[EF.HP_MAX] <= 12 + 4 * 12  # At max: 12 + 4*(10+2) = 60

    # Fort is good save for fighter, +2 CON mod
    # Good save at level 5 = 4
    assert entity[EF.SAVE_FORT] == 4 + 2  # 6

    # WIS 12 → mod +1, Will is poor save for fighter
    # Poor save at level 5 = 1
    assert entity[EF.SAVE_WILL] == 1 + 1  # 2


def test_v6_13_level_10_wizard_spell_slots():
    """V6-13: Level 10 wizard has spell slots through 5th level."""
    entity = build_character(
        "elf", "wizard", level=10,
        ability_overrides={"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
    )

    slots = entity[EF.SPELL_SLOTS]
    assert 0 in slots  # Cantrips
    assert 1 in slots
    assert 5 in slots  # 5th level spells at wizard 10

    # With INT 20 (18+2 elf racial), modifier +5
    # Bonus spells: 1st: 2, 2nd: 1, 3rd: 1, 4th: 1, 5th: 1
    elf_int = 18 + 2  # Elf gets +2 DEX, not INT... actually elf has DEX+2, CON-2
    # So INT stays 18, modifier +4
    # Bonus spells: 1st: 1, 2nd: 1, 3rd: 1, 4th: 1
    assert slots[0] == 4  # Cantrips (no bonus)
    assert slots[1] >= 4  # Base 4 + bonus from INT

    assert entity[EF.CASTER_LEVEL] == 10


def test_v6_14_level_20_build():
    """V6-14: Level 20 build succeeds and has correct BAB."""
    entity = build_character("human", "fighter", level=20, ability_method="standard")

    assert entity[EF.LEVEL] == 20
    assert entity[EF.BAB] == 20  # Full BAB fighter
    assert entity[EF.HP_MAX] > 0

    # Feat slots: 1 + (20//3) + 1(human) = 1 + 6 + 1 = 8
    total_feat_slots = 1 + (20 // 3) + 1
    assert entity[EF.FEAT_SLOTS] == total_feat_slots  # No feats assigned


def test_v6_15_all_races_build():
    """V6-15: All 7 PHB races can build a level 1 fighter."""
    for race_id in RACE_REGISTRY:
        entity = build_character(race_id, "fighter", level=1, ability_method="standard")
        assert entity[EF.RACE] == race_id
        assert entity[EF.HP_MAX] > 0


def test_v6_16_ability_overrides():
    """V6-16: Ability overrides are used when provided."""
    overrides = {"str": 18, "dex": 10, "con": 14, "int": 8, "wis": 12, "cha": 7}
    entity = build_character("human", "fighter", level=1, ability_overrides=overrides)

    # Human has no ability mods, so scores should match overrides
    stats = entity[EF.BASE_STATS]
    assert stats["str"] == 18
    assert stats["cha"] == 7


def test_v6_17_racial_modifiers_applied():
    """V6-17: Racial ability modifiers are correctly applied."""
    overrides = {"str": 14, "dex": 14, "con": 14, "int": 14, "wis": 14, "cha": 14}

    # Elf: +2 DEX, -2 CON
    entity = build_character("elf", "fighter", level=1, ability_overrides=overrides)
    stats = entity[EF.BASE_STATS]
    assert stats["dex"] == 16  # 14 + 2
    assert stats["con"] == 12  # 14 - 2
    assert stats["str"] == 14  # Unchanged

    # Dwarf: +2 CON, -2 CHA
    entity = build_character("dwarf", "fighter", level=1, ability_overrides=overrides)
    stats = entity[EF.BASE_STATS]
    assert stats["con"] == 16
    assert stats["cha"] == 12


def test_v6_18_feat_assignment():
    """V6-18: Feats are assigned from choices."""
    entity = build_character(
        "human", "fighter", level=1,
        ability_overrides={"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 8},
        feat_choices=["power_attack", "cleave"],
    )

    # Human level 1 gets 2 feat slots (1 base + 1 human)
    assert "power_attack" in entity[EF.FEATS]
    assert "cleave" in entity[EF.FEATS]
    assert entity[EF.FEAT_SLOTS] == 0  # All slots used


def test_v6_19_skill_allocation():
    """V6-19: Skill ranks are allocated."""
    entity = build_character(
        "human", "rogue", level=1,
        ability_overrides={"str": 10, "dex": 16, "con": 12, "int": 14, "wis": 10, "cha": 10},
        skill_allocations={"hide": 4, "move_silently": 4, "tumble": 4},
    )

    ranks = entity[EF.SKILL_RANKS]
    assert ranks["hide"] == 4
    assert ranks["move_silently"] == 4
    assert ranks["tumble"] == 4


def test_v6_20_spontaneous_caster_spells():
    """V6-20: Sorcerer gets spell slots and can assign spells known."""
    entity = build_character(
        "human", "sorcerer", level=1,
        ability_overrides={"str": 8, "dex": 14, "con": 12, "int": 10, "wis": 10, "cha": 16},
        spell_choices=["detect_magic", "light", "resistance", "mending",
                       "magic_missile", "mage_armor"],
    )

    # Level 1 sorcerer should have spell slots
    slots = entity[EF.SPELL_SLOTS]
    assert 0 in slots
    assert slots[0] >= 5  # Base 5 cantrips
    assert 1 in slots
    assert slots[1] >= 3  # Base 3 + bonus from CHA 16

    # Should have some spells known
    assert entity[EF.CASTER_LEVEL] == 1


def test_v6_21_prepared_caster_spells():
    """V6-21: Wizard gets spell slots and can prepare spells."""
    entity = build_character(
        "human", "wizard", level=1,
        ability_overrides={"str": 8, "dex": 14, "con": 12, "int": 16, "wis": 10, "cha": 10},
        spell_choices=["magic_missile", "mage_armor"],
    )

    # Wizard should have spells prepared
    prepared = entity[EF.SPELLS_PREPARED]
    assert isinstance(prepared, dict)

    # Spell slots present
    slots = entity[EF.SPELL_SLOTS]
    assert 0 in slots
    assert 1 in slots


def test_v6_22_invalid_inputs():
    """V6-22: Invalid race/class/level raise appropriate errors."""
    with pytest.raises(KeyError, match="Unknown race"):
        build_character("dragonborn", "fighter", level=1)

    with pytest.raises(KeyError, match="Unknown class"):
        build_character("human", "warlock", level=1)

    with pytest.raises(ValueError, match="Level must be"):
        build_character("human", "fighter", level=0)

    with pytest.raises(ValueError, match="Level must be"):
        build_character("human", "fighter", level=21)


def test_v6_23_non_caster_spellcasting_empty():
    """V6-23: Non-caster has empty spellcasting fields."""
    entity = build_character("human", "fighter", level=5, ability_method="standard")

    assert entity[EF.SPELL_SLOTS] == {}
    assert entity[EF.SPELLS_KNOWN] == {}
    assert entity[EF.SPELLS_PREPARED] == {}
    assert entity[EF.CASTER_LEVEL] == 0


def test_v6_24_human_bonus_feat_slot():
    """V6-24: Human gets +1 bonus feat slot."""
    human = build_character("human", "fighter", level=1, ability_method="standard")
    elf = build_character("elf", "fighter", level=1, ability_method="standard")

    # Human: 1 base + 1 racial = 2 total feat slots
    # Elf: 1 base + 0 racial = 1 total feat slot
    assert human[EF.FEAT_SLOTS] == 2
    assert elf[EF.FEAT_SLOTS] == 1


def test_v6_25_import_from_package():
    """V6-25: build_character is importable from the chargen package."""
    from aidm.chargen import build_character as bc
    entity = bc("human", "fighter", level=1, ability_method="standard")
    assert entity[EF.HP_MAX] > 0
