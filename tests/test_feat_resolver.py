"""Tests for feat resolver (WO-034: Core Feat System).

Tests cover:
- Prerequisite validation for all 15 feats
- Combat modifier computation (attack, damage, AC, initiative)
- Feat chain dependencies (Cleave requires Power Attack, etc.)
- Weapon-specific feat handling (Weapon Focus, Weapon Specialization)
- Two-Weapon Fighting penalties and extra attacks
- Special feat mechanics (Power Attack trade-off, Cleave triggering, etc.)

All tests cite PHB page numbers per D&D 3.5e rules.
"""

import pytest
from aidm.core.feat_resolver import (
    check_prerequisites,
    has_feat,
    get_attack_modifier,
    get_damage_modifier,
    get_ac_modifier,
    get_initiative_modifier,
    get_twf_penalties,
    get_twf_extra_attacks,
    ignores_shooting_into_melee_penalty,
)
from aidm.schemas.feats import FeatID, FEAT_REGISTRY, get_feat_definition
from aidm.schemas.entity_fields import EF


# ==============================================================================
# PREREQUISITE VALIDATION TESTS
# ==============================================================================

class TestPrerequisites:
    """Test feat prerequisite validation."""

    def test_power_attack_requires_str_13_bab_1(self):
        """Power Attack requires STR 13, BAB +1 (PHB p.98)."""
        # Has prerequisites
        entity = {
            EF.BASE_STATS: {"str": 13},
            EF.BAB: 1,
        }
        met, reason = check_prerequisites(entity, FeatID.POWER_ATTACK)
        assert met is True
        assert reason == ""

        # Missing STR
        entity = {
            EF.BASE_STATS: {"str": 12},
            EF.BAB: 1,
        }
        met, reason = check_prerequisites(entity, FeatID.POWER_ATTACK)
        assert met is False
        assert "STR" in reason

        # Missing BAB
        entity = {
            EF.BASE_STATS: {"str": 13},
            EF.BAB: 0,
        }
        met, reason = check_prerequisites(entity, FeatID.POWER_ATTACK)
        assert met is False
        assert "BAB" in reason

    def test_cleave_requires_str_13_power_attack(self):
        """Cleave requires STR 13, Power Attack (PHB p.92)."""
        # Has prerequisites
        entity = {
            EF.BASE_STATS: {"str": 13},
            EF.FEATS: [FeatID.POWER_ATTACK],
        }
        met, reason = check_prerequisites(entity, FeatID.CLEAVE)
        assert met is True

        # Missing Power Attack
        entity = {
            EF.BASE_STATS: {"str": 13},
            EF.FEATS: [],
        }
        met, reason = check_prerequisites(entity, FeatID.CLEAVE)
        assert met is False
        assert "Power Attack" in reason

    def test_great_cleave_requires_str_13_cleave_bab_4(self):
        """Great Cleave requires STR 13, Cleave, BAB +4 (PHB p.94)."""
        entity = {
            EF.BASE_STATS: {"str": 13},
            EF.BAB: 4,
            EF.FEATS: [FeatID.CLEAVE],
        }
        met, reason = check_prerequisites(entity, FeatID.GREAT_CLEAVE)
        assert met is True

        # Missing Cleave
        entity = {
            EF.BASE_STATS: {"str": 13},
            EF.BAB: 4,
            EF.FEATS: [],
        }
        met, reason = check_prerequisites(entity, FeatID.GREAT_CLEAVE)
        assert met is False

    def test_dodge_requires_dex_13(self):
        """Dodge requires DEX 13 (PHB p.93)."""
        entity = {
            EF.BASE_STATS: {"dex": 13},
        }
        met, reason = check_prerequisites(entity, FeatID.DODGE)
        assert met is True

        entity = {
            EF.BASE_STATS: {"dex": 12},
        }
        met, reason = check_prerequisites(entity, FeatID.DODGE)
        assert met is False
        assert "DEX" in reason

    def test_mobility_requires_dex_13_dodge(self):
        """Mobility requires DEX 13, Dodge (PHB p.98)."""
        entity = {
            EF.BASE_STATS: {"dex": 13},
            EF.FEATS: [FeatID.DODGE],
        }
        met, reason = check_prerequisites(entity, FeatID.MOBILITY)
        assert met is True

        entity = {
            EF.BASE_STATS: {"dex": 13},
            EF.FEATS: [],
        }
        met, reason = check_prerequisites(entity, FeatID.MOBILITY)
        assert met is False

    def test_spring_attack_requires_dex_13_dodge_mobility_bab_4(self):
        """Spring Attack requires DEX 13, Dodge, Mobility, BAB +4 (PHB p.100)."""
        entity = {
            EF.BASE_STATS: {"dex": 13},
            EF.BAB: 4,
            EF.FEATS: [FeatID.DODGE, FeatID.MOBILITY],
        }
        met, reason = check_prerequisites(entity, FeatID.SPRING_ATTACK)
        assert met is True

        # Missing Mobility
        entity = {
            EF.BASE_STATS: {"dex": 13},
            EF.BAB: 4,
            EF.FEATS: [FeatID.DODGE],
        }
        met, reason = check_prerequisites(entity, FeatID.SPRING_ATTACK)
        assert met is False

    def test_point_blank_shot_no_prerequisites(self):
        """Point Blank Shot has no prerequisites (PHB p.98)."""
        entity = {}
        met, reason = check_prerequisites(entity, FeatID.POINT_BLANK_SHOT)
        assert met is True

    def test_precise_shot_requires_point_blank_shot(self):
        """Precise Shot requires Point Blank Shot (PHB p.98)."""
        entity = {
            EF.FEATS: [FeatID.POINT_BLANK_SHOT],
        }
        met, reason = check_prerequisites(entity, FeatID.PRECISE_SHOT)
        assert met is True

        entity = {EF.FEATS: []}
        met, reason = check_prerequisites(entity, FeatID.PRECISE_SHOT)
        assert met is False

    def test_rapid_shot_requires_dex_13_point_blank_shot(self):
        """Rapid Shot requires DEX 13, Point Blank Shot (PHB p.99)."""
        entity = {
            EF.BASE_STATS: {"dex": 13},
            EF.FEATS: [FeatID.POINT_BLANK_SHOT],
        }
        met, reason = check_prerequisites(entity, FeatID.RAPID_SHOT)
        assert met is True

    def test_weapon_focus_requires_bab_1(self):
        """Weapon Focus requires BAB +1 (PHB p.102)."""
        entity = {EF.BAB: 1}
        met, reason = check_prerequisites(entity, "weapon_focus_longsword")
        assert met is True

        entity = {EF.BAB: 0}
        met, reason = check_prerequisites(entity, "weapon_focus_longsword")
        assert met is False

    def test_weapon_specialization_requires_weapon_focus_fighter_4(self):
        """Weapon Specialization requires Weapon Focus (same weapon), Fighter 4 (PHB p.102)."""
        # Has prerequisites
        entity = {
            EF.CLASS_LEVELS: {"fighter": 4},
            EF.FEATS: ["weapon_focus_longsword"],
        }
        met, reason = check_prerequisites(entity, "weapon_specialization_longsword")
        assert met is True

        # Missing Fighter level
        entity = {
            EF.CLASS_LEVELS: {"fighter": 3},
            EF.FEATS: ["weapon_focus_longsword"],
        }
        met, reason = check_prerequisites(entity, "weapon_specialization_longsword")
        assert met is False
        assert "Fighter" in reason

        # Missing Weapon Focus for same weapon
        entity = {
            EF.CLASS_LEVELS: {"fighter": 4},
            EF.FEATS: ["weapon_focus_greatsword"],  # Wrong weapon
        }
        met, reason = check_prerequisites(entity, "weapon_specialization_longsword")
        assert met is False
        assert "weapon_focus_longsword" in reason

    def test_two_weapon_fighting_requires_dex_15(self):
        """Two-Weapon Fighting requires DEX 15 (PHB p.102)."""
        entity = {EF.BASE_STATS: {"dex": 15}}
        met, reason = check_prerequisites(entity, FeatID.TWO_WEAPON_FIGHTING)
        assert met is True

        entity = {EF.BASE_STATS: {"dex": 14}}
        met, reason = check_prerequisites(entity, FeatID.TWO_WEAPON_FIGHTING)
        assert met is False

    def test_improved_twf_requires_dex_17_twf_bab_6(self):
        """Improved TWF requires DEX 17, TWF, BAB +6 (PHB p.96)."""
        entity = {
            EF.BASE_STATS: {"dex": 17},
            EF.BAB: 6,
            EF.FEATS: [FeatID.TWO_WEAPON_FIGHTING],
        }
        met, reason = check_prerequisites(entity, FeatID.IMPROVED_TWF)
        assert met is True

    def test_greater_twf_requires_dex_19_improved_twf_bab_11(self):
        """Greater TWF requires DEX 19, Improved TWF, BAB +11 (PHB p.94)."""
        entity = {
            EF.BASE_STATS: {"dex": 19},
            EF.BAB: 11,
            EF.FEATS: [FeatID.IMPROVED_TWF],
        }
        met, reason = check_prerequisites(entity, FeatID.GREATER_TWF)
        assert met is True

    def test_improved_initiative_no_prerequisites(self):
        """Improved Initiative has no prerequisites (PHB p.96)."""
        entity = {}
        met, reason = check_prerequisites(entity, FeatID.IMPROVED_INITIATIVE)
        assert met is True


