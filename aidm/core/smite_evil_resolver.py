"""Paladin Smite Evil runtime resolver -- WO-ENGINE-SMITE-EVIL-001.

PHB p.44: +CHA mod attack bonus, +paladin level damage bonus on a single attack.
Declare before attack roll. Use consumed even if target not evil.
"""

import dataclasses
from copy import deepcopy
from typing import List, Optional, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


def _has_paladin_feature(actor: dict) -> bool:
    class_levels = actor.get(EF.CLASS_LEVELS, {}) or {}
    if isinstance(class_levels, dict):
        return class_levels.get("paladin", 0) >= 1
    return False


def _get_paladin_level(actor: dict) -> int:
    class_levels = actor.get(EF.CLASS_LEVELS, {}) or {}
    if isinstance(class_levels, dict):
        return class_levels.get("paladin", 0)
    return 0


def validate_smite(actor: dict, world_state: WorldState) -> Optional[str]:
    """Validate smite preconditions. Returns error reason or None."""
    if not _has_paladin_feature(actor):
        return "not_a_paladin"
    if actor.get(EF.SMITE_USES_REMAINING, 0) <= 0:
        return "no_smite_uses"
    return None


def resolve_smite_evil(
    intent,
    world_state: WorldState,
    rng,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve Paladin Smite Evil.

    Returns (events, updated_world_state). The world_state returned has
    SMITE_USES_REMAINING decremented. HP events from the underlying attack
    are carried in the events list (same as normal attack flow).
    """
    from aidm.core.attack_resolver import resolve_attack

    events: List[Event] = []

    actor = world_state.entities.get(intent.actor_id, {})

    # Validate
    err = validate_smite(actor, world_state)
    if err:
        events.append(Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "intent_type": "SmiteEvilIntent",
                "reason": err,
            },
        ))
        return events, world_state

    # Decrement uses
    entities = deepcopy(world_state.entities)
    uses_before = entities[intent.actor_id].get(EF.SMITE_USES_REMAINING, 0)
    uses_after = max(0, uses_before - 1)
    entities[intent.actor_id][EF.SMITE_USES_REMAINING] = uses_after
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )
    actor = world_state.entities[intent.actor_id]

    # Compute bonuses
    cha_mod = actor.get(EF.CHA_MOD, 0)
    paladin_level = _get_paladin_level(actor)
    attack_bonus_delta = cha_mod if intent.target_is_evil else 0
    damage_bonus_delta = paladin_level if intent.target_is_evil else 0

    # Emit smite_declared
    events.append(Event(
        event_id=next_event_id,
        event_type="smite_declared",
        timestamp=timestamp,
        payload={
            "actor_id": intent.actor_id,
            "target_id": intent.target_id,
            "target_is_evil": intent.target_is_evil,
            "attack_bonus": attack_bonus_delta,
            "damage_bonus": damage_bonus_delta,
            "smite_uses_remaining": uses_after,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 44}],
    ))
    next_event_id += 1

    # Build smite-modified weapon (damage_bonus baked in)
    weapon = intent.weapon
    if isinstance(weapon, dict):
        weapon = Weapon(
            damage_dice=weapon.get("damage_dice", "1d8"),
            damage_bonus=weapon.get("damage_bonus", 0) + damage_bonus_delta,
            damage_type=weapon.get("damage_type", "slashing"),
            critical_multiplier=weapon.get("critical_multiplier", 2),
            critical_range=weapon.get("critical_range", 20),
            is_two_handed=weapon.get("is_two_handed", False),
            grip=weapon.get("grip", "one-handed"),
            weapon_type=weapon.get("weapon_type", "one-handed"),
            range_increment=weapon.get("range_increment", 0),
        )
    else:
        weapon = dataclasses.replace(weapon, damage_bonus=weapon.damage_bonus + damage_bonus_delta)

    # Build modified AttackIntent with smite attack bonus added
    base_attack_bonus = actor.get(EF.ATTACK_BONUS, actor.get(EF.BAB, 0))
    attack_intent = AttackIntent(
        attacker_id=intent.actor_id,
        target_id=intent.target_id,
        weapon=weapon,
        attack_bonus=base_attack_bonus + attack_bonus_delta,
    )

    # Resolve the underlying attack
    attack_events = resolve_attack(
        intent=attack_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=next_event_id,
        timestamp=timestamp + 0.1,
    )
    events.extend(attack_events)

    return events, world_state
