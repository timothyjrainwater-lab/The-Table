"""Cover resolution for Box geometric engine.

Implements RAW 3.5e corner-to-corner cover calculation (PHB p.150-152).
Uses the geometric engine's PropertyMask system to check LOS/LOE blocking.

WO-002: Cover Resolution
Reference: RQ-BOX-001 Finding 3 (Deterministic Cover Resolution)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
import math

from aidm.schemas.position import Position
from aidm.schemas.geometry import PropertyMask, Direction, SizeCategory
from aidm.core.geometry_engine import BattleGrid


# ==============================================================================
# COVER DEGREE ENUM
# ==============================================================================

class CoverDegree(Enum):
    """Cover degree for RAW 3.5e cover resolution.

    Per PHB p.150-152 and RQ-BOX-001 Finding 3:
    - NO_COVER: 0-4 lines blocked (of 16)
    - HALF_COVER: 5-8 lines blocked (+2 AC, +1 Reflex)
    - THREE_QUARTERS_COVER: 9-12 lines blocked (+5 AC, +2 Reflex)
    - TOTAL_COVER: 13-16 lines blocked (untargetable)
    """
    NO_COVER = "no_cover"
    HALF_COVER = "half_cover"
    THREE_QUARTERS_COVER = "three_quarters_cover"
    TOTAL_COVER = "total_cover"


# ==============================================================================
# COVER RESULT DATACLASS
# ==============================================================================

@dataclass(frozen=True)
class CoverResult:
    """Result of cover calculation between attacker and defender.

    Immutable for determinism and event logging.
    """

    cover_degree: CoverDegree
    """The degree of cover the defender has."""

    ac_bonus: int
    """AC bonus from cover (0, +2, +5, or N/A for total)."""

    reflex_bonus: int
    """Reflex save bonus from cover (0, +1, +2, or N/A for total)."""

    lines_blocked: int
    """Number of corner-to-corner lines blocked."""

    lines_total: int
    """Total number of lines traced (typically 16 for Medium vs Medium)."""

    blocks_targeting: bool
    """True if defender cannot be targeted (total cover)."""

    attacker_pos: Position
    """Attacker's position."""

    defender_pos: Position
    """Defender's position."""

    def to_dict(self) -> dict:
        """Serialize for event logging."""
        return {
            "cover_degree": self.cover_degree.value,
            "ac_bonus": self.ac_bonus,
            "reflex_bonus": self.reflex_bonus,
            "lines_blocked": self.lines_blocked,
            "lines_total": self.lines_total,
            "blocks_targeting": self.blocks_targeting,
            "attacker_pos": self.attacker_pos.to_dict(),
            "defender_pos": self.defender_pos.to_dict(),
        }


# ==============================================================================
# COVER CONSTANTS
# ==============================================================================

