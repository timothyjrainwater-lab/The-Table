"""Canonical entity field name constants.

This module is the SINGLE SOURCE OF TRUTH for all entity dict field names
used throughout the AIDM engine. Every module that reads or writes entity
fields MUST use these constants instead of bare string literals.

WHY THIS EXISTS:
A silent bug was found where permanent_stats.py used "current_hp" while
every other module used "hp_current". Using constants prevents this class
of mismatch bugs entirely.

BOUNDARY LAW: If you add a new entity field, add the constant HERE FIRST.
Any code using bare string literals for entity field keys is a latent bug
waiting to happen. The audit found three such bugs (CRIT-01, CRIT-02, D1).

RULES FOR ADDING NEW FIELDS:
1. Add the constant here FIRST, before using it in any module.
2. Use the constant in all code that reads/writes the field.
3. Document which CP introduced the field.
4. Never rename a constant after tests depend on it — add a new one
   and deprecate the old one explicitly.

SINGLE SOURCE OF TRUTH for: Entity dict field names.
CANONICAL OWNER: aidm.schemas.entity_fields (this file).

Usage:
    from aidm.schemas.entity_fields import EF

    hp = entity.get(EF.HP_CURRENT, 0)
    entity[EF.DEFEATED] = True
"""


class _EntityFields:
    """Namespace for entity field name constants.

    Access via the singleton: ``from aidm.schemas.entity_fields import EF``
    """

    # --- Identity & Meta (CP-00) ---
    ENTITY_ID = "entity_id"
    TEAM = "team"

    # --- Hit Points (CP-10) ---
    HP_CURRENT = "hp_current"
    HP_MAX = "hp_max"

    # --- Armor Class (CP-10) ---
    AC = "ac"

    # --- Combat Status (CP-10) ---
    DEFEATED = "defeated"

    # --- Ability Scores (SKR-002) ---
    BASE_STATS = "base_stats"

    # --- Ability Modifiers (CP-17) ---
    CON_MOD = "con_mod"
    DEX_MOD = "dex_mod"
    WIS_MOD = "wis_mod"
    STR_MOD = "str_mod"
    INT_MOD = "int_mod"
    CHA_MOD = "cha_mod"

    # --- Saves (CP-17) ---
    SAVE_FORT = "save_fortitude"
    SAVE_REF = "save_reflex"
    SAVE_WILL = "save_will"

    # --- Position (CP-14 / CP-15 / CP-18A-T&V) ---
    POSITION = "position"

    # --- Conditions (CP-16) ---
    CONDITIONS = "conditions"

    # --- Permanent Stat Modifiers (SKR-002) ---
    PERMANENT_STAT_MODIFIERS = "permanent_stat_modifiers"

    # --- Hit Dice (SKR-002 Phase 3) ---
    HD_COUNT = "hd_count"
    BASE_HP = "base_hp"

    # --- Spell Resistance (CP-17) ---
    SR = "sr"

    # --- Mounted Combat (CP-18A) ---
    MOUNTED_STATE = "mounted_state"      # MountedState dict on rider
    RIDER_ID = "rider_id"                # Backref on mount to rider entity ID
    MOUNT_SIZE = "mount_size"            # "medium", "large", "huge" for reach/space
    IS_MOUNT_TRAINED = "is_mount_trained"  # True for warhorse/warpony

    # --- Combat Maneuvers (CP-18) ---
    SIZE_CATEGORY = "size_category"      # "fine", "small", "medium", "large", etc.
    STABILITY_BONUS = "stability_bonus"  # +4 for dwarves, quadrupeds, etc.
    GRAPPLE_SIZE_MODIFIER = "grapple_size_modifier"  # Special scale for grapple checks

    # --- Attack (CP-10 / CP-18) ---
    ATTACK_BONUS = "attack_bonus"        # Melee/ranged attack bonus
    BAB = "bab"                          # Base Attack Bonus
    TEMPORARY_MODIFIERS = "temporary_modifiers"  # Transient buff/debuff dict
    WEAPON = "weapon"                    # Weapon data dict

    # --- Environment & Terrain (CP-19) ---
    ELEVATION = "elevation"              # Current elevation in feet (for higher ground)

    # --- Experience & Leveling (WO-037) ---
    XP = "xp"                            # Total experience points
    LEVEL = "level"                      # Total character level
    CLASS_LEVELS = "class_levels"        # Dict mapping class name to level (e.g., {"fighter": 3})
    FEAT_SLOTS = "feat_slots"            # Number of unspent feat slots

    # --- Feats (WO-034) ---
    FEATS = "feats"                      # List of feat IDs (e.g., ["power_attack", "weapon_focus_longsword"])

    # --- Skills (WO-035) ---
    SKILL_RANKS = "skill_ranks"          # Dict mapping skill_id to rank (e.g., {"tumble": 5, "hide": 3})
    CLASS_SKILLS = "class_skills"        # List of skill_ids that are class skills (e.g., ["tumble", "hide"])
    ARMOR_CHECK_PENALTY = "armor_check_penalty"  # Armor check penalty value (subtracted from relevant skills)

    # --- Damage Reduction (WO-048) ---
    DAMAGE_REDUCTIONS = "damage_reductions"  # List of DR dicts, e.g., [{"amount": 10, "bypass": "magic"}]

    # --- Concealment (WO-049) ---
    MISS_CHANCE = "miss_chance"  # Percentile miss chance (0-100), e.g., 20 for blur, 50 for invisibility

    # --- Race (WO-CHARGEN-FOUNDATION-001) ---
    RACE = "race"                                    # Race ID string (e.g., "dwarf", "halfling")

    # --- Inventory & Encumbrance (WO-054, AD-005) ---
    INVENTORY = "inventory"                        # List of item dicts: [{"item_id": "rope_hemp_50ft", "quantity": 1, "stow_location": "external"}, ...]
    STRENGTH_SCORE = "strength_score"              # Raw Strength score (integer), used for carrying capacity
    ENCUMBRANCE_LOAD = "encumbrance_load"          # Current load tier: "light", "medium", "heavy", "overloaded"
    BASE_SPEED = "base_speed"                      # Base movement speed in feet before encumbrance penalties


# Singleton instance — import this
EF = _EntityFields()
