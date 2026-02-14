"""Terrain resolution for CP-19 — Environment & Terrain.

Implements deterministic terrain queries and effect resolution:
- Difficult terrain movement cost calculation
- Cover determination (standard, improved, total, soft)
- Higher ground bonus (+1 melee)
- Falling damage calculation (1d6/10ft, max 20d6)
- Hazard detection (pits, ledges)

CP-20 EXTENSION:
- Environmental damage hazards (fire, acid, lava, spiked pits)
- Contact hazard resolution on entry/forced movement

DESIGN PRINCIPLES (per CP19_ENVIRONMENT_TERRAIN_DECISIONS.md):
- Read-only terrain (no terrain mutations during play)
- Deterministic queries (all terrain effects are pure lookups)
- RNG isolation (only falling/environmental damage uses RNG, "combat" stream)
- Composable modifiers (cover, elevation, conditions stack cleanly)

RNG STREAM: "combat" (falling damage and environmental damage only)

ORDERING CONTRACT (T-19-03, extended by CP-20):
1. AoOs resolved first (per CP-15)
2. Movement executed
3. Hazard detection (pits, ledges)
4. Environmental damage resolved (fire, acid, lava, spiked pits)
"""

from copy import deepcopy
from typing import List, Dict, Any, Optional, Tuple
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position  # CP-001: Canonical position type
from aidm.schemas.terrain import (
    TerrainCell, TerrainTag, CoverType,
    ElevationDifference, FallingResult, CoverCheckResult,
)


# ==============================================================================
# TERRAIN MAP ACCESS
# ==============================================================================

def get_terrain_cell(
    world_state: WorldState,
    position: Dict[str, int]
) -> Optional[TerrainCell]:
    """Get terrain cell at a position.

    Args:
        world_state: Current world state
        position: Position dict with "x" and "y" keys

    Returns:
        TerrainCell if terrain data exists at position, else None
    """
    terrain_map = world_state.active_combat.get("terrain_map") if world_state.active_combat else None
    if terrain_map is None:
        return None

    # Terrain map keyed by "x,y" string
    key = f"{position['x']},{position['y']}"
    cell_data = terrain_map.get(key)
    if cell_data is None:
        return None

    return TerrainCell.from_dict(cell_data)


def get_terrain_cell_by_coords(
    world_state: WorldState,
    x: int,
    y: int
) -> Optional[TerrainCell]:
    """Get terrain cell at specific coordinates.

    Args:
        world_state: Current world state
        x: X coordinate
        y: Y coordinate

    Returns:
        TerrainCell if terrain data exists, else None
    """
    return get_terrain_cell(world_state, {"x": x, "y": y})


# ==============================================================================
# MOVEMENT COST CALCULATION
# ==============================================================================

def get_movement_cost(
    world_state: WorldState,
    from_pos: Dict[str, int],
    to_pos: Dict[str, int]
) -> int:
    """Calculate movement cost to enter a cell.

    Per PHB p.148-150:
    - Normal terrain: 1 square
    - Difficult terrain: 2 squares
    - Stacked difficult: 4 squares (highest wins, per design doc)

    Args:
        world_state: Current world state
        from_pos: Starting position
        to_pos: Destination position

    Returns:
        Movement cost multiplier (1, 2, or 4)
    """
    cell = get_terrain_cell(world_state, to_pos)
    if cell is None:
        return 1  # Default to normal terrain

    return cell.movement_cost


def is_difficult_terrain(world_state: WorldState, position: Dict[str, int]) -> bool:
    """Check if position is difficult terrain.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        True if movement_cost > 1
    """
    cell = get_terrain_cell(world_state, position)
    if cell is None:
        return False
    return cell.movement_cost >= 2


def can_run_through(world_state: WorldState, position: Dict[str, int]) -> bool:
    """Check if running/charging through position is allowed.

    Per PHB p.148: Cannot run/charge through difficult terrain.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        True if running/charging is allowed
    """
    cell = get_terrain_cell(world_state, position)
    if cell is None:
        return True
    return cell.movement_cost < 2


