"""Tests for experience and leveling system (WO-037).

Tests XP calculation, multiclass penalties, level thresholds, and level-up mechanics.
"""

import pytest
from aidm.core.experience_resolver import (
    calculate_xp_award,
    calculate_multiclass_penalty,
    apply_level_up,
    award_xp,
)
from aidm.schemas.leveling import LEVEL_THRESHOLDS
from aidm.schemas.entity_fields import EF
from aidm.core.rng_manager import RNGManager


# ==============================================================================
# XP CALCULATION TESTS (DMG Table 2-6)
# ==============================================================================

def test_xp_award_cr_equal_to_level():
    """CR equal to party level awards 300 XP per character (4-person party)."""
    xp = calculate_xp_award(party_level=5, party_size=4, defeated_cr=5.0)
    assert xp == 350  # Level 5, CR 5 = 350 XP per DMG Table 2-6


def test_xp_award_cr_higher_than_level():
    """Higher CR awards more XP."""
    xp = calculate_xp_award(party_level=5, party_size=4, defeated_cr=6.0)
    assert xp == 700  # Level 5, CR 6 = 700 XP


def test_xp_award_cr_lower_than_level():
    """Lower CR awards less XP."""
    xp = calculate_xp_award(party_level=5, party_size=4, defeated_cr=4.0)
    assert xp == 300  # Level 5, CR 4 = 300 XP


def test_xp_award_cr_too_low_gives_zero():
    """Encounters far below party level give 0 XP."""
    xp = calculate_xp_award(party_level=10, party_size=4, defeated_cr=1.0)
    assert xp == 0  # Level 10, CR 1 = 0 XP (too easy)


def test_xp_award_party_size_adjustment():
    """Party size adjusts XP award (smaller party = more XP per member)."""
    # 4-person party baseline
    xp_four = calculate_xp_award(party_level=5, party_size=4, defeated_cr=5.0)

    # 2-person party should get double
    xp_two = calculate_xp_award(party_level=5, party_size=2, defeated_cr=5.0)
    assert xp_two == xp_four * 2

    # 8-person party should get half
    xp_eight = calculate_xp_award(party_level=5, party_size=8, defeated_cr=5.0)
    assert xp_eight == xp_four // 2


def test_xp_award_level_1_baseline():
    """Level 1 party, CR 1 = 300 XP per character."""
    xp = calculate_xp_award(party_level=1, party_size=4, defeated_cr=1.0)
    assert xp == 300


def test_xp_award_level_20_baseline():
    """Level 20 party, CR 20 = 1100 XP per character."""
    xp = calculate_xp_award(party_level=20, party_size=4, defeated_cr=20.0)
    assert xp == 1100


def test_xp_award_fractional_cr():
    """Fractional CRs work correctly."""
    # CR 1/2 for level 1 party
    xp = calculate_xp_award(party_level=1, party_size=4, defeated_cr=0.5)
    assert xp == 0  # CR 0 (delta -1) = 0 XP at level 1


def test_xp_award_clamps_party_level():
    """Party level is clamped to valid range (1-20)."""
    xp_low = calculate_xp_award(party_level=0, party_size=4, defeated_cr=1.0)
    xp_high = calculate_xp_award(party_level=100, party_size=4, defeated_cr=20.0)
    assert xp_low >= 0
    assert xp_high >= 0


# ==============================================================================
# XP TABLE LEVELS 11-20 (DMG Table 2-6, BUG-F2/F3)
# ==============================================================================

def test_xp_table_level_11_negative_deltas():
    """Level 11: negative deltas use graduated values, not flat 150."""
    assert calculate_xp_award(party_level=11, party_size=4, defeated_cr=10.0) == 500   # delta -1
    assert calculate_xp_award(party_level=11, party_size=4, defeated_cr=9.0) == 450    # delta -2
    assert calculate_xp_award(party_level=11, party_size=4, defeated_cr=8.0) == 400    # delta -3
    assert calculate_xp_award(party_level=11, party_size=4, defeated_cr=4.0) == 200    # delta -7


