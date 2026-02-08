"""Full attack sequence resolution for CP-11.

This module extends CP-10's single attack resolution to handle:
- Multiple iterative attacks based on BAB progression
- Critical threat detection (natural 20)
- Critical confirmation rolls
- Critical damage multiplication (×2/×3/×4)

RNG CONSUMPTION ORDER (deterministic):
1. Attack roll (d20)
2. IF threat: Confirmation roll (d20)
3. IF hit: Damage roll (XdY)

NO MECHANICS BEYOND CP-11 SCOPE:
- No expanded threat range (19-20, 18-20) - always 20 only
- No two-weapon fighting
- No attacks of opportunity
- No DR/resistance/conditions

All state mutations are event-driven only.
"""

from typing import List, Tuple
from dataclasses import dataclass

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent
from aidm.core.attack_resolver import parse_damage_dice, roll_dice


@dataclass
class FullAttackIntent:
    """Intent to perform a full attack action with multiple iterative attacks."""

    attacker_id: str
    """Entity performing the full attack"""

    target_id: str
    """Entity being attacked"""

    base_attack_bonus: int
    """Base attack bonus (without iterative penalties)"""

    weapon: "Weapon"  # noqa: F821
    """Weapon being used for all attacks"""

    def __post_init__(self):
        """Validate full attack intent."""
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")


def calculate_iterative_attacks(base_attack_bonus: int) -> List[int]:
    """
    Calculate attack bonuses for all iterative attacks in a full attack.

    Per D&D 3.5e PHB p.143:
    - First attack: full BAB
    - Second attack: BAB - 5 (if BAB >= 6)
    - Third attack: BAB - 10 (if BAB >= 11)
    - Fourth attack: BAB - 15 (if BAB >= 16)

    Args:
        base_attack_bonus: Base attack bonus (full BAB)

    Returns:
        List of attack bonuses for each iterative attack
    """
    attacks = [base_attack_bonus]

    # Add iterative attacks at -5 increments
    current_bab = base_attack_bonus - 5
    while current_bab >= 1:
        attacks.append(current_bab)
        current_bab -= 5

    return attacks


def resolve_single_attack_with_critical(
    attacker_id: str,
    target_id: str,
    attack_bonus: int,
    weapon: "Weapon",  # noqa: F821
    target_ac: int,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    attack_index: int
) -> Tuple[List[Event], int]:
    """
    Resolve a single attack with critical hit logic.

    RNG consumption order:
    1. Attack roll (d20)
    2. IF threat (natural 20): Confirmation roll (d20)
    3. IF hit: Damage roll (XdY)

    Args:
        attacker_id: Attacker entity ID
        target_id: Target entity ID
        attack_bonus: Attack bonus for this specific attack
        weapon: Weapon being used
        target_ac: Target's AC
        rng: RNG manager
        next_event_id: Next available event ID
        timestamp: Event timestamp
        attack_index: Index of this attack in the full attack sequence (0-based)

    Returns:
        Tuple of (events, next_event_id, damage_total)
    """
    events = []
    current_event_id = next_event_id
    combat_rng = rng.stream("combat")

    # Step 1: Roll attack (d20 + bonus)
    d20_result = combat_rng.randint(1, 20)
    total = d20_result + attack_bonus

    # Determine threat and hit
    is_threat = (d20_result == 20)  # CP-11: Only natural 20 threatens (no 19-20 yet)
    is_natural_1 = (d20_result == 1)

    # Initial hit determination (before confirmation)
    if is_natural_1:
        hit = False
    elif is_threat:
        hit = True  # Natural 20 auto-hits
    else:
        hit = (total >= target_ac)

    # Step 2: Critical confirmation (only if threat AND not already a miss)
    is_critical = False
    confirmation_total = None

    if is_threat and hit:
        # Roll confirmation attack
        confirmation_d20 = combat_rng.randint(1, 20)
        confirmation_total = confirmation_d20 + attack_bonus

        # Confirmation hits if it would hit normally (no auto-hit on natural 20 for confirmation)
        if confirmation_total >= target_ac:
            is_critical = True

    # Emit attack_roll event
    events.append(Event(
        event_id=current_event_id,
        event_type="attack_roll",
        timestamp=timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
            "attack_index": attack_index,
            "d20_result": d20_result,
            "attack_bonus": attack_bonus,
            "total": total,
            "target_ac": target_ac,
            "hit": hit,
            "is_natural_20": is_threat,
            "is_natural_1": is_natural_1,
            "is_threat": is_threat,
            "is_critical": is_critical,  # CP-11: New field (backward compatible with default False)
            "confirmation_total": confirmation_total  # CP-11: New field (None if no confirmation)
        },
        citations=[{"source_id": "681f92bc94ff", "page": 143}]  # PHB attack rules
    ))
    current_event_id += 1

    # Step 3: Damage roll (only if hit)
    if hit:
        # Parse damage dice
        num_dice, die_size = parse_damage_dice(weapon.damage_dice)

        # Roll base damage
        damage_rolls = roll_dice(num_dice, die_size, rng)
        base_damage = sum(damage_rolls) + weapon.damage_bonus

        # Apply critical multiplier if critical hit
        if is_critical:
            damage_total = base_damage * weapon.critical_multiplier
        else:
            damage_total = base_damage

        # Emit damage_roll event
        events.append(Event(
            event_id=current_event_id,
            event_type="damage_roll",
            timestamp=timestamp + 0.1,
            payload={
                "attacker_id": attacker_id,
                "target_id": target_id,
                "attack_index": attack_index,
                "damage_dice": weapon.damage_dice,
                "damage_rolls": damage_rolls,
                "damage_bonus": weapon.damage_bonus,
                "base_damage": base_damage,  # CP-11: New field (backward compatible)
                "critical_multiplier": weapon.critical_multiplier if is_critical else 1,  # CP-11: New field
                "damage_total": damage_total,
                "damage_type": weapon.damage_type
            },
            citations=[{"source_id": "681f92bc94ff", "page": 145}]  # PHB damage rules
        ))
        current_event_id += 1

        # Return damage total for HP processing
        return events, current_event_id, damage_total

    # No damage on miss
    return events, current_event_id, 0


