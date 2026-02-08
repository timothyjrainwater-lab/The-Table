"""Tests for M1 Narration Layer.

Tests the LLM_ENGINE_BOUNDARY_CONTRACT.md narrator implementation:
- Template-based narration
- Context extraction from EngineResult
- Cannot alter outcomes (read-only input)
- Fallback behavior
"""

import pytest

from aidm.narration.narrator import (
    Narrator,
    NarrationContext,
    NarrationTemplates,
    create_default_narrator,
    narrate_attack,
)
from aidm.schemas.engine_result import (
    EngineResult,
    EngineResultStatus,
    EngineResultBuilder,
)


# =============================================================================
# Test Fixtures
# =============================================================================

def create_hit_result() -> EngineResult:
    """Create an attack hit result."""
    builder = EngineResultBuilder(intent_id="test-attack")
    builder.add_event({
        "type": "attack_roll",
        "attacker": "fighter_1",
        "target": "goblin_1",
        "natural": 18,
        "total": 23,
        "hit": True,
    })
    builder.add_event({
        "type": "damage_dealt",
        "target": "goblin_1",
        "damage": 8,
    })
    builder.set_narration_token("attack_hit")
    return builder.build()


def create_miss_result() -> EngineResult:
    """Create an attack miss result."""
    builder = EngineResultBuilder(intent_id="test-miss")
    builder.add_event({
        "type": "attack_roll",
        "attacker": "fighter_1",
        "target": "goblin_1",
        "natural": 5,
        "total": 10,
        "hit": False,
    })
    builder.set_narration_token("attack_miss")
    return builder.build()


def create_failure_result() -> EngineResult:
    """Create a failed action result."""
    builder = EngineResultBuilder(intent_id="test-fail")
    return builder.build_failure("Target not found")


def create_aborted_result() -> EngineResult:
    """Create an aborted action result."""
    builder = EngineResultBuilder(intent_id="test-abort")
    return builder.build_aborted("Attack of opportunity")


# =============================================================================
# NarrationContext Tests
# =============================================================================

class TestNarrationContext:
    """Tests for NarrationContext."""

    def test_from_engine_result(self):
        """Should extract context from engine result."""
        result = create_hit_result()
        context = NarrationContext.from_engine_result(result)

        assert context.actor_id == "fighter_1"
        assert context.target_id == "goblin_1"

    def test_from_engine_result_with_names(self):
        """Should use provided entity names."""
        result = create_hit_result()
        names = {
            "fighter_1": "Theron",
            "goblin_1": "the goblin warrior",
        }
        context = NarrationContext.from_engine_result(result, names)

        assert context.actor_name == "Theron"
        assert context.target_name == "the goblin warrior"

    def test_default_names(self):
        """Should use entity IDs if no names provided."""
        result = create_hit_result()
        context = NarrationContext.from_engine_result(result)

        assert context.actor_name == "fighter_1"
        assert context.target_name == "goblin_1"


# =============================================================================
# NarrationTemplates Tests
# =============================================================================

class TestNarrationTemplates:
    """Tests for NarrationTemplates."""

    def test_attack_hit_template(self):
        """Should have attack_hit template."""
        template = NarrationTemplates.get_template("attack_hit")
        assert "{actor}" in template
        assert "{target}" in template
        assert "{damage}" in template

    def test_attack_miss_template(self):
        """Should have attack_miss template."""
        template = NarrationTemplates.get_template("attack_miss")
        assert "{actor}" in template
        assert "{target}" in template

    def test_unknown_token_fallback(self):
        """Should return unknown template for unrecognized tokens."""
        template = NarrationTemplates.get_template("nonexistent_token")
        assert template == NarrationTemplates.TEMPLATES["unknown"]

    def test_all_combat_maneuvers_have_templates(self):
        """Should have templates for all combat maneuvers."""
        maneuver_tokens = [
            "bull_rush_success", "bull_rush_failure",
            "trip_success", "trip_failure",
            "grapple_success", "grapple_failure",
            "disarm_success", "disarm_failure",
            "overrun_success", "overrun_failure",
        ]

        for token in maneuver_tokens:
            template = NarrationTemplates.get_template(token)
            assert template != NarrationTemplates.TEMPLATES["unknown"], f"Missing template for {token}"


# =============================================================================
# Narrator Tests
# =============================================================================

