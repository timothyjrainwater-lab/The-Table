"""Gate tests — WO-DATA-MONSTERS-001
DATA-MONSTERS gate: 8 tests (MT-001 – MT-008)

Verifies creature stat block registry in aidm/data/creature_registry.py.
All values derived from Monster Manual 3.5e.
"""

import pytest
from aidm.data.creature_registry import CREATURE_REGISTRY


# MT-001: goblin exists with correct CR (1/4 = 0.25)
def test_mt_001_goblin_cr():
    assert "goblin" in CREATURE_REGISTRY, "goblin missing from registry"
    assert CREATURE_REGISTRY["goblin"].cr == 0.25


# MT-002: troll has regeneration_5 tag in special_qualities
def test_mt_002_troll_regeneration():
    assert "troll" in CREATURE_REGISTRY, "troll missing from registry"
    sq = CREATURE_REGISTRY["troll"].special_qualities
    assert "regeneration_5" in sq, (
        f"troll.special_qualities missing 'regeneration_5': {sq}"
    )


# MT-003: fire_giant has immunity_fire tag in special_qualities
def test_mt_003_fire_giant_energy_resistance():
    assert "fire_giant" in CREATURE_REGISTRY, "fire_giant missing from registry"
    sq = CREATURE_REGISTRY["fire_giant"].special_qualities
    assert "immunity_fire" in sq, (
        f"fire_giant.special_qualities missing 'immunity_fire': {sq}"
    )


# MT-004: skeleton_human is undead creature type
def test_mt_004_skeleton_is_undead():
    assert "skeleton_human" in CREATURE_REGISTRY, "skeleton_human missing from registry"
    assert CREATURE_REGISTRY["skeleton_human"].creature_type == "undead"


# MT-005: ogre HP in plausible MM range (avg 29, allow 25–35)
def test_mt_005_ogre_hp_range():
    assert "ogre" in CREATURE_REGISTRY, "ogre missing from registry"
    hp = CREATURE_REGISTRY["ogre"].hp
    assert 25 <= hp <= 35, f"ogre.hp={hp} outside expected range 25–35"


# MT-006: bugbear AC == 17 (MM: hide armor + natural + size)
def test_mt_006_bugbear_ac():
    assert "bugbear" in CREATURE_REGISTRY, "bugbear missing from registry"
    assert CREATURE_REGISTRY["bugbear"].ac == 17


# MT-007: coverage — at least 20 creatures in registry
def test_mt_007_coverage():
    count = len(CREATURE_REGISTRY)
    assert count >= 20, f"Expected >= 20 creatures, got {count}"


# MT-008: wolf has bite attack with correct damage dice (1d6+1, PHB MM p.283)
def test_mt_008_wolf_attack():
    assert "wolf" in CREATURE_REGISTRY, "wolf missing from registry"
    wolf = CREATURE_REGISTRY["wolf"]
    assert len(wolf.attacks) >= 1, "wolf has no attacks"
    assert wolf.attacks[0]["damage_dice"] == "1d6+1", (
        f"wolf bite damage_dice: expected '1d6+1', got '{wolf.attacks[0]['damage_dice']}'"
    )
