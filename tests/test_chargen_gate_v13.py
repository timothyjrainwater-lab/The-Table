"""Gate V13 -- Character Level-Up System.

WO-CHARGEN-PHASE3-LEVELUP: level_up() pure delta function.

Tests:
    V13-01  Fighter L1->L2: hp_gained >= 1, bab=2, saves correct, no feat slot
    V13-02  Fighter L2->L3: feat_slots_gained=1
    V13-03  Fighter L3->L4: bonus_feat in class_features_gained
    V13-04  Wizard L1->L2: spell_slots updated
    V13-05  Paladin L1->L2: divine_grace + lay_on_hands in class_features_gained
    V13-06  Rogue L1->L2: skill_points_gained = max(1, 8 + int_mod)
    V13-07  Human fighter L1->L2: no extra feat (human bonus already at L1)
    V13-08  HP minimum 1: CON -5 on d4 class -> hp_gained >= 1
    V13-09  HP seeded determinism: same seed -> same hp_gained
    V13-10  Multiclass fighter3/wizard2, level_up wizard->L3: BAB from fighter3
    V13-11  First class level max HP: multiclass first wizard level = d4 + CON max
    V13-12  Feat choices applied when slot opens
    V13-13  Feat choices ignored when no slot
    V13-14 level_up is pure (no mutation)
    V13-15  Invalid class raises ValueError
    V13-16  new_class_level not exactly +1 raises ValueError
    V13-17  Total level > 20 raises ValueError
    V13-18  Sorcerer L1->L2: spell_slots present (spontaneous caster)
    V13-19  Non-caster spell_slots empty
    V13-20  Barbarian L6->L7: damage_reduction_1 in class_features_gained
"""

import copy
import pytest

from aidm.chargen.builder import build_character, level_up
from aidm.schemas.entity_fields import EF
from aidm.schemas.leveling import GOOD_SAVE_PROGRESSION, POOR_SAVE_PROGRESSION


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _fighter_l1():
    return build_character(
        "human", "fighter", level=1,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 8},
    )


def _fighter_l2():
    return build_character(
        "human", "fighter", level=2,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 8},
    )


def _fighter_l3():
    return build_character(
        "human", "fighter", level=3,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 8},
    )


def _wizard_l1():
    return build_character(
        "human", "wizard", level=1,
        ability_overrides={"str": 8, "dex": 12, "con": 12, "int": 18, "wis": 10, "cha": 10},
    )


def _paladin_l1():
    return build_character(
        "human", "paladin", level=1,
        ability_overrides={"str": 16, "dex": 10, "con": 14, "int": 10, "wis": 12, "cha": 14},
    )


def _rogue_l1(int_score=14):
    return build_character(
        "human", "rogue", level=1,
        ability_overrides={"str": 10, "dex": 16, "con": 12, "int": int_score, "wis": 10, "cha": 10},
    )

# --------------------------------------------------------------------------
# V13-01: Fighter L1->L2
# --------------------------------------------------------------------------

class TestV1301FighterL1L2:
    def test_hp_gained_at_least_1(self):
        delta = level_up(_fighter_l1(), "fighter", 2, hp_seed=42)
        assert delta["hp_gained"] >= 1

    def test_bab_equals_2(self):
        delta = level_up(_fighter_l1(), "fighter", 2, hp_seed=42)
        assert delta["bab"] == 2

    def test_saves_correct(self):
        delta = level_up(_fighter_l1(), "fighter", 2, hp_seed=42)
        assert delta["saves"]["fort"] == GOOD_SAVE_PROGRESSION[1] + 2
        assert delta["saves"]["ref"]  == POOR_SAVE_PROGRESSION[1] + 1
        assert delta["saves"]["will"] == POOR_SAVE_PROGRESSION[1] + 0

    def test_no_feat_slot_at_l2(self):
        delta = level_up(_fighter_l1(), "fighter", 2, hp_seed=42)
        assert delta["feat_slots_gained"] == 0

    def test_new_total_level(self):
        delta = level_up(_fighter_l1(), "fighter", 2, hp_seed=42)
        assert delta["new_total_level"] == 2


# --------------------------------------------------------------------------
# V13-02: Fighter L2->L3 -- feat slot opens
# --------------------------------------------------------------------------

class TestV1302FighterL2L3:
    def test_feat_slot_gained(self):
        delta = level_up(_fighter_l2(), "fighter", 3, hp_seed=1)
        assert delta["feat_slots_gained"] == 1


# --------------------------------------------------------------------------
# V13-03: Fighter L3->L4 -- bonus_feat class feature
# --------------------------------------------------------------------------

class TestV1303FighterL3L4:
    def test_bonus_feat_in_class_features(self):
        delta = level_up(_fighter_l3(), "fighter", 4, hp_seed=7)
        assert "bonus_feat" in delta["class_features_gained"]


