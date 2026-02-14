"""Attack resolution for CP-10 — Deterministic Attack Proof.

This module implements single attack resolution:
- Attack roll (d20 + bonus vs AC)
- Hit/miss determination (including natural 20/1)
- Critical threat detection and confirmation (PHB p.140)
- Damage roll (on hit), with critical damage multiplication
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

WO-FIX-002: Critical hit logic (PHB p.140)
- Threat range from weapon (default 20, can be 19-20, 18-20)
- Confirmation roll (d20 + attack bonus vs AC, no auto-hit on nat 20)
- Damage multiplication on confirmed critical (×2/×3/×4)

WO-048 INTEGRATION:
- Damage Reduction applied after critical multiplier (PHB p.291)

WO-049 INTEGRATION:
- Concealment miss chance checked after hit, before damage (PHB p.152)
- d100 roll consumed only when hit=True and miss_chance > 0

FLANKING INTEGRATION:
- Flanking bonus (+2 melee) when attacker and ally on opposite sides of target
- PHB p.153: angle >= 135 degrees between attacker-target and ally-target vectors

WO-050B INTEGRATION (Sneak Attack):
- Precision damage (Xd6) when target is flanked or denied Dex to AC
- NOT multiplied on critical hits (PHB p.50)
- Not effective vs creatures immune to critical hits
- Ranged sneak attacks limited to 30 feet

RNG CONSUMPTION ORDER (deterministic):
1. Attack roll (d20)
2. IF threat: Confirmation roll (d20)
3. IF hit AND miss_chance > 0: Miss chance roll (d100)
4. IF hit: Damage roll (XdY)
5. IF hit AND sneak attack eligible: Sneak attack roll (Xd6) (WO-050B)

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
    2. Checks critical threat (d20 >= weapon.critical_range) (PHB p.140)
    3. If threat: rolls confirmation (d20 + bonus vs AC)
    4. On hit: rolls damage (multiplied on confirmed critical)
    5. Updates HP and checks for defeat

    RNG consumption order (deterministic):
    1. Attack roll (d20)
    2. IF threat: Confirmation roll (d20)
    3. IF hit: Damage roll (XdY)

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

    # WO-034: Get feat-based attack modifier
    from aidm.core.feat_resolver import get_attack_modifier
    attacker = world_state.entities[intent.attacker_id]
    target = world_state.entities[intent.target_id]

    # Build context for feat modifier computation
    feat_context = {
        "weapon_name": "unknown",  # Placeholder until weapon tracking exists
        "range_ft": 5,  # Assume melee range for now
        "is_ranged": False,  # TODO: Detect from weapon type
        "is_twf": False,  # TODO: Detect from attack intent
        "power_attack_penalty": intent.power_attack_penalty,  # WO-034-FIX: from intent
        "is_two_handed": intent.weapon.is_two_handed,  # WO-034-FIX: from weapon
    }
    feat_attack_modifier = get_attack_modifier(attacker, target, feat_context)

    # Flanking: +2 melee attack bonus when attacker and ally on opposite sides (PHB p.153)
    from aidm.core.flanking import get_flanking_info
    flanking_bonus, is_flanking, flanking_ally_ids = get_flanking_info(
        world_state, intent.attacker_id, intent.target_id
    )

    # Get target AC (base AC + condition modifiers + cover bonus)
    base_ac = target.get(EF.AC, 10)  # Default AC 10 if not specified
    # CP-16: condition modifier, CP-19: cover bonus
    target_ac = base_ac + defender_modifiers.ac_modifier + cover_result.ac_bonus

    # Step 1: Roll attack (d20 + bonus + condition modifiers + mounted bonus + terrain higher ground + feat modifier + flanking)
    combat_rng = rng.stream("combat")
    d20_result = combat_rng.randint(1, 20)
    # CP-16: condition modifier, CP-18A: mounted bonus, CP-19: terrain higher ground, WO-034: feat modifier, flanking
    attack_bonus_with_conditions = (
        intent.attack_bonus +
        attacker_modifiers.attack_modifier +
        mounted_bonus +
        terrain_higher_ground +
        feat_attack_modifier +
        flanking_bonus
    )
    total = d20_result + attack_bonus_with_conditions

    # Determine threat and hit (PHB p.140)
    is_threat = (d20_result >= intent.weapon.critical_range)
    is_natural_20 = (d20_result == 20)
    is_natural_1 = (d20_result == 1)

    # PHB p.140: Natural 1 always misses. Natural 20 always hits AND threatens.
    # Expanded threat range (e.g., 19-20): the roll threatens a critical, but
    # the attack must still meet AC to hit (only natural 20 auto-hits).
    if is_natural_1:
        hit = False
    elif is_natural_20:
        hit = True
    else:
        hit = (total >= target_ac)

    # Step 2: Critical confirmation (PHB p.140) — only if threat AND hit
    is_critical = False
    confirmation_total = None

    if is_threat and hit:
        confirmation_d20 = combat_rng.randint(1, 20)
        confirmation_total = confirmation_d20 + attack_bonus_with_conditions
        # Confirmation hits if it would hit normally (no auto-hit on natural 20 for confirmation)
        if confirmation_total >= target_ac:
            is_critical = True

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
            "feat_modifier": feat_attack_modifier,  # WO-034
            "flanking_bonus": flanking_bonus,  # PHB p.153
            "is_flanking": is_flanking,  # PHB p.153
            "flanking_ally_ids": flanking_ally_ids,  # PHB p.153
            "cover_type": cover_result.cover_type,  # CP-19
            "cover_ac_bonus": cover_result.ac_bonus,  # CP-19
            "total": total,
            "target_ac": target_ac,
            "target_base_ac": base_ac,  # CP-16: Track base AC separately
            "target_ac_modifier": defender_modifiers.ac_modifier,  # CP-16
            "hit": hit,
            "is_natural_20": is_natural_20,
            "is_natural_1": is_natural_1,
            "is_threat": is_threat,  # WO-FIX-002
            "is_critical": is_critical,  # WO-FIX-002
            "confirmation_total": confirmation_total  # WO-FIX-002 (None if no confirmation)
        },
        citations=[{"source_id": "681f92bc94ff", "page": 140}]  # PHB critical hit rules
    ))
    current_event_id += 1

    # WO-049: Miss chance from concealment (PHB p.152)
    # Check AFTER hit determination, BEFORE damage roll
    miss_chance_miss = False
    miss_chance_d100 = None
    if hit:
        from aidm.core.concealment import get_miss_chance, check_miss_chance
        miss_chance_percent = get_miss_chance(world_state, intent.target_id)
        if miss_chance_percent > 0:
            miss_chance_d100 = combat_rng.randint(1, 100)
            if check_miss_chance(miss_chance_percent, miss_chance_d100):
                miss_chance_miss = True
                hit = False  # Override hit to miss
                # Emit concealment_miss event
                events.append(Event(
                    event_id=current_event_id,
                    event_type="concealment_miss",
                    timestamp=timestamp + 0.05,
                    payload={
                        "attacker_id": intent.attacker_id,
                        "target_id": intent.target_id,
                        "miss_chance_percent": miss_chance_percent,
                        "d100_result": miss_chance_d100,
                        "original_hit": True,
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 152}]  # PHB concealment
                ))
                current_event_id += 1

    # If hit, roll damage
    if hit:
        # Parse damage dice
        num_dice, die_size = parse_damage_dice(intent.weapon.damage_dice)

        # Roll damage
        damage_rolls = roll_dice(num_dice, die_size, rng)
        # PHB p.113: STR modifier applies to melee damage
        str_modifier = attacker.get(EF.STR_MOD, 0)

        # WO-034: Get feat-based damage modifier
        from aidm.core.feat_resolver import get_damage_modifier
        # Update context for damage computation
        feat_context["is_two_handed"] = intent.weapon.is_two_handed  # WO-034-FIX
        feat_damage_modifier = get_damage_modifier(attacker, target, feat_context)

        # WO-FIX-01 (BUG-1): STR-to-damage multiplier based on weapon grip (PHB p.113)
        weapon_grip = intent.weapon.grip
        if weapon_grip == "two-handed":
            str_to_damage = int(str_modifier * 1.5)
        elif weapon_grip == "off-hand":
            str_to_damage = int(str_modifier * 0.5)
        else:
            str_to_damage = str_modifier

        base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_to_damage
        # CP-16: Apply condition damage modifier, WO-034: Apply feat damage modifier
        base_damage_with_modifiers = base_damage + attacker_modifiers.damage_modifier + feat_damage_modifier

        # WO-FIX-002: Apply critical multiplier (PHB p.140)
        if is_critical:
            damage_total = max(1, base_damage_with_modifiers * intent.weapon.critical_multiplier)  # WO-FIX-01 (BUG-8/9): min 1 on hit, before DR
        else:
            damage_total = max(1, base_damage_with_modifiers)  # WO-FIX-01 (BUG-8/9): min 1 on hit, before DR

        # WO-050B: Sneak Attack precision damage (PHB p.50)
        # Added AFTER critical multiplier — precision damage is NOT multiplied on crits
        from aidm.core.sneak_attack import calculate_sneak_attack
        sa_eligible, sa_damage, sa_dice_expr, sa_rolls, sa_reason = calculate_sneak_attack(
            world_state, intent.attacker_id, intent.target_id,
            is_flanking=is_flanking,
            rng=rng,
        )
        if sa_eligible:
            damage_total += sa_damage

        # WO-048: Apply Damage Reduction (PHB p.291)
        from aidm.core.damage_reduction import get_applicable_dr, apply_dr_to_damage
        dr_amount = get_applicable_dr(
            world_state, intent.target_id, intent.weapon.damage_type,
        )
        final_damage, damage_reduced = apply_dr_to_damage(damage_total, dr_amount)

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
                "feat_modifier": feat_damage_modifier,  # WO-034
                "base_damage": base_damage_with_modifiers,  # WO-FIX-002: pre-multiplier damage
                "critical_multiplier": intent.weapon.critical_multiplier if is_critical else 1,  # WO-FIX-002
                "sneak_attack_eligible": sa_eligible,  # WO-050B
                "sneak_attack_dice": sa_dice_expr,  # WO-050B
                "sneak_attack_rolls": sa_rolls,  # WO-050B
                "sneak_attack_damage": sa_damage,  # WO-050B
                "sneak_attack_reason": sa_reason,  # WO-050B
                "damage_total": damage_total,  # Pre-DR damage (includes sneak attack)
                "dr_amount": dr_amount,  # WO-048
                "damage_reduced": damage_reduced,  # WO-048
                "final_damage": final_damage,  # WO-048: Post-DR damage
                "damage_type": intent.weapon.damage_type
            },
            citations=[{"source_id": "681f92bc94ff", "page": 140}]  # PHB critical/damage rules
        ))
        current_event_id += 1

        # Get current HP — use final_damage (post-DR)
        hp_before = target.get(EF.HP_CURRENT, 0)
        hp_after = hp_before - final_damage

        # Emit hp_changed event
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=timestamp + 0.2,
            payload={
                "entity_id": intent.target_id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "delta": -final_damage,
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
