"""Engine Result schema for M1 runtime.

Implements the IPC_CONTRACT.md Section 3.4 Engine (Resolver) output:
- EngineResult is the authoritative mechanical outcome
- Captures all events, state changes, and resolution data
- Immutable once created (no modifications allowed)

Reference: docs/runtime/IPC_CONTRACT.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class EngineResultStatus(Enum):
    """Status of engine resolution.

    SUCCESS: Intent resolved without errors
    FAILURE: Intent could not be resolved (validation failed, target invalid, etc.)
    ABORTED: Resolution started but was interrupted (e.g., AoO defeated actor)
    """

    SUCCESS = "success"
    FAILURE = "failure"
    ABORTED = "aborted"


@dataclass
class RollResult:
    """Individual dice roll result for auditing.

    Captures RNG consumption for determinism verification.
    """

    roll_type: str
    """Type of roll: 'attack', 'd20', 'damage', 'initiative', 'skill', etc."""

    dice: str
    """Dice notation used: '1d20', '2d6+3', etc."""

    natural_roll: int
    """Raw die result before modifiers."""

    modifiers: int
    """Sum of all modifiers applied."""

    total: int
    """Final result (natural_roll + modifiers)."""

    rng_offset: int
    """RNG stream offset for replay verification."""

    context: Optional[Dict[str, Any]] = None
    """Additional context: weapon name, ability score, target AC, etc."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "roll_type": self.roll_type,
            "dice": self.dice,
            "natural_roll": self.natural_roll,
            "modifiers": self.modifiers,
            "total": self.total,
            "rng_offset": self.rng_offset,
        }
        if self.context:
            result["context"] = self.context
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollResult":
        """Create from dictionary."""
        return cls(
            roll_type=data["roll_type"],
            dice=data["dice"],
            natural_roll=data["natural_roll"],
            modifiers=data["modifiers"],
            total=data["total"],
            rng_offset=data["rng_offset"],
            context=data.get("context"),
        )


@dataclass
class StateChange:
    """Single state change for event sourcing.

    Represents an atomic change to world state.
    """

    entity_id: str
    """Entity affected by the change."""

    field: str
    """Field that was changed."""

    old_value: Any
    """Value before change (None if new field)."""

    new_value: Any
    """Value after change."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateChange":
        """Create from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            field=data["field"],
            old_value=data["old_value"],
            new_value=data["new_value"],
        )


