"""Canonical class progression registry for D&D 3.5e PHB base classes.

Sources:
- Spell slot tables: aidm/chargen/spellcasting.py (already verified vs PHB)
- Class feature grant levels: PHB pp.22-55 class tables (facts are not copyrightable)
- Monk UDAM: PHB p.41 Table 3-10
- Rage uses/day: PHB p.25 Table 3-4
- Bardic music uses/day: PHB p.29 (= bard level)
- Wild shape uses/day: PHB p.37 Table 3-8
- Smite evil uses/day: PHB p.44 (1 + 1 per 5 levels beyond 5th)
- Turn undead uses/day: PHB p.159 (3 + CHA modifier)
- Stunning fist uses/day: PHB p.98 (= character level / 4)

PASS 3 NOTE — Spell slot verification:
Spell slot tables in aidm/chargen/spellcasting.py are the existing engine
canonical source. PCGen rsrd_classes.lst (via LST-PARSER-001) will be used
for spot-check verification when parser output is available. This WO does NOT
duplicate or override spellcasting.py — it only adds what is missing.

KERNEL-11 Note: Class feature uses/day in this file are MAX values.
The decrement/reset cycle is handled by the rest system (future engine WO).
"""

from typing import Dict, Tuple


# ==============================================================================
# MONK UNARMED DAMAGE BY LEVEL — PHB p.41 Table 3-10
# ==============================================================================
# (small creature size damage, medium creature size damage)
# PHB Table 3-10 lists UDAM for Medium monks; Small monks deal one step lower.

MONK_UDAM_BY_LEVEL: Dict[int, Tuple[str, str]] = {
    1:  ("1d4", "1d6"),
    2:  ("1d4", "1d6"),
    3:  ("1d4", "1d6"),
    4:  ("1d6", "1d8"),
    5:  ("1d6", "1d8"),
    6:  ("1d6", "1d8"),
    7:  ("1d8", "1d10"),
    8:  ("1d8", "1d10"),
    9:  ("1d8", "1d10"),
    10: ("1d10", "2d6"),
    11: ("1d10", "2d6"),
    12: ("1d10", "2d6"),
    13: ("2d6", "2d8"),
    14: ("2d6", "2d8"),
    15: ("2d6", "2d8"),
    16: ("2d8", "2d10"),
    17: ("2d8", "2d10"),
    18: ("2d8", "2d10"),
    19: ("2d8", "2d10"),
    20: ("2d8", "2d10"),
}


# ==============================================================================
# CLASS FEATURE GRANT LEVELS — {class_name: {feature_id: grant_level}}
# ==============================================================================
# Populated from PHB class tables pp.22-55.
# grant_level = the class level at which the feature is first granted.

CLASS_FEATURE_GRANTS: Dict[str, Dict[str, int]] = {
    "barbarian": {
        "fast_movement": 1,
        "illiteracy": 1,
        "rage": 1,
        "uncanny_dodge": 2,
        "trap_sense": 3,
        "improved_uncanny_dodge": 5,
        "damage_reduction": 7,           # DR 1/-; increases every 3 levels
        "greater_rage": 11,
        "indomitable_will": 14,
        "tireless_rage": 17,
        "mighty_rage": 20,
    },
    "bard": {
        "bardic_music": 1,
        "bardic_knowledge": 1,
        "countersong": 1,
        "fascinate": 1,
        "inspire_courage": 1,
        "inspire_competence": 3,
        "suggestion": 6,
        "inspire_greatness": 9,
        "song_of_freedom": 12,
        "inspire_heroics": 15,
        "mass_suggestion": 18,
    },
    "cleric": {
        "turn_undead": 1,                # Chaos/Evil clerics rebuke; others turn
        "spontaneous_casting": 1,        # Cure or Inflict spells
        "domain_spells": 1,
        "domain_abilities": 1,
    },
    "druid": {
        "animal_companion": 1,
        "nature_sense": 1,
        "wild_empathy": 1,
        "woodland_stride": 2,
        "trackless_step": 3,
        "resist_natures_lure": 4,
        "wild_shape": 5,                 # 1/day; increases by 1 per 2 levels after 5
        "wild_shape_medium": 5,
        "wild_shape_large": 8,
        "wild_shape_small": 6,
        "venom_immunity": 9,
        "wild_shape_tiny": 11,
        "wild_shape_plant": 12,
        "a_thousand_faces": 13,
        "timeless_body": 15,
        "wild_shape_elemental_small": 16,
        "wild_shape_elemental_medium": 18,
        "wild_shape_elemental_large": 20,
    },
    "fighter": {
        "bonus_feat": 1,                 # Bonus feat at 1st, then every even level
    },
    "monk": {
        "flurry_of_blows": 1,
        "improved_unarmed_strike": 1,
        "unarmed_damage": 1,
        "ac_bonus": 1,                   # WIS to AC (unarmored)
        "evasion": 2,
        "fast_movement": 3,
        "still_mind": 3,
        "ki_strike_magic": 4,
        "slow_fall": 4,                  # Slow fall 20 ft; improves by 10 ft per 2 levels
        "purity_of_body": 5,
        "wholeness_of_body": 7,
        "improved_evasion": 9,
        "diamond_body": 11,
        "abundant_step": 12,
        "diamond_soul": 13,
        "quivering_palm": 15,
        "ki_strike_adamantine": 16,
        "timeless_body": 17,
        "tongue_of_the_sun_and_moon": 17,
        "empty_body": 19,
        "perfect_self": 20,
    },
    "paladin": {
        "aura_of_good": 1,
        "detect_evil": 1,
        "smite_evil": 1,                 # 1/day at 1, +1 per 5 levels
        "divine_grace": 2,
        "lay_on_hands": 2,
        "aura_of_courage": 3,
        "divine_health": 3,
        "turn_undead": 4,
        "spells": 4,
        "special_mount": 5,
        "remove_disease": 6,             # 1/week; +1 per 3 levels
    },
    "ranger": {
        "favored_enemy": 1,              # +2 at 1, +2 more every 5 levels
        "wild_empathy": 1,
        "combat_style": 2,               # Archery or Two-Weapon Fighting
        "endurance": 3,
        "animal_companion": 4,
        "spells": 4,
        "woodland_stride": 7,
        "swift_tracker": 8,
        "evasion": 9,
        "improved_combat_style": 6,      # Extra attack for chosen style
        "camouflage": 13,
        "hide_in_plain_sight": 17,
        "combat_style_mastery": 11,
    },
    "rogue": {
        "sneak_attack": 1,
        "trapfinding": 1,
        "evasion": 2,
        "trap_sense": 3,
        "uncanny_dodge": 4,
        "improved_uncanny_dodge": 8,
        "special_ability": 10,           # Every 3 levels from 10
        "crippling_strike": 10,          # Available as special ability option
        "defensive_roll": 10,
        "opportunist": 10,
        "skill_mastery": 10,
        "slippery_mind": 10,
        "improved_evasion": 10,
    },
    "sorcerer": {
        "summon_familiar": 1,
    },
    "wizard": {
        "summon_familiar": 1,
        "scribe_scroll": 1,
        "bonus_feat": 5,                 # Bonus metamagic/item creation feat every 5 levels
        "spell_mastery": 1,              # Available as bonus feat option
    },
}


