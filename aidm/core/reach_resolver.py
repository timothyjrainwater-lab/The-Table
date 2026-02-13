"""Reach weapon mechanics and threatened square calculation.

Implements D&D 3.5e reach rules (PHB p.137, p.157):
- Natural reach by creature size
- Reach weapon reach (don't threaten adjacent)
- Threatened square calculation for AoO eligibility
- Large+ creature multi-square footprints

WO-006: Reach Weapons and Threatened Squares
Reference: PHB p.137 (Attacks of Opportunity), p.157 (Reach Weapons)
"""

from typing import List, Optional, Tuple

from aidm.schemas.position import Position
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid


# ==============================================================================
# REACH CONSTANTS — Natural reach by size (PHB p.149)
# ==============================================================================

# Default reach for "tall" creatures (bipedal) in feet
# Long creatures (quadrupeds) use reduced reach values
DEFAULT_REACH_BY_SIZE_TALL = {
    SizeCategory.FINE: 0,
    SizeCategory.DIMINUTIVE: 0,
    SizeCategory.TINY: 0,
    SizeCategory.SMALL: 5,
    SizeCategory.MEDIUM: 5,
    SizeCategory.LARGE: 10,
    SizeCategory.HUGE: 15,
    SizeCategory.GARGANTUAN: 20,
    SizeCategory.COLOSSAL: 30,
}

# Reach for "long" creatures (quadrupeds, serpentine) in feet
DEFAULT_REACH_BY_SIZE_LONG = {
    SizeCategory.FINE: 0,
    SizeCategory.DIMINUTIVE: 0,
    SizeCategory.TINY: 0,
    SizeCategory.SMALL: 5,
    SizeCategory.MEDIUM: 5,
    SizeCategory.LARGE: 5,
    SizeCategory.HUGE: 10,
    SizeCategory.GARGANTUAN: 15,
    SizeCategory.COLOSSAL: 20,
}


# ==============================================================================
# CORE REACH FUNCTIONS
# ==============================================================================

def get_natural_reach(size: SizeCategory, is_long: bool = False) -> int:
    """Get natural reach in feet based on creature size.

    Natural reach is the maximum distance at which a creature can make
    melee attacks without a reach weapon (PHB p.149).

    Args:
        size: Creature size category
        is_long: True for quadrupeds/long creatures (reduced reach)

    Returns:
        Natural reach in feet (0, 5, 10, 15, 20, or 30)
    """
    if is_long:
        return DEFAULT_REACH_BY_SIZE_LONG[size]
    return DEFAULT_REACH_BY_SIZE_TALL[size]


def get_weapon_reach(base_reach_ft: int, weapon_reach_ft: int) -> int:
    """Calculate effective reach when using a reach weapon.

    Reach weapons (longspear, glaive, etc.) grant extended reach but
    cannot be used against adjacent foes (PHB p.157).

    For a Medium creature:
    - No weapon: 5ft reach, threatens adjacent
    - Longspear: 10ft reach, threatens at distance 2 only

    Args:
        base_reach_ft: Natural reach in feet (usually 5 for Medium)
        weapon_reach_ft: Weapon's reach property in feet (10 for longspear)

    Returns:
        Effective reach in feet for threat calculation
    """
    # Reach weapons replace natural reach, they don't add to it
    # A Medium creature with a longspear (10ft) has 10ft reach, not 15ft
    return weapon_reach_ft


def _discrete_distance(pos1: Position, pos2: Position) -> int:
    """Calculate discrete distance in squares (not feet).

    Uses Chebyshev distance (max of dx, dy) for square grid.
    This matches D&D 3.5e discrete distance for reach purposes:
    - Distance 1 = adjacent (5ft)
    - Distance 2 = 10ft
    - Distance 3 = 15ft

    Note: This differs from Position.distance_to() which uses 1-2-1-2
    diagonal movement for actual movement costs. For reach/threat
    calculations, we use simple Chebyshev distance.

    Args:
        pos1: First position
        pos2: Second position

    Returns:
        Distance in squares (Chebyshev distance)
    """
    dx = abs(pos1.x - pos2.x)
    dy = abs(pos1.y - pos2.y)
    return max(dx, dy)


def _get_occupied_squares(entity_pos: Position, size: SizeCategory) -> List[Position]:
    """Get all squares occupied by an entity.

    Args:
        entity_pos: Top-left corner of entity footprint
        size: Entity size category

    Returns:
        List of all occupied positions
    """
    grid_size = size.grid_size()
    positions = []
    for dy in range(grid_size):
        for dx in range(grid_size):
            positions.append(Position(x=entity_pos.x + dx, y=entity_pos.y + dy))
    return positions


