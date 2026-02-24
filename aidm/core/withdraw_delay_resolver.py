"""Withdraw and Delay action resolver — WO-ENGINE-WITHDRAW-DELAY-001.

Implements PHB p.144 (Withdraw) and PHB p.160 (Delay):

Withdraw (full-round action):
- First square departed does NOT provoke AoO (PHB p.144 "exception").
- Subsequent movement may provoke normally.
- Tracked via active_combat["withdrew_actors"] set.

Delay (free action that defers your turn):
- Actor chooses to act at a lower initiative count.
- initiative_order is permanently reordered for the rest of the encounter.
- When delaying to the same count as another non-delayed actor, the delayed
  actor acts after that actor (PHB p.160).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import WithdrawIntent, DelayIntent
from aidm.core.state import WorldState


def resolve_withdraw(
    intent: WithdrawIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[WorldState, List[Dict[str, Any]]]:
    """Record that actor used the Withdraw action.

    Marks the actor in active_combat["withdrew_actors"] so that the AoO
    kernel can suppress the first-square departure AoO.

    Args:
        intent: WithdrawIntent.
        world_state: Current world state.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated WorldState, events).
    """
    events: List[Dict[str, Any]] = []

    if world_state.active_combat is None:
        events.append({
            "event_id": next_event_id,
            "event_type": "withdraw_denied",
            "payload": {"actor_id": intent.actor_id, "reason": "not_in_combat"},
            "timestamp": timestamp,
        })
        return world_state, events

    actor = world_state.entities.get(intent.actor_id)
    if actor is None or actor.get(EF.DEFEATED, False):
        events.append({
            "event_id": next_event_id,
            "event_type": "withdraw_denied",
            "payload": {"actor_id": intent.actor_id, "reason": "actor_not_found"},
            "timestamp": timestamp,
        })
        return world_state, events

    # Record withdrawal in active_combat
    active_combat = deepcopy(world_state.active_combat)
    withdrew_actors: List[str] = list(active_combat.get("withdrew_actors", []))
    if intent.actor_id not in withdrew_actors:
        withdrew_actors.append(intent.actor_id)
    active_combat["withdrew_actors"] = withdrew_actors

    events.append({
        "event_id": next_event_id,
        "event_type": "withdraw_declared",
        "payload": {
            "actor_id": intent.actor_id,
        },
        "timestamp": timestamp,
        "citations": [{"source_id": "681f92bc94ff", "page": 144}],
    })

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=active_combat,
    )
    return updated_state, events


def resolve_delay(
    intent: DelayIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[WorldState, List[Dict[str, Any]]]:
    """Permanently reorder initiative to reflect the actor's new delay position.

    PHB p.160: Delaying to same count as another actor → delayed actor goes after.
    The actor is removed from their current position and inserted just after the
    last actor at new_initiative (or at the end if none share that count).

    Args:
        intent: DelayIntent with actor_id and new_initiative.
        world_state: Current world state.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated WorldState, events).
    """
    events: List[Dict[str, Any]] = []

    if world_state.active_combat is None:
        events.append({
            "event_id": next_event_id,
            "event_type": "delay_denied",
            "payload": {"actor_id": intent.actor_id, "reason": "not_in_combat"},
            "timestamp": timestamp,
        })
        return world_state, events

    active_combat = deepcopy(world_state.active_combat)
    initiative_order: List[str] = list(active_combat.get("initiative_order", []))
    initiative_scores: Dict[str, int] = dict(active_combat.get("initiative_scores", {}))

    if intent.actor_id not in initiative_order:
        events.append({
            "event_id": next_event_id,
            "event_type": "delay_denied",
            "payload": {"actor_id": intent.actor_id, "reason": "actor_not_in_initiative"},
            "timestamp": timestamp,
        })
        return world_state, events

    old_initiative = initiative_scores.get(intent.actor_id, 0)

    # Validate: cannot delay to higher than current initiative
    if intent.new_initiative >= old_initiative:
        events.append({
            "event_id": next_event_id,
            "event_type": "delay_denied",
            "payload": {
                "actor_id": intent.actor_id,
                "reason": "cannot_delay_to_higher_initiative",
                "current": old_initiative,
                "requested": intent.new_initiative,
            },
            "timestamp": timestamp,
        })
        return world_state, events

    # Remove actor from current position
    initiative_order.remove(intent.actor_id)

    # Find insertion point: just after the last actor with new_initiative score
    # (PHB: delayed actor acts after others at same count)
    initiative_scores[intent.actor_id] = intent.new_initiative

    # Rebuild order by score descending, maintaining relative order within same score
    # Place actor AFTER others with same score (delay rule)
    insert_idx = len(initiative_order)  # Default: end of list
    for i, eid in enumerate(initiative_order):
        score = initiative_scores.get(eid, 0)
        if score < intent.new_initiative:
            insert_idx = i
            break

    initiative_order.insert(insert_idx, intent.actor_id)

    active_combat["initiative_order"] = initiative_order
    active_combat["initiative_scores"] = initiative_scores

    events.append({
        "event_id": next_event_id,
        "event_type": "delay_declared",
        "payload": {
            "actor_id": intent.actor_id,
            "old_initiative": old_initiative,
            "new_initiative": intent.new_initiative,
            "new_position": insert_idx,
        },
        "timestamp": timestamp,
        "citations": [{"source_id": "681f92bc94ff", "page": 160}],
    })

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=active_combat,
    )
    return updated_state, events


def is_withdrawn(world_state: WorldState, actor_id: str) -> bool:
    """Return True if actor used Withdraw this round (first-square AoO immune).

    Called by aoo.py before checking AoO triggers.

    Args:
        world_state: Current world state.
        actor_id: Entity to check.

    Returns:
        True if actor has the withdraw flag set.
    """
    if world_state.active_combat is None:
        return False
    withdrew_actors = world_state.active_combat.get("withdrew_actors", [])
    return actor_id in withdrew_actors


def clear_withdrew_actors(
    world_state: WorldState,
    actor_id: str,
) -> WorldState:
    """Remove actor from withdrew_actors at the start of their next turn.

    Called by execute_turn() turn-start block.

    Args:
        world_state: Current world state.
        actor_id: Entity whose withdraw flag to clear.

    Returns:
        Updated WorldState.
    """
    if world_state.active_combat is None:
        return world_state
    withdrew_actors = list(world_state.active_combat.get("withdrew_actors", []))
    if actor_id not in withdrew_actors:
        return world_state
    withdrew_actors.remove(actor_id)
    active_combat = deepcopy(world_state.active_combat)
    active_combat["withdrew_actors"] = withdrew_actors
    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=active_combat,
    )
