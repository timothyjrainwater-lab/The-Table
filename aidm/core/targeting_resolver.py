"""Targeting & Visibility resolver for CP-18A-T&V.

Implements deterministic target legality evaluation, LoS/LoE checks.

All functions are pure: (state, params) → (result)
No RNG access, no state mutation.
"""

import logging
from typing import List, Set
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.targeting import (
    VisibilityState,
    TargetingLegalityResult,
    VisibilityBlockReason,
    RuleCitation,
    GridPoint
)

logger = logging.getLogger(__name__)


# PHB citation for targeting rules
PHB_TARGETING_CITATION = RuleCitation(
    source_id="681f92bc94ff",  # PHB
    page=147,
    section="Line of Effect"
)

PHB_RANGE_CITATION = RuleCitation(
    source_id="681f92bc94ff",  # PHB
    page=148,
    section="Range"
)


def get_entity_position(world_state: WorldState, entity_id: str) -> GridPoint:
    """Get entity's grid position.

    Args:
        world_state: Current world state
        entity_id: Entity ID

    Returns:
        GridPoint position

    Raises:
        ValueError: If entity not found

    CP-18A-T&V backward compatibility:
    - If entity has no position, defaults to (0, 0) for legacy compatibility
    - This ensures existing tests without positions continue to work
    """
    entity = world_state.entities.get(entity_id)
    if entity is None:
        raise ValueError(f"Entity not found: {entity_id}")

    pos = entity.get(EF.POSITION)
    if pos is None:
        # Default position for backward compatibility with pre-CP-18A-T&V tests
        logger.warning("Entity '%s' has no position field; defaulting to (0, 0)", entity_id)
        return GridPoint(0, 0)

    if isinstance(pos, dict):
        return GridPoint.from_dict(pos)
    elif isinstance(pos, GridPoint):
        return pos
    else:
        raise ValueError(f"Invalid position format for {entity_id}: {type(pos)}")


def bresenham_line(start: GridPoint, end: GridPoint) -> List[GridPoint]:
    """Bresenham's line algorithm for grid raycast.

    Returns all grid points from start to end (inclusive).

    Args:
        start: Starting grid point
        end: Ending grid point

    Returns:
        List of grid points along line (including start and end)
    """
    points = []

    dx = abs(end.x - start.x)
    dy = abs(end.y - start.y)
    sx = 1 if start.x < end.x else -1
    sy = 1 if start.y < end.y else -1
    err = dx - dy

    x, y = start.x, start.y

    while True:
        points.append(GridPoint(x, y))

        if x == end.x and y == end.y:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return points


def is_terrain_opaque(world_state: WorldState, pos: GridPoint) -> bool:
    """Check if terrain at position blocks LoS/LoE.

    Args:
        world_state: Current world state
        pos: Grid position to check

    Returns:
        True if terrain blocks LoS/LoE, False otherwise

    CP-18A-T&V: Minimal implementation. Full terrain system deferred.
    """
    # Check if there's a terrain map
    terrain = world_state.entities.get("_terrain", {}).get("map", {})

    # Convert position to string key (e.g., "5,10")
    key = f"{pos.x},{pos.y}"

    # Check if this position is marked as blocking
    cell = terrain.get(key, {})
    return cell.get("blocks_loe", False) or cell.get("blocks_los", False)


def check_line_of_effect(
    world_state: WorldState,
    observer_id: str,
    target_id: str
) -> bool:
    """Check if there is a clear Line of Effect (LoE) between observer and target.

    PHB p. 147: "To have line of effect, a line from one space to another
    space can't pass through solid barriers (such as walls)."

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID

    Returns:
        True if LoE is clear, False if blocked

    CP-18A-T&V constraints:
    - Computed via grid raycast (Bresenham's algorithm)
    - Any opaque terrain square blocks LoE
    - Creatures do NOT block LoE in this packet (deferred to cover/soft-cover)
    """
    observer_pos = get_entity_position(world_state, observer_id)
    target_pos = get_entity_position(world_state, target_id)

    # Get all grid points along line
    line_points = bresenham_line(observer_pos, target_pos)

    # Check each point (excluding start and end) for opaque terrain
    for point in line_points[1:-1]:  # Skip observer and target positions
        if is_terrain_opaque(world_state, point):
            return False

    return True