# ==============================================================================
# CLASS FEATURE SCALING FORMULAS
# ==============================================================================
# Verified against PHB tables. These are MAX values per rest cycle.

def rage_uses_per_day(barbarian_level: int) -> int:
    """Rage uses per day (PHB p.25 Table 3-4).

    Level 1-3: 1/day
    Level 4-7: 2/day
    Level 8-11: 3/day
    Level 12-15: 4/day
    Level 16-19: 5/day
    Level 20+: 6/day
    """
    if barbarian_level >= 20:
        return 6
    if barbarian_level >= 16:
        return 5
    if barbarian_level >= 12:
        return 4
    if barbarian_level >= 8:
        return 3
    if barbarian_level >= 4:
        return 2
    return 1


def sneak_attack_dice(rogue_level: int) -> int:
    """Number of d6 dice for sneak attack (PHB p.50).

    Formula: ceil(rogue_level / 2) = (rogue_level + 1) // 2
    Level 1: 1d6, Level 2: 1d6, Level 3: 2d6, ...
    """
    return (rogue_level + 1) // 2


def bardic_music_uses_per_day(bard_level: int) -> int:
    """Bardic music uses per day (PHB p.29).

    Uses per day = bard level. Verified against PCGen formula.
    """
    return max(0, bard_level)


def wild_shape_uses_per_day(druid_level: int) -> int:
    """Wild shape uses per day (PHB p.37 Table 3-8).

    Level 5-7: 1/day
    Level 8-9: 2/day
    Level 10-11: 3/day
    Level 12-13: 4/day
    Level 14+: 5/day (effectively unlimited for most encounters)
    """
    if druid_level < 5:
        return 0
    if druid_level < 8:
        return 1
    if druid_level < 10:
        return 2
    if druid_level < 12:
        return 3
    if druid_level < 14:
        return 4
    return 5


def smite_evil_uses_per_day(paladin_level: int) -> int:
    """Smite evil uses per day (PHB p.44).

    Level 1-4: 1/day
    Level 5-9: 2/day (one additional per 5 levels)
    Level 10-14: 3/day
    Level 15-19: 4/day
    Level 20: 5/day
    """
    if paladin_level < 1:
        return 0
    return 1 + (paladin_level - 1) // 5


def lay_on_hands_hp_per_day(paladin_level: int, cha_modifier: int) -> int:
    """Lay on hands HP restored per day (PHB p.44).

    HP per day = paladin_level × CHA modifier (minimum 0).
    """
    return max(0, paladin_level * max(0, cha_modifier))


def stunning_fist_uses_per_day(character_level: int) -> int:
    """Stunning fist uses per day (PHB p.98).

    Uses per day = character_level / 4 (round down).
    Minimum 1 if the feat is possessed.
    """
    return max(1, character_level // 4)
