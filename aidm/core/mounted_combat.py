"""Mounted combat core logic for CP-18A — Rider–Mount Coupling.

Provides movement, dismount, and condition handling for mounted combat.

CP-18A SCOPE:
- Rider-mount position derivation (rider at mount position)
- Mounted movement resolution (mount moves, AoOs against mount)
- Voluntary dismount (normal + fast)
- Forced dismount (mount fall, defeat)
- Unconscious rider saddle check
- Condition-triggered dismount logic

OUT OF SCOPE:
- Independent mounts (SKR-003)
- Mounted spellcasting (blocked)
- Mounted grapple (SKR-005)
- Feat logic (Mounted Combat, etc.)

All state changes are event-sourced. RNG uses "combat" stream only.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict, Any
from aidm.core.state import WorldState
from aidm.core.event_log import Event
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.position import Position  # CP-001: Canonical position type
from aidm.schemas.mounted_combat import (
    MountedState, MountedMoveIntent, DismountIntent, MountIntent, SaddleType
)
from aidm.schemas.entity_fields import EF


# ============================================================================
# POSITION DERIVATION
# ============================================================================

def get_entity_position(entity_id: str, world_state: WorldState) -> Optional[Position]:
    """Get entity position, accounting for mounted state.

    If entity is a mounted rider, returns MOUNT's position.
    This ensures rider and mount always share the same grid square.

    PHB p.157: "For simplicity, assume that you share your mount's
    space during combat."

    Args:
        entity_id: Entity ID to get position for
        world_state: Current world state

    Returns:
        Position or None if position unavailable
    """
    entity = world_state.entities.get(entity_id)
    if entity is None:
        return None

    mounted_state_data = entity.get(EF.MOUNTED_STATE)
    if mounted_state_data is not None:
        # Rider is mounted - return mount's position
        mount = world_state.entities.get(mounted_state_data["mount_id"])
        if mount is not None:
            pos_dict = mount.get(EF.POSITION)
            if pos_dict is not None:
                return Position.from_dict(pos_dict)
        # Mount missing - fall through to rider's own position (dismounted)

    # Not mounted or mount missing - return entity's own position
    pos_dict = entity.get(EF.POSITION)
    if pos_dict is not None:
        return Position.from_dict(pos_dict)

    return None


def is_mounted(entity_id: str, world_state: WorldState) -> bool:
    """Check if an entity is currently mounted.

    Args:
        entity_id: Entity ID to check
        world_state: Current world state

    Returns:
        True if entity has a mounted_state, False otherwise
    """
    entity = world_state.entities.get(entity_id)
    if entity is None:
        return False
    return entity.get(EF.MOUNTED_STATE) is not None


def get_rider_for_mount(mount_id: str, world_state: WorldState) -> Optional[str]:
    """Get the rider ID for a mount, if any.

    Args:
        mount_id: Mount entity ID
        world_state: Current world state

    Returns:
        Rider entity ID or None if no rider
    """
    mount = world_state.entities.get(mount_id)
    if mount is None:
        return None
    return mount.get(EF.RIDER_ID)


# ============================================================================
# COUPLING VALIDATION
# ============================================================================

def validate_mounted_coupling(world_state: WorldState) -> bool:
    """Validate rider-mount coupling is bidirectionally consistent.

    INVARIANT: If rider has mounted_state, mount has rider_id pointing back.

    Args:
        world_state: Current world state

    Returns:
        True if all coupling is consistent, False otherwise
    """
    for entity_id, entity in world_state.entities.items():
        mounted_state_data = entity.get(EF.MOUNTED_STATE)
        if mounted_state_data is not None:
            # Rider claims to be on mount
            mount = world_state.entities.get(mounted_state_data["mount_id"])
            if mount is None:
                return False  # Mount doesn't exist
            if mount.get(EF.RIDER_ID) != entity_id:
                return False  # Mount doesn't know about rider

        rider_id = entity.get(EF.RIDER_ID)
        if rider_id is not None:
            # Mount claims to have rider
            rider = world_state.entities.get(rider_id)
            if rider is None:
                return False  # Rider doesn't exist
            mounted_state_data = rider.get(EF.MOUNTED_STATE)
            if mounted_state_data is None:
                return False  # Rider doesn't know about mount
            if mounted_state_data["mount_id"] != entity_id:
                return False  # Rider on different mount

    return True


# ============================================================================
# MOUNTING
# ============================================================================

def resolve_mount(
    intent: MountIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Resolve mounting a creature.

    PHB p.80: Mounting is a move action, or free action with DC 20 Ride.

    Args:
        intent: MountIntent specifying rider and mount
        world_state: Current world state
        next_event_id: Starting event ID
        timestamp: Starting timestamp

    Returns:
        Updated world state and events
    """
    events = []

    rider = world_state.entities.get(intent.rider_id)
    mount = world_state.entities.get(intent.mount_id)

    if rider is None or mount is None:
        return world_state, events

    # Check if already mounted
    if rider.get(EF.MOUNTED_STATE) is not None:
        return world_state, events  # Already mounted

    # Check if mount already has a rider
    if mount.get(EF.RIDER_ID) is not None:
        return world_state, events  # Mount occupied

    # Determine if mount is war-trained
    is_trained = mount.get(EF.IS_MOUNT_TRAINED, False)

    # Create mounted state
    mounted_state = MountedState(
        mount_id=intent.mount_id,
        is_controlled=is_trained,
        saddle_type=intent.saddle_type,
        mounted_at_event_id=next_event_id
    )

    # Get mount position for rider positioning
    mount_pos = mount.get(EF.POSITION)

    # Emit mount event
    events.append(Event(
        event_id=next_event_id,
        event_type="rider_mounted",
        timestamp=timestamp,
        payload={
            "rider_id": intent.rider_id,
            "mount_id": intent.mount_id,
            "saddle_type": intent.saddle_type,
            "is_controlled": is_trained,
            "position": mount_pos,
            "fast_mount": intent.fast_mount
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    ))

    # Update world state
    entities = deepcopy(world_state.entities)

    # Update rider
    entities[intent.rider_id][EF.MOUNTED_STATE] = mounted_state.to_dict()
    # Position is derived from mount, so we don't store it on rider

    # Update mount
    entities[intent.mount_id][EF.RIDER_ID] = intent.rider_id

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat
    )

    return world_state, events


