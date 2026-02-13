"""Geometric engine schemas for box geometry system.

Defines data structures for the uniform grid geometry engine:
- PropertyMask: Bitmask for cell and border properties (LOS/LOE blocking)
- Direction: Cardinal directions with opposite/delta methods
- CellState: Finite state machine for destructibility
- SizeCategory: D&D 3.5e creature sizes with footprint calculation
- GridCell: Single cell in the uniform grid

WO-001: Box Geometric Engine Core
Reference: RQ-BOX-001 (Geometric Engine Research)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
from enum import Enum, IntFlag

from aidm.schemas.position import Position


# ==============================================================================
# PROPERTY MASK — Bitmask for cell and border properties
# ==============================================================================

class PropertyFlag(IntFlag):
    """Bit flags for PropertyMask.

    Bit layout (per WO-001 specification):
    - Bit 0: SOLID — physically solid, blocks movement
    - Bit 1: OPAQUE — blocks visual light (LOS)
    - Bit 2: PERMEABLE — allows LOE despite solidity (e.g., grate, arrow slit)
    - Bit 3: DIFFICULT — difficult terrain
    - Bit 4: HAZARDOUS — environmental hazard present
    - Bit 5: FLAMMABLE — catches fire from energy damage
    - Bit 6: FRAGILE — takes double damage from impact
    - Bit 7: CONDUCTIVE — electricity arcs to adjacent
    - Bit 8: CRYSTALLINE — vulnerable to sonic
    - Bit 9: DENSE — provides total cover even if damaged
    - Bits 10-31: Reserved
    """
    NONE = 0
    SOLID = 1 << 0       # Bit 0
    OPAQUE = 1 << 1      # Bit 1
    PERMEABLE = 1 << 2   # Bit 2
    DIFFICULT = 1 << 3   # Bit 3
    HAZARDOUS = 1 << 4   # Bit 4
    FLAMMABLE = 1 << 5   # Bit 5
    FRAGILE = 1 << 6     # Bit 6
    CONDUCTIVE = 1 << 7  # Bit 7
    CRYSTALLINE = 1 << 8 # Bit 8
    DENSE = 1 << 9       # Bit 9


@dataclass(frozen=True)
class PropertyMask:
    """Immutable bitmask for cell and border properties.

    Used for both cell volumes and border edges. Immutable design ensures
    thread safety and prevents accidental mutation.

    Barrier type truth table (from RQ-BOX-001 Finding 4):

    | Barrier      | SOLID | OPAQUE | PERMEABLE | blocks_los | blocks_loe |
    |-------------|-------|--------|-----------|------------|------------|
    | Stone Wall  |   1   |   1    |     0     |    True    |    True    |
    | Glass Wall  |   1   |   0    |     0     |   False    |    True    |
    | Magic Dark  |   0   |   1    |     1     |   False*   |   False    |
    | Iron Grate  |   1   |   0    |     1     |   False    |   False    |

    *Magical darkness is OPAQUE + PERMEABLE. blocks_los() returns False because
    the formula is `OPAQUE and not PERMEABLE`. The darkness effect is handled
    by the concealment system, not geometric LOS.
    """

    _value: int = 0

    def has_flag(self, flag: PropertyFlag) -> bool:
        """Check if a flag is set.

        Args:
            flag: PropertyFlag to check

        Returns:
            True if the flag is set
        """
        return bool(self._value & flag)

    def set_flag(self, flag: PropertyFlag) -> 'PropertyMask':
        """Return a new PropertyMask with the flag set.

        Args:
            flag: PropertyFlag to set

        Returns:
            New PropertyMask instance with the flag set
        """
        return PropertyMask(_value=self._value | flag)

    def clear_flag(self, flag: PropertyFlag) -> 'PropertyMask':
        """Return a new PropertyMask with the flag cleared.

        Args:
            flag: PropertyFlag to clear

        Returns:
            New PropertyMask instance with the flag cleared
        """
        return PropertyMask(_value=self._value & ~flag)

    def blocks_los(self) -> bool:
        """Check if this mask blocks line of sight.

        LOS is blocked if OPAQUE is set AND PERMEABLE is not set.
        Magical darkness (OPAQUE + PERMEABLE) does not block geometric LOS;
        the concealment effect is handled separately.

        Returns:
            True if LOS is blocked
        """
        return self.has_flag(PropertyFlag.OPAQUE) and not self.has_flag(PropertyFlag.PERMEABLE)

    def blocks_loe(self) -> bool:
        """Check if this mask blocks line of effect.

        LOE is blocked if SOLID is set AND PERMEABLE is not set.
        Iron grates (SOLID + PERMEABLE) allow spells through.

        Returns:
            True if LOE is blocked
        """
        return self.has_flag(PropertyFlag.SOLID) and not self.has_flag(PropertyFlag.PERMEABLE)

    def to_int(self) -> int:
        """Return the raw integer value.

        Returns:
            Integer bitmask value
        """
        return self._value

    @classmethod
    def from_int(cls, value: int) -> 'PropertyMask':
        """Create a PropertyMask from an integer value.

        Args:
            value: Integer bitmask value

        Returns:
            PropertyMask instance
        """
        return cls(_value=value)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary with 'value' key
        """
        return {"value": self._value}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyMask':
        """Deserialize from dictionary.

        Args:
            data: Dictionary with 'value' key

        Returns:
            PropertyMask instance
        """
        return cls(_value=data["value"])

    def __repr__(self) -> str:
        """Debug representation showing active flags."""
        flags = []
        for flag in PropertyFlag:
            if flag != PropertyFlag.NONE and self.has_flag(flag):
                flags.append(flag.name)
        if not flags:
            return "PropertyMask(NONE)"
        return f"PropertyMask({' | '.join(flags)})"


