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

WO-050B INTEGRATION (Sneak Attack):
- Precision damage (Xd6) when target is flanked or denied Dex to AC
- NOT multiplied on critical hits (PHB p.50)
- Not effective vs creatures immune to critical hits
- Ranged sneak attacks limited to 30 feet
- Computed once per full attack, applied to each individual hit

RNG CONSUMPTION ORDER (deterministic):
1. Attack roll (d20)
2. IF threat: Confirmation roll (d20)
3. IF hit AND miss_chance > 0: Miss chance roll (d100)
4. IF hit: Damage roll (XdY)
5. IF hit AND sneak attack eligible: Sneak attack roll (Xd6) (WO-050B)

All state mutations are event-driven only.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.attack import AttackIntent
from aidm.core.attack_resolver import parse_damage_dice, roll_dice
from aidm.core.conditions import get_condition_modifiers
from aidm.core.targeting_resolver import evaluate_target_legality, get_entity_position
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

    off_hand_weapon: Optional["Weapon"] = None  # noqa: F821
    """CP-21: Off-hand weapon for two-weapon fighting. If set, TWF penalty sequence applies.
    PHB p.160: off-hand gets one attack at BAB with penalty applied."""

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


TWD_FEATS = {
    "Two-Weapon Defense": 1,
    "Improved Two-Weapon Defense": 2,
    "Greater Two-Weapon Defense": 3,
}


def _has_off_hand_weapon(entity: dict) -> bool:
    """Return True if entity is wielding an off-hand weapon.

    PHB p.102: TWD bonus only applies when wielding two weapons.
    Checks EF.WEAPON dict for is_off_hand=True, or presence of
    off_hand_weapon key on the entity dict.
    """
    # Explicit off_hand_weapon entry on entity
    if entity.get("off_hand_weapon"):
        return True
    # Weapon dict with is_off_hand flag
    weapon = entity.get(EF.WEAPON)
    if isinstance(weapon, dict) and weapon.get("is_off_hand", False):
        return True
    return False


def _compute_twd_ac_bonus(defender: dict) -> int:
    """Compute Two-Weapon Defense AC bonus for defender.

    PHB p.102: Shield bonus when wielding two weapons.
    Returns 0 if feat not present, defender is flat-footed, or
    defender is not wielding an off-hand weapon.

    Progression:
      Two-Weapon Defense          -> +1
      Improved Two-Weapon Defense -> +2
      Greater Two-Weapon Defense  -> +3
    """
    from aidm.schemas.conditions import ConditionType

    feats = defender.get(EF.FEATS, [])
    bonus = 0
    for feat_name, feat_bonus in TWD_FEATS.items():
        if feat_name in feats:
            bonus = feat_bonus  # Higher feat supersedes lower

    if bonus == 0:
        return 0

    if not _has_off_hand_weapon(defender):
        return 0

    # Shield bonus is lost when flat-footed (loses Dex to AC)
    conditions = defender.get(EF.CONDITIONS, {})
    flat_footed_conditions = {
        ConditionType.HELPLESS.value,
        ConditionType.STUNNED.value,
        ConditionType.PINNED.value,
        ConditionType.UNCONSCIOUS.value,
        ConditionType.PARALYZED.value,
    }
    if isinstance(conditions, dict):
        for cond_key in conditions:
            if cond_key in flat_footed_conditions:
                return 0
    elif isinstance(conditions, (list, tuple)):
        for cond in conditions:
            if cond in flat_footed_conditions:
                return 0

    return bonus


def _compute_twf_penalties(
    attacker: dict,
    off_hand_weapon: "Weapon",  # noqa: F821
) -> Tuple[int, int]:
    """Compute main-hand and off-hand attack penalties for two-weapon fighting.

    PHB p.160 penalty table:
    - Base: -6 main / -10 off
    - Light off-hand: -4 main / -8 off
    - TWF feat: -4 main / -4 off
    - TWF feat + light off-hand: -2 main / -2 off (best case)

    Args:
        attacker: Entity dict for the attacker
        off_hand_weapon: Off-hand weapon (used to check is_light)

    Returns:
        (main_penalty, off_hand_penalty) — both non-positive integers
    """
    feats = attacker.get(EF.FEATS, [])
    has_twf = "Two-Weapon Fighting" in feats
    light_off_hand = off_hand_weapon.is_light

    if has_twf and light_off_hand:
        return (-2, -2)
    elif has_twf:
        return (-4, -4)
    elif light_off_hand:
        return (-4, -8)
    else:
        return (-6, -10)