def can_5_foot_step(world_state: WorldState, position: Dict[str, int]) -> bool:
    """Check if 5-foot step is allowed into position.

    Per SRD PHB p.144: Cannot 5-foot step in difficult terrain
    (movement_cost >= 2). E-AMB-03 decision: FIX-SRD.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        True if 5-foot step is allowed
    """
    cell = get_terrain_cell(world_state, position)
    if cell is None:
        return True
    return cell.movement_cost < 2


# ==============================================================================
# COVER DETERMINATION
# ==============================================================================

def check_cover(
    world_state: WorldState,
    attacker_id: str,
    defender_id: str,
    is_melee: bool = True
) -> CoverCheckResult:
    """Determine cover between attacker and defender.

    Cover bonuses (PHB p.150-152):
    - Standard: +4 AC, +2 Reflex, blocks AoO
    - Improved: +8 AC, +4 Reflex, blocks AoO
    - Total: Cannot be targeted, blocks AoO
    - Soft: +4 AC melee only, does NOT block AoO

    Args:
        world_state: Current world state
        attacker_id: Attacking entity ID
        defender_id: Defending entity ID
        is_melee: True if melee attack (affects soft cover)

    Returns:
        CoverCheckResult with cover type and modifiers
    """
    # Get positions
    attacker = world_state.entities.get(attacker_id)
    defender = world_state.entities.get(defender_id)

    if attacker is None or defender is None:
        return CoverCheckResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            cover_type=None,
            ac_bonus=0,
            reflex_bonus=0,
            blocks_aoo=False,
            blocks_targeting=False,
        )

    attacker_pos = attacker.get(EF.POSITION, {"x": 0, "y": 0})
    defender_pos = defender.get(EF.POSITION, {"x": 0, "y": 0})

    # Check terrain-based cover at defender position
    defender_cell = get_terrain_cell(world_state, defender_pos)
    terrain_cover = defender_cell.cover_type if defender_cell else None

    # Check for soft cover (intervening creatures)
    soft_cover = _check_soft_cover(world_state, attacker_pos, defender_pos, attacker_id, defender_id)

    # Determine highest cover (terrain takes precedence over soft cover)
    if terrain_cover == CoverType.TOTAL:
        return CoverCheckResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            cover_type=CoverType.TOTAL,
            ac_bonus=0,  # Cannot be targeted
            reflex_bonus=0,
            blocks_aoo=True,
            blocks_targeting=True,
        )
    elif terrain_cover == CoverType.IMPROVED:
        return CoverCheckResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            cover_type=CoverType.IMPROVED,
            ac_bonus=8,
            reflex_bonus=4,
            blocks_aoo=True,
            blocks_targeting=False,
        )
    elif terrain_cover == CoverType.STANDARD:
        return CoverCheckResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            cover_type=CoverType.STANDARD,
            ac_bonus=4,
            reflex_bonus=2,
            blocks_aoo=True,
            blocks_targeting=False,
        )
    elif soft_cover and not is_melee:
        # Soft cover from creatures applies to ranged attacks only (PHB p.152)
        return CoverCheckResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            cover_type=CoverType.SOFT,
            ac_bonus=4,
            reflex_bonus=0,
            blocks_aoo=False,  # Soft cover does NOT block AoO
            blocks_targeting=False,
        )
    else:
        return CoverCheckResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            cover_type=None,
            ac_bonus=0,
            reflex_bonus=0,
            blocks_aoo=False,
            blocks_targeting=False,
        )


