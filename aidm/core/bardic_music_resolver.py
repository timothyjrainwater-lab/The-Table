"""Bardic Music -- Inspire Courage + Inspire Greatness runtime resolver.

WO-ENGINE-BARDIC-MUSIC-001: Inspire Courage (PHB pp.29-30).
WO-ENGINE-INSPIRE-GREATNESS-001: Inspire Greatness (PHB p.30).

Uses/day = Bard level. Inspire Greatness requires L9+ and 12+ Perform ranks.
Duration: 8 rounds (Inspire Courage v1 fixed); concentration + 5 rounds (Inspire Greatness).
"""

from copy import deepcopy
from typing import List, Optional, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF

_INSPIRE_COURAGE_DURATION_ROUNDS = 8  # v1 fixed duration (FINDING-BARDIC-DURATION-001)


def _has_bard_feature(actor: dict) -> bool:
    class_levels = actor.get(EF.CLASS_LEVELS, {}) or {}
    if isinstance(class_levels, dict):
        return class_levels.get("bard", 0) >= 1
    return False


def _bard_is_incapacitated(bard: dict) -> bool:
    """Return True if the bard can no longer maintain Inspire Courage.

    PHB p.29: Inspire Courage ends if the bard becomes unconscious, dies,
    or is deafened. Mapped to: DEFEATED, DYING, or DEAFENED condition present.
    """
    if bard.get(EF.DEFEATED, False):
        return True
    if bard.get(EF.DYING, False):
        return True
    conditions = bard.get(EF.CONDITIONS, {}) or {}
    if isinstance(conditions, dict) and "deafened" in conditions:
        return True
    return False


def _get_bard_level(actor: dict) -> int:
    class_levels = actor.get(EF.CLASS_LEVELS, {}) or {}
    if isinstance(class_levels, dict):
        return class_levels.get("bard", 0)
    return 0


def get_inspire_courage_bonus(bard_class_level: int) -> int:
    """Return morale bonus for Bard class level (PHB p.29).
    Level 1-7: +1. Level 8-13: +2. Level 14-19: +3. Level 20+: +4.
    """
    if bard_class_level >= 20:
        return 4
    elif bard_class_level >= 14:
        return 3
    elif bard_class_level >= 8:
        return 2
    else:
        return 1


def validate_bardic_music(actor: dict, world_state: WorldState,
                           performance: str = "inspire_courage") -> Optional[str]:
    """Validate bardic music activation. Returns error reason or None."""
    if not _has_bard_feature(actor):
        return "not_a_bard"
    if performance not in ("inspire_courage", "inspire_greatness"):
        return "unsupported_performance"
    if actor.get(EF.BARDIC_MUSIC_USES_REMAINING, 0) <= 0:
        return "no_bardic_music_uses"
    return None


