"""Tests for Spellcasting Resolution Core.

WO-014: Spellcasting Resolution Core
Tests the full spell resolution cycle including targeting, saves, damage, and STPs.
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
def grid_with_wall():
    """Create a grid with a solid wall blocking LOS."""
    from aidm.schemas.geometry import PropertyMask, PropertyFlag
    grid = BattleGrid(20, 20)
    # Create a wall at (10, 10)
    cell = grid.get_cell(Position(10, 10))
    cell.cell_mask = PropertyMask().set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
    return grid


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
        caster_level=8,
        spell_dc_base=14,  # 10 + 4 (INT mod)
        attack_bonus=4,
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
        ref_save=2,
        will_save=3,
    )


@pytest.fixture
def targets_dict(target):
    """Create a targets dictionary with the standard target."""
    return {target.entity_id: target}


@pytest.fixture
def multiple_targets(grid):
    """Create multiple targets for area spells."""
    positions = [
        Position(8, 5),  # target_01
        Position(9, 5),  # target_02
        Position(8, 6),  # target_03
        Position(10, 5), # target_04 - further away
    ]
    targets = {}
    for i, pos in enumerate(positions):
        entity_id = f"target_{i+1:02d}"
        grid.place_entity(entity_id, pos, SizeCategory.MEDIUM)
        targets[entity_id] = TargetStats(
            entity_id=entity_id,
            position=pos,
            hit_points=30,
            max_hit_points=40,
            fort_save=5,
            ref_save=2 + i,  # Varying saves
            will_save=3,
        )
    return targets


# ==============================================================================
# TESTS: SpellDefinition Schema
# ==============================================================================

class TestSpellDefinitionSchema:
    """Tests for SpellDefinition dataclass."""

    def test_create_damage_spell(self):
        """Create a damage spell definition."""
        spell = SpellDefinition(
            spell_id="test_spell",
            name="Test Spell",
            level=3,
            school="evocation",
            target_type=SpellTarget.SINGLE,
            range_ft=100,
            effect_type=SpellEffect.DAMAGE,
            damage_dice="6d6",
            damage_type=DamageType.FIRE,
            save_type=SaveType.REF,
            save_effect=SaveEffect.HALF,
        )
        assert spell.spell_id == "test_spell"
        assert spell.level == 3
        assert spell.damage_dice == "6d6"
        assert spell.save_type == SaveType.REF
        assert spell.save_effect == SaveEffect.HALF

    def test_create_healing_spell(self):
        """Create a healing spell definition."""
        spell = SpellDefinition(
            spell_id="test_heal",
            name="Test Heal",
            level=1,
            school="conjuration",
            target_type=SpellTarget.TOUCH,
            range_ft=0,
            effect_type=SpellEffect.HEALING,
            healing_dice="1d8",
        )
        assert spell.healing_dice == "1d8"
        assert spell.effect_type == SpellEffect.HEALING

    def test_create_buff_spell(self):
        """Create a buff spell definition."""
        spell = SpellDefinition(
            spell_id="test_buff",
            name="Test Buff",
            level=2,
            school="transmutation",
            target_type=SpellTarget.TOUCH,
            range_ft=0,
            effect_type=SpellEffect.BUFF,
            duration_rounds=10,
            conditions_on_success=("test_buff",),
        )
        assert spell.duration_rounds == 10
        assert "test_buff" in spell.conditions_on_success

    def test_spell_definition_is_frozen(self):
        """SpellDefinition is immutable."""
        spell = SpellDefinition(
            spell_id="frozen_test",
            name="Frozen",
            level=1,
            school="evocation",
            target_type=SpellTarget.SINGLE,
            range_ft=30,
        )
        with pytest.raises(AttributeError):
            spell.level = 5

    def test_spell_to_dict(self):
        """SpellDefinition serializes to dict."""
        spell = SpellDefinition(
            spell_id="serialize_test",
            name="Serialize",
            level=2,
            school="abjuration",
            target_type=SpellTarget.SELF,
            range_ft=0,
        )
        d = spell.to_dict()
        assert d["spell_id"] == "serialize_test"
        assert d["level"] == 2
        assert d["target_type"] == "self"


# ==============================================================================
# TESTS: SpellCastIntent Schema
# ==============================================================================

class TestSpellCastIntentSchema:
    """Tests for SpellCastIntent dataclass."""

    def test_create_targeted_intent(self):
        """Create an intent targeting an entity."""
        intent = SpellCastIntent(
            caster_id="caster_01",
            spell_id="magic_missile",
            target_entity_id="target_01",
        )
        assert intent.caster_id == "caster_01"
        assert intent.spell_id == "magic_missile"
        assert intent.target_entity_id == "target_01"
        assert intent.target_position is None

    def test_create_area_intent(self):
        """Create an intent targeting a position."""
        intent = SpellCastIntent(
            caster_id="caster_01",
            spell_id="fireball",
            target_position=Position(10, 10),
        )
        assert intent.target_position == Position(10, 10)
        assert intent.target_entity_id is None

    def test_create_cone_intent(self):
        """Create an intent for a cone spell with direction."""
        intent = SpellCastIntent(
            caster_id="caster_01",
            spell_id="burning_hands",
            aoe_direction=AoEDirection.E,
        )
        assert intent.aoe_direction == AoEDirection.E

    def test_intent_is_frozen(self):
        """SpellCastIntent is immutable."""
        intent = SpellCastIntent(
            caster_id="caster_01",
            spell_id="fireball",
        )
        with pytest.raises(AttributeError):
            intent.spell_id = "other_spell"


# ==============================================================================
# TESTS: Spell Validation
# ==============================================================================

class TestSpellValidation:
    """Test spell cast validation."""

    def test_valid_single_target_spell(self, resolver, caster, target, targets_dict):
        """Valid single-target spell passes validation."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="magic_missile",
            target_entity_id=target.entity_id,
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is True
        assert error is None

    def test_unknown_spell_fails(self, resolver, caster):
        """Unknown spell fails validation."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="nonexistent_spell",
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is False
        assert "Unknown spell" in error

    def test_out_of_range_fails(self, resolver, caster, grid):
        """Target out of range fails validation."""
        # Place target far away
        grid.place_entity("far_target", Position(19, 19), SizeCategory.MEDIUM)
        caster.position = Position(0, 0)

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="scorching_ray",  # 25ft range
            target_entity_id="far_target",
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is False
        assert "out of range" in error.lower()

    def test_no_los_fails(self, grid_with_wall, rng, spell_registry, caster):
        """No line of sight fails validation."""
        resolver = create_spell_resolver(grid_with_wall, rng, spell_registry)

        # Place caster and target on opposite sides of wall
        grid_with_wall.place_entity(caster.caster_id, Position(5, 10), SizeCategory.MEDIUM)
        grid_with_wall.place_entity("blocked_target", Position(15, 10), SizeCategory.MEDIUM)
        caster.position = Position(5, 10)

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="magic_missile",
            target_entity_id="blocked_target",
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is False
        assert "line of sight" in error.lower()

    def test_self_spell_always_valid(self, resolver, caster):
        """Self-targeting spells are always valid."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="shield",
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is True

    def test_cone_requires_direction(self, resolver, caster):
        """Cone spells require a direction."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="burning_hands",
            # Missing aoe_direction
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is False
        assert "direction" in error.lower()

    def test_cone_with_direction_valid(self, resolver, caster):
        """Cone spells with direction are valid."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="burning_hands",
            aoe_direction=AoEDirection.E,
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is True


