"""Feat benefit registry — numeric benefit values for D&D 3.5e PHB feats.

Each entry maps a canonical feat ID (snake_case) to a FeatDefinition with
numeric benefit fields. This registry is the data layer for benefit lookups.

Source: PHB 3.5e feat tables (facts are not copyrightable).
Cross-referenced with aidm/schemas/feats.py (prerequisite/resolver schema).

NOTE: The canonical feat prerequisite schema is in aidm/schemas/feats.py,
which feat_resolver.py imports. This file is the *benefit* data layer only —
it records what a feat grants numerically (fort_bonus, ref_bonus, etc.).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple


@dataclass(frozen=True)
class FeatDefinition:
    feat_id: str            # snake_case canonical ID
    name: str               # Display name
    feat_type: str          # "General" | "Metamagic" | "Item Creation" | "Fighter"
    prerequisites: Tuple[str, ...]  # Tuple of prereq strings (human-readable)
    fort_bonus: int = 0
    ref_bonus: int = 0
    will_bonus: int = 0
    attack_bonus: int = 0
    ac_bonus: int = 0
    damage_bonus: int = 0
    hp_bonus: int = 0
    initiative_bonus: int = 0
    skill_bonus: int = 0    # Generic skill bonus (used for double-skill feats)
    # For feats that provide special mechanics only (no numeric bonus), all remain 0


FEAT_REGISTRY: Dict[str, FeatDefinition] = {
    # =========================================================================
    # SAVE FEATS
    # =========================================================================
    "great_fortitude": FeatDefinition(
        feat_id="great_fortitude",
        name="Great Fortitude",
        feat_type="General",
        prerequisites=(),
        fort_bonus=2,
    ),
    "iron_will": FeatDefinition(
        feat_id="iron_will",
        name="Iron Will",
        feat_type="General",
        prerequisites=(),
        will_bonus=2,
    ),
    "lightning_reflexes": FeatDefinition(
        feat_id="lightning_reflexes",
        name="Lightning Reflexes",
        feat_type="General",
        prerequisites=(),
        ref_bonus=2,
    ),

    # =========================================================================
    # TOUGHNESS
    # =========================================================================
    "toughness": FeatDefinition(
        feat_id="toughness",
        name="Toughness",
        feat_type="General",
        prerequisites=(),
        hp_bonus=3,
    ),

    # =========================================================================
    # INITIATIVE
    # =========================================================================
    "improved_initiative": FeatDefinition(
        feat_id="improved_initiative",
        name="Improved Initiative",
        feat_type="General",
        prerequisites=(),
        initiative_bonus=4,
    ),

    # =========================================================================
    # MELEE COMBAT CHAIN
    # =========================================================================
    "power_attack": FeatDefinition(
        feat_id="power_attack",
        name="Power Attack",
        feat_type="Fighter",
        prerequisites=("STR 13", "BAB +1"),
    ),
    "cleave": FeatDefinition(
        feat_id="cleave",
        name="Cleave",
        feat_type="Fighter",
        prerequisites=("STR 13", "Power Attack"),
    ),
    "great_cleave": FeatDefinition(
        feat_id="great_cleave",
        name="Great Cleave",
        feat_type="Fighter",
        prerequisites=("STR 13", "BAB +4", "Cleave", "Power Attack"),
    ),

    # =========================================================================
    # DEFENSE CHAIN
    # =========================================================================
    "dodge": FeatDefinition(
        feat_id="dodge",
        name="Dodge",
        feat_type="Fighter",
        prerequisites=("DEX 13",),
        ac_bonus=1,
    ),
    "mobility": FeatDefinition(
        feat_id="mobility",
        name="Mobility",
        feat_type="Fighter",
        prerequisites=("DEX 13", "Dodge"),
        ac_bonus=4,  # vs AoO from movement only
    ),
    "spring_attack": FeatDefinition(
        feat_id="spring_attack",
        name="Spring Attack",
        feat_type="Fighter",
        prerequisites=("DEX 13", "BAB +4", "Dodge", "Mobility"),
    ),

    # =========================================================================
    # RANGED COMBAT CHAIN
    # =========================================================================
    "point_blank_shot": FeatDefinition(
        feat_id="point_blank_shot",
        name="Point Blank Shot",
        feat_type="Fighter",
        prerequisites=(),
        attack_bonus=1,   # within 30 ft only
        damage_bonus=1,   # within 30 ft only
    ),
    "precise_shot": FeatDefinition(
        feat_id="precise_shot",
        name="Precise Shot",
        feat_type="Fighter",
        prerequisites=("Point Blank Shot",),
    ),
    "rapid_shot": FeatDefinition(
        feat_id="rapid_shot",
        name="Rapid Shot",
        feat_type="Fighter",
        prerequisites=("DEX 13", "Point Blank Shot"),
    ),
    "manyshot": FeatDefinition(
        feat_id="manyshot",
        name="Manyshot",
        feat_type="Fighter",
        prerequisites=("DEX 17", "BAB +6", "Point Blank Shot", "Rapid Shot"),
    ),
    "shot_on_the_run": FeatDefinition(
        feat_id="shot_on_the_run",
        name="Shot on the Run",
        feat_type="Fighter",
        prerequisites=("DEX 13", "BAB +4", "Dodge", "Mobility", "Point Blank Shot"),
    ),
    "far_shot": FeatDefinition(
        feat_id="far_shot",
        name="Far Shot",
        feat_type="Fighter",
        prerequisites=("Point Blank Shot",),
    ),

    # =========================================================================
    # WEAPON CHAIN
    # =========================================================================
    "weapon_focus": FeatDefinition(
        feat_id="weapon_focus",
        name="Weapon Focus",
        feat_type="Fighter",
        prerequisites=("BAB +1",),
        attack_bonus=1,
    ),
    "weapon_specialization": FeatDefinition(
        feat_id="weapon_specialization",
        name="Weapon Specialization",
        feat_type="Fighter",
        prerequisites=("Weapon Focus (same weapon)", "Fighter 4"),
        damage_bonus=2,
    ),
    "greater_weapon_focus": FeatDefinition(
        feat_id="greater_weapon_focus",
        name="Greater Weapon Focus",
        feat_type="Fighter",
        prerequisites=("Weapon Focus (same weapon)", "Fighter 8"),
        attack_bonus=1,
    ),
    "greater_weapon_specialization": FeatDefinition(
        feat_id="greater_weapon_specialization",
        name="Greater Weapon Specialization",
        feat_type="Fighter",
        prerequisites=("Weapon Focus", "Weapon Specialization", "Greater Weapon Focus", "Fighter 12"),
        damage_bonus=2,
    ),
    "improved_critical": FeatDefinition(
        feat_id="improved_critical",
        name="Improved Critical",
        feat_type="Fighter",
        prerequisites=("BAB +8",),
    ),

    # =========================================================================
    # TWO-WEAPON FIGHTING CHAIN
    # =========================================================================
    "two_weapon_fighting": FeatDefinition(
        feat_id="two_weapon_fighting",
        name="Two-Weapon Fighting",
        feat_type="Fighter",
        prerequisites=("DEX 15",),
    ),
    "improved_two_weapon_fighting": FeatDefinition(
        feat_id="improved_two_weapon_fighting",
        name="Improved Two-Weapon Fighting",
        feat_type="Fighter",
        prerequisites=("DEX 17", "BAB +6", "Two-Weapon Fighting"),
    ),
    "greater_two_weapon_fighting": FeatDefinition(
        feat_id="greater_two_weapon_fighting",
        name="Greater Two-Weapon Fighting",
        feat_type="Fighter",
        prerequisites=("DEX 19", "BAB +11", "Improved Two-Weapon Fighting", "Two-Weapon Fighting"),
    ),
    "two_weapon_defense": FeatDefinition(
        feat_id="two_weapon_defense",
        name="Two-Weapon Defense",
        feat_type="Fighter",
        prerequisites=("DEX 15", "Two-Weapon Fighting"),
        ac_bonus=1,  # Shield bonus when wielding two weapons
    ),

    # =========================================================================
    # COMBAT MANEUVER FEATS
    # =========================================================================
    "combat_reflexes": FeatDefinition(
        feat_id="combat_reflexes",
        name="Combat Reflexes",
        feat_type="Fighter",
        prerequisites=(),
    ),
    "combat_expertise": FeatDefinition(
        feat_id="combat_expertise",
        name="Combat Expertise",
        feat_type="Fighter",
        prerequisites=("INT 13",),
    ),
    "improved_disarm": FeatDefinition(
        feat_id="improved_disarm",
        name="Improved Disarm",
        feat_type="Fighter",
        prerequisites=("INT 13", "Combat Expertise"),
        attack_bonus=4,  # On disarm checks
    ),
    "improved_feint": FeatDefinition(
        feat_id="improved_feint",
        name="Improved Feint",
        feat_type="Fighter",
        prerequisites=("INT 13", "Combat Expertise"),
    ),
    "improved_grapple": FeatDefinition(
        feat_id="improved_grapple",
        name="Improved Grapple",
        feat_type="Fighter",
        prerequisites=("DEX 13", "Improved Unarmed Strike"),
        attack_bonus=4,  # On grapple checks
    ),
    "improved_trip": FeatDefinition(
        feat_id="improved_trip",
        name="Improved Trip",
        feat_type="Fighter",
        prerequisites=("INT 13", "Combat Expertise"),
        attack_bonus=4,  # On trip attempts
    ),
    "improved_bull_rush": FeatDefinition(
        feat_id="improved_bull_rush",
        name="Improved Bull Rush",
        feat_type="Fighter",
        prerequisites=("STR 13", "Power Attack"),
        attack_bonus=4,  # On bull rush checks
    ),
    "improved_overrun": FeatDefinition(
        feat_id="improved_overrun",
        name="Improved Overrun",
        feat_type="Fighter",
        prerequisites=("STR 13", "Power Attack"),
        attack_bonus=4,  # On overrun checks
    ),
    "improved_sunder": FeatDefinition(
        feat_id="improved_sunder",
        name="Improved Sunder",
        feat_type="Fighter",
        prerequisites=("STR 13", "Power Attack"),
        attack_bonus=4,  # On sunder checks
    ),
    "whirlwind_attack": FeatDefinition(
        feat_id="whirlwind_attack",
        name="Whirlwind Attack",
        feat_type="Fighter",
        prerequisites=("DEX 13", "INT 13", "BAB +4", "Combat Expertise", "Dodge",
                       "Mobility", "Spring Attack"),
    ),
    "blind_fight": FeatDefinition(
        feat_id="blind_fight",
        name="Blind-Fight",
        feat_type="Fighter",
        prerequisites=(),
    ),

    # =========================================================================
    # UNARMED / MONK FEATS
    # =========================================================================
    "improved_unarmed_strike": FeatDefinition(
        feat_id="improved_unarmed_strike",
        name="Improved Unarmed Strike",
        feat_type="Fighter",
        prerequisites=(),
    ),
    "deflect_arrows": FeatDefinition(
        feat_id="deflect_arrows",
        name="Deflect Arrows",
        feat_type="Fighter",
        prerequisites=("DEX 13", "Improved Unarmed Strike"),
    ),
    "snatch_arrows": FeatDefinition(
        feat_id="snatch_arrows",
        name="Snatch Arrows",
        feat_type="Fighter",
        prerequisites=("DEX 15", "Deflect Arrows", "Improved Unarmed Strike"),
    ),
    "stunning_fist": FeatDefinition(
        feat_id="stunning_fist",
        name="Stunning Fist",
        feat_type="Fighter",
        prerequisites=("DEX 13", "WIS 13", "BAB +8", "Improved Unarmed Strike"),
    ),

    # =========================================================================
    # MOUNTED COMBAT
    # =========================================================================
    "mounted_combat": FeatDefinition(
        feat_id="mounted_combat",
        name="Mounted Combat",
        feat_type="Fighter",
        prerequisites=("Ride 1 rank",),
    ),
    "ride_by_attack": FeatDefinition(
        feat_id="ride_by_attack",
        name="Ride-By Attack",
        feat_type="Fighter",
        prerequisites=("Mounted Combat", "Ride 1 rank"),
    ),
    "spirited_charge": FeatDefinition(
        feat_id="spirited_charge",
        name="Spirited Charge",
        feat_type="Fighter",
        prerequisites=("Mounted Combat", "Ride-By Attack", "Ride 1 rank"),
        damage_bonus=0,  # Special: doubles charge damage (not a flat bonus)
    ),
    "trample": FeatDefinition(
        feat_id="trample",
        name="Trample",
        feat_type="Fighter",
        prerequisites=("Mounted Combat", "Ride 1 rank"),
    ),

    # =========================================================================
    # METAMAGIC FEATS
    # =========================================================================
    "empower_spell": FeatDefinition(
        feat_id="empower_spell",
        name="Empower Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "enlarge_spell": FeatDefinition(
        feat_id="enlarge_spell",
        name="Enlarge Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "extend_spell": FeatDefinition(
        feat_id="extend_spell",
        name="Extend Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "heighten_spell": FeatDefinition(
        feat_id="heighten_spell",
        name="Heighten Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "maximize_spell": FeatDefinition(
        feat_id="maximize_spell",
        name="Maximize Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "quicken_spell": FeatDefinition(
        feat_id="quicken_spell",
        name="Quicken Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "silent_spell": FeatDefinition(
        feat_id="silent_spell",
        name="Silent Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "still_spell": FeatDefinition(
        feat_id="still_spell",
        name="Still Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "widen_spell": FeatDefinition(
        feat_id="widen_spell",
        name="Widen Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "twin_spell": FeatDefinition(
        feat_id="twin_spell",
        name="Twin Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "chain_spell": FeatDefinition(
        feat_id="chain_spell",
        name="Chain Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),
    "repeat_spell": FeatDefinition(
        feat_id="repeat_spell",
        name="Repeat Spell",
        feat_type="Metamagic",
        prerequisites=(),
    ),

    # =========================================================================
    # SPELL FEATS
    # =========================================================================
    "spell_focus": FeatDefinition(
        feat_id="spell_focus",
        name="Spell Focus",
        feat_type="General",
        prerequisites=(),
    ),
    "greater_spell_focus": FeatDefinition(
        feat_id="greater_spell_focus",
        name="Greater Spell Focus",
        feat_type="General",
        prerequisites=("Spell Focus (same school)",),
    ),
    "spell_penetration": FeatDefinition(
        feat_id="spell_penetration",
        name="Spell Penetration",
        feat_type="General",
        prerequisites=(),
        attack_bonus=2,  # On caster level checks vs SR
    ),
    "greater_spell_penetration": FeatDefinition(
        feat_id="greater_spell_penetration",
        name="Greater Spell Penetration",
        feat_type="General",
        prerequisites=("Spell Penetration",),
        attack_bonus=2,  # Additional +2 on caster level checks vs SR (stacks)
    ),

    # =========================================================================
    # SKILL FEATS
    # =========================================================================
    "alertness": FeatDefinition(
        feat_id="alertness",
        name="Alertness",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Listen + Spot
    ),
    "athletic": FeatDefinition(
        feat_id="athletic",
        name="Athletic",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Climb + Swim
    ),
    "acrobatic": FeatDefinition(
        feat_id="acrobatic",
        name="Acrobatic",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Jump + Tumble
    ),
    "deceitful": FeatDefinition(
        feat_id="deceitful",
        name="Deceitful",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Disguise + Forgery
    ),
    "deft_hands": FeatDefinition(
        feat_id="deft_hands",
        name="Deft Hands",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Sleight of Hand + Use Rope
    ),
    "diligent": FeatDefinition(
        feat_id="diligent",
        name="Diligent",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Appraise + Decipher Script
    ),
    "investigator": FeatDefinition(
        feat_id="investigator",
        name="Investigator",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Gather Information + Search
    ),
    "negotiator": FeatDefinition(
        feat_id="negotiator",
        name="Negotiator",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Diplomacy + Sense Motive
    ),
    "nimble_fingers": FeatDefinition(
        feat_id="nimble_fingers",
        name="Nimble Fingers",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Disable Device + Open Lock
    ),
    "persuasive": FeatDefinition(
        feat_id="persuasive",
        name="Persuasive",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Bluff + Intimidate
    ),
    "self_sufficient": FeatDefinition(
        feat_id="self_sufficient",
        name="Self-Sufficient",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Heal + Survival
    ),
    "stealthy": FeatDefinition(
        feat_id="stealthy",
        name="Stealthy",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Hide + Move Silently
    ),
    "magical_aptitude": FeatDefinition(
        feat_id="magical_aptitude",
        name="Magical Aptitude",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Spellcraft + Use Magic Device
    ),
    "animal_affinity": FeatDefinition(
        feat_id="animal_affinity",
        name="Animal Affinity",
        feat_type="General",
        prerequisites=(),
        skill_bonus=2,  # Handle Animal + Ride
    ),

    # =========================================================================
    # PROFICIENCY FEATS
    # =========================================================================
    "armor_proficiency_light": FeatDefinition(
        feat_id="armor_proficiency_light",
        name="Armor Proficiency (Light)",
        feat_type="General",
        prerequisites=(),
    ),
    "armor_proficiency_medium": FeatDefinition(
        feat_id="armor_proficiency_medium",
        name="Armor Proficiency (Medium)",
        feat_type="General",
        prerequisites=("Armor Proficiency (Light)",),
    ),
    "armor_proficiency_heavy": FeatDefinition(
        feat_id="armor_proficiency_heavy",
        name="Armor Proficiency (Heavy)",
        feat_type="General",
        prerequisites=("Armor Proficiency (Light)", "Armor Proficiency (Medium)"),
    ),
    "shield_proficiency": FeatDefinition(
        feat_id="shield_proficiency",
        name="Shield Proficiency",
        feat_type="General",
        prerequisites=(),
    ),
    "tower_shield_proficiency": FeatDefinition(
        feat_id="tower_shield_proficiency",
        name="Tower Shield Proficiency",
        feat_type="General",
        prerequisites=("Shield Proficiency",),
    ),
    "simple_weapon_proficiency": FeatDefinition(
        feat_id="simple_weapon_proficiency",
        name="Simple Weapon Proficiency",
        feat_type="General",
        prerequisites=(),
    ),
    "martial_weapon_proficiency": FeatDefinition(
        feat_id="martial_weapon_proficiency",
        name="Martial Weapon Proficiency",
        feat_type="Fighter",
        prerequisites=(),
    ),
    "exotic_weapon_proficiency": FeatDefinition(
        feat_id="exotic_weapon_proficiency",
        name="Exotic Weapon Proficiency",
        feat_type="Fighter",
        prerequisites=("BAB +1",),
    ),

    # =========================================================================
    # CLASS-SPECIFIC / SPECIAL FEATS
    # =========================================================================
    "combat_casting": FeatDefinition(
        feat_id="combat_casting",
        name="Combat Casting",
        feat_type="General",
        prerequisites=(),
        skill_bonus=4,  # On Concentration checks for defensive casting
    ),
    "extra_turning": FeatDefinition(
        feat_id="extra_turning",
        name="Extra Turning",
        feat_type="General",
        prerequisites=("Turn Undead class ability",),
    ),
    "natural_spell": FeatDefinition(
        feat_id="natural_spell",
        name="Natural Spell",
        feat_type="General",
        prerequisites=("WIS 13", "Wild Shape class ability"),
    ),
    "track": FeatDefinition(
        feat_id="track",
        name="Track",
        feat_type="General",
        prerequisites=(),
    ),
    "endurance": FeatDefinition(
        feat_id="endurance",
        name="Endurance",
        feat_type="General",
        prerequisites=(),
    ),
    "diehard": FeatDefinition(
        feat_id="diehard",
        name="Diehard",
        feat_type="General",
        prerequisites=("Endurance",),
    ),
    "run": FeatDefinition(
        feat_id="run",
        name="Run",
        feat_type="General",
        prerequisites=(),
    ),
    "leadership": FeatDefinition(
        feat_id="leadership",
        name="Leadership",
        feat_type="General",
        prerequisites=("Character level 6",),
    ),
    "spell_mastery": FeatDefinition(
        feat_id="spell_mastery",
        name="Spell Mastery",
        feat_type="General",
        prerequisites=("Wizard level 1",),
    ),

    # =========================================================================
    # ITEM CREATION FEATS
    # =========================================================================
    "scribe_scroll": FeatDefinition(
        feat_id="scribe_scroll",
        name="Scribe Scroll",
        feat_type="Item Creation",
        prerequisites=("Caster level 1",),
    ),
    "brew_potion": FeatDefinition(
        feat_id="brew_potion",
        name="Brew Potion",
        feat_type="Item Creation",
        prerequisites=("Caster level 3",),
    ),
    "craft_magic_arms_and_armor": FeatDefinition(
        feat_id="craft_magic_arms_and_armor",
        name="Craft Magic Arms and Armor",
        feat_type="Item Creation",
        prerequisites=("Caster level 5",),
    ),
    "craft_rod": FeatDefinition(
        feat_id="craft_rod",
        name="Craft Rod",
        feat_type="Item Creation",
        prerequisites=("Caster level 9",),
    ),
    "craft_staff": FeatDefinition(
        feat_id="craft_staff",
        name="Craft Staff",
        feat_type="Item Creation",
        prerequisites=("Caster level 12",),
    ),
    "craft_wand": FeatDefinition(
        feat_id="craft_wand",
        name="Craft Wand",
        feat_type="Item Creation",
        prerequisites=("Caster level 5",),
    ),
    "craft_wondrous_item": FeatDefinition(
        feat_id="craft_wondrous_item",
        name="Craft Wondrous Item",
        feat_type="Item Creation",
        prerequisites=("Caster level 3",),
    ),
    "forge_ring": FeatDefinition(
        feat_id="forge_ring",
        name="Forge Ring",
        feat_type="Item Creation",
        prerequisites=("Caster level 12",),
    ),

    # =========================================================================
    # DIVINE / CLERIC FEATS
    # =========================================================================
    "divine_might": FeatDefinition(
        feat_id="divine_might",
        name="Divine Might",
        feat_type="General",
        prerequisites=("STR 13", "Turn Undead", "Power Attack"),
        damage_bonus=0,  # Special: add CHA bonus to damage for 1 round
    ),
    "divine_shield": FeatDefinition(
        feat_id="divine_shield",
        name="Divine Shield",
        feat_type="General",
        prerequisites=("STR 13", "Turn Undead", "Power Attack"),
        ac_bonus=0,  # Special: add CHA bonus to AC for 1 round
    ),
    "extra_smiting": FeatDefinition(
        feat_id="extra_smiting",
        name="Extra Smiting",
        feat_type="General",
        prerequisites=("Smite Evil class ability",),
    ),

    # =========================================================================
    # PSIONIC / OTHER (placeholders for completeness)
    # =========================================================================
    "augment_summoning": FeatDefinition(
        feat_id="augment_summoning",
        name="Augment Summoning",
        feat_type="General",
        prerequisites=("Spell Focus (Conjuration)",),
    ),
    "eschew_materials": FeatDefinition(
        feat_id="eschew_materials",
        name="Eschew Materials",
        feat_type="General",
        prerequisites=(),
    ),
    "improved_counterspell": FeatDefinition(
        feat_id="improved_counterspell",
        name="Improved Counterspell",
        feat_type="General",
        prerequisites=(),
    ),
    "improved_familiar": FeatDefinition(
        feat_id="improved_familiar",
        name="Improved Familiar",
        feat_type="General",
        prerequisites=("Arcane caster level 3",),
    ),
    "improved_turning": FeatDefinition(
        feat_id="improved_turning",
        name="Improved Turning",
        feat_type="General",
        prerequisites=("Turn Undead class ability",),
    ),
    "sacred_vow": FeatDefinition(
        feat_id="sacred_vow",
        name="Sacred Vow",
        feat_type="General",
        prerequisites=("Good alignment",),
    ),
    "vow_of_poverty": FeatDefinition(
        feat_id="vow_of_poverty",
        name="Vow of Poverty",
        feat_type="General",
        prerequisites=("Sacred Vow",),
    ),
    "penetrating_strike": FeatDefinition(
        feat_id="penetrating_strike",
        name="Penetrating Strike",
        feat_type="Fighter",
        prerequisites=("BAB +1",),
    ),
    "rapid_reload": FeatDefinition(
        feat_id="rapid_reload",
        name="Rapid Reload",
        feat_type="Fighter",
        prerequisites=(),
    ),
}


def get_feat(feat_id: str) -> Optional[FeatDefinition]:
    """Get feat benefit definition by ID. Returns None if not found.

    For weapon-specific variants (e.g., 'weapon_focus_longsword'),
    falls back to the base feat entry ('weapon_focus').
    """
    if feat_id in FEAT_REGISTRY:
        return FEAT_REGISTRY[feat_id]
    # Weapon-specific fallback
    if feat_id.startswith("weapon_focus_"):
        return FEAT_REGISTRY.get("weapon_focus")
    if feat_id.startswith("weapon_specialization_"):
        return FEAT_REGISTRY.get("weapon_specialization")
    if feat_id.startswith("greater_weapon_focus_"):
        return FEAT_REGISTRY.get("greater_weapon_focus")
    if feat_id.startswith("greater_weapon_specialization_"):
        return FEAT_REGISTRY.get("greater_weapon_specialization")
    if feat_id.startswith("improved_critical_"):
        return FEAT_REGISTRY.get("improved_critical")
    if feat_id.startswith("spell_focus_"):
        return FEAT_REGISTRY.get("spell_focus")
    if feat_id.startswith("greater_spell_focus_"):
        return FEAT_REGISTRY.get("greater_spell_focus")
    return None
