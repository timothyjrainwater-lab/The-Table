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
    CRIT_IMMUNE = "crit_immune"  # Bool: True if creature is immune to critical hits — WO-ENGINE-COUP-DE-GRACE-001

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

    # --- Spellcasting (WO-CHARGEN-SPELLCASTING) ---
    SPELLS_KNOWN = "spells_known"                  # Dict mapping spell_level → list of spell_ids known
    SPELLS_PREPARED = "spells_prepared"            # Dict mapping spell_level → list of spell_ids prepared
    SPELL_SLOTS = "spell_slots"                    # Dict mapping spell_level → int (total slots including bonus)
    CASTER_LEVEL = "caster_level"                  # Int: effective caster level for this class
    CASTER_CLASS = "caster_class"                  # Str: name of the primary caster class

    # --- Dual-Caster Spellcasting (WO-CHARGEN-DUALCASTER-001) ---
    SPELL_SLOTS_2 = "spell_slots_2"                # Second caster class slots
    SPELLS_PREPARED_2 = "spells_prepared_2"        # Second caster prepared spells
    SPELLS_KNOWN_2 = "spells_known_2"              # Second caster known spells (spontaneous)
    CASTER_CLASS_2 = "caster_class_2"              # Name of the second caster class
    CASTER_LEVEL_2 = "caster_level_2"              # Class level of second caster
    SPELL_DC_BASE = "spell_dc_base"                # WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001: 10 + casting ability modifier (Type 2)

    # --- Rest / Slot Recovery (WO-ENGINE-REST-001) ---
    SPELL_SLOTS_MAX = "spell_slots_max"            # Dict[int, int] — max slots snapshot at chargen, never decremented
    SPELL_SLOTS_MAX_2 = "spell_slots_max_2"        # Dict[int, int] — secondary caster max slots snapshot

    # --- Death / Dying (WO-ENGINE-DEATH-DYING-001) ---
    DYING = "dying"                # Bool: True if HP between -1 and -9 (inclusive)
    STABLE = "stable"              # Bool: True if formerly dying, now stable (no longer bleeding)
    DISABLED = "disabled"          # Bool: True if HP == 0 (disabled, not dying)

    # --- Nonlethal Damage (WO-ENGINE-NONLETHAL-001) ---
    NONLETHAL_DAMAGE = "nonlethal_damage"  # Int: accumulated nonlethal damage. 0 = none.

    # --- Animal Companion (WO-ENGINE-COMPANION-WIRE) ---
    COMPANION_OWNER_ID = "companion_owner_id"  # entity_id of the druid/ranger who owns this companion
    COMPANION_TYPE = "companion_type"          # companion species key: "wolf", "eagle", etc.

    # --- Turn Undead (WO-ENGINE-TURN-UNDEAD-001) ---
    TURN_UNDEAD_USES = "turn_undead_uses"          # Int: remaining turn undead uses today
    TURN_UNDEAD_USES_MAX = "turn_undead_uses_max"  # Int: max turn uses per day (3 + CHA mod, min 1)
    IS_UNDEAD = "is_undead"                        # Bool: True if creature is undead type

    # --- Domain System (WO-ENGINE-DOMAIN-SYSTEM-001, Batch V WO3) ---
    DOMAINS = "domains"  # List[str]: cleric/druid domain names, e.g. ["sun", "fire"]. Max 2 for clerics (PHB p.32). Default [].

    # --- Negative Levels (WO-ENGINE-ENERGY-DRAIN-001) ---
    NEGATIVE_LEVELS = "negative_levels"  # Int: accumulated negative levels (0 = none)

    # --- Ability Damage / Drain (WO-ENGINE-ABILITY-DAMAGE-001) ---
    STR_DAMAGE = "str_damage"          # Int: temporary STR ability damage (heals 1/night)
    DEX_DAMAGE = "dex_damage"          # Int: temporary DEX ability damage
    CON_DAMAGE = "con_damage"          # Int: temporary CON ability damage
    INT_DAMAGE = "int_damage"          # Int: temporary INT ability damage
    WIS_DAMAGE = "wis_damage"          # Int: temporary WIS ability damage
    CHA_DAMAGE = "cha_damage"          # Int: temporary CHA ability damage
    STR_DRAIN = "str_drain"            # Int: permanent STR drain (does not heal on rest)
    DEX_DRAIN = "dex_drain"            # Int: permanent DEX drain
    CON_DRAIN = "con_drain"            # Int: permanent CON drain
    INT_DRAIN = "int_drain"            # Int: permanent INT drain
    WIS_DRAIN = "wis_drain"            # Int: permanent WIS drain
    CHA_DRAIN = "cha_drain"            # Int: permanent CHA drain

    # --- Poison / Disease Tracking (WO-ENGINE-POISON-DISEASE-001) ---
    ACTIVE_POISONS = "active_poisons"      # List of poison instance dicts
    ACTIVE_DISEASES = "active_diseases"    # List of disease instance dicts

    # --- Weapon State (WO-ENGINE-SUNDER-DISARM-FULL-001) ---
    WEAPON_HP = "weapon_hp"            # Int: current HP of wielded weapon
    WEAPON_HP_MAX = "weapon_hp_max"    # Int: max HP of wielded weapon
    WEAPON_BROKEN = "weapon_broken"    # Bool: weapon has reached 0 HP (-2 attack penalty)
    WEAPON_DESTROYED = "weapon_destroyed"  # Bool: weapon is gone
    DISARMED = "disarmed"              # Bool: entity's weapon knocked away this round

    # --- Barbarian Rage (WO-ENGINE-BARBARIAN-RAGE-001) ---
    RAGE_ACTIVE = "rage_active"               # Bool: True while raging
    RAGE_USES_REMAINING = "rage_uses_remaining"  # Int: uses left this day
    RAGE_ROUNDS_REMAINING = "rage_rounds_remaining"  # Int: rounds left in current rage
    FATIGUED = "fatigued"                     # Bool: True after rage ends (until rest)

    # --- Paladin Smite Evil (WO-ENGINE-SMITE-EVIL-001) ---
    SMITE_USES_REMAINING = "smite_uses_remaining"  # Int: smite uses left today

    # --- Paladin Lay on Hands (WO-ENGINE-LAY-ON-HANDS-001) ---
    LAY_ON_HANDS_POOL = "lay_on_hands_pool"
    # int: total HP paladin can heal today via Lay on Hands.
    # = paladin_level * max(1, CHA_mod). 0 if CHA_mod <= 0.
    # Refreshes on full rest. PHB p.44.
    LAY_ON_HANDS_USED = "lay_on_hands_used"
    # int: HP already consumed from pool this day. 0 at rest.

    # --- Bardic Music (WO-ENGINE-BARDIC-MUSIC-001) ---
    BARDIC_MUSIC_USES_REMAINING = "bardic_music_uses_remaining"  # Int: uses left today
    INSPIRE_COURAGE_ACTIVE = "inspire_courage_active"   # Bool: inspire courage in effect
    INSPIRE_COURAGE_BONUS = "inspire_courage_bonus"     # Int: current morale bonus (+1 to +4)
    INSPIRE_COURAGE_ROUNDS_REMAINING = "inspire_courage_rounds_remaining"  # Int: rounds left
    INSPIRE_COURAGE_BARD_ID = "inspire_courage_bard_id"  # Str|None: entity_id of the bard who activated this effect (WO-ENGINE-BARDIC-DURATION-001)

    # --- Wild Shape (WO-ENGINE-WILD-SHAPE-001) ---
    WILD_SHAPE_USES_REMAINING = "wild_shape_uses_remaining"  # Int: uses left today
    WILD_SHAPE_ACTIVE = "wild_shape_active"         # Bool: True while wild shaped
    WILD_SHAPE_FORM = "wild_shape_form"             # Str: current animal form key
    ORIGINAL_STATS = "original_stats"               # Dict: pre-wild-shape stat snapshot (legacy alias)
    WILD_SHAPE_SAVED_STATS = "wild_shape_saved_stats"  # Dict: snapshot of original stats on transform
    WILD_SHAPE_HOURS_REMAINING = "wild_shape_hours_remaining"  # Int: hours left in form (PHB display value)
    WILD_SHAPE_ROUNDS_REMAINING = "wild_shape_rounds_remaining"  # Int: combat proxy countdown (druid_level * 10 per WO-ENGINE-WILDSHAPE-DURATION-001)
    EQUIPMENT_MELDED = "equipment_melded"           # Bool: equipment melded into form (weapon attacks blocked)
    NATURAL_ATTACKS = "natural_attacks"             # List[dict]: natural attack definitions while in form

    # --- Ranger Favored Enemy (WO-ENGINE-FAVORED-ENEMY-001) ---
    FAVORED_ENEMIES = "favored_enemies"
    # list[dict]: Ranger's favored enemy table.
    # Each entry: {"creature_type": str, "bonus": int}
    # Example: [{"creature_type": "humanoid", "bonus": 4}, {"creature_type": "undead", "bonus": 2}]
    # Populated at chargen. Empty list = no favored enemies (non-ranger).
    # PHB p.47. Bonus applies to attack rolls and damage rolls (not skills — deferred).

    CREATURE_TYPE = "creature_type"
    # str: Creature's primary type for mechanical matching.
    # PHB types: humanoid, undead, aberration, animal, construct, dragon, elemental,
    #   fey, giant, magical beast, monstrous humanoid, ooze, outsider, plant, vermin.
    # Default "": no type match (no favored enemy bonus applies).

    CREATURE_SUBTYPES = "creature_subtypes"
    # List[str]: Creature's subtypes for racial attack bonus matching.
    # WO-ENGINE-RACIAL-ATTACK-BONUS-001: dwarf +1 vs "orc"/"goblinoid"; gnome +1 vs "kobold"/"goblinoid".
    # Examples: ["orc"], ["goblinoid"], ["kobold"], [].
    # Populated in apply_racial_trait_fields() for PC races; creature_registry.py for monsters.

    # --- Racial Traits (WO-CHARGEN-RACIAL-001) ---
    SAVE_BONUS_SPELLS = "save_bonus_spells"        # Racial bonus vs spells and spell-like abilities
    STONECUNNING = "stonecunning"                  # Bool: +2 Search on stone/underground features
    ATTACK_BONUS_VS_ORCS = "attack_bonus_vs_orcs"  # +1 attack vs orcs and goblinoids (dwarf)
    DODGE_BONUS_VS_GIANTS = "dodge_bonus_vs_giants"  # +4 dodge AC vs giants (dwarf, gnome)
    LOW_LIGHT_VISION = "low_light_vision"          # Bool: low-light vision
    IMMUNE_SLEEP = "immune_sleep"                  # Bool: immunity to sleep effects
    SAVE_BONUS_ENCHANTMENT = "save_bonus_enchantment"  # Racial bonus vs enchantment spells
    AUTOMATIC_SEARCH_DOORS = "automatic_search_doors"  # Bool: 5ft passive search for secret doors
    RACIAL_SKILL_BONUS = "racial_skill_bonus"      # Dict: {skill_id: bonus_int}
    RACIAL_SAVE_BONUS = "racial_save_bonus"        # Int: bonus to all saving throws (halfling)
    ATTACK_BONUS_THROWN = "attack_bonus_thrown"    # Int: bonus to thrown weapon attacks
    SPELL_RESISTANCE_ILLUSION = "spell_resistance_illusion"  # Int: base SR vs illusion (gnome)
    ATTACK_BONUS_VS_KOBOLDS = "attack_bonus_vs_kobolds"  # +1 attack vs kobolds/goblinoids (gnome)
    ILLUSION_DC_BONUS = "illusion_dc_bonus"        # Int: bonus to illusion spell save DCs (gnome)
    DARKVISION_RANGE = "darkvision_range"          # Int: darkvision range in feet
    SAVE_BONUS_POISON = "save_bonus_poison"        # Int: racial bonus vs poison saves

    # --- Alignment (WO-ENGINE-EVIL-CLERIC-INFLICT-001) ---
    ALIGNMENT = "alignment"
    # Str: lowercase underscore — e.g. "chaotic_evil", "lawful_evil", "neutral_evil",
    # "true_neutral", "neutral_good", "chaotic_good", "lawful_good", "chaotic_neutral",
    # "lawful_neutral". Evil clerics (any *_evil) use inflict spontaneous swap.

    # --- Druid class features (WO-ENGINE-DRUID-SAVES-FEATURES-001) ---
    RESIST_NATURES_LURE = "resist_natures_lure"
    # Bool: True when druid L4+. +4 bonus on saves vs fey spell-like/supernatural abilities.
    # PHB p.36. Uses save_descriptor="fey" at call site.

    # --- Inspire Greatness temp buffs (WO-ENGINE-INSPIRE-GREATNESS-001) ---
    HP_TEMP = "hp_temp"
    # Int: temporary hit points. Lost before permanent HP. Removed when effect expires.
    INSPIRE_GREATNESS_ACTIVE = "inspire_greatness_active"
    # Bool: True while Inspire Greatness effect is running on this entity.
    INSPIRE_GREATNESS_ROUNDS_REMAINING = "inspire_greatness_rounds_remaining"
    # Int: rounds left on the effect (concentration + 5 after).
    INSPIRE_GREATNESS_BARD_ID = "inspire_greatness_bard_id"
    # Str|None: entity_id of the bard who applied the effect.

    # --- Arcane Spell Failure (WO-ENGINE-ARCANE-SPELL-FAILURE-001) ---
    ARCANE_SPELL_FAILURE = "arcane_spell_failure"
    # int: percentage chance (0-100) that arcane spells with somatic components fail.
    # 0 = no armor or divine caster. Set by chargen/equip system.


    # --- Combat Expertise (WO-ENGINE-COMBAT-EXPERTISE-001) ---
    COMBAT_EXPERTISE_BONUS = "combat_expertise_bonus"
    # int: Dodge AC bonus granted this turn by Combat Expertise declaration (PHB p.92).
    # penalty==1 -> +1 AC; penalty 2-5 -> +2 AC.
    # Cleared at start of attacker's next turn.

    # --- Evasion (WO-ENGINE-EVASION-001) ---
    EVASION = "evasion"
    # bool: True if entity has Evasion class ability (Rogue 2, Monk 2).
    # On successful Reflex save vs half-damage area effect: take 0 damage instead of half.
    # PHB Rogue p.56, Monk p.41. Armor restriction not enforced by this WO.

    IMPROVED_EVASION = "improved_evasion"
    # bool: True if entity has Improved Evasion (Rogue 10, Monk 9).
    # On failed Reflex save vs half-damage area effect: take half damage instead of full.
    # On successful save: take 0 damage (same as Evasion).
    # PHB Rogue p.57, Monk p.43.

    # --- Monk WIS-to-AC (WO-ENGINE-MONK-WIS-AC-001) ---
    MONK_WIS_AC_BONUS = "monk_wis_ac_bonus"
    # int: WIS modifier applied to monk AC at runtime (PHB p.41).
    # 0 for non-monks. Set at chargen for monks. Read in attack_resolver.
    # Applies only when unarmored (ARMOR_AC_BONUS == 0).
    # Encumbrance check deferred to encumbrance system integration.

    # --- Monk Unarmed Damage (WO-ENGINE-MONK-UNARMED-PROGRESSION-001) ---
    MONK_UNARMED_DICE = "monk_unarmed_dice"
    # str: dice expression for monk unarmed strike damage (PHB Table 3-10, p.41).
    # "1d6" at L1-3, "1d8" at L4-7, "1d10" at L8-11, "2d6" at L12-15,
    # "2d8" at L16-19, "2d10" at L20. Absent for non-monks.

    ARMOR_AC_BONUS = "armor_ac_bonus"
    # int: AC bonus from worn armor. 0 = unarmored. Set at chargen.
    # Used to gate monk WIS-to-AC and other armor-conditional features.

    ARMOR_TYPE = "armor_type"
    # str: "none" | "light" | "medium" | "heavy". Set at chargen.
    # Used to gate barbarian Fast Movement (blocked only by heavy armor, PHB p.26).

    # --- Barbarian Fast Movement (WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001) ---
    FAST_MOVEMENT_BONUS = "fast_movement_bonus"
    # int: bonus feet added to base speed (PHB p.26). 10 for barbarians, 0 for others.
    # Applied when NOT wearing heavy armor and NOT under heavy load.

    # --- Energy Resistance (WO-ENGINE-ENERGY-RESISTANCE-001) ---
    ENERGY_RESISTANCE = "energy_resistance"
    # dict[str, int]: energy type → resistance value (PHB p.291).
    # e.g., {"fire": 10, "cold": 5}. Absent key = no resistance. 0 = no resistance.
    # Resistance absorbs the first N points of that energy type per damage instance.

    # --- Defensive Casting / Concentration (WO-ENGINE-DEFENSIVE-CASTING-001) ---
    CONCENTRATION_BONUS = "concentration_bonus"
    # int: bonus to Concentration skill checks. = CON mod + skill ranks + class bonuses.
    # Used for defensive casting DC (15 + spell level), vigorous motion, violent weather, etc.
    # PHB p.69 (Concentration skill). Default 0 if not set.

    # --- Vigorous/Violent Motion (WO-ENGINE-CONCENTRATION-VIGOROUS-001) ---
    MOTION_STATE = "motion_state"
    # str | None: current motion state affecting spellcasting concentration.
    # "vigorous"  → DC 10 + spell level (fast mount, minor jostling — PHB p.69)
    # "violent"   → DC 15 + spell level (galloping, earthquake, etc. — PHB p.69)
    # None or absent → no motion penalty
    # Cleared when motion ends. Set by movement resolver / environmental triggers.

    # --- Deflection Bonus to AC (WO-ENGINE-DEFLECTION-BONUS-001) ---
    DEFLECTION_BONUS = "deflection_bonus"
    # int: deflection bonus to AC from magical sources (rings of protection, Shield of Faith, etc.)
    # PHB p.136: deflection bonuses apply vs ALL attacks including touch attacks.
    # Multiple deflection bonuses do NOT stack — only highest applies.
    # 0 = no deflection bonus (default / absent key).

    # --- Somatic Component Restriction (WO-ENGINE-SOMATIC-HAND-FREE-001) ---
    FREE_HAND_BLOCKED = "free_hand_blocked"

    # --- Monk Wholeness of Body (WO-ENGINE-WHOLENESS-OF-BODY-001) ---
    WHOLENESS_OF_BODY_POOL = "wholeness_of_body_pool"
    # int: Total HP monk can heal via Wholeness of Body today (= monk_level * 2).
    # Refreshes on full rest. PHB p.42. Unlocks at monk L7+.
    WHOLENESS_OF_BODY_USED = "wholeness_of_body_used"
    # int: HP already consumed from pool this day. 0 at rest.

    # --- Paladin Aura of Courage (WO-ENGINE-AURA-OF-COURAGE-001) ---
    FEAR_IMMUNE = "fear_immune"
    # bool: True if entity is immune to fear effects (magical or otherwise).
    # Set at chargen for paladin L2+. PHB p.44.
    # Also checked in save_resolver.get_save_bonus() when save_descriptor == "fear".
    # bool: True if caster has no free hand for somatic components (PHB p.174).
    # Set by: two-handed weapon grip, PINNED condition, hand binding.
    # When True: spells with has_somatic=True fail before ASF roll (cannot provide component).
    # FINDING-ENGINE-FREE-HAND-SETTER-001: chargen/equip WO will wire setter from
    # weapon type and condition state. This WO adds the field and guard only.


# Singleton instance — import this
EF = _EntityFields()
