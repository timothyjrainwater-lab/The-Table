"""Height-aware Line of Sight (LOS) and Line of Effect (LOE) resolution.

Implements 3D ray traversal with property mask checking for the Box geometric engine.
Uses integer-only Bresenham 3D algorithm for deterministic results.

WO-003: LOS/LOE Resolution
Reference: RQ-BOX-001 (Geometric Engine Research), Finding 4, Finding 13
Dependencies: WO-001 (PropertyMask, BattleGrid)
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from aidm.schemas.position import Position
from aidm.schemas.geometry import Direction


# ==============================================================================
# RESULT DATACLASSES
# ==============================================================================

@dataclass(frozen=True)
class LOSResult:
    """Result of a line of sight check.

    Immutable result containing whether LOS is clear and details about
    any blocking obstruction.
    """

    is_clear: bool
    """True if line of sight is unobstructed."""

    blocking_position: Optional[Position]
    """Position of first blocking cell, if any."""

    blocking_reason: Optional[str]
    """Reason for blocking: 'cell_opaque', 'border_opaque', 'height_occlusion'."""

    observer_pos: Position
    """Observer's grid position."""

    target_pos: Position
    """Target's grid position."""

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary representation with all fields.
        """
        return {
            "is_clear": self.is_clear,
            "blocking_position": self.blocking_position.to_dict() if self.blocking_position else None,
            "blocking_reason": self.blocking_reason,
            "observer_pos": self.observer_pos.to_dict(),
            "target_pos": self.target_pos.to_dict(),
        }


@dataclass(frozen=True)
class LOEResult:
    """Result of a line of effect check.

    Immutable result containing whether LOE is clear and details about
    any blocking obstruction.
    """

    is_clear: bool
    """True if line of effect is unobstructed."""

    blocking_position: Optional[Position]
    """Position of first blocking cell, if any."""

    blocking_reason: Optional[str]
    """Reason for blocking: 'cell_solid', 'border_solid'."""

    observer_pos: Position
    """Observer's grid position."""

    target_pos: Position
    """Target's grid position."""

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary representation with all fields.
        """
        return {
            "is_clear": self.is_clear,
            "blocking_position": self.blocking_position.to_dict() if self.blocking_position else None,
            "blocking_reason": self.blocking_reason,
            "observer_pos": self.observer_pos.to_dict(),
            "target_pos": self.target_pos.to_dict(),
        }


# ==============================================================================
# BRESENHAM 3D — Integer-only 3D line algorithm
# ==============================================================================

def bresenham_3d(
    start: Tuple[int, int, int],
    end: Tuple[int, int, int]
) -> List[Tuple[int, int, int]]:
    """3D Bresenham line algorithm using integer arithmetic only.

    Per RQ-BOX-001 Finding 13: Uses P_y and P_z error accumulators.
    Only addition, subtraction, and bit-shifting (multiply by 2) are used.

    Args:
        start: Starting point (x, y, z)
        end: Ending point (x, y, z)

    Returns:
        List of all (x, y, z) grid points from start to end inclusive.
    """
    x0, y0, z0 = start
    x1, y1, z1 = end

    points = []

    # Calculate deltas
    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0

    # Determine step directions
    sx = 1 if dx > 0 else -1 if dx < 0 else 0
    sy = 1 if dy > 0 else -1 if dy < 0 else 0
    sz = 1 if dz > 0 else -1 if dz < 0 else 0

    # Absolute deltas
    ax = abs(dx)
    ay = abs(dy)
    az = abs(dz)

    # Current position
    x, y, z = x0, y0, z0

    # Determine primary axis (largest delta)
    if ax >= ay and ax >= az:
        # X is primary axis
        # Error accumulators (doubled to avoid fractions)
        # P_y = 2*ay - ax, P_z = 2*az - ax
        p_y = (ay << 1) - ax
        p_z = (az << 1) - ax

        for _ in range(ax + 1):
            points.append((x, y, z))

            if x == x1:
                break

            # Update Y based on P_y accumulator
            if p_y >= 0:
                y += sy
                p_y -= ax << 1

            # Update Z based on P_z accumulator
            if p_z >= 0:
                z += sz
                p_z -= ax << 1

            # Always step along primary axis
            x += sx
            p_y += ay << 1
            p_z += az << 1

    elif ay >= ax and ay >= az:
        # Y is primary axis
        p_x = (ax << 1) - ay
        p_z = (az << 1) - ay

        for _ in range(ay + 1):
            points.append((x, y, z))

            if y == y1:
                break

            if p_x >= 0:
                x += sx
                p_x -= ay << 1

            if p_z >= 0:
                z += sz
                p_z -= ay << 1

            y += sy
            p_x += ax << 1
            p_z += az << 1

    else:
        # Z is primary axis
        p_x = (ax << 1) - az
        p_y = (ay << 1) - az

        for _ in range(az + 1):
            points.append((x, y, z))

            if z == z1:
                break

            if p_x >= 0:
                x += sx
                p_x -= az << 1

            if p_y >= 0:
                y += sy
                p_y -= az << 1

            z += sz
            p_x += ax << 1
            p_y += ay << 1

    # Handle the case where start == end (single point)
    if not points:
        points.append((x0, y0, z0))

    return points


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _get_border_direction_for_step(
    prev_x: int, prev_y: int,
    curr_x: int, curr_y: int
) -> Optional[Direction]:
    """Determine which border is crossed when moving from prev to curr cell.

    Only considers cardinal movement (diagonal moves handled by checking
    both borders separately).

    Args:
        prev_x: Previous cell X coordinate
        prev_y: Previous cell Y coordinate
        curr_x: Current cell X coordinate
        curr_y: Current cell Y coordinate

    Returns:
        Direction of border crossed from prev cell, or None if same cell.
    """
    dx = curr_x - prev_x
    dy = curr_y - prev_y

    if dx == 0 and dy == 0:
        return None

    # Check primary direction (larger delta)
    if abs(dx) >= abs(dy):
        if dx > 0:
            return Direction.E
        elif dx < 0:
            return Direction.W
    else:
        if dy > 0:
            return Direction.S
        elif dy < 0:
            return Direction.N

    return None


# ==============================================================================
# LOS/LOE CHECK FUNCTIONS
# ==============================================================================

def check_los(
    grid,
    observer_pos: Position,
    observer_height: int,
    target_pos: Position,
    target_height: int
) -> LOSResult:
    """Check line of sight from observer to target.

    Traces a 3D ray from observer to target and checks for obstructions.
    LOS is blocked by OPAQUE cells/borders (unless PERMEABLE).

    Per RQ-BOX-001 Finding 4:
    - Each GridCell has elevation (floor height) and height (content height)
    - Ray is blocked if Z_ray at cell < cell.elevation + cell.height
    - Observer effective Z = cell.elevation + observer_height
    - Target effective Z = cell.elevation + target_height

    Args:
        grid: BattleGrid instance
        observer_pos: Observer's grid position (x, y)
        observer_height: Observer height in feet above their cell elevation
        target_pos: Target's grid position (x, y)
        target_height: Target height in feet above their cell elevation

    Returns:
        LOSResult indicating if LOS is clear or what blocks it.
    """
    # Handle same-cell case
    if observer_pos.x == target_pos.x and observer_pos.y == target_pos.y:
        return LOSResult(
            is_clear=True,
            blocking_position=None,
            blocking_reason=None,
            observer_pos=observer_pos,
            target_pos=target_pos,
        )

    # Handle out of bounds
    if not grid.in_bounds(observer_pos):
        return LOSResult(
            is_clear=False,
            blocking_position=observer_pos,
            blocking_reason="out_of_bounds",
            observer_pos=observer_pos,
            target_pos=target_pos,
        )

    if not grid.in_bounds(target_pos):
        return LOSResult(
            is_clear=False,
            blocking_position=target_pos,
            blocking_reason="out_of_bounds",
            observer_pos=observer_pos,
            target_pos=target_pos,
        )

    # Calculate effective Z coordinates
    observer_cell = grid.get_cell(observer_pos)
    target_cell = grid.get_cell(target_pos)

    observer_z = observer_cell.elevation + observer_height
    target_z = target_cell.elevation + target_height

    # Generate 3D ray
    ray = bresenham_3d(
        (observer_pos.x, observer_pos.y, observer_z),
        (target_pos.x, target_pos.y, target_z)
    )

    # Skip first point (observer's position) and last point (target's position)
    prev_x, prev_y, _ = ray[0]

    for i in range(1, len(ray) - 1):
        curr_x, curr_y, curr_z = ray[i]
        cell_pos = Position(x=curr_x, y=curr_y)

        # Check if cell is in bounds
        if not grid.in_bounds(cell_pos):
            continue

        cell = grid.get_cell(cell_pos)

        # Check border crossing (from previous cell)
        if prev_x != curr_x or prev_y != curr_y:
            direction = _get_border_direction_for_step(prev_x, prev_y, curr_x, curr_y)
            if direction is not None:
                # Check the border on the previous cell
                prev_pos = Position(x=prev_x, y=prev_y)
                if grid.in_bounds(prev_pos):
                    prev_cell = grid.get_cell(prev_pos)
                    border_mask = prev_cell.get_border_mask(direction)
                    if border_mask.blocks_los():
                        return LOSResult(
                            is_clear=False,
                            blocking_position=prev_pos,
                            blocking_reason="border_opaque",
                            observer_pos=observer_pos,
                            target_pos=target_pos,
                        )

        # Check cell opacity
        if cell.cell_mask.blocks_los():
            return LOSResult(
                is_clear=False,
                blocking_position=cell_pos,
                blocking_reason="cell_opaque",
                observer_pos=observer_pos,
                target_pos=target_pos,
            )

        # Check height occlusion
        # Ray is blocked if Z_ray at cell < cell.elevation + cell.height
        cell_top = cell.elevation + cell.height
        if cell.height > 0 and curr_z < cell_top:
            return LOSResult(
                is_clear=False,
                blocking_position=cell_pos,
                blocking_reason="height_occlusion",
                observer_pos=observer_pos,
                target_pos=target_pos,
            )

        prev_x, prev_y = curr_x, curr_y

    # Check final border crossing to target cell
    if len(ray) >= 2:
        last_before_target_x, last_before_target_y, _ = ray[-2]
        direction = _get_border_direction_for_step(
            last_before_target_x, last_before_target_y,
            target_pos.x, target_pos.y
        )
        if direction is not None:
            last_pos = Position(x=last_before_target_x, y=last_before_target_y)
            if grid.in_bounds(last_pos):
                last_cell = grid.get_cell(last_pos)
                border_mask = last_cell.get_border_mask(direction)
                if border_mask.blocks_los():
                    return LOSResult(
                        is_clear=False,
                        blocking_position=last_pos,
                        blocking_reason="border_opaque",
                        observer_pos=observer_pos,
                        target_pos=target_pos,
                    )

    return LOSResult(
        is_clear=True,
        blocking_position=None,
        blocking_reason=None,
        observer_pos=observer_pos,
        target_pos=target_pos,
    )


def check_loe(
    grid,
    observer_pos: Position,
    observer_height: int,
    target_pos: Position,
    target_height: int
) -> LOEResult:
    """Check line of effect from observer to target.

    Traces a 3D ray from observer to target and checks for obstructions.
    LOE is blocked by SOLID cells/borders (unless PERMEABLE).

    Per RQ-BOX-001 Finding 4:
    - Glass wall blocks LOE but not LOS (SOLID, not OPAQUE)
    - Iron grate blocks neither (SOLID + PERMEABLE)

    Args:
        grid: BattleGrid instance
        observer_pos: Observer's grid position (x, y)
        observer_height: Observer height in feet above their cell elevation
        target_pos: Target's grid position (x, y)
        target_height: Target height in feet above their cell elevation

    Returns:
        LOEResult indicating if LOE is clear or what blocks it.
    """
    # Handle same-cell case
    if observer_pos.x == target_pos.x and observer_pos.y == target_pos.y:
        return LOEResult(
            is_clear=True,
            blocking_position=None,
            blocking_reason=None,
            observer_pos=observer_pos,
            target_pos=target_pos,
        )

    # Handle out of bounds
    if not grid.in_bounds(observer_pos):
        return LOEResult(
            is_clear=False,
            blocking_position=observer_pos,
            blocking_reason="out_of_bounds",
            observer_pos=observer_pos,
            target_pos=target_pos,
        )

    if not grid.in_bounds(target_pos):
        return LOEResult(
            is_clear=False,
            blocking_position=target_pos,
            blocking_reason="out_of_bounds",
            observer_pos=observer_pos,
            target_pos=target_pos,
        )

    # Calculate effective Z coordinates
    observer_cell = grid.get_cell(observer_pos)
    target_cell = grid.get_cell(target_pos)

    observer_z = observer_cell.elevation + observer_height
    target_z = target_cell.elevation + target_height

    # Generate 3D ray
    ray = bresenham_3d(
        (observer_pos.x, observer_pos.y, observer_z),
        (target_pos.x, target_pos.y, target_z)
    )

    # Skip first point (observer's position) and last point (target's position)
    prev_x, prev_y, _ = ray[0]

    for i in range(1, len(ray) - 1):
        curr_x, curr_y, curr_z = ray[i]
        cell_pos = Position(x=curr_x, y=curr_y)

        # Check if cell is in bounds
        if not grid.in_bounds(cell_pos):
            continue

        cell = grid.get_cell(cell_pos)

        # Check border crossing (from previous cell)
        if prev_x != curr_x or prev_y != curr_y:
            direction = _get_border_direction_for_step(prev_x, prev_y, curr_x, curr_y)
            if direction is not None:
                # Check the border on the previous cell
                prev_pos = Position(x=prev_x, y=prev_y)
                if grid.in_bounds(prev_pos):
                    prev_cell = grid.get_cell(prev_pos)
                    border_mask = prev_cell.get_border_mask(direction)
                    if border_mask.blocks_loe():
                        return LOEResult(
                            is_clear=False,
                            blocking_position=prev_pos,
                            blocking_reason="border_solid",
                            observer_pos=observer_pos,
                            target_pos=target_pos,
                        )

        # Check cell solidity (LOE uses blocks_loe, not blocks_los)
        if cell.cell_mask.blocks_loe():
            return LOEResult(
                is_clear=False,
                blocking_position=cell_pos,
                blocking_reason="cell_solid",
                observer_pos=observer_pos,
                target_pos=target_pos,
            )

        prev_x, prev_y = curr_x, curr_y

    # Check final border crossing to target cell
    if len(ray) >= 2:
        last_before_target_x, last_before_target_y, _ = ray[-2]
        direction = _get_border_direction_for_step(
            last_before_target_x, last_before_target_y,
            target_pos.x, target_pos.y
        )
        if direction is not None:
            last_pos = Position(x=last_before_target_x, y=last_before_target_y)
            if grid.in_bounds(last_pos):
                last_cell = grid.get_cell(last_pos)
                border_mask = last_cell.get_border_mask(direction)
                if border_mask.blocks_loe():
                    return LOEResult(
                        is_clear=False,
                        blocking_position=last_pos,
                        blocking_reason="border_solid",
                        observer_pos=observer_pos,
                        target_pos=target_pos,
                    )

    return LOEResult(
        is_clear=True,
        blocking_position=None,
        blocking_reason=None,
        observer_pos=observer_pos,
        target_pos=target_pos,
    )


# ==============================================================================
# ENTITY CONVENIENCE FUNCTIONS
# ==============================================================================

DEFAULT_ENTITY_HEIGHT = 5  # Default height in feet (Medium humanoid eye level)


def check_los_between_entities(
    grid,
    observer_id: str,
    target_id: str,
    observer_height: int = DEFAULT_ENTITY_HEIGHT,
    target_height: int = DEFAULT_ENTITY_HEIGHT
) -> LOSResult:
    """Check line of sight between two entities on the grid.

    Convenience function that looks up entity positions from the grid's
    entity tracking and performs the LOS check.

    Args:
        grid: BattleGrid instance
        observer_id: Entity ID of the observer
        target_id: Entity ID of the target
        observer_height: Observer height in feet (default: 5 ft)
        target_height: Target height in feet (default: 5 ft)

    Returns:
        LOSResult indicating if LOS is clear or what blocks it.

    Raises:
        KeyError: If observer_id or target_id not found on grid.
    """
    # Look up entity positions from grid._entities
    if observer_id not in grid._entities:
        raise KeyError(f"Observer entity '{observer_id}' not found on grid")
    if target_id not in grid._entities:
        raise KeyError(f"Target entity '{target_id}' not found on grid")

    observer_pos, _ = grid._entities[observer_id]
    target_pos, _ = grid._entities[target_id]

    return check_los(grid, observer_pos, observer_height, target_pos, target_height)


def check_loe_between_entities(
    grid,
    observer_id: str,
    target_id: str,
    observer_height: int = DEFAULT_ENTITY_HEIGHT,
    target_height: int = DEFAULT_ENTITY_HEIGHT
) -> LOEResult:
    """Check line of effect between two entities on the grid.

    Convenience function that looks up entity positions from the grid's
    entity tracking and performs the LOE check.

    Args:
        grid: BattleGrid instance
        observer_id: Entity ID of the observer
        target_id: Entity ID of the target
        observer_height: Observer height in feet (default: 5 ft)
        target_height: Target height in feet (default: 5 ft)

    Returns:
        LOEResult indicating if LOE is clear or what blocks it.

    Raises:
        KeyError: If observer_id or target_id not found on grid.
    """
    # Look up entity positions from grid._entities
    if observer_id not in grid._entities:
        raise KeyError(f"Observer entity '{observer_id}' not found on grid")
    if target_id not in grid._entities:
        raise KeyError(f"Target entity '{target_id}' not found on grid")

    observer_pos, _ = grid._entities[observer_id]
    target_pos, _ = grid._entities[target_id]

    return check_loe(grid, observer_pos, observer_height, target_pos, target_height)
