"""Poison and disease resolver — WO-ENGINE-POISON-DISEASE-001.

Implements PHB p.292 poison and disease mechanics.

POISON (PHB p.292):
- Initial Fort save when first hit (or exposure).
- Secondary save at 1 minute (10 rounds) later.
- Both saves use the same DC.
- Each failed save deals ability damage (from poison's stat block).
- Paladin 3+: immune to all poisons.
- Dwarf: +2 racial bonus vs poison (EF.SAVE_BONUS_POISON).
- Undead / constructs: immune to poison.

DISEASE (PHB p.292):
- Incubation period (days or hours) before save required.
- Repeating saves at specified interval.
- Two consecutive successful saves cure the disease.
- Different diseases deal different damage (ability or HP).

Active poison instance dict shape:
{
    "poison_id": str,           # e.g. "giant_wasp_poison"
    "dc": int,                  # Fort save DC
    "initial_done": bool,       # True after first save resolved
    "secondary_due_round": int, # Round when secondary save fires
    "initial_ability": str,     # e.g. "str"
    "initial_amount": int,      # ability damage on failed initial save
    "secondary_ability": str,
    "secondary_amount": int,
}

Active disease instance dict shape:
{
    "disease_id": str,
    "dc": int,
    "incubation_rounds": int,   # rounds until first save required
    "interval_rounds": int,     # rounds between subsequent saves
    "next_save_round": int,     # round when next save fires
    "consecutive_successes": int,
    "damage_ability": str,      # ability damaged on fail, or "hp"
    "damage_amount": int,
}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import ConditionType, ConditionInstance
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider


# ==============================================================================
# Immunity checks
# ==============================================================================

def is_immune_to_poison(entity: Dict[str, Any]) -> bool:
    """Return True if entity is immune to poison.

    PHB p.292 / p.294:
    - Undead: immune (EF.IS_UNDEAD).
    - Monk level 11+: immune — Diamond Body (PHB p.42).
    - Druid level 9+: immune — Venom Immunity (PHB p.38).
    """
    if entity.get(EF.IS_UNDEAD, False):
        return True
    class_levels: Dict[str, int] = entity.get(EF.CLASS_LEVELS, {})
    # WO-ENGINE-CLASS-IMMUNITY-001: Diamond Body (PHB p.42)
    if class_levels.get("monk", 0) >= 11:
        return True
    # WO-ENGINE-CLASS-IMMUNITY-001: Venom Immunity (PHB p.38)
    if class_levels.get("druid", 0) >= 9:
        return True
    # WO-ENGINE-CONDITION-IMMUNE-TO-WIRE-001: Scan ConditionInstance.immune_to (PHB p.311)
    for _cond_dict in (entity.get(EF.CONDITIONS, {}) or {}).values():
        if isinstance(_cond_dict, dict):
            _ci = ConditionInstance.from_dict(_cond_dict)
            if "poison" in _ci.immune_to:
                return True
    return False


def _get_poison_save_bonus(entity: Dict[str, Any]) -> int:
    """Return entity's bonus to poison saves (e.g. dwarf +2)."""
    return entity.get(EF.SAVE_BONUS_POISON, 0)


# ==============================================================================
# Poison mechanics
# ==============================================================================

