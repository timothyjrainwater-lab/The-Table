"""Tests for ClarificationLoop max_rounds enforcement.

Contract §4.6: After max_rounds failed clarifications, intent is RETRACTED.
WO-BUGFIX-BATCH-001 Deliverable 2.
"""

import pytest

from aidm.immersion.voice_intent_parser import ParseResult
from aidm.immersion.clarification_loop import ClarificationLoop
from aidm.schemas.intents import DeclaredAttackIntent


def _ambiguous_parse():
    """Create a ParseResult that needs clarification."""
    return ParseResult(
        intent=DeclaredAttackIntent(target_ref="goblin"),
        confidence=0.5,
        ambiguous_target=True,
    )


def _resolved_parse():
    """Create a ParseResult that does NOT need clarification."""
    return ParseResult(
        intent=DeclaredAttackIntent(target_ref="Goblin Warrior"),
        confidence=1.0,
    )


class TestClarificationLoopMaxRounds:
    """ClarificationLoop respects max_rounds and returns RETRACTED."""

    def test_default_max_rounds_is_3(self):
        loop = ClarificationLoop()
        assert loop.max_rounds == 3

    def test_custom_max_rounds(self):
        loop = ClarificationLoop(max_rounds=5)
        assert loop.max_rounds == 5

    def test_resolved_on_first_attempt(self):
        loop = ClarificationLoop()
        result = loop.attempt(_resolved_parse())
        assert result.resolved is True
        assert result.retracted is False
        assert result.round_number == 1

    def test_clarification_returned_within_limit(self):
        loop = ClarificationLoop(max_rounds=3)
        result = loop.attempt(_ambiguous_parse())
        assert result.resolved is False
        assert result.retracted is False
        assert result.clarification is not None
        assert result.round_number == 1

    def test_retracted_after_max_rounds(self):
        """After 3 failed clarifications, intent is RETRACTED."""
        loop = ClarificationLoop(max_rounds=3)

        for i in range(3):
            result = loop.attempt(_ambiguous_parse())
            assert result.retracted is False, f"Retracted too early at round {i+1}"
            assert result.clarification is not None

        # 4th attempt exceeds max_rounds → RETRACTED
        result = loop.attempt(_ambiguous_parse())
        assert result.retracted is True
        assert result.resolved is False
        assert result.round_number == 4

    def test_retracted_after_max_rounds_1(self):
        """max_rounds=1 means retracted on second attempt."""
        loop = ClarificationLoop(max_rounds=1)

        result = loop.attempt(_ambiguous_parse())
        assert result.retracted is False

        result = loop.attempt(_ambiguous_parse())
        assert result.retracted is True

    def test_resolved_before_max_rounds(self):
        """If resolved before max_rounds, no retraction."""
        loop = ClarificationLoop(max_rounds=3)

        loop.attempt(_ambiguous_parse())
        loop.attempt(_ambiguous_parse())

        # Third attempt resolves
        result = loop.attempt(_resolved_parse())
        assert result.resolved is True
        assert result.retracted is False

    def test_reset_clears_round_count(self):
        loop = ClarificationLoop(max_rounds=3)
        loop.attempt(_ambiguous_parse())
        loop.attempt(_ambiguous_parse())
        assert loop.round_count == 2

        loop.reset()
        assert loop.round_count == 0

    def test_round_count_tracks_attempts(self):
        loop = ClarificationLoop(max_rounds=5)
        for i in range(4):
            loop.attempt(_ambiguous_parse())
        assert loop.round_count == 4
