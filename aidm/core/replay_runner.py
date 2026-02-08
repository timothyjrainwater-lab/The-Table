"""Deterministic replay runner for event-sourced simulations."""

from typing import Dict, Any, List
from dataclasses import dataclass
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.rng_manager import RNGManager


@dataclass
class ReplayReport:
    """Report of replay execution with verification results."""

    final_state: WorldState
    final_hash: str
    events_processed: int
    determinism_verified: bool
    divergence_info: str = ""


def reduce_event(state: WorldState, event: Event, rng_manager: RNGManager) -> WorldState:
    """
    Single reducer function that applies an event to state.

    This is the ONLY function that mutates state based on events.
    All game logic mutations must go through here.
    """
    # Deep copy to avoid mutation
    new_state = deepcopy(state)

    event_type = event.event_type

    if event_type == "no-op":
        # No-op event does nothing
        pass

    elif event_type == "set_entity_field":
        # Example mutation: set a field on an entity
        entity_id = event.payload.get("entity_id")
        field = event.payload.get("field")
        value = event.payload.get("value")

        if entity_id and field:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}
            new_state.entities[entity_id][field] = value

    elif event_type == "add_entity":
        # Add a new entity
        entity_id = event.payload.get("entity_id")
        entity_data = event.payload.get("data", {})

        if entity_id:
            new_state.entities[entity_id] = entity_data

    elif event_type == "remove_entity":
        # Remove an entity
        entity_id = event.payload.get("entity_id")

        if entity_id and entity_id in new_state.entities:
            del new_state.entities[entity_id]

    else:
        # Unknown event types are ignored (fail-safe)
        pass

    return new_state


def run(
    initial_state: WorldState,
    master_seed: int,
    event_log: EventLog,
    expected_final_hash: str = None,
) -> ReplayReport:
    """
    Run deterministic replay of event log.

    Args:
        initial_state: Starting world state
        master_seed: Master RNG seed for deterministic randomness
        event_log: Sequence of events to apply
        expected_final_hash: Optional expected hash for verification

    Returns:
        ReplayReport with final state and verification results
    """
    rng_manager = RNGManager(master_seed)
    current_state = deepcopy(initial_state)

    events_processed = 0

    for event in event_log.events:
        current_state = reduce_event(current_state, event, rng_manager)
        events_processed += 1

    final_hash = current_state.state_hash()

    # Verify determinism if expected hash provided
    determinism_verified = True
    divergence_info = ""

    if expected_final_hash is not None:
        if final_hash != expected_final_hash:
            determinism_verified = False
            divergence_info = (
                f"Hash mismatch: expected {expected_final_hash}, got {final_hash}"
            )

    return ReplayReport(
        final_state=current_state,
        final_hash=final_hash,
        events_processed=events_processed,
        determinism_verified=determinism_verified,
        divergence_info=divergence_info,
    )
