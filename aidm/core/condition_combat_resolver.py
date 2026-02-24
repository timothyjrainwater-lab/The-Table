"""Condition combat resolver — WO-ENGINE-CONDITIONS-BLIND-DEAF-001.

Implements PHB p.309-310 mechanics for four conditions:

BLINDED (PHB p.309):
- 50% miss chance on own attacks (d100 1-50 = miss).
- Opponents get +2 to attack rolls vs blinded entity.
- Blinded entity loses Dex bonus to AC.
- -2 penalty to AC (stacked with losing Dex).

DEAFENED (PHB p.310):
- 20% arcane spell failure for verbal-component spells.

ENTANGLED (PHB p.310):
- -2 attack rolls.
- -4 effective Dexterity (affects AC, Reflex saves, etc.).

CONFUSED (PHB p.309):
- d100 behavior roll at turn start:
  01–10: Attack caster/nearest ally.
  11–20: Act normally.
  21–50: Babble incoherently (lose action).
  51–70: Flee at full speed.
  71–100: Attack nearest creature.
- Cannot make AoOs except vs. current target.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import (
    ConditionType, ConditionModifiers, ConditionInstance,
)
from aidm.core.rng_protocol import RNGProvider


# ==============================================================================
# Factory functions
# ==============================================================================

def create_blinded_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Blinded condition.

    PHB p.309:
    - 50% miss chance on own attacks.
    - Opponents +2 to attack vs this entity.
    - Loses Dex to AC; -2 penalty to AC.
    """
    return ConditionInstance(
        condition_type=ConditionType.BLINDED,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier=-2,              # -2 AC penalty (PHB p.309)
            loses_dex_to_ac=True,        # Loses Dex bonus to AC
            # is_blinded flag for miss check logic handled in attack_resolver
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Blinded: 50% miss on attacks, opponents +2 to hit, -2 AC, loses Dex to AC",
    )


def create_deafened_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Deafened condition.

    PHB p.310: 20% spell failure for verbal-component spells.
    """
    return ConditionInstance(
        condition_type=ConditionType.DEAFENED,
        source=source,
        modifiers=ConditionModifiers(),  # No numeric combat modifiers
        applied_at_event_id=applied_at_event_id,
        notes="Deafened: 20% spell failure for verbal-component spells",
    )


def create_entangled_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Entangled condition.

    PHB p.310: -2 attack rolls; -4 effective Dex.
    """
    return ConditionInstance(
        condition_type=ConditionType.ENTANGLED,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-2,    # -2 attack rolls (PHB p.310)
            dex_modifier=-4,       # -4 effective Dex (PHB p.310)
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Entangled: -2 attack, -4 effective Dex",
    )


def create_confused_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Confused condition.

    PHB p.309: d100 behavior roll each turn. Cannot make AoOs except vs current target.
    """
    return ConditionInstance(
        condition_type=ConditionType.CONFUSED,
        source=source,
        modifiers=ConditionModifiers(),  # Numeric effects from behavior roll only
        applied_at_event_id=applied_at_event_id,
        notes="Confused: d100 behavior roll each turn",
    )


# ==============================================================================
# Blinded miss check
# ==============================================================================

def check_blinded_miss(
    rng: RNGProvider,
    attacker_id: str,
    next_event_id: int,
    timestamp: float,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Roll 50% miss chance for a blinded attacker.

    PHB p.309: A blinded attacker must roll d100; 1–50 = miss.
    This is checked BEFORE the attack roll (RNG consumption order).

    Args:
        rng: RNG provider (uses "combat" stream).
        attacker_id: Entity ID for event payload.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (missed: bool, events).
        If missed is True, the attack does not proceed to the d20 roll.
    """
    roll = rng.stream("combat").randint(1, 100)
    missed = roll <= 50
    events: List[Dict[str, Any]] = [{
        "event_id": next_event_id,
        "event_type": "blinded_miss_check",
        "payload": {
            "attacker_id": attacker_id,
            "d100_roll": roll,
            "missed": missed,
        },
        "timestamp": timestamp,
        "citations": [{"source_id": "681f92bc94ff", "page": 309}],
    }]
    return missed, events


