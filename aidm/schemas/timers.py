"""Timer and deadline schemas for time-sensitive events.

Defines deadlines, timer status tracking, and validation.
NO EVALUATION ENGINE - schema only.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Literal, Optional


# Type alias for visibility levels
DeadlineVisibility = Literal["hidden", "hinted", "explicit"]


@dataclass
class Deadline:
    """
    Time-sensitive event with consequences.

    Represents a deadline that triggers consequences when expired.
    """

    id: str
    """Unique identifier for this deadline."""

    name: str
    """Human-readable name (e.g., 'Ritual completes', 'Guards arrive')."""

    due_at_t_seconds: int
    """Absolute time when deadline expires (campaign clock time)."""

    failure_consequence: str
    """Short description of what happens if deadline missed (not narrative)."""

    visibility: DeadlineVisibility
    """How visible this deadline is to players."""

    citations: List[Dict[str, Any]] = field(default_factory=list)
    """Optional citations for deadline rules/consequences."""

    def __post_init__(self):
        """Validate deadline fields."""
        if not self.id:
            raise ValueError("Deadline id cannot be empty")

        if not self.name:
            raise ValueError("Deadline name cannot be empty")

        if self.due_at_t_seconds < 0:
            raise ValueError(f"due_at_t_seconds must be >= 0, got {self.due_at_t_seconds}")

        valid_visibility = ["hidden", "hinted", "explicit"]
        if self.visibility not in valid_visibility:
            raise ValueError(f"visibility must be one of {valid_visibility}, got {self.visibility}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "due_at_t_seconds": self.due_at_t_seconds,
            "failure_consequence": self.failure_consequence,
            "visibility": self.visibility
        }

        if self.citations:
            result["citations"] = self.citations

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deadline":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            due_at_t_seconds=data["due_at_t_seconds"],
            failure_consequence=data["failure_consequence"],
            visibility=data["visibility"],
            citations=data.get("citations", [])
        )


@dataclass
class TimerStatus:
    """
    Current status of a timer or deadline.

    Computed from current game clock and deadline.
    """

    remaining_seconds: int
    """Seconds remaining (can be negative if expired)."""

    is_expired: bool
    """Whether this timer has expired."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "remaining_seconds": self.remaining_seconds,
            "is_expired": self.is_expired
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimerStatus":
        """Create from dictionary."""
        return cls(
            remaining_seconds=data["remaining_seconds"],
            is_expired=data["is_expired"]
        )

    @staticmethod
    def compute(current_t_seconds: int, deadline: Deadline) -> "TimerStatus":
        """
        Compute timer status from current time and deadline.

        Args:
            current_t_seconds: Current game clock time
            deadline: Deadline to check

        Returns:
            TimerStatus with computed remaining time and expiry
        """
        remaining = deadline.due_at_t_seconds - current_t_seconds
        is_expired = remaining <= 0

        return TimerStatus(
            remaining_seconds=remaining,
            is_expired=is_expired
        )