# ==============================================================================
# TESTS: Area Spell Resolution
# ==============================================================================

class TestAreaSpellResolution:
    """Test AoE spell mechanics."""

    def test_fireball_20ft_burst(self, resolver, caster, multiple_targets):
        """Fireball affects all in 20ft burst."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="fireball",
            target_position=Position(8, 5),  # Center on targets
        )
        result = resolver.resolve_spell(intent, caster, multiple_targets)

        assert result.success is True
        assert len(result.affected_entities) >= 2  # At least some targets hit

    def test_fireball_reflex_save_half(self, grid, spell_registry):
        """Fireball allows Reflex save for half damage."""
        # Use fixed RNG for predictable results
        rng = RNGManager(master_seed=12345)
        resolver = create_spell_resolver(grid, rng, spell_registry)

        grid.place_entity("caster_01", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("target_01", Position(4, 0), SizeCategory.MEDIUM)

        caster = CasterStats(
            caster_id="caster_01",
            position=Position(0, 0),
            caster_level=8,
            spell_dc_base=14,
        )
        target = TargetStats(
            entity_id="target_01",
            position=Position(4, 0),
            hit_points=50,
            max_hit_points=50,
            ref_save=20,  # Very high, will save
        )

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="fireball",
            target_position=Position(4, 0),
        )
        result = resolver.resolve_spell(intent, caster, {"target_01": target})

        # High reflex save should succeed
        assert result.saves_made.get("target_01", False) is True

    def test_cone_spell_direction(self, resolver, caster, grid):
        """Cone spells respect direction."""
        # Place target to the east
        grid.place_entity("east_target", Position(8, 5), SizeCategory.MEDIUM)
        # Place target to the west (shouldn't be hit by east cone)
        grid.place_entity("west_target", Position(2, 5), SizeCategory.MEDIUM)

        targets = {
            "east_target": TargetStats(
                entity_id="east_target",
                position=Position(8, 5),
                hit_points=30, max_hit_points=40,
                ref_save=2,
            ),
            "west_target": TargetStats(
                entity_id="west_target",
                position=Position(2, 5),
                hit_points=30, max_hit_points=40,
                ref_save=2,
            ),
        }

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="burning_hands",
            aoe_direction=AoEDirection.E,  # East
        )
        result = resolver.resolve_spell(intent, caster, targets)

        # East target should be affected, west target should not
        assert "east_target" in result.affected_entities
        assert "west_target" not in result.affected_entities

    def test_line_spell_all_in_path(self, resolver, caster, grid):
        """Line spells affect all in path."""
        # Place targets in a line east of caster
        grid.place_entity("line_target_1", Position(6, 5), SizeCategory.MEDIUM)
        grid.place_entity("line_target_2", Position(10, 5), SizeCategory.MEDIUM)

        targets = {
            "line_target_1": TargetStats(
                entity_id="line_target_1",
                position=Position(6, 5),
                hit_points=30, max_hit_points=40,
                ref_save=2,
            ),
            "line_target_2": TargetStats(
                entity_id="line_target_2",
                position=Position(10, 5),
                hit_points=30, max_hit_points=40,
                ref_save=2,
            ),
        }

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="lightning_bolt",
            aoe_direction=AoEDirection.E,
        )
        result = resolver.resolve_spell(intent, caster, targets)

        # Both targets in the line should be affected
        assert result.success is True


# ==============================================================================
# TESTS: Single Target Spells
# ==============================================================================

class TestSingleTargetSpells:
    """Test single-target mechanics."""

    def test_magic_missile_auto_hit(self, resolver, caster, target, targets_dict):
        """Magic missile automatically hits (no attack roll)."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="magic_missile",
            target_entity_id=target.entity_id,
        )
        result = resolver.resolve_spell(intent, caster, targets_dict)

        assert result.success is True
        assert target.entity_id in result.affected_entities
        assert target.entity_id in result.damage_dealt
        # Magic missile always deals damage (no save)
        assert result.damage_dealt[target.entity_id] > 0

    def test_hold_person_will_save(self, resolver, caster, target, targets_dict):
        """Hold person requires Will save to negate."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="hold_person",
            target_entity_id=target.entity_id,
        )
        result = resolver.resolve_spell(intent, caster, targets_dict)

        assert result.success is True
        assert target.entity_id in result.saves_made
        # Either saved (no condition) or failed (paralyzed)
        if not result.saves_made[target.entity_id]:
            assert (target.entity_id, "paralyzed") in result.conditions_applied

    def test_ray_requires_touch_attack(self, spell_registry):
        """Scorching ray requires attack roll."""
        spell = spell_registry["scorching_ray"]
        assert spell.requires_attack_roll is True
        assert spell.target_type == SpellTarget.RAY


# ==============================================================================
# TESTS: Saving Throws
# ==============================================================================

class TestSavingThrows:
    """Test save mechanics."""

    def test_reflex_save_half_damage(self, grid, spell_registry):
        """Successful Reflex save halves damage."""
        # Use seeded RNG for reproducibility
        rng = RNGManager(master_seed=99999)
        resolver = create_spell_resolver(grid, rng, spell_registry)

        grid.place_entity("caster", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("saver", Position(4, 0), SizeCategory.MEDIUM)

        caster = CasterStats(
            caster_id="caster",
            position=Position(0, 0),
            caster_level=8,
            spell_dc_base=10,  # Low DC
        )
        target = TargetStats(
            entity_id="saver",
            position=Position(4, 0),
            hit_points=50,
            max_hit_points=50,
            ref_save=30,  # Very high save, guaranteed success
        )

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="fireball",
            target_position=Position(4, 0),
        )
        result = resolver.resolve_spell(intent, caster, {"saver": target})

        # Should have saved
        assert result.saves_made.get("saver", False) is True

    def test_will_save_negates(self, resolver, caster, target, targets_dict):
        """Will save negates effect entirely."""
        # Modify target to have high Will save
        target.will_save = 30  # Guaranteed save

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="hold_person",
            target_entity_id=target.entity_id,
        )
        result = resolver.resolve_spell(intent, caster, targets_dict)

        # Should have saved
        assert result.saves_made.get(target.entity_id, False) is True
        # No paralyzed condition
        assert (target.entity_id, "paralyzed") not in result.conditions_applied


# ==============================================================================
# TESTS: Duration Tracking
# ==============================================================================

class TestDurationTracking:
    """Test spell duration mechanics."""

    def test_instantaneous_no_tracking(self):
        """Instantaneous spells don't need tracking."""
        spell = SPELL_REGISTRY["fireball"]
        assert spell.duration_rounds == 0  # Instantaneous

    def test_rounds_duration_decrements(self):
        """Duration decrements each round."""
        tracker = DurationTracker()
        effect = create_effect(
            spell_id="bulls_strength",
            spell_name="Bull's Strength",
            caster_id="caster_01",
            target_id="target_01",
            duration_rounds=5,
        )
        tracker.add_effect(effect)

        # Tick 3 rounds
        for _ in range(3):
            tracker.tick_round()

        effects = tracker.get_effects_on("target_01")
        assert len(effects) == 1
        assert effects[0].rounds_remaining == 2

    def test_concentration_broken_removes_effect(self):
        """Breaking concentration removes the effect."""
        tracker = DurationTracker()
        effect = create_effect(
            spell_id="detect_magic",
            spell_name="Detect Magic",
            caster_id="caster_01",
            target_id="caster_01",
            duration_rounds=10,
            concentration=True,
        )
        tracker.add_effect(effect)

        assert len(tracker.get_effects_on("caster_01")) == 1

        # Break concentration
        removed = tracker.break_concentration("caster_01")

        assert len(removed) == 1
        assert len(tracker.get_effects_on("caster_01")) == 0

    def test_multiple_effects_same_target(self):
        """Multiple effects can be on same target."""
        tracker = DurationTracker()

        effect1 = create_effect(
            spell_id="bulls_strength",
            spell_name="Bull's Strength",
            caster_id="caster_01",
            target_id="target_01",
            duration_rounds=10,
        )
        effect2 = create_effect(
            spell_id="mage_armor",
            spell_name="Mage Armor",
            caster_id="caster_02",
            target_id="target_01",
            duration_rounds=60,
        )

        tracker.add_effect(effect1)
        tracker.add_effect(effect2)

        effects = tracker.get_effects_on("target_01")
        assert len(effects) == 2

    def test_effect_expiration(self):
        """Effects expire when duration reaches 0."""
        tracker = DurationTracker()
        effect = create_effect(
            spell_id="shield",
            spell_name="Shield",
            caster_id="caster_01",
            target_id="caster_01",
            duration_rounds=2,
        )
        tracker.add_effect(effect)

        # Tick 1 round
        expired = tracker.tick_round()
        assert len(expired) == 0
        assert len(tracker.get_effects_on("caster_01")) == 1

        # Tick another round - should expire
        expired = tracker.tick_round()
        assert len(expired) == 1
        assert len(tracker.get_effects_on("caster_01")) == 0

    def test_permanent_effects_dont_expire(self):
        """Permanent effects (-1 duration) don't expire."""
        tracker = DurationTracker()
        effect = create_effect(
            spell_id="blindness_deafness",
            spell_name="Blindness/Deafness",
            caster_id="caster_01",
            target_id="target_01",
            duration_rounds=-1,  # Permanent
            condition="blinded",
        )
        tracker.add_effect(effect)

        # Tick many rounds
        for _ in range(100):
            tracker.tick_round()

        # Still active
        effects = tracker.get_effects_on("target_01")
        assert len(effects) == 1
        assert effects[0].is_permanent()


