"""Attack resolution for CP-10 — Deterministic Attack Proof.

This module implements minimal attack resolution:
- Attack roll (d20 + bonus vs AC)
- Hit/miss determination (including natural 20/1)
- Damage roll (on hit)
- HP update
- Defeat check

CP-16 INTEGRATION:
- Condition modifiers affect attack rolls and AC
- Attacker conditions modify attack bonus (e.g., shaken -2)
- Defender conditions modify AC (e.g., prone -4 vs melee)
- Damage modifiers apply to damage rolls (e.g., sickened -2)

CP-18A INTEGRATION:
- Mounted higher ground bonus (+1 vs smaller on-foot targets)

CP-19 INTEGRATION:
- Cover bonuses (standard +4 AC, improved +8 AC, total blocks targeting)
- Terrain higher ground bonus (+1 melee, stacks with mounted bonus)

All state mutations are event-driven only.
"""

from copy import deepcopy
from typing import List, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent
from aidm.core.conditions import get_condition_modifiers
from aidm.core.targeting_resolver import evaluate_target_legality  # CP-18A-T&V
from aidm.schemas.entity_fields import EF


def parse_damage_dice(dice_expr: str) -> Tuple[int, int]:
    """
    Parse simple dice expression like '1d8' or '2d6'.

    Args:
        dice_expr: Dice expression string

    Returns:
        Tuple of (num_dice, die_size)

    Raises:
        ValueError: If dice expression is invalid
    """
    if 'd' not in dice_expr:
        raise ValueError(f"Invalid dice expression: {dice_expr}")

    parts = dice_expr.split('d')
    if len(parts) != 2:
        raise ValueError(f"Invalid dice expression: {dice_expr}")

    try:
        num_dice = int(parts[0])
        die_size = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid dice expression: {dice_expr}")

    if num_dice < 1 or die_size < 1:
        raise ValueError(f"Dice count and size must be positive: {dice_expr}")

    return num_dice, die_size


def roll_dice(num_dice: int, die_size: int, rng: RNGManager) -> List[int]:
    """
    Roll multiple dice using deterministic RNG.

    Args:
        num_dice: Number of dice to roll
        die_size: Size of each die (e.g., 6 for d6)
        rng: RNG manager with combat stream

    Returns:
        List of individual die results
    """
    combat_rng = rng.stream("combat")
    return [combat_rng.randint(1, die_size) for _ in range(num_dice)]