# ==============================================================================
# Deafened spell failure check
# ==============================================================================

def check_deafened_spell_failure(
    rng: RNGProvider,
    caster_id: str,
    spell_name: str,
    has_verbal_component: bool,
    next_event_id: int,
    timestamp: float,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Roll 20% spell failure for a deafened caster with verbal component.

    PHB p.310: 20% arcane spell failure if deafened and spell has verbal component.

    Args:
        rng: RNG provider (uses "combat" stream).
        caster_id: Entity ID.
        spell_name: Spell being cast (for event payload).
        has_verbal_component: True if spell has V component.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (spell_failed: bool, events).
    """
    if not has_verbal_component:
        return False, []

    roll = rng.stream("combat").randint(1, 100)
    failed = roll <= 20
    events: List[Dict[str, Any]] = [{
        "event_id": next_event_id,
        "event_type": "deafened_spell_failure_check",
        "payload": {
            "caster_id": caster_id,
            "spell_name": spell_name,
            "d100_roll": roll,
            "failed": failed,
        },
        "timestamp": timestamp,
        "citations": [{"source_id": "681f92bc94ff", "page": 310}],
    }]
    return failed, events


# ==============================================================================
# Confused behavior roll
# ==============================================================================

_CONFUSED_BEHAVIORS = {
    (1, 10): "attack_caster",     # Attack caster or nearest ally
    (11, 20): "act_normally",     # Act normally
    (21, 50): "babble",           # Babble incoherently, lose action
    (51, 70): "flee",             # Flee at full speed
    (71, 100): "attack_nearest",  # Attack nearest creature
}


def roll_confused_behavior(
    rng: RNGProvider,
    confused_entity_id: str,
    next_event_id: int,
    timestamp: float,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Roll d100 to determine confused entity's behavior for this turn.

    PHB p.309.

    Args:
        rng: RNG provider (uses "combat" stream).
        confused_entity_id: Entity ID.
        next_event_id: Starting event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (behavior: str, events).
        Behavior is one of: "attack_caster", "act_normally", "babble",
        "flee", "attack_nearest".
    """
    roll = rng.stream("combat").randint(1, 100)
    behavior = "act_normally"
    for (lo, hi), beh in _CONFUSED_BEHAVIORS.items():
        if lo <= roll <= hi:
            behavior = beh
            break

    events: List[Dict[str, Any]] = [{
        "event_id": next_event_id,
        "event_type": "confused_behavior_roll",
        "payload": {
            "entity_id": confused_entity_id,
            "d100_roll": roll,
            "behavior": behavior,
        },
        "timestamp": timestamp,
        "citations": [{"source_id": "681f92bc94ff", "page": 309}],
    }]
    return behavior, events


# ==============================================================================
# Helpers: condition presence checks
# ==============================================================================

def is_blinded(world_state_or_entity, entity_id: Optional[str] = None) -> bool:
    """Return True if entity has the BLINDED condition.

    Accepts either a WorldState (with entity_id) or a bare entity dict.
    """
    if entity_id is not None:
        # WorldState path
        entity = world_state_or_entity.entities.get(entity_id, {})
    else:
        entity = world_state_or_entity
    conditions = entity.get(EF.CONDITIONS, {})
    if isinstance(conditions, dict):
        return ConditionType.BLINDED.value in conditions
    return False


def is_deafened(world_state_or_entity, entity_id: Optional[str] = None) -> bool:
    """Return True if entity has the DEAFENED condition."""
    if entity_id is not None:
        entity = world_state_or_entity.entities.get(entity_id, {})
    else:
        entity = world_state_or_entity
    conditions = entity.get(EF.CONDITIONS, {})
    if isinstance(conditions, dict):
        return ConditionType.DEAFENED.value in conditions
    return False


def is_confused(world_state_or_entity, entity_id: Optional[str] = None) -> bool:
    """Return True if entity has the CONFUSED condition."""
    if entity_id is not None:
        entity = world_state_or_entity.entities.get(entity_id, {})
    else:
        entity = world_state_or_entity
    conditions = entity.get(EF.CONDITIONS, {})
    if isinstance(conditions, dict):
        return ConditionType.CONFUSED.value in conditions
    return False