# ==============================================================================
# TESTS: STP Generation
# ==============================================================================

class TestSTPGeneration:
    """Test STP generation for spells."""

    def test_spell_generates_save_stp(self, resolver, caster, target, targets_dict):
        """Spells with saves generate SAVING_THROW STPs."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="hold_person",
            target_entity_id=target.entity_id,
        )
        result = resolver.resolve_spell(intent, caster, targets_dict)

        save_stps = [stp for stp in result.stps if stp.packet_type == STPType.SAVING_THROW]
        assert len(save_stps) >= 1

    def test_spell_generates_damage_stp(self, resolver, caster, target, targets_dict):
        """Damage spells generate DAMAGE_ROLL STPs."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="magic_missile",
            target_entity_id=target.entity_id,
        )
        result = resolver.resolve_spell(intent, caster, targets_dict)

        damage_stps = [stp for stp in result.stps if stp.packet_type == STPType.DAMAGE_ROLL]
        assert len(damage_stps) >= 1

    def test_area_spell_generates_aoe_stp(self, resolver, caster, multiple_targets):
        """Area spells generate AOE_RESOLUTION STPs."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="fireball",
            target_position=Position(8, 5),
        )
        result = resolver.resolve_spell(intent, caster, multiple_targets)

        aoe_stps = [stp for stp in result.stps if stp.packet_type == STPType.AOE_RESOLUTION]
        assert len(aoe_stps) >= 1

    def test_debuff_generates_condition_stp(self, grid, spell_registry):
        """Debuffs generate CONDITION_APPLIED STPs on failed save."""
        rng = RNGManager(master_seed=1)  # Seeded for predictable low rolls
        resolver = create_spell_resolver(grid, rng, spell_registry)

        grid.place_entity("caster", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("victim", Position(4, 0), SizeCategory.MEDIUM)

        caster = CasterStats(
            caster_id="caster",
            position=Position(0, 0),
            caster_level=10,
            spell_dc_base=20,  # High DC
        )
        target = TargetStats(
            entity_id="victim",
            position=Position(4, 0),
            hit_points=50,
            max_hit_points=50,
            will_save=-5,  # Very low, will fail
        )

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="hold_person",
            target_entity_id="victim",
        )
        result = resolver.resolve_spell(intent, caster, {"victim": target})

        # If they failed the save, should have condition STP
        if not result.saves_made.get("victim", True):
            condition_stps = [stp for stp in result.stps
                           if stp.packet_type == STPType.CONDITION_APPLIED]
            assert len(condition_stps) >= 1


# ==============================================================================
# TESTS: Determinism
# ==============================================================================

class TestDeterminism:
    """Test deterministic spell resolution."""

    def test_same_seed_same_results(self, grid, spell_registry):
        """Same RNG seed produces identical results."""
        results = []

        for _ in range(3):
            # Reset grid and RNG
            test_grid = BattleGrid(20, 20)
            test_grid.place_entity("caster", Position(0, 0), SizeCategory.MEDIUM)
            test_grid.place_entity("target", Position(4, 0), SizeCategory.MEDIUM)

            rng = RNGManager(master_seed=42)
            resolver = create_spell_resolver(test_grid, rng, spell_registry)

            caster = CasterStats(
                caster_id="caster",
                position=Position(0, 0),
                caster_level=8,
                spell_dc_base=14,
            )
            target = TargetStats(
                entity_id="target",
                position=Position(4, 0),
                hit_points=50,
                max_hit_points=50,
                ref_save=5,
            )

            intent = SpellCastIntent(
                caster_id="caster",
                spell_id="fireball",
                target_position=Position(4, 0),
            )
            result = resolver.resolve_spell(intent, caster, {"target": target})
            results.append(result)

        # All results should be identical
        for i in range(1, len(results)):
            assert results[i].damage_dealt == results[0].damage_dealt
            assert results[i].saves_made == results[0].saves_made


# ==============================================================================
# TESTS: Spell Registry
# ==============================================================================

class TestSpellRegistry:
    """Test the spell registry."""

    def test_registry_has_spells(self):
        """Registry contains spells."""
        assert len(SPELL_REGISTRY) >= 10

    def test_get_spell(self):
        """Can retrieve spell by ID."""
        spell = get_spell("fireball")
        assert spell.name == "Fireball"
        assert spell.level == 3

    def test_get_spell_not_found(self):
        """Unknown spell raises KeyError."""
        with pytest.raises(KeyError):
            get_spell("nonexistent_spell")

    def test_get_spells_by_level(self):
        """Can filter spells by level."""
        level_3 = get_spells_by_level(3)
        assert all(spell.level == 3 for spell in level_3.values())
        assert "fireball" in level_3
        assert "lightning_bolt" in level_3

    def test_get_damage_spells(self):
        """Can get all damage spells."""
        damage = get_damage_spells()
        assert all(spell.effect_type == SpellEffect.DAMAGE for spell in damage.values())
        assert "fireball" in damage
        assert "magic_missile" in damage

    def test_get_healing_spells(self):
        """Can get all healing spells."""
        healing = get_healing_spells()
        assert all(spell.effect_type == SpellEffect.HEALING for spell in healing.values())
        assert "cure_light_wounds" in healing


# ==============================================================================
# TESTS: Healing Spells
# ==============================================================================

class TestHealingSpells:
    """Test healing spell mechanics."""

    def test_cure_light_wounds_heals(self, resolver, caster, grid):
        """Cure Light Wounds restores HP."""
        # Create a damaged target
        grid.place_entity("injured", Position(6, 5), SizeCategory.MEDIUM)
        target = TargetStats(
            entity_id="injured",
            position=Position(6, 5),
            hit_points=10,  # Damaged
            max_hit_points=40,
        )

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="cure_light_wounds",
            target_entity_id="injured",
        )
        result = resolver.resolve_spell(intent, caster, {"injured": target})

        assert result.success is True
        assert "injured" in result.healing_done
        assert result.healing_done["injured"] > 0

    def test_healing_capped_at_max_hp(self, resolver, caster, grid):
        """Healing doesn't exceed max HP."""
        grid.place_entity("nearly_full", Position(6, 5), SizeCategory.MEDIUM)
        target = TargetStats(
            entity_id="nearly_full",
            position=Position(6, 5),
            hit_points=38,  # Only 2 HP down
            max_hit_points=40,
        )

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="cure_serious_wounds",  # 3d8 + level
            target_entity_id="nearly_full",
        )
        result = resolver.resolve_spell(intent, caster, {"nearly_full": target})

        # Should only heal up to 2 HP
        assert result.healing_done.get("nearly_full", 0) <= 2


