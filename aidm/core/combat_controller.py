"""Combat controller for initiative-driven combat rounds (CP-14).

Wrapper layer that orchestrates combat rounds by:
- Rolling initiative at combat start
- Managing round progression
- Calling execute_turn() for each actor in initiative order
- Tracking flat-footed state
- WO-015: Duration tick at round end for spell effects

Preserves CP-09/CP-12 execute_turn() API.
"""

from copy import deepcopy
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.play_loop import execute_turn, TurnContext, TurnResult
from aidm.core.initiative import roll_initiative_for_all_actors, InitiativeRoll
from aidm.core.rng_manager import RNGManager
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.entity_fields import EF
# WO-015: Duration tracker for spell effects
from aidm.core.duration_tracker import DurationTracker


# ==============================================================================
# WO-015: DURATION TRACKER HELPERS
# ==============================================================================

def _tick_duration_tracker(
    world_state: WorldState,
    current_round: int,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Tick the duration tracker at round end and expire effects.

    Args:
        world_state: Current world state
        current_round: Current round number
        next_event_id: Next event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (events, updated_world_state)
    """
    events = []
    current_event_id = next_event_id

    if world_state.active_combat is None:
        return events, world_state

    # Get duration tracker
    tracker_data = world_state.active_combat.get("duration_tracker")
    if tracker_data is None:
        return events, world_state

    duration_tracker = DurationTracker.from_dict(tracker_data)

    # Tick the tracker and get expired effects
    expired_effects = duration_tracker.tick_round()

    if not expired_effects:
        # Update tracker in active_combat even if no effects expired
        active_combat = deepcopy(world_state.active_combat)
        active_combat["duration_tracker"] = duration_tracker.to_dict()
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=deepcopy(world_state.entities),
            active_combat=active_combat,
        )
        return events, world_state

    # Process expired effects
    entities = deepcopy(world_state.entities)

    for effect in expired_effects:
        # Emit effect_expired event
        events.append(Event(
            event_id=current_event_id,
            event_type="spell_effect_expired",
            timestamp=timestamp,
            payload={
                "spell_id": effect.spell_id,
                "spell_name": effect.spell_name,
                "caster_id": effect.caster_id,
                "target_id": effect.target_id,
                "round": current_round,
            },
        ))
        current_event_id += 1

        # Remove condition from target if applicable
        if effect.condition_applied:
            target_entity = entities.get(effect.target_id, {})
            conditions = target_entity.get(EF.CONDITIONS, [])
            if effect.condition_applied in conditions:
                conditions.remove(effect.condition_applied)
                target_entity[EF.CONDITIONS] = conditions

                events.append(Event(
                    event_id=current_event_id,
                    event_type="condition_removed",
                    timestamp=timestamp + 0.01,
                    payload={
                        "entity_id": effect.target_id,
                        "condition": effect.condition_applied,
                        "reason": "duration_expired",
                        "spell_name": effect.spell_name,
                    },
                ))
                current_event_id += 1

    # Update active_combat with modified tracker
    active_combat = deepcopy(world_state.active_combat)
    active_combat["duration_tracker"] = duration_tracker.to_dict()

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=active_combat,
    )

    return events, updated_state


@dataclass
class CombatRoundResult:
    """Result of executing a full combat round."""

    round_index: int
    """1-indexed round number"""

    world_state: WorldState
    """Updated world state after round"""

    events: List[Event]
    """All events emitted during the round"""

    turn_results: List[TurnResult]
    """Individual turn results for each actor"""


def start_combat(
    world_state: WorldState,
    actors: List[Tuple[str, int]],  # (actor_id, dex_modifier)
    rng: RNGManager,
    next_event_id: int = 0,
    timestamp: float = 0.0,
    misc_modifiers: Dict[str, int] = None
) -> Tuple[WorldState, List[Event], int]:
    """
    Start combat by rolling initiative and emitting combat_started event.

    Args:
        world_state: Current world state
        actors: List of (actor_id, dex_modifier) tuples
        rng: RNG manager
        next_event_id: Next event ID
        timestamp: Event timestamp
        misc_modifiers: Optional misc modifiers for initiative

    Returns:
        Tuple of (updated_world_state, events, next_event_id)
    """
    events = []
    current_event_id = next_event_id

    # Roll initiative for all actors
    initiative_rolls, initiative_order = roll_initiative_for_all_actors(
        actors, rng, misc_modifiers
    )

    # Emit combat_started event
    events.append(Event(
        event_id=current_event_id,
        event_type="combat_started",
        timestamp=timestamp,
        payload={
            "num_actors": len(actors),
            "initiative_order": initiative_order
        }
    ))
    current_event_id += 1

    # Emit initiative_rolled events for each actor
    for roll in initiative_rolls:
        events.append(Event(
            event_id=current_event_id,
            event_type="initiative_rolled",
            timestamp=timestamp + 0.01,
            payload=roll.to_dict(),
            citations=[{"source_id": "681f92bc94ff", "page": 135}]  # PHB initiative
        ))
        current_event_id += 1

    # Initialize active_combat in WorldState
    active_combat = {
        "turn_counter": 0,
        "round_index": 0,  # Will increment to 1 when first round starts
        "initiative_order": initiative_order,
        "flat_footed_actors": list(initiative_order),  # All actors start flat-footed
        "aoo_used_this_round": []  # CP-15: Track AoO usage (reset each round)
    }

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=deepcopy(world_state.entities),
        active_combat=active_combat
    )

    return updated_state, events, current_event_id


def execute_combat_round(
    world_state: WorldState,
    doctrines: Dict[str, MonsterDoctrine],
    rng: RNGManager,
    next_event_id: int = 0,
    timestamp: float = 0.0,
    narration_service: Optional[Any] = None,  # WO-030: GuardedNarrationService
) -> CombatRoundResult:
    """
    Execute a single combat round in initiative order.

    Calls execute_turn() for each actor in initiative_order.
    Manages flat-footed state clearing.

    Args:
        world_state: Current world state (must have active_combat initialized)
        doctrines: Dict of monster_id -> MonsterDoctrine
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Starting timestamp
        narration_service: Optional GuardedNarrationService for narration generation (WO-030)

    Returns:
        CombatRoundResult with updated state and all events
    """
    if world_state.active_combat is None:
        raise ValueError("WorldState.active_combat must be initialized before executing combat round")

    if "initiative_order" not in world_state.active_combat:
        raise ValueError("initiative_order not found in active_combat")

    # Increment round index
    current_round = world_state.active_combat.get("round_index", 0) + 1

    events = []
    turn_results = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    # Emit combat_round_started event
    events.append(Event(
        event_id=current_event_id,
        event_type="combat_round_started",
        timestamp=current_timestamp,
        payload={
            "round_index": current_round
        }
    ))
    current_event_id += 1

    # Get initiative order and reset AoO usage for new round
    initiative_order = world_state.active_combat["initiative_order"]
    flat_footed_actors = set(world_state.active_combat.get("flat_footed_actors", []))
    # CP-15: Reset AoO usage at combat_round_started
    aoo_used_this_round = []

    # Execute turn for each actor in initiative order
    for actor_id in initiative_order:
        # Get actor team
        entity = world_state.entities.get(actor_id)
        if entity is None:
            # Actor no longer exists (defeated and removed), skip
            continue

        actor_team = entity.get(EF.TEAM, "unknown")

        # Create turn context (action_type defaults to None for CP-09/CP-12 compat)
        turn_ctx = TurnContext(
            turn_index=world_state.active_combat.get("turn_counter", 0),
            actor_id=actor_id,
            actor_team=actor_team,
            action_type=None  # CP-14: No action economy validation yet
        )

        # Get doctrine if monster
        doctrine = doctrines.get(actor_id) if actor_team == "monsters" else None

        # Execute turn
        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            doctrine=doctrine,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=current_timestamp,
            narration_service=narration_service,  # WO-030: Pass through narration service
        )

        # Check if flat-footed should be cleared
        # Clear if actor took a successful action (status == "ok" and events besides turn_start/turn_end)
        if actor_id in flat_footed_actors and turn_result.status == "ok":
            # Check if any action events were emitted (not just turn bookends)
            action_events = [
                e for e in turn_result.events
                if e.event_type not in {"turn_start", "turn_end", "turn_started", "turn_ended"}
            ]

            if action_events:
                # Emit flat_footed_cleared event
                flat_footed_cleared_event = Event(
                    event_id=current_event_id + len(turn_result.events),
                    event_type="flat_footed_cleared",
                    timestamp=current_timestamp + 0.2,
                    payload={"actor_id": actor_id},
                    citations=[{"source_id": "681f92bc94ff", "page": 137}]  # PHB flat-footed
                )

                # Add to turn result events (before final event)
                turn_result.events.append(flat_footed_cleared_event)

                # Remove from flat-footed set
                flat_footed_actors.discard(actor_id)

        # Collect events and update counters
        events.extend(turn_result.events)
        turn_results.append(turn_result)
        current_event_id += len(turn_result.events)
        current_timestamp += 1.0

        # Update world state for next turn
        world_state = turn_result.world_state

    # Update active_combat with new round index, flat-footed set, and AoO usage
    active_combat = deepcopy(world_state.active_combat)
    active_combat["round_index"] = current_round
    active_combat["flat_footed_actors"] = list(flat_footed_actors)  # Convert set to list for serialization
    active_combat["aoo_used_this_round"] = aoo_used_this_round  # CP-15: Reset for next round

    # Apply the updated active_combat to world_state BEFORE ticking duration
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=deepcopy(world_state.entities),
        active_combat=active_combat,
    )

    # WO-015: Tick duration tracker and expire effects at round end
    duration_events, world_state = _tick_duration_tracker(
        world_state=world_state,
        current_round=current_round,
        next_event_id=current_event_id,
        timestamp=current_timestamp,
    )
    events.extend(duration_events)
    current_event_id += len(duration_events)

    return CombatRoundResult(
        round_index=current_round,
        world_state=world_state,
        events=events,
        turn_results=turn_results
    )