def resolve_full_attack(
    intent: FullAttackIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float
) -> List[Event]:
    """
    Resolve a full attack action with multiple iterative attacks.

    This is the core CP-11 proof function. It:
    1. Calculates iterative attack bonuses from BAB
    2. Resolves each attack in sequence (attack roll → crit confirm → damage)
    3. Accumulates damage to target HP
    4. Checks for defeat after all attacks

    Args:
        intent: Full attack intent with attacker/target/weapon/BAB
        world_state: Current world state (for target AC/HP)
        rng: RNG manager (uses "combat" stream)
        next_event_id: Next available event ID
        timestamp: Event timestamp

    Returns:
        List of events emitted during resolution

    Raises:
        ValueError: If attacker or target not in world state
    """
    events = []
    current_event_id = next_event_id

    # Validate entities exist
    if intent.attacker_id not in world_state.entities:
        raise ValueError(f"Attacker not found in world state: {intent.attacker_id}")
    if intent.target_id not in world_state.entities:
        raise ValueError(f"Target not found in world state: {intent.target_id}")

    # Get target AC and HP
    target = world_state.entities[intent.target_id]
    target_ac = target.get("ac", 10)
    hp_current = target.get("hp_current", 0)

    # Calculate iterative attacks
    attack_bonuses = calculate_iterative_attacks(intent.base_attack_bonus)

    # Emit full_attack_start event
    events.append(Event(
        event_id=current_event_id,
        event_type="full_attack_start",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "base_attack_bonus": intent.base_attack_bonus,
            "num_attacks": len(attack_bonuses),
            "attack_bonuses": attack_bonuses
        },
        citations=[{"source_id": "681f92bc94ff", "page": 143}]  # PHB full attack
    ))
    current_event_id += 1

    # Resolve each attack in sequence
    total_damage = 0

    for attack_index, attack_bonus in enumerate(attack_bonuses):
        attack_events, current_event_id, damage = resolve_single_attack_with_critical(
            attacker_id=intent.attacker_id,
            target_id=intent.target_id,
            attack_bonus=attack_bonus,
            weapon=intent.weapon,
            target_ac=target_ac,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=timestamp + 0.5 * attack_index,
            attack_index=attack_index
        )

        events.extend(attack_events)
        total_damage += damage

    # Apply accumulated damage to HP
    if total_damage > 0:
        hp_before = hp_current
        hp_after = hp_before - total_damage

        # Emit hp_changed event
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=timestamp + 0.5 * len(attack_bonuses),
            payload={
                "entity_id": intent.target_id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "delta": -total_damage,
                "source": "full_attack_damage"
            }
        ))
        current_event_id += 1

        # Check for defeat
        if hp_after <= 0:
            events.append(Event(
                event_id=current_event_id,
                event_type="entity_defeated",
                timestamp=timestamp + 0.5 * len(attack_bonuses) + 0.1,
                payload={
                    "entity_id": intent.target_id,
                    "hp_final": hp_after,
                    "defeated_by": intent.attacker_id
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}]  # PHB HP/death
            ))
            current_event_id += 1

    # Emit full_attack_end event
    events.append(Event(
        event_id=current_event_id,
        event_type="full_attack_end",
        timestamp=timestamp + 0.5 * len(attack_bonuses) + 0.2,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "total_damage": total_damage,
            "num_hits": sum(1 for e in events if e.event_type == "damage_roll"),
            "num_attacks": len(attack_bonuses)
        }
    ))
    current_event_id += 1

    return events


def apply_full_attack_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """
    Apply full attack resolution events to world state.

    This function reuses the same mutation logic as CP-10's apply_attack_events.
    It handles hp_changed and entity_defeated events.

    Args:
        world_state: Current world state
        events: Events to apply

    Returns:
        Updated world state (new instance)
    """
    # Deep copy entities
    entities = {eid: e.copy() for eid, e in world_state.entities.items()}

    for event in events:
        if event.event_type == "hp_changed":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id]["hp_current"] = event.payload["hp_after"]

        elif event.event_type == "entity_defeated":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id]["defeated"] = True

    # Return new WorldState
    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat.copy() if world_state.active_combat else None
    )