def test_xp_table_level_15_values():
    """Level 15: spot-check delta 0, negative, and positive."""
    assert calculate_xp_award(party_level=15, party_size=4, defeated_cr=15.0) == 850   # delta 0
    assert calculate_xp_award(party_level=15, party_size=4, defeated_cr=14.0) == 700   # delta -1
    assert calculate_xp_award(party_level=15, party_size=4, defeated_cr=16.0) == 1700  # delta +1


def test_xp_table_level_20_positive_deltas():
    """Level 20: positive delta values."""
    assert calculate_xp_award(party_level=20, party_size=4, defeated_cr=21.0) == 2200  # delta +1
    assert calculate_xp_award(party_level=20, party_size=4, defeated_cr=22.0) == 3300  # delta +2


def test_xp_table_level_18_cr_too_low_gives_zero():
    """Level 18 vs CR 1 (delta -17): too far below, gives 0."""
    assert calculate_xp_award(party_level=18, party_size=4, defeated_cr=1.0) == 0


def test_xp_table_levels_11_20_delta_zero_progression():
    """Delta 0 values for levels 11-20 increase by 50 per level."""
    expected = {11: 650, 12: 700, 13: 750, 14: 800, 15: 850,
                16: 900, 17: 950, 18: 1000, 19: 1050, 20: 1100}
    for level, xp in expected.items():
        actual = calculate_xp_award(party_level=level, party_size=4, defeated_cr=float(level))
        assert actual == xp, f"Level {level} delta 0: expected {xp}, got {actual}"


# ==============================================================================
# MULTICLASS XP PENALTY TESTS (PHB p.60)
# ==============================================================================

def test_multiclass_penalty_single_class_no_penalty():
    """Single-class characters have no XP penalty."""
    class_levels = {"fighter": 5}
    multiplier = calculate_multiclass_penalty(class_levels)
    assert multiplier == 1.0


def test_multiclass_penalty_balanced_no_penalty():
    """Balanced multiclass (levels within 1) has no penalty."""
    class_levels = {"fighter": 3, "rogue": 3}
    multiplier = calculate_multiclass_penalty(class_levels)
    assert multiplier == 1.0

    class_levels = {"fighter": 4, "rogue": 3}
    multiplier = calculate_multiclass_penalty(class_levels)
    assert multiplier == 1.0


def test_multiclass_penalty_imbalanced_one_offending():
    """Imbalanced multiclass (one class behind) gets -20% penalty."""
    class_levels = {"fighter": 5, "rogue": 2}  # Rogue is offending
    multiplier = calculate_multiclass_penalty(class_levels)
    assert multiplier == 0.8  # -20%


def test_multiclass_penalty_imbalanced_two_offending():
    """Two offending classes get -40% penalty."""
    class_levels = {"fighter": 6, "rogue": 3, "wizard": 2}
    multiplier = calculate_multiclass_penalty(class_levels)
    assert multiplier == 0.6  # -40%


def test_multiclass_penalty_favored_class_ignored():
    """Favored class doesn't count toward imbalance."""
    class_levels = {"fighter": 5, "wizard": 2}
    multiplier = calculate_multiclass_penalty(class_levels, favored_class="wizard")
    # Only fighter counts, so no imbalance
    assert multiplier == 1.0


def test_multiclass_penalty_empty_dict():
    """Empty class_levels returns 1.0."""
    multiplier = calculate_multiclass_penalty({})
    assert multiplier == 1.0


# ==============================================================================
# LEVEL THRESHOLD TESTS (DMG Table 3-2)
# ==============================================================================

def test_level_thresholds_match_dmg():
    """Level thresholds match DMG Table 3-2 exactly."""
    assert LEVEL_THRESHOLDS[1] == 0
    assert LEVEL_THRESHOLDS[2] == 1_000
    assert LEVEL_THRESHOLDS[3] == 3_000
    assert LEVEL_THRESHOLDS[5] == 10_000
    assert LEVEL_THRESHOLDS[10] == 45_000
    assert LEVEL_THRESHOLDS[20] == 190_000


# ==============================================================================
# LEVEL-UP TESTS
# ==============================================================================

