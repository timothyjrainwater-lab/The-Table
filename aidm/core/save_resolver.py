"""Save resolution for CP-17 — Saving Throws & Defensive Resolution Kernel.

Implements deterministic saving throw resolution:
- Fort/Ref/Will saves with condition modifiers
- Natural 1/20 handling
- Spell Resistance checks
- Save outcome effects (damage scaling, condition application)

All state mutations are event-driven only.
"""

from copy import deepcopy
from typing import List, Optional, Tuple
from dataclasses import dataclass

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.saves import SaveContext, SaveType, SaveOutcome, EffectSpec, SRCheck
from aidm.core.conditions import get_condition_modifiers, apply_condition
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import (
    create_prone_condition,
    create_flat_footed_condition,
    create_grappled_condition,
    create_grappling_condition,
    create_helpless_condition,
    create_stunned_condition,
    create_dazed_condition,
    create_shaken_condition,
    create_sickened_condition,
    create_frightened_condition,
    create_panicked_condition,
    create_nauseated_condition,
    create_fatigued_condition,
    create_exhausted_condition,
    create_paralyzed_condition,
    create_staggered_condition,
    create_unconscious_condition,
    create_pinned_condition,
    create_turned_condition,
)


# Mapping of condition type strings to factory functions
CONDITION_FACTORIES = {
    "prone": create_prone_condition,
    "flat_footed": create_flat_footed_condition,
    "grappled": create_grappled_condition,
    "grappling": create_grappling_condition,
    "helpless": create_helpless_condition,
    "stunned": create_stunned_condition,
    "dazed": create_dazed_condition,
    "shaken": create_shaken_condition,
    "sickened": create_sickened_condition,
    "frightened": create_frightened_condition,
    "panicked": create_panicked_condition,
    "nauseated": create_nauseated_condition,
    "fatigued": create_fatigued_condition,
    "exhausted": create_exhausted_condition,
    "paralyzed": create_paralyzed_condition,
    "staggered": create_staggered_condition,
    "unconscious": create_unconscious_condition,
    "pinned": create_pinned_condition,
    "turned": create_turned_condition,
}