# --------------------------------------------------------------------------
# V13-04: Wizard L1->L2 -- spell_slots updated
# --------------------------------------------------------------------------

class TestV1304WizardSpellSlots:
    def test_spell_slots_present(self):
        delta = level_up(_wizard_l1(), "wizard", 2, hp_seed=5)
        assert isinstance(delta["spell_slots"], dict)
        assert len(delta["spell_slots"]) > 0

    def test_spell_slots_has_level_1(self):
        delta = level_up(_wizard_l1(), "wizard", 2, hp_seed=5)
        keys = {int(k) for k in delta["spell_slots"]}
        assert 1 in keys


# --------------------------------------------------------------------------
# V13-05: Paladin L1->L2 -- class features
# -------------------------------------------------------------------------

class TestV1305PaladinFeatures:
    def test_divine_grace_gained(self):
        delta = level_up(_paladin_l1(), "paladin", 2, hp_seed=3)
        assert "divine_grace" in delta["class_features_gained"]

    def test_lay_on_hands_gained(self):
        delta = level_up(_paladin_l1(), "paladin", 2, hp_seed=3)
        assert "lay_on_hands" in delta["class_features_gained"]


# --------------------------------------------------------------------------
# V13-06: Rogue skill points
# -------------------------------------------------------------------------

class TestV1306RogueSkillPoints:
    def test_skill_points_int_plus2(self):
        delta = level_up(_rogue_l1(int_score=14), "rogue", 2, hp_seed=9)
        assert delta["skill_points_gained"] == 10

    def test_skill_points_int_zero(self):
        delta = level_up(_rogue_l1(int_score=10), "rogue", 2, hp_seed=9)
        assert delta["skill_points_gained"] == 8


# --------------------------------------------------------------------------
# V13-07: Human no extra feat at L2
# --------------------------------------------------------------------------

class TestV1307HumanNoExtraFeat:
    def test_no_feat_slot_at_l2(self):
        delta = level_up(_fighter_l1(), "fighter", 2, hp_seed=0)
        assert delta["feat_slots_gained"] == 0

    def test_feat_choices_not_applied_without_slot(self):
        delta = level_up(_fighter_l1(), "fighter", 2,
                         feat_choices=["power_attack"], hp_seed=0)
        assert delta["feats_added"] == []


# --------------------------------------------------------------------------
# V13-08: HP minimum 1
# --------------------------------------------------------------------------

class TestV1308HpMinimum:
    def test_hp_always_at_least_1_with_large_negative_con(self):
        entity = build_character(
            "human", "sorcerer", level=1,
            ability_overrides={"str": 10, "dex": 10, "con": 1, "int": 10, "wis": 10, "cha": 18},
        )
        for seed in range(20):
            delta = level_up(entity, "sorcerer", 2, hp_seed=seed)
            assert delta["hp_gained"] >= 1, f"hp_gained < 1 at seed={seed}"


# --------------------------------------------------------------------------
# V13-09: HP seeded determinism
# --------------------------------------------------------------------------

class TestV1309HpDeterminism:
    def test_same_seed_same_hp(self):
        entity = _fighter_l1()
        assert (level_up(entity, "fighter", 2, hp_seed=1234)["hp_gained"] ==
                level_up(entity, "fighter", 2, hp_seed=1234)["hp_gained"])

    def test_different_seeds_produce_variance(self):
        entity = _fighter_l1()
        results = {level_up(entity, "fighter", 2, hp_seed=s)["hp_gained"] for s in range(50)}
        assert len(results) >= 2

# -------------------------------------------------------------------------
# V13-10: Multiclass fighter3/wizard2 -> level_up wizard->L3
# --------------------------------------------------------------------------

class TestV1310MulticlassLevelUp:
    def _entity(self):
        return build_character(
            "human", "fighter",
            class_mix={"fighter": 3, "wizard": 2},
            ability_overrides={"str": 14, "dex": 10, "con": 12, "int": 16, "wis": 10, "cha": 10},
        )

    def test_bab_uses_sum_across_classes(self):
        delta = level_up(self._entity(), "wizard", 3, hp_seed=7)
        # BAB: sum(fighter full L3=3, wizard half L3=1) = 4 (PHB p.22)
        assert delta["bab"] == 4

    def test_saves_use_sum_per_type(self):
        delta = level_up(self._entity(), "wizard", 3, hp_seed=7)
        # Fort: sum(fighter good L3=3, wizard poor L3=1) + CON(+1) = 5 (PHB p.22)
        assert delta["saves"]["fort"] == 5
        # Will: sum(fighter poor L3=1, wizard good L3=3) + WIS(0) = 4
        assert delta["saves"]["will"] == 4


