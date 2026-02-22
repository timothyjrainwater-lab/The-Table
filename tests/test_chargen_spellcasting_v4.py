"""Gate V4: Spellcasting Infrastructure Tests (WO-CHARGEN-SPELLCASTING).

15 tests covering:
- EF constants exist (V4-01)
- Spells-per-day tables for all 7 caster classes (V4-02 through V4-08)
- Bonus spells from high ability scores (V4-09)
- get_spell_slots integration (V4-10)
- Spells known tables for spontaneous casters (V4-11)
- Class spell lists populated (V4-12)
- Casting ability lookup (V4-13)
- can_cast_spell_level edge cases (V4-14)
- Non-casters excluded (V4-15)

Source: PHB Tables 3-1, 3-3, 3-5, 3-12, 3-13, 3-17, 3-18, and Table 1-1
"""

import pytest

from aidm.schemas.entity_fields import EF
from aidm.chargen.spellcasting import (
    SPELLS_PER_DAY,
    SPELLS_KNOWN_TABLE,
    CLASS_SPELL_LISTS,
    CASTING_ABILITY,
    SPONTANEOUS_CASTERS,
    MAX_SPELL_LEVEL,
    bonus_spells,
    can_cast_spell_level,
    get_spell_slots,
    get_spells_known_count,
    get_class_spell_list,
    is_caster,
)


def test_v4_01_ef_spellcasting_constants():
    """V4-01: EF has all 4 spellcasting field constants."""
    assert EF.SPELLS_KNOWN == "spells_known"
    assert EF.SPELLS_PREPARED == "spells_prepared"
    assert EF.SPELL_SLOTS == "spell_slots"
    assert EF.CASTER_LEVEL == "caster_level"


def test_v4_02_wizard_spells_per_day():
    """V4-02: Wizard spells-per-day table covers levels 1-20 with correct PHB values."""
    table = SPELLS_PER_DAY["wizard"]
    assert len(table) == 20
    # Level 1 wizard: 3 cantrips, 1 first-level
    assert table[1] == (3, 1)
    # Level 5 wizard: 4, 3, 2, 1
    assert table[5] == (4, 3, 2, 1)
    # Level 20 wizard: full progression through 9th level
    assert len(table[20]) == 10  # levels 0-9
    assert table[20] == (4, 4, 4, 4, 4, 4, 4, 4, 4, 4)


def test_v4_03_cleric_spells_per_day():
    """V4-03: Cleric spells-per-day table has PHB-correct values."""
    table = SPELLS_PER_DAY["cleric"]
    assert len(table) == 20
    # Level 1 cleric: 3 cantrips, 1 first-level (plus domain slot, but that's domain-specific)
    assert table[1] == (3, 1)
    # Level 7 cleric gains access to 4th-level spells
    assert len(table[7]) == 5  # levels 0-4
    assert table[7] == (6, 4, 3, 2, 1)


def test_v4_04_druid_spells_per_day():
    """V4-04: Druid uses same table as cleric (PHB Table 3-5)."""
    assert SPELLS_PER_DAY["druid"] == SPELLS_PER_DAY["cleric"]


def test_v4_05_sorcerer_spells_per_day():
    """V4-05: Sorcerer spells-per-day table has higher slot counts (spontaneous caster)."""
    table = SPELLS_PER_DAY["sorcerer"]
    assert len(table) == 20
    # Level 1 sorcerer: 5 cantrips, 3 first-level
    assert table[1] == (5, 3)
    # Level 4 sorcerer gains 2nd-level spells
    assert table[4] == (6, 6, 3)
    # Sorcerer at any level should have more 1st-level slots than wizard
    assert table[5][1] >= SPELLS_PER_DAY["wizard"][5][1]


def test_v4_06_bard_spells_per_day():
    """V4-06: Bard spells-per-day table maxes at 6th level."""
    table = SPELLS_PER_DAY["bard"]
    assert len(table) == 20
    # Level 1 bard: 2 cantrips only
    assert table[1] == (2,)
    # Level 2 bard gains 1st-level spells (0 base = bonus only)
    assert table[2] == (3, 0)
    # Level 20 bard: maxes out at 6th level (7 entries: 0-6)
    assert len(table[20]) == 7


def test_v4_07_ranger_spells_per_day():
    """V4-07: Ranger gains spells at level 4, maxes at 4th level."""
    table = SPELLS_PER_DAY["ranger"]
    # Levels 1-3: no spells
    assert table[1] == ()
    assert table[3] == ()
    # Level 4: gains 1st-level spells (0 base = bonus only)
    assert table[4] == (0,)
    # Level 20 ranger: 4 spell levels (1-4)
    assert len(table[20]) == 4


def test_v4_08_paladin_spells_per_day():
    """V4-08: Paladin gains spells at level 4, same structure as ranger."""
    table = SPELLS_PER_DAY["paladin"]
    assert table[1] == ()
    assert table[4] == (0,)
    assert len(table[20]) == 4