def _check_soft_cover(
    world_state: WorldState,
    attacker_pos: Dict[str, int],
    defender_pos: Dict[str, int],
    attacker_id: str,
    defender_id: str
) -> bool:
    """Check if there's a creature providing soft cover.

    Soft cover exists if another creature is in the line between
    attacker and defender (PHB p.152).

    Args:
        world_state: Current world state
        attacker_pos: Attacker position
        defender_pos: Defender position
        attacker_id: Attacker entity ID (excluded from check)
        defender_id: Defender entity ID (excluded from check)

    Returns:
        True if soft cover exists
    """
    # Simplified: Check if any creature (not attacker/defender) is on the
    # line between attacker and defender positions
    ax, ay = attacker_pos["x"], attacker_pos["y"]
    dx, dy = defender_pos["x"], defender_pos["y"]

    # If adjacent, no soft cover possible
    if abs(ax - dx) <= 1 and abs(ay - dy) <= 1:
        return False

    # Get cells on the line (simplified: just check direct path)
    for entity_id, entity in world_state.entities.items():
        if entity_id in (attacker_id, defender_id):
            continue
        if entity.get(EF.DEFEATED, False):
            continue

        entity_pos = entity.get(EF.POSITION)
        if entity_pos is None:
            continue

        ex, ey = entity_pos["x"], entity_pos["y"]

        # Check if entity is between attacker and defender
        # Simplified: on the line segment
        if _is_between(ax, ay, dx, dy, ex, ey):
            return True

    return False


def _is_between(ax: int, ay: int, dx: int, dy: int, ex: int, ey: int) -> bool:
    """Check if point (ex, ey) is between (ax, ay) and (dx, dy) on the grid line.

    Uses cross-product proximity test: the point must be close to the line
    segment AND within the segment's extent (exclusive of endpoints).

    For grid-based combat, a creature provides soft cover if it lies on or
    adjacent to the line segment between attacker and defender.
    """
    # Handle collinear cases (horizontal/vertical lines) first
    if ax == dx:
        # Vertical line: x must match, y must be strictly between
        if ex != ax:
            return False
        return min(ay, dy) < ey < max(ay, dy)
    if ay == dy:
        # Horizontal line: y must match, x must be strictly between
        if ey != ay:
            return False
        return min(ax, dx) < ex < max(ax, dx)

    # General case: point must be inside bounding box (exclusive of endpoints)
    if ex <= min(ax, dx) or ex >= max(ax, dx):
        return False
    if ey <= min(ay, dy) or ey >= max(ay, dy):
        return False

    # Cross product to check proximity to line segment
    # If |cross| <= half the segment length, the point is close enough
    # to the line for grid-based soft cover (within ~1 square)
    cross = abs((dx - ax) * (ey - ay) - (dy - ay) * (ex - ax))
    seg_len = max(abs(dx - ax), abs(dy - ay))

    return cross <= seg_len


# ==============================================================================
# ELEVATION AND HIGHER GROUND
# ==============================================================================

def get_elevation(world_state: WorldState, entity_id: str) -> int:
    """Get entity's current elevation.

    Elevation sources (stacked):
    - Entity's ELEVATION field
    - Terrain cell elevation at entity's position

    Args:
        world_state: Current world state
        entity_id: Entity to check

    Returns:
        Total elevation in feet
    """
    entity = world_state.entities.get(entity_id)
    if entity is None:
        return 0

    # Entity's personal elevation (e.g., flying)
    entity_elevation = entity.get(EF.ELEVATION, 0)

    # Terrain elevation at position
    position = entity.get(EF.POSITION)
    if position:
        cell = get_terrain_cell(world_state, position)
        terrain_elevation = cell.elevation if cell else 0
    else:
        terrain_elevation = 0

    return entity_elevation + terrain_elevation


def get_elevation_difference(
    world_state: WorldState,
    attacker_id: str,
    defender_id: str
) -> ElevationDifference:
    """Compare elevation between attacker and defender.

    Args:
        world_state: Current world state
        attacker_id: Attacking entity ID
        defender_id: Defending entity ID

    Returns:
        ElevationDifference with comparison result
    """
    attacker_elev = get_elevation(world_state, attacker_id)
    defender_elev = get_elevation(world_state, defender_id)

    return ElevationDifference(
        attacker_elevation=attacker_elev,
        defender_elevation=defender_elev,
        difference=attacker_elev - defender_elev,
    )


