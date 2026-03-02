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
        damage_dice=None,           # WO-ENGINE-CL-DAMAGE-SCALE-001: CL-scaled below
        damage_dice_per_cl="d6",    # 1d6 per CL (PHB p.231)
        max_damage_cl=10,           # Cap at 10d6
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
        damage_dice=None,           # WO-ENGINE-CL-DAMAGE-SCALE-001: CL-scaled below
        damage_dice_per_cl="d6",    # 1d6 per CL (PHB p.243)
        max_damage_cl=10,           # Cap at 10d6
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
    # INFLICT SPELLS (WO-ENGINE-EVIL-CLERIC-INFLICT-001)
    # PHB p.244-245: Necromancy, deals negative energy damage to living (heals undead).
    # Evil cleric spontaneous swap — mirrors cure spells by level.
    # ==========================================================================

    "inflict_light_wounds": SpellDefinition(
        spell_id="inflict_light_wounds",
        name="Inflict Light Wounds",
        level=1,
        school="necromancy",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="1d8",
        damage_type=DamageType.NEGATIVE,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.244",),
        content_id="spell.inflict_light_wounds_003",
    ),

    "inflict_moderate_wounds": SpellDefinition(
        spell_id="inflict_moderate_wounds",
        name="Inflict Moderate Wounds",
        level=2,
        school="necromancy",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="2d8",
        damage_type=DamageType.NEGATIVE,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.244",),
        content_id="spell.inflict_moderate_wounds_003",
    ),

    "inflict_serious_wounds": SpellDefinition(
        spell_id="inflict_serious_wounds",
        name="Inflict Serious Wounds",
        level=3,
        school="necromancy",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="3d8",
        damage_type=DamageType.NEGATIVE,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.244",),
        content_id="spell.inflict_serious_wounds_003",
    ),

    "inflict_critical_wounds": SpellDefinition(
        spell_id="inflict_critical_wounds",
        name="Inflict Critical Wounds",
        level=4,
        school="necromancy",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="4d8",
        damage_type=DamageType.NEGATIVE,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.244",),
        content_id="spell.inflict_critical_wounds_003",
    ),

    "mass_inflict_light_wounds": SpellDefinition(
        spell_id="mass_inflict_light_wounds",
        name="Inflict Light Wounds, Mass",
        level=5,
        school="necromancy",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="1d8",
        damage_type=DamageType.NEGATIVE,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.244",),
        content_id="spell.mass_inflict_light_wounds_003",
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
        duration_rounds=0,              # WO-ENGINE-CL-DURATION-SCALE-001: CL-scaled below
        duration_rounds_per_cl=1,       # 1 round/level (PHB p.239)
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
        duration_rounds=0,              # WO-ENGINE-CL-DURATION-SCALE-001: CL-scaled below
        duration_rounds_per_cl=1,       # 1 round/level (PHB p.280)
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
        spell_resistance=False,  # WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001: PHB p.301 SR: No
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
        duration_rounds=0,              # WO-ENGINE-CL-DURATION-SCALE-001: CL-scaled below
        duration_rounds_per_cl=10,      # 1 min/level = 10 rounds/level (PHB p.205)
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
        spell_resistance=False,  # WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001: PHB p.237 SR: No
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
        spell_resistance=False,  # WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001: PHB p.284 SR: No
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

    # ==========================================================================
    # WO-CHARGEN-SPELL-EXPANSION: LEVEL 6-9 SPELLS (28 new)
    # ==========================================================================

    # ── LEVEL 6 SPELLS (7 new) ──

    "chain_lightning": SpellDefinition(
        spell_id="chain_lightning",
        name="Chain Lightning",
        level=6,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=400,  # Long range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="12d6",  # 1d6/level, max 20d6 primary; secondary arcs
        damage_type=DamageType.ELECTRICITY,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.208",),
        content_id="spell.chain_lightning_003",
    ),

    "disintegrate": SpellDefinition(
        spell_id="disintegrate",
        name="Disintegrate",
        level=6,
        school="transmutation",
        target_type=SpellTarget.RAY,
        range_ft=100,  # Medium range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="22d6",  # 2d6/level, max 40d6
        damage_type=DamageType.FORCE,
        save_type=SaveType.FORT,
        save_effect=SaveEffect.PARTIAL,  # 5d6 on save
        duration_rounds=0,
        concentration=False,
        requires_attack_roll=True,
        rule_citations=("PHB p.222", "Fort save: 5d6 instead of full"),
        content_id="spell.disintegrate_003",
    ),

    "heal_spell": SpellDefinition(
        spell_id="heal_spell",
        name="Heal",
        level=6,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="150",  # Heals 10/level, max 150
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.239",),
        content_id="spell.heal_spell_003",
    ),

    "greater_dispel_magic": SpellDefinition(
        spell_id="greater_dispel_magic",
        name="Greater Dispel Magic",
        level=6,
        school="abjuration",
        target_type=SpellTarget.SINGLE,
        range_ft=100,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.223", "No caster level cap on dispel check"),
        content_id="spell.greater_dispel_magic_003",
    ),

    "true_seeing": SpellDefinition(
        spell_id="true_seeing",
        name="True Seeing",
        level=6,
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
        duration_rounds=10,  # 1 min/level
        concentration=False,
        conditions_on_success=("true_seeing",),
        rule_citations=("PHB p.296",),
        content_id="spell.true_seeing_003",
    ),

    "antimagic_field": SpellDefinition(
        spell_id="antimagic_field",
        name="Antimagic Field",
        level=6,
        school="abjuration",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=10,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        rule_citations=("PHB p.200", "Suppresses all magic in 10-ft emanation"),
        content_id="spell.antimagic_field_003",
    ),

    "blade_barrier": SpellDefinition(
        spell_id="blade_barrier",
        name="Blade Barrier",
        level=6,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=100,
        aoe_shape=AoEShape.LINE,
        aoe_radius_ft=20,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="11d6",  # 1d6/level, max 15d6
        damage_type=DamageType.UNTYPED,  # Slashing (physical), not an energy type
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=10,  # 1 min/level
        concentration=False,
        rule_citations=("PHB p.205",),
        content_id="spell.blade_barrier_003",
    ),

    # ── LEVEL 7 SPELLS (7 new) ──

    "finger_of_death": SpellDefinition(
        spell_id="finger_of_death",
        name="Finger of Death",
        level=7,
        school="necromancy",
        target_type=SpellTarget.SINGLE,
        range_ft=25,  # Close range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="10d6+10",  # Fort save or die; 3d6+CL on save
        damage_type=DamageType.NEGATIVE,
        save_type=SaveType.FORT,
        save_effect=SaveEffect.PARTIAL,  # 3d6+CL on save instead of death
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.230", "Fort: 3d6+CL instead of death"),
        content_id="spell.finger_of_death_003",
    ),

    "delayed_blast_fireball": SpellDefinition(
        spell_id="delayed_blast_fireball",
        name="Delayed Blast Fireball",
        level=7,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=400,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=20,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="12d6",  # 1d6/level, max 20d6
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.217", "Can delay up to 5 rounds"),
        content_id="spell.delayed_blast_fireball_003",
    ),

    "greater_teleport": SpellDefinition(
        spell_id="greater_teleport",
        name="Greater Teleport",
        level=7,
        school="conjuration",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.293", "No range limit, no off-target chance"),
        content_id="spell.greater_teleport_003",
    ),

    "regenerate": SpellDefinition(
        spell_id="regenerate",
        name="Regenerate",
        level=7,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="4d8+35",  # 4d8+CL (max CL 35) and regrows severed limbs
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.270", "Regrows severed limbs"),
        content_id="spell.regenerate_003",
    ),

    "resurrection": SpellDefinition(
        spell_id="resurrection",
        name="Resurrection",
        level=7,
        school="conjuration",
        target_type=SpellTarget.TOUCH,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="0",
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.272", "Restore life, no level loss, body not required to be present"),
        content_id="spell.resurrection_003",
    ),

    "prismatic_spray": SpellDefinition(
        spell_id="prismatic_spray",
        name="Prismatic Spray",
        level=7,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=0,  # Caster origin
        aoe_shape=AoEShape.CONE,
        aoe_radius_ft=60,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="10d6",  # Varies by color; simplified
        damage_type=DamageType.FORCE,  # Mixed types, simplified
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,  # Varies by color
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.264", "Random color determines effect"),
        content_id="spell.prismatic_spray_003",
    ),

    "reverse_gravity": SpellDefinition(
        spell_id="reverse_gravity",
        name="Reverse Gravity",
        level=7,
        school="transmutation",
        target_type=SpellTarget.AREA,
        range_ft=100,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=30,  # Cylinder: 30ft radius
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.REF,
        save_effect=SaveEffect.NEGATES,  # Grab hold of something
        duration_rounds=1,  # 1 round/level
        concentration=False,
        conditions_on_fail=("reverse_gravity",),
        rule_citations=("PHB p.273",),
        content_id="spell.reverse_gravity_003",
    ),

    # ── LEVEL 8 SPELLS (7 new) ──

    "horrid_wilting": SpellDefinition(
        spell_id="horrid_wilting",
        name="Horrid Wilting",
        level=8,
        school="necromancy",
        target_type=SpellTarget.AREA,
        range_ft=400,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=30,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="15d6",  # 1d6/level, max 20d6
        damage_type=DamageType.NEGATIVE,
        save_type=SaveType.FORT,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.242",),
        content_id="spell.horrid_wilting_003",
    ),

    "polar_ray": SpellDefinition(
        spell_id="polar_ray",
        name="Polar Ray",
        level=8,
        school="evocation",
        target_type=SpellTarget.RAY,
        range_ft=25,  # Close range
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="15d6",  # 1d6/level, max 25d6
        damage_type=DamageType.COLD,
        save_type=None,  # No save, ranged touch
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        requires_attack_roll=True,
        rule_citations=("PHB p.262",),
        content_id="spell.polar_ray_003",
    ),

    "sunburst": SpellDefinition(
        spell_id="sunburst",
        name="Sunburst",
        level=8,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=400,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=80,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="6d6",  # Plus blindness
        damage_type=DamageType.FIRE,  # Bright light/radiant, simplified as fire
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,  # Half damage, no blindness on save
        duration_rounds=0,
        concentration=False,
        conditions_on_fail=("blinded",),
        rule_citations=("PHB p.289", "6d6 damage + permanent blindness"),
        content_id="spell.sunburst_003",
    ),

    "power_word_stun": SpellDefinition(
        spell_id="power_word_stun",
        name="Power Word Stun",
        level=8,
        school="enchantment",
        target_type=SpellTarget.SINGLE,
        range_ft=25,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,  # No save
        save_effect=SaveEffect.NONE,
        duration_rounds=4,  # Varies by current HP
        concentration=False,
        conditions_on_fail=("stunned",),  # Stuns creature with <=150 HP
        rule_citations=("PHB p.263", "No save, stuns creature with <=150 current HP"),
        content_id="spell.power_word_stun_003",
    ),

    "greater_planar_ally": SpellDefinition(
        spell_id="greater_planar_ally",
        name="Greater Planar Ally",
        level=8,
        school="conjuration",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # Instantaneous (negotiated service)
        concentration=False,
        rule_citations=("PHB p.261", "Calls outsider of up to 18 HD"),
        content_id="spell.greater_planar_ally_003",
    ),

    "mass_cure_critical_wounds": SpellDefinition(
        spell_id="mass_cure_critical_wounds",
        name="Mass Cure Critical Wounds",
        level=8,
        school="conjuration",
        target_type=SpellTarget.AREA,
        range_ft=25,  # Close range
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=30,
        effect_type=SpellEffect.HEALING,
        damage_dice=None,
        damage_type=None,
        healing_dice="4d8",  # +1/level per creature, max +20
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.216",),
        content_id="spell.mass_cure_critical_wounds_003",
    ),

    "mind_blank": SpellDefinition(
        spell_id="mind_blank",
        name="Mind Blank",
        level=8,
        school="abjuration",
        target_type=SpellTarget.SINGLE,
        range_ft=25,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=14400,  # 24 hours
        concentration=False,
        conditions_on_success=("mind_blank",),
        rule_citations=("PHB p.253", "Immune to divination, mind-affecting"),
        content_id="spell.mind_blank_003",
    ),

    # ── LEVEL 9 SPELLS (7 new) ──

    "wish": SpellDefinition(
        spell_id="wish",
        name="Wish",
        level=9,
        school="universal",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.302", "Duplicate any 8th-level or lower spell, or greater effects"),
        content_id="spell.wish_003",
    ),

    "meteor_swarm": SpellDefinition(
        spell_id="meteor_swarm",
        name="Meteor Swarm",
        level=9,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=400,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=40,  # Four 40-ft radius spreads
        effect_type=SpellEffect.DAMAGE,
        damage_dice="24d6",  # 6d6 per meteor x4, simplified
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.253", "Four meteors: 2d6 bludgeon + 6d6 fire each"),
        content_id="spell.meteor_swarm_003",
    ),

    "power_word_kill": SpellDefinition(
        spell_id="power_word_kill",
        name="Power Word Kill",
        level=9,
        school="enchantment",
        target_type=SpellTarget.SINGLE,
        range_ft=25,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.DEBUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,  # No save
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        conditions_on_fail=("dead",),  # Kills creature with <=100 HP
        rule_citations=("PHB p.262", "No save, kills creature with <=100 current HP"),
        content_id="spell.power_word_kill_003",
    ),

    "gate": SpellDefinition(
        spell_id="gate",
        name="Gate",
        level=9,
        school="conjuration",
        target_type=SpellTarget.SELF,
        range_ft=100,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=1,  # 1 round/level
        concentration=True,
        rule_citations=("PHB p.234", "Opens portal to another plane, or calls specific being"),
        content_id="spell.gate_003",
    ),

    "miracle": SpellDefinition(
        spell_id="miracle",
        name="Miracle",
        level=9,
        school="evocation",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=False,
        rule_citations=("PHB p.254", "Divine equivalent of wish"),
        content_id="spell.miracle_003",
    ),

    "prismatic_sphere": SpellDefinition(
        spell_id="prismatic_sphere",
        name="Prismatic Sphere",
        level=9,
        school="abjuration",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=10,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        conditions_on_success=("prismatic_sphere",),
        rule_citations=("PHB p.264", "Seven-layered protective sphere"),
        content_id="spell.prismatic_sphere_003",
    ),

    "time_stop": SpellDefinition(
        spell_id="time_stop",
        name="Time Stop",
        level=9,
        school="transmutation",
        target_type=SpellTarget.SELF,
        range_ft=0,
        aoe_shape=None,
        aoe_radius_ft=None,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=3,  # 1d4+1 rounds of apparent time
        concentration=False,
        conditions_on_success=("time_stop",),
        rule_citations=("PHB p.294", "1d4+1 rounds of apparent time, can't affect others"),
        content_id="spell.time_stop_003",
    ),

    # ==========================================================================
    # WO-ENGINE-ARCANE-SPELL-FAILURE-001: V-only spells (no somatic component)
    # PHB: these spells require only verbal components; armor does not interfere.
    # ==========================================================================

    "message": SpellDefinition(
        spell_id="message",
        name="Message",
        level=0,
        school="transmutation",
        target_type=SpellTarget.SINGLE,
        range_ft=100,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        has_somatic=False,  # V-only: no somatic component -- PHB p.254
        rule_citations=("PHB p.254",),
    ),

    "silent_image": SpellDefinition(
        spell_id="silent_image",
        name="Silent Image",
        level=1,
        school="illusion",
        target_type=SpellTarget.SINGLE,
        range_ft=400,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,
        concentration=True,
        has_somatic=False,  # V-only: no somatic component -- PHB p.279
        rule_citations=("PHB p.279",),
    ),

    "alarm": SpellDefinition(
        spell_id="alarm",
        name="Alarm",
        level=1,
        school="abjuration",
        target_type=SpellTarget.AREA,
        range_ft=30,
        aoe_shape=AoEShape.BURST,
        aoe_radius_ft=20,
        effect_type=SpellEffect.UTILITY,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=0,  # 2 hours/level
        concentration=False,
        has_somatic=False,  # V-only: no somatic component -- PHB p.197
        rule_citations=("PHB p.197",),
    ),

    "tongues": SpellDefinition(
        spell_id="tongues",
        name="Tongues",
        level=3,
        school="divination",
        target_type=SpellTarget.SINGLE,
        range_ft=0,
        effect_type=SpellEffect.BUFF,
        damage_dice=None,
        damage_type=None,
        save_type=None,
        save_effect=SaveEffect.NONE,
        duration_rounds=100,  # 10 min/level
        concentration=False,
        has_somatic=False,  # V-only: no somatic component -- PHB p.294
        rule_citations=("PHB p.294",),
    ),

    # ==========================================================================
    # WO-DATA-SPELLS-001 STUB ENTRIES — PHB spells not yet in registry
    # ==========================================================================
    # Fields from PHB component/school/level facts (facts are not copyrightable).
    # effect_type=SpellEffect.UTILITY for stubs where PCGen has no effect data.
    # Behavior fields (damage_dice, save_type, etc.) filled by future WOs as needed.
    # ==========================================================================

    # -- Level 0 ---------------------------------------------------------------
    "arcane_mark": SpellDefinition(
        spell_id="arcane_mark", name="Arcane Mark", level=0, school="universal",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.201",),
    ),
    "dancing_lights": SpellDefinition(
        spell_id="dancing_lights", name="Dancing Lights", level=0, school="evocation",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.216",),
    ),
    "daze": SpellDefinition(
        spell_id="daze", name="Daze", level=0, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.217",),
    ),
    "disrupt_undead": SpellDefinition(
        spell_id="disrupt_undead", name="Disrupt Undead", level=0, school="necromancy",
        target_type=SpellTarget.RAY, range_ft=25, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d6", has_verbal=True, has_somatic=True, rule_citations=("PHB p.222",),
    ),
    "flare": SpellDefinition(
        spell_id="flare", name="Flare", level=0, school="evocation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=False, rule_citations=("PHB p.232",),
    ),
    "ghost_sound": SpellDefinition(
        spell_id="ghost_sound", name="Ghost Sound", level=0, school="illusion",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.235",),
    ),
    "know_direction": SpellDefinition(
        spell_id="know_direction", name="Know Direction", level=0, school="divination",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.246",),
    ),
    "mage_hand": SpellDefinition(
        spell_id="mage_hand", name="Mage Hand", level=0, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.249",),
    ),
    "mending": SpellDefinition(
        spell_id="mending", name="Mending", level=0, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.253",),
    ),
    "open_close": SpellDefinition(
        spell_id="open_close", name="Open/Close", level=0, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.258",),
    ),
    "prestidigitation": SpellDefinition(
        spell_id="prestidigitation", name="Prestidigitation", level=0, school="universal",
        target_type=SpellTarget.SINGLE, range_ft=10, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.264",),
    ),
    "read_magic": SpellDefinition(
        spell_id="read_magic", name="Read Magic", level=0, school="divination",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.269",),
    ),
    "resistance": SpellDefinition(
        spell_id="resistance", name="Resistance", level=0, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=1, rule_citations=("PHB p.270",),
    ),
    "touch_of_fatigue": SpellDefinition(
        spell_id="touch_of_fatigue", name="Touch of Fatigue", level=0, school="necromancy",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True, rule_citations=("PHB p.295",),
    ),
    "virtue": SpellDefinition(
        spell_id="virtue", name="Virtue", level=0, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=1, rule_citations=("PHB p.298",),
    ),

    # -- Level 1 ---------------------------------------------------------------
    "animate_rope": SpellDefinition(
        spell_id="animate_rope", name="Animate Rope", level=1, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.200",),
    ),
    "cause_fear": SpellDefinition(
        spell_id="cause_fear", name="Cause Fear", level=1, school="necromancy",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=2,         # PHB p.208: 1d4 rounds — static midpoint; dice-duration hook deferred
        duration_rounds_per_cl=0,  # NOT per-CL; cause_fear is flat 1d4 (PHB p.229 *fear* = 1r/CL)
        rule_citations=("PHB p.208",),
    ),
    "charm_person": SpellDefinition(
        spell_id="charm_person", name="Charm Person", level=1, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=600, rule_citations=("PHB p.209",),
    ),
    "color_spray": SpellDefinition(
        spell_id="color_spray", name="Color Spray", level=1, school="illusion",
        target_type=SpellTarget.AREA, range_ft=0, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.210",),
    ),
    "comprehend_languages": SpellDefinition(
        spell_id="comprehend_languages", name="Comprehend Languages", level=1, school="divination",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.212",),
    ),
    "disguise_self": SpellDefinition(
        spell_id="disguise_self", name="Disguise Self", level=1, school="illusion",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.222",),
    ),
    "endure_elements": SpellDefinition(
        spell_id="endure_elements", name="Endure Elements", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=1440, rule_citations=("PHB p.226",),
    ),
    "enlarge_person": SpellDefinition(
        spell_id="enlarge_person", name="Enlarge Person", level=1, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.BUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.226",),
    ),
    "expeditious_retreat": SpellDefinition(
        spell_id="expeditious_retreat", name="Expeditious Retreat", level=1, school="transmutation",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.228",),
    ),
    "feather_fall": SpellDefinition(
        spell_id="feather_fall", name="Feather Fall", level=1, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.BUFF,
        has_verbal=False, has_somatic=False, duration_rounds=10, rule_citations=("PHB p.229",),
    ),
    "grease": SpellDefinition(
        spell_id="grease", name="Grease", level=1, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.REF, has_verbal=True, has_somatic=True,
        duration_rounds=10,
        spell_resistance=False,  # WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001: PHB p.237 SR: No
        rule_citations=("PHB p.237",),
    ),
    "hide_from_animals": SpellDefinition(
        spell_id="hide_from_animals", name="Hide from Animals", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=False, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.240",),
    ),
    "hide_from_undead": SpellDefinition(
        spell_id="hide_from_undead", name="Hide from Undead", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.240",),
    ),
    "hypnotism": SpellDefinition(
        spell_id="hypnotism", name="Hypnotism", level=1, school="enchantment",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=20, rule_citations=("PHB p.242",),
    ),
    "identify": SpellDefinition(
        spell_id="identify", name="Identify", level=1, school="divination",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.243",),
    ),
    "jump": SpellDefinition(
        spell_id="jump", name="Jump", level=1, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.246",),
    ),
    "longstrider": SpellDefinition(
        spell_id="longstrider", name="Longstrider", level=1, school="transmutation",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.249",),
    ),
    "magic_weapon": SpellDefinition(
        spell_id="magic_weapon", name="Magic Weapon", level=1, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.251",),
    ),
    "obscuring_mist": SpellDefinition(
        spell_id="obscuring_mist", name="Obscuring Mist", level=1, school="conjuration",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.258",),
    ),
    "protection_from_chaos": SpellDefinition(
        spell_id="protection_from_chaos", name="Protection from Chaos", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.266",),
    ),
    "protection_from_evil": SpellDefinition(
        spell_id="protection_from_evil", name="Protection from Evil", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.266",),
    ),
    "protection_from_good": SpellDefinition(
        spell_id="protection_from_good", name="Protection from Good", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.267",),
    ),
    "protection_from_law": SpellDefinition(
        spell_id="protection_from_law", name="Protection from Law", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.267",),
    ),
    "reduce_person": SpellDefinition(
        spell_id="reduce_person", name="Reduce Person", level=1, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.BUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.269",),
    ),
    "remove_fear": SpellDefinition(
        spell_id="remove_fear", name="Remove Fear", level=1, school="abjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.270",),
    ),
    "sanctuary": SpellDefinition(
        spell_id="sanctuary", name="Sanctuary", level=1, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.274",),
    ),
    "sleep": SpellDefinition(
        spell_id="sleep", name="Sleep", level=1, school="enchantment",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.280",),
    ),
    "summon_monster_i": SpellDefinition(
        spell_id="summon_monster_i", name="Summon Monster I", level=1, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "unseen_servant": SpellDefinition(
        spell_id="unseen_servant", name="Unseen Servant", level=1, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.297",),
    ),

    # -- Level 2 ---------------------------------------------------------------
    "alter_self": SpellDefinition(
        spell_id="alter_self", name="Alter Self", level=2, school="transmutation",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.197",),
    ),
    "arcane_lock": SpellDefinition(
        spell_id="arcane_lock", name="Arcane Lock", level=2, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=9999, rule_citations=("PHB p.201",),
    ),
    "bears_endurance": SpellDefinition(
        spell_id="bears_endurance", name="Bear's Endurance", level=2, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.203",),
    ),
    "cats_grace": SpellDefinition(
        spell_id="cats_grace", name="Cat's Grace", level=2, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.208",),
    ),
    "command_undead": SpellDefinition(
        spell_id="command_undead", name="Command Undead", level=2, school="necromancy",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=1440, rule_citations=("PHB p.211",),
    ),
    "darkness": SpellDefinition(
        spell_id="darkness", name="Darkness", level=2, school="evocation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=False, duration_rounds=10, rule_citations=("PHB p.216",),
    ),
    "darkvision": SpellDefinition(
        spell_id="darkvision", name="Darkvision", level=2, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.216",),
    ),
    "daze_monster": SpellDefinition(
        spell_id="daze_monster", name="Daze Monster", level=2, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.217",),
    ),
    "eagles_splendor": SpellDefinition(
        spell_id="eagles_splendor", name="Eagle's Splendor", level=2, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.225",),
    ),
    "false_life": SpellDefinition(
        spell_id="false_life", name="False Life", level=2, school="necromancy",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.229",),
    ),
    "fog_cloud": SpellDefinition(
        spell_id="fog_cloud", name="Fog Cloud", level=2, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10,
        spell_resistance=False,  # WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001: PHB p.232 SR: No
        rule_citations=("PHB p.232",),
    ),
    "ghoul_touch": SpellDefinition(
        spell_id="ghoul_touch", name="Ghoul Touch", level=2, school="necromancy",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.235",),
    ),
    "glitterdust": SpellDefinition(
        spell_id="glitterdust", name="Glitterdust", level=2, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.236",),
    ),
    "invisibility": SpellDefinition(
        spell_id="invisibility", name="Invisibility", level=2, school="illusion",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.245",),
    ),
    "knock": SpellDefinition(
        spell_id="knock", name="Knock", level=2, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=False, rule_citations=("PHB p.246",),
    ),
    "levitate": SpellDefinition(
        spell_id="levitate", name="Levitate", level=2, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.BUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=100, rule_citations=("PHB p.248",),
    ),
    "locate_object": SpellDefinition(
        spell_id="locate_object", name="Locate Object", level=2, school="divination",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.249",),
    ),
    "mirror_image": SpellDefinition(
        spell_id="mirror_image", name="Mirror Image", level=2, school="illusion",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.254",),
    ),
    "owls_wisdom": SpellDefinition(
        spell_id="owls_wisdom", name="Owl's Wisdom", level=2, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.259",),
    ),
    "remove_paralysis": SpellDefinition(
        spell_id="remove_paralysis", name="Remove Paralysis", level=2, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.271",),
    ),
    "resist_energy": SpellDefinition(
        spell_id="resist_energy", name="Resist Energy", level=2, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.272",),
    ),
    "scare": SpellDefinition(
        spell_id="scare", name="Scare", level=2, school="necromancy",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.274",),
    ),
    "see_invisibility": SpellDefinition(
        spell_id="see_invisibility", name="See Invisibility", level=2, school="divination",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.275",),
    ),
    "shatter": SpellDefinition(
        spell_id="shatter", name="Shatter", level=2, school="evocation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DAMAGE,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.278",),
    ),
    "silence": SpellDefinition(
        spell_id="silence", name="Silence", level=2, school="illusion",
        target_type=SpellTarget.SINGLE, range_ft=400, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=False,
        duration_rounds=10, rule_citations=("PHB p.279",),
    ),
    "spider_climb": SpellDefinition(
        spell_id="spider_climb", name="Spider Climb", level=2, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.283",),
    ),
    "summon_monster_ii": SpellDefinition(
        spell_id="summon_monster_ii", name="Summon Monster II", level=2, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "touch_of_idiocy": SpellDefinition(
        spell_id="touch_of_idiocy", name="Touch of Idiocy", level=2, school="enchantment",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.294",),
    ),

    # -- Level 3 ---------------------------------------------------------------
    "arcane_sight": SpellDefinition(
        spell_id="arcane_sight", name="Arcane Sight", level=3, school="divination",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.201",),
    ),
    "bestow_curse": SpellDefinition(
        spell_id="bestow_curse", name="Bestow Curse", level=3, school="necromancy",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=9999, rule_citations=("PHB p.203",),
    ),
    "clairaudience_clairvoyance": SpellDefinition(
        spell_id="clairaudience_clairvoyance", name="Clairaudience/Clairvoyance",
        level=3, school="divination",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.209",),
    ),
    "contagion": SpellDefinition(
        spell_id="contagion", name="Contagion", level=3, school="necromancy",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True, rule_citations=("PHB p.213",),
    ),
    "daylight": SpellDefinition(
        spell_id="daylight", name="Daylight", level=3, school="evocation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.216",),
    ),
    "deep_slumber": SpellDefinition(
        spell_id="deep_slumber", name="Deep Slumber", level=3, school="enchantment",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=100, rule_citations=("PHB p.218",),
    ),
    "dispel_magic": SpellDefinition(
        spell_id="dispel_magic", name="Dispel Magic", level=3, school="abjuration",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.223",),
    ),
    "explosive_runes": SpellDefinition(
        spell_id="explosive_runes", name="Explosive Runes", level=3, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.DAMAGE,
        damage_dice="6d6", save_type=SaveType.REF, save_effect=SaveEffect.HALF,
        has_verbal=True, has_somatic=True, duration_rounds=9999, rule_citations=("PHB p.228",),
    ),
    "greater_magic_weapon": SpellDefinition(
        spell_id="greater_magic_weapon", name="Greater Magic Weapon", level=3, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.238",),
    ),
    "heroism": SpellDefinition(
        spell_id="heroism", name="Heroism", level=3, school="enchantment",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.240",),
    ),
    "magic_circle_against_evil": SpellDefinition(
        spell_id="magic_circle_against_evil", name="Magic Circle against Evil",
        level=3, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.249",),
    ),
    "magic_circle_against_chaos": SpellDefinition(
        spell_id="magic_circle_against_chaos", name="Magic Circle against Chaos",
        level=3, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.249",),
    ),
    "neutralize_poison": SpellDefinition(
        spell_id="neutralize_poison", name="Neutralize Poison", level=3, school="conjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.257",),
    ),
    "remove_blindness_deafness": SpellDefinition(
        spell_id="remove_blindness_deafness", name="Remove Blindness/Deafness",
        level=3, school="conjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.270",),
    ),
    "remove_curse": SpellDefinition(
        spell_id="remove_curse", name="Remove Curse", level=3, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.270",),
    ),
    "remove_disease": SpellDefinition(
        spell_id="remove_disease", name="Remove Disease", level=3, school="conjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.270",),
    ),
    "sleet_storm": SpellDefinition(
        spell_id="sleet_storm", name="Sleet Storm", level=3, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=400, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.280",),
    ),
    "stinking_cloud": SpellDefinition(
        spell_id="stinking_cloud", name="Stinking Cloud", level=3, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=10,
        spell_resistance=False,  # WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001: PHB p.284 SR: No
        rule_citations=("PHB p.284",),
    ),
    "summon_monster_iii": SpellDefinition(
        spell_id="summon_monster_iii", name="Summon Monster III", level=3, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "vampiric_touch": SpellDefinition(
        spell_id="vampiric_touch", name="Vampiric Touch", level=3, school="necromancy",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d6", has_verbal=True, has_somatic=True, rule_citations=("PHB p.298",),
    ),
    "wind_wall": SpellDefinition(
        spell_id="wind_wall", name="Wind Wall", level=3, school="evocation",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.302",),
    ),

    # -- Level 4 ---------------------------------------------------------------
    "animate_dead": SpellDefinition(
        spell_id="animate_dead", name="Animate Dead", level=4, school="necromancy",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=9999, rule_citations=("PHB p.199",),
    ),
    "black_tentacles": SpellDefinition(
        spell_id="black_tentacles", name="Black Tentacles", level=4, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.204",),
    ),
    "charm_monster": SpellDefinition(
        spell_id="charm_monster", name="Charm Monster", level=4, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=1440, rule_citations=("PHB p.209",),
    ),
    "confusion": SpellDefinition(
        spell_id="confusion", name="Confusion", level=4, school="enchantment",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.212",),
    ),
    "cure_critical_wounds": SpellDefinition(
        spell_id="cure_critical_wounds", name="Cure Critical Wounds", level=4, school="conjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.HEALING,
        healing_dice="4d8", save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        rule_citations=("PHB p.215",),
    ),
    "dimensional_anchor": SpellDefinition(
        spell_id="dimensional_anchor", name="Dimensional Anchor", level=4, school="abjuration",
        target_type=SpellTarget.RAY, range_ft=100, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.221",),
    ),
    "dimension_door": SpellDefinition(
        spell_id="dimension_door", name="Dimension Door", level=4, school="conjuration",
        target_type=SpellTarget.SELF, range_ft=400, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=False, rule_citations=("PHB p.221",),
    ),
    "enervation": SpellDefinition(
        spell_id="enervation", name="Enervation", level=4, school="necromancy",
        target_type=SpellTarget.RAY, range_ft=25, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.226",),
    ),
    "fear": SpellDefinition(
        spell_id="fear", name="Fear", level=4, school="necromancy",
        target_type=SpellTarget.AREA, range_ft=0, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.229",),
    ),
    "fire_shield": SpellDefinition(
        spell_id="fire_shield", name="Fire Shield", level=4, school="evocation",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.230",),
    ),
    "greater_invisibility": SpellDefinition(
        spell_id="greater_invisibility", name="Greater Invisibility", level=4, school="illusion",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.245",),
    ),
    "ice_storm": SpellDefinition(
        spell_id="ice_storm", name="Ice Storm", level=4, school="evocation",
        target_type=SpellTarget.AREA, range_ft=400, effect_type=SpellEffect.DAMAGE,
        damage_dice="3d6", has_verbal=True, has_somatic=True,
        duration_rounds=1, rule_citations=("PHB p.243",),
    ),
    "minor_creation": SpellDefinition(
        spell_id="minor_creation", name="Minor Creation", level=4, school="conjuration",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=False, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.253",),
    ),
    "polymorph": SpellDefinition(
        spell_id="polymorph", name="Polymorph", level=4, school="transmutation",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=100, rule_citations=("PHB p.263",),
    ),
    "rainbow_pattern": SpellDefinition(
        spell_id="rainbow_pattern", name="Rainbow Pattern", level=4, school="illusion",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=False, has_somatic=True,
        concentration=True, rule_citations=("PHB p.268",),
    ),
    "repel_vermin": SpellDefinition(
        spell_id="repel_vermin", name="Repel Vermin", level=4, school="abjuration",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=100, rule_citations=("PHB p.272",),
    ),
    "resilient_sphere": SpellDefinition(
        spell_id="resilient_sphere", name="Resilient Sphere", level=4, school="evocation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.REF, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.272",),
    ),
    "sending": SpellDefinition(
        spell_id="sending", name="Sending", level=4, school="evocation",
        target_type=SpellTarget.SINGLE, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.275",),
    ),
    "shout": SpellDefinition(
        spell_id="shout", name="Shout", level=4, school="evocation",
        target_type=SpellTarget.AREA, range_ft=0, effect_type=SpellEffect.DAMAGE,
        damage_dice="5d6", save_type=SaveType.FORT, save_effect=SaveEffect.HALF,
        has_verbal=True, has_somatic=False, rule_citations=("PHB p.278",),
    ),
    "solid_fog": SpellDefinition(
        spell_id="solid_fog", name="Solid Fog", level=4, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.281",),
    ),
    "stoneskin": SpellDefinition(
        spell_id="stoneskin", name="Stoneskin", level=4, school="abjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.284",),
    ),
    "summon_monster_iv": SpellDefinition(
        spell_id="summon_monster_iv", name="Summon Monster IV", level=4, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "wall_of_fire": SpellDefinition(
        spell_id="wall_of_fire", name="Wall of Fire", level=4, school="evocation",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DAMAGE,
        damage_dice="2d4", save_type=SaveType.REF, has_verbal=True, has_somatic=True,
        concentration=True, rule_citations=("PHB p.298",),
    ),
    "wall_of_ice": SpellDefinition(
        spell_id="wall_of_ice", name="Wall of Ice", level=4, school="evocation",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.REF, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.299",),
    ),

    # -- Level 5 ---------------------------------------------------------------
    "baleful_polymorph": SpellDefinition(
        spell_id="baleful_polymorph", name="Baleful Polymorph", level=5, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=9999, rule_citations=("PHB p.202",),
    ),
    "break_enchantment": SpellDefinition(
        spell_id="break_enchantment", name="Break Enchantment", level=5, school="abjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.205",),
    ),
    "cloudkill": SpellDefinition(
        spell_id="cloudkill", name="Cloudkill", level=5, school="conjuration",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d10", save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.210",),
    ),
    "dominate_person": SpellDefinition(
        spell_id="dominate_person", name="Dominate Person", level=5, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=1440, rule_citations=("PHB p.224",),
    ),
    "feeblemind": SpellDefinition(
        spell_id="feeblemind", name="Feeblemind", level=5, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=False, has_somatic=True,
        duration_rounds=9999, rule_citations=("PHB p.229",),
    ),
    "hold_monster": SpellDefinition(
        spell_id="hold_monster", name="Hold Monster", level=5, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.241",),
    ),
    "mind_fog": SpellDefinition(
        spell_id="mind_fog", name="Mind Fog", level=5, school="enchantment",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=10, rule_citations=("PHB p.254",),
    ),
    "passwall": SpellDefinition(
        spell_id="passwall", name="Passwall", level=5, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=600, rule_citations=("PHB p.260",),
    ),
    "plane_shift": SpellDefinition(
        spell_id="plane_shift", name="Plane Shift", level=5, school="conjuration",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.261",),
    ),
    "summon_monster_v": SpellDefinition(
        spell_id="summon_monster_v", name="Summon Monster V", level=5, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "telekinesis": SpellDefinition(
        spell_id="telekinesis", name="Telekinesis", level=5, school="transmutation",
        target_type=SpellTarget.SINGLE, range_ft=400, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        concentration=True, rule_citations=("PHB p.291",),
    ),
    "true_seeing": SpellDefinition(
        spell_id="true_seeing", name="True Seeing", level=5, school="divination",
        target_type=SpellTarget.TOUCH, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.296",),
    ),
    "waves_of_fatigue": SpellDefinition(
        spell_id="waves_of_fatigue", name="Waves of Fatigue", level=5, school="necromancy",
        target_type=SpellTarget.AREA, range_ft=0, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.300",),
    ),

    # -- Level 6 ---------------------------------------------------------------
    "antimagic_field": SpellDefinition(
        spell_id="antimagic_field", name="Antimagic Field", level=6, school="abjuration",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.200",),
    ),
    "chain_lightning": SpellDefinition(
        spell_id="chain_lightning", name="Chain Lightning", level=6, school="evocation",
        target_type=SpellTarget.SINGLE, range_ft=400, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d6", save_type=SaveType.REF, save_effect=SaveEffect.HALF,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.208",),
    ),
    "circle_of_death": SpellDefinition(
        spell_id="circle_of_death", name="Circle of Death", level=6, school="necromancy",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d4", save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        rule_citations=("PHB p.209",),
    ),
    "contingency": SpellDefinition(
        spell_id="contingency", name="Contingency", level=6, school="evocation",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=1440, rule_citations=("PHB p.213",),
    ),
    "disintegrate": SpellDefinition(
        spell_id="disintegrate", name="Disintegrate", level=6, school="transmutation",
        target_type=SpellTarget.RAY, range_ft=25, effect_type=SpellEffect.DAMAGE,
        damage_dice="2d6", save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        rule_citations=("PHB p.222",),
    ),
    "flesh_to_stone": SpellDefinition(
        spell_id="flesh_to_stone", name="Flesh to Stone", level=6, school="transmutation",
        target_type=SpellTarget.RAY, range_ft=100, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        duration_rounds=9999, rule_citations=("PHB p.232",),
    ),
    "globe_of_invulnerability": SpellDefinition(
        spell_id="globe_of_invulnerability", name="Globe of Invulnerability",
        level=6, school="abjuration",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, concentration=True, rule_citations=("PHB p.236",),
    ),
    "move_earth": SpellDefinition(
        spell_id="move_earth", name="Move Earth", level=6, school="transmutation",
        target_type=SpellTarget.AREA, range_ft=400, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.256",),
    ),
    "stone_to_flesh": SpellDefinition(
        spell_id="stone_to_flesh", name="Stone to Flesh", level=6, school="transmutation",
        target_type=SpellTarget.RAY, range_ft=100, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.FORT, has_verbal=True, has_somatic=True, rule_citations=("PHB p.284",),
    ),
    "summon_monster_vi": SpellDefinition(
        spell_id="summon_monster_vi", name="Summon Monster VI", level=6, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "greater_dispel_magic": SpellDefinition(
        spell_id="greater_dispel_magic", name="Greater Dispel Magic", level=6, school="abjuration",
        target_type=SpellTarget.SINGLE, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.223",),
    ),
    "undeath_to_death": SpellDefinition(
        spell_id="undeath_to_death", name="Undeath to Death", level=6, school="necromancy",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d6", save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        rule_citations=("PHB p.297",),
    ),

    # -- Level 7+ --------------------------------------------------------------
    "finger_of_death": SpellDefinition(
        spell_id="finger_of_death", name="Finger of Death", level=7, school="necromancy",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DAMAGE,
        damage_dice="3d6", save_type=SaveType.FORT, has_verbal=True, has_somatic=True,
        rule_citations=("PHB p.230",),
    ),
    "greater_teleport": SpellDefinition(
        spell_id="greater_teleport", name="Greater Teleport", level=7, school="conjuration",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=False, rule_citations=("PHB p.293",),
    ),
    "limited_wish": SpellDefinition(
        spell_id="limited_wish", name="Limited Wish", level=7, school="universal",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=False, rule_citations=("PHB p.248",),
    ),
    "power_word_blind": SpellDefinition(
        spell_id="power_word_blind", name="Power Word Blind", level=7, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=False, duration_rounds=10, rule_citations=("PHB p.263",),
    ),
    "prismatic_spray": SpellDefinition(
        spell_id="prismatic_spray", name="Prismatic Spray", level=7, school="evocation",
        target_type=SpellTarget.AREA, range_ft=0, effect_type=SpellEffect.DAMAGE,
        damage_dice="8d6", has_verbal=True, has_somatic=True, rule_citations=("PHB p.264",),
    ),
    "reverse_gravity": SpellDefinition(
        spell_id="reverse_gravity", name="Reverse Gravity", level=7, school="transmutation",
        target_type=SpellTarget.AREA, range_ft=100, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, concentration=True, rule_citations=("PHB p.272",),
    ),
    "spell_turning": SpellDefinition(
        spell_id="spell_turning", name="Spell Turning", level=7, school="abjuration",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.282",),
    ),
    "summon_monster_vii": SpellDefinition(
        spell_id="summon_monster_vii", name="Summon Monster VII", level=7, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "waves_of_exhaustion": SpellDefinition(
        spell_id="waves_of_exhaustion", name="Waves of Exhaustion", level=7, school="necromancy",
        target_type=SpellTarget.AREA, range_ft=0, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.300",),
    ),
    "antipathy": SpellDefinition(
        spell_id="antipathy", name="Antipathy", level=8, school="enchantment",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=1440, rule_citations=("PHB p.200",),
    ),
    "horrid_wilting": SpellDefinition(
        spell_id="horrid_wilting", name="Horrid Wilting", level=8, school="necromancy",
        target_type=SpellTarget.AREA, range_ft=400, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d6", save_type=SaveType.FORT, save_effect=SaveEffect.HALF,
        has_verbal=True, has_somatic=True, rule_citations=("PHB p.242",),
    ),
    "mind_blank": SpellDefinition(
        spell_id="mind_blank", name="Mind Blank", level=8, school="abjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=1440, rule_citations=("PHB p.254",),
    ),
    "polar_ray": SpellDefinition(
        spell_id="polar_ray", name="Polar Ray", level=8, school="evocation",
        target_type=SpellTarget.RAY, range_ft=25, effect_type=SpellEffect.DAMAGE,
        damage_dice="1d6", has_verbal=True, has_somatic=True, rule_citations=("PHB p.263",),
    ),
    "power_word_stun": SpellDefinition(
        spell_id="power_word_stun", name="Power Word Stun", level=8, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        has_verbal=True, has_somatic=False, duration_rounds=10, rule_citations=("PHB p.263",),
    ),
    "summon_monster_viii": SpellDefinition(
        spell_id="summon_monster_viii", name="Summon Monster VIII", level=8, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "sympathy": SpellDefinition(
        spell_id="sympathy", name="Sympathy", level=8, school="enchantment",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=1440, rule_citations=("PHB p.289",),
    ),
    "dominate_monster": SpellDefinition(
        spell_id="dominate_monster", name="Dominate Monster", level=9, school="enchantment",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
        duration_rounds=1440, rule_citations=("PHB p.224",),
    ),
    "foresight": SpellDefinition(
        spell_id="foresight", name="Foresight", level=9, school="divination",
        target_type=SpellTarget.SINGLE, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, duration_rounds=100, rule_citations=("PHB p.233",),
    ),
    "mages_disjunction": SpellDefinition(
        spell_id="mages_disjunction", name="Mage's Disjunction", level=9, school="abjuration",
        target_type=SpellTarget.AREA, range_ft=25, effect_type=SpellEffect.UTILITY,
        save_type=SaveType.WILL, has_verbal=True, has_somatic=True, rule_citations=("PHB p.249",),
    ),
    "shapechange": SpellDefinition(
        spell_id="shapechange", name="Shapechange", level=9, school="transmutation",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.BUFF,
        has_verbal=True, has_somatic=True, concentration=True, rule_citations=("PHB p.278",),
    ),
    "summon_monster_ix": SpellDefinition(
        spell_id="summon_monster_ix", name="Summon Monster IX", level=9, school="conjuration",
        target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=True, duration_rounds=10, rule_citations=("PHB p.285",),
    ),
    "wish": SpellDefinition(
        spell_id="wish", name="Wish", level=9, school="universal",
        target_type=SpellTarget.SELF, range_ft=0, effect_type=SpellEffect.UTILITY,
        has_verbal=True, has_somatic=False, rule_citations=("PHB p.302",),
    ),

}

# ---------------------------------------------------------------------------
# OSS-INGESTION-SPRINT-001 — PCGen stub extensions (CC0 / OGL)
# 518 novel spells not previously in registry, heuristically-typed stubs.
# Existing entries above remain unmodified with full PHB fidelity.
# ---------------------------------------------------------------------------
from aidm.data.spell_definitions_ext import SPELL_REGISTRY_EXT  # noqa: E402
SPELL_REGISTRY.update(SPELL_REGISTRY_EXT)

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
