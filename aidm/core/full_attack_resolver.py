"""Full attack sequence resolution for CP-11.

This module extends CP-10's single attack resolution to handle:
- Multiple iterative attacks based on BAB progression
- Critical threat detection (natural 20)
- Critical confirmation rolls
- Critical damage multiplication (×2/×3/×4)

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

WO-034 INTEGRATION:
- Feat-based attack modifiers (Weapon Focus, etc.)
- Feat-based damage modifiers (Weapon Specialization, Power Attack, etc.)

WO-FIX-003: Unified AC/modifier computation (PHB p.140)
- All modifier layers (conditions, mounted, terrain, cover, feats) applied
- Matches attack_resolver.py's resolve_attack() modifier discipline

WO-048 INTEGRATION:
- Damage Reduction applied per-attack after critical multiplier (PHB p.291)

WO-049 INTEGRATION:
- Concealment miss chance checked after hit, before damage (PHB p.152)
- d100 roll consumed only when hit=True and miss_chance > 0

RNG CONSUMPTION ORDER (deterministic):
1. Attack roll (d20)
2. IF threat: Confirmation roll (d20)
3. IF hit AND miss_chance > 0: Miss chance roll (d100)
4. IF hit: Damage roll (XdY)

All state mutations are event-driven only.
"""

