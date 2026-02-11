"""M3 Ghost Stencils — Phantom AoE overlays for targeting.

WO-025: Table-Native UX (Ghost Stencils)

Provides:
- GhostStencil: Phantom AoE overlay during targeting
- create_stencil(): Factory for burst/cone/line stencils
- nudge_stencil(): Immutable stencil repositioning
- confirm_stencil(): Freeze stencil for resolution
- Pure functions using existing AoE rasterizer logic

All data models, no rendering. Rendering is frontend responsibility.
No grid mutation (pure functions only).
"""

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aidm.schemas.position import Position
from aidm.core.aoe_rasterizer import AoEShape, AoEDirection, rasterize_burst


# ==============================================================================
# STENCIL SHAPE TYPE
# ==============================================================================

class StencilShape(Enum):
    """Ghost stencil shape types.

    Maps to AoE shapes but includes only player-targetable types.
    """
    BURST = "burst"       # Circular AoE (Fireball, etc.)
    CONE = "cone"         # Triangular cone
    LINE = "line"         # 5-foot wide line

    def to_aoe_shape(self) -> AoEShape:
        """Convert to AoEShape enum.

        Returns:
            Corresponding AoEShape
        """
        mapping = {
            StencilShape.BURST: AoEShape.BURST,
            StencilShape.CONE: AoEShape.CONE,
            StencilShape.LINE: AoEShape.LINE,
        }
        return mapping[self]


# ==============================================================================
# GHOST STENCIL DATACLASS
# ==============================================================================

