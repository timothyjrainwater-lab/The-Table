"""Feat definition data — D&D 3.5e PHB feats (data layer).

Content-pack data file. Provides FeatDefinition records with structured
prerequisite tuples (human-readable strings) and flat numeric bonus fields.

This is the DATA LAYER file.  Runtime logic lives in aidm/schemas/feats.py
and aidm/core/feat_resolver.py.

WO-DATA-FEATS-PREREQS-001: prerequisite population (string-tuple format).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class FeatDefinition:
    """Static data record for a D&D 3.5e feat.

    prerequisites: tuple of human-readable requirement strings,
        e.g. ("STR 13", "Power Attack").  Empty tuple = no prerequisites.

    Numeric bonus fields are 0 when the feat's benefit is non-numeric
    (e.g. cleave, combat reflexes) or handled by the resolver.
    """

    feat_id: str
    name: str
    feat_type: str                   # "combat", "general", "metamagic", "item_creation"
    prerequisites: Tuple[str, ...]   # human-readable strings
    fort_bonus: int = 0
    ref_bonus: int = 0
    will_bonus: int = 0
    attack_bonus: int = 0
    ac_bonus: int = 0
    damage_bonus: int = 0
    hp_bonus: int = 0
    initiative_bonus: int = 0
    skill_bonus: int = 0


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

FEAT_REGISTRY: Dict[str, FeatDefinition] = {

    # -----------------------------------------------------------------------
    # MELEE CHAIN
    # -----------------------------------------------------------------------
    "power_attack": FeatDefinition(
        feat_id="power_attack", name="Power Attack", feat_type="combat",
        prerequisites=("STR 13", "BAB +1"),
    ),
    "cleave": FeatDefinition(
        feat_id="cleave", name="Cleave", feat_type="combat",
        prerequisites=("STR 13", "Power Attack"),
    ),
    "great_cleave": FeatDefinition(
        feat_id="great_cleave", name="Great Cleave", feat_type="combat",
        prerequisites=("STR 13", "BAB +4", "Cleave", "Power Attack"),
    ),
    "improved_bull_rush": FeatDefinition(
        feat_id="improved_bull_rush", name="Improved Bull Rush", feat_type="combat",
        prerequisites=("STR 13", "Power Attack"),
    ),
    "improved_overrun": FeatDefinition(
        feat_id="improved_overrun", name="Improved Overrun", feat_type="combat",
        prerequisites=("STR 13", "Power Attack"),
    ),
    "improved_sunder": FeatDefinition(
        feat_id="improved_sunder", name="Improved Sunder", feat_type="combat",
        prerequisites=("STR 13", "Power Attack"),
    ),

    # -----------------------------------------------------------------------
    # DEFENSE CHAIN
    # -----------------------------------------------------------------------
    "dodge": FeatDefinition(
        feat_id="dodge", name="Dodge", feat_type="combat",
        prerequisites=("DEX 13",),
        ac_bonus=1,
    ),
    "mobility": FeatDefinition(
        feat_id="mobility", name="Mobility", feat_type="combat",
        prerequisites=("DEX 13", "Dodge"),
    ),
    "spring_attack": FeatDefinition(
        feat_id="spring_attack", name="Spring Attack", feat_type="combat",
        prerequisites=("DEX 13", "BAB +4", "Dodge", "Mobility"),
    ),
    "whirlwind_attack": FeatDefinition(
        feat_id="whirlwind_attack", name="Whirlwind Attack", feat_type="combat",
        prerequisites=("DEX 13", "INT 13", "BAB +4",
                       "Combat Expertise", "Dodge", "Mobility", "Spring Attack"),
    ),

    # -----------------------------------------------------------------------
    # RANGED CHAIN
    # -----------------------------------------------------------------------
    "point_blank_shot": FeatDefinition(
        feat_id="point_blank_shot", name="Point Blank Shot", feat_type="combat",
        prerequisites=(),
        attack_bonus=1,
    ),
    "precise_shot": FeatDefinition(
        feat_id="precise_shot", name="Precise Shot", feat_type="combat",
        prerequisites=("Point Blank Shot",),
    ),
    "rapid_shot": FeatDefinition(
        feat_id="rapid_shot", name="Rapid Shot", feat_type="combat",
        prerequisites=("DEX 13", "Point Blank Shot"),
    ),
    "manyshot": FeatDefinition(
        feat_id="manyshot", name="Manyshot", feat_type="combat",
        prerequisites=("DEX 17", "BAB +6", "Point Blank Shot", "Rapid Shot"),
    ),
    "shot_on_the_run": FeatDefinition(
        feat_id="shot_on_the_run", name="Shot on the Run", feat_type="combat",
        prerequisites=("DEX 13", "BAB +4", "Dodge", "Mobility", "Point Blank Shot"),
    ),
    "far_shot": FeatDefinition(
        feat_id="far_shot", name="Far Shot", feat_type="combat",
        prerequisites=("Point Blank Shot",),
    ),

    # -----------------------------------------------------------------------
    # WEAPON CHAIN
    # -----------------------------------------------------------------------
    "weapon_focus": FeatDefinition(
        feat_id="weapon_focus", name="Weapon Focus", feat_type="combat",
        prerequisites=("BAB +1", "Proficiency with chosen weapon"),
        attack_bonus=1,
    ),
    "greater_weapon_focus": FeatDefinition(
        feat_id="greater_weapon_focus", name="Greater Weapon Focus", feat_type="combat",
        prerequisites=("BAB +8", "Fighter 8", "Weapon Focus"),
        attack_bonus=1,
    ),
    "weapon_specialization": FeatDefinition(
        feat_id="weapon_specialization", name="Weapon Specialization", feat_type="combat",
        prerequisites=("Fighter 4", "Weapon Focus"),
        damage_bonus=2,
    ),
    "greater_weapon_specialization": FeatDefinition(
        feat_id="greater_weapon_specialization", name="Greater Weapon Specialization",
        feat_type="combat",
        prerequisites=("Fighter 12", "Greater Weapon Focus", "Weapon Focus",
                       "Weapon Specialization"),
        damage_bonus=2,
    ),
    "improved_critical": FeatDefinition(
        feat_id="improved_critical", name="Improved Critical", feat_type="combat",
        prerequisites=("BAB +8", "Proficiency with chosen weapon"),
    ),

    # -----------------------------------------------------------------------
    # TWO-WEAPON FIGHTING CHAIN
    # -----------------------------------------------------------------------
    "two_weapon_fighting": FeatDefinition(
        feat_id="two_weapon_fighting", name="Two-Weapon Fighting", feat_type="combat",
        prerequisites=("DEX 15",),
    ),
    "improved_two_weapon_fighting": FeatDefinition(
        feat_id="improved_two_weapon_fighting", name="Improved Two-Weapon Fighting",
        feat_type="combat",
        prerequisites=("DEX 17", "BAB +6", "Two-Weapon Fighting"),
    ),
    "greater_two_weapon_fighting": FeatDefinition(
        feat_id="greater_two_weapon_fighting", name="Greater Two-Weapon Fighting",
        feat_type="combat",
        prerequisites=("DEX 19", "BAB +11", "Improved Two-Weapon Fighting",
                       "Two-Weapon Fighting"),
    ),
    "two_weapon_defense": FeatDefinition(
        feat_id="two_weapon_defense", name="Two-Weapon Defense", feat_type="combat",
        prerequisites=("DEX 15", "Two-Weapon Fighting"),
    ),

    # -----------------------------------------------------------------------
    # UNARMED / MONK CHAIN
    # -----------------------------------------------------------------------
    "improved_unarmed_strike": FeatDefinition(
        feat_id="improved_unarmed_strike", name="Improved Unarmed Strike",
        feat_type="combat", prerequisites=(),
    ),
    "stunning_fist": FeatDefinition(
        feat_id="stunning_fist", name="Stunning Fist", feat_type="combat",
        prerequisites=("DEX 13", "WIS 13", "BAB +8", "Improved Unarmed Strike"),
    ),
    "deflect_arrows": FeatDefinition(
        feat_id="deflect_arrows", name="Deflect Arrows", feat_type="combat",
        prerequisites=("DEX 13", "Improved Unarmed Strike"),
    ),
    "snatch_arrows": FeatDefinition(
        feat_id="snatch_arrows", name="Snatch Arrows", feat_type="combat",
        prerequisites=("DEX 15", "Deflect Arrows", "Improved Unarmed Strike"),
    ),

    # -----------------------------------------------------------------------
    # COMBAT MANEUVERS
    # -----------------------------------------------------------------------
    "combat_expertise": FeatDefinition(
        feat_id="combat_expertise", name="Combat Expertise", feat_type="combat",
        prerequisites=("INT 13",),
    ),
    "improved_disarm": FeatDefinition(
        feat_id="improved_disarm", name="Improved Disarm", feat_type="combat",
        prerequisites=("INT 13", "Combat Expertise"),
    ),
    "improved_feint": FeatDefinition(
        feat_id="improved_feint", name="Improved Feint", feat_type="combat",
        prerequisites=("INT 13", "Combat Expertise"),
    ),
    "improved_grapple": FeatDefinition(
        feat_id="improved_grapple", name="Improved Grapple", feat_type="combat",
        prerequisites=("DEX 13", "Improved Unarmed Strike"),
    ),
    "improved_trip": FeatDefinition(
        feat_id="improved_trip", name="Improved Trip", feat_type="combat",
        prerequisites=("INT 13", "Combat Expertise"),
    ),
    "combat_reflexes": FeatDefinition(
        feat_id="combat_reflexes", name="Combat Reflexes", feat_type="combat",
        prerequisites=(),
    ),
    "blind_fight": FeatDefinition(
        feat_id="blind_fight", name="Blind-Fight", feat_type="combat",
        prerequisites=(),
    ),

    # -----------------------------------------------------------------------
    # MOUNTED FEATS
    # -----------------------------------------------------------------------
    "mounted_combat": FeatDefinition(
        feat_id="mounted_combat", name="Mounted Combat", feat_type="combat",
        prerequisites=("Ride 1 rank",),
    ),
    "ride_by_attack": FeatDefinition(
        feat_id="ride_by_attack", name="Ride-By Attack", feat_type="combat",
        prerequisites=("Ride 1 rank", "Mounted Combat"),
    ),
    "spirited_charge": FeatDefinition(
        feat_id="spirited_charge", name="Spirited Charge", feat_type="combat",
        prerequisites=("Ride 1 rank", "Mounted Combat", "Ride-By Attack"),
    ),
    "trample": FeatDefinition(
        feat_id="trample", name="Trample", feat_type="combat",
        prerequisites=("Ride 1 rank", "Mounted Combat"),
    ),

    # -----------------------------------------------------------------------
    # INITIATIVE
    # -----------------------------------------------------------------------
    "improved_initiative": FeatDefinition(
        feat_id="improved_initiative", name="Improved Initiative", feat_type="combat",
        prerequisites=(),
        initiative_bonus=4,
    ),

    # -----------------------------------------------------------------------
    # SAVE FEATS
    # -----------------------------------------------------------------------
    "great_fortitude": FeatDefinition(
        feat_id="great_fortitude", name="Great Fortitude", feat_type="general",
        prerequisites=(),
        fort_bonus=2,
    ),
    "iron_will": FeatDefinition(
        feat_id="iron_will", name="Iron Will", feat_type="general",
        prerequisites=(),
        will_bonus=2,
    ),
    "lightning_reflexes": FeatDefinition(
        feat_id="lightning_reflexes", name="Lightning Reflexes", feat_type="general",
        prerequisites=(),
        ref_bonus=2,
    ),

    # -----------------------------------------------------------------------
    # TOUGHNESS / ENDURANCE / DIEHARD
    # -----------------------------------------------------------------------
    "toughness": FeatDefinition(
        feat_id="toughness", name="Toughness", feat_type="general",
        prerequisites=(),
        hp_bonus=3,
    ),
    "endurance": FeatDefinition(
        feat_id="endurance", name="Endurance", feat_type="general",
        prerequisites=(),
    ),
    "diehard": FeatDefinition(
        feat_id="diehard", name="Diehard", feat_type="general",
        prerequisites=("Endurance",),
    ),

    # -----------------------------------------------------------------------
    # SPELL FEATS
    # -----------------------------------------------------------------------
    "spell_focus": FeatDefinition(
        feat_id="spell_focus", name="Spell Focus", feat_type="general",
        prerequisites=(),
    ),
    "greater_spell_focus": FeatDefinition(
        feat_id="greater_spell_focus", name="Greater Spell Focus", feat_type="general",
        prerequisites=("Spell Focus in chosen school",),
    ),
    "spell_penetration": FeatDefinition(
        feat_id="spell_penetration", name="Spell Penetration", feat_type="general",
        prerequisites=(),
    ),
    "greater_spell_penetration": FeatDefinition(
        feat_id="greater_spell_penetration", name="Greater Spell Penetration",
        feat_type="general",
        prerequisites=("Spell Penetration",),
    ),

    # -----------------------------------------------------------------------
    # CLASS-SPECIFIC
    # -----------------------------------------------------------------------
    "extra_turning": FeatDefinition(
        feat_id="extra_turning", name="Extra Turning", feat_type="general",
        prerequisites=("Ability to turn or rebuke undead",),
    ),
    "natural_spell": FeatDefinition(
        feat_id="natural_spell", name="Natural Spell", feat_type="general",
        prerequisites=("WIS 13", "Wild shape class feature"),
    ),
    "track": FeatDefinition(
        feat_id="track", name="Track", feat_type="general",
        prerequisites=(),
    ),

    # -----------------------------------------------------------------------
    # SKILL FEATS
    # -----------------------------------------------------------------------
    "alertness": FeatDefinition(
        feat_id="alertness", name="Alertness", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "athletic": FeatDefinition(
        feat_id="athletic", name="Athletic", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "acrobatic": FeatDefinition(
        feat_id="acrobatic", name="Acrobatic", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "deceitful": FeatDefinition(
        feat_id="deceitful", name="Deceitful", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "deft_hands": FeatDefinition(
        feat_id="deft_hands", name="Deft Hands", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "diligent": FeatDefinition(
        feat_id="diligent", name="Diligent", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "investigator": FeatDefinition(
        feat_id="investigator", name="Investigator", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "negotiator": FeatDefinition(
        feat_id="negotiator", name="Negotiator", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "nimble_fingers": FeatDefinition(
        feat_id="nimble_fingers", name="Nimble Fingers", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "persuasive": FeatDefinition(
        feat_id="persuasive", name="Persuasive", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "self_sufficient": FeatDefinition(
        feat_id="self_sufficient", name="Self-Sufficient", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
    "stealthy": FeatDefinition(
        feat_id="stealthy", name="Stealthy", feat_type="general",
        prerequisites=(),
        skill_bonus=2,
    ),
}


def get_feat(feat_id: str) -> Optional[FeatDefinition]:
    """Return FeatDefinition by ID, or None if not found."""
    return FEAT_REGISTRY.get(feat_id)