# ==============================================================================
# ATTACK MODIFIER TESTS
# ==============================================================================

class TestAttackModifiers:
    """Test feat-based attack modifiers."""

    def test_weapon_focus_grants_plus_1_attack(self):
        """Weapon Focus grants +1 attack with chosen weapon (PHB p.102)."""
        attacker = {
            EF.FEATS: ["weapon_focus_longsword"],
        }
        context = {"weapon_name": "longsword"}

        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == 1

        # Different weapon: no bonus
        context = {"weapon_name": "greatsword"}
        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == 0

    def test_point_blank_shot_grants_plus_1_within_30ft(self):
        """Point Blank Shot grants +1 attack within 30 ft (PHB p.98)."""
        attacker = {EF.FEATS: [FeatID.POINT_BLANK_SHOT]}

        # Within 30 ft
        context = {"is_ranged": True, "range_ft": 30}
        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == 1

        # Beyond 30 ft
        context = {"is_ranged": True, "range_ft": 35}
        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == 0

        # Melee attack (not ranged)
        context = {"is_ranged": False, "range_ft": 5}
        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == 0

    def test_rapid_shot_grants_minus_2_attack(self):
        """Rapid Shot grants -2 to all attacks (PHB p.99)."""
        attacker = {EF.FEATS: [FeatID.RAPID_SHOT]}
        context = {"is_ranged": True}

        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == -2

    def test_power_attack_penalty_applied(self):
        """Power Attack applies user-chosen penalty to attack (PHB p.98)."""
        attacker = {EF.FEATS: [FeatID.POWER_ATTACK]}
        context = {"power_attack_penalty": 5}

        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == -5

    def test_combined_attack_modifiers(self):
        """Multiple feats stack correctly."""
        attacker = {
            EF.FEATS: [
                "weapon_focus_longsword",
                FeatID.POWER_ATTACK,
            ],
        }
        context = {
            "weapon_name": "longsword",
            "power_attack_penalty": 3,
        }

        modifier = get_attack_modifier(attacker, {}, context)
        assert modifier == 1 - 3  # +1 from Weapon Focus, -3 from Power Attack


