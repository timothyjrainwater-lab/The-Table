"""Dying and stabilization resolver. WO-ENGINE-DEATH-DYING-001.

PHB p.145: Three HP bands — disabled (0), dying (-1 to -9), dead (-10+).
Dying creatures lose 1 HP/round unless they pass DC 10 Fort save.
"""

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from aidm.schemas.entity_fields import EF
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider


def classify_hp(hp: int) -> str:
    """Classify HP value into PHB death band.

    Returns: 'conscious', 'disabled', 'dying', or 'dead'
    """
    if hp >= 1:
        return 'conscious'
    elif hp == 0:
        return 'disabled'
    elif hp >= -9:
        return 'dying'
    else:
        return 'dead'


def resolve_hp_transition(
    entity_id: str,
    old_hp: int,
    new_hp: int,
    source: str,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], Dict[str, Any]]:
    """Resolve state transition when an entity's HP changes.

    Emits appropriate state transition events based on old→new HP band.
    Returns (events, entity_field_updates) — caller applies field updates.

    PHB p.145: Transitions are:
    - Any → disabled (new_hp == 0): entity_disabled event
    - Any → dying (-1 to -9): entity_dying event
    - Any → dead (-10+): entity_defeated event (true death)
    - Dying/disabled → conscious (healing): entity_revived event, clear DYING/STABLE
    - No transition if band unchanged.

    Args:
        entity_id: Entity whose HP changed
        old_hp: HP before change
        new_hp: HP after change
        source: Source of change (e.g., "attack_damage", "bleed")
        world_state: Current world state
        next_event_id: Next event ID for sequencing
        timestamp: Event timestamp

    Returns:
        (events, field_updates): events to emit, dict of EF fields to apply
    """
    events = []
    field_updates: Dict[str, Any] = {}
    eid = next_event_id

    old_band = classify_hp(old_hp)
    new_band = classify_hp(new_hp)

    if old_band == new_band:
        return events, field_updates  # No transition

    if new_band == 'disabled':
        field_updates[EF.DISABLED] = True
        field_updates[EF.DYING] = False
        field_updates[EF.STABLE] = False
        events.append(Event(
            event_id=eid, event_type="entity_disabled", timestamp=timestamp,
            payload={"entity_id": entity_id, "hp": new_hp, "source": source},
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    elif new_band == 'dying':
        field_updates[EF.DYING] = True
        field_updates[EF.DISABLED] = False
        field_updates[EF.STABLE] = False
        field_updates[EF.DEFEATED] = False  # NOT dead yet
        events.append(Event(
            event_id=eid, event_type="entity_dying", timestamp=timestamp,
            payload={"entity_id": entity_id, "hp": new_hp, "source": source},
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    elif new_band == 'dead':
        field_updates[EF.DYING] = False
        field_updates[EF.DISABLED] = False
        field_updates[EF.STABLE] = False
        field_updates[EF.DEFEATED] = True  # Actually dead
        events.append(Event(
            event_id=eid, event_type="entity_defeated", timestamp=timestamp,
            payload={
                "entity_id": entity_id, "hp": new_hp,
                "source": source, "cause": "dead",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    elif new_band == 'conscious' and old_band in ('dying', 'disabled'):
        # Healed out of danger
        field_updates[EF.DYING] = False
        field_updates[EF.DISABLED] = False
        field_updates[EF.STABLE] = False
        field_updates[EF.DEFEATED] = False
        events.append(Event(
            event_id=eid, event_type="entity_revived", timestamp=timestamp,
            payload={"entity_id": entity_id, "hp": new_hp, "source": source},
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    return events, field_updates


def resolve_dying_tick(
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Process dying bleed for all dying entities at end of round.

    PHB p.145: Each dying entity loses 1 HP unless they pass DC 10 Fort save.
    On save success: entity becomes stable (no further HP loss).
    On save fail: lose 1 HP. If new HP <= -10: dead.

    Called from play_loop.py at end-of-round tick (after tick_round()).

    RNG consumption: one "combat" stream d20 per dying entity, in entity_id
    alphabetical order (deterministic).

    Args:
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Event timestamp

    Returns:
        (events, updated_world_state)
    """
    events = []
    current_event_id = next_event_id
    entities = {k: deepcopy(v) for k, v in world_state.entities.items()}

    # Alphabetical order for determinism
    dying_entities = sorted(
        eid for eid, e in entities.items()
        if e.get(EF.DYING, False) and not e.get(EF.STABLE, False)
    )

    for entity_id in dying_entities:
        entity = entities[entity_id]
        fort_save = entity.get(EF.SAVE_FORT, 0)

        roll = rng.stream("combat").randint(1, 20)
        total = roll + fort_save
        dc = 10

        if total >= dc:
            # Stabilized — no more HP loss
            entity[EF.STABLE] = True
            events.append(Event(
                event_id=current_event_id,
                event_type="entity_stabilized",
                timestamp=timestamp,
                payload={
                    "entity_id": entity_id,
                    "hp": entity.get(EF.HP_CURRENT, -1),
                    "roll": roll,
                    "fort_save": fort_save,
                    "total": total,
                    "dc": dc,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}],
            ))
            current_event_id += 1
        else:
            # Bleed: lose 1 HP
            old_hp = entity.get(EF.HP_CURRENT, -1)
            new_hp = old_hp - 1
            entity[EF.HP_CURRENT] = new_hp

            events.append(Event(
                event_id=current_event_id,
                event_type="hp_changed",
                timestamp=timestamp,
                payload={
                    "entity_id": entity_id,
                    "old_hp": old_hp,
                    "new_hp": new_hp,
                    "delta": -1,
                    "source": "dying_bleed",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}],
            ))
            current_event_id += 1

            # dying_fort_failed event (before possible entity_defeated)
            events.append(Event(
                event_id=current_event_id,
                event_type="dying_fort_failed",
                timestamp=timestamp + 0.01,
                payload={
                    "entity_id": entity_id,
                    "hp": new_hp,
                    "roll": roll,
                    "fort_save": fort_save,
                    "total": total,
                    "dc": dc,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}],
            ))
            current_event_id += 1

            # Check if now dead
            if new_hp <= -10:
                entity[EF.DYING] = False
                entity[EF.DEFEATED] = True
                events.append(Event(
                    event_id=current_event_id,
                    event_type="entity_defeated",
                    timestamp=timestamp + 0.02,
                    payload={
                        "entity_id": entity_id,
                        "hp": new_hp,
                        "source": "dying_bleed",
                        "cause": "dead",
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 145}],
                ))
                current_event_id += 1

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
    )
    return events, updated_state
