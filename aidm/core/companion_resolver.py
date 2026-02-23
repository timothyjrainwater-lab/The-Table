"""Animal companion spawning resolver for the engine runtime.

WO-ENGINE-COMPANION-WIRE

Wires build_animal_companion() (chargen layer) into the engine event stream.
spawn_companion() is a pure function: it reads WorldState, builds the companion
entity via the chargen layer, and emits an add_entity event.  No direct state
mutation occurs here — state change happens via the replay_runner reducer when
the emitted add_entity event is applied.

BOUNDARY LAW (BL-012): All state mutation is event-sourced.  This resolver
emits events; replay_runner.reduce_event() applies them.

BOUNDARY LAW (BL-020): Callers must pass raw WorldState (engine context).
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from copy import deepcopy

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.chargen.companions import build_animal_companion, BASE_COMPANION_STATS
from aidm.schemas.entity_fields import EF


@dataclass
class SummonCompanionResult:
    """Result of a companion spawn resolution."""

    status: str
    """
    "ok"             — companion successfully spawned.
    "already_active" — companion already present in WorldState (idempotent guard).
    "invalid_actor"  — actor has no qualifying class (druid or ranger 4+).
    "invalid_type"   — companion_type is unknown or None.
    "actor_not_found"— actor_id not in WorldState.entities.
    """

    events: List[Event]
    """Events to add to the event log (empty on failure)."""

    companion_entity_id: Optional[str] = None
    """entity_id of the spawned companion, or None on failure."""

    failure_reason: Optional[str] = None
    """Human-readable reason string when status != "ok"."""


def spawn_companion(
    owner_id: str,
    companion_type: str,
    world_state: WorldState,
    next_event_id: int = 0,
    timestamp: float = 0.0,
) -> SummonCompanionResult:
    """Spawn an animal companion entity into WorldState via add_entity event.

    This is a pure function.  It does NOT mutate world_state.  Callers apply
    the returned events to a WorldState copy via replay_runner.reduce_event()
    to obtain the updated state.

    Args:
        owner_id:       entity_id of the druid or ranger calling the companion.
        companion_type: Species key — one of BASE_COMPANION_STATS keys.
        world_state:    Current raw WorldState (engine context, BL-020).
        next_event_id:  Starting event_id for emitted events.
        timestamp:      Event timestamp.

    Returns:
        SummonCompanionResult with status, events list, and companion_entity_id.

    PHB references:
        - Druid animal companion: PHB p.36-37
        - Ranger animal companion: PHB p.47
    """
    events: List[Event] = []
    current_event_id = next_event_id

    # --- Validate companion_type ---
    if companion_type is None or companion_type not in BASE_COMPANION_STATS:
        valid = list(BASE_COMPANION_STATS.keys())
        return SummonCompanionResult(
            status="invalid_type",
            events=[],
            failure_reason=(
                f"Unknown companion type '{companion_type}'. "
                f"Valid types: {valid}"
            ),
        )

    # --- Validate actor exists ---
    owner_entity = world_state.entities.get(owner_id)
    if owner_entity is None:
        return SummonCompanionResult(
            status="actor_not_found",
            events=[],
            failure_reason=f"Actor '{owner_id}' not found in WorldState.",
        )

    # --- Check for qualifying class (druid or ranger 4+) ---
    class_levels = owner_entity.get(EF.CLASS_LEVELS, {})
    druid_lvl = class_levels.get("druid", 0)
    ranger_lvl = class_levels.get("ranger", 0)
    effective_level = druid_lvl + max(0, ranger_lvl - 3)
    if effective_level < 1:
        return SummonCompanionResult(
            status="invalid_actor",
            events=[],
            failure_reason=(
                f"Actor '{owner_id}' has no qualifying companion class "
                f"(druid or ranger level 4+). class_levels={class_levels}"
            ),
        )

    # --- Compute expected companion entity_id ---
    companion_entity_id = f"companion_{companion_type}_{owner_id}"

    # --- Idempotent guard: companion already in WorldState ---
    if companion_entity_id in world_state.entities:
        return SummonCompanionResult(
            status="already_active",
            events=[],
            companion_entity_id=companion_entity_id,
            failure_reason=(
                f"Companion '{companion_entity_id}' is already present in WorldState."
            ),
        )

    # --- Build companion entity dict via chargen layer ---
    # build_animal_companion() may raise ValueError for invalid inputs;
    # those are guarded above so this call should succeed.
    companion_entity = build_animal_companion(
        parent_entity=dict(owner_entity),  # plain dict copy (not MappingProxy)
        companion_type=companion_type,
    )

    # --- Tag with engine-wire metadata fields ---
    companion_entity[EF.COMPANION_OWNER_ID] = owner_id
    companion_entity[EF.COMPANION_TYPE] = companion_type

    # --- Emit add_entity event ---
    events.append(Event(
        event_id=current_event_id,
        event_type="add_entity",
        timestamp=timestamp,
        payload={
            "entity_id": companion_entity_id,
            "data": deepcopy(companion_entity),
            "source": "companion_resolver",
            "owner_id": owner_id,
            "companion_type": companion_type,
        },
    ))

    return SummonCompanionResult(
        status="ok",
        events=events,
        companion_entity_id=companion_entity_id,
    )
