"""Character builder for D&D 3.5e — assembles a complete entity dict.

WO-CHARGEN-BUILDER-001

Pulls together ability scores, racial mods, class progression, feats,
skills, and spellcasting into a single entity dict ready for the combat
engine or any other consumer.

Usage:
    from aidm.chargen.builder import build_character

    entity = build_character("human", "fighter", level=1)
    entity = build_character("elf", "wizard", level=10, ability_method="standard")
"""

import random
from typing import Dict, List, Optional, Any

from aidm.schemas.entity_fields import EF
from aidm.schemas.leveling import (
    CLASS_PROGRESSIONS,
    BAB_PROGRESSION,
    GOOD_SAVE_PROGRESSION,
    POOR_SAVE_PROGRESSION,
)
from aidm.chargen.ability_scores import (
    ABILITY_NAMES,
    ability_modifier,
    generate_ability_array,
)
from aidm.data.races import RACE_REGISTRY, get_race, apply_racial_mods
from aidm.schemas.feats import FEAT_REGISTRY, get_feat_definition
from aidm.schemas.skills import SKILLS
from aidm.chargen.spellcasting import (
    SPELLS_PER_DAY,
    CASTING_ABILITY,
    SPONTANEOUS_CASTERS,
    get_spell_slots,
    get_spells_known_count,
    get_class_spell_list,
    is_caster,
)


def _roll_hit_die(die_size: int) -> int:
    """Roll a single hit die."""
    return random.randint(1, die_size)


def _calculate_hp(
    hit_die: int,
    level: int,
    con_mod: int,
) -> int:
    """Calculate HP for a character.

    Level 1: max hit die + CON mod (minimum 1 per level).
    Levels 2+: roll hit die + CON mod each level (minimum 1 per level).

    Args:
        hit_die: Hit die size (4, 6, 8, 10, 12)
        level: Character level (1-20)
        con_mod: Constitution modifier

    Returns:
        Total HP
    """
    # Level 1: max hit die
    hp = max(1, hit_die + con_mod)

    # Levels 2+
    for _ in range(level - 1):
        roll = _roll_hit_die(hit_die)
        hp += max(1, roll + con_mod)

    return hp


def _calculate_bab(bab_type: str, level: int) -> int:
    """Get BAB for a given class type and level.

    Args:
        bab_type: "full", "threequarters", or "half"
        level: Class level (1-20)

    Returns:
        Base Attack Bonus
    """
    return BAB_PROGRESSION[bab_type][level - 1]


def _calculate_saves(
    good_saves: tuple,
    level: int,
    modifiers: Dict[str, int],
) -> Dict[str, int]:
    """Calculate saving throw bonuses.

    Args:
        good_saves: Tuple of save types with good progression ("fort", "ref", "will")
        level: Character level (1-20)
        modifiers: Dict with con_mod, dex_mod, wis_mod

    Returns:
        Dict mapping save type to total bonus
    """
    save_ability_map = {
        "fort": modifiers.get("con_mod", 0),
        "ref": modifiers.get("dex_mod", 0),
        "will": modifiers.get("wis_mod", 0),
    }

    saves = {}
    for save_type in ("fort", "ref", "will"):
        if save_type in good_saves:
            base = GOOD_SAVE_PROGRESSION[level - 1]
        else:
            base = POOR_SAVE_PROGRESSION[level - 1]
        saves[save_type] = base + save_ability_map[save_type]

    return saves


def _calculate_skill_points(
    class_name: str,
    level: int,
    int_mod: int,
    race_id: str,
) -> int:
    """Calculate total skill points available.

    Level 1: (base + INT mod + racial bonus) * 4
    Levels 2+: (base + INT mod + racial bonus) per level

    Minimum 1 skill point per level.

    Args:
        class_name: Class name
        level: Character level
        int_mod: Intelligence modifier
        race_id: Race ID (for human bonus skill points)

    Returns:
        Total skill points to allocate
    """
    progression = CLASS_PROGRESSIONS[class_name]
    race = get_race(race_id)
    base = progression.skill_points_per_level
    per_level = max(1, base + int_mod + race.bonus_skill_points_per_level)

    # Level 1 gets x4
    total = per_level * 4

    # Levels 2+
    total += per_level * (level - 1)

    return total


