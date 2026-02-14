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
        content_id="spell.fireball_003",
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
        content_id="spell.burning_hands_003",
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
        content_id="spell.lightning_bolt_003",
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
        content_id="spell.cone_of_cold_003",
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
        content_id="spell.magic_missile_003",
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
        content_id="spell.scorching_ray_003",
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
        content_id="spell.acid_arrow_003",
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
        content_id="spell.cure_light_wounds_003",
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
        content_id="spell.cure_moderate_wounds_003",
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
        content_id="spell.cure_serious_wounds_003",
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
        content_id="spell.mage_armor_003",
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
        content_id="spell.bulls_strength_003",
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
        content_id="spell.shield_003",
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
        content_id="spell.haste_003",
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
        content_id="spell.hold_person_003",
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
        content_id="spell.slow_003",
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
        content_id="spell.blindness_deafness_003",
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
        content_id="spell.web_003",
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
        content_id="spell.detect_magic_003",
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
        content_id="spell.light_003",
    ),

    # ==========================================================================
    # WO-036: EXPANDED SPELL REGISTRY (33 NEW SPELLS)
    # ==========================================================================

    # ── LEVEL 0 CANTRIPS (4 new) ──

    "resistance": SpellDefinition(
        spell_id="resistance",
        name="Resistance",
        level=0,
        school="abjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # 1 min
        concentration=False,
        conditions_on_success=("resistance",),  # +1 resistance bonus to saves
        rule_citations=("PHB p.272",),
        content_id="spell.resistance_003",
    ),

    "guidance": SpellDefinition(
        spell_id="guidance",
        name="Guidance",
        level=0,
        school="divination",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # 1 min
        concentration=False,
        conditions_on_success=("guidance",),  # +1 competence bonus to attack/save/skill
        rule_citations=("PHB p.238",),
        content_id="spell.guidance_003",
    ),

    "mending": SpellDefinition(
        spell_id="mending",
        name="Mending",
        level=0,
        school="transmutation",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="1d4",  # Repairs 1d4 HP to object
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Instantaneous
        concentration=False,
        rule_citations=("PHB p.253",),
        content_id="spell.mending_003",
    ),

    "read_magic": SpellDefinition(
        spell_id="read_magic",
        name="Read Magic",
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
        duration_rounds=100,  # 10 min/level
        concentration=False,
        rule_citations=("PHB p.269",),
        content_id="spell.read_magic_003",
    ),

    # ── LEVEL 1 SPELLS (6 new) ──

    "bless": SpellDefinition(
        spell_id="bless",
        name="Bless",
        level=1,
        school="enchantment",
        target_type=SpellTarget.AREA,
        range_ft=50,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=50,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # 1 min/level
        concentration=False,
        conditions_on_success=("blessed",),  # +1 morale attack & fear saves
        rule_citations=("PHB p.205",),
        content_id="spell.bless_003",
    ),

    "bane": SpellDefinition(
        spell_id="bane",
        name="Bane",
        level=1,
        school="enchantment",
        target_type=SpellTarget.AREA,
        range_ft=50,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=50,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=10,  # 1 min/level
        concentration=False,
        conditions_on_fail=("bane",),  # -1 morale attack & fear saves
        rule_citations=("PHB p.203",),
        content_id="spell.bane_003",
    ),

    "grease": SpellDefinition(
        spell_id="grease",
        name="Grease",
        level=1,
        school="conjuration",
        target_type=SpellTarget.AREA,
        range_ft=25,  # Close range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=10,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.REF,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=1,  # 1 round/level
        concentration=False,
        conditions_on_fail=("prone",),  # Balance DC 10 or fall prone
        rule_citations=("PHB p.237",),
        content_id="spell.grease_003",
    ),

    "sleep": SpellDefinition(
        spell_id="sleep",
        name="Sleep",
        level=1,
        school="enchantment",
        target_type=SpellTarget.AREA,
        range_ft=100,  # Medium range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=10,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,  # No save — HD-limited effect (PHB p.280)
        save_effect=SaveEffect.NONE,
        duration_rounds=10,  # 1 min/level
        concentration=False,
        conditions_on_fail=("unconscious",),  # HD-limited: affects 4 HD max, lowest HD first
        rule_citations=("PHB p.280", "HD-limited effect: no save, affects 4 HD, lowest HD first"),
        content_id="spell.sleep_003",
    ),

    "entangle": SpellDefinition(
        spell_id="entangle",
        name="Entangle",
        level=1,
        school="transmutation",
        target_type=SpellTarget.AREA,
        range_ft=400,  # Long range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=40,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.REF,
        save_effect=SaveEffect.PARTIAL,
        duration_rounds=10,  # 1 min/level
        concentration=False,
        conditions_on_fail=("entangled",),
        rule_citations=("PHB p.227",),
        content_id="spell.entangle_003",
    ),

    "color_spray": SpellDefinition(
        spell_id="color_spray",
        name="Color Spray",
        level=1,
        school="illusion",
        target_type=SpellTarget.AREA,
        range_ft=0,  # Caster origin
        aoe_shape=AoEShape.CONE,
        aoe_radius_ft=15,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=0,  # Varies by HD
        concentration=False,
        conditions_on_fail=("stunned",),  # Simplified: stunned for all HD
        rule_citations=("PHB p.210", "Effect varies by HD"),
        content_id="spell.color_spray_003",
    ),

    # ── LEVEL 2 SPELLS (7 new) ──

    "invisibility": SpellDefinition(
        spell_id="invisibility",
        name="Invisibility",
        level=2,
        school="illusion",
        target_type=SpellTarget.TOUCH,
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
        conditions_on_success=("invisible",),  # Breaks on attack
        rule_citations=("PHB p.245",),
        content_id="spell.invisibility_003",
    ),

    "mirror_image": SpellDefinition(
        spell_id="mirror_image",
        name="Mirror Image",
        level=2,
        school="illusion",
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
        conditions_on_success=("mirror_image",),  # 1d4+1 duplicates
        rule_citations=("PHB p.254", "Creates 1d4+1 duplicates"),
        content_id="spell.mirror_image_003",
    ),

    "cats_grace": SpellDefinition(
        spell_id="cats_grace",
        name="Cat's Grace",
        level=2,
        school="transmutation",
        target_type=SpellTarget.TOUCH,
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
        conditions_on_success=("cats_grace",),  # +4 DEX
        rule_citations=("PHB p.208",),
        content_id="spell.cats_grace_003",
    ),

    "bears_endurance": SpellDefinition(
        spell_id="bears_endurance",
        name="Bear's Endurance",
        level=2,
        school="transmutation",
        target_type=SpellTarget.TOUCH,
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
        conditions_on_success=("bears_endurance",),  # +4 CON
        rule_citations=("PHB p.203",),
        content_id="spell.bears_endurance_003",
    ),

    "owls_wisdom": SpellDefinition(
        spell_id="owls_wisdom",
        name="Owl's Wisdom",
        level=2,
        school="transmutation",
        target_type=SpellTarget.TOUCH,
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
        conditions_on_success=("owls_wisdom",),  # +4 WIS
        rule_citations=("PHB p.259",),
        content_id="spell.owls_wisdom_003",
    ),

    "resist_energy": SpellDefinition(
        spell_id="resist_energy",
        name="Resist Energy",
        level=2,
        school="abjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        conditions_on_success=("resist_energy",),  # Resistance 10 to chosen energy
        rule_citations=("PHB p.272",),
        content_id="spell.resist_energy_003",
    ),

    "silence": SpellDefinition(
        spell_id="silence",
        name="Silence",
        level=2,
        school="illusion",
        target_type=SpellTarget.AREA,
        range_ft=400,  # Long range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=20,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=1,  # 1 round/level
        concentration=False,
        conditions_on_fail=("silenced",),  # No sound, blocks verbal spells
        rule_citations=("PHB p.279",),
        content_id="spell.silence_003",
    ),

    # ── LEVEL 3 SPELLS (5 new) ──

    "dispel_magic": SpellDefinition(
        spell_id="dispel_magic",
        name="Dispel Magic",
        level=3,
        school="abjuration",
        target_type=SpellTarget.SINGLE,
        range_ft=100,  # Medium range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Instantaneous
        concentration=False,
        conditions_on_success=(),  # Caster level check to remove effects
        rule_citations=("PHB p.223", "Caster level check required"),
        content_id="spell.dispel_magic_003",
    ),

    "protection_from_energy": SpellDefinition(
        spell_id="protection_from_energy",
        name="Protection from Energy",
        level=3,
        school="abjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        conditions_on_success=("protection_from_energy",),  # Absorbs 12/level (max 120)
        rule_citations=("PHB p.266",),
        content_id="spell.protection_from_energy_003",
    ),

    "magic_circle_against_evil": SpellDefinition(
        spell_id="magic_circle_against_evil",
        name="Magic Circle against Evil",
        level=3,
        school="abjuration",
        target_type=SpellTarget.AREA,
        range_ft=0,  # Self + 10ft radius
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=10,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        conditions_on_success=("magic_circle_evil",),  # +2 deflection AC, +2 resistance saves
        rule_citations=("PHB p.249",),
        content_id="spell.magic_circle_against_evil_003",
    ),

    "fly": SpellDefinition(
        spell_id="fly",
        name="Fly",
        level=3,
        school="transmutation",
        target_type=SpellTarget.TOUCH,
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
        conditions_on_success=("flying",),  # Fly speed 60ft
        rule_citations=("PHB p.232",),
        content_id="spell.fly_003",
    ),

    "stinking_cloud": SpellDefinition(
        spell_id="stinking_cloud",
        name="Stinking Cloud",
        level=3,
        school="conjuration",
        target_type=SpellTarget.AREA,
        range_ft=100,  # Medium range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=20,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.FORT,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=1,  # 1 round/level
        concentration=True,  # Concentration required
        conditions_on_fail=("nauseated",),  # Nauseated 1d4+1 rounds
        rule_citations=("PHB p.284",),
        content_id="spell.stinking_cloud_003",
    ),

    # ── LEVEL 4 SPELLS (6 new) ──

    "cure_critical_wounds": SpellDefinition(
        spell_id="cure_critical_wounds",
        name="Cure Critical Wounds",
        level=4,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="4d8",  # +1/level, max +20
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Instantaneous
        concentration=False,
        rule_citations=("PHB p.215",),
        content_id="spell.cure_critical_wounds_003",
    ),

    "stoneskin": SpellDefinition(
        spell_id="stoneskin",
        name="Stoneskin",
        level=4,
        school="abjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        conditions_on_success=("stoneskin",),  # DR 10/adamantine (max 150 absorbed)
        rule_citations=("PHB p.284", "DR 10/adamantine, max 150 damage absorbed"),
        content_id="spell.stoneskin_003",
    ),

    "wall_of_fire": SpellDefinition(
        spell_id="wall_of_fire",
        name="Wall of Fire",
        level=4,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=100,  # Medium range
        aoe_shape=AoEShape.LINE,
        aoe_radius_ft=20,  # 20ft long wall
        effect_type=SpellEffect.DAMAGE,
        damage_dice="2d4",  # Within 10ft, 2d6+CL passing through
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=1,  # Concentration + 1 round/level (PHB p.298)
        concentration=True,  # Concentration required
        rule_citations=("PHB p.298",),
        content_id="spell.wall_of_fire_003",
    ),

    "dimension_door": SpellDefinition(
        spell_id="dimension_door",
        name="Dimension Door",
        level=4,
        school="conjuration",
        target_type=SpellTarget.SELF,
        range_ft=400,  # 400ft + 40ft/level
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Instantaneous
        concentration=False,
        rule_citations=("PHB p.221", "Teleport up to range"),
        content_id="spell.dimension_door_003",
    ),

    "greater_invisibility": SpellDefinition(
        spell_id="greater_invisibility",
        name="Greater Invisibility",
        level=4,
        school="illusion",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=1,  # 1 round/level
        concentration=False,
        conditions_on_success=("greater_invisibility",),  # Invisible even while attacking
        rule_citations=("PHB p.245",),
        content_id="spell.greater_invisibility_003",
    ),

    "ice_storm": SpellDefinition(
        spell_id="ice_storm",
        name="Ice Storm",
        level=4,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=400,  # Long range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=20,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="5d6",  # 3d6 bludgeoning + 2d6 cold (simplified to 5d6)
        damage_type=DamageType.COLD,
        save_type=None,  # No save
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Instantaneous
        concentration=False,
        rule_citations=("PHB p.243", "3d6 bludgeoning + 2d6 cold, no save"),
        content_id="spell.ice_storm_003",
    ),

    # ── LEVEL 5 SPELLS (5 new) ──

    "hold_monster": SpellDefinition(
        spell_id="hold_monster",
        name="Hold Monster",
        level=5,
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
        duration_rounds=1,  # 1 round/level
        concentration=False,
        conditions_on_fail=("paralyzed",),
        rule_citations=("PHB p.241",),
        content_id="spell.hold_monster_003",
    ),

    "wall_of_stone": SpellDefinition(
        spell_id="wall_of_stone",
        name="Wall of Stone",
        level=5,
        school="conjuration",
        target_type=SpellTarget.AREA,
        range_ft=100,  # Medium range
        aoe_shape=AoEShape.LINE,
        aoe_radius_ft=0,  # Variable size
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=-1,  # Permanent
        concentration=False,
        rule_citations=("PHB p.299", "Create stone wall, permanent"),
        content_id="spell.wall_of_stone_003",
    ),

    "raise_dead": SpellDefinition(
        spell_id="raise_dead",
        name="Raise Dead",
        level=5,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="0",  # Restore life, not HP
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Instantaneous
        concentration=False,
        rule_citations=("PHB p.268", "Restore life, -1 level"),
        content_id="spell.raise_dead_003",
    ),

    "telekinesis": SpellDefinition(
        spell_id="telekinesis",
        name="Telekinesis",
        level=5,
        school="transmutation",
        target_type=SpellTarget.SINGLE,
        range_ft=400,  # Long range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=1,  # 1 round/level
        concentration=True,  # Concentration required
        rule_citations=("PHB p.292", "Move 25lb/level, concentration"),
        content_id="spell.telekinesis_003",
    ),

    "baleful_polymorph": SpellDefinition(
        spell_id="baleful_polymorph",
        name="Baleful Polymorph",
        level=5,
        school="transmutation",
        target_type=SpellTarget.SINGLE,
        range_ft=25,  # Close range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.FORT,
        save_effect=SaveEffect.NEGATES,
        duration_rounds=-1,  # Permanent
        concentration=False,
        conditions_on_fail=("polymorphed",),  # Transform into animal
        rule_citations=("PHB p.202",),
        content_id="spell.baleful_polymorph_003",
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
