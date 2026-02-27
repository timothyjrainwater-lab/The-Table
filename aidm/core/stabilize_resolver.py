"""Stabilize-ally resolver — WO-ENGINE-STABILIZE-ALLY-001.

PHB p.152: First Aid (standard action). DC 15 Heal check.
On success, target gains EF.STABLE = True — the dying bleed stops.
HP remains negative; the target is not healed.
"""

from typing import List, Tuple

from aidm.core.skill_resolver import resolve_skill_check
from aidm.schemas.entity_fields import EF
from aidm.core.event_log import Event
from aidm.schemas.intents import StabilizeIntent

STABILIZE_DC = 15


def resolve_stabilize(
    intent: StabilizeIntent,
    world_state,
    rng,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], object]:
    """Resolve a Heal check to stabilize a dying ally (PHB p.152).

    Args:
        intent: StabilizeIntent with actor_id and target_id.
        world_state: Current WorldState.
        rng: RNG provider.
        next_event_id: Next available event ID.
        timestamp: Base timestamp for events.

    Returns:
        (events, world_state) — world_state is mutated in-place on success.
    """
    events: List[Event] = []
    current_event_id = next_event_id

    actor = world_state.entities.get(intent.actor_id)
    target = world_state.entities.get(intent.target_id)

    if actor is None or target is None:
        return events, world_state

    # Reject: self-stabilization (PHB p.152 requires another creature)
    if intent.actor_id == intent.target_id:
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_invalid",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "reason": "cannot_stabilize_self",
            },
            citations=["PHB p.152"],
        ))
        return events, world_state

    # Reject: target is not dying (HP must be -1 to -9, not already stable)
    target_hp = target.get(EF.HP_CURRENT, 0)
    already_stable = target.get(EF.STABLE, False)
    is_dying = target_hp <= -1 and target_hp >= -9 and not already_stable
    if not is_dying:
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_invalid",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "reason": "target_not_dying",
                "target_hp": target_hp,
                "already_stable": already_stable,
            },
            citations=["PHB p.152"],
        ))
        return events, world_state

    # DC 15 Heal check
    result = resolve_skill_check(actor, "heal", STABILIZE_DC, rng)
    heal_bonus = result.ability_modifier + result.skill_ranks

    if result.success:
        # Set STABLE — dying tick will skip this entity
        world_state.entities[intent.target_id][EF.STABLE] = True
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_success",
            timestamp=timestamp + 0.1,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "heal_roll": result.d20_roll,
                "heal_bonus": heal_bonus,
                "heal_total": result.total,
                "dc": STABILIZE_DC,
                "target_hp": target_hp,
            },
            citations=["PHB p.152"],
        ))
    else:
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_failed",
            timestamp=timestamp + 0.1,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "heal_roll": result.d20_roll,
                "heal_bonus": heal_bonus,
                "heal_total": result.total,
                "dc": STABILIZE_DC,
                "target_hp": target_hp,
            },
            citations=["PHB p.152"],
        ))

    return events, world_state