def _feat_slots_at_level(level: int, race_id: str) -> int:
    """Calculate total feat slots available at a given level.

    Every character gets 1 feat at level 1, then 1 more at levels 3, 6, 9, 12, 15, 18.
    Humans get +1 bonus feat at level 1.
    Fighters get bonus feats at 1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20.

    Note: Fighter bonus feats are NOT counted here — they're class-specific.
    This returns general feat slots only.

    Args:
        level: Character level (1-20)
        race_id: Race ID

    Returns:
        Total general feat slots
    """
    race = get_race(race_id)
    # 1 at level 1, +1 at every 3rd level
    slots = 1 + (level // 3)
    # Human bonus feat
    slots += race.bonus_feats
    return slots


def build_character(
    race: str,
    class_name: str,
    level: int = 1,
    ability_method: str = "standard",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a complete D&D 3.5e character entity dict.

    This is the capstone function that assembles all chargen subsystems
    into a single entity dict compatible with the combat engine.

    Args:
        race: Race ID (e.g., "human", "elf", "dwarf")
        class_name: Class name (e.g., "fighter", "wizard")
        level: Character level (1-20). Default 1.
        ability_method: "4d6", "standard", or "point_buy". Default "standard".
        ability_overrides: Manual ability scores. If provided, ability_method is ignored.
        feat_choices: List of feat_ids to assign. If None, no feats assigned.
        skill_allocations: Dict of skill_id -> ranks. If None, no skills allocated.
        spell_choices: List of spell_ids for casters. If None, no spells assigned.

    Returns:
        Complete entity dict with all EF fields populated.

    Raises:
        KeyError: If race or class_name is invalid.
        ValueError: If level is out of range.
    """
    # --- Validate inputs ---
    if race not in RACE_REGISTRY:
        raise KeyError(f"Unknown race: {race}. Available: {list(RACE_REGISTRY.keys())}")
    if class_name not in CLASS_PROGRESSIONS:
        raise KeyError(f"Unknown class: {class_name}. Available: {list(CLASS_PROGRESSIONS.keys())}")
    if level < 1 or level > 20:
        raise ValueError(f"Level must be 1-20, got {level}")

    race_def = get_race(race)
    class_prog = CLASS_PROGRESSIONS[class_name]

    # --- Step 1: Ability Scores ---
    if ability_overrides:
        base_scores = dict(ability_overrides)
    else:
        base_scores = generate_ability_array(ability_method)

    # --- Step 2: Apply racial mods ---
    final_scores = apply_racial_mods(base_scores, race)

    # --- Step 3: Calculate modifiers ---
    modifiers = {name: ability_modifier(final_scores[name]) for name in ABILITY_NAMES}

    # --- Step 4: Calculate HP ---
    hp = _calculate_hp(class_prog.hit_die, level, modifiers["con"])

    # --- Step 5: Calculate BAB ---
    bab = _calculate_bab(class_prog.bab_type, level)

    # --- Step 6: Calculate saves ---
    save_mods = {
        "con_mod": modifiers["con"],
        "dex_mod": modifiers["dex"],
        "wis_mod": modifiers["wis"],
    }
    saves = _calculate_saves(class_prog.good_saves, level, save_mods)

    # --- Step 7: Skill points & allocations ---
    total_skill_points = _calculate_skill_points(
        class_name, level, modifiers["int"], race,
    )
    skill_ranks = {}
    class_skills_list = list(class_prog.class_skills)

    if skill_allocations:
        max_rank = level + 3  # Max ranks for class skill
        max_cross = (level + 3) / 2  # Max ranks for cross-class
        for skill_id, ranks in skill_allocations.items():
            is_class_skill = skill_id in class_skills_list
            limit = max_rank if is_class_skill else max_cross
            actual_ranks = min(ranks, limit)
            skill_ranks[skill_id] = actual_ranks

    # --- Step 8: Feats ---
    feat_slot_count = _feat_slots_at_level(level, race)
    feats = []
    if feat_choices:
        feats = list(feat_choices[:feat_slot_count])

    # --- Step 9: Spellcasting ---
    spell_slots = {}
    spells_known = {}
    spells_prepared = {}
    caster_level = 0

    if is_caster(class_name):
        casting_stat = CASTING_ABILITY[class_name]
        casting_score = final_scores[casting_stat]
        caster_level = level

        spell_slots = get_spell_slots(class_name, level, casting_score)

        if class_name in SPONTANEOUS_CASTERS:
            known_counts = get_spells_known_count(class_name, level) or {}
            if spell_choices:
                # Distribute spell choices across levels
                remaining = list(spell_choices)
                for spell_level in sorted(known_counts.keys()):
                    count = known_counts[spell_level]
                    available = get_class_spell_list(class_name, spell_level)
                    level_spells = []
                    for sid in remaining[:]:
                        if sid in available and len(level_spells) < count:
                            level_spells.append(sid)
                            remaining.remove(sid)
                    if level_spells:
                        spells_known[spell_level] = level_spells
            else:
                spells_known = {lvl: [] for lvl in known_counts}
        else:
            # Prepared caster
            if spell_choices:
                from aidm.data.spell_definitions import SPELL_REGISTRY
                for sid in spell_choices:
                    if sid in SPELL_REGISTRY:
                        spell = SPELL_REGISTRY[sid]
                        slvl = spell.level
                        if slvl not in spells_prepared:
                            spells_prepared[slvl] = []
                        spells_prepared[slvl].append(sid)

    # --- Step 10: Assemble entity dict ---
    entity: Dict[str, Any] = {
        EF.ENTITY_ID: f"{race}_{class_name}_{level}",
        EF.RACE: race,
        EF.TEAM: "player",

        # Ability scores
        EF.BASE_STATS: dict(final_scores),
        EF.STR_MOD: modifiers["str"],
        EF.DEX_MOD: modifiers["dex"],
        EF.CON_MOD: modifiers["con"],
        EF.INT_MOD: modifiers["int"],
        EF.WIS_MOD: modifiers["wis"],
        EF.CHA_MOD: modifiers["cha"],

        # Hit points
        EF.HP_MAX: hp,
        EF.HP_CURRENT: hp,

        # Combat
        EF.BAB: bab,
        EF.ATTACK_BONUS: bab + modifiers["str"],  # Melee default
        EF.AC: 10 + modifiers["dex"],
        EF.DEFEATED: False,

        # Saves
        EF.SAVE_FORT: saves["fort"],
        EF.SAVE_REF: saves["ref"],
        EF.SAVE_WILL: saves["will"],

        # Level & class
        EF.LEVEL: level,
        EF.CLASS_LEVELS: {class_name: level},
        EF.XP: 0,

        # Feats
        EF.FEATS: feats,
        EF.FEAT_SLOTS: max(0, feat_slot_count - len(feats)),

        # Skills
        EF.SKILL_RANKS: skill_ranks,
        EF.CLASS_SKILLS: class_skills_list,

        # Size & Speed
        EF.SIZE_CATEGORY: race_def.size,
        EF.BASE_SPEED: race_def.base_speed,

        # Conditions
        EF.CONDITIONS: [],

        # Position
        EF.POSITION: (0, 0),
    }

    # Spellcasting fields (always present, empty for non-casters)
    entity[EF.SPELL_SLOTS] = spell_slots
    entity[EF.SPELLS_KNOWN] = spells_known
    entity[EF.SPELLS_PREPARED] = spells_prepared
    entity[EF.CASTER_LEVEL] = caster_level

    return entity
