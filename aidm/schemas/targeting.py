"""Targeting & Visibility schemas for CP-18A-T&V.

Minimal, deterministic targeting-legality kernel required to unlock spellcasting.

CP-18A-T&V SCOPE:
- Binary visibility state (visible or not)
- Line of Effect (LoE) and Line of Sight (LoS) checks
- Target legality evaluation
- Structured failure reasons

OUT OF SCOPE (Deferred):
- Concealment percentages / miss chance
- Partial cover vs soft cover math
- Invisibility state transitions
- AoE / cone / line targeting
- Flight / vertical geometry
- Reactive visibility changes
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class VisibilityBlockReason(str, Enum):
    """Reasons why targeting might be blocked.

    CP-18A-T&V contract: Every failed targeting check MUST emit exactly one primary reason.

    CANONICAL DEFINITION — all modules MUST import from here (or via visibility.py re-export).
    """

    LOS_BLOCKED = "los_blocked"
    """Line of Sight blocked by opaque terrain"""

    LOE_BLOCKED = "loe_blocked"
    """Line of Effect blocked by solid terrain"""

    OUT_OF_RANGE = "out_of_range"
    """Target exceeds maximum range"""

    NOT_IN_LINE = "not_in_line"
    """Target not in valid line (for line effects)"""

    TARGET_NOT_VISIBLE = "target_not_visible"
    """Target is not visible (general catch-all)"""

    OUT_OF_VISION_RANGE = "out_of_vision_range"
    """Target beyond vision range for current mode"""


@dataclass
class VisibilityState:
    """Deterministic, binary visibility state.

    CP-18A-T&V: No probabilistic visibility. Either visible or not.
    """

    observer_id: str
    """Entity observing"""

    target_id: str
    """Entity being observed"""

    is_visible: bool
    """True if target is visible to observer"""

    reason: Optional[VisibilityBlockReason] = None
    """If not visible, why? (for debugging/explanation)"""

    def __post_init__(self):
        """Validate visibility state."""
        if not self.observer_id:
            raise ValueError("observer_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if not self.is_visible and self.reason is None:
            raise ValueError("reason required when is_visible=False")
        if self.is_visible and self.reason is not None:
            raise ValueError("reason must be None when is_visible=True")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "observer_id": self.observer_id,
            "target_id": self.target_id,
            "is_visible": self.is_visible,
            "reason": self.reason.value if self.reason else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisibilityState":
        """Create from dictionary."""
        return cls(
            observer_id=data["observer_id"],
            target_id=data["target_id"],
            is_visible=data["is_visible"],
            reason=VisibilityBlockReason(data["reason"]) if data.get("reason") else None
        )


@dataclass
class RuleCitation:
    """PHB/DMG/MM citation for rule application."""

    source_id: str
    """Source book ID (e.g., '681f92bc94ff' for PHB)"""

    page: int
    """Page number"""

    section: Optional[str] = None
    """Optional section/subsection reference"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "page": self.page,
            "section": self.section
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleCitation":
        """Create from dictionary."""
        return cls(
            source_id=data["source_id"],
            page=data["page"],
            section=data.get("section")
        )


@dataclass
class TargetingLegalityResult:
    """Result of target legality evaluation.

    This object is event-loggable and hash-stable (deterministic).
    """

    is_legal: bool
    """True if targeting is legal"""

    failure_reason: Optional[VisibilityBlockReason] = None
    """If not legal, why? (structured, replayable)"""

    citations: List[RuleCitation] = None
    """PHB/DMG/MM citations for this ruling"""

    def __post_init__(self):
        """Validate legality result."""
        if self.citations is None:
            self.citations = []
        if not self.is_legal and self.failure_reason is None:
            raise ValueError("failure_reason required when is_legal=False")
        if self.is_legal and self.failure_reason is not None:
            raise ValueError("failure_reason must be None when is_legal=True")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_legal": self.is_legal,
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
            "citations": [c.to_dict() for c in self.citations]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TargetingLegalityResult":
        """Create from dictionary."""
        return cls(
            is_legal=data["is_legal"],
            failure_reason=VisibilityBlockReason(data["failure_reason"]) if data.get("failure_reason") else None,
            citations=[RuleCitation.from_dict(c) for c in data.get("citations", [])]
        )


@dataclass
class GridPoint:
    """2D grid position (used for LoS/LoE calculations).

    Note: This is a minimal representation. Full spatial system deferred to CP-19+.
    """

    x: int
    y: int

    def __post_init__(self):
        """Validate grid point."""
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise ValueError("x and y must be integers")

    def distance_to(self, other: "GridPoint") -> int:
        """Calculate grid distance using CP-14 diagonal constraints.

        PHB p. 148: First diagonal is 5 ft, second is 10 ft, repeat (1-2-1-2 pattern).
        """
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)

        # Diagonal distance: max(dx, dy) + min(dx, dy) // 2
        # This implements the 1-2-1-2 diagonal pattern
        diagonals = min(dx, dy)
        straights = max(dx, dy) - diagonals

        # Cost: diagonals at 1.5 average (1-2-1-2), straights at 1
        # For integer grid: diagonals count as (diagonals + diagonals // 2)
        return straights + diagonals + (diagonals // 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridPoint":
        """Create from dictionary."""
        return cls(x=data["x"], y=data["y"])
