"""Natural attack resolver for D&D 3.5e.

Resolves attacks made with natural weapons (bite, claw, slam, talon, etc.).
Used by Wild Shape forms, monsters, and any entity with EF.NATURAL_ATTACKS set.

Key design: delegates to a shared _resolve_single_attack() function that is also
called by attack_resolver.resolve_attack(). The EQUIPMENT_MELDED guard lives only
in resolve_attack — natural attacks bypass it cleanly (PHB p.36).

WO-ENGINE-NATURAL-ATTACK-001
"""

from copy import deepcopy
from typing import List, Optional, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.attack import Weapon, AttackIntent
from aidm.schemas.entity_fields import EF


def validate_natural_attack(
    actor: dict,
    attack_name: str,
    target_id: str,
    world_state: WorldState,
) -> Optional[str]:
    """Validate a natural attack request.

    Returns an error reason string on failure, or None if valid.
    """
    natural_attacks = actor.get(EF.NATURAL_ATTACKS, []) or []
    if not natural_attacks:
        return "no_natural_attacks"
    names = [a.get("name", "") for a in natural_attacks]
    if attack_name not in names:
        return "unknown_natural_attack"
    if target_id not in world_state.entities:
        return "target_not_found"
    target = world_state.entities[target_id]
    if target.get(EF.DEFEATED, False):
        return "target_already_defeated"
    return None


def _build_weapon_from_natural_attack(attack_dict: dict) -> Weapon:
    """Convert a NATURAL_ATTACKS list entry to a Weapon dataclass.

    attack_dict keys: name, damage (dice expr), damage_type.
    """
    damage_dice = attack_dict.get("damage") or attack_dict.get("damage_dice", "1d4")
    damage_type = attack_dict.get("damage_type", "piercing")
    return Weapon(
        damage_dice=damage_dice,
        damage_bonus=0,
        damage_type=damage_type,
        critical_multiplier=2,
        critical_range=20,
        weapon_type="natural",
        grip="one-handed",
        is_two_handed=False,
    )


def resolve_natural_attack(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve a natural attack (bite, claw, talon, etc.).

    Looks up the named attack in actor's EF.NATURAL_ATTACKS, builds a Weapon,
    then delegates to attack_resolver.resolve_attack() which handles all the
    standard attack roll, damage, DR, and death-transition logic.

    The EQUIPMENT_MELDED guard in resolve_attack is bypassed because this
    function builds an AttackIntent from a natural weapon, not a manufactured one.
    resolve_attack checks EQUIPMENT_MELDED before the legality/condition path,
    so we patch around it by temporarily clearing EQUIPMENT_MELDED on the
    deepcopy of world_state we pass in.

    PHB p.36: Equipment melds into form — natural attacks are not equipment.

    Returns:
        (events, world_state_unchanged) — world_state is not mutated here;
        the caller (play_loop) applies hp_changed events via apply_attack_events.
    """
    from aidm.core.attack_resolver import resolve_attack

    events: List[Event] = []

    actor_id: str = intent.attacker_id
    target_id: str = intent.target_id
    attack_name: str = intent.attack_name

    actor = world_state.entities.get(actor_id, {})

    error = validate_natural_attack(actor, attack_name, target_id, world_state)
    if error:
        events.append(Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "actor_id": actor_id,
                "target_id": target_id,
                "intent_type": "natural_attack",
                "reason": error,
            },
        ))
        return events, world_state

    # Find the matching attack entry
    natural_attacks = actor.get(EF.NATURAL_ATTACKS, []) or []
    attack_dict = next(a for a in natural_attacks if a.get("name") == attack_name)

    weapon = _build_weapon_from_natural_attack(attack_dict)

    # Build AttackIntent for delegation to resolve_attack
    attack_intent = AttackIntent(
        attacker_id=actor_id,
        target_id=target_id,
        weapon=weapon,
        attack_bonus=intent.attack_bonus,
    )

    # Temporarily clear EQUIPMENT_MELDED on the deepcopy so resolve_attack
    # does not block this natural attack (PHB p.36: natural attacks are not equipment)
    ws_for_attack = deepcopy(world_state)
    ws_for_attack.entities[actor_id] = dict(ws_for_attack.entities[actor_id])
    ws_for_attack.entities[actor_id][EF.EQUIPMENT_MELDED] = False

    attack_events = resolve_attack(
        intent=attack_intent,
        world_state=ws_for_attack,
        rng=rng,
        next_event_id=next_event_id,
        timestamp=timestamp,
    )
    events.extend(attack_events)

    return events, world_state