def _get_minimum_distance_to_occupied(
    target_pos: Position,
    entity_pos: Position,
    size: SizeCategory
) -> int:
    """Get minimum discrete distance from target to any occupied square.

    Args:
        target_pos: Position to measure from
        entity_pos: Top-left of entity footprint
        size: Entity size category

    Returns:
        Minimum Chebyshev distance to any occupied square
    """
    occupied = _get_occupied_squares(entity_pos, size)
    min_dist = float('inf')
    for occ_pos in occupied:
        dist = _discrete_distance(target_pos, occ_pos)
        if dist < min_dist:
            min_dist = dist
    return int(min_dist) if min_dist != float('inf') else 0


def get_threatened_squares(
    entity_pos: Position,
    size: SizeCategory,
    reach_ft: int,
    grid_width: int = 100,
    grid_height: int = 100
) -> List[Position]:
    """Get all squares threatened by an entity at given position.

    Threatened squares are those within reach where the entity can
    make attacks of opportunity (PHB p.137).

    For 5ft reach (natural): threatens all adjacent squares (distance 1)
    For 10ft reach (reach weapon): threatens ring at distance 2 ONLY
    For 15ft reach: threatens ring at distance 3 ONLY

    Large+ creatures threaten from all occupied squares.

    Args:
        entity_pos: Top-left corner of entity footprint
        size: Entity size category
        reach_ft: Reach in feet (5, 10, 15, etc.)
        grid_width: Maximum grid width for bounds checking
        grid_height: Maximum grid height for bounds checking

    Returns:
        List of threatened positions (deduplicated, sorted)
    """
    if reach_ft <= 0:
        return []

    # Convert reach to squares
    reach_squares = reach_ft // 5

    # Get all squares occupied by this entity
    occupied = _get_occupied_squares(entity_pos, size)
    occupied_set = set(occupied)

    # For each occupied square, find threatened squares at exact reach distance
    # Natural reach (5ft) threatens adjacent (distance 1)
    # Reach weapon threatens at weapon reach distance only
    threatened_set = set()

    # Determine threat range
    # Natural reach = 5ft: threaten distance 1
    # Reach weapon (10ft): threaten distance 2 only (not 1)
    # Natural 10ft (Large): threaten distances 1 and 2
    # For this function, we assume reach_ft is the total reach
    # The distinction between natural vs weapon reach is handled by caller

    # Search area around all occupied squares
    min_x = min(p.x for p in occupied) - reach_squares
    max_x = max(p.x for p in occupied) + reach_squares
    min_y = min(p.y for p in occupied) - reach_squares
    max_y = max(p.y for p in occupied) + reach_squares

    for y in range(max(0, min_y), min(grid_height, max_y + 1)):
        for x in range(max(0, min_x), min(grid_width, max_x + 1)):
            candidate = Position(x=x, y=y)

            # Skip occupied squares
            if candidate in occupied_set:
                continue

            # Find minimum distance to any occupied square
            min_dist = _get_minimum_distance_to_occupied(candidate, entity_pos, size)

            # Check if within reach
            # For natural reach: distance 1 to reach_squares
            # For reach weapons: only exact reach_squares distance
            # This function handles natural reach (all distances up to reach)
            if 1 <= min_dist <= reach_squares:
                threatened_set.add(candidate)

    # Sort for deterministic ordering
    return sorted(threatened_set, key=lambda p: (p.x, p.y))


def get_threatened_squares_for_entity(
    grid: BattleGrid,
    entity_id: str,
    reach_ft: int
) -> List[Position]:
    """Get threatened squares for an entity tracked on a BattleGrid.

    Convenience function that looks up entity position and size from grid.

    Args:
        grid: BattleGrid with entity tracking
        entity_id: Entity identifier
        reach_ft: Reach in feet

    Returns:
        List of threatened positions, empty if entity not found
    """
    pos = grid.get_entity_position(entity_id)
    if pos is None:
        return []

    # Look up size from grid's entity tracking
    if entity_id not in grid._entities:
        return []

    _, size = grid._entities[entity_id]

    return get_threatened_squares(
        entity_pos=pos,
        size=size,
        reach_ft=reach_ft,
        grid_width=grid.width,
        grid_height=grid.height
    )


def is_square_threatened(
    entity_pos: Position,
    size: SizeCategory,
    reach_ft: int,
    target_pos: Position
) -> bool:
    """Check if a specific square is threatened by an entity.

    More efficient than get_threatened_squares for single-square checks.

    Args:
        entity_pos: Top-left corner of entity footprint
        size: Entity size category
        reach_ft: Reach in feet
        target_pos: Position to check

    Returns:
        True if target_pos is threatened
    """
    if reach_ft <= 0:
        return False

    reach_squares = reach_ft // 5

    # Check if target is in any occupied square
    occupied = _get_occupied_squares(entity_pos, size)
    if target_pos in occupied:
        return False

    # Find minimum distance to any occupied square
    min_dist = _get_minimum_distance_to_occupied(target_pos, entity_pos, size)

    # Threatened if within reach range
    return 1 <= min_dist <= reach_squares


