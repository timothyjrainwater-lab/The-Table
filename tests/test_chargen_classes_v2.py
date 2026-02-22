"""Gate V2: Complete PHB Class List Tests (WO-CHARGEN-CLASSES-COMPLETE).

12 tests covering:
- Total class count (V2-01)
- Each new class spot-check (V2-02 through V2-08)
- Class skills validation (V2-09)
- Starting gold format (V2-10)
- BAB type coverage (V2-11)
- Existing classes preserved (V2-12)

Source: PHB Chapter 3, Tables 3-1 through 3-11
"""

import pytest

from aidm.schemas.leveling import CLASS_PROGRESSIONS, ClassProgression
from aidm.schemas.skills import SKILLS


def test_v2_01_total_class_count():
    """V2-01: CLASS_PROGRESSIONS has exactly 11 entries."""
    assert len(CLASS_PROGRESSIONS) == 11, f"Expected 11 classes, got {len(CLASS_PROGRESSIONS)}"
    expected = {
        "barbarian", "bard", "cleric", "druid", "fighter",
        "monk", "paladin", "ranger", "rogue", "sorcerer", "wizard",
    }
    assert set(CLASS_PROGRESSIONS.keys()) == expected


def test_v2_02_barbarian():
    """V2-02: Barbarian has d12, full BAB, good Fort, 4 skill points."""
    barb = CLASS_PROGRESSIONS["barbarian"]
    assert barb.hit_die == 12
    assert barb.bab_type == "full"
    assert barb.good_saves == ("fort",)
    assert barb.skill_points_per_level == 4
    assert barb.starting_gold_dice == "4d4x10"


def test_v2_03_paladin():
    """V2-03: Paladin has d10, full BAB, good Fort, 2 skill points."""
    pal = CLASS_PROGRESSIONS["paladin"]
    assert pal.hit_die == 10
    assert pal.bab_type == "full"
    assert pal.good_saves == ("fort",)
    assert pal.skill_points_per_level == 2
    assert pal.starting_gold_dice == "6d4x10"


def test_v2_04_ranger():
    """V2-04: Ranger has d8, full BAB, good Fort+Ref, 6 skill points."""
    ranger = CLASS_PROGRESSIONS["ranger"]
    assert ranger.hit_die == 8
    assert ranger.bab_type == "full"
    assert set(ranger.good_saves) == {"fort", "ref"}
    assert ranger.skill_points_per_level == 6
    assert ranger.starting_gold_dice == "6d4x10"


def test_v2_05_monk():
    """V2-05: Monk has d8, 3/4 BAB, good Fort+Ref+Will, 4 skill points."""
    monk = CLASS_PROGRESSIONS["monk"]
    assert monk.hit_die == 8
    assert monk.bab_type == "threequarters"
    assert set(monk.good_saves) == {"fort", "ref", "will"}
    assert monk.skill_points_per_level == 4
    assert monk.starting_gold_dice == "5d4"


def test_v2_06_bard():
    """V2-06: Bard has d6, 3/4 BAB, good Ref+Will, 6 skill points."""
    bard = CLASS_PROGRESSIONS["bard"]
    assert bard.hit_die == 6
    assert bard.bab_type == "threequarters"
    assert set(bard.good_saves) == {"ref", "will"}
    assert bard.skill_points_per_level == 6
    assert bard.starting_gold_dice == "4d4x10"


def test_v2_07_druid():
    """V2-07: Druid has d8, 3/4 BAB, good Fort+Will, 4 skill points."""
    druid = CLASS_PROGRESSIONS["druid"]
    assert druid.hit_die == 8
    assert druid.bab_type == "threequarters"
    assert set(druid.good_saves) == {"fort", "will"}
    assert druid.skill_points_per_level == 4
    assert druid.starting_gold_dice == "2d4x10"


def test_v2_08_sorcerer():
    """V2-08: Sorcerer has d4, half BAB, good Will, 2 skill points."""
    sorc = CLASS_PROGRESSIONS["sorcerer"]
    assert sorc.hit_die == 4
    assert sorc.bab_type == "half"
    assert sorc.good_saves == ("will",)
    assert sorc.skill_points_per_level == 2
    assert sorc.starting_gold_dice == "3d4x10"


def test_v2_09_class_skills_reference_valid_skills():
    """V2-09: Every class_skills entry references a valid skill_id in SKILLS registry."""
    for class_name, prog in CLASS_PROGRESSIONS.items():
        for skill_id in prog.class_skills:
            # speak_language is a PHB class skill but not a check-based skill
            if skill_id == "speak_language":
                continue
            assert skill_id in SKILLS, (
                f"{class_name} has class skill '{skill_id}' not in SKILLS registry"
            )


def test_v2_10_starting_gold_format():
    """V2-10: Every class has a non-empty starting_gold_dice string."""
    for class_name, prog in CLASS_PROGRESSIONS.items():
        assert prog.starting_gold_dice, f"{class_name} has empty starting_gold_dice"
        # Should match pattern like "5d4x10" or "5d4"
        assert "d" in prog.starting_gold_dice, (
            f"{class_name} starting_gold_dice '{prog.starting_gold_dice}' missing 'd'"
        )


def test_v2_11_bab_types_coverage():
    """V2-11: All three BAB types are used across classes."""
    bab_types = {prog.bab_type for prog in CLASS_PROGRESSIONS.values()}
    assert bab_types == {"full", "threequarters", "half"}


def test_v2_12_existing_classes_preserved():
    """V2-12: Original 4 classes (fighter/rogue/cleric/wizard) preserved."""
    fighter = CLASS_PROGRESSIONS["fighter"]
    assert fighter.hit_die == 10
    assert fighter.bab_type == "full"
    assert fighter.skill_points_per_level == 2

    rogue = CLASS_PROGRESSIONS["rogue"]
    assert rogue.hit_die == 6
    assert rogue.skill_points_per_level == 8

    cleric = CLASS_PROGRESSIONS["cleric"]
    assert set(cleric.good_saves) == {"fort", "will"}

    wizard = CLASS_PROGRESSIONS["wizard"]
    assert wizard.hit_die == 4
    assert wizard.bab_type == "half"
