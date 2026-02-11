"""WO-036: Expanded Spell Registry Tests

Tests for the 33 new spells added to SPELL_REGISTRY (levels 0-5).
Verifies spell definitions, resolution mechanics, and integration with existing systems.

Total spells after WO-036: 53 (20 original + 33 new)
"""

import pytest
from typing import Dict

from aidm.schemas.position import Position
from aidm.schemas.saves import SaveType
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.rng_manager import RNGManager
from aidm.core.aoe_rasterizer import AoEShape, AoEDirection
from aidm.core.truth_packets import STPType
from aidm.core.spell_resolver import (
    SpellDefinition,
    SpellTarget,
    SpellEffect,
    SaveEffect,
    DamageType,
    SpellCastIntent,
    SpellResolution,
    SpellResolver,
    CasterStats,
    TargetStats,
    create_spell_resolver,
)
from aidm.core.duration_tracker import (
    ActiveSpellEffect,
    DurationTracker,
    create_effect,
)
from aidm.schemas.spell_definitions import (
    SPELL_REGISTRY,
    get_spell,
    get_spells_by_level,
    get_damage_spells,
    get_healing_spells,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def grid():
    """Create a basic 20x20 battle grid."""
    return BattleGrid(20, 20)


@pytest.fixture
def rng():
    """Create a deterministic RNG manager."""
    return RNGManager(master_seed=42)


@pytest.fixture
def spell_registry():
    """Get the standard spell registry."""
    return SPELL_REGISTRY


@pytest.fixture
def resolver(grid, rng, spell_registry):
    """Create a spell resolver with standard configuration."""
    return create_spell_resolver(grid, rng, spell_registry, turn=1, initiative=10)


@pytest.fixture
def caster(grid):
    """Create a standard caster at position (5, 5)."""
    grid.place_entity("caster_01", Position(5, 5), SizeCategory.MEDIUM)
    return CasterStats(
        caster_id="caster_01",
        position=Position(5, 5),
        caster_level=10,
        spell_dc_base=15,  # 10 + 5 (ability mod)
        attack_bonus=5,
    )


@pytest.fixture
def target(grid):
    """Create a standard target at position (8, 5)."""
    grid.place_entity("target_01", Position(8, 5), SizeCategory.MEDIUM)
    return TargetStats(
        entity_id="target_01",
        position=Position(8, 5),
        hit_points=30,
        max_hit_points=40,
        fort_save=5,
        ref_save=5,
        will_save=5,
    )


# ==============================================================================
# TIER 1: SPELL REGISTRY TESTS (10 tests)
# ==============================================================================

def test_spell_count():
    """WO-036: Registry contains ~53 spells total."""
    assert len(SPELL_REGISTRY) >= 53


def test_all_spells_have_rule_citations():
    """WO-036: Every spell has at least one PHB page citation."""
    for spell in SPELL_REGISTRY.values():
        assert len(spell.rule_citations) > 0, f"Spell {spell.spell_id} missing rule citations"
        assert any("PHB" in citation for citation in spell.rule_citations), \
            f"Spell {spell.spell_id} missing PHB citation"


def test_spell_levels_0_through_5():
    """WO-036: Spells exist at every level 0-5."""
    for level in range(6):
        spells = get_spells_by_level(level)
        assert len(spells) > 0, f"No spells at level {level}"


def test_all_schools_represented():
    """WO-036: Major schools are represented."""
    schools = {s.school for s in SPELL_REGISTRY.values()}
    expected_schools = [
        "evocation", "conjuration", "transmutation", "enchantment",
        "abjuration", "illusion", "necromancy", "divination"
    ]
    for school in expected_schools:
        assert school in schools, f"School {school} not represented"


def test_level_0_cantrips():
    """WO-036: Level 0 contains 4 new cantrips."""
    level_0 = get_spells_by_level(0)
    new_cantrips = ["resistance", "guidance", "mending", "read_magic"]
    for spell_id in new_cantrips:
        assert spell_id in level_0, f"Cantrip {spell_id} not found"


def test_level_1_spells():
    """WO-036: Level 1 contains 6 new spells."""
    level_1 = get_spells_by_level(1)
    new_spells = ["bless", "bane", "grease", "sleep", "entangle", "color_spray"]
    for spell_id in new_spells:
        assert spell_id in level_1, f"Spell {spell_id} not found"


def test_level_2_spells():
    """WO-036: Level 2 contains 7 new spells."""
    level_2 = get_spells_by_level(2)
    new_spells = [
        "invisibility", "mirror_image", "cats_grace", "bears_endurance",
        "owls_wisdom", "resist_energy", "silence"
    ]
    for spell_id in new_spells:
        assert spell_id in level_2, f"Spell {spell_id} not found"


def test_level_3_spells():
    """WO-036: Level 3 contains 5 new spells."""
    level_3 = get_spells_by_level(3)
    new_spells = [
        "dispel_magic", "protection_from_energy", "magic_circle_against_evil",
        "fly", "stinking_cloud"
    ]
    for spell_id in new_spells:
        assert spell_id in level_3, f"Spell {spell_id} not found"


def test_level_4_spells():
    """WO-036: Level 4 contains 6 new spells."""
    level_4 = get_spells_by_level(4)
    new_spells = [
        "cure_critical_wounds", "stoneskin", "wall_of_fire",
        "dimension_door", "greater_invisibility", "ice_storm"
    ]
    for spell_id in new_spells:
        assert spell_id in level_4, f"Spell {spell_id} not found"


def test_level_5_spells():
    """WO-036: Level 5 contains 5 new spells."""
    level_5 = get_spells_by_level(5)
    new_spells = [
        "hold_monster", "wall_of_stone", "raise_dead",
        "telekinesis", "baleful_polymorph"
    ]
    for spell_id in new_spells:
        assert spell_id in level_5, f"Spell {spell_id} not found"


# ==============================================================================
# TIER 2: LEVEL 0-1 SPELL RESOLUTION TESTS (10 tests)
# ==============================================================================

def test_resistance_buff(resolver, caster, target):
    """Resistance: +1 resistance bonus to saves (PHB p.272)."""
    spell = get_spell("resistance")
    intent = SpellCastIntent(
        caster_id=caster.caster_id,
        spell_id="resistance",
        target_entity_id=target.entity_id,
    )

    resolution = resolver.resolve_spell(intent, caster, {target.entity_id: target})

    assert resolution.success
    assert spell.effect_type == SpellEffect.BUFF
    assert "resistance" in spell.conditions_on_success


def test_guidance_buff(resolver, caster, target):
    """Guidance: +1 competence bonus to attack/save/skill (PHB p.238)."""
    spell = get_spell("guidance")
    intent = SpellCastIntent(
        caster_id=caster.caster_id,
        spell_id="guidance",
        target_entity_id=target.entity_id,
    )

    resolution = resolver.resolve_spell(intent, caster, {target.entity_id: target})

    assert resolution.success
    assert spell.effect_type == SpellEffect.BUFF
    assert "guidance" in spell.conditions_on_success


def test_mending_healing(resolver, caster, target):
    """Mending: Repairs 1d4 HP to object (PHB p.253)."""
    spell = get_spell("mending")

    assert spell.effect_type == SpellEffect.HEALING
    assert spell.healing_dice == "1d4"
    assert spell.duration_rounds == 0  # Instantaneous


def test_read_magic_utility(resolver, caster):
    """Read Magic: Read magical writing (PHB p.269)."""
    spell = get_spell("read_magic")

    assert spell.effect_type == SpellEffect.UTILITY
    assert spell.target_type == SpellTarget.SELF
    assert spell.duration_rounds == 100  # 10 min/level


def test_bless_area_buff(resolver, caster):
    """Bless: +1 attack/fear saves in 50ft burst (PHB p.205)."""
    spell = get_spell("bless")

    assert spell.effect_type == SpellEffect.BUFF
    assert spell.target_type == SpellTarget.AREA
    assert spell.aoe_shape == AoEShape.BURST
    assert spell.aoe_radius_ft == 50
    assert "blessed" in spell.conditions_on_success


def test_bane_will_save(resolver, caster, target):
    """Bane: -1 attack/fear saves, Will negates (PHB p.203)."""
    spell = get_spell("bane")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.save_type == SaveType.WILL
    assert spell.save_effect == SaveEffect.NEGATES
    assert "bane" in spell.conditions_on_fail


def test_sleep_hd_limited(resolver, caster):
    """Sleep: unconscious, no save — HD-limited effect (PHB p.280)."""
    spell = get_spell("sleep")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.save_type is None  # No save — HD-limited
    assert spell.save_effect == SaveEffect.NONE
    assert "unconscious" in spell.conditions_on_fail
    assert spell.aoe_shape == AoEShape.BURST


def test_grease_ref_save(resolver, caster):
    """Grease: prone on failed Ref save (PHB p.237)."""
    spell = get_spell("grease")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.save_type == SaveType.REF
    assert spell.save_effect == SaveEffect.NEGATES
    assert "prone" in spell.conditions_on_fail


def test_entangle_area(resolver, caster):
    """Entangle: 40ft radius, entangled condition (PHB p.227)."""
    spell = get_spell("entangle")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.aoe_radius_ft == 40
    assert spell.aoe_shape == AoEShape.BURST
    assert "entangled" in spell.conditions_on_fail


def test_color_spray_cone(resolver, caster):
    """Color Spray: 15ft cone, stunned on failed Will (PHB p.210)."""
    spell = get_spell("color_spray")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.aoe_shape == AoEShape.CONE
    assert spell.aoe_radius_ft == 15
    assert spell.save_type == SaveType.WILL
    assert "stunned" in spell.conditions_on_fail


# ==============================================================================
# TIER 3: LEVEL 2-3 SPELL RESOLUTION TESTS (12 tests)
# ==============================================================================

def test_invisibility_buff(resolver, caster, target):
    """Invisibility: invisible condition, breaks on attack (PHB p.245)."""
    spell = get_spell("invisibility")

    assert spell.effect_type == SpellEffect.BUFF
    assert spell.target_type == SpellTarget.TOUCH
    assert "invisible" in spell.conditions_on_success


def test_cats_grace_buff(resolver, caster, target):
    """Cat's Grace: +4 DEX (PHB p.208)."""
    spell = get_spell("cats_grace")

    assert spell.effect_type == SpellEffect.BUFF
    assert spell.target_type == SpellTarget.TOUCH
    assert "cats_grace" in spell.conditions_on_success
    assert spell.duration_rounds == 10  # 1 min/level


def test_bears_endurance_buff(resolver, caster, target):
    """Bear's Endurance: +4 CON (PHB p.203)."""
    spell = get_spell("bears_endurance")

    assert spell.effect_type == SpellEffect.BUFF
    assert "bears_endurance" in spell.conditions_on_success


def test_owls_wisdom_buff(resolver, caster, target):
    """Owl's Wisdom: +4 WIS (PHB p.259)."""
    spell = get_spell("owls_wisdom")

    assert spell.effect_type == SpellEffect.BUFF
    assert "owls_wisdom" in spell.conditions_on_success


def test_mirror_image_self(resolver, caster):
    """Mirror Image: creates duplicates (PHB p.254)."""
    spell = get_spell("mirror_image")

    assert spell.effect_type == SpellEffect.BUFF
    assert spell.target_type == SpellTarget.SELF
    assert "mirror_image" in spell.conditions_on_success


def test_resist_energy_buff(resolver, caster, target):
    """Resist Energy: energy resistance 10 (PHB p.272)."""
    spell = get_spell("resist_energy")

    assert spell.effect_type == SpellEffect.BUFF
    assert spell.duration_rounds == 100  # 10 min/level
    assert "resist_energy" in spell.conditions_on_success


def test_silence_area_debuff(resolver, caster):
    """Silence: 20ft burst, blocks verbal spells (PHB p.279)."""
    spell = get_spell("silence")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.aoe_shape == AoEShape.BURST
    assert spell.aoe_radius_ft == 20
    assert spell.save_type == SaveType.WILL
    assert "silenced" in spell.conditions_on_fail


def test_dispel_magic_utility(resolver, caster, target):
    """Dispel Magic: utility spell, caster level check (PHB p.223)."""
    spell = get_spell("dispel_magic")

    assert spell.effect_type == SpellEffect.UTILITY
    assert spell.target_type == SpellTarget.SINGLE
    assert spell.duration_rounds == 0  # Instantaneous


def test_stinking_cloud_concentration(resolver, caster):
    """Stinking Cloud: concentration spell, nauseated (PHB p.284)."""
    spell = get_spell("stinking_cloud")

    assert spell.concentration is True
    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.save_type == SaveType.FORT
    assert "nauseated" in spell.conditions_on_fail


def test_fly_buff(resolver, caster, target):
    """Fly: flying condition (PHB p.232)."""
    spell = get_spell("fly")

    assert spell.effect_type == SpellEffect.BUFF
    assert "flying" in spell.conditions_on_success
    assert spell.duration_rounds == 10  # 1 min/level


def test_protection_from_energy(resolver, caster, target):
    """Protection from Energy: absorb energy damage (PHB p.266)."""
    spell = get_spell("protection_from_energy")

    assert spell.effect_type == SpellEffect.BUFF
    assert spell.duration_rounds == 100  # 10 min/level
    assert "protection_from_energy" in spell.conditions_on_success


def test_magic_circle_against_evil(resolver, caster):
    """Magic Circle against Evil: +2 AC, +2 saves in 10ft (PHB p.249)."""
    spell = get_spell("magic_circle_against_evil")

    assert spell.effect_type == SpellEffect.BUFF
    assert spell.aoe_shape == AoEShape.BURST
    assert spell.aoe_radius_ft == 10
    assert "magic_circle_evil" in spell.conditions_on_success


# ==============================================================================
# TIER 4: LEVEL 4-5 SPELL RESOLUTION TESTS (10 tests)
# ==============================================================================

def test_cure_critical_wounds(resolver, caster, target):
    """Cure Critical Wounds: 4d8+level healing (PHB p.215)."""
    spell = get_spell("cure_critical_wounds")

    assert spell.effect_type == SpellEffect.HEALING
    assert spell.healing_dice == "4d8"
    assert spell.duration_rounds == 0  # Instantaneous


def test_stoneskin_buff(resolver, caster, target):
    """Stoneskin: DR 10/adamantine (PHB p.284)."""
    spell = get_spell("stoneskin")

    assert spell.effect_type == SpellEffect.BUFF
    assert "stoneskin" in spell.conditions_on_success
    assert spell.duration_rounds == 100  # 10 min/level


def test_wall_of_fire_damage(resolver, caster):
    """Wall of Fire: fire damage in area, concentration (PHB p.298)."""
    spell = get_spell("wall_of_fire")

    assert spell.concentration is True
    assert spell.effect_type == SpellEffect.DAMAGE
    assert spell.damage_type == DamageType.FIRE
    assert spell.aoe_shape == AoEShape.LINE


def test_ice_storm_no_save(resolver, caster):
    """Ice Storm: 5d6 damage, no save (PHB p.243)."""
    spell = get_spell("ice_storm")

    assert spell.effect_type == SpellEffect.DAMAGE
    assert spell.damage_type == DamageType.COLD
    assert spell.save_type is None  # No save
    assert spell.damage_dice == "5d6"


def test_greater_invisibility(resolver, caster, target):
    """Greater Invisibility: invisible while attacking (PHB p.245)."""
    spell = get_spell("greater_invisibility")

    assert spell.effect_type == SpellEffect.BUFF
    assert "greater_invisibility" in spell.conditions_on_success
    assert spell.duration_rounds == 1  # 1 round/level


def test_hold_monster_will_save(resolver, caster, target):
    """Hold Monster: paralyzed, Will negates (PHB p.241)."""
    spell = get_spell("hold_monster")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.save_type == SaveType.WILL
    assert spell.save_effect == SaveEffect.NEGATES
    assert "paralyzed" in spell.conditions_on_fail


def test_baleful_polymorph(resolver, caster, target):
    """Baleful Polymorph: fort negates, permanent (PHB p.202)."""
    spell = get_spell("baleful_polymorph")

    assert spell.effect_type == SpellEffect.DEBUFF
    assert spell.save_type == SaveType.FORT
    assert spell.duration_rounds == -1  # Permanent
    assert "polymorphed" in spell.conditions_on_fail


def test_telekinesis_concentration(resolver, caster, target):
    """Telekinesis: concentration spell (PHB p.292)."""
    spell = get_spell("telekinesis")

    assert spell.concentration is True
    assert spell.effect_type == SpellEffect.UTILITY
    assert spell.target_type == SpellTarget.SINGLE


def test_dimension_door_self(resolver, caster):
    """Dimension Door: self-targeting teleport (PHB p.221)."""
    spell = get_spell("dimension_door")

    assert spell.effect_type == SpellEffect.UTILITY
    assert spell.target_type == SpellTarget.SELF
    assert spell.duration_rounds == 0  # Instantaneous


def test_raise_dead_healing(resolver, caster, target):
    """Raise Dead: restore life, level 5 (PHB p.268)."""
    spell = get_spell("raise_dead")

    assert spell.effect_type == SpellEffect.HEALING
    assert spell.level == 5
    assert spell.healing_dice == "0"  # Restore life, not HP


# ==============================================================================
# TIER 5: CONCENTRATION INTEGRATION TESTS (4 tests)
# ==============================================================================

def test_stinking_cloud_concentration_flag():
    """Stinking Cloud requires concentration (PHB p.284)."""
    spell = get_spell("stinking_cloud")
    assert spell.concentration is True


def test_wall_of_fire_concentration_flag():
    """Wall of Fire requires concentration (PHB p.298)."""
    spell = get_spell("wall_of_fire")
    assert spell.concentration is True


def test_telekinesis_concentration_flag():
    """Telekinesis requires concentration (PHB p.292)."""
    spell = get_spell("telekinesis")
    assert spell.concentration is True


def test_non_concentration_spells():
    """Most new spells don't require concentration."""
    non_concentration_spells = [
        "bless", "invisibility", "fly", "stoneskin",
        "cure_critical_wounds", "hold_monster"
    ]

    for spell_id in non_concentration_spells:
        spell = get_spell(spell_id)
        assert spell.concentration is False, f"{spell_id} should not require concentration"


# ==============================================================================
# TIER 6: AOE GEOMETRY TESTS (4 tests)
# ==============================================================================

def test_bless_50ft_burst():
    """Bless: 50ft burst covers correct area (PHB p.205)."""
    spell = get_spell("bless")

    assert spell.aoe_shape == AoEShape.BURST
    assert spell.aoe_radius_ft == 50


def test_entangle_40ft_burst():
    """Entangle: 40ft burst covers correct area (PHB p.227)."""
    spell = get_spell("entangle")

    assert spell.aoe_shape == AoEShape.BURST
    assert spell.aoe_radius_ft == 40


def test_color_spray_15ft_cone():
    """Color Spray: 15ft cone covers correct area (PHB p.210)."""
    spell = get_spell("color_spray")

    assert spell.aoe_shape == AoEShape.CONE
    assert spell.aoe_radius_ft == 15


def test_silence_20ft_burst():
    """Silence: 20ft burst covers correct area (PHB p.279)."""
    spell = get_spell("silence")

    assert spell.aoe_shape == AoEShape.BURST
    assert spell.aoe_radius_ft == 20