# --------------------------------------------------------------------------
# V13-11: First class level max HP
# --------------------------------------------------------------------------

class TestV1311FirstClassLevelMaxHp:
    def test_first_wizard_level_takes_max_hit_die(self):
        entity = build_character(
            "human", "fighter", level=3,
            ability_overrides={"str": 16, "dex": 10, "con": 14, "int": 14, "wis": 10, "cha": 8},
        )
        delta = level_up(entity, "wizard", 1, hp_seed=999)
        assert delta["hp_gained"] == max(1, 4 + 2)


# --------------------------------------------------------------------------
# V13-12: Feat choices applied when slot opens
# --------------------------------------------------------------------------

class TestV1312FeatChoicesApplied:
    def test_feat_added_at_level_3(self):
        delta = level_up(_fighter_l2(), "fighter", 3,
                         feat_choices=["power_attack", "cleave"], hp_seed=0)
        assert delta["feat_slots_gained"] == 1
        assert delta["feats_added"] == ["power_attack"]

    def test_not_more_feats_than_slots(self):
        delta = level_up(_fighter_l2(), "fighter", 3,
                         feat_choices=["power_attack", "cleave", "weapon_focus"],
                         hp_seed=0)
        assert len(delta["feats_added"]) == delta["feat_slots_gained"]


# --------------------------------------------------------------------------
# V13-13: Feat choices ignored when no slot
# --------------------------------------------------------------------------

class TestV1313FeatChoicesIgnoredNoSlot:
    def test_no_feats_added_without_slot(self):
        delta = level_up(_fighter_l1(), "fighter", 2,
                         feat_choices=["power_attack"], hp_seed=0)
        assert delta["feat_slots_gained"] == 0
        assert delta["feats_added"] == []


# ---------------------------------------------------------------------------
# V13-14: level_up is pure
# --------------------------------------------------------------------------

class TestV1314Purity:
    def test_entity_not_mutated(self):
        entity = _fighter_l1()
        original = copy.deepcopy(entity)
        level_up(entity, "fighter", 2, hp_seed=42)
        assert entity == original

# --------------------------------------------------------------------------
# V13-15: Invalid class raises ValueError
# --------------------------------------------------------------------------

class TestV1315InvalidClass:
    def test_unknown_class_raises(self):
        with pytest.raises(ValueError, match="Unknown class"):
            level_up(_fighter_l1(), "archmage", 1)


# --------------------------------------------------------------------------
# V13-16: new_class_level not exactly +1
# --------------------------------------------------------------------------

class TestV1316InvalidNewClassLevel:
    def test_skip_level_raises(self):
        with pytest.raises(ValueError):
            level_up(_fighter_l1(), "fighter", 3)

    def test_same_level_raises(self):
        with pytest.raises(ValueError):
            level_up(_fighter_l1(), "fighter", 1)


# ---------------------------------------------------------------------------
# V13-17: Total level > 20
# --------------------------------------------------------------------------

class TestV1317TotalLevelCap:
    def test_level_21_raises(self):
        entity = build_character(
            "human", "fighter", level=20,
            ability_overrides={"str": 16, "dex": 10, "con": 14, "int": 10, "wis": 10, "cha": 8},
        )
        with pytest.raises(ValueError, match="exceed 20"):
            level_up(entity, "fighter", 21)


# ---------------------------------------------------------------------------
# V13-18: Sorcerer L1->L2 spell_slots
# --------------------------------------------------------------------------

class TestV1318SorcererSpellSlots:
    def test_spell_slots_present(self):
        entity = build_character(
            "human", "sorcerer", level=1,
            ability_overrides={"str": 8, "dex": 10, "con": 12, "int": 10, "wis": 10, "cha": 18},
        )
        delta = level_up(entity, "sorcerer", 2, hp_seed=3)
        assert isinstance(delta["spell_slots"], dict)
        assert len(delta["spell_slots"]) > 0


# ---------------------------------------------------------------------------
# V13-19: Non-caster spell_slots empty
# --------------------------------------------------------------------------

class TestV1319NonCasterSpellSlots:
    def test_fighter_spell_slots_empty(self):
        delta = level_up(_fighter_l1(), "fighter", 2, hp_seed=0)
        assert delta["spell_slots"] == {}


# --------------------------------------------------------------------------
# V13-20: Barbarian L6->L7 class features
# --------------------------------------------------------------------------

class TestV1320BarbarianClassFeatures:
    def test_damage_reduction_at_l7(self):
        entity = build_character(
            "human", "barbarian", level=6,
            ability_overrides={"str": 18, "dex": 10, "con": 16, "int": 8, "wis": 10, "cha": 8},
        )
        delta = level_up(entity, "barbarian", 7, hp_seed=5)
        assert "damage_reduction_1" in delta["class_features_gained"]
