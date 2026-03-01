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
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.attack import AttackIntent
from aidm.core.conditions import get_condition_modifiers
from aidm.core.targeting_resolver import evaluate_target_legality, get_entity_position  # CP-18A-T&V
from aidm.schemas.entity_fields import EF


# =============================================================================
# WO-ENGINE-WEAPON-PROFICIENCY-001: Non-proficiency penalty (PHB p.113)
# =============================================================================

# Classes proficient with ALL martial weapons (PHB p.113)
_MARTIAL_PROFICIENT_CLASSES = frozenset({"barbarian", "fighter", "paladin", "ranger"})


def _is_weapon_proficient(attacker: dict, weapon) -> bool:
    """Return True if attacker is proficient with weapon (no -4 non-proficiency penalty).

    PHB p.113: A character who uses a weapon with which he or she is not
    proficient takes a -4 penalty on attack rolls.

    Proficiency rules:
    - Natural attacks: always proficient (weapon_type='natural')
    - proficiency_category=None: unknown → assume proficient (safe default)
    - 'simple': always proficient for all classes
    - 'martial': proficient if class in martial list OR has martial_weapon_proficiency feat
    - 'exotic': proficient if has any exotic_weapon_proficiency* feat

    Args:
        attacker: Entity dict of the attacker.
        weapon: Weapon dataclass instance.

    Returns:
        True if proficient (no -4 penalty), False if non-proficient (-4 applies).
    """
    # Natural attacks: always proficient regardless of category
    if getattr(weapon, "weapon_type", "") == "natural":
        return True

    prof_cat = getattr(weapon, "proficiency_category", None)

    # Unknown proficiency: assume proficient (backwards-compatible safe default)
    if prof_cat is None:
        return True

    # Simple: all classes are proficient (PHB p.113)
    if prof_cat == "simple":
        return True

    attacker_feats = attacker.get(EF.FEATS, [])
    class_levels = attacker.get(EF.CLASS_LEVELS, {})

    # Martial: proficient if class is in martial list OR has feat
    if prof_cat == "martial":
        if any(cls in _MARTIAL_PROFICIENT_CLASSES for cls in class_levels):
            return True
        if "martial_weapon_proficiency" in attacker_feats:
            return True
        return False

    # Exotic: proficient only if has matching exotic_weapon_proficiency feat
    if prof_cat == "exotic":
        if any(feat.startswith("exotic_weapon_proficiency") for feat in attacker_feats):
            return True
        return False

    # Unknown category string: assume proficient
    return True


def _find_cleave_target(attacker_id: str, killed_id: str, world_state: "WorldState"):
    """Find an adjacent enemy to target with a Cleave bonus attack.

    PHB p.92: the bonus attack must be against a foe *adjacent to the killed
    creature*.  If position data is unavailable for any entity we fall back to
    the legacy "first living hostile" behaviour so that position-free test
    scenarios continue to work.

    WO-ENGINE-CLEAVE-ADJACENCY-001
    """
    from aidm.schemas.position import Position

    attacker = world_state.entities.get(attacker_id)
    killed = world_state.entities.get(killed_id)
    if attacker is None:
        return None

    attacker_team = attacker.get(EF.TEAM, "")

    # Resolve killed creature's position (may be None if not tracked)
    killed_pos = None
    if killed is not None:
        _killed_pos_raw = killed.get(EF.POSITION)
        if _killed_pos_raw is not None:
            killed_pos = (
                Position(**_killed_pos_raw)
                if isinstance(_killed_pos_raw, dict)
                else _killed_pos_raw
            )

    for eid, entity in world_state.entities.items():
        if eid == attacker_id or eid == killed_id:
            continue
        if entity.get(EF.DEFEATED, False):
            continue
        if entity.get(EF.HP_CURRENT, 0) <= 0:
            continue
        if entity.get(EF.TEAM, "") == attacker_team:
            continue
        # Adjacency check: candidate must be adjacent to the killed creature.
        # If killed position is unknown, skip the check (fail-open / legacy).
        if killed_pos is not None:
            _cand_pos_raw = entity.get(EF.POSITION)
            if _cand_pos_raw is not None:
                _cand_pos = (
                    Position(**_cand_pos_raw)
                    if isinstance(_cand_pos_raw, dict)
                    else _cand_pos_raw
                )
                if not killed_pos.is_adjacent_to(_cand_pos):
                    continue  # Not adjacent to killed creature — skip
        return eid
    return None

def _is_target_in_melee(target_id: str, attacker_team: str, world_state: "WorldState") -> bool:
    """Check if target is engaged in melee with a friendly of the attacker.

    PHB p.140: -4 penalty on ranged attacks if target is in melee with friendly.
    Target is "in melee" if any non-defeated ally of the attacker is adjacent (within 5 ft).
    """
    from aidm.schemas.position import Position

    target = world_state.entities.get(target_id)
    if target is None:
        return False

    target_pos_raw = target.get(EF.POSITION)
    if target_pos_raw is None:
        return False
    target_pos = Position(**target_pos_raw) if isinstance(target_pos_raw, dict) else target_pos_raw

    for eid, entity in world_state.entities.items():
        if eid == target_id:
            continue
        if entity.get(EF.DEFEATED, False):
            continue
        if entity.get(EF.TEAM, "") != attacker_team:
            continue  # Only allies of the ranged attacker matter
        pos_raw = entity.get(EF.POSITION)
        if pos_raw is None:
            continue
        pos = Position(**pos_raw) if isinstance(pos_raw, dict) else pos_raw
        if target_pos.is_adjacent_to(pos):
            return True
    return False


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


def roll_dice(num_dice: int, die_size: int, rng: RNGProvider) -> List[int]:
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



# WO-ENGINE-UNCANNY-DODGE-001: Helper — Uncanny Dodge flat-footed DEX retention (PHB p.51/47/26)
# IMMOBILIZING conditions (paralyzed, stunned, helpless, unconscious, pinned, blinded) still deny DEX.
# Only the flat-footed DEX denial is bypassed by Uncanny Dodge.
_UNCANNY_DODGE_IMMOBILIZING_CONDITIONS = {
    "paralyzed",
    "stunned",
    "helpless",
    "unconscious",
    "pinned",
    "blinded",
}


def _target_retains_dex_via_uncanny_dodge(target: dict) -> bool:
    """Return True if target has Uncanny Dodge AND is not additionally immobilized.

    Called only when defender_modifiers.loses_dex_to_ac is True.
    Uncanny Dodge (PHB p.51/47/26) lets the entity keep DEX bonus when flat-footed.
    Exception: immobilized conditions (paralyzed, stunned, etc.) still deny DEX.

    WO-ENGINE-UNCANNY-DODGE-001
    """
    class_levels = target.get(EF.CLASS_LEVELS, {}) or {}
    # WO-ENGINE-UNCANNY-DODGE-CLASS-FIX-001: PHB p.26 barb L2, PHB p.50 rogue L4
    # Rangers do NOT get Uncanny Dodge in D&D 3.5e (PHB p.48)
    _UD_THRESHOLDS = {"barbarian": 2, "rogue": 4}
    has_uncanny_dodge = any(
        class_levels.get(cls, 0) >= lvl
        for cls, lvl in _UD_THRESHOLDS.items()
    )
    if not has_uncanny_dodge:
        return False

    # Check for immobilizing conditions — these override Uncanny Dodge
    conditions = target.get(EF.CONDITIONS, {}) or {}
    for cond_key in conditions:
        if cond_key in _UNCANNY_DODGE_IMMOBILIZING_CONDITIONS:
            return False  # Immobilized: still deny DEX even with Uncanny Dodge

    return True  # Uncanny Dodge active, not immobilized -> retain DEX


