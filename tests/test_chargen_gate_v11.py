"""Gate V11 — Racial Trait Mechanical Encoding.

WO-CHARGEN-RACIAL-001

Tests that build_character() correctly populates racial trait EF fields
for all 7 PHB races. Fields must be present and accurate for applicable
races; fields must be ABSENT (not zero/False) for races without the trait.

PHB references:
- All races: PHB Chapter 2, pp.12-18
"""

import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _build(race: str, class_name: str = "fighter", level: int = 1, **kwargs):
    """Build a character with neutral ability overrides for clean trait testing."""
    defaults = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
    return build_character(race, class_name, level=level, ability_overrides=defaults, **kwargs)


# ---------------------------------------------------------------------------
# V11-01: Dwarf fighter 1: STABILITY_BONUS = 4
# ---------------------------------------------------------------------------

def test_v11_01_dwarf_stability_bonus():
    """Dwarf fighter 1: STABILITY_BONUS = 4 (PHB p.14)."""
    entity = _build("dwarf")
    assert entity[EF.STABILITY_BONUS] == 4


# ---------------------------------------------------------------------------
# V11-02: Dwarf fighter 1: SAVE_BONUS_POISON = 2
# ---------------------------------------------------------------------------

def test_v11_02_dwarf_save_bonus_poison():
    """Dwarf fighter 1: SAVE_BONUS_POISON = 2 (PHB p.14)."""
    entity = _build("dwarf")
    assert entity[EF.SAVE_BONUS_POISON] == 2


# ---------------------------------------------------------------------------
# V11-03: Dwarf fighter 1: SAVE_BONUS_SPELLS = 2
# ---------------------------------------------------------------------------

def test_v11_03_dwarf_save_bonus_spells():
    """Dwarf fighter 1: SAVE_BONUS_SPELLS = 2 vs spells/spell-like abilities (PHB p.14)."""
    entity = _build("dwarf")
    assert entity[EF.SAVE_BONUS_SPELLS] == 2


# ---------------------------------------------------------------------------
# V11-04: Dwarf fighter 1: DARKVISION_RANGE = 60
# ---------------------------------------------------------------------------

def test_v11_04_dwarf_darkvision():
    """Dwarf fighter 1: DARKVISION_RANGE = 60 feet (PHB p.14)."""
    entity = _build("dwarf")
    assert entity[EF.DARKVISION_RANGE] == 60


# ---------------------------------------------------------------------------
# V11-05: Dwarf fighter 1: STONECUNNING = True
# ---------------------------------------------------------------------------

def test_v11_05_dwarf_stonecunning():
    """Dwarf fighter 1: STONECUNNING = True (PHB p.14)."""
    entity = _build("dwarf")
    assert entity[EF.STONECUNNING] is True


# ---------------------------------------------------------------------------
# V11-06: Dwarf fighter 1: ATTACK_BONUS_VS_ORCS = 1
# ---------------------------------------------------------------------------

def test_v11_06_dwarf_attack_bonus_vs_orcs():
    """Dwarf fighter 1: ATTACK_BONUS_VS_ORCS = 1 (PHB p.14)."""
    entity = _build("dwarf")
    assert entity[EF.ATTACK_BONUS_VS_ORCS] == 1


# ---------------------------------------------------------------------------
# V11-07: Dwarf fighter 1: DODGE_BONUS_VS_GIANTS = 4
# ---------------------------------------------------------------------------

def test_v11_07_dwarf_dodge_bonus_vs_giants():
    """Dwarf fighter 1: DODGE_BONUS_VS_GIANTS = 4 (PHB p.14)."""
    entity = _build("dwarf")
    assert entity[EF.DODGE_BONUS_VS_GIANTS] == 4


# ---------------------------------------------------------------------------
# V11-08: Elf wizard 1: LOW_LIGHT_VISION = True
# ---------------------------------------------------------------------------

def test_v11_08_elf_low_light_vision():
    """Elf wizard 1: LOW_LIGHT_VISION = True (PHB p.15)."""
    entity = _build("elf", "wizard")
    assert entity[EF.LOW_LIGHT_VISION] is True


# ---------------------------------------------------------------------------
# V11-09: Elf wizard 1: IMMUNE_SLEEP = True
# ---------------------------------------------------------------------------

def test_v11_09_elf_immune_sleep():
    """Elf wizard 1: IMMUNE_SLEEP = True (PHB p.15)."""
    entity = _build("elf", "wizard")
    assert entity[EF.IMMUNE_SLEEP] is True


# ---------------------------------------------------------------------------
# V11-10: Elf wizard 1: SAVE_BONUS_ENCHANTMENT = 2
# ---------------------------------------------------------------------------

def test_v11_10_elf_save_bonus_enchantment():
    """Elf wizard 1: SAVE_BONUS_ENCHANTMENT = 2 (PHB p.15)."""
    entity = _build("elf", "wizard")
    assert entity[EF.SAVE_BONUS_ENCHANTMENT] == 2


