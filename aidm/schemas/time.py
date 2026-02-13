"""Temporal schemas for time tracking and clock management.

Defines time scales, spans, clocks, and time advancement events.
NO SIMULATION LOOP - schema only.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Literal


class TimeScale(Enum):
    """Time scale for tracking game time."""
    COMBAT_ROUND = "combat_round"
    NARRATIVE = "narrative"
    EXPLORATION = "exploration"


# Type alias for TimeScale literal values
TimeScaleLiteral = Literal["combat_round", "narrative", "exploration"]


@dataclass
class TimeSpan:
    """
    Duration of time in seconds.

    Provides deterministic representation of time durations.
    """

    seconds: int
    """Duration in seconds (>= 0)."""

    def __post_init__(self):
        """Validate time span."""
        if self.seconds < 0:
            raise ValueError(f"seconds must be >= 0, got {self.seconds}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {"seconds": self.seconds}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeSpan":
        """Create from dictionary."""
        return cls(seconds=data["seconds"])


# Common time span constants (optional helpers)
ROUND = TimeSpan(seconds=6)  # D&D 3.5e combat round
MINUTE = TimeSpan(seconds=60)
HOUR = TimeSpan(seconds=3600)
DAY = TimeSpan(seconds=86400)


@dataclass
class GameClock:
    """
    Campaign-global monotonic clock.

    Tracks absolute game time in seconds with associated time scale.
    """

    t_seconds: int
    """Absolute time in seconds (monotonic, campaign-global)."""

    scale: TimeScaleLiteral
    """Current time scale context."""

    def __post_init__(self):
        """Validate clock state."""
        if self.t_seconds < 0:
            raise ValueError(f"t_seconds must be >= 0, got {self.t_seconds}")

        # Validate scale is a valid literal
        valid_scales = ["combat_round", "narrative", "exploration"]
        if self.scale not in valid_scales:
            raise ValueError(f"scale must be one of {valid_scales}, got {self.scale}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "t_seconds": self.t_seconds,
            "scale": self.scale
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameClock":
        """Create from dictionary."""
        return cls(
            t_seconds=data["t_seconds"],
            scale=data["scale"]
        )


@dataclass
class TimeAdvanceEvent:
    """
    Event representing time advancement.

    Used in event log to track time passage with reason and scale context.
    """

    delta: TimeSpan
    """Amount of time advanced."""

    reason: str
    """Short description (e.g., 'talked_to_shopkeeper', 'traveled_overland')."""

    scale: TimeScaleLiteral
    """Time scale during advancement."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "delta": self.delta.to_dict(),
            "reason": self.reason,
            "scale": self.scale
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeAdvanceEvent":
        """Create from dictionary."""
        return cls(
            delta=TimeSpan.from_dict(data["delta"]),
            reason=data["reason"],
            scale=data["scale"]
        )