# ==============================================================================
# TESTS: Edge Cases
# ==============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_self_target_spell(self, resolver, caster, targets_dict):
        """Self-targeting spells work correctly."""
        # Add caster to targets
        caster_target = TargetStats(
            entity_id=caster.caster_id,
            position=caster.position,
            hit_points=30,
            max_hit_points=40,
        )
        targets_dict[caster.caster_id] = caster_target

        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="shield",
        )
        result = resolver.resolve_spell(intent, caster, targets_dict)

        assert result.success is True
        assert caster.caster_id in result.affected_entities

    def test_zero_damage_on_full_negate(self, grid, spell_registry):
        """Negated spells deal zero damage."""
        rng = RNGManager(master_seed=42)
        resolver = create_spell_resolver(grid, rng, spell_registry)

        grid.place_entity("caster", Position(0, 0), SizeCategory.MEDIUM)
        grid.place_entity("evasive", Position(4, 0), SizeCategory.MEDIUM)

        caster = CasterStats(
            caster_id="caster",
            position=Position(0, 0),
            caster_level=8,
            spell_dc_base=10,  # Low DC
        )
        # Hold person has negates on save
        target = TargetStats(
            entity_id="evasive",
            position=Position(4, 0),
            hit_points=50,
            max_hit_points=50,
            will_save=30,  # Very high
        )

        intent = SpellCastIntent(
            caster_id="caster",
            spell_id="hold_person",
            target_entity_id="evasive",
        )
        result = resolver.resolve_spell(intent, caster, {"evasive": target})

        # Should have saved
        assert result.saves_made.get("evasive", False) is True
        # No conditions applied
        assert ("evasive", "paralyzed") not in result.conditions_applied

    def test_unknown_entity_target(self, resolver, caster):
        """Targeting unknown entity fails validation."""
        intent = SpellCastIntent(
            caster_id=caster.caster_id,
            spell_id="magic_missile",
            target_entity_id="nonexistent_target",
        )
        valid, error = resolver.validate_cast(intent, caster)
        assert valid is False
        assert "not found" in error.lower()