def resolve_single_attack_with_critical(
    attacker_id: str,
    target_id: str,
    attack_bonus: int,
    weapon: "Weapon",  # noqa: F821
    target_ac: int,
    rng: RNGProvider,
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
    flanking_bonus: int = 0,
    is_flanking: bool = False,
    flanking_ally_ids: list = None,
    sneak_attack_dice: int = 0,
    sneak_attack_eligible: bool = False,
    sneak_attack_reason: str = "",
    favored_enemy_bonus: int = 0,
    attacker_feats: list = None,
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
    # WO-ENGINE-IMPROVED-CRITICAL-001: Improved Critical feat doubles threat range (PHB p.96)
    # e.g., crit_range 20→19, 19→17, 18→15. Formula: 21 - (21 - base_range) * 2
    _eff_crit_range = weapon.critical_range
    _ic_feats = attacker_feats if attacker_feats is not None else []
    _weapon_type = getattr(weapon, "weapon_type", None)
    _ic_specific = f"improved_critical_{_weapon_type}" if _weapon_type else None
    if "improved_critical" in _ic_feats or (_ic_specific and _ic_specific in _ic_feats):
        _eff_crit_range = max(1, 21 - (21 - weapon.critical_range) * 2)
    is_threat = (d20_result >= _eff_crit_range)  # PHB p.140: threat range from weapon
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
            "flanking_bonus": flanking_bonus,  # PHB p.153
            "is_flanking": is_flanking,  # PHB p.153
            "flanking_ally_ids": flanking_ally_ids or [],  # PHB p.153
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
        # WO-FIX-01 (BUG-1): STR-to-damage multiplier based on weapon grip (PHB p.113)
        weapon_grip = weapon.grip
        if weapon_grip == "two-handed":
            str_to_damage = int(str_modifier * 1.5)
        elif weapon_grip == "off-hand":
            str_to_damage = int(str_modifier * 0.5)
        else:
            str_to_damage = str_modifier

        base_damage = sum(damage_rolls) + weapon.damage_bonus + str_to_damage + weapon.enhancement_bonus  # WO-ENGINE-WEAPON-ENHANCEMENT-001: enhancement is pre-crit (PHB p.224)
        # WO-ENGINE-WEAPON-SPECIALIZATION-001: Weapon Specialization +2 damage bonus (PHB p.102)
        # Pre-crit: multiplied on critical hits (same as enhancement bonus, PHB p.224)
        _ic_wsp = attacker_feats if attacker_feats is not None else []
        _wsp_bonus = 2 if f"weapon_specialization_{getattr(weapon, 'weapon_type', '')}" in _ic_wsp else 0
        base_damage += _wsp_bonus
        # CP-16: condition damage modifier, WO-034: feat damage modifier
        base_damage_with_modifiers = base_damage + condition_damage_modifier + feat_damage_modifier

        # WO-FIX-002: Apply critical multiplier (PHB p.140)
        if is_critical:
            damage_total = max(1, base_damage_with_modifiers * weapon.critical_multiplier)  # WO-FIX-01 (BUG-8/9): min 1 on hit, before DR
        else:
            damage_total = max(1, base_damage_with_modifiers)  # WO-FIX-01 (BUG-8/9): min 1 on hit, before DR

        # WO-ENGINE-FAVORED-ENEMY-001: Favored Enemy damage bonus is NOT multiplied on crit (PHB p.47 — flat bonus)
        damage_total += favored_enemy_bonus

        # WO-050B: Sneak Attack precision damage (PHB p.50)
        # Added AFTER critical multiplier — precision damage is NOT multiplied on crits
        sa_damage = 0
        sa_dice_expr = ""
        sa_rolls = []
        if sneak_attack_eligible and sneak_attack_dice > 0:
            from aidm.core.sneak_attack import roll_sneak_attack_damage
            sa_damage, sa_dice_expr, sa_rolls = roll_sneak_attack_damage(sneak_attack_dice, rng)
            damage_total += sa_damage

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
                "sneak_attack_eligible": sneak_attack_eligible,  # WO-050B
                "sneak_attack_dice": sa_dice_expr,  # WO-050B
                "sneak_attack_rolls": sa_rolls,  # WO-050B
                "sneak_attack_damage": sa_damage,  # WO-050B
                "sneak_attack_reason": sneak_attack_reason,  # WO-050B
                "damage_total": damage_total,  # Pre-DR damage (includes sneak attack)
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
    rng: RNGProvider,
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

    # WO-WEAPON-PLUMBING-001: Compute actual range between attacker and target
    attacker_pos = get_entity_position(world_state, intent.attacker_id)
    target_pos = get_entity_position(world_state, intent.target_id)
    range_ft = attacker_pos.distance_to(target_pos)

    # CP-18A-T&V: Validate targeting legality BEFORE any RNG access
    legality = evaluate_target_legality(
        actor_id=intent.attacker_id,
        target_id=intent.target_id,
        world_state=world_state,
        max_range=(intent.weapon.range_increment * 10) if intent.weapon.is_ranged else 100,  # WO-WEAPON-PLUMBING-001: ranged=weapon data; melee=legacy 100ft cap
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
    cover_result = check_cover(world_state, intent.attacker_id, intent.target_id, is_melee=not intent.weapon.is_ranged)

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
        "range_ft": range_ft,  # WO-WEAPON-PLUMBING-001: actual range from positions
        "is_ranged": intent.weapon.is_ranged,  # WO-WEAPON-PLUMBING-001: from weapon type
        "is_twf": intent.off_hand_weapon is not None,  # CP-21: derived from intent
        "power_attack_penalty": intent.power_attack_penalty,  # WO-034-FIX: from intent
        "is_two_handed": intent.weapon.is_two_handed,  # WO-034-FIX: from weapon
    }
    feat_attack_modifier = get_attack_modifier(attacker, target, feat_context)
    feat_damage_modifier = get_damage_modifier(attacker, target, feat_context)

    # WO-ENGINE-FAVORED-ENEMY-001: Ranger Favored Enemy attack/damage bonus (PHB p.47)
    _favored_enemy_bonus = 0
    _attacker_favored = attacker.get(EF.FAVORED_ENEMIES, [])
    if _attacker_favored:
        _target_type = target.get(EF.CREATURE_TYPE, "")
        for _fe in _attacker_favored:
            if _fe.get("creature_type", "") == _target_type and _target_type != "":
                _favored_enemy_bonus = _fe.get("bonus", 0)
                break

    # Flanking: +2 melee attack bonus when attacker and ally on opposite sides (PHB p.153)
    from aidm.core.flanking import get_flanking_info
    flanking_bonus, is_flanking, flanking_ally_ids = get_flanking_info(
        world_state, intent.attacker_id, intent.target_id
    )

    # WO-ENGINE-IMPROVED-UNCANNY-DODGE-001: IUD suppresses flanking-based sneak attack (PHB p.26/50)
    # Flanking attack bonus is preserved — IUD only suppresses SA eligibility.
    _sa_is_flanking = is_flanking
    if is_flanking and "improved_uncanny_dodge" in target.get(EF.FEATS, []):
        _attacker_rogue = attacker.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
        _target_iud_base = (
            target.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
            + target.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)
        )
        if _attacker_rogue < _target_iud_base + 4:
            _sa_is_flanking = False  # Flanking suppressed for sneak attack eligibility

    # WO-050B: Check sneak attack eligibility (computed once per full attack)
    from aidm.core.sneak_attack import is_sneak_attack_eligible, get_sneak_attack_dice
    sa_eligible, sa_reason = is_sneak_attack_eligible(
        world_state, intent.attacker_id, intent.target_id,
        is_flanking=_sa_is_flanking,
    )
    sa_dice = get_sneak_attack_dice(attacker) if sa_eligible else 0

    # WO-048: Get applicable Damage Reduction
    # WO-ENGINE-DR-001: Extract weapon bypass flags for accurate DR calculation
    from aidm.core.damage_reduction import get_applicable_dr, extract_weapon_bypass_flags
    is_magic_weapon, weapon_material, weapon_alignment, weapon_enhancement = \
        extract_weapon_bypass_flags(intent.weapon, attacker)
    dr_amount = get_applicable_dr(
        world_state, intent.target_id, intent.weapon.damage_type,
        is_magic_weapon=is_magic_weapon,
        weapon_material=weapon_material,
        weapon_alignment=weapon_alignment,
        weapon_enhancement=weapon_enhancement,
    )

    # WO-049: Get miss chance from concealment (PHB p.152)
    from aidm.core.concealment import get_miss_chance
    miss_chance_percent = get_miss_chance(world_state, intent.target_id)

    # Get target AC (base AC + condition modifiers + cover bonus) — WO-FIX-003
    base_ac = target.get(EF.AC, 10)
    # CP-16: melee/ranged differentiated condition AC
    is_melee = not feat_context.get("is_ranged", False)
    if is_melee and defender_modifiers.ac_modifier_melee != 0:
        condition_ac = defender_modifiers.ac_modifier_melee
    elif not is_melee and defender_modifiers.ac_modifier_ranged != 0:
        condition_ac = defender_modifiers.ac_modifier_ranged
    else:
        condition_ac = defender_modifiers.ac_modifier
    target_ac = base_ac + condition_ac + cover_result.ac_bonus

    hp_current = target.get(EF.HP_CURRENT, 0)

    # PHB p.113: STR modifier applies to melee damage
    str_modifier = attacker.get(EF.STR_MOD, 0)

    # CP-21: Detect two-weapon fighting and compute penalties (PHB p.160)
    is_twf = intent.off_hand_weapon is not None
    main_penalty = 0
    off_penalty = 0
    if is_twf:
        main_penalty, off_penalty = _compute_twf_penalties(attacker, intent.off_hand_weapon)

    # Calculate iterative attacks — apply TWF main-hand penalty if applicable
    raw_attack_bonuses = calculate_iterative_attacks(intent.base_attack_bonus)
    attack_bonuses = [b + main_penalty for b in raw_attack_bonuses]

    # WO-ENGINE-RAPID-SHOT-001: Rapid Shot extra attack (PHB p.99)
    # Penalty (-2 to all attacks) already handled by feat_resolver.get_attack_modifier().
    _attacker_feats = attacker.get(EF.FEATS, [])
    if "rapid_shot" in _attacker_feats and intent.weapon.is_ranged:
        raw_attack_bonuses = list(raw_attack_bonuses)  # ensure mutable
        raw_attack_bonuses.append(raw_attack_bonuses[0])  # extra attack at highest BAB
        attack_bonuses = [b + main_penalty for b in raw_attack_bonuses]  # rebuild with extra

    # WO-ENGINE-WEAPON-FOCUS-001: Weapon Focus +1 attack bonus (PHB p.102)
    # Feat key: f"weapon_focus_{weapon_type}" (e.g. "weapon_focus_one-handed")
    _wf_bonus = 1 if f"weapon_focus_{intent.weapon.weapon_type}" in _attacker_feats else 0

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
            "condition_ac_modifier": condition_ac,  # CP-16
            "mounted_bonus": mounted_bonus,  # CP-18A
            "terrain_higher_ground": terrain_higher_ground,  # CP-19
            "cover_type": cover_result.cover_type,  # CP-19
            "cover_ac_bonus": cover_result.ac_bonus,  # CP-19
            "feat_attack_modifier": feat_attack_modifier,  # WO-034
            "feat_damage_modifier": feat_damage_modifier,  # WO-034
            "flanking_bonus": flanking_bonus,  # PHB p.153
            "is_flanking": is_flanking,  # PHB p.153
            "flanking_ally_ids": flanking_ally_ids,  # PHB p.153
            "sneak_attack_eligible": sa_eligible,  # WO-050B
            "sneak_attack_dice": sa_dice,  # WO-050B
            "sneak_attack_reason": sa_reason,  # WO-050B
            "dr_amount": dr_amount,  # WO-048
            "miss_chance_percent": miss_chance_percent,  # WO-049
            "target_base_ac": base_ac,  # WO-FIX-003
            "target_ac": target_ac,  # WO-FIX-003: fully adjusted AC
            "is_twf": is_twf,  # CP-21
            "twf_main_penalty": main_penalty,  # CP-21
            "twf_off_penalty": off_penalty,  # CP-21
        },
        citations=[{"source_id": "681f92bc94ff", "page": 143}]  # PHB full attack
    ))
    current_event_id += 1

    # Resolve each attack in sequence
    # WO-FIX-02 (BUG-2): Track HP per-attack and break on defeat
    total_damage = 0
    total_dr_absorbed = 0  # WO-ENGINE-DR-001: accumulate per-hit DR
    current_hp = hp_current
    attacks_executed = 0

    # WO-ENGINE-WEAPON-PROFICIENCY-001: Non-proficiency penalty (PHB p.113) — compute once per full attack
    from aidm.core.attack_resolver import _is_weapon_proficient as _wp_proficient_check
    _prof_proficient = _wp_proficient_check(attacker, intent.weapon)

    for attack_index, penalized_bonus in enumerate(attack_bonuses):
        # Raw BAB for this iterative (without TWF penalty) — for audit trail
        raw_bab = raw_attack_bonuses[attack_index]
        # WO-FIX-003: Apply all modifiers to each iterative attack bonus
        adjusted_attack_bonus = (
            penalized_bonus +
            attacker_modifiers.attack_modifier +
            mounted_bonus +
            terrain_higher_ground +
            feat_attack_modifier +
            flanking_bonus +
            _favored_enemy_bonus +  # WO-ENGINE-FAVORED-ENEMY-001: ranger favored enemy (PHB p.47)
            intent.weapon.enhancement_bonus  # WO-ENGINE-WEAPON-ENHANCEMENT-001: magic weapon (PHB p.224)
            + (0 if _prof_proficient else -4)  # WO-ENGINE-WEAPON-PROFICIENCY-001: PHB p.113
            + _wf_bonus  # WO-ENGINE-WEAPON-FOCUS-001: Weapon Focus +1 attack (PHB p.102)
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
            base_attack_bonus_raw=raw_bab,
            condition_attack_modifier=attacker_modifiers.attack_modifier,
            mounted_bonus=mounted_bonus,
            terrain_higher_ground=terrain_higher_ground,
            feat_attack_modifier=feat_attack_modifier,
            target_base_ac=base_ac,
            target_ac_modifier=condition_ac,
            cover_type=cover_result.cover_type,
            cover_ac_bonus=cover_result.ac_bonus,
            dr_amount=dr_amount,
            miss_chance_percent=miss_chance_percent,
            flanking_bonus=flanking_bonus,
            is_flanking=is_flanking,
            flanking_ally_ids=flanking_ally_ids,
            sneak_attack_dice=sa_dice,
            sneak_attack_eligible=sa_eligible,
            sneak_attack_reason=sa_reason,
            favored_enemy_bonus=_favored_enemy_bonus,  # WO-ENGINE-FAVORED-ENEMY-001
            attacker_feats=_attacker_feats,  # WO-ENGINE-IMPROVED-CRITICAL-001
        )

        events.extend(attack_events)
        total_damage += damage
        # WO-ENGINE-DR-001: accumulate DR absorbed from damage_roll event
        for ev in attack_events:
            if ev.event_type == "damage_roll":
                total_dr_absorbed += ev.payload.get("damage_reduced", 0)
        current_hp -= damage
        attacks_executed += 1

        # WO-ENGINE-CLEAVE-WIRE-001: Cleave bonus attack on kill within full attack (PHB p.92/94)
        if current_hp <= 0 and damage > 0:
            from aidm.core.feat_resolver import can_use_cleave, get_cleave_limit
            from aidm.core.attack_resolver import _find_cleave_target
            from aidm.schemas.attack import AttackIntent as _AttackIntent
            _cl_attacker = attacker  # already bound above
            if can_use_cleave(_cl_attacker, intent.target_id, world_state):
                _cl_limit = get_cleave_limit(_cl_attacker)
                _cl_used_set = set()
                if world_state.active_combat is not None:
                    _cl_used_set = set(world_state.active_combat.get("cleave_used_this_turn", set()))
                _cl_already = intent.attacker_id in _cl_used_set
                if _cl_limit is None or not _cl_already:
                    _cl_target_id = _find_cleave_target(intent.attacker_id, intent.target_id, world_state)
                    if _cl_target_id is not None:
                        if _cl_limit == 1 and world_state.active_combat is not None:
                            world_state.active_combat["cleave_used_this_turn"] = _cl_used_set | {intent.attacker_id}
                        _feat_name = "great_cleave" if _cl_limit is None else "cleave"
                        events.append(Event(
                            event_id=current_event_id,
                            event_type="cleave_triggered",
                            timestamp=timestamp + 0.5 * attacks_executed + 0.35,
                            payload={
                                "attacker_id": intent.attacker_id,
                                "killed_target_id": intent.target_id,
                                "cleave_target_id": _cl_target_id,
                                "feat": _feat_name,
                            },
                            citations=[{"source_id": "681f92bc94ff", "page": 92}],
                        ))
                        current_event_id += 1
                        _cleave_bonus_intent = _AttackIntent(
                            attacker_id=intent.attacker_id,
                            target_id=_cl_target_id,
                            weapon=intent.weapon,
                            attack_bonus=adjusted_attack_bonus,
                        )
                        from aidm.core.attack_resolver import resolve_attack as _resolve_atk
                        _cl_events = _resolve_atk(
                            intent=_cleave_bonus_intent,
                            world_state=world_state,
                            rng=rng,
                            next_event_id=current_event_id,
                            timestamp=timestamp + 0.5 * attacks_executed + 0.4,
                        )
                        events.extend(_cl_events)
                        current_event_id += len(_cl_events)

        # WO-FIX-02 (BUG-2): Stop attacking defeated targets
        if current_hp <= 0 and damage > 0:
            break  # Target defeated -- remaining attacks not executed

    # CP-21: Off-hand attack(s) after main-hand sequence
    if is_twf and current_hp > 0:
        off_hand_bab = intent.base_attack_bonus + off_penalty
        off_hand_adjusted = (
            off_hand_bab +
            attacker_modifiers.attack_modifier +
            mounted_bonus +
            terrain_higher_ground +
            feat_attack_modifier +
            flanking_bonus
            + (0 if _wp_proficient_check(attacker, intent.off_hand_weapon) else -4)  # WO-ENGINE-WEAPON-PROFICIENCY-001
        )
        # Off-hand grip — half STR for damage (PHB p.160)
        off_str_mod = str_modifier // 2 if str_modifier > 0 else str_modifier

        oh_events, current_event_id, oh_damage = resolve_single_attack_with_critical(
            attacker_id=intent.attacker_id,
            target_id=intent.target_id,
            attack_bonus=off_hand_adjusted,
            weapon=intent.off_hand_weapon,
            target_ac=target_ac,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=timestamp + 0.5 * attacks_executed,
            attack_index=attacks_executed,
            str_modifier=off_str_mod,  # PHB p.160: half STR for off-hand
            condition_damage_modifier=attacker_modifiers.damage_modifier,
            feat_damage_modifier=0,  # feat damage doesn't apply to off-hand by default
            base_attack_bonus_raw=off_hand_bab,
            condition_attack_modifier=attacker_modifiers.attack_modifier,
            mounted_bonus=mounted_bonus,
            terrain_higher_ground=terrain_higher_ground,
            feat_attack_modifier=0,
            target_base_ac=base_ac,
            target_ac_modifier=condition_ac,
            cover_type=cover_result.cover_type,
            cover_ac_bonus=cover_result.ac_bonus,
            dr_amount=dr_amount,
            miss_chance_percent=miss_chance_percent,
            flanking_bonus=flanking_bonus,
            is_flanking=is_flanking,
            flanking_ally_ids=flanking_ally_ids,
            sneak_attack_dice=sa_dice,
            sneak_attack_eligible=sa_eligible,
            sneak_attack_reason=sa_reason,
            favored_enemy_bonus=_favored_enemy_bonus,  # WO-ENGINE-FAVORED-ENEMY-001
            attacker_feats=_attacker_feats,  # WO-ENGINE-IMPROVED-CRITICAL-001
        )
        events.extend(oh_events)
        total_damage += oh_damage
        for ev in oh_events:
            if ev.event_type == "damage_roll":
                total_dr_absorbed += ev.payload.get("damage_reduced", 0)
        current_hp -= oh_damage
        attacks_executed += 1

        # CP-21: Improved TWF — second off-hand attack at BAB-5+off_penalty
        feats = attacker.get(EF.FEATS, [])
        if "Improved Two-Weapon Fighting" in feats and current_hp > 0:
            itwf_bab = intent.base_attack_bonus - 5 + off_penalty
            itwf_adjusted = (
                itwf_bab +
                attacker_modifiers.attack_modifier +
                mounted_bonus +
                terrain_higher_ground +
                feat_attack_modifier +
                flanking_bonus
                + (0 if _wp_proficient_check(attacker, intent.off_hand_weapon) else -4)  # WO-ENGINE-WEAPON-PROFICIENCY-001
            )
            itwf_events, current_event_id, itwf_damage = resolve_single_attack_with_critical(
                attacker_id=intent.attacker_id,
                target_id=intent.target_id,
                attack_bonus=itwf_adjusted,
                weapon=intent.off_hand_weapon,
                target_ac=target_ac,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.5 * attacks_executed,
                attack_index=attacks_executed,
                str_modifier=off_str_mod,
                condition_damage_modifier=attacker_modifiers.damage_modifier,
                feat_damage_modifier=0,
                base_attack_bonus_raw=itwf_bab,
                condition_attack_modifier=attacker_modifiers.attack_modifier,
                mounted_bonus=mounted_bonus,
                terrain_higher_ground=terrain_higher_ground,
                feat_attack_modifier=0,
                target_base_ac=base_ac,
                target_ac_modifier=condition_ac,
                cover_type=cover_result.cover_type,
                cover_ac_bonus=cover_result.ac_bonus,
                dr_amount=dr_amount,
                miss_chance_percent=miss_chance_percent,
                flanking_bonus=flanking_bonus,
                is_flanking=is_flanking,
                flanking_ally_ids=flanking_ally_ids,
                sneak_attack_dice=sa_dice,
                sneak_attack_eligible=sa_eligible,
                sneak_attack_reason=sa_reason,
                favored_enemy_bonus=_favored_enemy_bonus,  # WO-ENGINE-FAVORED-ENEMY-001
                attacker_feats=_attacker_feats,  # WO-ENGINE-IMPROVED-CRITICAL-001
            )
            events.extend(itwf_events)
            total_damage += itwf_damage
            for ev in itwf_events:
                if ev.event_type == "damage_roll":
                    total_dr_absorbed += ev.payload.get("damage_reduced", 0)
            current_hp -= itwf_damage
            attacks_executed += 1

        # Greater Two-Weapon Fighting: third off-hand attack at BAB-10+off_penalty
        # PHB p.96: GTWF grants a third off-hand attack (same chain as ITWF at -5, GTWF at -10)
        # Feat string: "Greater Two-Weapon Fighting" (Title Case — matches TWF/ITWF convention)
        if "Greater Two-Weapon Fighting" in feats and current_hp > 0:
            gtwf_bab = intent.base_attack_bonus - 10 + off_penalty
            gtwf_adjusted = (
                gtwf_bab +
                attacker_modifiers.attack_modifier +
                mounted_bonus +
                terrain_higher_ground +
                feat_attack_modifier +
                flanking_bonus
                + (0 if _wp_proficient_check(attacker, intent.off_hand_weapon) else -4)  # WO-ENGINE-WEAPON-PROFICIENCY-001
            )
            gtwf_events, current_event_id, gtwf_damage = resolve_single_attack_with_critical(
                attacker_id=intent.attacker_id,
                target_id=intent.target_id,
                attack_bonus=gtwf_adjusted,
                weapon=intent.off_hand_weapon,
                target_ac=target_ac,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.5 * attacks_executed,
                attack_index=attacks_executed,
                str_modifier=off_str_mod,
                condition_damage_modifier=attacker_modifiers.damage_modifier,
                feat_damage_modifier=0,
                base_attack_bonus_raw=gtwf_bab,
                condition_attack_modifier=attacker_modifiers.attack_modifier,
                mounted_bonus=mounted_bonus,
                terrain_higher_ground=terrain_higher_ground,
                feat_attack_modifier=0,
                target_base_ac=base_ac,
                target_ac_modifier=condition_ac,
                cover_type=cover_result.cover_type,
                cover_ac_bonus=cover_result.ac_bonus,
                dr_amount=dr_amount,
                miss_chance_percent=miss_chance_percent,
                flanking_bonus=flanking_bonus,
                is_flanking=is_flanking,
                flanking_ally_ids=flanking_ally_ids,
                sneak_attack_dice=sa_dice,
                sneak_attack_eligible=sa_eligible,
                sneak_attack_reason=sa_reason,
                favored_enemy_bonus=_favored_enemy_bonus,  # WO-ENGINE-FAVORED-ENEMY-001
                attacker_feats=_attacker_feats,  # WO-ENGINE-IMPROVED-CRITICAL-001
            )
            events.extend(gtwf_events)
            total_damage += gtwf_damage
            for ev in gtwf_events:
                if ev.event_type == "damage_roll":
                    total_dr_absorbed += ev.payload.get("damage_reduced", 0)
            current_hp -= gtwf_damage
            attacks_executed += 1

    # Apply accumulated damage to HP
    # WO-ENGINE-DR-001: total_damage is already post-DR (sum of final_damage per hit)
    if total_damage > 0:
        hp_before = hp_current
        hp_after = hp_before - total_damage

        # Emit hp_changed event
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=timestamp + 0.5 * attacks_executed,
            payload={
                "entity_id": intent.target_id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "delta": -total_damage,
                "source": "full_attack_damage",
                "dr_absorbed": total_dr_absorbed,  # WO-ENGINE-DR-001
            }
        ))
        current_event_id += 1

        # WO-ENGINE-DEATH-DYING-001: Three-band defeat check (PHB p.145)
        from aidm.core.dying_resolver import resolve_hp_transition
        trans_events, _field_updates = resolve_hp_transition(
            entity_id=intent.target_id,
            old_hp=hp_before,
            new_hp=hp_after,
            source="full_attack_damage",
            world_state=world_state,
            next_event_id=current_event_id,
            timestamp=timestamp + 0.5 * attacks_executed + 0.1,
        )
        events.extend(trans_events)
        current_event_id += len(trans_events)

    # Emit full_attack_end event
    events.append(Event(
        event_id=current_event_id,
        event_type="full_attack_end",
        timestamp=timestamp + 0.5 * attacks_executed + 0.2,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "total_damage": total_damage,
            "num_hits": sum(1 for e in events if e.event_type == "damage_roll"),
            "num_attacks": attacks_executed
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
    # Deep copy entities — must use deepcopy, not shallow .copy(),
    # because entity dicts contain nested structures (conditions lists, etc.)
    # that would be shared references with shallow copy.
    from copy import deepcopy
    entities = {eid: deepcopy(e) for eid, e in world_state.entities.items()}

    for event in events:
        if event.event_type == "hp_changed":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.HP_CURRENT] = event.payload["hp_after"]

        elif event.event_type == "entity_defeated":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DEFEATED] = True
                entities[entity_id][EF.DYING] = False
                entities[entity_id][EF.DISABLED] = False
                entities[entity_id][EF.STABLE] = False

        elif event.event_type == "entity_disabled":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DISABLED] = True
                entities[entity_id][EF.DYING] = False

        elif event.event_type == "entity_dying":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DYING] = True
                entities[entity_id][EF.DISABLED] = False
                entities[entity_id][EF.DEFEATED] = False

        elif event.event_type == "entity_revived":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DYING] = False
                entities[entity_id][EF.DISABLED] = False
                entities[entity_id][EF.STABLE] = False

    # Return new WorldState
    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None
    )