# ==============================================================================
# DIRECTION — Cardinal directions with opposite/delta methods
# ==============================================================================

class Direction(Enum):
    """Cardinal directions for border references.

    Used to identify which edge of a cell a border applies to.
    Includes opposite() for reciprocal border updates and
    delta() for neighbor position calculation.
    """
    N = "north"
    E = "east"
    S = "south"
    W = "west"

    def opposite(self) -> 'Direction':
        """Return the opposite direction.

        N <-> S, E <-> W

        Returns:
            Opposite Direction
        """
        opposites = {
            Direction.N: Direction.S,
            Direction.S: Direction.N,
            Direction.E: Direction.W,
            Direction.W: Direction.E,
        }
        return opposites[self]

    def delta(self) -> Tuple[int, int]:
        """Return the (dx, dy) offset for this direction.

        Uses screen coordinates (Y increases downward):
        - N → (0, -1)
        - E → (1, 0)
        - S → (0, 1)
        - W → (-1, 0)

        Returns:
            Tuple of (dx, dy)
        """
        deltas = {
            Direction.N: (0, -1),
            Direction.E: (1, 0),
            Direction.S: (0, 1),
            Direction.W: (-1, 0),
        }
        return deltas[self]


# ==============================================================================
# CELL STATE — FSM for destructibility
# ==============================================================================

class CellState(Enum):
    """Finite state machine for cell destructibility.

    State transitions:
    - INTACT → DAMAGED (HP < 100%)
    - DAMAGED → BROKEN (HP < 50%)
    - BROKEN → DESTROYED (HP = 0)

    No reverse transitions allowed.
    """
    INTACT = "intact"
    DAMAGED = "damaged"
    BROKEN = "broken"
    DESTROYED = "destroyed"


# ==============================================================================
# SIZE CATEGORY — D&D 3.5e creature sizes
# ==============================================================================

