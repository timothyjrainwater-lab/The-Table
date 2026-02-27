"""Movement resolver for CP-16 — Multi-square movement with speed enforcement.

Implements D&D 3.5e movement rules (PHB p.143-148):
- Entities move up to their base speed per move action
- Path must be contiguous (each step adjacent to previous)
- Cannot move through squares occupied by enemies
- Can move through squares occupied by allies
- Diagonal movement uses 5/10/5/10 alternating cost (PHB p.148)
- Terrain movement cost multipliers applied per square entered
- AoO triggered at each square departed (handled by play_loop)

CP-16 SCOPE:
- FullMoveIntent construction from (actor, destination) pair
- BFS pathfinding on flat grid
- Speed enforcement against EF.BASE_SPEED
- Occupied-square validation (enemies block, allies don't)
- Terrain cost integration via terrain_resolver.get_movement_cost()
- No elevation, no swimming/climbing, no special movement modes

DESIGN PRINCIPLES:
- Pure functions, no side effects
- Deterministic pathfinding (BFS with sorted neighbor order)
- Returns FullMoveIntent or error string — never raises
"""

from collections import deque
import heapq
from typing import Dict, List, Optional, Tuple, Any

from aidm.schemas.attack import FullMoveIntent
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.state import WorldState


def _get_occupied_squares(
    world_state: WorldState,
    actor_id: str,
) -> Tuple[set, set]:
    """Get sets of squares occupied by enemies and allies relative to actor.

    Returns:
        (enemy_squares, ally_squares) — sets of (x, y) tuples
    """
    actor = world_state.entities.get(actor_id, {})
    actor_team = actor.get(EF.TEAM, "party")

    enemy_squares = set()
    ally_squares = set()

    for eid, entity in world_state.entities.items():
        if eid == actor_id:
            continue
        if entity.get(EF.DEFEATED, False):
            continue
        pos = entity.get(EF.POSITION)
        if pos is None:
            continue
        sq = (pos["x"], pos["y"])
        if entity.get(EF.TEAM) == actor_team:
            ally_squares.add(sq)
        else:
            enemy_squares.add(sq)

    return enemy_squares, ally_squares


def _step_cost(
    prev: Position,
    pos: Position,
    diagonal_count: int,
    terrain_mult: int = 1,
) -> Tuple[int, int]:
    """Calculate movement cost for a single step.

    Args:
        prev: Previous position
        pos: Target position
        diagonal_count: Running count of diagonals taken so far
        terrain_mult: Terrain cost multiplier (1, 2, or 4)

    Returns:
        (cost_ft, new_diagonal_count)
    """
    dx = abs(pos.x - prev.x)
    dy = abs(pos.y - prev.y)
    is_diagonal = dx == 1 and dy == 1

    if is_diagonal:
        diagonal_count += 1
        base_cost = 10 if diagonal_count % 2 == 0 else 5
    else:
        base_cost = 5

    return base_cost * terrain_mult, diagonal_count


def find_path_bfs(
    from_pos: Position,
    to_pos: Position,
    enemy_squares: set,
    speed_ft: int,
    world_state: Optional[WorldState] = None,
) -> Optional[List[Position]]:
    """Dijkstra pathfinding on flat grid with speed and occupied-square constraints.

    Finds lowest-cost path from from_pos to to_pos, avoiding enemy-occupied
    squares. Uses 5/10/5 diagonal cost rule. Prioritizes orthogonal moves
    over diagonals when cost is equal for deterministic behavior.

    The search is bounded by speed_ft to avoid exploring the entire grid.

    Args:
        from_pos: Starting position
        to_pos: Destination position
        enemy_squares: Set of (x, y) tuples that cannot be entered
        speed_ft: Maximum movement budget in feet
        world_state: Optional world state for terrain cost queries

    Returns:
        List of positions (excluding from_pos, including to_pos) or None if unreachable
    """
    if from_pos == to_pos:
        return []

    # Import terrain resolver only if world_state provided
    get_terrain_cost = None
    if world_state is not None:
        from aidm.core.terrain_resolver import get_movement_cost
        get_terrain_cost = lambda fp, tp: get_movement_cost(
            world_state, {"x": fp.x, "y": fp.y}, {"x": tp.x, "y": tp.y}
        )

    # Dijkstra with priority queue
    # Priority: (cost_ft, tie_break_counter, position, diagonal_count, path)
    counter = 0
    start_state = (0, counter, from_pos, 0, [])
    heap = [start_state]

    # best_cost[pos] = lowest cost to reach pos
    best_cost = {(from_pos.x, from_pos.y): 0}

    # 8-directional neighbors: orthogonal first, then diagonal (deterministic)
    DIRECTIONS = [
        (0, 1), (1, 0), (0, -1), (-1, 0),   # N, E, S, W (orthogonal)
        (1, 1), (1, -1), (-1, -1), (-1, 1),  # NE, SE, SW, NW (diagonal)
    ]

    while heap:
        current_cost, _, current_pos, diag_count, path = heapq.heappop(heap)

        # Skip if we've found a better path to this position
        pos_key = (current_pos.x, current_pos.y)
        if pos_key in best_cost and best_cost[pos_key] < current_cost:
            continue

        # Try each neighbor
        for dx, dy in DIRECTIONS:
            nx, ny = current_pos.x + dx, current_pos.y + dy
            next_pos = Position(x=nx, y=ny)
            next_sq = (nx, ny)

            # Cannot enter enemy-occupied squares
            if next_sq in enemy_squares:
                continue

            # Calculate step cost
            terrain_mult = 1
            if get_terrain_cost is not None:
                terrain_mult = get_terrain_cost(current_pos, next_pos)

            step_ft, new_diag = _step_cost(current_pos, next_pos, diag_count, terrain_mult)
            new_cost = current_cost + step_ft

            # Speed limit
            if new_cost > speed_ft:
                continue

            # Only visit if we found a cheaper path
            if next_sq in best_cost and best_cost[next_sq] <= new_cost:
                continue
            best_cost[next_sq] = new_cost

            new_path = path + [next_pos]

            # Found destination
            if next_pos == to_pos:
                return new_path

            counter += 1
            heapq.heappush(heap, (new_cost, counter, next_pos, new_diag, new_path))

    return None  # Unreachable


