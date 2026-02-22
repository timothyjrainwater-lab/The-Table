"""Spellcasting infrastructure for D&D 3.5e character generation.

Contains PHB spell slot tables, spells-known tables for spontaneous casters,
class spell lists, and bonus spell calculation.

WO-CHARGEN-SPELLCASTING

References:
- PHB Table 3-1 (Bard): p.27
- PHB Table 3-3 (Cleric): p.31
- PHB Table 3-5 (Druid): p.35
- PHB Table 3-12 (Paladin): p.44
- PHB Table 3-13 (Ranger): p.47
- PHB Table 3-17 (Sorcerer): p.54
- PHB Table 3-18 (Wizard): p.56
- PHB Table 1-1 (Ability Modifiers and Bonus Spells): p.8
"""

from typing import Dict, List, Optional, Tuple


# ==============================================================================
# SPELLS PER DAY TABLES (PHB Chapter 3)
# ==============================================================================
# Format: {class_level: (slot_0, slot_1, slot_2, ..., slot_9)}
# "-" in the PHB = None (can't cast that level yet)
# Note: These are BASE slots before bonus spells from high ability scores.

# PHB Table 3-18, p.56 — Wizard Spells Per Day
SPELLS_PER_DAY_WIZARD: Dict[int, Tuple[int, ...]] = {
    1:  (3, 1),
    2:  (4, 2),
    3:  (4, 2, 1),
    4:  (4, 3, 2),
    5:  (4, 3, 2, 1),
    6:  (4, 3, 3, 2),
    7:  (4, 4, 3, 2, 1),
    8:  (4, 4, 3, 3, 2),
    9:  (4, 4, 4, 3, 2, 1),
    10: (4, 4, 4, 3, 3, 2),
    11: (4, 4, 4, 4, 3, 2, 1),
    12: (4, 4, 4, 4, 3, 3, 2),
    13: (4, 4, 4, 4, 4, 3, 2, 1),
    14: (4, 4, 4, 4, 4, 3, 3, 2),
    15: (4, 4, 4, 4, 4, 4, 3, 2, 1),
    16: (4, 4, 4, 4, 4, 4, 3, 3, 2),
    17: (4, 4, 4, 4, 4, 4, 4, 3, 2, 1),
    18: (4, 4, 4, 4, 4, 4, 4, 3, 3, 2),
    19: (4, 4, 4, 4, 4, 4, 4, 4, 3, 3),
    20: (4, 4, 4, 4, 4, 4, 4, 4, 4, 4),
}

# PHB Table 3-3, p.31 — Cleric Spells Per Day
SPELLS_PER_DAY_CLERIC: Dict[int, Tuple[int, ...]] = {
    1:  (3, 1),
    2:  (4, 2),
    3:  (4, 2, 1),
    4:  (5, 3, 2),
    5:  (5, 3, 2, 1),
    6:  (5, 3, 3, 2),
    7:  (6, 4, 3, 2, 1),
    8:  (6, 4, 3, 3, 2),
    9:  (6, 4, 4, 3, 2, 1),
    10: (6, 4, 4, 3, 3, 2),
    11: (6, 5, 4, 4, 3, 2, 1),
    12: (6, 5, 4, 4, 3, 3, 2),
    13: (6, 5, 5, 4, 4, 3, 2, 1),
    14: (6, 5, 5, 4, 4, 3, 3, 2),
    15: (6, 5, 5, 5, 4, 4, 3, 2, 1),
    16: (6, 5, 5, 5, 4, 4, 3, 3, 2),
    17: (6, 5, 5, 5, 5, 4, 4, 3, 2, 1),
    18: (6, 5, 5, 5, 5, 4, 4, 3, 3, 2),
    19: (6, 5, 5, 5, 5, 5, 4, 4, 3, 3),
    20: (6, 5, 5, 5, 5, 5, 4, 4, 4, 4),
}

# PHB Table 3-5, p.35 — Druid Spells Per Day (same as Cleric)
SPELLS_PER_DAY_DRUID: Dict[int, Tuple[int, ...]] = SPELLS_PER_DAY_CLERIC.copy()

