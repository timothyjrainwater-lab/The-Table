"""Tests for CP-20 — Discrete Environmental Damage.

Tests environmental damage hazards:
- Fire squares (1d6 fire)
- Acid pools (1d6 acid)
- Lava edges (2d6 fire)
- Spiked pits (falling + 1d6 piercing)

Per CP20_TEST_CASE_CATALOG.md:
- Direct entry hazards
- Forced movement hazards
- Falling + damage combinations
- Ordering assertions
- Determinism verification
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.core.environmental_damage_resolver import (
    resolve_environmental_damage,
    resolve_spiked_pit_damage,
    check_and_resolve_entry_hazard,
    get_environmental_hazard,
    has_environmental_hazard,
    HAZARD_DAMAGE_CONFIG,
    EnvironmentalDamageResult,
)
from aidm.core.terrain_resolver import (
    resolve_forced_movement_with_hazards,
)


# ==============================================================================
# TEST FIXTURES
# ==============================================================================

def make_world_state_with_hazard(
    entity_hp: int = 50,
    hazard_type: str = "fire",
    hazard_pos: dict = None,
    is_pit: bool = False,
    pit_depth: int = 0,
) -> WorldState:
    """Create a world state with an environmental hazard."""
    if hazard_pos is None:
        hazard_pos = {"x": 5, "y": 5}

    terrain_cell = {
        "position": hazard_pos,
        "elevation": 0,
        "movement_cost": 1,
        "terrain_tags": [],
        "cover_type": None,
        "is_pit": is_pit,
        "pit_depth": pit_depth,
        "is_ledge": False,
        "ledge_drop": 0,
        "hazard_type": hazard_type,
    }

    return WorldState(
        ruleset_version="3.5e",
        entities={
            "test_entity": {
                EF.ENTITY_ID: "test_entity",
                EF.TEAM: "party",
                EF.HP_CURRENT: entity_hp,
                EF.HP_MAX: 50,
                EF.POSITION: {"x": 0, "y": 0},
                EF.DEFEATED: False,
            },
        },
        active_combat={
            "round": 1,
            "terrain_map": {
                f"{hazard_pos['x']},{hazard_pos['y']}": terrain_cell,
            },
        },
    )


def make_rng(seed: int = 42) -> RNGManager:
    """Create a seeded RNG manager."""
    return RNGManager(master_seed=seed)


# ==============================================================================
# DIRECT ENTRY HAZARD TESTS
# ==============================================================================

class TestDirectEntryHazards:
    """Tests for voluntary entry into environmental hazards."""

    def test_fire_square_entry(self):
        """Entering a fire square deals 1d6 fire damage."""
        world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="fire")
        rng = make_rng(seed=42)
        position = {"x": 5, "y": 5}

        events, updated_state, result = resolve_environmental_damage(
            entity_id="test_entity",
            position=position,
            hazard_type="fire",
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # Should have events
        assert len(events) >= 1
        assert events[0].event_type == "environmental_damage"
        assert events[0].payload["hazard_type"] == "fire"
        assert events[0].payload["damage_type"] == "fire"
        assert events[0].payload["dice"] == "1d6"

        # Result should have correct damage
        assert result.hazard_type == "fire"
        assert result.dice_count == 1
        assert result.dice_size == 6
        assert len(result.dice_results) == 1
        assert 1 <= result.total_damage <= 6

        # HP should be reduced
        entity = updated_state.entities["test_entity"]
        assert entity[EF.HP_CURRENT] == 50 - result.total_damage

    def test_acid_pool_entry(self):
        """Entering an acid pool deals 1d6 acid damage."""
        world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="acid")
        rng = make_rng(seed=123)
        position = {"x": 5, "y": 5}

        events, updated_state, result = resolve_environmental_damage(
            entity_id="test_entity",
            position=position,
            hazard_type="acid",
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        assert events[0].event_type == "environmental_damage"
        assert events[0].payload["hazard_type"] == "acid"
        assert events[0].payload["damage_type"] == "acid"
        assert result.dice_count == 1
        assert 1 <= result.total_damage <= 6

    def test_lava_edge_entry(self):
        """Entering a lava edge deals 2d6 fire damage."""
        world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="lava")
        rng = make_rng(seed=456)
        position = {"x": 5, "y": 5}

        events, updated_state, result = resolve_environmental_damage(
            entity_id="test_entity",
            position=position,
            hazard_type="lava",
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        assert events[0].event_type == "environmental_damage"
        assert events[0].payload["hazard_type"] == "lava"
        assert events[0].payload["damage_type"] == "fire"
        assert events[0].payload["dice"] == "2d6"
        assert result.dice_count == 2
        assert len(result.dice_results) == 2
        assert 2 <= result.total_damage <= 12

    def test_no_damage_on_empty_cell(self):
        """No damage when entering a cell without hazards."""
        world_state = WorldState(
            ruleset_version="3.5e",
            entities={
                "test_entity": {
                    EF.ENTITY_ID: "test_entity",
                    EF.HP_CURRENT: 50,
                    EF.POSITION: {"x": 0, "y": 0},
                },
            },
            active_combat={"terrain_map": {}},
        )
        rng = make_rng()
        position = {"x": 5, "y": 5}

        events, updated_state, result = check_and_resolve_entry_hazard(
            entity_id="test_entity",
            position=position,
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        assert len(events) == 0
        assert result is None


# ==============================================================================
# FORCED MOVEMENT HAZARD TESTS
# ==============================================================================

class TestForcedMovementHazards:
    """Tests for forced movement into environmental hazards."""

    def test_bull_rush_into_fire(self):
        """Bull Rush pushing entity into fire square triggers fire damage."""
        # Setup: fire square at (2, 0)
        world_state = make_world_state_with_hazard(
            entity_hp=50,
            hazard_type="fire",
            hazard_pos={"x": 2, "y": 0},
        )
        # Update entity position to (1, 0)
        entities = world_state.entities.copy()
        entities["test_entity"] = entities["test_entity"].copy()
        entities["test_entity"][EF.POSITION] = {"x": 1, "y": 0}
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=world_state.active_combat,
        )

        rng = make_rng(seed=42)

        events, updated_state, final_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id="test_entity",
            start_pos={"x": 1, "y": 0},
            push_direction=(1, 0),  # Push east
            push_distance=5,  # One square
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # Should have environmental damage event
        env_damage_events = [e for e in events if e.event_type == "environmental_damage"]
        assert len(env_damage_events) == 1
        assert env_damage_events[0].payload["hazard_type"] == "fire"

        # Final position should be fire square
        assert final_pos == {"x": 2, "y": 0}

    def test_forced_movement_into_acid(self):
        """Forced movement into acid pool triggers acid damage."""
        world_state = make_world_state_with_hazard(
            entity_hp=50,
            hazard_type="acid",
            hazard_pos={"x": 3, "y": 0},
        )
        entities = world_state.entities.copy()
        entities["test_entity"] = entities["test_entity"].copy()
        entities["test_entity"][EF.POSITION] = {"x": 1, "y": 0}
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=world_state.active_combat,
        )

        rng = make_rng(seed=789)

        events, updated_state, final_pos, _ = resolve_forced_movement_with_hazards(
            entity_id="test_entity",
            start_pos={"x": 1, "y": 0},
            push_direction=(1, 0),
            push_distance=10,  # Two squares
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # Check for acid damage
        env_events = [e for e in events if e.event_type == "environmental_damage"]
        assert len(env_events) == 1
        assert env_events[0].payload["damage_type"] == "acid"


# ==============================================================================
# FALLING + DAMAGE COMBINATION TESTS
# ==============================================================================

class TestFallingPlusDamage:
    """Tests for combined falling and environmental damage."""

    def test_fall_into_spiked_pit(self):
        """Falling into spiked pit deals falling damage + 1d6 piercing."""
        # Setup: spiked pit at (2, 0) with 20 ft depth
        terrain_cell = {
            "position": {"x": 2, "y": 0},
            "elevation": 0,
            "movement_cost": 1,
            "terrain_tags": [],
            "cover_type": None,
            "is_pit": True,
            "pit_depth": 20,
            "is_ledge": False,
            "ledge_drop": 0,
            "hazard_type": "spiked_pit",
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities={
                "test_entity": {
                    EF.ENTITY_ID: "test_entity",
                    EF.HP_CURRENT: 50,
                    EF.HP_MAX: 50,
                    EF.POSITION: {"x": 1, "y": 0},
                    EF.DEFEATED: False,
                },
            },
            active_combat={
                "round": 1,
                "terrain_map": {
                    "2,0": terrain_cell,
                },
            },
        )

        rng = make_rng(seed=42)

        events, updated_state, final_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id="test_entity",
            start_pos={"x": 1, "y": 0},
            push_direction=(1, 0),
            push_distance=5,
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # Should have hazard triggered event
        hazard_events = [e for e in events if e.event_type == "hazard_triggered"]
        assert len(hazard_events) == 1
        assert hazard_events[0].payload["hazard_type"] == "pit"

        # Should have falling damage event
        falling_events = [e for e in events if e.event_type == "falling_damage"]
        assert len(falling_events) == 1

        # Should have spike damage event (environmental_damage)
        spike_events = [e for e in events if e.event_type == "environmental_damage"]
        assert len(spike_events) == 1
        assert spike_events[0].payload["hazard_type"] == "spiked_pit"
        assert spike_events[0].payload["damage_type"] == "piercing"

        # Falling result should exist
        assert falling_result is not None
        assert falling_result.fall_distance == 20


# ==============================================================================
# ORDERING TESTS
# ==============================================================================

class TestOrdering:
    """Tests for correct event ordering."""

    def test_hazard_before_environmental_damage(self):
        """Hazard triggered event comes before environmental damage."""
        terrain_cell = {
            "position": {"x": 2, "y": 0},
            "elevation": 0,
            "movement_cost": 1,
            "terrain_tags": [],
            "cover_type": None,
            "is_pit": True,
            "pit_depth": 20,
            "is_ledge": False,
            "ledge_drop": 0,
            "hazard_type": "spiked_pit",
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities={
                "test_entity": {
                    EF.ENTITY_ID: "test_entity",
                    EF.HP_CURRENT: 50,
                    EF.POSITION: {"x": 1, "y": 0},
                    EF.DEFEATED: False,
                },
            },
            active_combat={"terrain_map": {"2,0": terrain_cell}},
        )

        rng = make_rng(seed=42)

        events, _, _, _ = resolve_forced_movement_with_hazards(
            entity_id="test_entity",
            start_pos={"x": 1, "y": 0},
            push_direction=(1, 0),
            push_distance=5,
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # Find indices of key events
        hazard_idx = next(i for i, e in enumerate(events) if e.event_type == "hazard_triggered")
        falling_idx = next(i for i, e in enumerate(events) if e.event_type == "falling_damage")
        spike_idx = next(i for i, e in enumerate(events) if e.event_type == "environmental_damage")

        # Verify ordering: hazard -> falling -> spike
        assert hazard_idx < falling_idx < spike_idx

    def test_hp_changed_after_damage(self):
        """HP changed event follows damage event."""
        world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="fire")
        rng = make_rng(seed=42)

        events, _, result = resolve_environmental_damage(
            entity_id="test_entity",
            position={"x": 5, "y": 5},
            hazard_type="fire",
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        damage_idx = next(i for i, e in enumerate(events) if e.event_type == "environmental_damage")
        hp_idx = next(i for i, e in enumerate(events) if e.event_type == "hp_changed")

        assert damage_idx < hp_idx


# ==============================================================================
# DETERMINISM TESTS
# ==============================================================================

class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_seed_same_damage(self):
        """Same RNG seed produces identical damage across runs."""
        results = []

        for _ in range(10):
            world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="lava")
            rng = make_rng(seed=12345)

            events, _, result = resolve_environmental_damage(
                entity_id="test_entity",
                position={"x": 5, "y": 5},
                hazard_type="lava",
                world_state=world_state,
                rng=rng,
                next_event_id=1,
                timestamp=1.0,
            )
            results.append(result.total_damage)

        # All results should be identical
        assert all(r == results[0] for r in results)

    def test_different_seeds_different_damage(self):
        """Different RNG seeds produce different damage (probabilistically)."""
        damages = set()

        for seed in range(100):
            world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="fire")
            rng = make_rng(seed=seed)

            _, _, result = resolve_environmental_damage(
                entity_id="test_entity",
                position={"x": 5, "y": 5},
                hazard_type="fire",
                world_state=world_state,
                rng=rng,
                next_event_id=1,
                timestamp=1.0,
            )
            damages.add(result.total_damage)

        # Should have multiple different values (1-6 for 1d6)
        assert len(damages) > 1


# ==============================================================================
# NEGATIVE TESTS
# ==============================================================================

class TestNegativeCases:
    """Tests for edge cases and no-op scenarios."""

    def test_no_persistence(self):
        """Environmental damage is one-shot, no persistence on same position."""
        world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="fire")
        rng = make_rng(seed=42)
        position = {"x": 5, "y": 5}

        # First resolution
        events1, state1, result1 = resolve_environmental_damage(
            entity_id="test_entity",
            position=position,
            hazard_type="fire",
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # Damage applied
        hp_after_first = state1.entities["test_entity"][EF.HP_CURRENT]
        assert hp_after_first < 50

        # Second resolution with fresh state (simulating "staying" in square)
        # Note: In actual play, this would only trigger on re-entry, not staying
        rng2 = make_rng(seed=43)
        events2, state2, result2 = resolve_environmental_damage(
            entity_id="test_entity",
            position=position,
            hazard_type="fire",
            world_state=state1,  # Use state after first damage
            rng=rng2,
            next_event_id=10,
            timestamp=2.0,
        )

        # Should still work (one-shot per entry, not turn-based persistence)
        assert len(events2) >= 1

    def test_unknown_hazard_type_no_damage(self):
        """Unknown hazard type results in zero damage."""
        world_state = make_world_state_with_hazard(entity_hp=50, hazard_type="fire")
        rng = make_rng(seed=42)

        events, updated_state, result = resolve_environmental_damage(
            entity_id="test_entity",
            position={"x": 5, "y": 5},
            hazard_type="unknown_hazard",
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # No damage for unknown hazard
        assert len(events) == 0
        assert result.total_damage == 0

    def test_entity_defeat_on_lethal_damage(self):
        """Entity is defeated when environmental damage reduces HP to 0 or below."""
        world_state = make_world_state_with_hazard(entity_hp=3, hazard_type="lava")
        rng = make_rng(seed=42)

        events, updated_state, result = resolve_environmental_damage(
            entity_id="test_entity",
            position={"x": 5, "y": 5},
            hazard_type="lava",
            world_state=world_state,
            rng=rng,
            next_event_id=1,
            timestamp=1.0,
        )

        # Lava does 2d6, minimum 2 damage
        if result.total_damage >= 3:
            defeated_events = [e for e in events if e.event_type == "entity_defeated"]
            assert len(defeated_events) == 1
            assert updated_state.entities["test_entity"][EF.DEFEATED] is True


# ==============================================================================
# HAZARD DETECTION TESTS
# ==============================================================================

class TestHazardDetection:
    """Tests for hazard detection utilities."""

    def test_get_environmental_hazard(self):
        """get_environmental_hazard returns correct hazard type."""
        world_state = make_world_state_with_hazard(hazard_type="acid")
        position = {"x": 5, "y": 5}

        hazard = get_environmental_hazard(world_state, position)
        assert hazard == "acid"

    def test_get_environmental_hazard_no_hazard(self):
        """get_environmental_hazard returns None for empty cell."""
        world_state = WorldState(
            ruleset_version="3.5e",
            entities={},
            active_combat={"terrain_map": {}},
        )

        hazard = get_environmental_hazard(world_state, {"x": 0, "y": 0})
        assert hazard is None

    def test_has_environmental_hazard(self):
        """has_environmental_hazard returns True/False correctly."""
        world_state = make_world_state_with_hazard(hazard_type="fire")

        assert has_environmental_hazard(world_state, {"x": 5, "y": 5}) is True
        assert has_environmental_hazard(world_state, {"x": 0, "y": 0}) is False


# ==============================================================================
# CONFIGURATION TESTS
# ==============================================================================

class TestConfiguration:
    """Tests for hazard configuration."""

    def test_hazard_config_fire(self):
        """Fire hazard configuration is correct."""
        dice, size, dtype = HAZARD_DAMAGE_CONFIG["fire"]
        assert dice == 1
        assert size == 6
        assert dtype == "fire"

    def test_hazard_config_acid(self):
        """Acid hazard configuration is correct."""
        dice, size, dtype = HAZARD_DAMAGE_CONFIG["acid"]
        assert dice == 1
        assert size == 6
        assert dtype == "acid"

    def test_hazard_config_lava(self):
        """Lava hazard configuration is correct."""
        dice, size, dtype = HAZARD_DAMAGE_CONFIG["lava"]
        assert dice == 2
        assert size == 6
        assert dtype == "fire"

    def test_hazard_config_spiked_pit(self):
        """Spiked pit hazard configuration is correct."""
        dice, size, dtype = HAZARD_DAMAGE_CONFIG["spiked_pit"]
        assert dice == 1
        assert size == 6
        assert dtype == "piercing"