def test_v4_09_bonus_spells_calculation():
    """V4-09: Bonus spells from ability scores match PHB Table 1-1."""
    # Score 10-11: modifier 0, no bonus spells
    assert bonus_spells(10) == {}
    assert bonus_spells(11) == {}

    # Score 12-13: modifier 1, bonus 1st-level: 1
    bs = bonus_spells(12)
    assert bs.get(1) == 1
    assert 2 not in bs  # Can't cast 2nd-level spells with score 12

    # Score 14-15: modifier 2, bonus 1st: 1, 2nd: 1
    bs = bonus_spells(14)
    assert bs.get(1) == 1
    assert bs.get(2) == 1

    # Score 16-17: modifier 3
    bs = bonus_spells(16)
    assert bs.get(1) == 1
    assert bs.get(2) == 1
    assert bs.get(3) == 1

    # Score 20: modifier 5, bonus 1st through 5th: 1 each
    # Plus extra 1st: (5-1)//4 + 1 = 2
    bs = bonus_spells(20)
    assert bs.get(1) == 2  # (5-1)//4 + 1 = 2
    assert bs.get(5) == 1


def test_v4_10_get_spell_slots_integration():
    """V4-10: get_spell_slots combines base + bonus correctly."""
    # Level 1 wizard with INT 16 (modifier +3)
    slots = get_spell_slots("wizard", 1, 16)
    # Base: 3 cantrips, 1 first-level
    # Bonus: +1 to 1st level (INT 16 → modifier 3 → bonus 1st: 1)
    assert slots[0] == 3  # cantrips never get bonus
    assert slots[1] == 2  # 1 base + 1 bonus

    # Level 5 wizard with INT 18 (modifier +4)
    slots = get_spell_slots("wizard", 5, 18)
    assert slots[0] == 4   # cantrips
    assert slots[1] == 4   # 3 base + 1 bonus
    assert slots[2] == 3   # 2 base + 1 bonus
    assert slots[3] == 2   # 1 base + 1 bonus

    # Non-caster raises error
    with pytest.raises(ValueError):
        get_spell_slots("fighter", 1, 14)


def test_v4_11_spells_known_spontaneous():
    """V4-11: Spells-known tables exist for sorcerer and bard only."""
    assert "sorcerer" in SPELLS_KNOWN_TABLE
    assert "bard" in SPELLS_KNOWN_TABLE
    assert "wizard" not in SPELLS_KNOWN_TABLE

    # Sorcerer level 1: 4 cantrips known, 2 first-level known
    sk = get_spells_known_count("sorcerer", 1)
    assert sk[0] == 4
    assert sk[1] == 2

    # Bard level 1: 4 cantrips known
    sk = get_spells_known_count("bard", 1)
    assert sk[0] == 4

    # Prepared caster returns None
    assert get_spells_known_count("wizard", 1) is None


def test_v4_12_class_spell_lists_populated():
    """V4-12: All 7 caster classes have spell lists with at least some spells."""
    for cls in SPELLS_PER_DAY:
        assert cls in CLASS_SPELL_LISTS, f"{cls} missing from CLASS_SPELL_LISTS"
        total_spells = sum(len(spells) for spells in CLASS_SPELL_LISTS[cls].values())
        assert total_spells > 0, f"{cls} has empty spell list"

    # Wizard should have the largest list
    wizard_total = sum(len(s) for s in CLASS_SPELL_LISTS["wizard"].values())
    ranger_total = sum(len(s) for s in CLASS_SPELL_LISTS["ranger"].values())
    assert wizard_total > ranger_total


def test_v4_13_casting_ability_lookup():
    """V4-13: Casting ability is correct for each class."""
    assert CASTING_ABILITY["wizard"] == "int"
    assert CASTING_ABILITY["cleric"] == "wis"
    assert CASTING_ABILITY["druid"] == "wis"
    assert CASTING_ABILITY["sorcerer"] == "cha"
    assert CASTING_ABILITY["bard"] == "cha"
    assert CASTING_ABILITY["ranger"] == "wis"
    assert CASTING_ABILITY["paladin"] == "wis"


def test_v4_14_can_cast_spell_level():
    """V4-14: can_cast_spell_level enforces minimum ability score."""
    # Cantrips need 10+
    assert can_cast_spell_level(10, 0) is True
    assert can_cast_spell_level(9, 0) is False

    # 1st-level spells need 11+
    assert can_cast_spell_level(11, 1) is True
    assert can_cast_spell_level(10, 1) is False

    # 9th-level spells need 19+
    assert can_cast_spell_level(19, 9) is True
    assert can_cast_spell_level(18, 9) is False


def test_v4_15_non_casters_excluded():
    """V4-15: Non-caster classes are correctly excluded."""
    non_casters = ["fighter", "barbarian", "rogue", "monk"]
    for cls in non_casters:
        assert not is_caster(cls), f"{cls} should not be a caster"
        assert cls not in CASTING_ABILITY
        assert cls not in SPELLS_PER_DAY

    # All 7 casters are present
    casters = ["wizard", "cleric", "druid", "sorcerer", "bard", "ranger", "paladin"]
    for cls in casters:
        assert is_caster(cls), f"{cls} should be a caster"