# ============================================================================
# DISMOUNTING
# ============================================================================

def _find_adjacent_empty(
    center_pos: Position,
    world_state: WorldState
) -> Optional[Position]:
    """Find an empty adjacent square for dismounting.

    Args:
        center_pos: Center position (mount's position)
        world_state: Current world state

    Returns:
        First available adjacent Position, or None if all occupied
    """
    # Check all 8 adjacent squares
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue

            candidate = Position(x=center_pos.x + dx, y=center_pos.y + dy)

            # Check if any entity occupies this square
            occupied = False
            for entity_id, entity in world_state.entities.items():
                pos_dict = entity.get(EF.POSITION)
                if pos_dict is not None:
                    entity_pos = Position.from_dict(pos_dict)
                    if entity_pos == candidate:
                        occupied = True
                        break

            if not occupied:
                return candidate

    # All squares occupied - return first adjacent as fallback
    return Position(x=center_pos.x + 1, y=center_pos.y)


def resolve_dismount(
    intent: DismountIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Resolve voluntary dismount.

    PHB p.80: Normal dismount is move action, fast dismount (DC 20) is free action.

    Args:
        intent: DismountIntent specifying rider
        world_state: Current world state
        next_event_id: Starting event ID
        timestamp: Starting timestamp

    Returns:
        Updated world state and events
    """
    events = []

    rider = world_state.entities.get(intent.rider_id)
    if rider is None:
        return world_state, events

    mounted_state_data = rider.get(EF.MOUNTED_STATE)
    if mounted_state_data is None:
        return world_state, events  # Not mounted

    mount_id = mounted_state_data["mount_id"]
    mount = world_state.entities.get(mount_id)
    if mount is None:
        return world_state, events

    # Get mount position for dismount positioning
    mount_pos_dict = mount.get(EF.POSITION)
    if mount_pos_dict is None:
        return world_state, events

    mount_pos = Position.from_dict(mount_pos_dict)

    # Determine landing position
    dismount_pos = intent.dismount_to
    if dismount_pos is None:
        dismount_pos = _find_adjacent_empty(mount_pos, world_state)
    if dismount_pos is None:
        dismount_pos = Position(x=mount_pos.x + 1, y=mount_pos.y)

    # Fast dismount requires Ride check (deferred - skill system)
    action_type = "free_action" if intent.fast_dismount else "move_action"

    # Emit dismount event
    events.append(Event(
        event_id=next_event_id,
        event_type="rider_dismounted",
        timestamp=timestamp,
        payload={
            "rider_id": intent.rider_id,
            "mount_id": mount_id,
            "action_type": action_type,
            "from_pos": mount_pos.to_dict(),
            "to_pos": dismount_pos.to_dict(),
            "voluntary": True
        },
        citations=[{"source_id": "681f92bc94ff", "page": 80}]
    ))

    # Update world state
    entities = deepcopy(world_state.entities)

    # Update rider - remove mounted state, set position
    if EF.MOUNTED_STATE in entities[intent.rider_id]:
        del entities[intent.rider_id][EF.MOUNTED_STATE]
    entities[intent.rider_id][EF.POSITION] = dismount_pos.to_dict()

    # Update mount - remove rider reference
    if EF.RIDER_ID in entities[mount_id]:
        del entities[mount_id][EF.RIDER_ID]

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat
    )

    return world_state, events


def trigger_forced_dismount(
    rider_id: str,
    mount_id: str,
    reason: str,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Handle forced dismount when mount falls, is defeated, etc.

    PHB p.157: "If your mount falls, you have to succeed on a DC 15 Ride
    check to make a soft fall and take no damage. If the check fails,
    you take 1d6 points of damage."

    Uses "combat" RNG stream for Ride check and damage roll.

    Args:
        rider_id: Rider entity ID
        mount_id: Mount entity ID
        reason: Reason for forced dismount (e.g., "mount_defeated")
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Starting timestamp

    Returns:
        Updated world state and events
    """
    events = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    rider = world_state.entities.get(rider_id)
    if rider is None:
        return world_state, events

    mounted_state_data = rider.get(EF.MOUNTED_STATE)
    if mounted_state_data is None:
        return world_state, events  # Not mounted

    mount = world_state.entities.get(mount_id)
    mount_pos = None
    if mount is not None:
        pos_dict = mount.get(EF.POSITION)
        if pos_dict is not None:
            mount_pos = Position.from_dict(pos_dict)

    # Roll Ride check (DC 15 for soft fall)
    # Placeholder: Assume +5 Ride modifier (skill system not implemented)
    ride_roll = rng.stream("combat").randint(1, 20)
    ride_modifier = 5  # Placeholder
    ride_dc = 15
    ride_total = ride_roll + ride_modifier
    soft_fall = ride_total >= ride_dc

    # Emit ride check event
    events.append(Event(
        event_id=current_event_id,
        event_type="ride_check",
        timestamp=current_timestamp,
        payload={
            "rider_id": rider_id,
            "check_type": "soft_fall",
            "d20_result": ride_roll,
            "modifier": ride_modifier,
            "total": ride_total,
            "dc": ride_dc,
            "success": soft_fall
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Calculate falling damage if failed
    fall_damage = 0
    if not soft_fall:
        fall_damage = rng.stream("combat").randint(1, 6)
        events.append(Event(
            event_id=current_event_id,
            event_type="damage_applied",
            timestamp=current_timestamp,
            payload={
                "entity_id": rider_id,
                "damage": fall_damage,
                "damage_type": "bludgeoning",
                "source": "dismount_fall"
            },
            citations=[{"source_id": "681f92bc94ff", "page": 157}]
        ))
        current_event_id += 1
        current_timestamp += 0.01

    # Determine dismount position
    dismount_pos = None
    if mount_pos is not None:
        dismount_pos = _find_adjacent_empty(mount_pos, world_state)
        if dismount_pos is None:
            dismount_pos = Position(x=mount_pos.x + 1, y=mount_pos.y)

    # Emit dismount event
    events.append(Event(
        event_id=current_event_id,
        event_type="rider_dismounted",
        timestamp=current_timestamp,
        payload={
            "rider_id": rider_id,
            "mount_id": mount_id,
            "action_type": "forced",
            "reason": reason,
            "from_pos": mount_pos.to_dict() if mount_pos else None,
            "to_pos": dismount_pos.to_dict() if dismount_pos else None,
            "voluntary": False,
            "soft_fall": soft_fall,
            "fall_damage": fall_damage
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    ))

    # Update world state
    entities = deepcopy(world_state.entities)

    # Update rider
    updated_rider = entities[rider_id]
    if EF.MOUNTED_STATE in updated_rider:
        del updated_rider[EF.MOUNTED_STATE]
    if dismount_pos:
        updated_rider[EF.POSITION] = dismount_pos.to_dict()

    # Apply fall damage to HP
    current_hp = updated_rider.get(EF.HP_CURRENT, 0)
    updated_rider[EF.HP_CURRENT] = max(0, current_hp - fall_damage)
    if updated_rider[EF.HP_CURRENT] <= 0:
        updated_rider[EF.DEFEATED] = True

    # Clear rider_id from mount if mount exists
    if mount is not None and mount_id in entities:
        if EF.RIDER_ID in entities[mount_id]:
            del entities[mount_id][EF.RIDER_ID]

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat
    )

    return world_state, events


def check_unconscious_fall(
    rider_id: str,
    mounted_state_data: Dict[str, Any],
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Check if unconscious rider falls from saddle.

    PHB p.157: "If you are knocked unconscious, you have a 50% chance
    to stay in the saddle (or 75% if you're in a military saddle)."

    Uses "combat" RNG stream for d100 roll.

    Args:
        rider_id: Rider entity ID
        mounted_state_data: Rider's mounted_state dict
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Starting timestamp

    Returns:
        Updated world state and events
    """
    events = []

    saddle_type = mounted_state_data.get("saddle_type", SaddleType.RIDING)
    stay_chance = 75 if saddle_type == SaddleType.MILITARY else 50

    # Roll d100
    roll = rng.stream("combat").randint(1, 100)
    stays_mounted = roll <= stay_chance

    events.append(Event(
        event_id=next_event_id,
        event_type="unconscious_saddle_check",
        timestamp=timestamp,
        payload={
            "rider_id": rider_id,
            "mount_id": mounted_state_data["mount_id"],
            "saddle_type": saddle_type,
            "stay_chance_percent": stay_chance,
            "roll": roll,
            "stays_mounted": stays_mounted
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    ))

    if not stays_mounted:
        # Rider falls - trigger forced dismount
        world_state, fall_events = trigger_forced_dismount(
            rider_id=rider_id,
            mount_id=mounted_state_data["mount_id"],
            reason="rider_unconscious",
            world_state=world_state,
            rng=rng,
            next_event_id=next_event_id + 1,
            timestamp=timestamp + 0.01
        )
        events.extend(fall_events)

    return world_state, events


# ============================================================================
# CONDITION COUPLING
# ============================================================================

# Conditions that trigger rider dismount when applied to mount
MOUNT_DISMOUNT_CONDITIONS = {"prone", "stunned", "paralyzed", "helpless", "unconscious"}


def handle_mounted_condition_change(
    entity_id: str,
    condition_type: str,
    condition_applied: bool,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Handle condition changes with mounted combat coupling.

    Called when a condition is applied or removed. Triggers appropriate
    dismount logic for mounted entities.

    Condition propagation rules:
    - Mount conditions (prone, defeated, stunned, etc.) → Rider dismounts
    - Rider unconscious → Check saddle stay chance

    Args:
        entity_id: Entity that gained/lost condition
        condition_type: Type of condition
        condition_applied: True if applied, False if removed
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Starting timestamp

    Returns:
        Updated world state and events
    """
    events = []

    entity = world_state.entities.get(entity_id)
    if entity is None:
        return world_state, events

    # Check if this entity is a mount with a rider
    rider_id = entity.get(EF.RIDER_ID)
    if rider_id is not None and condition_applied:
        # Mount gained a condition - check rider effects
        if condition_type in MOUNT_DISMOUNT_CONDITIONS:
            # Mount falls - rider must dismount
            world_state, dismount_events = trigger_forced_dismount(
                rider_id=rider_id,
                mount_id=entity_id,
                reason=f"mount_{condition_type}",
                world_state=world_state,
                rng=rng,
                next_event_id=next_event_id,
                timestamp=timestamp
            )
            events.extend(dismount_events)

    # Check if this entity is a mounted rider
    mounted_state_data = entity.get(EF.MOUNTED_STATE)
    if mounted_state_data is not None and condition_applied:
        if condition_type == "unconscious":
            # Rider KO'd - check if stays in saddle
            world_state, fall_events = check_unconscious_fall(
                rider_id=entity_id,
                mounted_state_data=mounted_state_data,
                world_state=world_state,
                rng=rng,
                next_event_id=next_event_id + len(events),
                timestamp=timestamp
            )
            events.extend(fall_events)

    return world_state, events


# ============================================================================
# ATTACK BONUSES
# ============================================================================

# Size ordering for higher ground comparison
SIZE_ORDER = {
    "fine": 0, "diminutive": 1, "tiny": 2, "small": 3,
    "medium": 4, "large": 5, "huge": 6, "gargantuan": 7, "colossal": 8
}


def get_mounted_attack_bonus(
    attacker_id: str,
    target_id: str,
    world_state: WorldState
) -> int:
    """Calculate mounted attack bonus (higher ground).

    PHB p.157: "+1 bonus on melee attacks for being on higher ground"
    when attacking creatures smaller than mount that are on foot.

    Args:
        attacker_id: Attacking entity ID
        target_id: Target entity ID
        world_state: Current world state

    Returns:
        Additional attack bonus (0 or +1)
    """
    attacker = world_state.entities.get(attacker_id)
    if attacker is None:
        return 0

    mounted_state_data = attacker.get(EF.MOUNTED_STATE)
    if mounted_state_data is None:
        return 0  # Not mounted

    mount = world_state.entities.get(mounted_state_data["mount_id"])
    if mount is None:
        return 0

    target = world_state.entities.get(target_id)
    if target is None:
        return 0

    # Check if target is mounted (mounted targets don't give higher ground)
    target_mounted = target.get(EF.MOUNTED_STATE) is not None
    if target_mounted:
        return 0

    # Compare sizes (mount must be larger than target)
    mount_size = mount.get(EF.MOUNT_SIZE, "large")  # Default horse is Large
    target_size = target.get("size", "medium")      # Default humanoid is Medium

    mount_size_val = SIZE_ORDER.get(mount_size.lower(), 4)
    target_size_val = SIZE_ORDER.get(target_size.lower(), 4)

    if mount_size_val > target_size_val:
        return 1  # +1 higher ground bonus

    return 0


def can_rider_full_attack(mount_moved_distance: int) -> bool:
    """Check if rider can make a full attack.

    PHB p.157: "If your mount moves more than 5 feet, you can only make
    a single melee attack."

    Args:
        mount_moved_distance: Total distance mount moved this turn (in feet)

    Returns:
        True if full attack allowed, False if only single attack
    """
    return mount_moved_distance <= 5
