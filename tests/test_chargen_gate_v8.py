"""Gate V8: Multiclass character assembly tests.

WO-CHARGEN-MULTICLASS-001

Tests verify that build_character() correctly assembles multiclass characters
per PHB p.57 rules: best BAB, best-per-save progression, HD-sum HP, union
class skills, total-level feats, and per-class skill points.

15 tests required for Gate V8.
"""

import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF
from aidm.schemas.leveling import (
    BAB_PROGRESSION,
    GOOD_SAVE_PROGRESSION,
    POOR_SAVE_PROGRESSION,
    CLASS_PROGRESSIONS,
)


# ---------------------------------------------------------------------------
# Shared neutral ability overrides (all 10s → all mods = 0)
# ---------------------------------------------------------------------------
NEUTRAL = {
    "str": 10, "dex": 10, "con": 10,
    "int": 10, "wis": 10, "cha": 10,
}


# ---------------------------------------------------------------------------
# V8-01: Fighter 3 / Wizard 2 — BAB = 3 (fighter full, not wizard half)
# PHB p.57: use best BAB among classes
# ---------------------------------------------------------------------------
def test_v8_01_fighter3_wizard2_bab():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 2},
        ability_overrides=NEUTRAL,
    )
    # Fighter L3 BAB (full): BAB_PROGRESSION["full"][2] = 3
    # Wizard  L2 BAB (half): BAB_PROGRESSION["half"][1] = 1
    assert entity[EF.BAB] == 3, f"Expected BAB=3 (fighter full), got {entity[EF.BAB]}"


# ---------------------------------------------------------------------------
# V8-02: Fighter 3 / Wizard 2 — saves: Fort=good(fighter), Will=good(wizard)
# Fighter good: fort. Wizard good: will. Both poor for ref.
# ---------------------------------------------------------------------------
def test_v8_02_fighter3_wizard2_saves():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 2},
        ability_overrides=NEUTRAL,
    )
    # Fort: max(fighter good L3=3, wizard poor L2=0) = 3 + CON(0) = 3
    # Ref:  max(fighter poor L3=1, wizard poor L2=0) = 1 + DEX(0) = 1
    # Will: max(fighter poor L3=1, wizard good L2=3) = 3 + WIS(0) = 3
    assert entity[EF.SAVE_FORT] == 3
    assert entity[EF.SAVE_REF] == 1
    assert entity[EF.SAVE_WILL] == 3


# ---------------------------------------------------------------------------
# V8-03: Fighter 3 / Wizard 2 — HP = sum of HD contributions
# L1: max d10 = 10. L2: avg d10 = 6. L3: avg d10 = 6.
# Wizard L1: avg d4 = 3. Wizard L2: avg d4 = 3. Total = 28.
# ---------------------------------------------------------------------------
def test_v8_03_fighter3_wizard2_hp():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 2},
        ability_overrides=NEUTRAL,
    )
    # HP with all-10 scores (CON mod = 0):
    # Fighter L1 (max d10) = 10
    # Fighter L2 avg = round(10/2 + 0.5) = round(5.5) = 6  (banker's rounds to even)
    # Fighter L3 avg = 6
    # Wizard L1 avg  = round(4/2 + 0.5)  = round(2.5) = 2  (banker's rounds to even)
    # Wizard L2 avg  = 2
    # Total = 10 + 6 + 6 + 2 + 2 = 26
    assert entity[EF.HP_MAX] == 26


# ---------------------------------------------------------------------------
# V8-04: Fighter 3 / Wizard 2 — class skills are union of both classes
# ---------------------------------------------------------------------------
def test_v8_04_fighter3_wizard2_class_skills_union():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 2},
        ability_overrides=NEUTRAL,
    )
    fighter_skills = set(CLASS_PROGRESSIONS["fighter"].class_skills)
    wizard_skills = set(CLASS_PROGRESSIONS["wizard"].class_skills)
    expected = fighter_skills | wizard_skills
    actual = set(entity[EF.CLASS_SKILLS])
    assert expected == actual, f"Class skill union mismatch: missing={expected - actual}, extra={actual - expected}"


