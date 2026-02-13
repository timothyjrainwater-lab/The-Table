"""WO-CODE-LOOP-001: No-coaching clarification prompt tests.

Verifies that:
  - Clarification prompts contain ONLY neutral reference resolution questions
  - No tactical hints, warnings, recommendations, or mechanical disclosures
  - Forbidden phrases from INTENT_BRIDGE.md Section 4.3 are absent
"""

import re
import pytest

from aidm.core.event_log import EventLog
from aidm.runtime.play_controller import (
    PlayOneTurnController,
    ScenarioFixture,
)

# ─── Forbidden phrase patterns (from INTENT_BRIDGE.md §4.3, FC-001..FC-010) ──

FORBIDDEN_PATTERNS = [
    # FC-001: "Are you sure" coaching
    re.compile(r"(?i)\bare\s+you\s+sure\b"),
    # FC-002: AoO warning
    re.compile(r"(?i)\b(attack\s+of\s+opportunity|provoke|AoO)\b"),
    # FC-003: Tactical suggestion
    re.compile(
        r"(?i)\b(you\s+might\s+want|you\s+should|consider|I\s+recommend"
        r"|the\s+better\s+option|you\s+could\s+try|a\s+better\s+choice)\b"
    ),
    # FC-004: Negative judgment
    re.compile(
        r"(?i)\b(not\s+a\s+good\s+idea|bad\s+idea|risky|dangerous\s+move|unwise)\b"
    ),
    # FC-005: HP/AC/Save DC disclosure
    re.compile(
        r"(?i)\b\d+\s*(hit\s*points?|hp|AC|armor\s*class|DC|save\s*DC)\b"
    ),
    # FC-006: Generic mechanical disclosure
    re.compile(
        r"(?i)\b(has\s+resistance|has\s+immunity|is\s+vulnerable"
        r"|damage\s+reduction|spell\s+resistance|SR\s+\d+)\b"
    ),
    # FC-008: System-language framing
    re.compile(r"(?i)^(Warning|Caution|Error|Notice|Alert|System):"),
    # FC-009: Pre-emptive coaching
    re.compile(
        r"(?i)\b(keep\s+in\s+mind|be\s+aware|note\s+that"
        r"|remember\s+that|don't\s+forget)\b"
    ),
    # FC-010: Modifier/bonus disclosure
    re.compile(
        r"(?i)\b(attack\s+bonus|damage\s+bonus|modifier"
        r"|saving\s+throw|BAB|base\s+attack)\b"
    ),
]


def assert_no_coaching(text: str, context: str = "") -> None:
    """Assert that text contains none of the forbidden coaching patterns."""
    for pattern in FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        assert match is None, (
            f"Coaching detected{' in ' + context if context else ''}: "
            f"matched pattern {pattern.pattern!r} → {match.group(0)!r} "
            f"in text: {text!r}"
        )


class TestClarificationNoCoaching:
    """All clarification prompts must be neutral reference resolution."""

    def test_ambiguous_target_no_coaching(self, multi_goblin_fixture):
        """When multiple goblins match, clarification must be neutral."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(multi_goblin_fixture, "attack the goblin")

        assert result.clarification_needed is True
        assert result.clarification_message is not None

        assert_no_coaching(
            result.clarification_message,
            "ambiguous target clarification",
        )

    def test_unknown_target_no_coaching(self, simple_fixture):
        """When target doesn't exist, clarification must be neutral."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(simple_fixture, "attack the dragon")

        assert result.clarification_needed is True
        assert result.clarification_message is not None

        assert_no_coaching(
            result.clarification_message,
            "unknown target clarification",
        )

    def test_missing_target_no_coaching(self, simple_fixture):
        """When no target specified, clarification must be neutral."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(simple_fixture, "attack")

        assert result.clarification_needed is True
        assert result.clarification_message is not None

        assert_no_coaching(
            result.clarification_message,
            "missing target clarification",
        )

    def test_missing_move_destination_no_coaching(self, simple_fixture):
        """When no move destination, clarification must be neutral."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(simple_fixture, "move")

        assert result.clarification_needed is True
        assert result.clarification_message is not None

        assert_no_coaching(
            result.clarification_message,
            "missing destination clarification",
        )

    def test_candidates_contain_no_mechanical_info(self, multi_goblin_fixture):
        """Clarification candidates must not leak HP, AC, etc."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(multi_goblin_fixture, "attack the goblin")

        assert result.clarification_candidates is not None
        for candidate in result.clarification_candidates:
            assert_no_coaching(candidate, f"candidate '{candidate}'")

    def test_successful_attack_narration_no_coaching(
        self, simple_fixture,
    ):
        """Even successful attack narration must not coach."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(simple_fixture, "attack the goblin")

        assert result.narration_text
        assert_no_coaching(
            result.narration_text, "attack narration",
        )

    def test_move_narration_no_coaching(self, move_fixture):
        """Movement narration must not coach."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(move_fixture, "move 4 4")

        assert result.narration_text
        assert_no_coaching(result.narration_text, "move narration")


class TestClarificationContent:
    """Clarification prompts must contain useful disambiguation info."""

    def test_ambiguous_target_lists_candidates(self, multi_goblin_fixture):
        """When multiple goblins match, candidates must be listed."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(multi_goblin_fixture, "attack the goblin")

        assert result.clarification_candidates is not None
        assert len(result.clarification_candidates) >= 2

    def test_unknown_target_lists_available(self, simple_fixture):
        """When target not found, available entities should be listed."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(simple_fixture, "attack the dragon")

        assert result.clarification_candidates is not None
        # Should list available targets (Goblin Warrior)
        assert len(result.clarification_candidates) >= 1