def resolve_attack(
    intent: AttackIntent,
    world_state: WorldState,
    rng: RNGProvider,
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

    # WO-ENGINE-WILD-SHAPE-001: Block weapon attacks while equipment is melded (PHB p.36)
    _attacker_entity = world_state.entities.get(intent.attacker_id, {})
    if _attacker_entity.get(EF.EQUIPMENT_MELDED, False):
        events.append(Event(
            event_id=current_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.attacker_id,
                "target_id": intent.target_id,
                "intent_type": "AttackIntent",
                "reason": "equipment_melded",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 36}],
        ))
        return events

    # CP-16: Get condition modifiers for attacker and defender
    attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
    defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")

    # WO-ENGINE-SUNDER-DISARM-FULL-001: DISARMED guard (PHB p.155)
    # A disarmed entity cannot make attacks with the disarmed weapon.
    attacker = world_state.entities[intent.attacker_id]
    if attacker.get(EF.DISARMED, False):
        events.append(Event(
            event_id=current_event_id,
            event_type="attack_denied",
            timestamp=timestamp,
            payload={
                "attacker_id": intent.attacker_id,
                "target_id": intent.target_id,
                "reason": "disarmed",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 155}],
        ))
        return events

    # WO-ENGINE-SUNDER-DISARM-FULL-001: WEAPON_BROKEN penalty applied in attack bonus below (-2)
    _weapon_broken_penalty = -2 if attacker.get(EF.WEAPON_BROKEN, False) else 0

    # CP-18A: Get mounted higher ground bonus
    from aidm.core.mounted_combat import get_mounted_attack_bonus
    mounted_bonus = get_mounted_attack_bonus(intent.attacker_id, intent.target_id, world_state)

    # CP-19: Get terrain higher ground bonus (stacks with mounted)
    from aidm.core.terrain_resolver import get_higher_ground_bonus, check_cover
    terrain_higher_ground = get_higher_ground_bonus(world_state, intent.attacker_id, intent.target_id)

    # CP-19: Check cover between attacker and defender
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
        "weapon_name": attacker.get(EF.WEAPON, "unknown"),  # WO-WAYPOINT-003: actual weapon name from entity
        "range_ft": range_ft,  # WO-WEAPON-PLUMBING-001: actual range from positions
        "is_ranged": intent.weapon.is_ranged,  # WO-WEAPON-PLUMBING-001: from weapon type
        "is_twf": False,  # TODO: Detect from attack intent
        "power_attack_penalty": intent.power_attack_penalty,  # WO-034-FIX: from intent
        "is_two_handed": intent.weapon.is_two_handed,  # WO-034-FIX: from weapon
        "grip": intent.weapon.grip,  # WO-ENGINE-POWER-ATTACK-001: for off-hand damage ratio
    }
    feat_attack_modifier = get_attack_modifier(attacker, target, feat_context)

    # WO-ENGINE-POWER-ATTACK-001: Validate Power Attack declaration (PHB p.98)
    _pa_penalty = intent.power_attack_penalty
    if _pa_penalty > 0:
        _pa_feats = attacker.get(EF.FEATS, [])
        if "power_attack" not in _pa_feats:
            events.append(Event(
                event_id=current_event_id,
                event_type="intent_validation_failed",
                timestamp=timestamp,
                payload={
                    "actor_id": intent.attacker_id,
                    "reason": "feat_requirement_not_met",
                    "feat": "power_attack",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 98}],
            ))
            return events
        _attacker_bab = attacker.get(EF.BAB, 0)
        if _pa_penalty > _attacker_bab:
            events.append(Event(
                event_id=current_event_id,
                event_type="intent_validation_failed",
                timestamp=timestamp,
                payload={
                    "actor_id": intent.attacker_id,
                    "reason": "penalty_exceeds_bab",
                    "power_attack_penalty": _pa_penalty,
                    "bab": _attacker_bab,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 98}],
            ))
            return events

    # Flanking: +2 melee attack bonus when attacker and ally on opposite sides (PHB p.153)
    from aidm.core.flanking import get_flanking_info
    flanking_bonus, is_flanking, flanking_ally_ids = get_flanking_info(
        world_state, intent.attacker_id, intent.target_id
    )

    # CP-17: Helpless auto-hit (PHB p.153) — melee attacks vs helpless targets auto-hit
    is_melee = not intent.weapon.is_ranged
    auto_hit_helpless = False
    if is_melee and defender_modifiers.auto_hit_if_helpless:
        auto_hit_helpless = True

    # Get target AC (base AC + condition modifiers + cover bonus)
    base_ac = target.get(EF.AC, 10)  # Default AC 10 if not specified
    # CP-17: loses_dex_to_ac — subtract DEX mod from AC when condition active
    # WO-ENGINE-UNCANNY-DODGE-001: Uncanny Dodge bypasses flat-footed DEX denial (PHB p.51/47/26)
    dex_penalty = 0
    if defender_modifiers.loses_dex_to_ac and not _target_retains_dex_via_uncanny_dodge(target):
        dex_mod = target.get(EF.DEX_MOD, 0)
        if dex_mod > 0:  # Only subtract positive DEX bonus (never penalize further)
            dex_penalty = -dex_mod
    # CP-16: condition modifier (melee/ranged differentiated), CP-19: cover bonus
    if is_melee and defender_modifiers.ac_modifier_melee != 0:
        condition_ac = defender_modifiers.ac_modifier_melee
    elif not is_melee and defender_modifiers.ac_modifier_ranged != 0:
        condition_ac = defender_modifiers.ac_modifier_ranged
    else:
        condition_ac = defender_modifiers.ac_modifier
    # WO-ENGINE-TWD-001: Fight defensively / total defense AC bonus (dodge type)
    _defender_temp_mods = target.get(EF.TEMPORARY_MODIFIERS, {}) or {}
    _fd_ac_bonus = _defender_temp_mods.get("fight_defensively_ac", 0)
    _td_ac_bonus = _defender_temp_mods.get("total_defense_ac", 0)
    _defend_ac_total = _fd_ac_bonus + _td_ac_bonus

    # WO-ENGINE-TWD-001: Two-Weapon Defense passive shield AC bonus (PHB p.102)
    from aidm.core.full_attack_resolver import _compute_twd_ac_bonus
    _twd_ac_bonus = _compute_twd_ac_bonus(target)

    # WO-ENGINE-COMBAT-EXPERTISE-001: CE dodge AC bonus on target (if target declared CE) (PHB p.92)
    _ce_ac_bonus = target.get(EF.COMBAT_EXPERTISE_BONUS, 0)

    # WO-ENGINE-FEINT-001: Check feint flat-footed marker (consumes on use)
    from aidm.core.feint_resolver import consume_feint_marker as _consume_feint
    world_state, _feint_active = _consume_feint(
        world_state, attacker_id=intent.attacker_id, target_id=intent.target_id
    )
    if _feint_active:
        # Feinted target is denied Dex to AC (same path as other denied-Dex cases)
        if not defender_modifiers.loses_dex_to_ac:
            dex_mod = target.get(EF.DEX_MOD, 0)
            if dex_mod > 0:
                dex_penalty = -dex_mod

    # WO-ENGINE-MONK-WIS-AC-001: Monk WIS bonus to AC (PHB p.41) — applies when unarmored
    _monk_wis_ac = 0
    _monk_level_target = target.get(EF.CLASS_LEVELS, {}).get("monk", 0)
    if _monk_level_target >= 1:
        _armor_bonus = target.get(EF.ARMOR_AC_BONUS, 0)
        # WO-ENGINE-ENCUMBRANCE-WIRE-001: Monk WIS AC also suppressed by medium+ load (PHB p.41)
        _monk_enc_load = target.get(EF.ENCUMBRANCE_LOAD, "light")
        if _armor_bonus == 0 and _monk_enc_load == "light":
            _monk_wis_ac = target.get(EF.MONK_WIS_AC_BONUS, 0)

    # WO-ENGINE-DEFLECTION-BONUS-001: Deflection bonus to AC (PHB p.136)
    # Applies vs ALL attacks including touch attacks (unlike armor/shield which touch bypasses).
    _deflection_ac = target.get(EF.DEFLECTION_BONUS, 0)

    # WO-ENGINE-RACIAL-DODGE-AC-001: Dwarf/gnome +4 dodge AC vs. giants (PHB p.15/17)
    # Dodge bonuses lost when flat-footed (PHB p.179).
    _racial_dodge_vs_giants = 0
    _attacker_creature_type = attacker.get(EF.CREATURE_TYPE, "")
    if _attacker_creature_type == "giant":
        _is_flat_footed = defender_modifiers.loses_dex_to_ac and not _target_retains_dex_via_uncanny_dodge(target)
        if not _is_flat_footed:
            _racial_dodge_vs_giants = target.get(EF.DODGE_BONUS_VS_GIANTS, 0)

    target_ac = base_ac + condition_ac + cover_result.ac_bonus + dex_penalty + _defend_ac_total + _twd_ac_bonus + _ce_ac_bonus + _monk_wis_ac + _deflection_ac + _racial_dodge_vs_giants  # WO-ENGINE-COMBAT-EXPERTISE-001, WO-ENGINE-MONK-WIS-AC-001, WO-ENGINE-DEFLECTION-BONUS-001, WO-ENGINE-RACIAL-DODGE-AC-001

    # WO-ENGINE-CONDITIONS-BLIND-DEAF-001: +2 attack bonus against blinded defender (PHB p.309)
    from aidm.core.condition_combat_resolver import is_blinded as _is_blinded
    _vs_blinded_bonus = 2 if _is_blinded(world_state, intent.target_id) else 0

    # WO-ENGINE-CONDITIONS-BLIND-DEAF-001: Blinded attacker has 50% miss chance (PHB p.309)
    # Check BEFORE the d20 roll — if miss, return early (no RNG consumed for d20/damage)
    if _is_blinded(world_state, intent.attacker_id):
        from aidm.core.condition_combat_resolver import check_blinded_miss as _check_blind
        _blind_miss, _blind_events = _check_blind(rng, intent.attacker_id, current_event_id, timestamp)
        for _ev in _blind_events:
            events.append(Event(
                event_id=_ev["event_id"],
                event_type=_ev["event_type"],
                timestamp=_ev["timestamp"],
                payload=_ev["payload"],
                citations=_ev.get("citations", []),
            ))
            current_event_id += 1
        if _blind_miss:
            return events

    # WO-ENGINE-AG-WO1: Stunning Fist early validation (PHB p.101)
    # Must declare before attack roll. Invalid/exhausted → return early (no attack made).
    if getattr(intent, 'stunning_fist', False):
        if not attacker.get(EF.HAS_STUNNING_FIST, False):
            events.append(Event(
                event_id=current_event_id,
                event_type="stunning_fist_invalid",
                timestamp=timestamp,
                payload={"actor_id": intent.attacker_id, "reason": "no_feat"},
                citations=[{"source_id": "681f92bc94ff", "page": 101}],
            ))
            return events
        _sf_uses_max = attacker.get(EF.STUNNING_FIST_USES, 0)
        _sf_uses_used = attacker.get(EF.STUNNING_FIST_USED, 0)
        if _sf_uses_used >= _sf_uses_max:
            events.append(Event(
                event_id=current_event_id,
                event_type="stunning_fist_exhausted",
                timestamp=timestamp,
                payload={"actor_id": intent.attacker_id, "uses_max": _sf_uses_max},
                citations=[{"source_id": "681f92bc94ff", "page": 101}],
            ))
            return events

    # Step 1: Roll attack (d20 + bonus + condition modifiers + mounted bonus + terrain higher ground + feat modifier + flanking)
    combat_rng = rng.stream("combat")
    d20_result = combat_rng.randint(1, 20)
    # CP-16: condition modifier, CP-18A: mounted bonus, CP-19: terrain higher ground, WO-034: feat modifier, flanking
    # WO-ENGINE-DEFEND-001: Fight defensively attack penalty
    _attacker_temp_mods = attacker.get(EF.TEMPORARY_MODIFIERS, {}) or {}
    _fd_attack_penalty = _attacker_temp_mods.get("fight_defensively_attack", 0)
    # WO-ENGINE-BARDIC-MUSIC-001: Inspire Courage morale bonus (PHB p.29)
    _inspire_attack_bonus = (
        attacker.get(EF.INSPIRE_COURAGE_BONUS, 0)
        if attacker.get(EF.INSPIRE_COURAGE_ACTIVE, False) else 0
    )
    # WO-ENGINE-INSPIRE-GREATNESS-001: Inspire Greatness competence attack bonus (PHB p.30)
    # Competence bonuses don't stack — already stored as max() in bardic_music_resolver.
    _inspire_greatness_attack_bonus = _attacker_temp_mods.get("inspire_greatness_bab", 0)

    # WO-ENGINE-FAVORED-ENEMY-001: Ranger Favored Enemy attack/damage bonus (PHB p.47)
    _favored_enemy_bonus = 0
    _attacker_favored = attacker.get(EF.FAVORED_ENEMIES, [])
    if _attacker_favored:
        _target_type = target.get(EF.CREATURE_TYPE, "")
        for _fe in _attacker_favored:
            if _fe.get("creature_type", "") == _target_type and _target_type != "":
                _favored_enemy_bonus = _fe.get("bonus", 0)
                break

    # WO-ENGINE-RACIAL-ATTACK-BONUS-001: Racial attack bonuses (PHB p.15/p.17/p.21)
    # Dwarf: +1 vs orcs/goblinoids. Gnome: +1 vs kobolds/goblinoids. Halfling: +1 thrown/sling.
    _racial_attack_bonus = 0
    _target_subtypes = target.get(EF.CREATURE_SUBTYPES, [])
    _dwarf_orc_bonus = attacker.get(EF.ATTACK_BONUS_VS_ORCS, 0)
    _gnome_kobold_bonus = attacker.get(EF.ATTACK_BONUS_VS_KOBOLDS, 0)
    _thrown_bonus = attacker.get(EF.ATTACK_BONUS_THROWN, 0)
    if _dwarf_orc_bonus and ("orc" in _target_subtypes or "goblinoid" in _target_subtypes):
        _racial_attack_bonus = max(_racial_attack_bonus, _dwarf_orc_bonus)
    if _gnome_kobold_bonus and ("kobold" in _target_subtypes or "goblinoid" in _target_subtypes):
        _racial_attack_bonus = max(_racial_attack_bonus, _gnome_kobold_bonus)
    if _thrown_bonus and getattr(intent.weapon, "is_thrown", False):
        _racial_attack_bonus = max(_racial_attack_bonus, _thrown_bonus)

    # WO-ENGINE-WEAPON-FINESSE-001: Weapon Finesse � DEX replaces STR for light weapon attacks (PHB p.102)
    # intent.attack_bonus is BAB + STR_MOD (from intent_bridge.py); delta = DEX - STR replaces STR with DEX
    _finesse_delta = 0
    _attacker_feats = attacker.get(EF.FEATS, [])
    if "weapon_finesse" in _attacker_feats and intent.weapon.is_light:
        _str_mod = attacker.get(EF.STR_MOD, 0)
        _dex_mod = attacker.get(EF.DEX_MOD, 0)
        _finesse_delta = _dex_mod - _str_mod  # positive if DEX > STR, negative if DEX < STR

    # WO-ENGINE-PRECISE-SHOT-001: Ranged-into-melee penalty (PHB p.140)
    # -4 to attack when shooting at target engaged in melee with an ally. Negated by Precise Shot.
    _ranged_into_melee_penalty = 0
    if not is_melee and _is_target_in_melee(intent.target_id, attacker.get(EF.TEAM, ""), world_state):
        if "precise_shot" in _attacker_feats:
            events.append(Event(
                event_id=current_event_id,
                event_type="precise_shot_active",
                timestamp=timestamp,
                payload={"actor_id": intent.attacker_id},
                citations=[{"source_id": "681f92bc94ff", "page": 99}],
            ))
            current_event_id += 1
        else:
            _ranged_into_melee_penalty = -4

    # WO-ENGINE-WEAPON-FOCUS-001: Weapon Focus +1 attack bonus (PHB p.102)
    # Feat key: f"weapon_focus_{weapon_type}" (e.g. "weapon_focus_light", "weapon_focus_one-handed")
    _wf_bonus = 1 if f"weapon_focus_{intent.weapon.weapon_type}" in _attacker_feats else 0
    if _wf_bonus:
        events.append(Event(
            event_id=current_event_id,
            event_type="weapon_focus_active",
            timestamp=timestamp,
            payload={"actor_id": intent.attacker_id, "weapon_type": intent.weapon.weapon_type},
            citations=[{"source_id": "681f92bc94ff", "page": 102}],
        ))
        current_event_id += 1

    attack_bonus_with_conditions = (
        intent.attack_bonus +
        attacker_modifiers.attack_modifier +
        mounted_bonus +
        terrain_higher_ground +
        feat_attack_modifier +
        flanking_bonus
        - attacker.get(EF.NEGATIVE_LEVELS, 0)  # WO-ENGINE-ENERGY-DRAIN-001: -1/neg level (PHB p.215)
        + _fd_attack_penalty  # WO-ENGINE-DEFEND-001: 0 or negative (e.g. -4)
        + _weapon_broken_penalty  # WO-ENGINE-SUNDER-DISARM-FULL-001: -2 if weapon broken
        + _vs_blinded_bonus  # WO-ENGINE-CONDITIONS-BLIND-DEAF-001: +2 vs blinded
        + _inspire_attack_bonus  # WO-ENGINE-BARDIC-MUSIC-001: morale bonus to attack
        + _inspire_greatness_attack_bonus  # WO-ENGINE-INSPIRE-GREATNESS-001: competence bonus
        + _favored_enemy_bonus  # WO-ENGINE-FAVORED-ENEMY-001: ranger favored enemy bonus
        + intent.weapon.enhancement_bonus  # WO-ENGINE-WEAPON-ENHANCEMENT-001: magic weapon (PHB p.224)
        + _finesse_delta  # WO-ENGINE-WEAPON-FINESSE-001: DEX delta for light weapons
        - intent.combat_expertise_penalty  # WO-ENGINE-COMBAT-EXPERTISE-001: CE attack penalty (PHB p.92)
        + (0 if _is_weapon_proficient(attacker, intent.weapon) else -4)  # WO-ENGINE-WEAPON-PROFICIENCY-001: PHB p.113
        + _ranged_into_melee_penalty  # WO-ENGINE-PRECISE-SHOT-001: PHB p.140
        + _wf_bonus  # WO-ENGINE-WEAPON-FOCUS-001: Weapon Focus +1 attack (PHB p.102)
        + _racial_attack_bonus  # WO-ENGINE-RACIAL-ATTACK-BONUS-001: Dwarf/Gnome/Halfling (PHB p.15/17/21)
    )
    total = d20_result + attack_bonus_with_conditions

    # WO-ENGINE-COMBAT-EXPERTISE-001: Write CE dodge AC bonus to attacker entity (PHB p.92)
    # penalty==1 -> +1; penalty 2-5 -> +2. Cleared at start of attacker next turn.
    if intent.combat_expertise_penalty > 0:
        _ce_ac = 1 if intent.combat_expertise_penalty == 1 else 2
        world_state.entities[intent.attacker_id][EF.COMBAT_EXPERTISE_BONUS] = _ce_ac

    # Determine threat and hit (PHB p.140)
    # WO-ENGINE-IMPROVED-CRITICAL-001: Improved Critical feat doubles threat range (PHB p.96)
    _ic_eff_range = intent.weapon.critical_range
    _ic_specific = f"improved_critical_{getattr(intent.weapon, 'weapon_type', None)}" if getattr(intent.weapon, 'weapon_type', None) else None
    if "improved_critical" in _attacker_feats or (_ic_specific and _ic_specific in _attacker_feats):
        _ic_eff_range = max(1, 21 - (21 - intent.weapon.critical_range) * 2)
    is_threat = (d20_result >= _ic_eff_range)
    is_natural_20 = (d20_result == 20)
    is_natural_1 = (d20_result == 1)

    # CP-17: Helpless auto-hit bypasses normal hit determination (melee only, PHB p.153)
    # PHB p.140: Natural 1 always misses. Natural 20 always hits AND threatens.
    # Expanded threat range (e.g., 19-20): the roll threatens a critical, but
    # the attack must still meet AC to hit (only natural 20 auto-hits).
    if auto_hit_helpless:
        hit = True  # Auto-hit: skip roll entirely for melee vs helpless
    elif is_natural_1:
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
            "weapon_name": feat_context["weapon_name"],  # WO-WAYPOINT-003: for NarrativeBrief extraction
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
            "target_ac_modifier": condition_ac,  # CP-16 (melee/ranged differentiated)
            "dex_penalty": dex_penalty,  # CP-17: DEX stripped from AC when loses_dex_to_ac
            "auto_hit_helpless": auto_hit_helpless,  # CP-17: melee auto-hit vs helpless
            "hit": hit,
            "is_natural_20": is_natural_20,
            "is_natural_1": is_natural_1,
            "is_threat": is_threat,  # WO-FIX-002
            "is_critical": is_critical,  # WO-FIX-002
            "confirmation_total": confirmation_total,  # WO-FIX-002 (None if no confirmation)
            "fight_defensively_ac_bonus": _defend_ac_total,  # WO-ENGINE-DEFEND-001
            "fight_defensively_attack_penalty": _fd_attack_penalty,  # WO-ENGINE-DEFEND-001
            "feint_flat_footed": _feint_active,  # WO-ENGINE-FEINT-001
            "twd_ac_bonus": _twd_ac_bonus,  # WO-ENGINE-TWD-001
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
                # WO-ENGINE-BLIND-FIGHT-001: Blind-Fight feat — reroll once on miss (PHB p.91)
                _bf_rerolled = False
                if "blind_fight" in attacker.get(EF.FEATS, []):
                    _bf_reroll = combat_rng.randint(1, 100)
                    # Always emit reroll event (records outcome for event log)
                    events.append(Event(
                        event_id=current_event_id,
                        event_type="blind_fight_reroll",
                        timestamp=timestamp + 0.05,
                        payload={
                            "attacker_id": intent.attacker_id,
                            "target_id": intent.target_id,
                            "original_roll": miss_chance_d100,
                            "reroll": _bf_reroll,
                            "miss_chance_percent": miss_chance_percent,
                        },
                        citations=[{"source_id": "681f92bc94ff", "page": 91}]  # PHB Blind-Fight
                    ))
                    current_event_id += 1
                    if not check_miss_chance(miss_chance_percent, _bf_reroll):
                        # Reroll succeeds — attack proceeds past miss chance
                        _bf_rerolled = True  # Do not miss; continue to damage

                if not _bf_rerolled:
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

    # WO-ENGINE-AG-WO1: Stunning Fist — consume use (declared before roll; forfeited on hit or miss, PHB p.101)
    if getattr(intent, 'stunning_fist', False) and attacker.get(EF.HAS_STUNNING_FIST, False):
        events.append(Event(
            event_id=current_event_id,
            event_type="stunning_fist_used",
            timestamp=timestamp + 0.06,
            payload={
                "actor_id": intent.attacker_id,
                "target_id": intent.target_id,
                "hit": hit,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 101}],
        ))
        current_event_id += 1

    # WO-ENGINE-FEINT-001: emit feint_bonus_consumed when feint marker was active
    if _feint_active and hit:
        events.append(Event(
            event_id=current_event_id,
            event_type="feint_bonus_consumed",
            timestamp=timestamp + 0.05,
            payload={
                "attacker_id": intent.attacker_id,
                "target_id": intent.target_id,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 76}]
        ))
        current_event_id += 1

    # If hit, roll damage
    if hit:
        # WO-ENGINE-MONK-UNARMED-WIRE-AF: Override damage dice for monk unarmed strikes (PHB Table 3-10, p.41)
        # Flurry path already uses MONK_UNARMED_DICE via _make_unarmed_weapon() in flurry_of_blows_resolver.
        # AttackIntent path did not — this closes FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001.
        _damage_dice_expr = intent.weapon.damage_dice
        if (intent.weapon.weapon_type == "natural"
                and attacker.get(EF.CLASS_LEVELS, {}).get("monk", 0) > 0):
            _monk_override = attacker.get(EF.MONK_UNARMED_DICE)
            if _monk_override:
                _damage_dice_expr = _monk_override

        # Parse damage dice
        num_dice, die_size = parse_damage_dice(_damage_dice_expr)

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

        base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_to_damage + intent.weapon.enhancement_bonus  # WO-ENGINE-WEAPON-ENHANCEMENT-001: enhancement is pre-crit (PHB p.224)
        # WO-ENGINE-WEAPON-SPECIALIZATION-001: Weapon Specialization +2 damage bonus (PHB p.102)
        # Pre-crit: multiplied on critical hits (same as enhancement bonus, PHB p.224)
        _wsp_bonus = 2 if f"weapon_specialization_{intent.weapon.weapon_type}" in _attacker_feats else 0
        base_damage += _wsp_bonus
        # CP-16: Apply condition damage modifier, WO-034: Apply feat damage modifier
        # WO-ENGINE-BARDIC-MUSIC-001: Inspire Courage morale bonus to damage (PHB p.29)
        _inspire_dmg_bonus = (
            attacker.get(EF.INSPIRE_COURAGE_BONUS, 0)
            if attacker.get(EF.INSPIRE_COURAGE_ACTIVE, False) else 0
        )
        base_damage_with_modifiers = base_damage + attacker_modifiers.damage_modifier + feat_damage_modifier + _inspire_dmg_bonus + _favored_enemy_bonus  # WO-ENGINE-ATTACK-MODIFIER-FIDELITY-001: FE is pre-crit (PHB p.140)

        # WO-FIX-002: Apply critical multiplier (PHB p.140)
        if is_critical:
            damage_total = max(1, base_damage_with_modifiers * intent.weapon.critical_multiplier)  # WO-FIX-01 (BUG-8/9): min 1 on hit, before DR
        else:
            damage_total = max(1, base_damage_with_modifiers)  # WO-FIX-01 (BUG-8/9): min 1 on hit, before DR

        # WO-ENGINE-IMPROVED-UNCANNY-DODGE-001: IUD suppresses flanking-based sneak attack (PHB p.26/50)
        # The flanking_bonus already applied to attack roll above is preserved — IUD only blocks SA.
        _sa_is_flanking = is_flanking
        if is_flanking and "improved_uncanny_dodge" in target.get(EF.FEATS, []):
            _attacker_rogue = attacker.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
            _target_iud_base = (
                target.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
                + target.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)
            )
            if _attacker_rogue < _target_iud_base + 4:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="improved_uncanny_dodge_active",
                    timestamp=timestamp + 0.06,
                    payload={"target_id": intent.target_id},
                    citations=[{"source_id": "681f92bc94ff", "page": 26}],
                ))
                current_event_id += 1
                _sa_is_flanking = False  # Flanking suppressed for sneak attack eligibility

        # WO-050B: Sneak Attack precision damage (PHB p.50)
        # Added AFTER critical multiplier — precision damage is NOT multiplied on crits
        from aidm.core.sneak_attack import calculate_sneak_attack
        sa_eligible, sa_damage, sa_dice_expr, sa_rolls, sa_reason = calculate_sneak_attack(
            world_state, intent.attacker_id, intent.target_id,
            is_flanking=_sa_is_flanking,
            rng=rng,
        )
        if sa_eligible:
            damage_total += sa_damage

        # WO-ENGINE-AG-WO2: Crippling Strike (PHB p.51)
        # After confirmed sneak attack: target takes 1 STR ability damage. No save. No daily limit.
        if sa_eligible and attacker.get(EF.HAS_CRIPPLING_STRIKE, False):
            events.append(Event(
                event_id=current_event_id,
                event_type="crippling_strike",
                timestamp=timestamp + 0.065,
                payload={
                    "attacker_id": intent.attacker_id,
                    "target_id": intent.target_id,
                    "str_damage": 1,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 51}],
            ))
            current_event_id += 1

        # WO-048: Apply Damage Reduction (PHB p.291)
        # WO-ENGINE-DR-001: Extract weapon bypass flags for accurate DR calculation
        from aidm.core.damage_reduction import (
            get_applicable_dr, apply_dr_to_damage,
            extract_weapon_bypass_flags, _get_bypass_type,
        )
        is_magic_weapon, weapon_material, weapon_alignment, weapon_enhancement = \
            extract_weapon_bypass_flags(intent.weapon, attacker)
        dr_amount = get_applicable_dr(
            world_state, intent.target_id, intent.weapon.damage_type,
            is_magic_weapon=is_magic_weapon,
            weapon_material=weapon_material,
            weapon_alignment=weapon_alignment,
            weapon_enhancement=weapon_enhancement,
        )
        final_damage, dr_absorbed = apply_dr_to_damage(damage_total, dr_amount)

        # WO-ENGINE-DR-001: Emit damage_reduced event when DR absorbs damage
        if dr_absorbed > 0:
            events.append(Event(
                event_id=current_event_id,
                event_type="damage_reduced",
                timestamp=timestamp + 0.09,
                payload={
                    "entity_id": intent.target_id,
                    "base_damage": damage_total,
                    "dr_absorbed": dr_absorbed,
                    "final_damage": final_damage,
                    "dr_amount": dr_amount,
                    "bypass_type": _get_bypass_type(
                        target.get(EF.DAMAGE_REDUCTIONS, []), dr_amount
                    ),
                },
                citations=[{"source_id": "681f92bc94ff", "page": 291}]
            ))
            current_event_id += 1

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
                "damage_reduced": dr_absorbed,  # WO-048 / WO-ENGINE-DR-001
                "final_damage": final_damage,  # WO-048: Post-DR damage
                "damage_type": intent.weapon.damage_type
            },
            citations=[{"source_id": "681f92bc94ff", "page": 140}]  # PHB critical/damage rules
        ))
        current_event_id += 1

        # WO-ENGINE-AG-WO1: Stunning Fist — Fort save on hit (PHB p.101)
        # DC = 10 + (char_level // 2) + WIS_mod. STUNNED 1 round on failure.
        # Fort save goes through canonical resolve_save() — not inline.
        if getattr(intent, 'stunning_fist', False) and attacker.get(EF.HAS_STUNNING_FIST, False):
            from aidm.core.save_resolver import resolve_save as _sf_resolve_save
            from aidm.schemas.saves import SaveContext as _SFSaveContext, SaveType as _SFSaveType, SaveOutcome as _SFSaveOutcome
            _sf_char_level = attacker.get(EF.LEVEL, 1)
            _sf_wis_mod = attacker.get(EF.WIS_MOD, 0)
            _sf_dc = 10 + (_sf_char_level // 2) + _sf_wis_mod
            _sf_ctx = _SFSaveContext(
                save_type=_SFSaveType.FORT,
                dc=_sf_dc,
                source_id=intent.attacker_id,
                target_id=intent.target_id,
            )
            _sf_outcome, _sf_save_events = _sf_resolve_save(
                _sf_ctx, world_state, rng, current_event_id, timestamp + 0.11
            )
            events.extend(_sf_save_events)
            current_event_id += len(_sf_save_events)
            if _sf_outcome == _SFSaveOutcome.FAILURE:
                # Target STUNNED 1 round — can't act, loses DEX to AC, attackers +2 (PHB p.101)
                from aidm.schemas.conditions import create_stunned_condition as _sf_mkstun
                _sf_cond = _sf_mkstun(source="stunning_fist", applied_at_event_id=current_event_id)
                events.append(Event(
                    event_id=current_event_id,
                    event_type="condition_applied",
                    timestamp=timestamp + 0.12,
                    payload={
                        "entity_id": intent.target_id,
                        "condition": _sf_cond.condition_type,
                        "source": "stunning_fist",
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 101}],
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="stunning_fist_hit",
                    timestamp=timestamp + 0.125,
                    payload={"actor_id": intent.attacker_id, "target_id": intent.target_id, "dc": _sf_dc},
                    citations=[{"source_id": "681f92bc94ff", "page": 101}],
                ))
            else:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="stunning_fist_saved",
                    timestamp=timestamp + 0.12,
                    payload={"actor_id": intent.attacker_id, "target_id": intent.target_id, "dc": _sf_dc},
                    citations=[{"source_id": "681f92bc94ff", "page": 101}],
                ))
            current_event_id += 1

        # WO-ENGINE-DR-001: Only emit hp_changed if damage penetrated DR
        hp_before = target.get(EF.HP_CURRENT, 0)
        hp_after = hp_before - final_damage

        # WO-ENGINE-AF-WO4: Rogue Defensive Roll (PHB p.51)
        # Trigger: weapon/physical blow (not spell) that would reduce rogue to ≤0 HP.
        # 1/day. Cannot use if flat-footed (denied DEX to AC). Reflex save DC = final_damage.
        # Success: take half damage. Failure: full damage. Uses save_resolver canonical path.
        if (hp_before > 0
                and hp_after <= 0
                and target.get(EF.HAS_DEFENSIVE_ROLL, False)
                and not target.get(EF.DEFENSIVE_ROLL_USED, False)):
            _dr_flat_footed = (
                defender_modifiers.loses_dex_to_ac
                and not _target_retains_dex_via_uncanny_dodge(target)
            )
            # Also handle legacy list-format conditions (e.g., ["flat_footed"])
            _target_conditions = target.get(EF.CONDITIONS, [])
            if isinstance(_target_conditions, list) and "flat_footed" in _target_conditions:
                _dr_flat_footed = True
            if not _dr_flat_footed:
                from aidm.core.save_resolver import get_save_bonus, SaveType
                _dr_ref_bonus = get_save_bonus(world_state, intent.target_id, SaveType.REF)
                _dr_roll = rng.stream("combat").randint(1, 20)
                _dr_total = _dr_roll + _dr_ref_bonus
                _dr_dc = final_damage
                _dr_saved = _dr_total >= _dr_dc
                events.append(Event(
                    event_id=current_event_id,
                    event_type="defensive_roll_check",
                    timestamp=timestamp + 0.16,
                    payload={
                        "target_id": intent.target_id,
                        "ref_roll": _dr_roll,
                        "ref_bonus": _dr_ref_bonus,
                        "ref_total": _dr_total,
                        "dc": _dr_dc,
                        "saved": _dr_saved,
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 51}],
                ))
                current_event_id += 1
                if _dr_saved:
                    final_damage = final_damage // 2
                    hp_after = hp_before - final_damage
                    events.append(Event(
                        event_id=current_event_id,
                        event_type="defensive_roll_success",
                        timestamp=timestamp + 0.17,
                        payload={
                            "target_id": intent.target_id,
                            "damage_halved": final_damage,
                        },
                        citations=[{"source_id": "681f92bc94ff", "page": 51}],
                    ))
                else:
                    events.append(Event(
                        event_id=current_event_id,
                        event_type="defensive_roll_failure",
                        timestamp=timestamp + 0.17,
                        payload={"target_id": intent.target_id},
                        citations=[{"source_id": "681f92bc94ff", "page": 51}],
                    ))
                current_event_id += 1
                # Mark used (applied by apply_attack_events on "defensive_roll_used" event)
                events.append(Event(
                    event_id=current_event_id,
                    event_type="defensive_roll_used",
                    timestamp=timestamp + 0.175,
                    payload={"target_id": intent.target_id},
                    citations=[{"source_id": "681f92bc94ff", "page": 51}],
                ))
                current_event_id += 1

        # PHB p.145 -- Massive Damage instant-death check
        # Trigger: single attack dealing 50+ post-DR damage → DC 15 Fort save or die
        if final_damage >= 50:
            from aidm.core.save_resolver import get_save_bonus, SaveType
            _md_save_bonus = get_save_bonus(world_state, intent.target_id, SaveType.FORT)
            _md_roll = rng.stream("combat").randint(1, 20)
            _md_total = _md_roll + _md_save_bonus
            # WO-ENGINE-MD-SAVE-RULES-001: nat1/nat20 auto-fail/pass (PHB p.136)
            if _md_roll == 1:
                _md_saved = False  # natural 1 always fails
            elif _md_roll == 20:
                _md_saved = True  # natural 20 always succeeds
            else:
                _md_saved = _md_total >= 15

            events.append(Event(
                event_id=current_event_id,
                event_type="massive_damage_check",
                timestamp=timestamp + 0.15,
                payload={
                    "target_id": intent.target_id,
                    "damage": final_damage,
                    "fort_roll": _md_roll,
                    "fort_bonus": _md_save_bonus,
                    "fort_total": _md_total,
                    "dc": 15,
                    "saved": _md_saved,
                },
                citations=["PHB p.145"],
            ))
            current_event_id += 1

            if not _md_saved:
                # Instant death — override hp_after to -10 (dead threshold)
                hp_after = -10

        if final_damage > 0:
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
                    "source": "attack_damage",
                    "dr_absorbed": dr_absorbed,  # WO-ENGINE-DR-001
                }
            ))
            current_event_id += 1

            # WO-ENGINE-DEATH-DYING-001: Three-band defeat check (PHB p.145)
            from aidm.core.dying_resolver import resolve_hp_transition
            trans_events, field_updates = resolve_hp_transition(
                entity_id=intent.target_id,
                old_hp=hp_before,
                new_hp=hp_after,
                source="attack_damage",
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.3,
            )
            events.extend(trans_events)
            current_event_id += len(trans_events)
            # (apply_attack_events reads new event types directly)

            # WO-ENGINE-CLEAVE-WIRE-001: Cleave / Great Cleave bonus attack on kill (PHB p.92/94)
            if hp_after <= 0:
                from aidm.core.feat_resolver import can_use_cleave, get_cleave_limit
                _cleave_attacker = world_state.entities.get(intent.attacker_id, {})
                if can_use_cleave(_cleave_attacker, intent.target_id, world_state):
                    _cleave_limit = get_cleave_limit(_cleave_attacker)
                    _cleave_used_set = set()
                    if world_state.active_combat is not None:
                        _cleave_used_set = set(world_state.active_combat.get("cleave_used_this_turn", set()))
                    _already_cleaved = intent.attacker_id in _cleave_used_set
                    if _cleave_limit is None or not _already_cleaved:
                        _cleave_target_id = _find_cleave_target(
                            intent.attacker_id, intent.target_id, world_state
                        )
                        if _cleave_target_id is not None:
                            # Mark used for Cleave once-per-round (Great Cleave has no limit)
                            if _cleave_limit == 1 and world_state.active_combat is not None:
                                world_state.active_combat["cleave_used_this_turn"] = _cleave_used_set | {intent.attacker_id}
                            _feat_name = "great_cleave" if get_cleave_limit(_cleave_attacker) is None else "cleave"
                            events.append(Event(
                                event_id=current_event_id,
                                event_type="cleave_triggered",
                                timestamp=timestamp + 0.35,
                                payload={
                                    "attacker_id": intent.attacker_id,
                                    "killed_target_id": intent.target_id,
                                    "cleave_target_id": _cleave_target_id,
                                    "feat": _feat_name,
                                },
                                citations=[{"source_id": "681f92bc94ff", "page": 92}],
                            ))
                            current_event_id += 1
                            # Bonus attack at same attack bonus as the killing blow
                            _cleave_intent = AttackIntent(
                                attacker_id=intent.attacker_id,
                                target_id=_cleave_target_id,
                                weapon=intent.weapon,
                                attack_bonus=intent.attack_bonus,
                            )
                            _cleave_events = resolve_attack(
                                intent=_cleave_intent,
                                world_state=world_state,
                                rng=rng,
                                next_event_id=current_event_id,
                                timestamp=timestamp + 0.4,
                            )
                            events.extend(_cleave_events)
                            current_event_id += len(_cleave_events)

    return events