# ==============================================================================
# DAMAGE MODIFIER TESTS
# ==============================================================================

class TestDamageModifiers:
    """Test feat-based damage modifiers."""

    def test_weapon_specialization_grants_plus_2_damage(self):
        """Weapon Specialization grants +2 damage with chosen weapon (PHB p.102)."""
        attacker = {
            EF.FEATS: ["weapon_specialization_longsword"],
        }
        context = {"weapon_name": "longsword"}

        modifier = get_damage_modifier(attacker, {}, context)
        assert modifier == 2

        # Different weapon: no bonus
        context = {"weapon_name": "greatsword"}
        modifier = get_damage_modifier(attacker, {}, context)
        assert modifier == 0

    def test_point_blank_shot_grants_plus_1_damage_within_30ft(self):
        """Point Blank Shot grants +1 damage within 30 ft (PHB p.98)."""
        attacker = {EF.FEATS: [FeatID.POINT_BLANK_SHOT]}

        context = {"is_ranged": True, "range_ft": 30}
        modifier = get_damage_modifier(attacker, {}, context)
        assert modifier == 1

        context = {"is_ranged": True, "range_ft": 35}
        modifier = get_damage_modifier(attacker, {}, context)
        assert modifier == 0

    def test_power_attack_1_to_1_one_handed(self):
        """Power Attack grants 1:1 damage for one-handed weapons (PHB p.98)."""
        attacker = {EF.FEATS: [FeatID.POWER_ATTACK]}
        context = {
            "power_attack_penalty": 5,
            "is_two_handed": False,
        }

        modifier = get_damage_modifier(attacker, {}, context)
        assert modifier == 5  # 1:1 trade-off

    def test_power_attack_1_to_2_two_handed(self):
        """Power Attack grants 1:2 damage for two-handed weapons (PHB p.98)."""
        attacker = {EF.FEATS: [FeatID.POWER_ATTACK]}
        context = {
            "power_attack_penalty": 5,
            "is_two_handed": True,
        }

        modifier = get_damage_modifier(attacker, {}, context)
        assert modifier == 10  # 1:2 trade-off for two-handed

    def test_combined_damage_modifiers(self):
        """Multiple damage feats stack correctly."""
        attacker = {
            EF.FEATS: [
                "weapon_specialization_greatsword",
                FeatID.POWER_ATTACK,
            ],
        }
        context = {
            "weapon_name": "greatsword",
            "power_attack_penalty": 3,
            "is_two_handed": True,
        }

        modifier = get_damage_modifier(attacker, {}, context)
        assert modifier == 2 + 6  # +2 from Weapon Spec, +6 from Power Attack (1:2)


