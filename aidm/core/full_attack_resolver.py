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
from dataclasses import dataclass, field, replace

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.attack import AttackIntent
from aidm.core.attack_resolver import parse_damage_dice, roll_dice, resolve_attack
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

    # WO-ENGINE-WF-SCHEMA-FIX-001: extract canonical weapon name from EF.WEAPON dict
    _fa_ef_weapon = attacker.get(EF.WEAPON, {})
    _fa_weapon_name = (
        _fa_ef_weapon.get("name", "").lower().replace(" ", "_")
        if isinstance(_fa_ef_weapon, dict)
        else str(_fa_ef_weapon).lower().replace(" ", "_")
    )
    feat_context = {
        "weapon_name": _fa_weapon_name,  # WO-ENGINE-WF-SCHEMA-FIX-001: canonical name from entity dict
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

    # WO-050B: Check sneak attack eligibility (for full_attack_start event payload)
    # NOTE: IUD suppression is handled per-hit inside resolve_attack() (FAGU delegation).
    from aidm.core.sneak_attack import is_sneak_attack_eligible, get_sneak_attack_dice
    sa_eligible, sa_reason = is_sneak_attack_eligible(
        world_state, intent.attacker_id, intent.target_id,
        is_flanking=is_flanking,
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

    # WO-ENGINE-WEAPON-FOCUS-001: _wf_bonus removed — resolve_attack() handles it per-hit (FAGU)

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

    # FAGU: Working WorldState copy for inter-attack HP tracking.
    # resolve_attack() reads HP from world_state; we update _ws between attacks
    # so Cleave detection and per-hit hp_changed events reflect actual cumulative HP.
    _ws = world_state

    for attack_index, penalized_bonus in enumerate(attack_bonuses):
        # FAGU: Build per-iterative AttackIntent and delegate to resolve_attack().
        # resolve_attack() handles ALL 21 mechanics previously missing from FAR
        # (Inspire Courage, Finesse, Neg Levels, Fight Def, Broken, vs-Blinded,
        #  Blind attacker, CE, Precise Shot, DEX denial, TWD AC, CE AC, Monk WIS AC,
        #  Deflection, Feint, Inspire dmg, Disarmed, EqMelded, Blind-Fight, MassiveDmg).
        iter_intent = AttackIntent(
            attacker_id=intent.attacker_id,
            target_id=intent.target_id,
            weapon=intent.weapon,
            attack_bonus=penalized_bonus,  # iterative BAB (base_attack_bonus - 5*i + twf_penalty)
            power_attack_penalty=intent.power_attack_penalty,
        )
        attack_events = resolve_attack(
            intent=iter_intent,
            world_state=_ws,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=timestamp + 0.5 * attack_index,
        )
        events.extend(attack_events)
        current_event_id += len(attack_events)
        attacks_executed += 1

        _hit_damage = next(
            (e.payload.get("final_damage", 0) for e in attack_events
             if e.event_type == "damage_roll"),
            0
        )
        total_damage += _hit_damage
        # WO-ENGINE-DR-001: accumulate DR absorbed from damage_roll event
        for ev in attack_events:
            if ev.event_type == "damage_roll":
                total_dr_absorbed += ev.payload.get("damage_reduced", 0)
        current_hp -= _hit_damage

        # FAGU: Update _ws target HP so next resolve_attack() call sees correct HP
        # (enables Cleave detection and per-hit hp_changed events to be accurate)
        if _hit_damage > 0:
            _tgt = dict(_ws.entities.get(intent.target_id, {}))
            _tgt[EF.HP_CURRENT] = current_hp
            _ws = WorldState(
                ruleset_version=_ws.ruleset_version,
                entities={**_ws.entities, intent.target_id: _tgt},
                active_combat=_ws.active_combat,
            )

        # WO-FIX-02 (BUG-2): Stop attacking defeated targets
        # Cleave handled inside resolve_attack() automatically (FAGU)
        if current_hp <= 0:
            break

    # CP-21: Off-hand attack(s) after main-hand sequence
    if is_twf and current_hp > 0:
        off_hand_bab = intent.base_attack_bonus + off_penalty
        # FAGU: Ensure off-hand weapon has grip="off-hand" so resolve_attack() applies half-STR
        # to damage correctly (PHB p.160). Default weapon grip may be "one-handed".
        off_weapon = (
            replace(intent.off_hand_weapon, grip="off-hand")
            if intent.off_hand_weapon.grip != "off-hand"
            else intent.off_hand_weapon
        )

        oh_intent = AttackIntent(
            attacker_id=intent.attacker_id,
            target_id=intent.target_id,
            weapon=off_weapon,
            attack_bonus=off_hand_bab,  # base_attack_bonus + off_penalty
            power_attack_penalty=0,
        )
        oh_events = resolve_attack(
            intent=oh_intent,
            world_state=_ws,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=timestamp + 0.5 * attacks_executed,
        )
        events.extend(oh_events)
        current_event_id += len(oh_events)
        attacks_executed += 1

        _oh_damage = next(
            (e.payload.get("final_damage", 0) for e in oh_events
             if e.event_type == "damage_roll"),
            0
        )
        total_damage += _oh_damage
        for ev in oh_events:
            if ev.event_type == "damage_roll":
                total_dr_absorbed += ev.payload.get("damage_reduced", 0)
        current_hp -= _oh_damage
        if _oh_damage > 0:
            _tgt = dict(_ws.entities.get(intent.target_id, {}))
            _tgt[EF.HP_CURRENT] = current_hp
            _ws = WorldState(
                ruleset_version=_ws.ruleset_version,
                entities={**_ws.entities, intent.target_id: _tgt},
                active_combat=_ws.active_combat,
            )

        # CP-21: Improved TWF — second off-hand attack at BAB-5+off_penalty
        feats = attacker.get(EF.FEATS, [])
        if "Improved Two-Weapon Fighting" in feats and current_hp > 0:
            itwf_bab = intent.base_attack_bonus - 5 + off_penalty
            itwf_intent = AttackIntent(
                attacker_id=intent.attacker_id,
                target_id=intent.target_id,
                weapon=off_weapon,
                attack_bonus=itwf_bab,
                power_attack_penalty=0,
            )
            itwf_events = resolve_attack(
                intent=itwf_intent,
                world_state=_ws,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.5 * attacks_executed,
            )
            events.extend(itwf_events)
            current_event_id += len(itwf_events)
            attacks_executed += 1

            _itwf_damage = next(
                (e.payload.get("final_damage", 0) for e in itwf_events
                 if e.event_type == "damage_roll"),
                0
            )
            total_damage += _itwf_damage
            for ev in itwf_events:
                if ev.event_type == "damage_roll":
                    total_dr_absorbed += ev.payload.get("damage_reduced", 0)
            current_hp -= _itwf_damage
            if _itwf_damage > 0:
                _tgt = dict(_ws.entities.get(intent.target_id, {}))
                _tgt[EF.HP_CURRENT] = current_hp
                _ws = WorldState(
                    ruleset_version=_ws.ruleset_version,
                    entities={**_ws.entities, intent.target_id: _tgt},
                    active_combat=_ws.active_combat,
                )

        # Greater Two-Weapon Fighting: third off-hand attack at BAB-10+off_penalty
        # PHB p.96: GTWF grants a third off-hand attack (same chain as ITWF at -5, GTWF at -10)
        # Feat string: "Greater Two-Weapon Fighting" (Title Case — matches TWF/ITWF convention)
        if "Greater Two-Weapon Fighting" in feats and current_hp > 0:
            gtwf_bab = intent.base_attack_bonus - 10 + off_penalty
            gtwf_intent = AttackIntent(
                attacker_id=intent.attacker_id,
                target_id=intent.target_id,
                weapon=off_weapon,
                attack_bonus=gtwf_bab,
                power_attack_penalty=0,
            )
            gtwf_events = resolve_attack(
                intent=gtwf_intent,
                world_state=_ws,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.5 * attacks_executed,
            )
            events.extend(gtwf_events)
            current_event_id += len(gtwf_events)
            attacks_executed += 1

            _gtwf_damage = next(
                (e.payload.get("final_damage", 0) for e in gtwf_events
                 if e.event_type == "damage_roll"),
                0
            )
            total_damage += _gtwf_damage
            for ev in gtwf_events:
                if ev.event_type == "damage_roll":
                    total_dr_absorbed += ev.payload.get("damage_reduced", 0)
            current_hp -= _gtwf_damage

    # FAGU: Per-hit hp_changed + resolve_hp_transition now handled by resolve_attack() per-hit.
    # FAR's cumulative hp_changed removed — event applier processes AR's per-hit events.
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