def apply_poison(
    entity: Dict[str, Any],
    target_id: str,
    source_id: str,
    poison_stat: Dict[str, Any],
    current_round: int,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Apply an initial poison exposure and roll the first Fort save.

    Args:
        entity: Mutable target entity dict.
        target_id: Entity ID.
        source_id: Attacker / source ID.
        poison_stat: Dict with keys: poison_id, dc, initial_ability,
                     initial_amount, secondary_ability, secondary_amount.
        current_round: Current combat round number.
        rng: RNG provider.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated entity, events).
    """
    events: List[Dict[str, Any]] = []
    eid = next_event_id

    if is_immune_to_poison(entity):
        # WO-ENGINE-CLASS-IMMUNITY-001: Identify reason for poison immunity
        _reason = "unknown"
        if entity.get(EF.IS_UNDEAD, False):
            _reason = "undead"
        elif entity.get(EF.CLASS_LEVELS, {}).get("monk", 0) >= 11:
            _reason = "diamond_body"
        elif entity.get(EF.CLASS_LEVELS, {}).get("druid", 0) >= 9:
            _reason = "venom_immunity"
        events.append({
            "event_id": eid,
            "event_type": "poison_immune",
            "payload": {
                "target_id": target_id,
                "poison_id": poison_stat.get("poison_id"),
                "reason": _reason,
            },
            "timestamp": timestamp,
        })
        return entity, events

    dc = poison_stat["dc"]
    fort_base = entity.get(EF.SAVE_FORT, 0)
    # WO-AE-WO1: EF.SAVE_FORT is Type 2 (base+CON already included). Strip redundant CON.
    bonus = _get_poison_save_bonus(entity)
    roll = rng.stream("combat").randint(1, 20)
    total = roll + fort_base + bonus
    saved = total >= dc

    events.append({
        "event_id": eid,
        "event_type": "poison_save_initial",
        "payload": {
            "target_id": target_id,
            "source_id": source_id,
            "poison_id": poison_stat.get("poison_id"),
            "dc": dc,
            "roll": roll,
            "total": total,
            "saved": saved,
        },
        "timestamp": timestamp,
        "citations": [{"source_id": "681f92bc94ff", "page": 292}],
    })
    eid += 1

    if not saved:
        # Apply initial ability damage
        ability = poison_stat["initial_ability"]
        amount = poison_stat["initial_amount"]
        from aidm.core.ability_damage_resolver import _DAMAGE_FIELD
        field = _DAMAGE_FIELD[ability]
        old_val = entity.get(field, 0)
        entity[field] = old_val + amount
        events.append({
            "event_id": eid,
            "event_type": "ability_damaged",
            "payload": {
                "target_id": target_id,
                "source_id": f"poison_{poison_stat.get('poison_id')}",
                "ability": ability,
                "amount": amount,
                "old_value": old_val,
                "new_value": entity[field],
                "is_drain": False,
            },
            "timestamp": timestamp + 0.01,
        })
        eid += 1

    # Queue secondary save (10 rounds later)
    active_poisons = list(entity.get(EF.ACTIVE_POISONS, []))
    active_poisons.append({
        "poison_id": poison_stat.get("poison_id"),
        "dc": dc,
        "initial_done": True,
        "secondary_due_round": current_round + 10,
        "secondary_ability": poison_stat["secondary_ability"],
        "secondary_amount": poison_stat["secondary_amount"],
    })
    entity[EF.ACTIVE_POISONS] = active_poisons

    return entity, events


def process_poison_secondaries(
    entity: Dict[str, Any],
    target_id: str,
    current_round: int,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Process any secondary poison saves due this round.

    Called at end-of-round from play_loop.py tick.

    Args:
        entity: Mutable entity dict.
        target_id: Entity ID.
        current_round: Current round number.
        rng: RNG provider.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated entity, events).
    """
    events: List[Dict[str, Any]] = []
    eid = next_event_id

    active_poisons = entity.get(EF.ACTIVE_POISONS, [])
    remaining_poisons = []

    for poison in active_poisons:
        if poison.get("secondary_due_round", 9999) > current_round:
            remaining_poisons.append(poison)
            continue

        # Secondary save is due
        dc = poison["dc"]
        fort_base = entity.get(EF.SAVE_FORT, 0)
        # WO-AE-WO1: EF.SAVE_FORT is Type 2 (base+CON already included). Strip redundant CON.
        bonus = _get_poison_save_bonus(entity)
        roll = rng.stream("combat").randint(1, 20)
        total = roll + fort_base + bonus
        saved = total >= dc

        events.append({
            "event_id": eid,
            "event_type": "poison_save_secondary",
            "payload": {
                "target_id": target_id,
                "poison_id": poison.get("poison_id"),
                "dc": dc,
                "roll": roll,
                "total": total,
                "saved": saved,
            },
            "timestamp": timestamp,
            "citations": [{"source_id": "681f92bc94ff", "page": 292}],
        })
        eid += 1

        if not saved:
            ability = poison["secondary_ability"]
            amount = poison["secondary_amount"]
            from aidm.core.ability_damage_resolver import _DAMAGE_FIELD
            field = _DAMAGE_FIELD[ability]
            old_val = entity.get(field, 0)
            entity[field] = old_val + amount
            events.append({
                "event_id": eid,
                "event_type": "ability_damaged",
                "payload": {
                    "target_id": target_id,
                    "source_id": f"poison_{poison.get('poison_id')}_secondary",
                    "ability": ability,
                    "amount": amount,
                    "old_value": old_val,
                    "new_value": entity[field],
                    "is_drain": False,
                },
                "timestamp": timestamp + 0.01,
            })
            eid += 1
        # Secondary is done — don't re-add to remaining

    entity[EF.ACTIVE_POISONS] = remaining_poisons
    return entity, events


