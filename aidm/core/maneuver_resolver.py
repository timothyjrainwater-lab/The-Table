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
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent, GrappleEscapeIntent, PinEscapeIntent,
    OpposedCheckResult, ManeuverResult, TouchAttackResult,
    get_size_modifier, get_standard_attack_size_modifier,
)
from aidm.core.attack_resolver import parse_damage_dice, roll_dice
from aidm.schemas.conditions import (
    create_prone_condition, create_grappled_condition, create_grappling_condition,
    create_pinned_condition, ConditionType,
)
from aidm.core.conditions import apply_condition, remove_condition


@dataclass(frozen=True)
class GrappleResult:
    """Result of a grapple initiation attempt. CP-22."""
    success: bool
    touch_hit: bool
    initiator_roll: int
    defender_roll: int
    initiator_id: str
    target_id: str
    events: list

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
    """Get entity's SPECIAL size modifier for combat maneuver opposed checks."""
    size_category = _get_entity_field(world_state, entity_id, EF.SIZE_CATEGORY, "medium")
    return get_size_modifier(size_category)


def _get_standard_attack_size_modifier(world_state: WorldState, entity_id: str) -> int:
    """Get entity's STANDARD attack size modifier (PHB Table 8-1).

    Used for touch attacks to initiate maneuvers and sunder attack rolls.
    """
    size_category = _get_entity_field(world_state, entity_id, EF.SIZE_CATEGORY, "medium")
    return get_standard_attack_size_modifier(size_category)


def _get_stability_bonus(world_state: WorldState, entity_id: str) -> int:
    """Get entity's stability bonus (+4 for dwarves, quadrupeds, etc.)."""
    return _get_entity_field(world_state, entity_id, EF.STABILITY_BONUS, 0)


def _get_weapon_type(world_state: WorldState, entity_id: str) -> str:
    """Get entity's weapon type from EF.WEAPON dict data.

    WO-WEAPON-PLUMBING-001: Returns 'one-handed' default if no weapon_type in data.
    Handles both string and dict EF.WEAPON patterns.
    """
    weapon_data = _get_entity_field(world_state, entity_id, EF.WEAPON)
    if weapon_data and isinstance(weapon_data, dict):
        return weapon_data.get("weapon_type", "one-handed")
    return "one-handed"


def _get_weapon_grip(world_state: WorldState, entity_id: str) -> str:
    """Get entity's weapon grip from EF.WEAPON dict data.

    WO-WEAPON-PLUMBING-001: Returns 'one-handed' default if no grip in data.
    """
    weapon_data = _get_entity_field(world_state, entity_id, EF.WEAPON)
    if weapon_data and isinstance(weapon_data, dict):
        return weapon_data.get("grip", "one-handed")
    return "one-handed"