# Cover thresholds per RQ-BOX-001 Finding 3 table
# For 16 total lines (Medium vs Medium):
COVER_THRESHOLDS = {
    # (min_blocked, max_blocked): (CoverDegree, ac_bonus, reflex_bonus)
    (0, 4): (CoverDegree.NO_COVER, 0, 0),
    (5, 8): (CoverDegree.HALF_COVER, 2, 1),
    (9, 12): (CoverDegree.THREE_QUARTERS_COVER, 5, 2),
    (13, 16): (CoverDegree.TOTAL_COVER, 0, 0),  # Untargetable, bonuses N/A
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_square_corners(pos: Position) -> List[Tuple[float, float]]:
    """Get the 4 corners of a 5-foot square.

    Returns corners in order: NW, NE, SE, SW.
    Position represents the cell center; corners are at ±0.5 offset.

    Grid coordinate system (screen coords, Y increases downward):
    - NW corner: (x - 0.5, y - 0.5)
    - NE corner: (x + 0.5, y - 0.5)
    - SE corner: (x + 0.5, y + 0.5)
    - SW corner: (x - 0.5, y + 0.5)

    Args:
        pos: Grid position (cell center)

    Returns:
        List of 4 corners as (x, y) float tuples

    Example:
        Position(3, 5) returns:
        - NW: (2.5, 4.5)
        - NE: (3.5, 4.5)
        - SE: (3.5, 5.5)
        - SW: (2.5, 5.5)
    """
    x, y = float(pos.x), float(pos.y)
    return [
        (x - 0.5, y - 0.5),  # NW
        (x + 0.5, y - 0.5),  # NE
        (x + 0.5, y + 0.5),  # SE
        (x - 0.5, y + 0.5),  # SW
    ]


def get_cells_along_line(
    start: Tuple[float, float],
    end: Tuple[float, float]
) -> List[Position]:
    """Get all grid cells that a line between two corners passes through.

    Uses a float-based line traversal algorithm to find all cells
    intersected by the line from start to end.

    Args:
        start: Starting corner (x, y) as floats
        end: Ending corner (x, y) as floats

    Returns:
        List of Position objects for cells the line passes through
    """
    x0, y0 = start
    x1, y1 = end

    # Handle the case where start and end are the same point
    if abs(x1 - x0) < 1e-9 and abs(y1 - y0) < 1e-9:
        return [Position(x=int(math.floor(x0)), y=int(math.floor(y0)))]

    cells = []
    visited = set()

    dx = x1 - x0
    dy = y1 - y0

    # Number of steps based on the longer dimension
    steps = max(abs(dx), abs(dy))
    if steps < 1:
        steps = 1

    # Use more steps for accuracy (sample along the line)
    num_samples = int(steps * 10) + 1

    for i in range(num_samples + 1):
        t = i / num_samples if num_samples > 0 else 0
        x = x0 + t * dx
        y = y0 + t * dy

        # Convert to grid cell (floor for cells, handle exact corners)
        # When exactly on a corner/edge, the line conceptually passes through
        # adjacent cells. For cover purposes, we use floor.
        cell_x = int(math.floor(x)) if x != math.floor(x) else int(x)
        cell_y = int(math.floor(y)) if y != math.floor(y) else int(y)

        # Handle corner cases - when on exact integer boundary
        if x == math.floor(x) and x == x0:
            # Starting on vertical edge - could be in cell to left
            cell_x = int(x) if dx >= 0 else int(x) - 1
        if y == math.floor(y) and y == y0:
            # Starting on horizontal edge - could be in cell above
            cell_y = int(y) if dy >= 0 else int(y) - 1

        key = (cell_x, cell_y)
        if key not in visited:
            visited.add(key)
            cells.append(Position(x=cell_x, y=cell_y))

    return cells


def get_border_crossings(
    start: Tuple[float, float],
    end: Tuple[float, float]
) -> List[Tuple[Position, Direction]]:
    """Get all grid borders that a line crosses.

    Returns a list of (cell_position, direction) pairs indicating
    which cell borders the line crosses and from which direction.

    Args:
        start: Starting corner (x, y) as floats
        end: Ending corner (x, y) as floats

    Returns:
        List of (Position, Direction) tuples for each border crossed
    """
    x0, y0 = start
    x1, y1 = end

    crossings = []

    dx = x1 - x0
    dy = y1 - y0

    # Find all vertical border crossings (integer x values)
    if abs(dx) > 1e-9:
        x_min, x_max = min(x0, x1), max(x0, x1)
        for x_border in range(int(math.floor(x_min)) + 1, int(math.floor(x_max)) + 1):
            if x_min < x_border < x_max:
                # Calculate y at this x
                t = (x_border - x0) / dx
                y_at_border = y0 + t * dy

                # Determine which cells this border is between
                cell_y = int(math.floor(y_at_border))

                if dx > 0:
                    # Moving east: crossing west border of cell (x_border, cell_y)
                    crossings.append((Position(x=x_border, y=cell_y), Direction.W))
                else:
                    # Moving west: crossing east border of cell (x_border - 1, cell_y)
                    crossings.append((Position(x=x_border - 1, y=cell_y), Direction.E))

    # Find all horizontal border crossings (integer y values)
    if abs(dy) > 1e-9:
        y_min, y_max = min(y0, y1), max(y0, y1)
        for y_border in range(int(math.floor(y_min)) + 1, int(math.floor(y_max)) + 1):
            if y_min < y_border < y_max:
                # Calculate x at this y
                t = (y_border - y0) / dy
                x_at_border = x0 + t * dx

                # Determine which cells this border is between
                cell_x = int(math.floor(x_at_border))

                if dy > 0:
                    # Moving south: crossing north border of cell (cell_x, y_border)
                    crossings.append((Position(x=cell_x, y=y_border), Direction.N))
                else:
                    # Moving north: crossing south border of cell (cell_x, y_border - 1)
                    crossings.append((Position(x=cell_x, y=y_border - 1), Direction.S))

    return crossings


def trace_corner_line(
    start: Tuple[float, float],
    end: Tuple[float, float],
    grid: BattleGrid,
    check_type: str = "loe"
) -> bool:
    """Trace a line between two corners, checking for blockage.

    For each cell the line passes through, checks cell_mask.blocks_loe()
    or blocks_los() (depending on check_type). Also checks border_masks
    for any border the line crosses.

    Args:
        start: Starting corner (x, y) as floats
        end: Ending corner (x, y) as floats
        grid: BattleGrid to query
        check_type: "loe" for line of effect, "los" for line of sight

    Returns:
        True if line is blocked, False if clear
    """
    # Get all cells the line passes through
    cells = get_cells_along_line(start, end)

    # Check each cell (excluding start and end cells if they contain combatants)
    # For cover, we check intermediate cells only
    for cell_pos in cells:
        if not grid.in_bounds(cell_pos):
            continue

        cell = grid.get_cell(cell_pos)

        if check_type == "loe":
            if cell.cell_mask.blocks_loe():
                return True
        else:  # los
            if cell.cell_mask.blocks_los():
                return True

    # Check border crossings
    crossings = get_border_crossings(start, end)
    for cell_pos, direction in crossings:
        if not grid.in_bounds(cell_pos):
            continue

        border_mask = grid.get_border(cell_pos, direction)

        if check_type == "loe":
            if border_mask.blocks_loe():
                return True
        else:  # los
            if border_mask.blocks_los():
                return True

    return False


def get_footprint_squares(pos: Position, size: SizeCategory) -> List[Position]:
    """Get all squares occupied by a creature of given size.

    For Medium and smaller, returns just the position.
    For Large (2x2), returns 4 positions with pos as top-left.
    For Huge (3x3), returns 9 positions, etc.

    Args:
        pos: Top-left corner position (anchor point)
        size: Size category of the creature

    Returns:
        List of all positions occupied
    """
    grid_size = size.grid_size()
    positions = []
    for dy in range(grid_size):
        for dx in range(grid_size):
            positions.append(Position(x=pos.x + dx, y=pos.y + dy))
    return positions


# ==============================================================================
# MAIN COVER CALCULATION
# ==============================================================================

def calculate_cover(
    attacker_pos: Position,
    defender_pos: Position,
    grid: BattleGrid,
    attacker_size: SizeCategory = SizeCategory.MEDIUM,
    defender_size: SizeCategory = SizeCategory.MEDIUM,
    check_type: str = "loe"
) -> CoverResult:
    """Calculate cover between attacker and defender using RAW 3.5e rules.

    Implements the corner-to-corner cover algorithm from PHB p.150-152:
    1. Get corners of attacker's square(s)
    2. Get corners of defender's square(s)
    3. Trace lines from each attacker corner to each defender corner
    4. Count blocked lines and determine cover degree

    For Large+ creatures, uses the most favorable square for each.

    Args:
        attacker_pos: Attacker's position (top-left for Large+)
        defender_pos: Defender's position (top-left for Large+)
        grid: BattleGrid for LOS/LOE queries
        attacker_size: Attacker's size category
        defender_size: Defender's size category
        check_type: "loe" or "los" for which blocking check to use

    Returns:
        CoverResult with cover degree, bonuses, and line counts
    """
    # For Medium vs Medium, we trace from all 4 corners to all 4 corners = 16 lines
    # For Large+ creatures, we pick the optimal square for each

    # Get attacker's squares and find the optimal one (closest to defender)
    attacker_squares = get_footprint_squares(attacker_pos, attacker_size)

    # Find the attacker square closest to defender (for optimal corner selection)
    best_attacker_square = attacker_pos
    best_distance = float('inf')
    for sq in attacker_squares:
        dist = abs(sq.x - defender_pos.x) + abs(sq.y - defender_pos.y)
        if dist < best_distance:
            best_distance = dist
            best_attacker_square = sq

    # Get defender's squares and find the optimal one (closest to attacker)
    defender_squares = get_footprint_squares(defender_pos, defender_size)

    best_defender_square = defender_pos
    best_distance = float('inf')
    for sq in defender_squares:
        dist = abs(sq.x - attacker_pos.x) + abs(sq.y - attacker_pos.y)
        if dist < best_distance:
            best_distance = dist
            best_defender_square = sq

    # Get corners of the selected squares
    attacker_corners = get_square_corners(best_attacker_square)
    defender_corners = get_square_corners(best_defender_square)

    # Trace all 16 lines (4 attacker corners × 4 defender corners)
    lines_total = len(attacker_corners) * len(defender_corners)
    lines_blocked = 0

    for atk_corner in attacker_corners:
        for def_corner in defender_corners:
            if trace_corner_line(atk_corner, def_corner, grid, check_type):
                lines_blocked += 1

    # Determine cover degree from blocked line count
    # Scale thresholds based on total lines if not 16
    cover_degree = CoverDegree.NO_COVER
    ac_bonus = 0
    reflex_bonus = 0

    if lines_total == 16:
        # Use standard thresholds
        for (min_blocked, max_blocked), (degree, ac, reflex) in COVER_THRESHOLDS.items():
            if min_blocked <= lines_blocked <= max_blocked:
                cover_degree = degree
                ac_bonus = ac
                reflex_bonus = reflex
                break
    else:
        # Scale thresholds proportionally
        ratio = lines_blocked / lines_total if lines_total > 0 else 0
        if ratio <= 0.25:
            cover_degree = CoverDegree.NO_COVER
            ac_bonus = 0
            reflex_bonus = 0
        elif ratio <= 0.5:
            cover_degree = CoverDegree.HALF_COVER
            ac_bonus = 2
            reflex_bonus = 1
        elif ratio <= 0.75:
            cover_degree = CoverDegree.THREE_QUARTERS_COVER
            ac_bonus = 5
            reflex_bonus = 2
        else:
            cover_degree = CoverDegree.TOTAL_COVER
            ac_bonus = 0
            reflex_bonus = 0

    blocks_targeting = (cover_degree == CoverDegree.TOTAL_COVER)

    return CoverResult(
        cover_degree=cover_degree,
        ac_bonus=ac_bonus,
        reflex_bonus=reflex_bonus,
        lines_blocked=lines_blocked,
        lines_total=lines_total,
        blocks_targeting=blocks_targeting,
        attacker_pos=attacker_pos,
        defender_pos=defender_pos,
    )


def calculate_cover_from_positions(
    attacker_pos: Position,
    defender_pos: Position,
    grid: BattleGrid
) -> CoverResult:
    """Simplified cover calculation for Medium creatures.

    Convenience wrapper for the common case of Medium vs Medium.

    Args:
        attacker_pos: Attacker's position
        defender_pos: Defender's position
        grid: BattleGrid for queries

    Returns:
        CoverResult
    """
    return calculate_cover(
        attacker_pos=attacker_pos,
        defender_pos=defender_pos,
        grid=grid,
        attacker_size=SizeCategory.MEDIUM,
        defender_size=SizeCategory.MEDIUM,
    )


def has_cover(
    attacker_pos: Position,
    defender_pos: Position,
    grid: BattleGrid
) -> bool:
    """Quick check if defender has any cover from attacker.

    Args:
        attacker_pos: Attacker's position
        defender_pos: Defender's position
        grid: BattleGrid for queries

    Returns:
        True if defender has at least half cover
    """
    result = calculate_cover_from_positions(attacker_pos, defender_pos, grid)
    return result.cover_degree != CoverDegree.NO_COVER


def has_total_cover(
    attacker_pos: Position,
    defender_pos: Position,
    grid: BattleGrid
) -> bool:
    """Quick check if defender has total cover from attacker.

    Args:
        attacker_pos: Attacker's position
        defender_pos: Defender's position
        grid: BattleGrid for queries

    Returns:
        True if defender has total cover (cannot be targeted)
    """
    result = calculate_cover_from_positions(attacker_pos, defender_pos, grid)
    return result.blocks_targeting
