"""Attack resolution schemas for CP-10.

Data-only contracts for attack intent and weapon definitions.
NO RESOLUTION LOGIC IN THIS MODULE.

CP-15: Added StepMoveIntent for AoO trigger detection.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Weapon:
    """Weapon definition for attack resolution."""

    damage_dice: str
    """Damage dice expression (e.g., '1d8', '2d6')"""

    damage_bonus: int
    """Flat damage bonus (e.g., STR modifier)"""

    damage_type: str
    """Damage type: 'slashing', 'piercing', 'bludgeoning', 'fire', 'cold', etc."""

    critical_multiplier: int = 2
    """Critical hit damage multiplier (×2, ×3, ×4). Default ×2 per D&D 3.5e PHB p.140."""

    def __post_init__(self):
        """Validate weapon data."""
        if not self.damage_dice:
            raise ValueError("damage_dice cannot be empty")

        # Validate damage type is recognized (not exhaustive, descriptive)
        # D&D 3.5e PHB p.309: energy types use "electricity" (not "electric")
        valid_types = {
            "slashing", "piercing", "bludgeoning",
            "fire", "cold", "acid", "electricity", "sonic",
            "force", "positive", "negative", "nonlethal"
        }
        if self.damage_type not in valid_types:
            raise ValueError(f"damage_type must be one of {valid_types}, got {self.damage_type}")

        # Validate critical multiplier
        if self.critical_multiplier not in {2, 3, 4}:
            raise ValueError(f"critical_multiplier must be 2, 3, or 4, got {self.critical_multiplier}")


@dataclass
class AttackIntent:
    """Intent to perform a single attack action."""

    attacker_id: str
    """Entity performing the attack"""

    target_id: str
    """Entity being attacked"""

    attack_bonus: int
    """Total attack bonus (BAB + STR/DEX + misc)"""

    weapon: Weapon
    """Weapon being used for this attack"""

    def __post_init__(self):
        """Validate attack intent."""
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")


@dataclass
class GridPosition:
    """2D grid position for movement and positioning."""

    x: int
    """X coordinate (grid square)"""

    y: int
    """Y coordinate (grid square)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridPosition":
        """Create from dictionary."""
        return cls(x=data["x"], y=data["y"])

    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, GridPosition):
            return False
        return self.x == other.x and self.y == other.y

    def is_adjacent_to(self, other: "GridPosition") -> bool:
        """Check if this position is adjacent to another (5-ft reach)."""
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        # Adjacent: within 1 square in any direction (including diagonals)
        return (dx <= 1 and dy <= 1) and not (dx == 0 and dy == 0)


@dataclass
class StepMoveIntent:
    """Intent to move one step (CP-15 scoped movement for AoO detection).

    CP-15 SCOPE:
    - Single-step movement only (one 5-ft square)
    - No speed accounting, terrain, or diagonal restrictions
    - Minimal movement representation for AoO trigger evaluation
    - Full movement legality deferred to CP-16+

    from_pos must be provided explicitly (not inferred from WorldState)
    to ensure AoO timing is based on declared intent, not state diffs.
    """

    actor_id: str
    """Entity performing the move"""

    from_pos: GridPosition
    """Starting position (must be current entity position)"""

    to_pos: GridPosition
    """Destination position (must be adjacent to from_pos)"""

    def __post_init__(self):
        """Validate step move intent."""
        if not self.actor_id:
            raise ValueError("actor_id cannot be empty")

        # Validate adjacency (one-step constraint)
        if not self.from_pos.is_adjacent_to(self.to_pos):
            raise ValueError(
                f"StepMoveIntent requires adjacent positions: "
                f"from ({self.from_pos.x},{self.from_pos.y}) to ({self.to_pos.x},{self.to_pos.y})"
            )