# ==============================================================================
# AC MODIFIER TESTS
# ==============================================================================

class TestACModifiers:
    """Test feat-based AC modifiers."""

    def test_dodge_grants_plus_1_vs_designated_opponent(self):
        """Dodge grants +1 dodge AC vs designated opponent (PHB p.93)."""
        defender = {
            EF.FEATS: [FeatID.DODGE],
        }
        attacker = {EF.ENTITY_ID: "orc1"}

        # Designated target
        context = {"dodge_target": "orc1"}
        modifier = get_ac_modifier(defender, attacker, context)
        assert modifier == 1

        # Different attacker
        context = {"dodge_target": "orc2"}
        modifier = get_ac_modifier(defender, attacker, context)
        assert modifier == 0

    def test_mobility_grants_plus_4_vs_movement_aoo(self):
        """Mobility grants +4 dodge AC vs AoO from movement (PHB p.98)."""
        defender = {EF.FEATS: [FeatID.MOBILITY]}

        # Movement AoO
        context = {"is_aoo": True, "aoo_trigger": "movement_out"}
        modifier = get_ac_modifier(defender, {}, context)
        assert modifier == 4

        # Mounted movement AoO
        context = {"is_aoo": True, "aoo_trigger": "mounted_movement_out"}
        modifier = get_ac_modifier(defender, {}, context)
        assert modifier == 4

        # Non-movement AoO (e.g., ranged attack)
        context = {"is_aoo": True, "aoo_trigger": "ranged_attack"}
        modifier = get_ac_modifier(defender, {}, context)
        assert modifier == 0

        # Not an AoO
        context = {"is_aoo": False}
        modifier = get_ac_modifier(defender, {}, context)
        assert modifier == 0

    def test_dodge_and_mobility_stack(self):
        """Dodge and Mobility both apply when conditions are met."""
        defender = {
            EF.FEATS: [FeatID.DODGE, FeatID.MOBILITY],
        }
        attacker = {EF.ENTITY_ID: "orc1"}

        context = {
            "is_aoo": True,
            "aoo_trigger": "movement_out",
            "dodge_target": "orc1",
        }

        modifier = get_ac_modifier(defender, attacker, context)
        assert modifier == 5  # +1 Dodge, +4 Mobility


# ==============================================================================
# INITIATIVE MODIFIER TESTS
# ==============================================================================

class TestInitiativeModifiers:
    """Test feat-based initiative modifiers."""

    def test_improved_initiative_grants_plus_4(self):
        """Improved Initiative grants +4 initiative (PHB p.96)."""
        entity = {EF.FEATS: [FeatID.IMPROVED_INITIATIVE]}
        modifier = get_initiative_modifier(entity)
        assert modifier == 4

    def test_no_feat_grants_zero(self):
        """No initiative feat grants 0 modifier."""
        entity = {EF.FEATS: []}
        modifier = get_initiative_modifier(entity)
        assert modifier == 0


# ==============================================================================
# TWO-WEAPON FIGHTING TESTS
# ==============================================================================

