"""Combat maneuver resolver for CP-18 — Combat Maneuvers.

Implements deterministic resolution for all combat maneuvers:
- Bull Rush (full)
- Trip (full)
- Overrun (full, with AI-controlled avoidance)
- Sunder (degraded - narrative only)
- Disarm (degraded - no persistence)
- Grapple-lite (degraded - unidirectional condition)

DESIGN PRINCIPLES (per CP18_COMBAT_MANEUVERS_DECISIONS.md):
- All maneuvers resolve within a single action window
- Deterministic RNG consumption order (documented per maneuver)
- Events returned, no direct state mutation
- Gate-safe: G-T1 only (no G-T3C relational conditions)

CP-19 INTEGRATION:
- Forced movement hazard checking (pits, ledges)
- Falling damage resolution when pushed into hazards
- Hazard events emitted before position update

RNG STREAM: "combat" (all maneuvers use this stream only)

RNG CONSUMPTION ORDER (per maneuver):
- Bull Rush: AoO rolls → attacker Str check → defender Str check → [falling damage if hazard]
- Trip: AoO rolls → touch attack → attacker trip check → defender trip check → [counter-trip]
- Overrun: AoO rolls → attacker overrun check → defender overrun check
- Sunder: AoO rolls → attacker attack roll → defender attack roll → [damage roll]
- Disarm: AoO rolls → attacker attack roll → defender attack roll → [counter-disarm]
- Grapple: AoO rolls → touch attack → attacker grapple check → defender grapple check
"""

import logging
from copy import deepcopy
from typing import List, Dict, Any, Optional, Tuple, Union
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent,
    OpposedCheckResult, ManeuverResult, TouchAttackResult,
    get_size_modifier,
)
from aidm.schemas.conditions import (
    create_prone_condition, create_grappled_condition,
)
from aidm.core.conditions import apply_condition

logger = logging.getLogger(__name__)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _get_entity_field(world_state: WorldState, entity_id: str, field: str, default: Any = None) -> Any:
    """Get entity field with default. Fail-closed: returns default if entity missing."""
    entity = world_state.entities.get(entity_id)
    if entity is None:
        logger.warning("Entity '%s' not found; returning default for field '%s'", entity_id, field)
        return default
    return entity.get(field, default)


def _get_str_modifier(world_state: WorldState, entity_id: str) -> int:
    """Get entity's Strength modifier."""
    return _get_entity_field(world_state, entity_id, EF.STR_MOD, 0)


def _get_dex_modifier(world_state: WorldState, entity_id: str) -> int:
    """Get entity's Dexterity modifier."""
    return _get_entity_field(world_state, entity_id, EF.DEX_MOD, 0)


def _get_size_modifier(world_state: WorldState, entity_id: str) -> int:
    """Get entity's size modifier for combat maneuvers."""
    size_category = _get_entity_field(world_state, entity_id, EF.SIZE_CATEGORY, "medium")
    return get_size_modifier(size_category)


def _get_stability_bonus(world_state: WorldState, entity_id: str) -> int:
    """Get entity's stability bonus (+4 for dwarves, quadrupeds, etc.)."""
    return _get_entity_field(world_state, entity_id, EF.STABILITY_BONUS, 0)


def _get_bab(world_state: WorldState, entity_id: str) -> int:
    """Get entity's Base Attack Bonus. Defaults to attack_bonus field if available."""
    entity = world_state.entities.get(entity_id)
    if entity is None:
        logger.warning("Entity '%s' not found; defaulting BAB to 0", entity_id)
        return 0
    # Use attack_bonus as BAB proxy (actual BAB would need character level system)
    return entity.get(EF.ATTACK_BONUS, entity.get(EF.BAB, 0))


def _get_touch_ac(world_state: WorldState, entity_id: str) -> int:
    """Get entity's touch AC. Touch AC = 10 + Dex modifier + size modifier + deflection."""
    dex_mod = _get_dex_modifier(world_state, entity_id)
    size_mod = _get_size_modifier(world_state, entity_id)
    # Touch AC excludes armor, natural armor, shield bonuses
    # Simplified: base 10 + Dex + size
    return 10 + dex_mod + size_mod


def _is_entity_defeated(world_state: WorldState, entity_id: str) -> bool:
    """Check if entity is defeated."""
    return _get_entity_field(world_state, entity_id, EF.DEFEATED, False)