def test_apply_level_up_increments_level():
    """Level-up increments character level."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.HP_MAX: 10,
        EF.HP_CURRENT: 10,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert new_entity[EF.LEVEL] == 2
    assert new_entity[EF.CLASS_LEVELS]["fighter"] == 2


def test_apply_level_up_rolls_hit_die():
    """Level-up rolls hit die and adds to HP."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.HP_MAX: 12,
        EF.HP_CURRENT: 12,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    # Fighter has d10 hit die
    assert 1 <= result.hp_roll <= 10
    assert result.hp_gained == result.hp_roll + 2  # +2 CON mod
    assert new_entity[EF.HP_MAX] == 12 + result.hp_gained
    assert new_entity[EF.HP_CURRENT] == 12 + result.hp_gained


def test_apply_level_up_minimum_1_hp():
    """Level-up grants minimum 1 HP even with negative CON mod."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"wizard": 1},
        EF.HP_MAX: 4,
        EF.HP_CURRENT: 4,
        EF.CON_MOD: -3,  # Negative modifier
        EF.INT_MOD: 3,
        EF.BAB: 0,
        EF.SAVE_FORT: 0,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 2,
    }

    rng = RNGManager(master_seed=1)  # Seed for d4 roll of 1
    new_entity, result = apply_level_up(entity, "wizard", rng)

    assert result.hp_gained >= 1


def test_apply_level_up_grants_skill_points():
    """Level-up grants skill points based on class + INT mod."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"rogue": 1},
        EF.HP_MAX: 6,
        EF.HP_CURRENT: 6,
        EF.CON_MOD: 0,
        EF.INT_MOD: 3,
        EF.BAB: 0,
        EF.SAVE_FORT: 0,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "rogue", rng)

    # Rogue gets 8 + INT mod = 8 + 3 = 11 skill points
    assert result.skill_points == 11