def resolve_bardic_music(
    intent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve Bardic Music -- Inspire Courage.

    Decrements uses, sets INSPIRE_COURAGE_ACTIVE + INSPIRE_COURAGE_BONUS on bard
    and all ally_ids. Stores INSPIRE_COURAGE_BARD_ID on each affected entity so
    tick_inspire_courage can check bard state. Emits inspire_courage_start.
    Returns (events, world_state).
    """
    events: List[Event] = []
    actor = world_state.entities.get(intent.actor_id, {})

    err = validate_bardic_music(actor, world_state, intent.performance)
    if err:
        events.append(Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "intent_type": "BardicMusicIntent",
                "reason": err,
            },
        ))
        return events, world_state

    entities = deepcopy(world_state.entities)
    bard_actor = entities[intent.actor_id]

    # Decrement uses
    uses_before = bard_actor.get(EF.BARDIC_MUSIC_USES_REMAINING, 0)
    uses_after = max(0, uses_before - 1)
    bard_actor[EF.BARDIC_MUSIC_USES_REMAINING] = uses_after

    bard_level = _get_bard_level(bard_actor)
    bonus = get_inspire_courage_bonus(bard_level)

    # Apply to bard + all specified allies (morale bonuses don't stack -- take max)
    affected_ids = [intent.actor_id] + [a for a in (intent.ally_ids or []) if a != intent.actor_id]
    for eid in affected_ids:
        if eid not in entities:
            continue
        target = entities[eid]
        existing_bonus = target.get(EF.INSPIRE_COURAGE_BONUS, 0) or 0
        new_bonus = max(existing_bonus, bonus)
        target[EF.INSPIRE_COURAGE_ACTIVE] = True
        target[EF.INSPIRE_COURAGE_BONUS] = new_bonus
        target[EF.INSPIRE_COURAGE_ROUNDS_REMAINING] = _INSPIRE_COURAGE_DURATION_ROUNDS
        target[EF.INSPIRE_COURAGE_BARD_ID] = intent.actor_id  # WO-ENGINE-BARDIC-DURATION-001

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )

    events.append(Event(
        event_id=next_event_id,
        event_type="inspire_courage_start",
        timestamp=timestamp,
        payload={
            "actor_id": intent.actor_id,
            "affected_ids": affected_ids,
            "bonus": bonus,
            "rounds": _INSPIRE_COURAGE_DURATION_ROUNDS,
            "uses_remaining": uses_after,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 29}],
    ))

    return events, world_state


def tick_inspire_courage(
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Decrement INSPIRE_COURAGE_ROUNDS_REMAINING for all affected entities at turn end.

    WO-ENGINE-BARDIC-DURATION-001: If the source bard (INSPIRE_COURAGE_BARD_ID) is
    defeated, dying, or deafened, the effect expires immediately on this tick regardless
    of rounds remaining.

    When rounds reach 0 (or bard is incapacitated), clears INSPIRE_COURAGE_ACTIVE,
    INSPIRE_COURAGE_BONUS, and INSPIRE_COURAGE_BARD_ID.
    Emits inspire_courage_end per affected entity group that expires.
    """
    events: List[Event] = []
    entities = deepcopy(world_state.entities)
    expired_ids = []
    any_mutated = False

    for eid, entity in entities.items():
        if not entity.get(EF.INSPIRE_COURAGE_ACTIVE, False):
            continue

        # Check bard incapacitation (WO-ENGINE-BARDIC-DURATION-001)
        bard_id = entity.get(EF.INSPIRE_COURAGE_BARD_ID)
        bard_incapacitated = False
        if bard_id and bard_id in entities:
            bard_incapacitated = _bard_is_incapacitated(entities[bard_id])

        rounds_left = entity.get(EF.INSPIRE_COURAGE_ROUNDS_REMAINING, 0)
        new_rounds = max(0, rounds_left - 1)

        if new_rounds <= 0 or bard_incapacitated:
            entity[EF.INSPIRE_COURAGE_ACTIVE] = False
            entity[EF.INSPIRE_COURAGE_BONUS] = 0
            entity[EF.INSPIRE_COURAGE_ROUNDS_REMAINING] = 0
            entity[EF.INSPIRE_COURAGE_BARD_ID] = None
            expired_ids.append(eid)
            any_mutated = True
        else:
            entity[EF.INSPIRE_COURAGE_ROUNDS_REMAINING] = new_rounds
            any_mutated = True

    if expired_ids:
        events.append(Event(
            event_id=next_event_id,
            event_type="inspire_courage_end",
            timestamp=timestamp,
            payload={"affected_ids": expired_ids},
        ))

    if any_mutated:
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
        )

    return events, world_state


# ==============================================================================
# WO-ENGINE-INSPIRE-GREATNESS-001: Inspire Greatness (PHB p.30)
# ==============================================================================

_INSPIRE_GREATNESS_MIN_BARD_LEVEL = 9
_INSPIRE_GREATNESS_MIN_PERFORM_RANKS = 12
_INSPIRE_GREATNESS_DURATION_ROUNDS = 8  # concentration + 5 (approx, same as IC v1)