def _roll_opposed_check(
    rng: RNGManager,
    attacker_modifier: int,
    defender_modifier: int,
    check_type: str
) -> OpposedCheckResult:
    """Roll an opposed check deterministically.

    Attacker roll consumed first, then defender roll.
    Ties go to defender (PHB convention).
    """
    combat_rng = rng.stream("combat")
    attacker_roll = combat_rng.randint(1, 20)
    defender_roll = combat_rng.randint(1, 20)

    attacker_total = attacker_roll + attacker_modifier
    defender_total = defender_roll + defender_modifier

    # Attacker wins only if strictly greater (ties go to defender)
    attacker_wins = attacker_total > defender_total
    margin = attacker_total - defender_total

    return OpposedCheckResult(
        check_type=check_type,
        attacker_roll=attacker_roll,
        attacker_modifier=attacker_modifier,
        attacker_total=attacker_total,
        defender_roll=defender_roll,
        defender_modifier=defender_modifier,
        defender_total=defender_total,
        attacker_wins=attacker_wins,
        margin=margin,
    )


def _roll_touch_attack(
    rng: RNGManager,
    attacker_id: str,
    target_id: str,
    world_state: WorldState,
    attack_bonus: int,
) -> TouchAttackResult:
    """Roll a melee touch attack.

    Natural 20 auto-hits, natural 1 auto-misses.
    """
    combat_rng = rng.stream("combat")
    roll = combat_rng.randint(1, 20)
    target_touch_ac = _get_touch_ac(world_state, target_id)
    total = roll + attack_bonus

    is_natural_20 = (roll == 20)
    is_natural_1 = (roll == 1)

    # Determine hit: natural 20 always hits, natural 1 always misses, else compare to AC
    if is_natural_1:
        hit = False
    elif is_natural_20:
        hit = True
    else:
        hit = total >= target_touch_ac

    return TouchAttackResult(
        attacker_id=attacker_id,
        target_id=target_id,
        roll=roll,
        attack_bonus=attack_bonus,
        total=total,
        target_touch_ac=target_touch_ac,
        hit=hit,
        is_natural_20=is_natural_20,
        is_natural_1=is_natural_1,
    )


# ==============================================================================
# BULL RUSH RESOLUTION
# ==============================================================================