# ---------------------------------------------------------------------------
# V11-11: Elf wizard 1: RACIAL_SKILL_BONUS includes listen+2, search+2, spot+2
# ---------------------------------------------------------------------------

def test_v11_11_elf_racial_skill_bonus():
    """Elf wizard 1: RACIAL_SKILL_BONUS = {listen:2, search:2, spot:2} (PHB p.15)."""
    entity = _build("elf", "wizard")
    bonus = entity[EF.RACIAL_SKILL_BONUS]
    assert bonus["listen"] == 2
    assert bonus["search"] == 2
    assert bonus["spot"] == 2


# ---------------------------------------------------------------------------
# V11-12: Halfling rogue 1: RACIAL_SAVE_BONUS = 1
# ---------------------------------------------------------------------------

def test_v11_12_halfling_racial_save_bonus():
    """Halfling rogue 1: RACIAL_SAVE_BONUS = 1 (all saves, PHB p.16)."""
    entity = _build("halfling", "rogue")
    assert entity[EF.RACIAL_SAVE_BONUS] == 1


# ---------------------------------------------------------------------------
# V11-13: Halfling rogue 1: RACIAL_SKILL_BONUS includes listen+2, move_silently+2
# ---------------------------------------------------------------------------

def test_v11_13_halfling_racial_skill_bonus():
    """Halfling rogue 1: RACIAL_SKILL_BONUS includes listen+2, move_silently+2 (PHB p.16)."""
    entity = _build("halfling", "rogue")
    bonus = entity[EF.RACIAL_SKILL_BONUS]
    assert bonus["listen"] == 2
    assert bonus["move_silently"] == 2


# ---------------------------------------------------------------------------
# V11-14: Half-orc barbarian 1: DARKVISION_RANGE = 60
# ---------------------------------------------------------------------------

def test_v11_14_half_orc_darkvision():
    """Half-orc barbarian 1: DARKVISION_RANGE = 60 feet (PHB p.18)."""
    entity = _build("half_orc", "barbarian")
    assert entity[EF.DARKVISION_RANGE] == 60


# ---------------------------------------------------------------------------
# V11-15: Half-elf ranger 1: LOW_LIGHT_VISION = True, SAVE_BONUS_ENCHANTMENT = 2
# ---------------------------------------------------------------------------

def test_v11_15_half_elf_traits():
    """Half-elf ranger 1: LOW_LIGHT_VISION=True, SAVE_BONUS_ENCHANTMENT=2 (PHB p.18)."""
    entity = _build("half_elf", "ranger")
    assert entity[EF.LOW_LIGHT_VISION] is True
    assert entity[EF.SAVE_BONUS_ENCHANTMENT] == 2


# ---------------------------------------------------------------------------
# V11-16: Human fighter 1: no DARKVISION_RANGE key (absent, not 0)
# ---------------------------------------------------------------------------

def test_v11_16_human_no_darkvision():
    """Human fighter 1: no DARKVISION_RANGE key — absent, not zero (PHB p.12)."""
    entity = _build("human")
    assert EF.DARKVISION_RANGE not in entity


# ---------------------------------------------------------------------------
# V11-17: Human fighter 1: no STABILITY_BONUS key (absent, not 0)
# ---------------------------------------------------------------------------

def test_v11_17_human_no_stability_bonus():
    """Human fighter 1: no STABILITY_BONUS key — absent, not zero (PHB p.12)."""
    entity = _build("human")
    assert EF.STABILITY_BONUS not in entity


# ---------------------------------------------------------------------------
# V11-18: V6 regression — spot check elf wizard, dwarf fighter, halfling rogue
# ---------------------------------------------------------------------------

def test_v11_18_v6_regression_spot_check():
    """V6 regression: standard builds still complete successfully with racial traits."""
    elf_wiz = build_character(
        "elf", "wizard", level=3,
        ability_overrides={"str": 8, "dex": 14, "con": 8, "int": 16, "wis": 10, "cha": 10},
    )
    assert elf_wiz[EF.RACE] == "elf"
    assert elf_wiz[EF.LEVEL] == 3
    assert elf_wiz[EF.LOW_LIGHT_VISION] is True

    dwarf_fighter = build_character(
        "dwarf", "fighter", level=5,
        ability_overrides={"str": 16, "dex": 10, "con": 14, "int": 8, "wis": 10, "cha": 8},
    )
    assert dwarf_fighter[EF.RACE] == "dwarf"
    assert dwarf_fighter[EF.LEVEL] == 5
    assert dwarf_fighter[EF.DARKVISION_RANGE] == 60

    halfling_rogue = build_character(
        "halfling", "rogue", level=4,
        ability_overrides={"str": 8, "dex": 16, "con": 12, "int": 12, "wis": 10, "cha": 10},
    )
    assert halfling_rogue[EF.RACE] == "halfling"
    assert halfling_rogue[EF.LEVEL] == 4
    assert halfling_rogue[EF.RACIAL_SAVE_BONUS] == 1
