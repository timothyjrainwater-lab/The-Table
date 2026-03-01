"""Feat definition schemas for D&D 3.5e PHB feats.

This module defines the FeatDefinition dataclass and the canonical registry
of PHB feats. Feats modify combat resolution through the feat_resolver module.

WO-034: Core Feat System (15 Feats)
WO-CHARGEN-FEATS-COMPLETE: Full PHB feat catalog (~52 feats)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class FeatDefinition:
    """Definition of a D&D 3.5e feat.

    Attributes:
        feat_id: Unique identifier (e.g., "power_attack", "dodge")
        name: Display name (e.g., "Power Attack")
        prerequisites: Prerequisite requirements dict
        modifier_type: Type of modifier ("attack", "damage", "ac", "initiative", "special")
        phb_page: PHB page number for rules citation
        description: Brief rules description
    """

    feat_id: str
    name: str
    prerequisites: Dict[str, Any]
    modifier_type: str
    phb_page: int
    description: str


# ==============================================================================
# FEAT REGISTRY — 15 Core Combat Feats
# ==============================================================================

# Feat IDs (constants for type safety)
class FeatID:
    """Feat ID constants."""
    # Melee Chain
    POWER_ATTACK = "power_attack"
    CLEAVE = "cleave"
    GREAT_CLEAVE = "great_cleave"

    # Defense Chain
    DODGE = "dodge"
    MOBILITY = "mobility"
    SPRING_ATTACK = "spring_attack"

    # Ranged Chain
    POINT_BLANK_SHOT = "point_blank_shot"
    PRECISE_SHOT = "precise_shot"
    RAPID_SHOT = "rapid_shot"

    # Weapon Chain
    WEAPON_FOCUS = "weapon_focus"  # Base ID, weapon-specific: "weapon_focus_longsword"
    WEAPON_SPECIALIZATION = "weapon_specialization"  # Base ID

    # Two-Weapon Fighting
    TWO_WEAPON_FIGHTING = "two_weapon_fighting"
    IMPROVED_TWF = "improved_two_weapon_fighting"
    GREATER_TWF = "greater_two_weapon_fighting"

    # Initiative
    IMPROVED_INITIATIVE = "improved_initiative"

    # --- WO-CHARGEN-FEATS-COMPLETE additions ---

    # Save feats
    GREAT_FORTITUDE = "great_fortitude"
    IRON_WILL = "iron_will"
    LIGHTNING_REFLEXES = "lightning_reflexes"

    # Toughness
    TOUGHNESS = "toughness"

    # Combat maneuver feats
    COMBAT_REFLEXES = "combat_reflexes"
    IMPROVED_BULL_RUSH = "improved_bull_rush"
    IMPROVED_DISARM = "improved_disarm"
    IMPROVED_FEINT = "improved_feint"
    IMPROVED_GRAPPLE = "improved_grapple"
    IMPROVED_OVERRUN = "improved_overrun"
    IMPROVED_SUNDER = "improved_sunder"
    IMPROVED_TRIP = "improved_trip"

    # Mounted feats
    MOUNTED_COMBAT = "mounted_combat"
    RIDE_BY_ATTACK = "ride_by_attack"
    SPIRITED_CHARGE = "spirited_charge"
    TRAMPLE = "trample"

    # Ranged extended
    SHOT_ON_THE_RUN = "shot_on_the_run"
    MANYSHOT = "manyshot"
    IMPROVED_CRITICAL = "improved_critical"

    # Melee extended
    BLIND_FIGHT = "blind_fight"
    COMBAT_EXPERTISE = "combat_expertise"
    WHIRLWIND_ATTACK = "whirlwind_attack"

    # Skill feats
    ALERTNESS = "alertness"
    ATHLETIC = "athletic"
    ACROBATIC = "acrobatic"
    DECEITFUL = "deceitful"
    DEFT_HANDS = "deft_hands"
    DILIGENT = "diligent"
    INVESTIGATOR = "investigator"
    NEGOTIATOR = "negotiator"
    NIMBLE_FINGERS = "nimble_fingers"
    PERSUASIVE = "persuasive"
    SELF_SUFFICIENT = "self_sufficient"
    STEALTHY = "stealthy"

    # Spell feats
    SPELL_FOCUS = "spell_focus"
    GREATER_SPELL_FOCUS = "greater_spell_focus"
    SPELL_PENETRATION = "spell_penetration"
    GREATER_SPELL_PENETRATION = "greater_spell_penetration"

    # Proficiency feats
    ARMOR_PROFICIENCY_LIGHT = "armor_proficiency_light"
    ARMOR_PROFICIENCY_MEDIUM = "armor_proficiency_medium"
    ARMOR_PROFICIENCY_HEAVY = "armor_proficiency_heavy"
    SHIELD_PROFICIENCY = "shield_proficiency"
    TOWER_SHIELD_PROFICIENCY = "tower_shield_proficiency"

    # Class-specific
    EXTRA_TURNING = "extra_turning"
    NATURAL_SPELL = "natural_spell"
    TRACK = "track"
    ENDURANCE = "endurance"
    DIEHARD = "diehard"

    # Item creation
    SCRIBE_SCROLL = "scribe_scroll"
    BREW_POTION = "brew_potion"
    CRAFT_WONDROUS_ITEM = "craft_wondrous_item"

    # --- OSS-INGESTION-SPRINT-001 additions (zellfaze CC0, source: feats.json) ---

    # Skill bonus feats
    AGILE = "agile"
    ANIMAL_AFFINITY = "animal_affinity"
    MAGICAL_APTITUDE = "magical_aptitude"
    SKILL_FOCUS = "skill_focus"

    # Weapon / combat feats
    DEFLECT_ARROWS = "deflect_arrows"
    EXOTIC_WEAPON_PROFICIENCY = "exotic_weapon_proficiency"
    FAR_SHOT = "far_shot"
    GREATER_WEAPON_FOCUS = "greater_weapon_focus"
    GREATER_WEAPON_SPECIALIZATION = "greater_weapon_specialization"
    IMPROVED_COUNTERSPELL = "improved_counterspell"
    IMPROVED_PRECISE_SHOT = "improved_precise_shot"
    IMPROVED_SHIELD_BASH = "improved_shield_bash"
    IMPROVED_TURNING = "improved_turning"
    IMPROVED_UNARMED_STRIKE = "improved_unarmed_strike"
    LEADERSHIP = "leadership"
    MARTIAL_WEAPON_PROFICIENCY = "martial_weapon_proficiency"
    MOUNTED_ARCHERY = "mounted_archery"
    QUICK_DRAW = "quick_draw"
    RAPID_RELOAD = "rapid_reload"
    RUN = "run"
    SIMPLE_WEAPON_PROFICIENCY = "simple_weapon_proficiency"
    SNATCH_ARROWS = "snatch_arrows"
    STUNNING_FIST = "stunning_fist"
    TWO_WEAPON_DEFENSE = "two_weapon_defense"
    WEAPON_FINESSE = "weapon_finesse"

    # Metamagic feats
    AUGMENT_SUMMONING = "augment_summoning"
    COMBAT_CASTING = "combat_casting"
    EMPOWER_SPELL = "empower_spell"
    ENLARGE_SPELL = "enlarge_spell"
    ESCHEW_MATERIALS = "eschew_materials"
    EXTEND_SPELL = "extend_spell"
    HEIGHTEN_SPELL = "heighten_spell"
    MAXIMIZE_SPELL = "maximize_spell"
    QUICKEN_SPELL = "quicken_spell"
    SILENT_SPELL = "silent_spell"
    SPELL_MASTERY = "spell_mastery"
    STILL_SPELL = "still_spell"
    WIDEN_SPELL = "widen_spell"

    # Item creation (additional)
    CRAFT_MAGIC_ARMS_AND_ARMOR = "craft_magic_arms_and_armor"
    CRAFT_ROD = "craft_rod"
    CRAFT_STAFF = "craft_staff"
    CRAFT_WAND = "craft_wand"
    FORGE_RING = "forge_ring"


# Feat registry
FEAT_REGISTRY: Dict[str, FeatDefinition] = {
    # -------------------------------------------------------------------------
    # MELEE CHAIN
    # -------------------------------------------------------------------------
    FeatID.POWER_ATTACK: FeatDefinition(
        feat_id=FeatID.POWER_ATTACK,
        name="Power Attack",
        prerequisites={
            "min_str": 13,
            "min_bab": 1,
        },
        modifier_type="special",
        phb_page=98,
        description="Trade attack bonus for damage (1:1 one-hand, 1:2 two-hand)"
    ),

    FeatID.CLEAVE: FeatDefinition(
        feat_id=FeatID.CLEAVE,
        name="Cleave",
        prerequisites={
            "min_str": 13,
            "required_feats": [FeatID.POWER_ATTACK],
        },
        modifier_type="special",
        phb_page=92,
        description="Free attack on adjacent enemy when you drop a foe"
    ),

    FeatID.GREAT_CLEAVE: FeatDefinition(
        feat_id=FeatID.GREAT_CLEAVE,
        name="Great Cleave",
        prerequisites={
            "min_str": 13,
            "min_bab": 4,
            "required_feats": [FeatID.CLEAVE],
        },
        modifier_type="special",
        phb_page=94,
        description="Cleave with no limit per round"
    ),

    # -------------------------------------------------------------------------
    # DEFENSE CHAIN
    # -------------------------------------------------------------------------
    FeatID.DODGE: FeatDefinition(
        feat_id=FeatID.DODGE,
        name="Dodge",
        prerequisites={
            "min_dex": 13,
        },
        modifier_type="ac",
        phb_page=93,
        description="+1 dodge AC vs one designated opponent"
    ),

    FeatID.MOBILITY: FeatDefinition(
        feat_id=FeatID.MOBILITY,
        name="Mobility",
        prerequisites={
            "min_dex": 13,
            "required_feats": [FeatID.DODGE],
        },
        modifier_type="ac",
        phb_page=98,
        description="+4 dodge AC vs AoO from movement"
    ),

    FeatID.SPRING_ATTACK: FeatDefinition(
        feat_id=FeatID.SPRING_ATTACK,
        name="Spring Attack",
        prerequisites={
            "min_dex": 13,
            "min_bab": 4,
            "required_feats": [FeatID.DODGE, FeatID.MOBILITY],
        },
        modifier_type="special",
        phb_page=100,
        description="Move before and after attack without AoO"
    ),

    # -------------------------------------------------------------------------
    # RANGED CHAIN
    # -------------------------------------------------------------------------
    FeatID.POINT_BLANK_SHOT: FeatDefinition(
        feat_id=FeatID.POINT_BLANK_SHOT,
        name="Point Blank Shot",
        prerequisites={},
        modifier_type="attack",
        phb_page=98,
        description="+1 attack and damage within 30 ft"
    ),

    FeatID.PRECISE_SHOT: FeatDefinition(
        feat_id=FeatID.PRECISE_SHOT,
        name="Precise Shot",
        prerequisites={
            "required_feats": [FeatID.POINT_BLANK_SHOT],
        },
        modifier_type="special",
        phb_page=98,
        description="No -4 penalty for shooting into melee"
    ),

    FeatID.RAPID_SHOT: FeatDefinition(
        feat_id=FeatID.RAPID_SHOT,
        name="Rapid Shot",
        prerequisites={
            "min_dex": 13,
            "required_feats": [FeatID.POINT_BLANK_SHOT],
        },
        modifier_type="attack",
        phb_page=99,
        description="Extra attack at -2 to all attacks"
    ),

    # -------------------------------------------------------------------------
    # WEAPON CHAIN (weapon-specific feat IDs handled in feat_resolver)
    # -------------------------------------------------------------------------
    FeatID.WEAPON_FOCUS: FeatDefinition(
        feat_id=FeatID.WEAPON_FOCUS,
        name="Weapon Focus",
        prerequisites={
            "min_bab": 1,
            "proficiency": True,  # Requires weapon proficiency
        },
        modifier_type="attack",
        phb_page=102,
        description="+1 attack with chosen weapon"
    ),

    FeatID.WEAPON_SPECIALIZATION: FeatDefinition(
        feat_id=FeatID.WEAPON_SPECIALIZATION,
        name="Weapon Specialization",
        prerequisites={
            "required_feats": [FeatID.WEAPON_FOCUS],  # Base check, weapon-specific validated in resolver
            "fighter_level": 4,
        },
        modifier_type="damage",
        phb_page=102,
        description="+2 damage with chosen weapon"
    ),

    # -------------------------------------------------------------------------
    # TWO-WEAPON FIGHTING CHAIN
    # -------------------------------------------------------------------------
    FeatID.TWO_WEAPON_FIGHTING: FeatDefinition(
        feat_id=FeatID.TWO_WEAPON_FIGHTING,
        name="Two-Weapon Fighting",
        prerequisites={
            "min_dex": 15,
        },
        modifier_type="special",
        phb_page=102,
        description="Reduce TWF penalties to -2/-2"
    ),

    FeatID.IMPROVED_TWF: FeatDefinition(
        feat_id=FeatID.IMPROVED_TWF,
        name="Improved Two-Weapon Fighting",
        prerequisites={
            "min_dex": 17,
            "min_bab": 6,
            "required_feats": [FeatID.TWO_WEAPON_FIGHTING],
        },
        modifier_type="special",
        phb_page=96,
        description="Second off-hand attack at -5"
    ),

    FeatID.GREATER_TWF: FeatDefinition(
        feat_id=FeatID.GREATER_TWF,
        name="Greater Two-Weapon Fighting",
        prerequisites={
            "min_dex": 19,
            "min_bab": 11,
            "required_feats": [FeatID.IMPROVED_TWF],
        },
        modifier_type="special",
        phb_page=94,
        description="Third off-hand attack at -10"
    ),

    # -------------------------------------------------------------------------
    # INITIATIVE
    # -------------------------------------------------------------------------
    FeatID.IMPROVED_INITIATIVE: FeatDefinition(
        feat_id=FeatID.IMPROVED_INITIATIVE,
        name="Improved Initiative",
        prerequisites={},
        modifier_type="initiative",
        phb_page=96,
        description="+4 initiative"
    ),

    # =========================================================================
    # SAVE FEATS (WO-CHARGEN-FEATS-COMPLETE)
    # =========================================================================
    FeatID.GREAT_FORTITUDE: FeatDefinition(
        feat_id=FeatID.GREAT_FORTITUDE,
        name="Great Fortitude",
        prerequisites={},
        modifier_type="save",
        phb_page=94,
        description="+2 Fortitude saves"
    ),
    FeatID.IRON_WILL: FeatDefinition(
        feat_id=FeatID.IRON_WILL,
        name="Iron Will",
        prerequisites={},
        modifier_type="save",
        phb_page=97,
        description="+2 Will saves"
    ),
    FeatID.LIGHTNING_REFLEXES: FeatDefinition(
        feat_id=FeatID.LIGHTNING_REFLEXES,
        name="Lightning Reflexes",
        prerequisites={},
        modifier_type="save",
        phb_page=97,
        description="+2 Reflex saves"
    ),

    # =========================================================================
    # TOUGHNESS
    # =========================================================================
    FeatID.TOUGHNESS: FeatDefinition(
        feat_id=FeatID.TOUGHNESS,
        name="Toughness",
        prerequisites={},
        modifier_type="hp",
        phb_page=101,
        description="+3 hit points"
    ),

    # =========================================================================
    # COMBAT MANEUVER FEATS
    # =========================================================================
    FeatID.COMBAT_REFLEXES: FeatDefinition(
        feat_id=FeatID.COMBAT_REFLEXES,
        name="Combat Reflexes",
        prerequisites={},
        modifier_type="special",
        phb_page=92,
        description="Additional AoO per round equal to DEX modifier"
    ),
    FeatID.IMPROVED_BULL_RUSH: FeatDefinition(
        feat_id=FeatID.IMPROVED_BULL_RUSH,
        name="Improved Bull Rush",
        prerequisites={
            "min_str": 13,
            "required_feats": ["power_attack"],
        },
        modifier_type="special",
        phb_page=95,
        description="+4 on bull rush, no AoO"
    ),
    FeatID.IMPROVED_DISARM: FeatDefinition(
        feat_id=FeatID.IMPROVED_DISARM,
        name="Improved Disarm",
        prerequisites={
            "min_int": 13,
            "required_feats": ["combat_expertise"],
        },
        modifier_type="special",
        phb_page=95,
        description="+4 on disarm, no AoO"
    ),
    FeatID.IMPROVED_FEINT: FeatDefinition(
        feat_id=FeatID.IMPROVED_FEINT,
        name="Improved Feint",
        prerequisites={
            "min_int": 13,
            "required_feats": ["combat_expertise"],
        },
        modifier_type="special",
        phb_page=95,
        description="Feint as move action instead of standard"
    ),
    FeatID.IMPROVED_GRAPPLE: FeatDefinition(
        feat_id=FeatID.IMPROVED_GRAPPLE,
        name="Improved Grapple",
        prerequisites={
            "min_dex": 13,
            "required_feats": ["improved_unarmed_strike"],
        },
        modifier_type="special",
        phb_page=95,
        description="+4 on grapple, no AoO"
    ),
    FeatID.IMPROVED_OVERRUN: FeatDefinition(
        feat_id=FeatID.IMPROVED_OVERRUN,
        name="Improved Overrun",
        prerequisites={
            "min_str": 13,
            "required_feats": ["power_attack"],
        },
        modifier_type="special",
        phb_page=96,
        description="+4 on overrun, no AoO, target can't avoid"
    ),
    FeatID.IMPROVED_SUNDER: FeatDefinition(
        feat_id=FeatID.IMPROVED_SUNDER,
        name="Improved Sunder",
        prerequisites={
            "min_str": 13,
            "required_feats": ["power_attack"],
        },
        modifier_type="special",
        phb_page=96,
        description="+4 on sunder, no AoO"
    ),
    FeatID.IMPROVED_TRIP: FeatDefinition(
        feat_id=FeatID.IMPROVED_TRIP,
        name="Improved Trip",
        prerequisites={
            "min_int": 13,
            "required_feats": ["combat_expertise"],
        },
        modifier_type="special",
        phb_page=96,
        description="+4 on trip, no AoO, free melee attack on success"
    ),

    # =========================================================================
    # MOUNTED FEATS
    # =========================================================================
    FeatID.MOUNTED_COMBAT: FeatDefinition(
        feat_id=FeatID.MOUNTED_COMBAT,
        name="Mounted Combat",
        prerequisites={
            "min_ride_ranks": 1,
        },
        modifier_type="special",
        phb_page=98,
        description="Ride check to negate hit on mount, once per round"
    ),
    FeatID.RIDE_BY_ATTACK: FeatDefinition(
        feat_id=FeatID.RIDE_BY_ATTACK,
        name="Ride-By Attack",
        prerequisites={
            "min_ride_ranks": 1,
            "required_feats": ["mounted_combat"],
        },
        modifier_type="special",
        phb_page=99,
        description="Move before and after mounted charge"
    ),
    FeatID.SPIRITED_CHARGE: FeatDefinition(
        feat_id=FeatID.SPIRITED_CHARGE,
        name="Spirited Charge",
        prerequisites={
            "min_ride_ranks": 1,
            "required_feats": ["mounted_combat", "ride_by_attack"],
        },
        modifier_type="damage",
        phb_page=100,
        description="Double damage on mounted charge (triple with lance)"
    ),
    FeatID.TRAMPLE: FeatDefinition(
        feat_id=FeatID.TRAMPLE,
        name="Trample",
        prerequisites={
            "min_ride_ranks": 1,
            "required_feats": ["mounted_combat"],
        },
        modifier_type="special",
        phb_page=101,
        description="Mount can overrun as part of charge"
    ),

    # =========================================================================
    # RANGED EXTENDED
    # =========================================================================
    FeatID.SHOT_ON_THE_RUN: FeatDefinition(
        feat_id=FeatID.SHOT_ON_THE_RUN,
        name="Shot on the Run",
        prerequisites={
            "min_dex": 13,
            "min_bab": 4,
            "required_feats": ["dodge", "mobility", "point_blank_shot"],
        },
        modifier_type="special",
        phb_page=100,
        description="Move before and after ranged attack"
    ),
    FeatID.MANYSHOT: FeatDefinition(
        feat_id=FeatID.MANYSHOT,
        name="Manyshot",
        prerequisites={
            "min_dex": 17,
            "min_bab": 6,
            "required_feats": ["point_blank_shot", "rapid_shot"],
        },
        modifier_type="special",
        phb_page=97,
        description="Fire multiple arrows as single attack"
    ),
    FeatID.IMPROVED_CRITICAL: FeatDefinition(
        feat_id=FeatID.IMPROVED_CRITICAL,
        name="Improved Critical",
        prerequisites={
            "min_bab": 8,
            "proficiency": True,
        },
        modifier_type="special",
        phb_page=95,
        description="Double threat range with chosen weapon"
    ),

    # =========================================================================
    # MELEE EXTENDED
    # =========================================================================
    FeatID.BLIND_FIGHT: FeatDefinition(
        feat_id=FeatID.BLIND_FIGHT,
        name="Blind-Fight",
        prerequisites={},
        modifier_type="special",
        phb_page=89,
        description="Reroll miss chance from concealment once"
    ),
    FeatID.COMBAT_EXPERTISE: FeatDefinition(
        feat_id=FeatID.COMBAT_EXPERTISE,
        name="Combat Expertise",
        prerequisites={
            "min_int": 13,
        },
        modifier_type="special",
        phb_page=92,
        description="Trade attack bonus for AC (up to -5/+5)"
    ),
    FeatID.WHIRLWIND_ATTACK: FeatDefinition(
        feat_id=FeatID.WHIRLWIND_ATTACK,
        name="Whirlwind Attack",
        prerequisites={
            "min_dex": 13,
            "min_int": 13,
            "min_bab": 4,
            "required_feats": ["combat_expertise", "dodge", "mobility", "spring_attack"],
        },
        modifier_type="special",
        phb_page=102,
        description="Attack all opponents within reach as full-round action"
    ),

    # =========================================================================
    # SKILL FEATS
    # =========================================================================
    FeatID.ALERTNESS: FeatDefinition(
        feat_id=FeatID.ALERTNESS,
        name="Alertness",
        prerequisites={},
        modifier_type="skill",
        phb_page=89,
        description="+2 Listen and Spot checks"
    ),
    FeatID.ATHLETIC: FeatDefinition(
        feat_id=FeatID.ATHLETIC,
        name="Athletic",
        prerequisites={},
        modifier_type="skill",
        phb_page=89,
        description="+2 Climb and Swim checks"
    ),
    FeatID.ACROBATIC: FeatDefinition(
        feat_id=FeatID.ACROBATIC,
        name="Acrobatic",
        prerequisites={},
        modifier_type="skill",
        phb_page=89,
        description="+2 Jump and Tumble checks"
    ),
    FeatID.DECEITFUL: FeatDefinition(
        feat_id=FeatID.DECEITFUL,
        name="Deceitful",
        prerequisites={},
        modifier_type="skill",
        phb_page=93,
        description="+2 Disguise and Forgery checks"
    ),
    FeatID.DEFT_HANDS: FeatDefinition(
        feat_id=FeatID.DEFT_HANDS,
        name="Deft Hands",
        prerequisites={},
        modifier_type="skill",
        phb_page=93,
        description="+2 Sleight of Hand and Use Rope checks"
    ),
    FeatID.DILIGENT: FeatDefinition(
        feat_id=FeatID.DILIGENT,
        name="Diligent",
        prerequisites={},
        modifier_type="skill",
        phb_page=93,
        description="+2 Appraise and Decipher Script checks"
    ),
    FeatID.INVESTIGATOR: FeatDefinition(
        feat_id=FeatID.INVESTIGATOR,
        name="Investigator",
        prerequisites={},
        modifier_type="skill",
        phb_page=97,
        description="+2 Gather Information and Search checks"
    ),
    FeatID.NEGOTIATOR: FeatDefinition(
        feat_id=FeatID.NEGOTIATOR,
        name="Negotiator",
        prerequisites={},
        modifier_type="skill",
        phb_page=98,
        description="+2 Diplomacy and Sense Motive checks"
    ),
    FeatID.NIMBLE_FINGERS: FeatDefinition(
        feat_id=FeatID.NIMBLE_FINGERS,
        name="Nimble Fingers",
        prerequisites={},
        modifier_type="skill",
        phb_page=98,
        description="+2 Disable Device and Open Lock checks"
    ),
    FeatID.PERSUASIVE: FeatDefinition(
        feat_id=FeatID.PERSUASIVE,
        name="Persuasive",
        prerequisites={},
        modifier_type="skill",
        phb_page=98,
        description="+2 Bluff and Intimidate checks"
    ),
    FeatID.SELF_SUFFICIENT: FeatDefinition(
        feat_id=FeatID.SELF_SUFFICIENT,
        name="Self-Sufficient",
        prerequisites={},
        modifier_type="skill",
        phb_page=100,
        description="+2 Heal and Survival checks"
    ),
    FeatID.STEALTHY: FeatDefinition(
        feat_id=FeatID.STEALTHY,
        name="Stealthy",
        prerequisites={},
        modifier_type="skill",
        phb_page=100,
        description="+2 Hide and Move Silently checks"
    ),

    # =========================================================================
    # SPELL FEATS
    # =========================================================================
    FeatID.SPELL_FOCUS: FeatDefinition(
        feat_id=FeatID.SPELL_FOCUS,
        name="Spell Focus",
        prerequisites={},
        modifier_type="spell",
        phb_page=100,
        description="+1 DC for chosen school of magic"
    ),
    FeatID.GREATER_SPELL_FOCUS: FeatDefinition(
        feat_id=FeatID.GREATER_SPELL_FOCUS,
        name="Greater Spell Focus",
        prerequisites={
            "required_feats": ["spell_focus"],
        },
        modifier_type="spell",
        phb_page=94,
        description="Additional +1 DC for chosen school (stacks with Spell Focus)"
    ),
    FeatID.SPELL_PENETRATION: FeatDefinition(
        feat_id=FeatID.SPELL_PENETRATION,
        name="Spell Penetration",
        prerequisites={},
        modifier_type="spell",
        phb_page=100,
        description="+2 caster level checks to overcome spell resistance"
    ),
    FeatID.GREATER_SPELL_PENETRATION: FeatDefinition(
        feat_id=FeatID.GREATER_SPELL_PENETRATION,
        name="Greater Spell Penetration",
        prerequisites={
            "required_feats": ["spell_penetration"],
        },
        modifier_type="spell",
        phb_page=94,
        description="Additional +2 caster level checks to overcome SR (stacks)"
    ),

    # =========================================================================
    # PROFICIENCY FEATS
    # =========================================================================
    FeatID.ARMOR_PROFICIENCY_LIGHT: FeatDefinition(
        feat_id=FeatID.ARMOR_PROFICIENCY_LIGHT,
        name="Armor Proficiency (Light)",
        prerequisites={},
        modifier_type="proficiency",
        phb_page=89,
        description="No armor check penalty on attack rolls for light armor"
    ),
    FeatID.ARMOR_PROFICIENCY_MEDIUM: FeatDefinition(
        feat_id=FeatID.ARMOR_PROFICIENCY_MEDIUM,
        name="Armor Proficiency (Medium)",
        prerequisites={
            "required_feats": ["armor_proficiency_light"],
        },
        modifier_type="proficiency",
        phb_page=89,
        description="No armor check penalty on attack rolls for medium armor"
    ),
    FeatID.ARMOR_PROFICIENCY_HEAVY: FeatDefinition(
        feat_id=FeatID.ARMOR_PROFICIENCY_HEAVY,
        name="Armor Proficiency (Heavy)",
        prerequisites={
            "required_feats": ["armor_proficiency_light", "armor_proficiency_medium"],
        },
        modifier_type="proficiency",
        phb_page=89,
        description="No armor check penalty on attack rolls for heavy armor"
    ),
    FeatID.SHIELD_PROFICIENCY: FeatDefinition(
        feat_id=FeatID.SHIELD_PROFICIENCY,
        name="Shield Proficiency",
        prerequisites={},
        modifier_type="proficiency",
        phb_page=100,
        description="No armor check penalty on attack rolls for shields"
    ),
    FeatID.TOWER_SHIELD_PROFICIENCY: FeatDefinition(
        feat_id=FeatID.TOWER_SHIELD_PROFICIENCY,
        name="Tower Shield Proficiency",
        prerequisites={
            "required_feats": ["shield_proficiency"],
        },
        modifier_type="proficiency",
        phb_page=101,
        description="No armor check penalty on attack rolls for tower shields"
    ),

    # =========================================================================
    # CLASS-SPECIFIC FEATS
    # =========================================================================
    FeatID.EXTRA_TURNING: FeatDefinition(
        feat_id=FeatID.EXTRA_TURNING,
        name="Extra Turning",
        prerequisites={
            "ability_turn_undead": True,
        },
        modifier_type="special",
        phb_page=94,
        description="+4 turning attempts per day"
    ),
    FeatID.NATURAL_SPELL: FeatDefinition(
        feat_id=FeatID.NATURAL_SPELL,
        name="Natural Spell",
        prerequisites={
            "min_wis": 13,
            "ability_wild_shape": True,
        },
        modifier_type="spell",
        phb_page=98,
        description="Cast spells while in wild shape"
    ),
    FeatID.TRACK: FeatDefinition(
        feat_id=FeatID.TRACK,
        name="Track",
        prerequisites={},
        modifier_type="skill",
        phb_page=101,
        description="Use Survival to track creatures"
    ),
    FeatID.ENDURANCE: FeatDefinition(
        feat_id=FeatID.ENDURANCE,
        name="Endurance",
        prerequisites={},
        modifier_type="special",
        phb_page=93,
        description="+4 on checks vs nonlethal damage from forced march, starvation, etc."
    ),
    FeatID.DIEHARD: FeatDefinition(
        feat_id=FeatID.DIEHARD,
        name="Diehard",
        prerequisites={
            "required_feats": ["endurance"],
        },
        modifier_type="special",
        phb_page=93,
        description="Automatically stabilize when dying, remain conscious at negative HP"
    ),

    # =========================================================================
    # ITEM CREATION FEATS
    # =========================================================================
    FeatID.SCRIBE_SCROLL: FeatDefinition(
        feat_id=FeatID.SCRIBE_SCROLL,
        name="Scribe Scroll",
        prerequisites={
            "min_caster_level": 1,
        },
        modifier_type="item_creation",
        phb_page=99,
        description="Create magic scrolls"
    ),
    FeatID.BREW_POTION: FeatDefinition(
        feat_id=FeatID.BREW_POTION,
        name="Brew Potion",
        prerequisites={
            "min_caster_level": 3,
        },
        modifier_type="item_creation",
        phb_page=89,
        description="Create magic potions (up to 3rd-level spells)"
    ),
    FeatID.CRAFT_WONDROUS_ITEM: FeatDefinition(
        feat_id=FeatID.CRAFT_WONDROUS_ITEM,
        name="Craft Wondrous Item",
        prerequisites={
            "min_caster_level": 3,
        },
        modifier_type="item_creation",
        phb_page=92,
        description="Create miscellaneous magic items"
    ),

    # =========================================================================
    # OSS-INGESTION-SPRINT-001 — zellfaze CC0 (feats.json, 109 feats)
    # 43 novel feats not previously in registry
    # =========================================================================

    # --- Skill Bonus Feats ---
    FeatID.AGILE: FeatDefinition(
        feat_id=FeatID.AGILE,
        name="Agile",
        prerequisites={},
        modifier_type="skill",
        phb_page=89,
        description="+2 Balance, +2 Escape Artist"
    ),
    FeatID.ANIMAL_AFFINITY: FeatDefinition(
        feat_id=FeatID.ANIMAL_AFFINITY,
        name="Animal Affinity",
        prerequisites={},
        modifier_type="skill",
        phb_page=89,
        description="+2 Handle Animal, +2 Ride"
    ),
    FeatID.MAGICAL_APTITUDE: FeatDefinition(
        feat_id=FeatID.MAGICAL_APTITUDE,
        name="Magical Aptitude",
        prerequisites={},
        modifier_type="skill",
        phb_page=97,
        description="+2 Spellcraft, +2 Use Magic Device"
    ),
    FeatID.SKILL_FOCUS: FeatDefinition(
        feat_id=FeatID.SKILL_FOCUS,
        name="Skill Focus",
        prerequisites={},
        modifier_type="skill",
        phb_page=100,
        description="+3 to one selected skill"
    ),

    # --- Combat / Weapon Feats ---
    FeatID.DEFLECT_ARROWS: FeatDefinition(
        feat_id=FeatID.DEFLECT_ARROWS,
        name="Deflect Arrows",
        prerequisites={
            "min_dex": 13,
            "required_feats": [FeatID.IMPROVED_UNARMED_STRIKE],
        },
        modifier_type="special",
        phb_page=93,
        description="Once per round deflect one non-magical ranged attack"
    ),
    FeatID.EXOTIC_WEAPON_PROFICIENCY: FeatDefinition(
        feat_id=FeatID.EXOTIC_WEAPON_PROFICIENCY,
        name="Exotic Weapon Proficiency",
        prerequisites={
            "min_bab": 1,
        },
        modifier_type="special",
        phb_page=94,
        description="Proficiency with one selected exotic weapon"
    ),
    FeatID.FAR_SHOT: FeatDefinition(
        feat_id=FeatID.FAR_SHOT,
        name="Far Shot",
        prerequisites={
            "required_feats": [FeatID.POINT_BLANK_SHOT],
        },
        modifier_type="special",
        phb_page=94,
        description="Increase projectile range by 50%; double thrown weapon range"
    ),
    FeatID.GREATER_WEAPON_FOCUS: FeatDefinition(
        feat_id=FeatID.GREATER_WEAPON_FOCUS,
        name="Greater Weapon Focus",
        prerequisites={
            "required_feats": [FeatID.WEAPON_FOCUS],
            "min_class_level": {"fighter": 8},
        },
        modifier_type="attack",
        phb_page=94,
        description="+1 attack with selected weapon (stacks with Weapon Focus)"
    ),
    FeatID.GREATER_WEAPON_SPECIALIZATION: FeatDefinition(
        feat_id=FeatID.GREATER_WEAPON_SPECIALIZATION,
        name="Greater Weapon Specialization",
        prerequisites={
            "required_feats": [FeatID.WEAPON_SPECIALIZATION, FeatID.GREATER_WEAPON_FOCUS],
            "min_class_level": {"fighter": 12},
        },
        modifier_type="damage",
        phb_page=94,
        description="+2 damage with selected weapon (stacks with Weapon Specialization)"
    ),
    FeatID.IMPROVED_COUNTERSPELL: FeatDefinition(
        feat_id=FeatID.IMPROVED_COUNTERSPELL,
        name="Improved Counterspell",
        prerequisites={},
        modifier_type="special",
        phb_page=95,
        description="Counter with same-school spell of equal or higher level"
    ),
    FeatID.IMPROVED_PRECISE_SHOT: FeatDefinition(
        feat_id=FeatID.IMPROVED_PRECISE_SHOT,
        name="Improved Precise Shot",
        prerequisites={
            "min_dex": 19,
            "min_bab": 11,
            "required_feats": [FeatID.POINT_BLANK_SHOT, FeatID.PRECISE_SHOT],
        },
        modifier_type="special",
        phb_page=96,
        description="Ranged attacks ignore cover/concealment less than total"
    ),
    FeatID.IMPROVED_SHIELD_BASH: FeatDefinition(
        feat_id=FeatID.IMPROVED_SHIELD_BASH,
        name="Improved Shield Bash",
        prerequisites={
            "required_feats": [FeatID.SHIELD_PROFICIENCY],
        },
        modifier_type="special",
        phb_page=96,
        description="Retain shield AC bonus when making a shield bash"
    ),
    FeatID.IMPROVED_TURNING: FeatDefinition(
        feat_id=FeatID.IMPROVED_TURNING,
        name="Improved Turning",
        prerequisites={},
        modifier_type="special",
        phb_page=97,
        description="+1 effective cleric level for turning/rebuking"
    ),
    FeatID.IMPROVED_UNARMED_STRIKE: FeatDefinition(
        feat_id=FeatID.IMPROVED_UNARMED_STRIKE,
        name="Improved Unarmed Strike",
        prerequisites={},
        modifier_type="special",
        phb_page=97,
        description="Unarmed attacks don't provoke AoO; deal lethal or nonlethal"
    ),
    FeatID.LEADERSHIP: FeatDefinition(
        feat_id=FeatID.LEADERSHIP,
        name="Leadership",
        prerequisites={
            "min_character_level": 6,
        },
        modifier_type="special",
        phb_page=97,
        description="Attract a cohort and followers based on Leadership score"
    ),
    FeatID.MARTIAL_WEAPON_PROFICIENCY: FeatDefinition(
        feat_id=FeatID.MARTIAL_WEAPON_PROFICIENCY,
        name="Martial Weapon Proficiency",
        prerequisites={},
        modifier_type="special",
        phb_page=97,
        description="Proficiency with one selected martial weapon"
    ),
    FeatID.MOUNTED_ARCHERY: FeatDefinition(
        feat_id=FeatID.MOUNTED_ARCHERY,
        name="Mounted Archery",
        prerequisites={
            "required_feats": [FeatID.MOUNTED_COMBAT],
        },
        modifier_type="special",
        phb_page=98,
        description="Halve penalties for using ranged weapons while mounted"
    ),
    FeatID.QUICK_DRAW: FeatDefinition(
        feat_id=FeatID.QUICK_DRAW,
        name="Quick Draw",
        prerequisites={
            "min_bab": 1,
        },
        modifier_type="special",
        phb_page=98,
        description="Draw weapons as a free action; draw hidden weapons as a move action"
    ),
    FeatID.RAPID_RELOAD: FeatDefinition(
        feat_id=FeatID.RAPID_RELOAD,
        name="Rapid Reload",
        prerequisites={},
        modifier_type="special",
        phb_page=99,
        description="Reduce crossbow reload to free (light/hand) or move (heavy) action"
    ),
    FeatID.RUN: FeatDefinition(
        feat_id=FeatID.RUN,
        name="Run",
        prerequisites={},
        modifier_type="special",
        phb_page=99,
        description="Run at x5 speed; retain Dex bonus to AC while running"
    ),
    FeatID.SIMPLE_WEAPON_PROFICIENCY: FeatDefinition(
        feat_id=FeatID.SIMPLE_WEAPON_PROFICIENCY,
        name="Simple Weapon Proficiency",
        prerequisites={},
        modifier_type="special",
        phb_page=100,
        description="Proficiency with all simple weapons"
    ),
    FeatID.SNATCH_ARROWS: FeatDefinition(
        feat_id=FeatID.SNATCH_ARROWS,
        name="Snatch Arrows",
        prerequisites={
            "min_dex": 13,
            "required_feats": [FeatID.DEFLECT_ARROWS, FeatID.IMPROVED_UNARMED_STRIKE],
        },
        modifier_type="special",
        phb_page=100,
        description="Catch deflected ranged weapons; immediately throw caught thrown weapons"
    ),
    FeatID.STUNNING_FIST: FeatDefinition(
        feat_id=FeatID.STUNNING_FIST,
        name="Stunning Fist",
        prerequisites={
            "min_dex": 13,
            "min_wis": 13,
            "min_bab": 8,
            "required_feats": [FeatID.IMPROVED_UNARMED_STRIKE],
        },
        modifier_type="special",
        phb_page=101,
        description="Declare before attack: target Fort DC 10+level/2+Wis or stunned 1 round"
    ),
    FeatID.TWO_WEAPON_DEFENSE: FeatDefinition(
        feat_id=FeatID.TWO_WEAPON_DEFENSE,
        name="Two-Weapon Defense",
        prerequisites={
            "min_dex": 15,
            "required_feats": [FeatID.TWO_WEAPON_FIGHTING],
        },
        modifier_type="ac",
        phb_page=102,
        description="+1 shield bonus to AC while wielding two weapons or a double weapon"
    ),
    FeatID.WEAPON_FINESSE: FeatDefinition(
        feat_id=FeatID.WEAPON_FINESSE,
        name="Weapon Finesse",
        prerequisites={
            "min_bab": 1,
        },
        modifier_type="attack",
        phb_page=102,
        description="Use Dex instead of Str for attack rolls with light weapons"
    ),

    # --- Metamagic Feats ---
    FeatID.AUGMENT_SUMMONING: FeatDefinition(
        feat_id=FeatID.AUGMENT_SUMMONING,
        name="Augment Summoning",
        prerequisites={
            "required_feats": [FeatID.SPELL_FOCUS],
        },
        modifier_type="metamagic",
        phb_page=90,
        description="Summoned creatures gain +4 Str and +4 Con"
    ),
    FeatID.COMBAT_CASTING: FeatDefinition(
        feat_id=FeatID.COMBAT_CASTING,
        name="Combat Casting",
        prerequisites={},
        modifier_type="special",
        phb_page=92,
        description="+4 Concentration when casting defensively or while grappled"
    ),
    FeatID.EMPOWER_SPELL: FeatDefinition(
        feat_id=FeatID.EMPOWER_SPELL,
        name="Empower Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=94,
        description="Increase numeric variables of a spell by 50% (+2 slot levels)"
    ),
    FeatID.ENLARGE_SPELL: FeatDefinition(
        feat_id=FeatID.ENLARGE_SPELL,
        name="Enlarge Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=94,
        description="Double a spell's range (+1 slot level)"
    ),
    FeatID.ESCHEW_MATERIALS: FeatDefinition(
        feat_id=FeatID.ESCHEW_MATERIALS,
        name="Eschew Materials",
        prerequisites={},
        modifier_type="special",
        phb_page=94,
        description="Cast spells without material components costing less than 1 gp"
    ),
    FeatID.EXTEND_SPELL: FeatDefinition(
        feat_id=FeatID.EXTEND_SPELL,
        name="Extend Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=94,
        description="Double a spell's duration (+1 slot level)"
    ),
    FeatID.HEIGHTEN_SPELL: FeatDefinition(
        feat_id=FeatID.HEIGHTEN_SPELL,
        name="Heighten Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=95,
        description="Cast a spell as a higher-level slot, increasing DC and level-dependent effects"
    ),
    FeatID.MAXIMIZE_SPELL: FeatDefinition(
        feat_id=FeatID.MAXIMIZE_SPELL,
        name="Maximize Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=97,
        description="Maximize all numeric variables of a spell (+3 slot levels)"
    ),
    FeatID.QUICKEN_SPELL: FeatDefinition(
        feat_id=FeatID.QUICKEN_SPELL,
        name="Quicken Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=98,
        description="Cast a spell as a free action (+4 slot levels)"
    ),
    FeatID.SILENT_SPELL: FeatDefinition(
        feat_id=FeatID.SILENT_SPELL,
        name="Silent Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=100,
        description="Remove verbal component from a spell (+1 slot level)"
    ),
    FeatID.SPELL_MASTERY: FeatDefinition(
        feat_id=FeatID.SPELL_MASTERY,
        name="Spell Mastery",
        prerequisites={
            "min_class_level": {"wizard": 1},
        },
        modifier_type="special",
        phb_page=100,
        description="Prepare selected spells without a spellbook"
    ),
    FeatID.STILL_SPELL: FeatDefinition(
        feat_id=FeatID.STILL_SPELL,
        name="Still Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=101,
        description="Remove somatic component from a spell (+1 slot level)"
    ),
    FeatID.WIDEN_SPELL: FeatDefinition(
        feat_id=FeatID.WIDEN_SPELL,
        name="Widen Spell",
        prerequisites={},
        modifier_type="metamagic",
        phb_page=103,
        description="Double a spell's area (+3 slot levels)"
    ),

    # --- Item Creation Feats (additional) ---
    FeatID.CRAFT_MAGIC_ARMS_AND_ARMOR: FeatDefinition(
        feat_id=FeatID.CRAFT_MAGIC_ARMS_AND_ARMOR,
        name="Craft Magic Arms and Armor",
        prerequisites={
            "min_caster_level": 5,
        },
        modifier_type="item_creation",
        phb_page=92,
        description="Create and repair magic weapons, armor, and shields"
    ),
    FeatID.CRAFT_ROD: FeatDefinition(
        feat_id=FeatID.CRAFT_ROD,
        name="Craft Rod",
        prerequisites={
            "min_caster_level": 9,
        },
        modifier_type="item_creation",
        phb_page=92,
        description="Create magic rods"
    ),
    FeatID.CRAFT_STAFF: FeatDefinition(
        feat_id=FeatID.CRAFT_STAFF,
        name="Craft Staff",
        prerequisites={
            "min_caster_level": 12,
        },
        modifier_type="item_creation",
        phb_page=93,
        description="Create magic staffs"
    ),
    FeatID.CRAFT_WAND: FeatDefinition(
        feat_id=FeatID.CRAFT_WAND,
        name="Craft Wand",
        prerequisites={
            "min_caster_level": 5,
        },
        modifier_type="item_creation",
        phb_page=93,
        description="Create magic wands"
    ),
    FeatID.FORGE_RING: FeatDefinition(
        feat_id=FeatID.FORGE_RING,
        name="Forge Ring",
        prerequisites={
            "min_caster_level": 12,
        },
        modifier_type="item_creation",
        phb_page=94,
        description="Create magic rings"
    ),
}


def get_feat_definition(feat_id: str) -> Optional[FeatDefinition]:
    """Get feat definition by ID.

    For weapon-specific feats (e.g., "weapon_focus_longsword"),
    returns the base definition ("weapon_focus").

    Args:
        feat_id: Feat ID (may include weapon suffix)

    Returns:
        FeatDefinition or None if not found
    """
    # Check direct match first
    if feat_id in FEAT_REGISTRY:
        return FEAT_REGISTRY[feat_id]

    # Check weapon-specific feat suffixes
    if feat_id.startswith("weapon_focus_"):
        return FEAT_REGISTRY[FeatID.WEAPON_FOCUS]

    if feat_id.startswith("weapon_specialization_"):
        return FEAT_REGISTRY[FeatID.WEAPON_SPECIALIZATION]

    return None


def extract_weapon_from_feat_id(feat_id: str) -> Optional[str]:
    """Extract weapon name from weapon-specific feat ID.

    Args:
        feat_id: Feat ID (e.g., "weapon_focus_longsword")

    Returns:
        Weapon name (e.g., "longsword") or None if not weapon-specific
    """
    if feat_id.startswith("weapon_focus_"):
        return feat_id[len("weapon_focus_"):]

    if feat_id.startswith("weapon_specialization_"):
        return feat_id[len("weapon_specialization_"):]

    return None