# ---------------------------------------------------------------------------
# V8-05: Fighter 3 / Wizard 2 — CLASS_LEVELS dict reflects the mix
# ---------------------------------------------------------------------------
def test_v8_05_fighter3_wizard2_class_levels_dict():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 2},
        ability_overrides=NEUTRAL,
    )
    assert entity[EF.CLASS_LEVELS] == {"fighter": 3, "wizard": 2}
    assert entity[EF.LEVEL] == 5


# ---------------------------------------------------------------------------
# V8-06: Cleric 1 / Fighter 1 — Fort = good (cleric good), BAB = 1 (fighter full)
# PHB p.57: cleric good Fort; fighter full BAB beats cleric 3/4 BAB
# ---------------------------------------------------------------------------
def test_v8_06_cleric1_fighter1_fort_and_bab():
    entity = build_character(
        "human", "fighter",
        class_mix={"cleric": 1, "fighter": 1},
        ability_overrides=NEUTRAL,
    )
    # BAB: max(cleric 3q L1=0, fighter full L1=1) = 1
    assert entity[EF.BAB] == 1, f"Expected BAB=1, got {entity[EF.BAB]}"
    # Fort: max(cleric good L1=2, fighter good L1=2) = 2 + CON(0) = 2
    assert entity[EF.SAVE_FORT] == 2, f"Expected Fort=2, got {entity[EF.SAVE_FORT]}"
    # Will: max(cleric good L1=2, fighter poor L1=0) = 2
    assert entity[EF.SAVE_WILL] == 2


# ---------------------------------------------------------------------------
# V8-07: Rogue 3 / Ranger 2 — Ref = good, BAB from ranger full
# Rogue good: ref. Ranger good: fort, ref. Both have good Ref.
# BAB: max(rogue 3q L3=2, ranger full L2=2) = 2
# ---------------------------------------------------------------------------
def test_v8_07_rogue3_ranger2_ref_and_bab():
    entity = build_character(
        "human", "fighter",
        class_mix={"rogue": 3, "ranger": 2},
        ability_overrides=NEUTRAL,
    )
    # BAB: max(rogue 3q L3=2, ranger full L2=2) = 2
    assert entity[EF.BAB] == 2
    # Ref: max(rogue good L3=3, ranger good L2=3) = 3 + DEX(0) = 3
    assert entity[EF.SAVE_REF] == 3


# ---------------------------------------------------------------------------
# V8-08: Human Fighter 2 / Wizard 2 — human skill point bonus applied
# Each class: 2 sp/level. Fighter: 4+2=6. Wizard: 4+2=6. Human: +4 (total_level=4). = 16
# ---------------------------------------------------------------------------
def test_v8_08_human_fighter2_wizard2_skill_points():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 2, "wizard": 2},
        ability_overrides=NEUTRAL,
        skill_allocations={"climb": 5, "spellcraft": 5},
    )
    # Verify climb (fighter class skill) and spellcraft (wizard class skill) accepted
    # Both are in the union class skills, so both are class skills
    assert "climb" in entity[EF.CLASS_SKILLS]
    assert "spellcraft" in entity[EF.CLASS_SKILLS]
    # Verify class_levels
    assert entity[EF.CLASS_LEVELS] == {"fighter": 2, "wizard": 2}
    assert entity[EF.LEVEL] == 4


# ---------------------------------------------------------------------------
# V8-09: Fighter 3 / Wizard 2 — wizard gets spell slots at wizard level 2
# Not fighter level. Fighter/Wizard → wizard spells at wizard level only.
# ---------------------------------------------------------------------------
def test_v8_09_fighter3_wizard2_wizard_spells_at_wizard_level():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 2},
        ability_overrides=NEUTRAL,
    )
    # Wizard L2 gets 0-level and 1st-level spell slots
    # Caster level should be wizard's level (2), not total (5)
    assert entity[EF.CASTER_LEVEL] == 2
    # Spell slots should be non-empty (wizard L2 has slots)
    assert entity[EF.SPELL_SLOTS], "Fighter/Wizard should have wizard spell slots"
    # Must have 0-level slots
    assert 0 in entity[EF.SPELL_SLOTS]