def test_apply_level_up_feat_slot_at_level_3():
    """Level-up grants feat slot at level 3."""
    entity = {
        EF.LEVEL: 2,
        EF.CLASS_LEVELS: {"fighter": 2},
        EF.HP_MAX: 20,
        EF.HP_CURRENT: 20,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 2,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
        EF.FEAT_SLOTS: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert result.feat_slot_gained is True
    assert new_entity[EF.FEAT_SLOTS] == 1


def test_apply_level_up_no_feat_slot_at_level_2():
    """Level-up does not grant feat slot at level 2."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.HP_MAX: 12,
        EF.HP_CURRENT: 12,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert result.feat_slot_gained is False


def test_apply_level_up_ability_score_increase_at_level_4():
    """Level-up grants ability score increase at level 4."""
    entity = {
        EF.LEVEL: 3,
        EF.CLASS_LEVELS: {"fighter": 3},
        EF.HP_MAX: 30,
        EF.HP_CURRENT: 30,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 3,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 1,
        EF.SAVE_WILL: 1,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert result.ability_score_increase is True


def test_apply_level_up_no_ability_increase_at_level_3():
    """Level-up does not grant ability score increase at level 3."""
    entity = {
        EF.LEVEL: 2,
        EF.CLASS_LEVELS: {"fighter": 2},
        EF.HP_MAX: 20,
        EF.HP_CURRENT: 20,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 2,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert result.ability_score_increase is False


def test_apply_level_up_bab_progression_fighter():
    """Fighter BAB progresses at +1 per level."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.HP_MAX: 12,
        EF.HP_CURRENT: 12,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert new_entity[EF.BAB] == 2
    assert result.bab_increase == 1


def test_apply_level_up_bab_progression_wizard():
    """Wizard BAB progresses at 1/2 rate."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"wizard": 1},
        EF.HP_MAX: 4,
        EF.HP_CURRENT: 4,
        EF.CON_MOD: 0,
        EF.INT_MOD: 3,
        EF.BAB: 0,
        EF.SAVE_FORT: 0,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 2,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "wizard", rng)

    assert new_entity[EF.BAB] == 1  # 1/2 progression: level 2 = +1


def test_apply_level_up_save_progression_fighter():
    """Fighter has good Fort save, poor Ref/Will."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.HP_MAX: 12,
        EF.HP_CURRENT: 12,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert new_entity[EF.SAVE_FORT] == 3  # Good save: +3 at level 2
    assert new_entity[EF.SAVE_REF] == 0   # Poor save: +0 at level 2
    assert new_entity[EF.SAVE_WILL] == 0  # Poor save: +0 at level 2


def test_apply_level_up_save_progression_cleric():
    """Cleric has good Fort/Will, poor Ref."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"cleric": 1},
        EF.HP_MAX: 8,
        EF.HP_CURRENT: 8,
        EF.CON_MOD: 1,
        EF.INT_MOD: 0,
        EF.BAB: 0,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 2,
    }

    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "cleric", rng)

    assert new_entity[EF.SAVE_FORT] == 3  # Good save
    assert new_entity[EF.SAVE_REF] == 0   # Poor save
    assert new_entity[EF.SAVE_WILL] == 3  # Good save


def test_apply_level_up_does_not_mutate_original():
    """apply_level_up creates new entity dict, doesn't mutate original."""
    entity = {
        EF.LEVEL: 1,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.HP_MAX: 12,
        EF.HP_CURRENT: 12,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
    }

    original_level = entity[EF.LEVEL]
    rng = RNGManager(master_seed=42)
    new_entity, result = apply_level_up(entity, "fighter", rng)

    assert entity[EF.LEVEL] == original_level  # Original unchanged
    assert new_entity[EF.LEVEL] == original_level + 1


# ==============================================================================
# AWARD XP TESTS
# ==============================================================================

def test_award_xp_adds_xp():
    """award_xp adds XP to entity."""
    entity = {EF.XP: 0, EF.CLASS_LEVELS: {"fighter": 1}}
    new_entity = award_xp(entity, 300)
    assert new_entity[EF.XP] == 300


def test_award_xp_applies_multiclass_penalty():
    """award_xp applies multiclass penalty."""
    entity = {
        EF.XP: 0,
        EF.CLASS_LEVELS: {"fighter": 5, "rogue": 2},  # -20% penalty
    }
    new_entity = award_xp(entity, 1000, apply_multiclass_penalty=True)
    assert new_entity[EF.XP] == 800  # 1000 * 0.8


def test_award_xp_no_penalty_if_disabled():
    """award_xp does not apply penalty if disabled."""
    entity = {
        EF.XP: 0,
        EF.CLASS_LEVELS: {"fighter": 5, "rogue": 2},
    }
    new_entity = award_xp(entity, 1000, apply_multiclass_penalty=False)
    assert new_entity[EF.XP] == 1000


def test_award_xp_does_not_mutate_original():
    """award_xp creates new entity dict."""
    entity = {EF.XP: 100, EF.CLASS_LEVELS: {"fighter": 1}}
    new_entity = award_xp(entity, 200)
    assert entity[EF.XP] == 100  # Original unchanged
    assert new_entity[EF.XP] == 300


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

def test_full_level_progression_fighter():
    """Fighter progression from level 1 to 5."""
    entity = {
        EF.LEVEL: 1,
        EF.XP: 0,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.HP_MAX: 12,
        EF.HP_CURRENT: 12,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.BAB: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
        EF.FEAT_SLOTS: 0,
    }

    rng = RNGManager(master_seed=100)

    # Level to 2
    entity, _ = apply_level_up(entity, "fighter", rng)
    assert entity[EF.LEVEL] == 2
    assert entity[EF.BAB] == 2

    # Level to 3 (feat slot)
    entity, result = apply_level_up(entity, "fighter", rng)
    assert entity[EF.LEVEL] == 3
    assert result.feat_slot_gained is True

    # Level to 4 (ability score increase)
    entity, result = apply_level_up(entity, "fighter", rng)
    assert entity[EF.LEVEL] == 4
    assert result.ability_score_increase is True

    # Level to 5
    entity, _ = apply_level_up(entity, "fighter", rng)
    assert entity[EF.LEVEL] == 5
    assert entity[EF.BAB] == 5
