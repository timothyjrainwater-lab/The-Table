"""Effect duration schemas for tracking spell/buff/debuff durations.

Defines duration units, effect durations, and deterministic tracking.
NO SPELL RESOLVER - schema only.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Literal, Optional


# Type alias for duration units
DurationUnit = Literal["rounds", "minutes", "hours", "days", "until_discharged", "permanent"]


@dataclass
class EffectDuration:
    """
    Duration tracking for spells, buffs, debuffs, and other timed effects.

    Provides deterministic structure for effect lifetime tracking.
    """

    unit: DurationUnit
    """Duration unit (rounds, minutes, hours, days, until_discharged, permanent)."""

    value: Optional[int]
    """Duration value (None for until_discharged/permanent)."""

    start_t_seconds: int
    """Game clock time when effect started (for deterministic tracking)."""

    ends_at_t_seconds: Optional[int] = None
    """Computed end time (None for until_discharged/permanent)."""

    citation: Optional[Dict[str, Any]] = None
    """Optional citation for effect duration rules."""

    def __post_init__(self):
        """Validate effect duration fields."""
        valid_units = ["rounds", "minutes", "hours", "days", "until_discharged", "permanent"]
        if self.unit not in valid_units:
            raise ValueError(f"unit must be one of {valid_units}, got {self.unit}")

        # Value must be positive if unit is time-based
        if self.unit in ["rounds", "minutes", "hours", "days"]:
            if self.value is None:
                raise ValueError(f"value required for unit '{self.unit}'")
            if self.value < 1:
                raise ValueError(f"value must be >= 1 for unit '{self.unit}', got {self.value}")
        else:
            # until_discharged and permanent don't use value
            if self.value is not None:
                raise ValueError(f"value must be None for unit '{self.unit}'")

        if self.start_t_seconds < 0:
            raise ValueError(f"start_t_seconds must be >= 0, got {self.start_t_seconds}")

        # If ends_at_t_seconds is set, it must be >= start_t_seconds
        if self.ends_at_t_seconds is not None:
            if self.ends_at_t_seconds < self.start_t_seconds:
                raise ValueError(
                    f"ends_at_t_seconds ({self.ends_at_t_seconds}) must be >= "
                    f"start_t_seconds ({self.start_t_seconds})"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "unit": self.unit,
            "value": self.value,
            "start_t_seconds": self.start_t_seconds
        }

        if self.ends_at_t_seconds is not None:
            result["ends_at_t_seconds"] = self.ends_at_t_seconds

        if self.citation is not None:
            result["citation"] = self.citation

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EffectDuration":
        """Create from dictionary."""
        return cls(
            unit=data["unit"],
            value=data["value"],
            start_t_seconds=data["start_t_seconds"],
            ends_at_t_seconds=data.get("ends_at_t_seconds"),
            citation=data.get("citation")
        )

    @staticmethod
    def compute_end_time(start_t_seconds: int, unit: DurationUnit, value: int) -> Optional[int]:
        """
        Compute end time from start time, unit, and value.

        Args:
            start_t_seconds: Start time in seconds
            unit: Duration unit
            value: Duration value

        Returns:
            End time in seconds, or None for until_discharged/permanent
        """
        if unit == "rounds":
            # D&D 3.5e: 1 round = 6 seconds
            return start_t_seconds + (value * 6)
        elif unit == "minutes":
            return start_t_seconds + (value * 60)
        elif unit == "hours":
            return start_t_seconds + (value * 3600)
        elif unit == "days":
            return start_t_seconds + (value * 86400)
        else:
            # until_discharged, permanent
            return None
