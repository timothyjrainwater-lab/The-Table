"""Paladin Lay on Hands resolver — WO-ENGINE-LAY-ON-HANDS-001.

PHB p.44: Each day a paladin can heal a total number of hit points equal to
her paladin level × her Charisma modifier (minimum 1 if CHA mod > 0; 0 if
CHA mod ≤ 0). Standard action. Touch range (self or adjacent ally).

Pool refreshes on full rest.
"""

from copy import deepcopy
from typing import List, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def resolve_lay_on_hands(
    intent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve Paladin Lay on Hands.

    Returns (events, updated_world_state).

    Events emitted:
    - ``lay_on_hands_invalid``: actor is not a paladin
    - ``lay_on_hands_exhausted``: pool is empty
    - ``lay_on_hands_heal``: healing applied

    The world_state returned has:
    - ``EF.LAY_ON_HANDS_USED`` incremented on the actor
    - ``EF.HP_CURRENT`` updated on the target
    """
    events: List[Event] = []

    actor = world_state.entities.get(intent.actor_id, {})

    # ── Validate: actor is a paladin ────────────────────────────────────────
    paladin_level = actor.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
    if paladin_level == 0:
        events.append(Event(
            event_id=next_event_id,
            event_type="lay_on_hands_invalid",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "reason": "not_a_paladin",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 44}],
        ))
        return events, world_state

    # ── Validate: pool available ─────────────────────────────────────────────
    pool = actor.get(EF.LAY_ON_HANDS_POOL, 0)
    used = actor.get(EF.LAY_ON_HANDS_USED, 0)
    remaining = pool - used

    if remaining <= 0:
        events.append(Event(
            event_id=next_event_id,
            event_type="lay_on_hands_exhausted",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "pool": pool,
                "used": used,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 44}],
        ))
        return events, world_state

    # ── Clamp amount to pool remaining ──────────────────────────────────────
    amount = min(intent.amount, remaining)

    # ── Apply healing ────────────────────────────────────────────────────────
    entities = deepcopy(world_state.entities)
    target = entities[intent.target_id]
    actor_entity = entities[intent.actor_id]

    hp_before = target.get(EF.HP_CURRENT, 0)
    hp_max = target.get(EF.HP_MAX, hp_before)
    hp_after = min(hp_before + amount, hp_max)
    actual_healed = hp_after - hp_before

    target[EF.HP_CURRENT] = hp_after
    actor_entity[EF.LAY_ON_HANDS_USED] = used + amount

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )

    events.append(Event(
        event_id=next_event_id,
        event_type="lay_on_hands_heal",
        timestamp=timestamp,
        payload={
            "actor_id": intent.actor_id,
            "target_id": intent.target_id,
            "amount_spent": amount,
            "hp_healed": actual_healed,
            "hp_before": hp_before,
            "hp_after": hp_after,
            "pool_remaining": remaining - amount,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 44}],
    ))

    return events, world_state