@dataclass(frozen=True)
class GhostStencil:
    """Phantom AoE overlay during targeting.

    Immutable stencil showing affected cells before confirmation.
    Contains shape, origin, affected cells, and visual parameters.
    """

    shape: StencilShape
    """Shape type (burst, cone, line)."""

    origin: Position
    """Origin point of the stencil."""

    affected_cells: frozenset
    """Frozenset of Position objects for affected cells."""

    # Shape-specific parameters
    radius_ft: int = 0
    """Radius in feet (burst only)."""

    length_ft: int = 0
    """Length in feet (cone/line only)."""

    direction: Optional[AoEDirection] = None
    """Direction for cone/line (None for burst)."""

    # Visual parameters
    opacity: float = 0.5
    """Visual opacity (0.0 to 1.0) for display."""

    grid_width: int = 0
    """Grid width for bounds checking."""

    grid_height: int = 0
    """Grid height for bounds checking."""

    def count(self) -> int:
        """Get count of affected cells.

        Returns:
            Number of affected cells
        """
        return len(self.affected_cells)

    def contains(self, pos: Position) -> bool:
        """Check if position is affected by this stencil.

        Args:
            pos: Position to check

        Returns:
            True if position is affected
        """
        return pos in self.affected_cells

    def get_cells_list(self) -> List[Position]:
        """Get affected cells as sorted list.

        Returns:
            List of Position objects sorted by (y, x)
        """
        return sorted(
            self.affected_cells,
            key=lambda p: (p.y, p.x)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        result = {
            "shape": self.shape.value,
            "origin": self.origin.to_dict(),
            "affected_cells": [p.to_dict() for p in sorted(self.affected_cells, key=lambda p: (p.y, p.x))],
            "opacity": self.opacity,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
        }
        if self.radius_ft > 0:
            result["radius_ft"] = self.radius_ft
        if self.length_ft > 0:
            result["length_ft"] = self.length_ft
        if self.direction is not None:
            result["direction"] = self.direction.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GhostStencil":
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            GhostStencil instance
        """
        shape = StencilShape(data["shape"])
        origin = Position.from_dict(data["origin"])
        affected_cells = frozenset(Position.from_dict(p) for p in data["affected_cells"])

        direction = None
        if "direction" in data:
            direction = AoEDirection(data["direction"])

        return cls(
            shape=shape,
            origin=origin,
            affected_cells=affected_cells,
            radius_ft=data.get("radius_ft", 0),
            length_ft=data.get("length_ft", 0),
            direction=direction,
            opacity=data.get("opacity", 0.5),
            grid_width=data.get("grid_width", 0),
            grid_height=data.get("grid_height", 0),
        )


# ==============================================================================
# FROZEN STENCIL (CONFIRMED)
# ==============================================================================

@dataclass(frozen=True)
class FrozenStencil:
    """Confirmed stencil ready for resolution.

    Immutable snapshot of stencil at confirmation time.
    """

    stencil: GhostStencil
    """Original ghost stencil."""

    confirmed_at: float
    """Timestamp of confirmation (Unix time)."""

    caster_id: str = ""
    """ID of casting entity."""

    spell_name: str = ""
    """Name of spell/ability."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "stencil": self.stencil.to_dict(),
            "confirmed_at": self.confirmed_at,
            "caster_id": self.caster_id,
            "spell_name": self.spell_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FrozenStencil":
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            FrozenStencil instance
        """
        return cls(
            stencil=GhostStencil.from_dict(data["stencil"]),
            confirmed_at=data["confirmed_at"],
            caster_id=data.get("caster_id", ""),
            spell_name=data.get("spell_name", ""),
        )


# ==============================================================================
# STENCIL CREATION
# ==============================================================================

def create_stencil(
    shape: StencilShape,
    origin: Position,
    grid_width: int,
    grid_height: int,
    radius_ft: int = 0,
    length_ft: int = 0,
    direction: Optional[AoEDirection] = None,
    opacity: float = 0.5,
) -> GhostStencil:
    """Create a ghost stencil for AoE targeting.

    Pure function: no state mutation.

    Args:
        shape: Stencil shape (burst, cone, line)
        origin: Origin position
        grid_width: Grid width for bounds checking
        grid_height: Grid height for bounds checking
        radius_ft: Radius in feet (burst only)
        length_ft: Length in feet (cone/line only)
        direction: Direction for cone/line (None for burst)
        opacity: Visual opacity (0.0-1.0)

    Returns:
        GhostStencil with affected cells computed

    Raises:
        ValueError: If parameters invalid for shape type
    """
    # Validate parameters
    if shape == StencilShape.BURST and radius_ft <= 0:
        raise ValueError(f"Burst stencil requires radius_ft > 0, got {radius_ft}")
    if shape in (StencilShape.CONE, StencilShape.LINE):
        if length_ft <= 0:
            raise ValueError(f"{shape.value} stencil requires length_ft > 0, got {length_ft}")
        if direction is None:
            raise ValueError(f"{shape.value} stencil requires direction")

    # Compute affected cells based on shape
    affected_positions: Set[Position] = set()

    if shape == StencilShape.BURST:
        # Use AoE rasterizer for burst
        affected_positions = set(_rasterize_burst_simple(origin, radius_ft))

    elif shape == StencilShape.CONE:
        # Approximate cone using directional spread
        affected_positions = set(_rasterize_cone_simple(origin, length_ft, direction))

    elif shape == StencilShape.LINE:
        # Simple line implementation
        affected_positions = set(_rasterize_line_simple(origin, length_ft, direction))

    # Filter out-of-bounds positions
    affected_positions = {
        pos for pos in affected_positions
        if 0 <= pos.x < grid_width and 0 <= pos.y < grid_height
    }

    return GhostStencil(
        shape=shape,
        origin=origin,
        affected_cells=frozenset(affected_positions),
        radius_ft=radius_ft,
        length_ft=length_ft,
        direction=direction,
        opacity=opacity,
        grid_width=grid_width,
        grid_height=grid_height,
    )


# ==============================================================================
# SIMPLE AoE RASTERIZERS (For stencil preview)
# ==============================================================================

def _rasterize_burst_simple(origin: Position, radius_ft: int) -> List[Position]:
    """Simple burst rasterization for stencil preview.

    Args:
        origin: Center position
        radius_ft: Radius in feet

    Returns:
        List of affected positions
    """
    # Use existing burst rasterizer
    return rasterize_burst(origin, radius_ft)


def _rasterize_cone_simple(
    origin: Position,
    length_ft: int,
    direction: AoEDirection
) -> List[Position]:
    """Simple cone rasterization for stencil preview.

    Args:
        origin: Cone origin
        length_ft: Cone length in feet
        direction: Cone direction

    Returns:
        List of affected positions
    """
    affected = []
    radius_sq = length_ft // 5  # Convert to squares

    dx, dy = direction.delta()

    # Expand width as distance increases (90-degree cone approximation)
    for distance in range(1, radius_sq + 1):
        center_x = origin.x + dx * distance
        center_y = origin.y + dy * distance

        # Width increases with distance (roughly 1 square per distance)
        width = max(1, distance)

        for offset in range(-width, width + 1):
            # Perpendicular offset
            if dx == 0:  # Vertical direction
                pos = Position(center_x + offset, center_y)
            elif dy == 0:  # Horizontal direction
                pos = Position(center_x, center_y + offset)
            else:  # Diagonal
                # For diagonal, spread in both perpendicular directions
                perp_dx = -dy  # Perpendicular to direction
                perp_dy = dx
                pos = Position(
                    center_x + perp_dx * (offset // 2),
                    center_y + perp_dy * (offset // 2)
                )

            affected.append(pos)

    # Always include origin
    if origin not in affected:
        affected.append(origin)

    return affected


def _rasterize_line_simple(
    origin: Position,
    length_ft: int,
    direction: AoEDirection
) -> List[Position]:
    """Simple line rasterization for stencil preview.

    Args:
        origin: Line origin
        length_ft: Line length in feet
        direction: Line direction

    Returns:
        List of affected positions
    """
    affected = []
    length_sq = length_ft // 5  # Convert to squares

    dx, dy = direction.delta()

    # Trace line from origin
    for distance in range(length_sq + 1):
        pos = Position(origin.x + dx * distance, origin.y + dy * distance)
        affected.append(pos)

    return affected


# ==============================================================================
# STENCIL MANIPULATION
# ==============================================================================

def nudge_stencil(
    stencil: GhostStencil,
    dx: int,
    dy: int
) -> GhostStencil:
    """Nudge stencil by offset (immutable update).

    Pure function: no state mutation.

    Args:
        stencil: Original stencil
        dx: X offset in squares
        dy: Y offset in squares

    Returns:
        New GhostStencil at offset position
    """
    new_origin = Position(stencil.origin.x + dx, stencil.origin.y + dy)

    # Recreate stencil with new origin
    return create_stencil(
        shape=stencil.shape,
        origin=new_origin,
        grid_width=stencil.grid_width,
        grid_height=stencil.grid_height,
        radius_ft=stencil.radius_ft,
        length_ft=stencil.length_ft,
        direction=stencil.direction,
        opacity=stencil.opacity,
    )


def rotate_stencil(
    stencil: GhostStencil,
    clockwise: bool = True
) -> GhostStencil:
    """Rotate directional stencil (cone/line only).

    Pure function: no state mutation.

    Args:
        stencil: Original stencil
        clockwise: True for clockwise, False for counter-clockwise

    Returns:
        New GhostStencil with rotated direction

    Raises:
        ValueError: If stencil has no direction (burst)
    """
    if stencil.direction is None:
        raise ValueError("Cannot rotate burst stencil (no direction)")

    # Rotation mapping (clockwise)
    rotation_cw = {
        AoEDirection.N: AoEDirection.NE,
        AoEDirection.NE: AoEDirection.E,
        AoEDirection.E: AoEDirection.SE,
        AoEDirection.SE: AoEDirection.S,
        AoEDirection.S: AoEDirection.SW,
        AoEDirection.SW: AoEDirection.W,
        AoEDirection.W: AoEDirection.NW,
        AoEDirection.NW: AoEDirection.N,
    }

    # Reverse for counter-clockwise
    rotation_ccw = {v: k for k, v in rotation_cw.items()}

    new_direction = rotation_cw[stencil.direction] if clockwise else rotation_ccw[stencil.direction]

    return create_stencil(
        shape=stencil.shape,
        origin=stencil.origin,
        grid_width=stencil.grid_width,
        grid_height=stencil.grid_height,
        radius_ft=stencil.radius_ft,
        length_ft=stencil.length_ft,
        direction=new_direction,
        opacity=stencil.opacity,
    )


def confirm_stencil(
    stencil: GhostStencil,
    timestamp: float,
    caster_id: str = "",
    spell_name: str = "",
) -> FrozenStencil:
    """Confirm stencil for resolution (freeze).

    Pure function: no state mutation.

    Args:
        stencil: Ghost stencil to confirm
        timestamp: Confirmation timestamp
        caster_id: ID of casting entity
        spell_name: Name of spell/ability

    Returns:
        FrozenStencil ready for resolution
    """
    return FrozenStencil(
        stencil=stencil,
        confirmed_at=timestamp,
        caster_id=caster_id,
        spell_name=spell_name,
    )


# ==============================================================================
# PUBLIC API
# ==============================================================================

__all__ = [
    "StencilShape",
    "GhostStencil",
    "FrozenStencil",
    "create_stencil",
    "nudge_stencil",
    "rotate_stencil",
    "confirm_stencil",
]
