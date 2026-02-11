"""Feat definition schemas for D&D 3.5e combat feats.

This module defines the FeatDefinition dataclass and the canonical registry
of 15 core combat feats per PHB. Feats modify combat resolution through
the feat_resolver module.

WO-034: Core Feat System (15 Feats)
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