def get_higher_ground_bonus(
    world_state: WorldState,
    attacker_id: str,
    defender_id: str
) -> int:
    """Get higher ground attack bonus.

    Per PHB p.151: +1 melee attack when on higher ground.
    This stacks with mounted higher ground bonus from CP-18A.

    Args:
        world_state: Current world state
        attacker_id: Attacking entity ID
        defender_id: Defending entity ID

    Returns:
        Attack bonus (1 if higher ground, 0 otherwise)
    """
    elev_diff = get_elevation_difference(world_state, attacker_id, defender_id)
    return 1 if elev_diff.attacker_has_higher_ground else 0


# ==============================================================================
# HAZARD DETECTION
# ==============================================================================

def is_pit(world_state: WorldState, position: Dict[str, int]) -> bool:
    """Check if position is a pit.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        True if position is a pit
    """
    cell = get_terrain_cell(world_state, position)
    return cell is not None and cell.is_pit


def get_pit_depth(world_state: WorldState, position: Dict[str, int]) -> int:
    """Get pit depth at position.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        Pit depth in feet (0 if not a pit)
    """
    cell = get_terrain_cell(world_state, position)
    if cell is None or not cell.is_pit:
        return 0
    return cell.pit_depth


def is_ledge(world_state: WorldState, position: Dict[str, int]) -> bool:
    """Check if position is a ledge (drop-off).

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        True if position is a ledge
    """
    cell = get_terrain_cell(world_state, position)
    return cell is not None and cell.is_ledge


def get_ledge_drop(world_state: WorldState, position: Dict[str, int]) -> int:
    """Get ledge drop height at position.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        Ledge drop in feet (0 if not a ledge)
    """
    cell = get_terrain_cell(world_state, position)
    if cell is None or not cell.is_ledge:
        return 0
    return cell.ledge_drop


def check_hazard(
    world_state: WorldState,
    position: Dict[str, int]
) -> Tuple[Optional[str], int]:
    """Check for hazards at position.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        Tuple of (hazard_type, fall_distance) or (None, 0) if no hazard
    """
    cell = get_terrain_cell(world_state, position)
    if cell is None:
        return (None, 0)

    if cell.is_pit:
        return ("pit", cell.pit_depth)
    if cell.is_ledge:
        return ("ledge", cell.ledge_drop)

    return (None, 0)


# ==============================================================================
# FALLING DAMAGE RESOLUTION
# ==============================================================================

def calculate_falling_damage(fall_distance: int, is_intentional: bool = False) -> int:
    """Calculate number of damage dice for a fall.

    Per DMG p.304:
    - 1d6 per 10 feet fallen
    - Maximum 20d6 (200 feet)

    Per design doc (degraded):
    - Intentional jump: first 10 feet free

    Args:
        fall_distance: Distance fallen in feet
        is_intentional: True if deliberate jump

    Returns:
        Number of d6 to roll
    """
    effective_distance = fall_distance
    if is_intentional:
        # First 10 feet free on intentional jump
        effective_distance = max(0, fall_distance - 10)

    # 1d6 per 10 feet, max 20d6
    dice = effective_distance // 10
    return min(dice, 20)