class SizeCategory(Enum):
    """D&D 3.5e creature size categories.

    Size determines the footprint (number of 5-foot squares occupied)
    and various combat modifiers (not handled here).

    Reference: PHB p.132, DMG p.29
    """
    FINE = "fine"
    DIMINUTIVE = "diminutive"
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    GARGANTUAN = "gargantuan"
    COLOSSAL = "colossal"

    def footprint(self) -> int:
        """Return the number of 5-foot squares occupied.

        Fine through Medium creatures occupy 1 square (may share).
        Large creatures occupy 4 squares (2x2).
        Huge creatures occupy 9 squares (3x3).
        Gargantuan creatures occupy 16 squares (4x4).
        Colossal creatures occupy 25 squares (5x5).

        Returns:
            Number of squares occupied
        """
        footprints = {
            SizeCategory.FINE: 1,
            SizeCategory.DIMINUTIVE: 1,
            SizeCategory.TINY: 1,
            SizeCategory.SMALL: 1,
            SizeCategory.MEDIUM: 1,
            SizeCategory.LARGE: 4,
            SizeCategory.HUGE: 9,
            SizeCategory.GARGANTUAN: 16,
            SizeCategory.COLOSSAL: 25,
        }
        return footprints[self]

    def grid_size(self) -> int:
        """Return the side length of the square footprint.

        Returns:
            Side length (1 for Medium and smaller, 2 for Large, etc.)
        """
        import math
        return int(math.sqrt(self.footprint()))


# ==============================================================================
# GRID CELL — Single cell in the uniform grid
# ==============================================================================

@dataclass
class GridCell:
    """Single cell in the BattleGrid.

    Contains volumetric properties (cell_mask), edge properties (border_masks),
    structural integrity (hardness, hit_points, state), and occupant tracking.

    All positions use the canonical Position type from aidm.schemas.position.
    """

    position: Position
    """Grid coordinates of this cell."""

    cell_mask: PropertyMask = field(default_factory=PropertyMask)
    """Properties of the cell volume (SOLID, OPAQUE, etc.)."""

    border_masks: Dict[Direction, PropertyMask] = field(default_factory=dict)
    """Properties of each border edge (N, E, S, W)."""

    elevation: int = 0
    """Height in feet above base level."""

    height: int = 0
    """Height of contents in feet for LOS occlusion."""

    material_mask: int = 0
    """Material property bits for damage type interactions."""

    hardness: int = 0
    """Damage reduction for destructible objects."""

    hit_points: int = 0
    """Structural integrity, 0 = destroyed."""

    state: CellState = CellState.INTACT
    """Current FSM state for destructibility."""

    occupant_ids: List[str] = field(default_factory=list)
    """Entity IDs currently occupying this cell."""

    def get_border_mask(self, direction: Direction) -> PropertyMask:
        """Get the border mask for a direction.

        Args:
            direction: Cardinal direction

        Returns:
            PropertyMask for that border, or empty mask if not set
        """
        return self.border_masks.get(direction, PropertyMask())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "position": self.position.to_dict(),
            "cell_mask": self.cell_mask.to_dict(),
            "border_masks": {
                d.value: m.to_dict() for d, m in self.border_masks.items()
            },
            "elevation": self.elevation,
            "height": self.height,
            "material_mask": self.material_mask,
            "hardness": self.hardness,
            "hit_points": self.hit_points,
            "state": self.state.value,
            "occupant_ids": list(self.occupant_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GridCell':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            GridCell instance
        """
        # Parse border masks
        border_masks = {}
        for dir_str, mask_data in data.get("border_masks", {}).items():
            direction = Direction(dir_str)
            border_masks[direction] = PropertyMask.from_dict(mask_data)

        # Parse state
        state_str = data.get("state", "intact")
        state = CellState(state_str)

        return cls(
            position=Position.from_dict(data["position"]),
            cell_mask=PropertyMask.from_dict(data.get("cell_mask", {"value": 0})),
            border_masks=border_masks,
            elevation=data.get("elevation", 0),
            height=data.get("height", 0),
            material_mask=data.get("material_mask", 0),
            hardness=data.get("hardness", 0),
            hit_points=data.get("hit_points", 0),
            state=state,
            occupant_ids=list(data.get("occupant_ids", [])),
        )

    def __repr__(self) -> str:
        """Debug representation."""
        return f"GridCell(pos={self.position}, mask={self.cell_mask}, occupants={self.occupant_ids})"