# PHB Table 3-17, p.54 — Sorcerer Spells Per Day
SPELLS_PER_DAY_SORCERER: Dict[int, Tuple[int, ...]] = {
    1:  (5, 3),
    2:  (6, 4),
    3:  (6, 5),
    4:  (6, 6, 3),
    5:  (6, 6, 4),
    6:  (6, 6, 5, 3),
    7:  (6, 6, 6, 4),
    8:  (6, 6, 6, 5, 3),
    9:  (6, 6, 6, 6, 4),
    10: (6, 6, 6, 6, 5, 3),
    11: (6, 6, 6, 6, 6, 4),
    12: (6, 6, 6, 6, 6, 5, 3),
    13: (6, 6, 6, 6, 6, 6, 4),
    14: (6, 6, 6, 6, 6, 6, 5, 3),
    15: (6, 6, 6, 6, 6, 6, 6, 4),
    16: (6, 6, 6, 6, 6, 6, 6, 5, 3),
    17: (6, 6, 6, 6, 6, 6, 6, 6, 4),
    18: (6, 6, 6, 6, 6, 6, 6, 6, 5, 3),
    19: (6, 6, 6, 6, 6, 6, 6, 6, 6, 4),
    20: (6, 6, 6, 6, 6, 6, 6, 6, 6, 6),
}

# PHB Table 3-1, p.27 — Bard Spells Per Day
SPELLS_PER_DAY_BARD: Dict[int, Tuple[int, ...]] = {
    1:  (2,),
    2:  (3, 0),
    3:  (3, 1),
    4:  (3, 2, 0),
    5:  (3, 3, 1),
    6:  (3, 3, 2),
    7:  (3, 3, 2, 0),
    8:  (3, 3, 3, 1),
    9:  (3, 3, 3, 2),
    10: (3, 3, 3, 2, 0),
    11: (3, 3, 3, 3, 1),
    12: (3, 3, 3, 3, 2),
    13: (3, 3, 3, 3, 2, 0),
    14: (4, 3, 3, 3, 3, 1),
    15: (4, 4, 3, 3, 3, 2),
    16: (4, 4, 4, 3, 3, 2, 0),
    17: (4, 4, 4, 4, 3, 3, 1),
    18: (4, 4, 4, 4, 4, 3, 2),
    19: (4, 4, 4, 4, 4, 4, 3),
    20: (4, 4, 4, 4, 4, 4, 4),
}

# PHB Table 3-13, p.47 — Ranger Spells Per Day
# Rangers gain spells at level 4+
SPELLS_PER_DAY_RANGER: Dict[int, Tuple[int, ...]] = {
    1:  (),
    2:  (),
    3:  (),
    4:  (0,),
    5:  (0,),
    6:  (1,),
    7:  (1,),
    8:  (1, 0),
    9:  (1, 0),
    10: (1, 1),
    11: (1, 1, 0),
    12: (1, 1, 1),
    13: (1, 1, 1),
    14: (2, 1, 1, 0),
    15: (2, 1, 1, 1),
    16: (2, 2, 1, 1),
    17: (2, 2, 2, 1),
    18: (3, 2, 2, 1),
    19: (3, 3, 3, 2),
    20: (3, 3, 3, 3),
}

# PHB Table 3-12, p.44 — Paladin Spells Per Day
# Paladins gain spells at level 4+
SPELLS_PER_DAY_PALADIN: Dict[int, Tuple[int, ...]] = {
    1:  (),
    2:  (),
    3:  (),
    4:  (0,),
    5:  (0,),
    6:  (1,),
    7:  (1,),
    8:  (1, 0),
    9:  (1, 0),
    10: (1, 1),
    11: (1, 1, 0),
    12: (1, 1, 1),
    13: (1, 1, 1),
    14: (2, 1, 1, 0),
    15: (2, 1, 1, 1),
    16: (2, 2, 1, 1),
    17: (2, 2, 2, 1),
    18: (3, 2, 2, 1),
    19: (3, 3, 3, 2),
    20: (3, 3, 3, 3),
}

# Master lookup
SPELLS_PER_DAY: Dict[str, Dict[int, Tuple[int, ...]]] = {
    "wizard": SPELLS_PER_DAY_WIZARD,
    "cleric": SPELLS_PER_DAY_CLERIC,
    "druid": SPELLS_PER_DAY_DRUID,
    "sorcerer": SPELLS_PER_DAY_SORCERER,
    "bard": SPELLS_PER_DAY_BARD,
    "ranger": SPELLS_PER_DAY_RANGER,
    "paladin": SPELLS_PER_DAY_PALADIN,
}