class TestTwoWeaponFighting:
    """Test Two-Weapon Fighting feat chain."""

    def test_no_feat_penalties_with_light_offhand(self):
        """No TWF feat: -4 main, -8 off with light off-hand (PHB p.160)."""
        entity = {EF.FEATS: []}
        main, off = get_twf_penalties(entity, has_light_offhand=True)
        assert main == -4
        assert off == -8

    def test_no_feat_penalties_without_light_offhand(self):
        """No TWF feat: -6 main, -10 off without light off-hand (PHB p.160)."""
        entity = {EF.FEATS: []}
        main, off = get_twf_penalties(entity, has_light_offhand=False)
        assert main == -6
        assert off == -10

    def test_twf_feat_reduces_penalties(self):
        """TWF feat: -2 main, -2 off (PHB p.102)."""
        entity = {EF.FEATS: [FeatID.TWO_WEAPON_FIGHTING]}
        main, off = get_twf_penalties(entity, has_light_offhand=False)
        assert main == -2
        assert off == -2

    def test_twf_extra_attacks_base(self):
        """TWF grants 1 off-hand attack."""
        entity = {EF.FEATS: [FeatID.TWO_WEAPON_FIGHTING]}
        attacks = get_twf_extra_attacks(entity)
        assert attacks == 1

    def test_improved_twf_extra_attacks(self):
        """Improved TWF grants 2 off-hand attacks (PHB p.96)."""
        entity = {EF.FEATS: [FeatID.IMPROVED_TWF]}
        attacks = get_twf_extra_attacks(entity)
        assert attacks == 2

    def test_greater_twf_extra_attacks(self):
        """Greater TWF grants 3 off-hand attacks (PHB p.94)."""
        entity = {EF.FEATS: [FeatID.GREATER_TWF]}
        attacks = get_twf_extra_attacks(entity)
        assert attacks == 3


# ==============================================================================
# SPECIAL FEAT MECHANICS TESTS
# ==============================================================================

class TestSpecialFeatMechanics:
    """Test special feat mechanics (Cleave, Spring Attack, Precise Shot, etc.)."""

    def test_precise_shot_ignores_shooting_into_melee_penalty(self):
        """Precise Shot ignores -4 penalty for shooting into melee (PHB p.98)."""
        entity = {EF.FEATS: [FeatID.PRECISE_SHOT]}
        assert ignores_shooting_into_melee_penalty(entity) is True

        entity = {EF.FEATS: []}
        assert ignores_shooting_into_melee_penalty(entity) is False

    def test_has_feat_utility(self):
        """has_feat() utility function works correctly."""
        entity = {EF.FEATS: [FeatID.POWER_ATTACK, "weapon_focus_longsword"]}

        assert has_feat(entity, FeatID.POWER_ATTACK) is True
        assert has_feat(entity, "weapon_focus_longsword") is True
        assert has_feat(entity, FeatID.CLEAVE) is False


# ==============================================================================
# FEAT DEFINITION TESTS
# ==============================================================================

class TestFeatDefinitions:
    """Test feat registry and definition lookup."""

    def test_all_15_feats_in_registry(self):
        """All 15 feats are registered."""
        expected_feats = [
            FeatID.POWER_ATTACK,
            FeatID.CLEAVE,
            FeatID.GREAT_CLEAVE,
            FeatID.DODGE,
            FeatID.MOBILITY,
            FeatID.SPRING_ATTACK,
            FeatID.POINT_BLANK_SHOT,
            FeatID.PRECISE_SHOT,
            FeatID.RAPID_SHOT,
            FeatID.WEAPON_FOCUS,
            FeatID.WEAPON_SPECIALIZATION,
            FeatID.TWO_WEAPON_FIGHTING,
            FeatID.IMPROVED_TWF,
            FeatID.GREATER_TWF,
            FeatID.IMPROVED_INITIATIVE,
        ]

        for feat_id in expected_feats:
            assert feat_id in FEAT_REGISTRY

    def test_weapon_specific_feat_lookup(self):
        """Weapon-specific feats return base definition."""
        feat_def = get_feat_definition("weapon_focus_longsword")
        assert feat_def is not None
        assert feat_def.feat_id == FeatID.WEAPON_FOCUS

        feat_def = get_feat_definition("weapon_specialization_greatsword")
        assert feat_def is not None
        assert feat_def.feat_id == FeatID.WEAPON_SPECIALIZATION

    def test_phb_page_citations(self):
        """All feats have PHB page citations."""
        for feat_id, feat_def in FEAT_REGISTRY.items():
            assert feat_def.phb_page > 0, f"{feat_id} missing PHB page"
            assert 92 <= feat_def.phb_page <= 102, f"{feat_id} has invalid PHB page"
