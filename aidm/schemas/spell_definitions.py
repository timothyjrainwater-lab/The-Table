"""Core spell definitions for D&D 3.5e spellcasting system.

Contains representative spell definitions covering all target types
for testing and demonstration purposes.

WO-014: Spellcasting Resolution Core
Reference: PHB Chapter 11 (Spells)
"""

from typing import Dict

from aidm.core.spell_resolver import (
    SpellDefinition, SpellTarget, SpellEffect, SaveEffect, DamageType
)
from aidm.core.aoe_rasterizer import AoEShape, AoEDirection
from aidm.schemas.saves import SaveType


# ==============================================================================
# CORE SPELL DEFINITIONS
# ==============================================================================

SPELL_REGISTRY: Dict[str, SpellDefinition] = {

    # ==========================================================================
    # DAMAGE SPELLS - AREA
    # ==========================================================================

    "fireball": SpellDefinition(
        spell_id="fireball",
        name="Fireball",
        level=3,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=400,  # Long range (400ft + 40ft/level)
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=20,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="8d6",
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,  # Instantaneous
        concentration=False,
        rule_citations=("PHB p.231",),
    ),

    "burning_hands": SpellDefinition(
        spell_id="burning_hands",
        name="Burning Hands",
        level=1,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=0,  # Caster origin
        aoe_shape=AoEShape.CONE,
        aoe_radius_ft=15,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="5d4",  # 1d4/level, max 5d4
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.207",),
    ),

    "lightning_bolt": SpellDefinition(
        spell_id="lightning_bolt",
        name="Lightning Bolt",
        level=3,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=0,  # Caster origin
        aoe_shape=AoEShape.LINE,
        aoe_radius_ft=120,  # 120-foot line
        effect_type=SpellEffect.DAMAGE,
        damage_dice="8d6",  # 1d6/level, max 10d6
        damage_type=DamageType.ELECTRICITY,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.248",),
    ),

    "cone_of_cold": SpellDefinition(
        spell_id="cone_of_cold",
        name="Cone of Cold",
        level=5,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=0,
        aoe_shape=AoEShape.CONE,
        aoe_radius_ft=60,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="10d6",  # 1d6/level, max 15d6
        damage_type=DamageType.COLD,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.212",),
    ),

    # ==========================================================================
    # DAMAGE SPELLS - SINGLE TARGET
    # ==========================================================================

    "magic_missile": SpellDefinition(
        spell_id="magic_missile",
        name="Magic Missile",
        level=1,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=100,  # Medium range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="3d4+3",  # 1d4+1 per missile, 3 missiles at CL 5
        damage_type=DamageType.FORCE,
        save_type=None,  # No save
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        auto_hit=True,  # Auto-hit (no attack roll needed)
        rule_citations=("PHB p.251",),
    ),

    "scorching_ray": SpellDefinition(
        spell_id="scorching_ray",
        name="Scorching Ray",
        level=2,
        school="evocation",
        target_type=SpellTarget.RAY,
        range_ft=25,  # Close range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="4d6",  # Per ray, multiple rays at higher levels
        damage_type=DamageType.FIRE,
        save_type=None,  # Touch attack, no save
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        requires_attack_roll=True,
        rule_citations=("PHB p.274",),
    ),

    "acid_arrow": SpellDefinition(
        spell_id="acid_arrow",
        name="Melf's Acid Arrow",
        level=2,
        school="conjuration",
        target_type=SpellTarget.RAY,
        range_ft=400,  # Long range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="2d4",  # Initial damage, continues over rounds
        damage_type=DamageType.ACID,
        save_type=None,  # Ranged touch attack
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Damage is per round but computed separately
        concentration=False,
        requires_attack_roll=True,
        rule_citations=("PHB p.253",),
    ),

    # ==========================================================================
    # HEALING SPELLS
    # ==========================================================================

    "cure_light_wounds": SpellDefinition(
        spell_id="cure_light_wounds",
        name="Cure Light Wounds",
        level=1,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,  # Touch
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="1d8",  # +1/level, max +5
        save_type=None,  # Will half for undead (not implemented)
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.215",),
    ),

    "cure_moderate_wounds": SpellDefinition(
        spell_id="cure_moderate_wounds",
        name="Cure Moderate Wounds",
        level=2,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="2d8",  # +1/level, max +10
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.216",),
    ),

    "cure_serious_wounds": SpellDefinition(
        spell_id="cure_serious_wounds",
        name="Cure Serious Wounds",
        level=3,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="3d8",  # +1/level, max +15
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.216",),
    ),

    # ==========================================================================
    # BUFF SPELLS
    # ==========================================================================

    "mage_armor": SpellDefinition(
        spell_id="mage_armor",
        name="Mage Armor",
        level=1,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,  # Touch
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,  # Harmless
        save_effect=SaveEffect.NONE,
        duration_rounds=600,  # 1 hour/level, using 10 rounds per level approx
        concentration=False,
        conditions_on_success=("mage_armor",),
        rule_citations=("PHB p.249",),
    ),

    "bulls_strength": SpellDefinition(
        spell_id="bulls_strength",
        name="Bull's Strength",
        level=2,
        school="transmutation",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,  # Harmless
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # 1 min/level
        concentration=False,
        conditions_on_success=("bulls_strength",),  # +4 enhancement to STR
        rule_citations=("PHB p.207",),
    ),

    "shield": SpellDefinition(
        spell_id="shield",
        name="Shield",
        level=1,
        school="abjuration",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # 1 min/level
        concentration=False,
        conditions_on_success=("shield",),  # +4 shield bonus to AC
        rule_citations=("PHB p.278",),
    ),

    "haste": SpellDefinition(
        spell_id="haste",
        name="Haste",
        level=3,
        school="transmutation",
        target_type=SpellTarget.AREA,
        range_ft=25,  # Close range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=25,  # One creature/level, no two more than 30ft apart
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,  # Harmless
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # 1 round/level
        concentration=False,
        conditions_on_success=("hasted",),
        rule_citations=("PHB p.239",),
    ),

    # ==========================================================================
    # DEBUFF SPELLS
    # ==========================================================================

    "hold_person": SpellDefinition(
        spell_id="hold_person",
        name="Hold Person",
        level=3,
        school="enchantment",
        target_type=SpellTarget.SINGLE,
        range_ft=100,  # Medium range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=10,  # 1 round/level
        concentration=False,
        conditions_on_fail=("paralyzed",),
        rule_citations=("PHB p.241",),
    ),

    "slow": SpellDefinition(
        spell_id="slow",
        name="Slow",
        level=3,
        school="transmutation",
        target_type=SpellTarget.AREA,
        range_ft=25,  # Close range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=30,  # 30-foot burst
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=10,  # 1 round/level
        concentration=False,
        conditions_on_fail=("slowed",),
        rule_citations=("PHB p.280",),
    ),

    "blindness_deafness": SpellDefinition(
        spell_id="blindness_deafness",
        name="Blindness/Deafness",
        level=2,
        school="necromancy",
        target_type=SpellTarget.SINGLE,
        range_ft=100,  # Medium range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.FORT,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=-1,  # Permanent
        concentration=False,
        conditions_on_fail=("blinded",),  # Caster chooses blind or deaf
        rule_citations=("PHB p.206",),
    ),

    "web": SpellDefinition(
        spell_id="web",
        name="Web",
        level=2,
        school="conjuration",
        target_type=SpellTarget.AREA,
        range_ft=100,  # Medium range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=20,  # 20-foot-radius spread
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.REF,
        save_effect=SaveEffect.PARTIAL,  # Reflex to avoid being stuck
        duration_rounds=100,  # 10 min/level
        concentration=False,
        conditions_on_fail=("entangled",),
        rule_citations=("PHB p.301",),
    ),

    # ==========================================================================
    # UTILITY SPELLS
    # ==========================================================================

    "detect_magic": SpellDefinition(
        spell_id="detect_magic",
        name="Detect Magic",
        level=0,
        school="divination",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # Concentration, up to 1 min/level
        concentration=True,
        rule_citations=("PHB p.219",),
    ),

    "light": SpellDefinition(
        spell_id="light",
        name="Light",
        level=0,
        school="evocation",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,  # Will negates if unwilling object
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        rule_citations=("PHB p.248",),
    ),

}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_spell(spell_id: str) -> SpellDefinition:
    """Look up a spell by ID.

    Args:
        spell_id: Unique spell identifier

    Returns:
        SpellDefinition

    Raises:
        KeyError: If spell not found
    """
    if spell_id not in SPELL_REGISTRY:
        raise KeyError(f"Unknown spell: {spell_id}")
    return SPELL_REGISTRY[spell_id]


def get_spells_by_level(level: int) -> Dict[str, SpellDefinition]:
    """Get all spells of a specific level.

    Args:
        level: Spell level (0-9)

    Returns:
        Dictionary of spell_id -> SpellDefinition
    """
    return {
        spell_id: spell
        for spell_id, spell in SPELL_REGISTRY.items()
        if spell.level == level
    }


def get_spells_by_school(school: str) -> Dict[str, SpellDefinition]:
    """Get all spells of a specific school.

    Args:
        school: Spell school (evocation, necromancy, etc.)

    Returns:
        Dictionary of spell_id -> SpellDefinition
    """
    return {
        spell_id: spell
        for spell_id, spell in SPELL_REGISTRY.items()
        if spell.school == school
    }


def get_damage_spells() -> Dict[str, SpellDefinition]:
    """Get all damage-dealing spells."""
    return {
        spell_id: spell
        for spell_id, spell in SPELL_REGISTRY.items()
        if spell.effect_type == SpellEffect.DAMAGE
    }


def get_healing_spells() -> Dict[str, SpellDefinition]:
    """Get all healing spells."""
    return {
        spell_id: spell
        for spell_id, spell in SPELL_REGISTRY.items()
        if spell.effect_type == SpellEffect.HEALING
    }