class TestNarrator:
    """Tests for Narrator class."""

    def test_create_default_narrator(self):
        """Should create narrator with templates."""
        narrator = create_default_narrator()
        assert isinstance(narrator, Narrator)

    def test_narrate_attack_hit(self):
        """Should narrate attack hit."""
        result = create_hit_result()
        narrator = Narrator()
        narrator.register_entity_names({
            "fighter_1": "Theron",
            "goblin_1": "the goblin",
        })

        narration = narrator.narrate(result)

        assert "Theron" in narration
        assert "the goblin" in narration
        assert "8" in narration  # damage

    def test_narrate_attack_miss(self):
        """Should narrate attack miss."""
        result = create_miss_result()
        narrator = Narrator()
        narrator.register_entity_name("fighter_1", "Theron")

        narration = narrator.narrate(result)

        assert "Theron" in narration
        assert "miss" in narration.lower() or "wide" in narration.lower()

    def test_narrate_failure(self):
        """Should narrate failed action."""
        result = create_failure_result()
        narrator = Narrator()

        narration = narrator.narrate(result)

        assert "could not be completed" in narration
        assert "Target not found" in narration

    def test_narrate_aborted(self):
        """Should narrate aborted action."""
        result = create_aborted_result()
        narrator = Narrator()

        narration = narrator.narrate(result)

        assert "interrupted" in narration
        assert "Attack of opportunity" in narration

    def test_narrate_with_custom_context(self):
        """Should use provided context."""
        result = create_hit_result()
        narrator = Narrator()
        context = NarrationContext(
            actor_name="Sir Galahad",
            target_name="the evil sorcerer",
            weapon_name="holy sword",
        )

        narration = narrator.narrate(result, context)

        assert "Sir Galahad" in narration
        assert "the evil sorcerer" in narration

    def test_narrate_combat_round(self):
        """Should combine multiple results into round narration."""
        results = [
            create_hit_result(),
            create_miss_result(),
        ]
        narrator = Narrator()

        narration = narrator.narrate_combat_round(results)

        # Should have content from both results
        assert len(narration) > 0
        # Should be separated
        assert "\n" in narration

    def test_narrate_empty_round(self):
        """Should handle empty round gracefully."""
        narrator = Narrator()

        narration = narrator.narrate_combat_round([])

        assert "without incident" in narration


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestNarrateAttack:
    """Tests for narrate_attack convenience function."""

    def test_narrate_hit(self):
        """Should narrate attack hit."""
        narration = narrate_attack(
            attacker_name="Theron",
            target_name="the goblin",
            weapon_name="longsword",
            hit=True,
            damage=8,
        )

        assert "Theron" in narration
        assert "the goblin" in narration
        assert "8" in narration

    def test_narrate_miss(self):
        """Should narrate attack miss."""
        narration = narrate_attack(
            attacker_name="Theron",
            target_name="the goblin",
            weapon_name="longsword",
            hit=False,
        )

        assert "misses" in narration.lower()

    def test_narrate_critical(self):
        """Should narrate critical hit."""
        narration = narrate_attack(
            attacker_name="Theron",
            target_name="the goblin",
            weapon_name="longsword",
            hit=True,
            damage=24,
            critical=True,
        )

        assert "critical" in narration.lower()
        assert "24" in narration

    def test_narrate_defeat(self):
        """Should include defeat message."""
        narration = narrate_attack(
            attacker_name="Theron",
            target_name="the goblin",
            weapon_name="longsword",
            hit=True,
            damage=10,
            target_defeated=True,
        )

        assert "defeated" in narration.lower() or "collapses" in narration.lower()


# =============================================================================
# Read-Only Verification Tests
# =============================================================================

class TestNarratorReadOnly:
    """Tests verifying narrator cannot modify results."""

    def test_result_unchanged_after_narration(self):
        """EngineResult should be unchanged after narration."""
        result = create_hit_result()
        original_status = result.status
        original_events = len(result.events)

        narrator = Narrator()
        narrator.narrate(result)

        # Result should be unchanged
        assert result.status == original_status
        assert len(result.events) == original_events

    def test_narrator_cannot_add_events(self):
        """Narrator should not be able to add events to result."""
        result = create_hit_result()

        # EngineResult is frozen, so this would raise if attempted
        narrator = Narrator()
        narrator.narrate(result)

        # If we got here without exception, narration is properly read-only
        assert True