def get_save_bonus(
    world_state: WorldState,
    actor_id: str,
    save_type: SaveType,
    save_descriptor: str = "",
    school: str = "",
) -> int:
    """Calculate total save bonus for an actor.

    Args:
        world_state: Current world state
        actor_id: Entity making the save
        save_type: Type of save (Fort/Ref/Will)
        save_descriptor: Optional context tag — "poison", "spell", "sla" (default: "")
        school: Spell school (lowercase) for school-specific racial bonuses (default: "")
                WO-ENGINE-RACIAL-ENCHANT-SAVE-001: pass "enchantment" for enchantment spells.

    Returns:
        Total save bonus (base + ability + condition modifiers)

    Raises:
        ValueError: If actor not found in world state
    """
    entity = world_state.entities.get(actor_id)
    if entity is None:
        raise ValueError(f"Actor not found in world state: {actor_id}")

    # Get base save using EF constants
    save_key_map = {
        SaveType.FORT: EF.SAVE_FORT,
        SaveType.REF: EF.SAVE_REF,
        SaveType.WILL: EF.SAVE_WILL,
    }
    base_save = entity.get(save_key_map[save_type], 0)

    # WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001: ability_mod removal (PHB p.136)
    # EF.SAVE_FORT/REF/WILL are Type 2 fields (base + ability_mod baked in at chargen).
    # Do NOT add ability_mod again here. The old code double-counted.

    # Get condition modifiers
    condition_mods = get_condition_modifiers(world_state, actor_id)
    save_mod_map = {
        SaveType.FORT: condition_mods.fort_save_modifier,
        SaveType.REF: condition_mods.ref_save_modifier,
        SaveType.WILL: condition_mods.will_save_modifier
    }
    condition_save_mod = save_mod_map[save_type]

    # WO-ENGINE-BARDIC-MUSIC-001: Inspire Courage morale bonus for fear/charm saves (PHB p.29)
    # v1: applied to all saves (no descriptor tracking yet; fear/charm are Will saves)
    # FINDING-BARDIC-SAVE-SCOPE-001: narrow to fear/charm descriptors when descriptor tracking added
    inspire_courage_bonus = (
        entity.get(EF.INSPIRE_COURAGE_BONUS, 0)
        if entity.get(EF.INSPIRE_COURAGE_ACTIVE, False) else 0
    )

    # WO-ENGINE-SAVE-FEATS-001: Great Fortitude / Iron Will / Lightning Reflexes
    feats = entity.get(EF.FEATS, [])
    feat_save_bonus = 0
    if save_type == SaveType.FORT and "great_fortitude" in feats:
        feat_save_bonus = 2
    elif save_type == SaveType.REF and "lightning_reflexes" in feats:
        feat_save_bonus = 2
    elif save_type == SaveType.WILL and "iron_will" in feats:
        feat_save_bonus = 2

    # WO-ENGINE-DIVINE-GRACE-001: Paladin Divine Grace � CHA mod to all saves (PHB p.44)
    # Gained at paladin level 2+. Bonus is 0 if CHA mod is not positive.
    divine_grace_bonus = 0
    _paladin_level = entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
    if _paladin_level >= 2:
        _cha_mod = entity.get(EF.CHA_MOD, 0)
        if _cha_mod > 0:
            divine_grace_bonus = _cha_mod

    # WO-ENGINE-RACIAL-SAVES-001: Racial saving throw bonuses (PHB Table 2-1)
    # Halfling: +1 all saves. Dwarf: +2 vs poison (Fort), +2 vs spells/SLAs.
    # Gnome +2 vs illusions: DEFERRED — spell school not in save_descriptor yet.
    # FINDING-ENGINE-GNOME-ILLUSION-SAVE-001: needs spell school in save context.
    racial_save_bonus = entity.get(EF.RACIAL_SAVE_BONUS, 0)  # halfling all-saves
    racial_poison_bonus = 0
    racial_spell_bonus = 0
    if save_descriptor == "poison":
        racial_poison_bonus = entity.get(EF.SAVE_BONUS_POISON, 0)
    if save_descriptor in ("spell", "sla"):
        racial_spell_bonus = entity.get(EF.SAVE_BONUS_SPELLS, 0)

    # WO-ENGINE-RACIAL-ENCHANT-SAVE-001: Elf/half-elf +2 vs enchantment spells (PHB p.14/18)
    racial_enchantment_bonus = 0
    if school == "enchantment":
        racial_enchantment_bonus = entity.get(EF.SAVE_BONUS_ENCHANTMENT, 0)

    # WO-ENGINE-STILL-MIND-INDOMITABLE-WILL-001: Monk Still Mind (PHB p.41)
    # "A monk of 3rd level or higher gains a +2 bonus on saving throws against
    #  enchantment spells and effects." — ALL saves (Fort, Ref, Will).
    still_mind_bonus = 0
    _monk_level_sm = entity.get(EF.CLASS_LEVELS, {}).get("monk", 0)
    if _monk_level_sm >= 3 and school == "enchantment":
        still_mind_bonus = 2

    # WO-ENGINE-STILL-MIND-INDOMITABLE-WILL-001: Barbarian Indomitable Will (PHB p.26)
    # "While in a rage, a barbarian of 14th level or higher gains a +4 bonus
    #  on Will saves to resist enchantment spells." — Will only, rage only.
    indomitable_will_bonus = 0
    if save_type == SaveType.WILL and school == "enchantment":
        _temp_mods = entity.get(EF.TEMPORARY_MODIFIERS, {})
        if _temp_mods.get("indomitable_will_active", False):
            indomitable_will_bonus = 4

    # WO-ENGINE-AURA-OF-COURAGE-001: Paladin fear immunity + ally +4 morale (PHB p.44)
    # Paladin L2+ is immune to fear; allies within 10 ft get +4 morale vs fear saves.
    # FINDING-ENGINE-SAVE-DESCRIPTOR-PASS-001: save_descriptor not passed from resolve_save()
    # (SaveContext has no descriptor field). Tests call get_save_bonus() directly with
    # save_descriptor="fear" — full round-trip via resolve_save() is CONSUME_DEFERRED.
    fear_bonus = 0
    if save_descriptor == "fear":
        if entity.get(EF.FEAR_IMMUNE, False):
            # Immunity: return a large sentinel that guarantees auto-pass vs any realistic DC
            fear_bonus = 999
        else:
            # Check for conscious paladin ally within 10 ft (2 squares, Chebyshev)
            _actor_pos = entity.get(EF.POSITION)
            _actor_team = entity.get(EF.TEAM)
            _best_aoc = 0
            for _eid, _ent in world_state.entities.items():
                if _eid == actor_id:
                    continue
                if _ent.get(EF.CLASS_LEVELS, {}).get("paladin", 0) < 2:
                    continue
                if _ent.get(EF.TEAM) != _actor_team:
                    continue
                # Conscious check: not defeated, not dying
                if _ent.get(EF.DEFEATED, False) or _ent.get(EF.DYING, False):
                    continue
                _conds = _ent.get(EF.CONDITIONS, [])
                if any(
                    (c.get("type") == "unconscious" if isinstance(c, dict) else False)
                    for c in _conds
                ):
                    continue
                # Distance check: ≤ 2 squares = within 10 ft
                _ent_pos = _ent.get(EF.POSITION)
                if _actor_pos is not None and _ent_pos is not None:
                    _ax = _actor_pos.get("x", 0) if isinstance(_actor_pos, dict) else getattr(_actor_pos, "x", 0)
                    _ay = _actor_pos.get("y", 0) if isinstance(_actor_pos, dict) else getattr(_actor_pos, "y", 0)
                    _px = _ent_pos.get("x", 0) if isinstance(_ent_pos, dict) else getattr(_ent_pos, "x", 0)
                    _py = _ent_pos.get("y", 0) if isinstance(_ent_pos, dict) else getattr(_ent_pos, "y", 0)
                    if max(abs(_ax - _px), abs(_ay - _py)) > 2:
                        continue
                _best_aoc = 4
                break  # One conscious paladin within range is sufficient
            fear_bonus = _best_aoc

    # Morale non-stacking: Inspire Courage and Aura of Courage are both morale bonuses.
    # PHB p.136: same-type bonuses don't stack — use the higher of the two for fear saves.
    # For non-fear saves: inspire_courage applies normally (no AoC interaction).
    if save_descriptor == "fear" and fear_bonus < 999:
        effective_morale = max(inspire_courage_bonus, fear_bonus)
        inspire_courage_bonus = 0
        fear_bonus = effective_morale

    # Total bonus
    # WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001: ability_mod already in base_save (Type 2 field)
    total_bonus = (
        base_save + condition_save_mod + inspire_courage_bonus
        + feat_save_bonus + divine_grace_bonus
        + racial_save_bonus + racial_poison_bonus + racial_spell_bonus
        + racial_enchantment_bonus
        + still_mind_bonus + indomitable_will_bonus
        + fear_bonus
    )

    return total_bonus


