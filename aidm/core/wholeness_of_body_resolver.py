"""Monk Wholeness of Body resolver — WO-ENGINE-WHOLENESS-OF-BODY-001.

PHB p.42: "At 7th level or higher, a monk can heal her own wounds. She can
heal a number of hit points of damage equal to twice her current monk level
each day, and she can spread this healing out among several uses."

Pool: 2 × monk_level HP per day. Tracked via EF.WHOLENESS_OF_BODY_USED.
Self-only. Standard action. Cannot exceed HP_MAX. Cannot use unconscious.
"""

from dataclasses import dataclass
from copy import deepcopy
from typing import List, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


@dataclass
class WholenessOfBodyIntent:
    """Intent to use Wholeness of Body self-healing."""

    actor_id: str
    """Monk healing themselves"""

    amount: int
    """HP requested to restore (actual may be clamped to pool/max)"""


def resolve_wholeness_of_body(
    intent: WholenessOfBodyIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve Wholeness of Body self-healing.

    Returns (events, updated_world_state).

    Events emitted:
    - ``wholeness_of_body_invalid``: actor is not a qualifying monk
    - ``wholeness_of_body_exhausted``: pool is empty
    - ``wholeness_of_body_blocked``: actor is unconscious
    - ``wholeness_of_body_no_effect``: actor already at full HP
    - ``wholeness_of_body_heal``: healing applied
    """
    events: List[Event] = []
    eid = next_event_id

    actor = world_state.entities.get(intent.actor_id, {})

    # ── Validate: must be monk L7+ ───────────────────────────────────────────
    monk_level = actor.get(EF.CLASS_LEVELS, {}).get("monk", 0)
    if monk_level < 7:
        events.append(Event(
            event_id=eid,
            event_type="wholeness_of_body_invalid",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "reason": "not_qualifying_monk",
                "monk_level": monk_level,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 42}],
        ))
        return events, world_state

    # ── Validate: cannot use while unconscious ───────────────────────────────
    _conds = actor.get(EF.CONDITIONS, [])
    _unconscious = any(
        (c.get("type") == "unconscious" if isinstance(c, dict) else False)
        for c in _conds
    )
    if actor.get(EF.DYING, False) or actor.get(EF.DEFEATED, False) or _unconscious:
        events.append(Event(
            event_id=eid,
            event_type="wholeness_of_body_blocked",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "reason": "unconscious",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 42}],
        ))
        return events, world_state

    # ── Check pool ────────────────────────────────────────────────────────────
    pool = actor.get(EF.WHOLENESS_OF_BODY_POOL, monk_level * 2)
    used = actor.get(EF.WHOLENESS_OF_BODY_USED, 0)
    remaining = pool - used

    if remaining <= 0:
        events.append(Event(
            event_id=eid,
            event_type="wholeness_of_body_exhausted",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "pool": pool,
                "used": used,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 42}],
        ))
        return events, world_state

    # ── Check if at full HP ───────────────────────────────────────────────────
    hp_before = actor.get(EF.HP_CURRENT, 0)
    hp_max = actor.get(EF.HP_MAX, hp_before)
    if hp_before >= hp_max:
        events.append(Event(
            event_id=eid,
            event_type="wholeness_of_body_no_effect",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "reason": "already_at_max_hp",
                "hp_current": hp_before,
                "hp_max": hp_max,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 42}],
        ))
        return events, world_state

    # ── Apply healing ─────────────────────────────────────────────────────────
    amount = min(intent.amount, remaining)
    hp_after = min(hp_before + amount, hp_max)
    actual_healed = hp_after - hp_before
    amount_spent = actual_healed  # Only consume what was actually healed

    entities = deepcopy(world_state.entities)
    entities[intent.actor_id][EF.HP_CURRENT] = hp_after
    entities[intent.actor_id][EF.WHOLENESS_OF_BODY_USED] = used + amount_spent

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )

    events.append(Event(
        event_id=eid,
        event_type="wholeness_of_body_heal",
        timestamp=timestamp,
        payload={
            "actor_id": intent.actor_id,
            "amount_requested": intent.amount,
            "amount_spent": amount_spent,
            "hp_healed": actual_healed,
            "hp_before": hp_before,
            "hp_after": hp_after,
            "pool_remaining": remaining - amount_spent,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 42}],
    ))

    return events, world_state
