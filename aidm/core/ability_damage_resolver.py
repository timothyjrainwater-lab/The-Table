"""Ability damage and drain resolver — WO-ENGINE-ABILITY-DAMAGE-001.

Implements PHB p.215 ability score damage and drain mechanics:
- Ability damage: temporary, heals 1 point per affected ability per overnight rest.
- Ability drain: permanent, does not heal naturally.

Effective score = base_score - damage - drain (minimum 0 for most abilities,
minimum 1 for CON — entity dies if CON drains to 0).

Modifier derivation: (effective_score - 10) // 2 (Python integer division).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import AbilityDamageIntent
from aidm.core.state import WorldState


# PHB p.215: ability field names
_ABILITY_BASE = {
    "str": EF.STR_MOD,
    "dex": EF.DEX_MOD,
    "con": EF.CON_MOD,
    "int": EF.INT_MOD,
    "wis": EF.WIS_MOD,
    "cha": EF.CHA_MOD,
}

_DAMAGE_FIELD = {
    "str": EF.STR_DAMAGE,
    "dex": EF.DEX_DAMAGE,
    "con": EF.CON_DAMAGE,
    "int": EF.INT_DAMAGE,
    "wis": EF.WIS_DAMAGE,
    "cha": EF.CHA_DAMAGE,
}

_DRAIN_FIELD = {
    "str": EF.STR_DRAIN,
    "dex": EF.DEX_DRAIN,
    "con": EF.CON_DRAIN,
    "int": EF.INT_DRAIN,
    "wis": EF.WIS_DRAIN,
    "cha": EF.CHA_DRAIN,
}


def get_effective_score(entity: Dict[str, Any], ability: str) -> int:
    """Return effective ability score after applying damage and drain.

    PHB p.215: effective = base - damage - drain, minimum 0 (min 1 for CON
    to avoid instant death until actual CON drain check).

    Args:
        entity: Entity dict.
        ability: One of "str", "dex", "con", "int", "wis", "cha".

    Returns:
        Effective ability score as integer.
    """
    # Derive base score from modifier (modifier = (score - 10) // 2)
    # We reconstruct score as 10 + mod*2 (rounded down from chargen value)
    # Alternatively, some entities store a base_stats dict.
    base_stats = entity.get(EF.BASE_STATS, {})
    score_key = ability + "_score"  # e.g. "str_score"
    if score_key in base_stats:
        base = base_stats[score_key]
    else:
        # Fall back: reconstruct from stored modifier (mod = (score-10)//2 → score ≈ 10+2*mod)
        mod = entity.get(_ABILITY_BASE[ability], 0)
        base = 10 + mod * 2

    damage = entity.get(_DAMAGE_FIELD[ability], 0)
    drain = entity.get(_DRAIN_FIELD[ability], 0)
    return max(0, base - damage - drain)


def get_ability_modifier(entity: Dict[str, Any], ability: str) -> int:
    """Return ability modifier derived from effective score.

    modifier = (effective_score - 10) // 2

    Args:
        entity: Entity dict.
        ability: One of "str", "dex", "con", "int", "wis", "cha".

    Returns:
        Effective ability modifier as integer.
    """
    score = get_effective_score(entity, ability)
    return (score - 10) // 2


def apply_ability_damage(
    entity: Dict[str, Any],
    ability: str,
    amount: int,
    is_drain: bool,
    target_id: str,
    source_id: str,
    next_event_id: int,
    timestamp: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Apply ability damage or drain to an entity.

    PHB p.215: Ability damage accumulates in the damage field (heals on rest).
    Drain accumulates in the drain field (permanent).

    If CON is drained to 0 or effective CON reaches 0, entity dies.

    Args:
        entity: Mutable entity dict (modified in-place).
        ability: Ability key ("str", "dex", "con", "int", "wis", "cha").
        amount: Points of damage/drain to apply.
        is_drain: True for permanent drain; False for temporary damage.
        target_id: Entity ID (for events).
        source_id: Source entity ID (for events).
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated entity dict, list of events).
    """
    events: List[Dict[str, Any]] = []
    field = _DRAIN_FIELD[ability] if is_drain else _DAMAGE_FIELD[ability]
    old_value = entity.get(field, 0)
    new_value = old_value + amount
    entity[field] = new_value

    event_type = "ability_drained" if is_drain else "ability_damaged"
    events.append({
        "event_id": next_event_id,
        "event_type": event_type,
        "payload": {
            "target_id": target_id,
            "source_id": source_id,
            "ability": ability,
            "amount": amount,
            "old_value": old_value,
            "new_value": new_value,
            "is_drain": is_drain,
            "effective_score": get_effective_score(entity, ability),
        },
        "timestamp": timestamp,
    })
    next_event_id += 1

    # PHB p.215: CON drain to 0 (or effective CON 0) = death
    if ability == "con" and get_effective_score(entity, "con") <= 0:
        entity[EF.DEFEATED] = True
        events.append({
            "event_id": next_event_id,
            "event_type": "entity_defeated",
            "payload": {
                "entity_id": target_id,
                "cause": "con_drain",
            },
            "timestamp": timestamp + 0.01,
        })
        next_event_id += 1

    return entity, events