def resolve_attack(
    intent: AttackIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float
) -> List[Event]:
    """
    Resolve a single attack action.

    This is the core CP-10 proof function. It:
    0. Validates targeting legality (CP-18A-T&V)
    1. Rolls d20 + attack_bonus
    2. Compares to target AC
    3. On hit: rolls damage and updates HP
    4. Checks for defeat (HP <= 0)

    Args:
        intent: Attack intent with attacker/target/weapon
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

    # CP-18A-T&V: Validate targeting legality BEFORE any RNG access
    legality = evaluate_target_legality(
        actor_id=intent.attacker_id,
        target_id=intent.target_id,
        world_state=world_state,
        max_range=100  # TODO: Use weapon range when available
    )

    if not legality.is_legal:
        # Emit targeting_failed event
        events.append(Event(
            event_id=current_event_id,
            event_type="targeting_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.attacker_id,
                "target_id": intent.target_id,
                "reason": legality.failure_reason.value,
                "intent_type": "attack"
            },
            citations=[c.to_dict() for c in legality.citations]
        ))

        # Return early with failure state (no attack roll, no damage, no HP change)
        return events

    # CP-16: Get condition modifiers for attacker and defender
    attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
    defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")

    # CP-18A: Get mounted higher ground bonus
    from aidm.core.mounted_combat import get_mounted_attack_bonus
    mounted_bonus = get_mounted_attack_bonus(intent.attacker_id, intent.target_id, world_state)

    # CP-19: Get terrain higher ground bonus (stacks with mounted)
    from aidm.core.terrain_resolver import get_higher_ground_bonus, check_cover
    terrain_higher_ground = get_higher_ground_bonus(world_state, intent.attacker_id, intent.target_id)

    # CP-19: Check cover between attacker and defender
    cover_result = check_cover(world_state, intent.attacker_id, intent.target_id, is_melee=True)

    # CP-19: If total cover, cannot target
    if cover_result.blocks_targeting:
        events.append(Event(
            event_id=current_event_id,
            event_type="targeting_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.attacker_id,
                "target_id": intent.target_id,
                "reason": "total_cover",
                "intent_type": "attack"
            },
            citations=[{"source_id": "681f92bc94ff", "page": 150}]  # PHB cover rules
        ))
        return events

    # Get target AC (base AC + condition modifiers + cover bonus)
    target = world_state.entities[intent.target_id]
    base_ac = target.get(EF.AC, 10)  # Default AC 10 if not specified
    # CP-16: condition modifier, CP-19: cover bonus
    target_ac = base_ac + defender_modifiers.ac_modifier + cover_result.ac_bonus

    # Roll attack (d20 + bonus + condition modifiers + mounted bonus + terrain higher ground)
    combat_rng = rng.stream("combat")
    d20_result = combat_rng.randint(1, 20)
    # CP-16: condition modifier, CP-18A: mounted bonus, CP-19: terrain higher ground
    attack_bonus_with_conditions = (
        intent.attack_bonus +
        attacker_modifiers.attack_modifier +
        mounted_bonus +
        terrain_higher_ground
    )
    total = d20_result + attack_bonus_with_conditions

    # Determine hit/miss
    is_natural_20 = (d20_result == 20)
    is_natural_1 = (d20_result == 1)

    if is_natural_20:
        hit = True
    elif is_natural_1:
        hit = False
    else:
        hit = (total >= target_ac)

    # Emit attack_roll event
    events.append(Event(
        event_id=current_event_id,
        event_type="attack_roll",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "d20_result": d20_result,
            "attack_bonus": intent.attack_bonus,
            "condition_modifier": attacker_modifiers.attack_modifier,  # CP-16
            "mounted_bonus": mounted_bonus,  # CP-18A
            "terrain_higher_ground": terrain_higher_ground,  # CP-19
            "cover_type": cover_result.cover_type,  # CP-19
            "cover_ac_bonus": cover_result.ac_bonus,  # CP-19
            "total": total,
            "target_ac": target_ac,
            "target_base_ac": base_ac,  # CP-16: Track base AC separately
            "target_ac_modifier": defender_modifiers.ac_modifier,  # CP-16
            "hit": hit,
            "is_natural_20": is_natural_20,
            "is_natural_1": is_natural_1
        },
        citations=[{"source_id": "681f92bc94ff", "page": 143}]  # PHB attack rules
    ))
    current_event_id += 1

    # If hit, roll damage
    if hit:
        # Parse damage dice
        num_dice, die_size = parse_damage_dice(intent.weapon.damage_dice)

        # Roll damage
        damage_rolls = roll_dice(num_dice, die_size, rng)
        # PHB p.113: STR modifier applies to melee damage
        attacker = world_state.entities[intent.attacker_id]
        str_modifier = attacker.get(EF.STR_MOD, 0)
        base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_modifier
        # CP-16: Apply condition damage modifier
        damage_total = max(0, base_damage + attacker_modifiers.damage_modifier)

        # Emit damage_roll event
        events.append(Event(
            event_id=current_event_id,
            event_type="damage_roll",
            timestamp=timestamp + 0.1,
            payload={
                "attacker_id": intent.attacker_id,
                "target_id": intent.target_id,
                "damage_dice": intent.weapon.damage_dice,
                "damage_rolls": damage_rolls,
                "damage_bonus": intent.weapon.damage_bonus,
                "str_modifier": str_modifier,  # PHB p.113
                "condition_modifier": attacker_modifiers.damage_modifier,  # CP-16
                "damage_total": damage_total,
                "damage_type": intent.weapon.damage_type
            },
            citations=[{"source_id": "681f92bc94ff", "page": 145}]  # PHB damage rules
        ))
        current_event_id += 1

        # Get current HP
        hp_before = target.get(EF.HP_CURRENT, 0)
        hp_after = hp_before - damage_total

        # Emit hp_changed event
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=timestamp + 0.2,
            payload={
                "entity_id": intent.target_id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "delta": -damage_total,
                "source": "attack_damage"
            }
        ))
        current_event_id += 1

        # Check for defeat
        if hp_after <= 0:
            events.append(Event(
                event_id=current_event_id,
                event_type="entity_defeated",
                timestamp=timestamp + 0.3,
                payload={
                    "entity_id": intent.target_id,
                    "hp_final": hp_after,
                    "defeated_by": intent.attacker_id
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}]  # PHB HP/death
            ))
            current_event_id += 1

    return events


def apply_attack_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """
    Apply attack resolution events to world state.

    This is the ONLY function that mutates WorldState based on attack events.

    Args:
        world_state: Current world state
        events: Events to apply

    Returns:
        Updated world state (new instance)
    """
    # Deep copy entities
    entities = deepcopy(world_state.entities)

    for event in events:
        if event.event_type == "hp_changed":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.HP_CURRENT] = event.payload["hp_after"]

        elif event.event_type == "entity_defeated":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DEFEATED] = True

    # Return new WorldState
    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None
    )