from typing import List, Tuple
from dataclasses import dataclass

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent
from aidm.core.attack_resolver import parse_damage_dice, roll_dice
from aidm.core.conditions import get_condition_modifiers
from aidm.core.targeting_resolver import evaluate_target_legality
from aidm.schemas.entity_fields import EF


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

    power_attack_penalty: int = 0
    """WO-034-FIX: Power Attack trade-off penalty (PHB p.98).
    0 = not using Power Attack. Max = BAB."""

    def __post_init__(self):
        """Validate full attack intent."""
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.power_attack_penalty < 0:
            raise ValueError("power_attack_penalty cannot be negative")


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
    attack_index: int,
    str_modifier: int = 0,
    condition_damage_modifier: int = 0,
    feat_damage_modifier: int = 0,
    base_attack_bonus_raw: int = 0,
    condition_attack_modifier: int = 0,
    mounted_bonus: int = 0,
    terrain_higher_ground: int = 0,
    feat_attack_modifier: int = 0,
    target_base_ac: int = 10,
    target_ac_modifier: int = 0,
    cover_type: str = "none",
    cover_ac_bonus: int = 0,
    dr_amount: int = 0,
    miss_chance_percent: int = 0,
) -> Tuple[List[Event], int]:
    """
    Resolve a single attack with critical hit logic.

    WO-FIX-003: Now accepts pre-computed modifiers from resolve_full_attack()
    so that all modifier layers are applied consistently.

    RNG consumption order:
    1. Attack roll (d20)
    2. IF threat (d20 >= weapon.critical_range): Confirmation roll (d20)
    3. IF hit AND miss_chance > 0: Miss chance roll (d100) (WO-049)
    4. IF hit: Damage roll (XdY)

    Args:
        attacker_id: Attacker entity ID
        target_id: Target entity ID
        attack_bonus: Fully adjusted attack bonus (BAB + conditions + mounted + terrain + feat)
        weapon: Weapon being used
        target_ac: Fully adjusted target AC (base + condition + cover)
        rng: RNG manager
        next_event_id: Next available event ID
        timestamp: Event timestamp
        attack_index: Index of this attack in the full attack sequence (0-based)
        str_modifier: STR modifier for damage (PHB p.113)
        condition_damage_modifier: CP-16 condition damage modifier
        feat_damage_modifier: WO-034 feat damage modifier
        base_attack_bonus_raw: Unadjusted BAB for this iterative (for audit trail)
        condition_attack_modifier: CP-16 condition attack modifier (for audit trail)
        mounted_bonus: CP-18A mounted bonus (for audit trail)
        terrain_higher_ground: CP-19 terrain bonus (for audit trail)
        feat_attack_modifier: WO-034 feat attack modifier (for audit trail)
        target_base_ac: Base AC before modifiers (for audit trail)
        target_ac_modifier: CP-16 defender condition AC modifier (for audit trail)
        cover_type: CP-19 cover type string (for audit trail)
        cover_ac_bonus: CP-19 cover AC bonus (for audit trail)
        dr_amount: WO-048 applicable Damage Reduction amount
        miss_chance_percent: WO-049 miss chance percentage (0-100)

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
    is_threat = (d20_result >= weapon.critical_range)  # PHB p.140: threat range from weapon
    is_natural_1 = (d20_result == 1)
    is_natural_20 = (d20_result == 20)

    # PHB p.140: Natural 1 always misses. Natural 20 always hits AND threatens.
    # Expanded threat range (e.g., 19-20): the roll threatens a critical, but
    # the attack must still meet AC to hit (only natural 20 auto-hits).
    if is_natural_1:
        hit = False
    elif is_natural_20:
        hit = True
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

    # Emit attack_roll event (WO-FIX-003: full modifier audit trail)
    events.append(Event(
        event_id=current_event_id,
        event_type="attack_roll",
        timestamp=timestamp,
        payload={
            "attacker_id": attacker_id,
            "target_id": target_id,
            "attack_index": attack_index,
            "d20_result": d20_result,
            "attack_bonus": base_attack_bonus_raw,  # WO-FIX-003: raw BAB for this iterative
            "condition_modifier": condition_attack_modifier,  # CP-16
            "mounted_bonus": mounted_bonus,  # CP-18A
            "terrain_higher_ground": terrain_higher_ground,  # CP-19
            "feat_modifier": feat_attack_modifier,  # WO-034
            "total": total,
            "target_ac": target_ac,
            "target_base_ac": target_base_ac,  # WO-FIX-003: base AC for audit
            "target_ac_modifier": target_ac_modifier,  # CP-16
            "cover_type": cover_type,  # CP-19
            "cover_ac_bonus": cover_ac_bonus,  # CP-19
            "hit": hit,
            "is_natural_20": is_natural_20,
            "is_natural_1": is_natural_1,
            "is_threat": is_threat,
            "is_critical": is_critical,
            "confirmation_total": confirmation_total
        },
        citations=[{"source_id": "681f92bc94ff", "page": 140}]  # PHB critical hit rules
    ))
    current_event_id += 1

    # WO-049: Miss chance from concealment (PHB p.152)
    # Check AFTER hit determination, BEFORE damage roll
    if hit and miss_chance_percent > 0:
        from aidm.core.concealment import check_miss_chance
        miss_chance_d100 = combat_rng.randint(1, 100)
        if check_miss_chance(miss_chance_percent, miss_chance_d100):
            hit = False  # Override hit to miss
            events.append(Event(
                event_id=current_event_id,
                event_type="concealment_miss",
                timestamp=timestamp + 0.05,
                payload={
                    "attacker_id": attacker_id,
                    "target_id": target_id,
                    "attack_index": attack_index,
                    "miss_chance_percent": miss_chance_percent,
                    "d100_result": miss_chance_d100,
                    "original_hit": True,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 152}]  # PHB concealment
            ))
            current_event_id += 1

    # Step 3: Damage roll (only if hit)
    if hit:
        # Parse damage dice
        num_dice, die_size = parse_damage_dice(weapon.damage_dice)

        # Roll base damage
        damage_rolls = roll_dice(num_dice, die_size, rng)
        # PHB p.113: STR modifier applies to melee damage
        base_damage = sum(damage_rolls) + weapon.damage_bonus + str_modifier
        # CP-16: condition damage modifier, WO-034: feat damage modifier
        base_damage_with_modifiers = base_damage + condition_damage_modifier + feat_damage_modifier

        # WO-FIX-002: Apply critical multiplier (PHB p.140)
        if is_critical:
            damage_total = max(0, base_damage_with_modifiers * weapon.critical_multiplier)
        else:
            damage_total = max(0, base_damage_with_modifiers)

        # WO-048: Apply Damage Reduction (PHB p.291)
        from aidm.core.damage_reduction import apply_dr_to_damage
        final_damage, damage_reduced = apply_dr_to_damage(damage_total, dr_amount)

        # Emit damage_roll event (WO-FIX-003: full modifier audit trail)
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
                "str_modifier": str_modifier,  # PHB p.113
                "condition_modifier": condition_damage_modifier,  # CP-16
                "feat_modifier": feat_damage_modifier,  # WO-034
                "base_damage": base_damage_with_modifiers,  # Pre-multiplier damage
                "critical_multiplier": weapon.critical_multiplier if is_critical else 1,
                "damage_total": damage_total,  # Pre-DR damage
                "dr_amount": dr_amount,  # WO-048
                "damage_reduced": damage_reduced,  # WO-048
                "final_damage": final_damage,  # WO-048: Post-DR damage
                "damage_type": weapon.damage_type
            },
            citations=[{"source_id": "681f92bc94ff", "page": 140}]  # PHB critical/damage rules
        ))
        current_event_id += 1

        # Return final damage (post-DR) for HP processing
        return events, current_event_id, final_damage

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
    1. Validates targeting legality (CP-18A-T&V)
    2. Checks cover (CP-19, including total cover blocking)
    3. Computes all modifiers once (conditions, mounted, terrain, cover, feats)
    4. Calculates iterative attack bonuses from BAB
    5. Resolves each attack in sequence (attack roll → crit confirm → damage)
    6. Accumulates damage to target HP
    7. Checks for defeat after all attacks

    WO-FIX-003: All modifier layers now match attack_resolver.py's resolve_attack().

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

    # CP-18A-T&V: Validate targeting legality BEFORE any RNG access
    legality = evaluate_target_legality(
        actor_id=intent.attacker_id,
        target_id=intent.target_id,
        world_state=world_state,
        max_range=100  # TODO: Use weapon range when available
    )

    if not legality.is_legal:
        events.append(Event(
            event_id=current_event_id,
            event_type="targeting_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.attacker_id,
                "target_id": intent.target_id,
                "reason": legality.failure_reason.value,
                "intent_type": "full_attack"
            },
            citations=[c.to_dict() for c in legality.citations]
        ))
        return events

    # CP-19: Check cover between attacker and defender
    from aidm.core.terrain_resolver import get_higher_ground_bonus, check_cover
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
                "intent_type": "full_attack"
            },
            citations=[{"source_id": "681f92bc94ff", "page": 150}]  # PHB cover rules
        ))
        return events

    # CP-16: Get condition modifiers for attacker and defender
    attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
    defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")

    # CP-18A: Get mounted higher ground bonus
    from aidm.core.mounted_combat import get_mounted_attack_bonus
    mounted_bonus = get_mounted_attack_bonus(intent.attacker_id, intent.target_id, world_state)

    # CP-19: Get terrain higher ground bonus (stacks with mounted)
    terrain_higher_ground = get_higher_ground_bonus(world_state, intent.attacker_id, intent.target_id)

    # WO-034: Get feat-based attack modifier
    from aidm.core.feat_resolver import get_attack_modifier, get_damage_modifier
    attacker = world_state.entities[intent.attacker_id]
    target = world_state.entities[intent.target_id]

    feat_context = {
        "weapon_name": "unknown",  # Placeholder until weapon tracking exists
        "range_ft": 5,  # Assume melee range for now
        "is_ranged": False,  # TODO: Detect from weapon type
        "is_twf": False,  # TODO: Detect from attack intent
        "power_attack_penalty": intent.power_attack_penalty,  # WO-034-FIX: from intent
        "is_two_handed": intent.weapon.is_two_handed,  # WO-034-FIX: from weapon
    }
    feat_attack_modifier = get_attack_modifier(attacker, target, feat_context)
    feat_damage_modifier = get_damage_modifier(attacker, target, feat_context)

    # WO-048: Get applicable Damage Reduction
    from aidm.core.damage_reduction import get_applicable_dr
    dr_amount = get_applicable_dr(
        world_state, intent.target_id, intent.weapon.damage_type,
    )

    # WO-049: Get miss chance from concealment (PHB p.152)
    from aidm.core.concealment import get_miss_chance
    miss_chance_percent = get_miss_chance(world_state, intent.target_id)

    # Get target AC (base AC + condition modifiers + cover bonus) — WO-FIX-003
    base_ac = target.get(EF.AC, 10)
    target_ac = base_ac + defender_modifiers.ac_modifier + cover_result.ac_bonus

    hp_current = target.get(EF.HP_CURRENT, 0)

    # PHB p.113: STR modifier applies to melee damage
    str_modifier = attacker.get(EF.STR_MOD, 0)

    # Calculate iterative attacks
    attack_bonuses = calculate_iterative_attacks(intent.base_attack_bonus)

    # Emit full_attack_start event (WO-FIX-003: include modifier audit trail)
    events.append(Event(
        event_id=current_event_id,
        event_type="full_attack_start",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "base_attack_bonus": intent.base_attack_bonus,
            "num_attacks": len(attack_bonuses),
            "attack_bonuses": attack_bonuses,
            "condition_attack_modifier": attacker_modifiers.attack_modifier,  # CP-16
            "condition_ac_modifier": defender_modifiers.ac_modifier,  # CP-16
            "mounted_bonus": mounted_bonus,  # CP-18A
            "terrain_higher_ground": terrain_higher_ground,  # CP-19
            "cover_type": cover_result.cover_type,  # CP-19
            "cover_ac_bonus": cover_result.ac_bonus,  # CP-19
            "feat_attack_modifier": feat_attack_modifier,  # WO-034
            "feat_damage_modifier": feat_damage_modifier,  # WO-034
            "dr_amount": dr_amount,  # WO-048
            "miss_chance_percent": miss_chance_percent,  # WO-049
            "target_base_ac": base_ac,  # WO-FIX-003
            "target_ac": target_ac,  # WO-FIX-003: fully adjusted AC
        },
        citations=[{"source_id": "681f92bc94ff", "page": 143}]  # PHB full attack
    ))
    current_event_id += 1

    # Resolve each attack in sequence
    total_damage = 0

    for attack_index, raw_attack_bonus in enumerate(attack_bonuses):
        # WO-FIX-003: Apply all modifiers to each iterative attack bonus
        adjusted_attack_bonus = (
            raw_attack_bonus +
            attacker_modifiers.attack_modifier +
            mounted_bonus +
            terrain_higher_ground +
            feat_attack_modifier
        )

        attack_events, current_event_id, damage = resolve_single_attack_with_critical(
            attacker_id=intent.attacker_id,
            target_id=intent.target_id,
            attack_bonus=adjusted_attack_bonus,
            weapon=intent.weapon,
            target_ac=target_ac,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=timestamp + 0.5 * attack_index,
            attack_index=attack_index,
            str_modifier=str_modifier,
            condition_damage_modifier=attacker_modifiers.damage_modifier,
            feat_damage_modifier=feat_damage_modifier,
            base_attack_bonus_raw=raw_attack_bonus,
            condition_attack_modifier=attacker_modifiers.attack_modifier,
            mounted_bonus=mounted_bonus,
            terrain_higher_ground=terrain_higher_ground,
            feat_attack_modifier=feat_attack_modifier,
            target_base_ac=base_ac,
            target_ac_modifier=defender_modifiers.ac_modifier,
            cover_type=cover_result.cover_type,
            cover_ac_bonus=cover_result.ac_bonus,
            dr_amount=dr_amount,
            miss_chance_percent=miss_chance_percent,
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
                entities[entity_id][EF.HP_CURRENT] = event.payload["hp_after"]

        elif event.event_type == "entity_defeated":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DEFEATED] = True

    # Return new WorldState
    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat.copy() if world_state.active_combat else None
    )