# ==============================================================================
# TESTS: DurationTracker Serialization
# ==============================================================================

class TestDurationTrackerSerialization:
    """Test DurationTracker serialization."""

    def test_serialize_deserialize(self):
        """Tracker serializes and deserializes correctly."""
        tracker = DurationTracker()
        effect1 = create_effect(
            spell_id="mage_armor",
            spell_name="Mage Armor",
            caster_id="caster_01",
            target_id="target_01",
            duration_rounds=60,
        )
        effect2 = create_effect(
            spell_id="bulls_strength",
            spell_name="Bull's Strength",
            caster_id="caster_02",
            target_id="target_01",
            duration_rounds=10,
        )
        tracker.add_effect(effect1)
        tracker.add_effect(effect2)

        # Serialize
        data = tracker.to_dict()

        # Deserialize
        restored = DurationTracker.from_dict(data)

        assert len(restored) == 2
        assert restored.has_effect("target_01", "mage_armor")
        assert restored.has_effect("target_01", "bulls_strength")


# ==============================================================================
# TESTS: Dice Rolling
# ==============================================================================

class TestDiceRolling:
    """Test dice rolling mechanics."""

    def test_roll_basic_dice(self, resolver):
        """Basic dice rolling works."""
        rolls, total = resolver._roll_dice("8d6")
        assert len(rolls) == 8
        assert all(1 <= r <= 6 for r in rolls)
        assert total == sum(rolls)

    def test_roll_dice_with_bonus(self, resolver):
        """Dice rolling with bonus works."""
        rolls, total = resolver._roll_dice("1d8+5")
        assert len(rolls) == 1
        assert total == rolls[0] + 5

    def test_roll_dice_with_penalty(self, resolver):
        """Dice rolling with penalty works."""
        rolls, total = resolver._roll_dice("2d6-2")
        assert len(rolls) == 2
        assert total == sum(rolls) - 2