def check_line_of_sight(
    world_state: WorldState,
    observer_id: str,
    target_id: str
) -> bool:
    """Check if there is a clear Line of Sight (LoS) between observer and target.

    PHB p. 147: "To have line of sight, a line from one space to another
    space can't pass through solid barriers that block sight."

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID

    Returns:
        True if LoS is clear, False if blocked

    CP-18A-T&V constraints:
    - Same geometry as LoE (uses identical raycast)
    - Light level modifiers are binary only (sufficient / insufficient)
    - No perception checks (deferred)
    """
    # In CP-18A-T&V minimal scope: LoS = LoE
    # Future packets may differentiate (transparent but not passable, etc.)
    return check_line_of_effect(world_state, observer_id, target_id)


def check_range(
    world_state: WorldState,
    observer_id: str,
    target_id: str,
    max_range: int
) -> bool:
    """Check if target is within range.

    PHB p. 148: "The maximum range is the farthest distance away a target can be
    for you to use a ranged weapon or spell against it."

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID
        max_range: Maximum range (in grid squares)

    Returns:
        True if within range, False otherwise

    CP-18A-T&V constraints:
    - Uses GridPoint.distance_to() (implements CP-14 diagonal constraints)
    - No range increment penalties (deferred)
    """
    observer_pos = get_entity_position(world_state, observer_id)
    target_pos = get_entity_position(world_state, target_id)

    distance = observer_pos.distance_to(target_pos)
    return distance <= max_range


def evaluate_visibility(
    world_state: WorldState,
    observer_id: str,
    target_id: str
) -> VisibilityState:
    """Evaluate binary visibility state between observer and target.

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID

    Returns:
        VisibilityState (visible or not, with reason if blocked)

    CP-18A-T&V contract: Binary visibility only. No probabilistic states.
    """
    # Check LoS first (most common blocker)
    if not check_line_of_sight(world_state, observer_id, target_id):
        return VisibilityState(
            observer_id=observer_id,
            target_id=target_id,
            is_visible=False,
            reason=VisibilityBlockReason.LOS_BLOCKED
        )

    # Check LoE (required for targeting)
    if not check_line_of_effect(world_state, observer_id, target_id):
        return VisibilityState(
            observer_id=observer_id,
            target_id=target_id,
            is_visible=False,
            reason=VisibilityBlockReason.LOE_BLOCKED
        )

    # If both clear, target is visible
    return VisibilityState(
        observer_id=observer_id,
        target_id=target_id,
        is_visible=True,
        reason=None
    )


def evaluate_target_legality(
    actor_id: str,
    target_id: str,
    world_state: WorldState,
    max_range: int = 100  # Default: 100 squares (500 ft)
) -> TargetingLegalityResult:
    """Evaluate whether target is legally targetable by actor.

    This is the core CP-18A-T&V proof function. It answers:
    "Is this target legally targetable by this actor, right now, under RAW constraints
    we can deterministically prove?"

    Args:
        actor_id: Acting entity ID
        target_id: Target entity ID
        world_state: Current world state
        max_range: Maximum targeting range (default 100 squares)

    Returns:
        TargetingLegalityResult (legal or not, with structured reason if illegal)

    Contract:
    - Pure function (no side effects)
    - No RNG access
    - Deterministic (same inputs → identical result)
    - Event-loggable and hash-stable
    """
    # Validate entities exist
    if actor_id not in world_state.entities:
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.TARGET_NOT_VISIBLE,
            citations=[PHB_TARGETING_CITATION]
        )

    if target_id not in world_state.entities:
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.TARGET_NOT_VISIBLE,
            citations=[PHB_TARGETING_CITATION]
        )

    # Check range first (fast fail)
    if not check_range(world_state, actor_id, target_id, max_range):
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.OUT_OF_RANGE,
            citations=[PHB_RANGE_CITATION]
        )

    # Check LoE (required for all targeting)
    if not check_line_of_effect(world_state, actor_id, target_id):
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.LOE_BLOCKED,
            citations=[PHB_TARGETING_CITATION]
        )

    # Check LoS (required for most attacks/spells)
    if not check_line_of_sight(world_state, actor_id, target_id):
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.LOS_BLOCKED,
            citations=[PHB_TARGETING_CITATION]
        )

    # All checks passed: targeting is legal
    return TargetingLegalityResult(
        is_legal=True,
        failure_reason=None,
        citations=[PHB_TARGETING_CITATION, PHB_RANGE_CITATION]
    )