def resolve_bull_rush(
    intent: BullRushIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a Bull Rush maneuver.

    PHB p.154-155: Opposed Strength check. Winner pushes loser.
    - Charge bonus: +2 if is_charge
    - Stability bonus: +4 for dwarves, quadrupeds, creatures with more than 2 legs

    RNG Consumption Order:
    1. AoO attack rolls (handled externally)
    2. Attacker Strength check (d20) - "combat" stream
    3. Defender Strength check (d20) - "combat" stream

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    # Add AoO events if provided
    if aoo_events:
        events.extend(aoo_events)
        current_event_id += len(aoo_events)

    # If attacker was defeated by AoO, abort
    if aoo_defeated:
        result = ManeuverResult(
            maneuver_type="bull_rush",
            success=False,
            events=[e.to_dict() if hasattr(e, 'to_dict') else {"event_type": e.event_type, "payload": e.payload} for e in events],
            provoker_defeated=True,
        )
        return events, world_state, result

    attacker_id = intent.attacker_id
    target_id = intent.target_id

    # Emit bull_rush_declared event
    events.append(Event(
        event_id=current_event_id,
        event_type="bull_rush_declared",
        timestamp=current_timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
            "is_charge": intent.is_charge,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 154}],  # PHB Bull Rush
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Calculate modifiers
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_size_modifier(world_state, attacker_id)
    charge_bonus = 2 if intent.is_charge else 0
    attacker_modifier = attacker_str + attacker_size + charge_bonus

    defender_str = _get_str_modifier(world_state, target_id)
    defender_size = _get_size_modifier(world_state, target_id)
    defender_stability = _get_stability_bonus(world_state, target_id)
    defender_modifier = defender_str + defender_size + defender_stability

    # Roll opposed Strength check
    check_result = _roll_opposed_check(rng, attacker_modifier, defender_modifier, "strength")

    # Emit opposed_check event
    events.append(Event(
        event_id=current_event_id,
        event_type="opposed_check",
        timestamp=current_timestamp,
        payload=check_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 154}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    position_change = None

    if check_result.attacker_wins:
        # Calculate push distance: 5 feet + 5 per 5 points margin
        base_push = 5
        extra_push = (check_result.margin // 5) * 5
        push_distance = base_push + extra_push

        # Get current positions (for position calculation)
        attacker_pos = _get_entity_field(world_state, attacker_id, EF.POSITION, {"x": 0, "y": 0})
        defender_pos = _get_entity_field(world_state, target_id, EF.POSITION, {"x": 0, "y": 0})

        # Calculate push direction (defender moves away from attacker)
        dx = defender_pos["x"] - attacker_pos["x"]
        dy = defender_pos["y"] - attacker_pos["y"]

        # Normalize direction (simplified: use sign)
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        # If adjacent, default to horizontal push
        if dx == 0 and dy == 0:
            dx = 1

        # CP-19: Check for hazards along push path
        from aidm.core.terrain_resolver import resolve_forced_movement_with_hazards

        hazard_events, world_state, final_defender_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id=target_id,
            start_pos=defender_pos,
            push_direction=(dx, dy),
            push_distance=push_distance,
            world_state=world_state,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=current_timestamp,
        )
        events.extend(hazard_events)
        current_event_id += len(hazard_events)
        current_timestamp += len(hazard_events) * 0.01

        new_defender_pos = final_defender_pos

        # Attacker may advance into vacated space
        new_attacker_pos = {
            "x": defender_pos["x"],
            "y": defender_pos["y"],
        }

        position_change = {
            "attacker": new_attacker_pos,
            "defender": new_defender_pos,
            "push_distance": push_distance,
            "hazard_triggered": falling_result is not None,
        }

        # Update world state with new positions
        entities = deepcopy(world_state.entities)
        if target_id in entities:
            entities[target_id][EF.POSITION] = new_defender_pos
        if attacker_id in entities:
            entities[attacker_id][EF.POSITION] = new_attacker_pos
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=world_state.active_combat,
        )

        # Emit success event
        events.append(Event(
            event_id=current_event_id,
            event_type="bull_rush_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "pushed_distance": push_distance,
                "new_attacker_pos": new_attacker_pos,
                "new_defender_pos": new_defender_pos,
                "hazard_triggered": falling_result is not None,
                "falling_damage": falling_result.total_damage if falling_result else 0,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 154}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="bull_rush",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            position_change=position_change,
        )
    else:
        # Attacker pushed back 5 feet
        attacker_pos = _get_entity_field(world_state, attacker_id, EF.POSITION, {"x": 0, "y": 0})
        defender_pos = _get_entity_field(world_state, target_id, EF.POSITION, {"x": 0, "y": 0})

        # Push attacker away from defender
        dx = attacker_pos["x"] - defender_pos["x"]
        dy = attacker_pos["y"] - defender_pos["y"]
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        if dx == 0 and dy == 0:
            dx = -1

        # CP-19B: Route failure pushback through hazard resolver
        from aidm.core.terrain_resolver import resolve_forced_movement_with_hazards

        hazard_events, world_state, new_attacker_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id=attacker_id,
            start_pos=attacker_pos,
            push_direction=(dx, dy),
            push_distance=5,
            world_state=world_state,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=current_timestamp,
        )
        events.extend(hazard_events)
        current_event_id += len(hazard_events)
        current_timestamp += len(hazard_events) * 0.01

        # Emit failure event
        events.append(Event(
            event_id=current_event_id,
            event_type="bull_rush_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "attacker_pushed_back": 5,
                "new_attacker_pos": new_attacker_pos,
                "attacker_prone": False,  # Origin occupied check simplified
                "hazard_triggered": falling_result is not None,
                "falling_damage": falling_result.total_damage if falling_result else 0,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 154}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="bull_rush",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            position_change={
                "attacker": new_attacker_pos,
                "defender": defender_pos,
                "push_distance": 0,
                "hazard_triggered": falling_result is not None,
            },
        )

    return events, world_state, result


# ==============================================================================
# TRIP RESOLUTION
# ==============================================================================