def resolve_falling(
    entity_id: str,
    fall_distance: int,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    landing_position: Optional[Dict[str, int]] = None,
    is_intentional: bool = False,
    is_into_water: bool = False,
    water_depth: int = 0,
) -> Tuple[List[Event], WorldState, FallingResult]:
    """Resolve a falling event.

    Per DMG p.304:
    - 1d6 per 10 feet, max 20d6
    - All damage is lethal

    RNG Stream: "combat"

    Args:
        entity_id: Falling entity
        fall_distance: Distance in feet
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Event timestamp
        landing_position: Position where entity lands (optional)
        is_intentional: True if deliberate jump
        is_into_water: True if falling into water
        water_depth: Depth of water in feet

    Returns:
        Tuple of (events, updated_world_state, FallingResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    # Calculate damage dice
    damage_dice = calculate_falling_damage(fall_distance, is_intentional)

    # Into water: reduced damage (DMG p.304)
    # Water fall damage is nonlethal 1d3 per 10ft beyond free zone.
    is_water_fall = False
    if is_into_water and water_depth >= 10:
        is_water_fall = True
        # DC 15 Swim check: if passed, first 20 feet = no damage
        combat_rng_check = rng.stream("combat")
        swim_check = combat_rng_check.randint(1, 20)  # d20 roll for swim check
        free_distance = 20 if swim_check >= 15 else 0  # DC 15 Swim check
        if fall_distance <= free_distance:
            damage_dice = 0
        else:
            # Beyond free zone: 1d3 nonlethal per 10 feet (DMG p.304)
            damage_dice = max(0, (fall_distance - free_distance) // 10)

    # Emit fall_triggered event
    events.append(Event(
        event_id=current_event_id,
        event_type="fall_triggered",
        timestamp=current_timestamp,
        payload={
            "entity_id": entity_id,
            "fall_distance": fall_distance,
            "damage_dice": damage_dice,
            "is_intentional": is_intentional,
            "is_into_water": is_into_water,
        },
        citations=[{"source_id": "dmg_srd", "page": 304}],  # DMG falling damage
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Roll damage if any
    damage_rolls = []
    total_damage = 0

    if damage_dice > 0:
        combat_rng = rng.stream("combat")
        die_size = 3 if is_water_fall else 6  # Water falls: d3 nonlethal (DMG p.304)
        damage_rolls = [combat_rng.randint(1, die_size) for _ in range(damage_dice)]
        total_damage = sum(damage_rolls)

    # Create FallingResult
    result = FallingResult(
        entity_id=entity_id,
        fall_distance=fall_distance,
        damage_dice=damage_dice,
        damage_rolls=damage_rolls,
        total_damage=total_damage,
        landing_position=Position.from_dict(landing_position) if landing_position else None,
        is_into_water=is_into_water,
        water_depth=water_depth,
        is_intentional=is_intentional,
    )

    # Emit falling_damage event
    events.append(Event(
        event_id=current_event_id,
        event_type="falling_damage",
        timestamp=current_timestamp,
        payload={
            "entity_id": entity_id,
            "dice_count": damage_dice,
            "dice_results": damage_rolls,
            "total_damage": total_damage,
            "damage_type": "falling",
        },
        citations=[{"source_id": "dmg_srd", "page": 304}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Apply damage to entity
    entity = world_state.entities.get(entity_id)
    if entity and total_damage > 0:
        hp_before = entity.get(EF.HP_CURRENT, 0)
        hp_after = hp_before - total_damage

        # Emit hp_changed event
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=current_timestamp,
            payload={
                "entity_id": entity_id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "delta": -total_damage,
                "source": "falling_damage",
            },
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # Update entity HP
        entities = deepcopy(world_state.entities)
        updated_entity = entities[entity_id]
        updated_entity[EF.HP_CURRENT] = hp_after
        entities[entity_id] = updated_entity

        # Check for defeat
        if hp_after <= 0:
            updated_entity[EF.DEFEATED] = True
            entities[entity_id] = updated_entity

            events.append(Event(
                event_id=current_event_id,
                event_type="entity_defeated",
                timestamp=current_timestamp,
                payload={
                    "entity_id": entity_id,
                    "hp_final": hp_after,
                    "defeated_by": "falling_damage",
                },
            ))
            current_event_id += 1

        # Update position if landing position provided
        if landing_position:
            updated_entity[EF.POSITION] = landing_position
            entities[entity_id] = updated_entity

        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=world_state.active_combat,
        )

    return events, world_state, result


# ==============================================================================
# FORCED MOVEMENT HAZARD CHECK (CP-18 Integration)
# ==============================================================================

def check_push_path_for_hazards(
    world_state: WorldState,
    start_pos: Dict[str, int],
    push_direction: Tuple[int, int],
    push_distance: int
) -> Tuple[Optional[Dict[str, int]], Optional[str], int]:
    """Check push path for hazards.

    Per design doc: Push path evaluated cell by cell.
    First hazard encountered triggers, remaining push canceled.

    Args:
        world_state: Current world state
        start_pos: Starting position
        push_direction: Direction tuple (dx, dy)
        push_distance: Push distance in feet

    Returns:
        Tuple of (hazard_position, hazard_type, fall_distance)
        Returns (None, None, 0) if no hazard
    """
    dx, dy = push_direction
    push_squares = push_distance // 5  # 5 feet per square

    current_x = start_pos["x"]
    current_y = start_pos["y"]

    for _ in range(push_squares):
        # Move one square
        current_x += dx
        current_y += dy
        current_pos = {"x": current_x, "y": current_y}

        # Check for hazard
        hazard_type, fall_distance = check_hazard(world_state, current_pos)
        if hazard_type is not None:
            return (current_pos, hazard_type, fall_distance)

    return (None, None, 0)


def resolve_forced_movement_with_hazards(
    entity_id: str,
    start_pos: Dict[str, int],
    push_direction: Tuple[int, int],
    push_distance: int,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float
) -> Tuple[List[Event], WorldState, Dict[str, int], Optional[FallingResult]]:
    """Resolve forced movement with hazard checking.

    Per design doc:
    1. Push path calculated
    2. Each cell in push path evaluated in order
    3. First hazard encountered triggers falling, abort push
    4. If no hazard, entity moves to final position

    CP-20 Extension:
    - Also checks for environmental damage hazards (fire, acid, lava)
    - Spiked pits: falling damage + spike damage

    Args:
        entity_id: Entity being pushed
        start_pos: Starting position
        push_direction: Direction tuple (dx, dy)
        push_distance: Push distance in feet
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (events, world_state, final_position, falling_result)
    """
    # Import here to avoid circular dependency
    from aidm.core.environmental_damage_resolver import (
        check_and_resolve_entry_hazard,
        resolve_spiked_pit_damage,
        get_environmental_hazard,
    )

    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    # Check for hazards along push path
    hazard_pos, hazard_type, fall_distance = check_push_path_for_hazards(
        world_state, start_pos, push_direction, push_distance
    )

    if hazard_type is not None:
        # Emit hazard_triggered event
        events.append(Event(
            event_id=current_event_id,
            event_type="hazard_triggered",
            timestamp=current_timestamp,
            payload={
                "entity_id": entity_id,
                "hazard_type": hazard_type,
                "position": hazard_pos,
                "fall_distance": fall_distance,
            },
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # Resolve falling
        falling_events, world_state, falling_result = resolve_falling(
            entity_id=entity_id,
            fall_distance=fall_distance,
            world_state=world_state,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=current_timestamp,
            landing_position=hazard_pos,
        )
        events.extend(falling_events)
        current_event_id += len(falling_events)
        current_timestamp += len(falling_events) * 0.01

        # CP-20: Check for spiked pit (additional piercing damage)
        env_hazard = get_environmental_hazard(world_state, hazard_pos)
        if env_hazard == "spiked_pit":
            spike_events, world_state, spike_result = resolve_spiked_pit_damage(
                entity_id=entity_id,
                position=hazard_pos,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=current_timestamp,
            )
            events.extend(spike_events)

        return events, world_state, hazard_pos, falling_result

    # No pit/ledge hazard - calculate final position
    dx, dy = push_direction
    push_squares = push_distance // 5
    final_pos = {
        "x": start_pos["x"] + dx * push_squares,
        "y": start_pos["y"] + dy * push_squares,
    }

    # CP-20: Check for environmental hazards at final position (fire, acid, lava)
    env_events, world_state, env_result = check_and_resolve_entry_hazard(
        entity_id=entity_id,
        position=final_pos,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=current_timestamp,
    )
    events.extend(env_events)

    return events, world_state, final_pos, None
