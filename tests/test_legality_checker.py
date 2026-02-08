"""Tests for legality checker."""

import pytest
from aidm.core.state import WorldState
from aidm.rules.legality_checker import check, LegalResult, ReasonCode


def test_missing_mover_id_is_illegal():
    """Move intent without mover_id should be illegal with missing_state."""
    state = WorldState(ruleset_version="dnd3.5", entities={})

    intent = {"type": "move", "path": [[1, 2]]}

    result = check(state, intent)

    assert result.is_legal is False
    assert result.reason_code == ReasonCode.MISSING_STATE
    assert "mover_id" in result.details


def test_missing_path_is_illegal():
    """Move intent without path should be illegal with missing_state."""
    state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"x": 0, "y": 0}},
    )

    intent = {"type": "move", "mover_id": "player1"}

    result = check(state, intent)

    assert result.is_legal is False
    assert result.reason_code == ReasonCode.MISSING_STATE
    assert "path" in result.details


def test_empty_path_is_illegal():
    """Move intent with empty path should be illegal with path_illegal."""
    state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"x": 0, "y": 0}},
    )

    intent = {"type": "move", "mover_id": "player1", "path": []}

    result = check(state, intent)

    assert result.is_legal is False
    assert result.reason_code == ReasonCode.PATH_ILLEGAL
    assert "empty" in result.details


def test_valid_move_is_legal():
    """Valid move intent should be legal."""
    state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"x": 0, "y": 0}},
    )

    intent = {"type": "move", "mover_id": "player1", "path": [[1, 0], [2, 0]]}

    result = check(state, intent)

    assert result.is_legal is True
    assert result.reason_code is None


def test_mover_not_found_is_illegal():
    """Move intent with non-existent mover should be illegal."""
    state = WorldState(ruleset_version="dnd3.5", entities={})

    intent = {"type": "move", "mover_id": "ghost", "path": [[1, 0]]}

    result = check(state, intent)

    assert result.is_legal is False
    assert result.reason_code == ReasonCode.ENTITY_NOT_FOUND
    assert "ghost" in result.details


def test_no_action_slot_is_illegal():
    """Move intent when mover has no action slots should be illegal."""
    state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"x": 0, "y": 0, "actions_remaining": 0}},
    )

    intent = {"type": "move", "mover_id": "player1", "path": [[1, 0]]}

    result = check(state, intent)

    assert result.is_legal is False
    assert result.reason_code == ReasonCode.NO_ACTION_SLOT
    assert "player1" in result.details


def test_action_slot_available_is_legal():
    """Move intent when mover has action slots should be legal."""
    state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"x": 0, "y": 0, "actions_remaining": 1}},
    )

    intent = {"type": "move", "mover_id": "player1", "path": [[1, 0]]}

    result = check(state, intent)

    assert result.is_legal is True


def test_missing_intent_type_is_illegal():
    """Intent without type field should be illegal."""
    state = WorldState(ruleset_version="dnd3.5", entities={})

    intent = {"mover_id": "player1", "path": [[1, 0]]}

    result = check(state, intent)

    assert result.is_legal is False
    assert result.reason_code == ReasonCode.INVALID_INTENT


def test_unknown_intent_type_is_illegal():
    """Unknown intent types should be illegal (fail-closed)."""
    state = WorldState(ruleset_version="dnd3.5", entities={})

    intent = {"type": "teleport", "target": [10, 10]}

    result = check(state, intent)

    assert result.is_legal is False
    assert result.reason_code == ReasonCode.INVALID_INTENT
    assert "teleport" in result.details


def test_legal_result_helpers():
    """LegalResult static helpers should work correctly."""
    legal = LegalResult.legal()
    assert legal.is_legal is True
    assert legal.reason_code is None

    illegal = LegalResult.illegal(ReasonCode.PATH_ILLEGAL, "test details")
    assert illegal.is_legal is False
    assert illegal.reason_code == ReasonCode.PATH_ILLEGAL
    assert illegal.details == "test details"


def test_legality_emits_structured_reasons_not_prose():
    """Legality check should emit structured reason codes, not prose."""
    state = WorldState(ruleset_version="dnd3.5", entities={})

    intent = {"type": "move", "mover_id": "player1", "path": []}

    result = check(state, intent)

    # Should have a reason_code enum, not just a text description
    assert isinstance(result.reason_code, ReasonCode)
    assert result.reason_code in [
        ReasonCode.MISSING_STATE,
        ReasonCode.PATH_ILLEGAL,
        ReasonCode.NO_ACTION_SLOT,
        ReasonCode.ENTITY_NOT_FOUND,
        ReasonCode.INVALID_INTENT,
    ]
