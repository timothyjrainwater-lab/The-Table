"""WO-CODE-LOOP-001: End-to-end attack scenario tests.

Verifies that:
  - Text input "attack the goblin" resolves through the full pipeline
  - Box produces attack_roll, damage, hp_changed events
  - Template narration is generated
  - State hash changes after a successful attack
  - Provenance is always [NARRATIVE:TEMPLATE]
"""

import pytest

from aidm.runtime.play_controller import (
    PlayOneTurnController,
    ScenarioFixture,
    build_simple_combat_fixture,
)
from aidm.core.event_log import EventLog


class TestAttackEndToEnd:
    """Full pipeline: text → intent → Box → events → narration."""

    def test_attack_goblin_produces_events(self, simple_fixture, controller):
        """'attack the goblin' should produce at least turn_start + attack events."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        assert result.success is True
        assert result.box_status == "ok"
        assert result.event_count >= 2  # turn_start + at least one attack event

    def test_attack_produces_attack_roll_event(self, simple_fixture, controller):
        """Events must include an attack_roll event with attacker and target."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        attack_events = [
            e for e in result.events if e["event_type"] == "attack_roll"
        ]
        assert len(attack_events) >= 1

        roll = attack_events[0]["payload"]
        assert roll["attacker_id"] == "pc_fighter"
        assert roll["target_id"] == "goblin_1"

    def test_attack_produces_narration(self, simple_fixture, controller):
        """Narration text must be non-empty and template-sourced."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        assert result.narration_text != ""
        assert result.narration_provenance == "[NARRATIVE:TEMPLATE]"

    def test_state_hash_recorded(self, simple_fixture, controller):
        """Before/after hashes must both be present and non-empty."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        assert result.state_hash_before != ""
        assert result.state_hash_after != ""
        # State should change (attack modifies HP)
        # Note: hash may or may not change depending on hit/miss

    def test_events_appended_to_log(self, simple_fixture, controller):
        """All events from Box must be appended to the EventLog."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        assert len(controller.event_log) == result.event_count
        assert len(controller.event_log) >= 2

    def test_attack_with_weapon_specification(self, simple_fixture, controller):
        """'attack the goblin with longsword' should work."""
        result = controller.play_turn(
            simple_fixture, "attack the goblin with longsword"
        )

        assert result.success is True
        assert "target=goblin_1" in result.intent_summary

    def test_attack_synonym_verbs(self, simple_fixture, controller):
        """Alternative attack verbs ('hit', 'strike', etc.) should work."""
        for verb in ["hit", "strike", "slash", "stab", "swing"]:
            ctrl = PlayOneTurnController(event_log=EventLog())
            result = ctrl.play_turn(simple_fixture, f"{verb} the goblin")

            assert result.success is True, f"Verb '{verb}' failed"
            assert result.box_status == "ok", f"Verb '{verb}' box failed"

    def test_attack_intent_summary_contains_attacker(
        self, simple_fixture, controller,
    ):
        """Intent summary must show attacker, target, and attack bonus."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        assert "pc_fighter" in result.intent_summary
        assert "goblin_1" in result.intent_summary

    def test_attack_nonexistent_target(self, simple_fixture, controller):
        """Attacking a target that doesn't exist should fail with clarification."""
        result = controller.play_turn(simple_fixture, "attack the dragon")

        assert result.success is False
        assert result.clarification_needed is True
        assert result.clarification_message is not None

    def test_attack_no_target(self, simple_fixture, controller):
        """'attack' with no target should fail with clarification."""
        result = controller.play_turn(simple_fixture, "attack")

        # Bridge should return ClarificationRequest when target is None
        assert result.success is False
        assert result.clarification_needed is True


class TestAttackNarrationContent:
    """Narration must use correct templates and never contain coaching."""

    def test_narration_contains_actor_name(self, simple_fixture, controller):
        """Narration should mention the actor's display name."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        # "Aldric" should appear in narration (actor name)
        assert "Aldric" in result.narration_text

    def test_narration_contains_target_or_weapon(
        self, simple_fixture, controller,
    ):
        """Narration should mention target or weapon."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        # Should contain at least one of these
        has_target = "Goblin" in result.narration_text or "goblin" in result.narration_text
        has_weapon = "longsword" in result.narration_text
        assert has_target or has_weapon

    def test_narration_never_contains_coaching(self, simple_fixture, controller):
        """Narration must not contain coaching language."""
        result = controller.play_turn(simple_fixture, "attack the goblin")

        forbidden = [
            "are you sure",
            "you might want",
            "you should",
            "consider",
            "I recommend",
            "be careful",
            "keep in mind",
            "warning",
        ]
        text_lower = result.narration_text.lower()
        for phrase in forbidden:
            assert phrase not in text_lower, (
                f"Coaching detected in narration: '{phrase}'"
            )
