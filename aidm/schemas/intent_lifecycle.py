"""Intent lifecycle management for M1 runtime.

Implements the INTENT_LIFECYCLE.md contract:
- IntentStatus: PENDING → CLARIFYING → CONFIRMED → RESOLVED | RETRACTED
- IntentObject: Wraps action intents with lifecycle state

BOUNDARY LAW (BL-014): Once _frozen is set to True (on CONFIRMED), it
cannot be set back to False. Attempting to unfreeze raises IntentFrozenError.
After freeze, only resolution fields (status, result_id, resolved_at,
updated_at) may be modified.

WHY: Confirmed intents are the basis for resolution. If they can be silently
modified after confirmation, the resolution operates on different data than
what the player confirmed — this is a correctness violation.

Reference: docs/runtime/INTENT_LIFECYCLE.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from aidm.schemas.intents import (
    Intent,
    CastSpellIntent,
    MoveIntent,
    DeclaredAttackIntent,
    BuyIntent,
    RestIntent,
    GridPoint,
    parse_intent,
)
from aidm.schemas.position import Position


class IntentStatus(Enum):
    """Lifecycle states for an intent.

    Transitions:
        PENDING → CLARIFYING (missing required fields)
        PENDING → CONFIRMED (all fields valid)
        CLARIFYING → CONFIRMED (player provides missing info)
        CLARIFYING → RETRACTED (player cancels or timeout)
        CONFIRMED → RESOLVED (engine processes)

    CONFIRMED marks the IMMUTABLE BOUNDARY - no modifications after this point.
    """

    PENDING = "pending"
    CLARIFYING = "clarifying"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    RETRACTED = "retracted"


class ActionType(Enum):
    """M1 supported action types.

    Per INTENT_LIFECYCLE.md Section 5, M1 supports:
    - ATTACK: Melee or ranged attack (requires target_id, method)
    - MOVE: Movement to location (requires target_location)
    - USE_ABILITY: Use class/racial ability (requires method, parameters)
    - END_TURN: End current turn (no additional requirements)
    """

    ATTACK = "attack"
    MOVE = "move"
    USE_ABILITY = "use_ability"
    END_TURN = "end_turn"
    # Extended types (map to existing intents)
    CAST_SPELL = "cast_spell"
    BUY = "buy"
    REST = "rest"


class IntentFrozenError(Exception):
    """Raised when attempting to modify a frozen (CONFIRMED+) intent."""

    pass


class IntentTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""

    pass


@dataclass
class IntentObject:
    """Player intent with lifecycle management.

    Represents a player's declared action before mechanical resolution.
    Implements the lifecycle contract from INTENT_LIFECYCLE.md.

    Once status reaches CONFIRMED, the intent is FROZEN and cannot be modified
    except for resolution fields (result_id, resolved_at, status→RESOLVED).

    Required Fields:
        intent_id: Unique identifier (UUID)
        actor_id: Entity performing the action
        action_type: Category of action
        status: Current lifecycle state
        source_text: Original player input
        created_at: When intent was created
        updated_at: Last modification time

    Optional Fields:
        target_id: Target entity (if applicable)
        target_location: Target position (if applicable)
        method: Weapon, spell, ability used
        parameters: Additional action-specific data
        declared_goal: Narrative intent (optional)
        action_data: The underlying action intent object

    Resolution Fields (set by engine):
        result_id: Reference to EngineResult
        resolved_at: When resolution completed
    """

    # Required fields — no defaults (BL-017, BL-018: inject-only)
    intent_id: str
    actor_id: str
    action_type: ActionType
    status: IntentStatus
    source_text: str
    created_at: datetime
    updated_at: datetime

    # Optional fields
    target_id: Optional[str] = None
    target_location: Optional[Position] = None
    method: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    declared_goal: Optional[str] = None
    action_data: Optional[Intent] = None

    # Resolution fields (engine-only)
    result_id: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Internal state
    _frozen: bool = field(default=False, repr=False)

    def __setattr__(self, name: str, value: Any) -> None:
        """Enforce immutability after CONFIRMED status."""
        # Allow setting _frozen to True only (never unfreeze)
        if name == "_frozen":
            if getattr(self, "_frozen", False) and not value:
                raise IntentFrozenError(
                    "Cannot unfreeze a confirmed intent"
                )
            object.__setattr__(self, name, value)
            return

        # Check if we're frozen
        frozen = getattr(self, "_frozen", False)
        if frozen:
            # Only allow resolution fields after freeze
            allowed_after_freeze = {"status", "result_id", "resolved_at", "updated_at"}
            if name not in allowed_after_freeze:
                raise IntentFrozenError(
                    f"Cannot modify field '{name}' on frozen intent {self.intent_id}"
                )
            # Status can only go to RESOLVED after freeze
            if name == "status" and value != IntentStatus.RESOLVED:
                raise IntentFrozenError(
                    f"Frozen intent can only transition to RESOLVED, not {value}"
                )

        object.__setattr__(self, name, value)

    def freeze(self) -> None:
        """Mark intent as frozen (called when transitioning to CONFIRMED).

        After freezing, only resolution fields may be modified.
        """
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        """Check if intent is frozen (immutable)."""
        return self._frozen

    def has_required_fields(self) -> bool:
        """Check if all required fields for this action type are populated.

        Per INTENT_LIFECYCLE.md Section 5:
        - ATTACK: requires target_id, method
        - MOVE: requires target_location
        - USE_ABILITY: requires method, parameters
        - END_TURN: no additional requirements
        """
        if not self.actor_id:
            return False

        if self.action_type == ActionType.ATTACK:
            return self.target_id is not None and self.method is not None
        elif self.action_type == ActionType.MOVE:
            return self.target_location is not None
        elif self.action_type == ActionType.USE_ABILITY:
            return self.method is not None and self.parameters is not None
        elif self.action_type == ActionType.END_TURN:
            return True
        elif self.action_type == ActionType.CAST_SPELL:
            # Spell casting has target requirements based on target_mode
            if self.action_data and isinstance(self.action_data, CastSpellIntent):
                if self.action_data.requires_target_entity:
                    return self.target_id is not None
                if self.action_data.requires_point:
                    return self.target_location is not None
            return self.method is not None
        elif self.action_type in (ActionType.BUY, ActionType.REST):
            return True  # These have minimal requirements

        return True

    def is_valid(self) -> bool:
        """Validate intent data beyond required fields.

        Checks that values are sensible (non-empty strings, valid enums, etc.)
        """
        if not self.intent_id:
            return False
        if not self.source_text:
            return False
        if not isinstance(self.action_type, ActionType):
            return False
        return True

    def get_missing_fields(self) -> list[str]:
        """Return list of missing required fields for clarification."""
        missing = []

        if not self.actor_id:
            missing.append("actor_id")

        if self.action_type == ActionType.ATTACK:
            if self.target_id is None:
                missing.append("target_id")
            if self.method is None:
                missing.append("method")
        elif self.action_type == ActionType.MOVE:
            if self.target_location is None:
                missing.append("target_location")
        elif self.action_type == ActionType.USE_ABILITY:
            if self.method is None:
                missing.append("method")
            if self.parameters is None:
                missing.append("parameters")
        elif self.action_type == ActionType.CAST_SPELL:
            if self.action_data and isinstance(self.action_data, CastSpellIntent):
                if self.action_data.requires_target_entity and self.target_id is None:
                    missing.append("target_id")
                if self.action_data.requires_point and self.target_location is None:
                    missing.append("target_location")
            elif self.method is None:
                missing.append("method")

        return missing

    def transition_to(self, new_status: IntentStatus, timestamp: datetime) -> None:
        """Attempt to transition to a new status.

        Validates transition is legal per lifecycle rules:
        - PENDING -> CLARIFYING, CONFIRMED
        - PENDING -> CLARIFYING, CONFIRMED, RETRACTED
        - CLARIFYING -> CONFIRMED, RETRACTED
        - CONFIRMED -> RESOLVED (only)
        - RESOLVED, RETRACTED are terminal

        Args:
            new_status: The status to transition to
            timestamp: Timestamp for this transition (BL-018: must be injected)

        Raises:
            IntentTransitionError: If transition is not allowed
            IntentFrozenError: If intent is frozen and transition is invalid
        """
        valid_transitions = {
            IntentStatus.PENDING: {IntentStatus.CLARIFYING, IntentStatus.CONFIRMED, IntentStatus.RETRACTED},
            IntentStatus.CLARIFYING: {IntentStatus.CONFIRMED, IntentStatus.RETRACTED},
            IntentStatus.CONFIRMED: {IntentStatus.RESOLVED},
            IntentStatus.RESOLVED: set(),  # Terminal
            IntentStatus.RETRACTED: set(),  # Terminal
        }

        if new_status not in valid_transitions.get(self.status, set()):
            raise IntentTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )

        # Set status first, then freeze (order matters for __setattr__ check)
        self.status = new_status
        self.updated_at = timestamp

        # Freeze after CONFIRMED status is set
        if new_status == IntentStatus.CONFIRMED:
            self.freeze()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization and logging."""
        result = {
            "intent_id": self.intent_id,
            "actor_id": self.actor_id,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "source_text": self.source_text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if self.target_id is not None:
            result["target_id"] = self.target_id
        if self.target_location is not None:
            result["target_location"] = self.target_location.to_dict()
        if self.method is not None:
            result["method"] = self.method
        if self.parameters is not None:
            result["parameters"] = self.parameters
        if self.declared_goal is not None:
            result["declared_goal"] = self.declared_goal
        if self.action_data is not None:
            result["action_data"] = self.action_data.to_dict()
        if self.result_id is not None:
            result["result_id"] = self.result_id
        if self.resolved_at is not None:
            result["resolved_at"] = self.resolved_at.isoformat()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntentObject":
        """Create IntentObject from dictionary.

        Note: Frozen state is restored based on status (CONFIRMED+ means frozen).
        All required fields (intent_id, created_at, updated_at) must be present
        in the data — no fallback generation (BL-017, BL-018).
        """
        # Parse datetime fields — must be present
        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        resolved_at = data.get("resolved_at")
        if isinstance(resolved_at, str):
            resolved_at = datetime.fromisoformat(resolved_at)

        # Parse target_location if present
        target_location = None
        if "target_location" in data and data["target_location"] is not None:
            target_location = Position.from_dict(data["target_location"])

        # Parse action_data if present
        action_data = None
        if "action_data" in data and data["action_data"] is not None:
            action_data = parse_intent(data["action_data"])

        # Parse enums
        status = IntentStatus(data["status"])
        action_type = ActionType(data["action_type"])

        intent = cls(
            intent_id=data["intent_id"],
            actor_id=data.get("actor_id", ""),
            action_type=action_type,
            status=status,
            source_text=data.get("source_text", ""),
            created_at=created_at,
            updated_at=updated_at,
            target_id=data.get("target_id"),
            target_location=target_location,
            method=data.get("method"),
            parameters=data.get("parameters"),
            declared_goal=data.get("declared_goal"),
            action_data=action_data,
            result_id=data.get("result_id"),
            resolved_at=resolved_at,
        )

        # Restore frozen state for CONFIRMED+ intents
        if status in (IntentStatus.CONFIRMED, IntentStatus.RESOLVED):
            intent._frozen = True

        return intent


def create_intent_from_input(
    actor_id: str,
    source_text: str,
    action_type: ActionType,
    intent_id: str,
    created_at: datetime,
    **kwargs: Any,
) -> IntentObject:
    """Factory function to create a new IntentObject from player input.

    Args:
        actor_id: The entity performing the action
        source_text: Original player input text
        action_type: Category of action
        intent_id: Unique identifier (BL-017: must be injected)
        created_at: Timestamp for creation (BL-018: must be injected)
        **kwargs: Additional fields (target_id, method, etc.)

    Returns:
        New IntentObject in PENDING status
    """
    return IntentObject(
        intent_id=intent_id,
        actor_id=actor_id,
        source_text=source_text,
        action_type=action_type,
        status=IntentStatus.PENDING,
        created_at=created_at,
        updated_at=created_at,
        **kwargs,
    )