def check_spell_resistance(
    sr_check: SRCheck,
    world_state: WorldState,
    target_id: str,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float
) -> Tuple[bool, List[Event]]:
    """Check Spell Resistance (SR).

    PHB p. 177: "To affect a creature that has spell resistance, a spellcaster
    must make a caster level check (d20 + caster level) at least equal to the
    creature's spell resistance."

    Args:
        sr_check: SR check specification
        world_state: Current world state
        target_id: Entity with SR
        rng: RNG manager (uses "saves" stream)
        next_event_id: Next event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (sr_passed, events)
        - sr_passed: True if SR was overcome, False if effect negated
        - events: SR check event
    """
    events = []

    # Get target SR
    target = world_state.entities.get(target_id)
    if target is None:
        # Target disappeared; treat as SR passed (effect continues)
        return (True, events)

    sr = target.get(EF.SR, 0)
    if sr == 0:
        # No SR; bypass check
        return (True, events)

    # Roll SR check (d20 + caster level)
    saves_rng = rng.stream("saves")
    d20_result = saves_rng.randint(1, 20)

    # WO-ENGINE-SPELL-PENETRATION-001: Spell Penetration feat bonus (PHB p.100)
    _caster = world_state.entities.get(sr_check.source_id, {})
    _caster_feats = _caster.get(EF.FEATS, [])
    _sp_bonus = 0
    if "spell_penetration" in _caster_feats:
        _sp_bonus += 2
    if "greater_spell_penetration" in _caster_feats:
        _sp_bonus += 2  # Stacks with spell_penetration per PHB p.94

    total = d20_result + sr_check.caster_level + _sp_bonus

    sr_passed = (total >= sr)

    # Emit SR check event
    events.append(Event(
        event_id=next_event_id,
        event_type="spell_resistance_checked",
        timestamp=timestamp,
        payload={
            "source_id": sr_check.source_id,
            "target_id": target_id,
            "d20_result": d20_result,
            "caster_level": sr_check.caster_level,
            "penetration_bonus": _sp_bonus,
            "total": total,
            "target_sr": sr,
            "sr_passed": sr_passed
        },
        citations=[{"source_id": "681f92bc94ff", "page": 177}]  # PHB SR rules
    ))

    return (sr_passed, events)