# ==============================================================================
# SPELLS KNOWN TABLES — Spontaneous casters only (PHB)
# ==============================================================================
# Format: {class_level: (known_0, known_1, known_2, ...)}
# Prepared casters (wizard, cleric, druid) don't use this table.

# PHB Table 3-17, p.54 — Sorcerer Spells Known
SPELLS_KNOWN_SORCERER: Dict[int, Tuple[int, ...]] = {
    1:  (4, 2),
    2:  (5, 2),
    3:  (5, 3),
    4:  (6, 3, 1),
    5:  (6, 4, 2),
    6:  (7, 4, 2, 1),
    7:  (7, 5, 3, 2),
    8:  (8, 5, 3, 2, 1),
    9:  (8, 5, 4, 3, 2),
    10: (9, 5, 4, 3, 2, 1),
    11: (9, 5, 5, 4, 3, 2),
    12: (9, 5, 5, 4, 3, 2, 1),
    13: (9, 5, 5, 4, 4, 3, 2),
    14: (9, 5, 5, 4, 4, 3, 2, 1),
    15: (9, 5, 5, 4, 4, 4, 3, 2),
    16: (9, 5, 5, 4, 4, 4, 3, 2, 1),
    17: (9, 5, 5, 4, 4, 4, 3, 3, 2),
    18: (9, 5, 5, 4, 4, 4, 3, 3, 2, 1),
    19: (9, 5, 5, 4, 4, 4, 3, 3, 3, 2),
    20: (9, 5, 5, 4, 4, 4, 3, 3, 3, 3),
}

# PHB Table 3-1, p.27 — Bard Spells Known
SPELLS_KNOWN_BARD: Dict[int, Tuple[int, ...]] = {
    1:  (4,),
    2:  (5, 2),
    3:  (6, 3),
    4:  (6, 3, 2),
    5:  (6, 4, 3),
    6:  (6, 4, 3),
    7:  (6, 4, 4, 2),
    8:  (6, 4, 4, 3),
    9:  (6, 4, 4, 3),
    10: (6, 4, 4, 4, 2),
    11: (6, 4, 4, 4, 3),
    12: (6, 4, 4, 4, 3),
    13: (6, 4, 4, 4, 4, 2),
    14: (6, 4, 4, 4, 4, 3),
    15: (6, 4, 4, 4, 4, 3),
    16: (6, 5, 4, 4, 4, 4, 2),
    17: (6, 5, 5, 4, 4, 4, 3),
    18: (6, 5, 5, 5, 4, 4, 3),
    19: (6, 5, 5, 5, 5, 4, 4),
    20: (6, 5, 5, 5, 5, 5, 4),
}

SPELLS_KNOWN_TABLE: Dict[str, Dict[int, Tuple[int, ...]]] = {
    "sorcerer": SPELLS_KNOWN_SORCERER,
    "bard": SPELLS_KNOWN_BARD,
}


# ==============================================================================
# CASTING ABILITY BY CLASS
# ==============================================================================
# The ability score that governs spellcasting for each class.

CASTING_ABILITY: Dict[str, str] = {
    "wizard": "int",
    "cleric": "wis",
    "druid": "wis",
    "sorcerer": "cha",
    "bard": "cha",
    "ranger": "wis",
    "paladin": "wis",
}

# Whether the class is a spontaneous caster (uses spells-known table)
# vs. prepared caster (prepares from full list)
SPONTANEOUS_CASTERS = {"sorcerer", "bard"}

# Maximum spell level each class can access
MAX_SPELL_LEVEL: Dict[str, int] = {
    "wizard": 9,
    "cleric": 9,
    "druid": 9,
    "sorcerer": 9,
    "bard": 6,
    "ranger": 4,
    "paladin": 4,
}


# ==============================================================================
# CLASS SPELL LISTS (PHB Chapter 11, class spell lists pp.192-196)
# ==============================================================================
# These define which spells each class CAN learn/prepare, by spell level.
# Only includes spells that exist in SPELL_REGISTRY.
# Format: {class_name: {spell_level: [spell_ids]}}