def resolve_trip(
    intent: TripIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a Trip maneuver.

    PHB p.158-160: Melee touch attack, then opposed check (Str vs max(Str, Dex)).
    On failure, defender may counter-trip.

    RNG Consumption Order:
    1. AoO attack rolls (handled externally)
    2. Touch attack roll (d20) - "combat" stream
    3. Attacker trip check (d20) - "combat" stream
    4. Defender trip check (d20) - "combat" stream
    5. [If counter-trip] Defender counter-trip check (d20) - "combat" stream
    6. [If counter-trip] Attacker counter-trip defense (d20) - "combat" stream

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    if aoo_events:
        events.extend(aoo_events)
        current_event_id += len(aoo_events)

    if aoo_defeated:
        result = ManeuverResult(
            maneuver_type="trip",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            provoker_defeated=True,
        )
        return events, world_state, result

    attacker_id = intent.attacker_id
    target_id = intent.target_id

    # Emit trip_declared event
    events.append(Event(
        event_id=current_event_id,
        event_type="trip_declared",
        timestamp=current_timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Calculate touch attack bonus (BAB + Str + size)
    attacker_bab = _get_bab(world_state, attacker_id)
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_size_modifier(world_state, attacker_id)
    touch_attack_bonus = attacker_bab + attacker_str + attacker_size

    # Roll touch attack
    touch_result = _roll_touch_attack(rng, attacker_id, target_id, world_state, touch_attack_bonus)

    # Emit touch attack event
    events.append(Event(
        event_id=current_event_id,
        event_type="touch_attack_roll",
        timestamp=current_timestamp,
        payload=touch_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # If touch attack misses, trip fails
    if not touch_result.hit:
        events.append(Event(
            event_id=current_event_id,
            event_type="trip_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "touch_attack_missed",
                "counter_trip_allowed": False,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 158}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="trip",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
        return events, world_state, result

    # Touch attack hit - proceed to opposed check
    # Attacker uses Str + size, Defender uses max(Str, Dex) + size + stability
    attacker_modifier = attacker_str + attacker_size

    defender_str = _get_str_modifier(world_state, target_id)
    defender_dex = _get_dex_modifier(world_state, target_id)
    defender_ability = max(defender_str, defender_dex)
    defender_size = _get_size_modifier(world_state, target_id)
    defender_stability = _get_stability_bonus(world_state, target_id)
    defender_modifier = defender_ability + defender_size + defender_stability

    # Roll opposed trip check
    check_result = _roll_opposed_check(rng, attacker_modifier, defender_modifier, "trip")

    # Emit opposed check event
    events.append(Event(
        event_id=current_event_id,
        event_type="opposed_check",
        timestamp=current_timestamp,
        payload=check_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    if check_result.attacker_wins:
        # Trip success - apply Prone condition to target
        condition = create_prone_condition(source="trip_attack", applied_at_event_id=current_event_id)
        world_state = apply_condition(world_state, target_id, condition)

        events.append(Event(
            event_id=current_event_id,
            event_type="trip_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "condition_applied": "prone",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 158}],
        ))
        current_event_id += 1

        # Emit condition_applied event
        events.append(Event(
            event_id=current_event_id,
            event_type="condition_applied",
            timestamp=current_timestamp,
            payload={
                "target_id": target_id,
                "condition_type": "prone",
                "source": "trip_attack",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 311}],  # PHB Prone condition
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="trip",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            condition_applied="prone",
        )
    else:
        # Trip failed - defender may counter-trip
        events.append(Event(
            event_id=current_event_id,
            event_type="trip_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "opposed_check_lost",
                "counter_trip_allowed": True,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 158}],
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # Counter-trip: defender becomes attacker, original attacker defends
        counter_attacker_modifier = defender_ability + defender_size + defender_stability
        counter_defender_modifier = attacker_str + attacker_size

        counter_result = _roll_opposed_check(rng, counter_attacker_modifier, counter_defender_modifier, "counter_trip")

        events.append(Event(
            event_id=current_event_id,
            event_type="opposed_check",
            timestamp=current_timestamp,
            payload={
                **counter_result.to_dict(),
                "is_counter_trip": True,
                "original_attacker": attacker_id,
                "counter_attacker": target_id,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 158}],
        ))
        current_event_id += 1
        current_timestamp += 0.01

        if counter_result.attacker_wins:
            # Counter-trip success - original attacker falls prone
            condition = create_prone_condition(source="counter_trip", applied_at_event_id=current_event_id)
            world_state = apply_condition(world_state, attacker_id, condition)

            events.append(Event(
                event_id=current_event_id,
                event_type="counter_trip_success",
                timestamp=current_timestamp,
                payload={
                    "counter_attacker": target_id,
                    "target_id": attacker_id,
                    "condition_applied": "prone",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 158}],
            ))
            current_event_id += 1

            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=current_timestamp,
                payload={
                    "target_id": attacker_id,
                    "condition_type": "prone",
                    "source": "counter_trip",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 311}],
            ))
            current_event_id += 1

            result = ManeuverResult(
                maneuver_type="trip",
                success=False,
                events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
                counter_attack_result={
                    "success": True,
                    "original_attacker_prone": True,
                },
            )
        else:
            # Counter-trip failed - no one is prone
            events.append(Event(
                event_id=current_event_id,
                event_type="counter_trip_failure",
                timestamp=current_timestamp,
                payload={
                    "counter_attacker": target_id,
                    "target_id": attacker_id,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 158}],
            ))
            current_event_id += 1

            result = ManeuverResult(
                maneuver_type="trip",
                success=False,
                events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
                counter_attack_result={
                    "success": False,
                    "original_attacker_prone": False,
                },
            )

    return events, world_state, result


# ==============================================================================
# OVERRUN RESOLUTION
# ==============================================================================

def resolve_overrun(
    intent: OverrunIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve an Overrun maneuver.

    PHB p.157-158: Opposed check (Str vs max(Str, Dex)).
    Defender may choose to avoid (step aside).
    Success = defender prone + attacker continues movement.
    Failure = attacker pushed back; failure by 5+ = attacker prone.

    RNG Consumption Order:
    1. AoO attack rolls (handled externally)
    2. Attacker overrun check (d20) - "combat" stream
    3. Defender overrun check (d20) - "combat" stream

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    if aoo_events:
        events.extend(aoo_events)
        current_event_id += len(aoo_events)

    if aoo_defeated:
        result = ManeuverResult(
            maneuver_type="overrun",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            provoker_defeated=True,
        )
        return events, world_state, result

    attacker_id = intent.attacker_id
    target_id = intent.target_id

    # Emit overrun_declared event
    events.append(Event(
        event_id=current_event_id,
        event_type="overrun_declared",
        timestamp=current_timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
            "is_charge": intent.is_charge,
            "defender_avoids": intent.defender_avoids,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Check if defender avoids (controlled by AI/doctrine)
    if intent.defender_avoids:
        events.append(Event(
            event_id=current_event_id,
            event_type="overrun_avoided",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "defender_id": target_id,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 157}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="overrun",
            success=True,  # Attacker gets to continue movement
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
        return events, world_state, result

    # Defender does not avoid - proceed to opposed check
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_size_modifier(world_state, attacker_id)
    charge_bonus = 2 if intent.is_charge else 0
    attacker_modifier = attacker_str + attacker_size + charge_bonus

    defender_str = _get_str_modifier(world_state, target_id)
    defender_dex = _get_dex_modifier(world_state, target_id)
    defender_ability = max(defender_str, defender_dex)
    defender_size = _get_size_modifier(world_state, target_id)
    defender_stability = _get_stability_bonus(world_state, target_id)
    defender_modifier = defender_ability + defender_size + defender_stability

    # Roll opposed check
    check_result = _roll_opposed_check(rng, attacker_modifier, defender_modifier, "overrun")

    # Emit opposed check event
    events.append(Event(
        event_id=current_event_id,
        event_type="opposed_check",
        timestamp=current_timestamp,
        payload=check_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 157}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    if check_result.attacker_wins:
        # Overrun success - defender is knocked prone
        condition = create_prone_condition(source="overrun", applied_at_event_id=current_event_id)
        world_state = apply_condition(world_state, target_id, condition)

        events.append(Event(
            event_id=current_event_id,
            event_type="overrun_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "defender_id": target_id,
                "condition_applied": "prone",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 157}],
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="condition_applied",
            timestamp=current_timestamp,
            payload={
                "target_id": target_id,
                "condition_type": "prone",
                "source": "overrun",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 311}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="overrun",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            condition_applied="prone",
        )
    else:
        # Overrun failure - attacker pushed back
        attacker_prone = check_result.margin <= -5  # Failure by 5+ means prone

        # Update attacker position (pushed back 5 feet)
        attacker_pos = _get_entity_field(world_state, attacker_id, EF.POSITION, {"x": 0, "y": 0})
        defender_pos = _get_entity_field(world_state, target_id, EF.POSITION, {"x": 0, "y": 0})

        dx = attacker_pos["x"] - defender_pos["x"]
        dy = attacker_pos["y"] - defender_pos["y"]
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        if dx == 0 and dy == 0:
            dx = -1

        # CP-19B: Route failure pushback through hazard resolver
        from aidm.core.terrain_resolver import resolve_forced_movement_with_hazards

        hazard_events, world_state, new_attacker_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id=attacker_id,
            start_pos=attacker_pos,
            push_direction=(dx, dy),
            push_distance=5,
            world_state=world_state,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=current_timestamp,
        )
        events.extend(hazard_events)
        current_event_id += len(hazard_events)
        current_timestamp += len(hazard_events) * 0.01

        events.append(Event(
            event_id=current_event_id,
            event_type="overrun_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "defender_id": target_id,
                "pushed_back": 5,
                "attacker_prone": attacker_prone,
                "margin": check_result.margin,
                "hazard_triggered": falling_result is not None,
                "falling_damage": falling_result.total_damage if falling_result else 0,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 157}],
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # If attacker falls prone, apply condition
        if attacker_prone:
            condition = create_prone_condition(source="overrun_failure", applied_at_event_id=current_event_id)
            world_state = apply_condition(world_state, attacker_id, condition)

            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=current_timestamp,
                payload={
                    "target_id": attacker_id,
                    "condition_type": "prone",
                    "source": "overrun_failure",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 311}],
            ))
            current_event_id += 1

        result = ManeuverResult(
            maneuver_type="overrun",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            condition_applied="prone" if attacker_prone else None,
        )

    return events, world_state, result


# ==============================================================================
# SUNDER RESOLUTION (DEGRADED)
# ==============================================================================

def resolve_sunder(
    intent: SunderIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a Sunder maneuver (DEGRADED).

    PHB p.158-159: Opposed attack rolls. Winner's item takes damage.
    DEGRADED: Damage is logged for narrative purposes only.
    No persistent item state change.

    RNG Consumption Order:
    1. AoO attack rolls (handled externally)
    2. Attacker attack roll (d20) - "combat" stream
    3. Defender attack roll (d20) - "combat" stream
    4. [If success] Damage roll - "combat" stream

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    if aoo_events:
        events.extend(aoo_events)
        current_event_id += len(aoo_events)

    if aoo_defeated:
        result = ManeuverResult(
            maneuver_type="sunder",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            provoker_defeated=True,
        )
        return events, world_state, result

    attacker_id = intent.attacker_id
    target_id = intent.target_id

    # Emit sunder_declared event
    events.append(Event(
        event_id=current_event_id,
        event_type="sunder_declared",
        timestamp=current_timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
            "target_item": intent.target_item,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Calculate attack roll modifiers
    attacker_bab = _get_bab(world_state, attacker_id)
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_size_modifier(world_state, attacker_id)
    attacker_modifier = attacker_bab + attacker_str + attacker_size

    defender_bab = _get_bab(world_state, target_id)
    defender_str = _get_str_modifier(world_state, target_id)
    defender_size = _get_size_modifier(world_state, target_id)
    defender_modifier = defender_bab + defender_str + defender_size

    # Roll opposed attack rolls
    check_result = _roll_opposed_check(rng, attacker_modifier, defender_modifier, "sunder")

    events.append(Event(
        event_id=current_event_id,
        event_type="opposed_check",
        timestamp=current_timestamp,
        payload=check_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    if check_result.attacker_wins:
        # Roll damage (use 1d8 as default weapon damage)
        combat_rng = rng.stream("combat")
        damage_roll = combat_rng.randint(1, 8)
        damage_bonus = attacker_str  # Add Str to damage
        total_damage = max(0, damage_roll + damage_bonus)

        events.append(Event(
            event_id=current_event_id,
            event_type="sunder_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "target_item": intent.target_item,
                "damage_roll": damage_roll,
                "damage_bonus": damage_bonus,
                "total_damage": total_damage,
                "note": "DEGRADED: Narrative only, no persistent state change",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 158}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="sunder",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            damage_dealt=total_damage,
        )
    else:
        events.append(Event(
            event_id=current_event_id,
            event_type="sunder_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "target_item": intent.target_item,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 158}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="sunder",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )

    return events, world_state, result


# ==============================================================================
# DISARM RESOLUTION (DEGRADED)
# ==============================================================================

def resolve_disarm(
    intent: DisarmIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    aoo_dealt_damage: bool = False,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a Disarm maneuver (DEGRADED).

    PHB p.155: Opposed attack rolls. Success = weapon dropped.
    DEGRADED: Weapon "drops" narratively but no persistent state change.
    If AoO deals damage, disarm automatically fails.

    RNG Consumption Order:
    1. AoO attack rolls (handled externally)
    2. Attacker attack roll (d20) - "combat" stream
    3. Defender attack roll (d20) - "combat" stream
    4. [If counter-disarm] Defender attack roll (d20) - "combat" stream
    5. [If counter-disarm] Attacker attack roll (d20) - "combat" stream

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    if aoo_events:
        events.extend(aoo_events)
        current_event_id += len(aoo_events)

    if aoo_defeated:
        result = ManeuverResult(
            maneuver_type="disarm",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            provoker_defeated=True,
        )
        return events, world_state, result

    attacker_id = intent.attacker_id
    target_id = intent.target_id

    # Emit disarm_declared event
    events.append(Event(
        event_id=current_event_id,
        event_type="disarm_declared",
        timestamp=current_timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 155}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # If AoO dealt any damage, disarm automatically fails
    if aoo_dealt_damage:
        events.append(Event(
            event_id=current_event_id,
            event_type="disarm_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "aoo_dealt_damage",
                "counter_disarm_allowed": False,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="disarm",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
        return events, world_state, result

    # Calculate attack roll modifiers
    attacker_bab = _get_bab(world_state, attacker_id)
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_size_modifier(world_state, attacker_id)
    attacker_modifier = attacker_bab + attacker_str + attacker_size

    defender_bab = _get_bab(world_state, target_id)
    defender_str = _get_str_modifier(world_state, target_id)
    defender_size = _get_size_modifier(world_state, target_id)
    defender_modifier = defender_bab + defender_str + defender_size

    # Roll opposed attack rolls
    check_result = _roll_opposed_check(rng, attacker_modifier, defender_modifier, "disarm")

    events.append(Event(
        event_id=current_event_id,
        event_type="opposed_check",
        timestamp=current_timestamp,
        payload=check_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 155}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    if check_result.attacker_wins:
        # Disarm success - weapon "dropped" (narrative only)
        events.append(Event(
            event_id=current_event_id,
            event_type="disarm_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "weapon_dropped": True,
                "note": "DEGRADED: Narrative only, no persistent state change",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="disarm",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
    else:
        # Disarm failed - defender may counter-disarm
        events.append(Event(
            event_id=current_event_id,
            event_type="disarm_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "opposed_check_lost",
                "counter_disarm_allowed": True,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # Counter-disarm: defender rolls against attacker
        counter_result = _roll_opposed_check(rng, defender_modifier, attacker_modifier, "counter_disarm")

        events.append(Event(
            event_id=current_event_id,
            event_type="opposed_check",
            timestamp=current_timestamp,
            payload={
                **counter_result.to_dict(),
                "is_counter_disarm": True,
                "original_attacker": attacker_id,
                "counter_attacker": target_id,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1
        current_timestamp += 0.01

        if counter_result.attacker_wins:
            # Counter-disarm success
            events.append(Event(
                event_id=current_event_id,
                event_type="counter_disarm_success",
                timestamp=current_timestamp,
                payload={
                    "counter_attacker": target_id,
                    "target_id": attacker_id,
                    "weapon_dropped": True,
                    "note": "DEGRADED: Narrative only, no persistent state change",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 155}],
            ))
            current_event_id += 1

            result = ManeuverResult(
                maneuver_type="disarm",
                success=False,
                events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
                counter_attack_result={"success": True},
            )
        else:
            # Counter-disarm failed
            events.append(Event(
                event_id=current_event_id,
                event_type="counter_disarm_failure",
                timestamp=current_timestamp,
                payload={
                    "counter_attacker": target_id,
                    "target_id": attacker_id,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 155}],
            ))
            current_event_id += 1

            result = ManeuverResult(
                maneuver_type="disarm",
                success=False,
                events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
                counter_attack_result={"success": False},
            )

    return events, world_state, result


# ==============================================================================
# GRAPPLE RESOLUTION (DEGRADED - GRAPPLE-LITE)
# ==============================================================================

def resolve_grapple(
    intent: GrappleIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    aoo_dealt_damage: bool = False,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a Grapple maneuver (DEGRADED - Grapple-Lite).

    PHB p.155-157: Melee touch attack, then opposed grapple check.
    DEGRADED (G-T3C Mitigation):
    - Only applies Grappled condition to target
    - Attacker does NOT gain any condition (asymmetric)
    - No pinning, no escape loops, no grapple damage
    If AoO deals damage, grapple automatically fails.

    RNG Consumption Order:
    1. AoO attack rolls (handled externally)
    2. Touch attack roll (d20) - "combat" stream
    3. Attacker grapple check (d20) - "combat" stream
    4. Defender grapple check (d20) - "combat" stream

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    if aoo_events:
        events.extend(aoo_events)
        current_event_id += len(aoo_events)

    if aoo_defeated:
        result = ManeuverResult(
            maneuver_type="grapple",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            provoker_defeated=True,
        )
        return events, world_state, result

    attacker_id = intent.attacker_id
    target_id = intent.target_id

    # Emit grapple_declared event
    events.append(Event(
        event_id=current_event_id,
        event_type="grapple_declared",
        timestamp=current_timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 155}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # If AoO dealt any damage, grapple automatically fails
    if aoo_dealt_damage:
        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "aoo_dealt_damage",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="grapple",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
        return events, world_state, result

    # Calculate touch attack bonus (BAB + Str + size)
    attacker_bab = _get_bab(world_state, attacker_id)
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_size_modifier(world_state, attacker_id)
    touch_attack_bonus = attacker_bab + attacker_str + attacker_size

    # Roll touch attack
    touch_result = _roll_touch_attack(rng, attacker_id, target_id, world_state, touch_attack_bonus)

    events.append(Event(
        event_id=current_event_id,
        event_type="touch_attack_roll",
        timestamp=current_timestamp,
        payload=touch_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 155}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # If touch attack misses, grapple fails
    if not touch_result.hit:
        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "touch_attack_missed",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="grapple",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
        return events, world_state, result

    # Touch attack hit - proceed to opposed grapple check
    # Grapple check = BAB + Str + size modifier
    attacker_grapple_modifier = attacker_bab + attacker_str + attacker_size

    defender_bab = _get_bab(world_state, target_id)
    defender_str = _get_str_modifier(world_state, target_id)
    defender_size = _get_size_modifier(world_state, target_id)
    defender_grapple_modifier = defender_bab + defender_str + defender_size

    # Roll opposed grapple check
    check_result = _roll_opposed_check(rng, attacker_grapple_modifier, defender_grapple_modifier, "grapple")

    events.append(Event(
        event_id=current_event_id,
        event_type="opposed_check",
        timestamp=current_timestamp,
        payload=check_result.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 156}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    if check_result.attacker_wins:
        # Grapple success - apply Grappled condition to target ONLY (asymmetric)
        condition = create_grappled_condition(source="grapple_attack", applied_at_event_id=current_event_id)
        world_state = apply_condition(world_state, target_id, condition)

        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "condition_applied": "grappled",
                "note": "DEGRADED: Unidirectional condition (target only), no attacker state change",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="condition_applied",
            timestamp=current_timestamp,
            payload={
                "target_id": target_id,
                "condition_type": "grappled",
                "source": "grapple_attack",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 311}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="grapple",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            condition_applied="grappled",
        )
    else:
        # Grapple failed - no effect
        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "opposed_check_lost",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="grapple",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )

    return events, world_state, result


# ==============================================================================
# UNIFIED MANEUVER RESOLUTION DISPATCHER
# ==============================================================================

ManeuverIntent = Union[
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent
]


def resolve_maneuver(
    intent: ManeuverIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    aoo_dealt_damage: bool = False,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Unified dispatcher for all combat maneuver resolution.

    Routes to appropriate resolver based on intent type.

    Args:
        intent: Maneuver intent (BullRushIntent, TripIntent, etc.)
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Starting timestamp
        aoo_events: Events from AoO resolution (optional)
        aoo_defeated: True if attacker was defeated by AoO
        aoo_dealt_damage: True if any AoO dealt damage (for Disarm/Grapple auto-fail)

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    if isinstance(intent, BullRushIntent):
        return resolve_bull_rush(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated)
    elif isinstance(intent, TripIntent):
        return resolve_trip(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated)
    elif isinstance(intent, OverrunIntent):
        return resolve_overrun(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated)
    elif isinstance(intent, SunderIntent):
        return resolve_sunder(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated)
    elif isinstance(intent, DisarmIntent):
        return resolve_disarm(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, aoo_dealt_damage)
    elif isinstance(intent, GrappleIntent):
        return resolve_grapple(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, aoo_dealt_damage)
    else:
        raise ValueError(f"Unknown maneuver intent type: {type(intent)}")