def can_threaten(
    attacker_pos: Position,
    attacker_size: SizeCategory,
    reach_ft: int,
    target_pos: Position,
    target_size: SizeCategory
) -> bool:
    """Check if attacker can threaten any square occupied by target.

    Used for determining if AoO is possible against a target creature.

    Args:
        attacker_pos: Top-left of attacker footprint
        attacker_size: Attacker size category
        reach_ft: Attacker's reach in feet
        target_pos: Top-left of target footprint
        target_size: Target size category

    Returns:
        True if attacker threatens any square occupied by target
    """
    # Get all squares occupied by target
    target_occupied = _get_occupied_squares(target_pos, target_size)

    # Check if any target square is threatened
    for pos in target_occupied:
        if is_square_threatened(attacker_pos, attacker_size, reach_ft, pos):
            return True

    return False


def get_aoo_eligible_squares(
    entity_pos: Position,
    size: SizeCategory,
    natural_reach_ft: int,
    weapon_reach_ft: int,
    grid_width: int = 100,
    grid_height: int = 100
) -> List[Position]:
    """Get squares where entity can make attacks of opportunity.

    Key rule (PHB p.157): Reach weapons threaten at their reach distance
    but NOT adjacent squares. An entity with a reach weapon only threatens
    at the weapon's reach, not their natural reach.

    Medium creature with 5ft natural + 10ft weapon:
    - Threatens at distance 2 only (10ft)
    - Does NOT threaten adjacent (distance 1)

    Medium creature with 5ft natural + unarmed/normal weapon:
    - Threatens at distance 1 only (5ft)

    Large creature with 10ft natural + 15ft weapon:
    - Threatens at distance 3 only (15ft)
    - Does NOT threaten at distances 1-2

    Args:
        entity_pos: Top-left corner of entity footprint
        size: Entity size category
        natural_reach_ft: Natural reach in feet (5 for Medium, 10 for Large, etc.)
        weapon_reach_ft: Weapon reach in feet (0 if not a reach weapon)
        grid_width: Maximum grid width for bounds checking
        grid_height: Maximum grid height for bounds checking

    Returns:
        List of AoO-eligible positions
    """
    if weapon_reach_ft > natural_reach_ft:
        # Using reach weapon: threaten at weapon reach distance only
        return _get_ring_at_distance(
            entity_pos=entity_pos,
            size=size,
            distance_squares=weapon_reach_ft // 5,
            grid_width=grid_width,
            grid_height=grid_height
        )
    else:
        # Using natural reach or non-reach weapon
        return get_threatened_squares(
            entity_pos=entity_pos,
            size=size,
            reach_ft=natural_reach_ft,
            grid_width=grid_width,
            grid_height=grid_height
        )


def _get_ring_at_distance(
    entity_pos: Position,
    size: SizeCategory,
    distance_squares: int,
    grid_width: int = 100,
    grid_height: int = 100
) -> List[Position]:
    """Get squares at exactly the specified distance from entity.

    Used for reach weapons which only threaten at exact reach distance.

    Args:
        entity_pos: Top-left corner of entity footprint
        size: Entity size category
        distance_squares: Exact distance in squares
        grid_width: Maximum grid width for bounds checking
        grid_height: Maximum grid height for bounds checking

    Returns:
        List of positions at exactly the given distance
    """
    if distance_squares <= 0:
        return []

    occupied = _get_occupied_squares(entity_pos, size)
    occupied_set = set(occupied)

    ring_set = set()

    # Search area around all occupied squares
    min_x = min(p.x for p in occupied) - distance_squares
    max_x = max(p.x for p in occupied) + distance_squares
    min_y = min(p.y for p in occupied) - distance_squares
    max_y = max(p.y for p in occupied) + distance_squares

    for y in range(max(0, min_y), min(grid_height, max_y + 1)):
        for x in range(max(0, min_x), min(grid_width, max_x + 1)):
            candidate = Position(x=x, y=y)

            # Skip occupied squares
            if candidate in occupied_set:
                continue

            # Find minimum distance to any occupied square
            min_dist = _get_minimum_distance_to_occupied(candidate, entity_pos, size)

            # Only include exact distance
            if min_dist == distance_squares:
                ring_set.add(candidate)

    return sorted(ring_set, key=lambda p: (p.x, p.y))