CLASS_SPELL_LISTS: Dict[str, Dict[int, List[str]]] = {
    "wizard": {
        0: ["detect_magic", "light", "read_magic", "resistance", "mending", "guidance"],
        1: ["magic_missile", "burning_hands", "mage_armor", "shield", "color_spray",
            "grease", "sleep"],
        2: ["scorching_ray", "acid_arrow", "invisibility", "mirror_image", "web",
            "blindness_deafness", "bulls_strength", "cats_grace", "bears_endurance",
            "owls_wisdom", "resist_energy", "silence"],
        3: ["fireball", "lightning_bolt", "haste", "slow", "fly", "dispel_magic",
            "hold_person", "stinking_cloud", "protection_from_energy",
            "magic_circle_against_evil"],
        4: ["stoneskin", "wall_of_fire", "dimension_door", "greater_invisibility",
            "ice_storm"],
        5: ["cone_of_cold", "hold_monster", "wall_of_stone", "telekinesis",
            "baleful_polymorph"],
    },
    "cleric": {
        0: ["detect_magic", "light", "read_magic", "resistance", "mending", "guidance"],
        1: ["bless", "bane", "cure_light_wounds"],
        2: ["cure_moderate_wounds", "bulls_strength", "bears_endurance", "owls_wisdom",
            "resist_energy", "silence"],
        3: ["cure_serious_wounds", "dispel_magic", "protection_from_energy",
            "magic_circle_against_evil"],
        4: ["cure_critical_wounds"],
        5: ["raise_dead"],
    },
    "druid": {
        0: ["detect_magic", "light", "read_magic", "resistance", "mending", "guidance"],
        1: ["cure_light_wounds", "entangle"],
        2: ["cure_moderate_wounds", "bulls_strength", "bears_endurance", "owls_wisdom",
            "cats_grace", "resist_energy"],
        3: ["cure_serious_wounds", "protection_from_energy"],
        4: ["cure_critical_wounds", "wall_of_fire"],
        5: ["wall_of_stone", "baleful_polymorph"],
    },
    "sorcerer": {
        0: ["detect_magic", "light", "read_magic", "resistance", "mending", "guidance"],
        1: ["magic_missile", "burning_hands", "mage_armor", "shield", "color_spray",
            "grease", "sleep"],
        2: ["scorching_ray", "acid_arrow", "invisibility", "mirror_image", "web",
            "blindness_deafness", "bulls_strength", "cats_grace", "bears_endurance",
            "resist_energy"],
        3: ["fireball", "lightning_bolt", "haste", "slow", "fly", "dispel_magic",
            "hold_person", "stinking_cloud", "protection_from_energy"],
        4: ["stoneskin", "wall_of_fire", "dimension_door", "greater_invisibility",
            "ice_storm"],
        5: ["cone_of_cold", "hold_monster", "wall_of_stone", "telekinesis",
            "baleful_polymorph"],
    },
    "bard": {
        0: ["detect_magic", "light", "read_magic", "resistance", "mending", "guidance"],
        1: ["cure_light_wounds", "grease", "sleep"],
        2: ["cure_moderate_wounds", "invisibility", "mirror_image", "silence",
            "cats_grace", "blindness_deafness"],
        3: ["cure_serious_wounds", "haste", "slow", "dispel_magic"],
        4: ["cure_critical_wounds", "dimension_door", "greater_invisibility"],
        5: ["hold_monster"],
        6: [],
    },
    "ranger": {
        1: ["entangle", "resist_energy"],
        2: ["cure_light_wounds", "cats_grace", "bears_endurance", "owls_wisdom",
            "protection_from_energy"],
        3: ["cure_moderate_wounds"],
        4: ["cure_serious_wounds"],
    },
    "paladin": {
        1: ["bless", "cure_light_wounds", "resistance"],
        2: ["cure_moderate_wounds", "bulls_strength", "bears_endurance", "owls_wisdom",
            "resist_energy"],
        3: ["cure_serious_wounds", "dispel_magic", "magic_circle_against_evil"],
        4: ["cure_critical_wounds"],
    },
}


# ==============================================================================
# BONUS SPELLS FROM HIGH ABILITY SCORES (PHB Table 1-1, p.8)
# ==============================================================================