@dataclass
class EngineResult:
    """Authoritative result of intent resolution.

    Per IPC_CONTRACT.md:
    - Engine is SOLE mechanical authority
    - EngineResult cannot be overridden by any component
    - Must produce identical results for same inputs (determinism)

    This object is immutable after creation. All mechanical outcomes
    are final once the Engine produces this result.

    Fields:
        result_id: Unique identifier for this result
        intent_id: Reference to the intent that was resolved
        status: Resolution status (SUCCESS, FAILURE, ABORTED)
        resolved_at: Timestamp of resolution
        events: List of event payloads emitted during resolution
        rolls: All dice rolls consumed (for replay verification)
        state_changes: Atomic state changes applied
        rng_final_offset: Final RNG offset after all rolls
        narration_token: Token for narrator layer (non-authoritative)
        failure_reason: Reason for failure (if status != SUCCESS)
        metadata: Additional resolution data
    """

    # Required fields
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent_id: str = ""
    status: EngineResultStatus = EngineResultStatus.SUCCESS
    resolved_at: datetime = field(default_factory=datetime.utcnow)

    # Resolution data
    events: List[Dict[str, Any]] = field(default_factory=list)
    rolls: List[RollResult] = field(default_factory=list)
    state_changes: List[StateChange] = field(default_factory=list)

    # RNG tracking for replay
    rng_initial_offset: int = 0
    rng_final_offset: int = 0

    # Narration support (non-authoritative)
    narration_token: Optional[str] = None

    # Failure information
    failure_reason: Optional[str] = None

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Freeze the result immediately after creation."""
        # Mark as frozen to prevent modification
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent modification after creation.

        EngineResult is immutable per IPC contract.
        """
        if getattr(self, "_frozen", False):
            raise EngineResultFrozenError(
                f"EngineResult is immutable. Cannot modify '{name}'."
            )
        object.__setattr__(self, name, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization and logging."""
        result = {
            "result_id": self.result_id,
            "intent_id": self.intent_id,
            "status": self.status.value,
            "resolved_at": self.resolved_at.isoformat(),
            "events": self.events,
            "rolls": [r.to_dict() for r in self.rolls],
            "state_changes": [sc.to_dict() for sc in self.state_changes],
            "rng_initial_offset": self.rng_initial_offset,
            "rng_final_offset": self.rng_final_offset,
        }

        if self.narration_token is not None:
            result["narration_token"] = self.narration_token
        if self.failure_reason is not None:
            result["failure_reason"] = self.failure_reason
        if self.metadata is not None:
            result["metadata"] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EngineResult":
        """Create EngineResult from dictionary.

        Note: Result is frozen immediately after creation.
        """
        # Parse datetime
        resolved_at = data.get("resolved_at")
        if isinstance(resolved_at, str):
            resolved_at = datetime.fromisoformat(resolved_at)
        elif resolved_at is None:
            resolved_at = datetime.utcnow()

        # Parse rolls
        rolls = [RollResult.from_dict(r) for r in data.get("rolls", [])]

        # Parse state changes
        state_changes = [
            StateChange.from_dict(sc) for sc in data.get("state_changes", [])
        ]

        # Parse status enum
        status = EngineResultStatus(data.get("status", "success"))

        # Temporarily disable freeze to set fields
        result = object.__new__(cls)
        object.__setattr__(result, "_frozen", False)
        object.__setattr__(result, "result_id", data.get("result_id", str(uuid.uuid4())))
        object.__setattr__(result, "intent_id", data.get("intent_id", ""))
        object.__setattr__(result, "status", status)
        object.__setattr__(result, "resolved_at", resolved_at)
        object.__setattr__(result, "events", data.get("events", []))
        object.__setattr__(result, "rolls", rolls)
        object.__setattr__(result, "state_changes", state_changes)
        object.__setattr__(result, "rng_initial_offset", data.get("rng_initial_offset", 0))
        object.__setattr__(result, "rng_final_offset", data.get("rng_final_offset", 0))
        object.__setattr__(result, "narration_token", data.get("narration_token"))
        object.__setattr__(result, "failure_reason", data.get("failure_reason"))
        object.__setattr__(result, "metadata", data.get("metadata"))
        object.__setattr__(result, "_frozen", True)

        return result


class EngineResultFrozenError(Exception):
    """Raised when attempting to modify an EngineResult."""

    pass


class EngineResultBuilder:
    """Builder for constructing EngineResult incrementally.

    Use this during resolution to accumulate events, rolls, and state changes.
    Call build() to create the final immutable EngineResult.
    """

    def __init__(self, intent_id: str, rng_offset: int = 0):
        """Initialize builder for an intent.

        Args:
            intent_id: ID of the intent being resolved
            rng_offset: Starting RNG offset
        """
        self.intent_id = intent_id
        self.events: List[Dict[str, Any]] = []
        self.rolls: List[RollResult] = []
        self.state_changes: List[StateChange] = []
        self.rng_initial_offset = rng_offset
        self.rng_current_offset = rng_offset
        self.narration_token: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self._built = False

    def add_event(self, event: Dict[str, Any]) -> "EngineResultBuilder":
        """Add an event to the result."""
        if self._built:
            raise ValueError("Cannot modify builder after build()")
        self.events.append(event)
        return self

    def add_roll(
        self,
        roll_type: str,
        dice: str,
        natural_roll: int,
        modifiers: int,
        total: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> "EngineResultBuilder":
        """Record a dice roll."""
        if self._built:
            raise ValueError("Cannot modify builder after build()")

        roll = RollResult(
            roll_type=roll_type,
            dice=dice,
            natural_roll=natural_roll,
            modifiers=modifiers,
            total=total,
            rng_offset=self.rng_current_offset,
            context=context,
        )
        self.rolls.append(roll)
        self.rng_current_offset += 1
        return self

    def add_state_change(
        self,
        entity_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
    ) -> "EngineResultBuilder":
        """Record a state change."""
        if self._built:
            raise ValueError("Cannot modify builder after build()")

        change = StateChange(
            entity_id=entity_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
        )
        self.state_changes.append(change)
        return self

    def set_narration_token(self, token: str) -> "EngineResultBuilder":
        """Set the narration token."""
        if self._built:
            raise ValueError("Cannot modify builder after build()")
        self.narration_token = token
        return self

    def add_metadata(self, key: str, value: Any) -> "EngineResultBuilder":
        """Add metadata key-value pair."""
        if self._built:
            raise ValueError("Cannot modify builder after build()")
        self.metadata[key] = value
        return self

    def build(
        self,
        status: EngineResultStatus = EngineResultStatus.SUCCESS,
        failure_reason: Optional[str] = None,
    ) -> EngineResult:
        """Build the final immutable EngineResult.

        Args:
            status: Resolution status
            failure_reason: Reason for failure (if status != SUCCESS)

        Returns:
            Immutable EngineResult
        """
        if self._built:
            raise ValueError("build() can only be called once")

        self._built = True

        # Use object.__new__ to bypass __post_init__ freeze
        result = object.__new__(EngineResult)
        object.__setattr__(result, "_frozen", False)
        object.__setattr__(result, "result_id", str(uuid.uuid4()))
        object.__setattr__(result, "intent_id", self.intent_id)
        object.__setattr__(result, "status", status)
        object.__setattr__(result, "resolved_at", datetime.utcnow())
        object.__setattr__(result, "events", self.events)
        object.__setattr__(result, "rolls", self.rolls)
        object.__setattr__(result, "state_changes", self.state_changes)
        object.__setattr__(result, "rng_initial_offset", self.rng_initial_offset)
        object.__setattr__(result, "rng_final_offset", self.rng_current_offset)
        object.__setattr__(result, "narration_token", self.narration_token)
        object.__setattr__(result, "failure_reason", failure_reason)
        object.__setattr__(result, "metadata", self.metadata if self.metadata else None)
        object.__setattr__(result, "_frozen", True)

        return result

    def build_failure(self, reason: str) -> EngineResult:
        """Build a failed EngineResult.

        Convenience method for failure cases.
        """
        return self.build(status=EngineResultStatus.FAILURE, failure_reason=reason)

    def build_aborted(self, reason: str) -> EngineResult:
        """Build an aborted EngineResult.

        Convenience method for aborted resolutions (e.g., AoO defeated actor).
        """
        return self.build(status=EngineResultStatus.ABORTED, failure_reason=reason)