def resolve_save(
    save_context: SaveContext,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float
) -> Tuple[SaveOutcome, List[Event]]:
    """Resolve a saving throw.

    This is the core CP-17 proof function. It:
    1. Checks SR (if applicable) - may negate effect
    2. Rolls d20 + save_bonus
    3. Compares to DC
    4. Determines outcome (SUCCESS / FAILURE / PARTIAL)
    5. Returns outcome and events

    Args:
        save_context: Save context with DC, effects, etc.
        world_state: Current world state
        rng: RNG manager (uses "saves" stream)
        next_event_id: Next available event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (outcome, events)
    """
    events = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    # Validate target exists
    if save_context.target_id not in world_state.entities:
        raise ValueError(f"Target not found in world state: {save_context.target_id}")

    # Step 1: SR check (if applicable)
    if save_context.sr_check is not None:
        sr_passed, sr_events = check_spell_resistance(
            sr_check=save_context.sr_check,
            world_state=world_state,
            target_id=save_context.target_id,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=current_timestamp
        )
        events.extend(sr_events)
        current_event_id += len(sr_events)
        current_timestamp += 0.01

        if not sr_passed:
            # SR negated effect - no save needed
            # Emit a save_negated event
            events.append(Event(
                event_id=current_event_id,
                event_type="save_negated",
                timestamp=current_timestamp,
                payload={
                    "target_id": save_context.target_id,
                    "save_type": save_context.save_type.value,
                    "reason": "spell_resistance"
                }
            ))
            return (SaveOutcome.SUCCESS, events)  # Treat as success (no effect)

    # Step 2: Calculate save bonus
    save_bonus = get_save_bonus(world_state, save_context.target_id, save_context.save_type)

    # Step 3: Roll save (d20 + bonus)
    saves_rng = rng.stream("saves")
    d20_result = saves_rng.randint(1, 20)
    total = d20_result + save_bonus

    # Step 4: Determine outcome
    is_natural_20 = (d20_result == 20)
    is_natural_1 = (d20_result == 1)

    if is_natural_20:
        success = True
    elif is_natural_1:
        success = False
    else:
        success = (total >= save_context.dc)

    # Step 5: Classify outcome (SUCCESS / FAILURE / PARTIAL)
    if success:
        # Success: check for partial vs full success
        if save_context.on_partial is not None:
            outcome = SaveOutcome.PARTIAL
        else:
            outcome = SaveOutcome.SUCCESS
    else:
        outcome = SaveOutcome.FAILURE

    # Emit save_rolled event
    events.append(Event(
        event_id=current_event_id,
        event_type="save_rolled",
        timestamp=current_timestamp,
        payload={
            "target_id": save_context.target_id,
            "save_type": save_context.save_type.value,
            "d20_result": d20_result,
            "save_bonus": save_bonus,
            "total": total,
            "dc": save_context.dc,
            "outcome": outcome.value,
            "is_natural_20": is_natural_20,
            "is_natural_1": is_natural_1
        },
        citations=[{"source_id": "681f92bc94ff", "page": 177}]  # PHB saving throw rules
    ))

    return (outcome, events)


