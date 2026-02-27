"""Natural attack resolver for D&D 3.5e.

Resolves attacks made with natural weapons (bite, claw, slam, talon, etc.).
Used by Wild Shape forms, monsters, and any entity with EF.NATURAL_ATTACKS set.

Key design: delegates to a shared _resolve_single_attack() function that is also
called by attack_resolver.resolve_attack(). The EQUIPMENT_MELDED guard lives only
in resolve_attack — natural attacks bypass it cleanly (PHB p.36).

WO-ENGINE-NATURAL-ATTACK-001
WO-ENGINE-MULTIATTACK-001
WO-ENGINE-IMPROVED-NATURAL-ATTACK-001
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


def _build_weapon_from_natural_attack(attack_dict: dict, damage_dice_override: Optional[str] = None) -> Weapon:
    """Convert a NATURAL_ATTACKS list entry to a Weapon dataclass.

    attack_dict keys: name, damage (dice expr), damage_type.
    damage_dice_override: if provided, use this instead of attack_dict damage (for INA upgrade).
    """
    damage_dice = damage_dice_override or attack_dict.get("damage") or attack_dict.get("damage_dice", "1d4")
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


# Improved Natural Attack: damage die progression table (PHB p.96)
_INA_STEP_TABLE = ["1d2", "1d3", "1d4", "1d6", "1d8", "2d6", "3d6", "4d6", "6d6", "8d6", "12d6"]


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

    # ── Multiattack feat: secondary natural attack penalty (PHB p.98) ─────────
    # is_primary defaults True if not specified in attack_dict.
    # Secondary penalty: −5 normally, −2 with Multiattack feat (PHB p.134).
    is_primary = attack_dict.get("is_primary", True)
    if is_primary:
        secondary_adjustment = 0
    else:
        feats = actor.get(EF.FEATS, [])
        if "multiattack" in feats:
            secondary_adjustment = -2  # PHB p.98: Multiattack reduces secondary penalty
        else:
            secondary_adjustment = -5  # PHB p.134: default secondary natural attack penalty

    # ── Improved Natural Attack: damage die upgrade (PHB p.96) ───────────────
    # attack_type defaults to attack name (e.g., "bite", "claw")
    attack_type = attack_dict.get("attack_type", attack_dict.get("name", ""))
    ina_key = f"improved_natural_attack_{attack_type}"
    base_damage_dice = attack_dict.get("damage") or attack_dict.get("damage_dice", "1d4")
    feats = actor.get(EF.FEATS, [])
    if ina_key in feats:
        current_idx = _INA_STEP_TABLE.index(base_damage_dice) if base_damage_dice in _INA_STEP_TABLE else -1
        if 0 <= current_idx < len(_INA_STEP_TABLE) - 1:
            attack_damage_dice = _INA_STEP_TABLE[current_idx + 1]
        else:
            attack_damage_dice = base_damage_dice  # already at max or unknown die
    else:
        attack_damage_dice = base_damage_dice

    weapon = _build_weapon_from_natural_attack(attack_dict, damage_dice_override=attack_damage_dice if attack_damage_dice != base_damage_dice else None)

    # WO-ENGINE-ATTACK-MODIFIER-FIDELITY-001: Secondary natural attacks get ½ STR (PHB p.314)
    # Setting grip="off-hand" reuses existing ½ STR logic in attack_resolver (line 866)
    if not is_primary:
        weapon = Weapon(
            damage_dice=weapon.damage_dice,
            damage_bonus=weapon.damage_bonus,
            damage_type=weapon.damage_type,
            critical_multiplier=weapon.critical_multiplier,
            critical_range=weapon.critical_range,
            weapon_type=weapon.weapon_type,
            grip="off-hand",
            is_two_handed=weapon.is_two_handed,
        )

    # Build AttackIntent for delegation to resolve_attack
    # Apply secondary penalty to attack_bonus (primary attacks unaffected).
    attack_intent = AttackIntent(
        attacker_id=actor_id,
        target_id=target_id,
        weapon=weapon,
        attack_bonus=intent.attack_bonus + secondary_adjustment,
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