# ==============================================================================
# Disease mechanics
# ==============================================================================

def apply_disease_exposure(
    entity: Dict[str, Any],
    target_id: str,
    source_id: str,
    disease_stat: Dict[str, Any],
    current_round: int,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Expose entity to a disease (immediate save vs. contraction).

    PHB p.292: Initial Fort save vs disease DC. On failure the disease
    is contracted and incubation begins.

    Args:
        entity: Mutable entity dict.
        target_id: Entity ID.
        source_id: Source of exposure.
        disease_stat: Dict with keys: disease_id, dc, incubation_rounds,
                      interval_rounds, damage_ability, damage_amount.
        current_round: Current round.
        rng: RNG provider.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated entity, events).
    """
    events: List[Dict[str, Any]] = []
    eid = next_event_id

    # WO-ENGINE-DIVINE-HEALTH-001: Paladin Divine Health — immune to all diseases at level 3+
    # PHB p.44: "Beginning at 3rd level, a paladin is immune to all diseases,
    # including supernatural and magical diseases."
    _paladin_level = entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
    if _paladin_level >= 3:
        events.append({
            "event_id": eid,
            "event_type": "disease_immunity",
            "payload": {
                "target_id": target_id,
                "disease_id": disease_stat.get("disease_id"),
                "reason": "divine_health",
            },
            "timestamp": timestamp,
            "citations": [{"source_id": "681f92bc94ff", "page": 44}],
        })
        return entity, events

    # WO-ENGINE-CLASS-IMMUNITY-001: Monk Purity of Body — immune to all diseases at level 5+
    # PHB p.42: "At 5th level, a monk gains immunity to all diseases except for
    # supernatural and magical diseases."
    # Note: standard reading (same scope as Divine Health) — all diseases.
    _monk_level_pb = entity.get(EF.CLASS_LEVELS, {}).get("monk", 0)
    if _monk_level_pb >= 5:
        events.append({
            "event_id": eid,
            "event_type": "disease_immunity",
            "payload": {
                "target_id": target_id,
                "disease_id": disease_stat.get("disease_id"),
                "reason": "purity_of_body",
            },
            "timestamp": timestamp,
            "citations": [{"source_id": "681f92bc94ff", "page": 42}],
        })
        return entity, events

    # WO-ENGINE-CONDITION-IMMUNE-TO-WIRE-001: Scan ConditionInstance.immune_to for "disease" (PHB p.311)
    for _dis_cond_dict in (entity.get(EF.CONDITIONS, {}) or {}).values():
        if isinstance(_dis_cond_dict, dict):
            _dis_ci = ConditionInstance.from_dict(_dis_cond_dict)
            if "disease" in _dis_ci.immune_to:
                events.append({
                    "event_id": eid,
                    "event_type": "disease_immunity",
                    "payload": {
                        "target_id": target_id,
                        "disease_id": disease_stat.get("disease_id"),
                        "reason": "condition_immune_to",
                    },
                    "timestamp": timestamp,
                    "citations": [{"source_id": "681f92bc94ff", "page": 311}],
                })
                return entity, events

    dc = disease_stat["dc"]
    fort_base = entity.get(EF.SAVE_FORT, 0)
    # WO-AE-WO1: EF.SAVE_FORT is Type 2 (base+CON already included). Strip redundant CON.
    roll = rng.stream("combat").randint(1, 20)
    total = roll + fort_base
    saved = total >= dc

    events.append({
        "event_id": eid,
        "event_type": "disease_exposure_save",
        "payload": {
            "target_id": target_id,
            "source_id": source_id,
            "disease_id": disease_stat.get("disease_id"),
            "dc": dc,
            "roll": roll,
            "total": total,
            "saved": saved,
        },
        "timestamp": timestamp,
        "citations": [{"source_id": "681f92bc94ff", "page": 292}],
    })
    eid += 1

    if not saved:
        # Contract disease — first save after incubation
        incubation = disease_stat.get("incubation_rounds", 0)
        active_diseases = list(entity.get(EF.ACTIVE_DISEASES, []))
        active_diseases.append({
            "disease_id": disease_stat.get("disease_id"),
            "dc": dc,
            "interval_rounds": disease_stat.get("interval_rounds", 1),
            "next_save_round": current_round + max(1, incubation),
            "consecutive_successes": 0,
            "damage_ability": disease_stat.get("damage_ability", "str"),
            "damage_amount": disease_stat.get("damage_amount", 1),
        })
        entity[EF.ACTIVE_DISEASES] = active_diseases

        events.append({
            "event_id": eid,
            "event_type": "disease_contracted",
            "payload": {
                "target_id": target_id,
                "disease_id": disease_stat.get("disease_id"),
                "first_save_round": current_round + max(1, incubation),
            },
            "timestamp": timestamp + 0.01,
        })
        eid += 1

    return entity, events


def process_disease_ticks(
    entity: Dict[str, Any],
    target_id: str,
    current_round: int,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Process active disease saves due this round.

    PHB p.292: Two consecutive successful saves cure the disease.

    Args:
        entity: Mutable entity dict.
        target_id: Entity ID.
        current_round: Current round.
        rng: RNG provider.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (updated entity, events).
    """
    events: List[Dict[str, Any]] = []
    eid = next_event_id

    # WO-ENGINE-DIVINE-HEALTH-001: Belt-and-suspenders — clear diseases on paladin 3+
    # Handles any disease contracted before the paladin reached level 3.
    _paladin_level = entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
    if _paladin_level >= 3 and entity.get(EF.ACTIVE_DISEASES):
        entity[EF.ACTIVE_DISEASES] = []
        return entity, events

    active_diseases = entity.get(EF.ACTIVE_DISEASES, [])
    remaining_diseases = []

    for disease in active_diseases:
        if disease.get("next_save_round", 9999) > current_round:
            remaining_diseases.append(disease)
            continue

        dc = disease["dc"]
        fort_base = entity.get(EF.SAVE_FORT, 0)
        # WO-AE-WO1: EF.SAVE_FORT is Type 2 (base+CON already included). Strip redundant CON.
        roll = rng.stream("combat").randint(1, 20)
        total = roll + fort_base
        saved = total >= dc

        disease["consecutive_successes"] = disease.get("consecutive_successes", 0) + (1 if saved else 0)
        if not saved:
            disease["consecutive_successes"] = 0

        events.append({
            "event_id": eid,
            "event_type": "disease_save",
            "payload": {
                "target_id": target_id,
                "disease_id": disease.get("disease_id"),
                "dc": dc,
                "roll": roll,
                "total": total,
                "saved": saved,
                "consecutive_successes": disease["consecutive_successes"],
            },
            "timestamp": timestamp,
            "citations": [{"source_id": "681f92bc94ff", "page": 292}],
        })
        eid += 1

        if disease["consecutive_successes"] >= 2:
            # Cured!
            events.append({
                "event_id": eid,
                "event_type": "disease_cured",
                "payload": {
                    "target_id": target_id,
                    "disease_id": disease.get("disease_id"),
                },
                "timestamp": timestamp + 0.01,
            })
            eid += 1
            # Don't re-add to remaining_diseases
            continue

        if not saved:
            # Apply damage
            ability = disease["damage_ability"]
            amount = disease["damage_amount"]
            if ability == "hp":
                old_hp = entity.get(EF.HP_CURRENT, 0)
                entity[EF.HP_CURRENT] = old_hp - amount
                events.append({
                    "event_id": eid,
                    "event_type": "hp_changed",
                    "payload": {
                        "entity_id": target_id,
                        "old_hp": old_hp,
                        "new_hp": entity[EF.HP_CURRENT],
                        "cause": f"disease_{disease.get('disease_id')}",
                    },
                    "timestamp": timestamp + 0.02,
                })
            else:
                from aidm.core.ability_damage_resolver import _DAMAGE_FIELD
                field = _DAMAGE_FIELD[ability]
                old_val = entity.get(field, 0)
                entity[field] = old_val + amount
                events.append({
                    "event_id": eid,
                    "event_type": "ability_damaged",
                    "payload": {
                        "target_id": target_id,
                        "source_id": f"disease_{disease.get('disease_id')}",
                        "ability": ability,
                        "amount": amount,
                        "old_value": old_val,
                        "new_value": entity[field],
                        "is_drain": False,
                    },
                    "timestamp": timestamp + 0.02,
                })
            eid += 1

        # Schedule next save
        disease["next_save_round"] = current_round + disease.get("interval_rounds", 1)
        remaining_diseases.append(disease)

    entity[EF.ACTIVE_DISEASES] = remaining_diseases
    return entity, events