def apply_save_effects(
    save_context: SaveContext,
    outcome: SaveOutcome,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Apply save outcome effects (damage, conditions).

    Args:
        save_context: Save context with effect specs
        outcome: Save outcome (SUCCESS / FAILURE / PARTIAL)
        world_state: Current world state
        next_event_id: Next event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (updated_world_state, events)
    """
    events = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    # Select effect spec based on outcome
    effect_spec_map = {
        SaveOutcome.SUCCESS: save_context.on_success,
        SaveOutcome.FAILURE: save_context.on_failure,
        SaveOutcome.PARTIAL: save_context.on_partial
    }
    effect_spec = effect_spec_map.get(outcome)

    if effect_spec is None:
        # No effect defined for this outcome
        return (world_state, events)

    # Apply damage (if any)
    if save_context.base_damage > 0 and effect_spec.damage_multiplier > 0:
        final_damage = int(save_context.base_damage * effect_spec.damage_multiplier)

        target = world_state.entities.get(save_context.target_id)
        if target:
            hp_before = target.get(EF.HP_CURRENT, 0)
            hp_after = hp_before - final_damage

            # Emit hp_changed event
            events.append(Event(
                event_id=current_event_id,
                event_type="hp_changed",
                timestamp=current_timestamp,
                payload={
                    "entity_id": save_context.target_id,
                    "hp_before": hp_before,
                    "hp_after": hp_after,
                    "delta": -final_damage,
                    "source": "save_effect"
                }
            ))
            current_event_id += 1
            current_timestamp += 0.01

            # Apply HP change to state
            entities = deepcopy(world_state.entities)
            entities[save_context.target_id][EF.HP_CURRENT] = hp_after
            world_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=entities,
                active_combat=world_state.active_combat
            )

            # Check for defeat
            if hp_after <= 0:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="entity_defeated",
                    timestamp=current_timestamp,
                    payload={
                        "entity_id": save_context.target_id,
                        "hp_final": hp_after,
                        "defeated_by": save_context.source_id
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 145}]
                ))
                current_event_id += 1
                current_timestamp += 0.01

                # Mark entity as defeated
                entities = deepcopy(world_state.entities)
                entities[save_context.target_id][EF.DEFEATED] = True
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=entities,
                    active_combat=world_state.active_combat
                )

    # Apply conditions (if any)
    for condition_type in effect_spec.conditions_to_apply:
        if condition_type in CONDITION_FACTORIES:
            factory = CONDITION_FACTORIES[condition_type]
            condition = factory(
                source=f"save_effect:{save_context.source_id}",
                applied_at_event_id=current_event_id
            )

            # Emit condition_applied event
            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=current_timestamp,
                payload={
                    "target_id": save_context.target_id,
                    "condition_type": condition_type,
                    "source": f"save_effect:{save_context.source_id}"
                }
            ))
            current_event_id += 1
            current_timestamp += 0.01

            # Apply condition to state
            world_state = apply_condition(world_state, save_context.target_id, condition)

    return (world_state, events)