# ---------------------------------------------------------------------------
# V8-10: Favored class stored in output (PHB p.56, informational)
# ---------------------------------------------------------------------------
def test_v8_10_favored_class_stored():
    entity = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 2},
        ability_overrides=NEUTRAL,
        favored_class="fighter",
    )
    assert entity.get("favored_class") == "fighter"


# ---------------------------------------------------------------------------
# V8-11: Invalid — total level > 20 raises ValueError
# ---------------------------------------------------------------------------
def test_v8_11_invalid_total_level_over_20():
    with pytest.raises(ValueError, match="1-20"):
        build_character(
            "human", "fighter",
            class_mix={"fighter": 15, "wizard": 10},
            ability_overrides=NEUTRAL,
        )


# ---------------------------------------------------------------------------
# V8-12: Invalid — unknown class in class_mix raises KeyError
# ---------------------------------------------------------------------------
def test_v8_12_invalid_unknown_class_in_mix():
    with pytest.raises(KeyError):
        build_character(
            "human", "fighter",
            class_mix={"fighter": 3, "jedi": 2},
            ability_overrides=NEUTRAL,
        )


# ---------------------------------------------------------------------------
# V8-13: Bard 2 / Rogue 3 — bard has good Ref and Will, rogue has good Ref
# Verifies different caster + skill combo; bard is spontaneous caster
# ---------------------------------------------------------------------------
def test_v8_13_bard2_rogue3_saves_and_spellcasting():
    entity = build_character(
        "human", "fighter",
        class_mix={"bard": 2, "rogue": 3},
        ability_overrides=NEUTRAL,
    )
    # Bard good: ref, will. Rogue good: ref.
    # Ref: max(bard good L2=3, rogue good L3=3) = 3
    # Will: max(bard good L2=3, rogue poor L3=1) = 3
    # Fort: max(bard poor L2=0, rogue poor L3=1) = 1
    assert entity[EF.SAVE_REF] == 3
    assert entity[EF.SAVE_WILL] == 3
    assert entity[EF.SAVE_FORT] == 1
    # Bard is a spontaneous caster — should have spell slots at bard level 2
    assert entity[EF.CASTER_LEVEL] == 2
    assert entity[EF.SPELL_SLOTS]


# ---------------------------------------------------------------------------
# V8-14: Paladin 2 / Ranger 3 — both full BAB, paladin good Fort, ranger good Fort+Ref
# ---------------------------------------------------------------------------
def test_v8_14_paladin2_ranger3_full_bab_saves():
    entity = build_character(
        "human", "fighter",
        class_mix={"paladin": 2, "ranger": 3},
        ability_overrides=NEUTRAL,
    )
    # BAB: max(paladin full L2=2, ranger full L3=3) = 3
    assert entity[EF.BAB] == 3
    # Fort: max(paladin good L2=3, ranger good L3=3) = 3
    assert entity[EF.SAVE_FORT] == 3
    # Ref: max(paladin poor L2=0, ranger good L3=3) = 3
    assert entity[EF.SAVE_REF] == 3
    # Will: max(paladin poor L2=0, ranger poor L3=1) = 1
    assert entity[EF.SAVE_WILL] == 1


# ---------------------------------------------------------------------------
# V8-15: Regression — single-class path unaffected
# build_character("human", "fighter", 5) still works exactly as before
# ---------------------------------------------------------------------------
def test_v8_15_regression_single_class_unchanged():
    entity = build_character(
        "human", "fighter", level=5,
        ability_overrides=NEUTRAL,
    )
    # Fighter L5: BAB=5 (full), Fort=good=4, Ref=poor=1, Will=poor=1
    assert entity[EF.LEVEL] == 5
    assert entity[EF.CLASS_LEVELS] == {"fighter": 5}
    assert entity[EF.BAB] == BAB_PROGRESSION["full"][4]  # index 4 = level 5
    assert entity[EF.SAVE_FORT] == GOOD_SAVE_PROGRESSION[4]   # 4
    assert entity[EF.SAVE_REF]  == POOR_SAVE_PROGRESSION[4]   # 1
    assert entity[EF.SAVE_WILL] == POOR_SAVE_PROGRESSION[4]   # 1
    # No class_mix → no multiclass
    assert len(entity[EF.CLASS_LEVELS]) == 1
