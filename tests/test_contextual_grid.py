"""Tests for M3 Contextual Grid.

Tests:
- Grid visible during active combat
- Grid hidden when no combat
- Grid hidden after combat ends (combat_ended reason)
- Entity positions extracted from world state
- Positions sorted by entity_id
- Dimensions computed from positions
- Deterministic output
"""

import pytest

from aidm.core.state import WorldState
from aidm.immersion.contextual_grid import compute_grid_state
from aidm.schemas.immersion import GridRenderState


# =============================================================================
# Visibility Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestGridVisibility:
    """Tests for grid show/hide logic."""

    def test_visible_during_combat(self):
        """Grid should be visible when combat is active."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert result.visible is True
        assert result.reason == "combat_active"

    def test_hidden_no_combat(self):
        """Grid should be hidden when no combat."""
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_grid_state(ws)
        assert result.visible is False
        assert result.reason == "no_combat"

    def test_hidden_after_combat_ends(self):
        """Grid should hide with 'combat_ended' after combat ends."""
        prev = GridRenderState(visible=True, reason="combat_active")
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_grid_state(ws, previous=prev)
        assert result.visible is False
        assert result.reason == "combat_ended"

    def test_stays_hidden_no_combat(self):
        """Grid should stay hidden with 'no_combat' if was already hidden."""
        prev = GridRenderState(visible=False, reason="no_combat")
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_grid_state(ws, previous=prev)
        assert result.visible is False
        assert result.reason == "no_combat"

    def test_stays_hidden_after_combat_ended(self):
        """After combat_ended, next state should be no_combat."""
        prev = GridRenderState(visible=False, reason="combat_ended")
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_grid_state(ws, previous=prev)
        assert result.visible is False
        assert result.reason == "no_combat"


# =============================================================================
# Entity Position Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestEntityPositions:
    """Tests for entity position extraction."""

    def test_extracts_positioned_entities(self):
        """Should extract entities with position data."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "fighter_1": {
                    "name": "Fighter",
                    "team": "party",
                    "position": {"x": 3, "y": 5},
                },
                "goblin_1": {
                    "name": "Goblin",
                    "team": "hostile",
                    "position": {"x": 7, "y": 5},
                },
            },
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert len(result.entity_positions) == 2

    def test_skips_entities_without_position(self):
        """Should skip entities without position data."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "fighter_1": {
                    "name": "Fighter",
                    "position": {"x": 3, "y": 5},
                },
                "npc_observer": {
                    "name": "Observer",
                    # No position
                },
            },
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert len(result.entity_positions) == 1
        assert result.entity_positions[0].entity_id == "fighter_1"

    def test_positions_sorted_by_entity_id(self):
        """Positions should be sorted by entity_id for determinism."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "zzz_zombie": {"name": "Zombie", "position": {"x": 1, "y": 1}},
                "aaa_archer": {"name": "Archer", "position": {"x": 2, "y": 2}},
                "mmm_mage": {"name": "Mage", "position": {"x": 3, "y": 3}},
            },
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        ids = [p.entity_id for p in result.entity_positions]
        assert ids == sorted(ids)

    def test_entity_label_from_name(self):
        """Label should come from entity 'name' field."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "goblin_1": {
                    "name": "Goblin Warrior",
                    "team": "hostile",
                    "position": {"x": 5, "y": 3},
                },
            },
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert result.entity_positions[0].label == "Goblin Warrior"
        assert result.entity_positions[0].team == "hostile"

    def test_entity_label_fallback_to_id(self):
        """Label should fall back to entity_id if no name."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "trap_01": {"position": {"x": 2, "y": 2}},
            },
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert result.entity_positions[0].label == "trap_01"

    def test_empty_positions_when_no_combat(self):
        """No combat should produce empty position list."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "fighter_1": {"position": {"x": 3, "y": 5}},
            },
        )
        result = compute_grid_state(ws)
        assert result.entity_positions == []


# =============================================================================
# Dimension Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestDimensions:
    """Tests for grid dimension computation."""

    def test_dimensions_from_positions(self):
        """Dimensions should be (max_x+1, max_y+1)."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "e1": {"position": {"x": 3, "y": 5}},
                "e2": {"position": {"x": 9, "y": 7}},
            },
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert result.dimensions == (10, 8)

    def test_zero_dimensions_no_combat(self):
        """No combat should produce (0, 0) dimensions."""
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_grid_state(ws)
        assert result.dimensions == (0, 0)

    def test_single_entity_dimensions(self):
        """Single entity at (0, 0) should produce (1, 1)."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"e1": {"position": {"x": 0, "y": 0}}},
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert result.dimensions == (1, 1)


# =============================================================================
# Determinism Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestGridDeterminism:
    """Tests for deterministic output."""

    def test_deterministic_10x(self):
        """Same inputs should produce identical output 10 times."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "a": {"name": "A", "position": {"x": 1, "y": 2}},
                "b": {"name": "B", "position": {"x": 3, "y": 4}},
            },
            active_combat={"round": 1},
        )

        results = [compute_grid_state(ws) for _ in range(10)]

        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first


# =============================================================================
# Validation Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestGridValidation:
    """Tests for output validation."""

    def test_combat_state_validates(self):
        """Grid state during combat should pass validation."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"e1": {"name": "E", "position": {"x": 1, "y": 1}}},
            active_combat={"round": 1},
        )
        result = compute_grid_state(ws)
        assert result.validate() == []

    def test_no_combat_state_validates(self):
        """Grid state without combat should pass validation."""
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_grid_state(ws)
        assert result.validate() == []