def heal_ability_damage(
    entity: Dict[str, Any],
    ability: str,
    amount: int,
    target_id: str,
    next_event_id: int,
    timestamp: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Heal ability damage (not drain) by the given amount.

    PHB p.215: Natural healing restores 1 point per ability per overnight rest.
    This function is the generic form; the rest resolver calls it per-ability.

    Args:
        entity: Mutable entity dict.
        ability: Ability key.
        amount: Points to restore (damage only; drain cannot be healed naturally).
        target_id: Entity ID.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated entity, list of events).
    """
    events: List[Dict[str, Any]] = []
    damage_field = _DAMAGE_FIELD[ability]
    old_damage = entity.get(damage_field, 0)
    if old_damage <= 0:
        return entity, events  # Nothing to heal

    healed = min(amount, old_damage)
    entity[damage_field] = old_damage - healed

    events.append({
        "event_id": next_event_id,
        "event_type": "ability_damage_healed",
        "payload": {
            "target_id": target_id,
            "ability": ability,
            "amount_healed": healed,
            "remaining_damage": entity[damage_field],
            "effective_score": get_effective_score(entity, ability),
        },
        "timestamp": timestamp,
    })
    return entity, events


def apply_ability_damage_events(
    world_state: WorldState,
    events: List[Dict[str, Any]],
) -> WorldState:
    """Apply ability_damaged / ability_drained events to world state.

    Reads event payloads and writes ability damage/drain fields to entity dicts.
    No-op for other event types.

    Args:
        world_state: Current world state.
        events: Event list from ability_damage_resolver.

    Returns:
        Updated WorldState.
    """
    from copy import deepcopy

    entities = deepcopy(world_state.entities)
    for ev in events:
        if ev["event_type"] not in ("ability_damaged", "ability_drained"):
            continue
        payload = ev["payload"]
        target_id = payload["target_id"]
        if target_id not in entities:
            continue
        ability = payload["ability"]
        is_drain = payload["is_drain"]
        field = _DRAIN_FIELD[ability] if is_drain else _DAMAGE_FIELD[ability]
        entities[target_id][field] = payload["new_value"]

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
    )


def expire_ability_damage_regen(
    entity: Dict[str, Any],
    target_id: str,
    next_event_id: int,
    timestamp: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Heal 1 point of each ability's damage on overnight rest (PHB p.215).

    Called by rest_resolver for overnight/full_day rests.

    Args:
        entity: Mutable entity dict.
        target_id: Entity ID (for events).
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated entity, list of events).
    """
    all_events: List[Dict[str, Any]] = []
    eid = next_event_id
    for ability in ("str", "dex", "con", "int", "wis", "cha"):
        entity, evs = heal_ability_damage(entity, ability, 1, target_id, eid, timestamp)
        all_events.extend(evs)
        eid += len(evs)
    return entity, all_events