def check_nonlethal_threshold(current_hp: int, nonlethal_total: int):
    """Check whether nonlethal damage has crossed a PHB p.146 threshold.

    Args:
        current_hp: Entity's current lethal HP (EF.HP_CURRENT).
        nonlethal_total: New total nonlethal damage after this hit.

    Returns:
        "staggered" if nonlethal_total == current_hp,
        "unconscious" if nonlethal_total > current_hp,
        None if below threshold.

    WO-ENGINE-NONLETHAL-001
    """
    if nonlethal_total > current_hp:
        return "unconscious"
    elif nonlethal_total == current_hp:
        return "staggered"
    return None


NONLETHAL_ATTACK_PENALTY = -4  # PHB p.146


def resolve_nonlethal_attack(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a nonlethal attack intent.

    PHB p.146: -4 attack penalty. On hit, damage accumulates in NONLETHAL_DAMAGE
    pool. Threshold crossed → STAGGERED or UNCONSCIOUS condition applied.

    RNG consumption order:
    1. Attack roll (d20)
    2. IF threat: Confirmation roll (d20)
    3. IF hit: Damage roll (XdY)

    WO-ENGINE-NONLETHAL-001
    """
    from aidm.schemas.conditions import ConditionType

    events: List[Event] = []
    current_event_id = next_event_id

    if intent.attacker_id not in world_state.entities:
        raise ValueError(f"Attacker not found in world state: {intent.attacker_id}")
    if intent.target_id not in world_state.entities:
        raise ValueError(f"Target not found in world state: {intent.target_id}")

    attacker = world_state.entities[intent.attacker_id]
    target = world_state.entities[intent.target_id]

    # Apply -4 nonlethal penalty to attack bonus (PHB p.146)
    adjusted_attack_bonus = intent.attack_bonus + NONLETHAL_ATTACK_PENALTY

    # Get condition modifiers
    attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
    defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")

    # Get target AC
    base_ac = target.get(EF.AC, 10)
    is_melee = True  # NonlethalAttackIntent is always melee
    # WO-ENGINE-UNCANNY-DODGE-001: Uncanny Dodge bypasses flat-footed DEX denial (PHB p.51/47/26)
    dex_penalty = 0
    if defender_modifiers.loses_dex_to_ac and not _target_retains_dex_via_uncanny_dodge(target):
        dex_mod = target.get(EF.DEX_MOD, 0)
        if dex_mod > 0:
            dex_penalty = -dex_mod
    if is_melee and defender_modifiers.ac_modifier_melee != 0:
        condition_ac = defender_modifiers.ac_modifier_melee
    else:
        condition_ac = defender_modifiers.ac_modifier
    # WO-ENGINE-MONK-WIS-AC-001: Monk WIS bonus to AC (PHB p.41) — applies when unarmored
    _monk_wis_ac_nl = 0
    _monk_level_target_nl = target.get(EF.CLASS_LEVELS, {}).get("monk", 0)
    if _monk_level_target_nl >= 1:
        _armor_bonus_nl = target.get(EF.ARMOR_AC_BONUS, 0)
        if _armor_bonus_nl == 0:
            _monk_wis_ac_nl = target.get(EF.MONK_WIS_AC_BONUS, 0)
    target_ac = base_ac + condition_ac + dex_penalty + _monk_wis_ac_nl

    # Step 1: Attack roll
    combat_rng = rng.stream("combat")
    d20_result = combat_rng.randint(1, 20)
    # WO-ENGINE-WEAPON-FINESSE-001: Weapon Finesse � DEX replaces STR for light weapon attacks (PHB p.102)
    # adjusted_attack_bonus includes NONLETHAL_ATTACK_PENALTY applied to BAB+STR_MOD
    _nl_finesse_delta = 0
    _nl_attacker_feats = attacker.get(EF.FEATS, [])
    if "weapon_finesse" in _nl_attacker_feats and intent.weapon.is_light:
        _nl_str_mod = attacker.get(EF.STR_MOD, 0)
        _nl_dex_mod = attacker.get(EF.DEX_MOD, 0)
        _nl_finesse_delta = _nl_dex_mod - _nl_str_mod  # positive if DEX > STR
    attack_bonus_with_conditions = adjusted_attack_bonus + attacker_modifiers.attack_modifier + _nl_finesse_delta
    total = d20_result + attack_bonus_with_conditions

    # WO-ENGINE-IMPROVED-CRITICAL-001: Improved Critical feat doubles threat range (PHB p.96)
    _nl_ic_eff_range = intent.weapon.critical_range
    _nl_weapon_type = getattr(intent.weapon, 'weapon_type', None)
    _nl_ic_specific = f"improved_critical_{_nl_weapon_type}" if _nl_weapon_type else None
    if "improved_critical" in _nl_attacker_feats or (_nl_ic_specific and _nl_ic_specific in _nl_attacker_feats):
        _nl_ic_eff_range = max(1, 21 - (21 - intent.weapon.critical_range) * 2)
    is_threat = (d20_result >= _nl_ic_eff_range)
    is_natural_20 = (d20_result == 20)
    is_natural_1 = (d20_result == 1)

    auto_hit_helpless = is_melee and defender_modifiers.auto_hit_if_helpless

    if auto_hit_helpless:
        hit = True
    elif is_natural_1:
        hit = False
    elif is_natural_20:
        hit = True
    else:
        hit = (total >= target_ac)

    # Step 2: Critical confirmation (crit rules still apply per PHB p.146)
    is_critical = False
    confirmation_total = None
    if is_threat and hit:
        confirmation_d20 = combat_rng.randint(1, 20)
        confirmation_total = confirmation_d20 + attack_bonus_with_conditions
        if confirmation_total >= target_ac:
            is_critical = True

    # Emit attack_roll event (includes nonlethal marker)
    events.append(Event(
        event_id=current_event_id,
        event_type="attack_roll",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "d20_result": d20_result,
            "attack_bonus": intent.attack_bonus,
            "nonlethal": True,
            "nonlethal_penalty": NONLETHAL_ATTACK_PENALTY,
            "adjusted_attack_bonus": adjusted_attack_bonus,
            "condition_modifier": attacker_modifiers.attack_modifier,
            "total": total,
            "target_ac": target_ac,
            "target_base_ac": base_ac,
            "hit": hit,
            "is_natural_20": is_natural_20,
            "is_natural_1": is_natural_1,
            "is_threat": is_threat,
            "is_critical": is_critical,
            "confirmation_total": confirmation_total,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 146}]
    ))
    current_event_id += 1

    if hit:
        # Roll damage (same dice/STR logic as resolve_attack)
        num_dice, die_size = parse_damage_dice(intent.weapon.damage_dice)
        damage_rolls = roll_dice(num_dice, die_size, rng)

        str_modifier = attacker.get(EF.STR_MOD, 0)
        weapon_grip = intent.weapon.grip
        if weapon_grip == "two-handed":
            str_to_damage = int(str_modifier * 1.5)
        elif weapon_grip == "off-hand":
            str_to_damage = int(str_modifier * 0.5)
        else:
            str_to_damage = str_modifier

        base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_to_damage
        base_damage_with_modifiers = base_damage + attacker_modifiers.damage_modifier

        if is_critical:
            damage_total = max(1, base_damage_with_modifiers * intent.weapon.critical_multiplier)
        else:
            damage_total = max(1, base_damage_with_modifiers)

        # NOTE: DR does NOT apply to nonlethal damage pool per WO-ENGINE-NONLETHAL-001 spec.
        # PHB p.146 is silent on DR vs nonlethal; nonlethal bypasses DR in this implementation.

        # Check threshold
        old_nonlethal = target.get(EF.NONLETHAL_DAMAGE, 0)
        new_nonlethal = old_nonlethal + damage_total
        current_hp = target.get(EF.HP_CURRENT, 0)
        threshold = check_nonlethal_threshold(current_hp, new_nonlethal)

        # Emit nonlethal_damage event
        events.append(Event(
            event_id=current_event_id,
            event_type="nonlethal_damage",
            timestamp=timestamp + 0.1,
            payload={
                "attacker_id": intent.attacker_id,
                "entity_id": intent.target_id,
                "amount": damage_total,
                "old_nonlethal_total": old_nonlethal,
                "new_nonlethal_total": new_nonlethal,
                "current_hp": current_hp,
                "threshold_crossed": threshold,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 146}]
        ))
        current_event_id += 1

        # Emit condition_applied if threshold crossed
        if threshold == "staggered":
            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=timestamp + 0.2,
                payload={
                    "entity_id": intent.target_id,
                    "condition": ConditionType.STAGGERED.value,
                    "source": "nonlethal_damage",
                    "notes": f"Nonlethal {new_nonlethal} == HP {current_hp}",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 146}]
            ))
            current_event_id += 1
        elif threshold == "unconscious":
            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=timestamp + 0.2,
                payload={
                    "entity_id": intent.target_id,
                    "condition": ConditionType.UNCONSCIOUS.value,
                    "source": "nonlethal_damage",
                    "notes": f"Nonlethal {new_nonlethal} > HP {current_hp}",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 146}]
            ))
            current_event_id += 1

    return events


def apply_nonlethal_attack_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """Apply nonlethal attack events to world state.

    Handles:
    - nonlethal_damage: updates EF.NONLETHAL_DAMAGE
    - condition_applied: appends condition to EF.CONDITIONS

    WO-ENGINE-NONLETHAL-001
    """
    entities = deepcopy(world_state.entities)

    for event in events:
        if event.event_type == "nonlethal_damage":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.NONLETHAL_DAMAGE] = event.payload["new_nonlethal_total"]

        elif event.event_type == "condition_applied":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                cond_val = event.payload["condition"]
                conds = entities[entity_id].get(EF.CONDITIONS, {})
                if isinstance(conds, dict):
                    if cond_val not in conds:
                        conds = dict(conds)
                        conds[cond_val] = {}
                    entities[entity_id][EF.CONDITIONS] = conds
                else:
                    # List form
                    if cond_val not in conds:
                        conds = list(conds) + [cond_val]
                    entities[entity_id][EF.CONDITIONS] = conds

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )


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

        elif event.event_type == "defensive_roll_used":
            # WO-ENGINE-AF-WO4: Mark defensive roll consumed for the day (PHB p.51)
            entity_id = event.payload["target_id"]
            if entity_id in entities:
                entities[entity_id][EF.DEFENSIVE_ROLL_USED] = True

        elif event.event_type == "stunning_fist_used":
            # WO-ENGINE-AG-WO1: Increment uses consumed today (PHB p.101)
            entity_id = event.payload["actor_id"]
            if entity_id in entities:
                entities[entity_id][EF.STUNNING_FIST_USED] = (
                    entities[entity_id].get(EF.STUNNING_FIST_USED, 0) + 1
                )

        elif event.event_type == "crippling_strike":
            # WO-ENGINE-AG-WO2: Apply 1 STR ability damage to target (PHB p.51)
            entity_id = event.payload["target_id"]
            if entity_id in entities:
                _old_str_dmg = entities[entity_id].get(EF.STR_DAMAGE, 0)
                _new_str_dmg = _old_str_dmg + event.payload["str_damage"]
                entities[entity_id][EF.STR_DAMAGE] = _new_str_dmg
                # Recompute EF.STR_MOD: effective STR = base STR - STR_DAMAGE (CS-005)
                _base_str = entities[entity_id].get(EF.BASE_STATS, {}).get("strength", 10)
                _eff_str = max(0, _base_str - _new_str_dmg)
                entities[entity_id][EF.STR_MOD] = (_eff_str - 10) // 2

    # Return new WorldState
    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None
    )


def resolve_charge(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a charge action intent (PHB p.150-151).

    Full-round action: +2 attack bonus, -2 AC penalty until start of next turn.
    Handles Spirited Charge feat damage multiplication when mounted.

    WO-ENGINE-CHARGE-001
    """
    from aidm.schemas.attack import AttackIntent as _AttackIntent, Weapon as _Weapon

    events: List[Event] = []
    current_event_id = next_event_id

    # Step 1: path_clear validation
    if not intent.path_clear:
        return [Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "attacker_id": intent.attacker_id,
                "target_id": intent.target_id,
                "reason": "charge_path_blocked",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 150}],
        )]

    # Step 2: target validation
    target = world_state.entities.get(intent.target_id)
    if target is None:
        return [Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "attacker_id": intent.attacker_id,
                "target_id": intent.target_id,
                "reason": "target_not_found",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 150}],
        )]
    if target.get(EF.DEFEATED, False):
        return [Event(
            event_id=next_event_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "attacker_id": intent.attacker_id,
                "target_id": intent.target_id,
                "reason": "target_already_defeated",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 150}],
        )]

    # Step 3: build AttackIntent with +2 charge bonus
    attacker = world_state.entities[intent.attacker_id]
    base_attack_bonus = attacker.get(EF.ATTACK_BONUS, 0)
    charge_attack_bonus = base_attack_bonus + 2  # PHB p.150: +2 on charge

    weapon_fields = {k: v for k, v in intent.weapon.items() if k != "is_ranged"}
    # Normalize weapon_type to valid Weapon values; lance → one-handed for dataclass
    _VALID_WEAPON_TYPES = {"light", "one-handed", "two-handed", "ranged", "natural"}
    if weapon_fields.get("weapon_type") not in _VALID_WEAPON_TYPES:
        weapon_fields = dict(weapon_fields)
        weapon_fields["weapon_type"] = "one-handed"
    weapon_obj = _Weapon(**weapon_fields)

    attack_intent = _AttackIntent(
        attacker_id=intent.attacker_id,
        target_id=intent.target_id,
        attack_bonus=charge_attack_bonus,
        weapon=weapon_obj,
    )

    # Step 4: emit charge_attack event (before attack roll events)
    events.append(Event(
        event_id=current_event_id,
        event_type="charge_attack",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "attack_bonus_applied": 2,
            "ac_penalty_applied": -2,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 150}],
    ))
    current_event_id += 1

    # Step 5: call resolve_attack()
    attack_events = resolve_attack(
        intent=attack_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.1,
    )
    events.extend(attack_events)
    current_event_id += len(attack_events)

    # Step 6: Spirited Charge damage multiplier (only on hit)
    hit_events = [e for e in attack_events if e.event_type == "attack_roll" and e.payload.get("hit")]
    if hit_events:
        feats = attacker.get(EF.FEATS, [])
        mounted = attacker.get(EF.MOUNTED_STATE)
        if "spirited_charge" in feats and mounted is not None:
            weapon_type = intent.weapon.get("weapon_type", "")
            multiplier = 3 if weapon_type == "lance" else 2

            # Find hp_changed event and replace delta in-place
            for idx, evt in enumerate(events):
                if evt.event_type == "hp_changed" and evt.payload.get("entity_id") == intent.target_id:
                    original_delta = evt.payload["delta"]
                    if original_delta < 0:
                        new_delta = original_delta * multiplier
                        hp_before = world_state.entities[intent.target_id].get(EF.HP_CURRENT, 0)
                        new_hp_after = hp_before + new_delta
                        events[idx] = Event(
                            event_id=evt.event_id,
                            event_type="hp_changed",
                            timestamp=evt.timestamp,
                            payload={
                                **evt.payload,
                                "delta": new_delta,
                                "hp_after": new_hp_after,
                            },
                            citations=evt.citations,
                        )
                    break

            # Emit spirited_charge_multiplier event
            events.append(Event(
                event_id=current_event_id,
                event_type="spirited_charge_multiplier",
                timestamp=timestamp + 0.25,
                payload={
                    "attacker_id": intent.attacker_id,
                    "target_id": intent.target_id,
                    "multiplier": multiplier,
                    "weapon_type": intent.weapon.get("weapon_type", "unknown"),
                },
                citations=[{"source_id": "681f92bc94ff", "page": 100}],
            ))
            current_event_id += 1

    # Step 7: emit charge_ac_applied event
    events.append(Event(
        event_id=current_event_id,
        event_type="charge_ac_applied",
        timestamp=timestamp + 0.3,
        payload={
            "attacker_id": intent.attacker_id,
            "charge_ac_penalty": -2,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 150}],
    ))

    # Step 8: return all events
    return events


