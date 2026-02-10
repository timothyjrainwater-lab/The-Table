"""Canonical 2D grid position type for AIDM.

This module provides the single source of truth for position representation
throughout the AIDM engine, consolidating three legacy position types:
- GridPoint (aidm/schemas/intents.py) - bare x/y, no methods
- GridPoint (aidm/schemas/targeting.py) - has distance_to() with 1-2-1-2 diagonal math
- GridPosition (aidm/schemas/attack.py) - has is_adjacent_to() for AoO checks

All positions are integer coordinates on a bounded 2D grid using D&D 3.5e
standard movement rules (PHB p.145, p.137, p.147).

INTRODUCED: CP-001 (Position Type Unification)
RESOLVES: TD-001 (Three Duplicate Grid Position Types)
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class Position:
    """Canonical 2D grid position type for AIDM.

    Consolidates three legacy position types:
    - GridPoint (intents.py)
    - GridPoint (targeting.py)
    - GridPosition (attack.py)

    All positions are integer coordinates on a bounded 2D grid.
    Uses 1-2-1-2 diagonal distance (PHB p.145 default, not variant).

    Immutable (frozen=True) for use in sets/dicts and to prevent accidental mutation.
    """
    x: int
    y: int

    def __post_init__(self):
        """Validate integer coordinates."""
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise TypeError(f"Position coordinates must be integers, got ({type(self.x).__name__}, {type(self.y).__name__})")

    def distance_to(self, other: 'Position') -> int:
        """Calculate distance using 1-2-1-2 diagonal movement (PHB p.148).

        D&D 3.5e default: First diagonal costs 5 feet (1 square), second diagonal
        costs 10 feet (2 squares), alternating pattern continues.

        Example: (0,0) to (3,3) = 20 feet (4 squares using 1-2-1-2)
            - First diagonal: 5 feet (1 square)
            - Second diagonal: 10 feet (2 squares)
            - Third diagonal: 5 feet (1 square)
            Total: 5 + 10 + 5 = 20 feet

        Args:
            other: Target position

        Returns:
            Distance in feet (integer multiples of 5)
        """
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)

        # 1-2-1-2 diagonal math
        # Each pair of diagonals costs 15 feet (5 + 10)
        # Remaining orthogonal movement costs 5 feet per square
        diagonals = min(dx, dy)
        orthogonal = abs(dx - dy)

        # Count diagonal pairs (each pair = 15 feet)
        diagonal_pairs = diagonals // 2
        remaining_diagonals = diagonals % 2

        return (diagonal_pairs * 15) + (remaining_diagonals * 5) + (orthogonal * 5)

    def is_adjacent_to(self, other: 'Position') -> bool:
        """Check if positions are adjacent (8-directional, 5-foot reach).

        Adjacent includes orthogonal and diagonal neighbors (PHB p.137).
        Used for AoO threat range and adjacency checks.

        Args:
            other: Target position

        Returns:
            True if positions are adjacent (distance ≤ 1 square in any direction)
        """
        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1 and self != other

    def to_dict(self) -> Dict[str, int]:
        """Serialize to dict for JSON/event storage.

        Returns:
            {"x": int, "y": int} with sorted keys for deterministic serialization
        """
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """Deserialize from dict.

        Args:
            data: Dict with 'x' and 'y' keys

        Returns:
            Position instance

        Raises:
            KeyError: If 'x' or 'y' missing from data
            TypeError: If x or y are not integers
        """
        return cls(x=data["x"], y=data["y"])

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Position(x={self.x}, y={self.y})"


# =============================================================================
# Backward Compatibility Helpers (DEPRECATED - Remove in CP-002)
# =============================================================================

def from_legacy_gridpoint_intents(gp: Any) -> Position:
    """Convert legacy GridPoint (intents.py) to Position.

    DEPRECATED: For migration only. Remove in CP-002.

    Args:
        gp: Legacy GridPoint instance with x and y attributes

    Returns:
        Position instance
    """
    return Position(x=gp.x, y=gp.y)


def from_legacy_gridpoint_targeting(gp: Any) -> Position:
    """Convert legacy GridPoint (targeting.py) to Position.

    DEPRECATED: For migration only. Remove in CP-002.

    Args:
        gp: Legacy GridPoint instance with x and y attributes

    Returns:
        Position instance
    """
    return Position(x=gp.x, y=gp.y)


def from_legacy_gridposition_attack(gpos: Any) -> Position:
    """Convert legacy GridPosition (attack.py) to Position.

    DEPRECATED: For migration only. Remove in CP-002.

    Args:
        gpos: Legacy GridPosition instance with x and y attributes

    Returns:
        Position instance
    """
    return Position(x=gpos.x, y=gpos.y)


def to_legacy_dict(pos: Position) -> Dict[str, int]:
    """Convert Position to legacy dict format {"x": int, "y": int}.

    DEPRECATED: For migration only. Remove in CP-002.

    Args:
        pos: Position instance

    Returns:
        Dict with x and y keys
    """
    return pos.to_dict()
