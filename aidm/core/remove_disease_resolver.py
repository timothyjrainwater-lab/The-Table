"""Paladin Remove Disease resolver — WO-ENGINE-AF-WO3.

PHB p.44: At 3rd level, a paladin can remove disease from herself or a touched
creature once per week. She gains one additional use for every three additional
paladin levels (twice at L6, three times at L9, etc.). Formula: paladin_level // 3.

HOUSE_POLICY: "per week" modeled as "per full rest" for resource management
consistency with spell slots, smite uses, and bardic music uses.
"""

from copy import deepcopy
from typing import List, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def resolve_remove_disease(
    intent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve Paladin Remove Disease.

    Returns (events, updated_world_state).

    Events emitted:
    - ``remove_disease_invalid``: actor is not a paladin L3+
    - ``remove_disease_exhausted``: no uses remaining this rest
    - ``remove_disease_cured``: disease cleared from target
    - ``remove_disease_no_effect``: target had no active disease (graceful no-op)

    # PHB p.44
    """
    events: List[Event] = []

    actor = world_state.entities.get(intent.actor_id, {})

    # ── Validate: actor is a paladin with remove disease (L3+) ───────────────
    paladin_level = actor.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
    uses_max = actor.get(EF.REMOVE_DISEASE_USES, 0)

    if paladin_level < 3 or uses_max == 0:
        events.append(Event(
            event_id=next_event_id,
            event_type="remove_disease_invalid",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "paladin_level": paladin_level,
                "reason": "not_a_paladin_l3" if paladin_level < 3 else "no_uses",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 44}],
        ))
        return events, world_state

    # ── Validate: uses remaining ─────────────────────────────────────────────
    used = actor.get(EF.REMOVE_DISEASE_USED, 0)
    remaining = uses_max - used

    if remaining <= 0:
        events.append(Event(
            event_id=next_event_id,
            event_type="remove_disease_exhausted",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "uses_max": uses_max,
                "used": used,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 44}],
        ))
        return events, world_state

    # ── Apply: clear diseases from target ────────────────────────────────────
    entities = deepcopy(world_state.entities)
    target = entities[intent.target_id]
    actor_entity = entities[intent.actor_id]

    active_diseases = list(target.get(EF.ACTIVE_DISEASES, []))
    diseases_cleared = len(active_diseases)

    target[EF.ACTIVE_DISEASES] = []
    actor_entity[EF.REMOVE_DISEASE_USED] = used + 1

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )

    if diseases_cleared == 0:
        # Graceful no-op — target had no disease
        events.append(Event(
            event_id=next_event_id,
            event_type="remove_disease_no_effect",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "uses_remaining": remaining - 1,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 44}],
        ))
    else:
        events.append(Event(
            event_id=next_event_id,
            event_type="remove_disease_cured",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "diseases_cleared": diseases_cleared,
                "uses_remaining": remaining - 1,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 44}],
        ))

    return events, world_state