def build_full_move_intent(
    actor_id: str,
    destination: Position,
    world_state: WorldState,
) -> Tuple[Optional[FullMoveIntent], Optional[str]]:
    """Build a FullMoveIntent from actor + destination, handling all validation.

    This is the main entry point for the CLI and AI to request movement.
    It reads the actor's position and speed from world state, finds a valid
    path via BFS, and constructs the intent.

    Args:
        actor_id: Entity requesting movement
        destination: Target position
        world_state: Current world state

    Returns:
        (FullMoveIntent, None) on success, or (None, error_message) on failure
    """
    entity = world_state.entities.get(actor_id)
    if entity is None:
        return None, f"Entity {actor_id} not found."

    pos_dict = entity.get(EF.POSITION)
    if pos_dict is None:
        return None, f"{actor_id} has no position."

    from_pos = Position(x=pos_dict["x"], y=pos_dict["y"])

    if from_pos == destination:
        return None, "You're already there."

    speed_ft = entity.get(EF.BASE_SPEED, 30)

    # WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001: Fast Movement (PHB p.26)
    # +10 ft for barbarians; blocked by heavy armor only (light/medium OK per PHB p.26)
    _fast_movement = entity.get(EF.FAST_MOVEMENT_BONUS, 0)
    if _fast_movement > 0:
        _armor_type = entity.get(EF.ARMOR_TYPE, "none")
        # WO-ENGINE-ENCUMBRANCE-WIRE-001: Fast Movement also suppressed by medium/heavy load (PHB p.26)
        _enc_load = entity.get(EF.ENCUMBRANCE_LOAD, "light")
        if _armor_type != "heavy" and _enc_load not in ("medium", "heavy", "overloaded"):
            speed_ft += _fast_movement

    enemy_squares, _ = _get_occupied_squares(world_state, actor_id)

    # Check if destination is enemy-occupied
    dest_sq = (destination.x, destination.y)
    if dest_sq in enemy_squares:
        return None, "Cannot move into a square occupied by an enemy."

    # Find path via BFS
    path = find_path_bfs(from_pos, destination, enemy_squares, speed_ft, world_state)

    if path is None:
        # Distinguish between "too far" and "blocked"
        # Try without speed limit to see if it's reachable at all
        unlimited_path = find_path_bfs(from_pos, destination, enemy_squares, 1000)
        if unlimited_path is None:
            return None, "No clear path to that square (blocked by enemies)."
        else:
            squares = speed_ft // 5
            return None, f"Too far! You can move {squares} squares ({speed_ft} ft) per move action."

    # Build terrain costs for the path
    terrain_costs = []
    from aidm.core.terrain_resolver import get_movement_cost
    prev = from_pos
    for pos in path:
        cost = get_movement_cost(
            world_state,
            {"x": prev.x, "y": prev.y},
            {"x": pos.x, "y": pos.y},
        )
        terrain_costs.append(cost)
        prev = pos

    intent = FullMoveIntent(
        actor_id=actor_id,
        from_pos=from_pos,
        path=path,
        speed_ft=speed_ft,
    )

    # Validate total cost against speed
    total_cost = intent.path_cost_ft(terrain_costs)
    if total_cost > speed_ft:
        squares = speed_ft // 5
        return None, f"Too far with terrain! Path costs {total_cost} ft but you can only move {speed_ft} ft."

    return intent, None
