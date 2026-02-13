"""WO-CODE-LOOP-001: End-to-end move scenario tests.

Verifies that:
  - Text input "move 4 4" resolves through the full pipeline
  - Box produces movement events
  - Template narration is generated for movement
  - Missing destination triggers clarification
"""

import pytest

from aidm.runtime.play_controller import (
    PlayOneTurnController,
    ScenarioFixture,
    build_simple_combat_fixture,
)
from aidm.core.event_log import EventLog


class TestMoveEndToEnd:
    """Full pipeline: text → intent → Box → events → narration for movement.

    Uses move_fixture (enemy far away) to avoid AoO trigger on step-move.
    """

    def test_move_with_coordinates(self, move_fixture, controller):
        """'move 4 4' should produce movement events."""
        result = controller.play_turn(move_fixture, "move 4 4")

        assert result.success is True
        assert result.box_status == "ok"
        assert result.event_count >= 2  # turn_start + movement

    def test_move_produces_narration(self, move_fixture, controller):
        """Movement narration should be template-based."""
        result = controller.play_turn(move_fixture, "move 4 4")

        assert result.narration_text != ""
        assert result.narration_provenance == "[NARRATIVE:TEMPLATE]"

    def test_move_intent_summary(self, move_fixture, controller):
        """Intent summary should show destination."""
        result = controller.play_turn(move_fixture, "move 4 4")

        assert "move" in result.intent_summary
        assert "(4, 4)" in result.intent_summary

    def test_move_with_to_keyword(self, move_fixture, controller):
        """'move to 4 4' should also work (strips 'to')."""
        result = controller.play_turn(move_fixture, "move to 4 4")

        assert result.success is True
        assert "(4, 4)" in result.intent_summary

    def test_move_synonym_verbs(self, move_fixture):
        """Alternative move verbs should work."""
        for verb in ["go", "walk", "run", "step"]:
            ctrl = PlayOneTurnController(event_log=EventLog())
            result = ctrl.play_turn(move_fixture, f"{verb} 4 4")

            assert result.success is True, f"Verb '{verb}' failed"

    def test_move_no_destination_needs_clarification(
        self, move_fixture, controller,
    ):
        """'move' with no coordinates should trigger clarification."""
        result = controller.play_turn(move_fixture, "move")

        assert result.success is False
        assert result.clarification_needed is True

    def test_move_events_appended_to_log(self, move_fixture, controller):
        """All movement events should be appended to EventLog."""
        result = controller.play_turn(move_fixture, "move 4 4")

        assert len(controller.event_log) == result.event_count
        assert len(controller.event_log) >= 2


class TestEndTurn:
    """End-turn action should pass through without combat."""

    def test_end_turn(self, simple_fixture, controller):
        """'end turn' should succeed with no combat resolution."""
        result = controller.play_turn(simple_fixture, "end turn")

        assert result.success is True
        assert result.box_status == "ok"
        assert result.intent_summary == "end_turn"

    def test_done_synonym(self, simple_fixture, controller):
        """'done' should be recognized as end turn."""
        result = controller.play_turn(simple_fixture, "done")

        assert result.success is True
        assert result.intent_summary == "end_turn"

    def test_pass_synonym(self, simple_fixture, controller):
        """'pass' should be recognized as end turn."""
        result = controller.play_turn(simple_fixture, "pass")

        assert result.success is True
        assert result.intent_summary == "end_turn"


class TestUnrecognizedInput:
    """Unrecognized input should fail gracefully."""

    def test_gibberish(self, simple_fixture, controller):
        """Random text should return parse failure."""
        result = controller.play_turn(simple_fixture, "asdfghjkl")

        assert result.success is False
        assert result.box_status == "parse_failed"
        assert result.error_message is not None

    def test_empty_input(self, simple_fixture, controller):
        """Empty string should return parse failure."""
        result = controller.play_turn(simple_fixture, "")

        assert result.success is False
        assert result.box_status == "parse_failed"

    def test_state_unchanged_on_failure(self, simple_fixture, controller):
        """Failed parse should not change state."""
        result = controller.play_turn(simple_fixture, "asdfghjkl")

        assert result.state_hash_before == result.state_hash_after
        assert result.event_count == 0