def apply_charge_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """Apply charge resolution events to world state.

    Handles charge_attack (no-op — annotation only), charge_ac_applied
    (writes EF.TEMPORARY_MODIFIERS["charge_ac"] = -2 on attacker),
    and delegates hp_changed / entity_defeated / entity_dying /
    entity_disabled to the same mutation logic as apply_attack_events().

    WO-ENGINE-CHARGE-001
    """
    entities = deepcopy(world_state.entities)

    for event in events:
        if event.event_type == "charge_ac_applied":
            attacker_id = event.payload["attacker_id"]
            if attacker_id in entities:
                mods = dict(entities[attacker_id].get(EF.TEMPORARY_MODIFIERS, {}))
                mods["charge_ac"] = event.payload["charge_ac_penalty"]  # -2
                entities[attacker_id][EF.TEMPORARY_MODIFIERS] = mods

        elif event.event_type == "hp_changed":
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

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )


def resolve_coup_de_grace(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a coup de grâce against a helpless or dying target.

    PHB p.153:
    - Auto-hit (no attack roll)
    - Auto-crit (crit_multiplier applied to all damage dice and bonuses)
    - Fort save DC = 10 + damage dealt; failure = immediate death (HP → -10)
    - Provokes AoO (handled by play_loop before this call)

    RNG consumption order (deterministic):
    1. Damage dice (XdY)
    2. Fort save (d20)

    WO-ENGINE-COUP-DE-GRACE-001
    """
    from aidm.core.dying_resolver import resolve_hp_transition
    from aidm.core.conditions import get_condition_modifiers as _get_cond_mods

    events: List[Event] = []
    current_event_id = next_event_id
    combat_rng = rng.stream("combat")

    attacker = world_state.entities.get(intent.attacker_id, {})
    target = world_state.entities.get(intent.target_id, {})

    # Weapon stats from intent.weapon dict
    weapon = intent.weapon
    damage_dice: str = weapon.get("damage_dice", "1d4")
    damage_bonus: int = weapon.get("damage_bonus", 0)
    crit_multiplier: int = weapon.get("crit_multiplier", 2)
    damage_type: str = weapon.get("damage_type", "slashing")
    grip: str = weapon.get("grip", "one-handed")

    # STR modifier (grip-adjusted), PHB p.113
    str_mod = attacker.get(EF.STR_MOD, 0)
    if grip == "two-handed":
        str_to_damage = int(str_mod * 1.5)
    elif grip == "off-hand":
        str_to_damage = int(str_mod * 0.5)
    else:
        str_to_damage = str_mod

    # Roll damage dice
    num_dice, die_size = parse_damage_dice(damage_dice)
    damage_rolls = [combat_rng.randint(1, die_size) for _ in range(num_dice)]

    # Crit damage: multiply all dice and bonuses by crit_multiplier (PHB p.8/p.140)
    base_damage = sum(damage_rolls) + damage_bonus + str_to_damage
    damage_total = max(1, base_damage * crit_multiplier)

    # Apply Damage Reduction
    from aidm.core.damage_reduction import get_applicable_dr, apply_dr_to_damage
    dr_amount = get_applicable_dr(world_state, intent.target_id, damage_type)
    final_damage, damage_reduced = apply_dr_to_damage(damage_total, dr_amount)

    # Emit cdg_damage_roll event (no attack_roll event — auto-hit)
    events.append(Event(
        event_id=current_event_id,
        event_type="cdg_damage_roll",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "damage_dice": damage_dice,
            "damage_rolls": damage_rolls,
            "damage_bonus": damage_bonus,
            "str_modifier": str_mod,
            "grip": grip,
            "str_to_damage": str_to_damage,
            "base_damage": base_damage,
            "crit_multiplier": crit_multiplier,
            "damage_total": damage_total,
            "dr_amount": dr_amount,
            "damage_reduced": damage_reduced,
            "final_damage": final_damage,
            "damage_type": damage_type,
            "auto_hit": True,
            "auto_crit": True,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 153}]
    ))
    current_event_id += 1

    # Emit hp_changed
    hp_before = target.get(EF.HP_CURRENT, 0)
    hp_after = hp_before - final_damage

    events.append(Event(
        event_id=current_event_id,
        event_type="hp_changed",
        timestamp=timestamp + 0.1,
        payload={
            "entity_id": intent.target_id,
            "hp_before": hp_before,
            "hp_after": hp_after,
            "delta": -final_damage,
            "source": "coup_de_grace",
        }
    ))
    current_event_id += 1

    # Call resolve_hp_transition for dying/defeated/disabled transitions
    trans_events, _ = resolve_hp_transition(
        entity_id=intent.target_id,
        old_hp=hp_before,
        new_hp=hp_after,
        source="coup_de_grace",
        world_state=world_state,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.2,
    )
    events.extend(trans_events)
    current_event_id += len(trans_events)

    # Fort save (PHB p.153): DC = 10 + damage dealt (pre-DR value)
    fort_dc = 10 + damage_total

    # WO-ENGINE-CDG-SAVE-PATH-001: canonical save path via get_save_bonus()
    # Includes: base save, condition mods, feat bonuses (Great Fortitude),
    # Divine Grace, racial bonuses (halfling +1), Inspire Courage.
    from aidm.core.save_resolver import get_save_bonus, SaveType
    fort_bonus = get_save_bonus(world_state, intent.target_id, SaveType.FORT)

    fort_roll = combat_rng.randint(1, 20)
    fort_total = fort_roll + fort_bonus

    # WO-ENGINE-CDG-SAVE-PATH-001: nat1/nat20 auto-fail/pass (PHB p.136)
    if fort_roll == 1:
        fort_passed = False   # natural 1 always fails
    elif fort_roll == 20:
        fort_passed = True    # natural 20 always succeeds
    else:
        fort_passed = fort_total >= fort_dc

    events.append(Event(
        event_id=current_event_id,
        event_type="cdg_fort_save",
        timestamp=timestamp + 0.3,
        payload={
            "entity_id": intent.target_id,
            "attacker_id": intent.attacker_id,
            "fort_roll": fort_roll,
            "fort_bonus": fort_bonus,
            "fort_total": fort_total,
            "dc": fort_dc,
            "damage_total": damage_total,
            "passed": fort_passed,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 153}]
    ))
    current_event_id += 1

    # If Fort save fails and target not already defeated → immediate death
    already_defeated = any(e.event_type == "entity_defeated" for e in trans_events)

    if not fort_passed and not already_defeated:
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=timestamp + 0.35,
            payload={
                "entity_id": intent.target_id,
                "hp_before": hp_after,
                "hp_after": -10,
                "delta": -(hp_after - (-10)),
                "source": "coup_de_grace_fort_fail",
            }
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="entity_defeated",
            timestamp=timestamp + 0.4,
            payload={
                "entity_id": intent.target_id,
                "hp_final": -10,
                "cause": "coup_de_grace",
                "attacker_id": intent.attacker_id,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 153}]
        ))
        current_event_id += 1

    return events


def apply_cdg_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """Apply coup de grâce resolution events to world state.

    Handles: hp_changed, entity_defeated, entity_dying, entity_disabled,
    entity_revived, condition_applied, condition_removed.

    Mirrors apply_attack_events() in structure.

    WO-ENGINE-COUP-DE-GRACE-001
    """
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

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None
    )


def resolve_spring_attack(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a Spring Attack (PHB p.100). WO-ENGINE-AH-WO2.

    Full-round action: move up to speed, make one melee attack, continue moving.
    Target does not get AoO against the attacker (suppressed via filter_aoo_from_target
    in play_loop handler). Other threatening creatures may still get movement AoOs.

    Validation:
    - Attacker must have 'spring_attack' in EF.FEATS (PHB p.100)
    - Attacker must NOT wear heavy armor (PHB p.100 — cannot use in heavy armor)

    Returns events starting at next_event_id. Caller must call apply_attack_events().
    """
    from aidm.schemas.attack import AttackIntent as _AttackIntent, Weapon as _Weapon

    events: List[Event] = []
    current_event_id = next_event_id

    attacker = world_state.entities.get(intent.attacker_id)
    if attacker is None:
        return [Event(
            event_id=current_event_id,
            event_type="spring_attack_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "attacker_not_found"},
            citations=["PHB p.100"],
        )]

    # Gate 1: Spring Attack feat required (PHB p.100)
    feats = attacker.get(EF.FEATS, []) or []
    if "spring_attack" not in feats:
        return [Event(
            event_id=current_event_id,
            event_type="spring_attack_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "missing_feat_spring_attack"},
            citations=["PHB p.100"],
        )]

    # Gate 2: Heavy armor blocks Spring Attack (PHB p.100)
    armor_type = attacker.get(EF.ARMOR_TYPE, "none")
    if armor_type == "heavy":
        return [Event(
            event_id=current_event_id,
            event_type="spring_attack_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "heavy_armor"},
            citations=["PHB p.100"],
        )]

    # Build AttackIntent: single melee attack, no bonus/penalty from feat itself
    base_attack_bonus = attacker.get(EF.ATTACK_BONUS, 0)
    weapon_fields = {k: v for k, v in intent.weapon.items()}
    _VALID_WEAPON_TYPES = {"light", "one-handed", "two-handed", "ranged", "natural"}
    if weapon_fields.get("weapon_type") not in _VALID_WEAPON_TYPES:
        weapon_fields = dict(weapon_fields)
        weapon_fields["weapon_type"] = "one-handed"
    weapon_obj = _Weapon(**weapon_fields)

    attack_intent = _AttackIntent(
        attacker_id=intent.attacker_id,
        target_id=intent.target_id,
        attack_bonus=base_attack_bonus,
        weapon=weapon_obj,
    )

    # Resolve the single melee attack.
    # AoO suppression (no AoO from target): handled in play_loop via filter_aoo_from_target.
    # Melee attacks do not provoke in the first place; filter_aoo_from_target is still called
    # as the shared mechanism with Shot on the Run (WO3) — see aoo.py:filter_aoo_from_target.
    attack_events = resolve_attack(
        intent=attack_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp,
    )
    events.extend(attack_events)

    return events


def resolve_shot_on_the_run(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve Shot on the Run (PHB p.99). WO-ENGINE-AH-WO3.

    Full-round action: move up to speed, make one ranged attack, continue moving.
    Target does not get AoO against the attacker (suppressed via filter_aoo_from_target
    in play_loop handler — same mechanism as Spring Attack, WO2). Range increment
    penalties still apply (intent.range_penalty added to effective bonus).

    Validation:
    - Attacker must have 'shot_on_the_run' in EF.FEATS (PHB p.99)
    - Attacker must NOT wear heavy armor (PHB p.99 — works like Spring Attack)

    Returns events starting at next_event_id. Caller must call apply_attack_events().
    """
    from aidm.schemas.attack import AttackIntent as _AttackIntent, Weapon as _Weapon

    events: List[Event] = []
    current_event_id = next_event_id

    attacker = world_state.entities.get(intent.attacker_id)
    if attacker is None:
        return [Event(
            event_id=current_event_id,
            event_type="shot_on_the_run_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "attacker_not_found"},
            citations=["PHB p.99"],
        )]

    # Gate 1: Shot on the Run feat required (PHB p.99)
    feats = attacker.get(EF.FEATS, []) or []
    if "shot_on_the_run" not in feats:
        return [Event(
            event_id=current_event_id,
            event_type="shot_on_the_run_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "missing_feat_shot_on_the_run"},
            citations=["PHB p.99"],
        )]

    # Gate 2: Heavy armor blocks Shot on the Run (PHB p.99)
    armor_type = attacker.get(EF.ARMOR_TYPE, "none")
    if armor_type == "heavy":
        return [Event(
            event_id=current_event_id,
            event_type="shot_on_the_run_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "heavy_armor"},
            citations=["PHB p.99"],
        )]

    # Build AttackIntent: single ranged attack with range_penalty applied
    # Range increment penalty still applies (PHB p.99 — not suppressed by feat)
    base_attack_bonus = attacker.get(EF.ATTACK_BONUS, 0)
    effective_bonus = base_attack_bonus + intent.range_penalty  # range_penalty is negative or 0
    weapon_fields = {k: v for k, v in intent.weapon.items()}
    if weapon_fields.get("weapon_type") not in ("ranged",):
        weapon_fields = dict(weapon_fields)
        weapon_fields["weapon_type"] = "ranged"
        if "range_increment" not in weapon_fields:
            weapon_fields["range_increment"] = 30
    weapon_obj = _Weapon(**weapon_fields)

    attack_intent = _AttackIntent(
        attacker_id=intent.attacker_id,
        target_id=intent.target_id,
        attack_bonus=effective_bonus,
        weapon=weapon_obj,
    )

    # Resolve the single ranged attack.
    # AoO suppression (no AoO from target): handled in play_loop via filter_aoo_from_target.
    # SAME mechanism as Spring Attack (WO2) — aoo.filter_aoo_from_target called from both
    # play_loop Spring Attack and Shot on the Run handlers.
    attack_events = resolve_attack(
        intent=attack_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp,
    )
    events.extend(attack_events)

    return events


def resolve_manyshot(
    intent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve Manyshot (PHB p.97). WO-ENGINE-AH-WO4.

    Standard action: fire two arrows at a single target within 30 feet.
    Single attack roll at -4 penalty. Each arrow deals damage independently on hit.
    BAB scaling (3+ arrows at BAB +11/+16) is OUT OF SCOPE — base 2-arrow case only.
    CONSUME_DEFERRED: BAB scaling left for future WO.

    Authority: PHB p.97 — '-4 penalty' for 2-arrow volley (NOT Rapid Shot's -2).

    Validation:
    - Attacker must have 'manyshot' in EF.FEATS (PHB p.97)
    - within_30_feet must be True (DM/AI assertion, PHB p.97)

    Returns events starting at next_event_id. Caller must call apply_attack_events().
    """
    events: List[Event] = []
    current_event_id = next_event_id

    attacker = world_state.entities.get(intent.attacker_id)
    target = world_state.entities.get(intent.target_id)

    if attacker is None:
        return [Event(
            event_id=current_event_id,
            event_type="manyshot_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "attacker_not_found"},
            citations=["PHB p.97"],
        )]

    # Gate 1: Manyshot feat required (PHB p.97)
    feats = attacker.get(EF.FEATS, []) or []
    if "manyshot" not in feats:
        return [Event(
            event_id=current_event_id,
            event_type="manyshot_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "missing_feat_manyshot"},
            citations=["PHB p.97"],
        )]

    # Gate 2: Target must be within 30 feet (PHB p.97)
    if not intent.within_30_feet:
        return [Event(
            event_id=current_event_id,
            event_type="manyshot_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "target_id": intent.target_id,
                     "reason": "target_out_of_30ft_range"},
            citations=["PHB p.97"],
        )]

    if target is None:
        return [Event(
            event_id=current_event_id,
            event_type="manyshot_invalid",
            timestamp=timestamp,
            payload={"attacker_id": intent.attacker_id, "reason": "target_not_found"},
            citations=["PHB p.97"],
        )]

    # PHB p.97: single attack roll at -4 penalty (Manyshot penalty, NOT Rapid Shot -2)
    base_attack_bonus = attacker.get(EF.ATTACK_BONUS, 0)
    manyshot_penalty = -4  # PHB p.97: 2-arrow volley at -4
    effective_bonus = base_attack_bonus + manyshot_penalty

    # Roll ONE d20 — single attack roll for both arrows (MS-007: only one d20 roll event)
    combat_rng = rng.stream("combat")
    d20_roll = combat_rng.randint(1, 20)
    attack_total = d20_roll + effective_bonus
    target_ac = target.get(EF.AC, 10)
    hit = attack_total >= target_ac

    events.append(Event(
        event_id=current_event_id,
        event_type="attack_roll",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "roll": d20_roll,
            "attack_bonus": effective_bonus,
            "manyshot_penalty": manyshot_penalty,
            "total": attack_total,
            "target_ac": target_ac,
            "hit": hit,
            "source": "manyshot",
        },
        citations=["PHB p.97"],
    ))
    current_event_id += 1

    if hit:
        # Both arrows hit — roll damage independently for each (PHB p.97: "deal damage normally")
        # CONSUME_DEFERRED: BAB +11 (3 arrows) / BAB +16 (4 arrows) scaling not implemented.
        weapon = intent.weapon
        damage_dice: str = weapon.get("damage_dice", "1d8")
        damage_bonus: int = weapon.get("damage_bonus", 0)
        damage_type: str = weapon.get("damage_type", "piercing")
        str_modifier = 0  # PHB p.113: standard ranged attacks do not add STR to damage

        target_hp_current = target.get(EF.HP_CURRENT, 0)
        hp_after = target_hp_current

        for arrow_index in range(2):
            num_dice, die_size = parse_damage_dice(damage_dice)
            damage_rolls = roll_dice(num_dice, die_size, rng)
            damage_total = max(1, sum(damage_rolls) + damage_bonus + str_modifier)

            events.append(Event(
                event_id=current_event_id,
                event_type="damage_roll",
                timestamp=timestamp + 0.1 + arrow_index * 0.01,
                payload={
                    "attacker_id": intent.attacker_id,
                    "target_id": intent.target_id,
                    "damage_dice": damage_dice,
                    "damage_rolls": damage_rolls,
                    "damage_bonus": damage_bonus,
                    "str_modifier": str_modifier,
                    "total": damage_total,
                    "damage_type": damage_type,
                    "arrow_index": arrow_index,
                    "source": "manyshot",
                },
                citations=["PHB p.97"],
            ))
            current_event_id += 1

            hp_before = hp_after
            hp_after = hp_before - damage_total
            events.append(Event(
                event_id=current_event_id,
                event_type="hp_changed",
                timestamp=timestamp + 0.1 + arrow_index * 0.01,
                payload={
                    "entity_id": intent.target_id,
                    "hp_before": hp_before,
                    "hp_after": hp_after,
                    "delta": -damage_total,
                    "source": "manyshot",
                    "arrow_index": arrow_index,
                },
            ))
            current_event_id += 1

        # Check defeat/dying/disabled after all arrows
        if hp_after <= -10:
            events.append(Event(
                event_id=current_event_id,
                event_type="entity_defeated",
                timestamp=timestamp + 0.2,
                payload={"entity_id": intent.target_id, "source": "manyshot"},
            ))
            current_event_id += 1
        elif hp_after < 0:
            events.append(Event(
                event_id=current_event_id,
                event_type="entity_dying",
                timestamp=timestamp + 0.2,
                payload={"entity_id": intent.target_id, "hp": hp_after, "source": "manyshot"},
            ))
            current_event_id += 1
        elif hp_after == 0:
            events.append(Event(
                event_id=current_event_id,
                event_type="entity_disabled",
                timestamp=timestamp + 0.2,
                payload={"entity_id": intent.target_id, "source": "manyshot"},
            ))
            current_event_id += 1

    return events