def bonus_spells(ability_score: int) -> Dict[int, int]:
    """Calculate bonus spell slots from a high ability score.

    Per PHB Table 1-1 (p.8), a caster gets bonus spell slots for each
    spell level they can cast, based on the relevant ability score.

    A character must have an ability score of at least 10 + spell_level
    to cast spells of that level at all.

    Args:
        ability_score: The relevant casting ability score (INT for wizard, etc.)

    Returns:
        Dict mapping spell_level (1-9) to bonus slots.
        Level 0 cantrips never get bonus slots.
    """
    if ability_score < 12:
        return {}

    modifier = (ability_score - 10) // 2
    result: Dict[int, int] = {}

    for spell_level in range(1, 10):
        # Must have ability score >= 10 + spell_level to cast
        if ability_score < 10 + spell_level:
            break
        # Bonus spells = (modifier - spell_level) // 4 + 1, if modifier >= spell_level
        # Simpler: PHB formula is 1 bonus slot per 4 points of modifier above the level
        bonus = (modifier - spell_level) // 4 + 1
        if bonus > 0:
            result[spell_level] = bonus

    return result


def can_cast_spell_level(ability_score: int, spell_level: int) -> bool:
    """Check if a caster's ability score is high enough to cast a spell level.

    Per PHB p.8: To cast a spell, you need an ability score of at least
    10 + spell_level in the relevant ability.

    Args:
        ability_score: The relevant casting ability score
        spell_level: The spell level to check (0-9)

    Returns:
        True if the caster can cast spells of this level
    """
    if spell_level == 0:
        return ability_score >= 10
    return ability_score >= 10 + spell_level


def get_spell_slots(
    class_name: str,
    class_level: int,
    ability_score: int,
) -> Dict[int, int]:
    """Calculate total spell slots for a caster at a given level.

    Combines base slots from the spells-per-day table with bonus slots
    from high ability scores. A slot of 0 in the table means the caster
    gains access to that level but only through bonus spells.

    Args:
        class_name: Caster class (e.g., "wizard", "cleric")
        class_level: Class level (1-20)
        ability_score: The relevant casting ability score

    Returns:
        Dict mapping spell_level to total slot count.
        Only includes levels the character can actually cast.

    Raises:
        ValueError: If class_name is not a spellcasting class
        ValueError: If class_level is out of range
    """
    if class_name not in SPELLS_PER_DAY:
        raise ValueError(f"{class_name} is not a spellcasting class")
    if class_level < 1 or class_level > 20:
        raise ValueError(f"class_level must be 1-20, got {class_level}")

    table = SPELLS_PER_DAY[class_name]
    base_slots = table.get(class_level, ())

    if not base_slots:
        return {}

    bonus = bonus_spells(ability_score)
    result: Dict[int, int] = {}

    for spell_level, base in enumerate(base_slots):
        if not can_cast_spell_level(ability_score, spell_level):
            continue
        total = base + bonus.get(spell_level, 0)
        result[spell_level] = total

    return result


def get_spells_known_count(
    class_name: str,
    class_level: int,
) -> Optional[Dict[int, int]]:
    """Get the number of spells known per level for spontaneous casters.

    Only applicable to sorcerer and bard. Returns None for prepared casters.

    Args:
        class_name: Class name
        class_level: Class level (1-20)

    Returns:
        Dict mapping spell_level to count of spells known, or None
        if the class is a prepared caster.
    """
    if class_name not in SPELLS_KNOWN_TABLE:
        return None

    table = SPELLS_KNOWN_TABLE[class_name]
    known = table.get(class_level, ())

    if not known:
        return {}

    return {level: count for level, count in enumerate(known) if count > 0}


def get_class_spell_list(
    class_name: str,
    spell_level: int,
) -> List[str]:
    """Get the list of spell_ids available to a class at a given spell level.

    Args:
        class_name: Class name
        spell_level: Spell level (0-9)

    Returns:
        List of spell_ids. Empty list if class has no spells at that level.
    """
    class_lists = CLASS_SPELL_LISTS.get(class_name, {})
    return list(class_lists.get(spell_level, []))


def is_caster(class_name: str) -> bool:
    """Check if a class has spellcasting ability.

    Args:
        class_name: Class name

    Returns:
        True if the class can cast spells
    """
    return class_name in SPELLS_PER_DAY