def resolve_inspire_greatness(
    intent,
    world_state: WorldState,
    rng,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve Inspire Greatness bardic performance (PHB p.30).

    Bard L9+, 12+ Perform ranks. Targets up to 1 + Cha mod allies within 30 ft.
    Each target gains:
      - 2d10 + (2 × Con mod) temp HP (EF.HP_TEMP)
      - +2 competence bonus to attack (TEMPORARY_MODIFIERS["inspire_greatness_bab"])
      - +1 competence bonus to Fort saves (TEMPORARY_MODIFIERS["inspire_greatness_fort"])
    Competence non-stacking: higher value wins (PHB p.136).
    Consumes one bardic music use.
    """
    events: List[Event] = []
    actor = world_state.entities.get(intent.actor_id, {})

    # Gate: validate base bardic music rules
    err = validate_bardic_music(actor, world_state, "inspire_greatness")
    if err:
        events.append(Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "intent_type": "BardicMusicIntent",
                "reason": err,
            },
        ))
        return events, world_state

    # Gate: bard L9+ requirement
    bard_level = _get_bard_level(actor)
    if bard_level < _INSPIRE_GREATNESS_MIN_BARD_LEVEL:
        events.append(Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "intent_type": "BardicMusicIntent",
                "reason": "inspire_greatness_level_too_low",
                "reason_detail": f"Bard L{bard_level} < L{_INSPIRE_GREATNESS_MIN_BARD_LEVEL} required (PHB p.30)",
            },
        ))
        return events, world_state

    # Gate: 12+ Perform ranks requirement
    perform_ranks = actor.get(EF.SKILL_RANKS, {}).get("perform", 0)
    if perform_ranks < _INSPIRE_GREATNESS_MIN_PERFORM_RANKS:
        events.append(Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "intent_type": "BardicMusicIntent",
                "reason": "inspire_greatness_perform_ranks_too_low",
                "reason_detail": f"Perform ranks {perform_ranks} < {_INSPIRE_GREATNESS_MIN_PERFORM_RANKS} required (PHB p.30)",
            },
        ))
        return events, world_state

    entities = deepcopy(world_state.entities)
    bard_actor = entities[intent.actor_id]

    # Decrement bardic music uses
    uses_before = bard_actor.get(EF.BARDIC_MUSIC_USES_REMAINING, 0)
    uses_after = max(0, uses_before - 1)
    bard_actor[EF.BARDIC_MUSIC_USES_REMAINING] = uses_after

    # Apply to bard + all specified allies
    affected_ids = [intent.actor_id] + [a for a in (intent.ally_ids or []) if a != intent.actor_id]
    music_rng = rng.stream("bardic_music") if hasattr(rng, "stream") else rng

    temp_hp_grants = []
    for eid in affected_ids:
        if eid not in entities:
            continue
        target = entities[eid]

        # Temp HP: 2d10 + (2 × Con mod) — no floats, all int
        _con_mod = target.get(EF.CON_MOD, 0)
        _roll1 = music_rng.randint(1, 10)
        _roll2 = music_rng.randint(1, 10)
        _temp_hp = _roll1 + _roll2 + 2 * _con_mod
        # Temp HP min 0 (edge case: negative Con mod can't make it negative)
        _temp_hp = max(0, _temp_hp)
        existing_temp = target.get(EF.HP_TEMP, 0) or 0
        target[EF.HP_TEMP] = existing_temp + _temp_hp
        temp_hp_grants.append({"entity_id": eid, "temp_hp": _temp_hp, "roll1": _roll1, "roll2": _roll2})

        # +2 competence attack (TEMPORARY_MODIFIERS — higher wins, non-stacking)
        _temp_mods = dict(target.get(EF.TEMPORARY_MODIFIERS, {}) or {})
        _existing_ig_bab = _temp_mods.get("inspire_greatness_bab", 0)
        _temp_mods["inspire_greatness_bab"] = max(_existing_ig_bab, 2)
        # +1 competence Fort save
        _existing_ig_fort = _temp_mods.get("inspire_greatness_fort", 0)
        _temp_mods["inspire_greatness_fort"] = max(_existing_ig_fort, 1)
        target[EF.TEMPORARY_MODIFIERS] = _temp_mods

        # Inspire Greatness state flags
        target[EF.INSPIRE_GREATNESS_ACTIVE] = True
        target[EF.INSPIRE_GREATNESS_ROUNDS_REMAINING] = _INSPIRE_GREATNESS_DURATION_ROUNDS
        target[EF.INSPIRE_GREATNESS_BARD_ID] = intent.actor_id

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )

    events.append(Event(
        event_id=next_event_id,
        event_type="inspire_greatness_start",
        timestamp=timestamp,
        payload={
            "actor_id": intent.actor_id,
            "affected_ids": affected_ids,
            "temp_hp_grants": temp_hp_grants,
            "attack_bonus": 2,
            "fort_bonus": 1,
            "rounds": _INSPIRE_GREATNESS_DURATION_ROUNDS,
            "uses_remaining": uses_after,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 30}],
    ))

    return events, world_state


def tick_inspire_greatness(
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Decrement INSPIRE_GREATNESS_ROUNDS_REMAINING at turn end; clear on expiry.

    On expiry: removes temp HP granted by Inspire Greatness, clears competence bonuses.
    Bard incapacitation causes immediate expiry (mirrors tick_inspire_courage pattern).
    """
    events: List[Event] = []
    entities = deepcopy(world_state.entities)
    expired_ids = []
    any_mutated = False

    for eid, entity in entities.items():
        if not entity.get(EF.INSPIRE_GREATNESS_ACTIVE, False):
            continue

        bard_id = entity.get(EF.INSPIRE_GREATNESS_BARD_ID)
        bard_incapacitated = False
        if bard_id and bard_id in entities:
            bard_incapacitated = _bard_is_incapacitated(entities[bard_id])

        rounds_left = entity.get(EF.INSPIRE_GREATNESS_ROUNDS_REMAINING, 0)
        new_rounds = max(0, rounds_left - 1)

        if new_rounds <= 0 or bard_incapacitated:
            # Expire: remove temp HP and competence bonuses
            entity[EF.INSPIRE_GREATNESS_ACTIVE] = False
            entity[EF.INSPIRE_GREATNESS_ROUNDS_REMAINING] = 0
            entity[EF.INSPIRE_GREATNESS_BARD_ID] = None
            entity[EF.HP_TEMP] = 0
            _temp_mods = dict(entity.get(EF.TEMPORARY_MODIFIERS, {}) or {})
            _temp_mods.pop("inspire_greatness_bab", None)
            _temp_mods.pop("inspire_greatness_fort", None)
            entity[EF.TEMPORARY_MODIFIERS] = _temp_mods
            expired_ids.append(eid)
            any_mutated = True
        else:
            entity[EF.INSPIRE_GREATNESS_ROUNDS_REMAINING] = new_rounds
            any_mutated = True

    if expired_ids:
        events.append(Event(
            event_id=next_event_id,
            event_type="inspire_greatness_end",
            timestamp=timestamp,
            payload={"affected_ids": expired_ids},
        ))

    if any_mutated:
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
        )

    return events, world_state