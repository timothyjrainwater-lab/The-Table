"""Legality checker - FIRST engine gate for validating intents."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

from aidm.core.state import WorldState


class ReasonCode(Enum):
    """Structured reason codes for legality check failures."""

    MISSING_STATE = "missing_state"
    PATH_ILLEGAL = "path_illegal"
    NO_ACTION_SLOT = "no_action_slot"
    ENTITY_NOT_FOUND = "entity_not_found"
    INVALID_INTENT = "invalid_intent"


@dataclass
class LegalResult:
    """Result of legality check with structured reason."""

    is_legal: bool
    reason_code: Optional[ReasonCode] = None
    details: str = ""

    @staticmethod
    def legal() -> "LegalResult":
        """Create a legal result."""
        return LegalResult(is_legal=True)

    @staticmethod
    def illegal(reason_code: ReasonCode, details: str = "") -> "LegalResult":
        """Create an illegal result with reason."""
        return LegalResult(is_legal=False, reason_code=reason_code, details=details)


def check(world_state: WorldState, intent: Dict[str, Any]) -> LegalResult:
    """
    Check if an intent is legal given current world state.

    Fail-closed: missing required fields or state returns illegal with missing_state.

    Currently supports:
    - move intents: requires path, mover_id, validates action slot availability

    Args:
        world_state: Current world state
        intent: Intent dictionary with type and parameters

    Returns:
        LegalResult indicating legality and reason if illegal
    """
    # Validate intent has required type field
    if "type" not in intent:
        return LegalResult.illegal(
            ReasonCode.INVALID_INTENT, "Intent missing 'type' field"
        )

    intent_type = intent["type"]

    if intent_type == "move":
        return _check_move_intent(world_state, intent)

    # Unknown intent types are illegal (fail-closed)
    return LegalResult.illegal(
        ReasonCode.INVALID_INTENT, f"Unknown intent type: {intent_type}"
    )


def _check_move_intent(world_state: WorldState, intent: Dict[str, Any]) -> LegalResult:
    """Check legality of a move intent."""
    # Required fields
    mover_id = intent.get("mover_id")
    path = intent.get("path")

    # Fail-closed: missing required fields
    if not mover_id:
        return LegalResult.illegal(
            ReasonCode.MISSING_STATE, "Move intent missing 'mover_id'"
        )

    if path is None:
        return LegalResult.illegal(
            ReasonCode.MISSING_STATE, "Move intent missing 'path'"
        )

    # Check mover entity exists
    if mover_id not in world_state.entities:
        return LegalResult.illegal(
            ReasonCode.ENTITY_NOT_FOUND, f"Mover entity '{mover_id}' not found"
        )

    # Check path is non-empty
    if not path or len(path) == 0:
        return LegalResult.illegal(
            ReasonCode.PATH_ILLEGAL, "Movement path cannot be empty"
        )

    # Check action slot available
    mover = world_state.entities[mover_id]

    # If entity has action tracking and no actions remaining, illegal
    if "actions_remaining" in mover:
        if mover["actions_remaining"] <= 0:
            return LegalResult.illegal(
                ReasonCode.NO_ACTION_SLOT,
                f"Mover '{mover_id}' has no action slots remaining",
            )

    # All checks passed
    return LegalResult.legal()