def _get_bab(world_state: WorldState, entity_id: str) -> int:
    """Get entity's Base Attack Bonus.

    WO-ENGINE-MANEUVER-BAB-FIX-001: Uses EF.BAB (Type 1 component — BAB only).
    Previous code used EF.ATTACK_BONUS (BAB+STR composite) which double-counted STR
    in maneuver opposed checks that add STR separately.
    """
    entity = world_state.entities.get(entity_id)
    if entity is None:
        logger.warning("Entity '%s' not found; defaulting BAB to 0", entity_id)
        return 0
    return entity.get(EF.BAB, 0)


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
    rng: RNGProvider,
    attacker_modifier: int,
    defender_modifier: int,
    check_type: str
) -> OpposedCheckResult:
    """Roll an opposed check deterministically.

    Attacker roll consumed first, then defender roll.
    Ties go to initiator (attacker) per B-AMB-02 decision.
    """
    combat_rng = rng.stream("combat")
    attacker_roll = combat_rng.randint(1, 20)
    defender_roll = combat_rng.randint(1, 20)

    attacker_total = attacker_roll + attacker_modifier
    defender_total = defender_roll + defender_modifier

    # Initiator (attacker) wins ties (B-AMB-02 / H-AMB-01)
    attacker_wins = attacker_total >= defender_total
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
    rng: RNGProvider,
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
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    causal_chain_id: Optional[str] = None,
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
    bull_rush_payload = {
        "attacker_id": attacker_id,
        "target_id": target_id,
        "is_charge": intent.is_charge,
    }
    # WO-BRIEF-WIDTH-001: Propagate causal chain
    if causal_chain_id is not None:
        bull_rush_payload["causal_chain_id"] = causal_chain_id
        bull_rush_payload["chain_position"] = 1
    events.append(Event(
        event_id=current_event_id,
        event_type="bull_rush_declared",
        timestamp=current_timestamp,
        payload=bull_rush_payload,
        citations=[{"source_id": "681f92bc94ff", "page": 154}],  # PHB Bull Rush
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Calculate modifiers
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_size_modifier(world_state, attacker_id)
    charge_bonus = 2 if intent.is_charge else 0
    attacker_modifier = attacker_str + attacker_size + charge_bonus
    # WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001: Improved Bull Rush grants +4 (PHB p.96)
    if "improved_bull_rush" in world_state.entities.get(attacker_id, {}).get(EF.FEATS, []):
        attacker_modifier += 4

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
        bull_rush_success_payload = {
            "attacker_id": attacker_id,
            "target_id": target_id,
            "pushed_distance": push_distance,
            "new_attacker_pos": new_attacker_pos,
            "new_defender_pos": new_defender_pos,
            "hazard_triggered": falling_result is not None,
            "falling_damage": falling_result.total_damage if falling_result else 0,
        }
        # WO-BRIEF-WIDTH-001: Propagate causal chain
        if causal_chain_id is not None:
            bull_rush_success_payload["causal_chain_id"] = causal_chain_id
            bull_rush_success_payload["chain_position"] = 1
        events.append(Event(
            event_id=current_event_id,
            event_type="bull_rush_success",
            timestamp=current_timestamp,
            payload=bull_rush_success_payload,
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
        bull_rush_fail_payload = {
            "attacker_id": attacker_id,
            "target_id": target_id,
            "attacker_pushed_back": 5,
            "new_attacker_pos": new_attacker_pos,
            "attacker_prone": False,  # Origin occupied check simplified
            "hazard_triggered": falling_result is not None,
            "falling_damage": falling_result.total_damage if falling_result else 0,
        }
        # WO-BRIEF-WIDTH-001: Propagate causal chain
        if causal_chain_id is not None:
            bull_rush_fail_payload["causal_chain_id"] = causal_chain_id
            bull_rush_fail_payload["chain_position"] = 1
        events.append(Event(
            event_id=current_event_id,
            event_type="bull_rush_failure",
            timestamp=current_timestamp,
            payload=bull_rush_fail_payload,
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
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    causal_chain_id: Optional[str] = None,
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
    trip_declared_payload = {
        "attacker_id": attacker_id,
        "target_id": target_id,
    }
    # WO-BRIEF-WIDTH-001: Propagate causal chain
    if causal_chain_id is not None:
        trip_declared_payload["causal_chain_id"] = causal_chain_id
        trip_declared_payload["chain_position"] = 1
    events.append(Event(
        event_id=current_event_id,
        event_type="trip_declared",
        timestamp=current_timestamp,
        payload=trip_declared_payload,
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Calculate touch attack bonus (BAB + Str + STANDARD attack size modifier)
    # WO-FIX-07: Touch attack to initiate trip uses STANDARD attack size modifier (PHB Table 8-1)
    attacker_bab = _get_bab(world_state, attacker_id)
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_std_size = _get_standard_attack_size_modifier(world_state, attacker_id)
    touch_attack_bonus = attacker_bab + attacker_str + attacker_std_size

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
        trip_fail_payload = {
            "attacker_id": attacker_id,
            "target_id": target_id,
            "reason": "touch_attack_missed",
            "counter_trip_allowed": False,
        }
        # WO-BRIEF-WIDTH-001: Propagate causal chain
        if causal_chain_id is not None:
            trip_fail_payload["causal_chain_id"] = causal_chain_id
            trip_fail_payload["chain_position"] = 1
        events.append(Event(
            event_id=current_event_id,
            event_type="trip_failure",
            timestamp=current_timestamp,
            payload=trip_fail_payload,
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
    # Opposed check uses SPECIAL size modifier (not standard attack)
    # Attacker uses Str + special size, Defender uses max(Str, Dex) + special size + stability
    attacker_size = _get_size_modifier(world_state, attacker_id)
    attacker_modifier = attacker_str + attacker_size
    # WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001: Improved Trip grants +4 to STR check (PHB p.96)
    if "improved_trip" in world_state.entities.get(attacker_id, {}).get(EF.FEATS, []):
        attacker_modifier += 4

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

        trip_success_payload = {
            "attacker_id": attacker_id,
            "target_id": target_id,
            "condition_applied": "prone",
        }
        # WO-BRIEF-WIDTH-001: Propagate causal chain
        if causal_chain_id is not None:
            trip_success_payload["causal_chain_id"] = causal_chain_id
            trip_success_payload["chain_position"] = 1
        events.append(Event(
            event_id=current_event_id,
            event_type="trip_success",
            timestamp=current_timestamp,
            payload=trip_success_payload,
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

        # WO-ENGINE-IMPROVED-TRIP-001: Free attack after successful trip (PHB p.96)
        # Improved Trip: "If you trip an opponent in melee combat, you immediately get
        # a melee attack against that opponent as if you hadn't used your attack for
        # the trip attempt." PHB p.96.
        attacker = world_state.entities.get(attacker_id)
        if attacker is not None and "improved_trip" in attacker.get(EF.FEATS, []):
            _weapon_dict = attacker.get(EF.WEAPON)
            if _weapon_dict is not None:
                from aidm.schemas.attack import Weapon, AttackIntent
                from aidm.core.attack_resolver import resolve_attack as _resolve_attack_free
                _weapon_fields = {k: v for k, v in _weapon_dict.items()
                                  if k in Weapon.__dataclass_fields__}
                _free_weapon = Weapon(**_weapon_fields)
                _free_attack_bonus = attacker.get(EF.ATTACK_BONUS, attacker.get(EF.BAB, 0))
                events.append(Event(
                    event_id=current_event_id,
                    event_type="improved_trip_free_attack",
                    timestamp=current_timestamp + 0.01,
                    payload={"attacker_id": attacker_id, "target_id": target_id},
                    citations=[{"source_id": "681f92bc94ff", "page": 96}],
                ))
                current_event_id += 1
                _free_intent = AttackIntent(
                    attacker_id=attacker_id,
                    target_id=target_id,
                    weapon=_free_weapon,
                    attack_bonus=_free_attack_bonus,
                )
                _free_events = _resolve_attack_free(
                    intent=_free_intent,
                    world_state=world_state,
                    rng=rng,
                    next_event_id=current_event_id,
                    timestamp=current_timestamp + 0.02,
                )
                events.extend(_free_events)
                current_event_id += len(_free_events)
            else:
                # PHB p.96: free attack fires for unarmed Improved Trippers too — no weapon restriction
                from aidm.schemas.attack import Weapon, AttackIntent
                from aidm.core.attack_resolver import resolve_attack as _resolve_attack_free
                _unarmed_dmg = attacker.get(EF.MONK_UNARMED_DICE, "1d3")
                _free_weapon = Weapon(
                    damage_dice=_unarmed_dmg,
                    damage_bonus=0,
                    damage_type="bludgeoning",
                    weapon_type="light",  # PHB p.140: unarmed attacks treated as light weapons
                )
                _free_attack_bonus = attacker.get(EF.ATTACK_BONUS, attacker.get(EF.BAB, 0))
                events.append(Event(
                    event_id=current_event_id,
                    event_type="improved_trip_free_attack",
                    timestamp=current_timestamp + 0.01,
                    payload={"attacker_id": attacker_id, "target_id": target_id},
                    citations=[{"source_id": "681f92bc94ff", "page": 96}],
                ))
                current_event_id += 1
                _free_intent = AttackIntent(
                    attacker_id=attacker_id,
                    target_id=target_id,
                    weapon=_free_weapon,
                    attack_bonus=_free_attack_bonus,
                )
                _free_events = _resolve_attack_free(
                    intent=_free_intent,
                    world_state=world_state,
                    rng=rng,
                    next_event_id=current_event_id,
                    timestamp=current_timestamp + 0.02,
                )
                events.extend(_free_events)
                current_event_id += len(_free_events)

        result = ManeuverResult(
            maneuver_type="trip",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            condition_applied="prone",
        )
    else:
        # Trip failed - defender may counter-trip
        trip_fail2_payload = {
            "attacker_id": attacker_id,
            "target_id": target_id,
            "reason": "opposed_check_lost",
            "counter_trip_allowed": True,
        }
        # WO-BRIEF-WIDTH-001: Propagate causal chain
        if causal_chain_id is not None:
            trip_fail2_payload["causal_chain_id"] = causal_chain_id
            trip_fail2_payload["chain_position"] = 1
        events.append(Event(
            event_id=current_event_id,
            event_type="trip_failure",
            timestamp=current_timestamp,
            payload=trip_fail2_payload,
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
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    causal_chain_id: Optional[str] = None,
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
    overrun_declared_payload = {
        "attacker_id": attacker_id,
        "target_id": target_id,
        "is_charge": intent.is_charge,
        "defender_avoids": intent.defender_avoids,
    }
    if causal_chain_id is not None:
        overrun_declared_payload["causal_chain_id"] = causal_chain_id
        overrun_declared_payload["chain_position"] = 1
    events.append(Event(
        event_id=current_event_id,
        event_type="overrun_declared",
        timestamp=current_timestamp,
        payload=overrun_declared_payload,
        citations=[{"source_id": "681f92bc94ff", "page": 157}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # WO-ENGINE-IMPROVED-OVERRUN-001: Improved Overrun forces opposed check — defender cannot avoid
    # PHB p.157: "If you have the Improved Overrun feat, the defender may not choose to avoid."
    _attacker_has_improved_overrun = "improved_overrun" in world_state.entities.get(
        attacker_id, {}
    ).get(EF.FEATS, [])

    # Check if defender avoids (controlled by AI/doctrine)
    if intent.defender_avoids and not _attacker_has_improved_overrun:
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
    improved_overrun_bonus = 4 if _attacker_has_improved_overrun else 0  # PHB p.157: +4 bonus on opposed STR check
    attacker_modifier = attacker_str + attacker_size + charge_bonus + improved_overrun_bonus

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
                **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
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
        # WO-FIX-08: Opposed STR check to determine if attacker falls prone (PHB p.157)
        # Both sides roll new d20s; uses SPECIAL size modifier; defender wins ties
        combat_rng = rng.stream("combat")
        prone_attacker_roll = combat_rng.randint(1, 20)
        prone_defender_roll = combat_rng.randint(1, 20)
        prone_attacker_str = _get_str_modifier(world_state, attacker_id)
        prone_defender_str = _get_str_modifier(world_state, target_id)
        # WO-ENGINE-MANEUVER-FIDELITY-002: PHB p.157 — "Strength or Dexterity
        # check (defender's choice)" → use max(STR_MOD, DEX_MOD) for defender
        prone_defender_dex = _get_dex_modifier(world_state, target_id)
        prone_defender_mod = max(prone_defender_str, prone_defender_dex)
        prone_attacker_special_size = _get_size_modifier(world_state, attacker_id)
        prone_defender_special_size = _get_size_modifier(world_state, target_id)
        prone_attacker_total = prone_attacker_roll + prone_attacker_str + prone_attacker_special_size
        prone_defender_total = prone_defender_roll + prone_defender_mod + prone_defender_special_size
        # Defender wins ties
        attacker_prone = prone_defender_total >= prone_attacker_total

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
                "prone_check": {
                    "attacker_roll": prone_attacker_roll,
                    "attacker_str_mod": prone_attacker_str,
                    "attacker_special_size_mod": prone_attacker_special_size,
                    "attacker_total": prone_attacker_total,
                    "defender_roll": prone_defender_roll,
                    "defender_str_mod": prone_defender_str,
                    "defender_special_size_mod": prone_defender_special_size,
                    "defender_total": prone_defender_total,
                },
                "hazard_triggered": falling_result is not None,
                "falling_damage": falling_result.total_damage if falling_result else 0,
                **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
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
# SUNDER RESOLUTION (FULL — WO-ENGINE-SUNDER-DISARM-FULL-001)
# ==============================================================================

# Hardness and HP tables PHB p.165
_ITEM_HARDNESS: Dict[str, int] = {
    "light": 5,
    "one-handed": 5,
    "two-handed": 5,
    "shield_light": 5,
    "shield_heavy": 7,
}
_ITEM_HP_MAX: Dict[str, int] = {
    "light": 2,
    "one-handed": 5,
    "two-handed": 10,
    "shield_light": 7,
    "shield_heavy": 15,
}


def _get_weapon_hp_info(world_state: WorldState, entity_id: str) -> Tuple[int, int, int]:
    """Return (current_hp, max_hp, hardness) for entity's wielded weapon."""
    entity = world_state.entities.get(entity_id, {})
    weapon_data = entity.get(EF.WEAPON)
    weapon_type = "one-handed"
    if weapon_data and isinstance(weapon_data, dict):
        weapon_type = weapon_data.get("weapon_type", "one-handed")

    hardness = _ITEM_HARDNESS.get(weapon_type, 5)
    hp_max = _ITEM_HP_MAX.get(weapon_type, 5)

    # Read current HP (default to max if not yet set)
    hp_current = entity.get(EF.WEAPON_HP, hp_max)
    return hp_current, hp_max, hardness


def resolve_sunder(
    intent: SunderIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    causal_chain_id: Optional[str] = None,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a Sunder maneuver (FULL — WO-ENGINE-SUNDER-DISARM-FULL-001).

    PHB p.158-159: Opposed attack rolls. Attacker wins → item takes damage
    minus hardness. At 0 HP: broken (-2 attack). At ≤ -max HP: destroyed.

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
    sunder_declared_payload = {
        "attacker_id": attacker_id,
        "target_id": target_id,
        "target_item": intent.target_item,
    }
    if causal_chain_id is not None:
        sunder_declared_payload["causal_chain_id"] = causal_chain_id
        sunder_declared_payload["chain_position"] = 1
    events.append(Event(
        event_id=current_event_id,
        event_type="sunder_declared",
        timestamp=current_timestamp,
        payload=sunder_declared_payload,
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Calculate attack roll modifiers
    attacker_bab = _get_bab(world_state, attacker_id)
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_size = _get_standard_attack_size_modifier(world_state, attacker_id)
    attacker_modifier = attacker_bab + attacker_str + attacker_size
    # WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001: Improved Sunder grants +4 (PHB p.96)
    if "improved_sunder" in world_state.entities.get(attacker_id, {}).get(EF.FEATS, []):
        attacker_modifier += 4

    defender_bab = _get_bab(world_state, target_id)
    defender_str = _get_str_modifier(world_state, target_id)
    defender_size = _get_standard_attack_size_modifier(world_state, target_id)
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
        # Roll damage
        attacker_entity = world_state.entities.get(attacker_id, {})
        weapon_data = attacker_entity.get(EF.WEAPON)
        if weapon_data and isinstance(weapon_data, dict):
            damage_dice_expr = weapon_data.get("damage_dice", "1d8")
        else:
            damage_dice_expr = "1d8"
        num_dice, die_size = parse_damage_dice(damage_dice_expr)
        damage_rolls = roll_dice(num_dice, die_size, rng)
        damage_roll = sum(damage_rolls)
        weapon_grip = _get_weapon_grip(world_state, attacker_id)
        if weapon_grip == "two-handed":
            damage_bonus = int(attacker_str * 1.5)
        elif weapon_grip == "off-hand":
            damage_bonus = int(attacker_str * 0.5)
        else:
            damage_bonus = attacker_str
        total_damage = max(0, damage_roll + damage_bonus)

        # Apply hardness and update weapon HP
        wp_current, wp_max, hardness = _get_weapon_hp_info(world_state, target_id)
        damage_after_hardness = max(0, total_damage - hardness)
        new_wp_hp = wp_current - damage_after_hardness

        # Determine broken/destroyed state
        is_broken = new_wp_hp <= 0 and new_wp_hp > -wp_max
        is_destroyed = new_wp_hp <= -wp_max

        # Write persistent weapon state to target entity
        entities = deepcopy(world_state.entities)
        if target_id in entities:
            entities[target_id][EF.WEAPON_HP] = new_wp_hp
            entities[target_id][EF.WEAPON_HP_MAX] = wp_max
            entities[target_id][EF.WEAPON_BROKEN] = is_broken or is_destroyed
            entities[target_id][EF.WEAPON_DESTROYED] = is_destroyed

        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=world_state.active_combat,
        )

        # Determine event type
        if is_destroyed:
            item_event_type = "weapon_destroyed"
        elif is_broken:
            item_event_type = "weapon_broken"
        else:
            item_event_type = "weapon_damaged"

        events.append(Event(
            event_id=current_event_id,
            event_type="sunder_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "target_item": intent.target_item,
                "damage_dice": damage_dice_expr,
                "damage_rolls": damage_rolls,
                "damage_roll": damage_roll,
                "damage_bonus": damage_bonus,
                "total_damage": total_damage,
                "hardness": hardness,
                "damage_after_hardness": damage_after_hardness,
                "weapon_hp_old": wp_current,
                "weapon_hp_new": new_wp_hp,
                "weapon_broken": is_broken,
                "weapon_destroyed": is_destroyed,
                **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
            },
            citations=[{"source_id": "681f92bc94ff", "page": 158}],
        ))
        current_event_id += 1

        if item_event_type != "weapon_damaged":
            events.append(Event(
                event_id=current_event_id,
                event_type=item_event_type,
                timestamp=current_timestamp + 0.01,
                payload={
                    "entity_id": target_id,
                    "weapon_hp": new_wp_hp,
                    "weapon_broken": entities.get(target_id, {}).get(EF.WEAPON_BROKEN, False),
                    "weapon_destroyed": is_destroyed,
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
                **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
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
# DISARM RESOLUTION (FULL — WO-ENGINE-SUNDER-DISARM-FULL-001)
# ==============================================================================

def resolve_disarm(
    intent: DisarmIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    aoo_dealt_damage: bool = False,
    causal_chain_id: Optional[str] = None,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a Disarm maneuver (FULL — WO-ENGINE-SUNDER-DISARM-FULL-001).

    PHB p.155: Opposed attack rolls.
    - Attacker wins: target gets DISARMED = True (weapon on ground).
    - Attacker loses by 10+: attacker gets DISARMED = True (counter-disarm).
    - If AoO deals damage, disarm automatically fails.

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
    disarm_declared_payload = {
        "attacker_id": attacker_id,
        "target_id": target_id,
    }
    if causal_chain_id is not None:
        disarm_declared_payload["causal_chain_id"] = causal_chain_id
        disarm_declared_payload["chain_position"] = 1
    events.append(Event(
        event_id=current_event_id,
        event_type="disarm_declared",
        timestamp=current_timestamp,
        payload=disarm_declared_payload,
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
                **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
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

    # Disarm weapon type modifiers (PHB p.155) — B-AMB-04
    attacker_weapon_type = _get_weapon_type(world_state, attacker_id)
    if attacker_weapon_type == "two-handed":
        attacker_modifier += 4
    elif attacker_weapon_type == "light":
        attacker_modifier -= 4
    defender_weapon_type = _get_weapon_type(world_state, target_id)
    if defender_weapon_type == "two-handed":
        defender_modifier += 4
    elif defender_weapon_type == "light":
        defender_modifier -= 4
    # WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001: Improved Disarm grants +4 (PHB p.96)
    if "improved_disarm" in world_state.entities.get(attacker_id, {}).get(EF.FEATS, []):
        attacker_modifier += 4

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
        # Disarm success — set DISARMED on target
        entities = deepcopy(world_state.entities)
        if target_id in entities:
            entities[target_id][EF.DISARMED] = True
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=world_state.active_combat,
        )

        events.append(Event(
            event_id=current_event_id,
            event_type="disarm_success",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "weapon_dropped": True,
                **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1
        events.append(Event(
            event_id=current_event_id,
            event_type="weapon_disarmed",
            timestamp=current_timestamp + 0.01,
            payload={"entity_id": target_id, "disarmed_by": attacker_id},
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="disarm",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
    else:
        # Disarm failed — check for counter-disarm (PHB p.155: any failure)
        # WO-ENGINE-IDC-001: margin uses totals, not raw rolls (PHB p.155)
        margin = check_result.defender_total - check_result.attacker_total
        # WO-ENGINE-DISARM-FIDELITY-001: any failure allows counter (was margin >= 10)
        counter_disarm_allowed = True
        events.append(Event(
            event_id=current_event_id,
            event_type="disarm_failure",
            timestamp=current_timestamp,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "reason": "opposed_check_lost",
                "margin": margin,
                "counter_disarm_allowed": counter_disarm_allowed,
                **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # WO-ENGINE-DISARM-FIDELITY-001: Defender may attempt counter-disarm on any failure (PHB p.155)
        _att_entity = world_state.entities.get(attacker_id, {})
        _att_feats = _att_entity.get(EF.FEATS, [])
        if "improved_disarm" in _att_feats:
            # WO-ENGINE-IDC-001: Improved Disarm suppresses the counter-disarm attempt
            events.append(Event(
                event_id=current_event_id,
                event_type="counter_disarm_suppressed",
                timestamp=current_timestamp,
                payload={
                    "actor_id": attacker_id,
                    "feat": "improved_disarm",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 96}],
            ))
            current_event_id += 1
            result = ManeuverResult(
                maneuver_type="disarm",
                success=False,
                events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            )
        else:
            # Defender rolls counter-disarm: defender_modifier vs attacker_modifier
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
                entities = deepcopy(world_state.entities)
                if attacker_id in entities:
                    entities[attacker_id][EF.DISARMED] = True
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=entities,
                    active_combat=world_state.active_combat,
                )
                events.append(Event(
                    event_id=current_event_id,
                    event_type="counter_disarm_success",
                    timestamp=current_timestamp,
                    payload={
                        "counter_attacker": target_id,
                        "target_id": attacker_id,
                        "weapon_dropped": True,
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
    intent,
    world_state,
    rng,
    next_event_id,
    timestamp,
    aoo_events=None,
    aoo_defeated=False,
    aoo_dealt_damage=False,
    causal_chain_id=None,
):
    """Resolve a Grapple maneuver (FULL - CP-22).

    PHB p.155-157: Touch attack then opposed grapple check.
    Touch miss => grapple_touch_miss. Check loss => grapple_check_fail.
    Success: grapple_established + grapple_success + bidirectional conditions.
    Updates active_combat[grapple_pairs] on success.
    """
    events = []
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

    grapple_declared_payload = {"attacker_id": attacker_id, "target_id": target_id}
    if causal_chain_id is not None:
        grapple_declared_payload["causal_chain_id"] = causal_chain_id
        grapple_declared_payload["chain_position"] = 1
    events.append(Event(
        event_id=current_event_id,
        event_type="grapple_declared",
        timestamp=current_timestamp,
        payload=grapple_declared_payload,
        citations=[{"source_id": "681f92bc94ff", "page": 155}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    if aoo_dealt_damage:
        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_failure",
            timestamp=current_timestamp,
            payload={"attacker_id": attacker_id, "target_id": target_id, "reason": "aoo_dealt_damage"},
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1
        result = ManeuverResult(
            maneuver_type="grapple",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
        return events, world_state, result

    attacker_bab = _get_bab(world_state, attacker_id)
    attacker_str = _get_str_modifier(world_state, attacker_id)
    attacker_std_size = _get_standard_attack_size_modifier(world_state, attacker_id)
    touch_attack_bonus = attacker_bab + attacker_str + attacker_std_size

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

    if not touch_result.hit:
        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_touch_miss",
            timestamp=current_timestamp,
            payload={"attacker_id": attacker_id, "target_id": target_id, "reason": "touch_attack_missed"},
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        current_event_id += 1
        result = ManeuverResult(
            maneuver_type="grapple",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
        return events, world_state, result

    attacker_size = _get_size_modifier(world_state, attacker_id)
    attacker_grapple_modifier = attacker_bab + attacker_str + attacker_size
    # WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001: Improved Grapple grants +4 (PHB p.96)
    if "improved_grapple" in world_state.entities.get(attacker_id, {}).get(EF.FEATS, []):
        attacker_grapple_modifier += 4

    defender_bab = _get_bab(world_state, target_id)
    defender_str = _get_str_modifier(world_state, target_id)
    defender_size = _get_size_modifier(world_state, target_id)
    defender_grapple_modifier = defender_bab + defender_str + defender_size

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

    # WO-ENGINE-GRAPPLE-PIN-001: Detect pin attempt (already grappling this target)
    already_grappling = False
    if world_state.active_combat is not None:
        grapple_pairs = world_state.active_combat.get("grapple_pairs", [])
        already_grappling = any(
            p[0] == attacker_id and p[1] == target_id
            for p in grapple_pairs
        )
    target_already_pinned = ConditionType.PINNED.value in (
        world_state.entities.get(target_id, {}).get(EF.CONDITIONS, {})
    )
    is_pin_attempt = already_grappling and not target_already_pinned

    if is_pin_attempt:
        # Pin escalation path (PHB p.156)
        if check_result.attacker_wins:
            # Remove grappled, apply pinned
            world_state = remove_condition(world_state, target_id, ConditionType.GRAPPLED.value)
            pinned_cond = create_pinned_condition(source="grapple_pin", applied_at_event_id=current_event_id)
            world_state = apply_condition(world_state, target_id, pinned_cond)

            events.append(Event(
                event_id=current_event_id,
                event_type="pin_established",
                timestamp=current_timestamp,
                payload={
                    "attacker_id": attacker_id,
                    "target_id": target_id,
                    "attacker_roll": check_result.attacker_roll,
                    "defender_roll": check_result.defender_roll,
                    "attacker_total": check_result.attacker_total,
                    "defender_total": check_result.defender_total,
                    "condition_applied": ConditionType.PINNED.value,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 156}],
            ))
            current_event_id += 1

            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=current_timestamp,
                payload={"target_id": target_id, "condition_type": ConditionType.PINNED.value, "source": "grapple_pin"},
                citations=[{"source_id": "681f92bc94ff", "page": 156}],
            ))
            current_event_id += 1

            result = ManeuverResult(
                maneuver_type="grapple",
                success=True,
                events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
                condition_applied=ConditionType.PINNED.value,
            )
        else:
            # Pin attempt failed — target stays grappled
            events.append(Event(
                event_id=current_event_id,
                event_type="pin_attempt_failed",
                timestamp=current_timestamp,
                payload={
                    "attacker_id": attacker_id,
                    "target_id": target_id,
                    "attacker_roll": check_result.attacker_roll,
                    "defender_roll": check_result.defender_roll,
                    "attacker_total": check_result.attacker_total,
                    "defender_total": check_result.defender_total,
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

    # Normal grapple path (not already grappling target)
    if check_result.attacker_wins:
        grappled_cond = create_grappled_condition(source="grapple_attack", applied_at_event_id=current_event_id)
        world_state = apply_condition(world_state, target_id, grappled_cond)

        grappling_cond = create_grappling_condition(source="grapple_attack", applied_at_event_id=current_event_id)
        world_state = apply_condition(world_state, attacker_id, grappling_cond)

        if world_state.active_combat is not None:
            active_combat = deepcopy(world_state.active_combat)
            grapple_pairs = list(active_combat.get("grapple_pairs", []))
            grapple_pairs.append([attacker_id, target_id])
            active_combat["grapple_pairs"] = grapple_pairs
            world_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=world_state.entities,
                active_combat=active_combat,
            )

        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_established",
            timestamp=current_timestamp,
            payload={"attacker_id": attacker_id, "target_id": target_id, "conditions_applied": ["grappled", "grappling"]},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_success",
            timestamp=current_timestamp,
            payload={"attacker_id": attacker_id, "target_id": target_id, "condition_applied": "grappled"},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="condition_applied",
            timestamp=current_timestamp,
            payload={"target_id": target_id, "condition_type": "grappled", "source": "grapple_attack"},
            citations=[{"source_id": "681f92bc94ff", "page": 311}],
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="condition_applied",
            timestamp=current_timestamp,
            payload={"target_id": attacker_id, "condition_type": "grappling", "source": "grapple_attack"},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        result = ManeuverResult(
            maneuver_type="grapple",
            success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
            condition_applied="grappled",
        )
    else:
        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_check_fail",
            timestamp=current_timestamp,
            payload={"attacker_id": attacker_id, "target_id": target_id, "reason": "opposed_check_lost"},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1
        result = ManeuverResult(
            maneuver_type="grapple",
            success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )

    return events, world_state, result


def resolve_grapple_escape(
    initiator_id,
    target_id,
    world_state,
    rng,
    next_event_id,
    timestamp,
):
    """Resolve a grapple escape attempt. CP-22.

    initiator_id: escaping entity (was grappled).
    target_id: holding entity (was grappling).
    Escaper wins on tied opposed check (as attacker in _roll_opposed_check).
    """
    events = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    escaper_bab = _get_bab(world_state, initiator_id)
    escaper_str = _get_str_modifier(world_state, initiator_id)
    escaper_size = _get_size_modifier(world_state, initiator_id)
    escaper_modifier = escaper_bab + escaper_str + escaper_size

    holder_bab = _get_bab(world_state, target_id)
    holder_str = _get_str_modifier(world_state, target_id)
    holder_size = _get_size_modifier(world_state, target_id)
    holder_modifier = holder_bab + holder_str + holder_size

    check_result = _roll_opposed_check(rng, escaper_modifier, holder_modifier, "grapple_escape")

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
        world_state = remove_condition(world_state, initiator_id, "grappled")
        world_state = remove_condition(world_state, target_id, "grappling")

        if world_state.active_combat is not None:
            active_combat = deepcopy(world_state.active_combat)
            pairs = list(active_combat.get("grapple_pairs", []))
            pairs = [
                p for p in pairs
                if not (
                    (p[0] == target_id and p[1] == initiator_id) or
                    (p[0] == initiator_id and p[1] == target_id)
                )
            ]
            active_combat["grapple_pairs"] = pairs
            world_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=world_state.entities,
                active_combat=active_combat,
            )

        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_broken",
            timestamp=current_timestamp,
            payload={"escaper_id": initiator_id, "holder_id": target_id},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="condition_removed",
            timestamp=current_timestamp,
            payload={"target_id": initiator_id, "condition_type": "grappled", "reason": "grapple_escape"},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="condition_removed",
            timestamp=current_timestamp,
            payload={"target_id": target_id, "condition_type": "grappling", "reason": "grapple_escape"},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

    else:
        events.append(Event(
            event_id=current_event_id,
            event_type="grapple_escape_failed",
            timestamp=current_timestamp,
            payload={"escaper_id": initiator_id, "holder_id": target_id},
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

    return events, world_state


def resolve_pin_escape(
    intent,
    world_state,
    rng,
    next_event_id,
    timestamp,
):
    """Resolve a pin escape attempt. WO-ENGINE-GRAPPLE-PIN-001.

    PHB p.156: Opposed grapple check (full-round action).
    On success: pinned condition removed, entity reverts to grappled.
    On failure: still pinned.

    RNG Consumption Order:
    1. Escaper's grapple check (d20) — "combat" stream
    2. Pinner's grapple check (d20) — "combat" stream
    """
    events = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    initiator_id = intent.attacker_id
    pinner_id = intent.target_id

    # Verify initiator is actually pinned
    initiator_conditions = world_state.entities.get(initiator_id, {}).get(EF.CONDITIONS, {})
    if ConditionType.PINNED.value not in initiator_conditions:
        events.append(Event(
            event_id=current_event_id,
            event_type="pin_escape_invalid",
            timestamp=current_timestamp,
            payload={
                "initiator_id": initiator_id,
                "reason": "not_pinned",
            }
        ))
        return events, world_state, ManeuverResult(
            maneuver_type="pin_escape", success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )

    # Opposed grapple check
    initiator_bab = _get_bab(world_state, initiator_id)
    initiator_str = _get_str_modifier(world_state, initiator_id)
    initiator_size = _get_size_modifier(world_state, initiator_id)
    initiator_mod = initiator_bab + initiator_str + initiator_size

    pinner_bab = _get_bab(world_state, pinner_id)
    pinner_str = _get_str_modifier(world_state, pinner_id)
    pinner_size = _get_size_modifier(world_state, pinner_id)
    pinner_mod = pinner_bab + pinner_str + pinner_size

    check = _roll_opposed_check(rng, initiator_mod, pinner_mod, "grapple_escape_pin")

    events.append(Event(
        event_id=current_event_id,
        event_type="opposed_check",
        timestamp=current_timestamp,
        payload=check.to_dict(),
        citations=[{"source_id": "681f92bc94ff", "page": 156}],
    ))
    current_event_id += 1
    current_timestamp += 0.01

    if check.attacker_wins:
        # Escape: remove pinned, reapply grappled (still in grapple_pairs)
        world_state = remove_condition(world_state, initiator_id, ConditionType.PINNED.value)
        grappled_cond = create_grappled_condition(
            source="grapple_reestablish", applied_at_event_id=current_event_id
        )
        world_state = apply_condition(world_state, initiator_id, grappled_cond)

        events.append(Event(
            event_id=current_event_id,
            event_type="pin_escape_success",
            timestamp=current_timestamp,
            payload={
                "initiator_id": initiator_id,
                "pinner_id": pinner_id,
                "initiator_roll": check.attacker_roll,
                "pinner_roll": check.defender_roll,
                "initiator_total": check.attacker_total,
                "pinner_total": check.defender_total,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        return events, world_state, ManeuverResult(
            maneuver_type="pin_escape", success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
    else:
        events.append(Event(
            event_id=current_event_id,
            event_type="pin_escape_failed",
            timestamp=current_timestamp,
            payload={
                "initiator_id": initiator_id,
                "pinner_id": pinner_id,
                "initiator_roll": check.attacker_roll,
                "pinner_roll": check.defender_roll,
                "initiator_total": check.attacker_total,
                "pinner_total": check.defender_total,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        current_event_id += 1

        return events, world_state, ManeuverResult(
            maneuver_type="pin_escape", success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )


# ==============================================================================
# UNIFIED MANEUVER RESOLUTION DISPATCHER
# ==============================================================================

ManeuverIntent = Union[
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent, GrappleEscapeIntent, PinEscapeIntent
]


def resolve_maneuver(
    intent: ManeuverIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
    aoo_events: Optional[List[Event]] = None,
    aoo_defeated: bool = False,
    aoo_dealt_damage: bool = False,
    causal_chain_id: Optional[str] = None,
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
        causal_chain_id: WO-BRIEF-WIDTH-001: Optional chain ID for causal linking

    Returns:
        Tuple of (events, updated_world_state, ManeuverResult)
    """
    if isinstance(intent, BullRushIntent):
        return resolve_bull_rush(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, causal_chain_id)
    elif isinstance(intent, TripIntent):
        return resolve_trip(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, causal_chain_id)
    elif isinstance(intent, OverrunIntent):
        return resolve_overrun(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, causal_chain_id)
    elif isinstance(intent, SunderIntent):
        return resolve_sunder(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, causal_chain_id)
    elif isinstance(intent, DisarmIntent):
        return resolve_disarm(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, aoo_dealt_damage, causal_chain_id)
    elif isinstance(intent, GrappleIntent):
        return resolve_grapple(intent, world_state, rng, next_event_id, timestamp, aoo_events, aoo_defeated, aoo_dealt_damage, causal_chain_id)
    else:
        raise ValueError(f"Unknown maneuver intent type: {type(intent)}")
