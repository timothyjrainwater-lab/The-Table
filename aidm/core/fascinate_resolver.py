"""Fascinate bardic performance resolver.

Implements Bard Fascinate ability (PHB p.29).

Bard uses a standard action to fascinate up to (bard_level // 3) creatures within 90 ft
that can see and hear. Requires 3+ Perform ranks. Targets in active combat are immune.
Each target makes a Will save (DC 10 + bard_level // 2 + CHA_mod) or becomes FASCINATED.

WO-ENGINE-AG-WO4
# PHB p.29
"""

from typing import List, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF
from aidm.schemas.saves import SaveContext, SaveType, SaveOutcome


def resolve_fascinate(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a Fascinate bardic performance attempt.

    PHB p.29: Bard uses bardic music to fascinate one or more creatures.
    Requires 3+ Perform ranks; up to (bard_level // 3) targets; targets in combat immune.
    Will save DC = 10 + (bard_level // 2) + CHA_mod per target.

    WO-ENGINE-AG-WO4
    # PHB p.29
    """
    from aidm.core.save_resolver import resolve_save as _resolve_save
    from aidm.schemas.conditions import create_fascinated_condition

    events: List[Event] = []
    current_event_id = next_event_id
    actor = world_state.entities.get(intent.actor_id, {})

    # --- Validation ---
    bard_level = actor.get(EF.CLASS_LEVELS, {}).get("bard", 0)
    if bard_level < 1:
        events.append(Event(
            event_id=current_event_id,
            event_type="fascinate_invalid",
            timestamp=timestamp,
            payload={"actor_id": intent.actor_id, "reason": "not_bard"},
            citations=[{"source_id": "681f92bc94ff", "page": 29}],
        ))
        return events

    # Require 3+ Perform ranks (PHB p.29)
    perform_ranks = actor.get(EF.PERFORM_RANKS, 0)
    if perform_ranks < 3:
        events.append(Event(
            event_id=current_event_id,
            event_type="fascinate_invalid",
            timestamp=timestamp,
            payload={"actor_id": intent.actor_id, "reason": "insufficient_perform_ranks",
                     "perform_ranks": perform_ranks},
            citations=[{"source_id": "681f92bc94ff", "page": 29}],
        ))
        return events

    # Check bardic music uses remaining
    uses_remaining = actor.get(EF.BARDIC_MUSIC_USES_REMAINING, 0)
    if uses_remaining <= 0:
        events.append(Event(
            event_id=current_event_id,
            event_type="bardic_music_exhausted",
            timestamp=timestamp,
            payload={"actor_id": intent.actor_id},
            citations=[{"source_id": "681f92bc94ff", "page": 29}],
        ))
        return events

    # Compute DC and target cap
    cha_mod = actor.get(EF.CHA_MOD, 0)
    dc = 10 + (bard_level // 2) + cha_mod
    max_targets = bard_level // 3  # 1 at L3, 2 at L6, etc.

    # Consume one bardic music use
    events.append(Event(
        event_id=current_event_id,
        event_type="bardic_music_used",
        timestamp=timestamp,
        payload={"actor_id": intent.actor_id, "uses_before": uses_remaining,
                 "uses_after": uses_remaining - 1, "performance": "fascinate"},
        citations=[{"source_id": "681f92bc94ff", "page": 29}],
    ))
    current_event_id += 1

    # --- Per-target resolution ---
    targets_attempted = 0
    for target_id in intent.target_ids:
        if targets_attempted >= max_targets:
            break

        target = world_state.entities.get(target_id, {})

        # Targets in active combat are immune (PHB p.29: distraction of nearby combat blocks)
        # The in_combat flag is asserted by the caller via the target_ids list;
        # we check EF.CONDITIONS for "in_combat" or trust the caller to exclude them.
        # FA-006: target with "in_combat" in CONDITIONS is blocked.
        target_conditions = target.get(EF.CONDITIONS, {})
        _in_combat = False
        if isinstance(target_conditions, dict):
            _in_combat = "in_combat" in target_conditions
        else:
            _in_combat = "in_combat" in target_conditions

        if _in_combat:
            events.append(Event(
                event_id=current_event_id,
                event_type="fascinate_blocked",
                timestamp=timestamp + 0.01 * targets_attempted,
                payload={"actor_id": intent.actor_id, "target_id": target_id,
                         "reason": "target_in_combat"},
                citations=[{"source_id": "681f92bc94ff", "page": 29}],
            ))
            current_event_id += 1
            targets_attempted += 1
            continue

        # Roll Will save per target
        save_ctx = SaveContext(
            save_type=SaveType.WILL,
            dc=dc,
            source_id=intent.actor_id,
            target_id=target_id,
        )
        outcome, save_events = _resolve_save(
            save_ctx, world_state, rng, current_event_id,
            timestamp + 0.01 + 0.01 * targets_attempted,
        )
        events.extend(save_events)
        current_event_id += len(save_events)

        if outcome == SaveOutcome.FAILURE:
            # Apply FASCINATED condition
            _cond = create_fascinated_condition(
                source=intent.actor_id,
                applied_at_event_id=current_event_id,
            )
            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=timestamp + 0.02 + 0.01 * targets_attempted,
                payload={
                    "entity_id": target_id,
                    "condition": _cond.condition_type,
                    "source": "fascinate",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 29}],
            ))
            current_event_id += 1
            events.append(Event(
                event_id=current_event_id,
                event_type="fascinate_success",
                timestamp=timestamp + 0.025 + 0.01 * targets_attempted,
                payload={"actor_id": intent.actor_id, "target_id": target_id, "dc": dc},
                citations=[{"source_id": "681f92bc94ff", "page": 29}],
            ))
        else:
            events.append(Event(
                event_id=current_event_id,
                event_type="fascinate_saved",
                timestamp=timestamp + 0.025 + 0.01 * targets_attempted,
                payload={"actor_id": intent.actor_id, "target_id": target_id, "dc": dc},
                citations=[{"source_id": "681f92bc94ff", "page": 29}],
            ))
        current_event_id += 1
        targets_attempted += 1

    return events


def apply_fascinate_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """Apply Fascinate events to world state.

    Handles:
    - bardic_music_used: decrements EF.BARDIC_MUSIC_USES_REMAINING
    - condition_applied (source=fascinate): appended via existing condition mechanism

    WO-ENGINE-AG-WO4
    """
    from copy import deepcopy
    entities = deepcopy(world_state.entities)

    for event in events:
        if event.event_type == "bardic_music_used":
            entity_id = event.payload["actor_id"]
            if entity_id in entities:
                entities[entity_id][EF.BARDIC_MUSIC_USES_REMAINING] = event.payload["uses_after"]

        elif event.event_type == "condition_applied":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                cond_val = event.payload["condition"]
                conds = entities[entity_id].get(EF.CONDITIONS, {})
                if isinstance(conds, dict):
                    if cond_val not in conds:
                        conds = dict(conds)
                        conds[cond_val] = {}
                    entities[entity_id][EF.CONDITIONS] = conds
                else:
                    if cond_val not in conds:
                        conds = list(conds) + [cond_val]
                    entities[entity_id][EF.CONDITIONS] = conds

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )
