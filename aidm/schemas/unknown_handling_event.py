"""Unknown Handling Event schema for structured logging.

WO-VOICE-UK-LOG-001: Structured logging for the unknown handling pipeline.
Every STOPLIGHT classification, clarification round, escalation, and
cancellation produces an UnknownHandlingEvent.

Source contract: docs/contracts/UNKNOWN_HANDLING_CONTRACT.md (Tier 1.2 — frozen)
"""

from dataclasses import dataclass
from typing import Optional


# Valid event types
VALID_EVENT_TYPES = frozenset({
    "classification",
    "clarification_round",
    "escalation",
    "cancellation",
})

# Valid failure classes from the Unknown Handling Contract (7 classes + None for GREEN)
VALID_FAILURE_CLASSES = frozenset({
    "FC-ASR",
    "FC-HOMO",
    "FC-PARTIAL",
    "FC-TIMING",
    "FC-AMBIG",
    "FC-OOG",
    "FC-BLEED",
})

# Valid STOPLIGHT colors
VALID_STOPLIGHTS = frozenset({"GREEN", "YELLOW", "RED"})

# Valid resolution states
VALID_RESOLUTIONS = frozenset({
    "handled",
    "clarified",
    "escalated_to_menu",
    "cancelled",
    "pending",
})


@dataclass(frozen=True)
class UnknownHandlingEvent:
    """Structured log event for the unknown handling pipeline.

    Emitted whenever a voice input is classified, a clarification round
    occurs, an escalation fires, or a cancellation happens. Frozen for
    determinism and auditability.

    Attributes:
        event_type: "classification" | "clarification_round" | "escalation" | "cancellation"
        failure_class: FC-ASR through FC-BLEED, or None for GREEN classification
        sub_class: e.g. FC-ASR-01, FC-AMBIG-06 — finer grain when available
        stoplight: "GREEN" | "YELLOW" | "RED"
        clarification_round: 0-based round counter (0 = first attempt)
        max_clarifications: Budget ceiling (default 2, configurable 1-3)
        resolution: "handled" | "clarified" | "escalated_to_menu" | "cancelled" | "pending"
        missing_attribute: For FORBIDDEN_DEFAULT detection (e.g. "size", "position")
        turn_number: Current game turn
        correlation_id: UUID linking to related boundary pressure events
        timestamp: ISO 8601 timestamp
    """

    event_type: str
    failure_class: Optional[str]
    sub_class: Optional[str]
    stoplight: str
    clarification_round: int
    max_clarifications: int
    resolution: str
    missing_attribute: Optional[str]
    turn_number: int
    correlation_id: str
    timestamp: str

    def __post_init__(self):
        """Validate field values at construction time."""
        if self.event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{self.event_type}'. "
                f"Must be one of: {sorted(VALID_EVENT_TYPES)}"
            )
        if self.failure_class is not None and self.failure_class not in VALID_FAILURE_CLASSES:
            raise ValueError(
                f"Invalid failure_class '{self.failure_class}'. "
                f"Must be one of: {sorted(VALID_FAILURE_CLASSES)} or None"
            )
        if self.stoplight not in VALID_STOPLIGHTS:
            raise ValueError(
                f"Invalid stoplight '{self.stoplight}'. "
                f"Must be one of: {sorted(VALID_STOPLIGHTS)}"
            )
        if self.resolution not in VALID_RESOLUTIONS:
            raise ValueError(
                f"Invalid resolution '{self.resolution}'. "
                f"Must be one of: {sorted(VALID_RESOLUTIONS)}"
            )
        if not isinstance(self.clarification_round, int) or self.clarification_round < 0:
            raise ValueError(
                f"clarification_round must be a non-negative int, got {self.clarification_round}"
            )
        if not isinstance(self.max_clarifications, int) or not (1 <= self.max_clarifications <= 3):
            raise ValueError(
                f"max_clarifications must be 1-3, got {self.max_clarifications}"
            )

    def to_dict(self) -> dict:
        """Serialize to dictionary for structured logging output."""
        return {
            "event_type": self.event_type,
            "failure_class": self.failure_class,
            "sub_class": self.sub_class,
            "stoplight": self.stoplight,
            "clarification_round": self.clarification_round,
            "max_clarifications": self.max_clarifications,
            "resolution": self.resolution,
            "missing_attribute": self.missing_attribute,
            "turn_number": self.turn_number,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }
