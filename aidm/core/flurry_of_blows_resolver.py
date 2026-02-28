"""Monk Flurry of Blows resolver — WO-ENGINE-FLURRY-OF-BLOWS-001.

PHB p.41: "When unarmored, a monk may strike with a flurry of blows at the
expense of accuracy. She may make one extra attack in a round at her highest
base attack bonus, but this attack takes a –2 penalty, as does each other
attack made that round."

Penalty by monk level (PHB Table 3-10):
  L1–4:  –2 (two attacks)
  L5–8:  –1 (two attacks)
  L9+:   +0 (iterative sequence + extra attack at top BAB)

Restrictions: unarmored + light load + unarmed/monk weapon only.
"""

from dataclasses import dataclass
from copy import deepcopy
from typing import List, Tuple, Any, Dict, Optional

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.attack_resolver import resolve_attack, apply_attack_events


# PHB Table 3-10 flurry penalty by monk level
_FLURRY_PENALTY_TABLE = [
    (9, 0),   # L9+: no penalty
    (5, -1),  # L5-8: -1 penalty
    (1, -2),  # L1-4: -2 penalty
]

# Monk weapons allowed for Flurry of Blows (PHB p.41)
_MONK_WEAPONS = frozenset({
    "kama", "nunchaku", "quarterstaff", "sai", "shuriken", "siangham",
})

# Default unarmed strike template (natural weapon type)
_UNARMED_DAMAGE_TYPE = "bludgeoning"


@dataclass
class FlurryOfBlowsIntent:
    """Intent for a monk Flurry of Blows attack sequence."""

    actor_id: str
    """Monk performing the flurry"""

    target_id: str
    """Target entity"""


def _flurry_penalty(monk_level: int) -> int:
    """Return the flurry attack penalty for the given monk level (PHB Table 3-10)."""
    for threshold, penalty in _FLURRY_PENALTY_TABLE:
        if monk_level >= threshold:
            return penalty
    return -2


def _flurry_attack_bonuses(attack_bonus: int, bab: int, monk_level: int) -> List[int]:
    """Return the ordered list of attack bonuses for a flurry sequence.

    Extra attack at top BAB (with penalty) + normal iterative sequence (with penalty).
    """
    penalty = _flurry_penalty(monk_level)
    # Extra attack: same bonus as the highest BAB attack
    attacks = [attack_bonus + penalty]
    # Normal iterative sequence (BAB, BAB-5, BAB-10, ...)
    cb = bab
    while cb > 0:
        offset = bab - cb  # 0 for first, 5 for second, 10 for third, ...
        attacks.append(attack_bonus - offset + penalty)
        cb -= 5
    return attacks


def _get_actor_weapon(actor: Dict[str, Any]) -> Optional[Weapon]:
    """Build a Weapon from the actor's EF.WEAPON dict, or None for unarmed."""
    weapon_data = actor.get(EF.WEAPON)
    if weapon_data is None:
        return None
    if isinstance(weapon_data, Weapon):
        return weapon_data
    if isinstance(weapon_data, dict):
        try:
            return Weapon(**{k: v for k, v in weapon_data.items() if k in Weapon.__dataclass_fields__})
        except (TypeError, ValueError):
            return None
    return None


def _make_unarmed_weapon(actor: Dict[str, Any]) -> Weapon:
    """Build the monk's unarmed strike Weapon."""
    dice = actor.get(EF.MONK_UNARMED_DICE, "1d6")
    return Weapon(
        damage_dice=dice,
        damage_bonus=0,
        damage_type=_UNARMED_DAMAGE_TYPE,
        critical_multiplier=2,
        critical_range=20,
        weapon_type="natural",
        proficiency_category="simple",
    )


def resolve_flurry_of_blows(
    intent: FlurryOfBlowsIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Resolve a Flurry of Blows attack sequence.

    Returns (events, updated_world_state).

    Events emitted:
    - ``flurry_blocked``: validation failed (not monk / armor / encumbrance / weapon)
    - Per-blow ``attack_roll`` events (from resolve_attack)
    """
    events: List[Event] = []
    eid = next_event_id
    ts = timestamp

    actor = world_state.entities.get(intent.actor_id, {})

    # ── Validate: must be a monk ─────────────────────────────────────────────
    monk_level = actor.get(EF.CLASS_LEVELS, {}).get("monk", 0)
    if monk_level == 0:
        events.append(Event(
            event_id=eid,
            event_type="flurry_blocked",
            timestamp=ts,
            payload={"actor_id": intent.actor_id, "reason": "not_a_monk"},
            citations=[{"source_id": "681f92bc94ff", "page": 41}],
        ))
        return events, world_state

    # ── Validate: must be unarmored (any armor blocks flurry) ────────────────
    armor_type = actor.get(EF.ARMOR_TYPE, "none")
    if armor_type != "none":
        events.append(Event(
            event_id=eid,
            event_type="flurry_blocked",
            timestamp=ts,
            payload={"actor_id": intent.actor_id, "reason": "wearing_armor"},
            citations=[{"source_id": "681f92bc94ff", "page": 41}],
        ))
        return events, world_state

    # ── Validate: must be light load ─────────────────────────────────────────
    enc_load = actor.get(EF.ENCUMBRANCE_LOAD, "light")
    if enc_load != "light":
        events.append(Event(
            event_id=eid,
            event_type="flurry_blocked",
            timestamp=ts,
            payload={"actor_id": intent.actor_id, "reason": "too_encumbered"},
            citations=[{"source_id": "681f92bc94ff", "page": 41}],
        ))
        return events, world_state

    # ── Validate: weapon must be unarmed (natural) or a monk weapon ──────────
    weapon = _get_actor_weapon(actor)
    if weapon is not None:
        weapon_id = actor.get(EF.WEAPON, {}).get("weapon_id", "") if isinstance(actor.get(EF.WEAPON), dict) else ""
        if weapon.weapon_type != "natural" and weapon_id not in _MONK_WEAPONS:
            events.append(Event(
                event_id=eid,
                event_type="flurry_blocked",
                timestamp=ts,
                payload={"actor_id": intent.actor_id, "reason": "invalid_weapon"},
                citations=[{"source_id": "681f92bc94ff", "page": 41}],
            ))
            return events, world_state
    else:
        weapon = _make_unarmed_weapon(actor)

    # ── Build attack sequence ─────────────────────────────────────────────────
    attack_bonus = actor.get(EF.ATTACK_BONUS, 0)
    bab = actor.get(EF.BAB, 0)
    bonuses = _flurry_attack_bonuses(attack_bonus, bab, monk_level)

    # ── Fire each blow through attack_resolver ────────────────────────────────
    for bonus in bonuses:
        blow_intent = AttackIntent(
            attacker_id=intent.actor_id,
            target_id=intent.target_id,
            attack_bonus=bonus,
            weapon=weapon,
        )
        blow_events = resolve_attack(
            intent=blow_intent,
            world_state=world_state,
            rng=rng,
            next_event_id=eid,
            timestamp=ts,
        )
        events.extend(blow_events)
        eid += len(blow_events)
        ts += 0.01
        world_state = apply_attack_events(world_state, blow_events)

    return events, world_state
