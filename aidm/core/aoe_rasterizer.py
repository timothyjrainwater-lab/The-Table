"""Area of Effect rasterization for D&D 3.5e tactical combat.

Converts spell/effect geometric shapes into lists of affected grid squares
using RAW 3.5e rules for distance, coverage, and shape geometry.

Supported shapes:
- BURST: Circular spread from origin (Fireball, etc.)
- SPREAD: Like burst but flows around corners (not yet implemented)
- CONE: Triangular area from caster (Burning Hands, Cone of Cold)
- LINE: 5-foot wide line (Lightning Bolt)
- CYLINDER: Burst with height (Flame Strike)
- SPHERE: 3D burst (same as burst for 2D grid)

Distance Formula (RQ-BOX-001 Finding 5):
D_discrete = max(|dx|, |dy|) + floor(min(|dx|, |dy|) / 2)

This approximates 3.5e 5/10/5 diagonal movement pattern and produces
octagonal shapes for bursts.

WO-004: AoE Rasterization
Reference: RQ-BOX-001 (Geometric Engine Research)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

from aidm.schemas.position import Position


# ==============================================================================
# AOE DIRECTION — 8-directional for cones and lines
# ==============================================================================

class AoEDirection(Enum):
    """8-directional enum for AoE targeting.

    Unlike geometry.Direction (4 cardinal only), this includes diagonals
    for cone and line targeting per PHB rules.

    Screen coordinates: Y increases downward (standard grid convention).
    """
    N = "north"
    NE = "northeast"
    E = "east"
    SE = "southeast"
    S = "south"
    SW = "southwest"
    W = "west"
    NW = "northwest"

    def delta(self) -> tuple[int, int]:
        """Return unit (dx, dy) for this direction.

        Returns:
            Tuple of (dx, dy) unit vector
        """
        deltas = {
            AoEDirection.N: (0, -1),
            AoEDirection.NE: (1, -1),
            AoEDirection.E: (1, 0),
            AoEDirection.SE: (1, 1),
            AoEDirection.S: (0, 1),
            AoEDirection.SW: (-1, 1),
            AoEDirection.W: (-1, 0),
            AoEDirection.NW: (-1, -1),
        }
        return deltas[self]

    def is_cardinal(self) -> bool:
        """Check if this is a cardinal direction (N, E, S, W)."""
        return self in (AoEDirection.N, AoEDirection.E,
                        AoEDirection.S, AoEDirection.W)

    def is_diagonal(self) -> bool:
        """Check if this is a diagonal direction (NE, SE, SW, NW)."""
        return self in (AoEDirection.NE, AoEDirection.SE,
                        AoEDirection.SW, AoEDirection.NW)


# ==============================================================================
# AOE SHAPE — Shape type enumeration
# ==============================================================================

class AoEShape(Enum):
    """AoE shape types per PHB p.175.

    Each shape has different geometry and coverage rules.
    """
    BURST = "burst"       # Circular, spreads from origin
    SPREAD = "spread"     # Circular, spreads around corners
    CONE = "cone"         # Triangle from caster
    LINE = "line"         # 5-foot wide line from caster
    CYLINDER = "cylinder" # Burst with height
    SPHERE = "sphere"     # 3D burst


# ==============================================================================
# AOE RESULT — Frozen dataclass for rasterization results
# ==============================================================================

@dataclass(frozen=True)
class AoEResult:
    """Result of AoE rasterization.

    Immutable record of affected squares and parameters.
    """
    shape: AoEShape
    origin: Position
    affected_squares: tuple  # Tuple[Position, ...] for immutability
    square_count: int
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Convert affected_squares to tuple if needed."""
        if isinstance(self.affected_squares, list):
            object.__setattr__(self, 'affected_squares', tuple(self.affected_squares))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "shape": self.shape.value,
            "origin": self.origin.to_dict(),
            "affected_squares": [pos.to_dict() for pos in self.affected_squares],
            "square_count": self.square_count,
            "params": dict(self.params),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AoEResult':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            AoEResult instance
        """
        return cls(
            shape=AoEShape(data["shape"]),
            origin=Position.from_dict(data["origin"]),
            affected_squares=tuple(Position.from_dict(p) for p in data["affected_squares"]),
            square_count=data["square_count"],
            params=data.get("params", {}),
        )


# ==============================================================================
# DISTANCE CALCULATION — 3.5e discrete distance formula
# ==============================================================================

def discrete_distance(dx: int, dy: int) -> int:
    """Calculate discrete distance per 3.5e diagonal rules.

    Formula: D = max(|dx|, |dy|) + floor(min(|dx|, |dy|) / 2)

    This matches the 5/10/5 diagonal pattern where:
    - Orthogonal step = 1 unit (5 feet)
    - First diagonal = 1 unit
    - Second diagonal = 2 units
    - Pattern repeats

    Example: dx=4, dy=4 (4 diagonal steps)
    - Diagonal pairs: 2 (each pair = 3 units: 1+2)
    - Result: 4 + 2 = 6 squares (30 feet)

    Args:
        dx: X offset from origin (squares)
        dy: Y offset from origin (squares)

    Returns:
        Distance in squares (multiply by 5 for feet)
    """
    abs_dx = abs(dx)
    abs_dy = abs(dy)
    return max(abs_dx, abs_dy) + min(abs_dx, abs_dy) // 2


# ==============================================================================
# BURST RASTERIZATION
# ==============================================================================

def rasterize_burst(origin: Position, radius_ft: int) -> List[Position]:
    """Rasterize a circular burst centered on origin.

    Uses discrete distance formula to produce octagonal shape
    matching 3.5e diagonal movement rules.

    Args:
        origin: Center of burst
        radius_ft: Radius in feet (5, 10, 15, 20, etc.)

    Returns:
        List of affected positions (no duplicates)
    """
    if radius_ft < 0:
        return []

    radius_squares = radius_ft // 5

    # Zero radius: origin only
    if radius_squares == 0:
        return [origin]

    affected = []

    # Check all squares within bounding box
    for dy in range(-radius_squares, radius_squares + 1):
        for dx in range(-radius_squares, radius_squares + 1):
            # Use discrete distance formula
            dist = discrete_distance(dx, dy)
            if dist <= radius_squares:
                affected.append(Position(x=origin.x + dx, y=origin.y + dy))

    return affected


# ==============================================================================
# CONE RASTERIZATION
# ==============================================================================

def rasterize_cone(
    origin: Position,
    direction: AoEDirection,
    length_ft: int
) -> List[Position]:
    """Rasterize a cone shape from origin in given direction.

    Per PHB p.175:
    - Cone point is a grid intersection (corner between squares)
    - Width at distance D equals D
    - Use 50% coverage rule

    For simplicity, we treat the origin as the square the cone starts from,
    and the cone expands in the given direction.

    Expected square counts (cardinal):
    - 15-foot cone: 6 squares
    - 30-foot cone: 21 squares
    - 60-foot cone: 91 squares

    Formula: N = L/5 * (L/5 + 1) / 2 (triangular number)

    Args:
        origin: Point of cone (grid intersection, we use southwest square)
        direction: One of 8 directions
        length_ft: Cone length in feet

    Returns:
        List of affected positions (no duplicates)
    """
    if length_ft <= 0:
        return []

    length_squares = length_ft // 5
    affected = []

    dx, dy = direction.delta()

    if direction.is_cardinal():
        # Cardinal cones: triangular shape along axis
        # For N direction: cone goes up, width expands left-right
        # At distance d (1 to length_squares), width = d squares
        for d in range(1, length_squares + 1):
            # Position along the direction
            cx = origin.x + dx * d
            cy = origin.y + dy * d

            # Width at this distance: d squares centered
            # For even d: d squares (d/2 each side of center)
            # For odd d: d squares (d//2 each side of center + center)
            half_width = (d - 1) // 2

            if dx != 0:  # E or W: expand along Y
                for offset in range(-half_width, half_width + d - half_width * 2):
                    pos = Position(x=cx, y=cy + offset)
                    if pos not in affected:
                        affected.append(pos)
            else:  # N or S: expand along X
                for offset in range(-half_width, half_width + d - half_width * 2):
                    pos = Position(x=cx + offset, y=cy)
                    if pos not in affected:
                        affected.append(pos)
    else:
        # Diagonal cones: rotated triangle
        # NE cone: goes up-right, width perpendicular to diagonal
        for d in range(1, length_squares + 1):
            # Move along diagonal
            cx = origin.x + dx * d
            cy = origin.y + dy * d

            # At distance d, add d squares in a diagonal band
            # The band is perpendicular to the direction
            # For NE: perpendicular is NW-SE axis
            if direction == AoEDirection.NE:
                # Perpendicular: go along (1,1) and (-1,-1) from diagonal point
                for offset in range(d):
                    # Main diagonal point
                    pos = Position(x=cx, y=cy)
                    if pos not in affected:
                        affected.append(pos)
                    # Spread perpendicular
                    if offset > 0:
                        # NW from main point
                        pos1 = Position(x=cx - offset, y=cy)
                        if pos1 not in affected:
                            affected.append(pos1)
                        # SE from main point
                        pos2 = Position(x=cx, y=cy + offset)
                        if pos2 not in affected:
                            affected.append(pos2)
            elif direction == AoEDirection.SE:
                for offset in range(d):
                    pos = Position(x=cx, y=cy)
                    if pos not in affected:
                        affected.append(pos)
                    if offset > 0:
                        pos1 = Position(x=cx, y=cy - offset)
                        if pos1 not in affected:
                            affected.append(pos1)
                        pos2 = Position(x=cx - offset, y=cy)
                        if pos2 not in affected:
                            affected.append(pos2)
            elif direction == AoEDirection.SW:
                for offset in range(d):
                    pos = Position(x=cx, y=cy)
                    if pos not in affected:
                        affected.append(pos)
                    if offset > 0:
                        pos1 = Position(x=cx + offset, y=cy)
                        if pos1 not in affected:
                            affected.append(pos1)
                        pos2 = Position(x=cx, y=cy - offset)
                        if pos2 not in affected:
                            affected.append(pos2)
            elif direction == AoEDirection.NW:
                for offset in range(d):
                    pos = Position(x=cx, y=cy)
                    if pos not in affected:
                        affected.append(pos)
                    if offset > 0:
                        pos1 = Position(x=cx + offset, y=cy)
                        if pos1 not in affected:
                            affected.append(pos1)
                        pos2 = Position(x=cx, y=cy + offset)
                        if pos2 not in affected:
                            affected.append(pos2)

    return affected


# ==============================================================================
# LINE RASTERIZATION
# ==============================================================================

def rasterize_line(
    origin: Position,
    direction: AoEDirection,
    length_ft: int,
    width_ft: int = 5
) -> List[Position]:
    """Rasterize a line from origin in given direction.

    Per RQ-BOX-001 Finding 9: Conservative rasterization.
    Any square the line touches is affected (not just centers).

    Args:
        origin: Start of line
        direction: One of 8 directions
        length_ft: Line length in feet
        width_ft: Line width in feet (default 5)

    Returns:
        List of affected positions (no duplicates)
    """
    if length_ft <= 0:
        return []

    length_squares = length_ft // 5
    width_squares = max(1, width_ft // 5)

    dx, dy = direction.delta()
    affected = []

    if direction.is_cardinal():
        # Cardinal direction: line goes straight
        half_width = (width_squares - 1) // 2

        for d in range(length_squares):
            # Position along the line
            cx = origin.x + dx * d
            cy = origin.y + dy * d

            # Width perpendicular to direction
            if dx != 0:  # E or W: expand along Y
                for offset in range(-half_width, half_width + 1):
                    pos = Position(x=cx, y=cy + offset)
                    if pos not in affected:
                        affected.append(pos)
            else:  # N or S: expand along X
                for offset in range(-half_width, half_width + 1):
                    pos = Position(x=cx + offset, y=cy)
                    if pos not in affected:
                        affected.append(pos)
    else:
        # Diagonal direction: line crosses both dimensions
        # Conservative rasterization: include all touched squares
        # For diagonal, a 5-foot line actually touches 2 squares per step
        for d in range(length_squares):
            cx = origin.x + dx * d
            cy = origin.y + dy * d

            # Main square
            pos = Position(x=cx, y=cy)
            if pos not in affected:
                affected.append(pos)

            # Conservative: also include adjacent squares touched by the line
            # For 5-foot width diagonal line, touch the parallel squares
            # For a NE line, it also grazes squares to the N and E of the path
            if width_ft >= 5:
                # Add squares that the diagonal line passes through
                # The line crosses cell borders
                pos_x = Position(x=cx, y=cy - dy)  # Square above/below
                pos_y = Position(x=cx - dx, y=cy)  # Square left/right
                if pos_x not in affected:
                    affected.append(pos_x)
                if pos_y not in affected:
                    affected.append(pos_y)

    return affected


# ==============================================================================
# CYLINDER RASTERIZATION
# ==============================================================================

def rasterize_cylinder(
    origin: Position,
    radius_ft: int,
    height_ft: int
) -> List[Position]:
    """Rasterize a cylinder shape.

    For 2D grid purposes, same as burst. Height is stored for
    3D line-of-effect checks handled elsewhere.

    Args:
        origin: Center of cylinder base
        radius_ft: Radius in feet
        height_ft: Cylinder height in feet (for 3D, stored but not used in 2D)

    Returns:
        List of affected positions (same as burst)
    """
    # 2D projection is same as burst
    return rasterize_burst(origin, radius_ft)


# ==============================================================================
# SPHERE RASTERIZATION
# ==============================================================================

def rasterize_sphere(origin: Position, radius_ft: int) -> List[Position]:
    """Rasterize a sphere shape.

    For 2D grid purposes, same as burst. 3D considerations
    handled by height checks elsewhere.

    Args:
        origin: Center of sphere
        radius_ft: Radius in feet

    Returns:
        List of affected positions (same as burst)
    """
    # 2D projection is same as burst
    return rasterize_burst(origin, radius_ft)


# ==============================================================================
# UNIFIED INTERFACE
# ==============================================================================

def get_aoe_affected_squares(
    shape: AoEShape,
    origin: Position,
    params: Dict[str, Any]
) -> List[Position]:
    """Unified interface for all AoE shapes.

    Dispatches to the appropriate rasterization function based on shape type.

    Args:
        shape: AoE shape type
        origin: Origin position
        params: Shape-specific parameters:
            - radius_ft: For burst, cylinder, sphere
            - length_ft: For cone, line
            - direction: For cone, line (AoEDirection)
            - width_ft: For line (default 5)
            - height_ft: For cylinder

    Returns:
        List of affected positions

    Raises:
        ValueError: If required parameters are missing
    """
    if shape == AoEShape.BURST:
        radius_ft = params.get("radius_ft")
        if radius_ft is None:
            raise ValueError("Burst requires 'radius_ft' parameter")
        return rasterize_burst(origin, radius_ft)

    elif shape == AoEShape.SPREAD:
        # Spread is like burst but flows around corners
        # For now, treat same as burst (corner-flow requires grid state)
        radius_ft = params.get("radius_ft")
        if radius_ft is None:
            raise ValueError("Spread requires 'radius_ft' parameter")
        return rasterize_burst(origin, radius_ft)

    elif shape == AoEShape.CONE:
        length_ft = params.get("length_ft")
        direction = params.get("direction")
        if length_ft is None:
            raise ValueError("Cone requires 'length_ft' parameter")
        if direction is None:
            raise ValueError("Cone requires 'direction' parameter")
        if isinstance(direction, str):
            direction = AoEDirection(direction)
        return rasterize_cone(origin, direction, length_ft)

    elif shape == AoEShape.LINE:
        length_ft = params.get("length_ft")
        direction = params.get("direction")
        width_ft = params.get("width_ft", 5)
        if length_ft is None:
            raise ValueError("Line requires 'length_ft' parameter")
        if direction is None:
            raise ValueError("Line requires 'direction' parameter")
        if isinstance(direction, str):
            direction = AoEDirection(direction)
        return rasterize_line(origin, direction, length_ft, width_ft)

    elif shape == AoEShape.CYLINDER:
        radius_ft = params.get("radius_ft")
        height_ft = params.get("height_ft", 0)
        if radius_ft is None:
            raise ValueError("Cylinder requires 'radius_ft' parameter")
        return rasterize_cylinder(origin, radius_ft, height_ft)

    elif shape == AoEShape.SPHERE:
        radius_ft = params.get("radius_ft")
        if radius_ft is None:
            raise ValueError("Sphere requires 'radius_ft' parameter")
        return rasterize_sphere(origin, radius_ft)

    else:
        raise ValueError(f"Unknown AoE shape: {shape}")


def create_aoe_result(
    shape: AoEShape,
    origin: Position,
    params: Dict[str, Any]
) -> AoEResult:
    """Create an AoEResult for a shape.

    Convenience function that rasterizes and wraps in AoEResult.

    Args:
        shape: AoE shape type
        origin: Origin position
        params: Shape-specific parameters

    Returns:
        AoEResult with affected squares
    """
    affected = get_aoe_affected_squares(shape, origin, params)
    return AoEResult(
        shape=shape,
        origin=origin,
        affected_squares=tuple(affected),
        square_count=len(affected),
        params=params,
    )
