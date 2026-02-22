"""Gate V5: Spell Expansion Tests (WO-CHARGEN-SPELL-EXPANSION).

8 tests covering:
- Total spell count after expansion (V5-01)
- Level 6 spells added (V5-02)
- Level 7 spells added (V5-03)
- Level 8 spells added (V5-04)
- Level 9 spells added (V5-05)
- Level distribution (V5-06)
- Spell school diversity (V5-07)
- Class spell lists reference valid spells (V5-08)

Source: PHB Chapter 11 (Spells)
"""

import pytest

from aidm.data.spell_definitions import (
    SPELL_REGISTRY,
    get_spell,
    get_spells_by_level,
)
from aidm.chargen.spellcasting import CLASS_SPELL_LISTS


def test_v5_01_total_spell_count():
    """V5-01: SPELL_REGISTRY has at least 75 spells (47 original + 28 new)."""
    assert len(SPELL_REGISTRY) >= 75, f"Expected >= 75 spells, got {len(SPELL_REGISTRY)}"


def test_v5_02_level_6_spells():
    """V5-02: Level 6 spells include key iconic entries."""
    level_6 = get_spells_by_level(6)
    expected = {"chain_lightning", "disintegrate", "heal_spell", "greater_dispel_magic",
                "true_seeing", "antimagic_field", "blade_barrier"}
    assert expected.issubset(set(level_6.keys())), (
        f"Missing level 6 spells: {expected - set(level_6.keys())}"
    )
    assert len(level_6) >= 7


def test_v5_03_level_7_spells():
    """V5-03: Level 7 spells include key iconic entries."""
    level_7 = get_spells_by_level(7)
    expected = {"finger_of_death", "delayed_blast_fireball", "greater_teleport",
                "regenerate", "resurrection", "prismatic_spray", "reverse_gravity"}
    assert expected.issubset(set(level_7.keys()))
    assert len(level_7) >= 7


def test_v5_04_level_8_spells():
    """V5-04: Level 8 spells include key iconic entries."""
    level_8 = get_spells_by_level(8)
    expected = {"horrid_wilting", "polar_ray", "sunburst", "power_word_stun",
                "greater_planar_ally", "mass_cure_critical_wounds", "mind_blank"}
    assert expected.issubset(set(level_8.keys()))
    assert len(level_8) >= 7


def test_v5_05_level_9_spells():
    """V5-05: Level 9 spells include the iconic capstone spells."""
    level_9 = get_spells_by_level(9)
    expected = {"wish", "meteor_swarm", "power_word_kill", "gate",
                "miracle", "prismatic_sphere", "time_stop"}
    assert expected.issubset(set(level_9.keys()))
    assert len(level_9) >= 7


def test_v5_06_level_distribution():
    """V5-06: All spell levels 0-9 have at least one spell."""
    for level in range(10):
        spells = get_spells_by_level(level)
        assert len(spells) > 0, f"No spells at level {level}"

    # Higher levels should have at least 7 each (our new additions)
    for level in range(6, 10):
        spells = get_spells_by_level(level)
        assert len(spells) >= 7, f"Level {level} has only {len(spells)} spells"


def test_v5_07_spell_school_diversity():
    """V5-07: New spells cover multiple schools."""
    schools_in_new = set()
    for level in range(6, 10):
        for spell in get_spells_by_level(level).values():
            schools_in_new.add(spell.school)

    # Should cover at least 5 schools across levels 6-9
    assert len(schools_in_new) >= 5, f"Only {len(schools_in_new)} schools in levels 6-9: {schools_in_new}"


def test_v5_08_class_spell_lists_reference_valid_spells():
    """V5-08: Every spell_id in CLASS_SPELL_LISTS exists in SPELL_REGISTRY."""
    missing = []
    for cls, levels in CLASS_SPELL_LISTS.items():
        for level, spell_ids in levels.items():
            for spell_id in spell_ids:
                if spell_id not in SPELL_REGISTRY:
                    missing.append(f"{cls}/{level}: {spell_id}")

    assert not missing, f"Missing spells in SPELL_REGISTRY: {missing}"
