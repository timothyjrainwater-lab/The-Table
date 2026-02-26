"""Vertical Slice V1 Play Loop — Execution Proof + Combat Integration (CP-12)

Deterministic turn execution that wires together:
- Intent ingestion (policy-based or combat intents)
- Legality checking and validation
- Policy evaluation (for monsters)
- Combat resolution (CP-10/CP-11 integration)
- Event emission
- State mutation via events

CP-12 SCOPE:
- Player combat intents (AttackIntent, FullAttackIntent) route to resolvers
- Monster policy stubs (combat integration deferred to CP-13)
- Intent validation (actor match, target exists, target not defeated)
- Deterministic narration tokens

CP-13 SCOPE:
- Monster combat intent mapping (policy → AttackIntent)
- Tactic-to-intent routing for attack_nearest, focus_fire
- Target selection from TacticCandidate.target_ids
- Preserve CP-09 behavior for unmapped tactics

CP-15 SCOPE:
- Attacks of Opportunity (AoO) interrupt system
- AoO trigger detection (movement out, ranged attack, spellcasting)
- AoO resolution in initiative order before main action
- Action abortion if provoker defeated by AoO

CP-18 SCOPE:
- Combat maneuver routing (Bull Rush, Trip, Overrun, Sunder, Disarm, Grapple)
- Maneuver-specific AoO handling
- Condition application from maneuvers (Prone, Grappled)

WO-015 SCOPE:
- Spellcasting resolution (CastSpellIntent handling)
- Integration with SpellResolver, DurationTracker
- STP generation for spell casts
- Concentration break on caster damage
"""

import uuid
import random
from copy import deepcopy
from typing import List, Dict, Any, Optional, Union, Tuple, Literal
from dataclasses import dataclass

from aidm.core.event_log import Event, EventLog
from aidm.core.conditions import get_condition_modifiers, tick_conditions
from aidm.core.state import WorldState, FrozenWorldStateView
# CP-24: Action economy enforcement
from aidm.core.action_economy import ActionBudget, get_action_type
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.entity_fields import EF
from aidm.core.tactical_policy import evaluate_tactics, TacticalPolicyResult
from aidm.schemas.attack import AttackIntent, Weapon, StepMoveIntent, FullMoveIntent, EnergyDrainAttackIntent
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.full_attack_resolver import FullAttackIntent, resolve_full_attack, apply_full_attack_events
from aidm.core.rng_protocol import RNGProvider
from aidm.core.aoo import check_aoo_triggers, resolve_aoo_sequence, aoo_dealt_damage  # CP-15/CP-18
# CP-18A: Mounted combat imports
from aidm.schemas.mounted_combat import MountedMoveIntent, DismountIntent, MountIntent
from aidm.core.mounted_combat import (
    resolve_mount, resolve_dismount, get_entity_position
)
# CP-18: Combat maneuver imports
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent, GrappleEscapeIntent,
)
from aidm.core.maneuver_resolver import resolve_maneuver, resolve_grapple_escape, resolve_pin_escape
from aidm.schemas.maneuvers import PinEscapeIntent
# WO-ENGINE-COMPANION-WIRE: Companion summon imports
from aidm.schemas.intents import (
    SummonCompanionIntent, RestIntent, PrepareSpellsIntent, CoupDeGraceIntent,
    ChargeIntent, TurnUndeadIntent, ReadyActionIntent, AidAnotherIntent,
    FightDefensivelyIntent, TotalDefenseIntent, FeintIntent,
    AbilityDamageIntent, WithdrawIntent, DelayIntent,
    RageIntent, SmiteEvilIntent, LayOnHandsIntent, BardicMusicIntent, WildShapeIntent, RevertFormIntent,
    NaturalAttackIntent, StabilizeIntent, CalledShotIntent, DemoralizeIntent,
)
from aidm.core.companion_resolver import spawn_companion
# WO-ENGINE-LEVELUP-WIRE: XP award and level-up wiring
from aidm.core.experience_resolver import award_xp, check_level_up, apply_level_up
# WO-015: Spellcasting imports
from aidm.schemas.conditions import ConditionType, ConditionModifiers, ConditionInstance
from aidm.core.spell_resolver import (
    SpellCastIntent, SpellResolver, CasterStats, TargetStats,
    SpellDefinition, SpellEffect
)
from aidm.schemas.spell_definitions import SPELL_REGISTRY
from aidm.core.duration_tracker import DurationTracker, ActiveSpellEffect, create_effect
from aidm.schemas.position import Position
from aidm.core.geometry_engine import BattleGrid


def resolve_monster_combat_intent(
    policy_result: TacticalPolicyResult,
    doctrine: MonsterDoctrine,
    actor_id: str,
    world_state: WorldState
) -> Optional[AttackIntent]:
    """
    Map monster policy output to combat intent (CP-13).

    Converts policy tactic selection to AttackIntent for attack-based tactics.
    Target selection: use TacticCandidate.target_ids if present, otherwise find
    enemy targets from WorldState, sorted lexicographically, pick first valid.

    Args:
        policy_result: Policy evaluation result
        doctrine: Monster doctrine (must have weapon and attack_bonus)
        actor_id: Monster entity ID
        world_state: Current world state

    Returns:
        AttackIntent if mapping succeeds, None if unmapped tactic or missing data
    """
    # Check policy status
    if policy_result.status != "ok" or policy_result.selected is None:
        return None

    selected_tactic = policy_result.selected.candidate.tactic_class

    # CP-13 SCOPE: Map attack-based tactics only
    ATTACK_TACTICS = {"attack_nearest", "focus_fire"}

    if selected_tactic not in ATTACK_TACTICS:
        # Unmapped tactic: preserve CP-09 behavior (return None)
        return None

    # Validate doctrine has required combat parameters
    if doctrine.weapon is None or doctrine.attack_bonus is None:
        # Missing combat data: cannot map to intent
        return None

    # Target selection: use policy output if available, otherwise find enemies
    target_ids = policy_result.selected.candidate.target_ids or []

    # If no targets from policy, find all enemy entities
    if not target_ids:
        actor_entity = world_state.entities.get(actor_id)
        if actor_entity:
            actor_team = actor_entity.get(EF.TEAM, "monsters")
            # Find all entities on different team
            for entity_id, entity in world_state.entities.items():
                if entity_id != actor_id:
                    entity_team = entity.get(EF.TEAM, "unknown")
                    if entity_team != actor_team and entity_team != "unknown":
                        target_ids.append(entity_id)

    # Sort lexicographically for determinism
    sorted_targets = sorted(target_ids)

    # Pick first valid target (exists and not defeated)
    target_id = None
    for tid in sorted_targets:
        if tid in world_state.entities:
            entity = world_state.entities[tid]
            if not entity.get(EF.DEFEATED, False):
                target_id = tid
                break

    # No valid target found
    if target_id is None:
        return None

    # Create AttackIntent
    return AttackIntent(
        attacker_id=actor_id,
        target_id=target_id,
        attack_bonus=doctrine.attack_bonus,
        weapon=doctrine.weapon
    )


# ==============================================================================
# WO-015: SPELLCASTING RESOLUTION HELPERS
# ==============================================================================

def _create_caster_stats(
    caster_id: str,
    world_state: WorldState,
) -> CasterStats:
    """Create CasterStats from WorldState entity data.

    Args:
        caster_id: Entity ID of the caster
        world_state: Current world state

    Returns:
        CasterStats with position and spell parameters
    """
    entity = world_state.entities.get(caster_id, {})

    # Get position
    pos_data = entity.get(EF.POSITION, {"x": 0, "y": 0})
    if isinstance(pos_data, Position):
        position = pos_data
    else:
        position = Position(x=pos_data.get("x", 0), y=pos_data.get("y", 0))

    # Get caster level (default 5 for testing)
    caster_level = entity.get("caster_level", 5)

    # Get spell DC base (default 10 + 3 for INT/WIS mod)
    spell_dc_base = entity.get("spell_dc_base", 13)

    # Get attack bonus for touch/ray spells
    attack_bonus = entity.get(EF.ATTACK_BONUS, 0)

    return CasterStats(
        caster_id=caster_id,
        position=position,
        caster_level=caster_level,
        spell_dc_base=spell_dc_base,
        attack_bonus=attack_bonus,
    )


def _create_target_stats(
    entity_id: str,
    world_state: WorldState,
) -> TargetStats:
    """Create TargetStats from WorldState entity data.

    Args:
        entity_id: Entity ID of the target
        world_state: Current world state

    Returns:
        TargetStats with position, HP, and saves
    """
    entity = world_state.entities.get(entity_id, {})

    # Get position
    pos_data = entity.get(EF.POSITION, {"x": 0, "y": 0})
    if isinstance(pos_data, Position):
        position = pos_data
    else:
        position = Position(x=pos_data.get("x", 0), y=pos_data.get("y", 0))

    # Get HP
    hp_current = entity.get(EF.HP_CURRENT, 10)
    hp_max = entity.get(EF.HP_MAX, 10)

    # Get saves
    fort_save = entity.get(EF.SAVE_FORT, 0)
    ref_save = entity.get(EF.SAVE_REF, 0)
    will_save = entity.get(EF.SAVE_WILL, 0)

    # WO-ENGINE-ENERGY-DRAIN-001: Each negative level gives -1 to all saves (PHB p.215)
    neg_level_penalty = entity.get(EF.NEGATIVE_LEVELS, 0)
    fort_save -= neg_level_penalty
    ref_save -= neg_level_penalty
    will_save -= neg_level_penalty

    # Get SR
    sr = entity.get(EF.SR, 0)

    return TargetStats(
        entity_id=entity_id,
        position=position,
        hit_points=hp_current,
        max_hit_points=hp_max,
        fort_save=fort_save,
        ref_save=ref_save,
        will_save=will_save,
        spell_resistance=sr,
    )


def _get_or_create_duration_tracker(world_state: WorldState) -> DurationTracker:
    """Get duration tracker from active_combat or create new one.

    Args:
        world_state: Current world state

    Returns:
        DurationTracker instance
    """
    if world_state.active_combat is None:
        return DurationTracker()

    tracker_data = world_state.active_combat.get("duration_tracker")
    if tracker_data is None:
        return DurationTracker()

    return DurationTracker.from_dict(tracker_data)


# Mapping from ConditionType values to their canonical factory functions.
# Import here to avoid circular imports at module level.
from aidm.schemas.conditions import (
    create_prone_condition, create_flat_footed_condition,
    create_grappled_condition, create_helpless_condition,
    create_stunned_condition, create_dazed_condition,
    create_shaken_condition, create_sickened_condition,
    create_frightened_condition, create_panicked_condition,
    create_nauseated_condition, create_fatigued_condition,
    create_exhausted_condition, create_paralyzed_condition,
    create_staggered_condition, create_unconscious_condition,
)

_CONDITION_FACTORIES = {
    "prone": create_prone_condition,
    "flat_footed": create_flat_footed_condition,
    "grappled": create_grappled_condition,
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
}


def _make_condition_dict(condition: str, source: str, event_id: int) -> Dict[str, Any]:
    """Build a ConditionInstance-compatible dict for storage in EF.CONDITIONS.

    For conditions with a canonical ConditionType factory (prone, stunned, etc.),
    uses the factory to get proper mechanical modifiers (AC penalty, attack penalty, etc.).
    For spell buff/debuff labels without a canonical factory (mage_armor, shield, etc.),
    creates a minimal dict with zero modifiers — tracked for presence, not effect.

    Returns a dict compatible with ConditionInstance.to_dict() / from_dict().
    """
    factory = _CONDITION_FACTORIES.get(condition)
    if factory is not None:
        instance = factory(source=source, applied_at_event_id=event_id)
        return instance.to_dict()

    # No canonical factory — build minimal dict with zero modifiers
    return {
        "condition_type": condition,
        "source": source,
        "modifiers": ConditionModifiers().to_dict(),
        "applied_at_event_id": event_id,
        "notes": None,
    }


# ==============================================================================
# SPELL SLOT GOVERNOR — WO-ENGINE-SPELL-SLOTS-001
# ==============================================================================

def _check_spell_slot_for_dict(
    slots: Dict[int, int],
    spell_level: int,
) -> Tuple[bool, str]:
    """Check a specific slots dict for availability at the given level.

    Returns (ok, reason). Handles both int and str keys (JSON deserialization).
    """
    # Support both int and str keys (JSON deserializes all dict keys as strings)
    available = slots.get(spell_level, slots.get(str(spell_level), 0))
    if available <= 0:
        return False, f"spell_slot_empty_level_{spell_level}"
    return True, ""


def _check_spell_slot(
    entity_state: Dict[str, Any],
    spell_level: int,
) -> Tuple[bool, str]:
    """Returns (ok, reason). reason is empty string on success.

    Cantrips (level 0) always pass.
    If entity has no SPELL_SLOTS, fails with 'no_spell_slots'.
    """
    if spell_level == 0:
        return True, ""

    slots: Optional[Dict[int, int]] = entity_state.get(EF.SPELL_SLOTS)
    if slots is None:
        return False, "no_spell_slots"

    return _check_spell_slot_for_dict(slots, spell_level)


def _validate_spell_known(
    entity_state: Dict[str, Any],
    spell_id: str,
    spell_level: int,
) -> Tuple[bool, str]:
    """Validates spell is in prepared list (prepared casters) or known list (spontaneous).

    Returns (ok, reason).
    Cantrips are exempt. Unknown caster class is fail-open (NPCs/monsters).
    """
    if spell_level == 0:
        return True, ""

    caster_class = entity_state.get(EF.CASTER_CLASS, "")

    PREPARED_CASTERS = {"wizard", "cleric", "druid", "ranger", "paladin"}
    SPONTANEOUS_CASTERS = {"sorcerer", "bard"}

    if caster_class in PREPARED_CASTERS:
        prepared: Dict[int, List[str]] = entity_state.get(EF.SPELLS_PREPARED, {})
        # Support both int and str keys (JSON deserialization)
        level_list = prepared.get(spell_level, prepared.get(str(spell_level), []))
        if spell_id not in level_list:
            return False, "spell_not_prepared"

    elif caster_class in SPONTANEOUS_CASTERS:
        known: Dict[int, List[str]] = entity_state.get(EF.SPELLS_KNOWN, {})
        # Support both int and str keys (JSON deserialization)
        level_list = known.get(spell_level, known.get(str(spell_level), []))
        if spell_id not in level_list:
            return False, "spell_not_known"

    # Unknown caster class — fail-open for NPCs/monsters
    return True, ""


def _decrement_spell_slot(
    entity_state: Dict[str, Any],
    spell_level: int,
    use_secondary: bool = False,
) -> None:
    """Decrements entity spell slot count for the given level.

    Cantrips are no-op. Never goes below 0.
    If use_secondary is True, decrements SPELL_SLOTS_2 instead.
    Handles both int and str keys (JSON deserialization).
    """
    if spell_level == 0:
        return
    slot_key = EF.SPELL_SLOTS_2 if use_secondary else EF.SPELL_SLOTS
    slots: Dict[int, int] = entity_state[slot_key]
    # Determine canonical key (int or str)
    if spell_level in slots:
        slots[spell_level] = max(0, slots[spell_level] - 1)
    elif str(spell_level) in slots:
        slots[str(spell_level)] = max(0, slots[str(spell_level)] - 1)


# ==============================================================================
# END SPELL SLOT GOVERNOR
# ==============================================================================


# WO-ENGINE-CALLED-SHOT-POLICY-001: Called shot suggestion map (STRAT-CAT-05 Option A)
_CALLED_SHOT_SUGGESTION_MAP = {
    # body-part / intent keywords → suggested PHB mechanics
    "weapon": ["disarm (PHB p.155)", "sunder (PHB p.158)"],
    "sword": ["disarm (PHB p.155)", "sunder (PHB p.158)"],
    "shield": ["sunder (PHB p.158)"],
    "leg": ["trip (PHB p.158)"],
    "knee": ["trip (PHB p.158)"],
    "foot": ["trip (PHB p.158)"],
    "eye": ["standard attack (PHB p.140)"],
    "head": ["standard attack (PHB p.140)"],
    "throat": ["standard attack (PHB p.140)"],
    "hand": ["disarm (PHB p.155)"],
}

_CALLED_SHOT_DEFAULT_SUGGESTIONS = [
    "standard attack (PHB p.140)",
    "trip (PHB p.158)",
    "disarm (PHB p.155)",
    "feint (PHB p.68)",
]


def _called_shot_suggestions(target_description: str) -> List[str]:
    """Map a called shot target description to nearest named mechanics (STRAT-CAT-05)."""
    desc_lower = target_description.lower()
    for keyword, suggestions in _CALLED_SHOT_SUGGESTION_MAP.items():
        if keyword in desc_lower:
            return suggestions
    return _CALLED_SHOT_DEFAULT_SUGGESTIONS


def _resolve_spell_cast(
    intent: SpellCastIntent,
    world_state: WorldState,
    rng: RNGProvider,
    grid: Optional[BattleGrid],
    next_event_id: int,
    timestamp: float,
    turn_index: int,
) -> Tuple[List[Event], WorldState, str]:
    """Resolve a spell cast intent.

    Args:
        intent: The spell cast intent
        world_state: Current world state
        rng: RNG manager
        grid: Optional battle grid for spatial queries
        next_event_id: Next event ID
        timestamp: Event timestamp
        turn_index: Current turn index

    Returns:
        Tuple of (events, updated_world_state, narration_token)
    """
    events = []
    current_event_id = next_event_id

    # Look up spell
    spell = SPELL_REGISTRY.get(intent.spell_id)
    if spell is None:
        # Unknown spell
        events.append(Event(
            event_id=current_event_id,
            event_type="spell_cast_failed",
            timestamp=timestamp,
            payload={
                "caster_id": intent.caster_id,
                "spell_id": intent.spell_id,
                "reason": f"Unknown spell: {intent.spell_id}",
                "turn_index": turn_index,
            }
        ))
        return events, world_state, "spell_failed"

    # ── Spell slot governor ────────────────────────────────────────────────────
    spell_level = spell.level
    # Work on a live reference so we can mutate after success
    caster_state = world_state.entities.get(intent.caster_id, {})

    # WO-ENGINE-VERBAL-SPELL-BLOCK-001: Verbal component block (PHB p.174)
    # Check BEFORE metamagic — a gagged/silenced caster cannot speak regardless
    # of any metamagic feat applied. Silent Spell suppresses the V component.
    _has_verbal = getattr(spell, "has_verbal", True)
    _is_silent = "silent" in getattr(intent, "metamagic", ())
    if _has_verbal and not _is_silent:
        _caster_conditions = caster_state.get(EF.CONDITIONS, {})
        _speech_blocked = (
            "silenced" in _caster_conditions
            or "gagged" in _caster_conditions
        )
        if _speech_blocked:
            events.append(Event(
                event_id=current_event_id,
                event_type="spell_blocked",
                timestamp=timestamp,
                payload={
                    "actor_id": intent.caster_id,
                    "spell_id": intent.spell_id,
                    "spell_name": spell.name,
                    "reason": "verbal_component_blocked",
                    "detail": "Caster cannot speak — Verbal component unavailable (PHB p.174).",
                    "turn_index": turn_index,
                },
                citations=["PHB p.174"],
            ))
            # No slot consumed — clean deny, player must re-declare (PHB p.174)
            return events, world_state, "spell_blocked"

    # WO-ENGINE-SOMATIC-COMPONENT-001: Somatic component block (PHB p.174)
    # A pinned or bound caster cannot gesture — somatic component unavailable.
    # Still Spell metamagic removes the somatic requirement — bypass this block.
    # GRAPPLED (not pinned) does NOT block somatic; it triggers Concentration instead (future WO).
    _has_somatic_sc = getattr(spell, "has_somatic", True)
    _is_still_sc = "still" in getattr(intent, "metamagic", ())
    if _has_somatic_sc and not _is_still_sc:
        _caster_conds_sc = caster_state.get(EF.CONDITIONS, {})
        _somatic_blocked = (
            "pinned" in _caster_conds_sc
            or "bound" in _caster_conds_sc
        )
        if _somatic_blocked:
            _blocking_cond = "pinned" if "pinned" in _caster_conds_sc else "bound"
            events.append(Event(
                event_id=current_event_id,
                event_type="spell_blocked",
                timestamp=timestamp,
                payload={
                    "actor_id": intent.caster_id,
                    "spell_id": intent.spell_id,
                    "spell_name": spell.name,
                    "reason": "somatic_component_blocked",
                    "blocking_condition": _blocking_cond,
                    "detail": "Caster cannot gesture — Somatic component unavailable (PHB p.174).",
                    "turn_index": turn_index,
                },
                citations=["PHB p.174"],
            ))
            # No slot consumed — clean deny (PHB p.174)
            return events, world_state, "spell_blocked"

    # WO-ENGINE-METAMAGIC-001: Validate metamagic prerequisites and compute effective slot level
    _metamagic = list(getattr(intent, "metamagic", ()) or ())
    _heighten_to_level: Optional[int] = getattr(intent, "heighten_to_level", None)
    _effective_slot_level = spell_level

    if _metamagic:
        from aidm.core.metamagic_resolver import (
            validate_metamagic, compute_effective_slot_level,
        )
        _mm_error = validate_metamagic(
            metamagic=_metamagic,
            caster=caster_state,
            heighten_to_level=_heighten_to_level,
            base_spell_level=spell_level,
        )
        if _mm_error:
            return [Event(
                event_id=current_event_id,
                event_type="metamagic_failed",
                timestamp=timestamp,
                payload={
                    "actor_id": intent.caster_id,
                    "spell_name": spell.name,
                    "spell_level": spell_level,
                    "metamagic": _metamagic,
                    "reason": _mm_error,
                    "turn_index": turn_index,
                },
            )], world_state, "metamagic_failed"

        _effective_slot_level = compute_effective_slot_level(
            spell_base_level=spell_level,
            metamagic=_metamagic,
            heighten_to_level=_heighten_to_level,
        )

    # Slot check uses the effective slot level (metamagic surcharge consumed)
    slot_ok, slot_reason = _check_spell_slot(caster_state, _effective_slot_level)
    _use_secondary = False

    if not slot_ok and EF.SPELL_SLOTS_2 in caster_state:
        # Dual-caster fallback: try secondary slot pool
        slots_2: Dict[int, int] = caster_state.get(EF.SPELL_SLOTS_2, {})
        slot_ok_2, _ = _check_spell_slot_for_dict(slots_2, _effective_slot_level)
        if slot_ok_2:
            slot_ok = True
            slot_reason = ""
            _use_secondary = True

    if not slot_ok:
        return [Event(
            event_id=current_event_id,
            event_type="spell_slot_empty",
            timestamp=timestamp,
            payload={
                "actor_id": intent.caster_id,
                "spell_name": spell.name,
                "spell_level": _effective_slot_level,
                "reason": slot_reason,
                "turn_index": turn_index,
            },
        )], world_state, "spell_slot_empty"

    known_ok, known_reason = _validate_spell_known(caster_state, intent.spell_id, spell_level)
    if not known_ok and _use_secondary:
        # Dual-caster using secondary slot pool: re-validate against secondary class lists
        secondary_state = {
            EF.CASTER_CLASS: caster_state.get(EF.CASTER_CLASS_2, ""),
            EF.SPELLS_PREPARED: caster_state.get(EF.SPELLS_PREPARED_2, {}),
            EF.SPELLS_KNOWN: caster_state.get(EF.SPELLS_KNOWN_2, {}),
        }
        known_ok, known_reason = _validate_spell_known(secondary_state, intent.spell_id, spell_level)
    if not known_ok:
        return [Event(
            event_id=current_event_id,
            event_type="spell_slot_empty",
            timestamp=timestamp,
            payload={
                "actor_id": intent.caster_id,
                "spell_name": spell.name,
                "spell_level": spell_level,
                "reason": known_reason,
                "turn_index": turn_index,
            },
        )], world_state, "spell_slot_empty"
    # ──────────────────────────────────────────────────────────────────────────

    # Create caster stats
    caster = _create_caster_stats(intent.caster_id, world_state)

    # WO-ENGINE-SPELL-FOCUS-DC-001: Spell Focus / Greater Spell Focus DC bonus
    _spell_focus_bonus = 0
    _caster_feats = world_state.entities.get(intent.caster_id, {}).get(EF.FEATS, [])
    _spell_school = spell.school if hasattr(spell, "school") else ""
    if _spell_school:
        if f"spell_focus_{_spell_school}" in _caster_feats:
            _spell_focus_bonus += 1
        if f"greater_spell_focus_{_spell_school}" in _caster_feats:
            _spell_focus_bonus += 1
    if _spell_focus_bonus:
        from dataclasses import replace as _dc_replace
        caster = _dc_replace(caster, spell_focus_bonus=_spell_focus_bonus)

    # WO-ENGINE-METAMAGIC-001: Heighten Spell raises spell DC by (heighten_to_level - base_level)
    # CasterStats.get_spell_dc(level) = spell_dc_base + level; raise base by the delta.
    if "heighten" in _metamagic and _heighten_to_level is not None:
        from dataclasses import replace as _dc_replace
        caster = _dc_replace(
            caster,
            spell_dc_base=caster.spell_dc_base + (_heighten_to_level - spell_level)
        )

    # Build target stats for all potential targets
    targets: Dict[str, TargetStats] = {}
    for entity_id in world_state.entities:
        if entity_id != intent.caster_id:
            targets[entity_id] = _create_target_stats(entity_id, world_state)

    # Add caster as potential target (for self spells)
    targets[intent.caster_id] = _create_target_stats(intent.caster_id, world_state)

    # Create a minimal grid if none provided
    if grid is None:
        grid = BattleGrid(100, 100)
        # Place entities on grid based on position
        from aidm.schemas.geometry import SizeCategory
        for entity_id, entity in world_state.entities.items():
            pos_data = entity.get(EF.POSITION, {"x": 0, "y": 0})
            if isinstance(pos_data, dict):
                pos = Position(x=pos_data.get("x", 0), y=pos_data.get("y", 0))
            else:
                pos = pos_data
            if grid.in_bounds(pos):
                grid.place_entity(entity_id, pos, SizeCategory.MEDIUM)

    # Create spell resolver
    resolver = SpellResolver(
        grid=grid,
        rng=rng,
        spell_registry=SPELL_REGISTRY,
        turn=turn_index,
        initiative=0,
    )

    # Validate cast
    valid, error = resolver.validate_cast(intent, caster)
    if not valid:
        events.append(Event(
            event_id=current_event_id,
            event_type="spell_cast_failed",
            timestamp=timestamp,
            payload={
                "caster_id": intent.caster_id,
                "spell_id": intent.spell_id,
                "spell_name": spell.name,
                "reason": error,
                "turn_index": turn_index,
            },
            citations=list(spell.rule_citations),
        ))
        return events, world_state, "spell_failed"

    # WO-ENGINE-ARCANE-SPELL-FAILURE-001: Arcane Spell Failure check (PHB p.123)
    _asf_pct = caster_state.get(EF.ARCANE_SPELL_FAILURE, 0) if caster_state else 0
    _has_somatic = getattr(spell, "has_somatic", True)
    _is_arcane = (
        caster_state.get(EF.CLASS_LEVELS, {}).get("wizard", 0) > 0
        or caster_state.get(EF.CLASS_LEVELS, {}).get("sorcerer", 0) > 0
        or caster_state.get(EF.CLASS_LEVELS, {}).get("bard", 0) > 0
    )

    # WO-ENGINE-STILL-SPELL-001: Still Spell suppresses somatic component -> bypass ASF (PHB p.100)
    _is_still = "still" in getattr(intent, "metamagic", ())
    if _asf_pct > 0 and _has_somatic and not _is_still and _is_arcane:
        _asf_roll = random.randint(1, 100)
        if _asf_roll <= _asf_pct:
            # Slot consumed on failure (PHB p.123)
            _asf_entities = deepcopy(world_state.entities)
            if _effective_slot_level > 0 and intent.caster_id in _asf_entities:
                _decrement_spell_slot(_asf_entities[intent.caster_id], _effective_slot_level, use_secondary=_use_secondary)
            _asf_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=_asf_entities,
                active_combat=world_state.active_combat,
            )
            events.append(Event(
                event_id=current_event_id,
                event_type="spell_failed_asf",
                timestamp=timestamp,
                payload={
                    "actor_id": intent.caster_id,
                    "spell_name": spell.name,
                    "asf_pct": _asf_pct,
                    "roll": _asf_roll,
                    "slot_consumed": True,
                },
                citations=["PHB p.123"],
            ))
            return events, _asf_state, "spell_failed_asf"

    # Resolve the spell (CP-18: pass world_state for condition save modifiers)
    # WO-ENGINE-METAMAGIC-001: pass maximize flag so SpellResolver skips dice consumption
    _maximize = "maximize" in _metamagic
    resolution = resolver.resolve_spell(intent, caster, targets, world_state=world_state,
                                        maximize=_maximize)

    # WO-ENGINE-METAMAGIC-001: Post-process resolution for empower/extend/heighten
    # Maximize is already handled in spell_resolver._resolve_damage — no post-processing needed.
    _mm_applied: List[str] = []
    if _metamagic:
        from aidm.core.metamagic_resolver import apply_empower
        # Empower: multiply final damage total by 1.5 (floor)
        if "empower" in _metamagic and resolution.damage_dealt:
            _new_damage = {eid: apply_empower(dmg) for eid, dmg in resolution.damage_dealt.items()}
            from dataclasses import replace as _dc_replace
            resolution = _dc_replace(resolution, damage_dealt=_new_damage)

        # Empower applied to healing dice (variable numeric)
        if "empower" in _metamagic and resolution.healing_done:
            _new_healing = {eid: apply_empower(h) for eid, h in resolution.healing_done.items()}
            from dataclasses import replace as _dc_replace
            resolution = _dc_replace(resolution, healing_done=_new_healing)

        _mm_applied = [mm for mm in ("empower", "maximize", "extend", "heighten", "quicken")
                       if mm in _metamagic]

    # Emit spell_cast event
    events.append(Event(
        event_id=current_event_id,
        event_type="spell_cast",
        timestamp=timestamp,
        payload={
            "cast_id": resolution.cast_id,
            "caster_id": resolution.caster_id,
            "spell_id": resolution.spell_id,
            "spell_name": spell.name,
            "spell_level": spell.level,
            "affected_entities": list(resolution.affected_entities),
            "turn_index": turn_index,
            "metamagic_applied": _mm_applied,  # WO-ENGINE-METAMAGIC-001
            "effective_slot_level": _effective_slot_level,  # WO-ENGINE-METAMAGIC-001
            **({"content_id": spell.content_id} if spell.content_id else {}),
        },
        citations=list(spell.rule_citations),
    ))
    current_event_id += 1

    # Deep copy entities for mutation
    entities = deepcopy(world_state.entities)

    # Apply damage
    for entity_id, damage in resolution.damage_dealt.items():
        if damage > 0 and entity_id in entities:
            old_hp = entities[entity_id].get(EF.HP_CURRENT, 0)
            new_hp = old_hp - damage

            # WO-ENGINE-MASSIVE-DAMAGE-RULE-001: Massive Damage check (PHB p.145)
            # Single hit 50+ HP damage → Fort DC 15 save or instant death.
            if damage >= 50:
                from aidm.core.save_resolver import get_save_bonus, SaveType as _SaveType
                _md_save_bonus = get_save_bonus(world_state, entity_id, _SaveType.FORT)
                _md_roll = rng.stream("combat").randint(1, 20)
                _md_total = _md_roll + _md_save_bonus
                _md_saved = _md_total >= 15
                events.append(Event(
                    event_id=current_event_id,
                    event_type="massive_damage_check",
                    timestamp=timestamp + 0.005,
                    payload={
                        "target_id": entity_id,
                        "damage": damage,
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
                    new_hp = -10  # Instant death (PHB p.145)

            entities[entity_id][EF.HP_CURRENT] = new_hp

            events.append(Event(
                event_id=current_event_id,
                event_type="hp_changed",
                timestamp=timestamp + 0.01,
                payload={
                    "entity_id": entity_id,
                    "old_hp": old_hp,
                    "new_hp": new_hp,
                    "delta": -damage,
                    "source": f"spell:{spell.name}",
                    "caster_id": intent.caster_id,
                    **({"damage_type": spell.damage_type.value} if spell.damage_type else {}),
                    **({"content_id": spell.content_id} if spell.content_id else {}),
                },
                citations=list(spell.rule_citations),
            ))
            current_event_id += 1

            # WO-ENGINE-DEATH-DYING-001: Three-band defeat check (PHB p.145)
            from aidm.core.dying_resolver import resolve_hp_transition
            trans_events, field_updates = resolve_hp_transition(
                entity_id=entity_id,
                old_hp=old_hp,
                new_hp=new_hp,
                source=f"spell:{spell.name}",
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.02,
            )
            for field_key, field_val in field_updates.items():
                entities[entity_id][field_key] = field_val
            events.extend(trans_events)
            current_event_id += len(trans_events)

    # Apply healing
    for entity_id, healing in resolution.healing_done.items():
        if healing > 0 and entity_id in entities:
            old_hp = entities[entity_id].get(EF.HP_CURRENT, 0)
            max_hp = entities[entity_id].get(EF.HP_MAX, old_hp)
            new_hp = min(old_hp + healing, max_hp)
            entities[entity_id][EF.HP_CURRENT] = new_hp

            events.append(Event(
                event_id=current_event_id,
                event_type="hp_changed",
                timestamp=timestamp + 0.01,
                payload={
                    "entity_id": entity_id,
                    "old_hp": old_hp,
                    "new_hp": new_hp,
                    "delta": healing,
                    "source": f"spell:{spell.name}",
                    **({"content_id": spell.content_id} if spell.content_id else {}),
                },
                citations=list(spell.rule_citations),
            ))
            current_event_id += 1

    # Get/create duration tracker
    duration_tracker = _get_or_create_duration_tracker(world_state)

    # Apply conditions and track durations
    for entity_id, condition in resolution.conditions_applied:
        # Initialize conditions dict if needed
        if EF.CONDITIONS not in entities[entity_id]:
            entities[entity_id][EF.CONDITIONS] = {}

        # Add condition if not already present (keyed by condition name)
        if condition not in entities[entity_id][EF.CONDITIONS]:
            condition_dict = _make_condition_dict(
                condition=condition,
                source=f"spell:{spell.name}",
                event_id=current_event_id,
            )
            entities[entity_id][EF.CONDITIONS][condition] = condition_dict

            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=timestamp + 0.02,
                payload={
                    "entity_id": entity_id,
                    "condition": condition,
                    "source": f"spell:{spell.name}",
                    "duration_rounds": spell.duration_rounds if spell.duration_rounds > 0 else None,
                    **({"content_id": spell.content_id} if spell.content_id else {}),
                },
                citations=list(spell.rule_citations),
            ))
            current_event_id += 1

        # Track duration for conditions with duration
        if spell.duration_rounds > 0:
            effect = create_effect(
                spell_id=spell.spell_id,
                spell_name=spell.name,
                caster_id=intent.caster_id,
                target_id=entity_id,
                duration_rounds=spell.duration_rounds,
                concentration=spell.concentration,
                condition=condition,
                turn=turn_index,
            )
            # WO-ENGINE-METAMAGIC-001: Extend doubles duration
            if "extend" in _metamagic:
                from aidm.core.metamagic_resolver import apply_extend
                effect = apply_extend(effect)
            duration_tracker.add_effect(effect)

    # Update active_combat with duration tracker
    active_combat = deepcopy(world_state.active_combat) if world_state.active_combat else {}
    active_combat["duration_tracker"] = duration_tracker.to_dict()

    # ── Decrement slot post-cast (only reaches here on success) ──────────────
    if _effective_slot_level > 0 and intent.caster_id in entities:
        _decrement_spell_slot(entities[intent.caster_id], _effective_slot_level, use_secondary=_use_secondary)
    # ──────────────────────────────────────────────────────────────────────────

    # Create updated world state
    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=active_combat,
    )

    # Determine narration token
    if spell.effect_type == SpellEffect.DAMAGE:
        total_damage = sum(resolution.damage_dealt.values())
        if total_damage > 0:
            narration = "spell_damage_dealt"
        else:
            narration = "spell_no_effect"
    elif spell.effect_type == SpellEffect.HEALING:
        narration = "spell_healed"
    elif spell.effect_type == SpellEffect.BUFF:
        narration = "spell_buff_applied"
    elif spell.effect_type == SpellEffect.DEBUFF:
        if resolution.conditions_applied:
            narration = "spell_debuff_applied"
        else:
            narration = "spell_resisted"
    else:
        narration = "spell_cast_success"

    return events, updated_state, narration


def _check_concentration_break(
    caster_id: str,
    damage_dealt: int,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Check if damage breaks concentration on a spell.

    Per PHB p.170, taking damage requires Concentration check DC 10 + damage dealt.
    On failure, concentration spell ends.

    Args:
        caster_id: Entity that took damage
        damage_dealt: Amount of damage taken
        world_state: Current world state
        rng: RNG manager
        next_event_id: Next event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (events, updated_world_state)
    """
    # WO-ENGINE-CONCENTRATION-001: Per-spell iteration (PHB p.170)
    events = []
    current_event_id = next_event_id

    duration_tracker = _get_or_create_duration_tracker(world_state)

    # Get ALL concentration effects — PHB p.170: each requires its own check
    concentration_effects = duration_tracker.get_concentration_effects(caster_id)
    if not concentration_effects:
        return events, world_state

    concentration_bonus = world_state.entities.get(caster_id, {}).get("concentration_bonus", 0)

    for effect in list(concentration_effects):  # list() to avoid mutate-during-iterate
        # Each spell gets its own independent check (PHB p.170)
        spell_level = getattr(effect, 'spell_level', 0)
        dc = 10 + damage_dealt + spell_level
        roll = rng.stream("combat").randint(1, 20)
        total = roll + concentration_bonus

        if total < dc:
            # This specific spell's concentration broken
            duration_tracker.remove_concentration_effect(effect.effect_id)

            events.append(Event(
                event_id=current_event_id,
                event_type="concentration_broken",
                timestamp=timestamp,
                payload={
                    "caster_id": caster_id,
                    "spell_id": effect.spell_id,
                    "spell_name": effect.spell_name,
                    "target_id": effect.target_id,
                    "dc": dc,
                    "roll": roll,
                    "total": total,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 170}],  # PHB Concentration
            ))
            current_event_id += 1

            # Remove condition applied by this specific effect
            if effect.condition_applied and effect.target_id:
                entities = deepcopy(world_state.entities)
                target_entity = entities.get(effect.target_id, {})
                conditions = target_entity.get(EF.CONDITIONS, {})
                if effect.condition_applied in conditions:
                    del conditions[effect.condition_applied]
                    target_entity[EF.CONDITIONS] = conditions

                    events.append(Event(
                        event_id=current_event_id,
                        event_type="condition_removed",
                        timestamp=timestamp + 0.01,
                        payload={
                            "entity_id": effect.target_id,
                            "condition": effect.condition_applied,
                            "reason": "concentration_broken",
                        },
                    ))
                    current_event_id += 1

                    # Update state after condition removal
                    active_combat = deepcopy(world_state.active_combat) if world_state.active_combat else {}
                    active_combat["duration_tracker"] = duration_tracker.to_dict()
                    world_state = WorldState(
                        ruleset_version=world_state.ruleset_version,
                        entities=entities,
                        active_combat=active_combat,
                    )
        else:
            # Check passed — spell maintained; emit audit event
            events.append(Event(
                event_id=current_event_id,
                event_type="concentration_check",
                timestamp=timestamp,
                payload={
                    "caster_id": caster_id,
                    "spell_id": effect.spell_id,
                    "spell_name": effect.spell_name,
                    "dc": dc,
                    "roll": roll,
                    "total": total,
                    "maintained": True,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 170}],  # PHB Concentration
            ))
            current_event_id += 1

    # Persist updated duration tracker
    active_combat = deepcopy(world_state.active_combat) if world_state.active_combat else {}
    active_combat["duration_tracker"] = duration_tracker.to_dict()
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=active_combat,
    )

    return events, world_state


@dataclass
class TurnContext:
    """Context for a single turn execution."""

    turn_index: int
    """0-indexed turn counter"""

    actor_id: str
    """Entity taking this turn"""

    actor_team: str
    """Team identifier (monsters/party)"""

    action_type: Optional[Literal["move", "standard", "move_and_standard", "full"]] = None
    """CP-14: Action economy type for this turn (None = no validation)"""


@dataclass
class TurnResult:
    """Result of executing a single turn."""

    status: str
    """Status: "ok" | "invalid_intent" | "requires_clarification" """

    world_state: WorldState
    """Updated world state after turn"""

    events: List[Event]
    """Events emitted during turn"""

    turn_index: int
    """Turn index that was executed"""

    failure_reason: Optional[str] = None
    """Reason for failure if status != "ok" """

    narration: Optional[str] = None
    """Narration token: "attack_hit", "attack_miss", "full_attack_complete", etc."""

    round_index: Optional[int] = None
    """CP-14: 1-indexed round number (None if not in combat round)"""

    action_type: Optional[str] = None
    """CP-14: Action type that was taken (None if not validated)"""

    narration_text: Optional[str] = None
    """WO-030: Generated narration text from GuardedNarrationService"""

    narration_provenance: Optional[str] = None
    """WO-030: Narration source tag — "[NARRATIVE]" for LLM, "[NARRATIVE:TEMPLATE]" for template"""


# ---------------------------------------------------------------------------
# WO-ENGINE-LEVELUP-WIRE: XP helpers
# ---------------------------------------------------------------------------

def _calculate_xp(defeated_cr: float, party_size: int) -> int:
    """Simple CR-to-XP lookup per PHB Table 3-1 / DMG Table 2-6.

    Uses the pre-existing calculate_xp_award() with a fixed party_level of 1
    as the reference point, then scales by CR. For a full implementation we
    would pass party avg level — using CR directly as the xp-per-creature
    column (300 × CR, min 50, split by party_size) matches PHB baseline.
    """
    from aidm.core.experience_resolver import calculate_xp_award
    # Use CR as a proxy for party level to get the on-level XP value
    cr_int = max(1, int(round(defeated_cr)))
    base_per_creature = calculate_xp_award(cr_int, 4, defeated_cr)  # 4-person reference
    if base_per_creature <= 0:
        # Fallback: PHB flat values — 300 XP per CR, split equally
        base_per_creature = max(50, int(300 * max(0.5, defeated_cr)))
    # Re-scale for actual party size
    if party_size <= 0:
        party_size = 1
    return max(1, int(base_per_creature * 4 / party_size))


def _best_class_to_level(entity: Dict[str, Any]) -> str:
    """Return the class to advance when leveling up.

    PHB p.60 simplified rule:
    - Use EF.FAVORED_CLASS if present and valid.
    - Otherwise use the class with the most existing levels (max-class rule).
    - Tie: lexicographic order (deterministic).
    """
    class_levels: Dict[str, int] = entity.get(EF.CLASS_LEVELS, {})
    if not class_levels:
        return "fighter"  # fallback for entities with no class data
    favored = entity.get("favored_class")
    if favored and favored in class_levels:
        return favored
    return max(sorted(class_levels.keys()), key=lambda c: class_levels[c])


def _award_xp_for_defeat(
    world_state: "WorldState",
    defeated_entity_id: str,
    events: List[Event],
    current_event_id: int,
    timestamp: float,
    rng: Optional["RNGProvider"],
) -> Tuple["WorldState", int]:
    """Award XP to the surviving opposing team and check for level-ups.

    Called by execute_turn() immediately after an entity_defeated event is
    added to the event list.

    Returns:
        (updated WorldState, updated current_event_id)
    """
    defeated = world_state.entities.get(defeated_entity_id, {})
    defeated_team = defeated.get(EF.TEAM, "")
    defeated_cr = defeated.get("challenge_rating", 1)

    # Surviving opposing party members
    survivors = [
        (eid, e) for eid, e in world_state.entities.items()
        if e.get(EF.TEAM) != defeated_team
        and not e.get(EF.DEFEATED, False)
        and eid != defeated_entity_id
    ]
    if not survivors:
        return world_state, current_event_id

    xp_per_entity = _calculate_xp(defeated_cr, len(survivors))
    entities = deepcopy(world_state.entities)

    for eid, _entity in survivors:
        updated_entity = award_xp(entities[eid], xp_per_entity)
        entities[eid] = updated_entity

        events.append(Event(
            event_id=current_event_id,
            event_type="xp_awarded",
            timestamp=timestamp + 0.3,
            payload={
                "entity_id": eid,
                "xp_amount": xp_per_entity,
                "source": f"defeat:{defeated_entity_id}",
                "new_total": updated_entity.get(EF.XP, 0),
            },
        ))
        current_event_id += 1

        # Check if XP award triggers a level-up
        level_result = check_level_up(updated_entity)
        if level_result is not None:
            # apply_level_up needs RNG for hit-die roll; use a stub if not available
            if rng is None:
                from aidm.core.rng_manager import RNGManager
                _stub_rng: RNGProvider = RNGManager(42)
            else:
                _stub_rng = rng
            leveled_entity, apply_result = apply_level_up(
                updated_entity, _best_class_to_level(updated_entity), _stub_rng
            )
            entities[eid] = leveled_entity
            events.append(Event(
                event_id=current_event_id,
                event_type="level_up_applied",
                timestamp=timestamp + 0.31,
                payload={
                    "entity_id": eid,
                    "old_level": level_result.new_level - 1,
                    "new_level": apply_result.new_level,
                    "hp_gained": apply_result.hp_gained,
                    "class_leveled": apply_result.class_name,
                    "new_bab": entities[eid].get(EF.BAB, 0),
                },
            ))
            current_event_id += 1

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
    )
    return updated_state, current_event_id


def execute_turn(
    world_state: WorldState,
    turn_ctx: TurnContext,
    doctrine: Optional[MonsterDoctrine] = None,
    combat_intent: Optional[Union[AttackIntent, FullAttackIntent]] = None,
    rng: Optional[RNGProvider] = None,
    next_event_id: int = 0,
    timestamp: float = 0.0,
    narration_service: Optional[Any] = None,  # WO-030: GuardedNarrationService
) -> TurnResult:
    """
    Execute a single turn in the play loop.

    CP-12 INTEGRATION:
    - Accepts optional combat_intent (AttackIntent or FullAttackIntent)
    - Routes combat intents to CP-10/CP-11 resolvers
    - Validates intent (actor match, target exists, target not defeated)
    - Returns status + narration token

    WO-030 INTEGRATION:
    - Accepts optional narration_service (GuardedNarrationService)
    - Generates narration text from narration token
    - Populates narration_text and narration_provenance in TurnResult

    BACKWARD COMPATIBILITY:
    - If combat_intent is None, uses policy-based resolution (CP-09 behavior)
    - If narration_service is None, skips narration generation
    - Monsters continue using policy stubs (combat deferred to CP-13)
    - PCs emit stub actions if no combat intent provided

    Args:
        world_state: Current world state
        turn_ctx: Turn context (actor, team, turn index)
        doctrine: Monster doctrine (if actor is monster), None for PCs
        combat_intent: Optional combat intent (AttackIntent or FullAttackIntent)
        rng: Optional RNG manager (required if combat_intent provided)
        next_event_id: Next available event ID
        timestamp: Event timestamp
        narration_service: Optional GuardedNarrationService for narration generation (WO-030)

    Returns:
        TurnResult with status, updated state, events, narration token, and optional narration text
    """
    events = []
    current_event_id = next_event_id
    narration = None

    # Emit turn_start event
    events.append(Event(
        event_id=current_event_id,
        event_type="turn_start",
        timestamp=timestamp,
        payload={
            "turn_index": turn_ctx.turn_index,
            "actor_id": turn_ctx.actor_id,
            "actor_team": turn_ctx.actor_team
        }
    ))
    current_event_id += 1

    # WO-ENGINE-CHARGE-001: Clear charge AC penalty at start of actor's turn.
    # The -2 AC from a charge (PHB p.150) expires at the start of the charger's
    # next turn. Clearing here (after turn_start, before any action processing)
    # ensures the penalty applies for the full intervening round.
    _actor_entity = world_state.entities.get(turn_ctx.actor_id, {})
    _temp_mods = _actor_entity.get(EF.TEMPORARY_MODIFIERS, {})
    if "charge_ac" in _temp_mods:
        _entities_cleared = deepcopy(world_state.entities)
        _cleared_mods = dict(_entities_cleared[turn_ctx.actor_id].get(EF.TEMPORARY_MODIFIERS, {}))
        del _cleared_mods["charge_ac"]
        _entities_cleared[turn_ctx.actor_id][EF.TEMPORARY_MODIFIERS] = _cleared_mods
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=_entities_cleared,
            active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
        )
        events.append(Event(
            event_id=current_event_id,
            event_type="charge_ac_expired",
            timestamp=timestamp + 0.01,
            payload={"entity_id": turn_ctx.actor_id},
            citations=[{"source_id": "681f92bc94ff", "page": 150}],
        ))
        current_event_id += 1

    # WO-ENGINE-READIED-ACTION-001: expire readied actions for this actor
    from aidm.core.readied_action_resolver import expire_readied_actions as _expire_readied
    world_state, _readied_expire_events, current_event_id = _expire_readied(
        world_state, turn_ctx.actor_id, current_event_id, timestamp + 0.011
    )
    events.extend(_readied_expire_events)

    # WO-ENGINE-FEINT-001: expire feint markers set by this actor
    from aidm.core.feint_resolver import expire_feint_markers as _expire_feint
    world_state, _feint_expire_events, current_event_id = _expire_feint(
        world_state, turn_ctx.actor_id, current_event_id, timestamp + 0.012
    )
    events.extend(_feint_expire_events)

    # WO-ENGINE-AID-ANOTHER-001: expire unconsumed Aid Another bonuses from this actor
    from aidm.core.aid_another_resolver import expire_aid_another_bonuses as _expire_aid
    world_state, _aid_expire_events = _expire_aid(
        world_state, turn_ctx.actor_id, timestamp + 0.013, current_event_id
    )
    events.extend(_aid_expire_events)
    current_event_id += len(_aid_expire_events)

    # WO-ENGINE-DEFEND-001: clear fight_defensively / total_defense temp modifiers
    _defend_keys = ("fight_defensively_attack", "fight_defensively_ac", "total_defense_ac")
    _actor_entity = world_state.entities.get(turn_ctx.actor_id, {})
    _temp_mods = _actor_entity.get(EF.TEMPORARY_MODIFIERS, {}) or {}
    _defend_active = {k: _temp_mods[k] for k in _defend_keys if k in _temp_mods}
    if _defend_active:
        _entities_def = deepcopy(world_state.entities)
        _def_mods = dict(_entities_def[turn_ctx.actor_id].get(EF.TEMPORARY_MODIFIERS, {}))
        for k in _defend_keys:
            _def_mods.pop(k, None)
        _entities_def[turn_ctx.actor_id][EF.TEMPORARY_MODIFIERS] = _def_mods
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=_entities_def,
            active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
        )
        if "fight_defensively_ac" in _defend_active:
            events.append(Event(
                event_id=current_event_id,
                event_type="fight_defensively_expired",
                timestamp=timestamp + 0.014,
                payload={"entity_id": turn_ctx.actor_id},
                citations=[{"source_id": "681f92bc94ff", "page": 142}],
            ))
            current_event_id += 1
        if "total_defense_ac" in _defend_active:
            events.append(Event(
                event_id=current_event_id,
                event_type="total_defense_expired",
                timestamp=timestamp + 0.015,
                payload={"entity_id": turn_ctx.actor_id},
                citations=[{"source_id": "681f92bc94ff", "page": 142}],
            ))
            current_event_id += 1

    # WO-ENGINE-COMBAT-EXPERTISE-001: Clear CE dodge AC bonus at start of actor's turn (PHB p.92).
    # CE bonus granted by intent.combat_expertise_penalty expires at the start of the
    # attacker's next turn (same duration as fight_defensively).
    _actor_entity = world_state.entities.get(turn_ctx.actor_id, {})
    if _actor_entity.get(EF.COMBAT_EXPERTISE_BONUS, 0) != 0:
        _entities_ce = deepcopy(world_state.entities)
        _entities_ce[turn_ctx.actor_id][EF.COMBAT_EXPERTISE_BONUS] = 0
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=_entities_ce,
            active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
        )

    # WO-WAYPOINT-002: actions_prohibited gate check
    # If the actor has a condition that sets actions_prohibited=True,
    # reject any action intent deterministically. The engine says no.

    # WO-ENGINE-CLEAVE-WIRE-001: clear cleave_used_this_turn at start of each turn (PHB p.92)
    if world_state.active_combat is not None and "cleave_used_this_turn" in world_state.active_combat:
        _cl_combat = deepcopy(world_state.active_combat)
        _cl_combat["cleave_used_this_turn"] = set()
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=deepcopy(world_state.entities),
            active_combat=_cl_combat,
        )

    condition_mods = get_condition_modifiers(world_state, turn_ctx.actor_id)
    if condition_mods.actions_prohibited:
        # Identify which conditions caused the prohibition
        actor_entity = world_state.entities.get(turn_ctx.actor_id, {})
        actor_conditions = actor_entity.get(EF.CONDITIONS, {})
        prohibiting_conditions = []
        if isinstance(actor_conditions, dict):
            for cond_id, cond_dict in actor_conditions.items():
                if isinstance(cond_dict, dict):
                    mods = cond_dict.get("modifiers", {})
                    if isinstance(mods, dict) and mods.get("actions_prohibited", False):
                        prohibiting_conditions.append(cond_id)

        # Determine denied intent type
        denied_intent_type = type(combat_intent).__name__ if combat_intent is not None else "none"

        # Emit action_denied event
        events.append(Event(
            event_id=current_event_id,
            event_type="action_denied",
            timestamp=timestamp + 0.05,
            payload={
                "entity_id": turn_ctx.actor_id,
                "reason": "actions_prohibited",
                "denied_intent_type": denied_intent_type,
                "conditions": prohibiting_conditions,
                "turn_index": turn_ctx.turn_index,
            }
        ))
        current_event_id += 1

        # Emit turn_end event
        events.append(Event(
            event_id=current_event_id,
            event_type="turn_end",
            timestamp=timestamp + 0.2,
            payload={
                "turn_index": turn_ctx.turn_index,
                "actor_id": turn_ctx.actor_id,
                "events_emitted": len(events)
            }
        ))

        return TurnResult(
            status="action_denied",
            world_state=world_state,
            events=events,
            turn_index=turn_ctx.turn_index,
            failure_reason=f"Actor {turn_ctx.actor_id} cannot act: actions_prohibited ({', '.join(prohibiting_conditions)})"
        )

    # CP-12/CP-15/CP-18: Combat intent validation and routing
    # CP-24: Action economy enforcement — check budget before routing
    if combat_intent is not None:
        action_type = get_action_type(combat_intent)
        # CP-24: Load persistent budget from active_combat for cross-call tracking.
        # Budget is stored in active_combat["action_budget"] keyed by actor.
        # A fresh budget is initialized whenever the acting entity changes.
        if world_state.active_combat is not None:
            _budget_actor = world_state.active_combat.get("action_budget_actor")
            _budget_raw = world_state.active_combat.get("action_budget")
            if _budget_actor == turn_ctx.actor_id and isinstance(_budget_raw, dict):
                _action_budget = ActionBudget.from_dict(_budget_raw)
            else:
                _action_budget = ActionBudget.fresh()
        else:
            _action_budget = ActionBudget.fresh()

        if not _action_budget.can_use(action_type):
            # Budget exhausted for this action type
            events.append(Event(
                event_id=current_event_id,
                event_type="ACTION_DENIED",
                timestamp=timestamp + 0.05,
                payload={
                    "entity_id": turn_ctx.actor_id,
                    "reason": "action_economy",
                    "slot": action_type,
                    "denied_intent_type": type(combat_intent).__name__,
                    "turn_index": turn_ctx.turn_index,
                }
            ))
            current_event_id += 1
            events.append(Event(
                event_id=current_event_id,
                event_type="turn_end",
                timestamp=timestamp + 0.2,
                payload={
                    "turn_index": turn_ctx.turn_index,
                    "actor_id": turn_ctx.actor_id,
                    "events_emitted": len(events)
                }
            ))
            return TurnResult(
                status="action_denied",
                world_state=world_state,
                events=events,
                turn_index=turn_ctx.turn_index,
                failure_reason=f"Action economy: {action_type} slot already used this turn"
            )
        _action_budget.consume(action_type)
        # Persist updated budget into active_combat for subsequent calls this turn
        if world_state.active_combat is not None:
            _ac_updated = deepcopy(world_state.active_combat)
            _ac_updated["action_budget"] = _action_budget.to_dict()
            _ac_updated["action_budget_actor"] = turn_ctx.actor_id
            world_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=world_state.entities,
                active_combat=_ac_updated,
            )

    if combat_intent is not None:
        # Determine intent actor based on intent type
        intent_actor_id = None
        if isinstance(combat_intent, (AttackIntent, FullAttackIntent, CoupDeGraceIntent,
                                      NaturalAttackIntent)):
            intent_actor_id = combat_intent.attacker_id
        elif isinstance(combat_intent, StepMoveIntent):
            intent_actor_id = combat_intent.actor_id
        # CP-16: Full multi-square movement
        elif isinstance(combat_intent, FullMoveIntent):
            intent_actor_id = combat_intent.actor_id
        # CP-18A: Mounted combat intents
        elif isinstance(combat_intent, MountedMoveIntent):
            intent_actor_id = combat_intent.rider_id
        elif isinstance(combat_intent, DismountIntent):
            intent_actor_id = combat_intent.rider_id
        elif isinstance(combat_intent, MountIntent):
            intent_actor_id = combat_intent.rider_id
        # CP-18: Combat maneuver intents
        elif isinstance(combat_intent, (BullRushIntent, TripIntent, OverrunIntent,
                                        SunderIntent, DisarmIntent, GrappleIntent,
                                        GrappleEscapeIntent)):
            intent_actor_id = combat_intent.attacker_id
        # WO-ENGINE-GRAPPLE-PIN-001: Pin escape intent
        elif isinstance(combat_intent, PinEscapeIntent):
            intent_actor_id = combat_intent.attacker_id
        # WO-015: Spellcasting intents
        elif isinstance(combat_intent, SpellCastIntent):
            intent_actor_id = combat_intent.caster_id
        # WO-ENGINE-COMPANION-WIRE: Companion summon intent
        elif isinstance(combat_intent, SummonCompanionIntent):
            intent_actor_id = turn_ctx.actor_id  # actor declares the summon
        # WO-ENGINE-REST-001: Rest intent
        elif isinstance(combat_intent, RestIntent):
            intent_actor_id = turn_ctx.actor_id
        # WO-ENGINE-SPELL-PREP-001: Spell preparation intent
        elif isinstance(combat_intent, PrepareSpellsIntent):
            intent_actor_id = turn_ctx.actor_id
        # WO-ENGINE-CHARGE-001: Charge intent
        elif isinstance(combat_intent, ChargeIntent):
            intent_actor_id = combat_intent.attacker_id
        elif isinstance(combat_intent, (ReadyActionIntent, AidAnotherIntent,
                                        FightDefensivelyIntent, TotalDefenseIntent,
                                        FeintIntent, RageIntent, SmiteEvilIntent, LayOnHandsIntent,
                                        BardicMusicIntent, WildShapeIntent, RevertFormIntent,
                                        AbilityDamageIntent, WithdrawIntent, DelayIntent,
                                        StabilizeIntent, CalledShotIntent, DemoralizeIntent)):
            intent_actor_id = combat_intent.actor_id
        else:
            # Unknown intent type
            raise ValueError(f"Unknown combat intent type: {type(combat_intent)}")

        # Validate: actor must match turn actor
        if intent_actor_id != turn_ctx.actor_id:
            # Emit validation failure event
            events.append(Event(
                event_id=current_event_id,
                event_type="intent_validation_failed",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": turn_ctx.actor_id,
                    "intent_actor": intent_actor_id,
                    "reason": "intent_actor_mismatch",
                    "turn_index": turn_ctx.turn_index
                }
            ))
            current_event_id += 1

            # Emit turn_end
            events.append(Event(
                event_id=current_event_id,
                event_type="turn_end",
                timestamp=timestamp + 0.2,
                payload={
                    "turn_index": turn_ctx.turn_index,
                    "actor_id": turn_ctx.actor_id,
                    "events_emitted": len(events)
                }
            ))

            # Return unchanged state with failure status
            return TurnResult(
                status="invalid_intent",
                world_state=world_state,
                events=events,
                turn_index=turn_ctx.turn_index,
                failure_reason="Combat intent actor does not match turn actor"
            )

        # Validate: target must exist in world state (for attack intents and maneuvers)
        if isinstance(combat_intent, (AttackIntent, FullAttackIntent, CoupDeGraceIntent)):
            if combat_intent.target_id not in world_state.entities:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_not_found",
                        "turn_index": turn_ctx.turn_index
                    }
                ))
                current_event_id += 1

                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events)
                    }
                ))

                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Target {combat_intent.target_id} not found in world state"
                )

            # Validate: target must not be defeated
            target = world_state.entities[combat_intent.target_id]
            if target.get(EF.DEFEATED, False):
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_already_defeated",
                        "turn_index": turn_ctx.turn_index
                    }
                ))
                current_event_id += 1

                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events)
                    }
                ))

                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Target {combat_intent.target_id} is already defeated"
                )

        # WO-ENGINE-COUP-DE-GRACE-001: Validate CDG target is helpless/dying
        if isinstance(combat_intent, CoupDeGraceIntent):
            _cdg_target = world_state.entities[combat_intent.target_id]
            _cdg_conditions = _cdg_target.get(EF.CONDITIONS, {})
            _helpless_conditions = {"helpless", "unconscious", "pinned", "paralyzed"}
            _target_is_dying = _cdg_target.get(EF.DYING, False)
            _target_is_helpless = bool(_helpless_conditions & set(_cdg_conditions.keys()))

            if not (_target_is_dying or _target_is_helpless):
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_not_helpless",
                        "turn_index": turn_ctx.turn_index,
                        "target_dying": _target_is_dying,
                        "target_conditions": list(_cdg_conditions.keys()),
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 153}]
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events),
                    }
                ))
                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Coup de grâce target {combat_intent.target_id} is not helpless or dying"
                )

            # Validate: crit immunity check
            if _cdg_target.get(EF.CRIT_IMMUNE, False):
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_crit_immune",
                        "turn_index": turn_ctx.turn_index,
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 153}]
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events),
                    }
                ))
                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Coup de grâce invalid: target {combat_intent.target_id} is immune to critical hits"
                )

        # CP-18: Validate target for maneuver intents
        if isinstance(combat_intent, (BullRushIntent, TripIntent, OverrunIntent,
                                      SunderIntent, DisarmIntent, GrappleIntent)):
            if combat_intent.target_id not in world_state.entities:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_not_found",
                        "turn_index": turn_ctx.turn_index
                    }
                ))
                current_event_id += 1

                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events)
                    }
                ))

                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Target {combat_intent.target_id} not found in world state"
                )

            # Validate: target must not be defeated
            target = world_state.entities[combat_intent.target_id]
            if target.get(EF.DEFEATED, False):
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_already_defeated",
                        "turn_index": turn_ctx.turn_index
                    }
                ))
                current_event_id += 1

                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events)
                    }
                ))

                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Target {combat_intent.target_id} is already defeated"
                )

        # Validate: RNG must be provided for combat intents
        # SummonCompanionIntent, RestIntent, and PrepareSpellsIntent are exempt — they use no RNG.
        if rng is None and not isinstance(combat_intent, (SummonCompanionIntent, RestIntent, PrepareSpellsIntent, CalledShotIntent)):
            raise ValueError("RNG manager required for combat intent resolution")

        # WO-BRIEF-WIDTH-001: Generate causal_chain_id for maneuver intents
        # Maneuvers can trigger causal chains (e.g., bull rush → AoO → trip)
        causal_chain_id = None
        if isinstance(combat_intent, (BullRushIntent, TripIntent, OverrunIntent,
                                      SunderIntent, DisarmIntent, GrappleIntent)):
            causal_chain_id = f"{type(combat_intent).__name__}_{turn_ctx.turn_index}_{uuid.uuid4().hex[:8]}"

        # WO-ENGINE-READIED-ACTION-001: Check if this intent fires any readied actions
        from aidm.core.readied_action_resolver import check_readied_triggers as _check_readied
        _intent_type_name = type(combat_intent).__name__
        _intent_payload = combat_intent.to_dict() if hasattr(combat_intent, "to_dict") else {}
        world_state, _readied_trigger_events, current_event_id = _check_readied(
            world_state,
            current_actor_id=turn_ctx.actor_id,
            trigger_event_type=_intent_type_name,
            event_payload=_intent_payload,
            rng=rng,
            current_event_id=current_event_id,
            timestamp=timestamp + 0.08,
        )
        events.extend(_readied_trigger_events)

        # CP-15: Check for AoO triggers before resolving main action
        aoo_triggers = check_aoo_triggers(world_state, turn_ctx.actor_id, combat_intent)

        # WO-ENGINE-DEFENSIVE-CASTING-001: Defensive casting bypass (PHB p.140)
        # If the intent is a SpellCastIntent with defensive=True, run Concentration check.
        # DC = 15 + spell level. Success: suppress AoO triggers for this cast.
        # Failure: AoO proceeds; concentration_failed event emitted.
        # Failure by 5+: spell also disrupted (spell_disrupted event, slot consumed). KERNEL-03.
        _defensive_cast_disrupted = False
        if (aoo_triggers
                and isinstance(combat_intent, SpellCastIntent)
                and getattr(combat_intent, "defensive", False)):
            _dc_spell = SPELL_REGISTRY.get(combat_intent.spell_id)
            _dc_spell_level = _dc_spell.level if _dc_spell else 0
            _dc_dc = 15 + _dc_spell_level
            _dc_caster_entity = world_state.entities.get(combat_intent.caster_id, {})
            _dc_conc_bonus = _dc_caster_entity.get(EF.CONCENTRATION_BONUS, 0)
            _dc_roll = rng.stream("combat").randint(1, 20)
            _dc_total = _dc_roll + _dc_conc_bonus
            if _dc_total >= _dc_dc:
                # Concentration success: suppress AoO
                aoo_triggers = []
                events.append(Event(
                    event_id=current_event_id,
                    event_type="concentration_success",
                    timestamp=timestamp + 0.05,
                    payload={
                        "actor_id": combat_intent.caster_id,
                        "spell_id": combat_intent.spell_id,
                        "roll": _dc_total,
                        "dc": _dc_dc,
                    },
                    citations=["PHB p.140"],
                ))
                current_event_id += 1
            else:
                # Concentration failure: AoO proceeds
                _dc_margin = _dc_dc - _dc_total  # how much it missed by
                events.append(Event(
                    event_id=current_event_id,
                    event_type="concentration_failed",
                    timestamp=timestamp + 0.05,
                    payload={
                        "actor_id": combat_intent.caster_id,
                        "spell_id": combat_intent.spell_id,
                        "roll": _dc_total,
                        "dc": _dc_dc,
                        "margin": _dc_margin,
                        "spell_disrupted": _dc_margin >= 5,
                    },
                    citations=["PHB p.140"],
                ))
                current_event_id += 1
                if _dc_margin >= 5:
                    # Failed by 5+: spell lost (slot consumed later in resolution)
                    _defensive_cast_disrupted = True

        if aoo_triggers:
            # Resolve AoO sequence
            aoo_result = resolve_aoo_sequence(
                triggers=aoo_triggers,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
                causal_chain_id=causal_chain_id,
            )

            # Emit AoO events
            events.extend(aoo_result.events)
            current_event_id += len(aoo_result.events)

            # Update world state with AoO results
            # Mark reactors as having used their AoO this round
            if world_state.active_combat is not None:
                aoo_used = list(world_state.active_combat.get("aoo_used_this_round", []))
                aoo_used.extend(aoo_result.aoo_reactors)
                active_combat_updated = deepcopy(world_state.active_combat)
                active_combat_updated["aoo_used_this_round"] = aoo_used
                # WO-ENGINE-COMBAT-REFLEXES-001: Mirror update to count tracker
                aoo_count = dict(active_combat_updated.get("aoo_count_this_round", {}))
                for _rid in aoo_result.aoo_reactors:
                    aoo_count[_rid] = aoo_count.get(_rid, 0) + 1
                active_combat_updated["aoo_count_this_round"] = aoo_count
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=deepcopy(world_state.entities),
                    active_combat=active_combat_updated
                )

            # CP-23: If spell cast, check concentration after any AoO damage
            # PHB p.170: Concentration DC = 10 + damage from AoO hit
            _spell_interrupted = False
            if isinstance(combat_intent, SpellCastIntent) and not getattr(combat_intent, 'quickened', False):
                aoo_damage_total = sum(
                    abs(e.payload.get("delta", 0))
                    for e in aoo_result.events
                    if e.event_type == "hp_changed"
                    and e.payload.get("entity_id") == turn_ctx.actor_id
                    and e.payload.get("delta", 0) < 0
                )
                if aoo_damage_total > 0:
                    conc_dc = 10 + aoo_damage_total
                    conc_bonus = world_state.entities.get(turn_ctx.actor_id, {}).get("concentration_bonus", 0)
                    conc_roll = rng.stream("combat").randint(1, 20)
                    conc_total = conc_roll + conc_bonus
                    events.append(Event(
                        event_id=current_event_id,
                        event_type="concentration_check",
                        timestamp=timestamp + 0.15,
                        payload={
                            "caster_id": turn_ctx.actor_id,
                            "dc": conc_dc,
                            "roll": conc_roll,
                            "bonus": conc_bonus,
                            "total": conc_total,
                            "success": conc_total >= conc_dc,
                        },
                        citations=[{"source_id": "681f92bc94ff", "page": 170}],
                    ))
                    current_event_id += 1
                    if conc_total < conc_dc:
                        _spell_interrupted = True
                        events.append(Event(
                            event_id=current_event_id,
                            event_type="spell_interrupted",
                            timestamp=timestamp + 0.16,
                            payload={
                                "caster_id": turn_ctx.actor_id,
                                "reason": "concentration_check_failed",
                                "dc": conc_dc,
                                "total": conc_total,
                            },
                            citations=[{"source_id": "681f92bc94ff", "page": 170}],
                        ))
                        current_event_id += 1

            # If provoker was defeated by AoO, abort the main action
            if aoo_result.provoker_defeated or _spell_interrupted:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="action_aborted",
                    timestamp=timestamp + 0.2,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "reason": "defeated_by_aoo",
                        "turn_index": turn_ctx.turn_index
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 137}]  # PHB AoO
                ))
                current_event_id += 1

                # Emit turn_end
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.3,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events)
                    }
                ))

                # Return aborted turn result
                return TurnResult(
                    status="ok",  # Turn succeeded, but action was aborted
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    narration="action_aborted_by_aoo"
                )

        # Route to appropriate resolver
        if isinstance(combat_intent, AttackIntent):
            # CP-10: Single attack resolution
            combat_events = resolve_attack(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
            )
            events.extend(combat_events)
            current_event_id += len(combat_events)

            # Apply events to get updated state
            world_state = apply_attack_events(world_state, combat_events)

            # WO-015: Check concentration break if target took damage
            hp_events = [e for e in combat_events if e.event_type == "hp_changed"]
            for hp_event in hp_events:
                target_id = hp_event.payload.get("entity_id")
                damage = abs(hp_event.payload.get("delta", 0))
                if damage > 0 and target_id:
                    conc_events, world_state = _check_concentration_break(
                        caster_id=target_id,
                        damage_dealt=damage,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.15,
                    )
                    events.extend(conc_events)
                    current_event_id += len(conc_events)

            # Generate narration token
            attack_events = [e for e in combat_events if e.event_type == "attack_roll"]
            if attack_events and attack_events[0].payload["hit"]:
                narration = "attack_hit"
            else:
                narration = "attack_miss"

        elif isinstance(combat_intent, EnergyDrainAttackIntent):
            # WO-ENGINE-ENERGY-DRAIN-001: Energy drain natural attack
            from aidm.core.energy_drain_resolver import resolve_energy_drain, apply_energy_drain_events
            drain_events = resolve_energy_drain(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(drain_events)
            current_event_id += len(drain_events)
            world_state = apply_energy_drain_events(drain_events, world_state)

            # Concentration break check
            hp_events = [e for e in drain_events if e.event_type == "hp_changed"]
            for hp_event in hp_events:
                target_id = hp_event.payload.get("entity_id")
                damage = abs(hp_event.payload.get("delta", 0))
                if damage > 0 and target_id:
                    conc_events, world_state = _check_concentration_break(
                        caster_id=target_id,
                        damage_dealt=damage,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.15,
                    )
                    events.extend(conc_events)
                    current_event_id += len(conc_events)
            narration = "energy_drain_attack_resolved"

        elif isinstance(combat_intent, FullAttackIntent):
            # CP-11: Full attack resolution
            combat_events = resolve_full_attack(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
            )
            events.extend(combat_events)
            current_event_id += len(combat_events)

            # Apply events to get updated state
            world_state = apply_full_attack_events(world_state, combat_events)

            # WO-015: Check concentration break if target took damage
            hp_events = [e for e in combat_events if e.event_type == "hp_changed"]
            for hp_event in hp_events:
                target_id = hp_event.payload.get("entity_id")
                damage = abs(hp_event.payload.get("delta", 0))
                if damage > 0 and target_id:
                    conc_events, world_state = _check_concentration_break(
                        caster_id=target_id,
                        damage_dealt=damage,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.15,
                    )
                    events.extend(conc_events)
                    current_event_id += len(conc_events)

            # Generate narration token
            narration = "full_attack_complete"

        elif isinstance(combat_intent, CoupDeGraceIntent):
            # WO-ENGINE-COUP-DE-GRACE-001: Coup de grâce resolution
            # AoO has already been resolved above (CDG provokes per PHB p.153)
            from aidm.core.attack_resolver import resolve_coup_de_grace, apply_cdg_events
            combat_events = resolve_coup_de_grace(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
            )
            events.extend(combat_events)
            current_event_id += len(combat_events)

            # Apply events to get updated state
            world_state = apply_cdg_events(world_state, combat_events)

            # WO-015: Check concentration break if target took damage
            hp_events = [e for e in combat_events if e.event_type == "hp_changed"]
            for hp_event in hp_events:
                target_id = hp_event.payload.get("entity_id")
                damage = abs(hp_event.payload.get("delta", 0))
                if damage > 0 and target_id:
                    conc_events, world_state = _check_concentration_break(
                        caster_id=target_id,
                        damage_dealt=damage,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.15,
                    )
                    events.extend(conc_events)
                    current_event_id += len(conc_events)

            narration = "coup_de_grace_delivered"

        elif isinstance(combat_intent, TurnUndeadIntent):
            # WO-ENGINE-TURN-UNDEAD-001: Turn/destroy undead
            from aidm.core.turn_undead_resolver import resolve_turn_undead, apply_turn_undead_events
            turn_events = resolve_turn_undead(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(turn_events)
            current_event_id += len(turn_events)
            world_state = apply_turn_undead_events(turn_events, world_state)
            narration = "turn_undead_resolved"

        elif isinstance(combat_intent, ReadyActionIntent):
            # WO-ENGINE-READIED-ACTION-001: Register readied action
            from aidm.core.readied_action_resolver import register_readied_action as _reg_readied
            world_state = _reg_readied(world_state, combat_intent, current_event_id)
            events.append(Event(
                event_id=current_event_id,
                event_type="readied_action_registered",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": combat_intent.actor_id,
                    "trigger_type": combat_intent.trigger_type,
                    "trigger_target_id": combat_intent.trigger_target_id,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 160}],
            ))
            current_event_id += 1
            narration = "readied_action_registered"

        elif isinstance(combat_intent, AidAnotherIntent):
            # WO-ENGINE-AID-ANOTHER-001: Aid Another
            from aidm.core.aid_another_resolver import resolve_aid_another as _resolve_aid
            world_state, _aid_events, current_event_id = _resolve_aid(
                world_state, combat_intent, rng, current_event_id, timestamp + 0.1
            )
            events.extend(_aid_events)
            narration = "aid_another_resolved"

        elif isinstance(combat_intent, StabilizeIntent):
            # WO-ENGINE-STABILIZE-ALLY-001: PHB p.152 First Aid — DC 15 Heal check to stabilize dying ally
            from aidm.core.stabilize_resolver import resolve_stabilize as _resolve_stabilize
            _stab_events, world_state = _resolve_stabilize(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_stab_events)
            current_event_id += len(_stab_events)
            narration = "stabilize_resolved"

        elif isinstance(combat_intent, FightDefensivelyIntent):
            # WO-ENGINE-DEFEND-001: Fight defensively
            _fd_actor = world_state.entities.get(combat_intent.actor_id, {})
            _fd_feats = _fd_actor.get(EF.FEATS, [])
            _has_expertise = ("COMBAT_EXPERTISE" in _fd_feats or "Combat Expertise" in _fd_feats)
            _fd_attack_pen = -5 if _has_expertise else -4
            _fd_ac_bon = 5 if _has_expertise else 2
            _fd_mods = dict(_fd_actor.get(EF.TEMPORARY_MODIFIERS, {}) or {})
            _fd_mods["fight_defensively_attack"] = _fd_attack_pen
            _fd_mods["fight_defensively_ac"] = _fd_ac_bon
            _fd_entities = deepcopy(world_state.entities)
            _fd_entities[combat_intent.actor_id][EF.TEMPORARY_MODIFIERS] = _fd_mods
            world_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=_fd_entities,
                active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
            )
            events.append(Event(
                event_id=current_event_id,
                event_type="fight_defensively_applied",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": combat_intent.actor_id,
                    "attack_penalty": _fd_attack_pen,
                    "ac_bonus": _fd_ac_bon,
                    "combat_expertise": _has_expertise,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 142}],
            ))
            current_event_id += 1
            narration = "fight_defensively_applied"

        elif isinstance(combat_intent, TotalDefenseIntent):
            # WO-ENGINE-DEFEND-001: Total defense
            _td_actor = world_state.entities.get(combat_intent.actor_id, {})
            _td_mods = dict(_td_actor.get(EF.TEMPORARY_MODIFIERS, {}) or {})
            _td_mods["total_defense_ac"] = 4
            _td_entities = deepcopy(world_state.entities)
            _td_entities[combat_intent.actor_id][EF.TEMPORARY_MODIFIERS] = _td_mods
            world_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=_td_entities,
                active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
            )
            events.append(Event(
                event_id=current_event_id,
                event_type="total_defense_applied",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": combat_intent.actor_id,
                    "ac_bonus": 4,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 142}],
            ))
            current_event_id += 1
            narration = "total_defense_applied"

        elif isinstance(combat_intent, FeintIntent):
            # WO-ENGINE-FEINT-001: Feint
            from aidm.core.feint_resolver import resolve_feint as _resolve_feint
            world_state, _feint_events, current_event_id = _resolve_feint(
                world_state, combat_intent, rng, current_event_id, timestamp + 0.1
            )
            events.extend(_feint_events)
            narration = "feint_resolved"

        elif isinstance(combat_intent, AbilityDamageIntent):
            # WO-ENGINE-ABILITY-DAMAGE-001: Ability damage / drain
            from aidm.core.ability_damage_resolver import apply_ability_damage as _apply_ab_dmg
            _ab_target_id = combat_intent.target_id
            if _ab_target_id in world_state.entities:
                _ab_entity = deepcopy(world_state.entities[_ab_target_id])
                _ab_entity, _ab_events = _apply_ab_dmg(
                    _ab_entity,
                    ability=combat_intent.ability,
                    amount=combat_intent.amount,
                    is_drain=combat_intent.is_drain,
                    target_id=_ab_target_id,
                    source_id=combat_intent.source_id,
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.1,
                )
                entities_copy = deepcopy(world_state.entities)
                entities_copy[_ab_target_id] = _ab_entity
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=entities_copy,
                    active_combat=world_state.active_combat,
                )
                for _ev in _ab_events:
                    events.append(Event(
                        event_id=_ev["event_id"],
                        event_type=_ev["event_type"],
                        timestamp=_ev.get("timestamp", timestamp),
                        payload=_ev["payload"],
                        citations=_ev.get("citations", []),
                    ))
                current_event_id += len(_ab_events)
            narration = "ability_damage_applied"

        elif isinstance(combat_intent, WithdrawIntent):
            # WO-ENGINE-WITHDRAW-DELAY-001: Withdraw
            from aidm.core.withdraw_delay_resolver import resolve_withdraw as _resolve_withdraw
            world_state, _withdraw_events = _resolve_withdraw(
                combat_intent, world_state, current_event_id, timestamp + 0.1
            )
            for _ev in _withdraw_events:
                events.append(Event(
                    event_id=_ev["event_id"],
                    event_type=_ev["event_type"],
                    timestamp=_ev.get("timestamp", timestamp),
                    payload=_ev["payload"],
                    citations=_ev.get("citations", []),
                ))
            current_event_id += len(_withdraw_events)
            narration = "withdraw_declared"

        elif isinstance(combat_intent, DelayIntent):
            # WO-ENGINE-WITHDRAW-DELAY-001: Delay
            from aidm.core.withdraw_delay_resolver import resolve_delay as _resolve_delay
            world_state, _delay_events = _resolve_delay(
                combat_intent, world_state, current_event_id, timestamp + 0.1
            )
            for _ev in _delay_events:
                events.append(Event(
                    event_id=_ev["event_id"],
                    event_type=_ev["event_type"],
                    timestamp=_ev.get("timestamp", timestamp),
                    payload=_ev["payload"],
                    citations=_ev.get("citations", []),
                ))
            current_event_id += len(_delay_events)
            narration = "delay_declared"

        # WO-ENGINE-PLAY-LOOP-ROUTING-001: Barbarian Rage
        elif isinstance(combat_intent, RageIntent):
            from aidm.core.rage_resolver import activate_rage, validate_rage
            _rage_actor = world_state.entities.get(combat_intent.actor_id, {})
            _rage_err = validate_rage(_rage_actor, world_state)
            if _rage_err:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": combat_intent.actor_id,
                        "intent_type": "RageIntent",
                        "reason": _rage_err,
                        "turn_index": turn_ctx.turn_index,
                    },
                ))
                current_event_id += 1
            else:
                _rage_events, world_state = activate_rage(
                    actor_id=combat_intent.actor_id,
                    world_state=world_state,
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.1,
                )
                events.extend(_rage_events)
                current_event_id += len(_rage_events)
            narration = "rage_activated"

        # WO-ENGINE-PLAY-LOOP-ROUTING-001: Paladin Smite Evil
        elif isinstance(combat_intent, SmiteEvilIntent):
            from aidm.core.smite_evil_resolver import resolve_smite_evil
            _smite_events, world_state = resolve_smite_evil(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_smite_events)
            current_event_id += len(_smite_events)
            world_state = apply_attack_events(world_state, _smite_events)
            narration = "smite_evil_resolved"

        # WO-ENGINE-LAY-ON-HANDS-001: Paladin Lay on Hands
        elif isinstance(combat_intent, LayOnHandsIntent):
            from aidm.core.lay_on_hands_resolver import resolve_lay_on_hands
            _loh_events, world_state = resolve_lay_on_hands(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_loh_events)
            current_event_id += len(_loh_events)
            narration = "lay_on_hands_resolved"

        # WO-ENGINE-PLAY-LOOP-ROUTING-001: Bardic Music (Inspire Courage)
        elif isinstance(combat_intent, BardicMusicIntent):
            from aidm.core.bardic_music_resolver import resolve_bardic_music
            _bardic_events, world_state = resolve_bardic_music(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_bardic_events)
            current_event_id += len(_bardic_events)
            narration = "bardic_music_resolved"

        # WO-ENGINE-PLAY-LOOP-ROUTING-001: Druid Wild Shape
        elif isinstance(combat_intent, WildShapeIntent):
            from aidm.core.wild_shape_resolver import resolve_wild_shape
            _ws_events, world_state = resolve_wild_shape(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_ws_events)
            current_event_id += len(_ws_events)
            narration = "wild_shape_resolved"

        # WO-ENGINE-PLAY-LOOP-ROUTING-001: Revert from Wild Shape
        elif isinstance(combat_intent, RevertFormIntent):
            from aidm.core.wild_shape_resolver import resolve_revert_form
            _revert_events, world_state = resolve_revert_form(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_revert_events)
            current_event_id += len(_revert_events)
            narration = "revert_form_resolved"

        elif isinstance(combat_intent, StepMoveIntent):
            # CP-22: Block 5-foot step if actor is grappling or grappled
            actor_conds = world_state.entities.get(turn_ctx.actor_id, {}).get(EF.CONDITIONS, {})
            if "grappling" in actor_conds or "grappled" in actor_conds:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="action_denied",
                    timestamp=timestamp + 0.05,
                    payload={
                        "entity_id": turn_ctx.actor_id,
                        "reason": "grappling_no_step",
                        "denied_intent_type": "StepMoveIntent",
                        "conditions": [k for k in ["grappling", "grappled"] if k in actor_conds],
                        "turn_index": turn_ctx.turn_index,
                    }
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={"turn_index": turn_ctx.turn_index, "actor_id": turn_ctx.actor_id, "events_emitted": len(events)}
                ))
                return TurnResult(
                    status="action_denied",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Actor {turn_ctx.actor_id} cannot 5-foot step while grappling/grappled"
                )

            # CP-15/CP-16: Movement resolution
            # AoOs have already been resolved above; now resolve movement
            events.append(Event(
                event_id=current_event_id,
                event_type="movement_declared",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": combat_intent.actor_id,
                    "from_pos": {"x": combat_intent.from_pos.x, "y": combat_intent.from_pos.y},
                    "to_pos": {"x": combat_intent.to_pos.x, "y": combat_intent.to_pos.y},
                }
            ))
            current_event_id += 1

            # Update entity position in world state
            entities = deepcopy(world_state.entities)
            if combat_intent.actor_id in entities:
                entities[combat_intent.actor_id][EF.POSITION] = {
                    "x": combat_intent.to_pos.x,
                    "y": combat_intent.to_pos.y
                }
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=entities,
                    active_combat=world_state.active_combat
                )

            narration = "movement_complete"

        # CP-16: Full multi-square movement intent
        elif isinstance(combat_intent, FullMoveIntent):
            # Process movement step-by-step for AoO resolution at each departure
            prev_pos = combat_intent.from_pos
            actor_defeated = False

            for step_pos in combat_intent.path:
                # Check AoO at each departure square
                step_intent = StepMoveIntent(
                    actor_id=combat_intent.actor_id,
                    from_pos=prev_pos,
                    to_pos=step_pos,
                )
                step_aoo_triggers = check_aoo_triggers(world_state, combat_intent.actor_id, step_intent)

                if step_aoo_triggers:
                    aoo_result = resolve_aoo_sequence(
                        triggers=step_aoo_triggers,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.05,
                    )
                    events.extend(aoo_result.events)
                    current_event_id += len(aoo_result.events)

                    # Update AoO tracking
                    if world_state.active_combat is not None:
                        aoo_used = list(world_state.active_combat.get("aoo_used_this_round", []))
                        aoo_used.extend(aoo_result.aoo_reactors)
                        active_combat_updated = deepcopy(world_state.active_combat)
                        active_combat_updated["aoo_used_this_round"] = aoo_used
                        # WO-ENGINE-COMBAT-REFLEXES-001: Mirror update to count tracker
                        aoo_count = dict(active_combat_updated.get("aoo_count_this_round", {}))
                        for _rid in aoo_result.aoo_reactors:
                            aoo_count[_rid] = aoo_count.get(_rid, 0) + 1
                        active_combat_updated["aoo_count_this_round"] = aoo_count
                        world_state = WorldState(
                            ruleset_version=world_state.ruleset_version,
                            entities=deepcopy(world_state.entities),
                            active_combat=active_combat_updated,
                        )

                    # If mover defeated by AoO, abort movement
                    if aoo_result.provoker_defeated:
                        actor_defeated = True
                        events.append(Event(
                            event_id=current_event_id,
                            event_type="action_aborted",
                            timestamp=timestamp + 0.2,
                            payload={
                                "actor_id": combat_intent.actor_id,
                                "reason": "defeated_by_aoo_during_movement",
                                "stopped_at": prev_pos.to_dict(),
                                "turn_index": turn_ctx.turn_index,
                            },
                        ))
                        current_event_id += 1
                        break

                # Move to this square
                entities = deepcopy(world_state.entities)
                if combat_intent.actor_id in entities:
                    entities[combat_intent.actor_id][EF.POSITION] = step_pos.to_dict()
                    world_state = WorldState(
                        ruleset_version=world_state.ruleset_version,
                        entities=entities,
                        active_combat=world_state.active_combat,
                    )
                prev_pos = step_pos

            # Emit single movement event for the full path
            if not actor_defeated:
                path_dicts = [p.to_dict() for p in combat_intent.path]
                events.append(Event(
                    event_id=current_event_id,
                    event_type="movement_declared",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": combat_intent.actor_id,
                        "from_pos": combat_intent.from_pos.to_dict(),
                        "to_pos": combat_intent.to_pos.to_dict(),
                        "path": path_dicts,
                        "distance_ft": combat_intent.path_cost_ft(),
                    },
                ))
                current_event_id += 1

            if actor_defeated:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.3,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events),
                    },
                ))
                return TurnResult(
                    status="ok",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    narration="movement_aborted",
                )

            narration = "movement_complete"
        elif isinstance(combat_intent, MountedMoveIntent):
            # AoOs have already been resolved above (against mount)
            # Emit mounted movement event
            events.append(Event(
                event_id=current_event_id,
                event_type="mounted_move_declared",
                timestamp=timestamp + 0.1,
                payload={
                    "rider_id": combat_intent.rider_id,
                    "mount_id": combat_intent.mount_id,
                    "from_pos": combat_intent.from_pos.to_dict(),
                    "to_pos": combat_intent.to_pos.to_dict(),
                    "is_charge": combat_intent.is_charge,
                    "is_run": combat_intent.is_run,
                    "is_double_move": combat_intent.is_double_move
                },
                citations=[{"source_id": "681f92bc94ff", "page": 157}]
            ))
            current_event_id += 1

            # Update mount position in world state
            entities = deepcopy(world_state.entities)
            mount_id = combat_intent.mount_id
            if mount_id in entities:
                entities[mount_id][EF.POSITION] = combat_intent.to_pos.to_dict()
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=entities,
                    active_combat=world_state.active_combat
                )

            narration = "mounted_movement"

        # CP-18A: Dismount intent
        elif isinstance(combat_intent, DismountIntent):
            dismount_state, dismount_events = resolve_dismount(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
            )
            events.extend(dismount_events)
            current_event_id += len(dismount_events)
            world_state = dismount_state
            narration = "dismounted"

        # CP-18A: Mount intent
        elif isinstance(combat_intent, MountIntent):
            mount_state, mount_events = resolve_mount(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
            )
            events.extend(mount_events)
            current_event_id += len(mount_events)
            world_state = mount_state
            narration = "mounted"

        # CP-18: Combat maneuver intents
        elif isinstance(combat_intent, (BullRushIntent, TripIntent, OverrunIntent,
                                        SunderIntent, DisarmIntent, GrappleIntent)):
            # Check if AoO dealt damage (for Disarm/Grapple auto-fail)
            aoo_damage = aoo_dealt_damage(events) if aoo_triggers else False

            # Resolve maneuver
            maneuver_events, world_state, maneuver_result = resolve_maneuver(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
                aoo_events=None,  # AoO events already added to events list
                aoo_defeated=False,  # Already handled in AoO section above
                aoo_dealt_damage=aoo_damage,
                causal_chain_id=causal_chain_id,
            )

            events.extend(maneuver_events)
            current_event_id += len(maneuver_events)

            # Generate narration token based on maneuver type and result
            maneuver_type = maneuver_result.maneuver_type
            if maneuver_result.success:
                narration = f"{maneuver_type}_success"
            else:
                narration = f"{maneuver_type}_failure"

        # CP-22: Grapple escape intent
        elif isinstance(combat_intent, GrappleEscapeIntent):
            escape_events, world_state = resolve_grapple_escape(
                initiator_id=combat_intent.attacker_id,
                target_id=combat_intent.target_id,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(escape_events)
            current_event_id += len(escape_events)

            # Determine narration based on event types
            escape_event_types = [e.event_type for e in escape_events]
            if "grapple_broken" in escape_event_types:
                narration = "grapple_escape_success"
            else:
                narration = "grapple_escape_failure"

        # WO-ENGINE-GRAPPLE-PIN-001: Pin escape intent
        elif isinstance(combat_intent, PinEscapeIntent):
            pin_escape_events, world_state, maneuver_result = resolve_pin_escape(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(pin_escape_events)
            current_event_id += len(pin_escape_events)
            narration = "pin_escape_success" if maneuver_result.success else "pin_escape_failed"

        # WO-015: Spellcasting intent
        elif isinstance(combat_intent, SpellCastIntent):
            # WO-ENGINE-DEFENSIVE-CASTING-001: If concentration failed by 5+, spell is disrupted
            # Slot consumed; no effect. (PHB p.140)
            if _defensive_cast_disrupted:
                _dc_entities = deepcopy(world_state.entities)
                _dc_spell_obj = SPELL_REGISTRY.get(combat_intent.spell_id)
                _dc_eff_level = _dc_spell_obj.level if _dc_spell_obj else 0
                if _dc_eff_level > 0 and combat_intent.caster_id in _dc_entities:
                    _decrement_spell_slot(_dc_entities[combat_intent.caster_id], _dc_eff_level)
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=_dc_entities,
                    active_combat=world_state.active_combat,
                )
                events.append(Event(
                    event_id=current_event_id,
                    event_type="spell_disrupted",
                    timestamp=timestamp + 0.15,
                    payload={
                        "actor_id": combat_intent.caster_id,
                        "spell_id": combat_intent.spell_id,
                        "reason": "concentration_failed_by_5",
                        "slot_consumed": True,
                    },
                    citations=["PHB p.140"],
                ))
                current_event_id += 1
                narration = "spell_disrupted"
            else:
                # Resolve the spell cast
                spell_events, world_state, narration = _resolve_spell_cast(
                    intent=combat_intent,
                    world_state=world_state,
                    rng=rng,
                    grid=None,  # Grid created internally if needed
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.1,
                    turn_index=turn_ctx.turn_index,
                )
                events.extend(spell_events)
                current_event_id += len(spell_events)

            # Check concentration break if the caster took damage this turn
            # (from AoO for example)
            hp_events = [e for e in events if e.event_type == "hp_changed"
                        and e.payload.get("entity_id") == combat_intent.caster_id
                        and e.payload.get("delta", 0) < 0]
            for hp_event in hp_events:
                damage = abs(hp_event.payload.get("delta", 0))
                conc_events, world_state = _check_concentration_break(
                    caster_id=combat_intent.caster_id,
                    damage_dealt=damage,
                    world_state=world_state,
                    rng=rng,
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.15,
                )
                events.extend(conc_events)
                current_event_id += len(conc_events)

        elif isinstance(combat_intent, SummonCompanionIntent):
            # WO-ENGINE-COMPANION-WIRE: spawn companion via event-sourced add_entity
            summon_result = spawn_companion(
                owner_id=turn_ctx.actor_id,
                companion_type=combat_intent.companion_type,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            if summon_result.status == "ok":
                from aidm.core.replay_runner import reduce_event
                from aidm.core.rng_manager import RNGManager
                _stub_rng = RNGManager(0)
                for evt in summon_result.events:
                    events.append(evt)
                    world_state = reduce_event(world_state, evt, _stub_rng)
                    current_event_id += 1
                narration = "companion_summoned"
            else:
                # Emit validation-failure event and fall through to turn_end
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "reason": summon_result.status,
                        "detail": summon_result.failure_reason,
                        "turn_index": turn_ctx.turn_index,
                    },
                ))
                current_event_id += 1

        # WO-ENGINE-REST-001: Rest intent
        elif isinstance(combat_intent, RestIntent):
            from aidm.core.rest_resolver import resolve_rest
            rest_result = resolve_rest(
                intent=combat_intent,
                world_state=world_state,
                actor_id=turn_ctx.actor_id,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            for evt in rest_result.events:
                events.append(Event(
                    event_id=evt["event_id"],
                    event_type=evt["event_type"],
                    timestamp=evt["timestamp"],
                    payload=evt["payload"],
                ))
            current_event_id += len(rest_result.events)
            world_state = rest_result.world_state
            narration = rest_result.narration or "rest_complete"

        # WO-ENGINE-SPELL-PREP-001: Spell preparation intent
        elif isinstance(combat_intent, PrepareSpellsIntent):
            from aidm.core.spell_prep_resolver import resolve_prepare_spells
            prep_events, world_state, narration = resolve_prepare_spells(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
                turn_index=turn_ctx.turn_index,
            )
            events.extend(prep_events)
            current_event_id += len(prep_events)

        # WO-ENGINE-CHARGE-001: Charge action (PHB p.150-151)
        elif isinstance(combat_intent, ChargeIntent):
            # AoO for charge movement (simplified: one trigger for full path)
            from aidm.schemas.attack import StepMoveIntent as _StepMoveIntent
            from aidm.schemas.position import Position as _Position
            attacker_pos = world_state.entities.get(turn_ctx.actor_id, {}).get(EF.POSITION)
            target_pos = world_state.entities.get(combat_intent.target_id, {}).get(EF.POSITION)
            _charge_aoo_events = []
            _charge_aoo_defeated = False
            _from_pos = _Position(x=attacker_pos["x"], y=attacker_pos["y"]) if attacker_pos else None
            _to_pos = _Position(x=target_pos["x"], y=target_pos["y"]) if target_pos else None
            if _from_pos and _to_pos and _from_pos.is_adjacent_to(_to_pos):
                _charge_step = _StepMoveIntent(
                    actor_id=turn_ctx.actor_id,
                    from_pos=_from_pos,
                    to_pos=_to_pos,
                )
                _charge_aoo_triggers = check_aoo_triggers(world_state, turn_ctx.actor_id, _charge_step)
                if _charge_aoo_triggers:
                    _charge_aoo_result = resolve_aoo_sequence(
                        triggers=_charge_aoo_triggers,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.05,
                    )
                    _charge_aoo_events = _charge_aoo_result.events
                    events.extend(_charge_aoo_events)
                    current_event_id += len(_charge_aoo_events)
                    world_state = apply_attack_events(world_state, _charge_aoo_events)
                    if _charge_aoo_result.provoker_defeated:
                        _charge_aoo_defeated = True

            if _charge_aoo_defeated:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="action_aborted",
                    timestamp=timestamp + 0.2,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "reason": "defeated_by_aoo_during_charge_movement",
                        "turn_index": turn_ctx.turn_index,
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 137}],
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.3,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events),
                    },
                ))
                return TurnResult(
                    status="ok",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    narration="action_aborted_by_aoo",
                )

            # Resolve the charge attack
            from aidm.core.attack_resolver import resolve_charge, apply_charge_events
            combat_events = resolve_charge(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(combat_events)
            current_event_id += len(combat_events)
            world_state = apply_charge_events(world_state, combat_events)

            # WO-015 pattern: concentration break on damage
            hp_events = [e for e in combat_events if e.event_type == "hp_changed"]
            for hp_event in hp_events:
                target_id = hp_event.payload.get("entity_id")
                damage = abs(hp_event.payload.get("delta", 0))
                if damage > 0 and target_id:
                    conc_events, world_state = _check_concentration_break(
                        caster_id=target_id,
                        damage_dealt=damage,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.15,
                    )
                    events.extend(conc_events)
                    current_event_id += len(conc_events)

            narration = "charge_complete"

        # WO-ENGINE-NATURAL-ATTACK-001: Natural attack (bite, claw, talon, etc.)
        elif isinstance(combat_intent, NaturalAttackIntent):
            from aidm.core.natural_attack_resolver import resolve_natural_attack
            nat_events, _ = resolve_natural_attack(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp,
            )
            events.extend(nat_events)
            current_event_id += len(nat_events)
            world_state = apply_attack_events(world_state, nat_events)
            narration = "natural_attack_resolved"

        # WO-ENGINE-CALLED-SHOT-POLICY-001: Called shot hard denial (STRAT-CAT-05 Option A)
        # Called shots are not a D&D 3.5e mechanic. Deny cleanly; surface nearest named mechanics.
        # KERNEL-04 (Intent Semantics) + KERNEL-10 (Adjudication Constitution) touch.
        elif isinstance(combat_intent, CalledShotIntent):
            suggestions = _called_shot_suggestions(combat_intent.target_description)
            payload = {
                "actor_id": combat_intent.actor_id,
                "dropped_action_type": "called_shot",
                "resolved_action_type": "none",
                "source_text": combat_intent.source_text,
                "reason": "Called shots are not a D&D 3.5e mechanic.",
                "suggestions": suggestions,
            }
            events.append(Event(event_id=current_event_id, event_type="action_dropped", timestamp=timestamp, payload=payload))
            current_event_id += 1
            # No state mutation. No action consumed. Player must re-declare.
            return TurnResult(
                status="action_dropped",
                world_state=world_state,
                events=events,
                turn_index=turn_ctx.turn_index,
                narration="called_shot_denied",
            )

        # WO-ENGINE-INTIMIDATE-DEMORALIZE-001: Demoralize Opponent (PHB p.76)
        # Standard action. Intimidate vs. target HD+WIS. Applies SHAKEN on success.
        # KERNEL-07 (Social Consequence) touch.
        elif isinstance(combat_intent, DemoralizeIntent):
            from aidm.core.skill_resolver import resolve_demoralize
            world_state, current_event_id, dem_events = resolve_demoralize(
                world_state=world_state,
                intent=combat_intent,
                next_event_id=current_event_id,
                rng=rng,
            )
            events.extend(dem_events)
            narration = "demoralize_resolved"

    # If no combat intent provided, use policy-based resolution (CP-09 behavior)
    elif doctrine is not None and turn_ctx.actor_team == "monsters":
        # Evaluate tactics using existing policy engine
        policy_result = evaluate_tactics(doctrine, world_state, turn_ctx.actor_id)

        # CP-13: Attempt to map policy output to combat intent
        monster_combat_intent = resolve_monster_combat_intent(
            policy_result=policy_result,
            doctrine=doctrine,
            actor_id=turn_ctx.actor_id,
            world_state=world_state
        )

        # If mapping succeeded, route to combat resolver
        if monster_combat_intent is not None:
            # Validate: RNG must be provided for combat
            if rng is None:
                raise ValueError("RNG manager required for monster combat intent resolution")

            # Route to attack resolver (CP-13 uses AttackIntent only)
            combat_events = resolve_attack(
                intent=monster_combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
            )
            events.extend(combat_events)
            current_event_id += len(combat_events)

            # Apply events to get updated state
            world_state = apply_attack_events(world_state, combat_events)

            # Generate narration token
            attack_events = [e for e in combat_events if e.event_type == "attack_roll"]
            if attack_events and attack_events[0].payload["hit"]:
                narration = "attack_hit"
            else:
                narration = "attack_miss"

        # Otherwise, preserve CP-09 behavior (emit tactic_selected stub)
        elif policy_result.status == "ok" and policy_result.selected is not None:
            # Emit tactic_selected event with citations
            events.append(Event(
                event_id=current_event_id,
                event_type="tactic_selected",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": turn_ctx.actor_id,
                    "tactic_class": policy_result.selected.candidate.tactic_class,
                    "score": policy_result.selected.score,
                    "reasons": policy_result.selected.reasons,
                    "turn_index": turn_ctx.turn_index
                },
                citations=[{"source_id": "e390dfd9143f", "page": 133}]  # MM goblin
            ))
            current_event_id += 1
        else:
            # Policy evaluation failed or no tactics available
            events.append(Event(
                event_id=current_event_id,
                event_type="policy_evaluation_failed",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": turn_ctx.actor_id,
                    "status": policy_result.status,
                    "missing_fields": policy_result.missing_fields,
                    "turn_index": turn_ctx.turn_index
                }
            ))
            current_event_id += 1
    else:
        # PC turn: emit stub action (no actual intent processing yet)
        events.append(Event(
            event_id=current_event_id,
            event_type="action_declared",
            timestamp=timestamp + 0.1,
            payload={
                "actor_id": turn_ctx.actor_id,
                "action_type": "attack",
                "target_id": "stub_target",
                "turn_index": turn_ctx.turn_index,
                "note": "Stub action for vertical slice V1"
            },
            citations=[{"source_id": "681f92bc94ff", "page": 140}]  # PHB attack action
        ))
        current_event_id += 1

    # Emit turn_end event
    # WO-ENGINE-LEVELUP-WIRE: Award XP for any entity_defeated events this turn
    defeated_ids = [
        e.payload.get("entity_id")
        for e in events
        if e.event_type == "entity_defeated" and e.payload.get("entity_id")
    ]
    for defeated_id in defeated_ids:
        world_state, current_event_id = _award_xp_for_defeat(
            world_state=world_state,
            defeated_entity_id=defeated_id,
            events=events,
            current_event_id=current_event_id,
            timestamp=timestamp,
            rng=rng,
        )

    # WO-ENGINE-BARDIC-MUSIC-001: tick inspire courage buff at end of each turn
    _has_ic = any(
        e.get(EF.INSPIRE_COURAGE_ACTIVE, False)
        for e in world_state.entities.values()
    )
    if _has_ic:
        from aidm.core.bardic_music_resolver import tick_inspire_courage as _tick_ic
        _ic_events, world_state = _tick_ic(world_state, current_event_id, timestamp + 0.12)
        events.extend(_ic_events)
        current_event_id += len(_ic_events)

    # WO-ENGINE-BARBARIAN-RAGE-001: tick rage at end of actor's turn (PHB p.25)
    _rage_tick_actor = world_state.entities.get(turn_ctx.actor_id, {})
    if _rage_tick_actor.get(EF.RAGE_ACTIVE, False):
        from aidm.core.rage_resolver import tick_rage as _tick_rage
        _rage_tick_evts, world_state = _tick_rage(
            turn_ctx.actor_id, world_state, current_event_id, timestamp + 0.15
        )
        events.extend(_rage_tick_evts)
        current_event_id += len(_rage_tick_evts)

    events.append(Event(
        event_id=current_event_id,
        event_type="turn_end",
        timestamp=timestamp + 0.2,
        payload={
            "turn_index": turn_ctx.turn_index,
            "actor_id": turn_ctx.actor_id,
            "events_emitted": len(events)
        }
    ))
    current_event_id += 1

    # State mutation: store turn counter in active_combat metadata
    active_combat = deepcopy(world_state.active_combat) if world_state.active_combat else {}
    active_combat["turn_counter"] = turn_ctx.turn_index + 1

    # CP-19: Round-end condition expiry — tick DurationTracker after last actor's turn
    initiative_order = active_combat.get("initiative_order", [])
    if initiative_order:
        last_actor_index = len(initiative_order) - 1
        current_position = turn_ctx.turn_index % len(initiative_order)
        if current_position == last_actor_index:
            # End of round — tick duration tracker
            duration_tracker = _get_or_create_duration_tracker(world_state)
            expired_effects = duration_tracker.tick_round()

            if expired_effects:
                entities_copy = deepcopy(world_state.entities)
                for effect in expired_effects:
                    # Emit spell_effect_expired event (matches existing schema)
                    events.append(Event(
                        event_id=current_event_id,
                        event_type="spell_effect_expired",
                        timestamp=timestamp + 0.25,
                        payload={
                            "spell_id": effect.spell_id,
                            "spell_name": effect.spell_name,
                            "caster_id": effect.caster_id,
                            "target_id": effect.target_id,
                        },
                    ))
                    current_event_id += 1

                    # Remove condition from entity and emit condition_removed event
                    if effect.condition_applied and effect.target_id in entities_copy:
                        target_conditions = entities_copy[effect.target_id].get(EF.CONDITIONS, {})
                        if isinstance(target_conditions, dict) and effect.condition_applied in target_conditions:
                            del target_conditions[effect.condition_applied]
                            entities_copy[effect.target_id][EF.CONDITIONS] = target_conditions
                            events.append(Event(
                                event_id=current_event_id,
                                event_type="condition_removed",
                                timestamp=timestamp + 0.26,
                                payload={
                                    "entity_id": effect.target_id,
                                    "condition": effect.condition_applied,
                                    "reason": "duration_expired",
                                    "spell_name": effect.spell_name,
                                },
                            ))
                            current_event_id += 1

                # Rebuild world_state with expired conditions removed
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=entities_copy,
                    active_combat=world_state.active_combat,
                )

            # Persist updated tracker to active_combat
            active_combat["duration_tracker"] = duration_tracker.to_dict()

            # WO-ENGINE-DEATH-DYING-001: Dying bleed tick — end of round
            # PHB p.145: Each dying entity makes DC 10 Fort save or loses 1 HP.
            if rng is not None:
                from aidm.core.dying_resolver import resolve_dying_tick
                dying_events, world_state = resolve_dying_tick(
                    world_state=world_state,
                    rng=rng,
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.5,
                )
                events.extend(dying_events)
                current_event_id += len(dying_events)

            # WO-ENGINE-CONDITION-DURATION-001: Tick timed conditions end-of-round.
            world_state, events, current_event_id = tick_conditions(
                world_state, events, current_event_id, timestamp + 0.55
            )

            # WO-ENGINE-WILDSHAPE-DURATION-001: Wild Shape duration auto-revert
            _has_ws = any(
                e.get(EF.WILD_SHAPE_ACTIVE, False)
                for e in world_state.entities.values()
            )
            if _has_ws:
                from aidm.core.wild_shape_resolver import tick_wild_shape_duration
                _wsd_events, world_state = tick_wild_shape_duration(
                    world_state=world_state,
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.6,
                )
                events.extend(_wsd_events)
                current_event_id += len(_wsd_events)

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=deepcopy(world_state.entities),
        active_combat=active_combat
    )

    # WO-030: Generate narration text if service provided
    narration_text = None
    narration_provenance = None

    if narration and narration_service is not None:
        try:
            # Import adapter dynamically to avoid BL-004 violation (no static import)
            # This uses importlib to avoid AST-level import detection
            import importlib
            adapter = importlib.import_module("aidm.narration.play_loop_adapter")
            generate_narration_for_turn = adapter.generate_narration_for_turn

            # Determine target_id from narration context
            target_id = None
            if combat_intent is not None:
                if isinstance(combat_intent, (AttackIntent, FullAttackIntent)):
                    target_id = combat_intent.target_id
                elif isinstance(combat_intent, (BullRushIntent, TripIntent, OverrunIntent,
                                                SunderIntent, DisarmIntent, GrappleIntent)):
                    target_id = combat_intent.target_id

            # Extract entity names from world state
            actor_entity = updated_state.entities.get(turn_ctx.actor_id, {})
            actor_name = actor_entity.get("name", turn_ctx.actor_id)

            target_name = None
            if target_id:
                target_entity = updated_state.entities.get(target_id, {})
                target_name = target_entity.get("name", target_id)

            # Extract weapon name from events
            weapon_name = None
            for event in events:
                if event.event_type == "attack_roll" and "weapon" in event.payload:
                    weapon_name = event.payload.get("weapon", "weapon")
                    break

            # Convert events to dicts for adapter (BL-003: narration can't import Event)
            event_dicts = []
            for event in events:
                event_dict = {
                    "type": event.event_type,
                    "timestamp": event.timestamp,
                    "payload": event.payload,
                }
                if event.citations:
                    event_dict["citations"] = event.citations
                event_dicts.append(event_dict)

            # Get world state hash
            from aidm.core.state import FrozenWorldStateView
            frozen_view = FrozenWorldStateView(updated_state)
            world_state_hash = frozen_view.state_hash()

            narration_text, narration_provenance = generate_narration_for_turn(
                narration_token=narration,
                events=event_dicts,
                actor_id=turn_ctx.actor_id,
                actor_name=actor_name,
                target_id=target_id,
                target_name=target_name,
                weapon_name=weapon_name,
                world_state_hash=world_state_hash,
                narration_service=narration_service,
            )
        except ImportError:
            # Narration adapter not available — gracefully skip
            narration_text = None
            narration_provenance = None
        except Exception:
            # Any other error — narration is non-critical, don't crash the turn
            narration_text = None
            narration_provenance = None

    return TurnResult(
        status="ok",
        world_state=updated_state,
        events=events,
        turn_index=turn_ctx.turn_index,
        narration=narration,
        narration_text=narration_text,
        narration_provenance=narration_provenance,
    )


def execute_exploration_skill_check(
    world_state: WorldState,
    actor_id: str,
    skill_name: str,
    dc: int,
    modifier: int,
    rng,
    take_10: bool = False,
    take_20: bool = False,
    target_id=None,
    method_tag: str = "default",
    next_event_id: int = 0,
):
    """WO-ENGINE-RETRY-001: Entry point for exploration skill checks.

    Wraps evaluate_check() from retry_policy.py, initializes game_clock if
    absent, and re-sequences raw event IDs to be monotonic from next_event_id.

    Returns:
        Tuple of (success, roll_used, updated_world_state, events).
    """
    from aidm.core.retry_policy import evaluate_check
    from aidm.schemas.time import GameClock

    ws = world_state
    if ws.game_clock is None:
        from copy import deepcopy
        ws = deepcopy(ws)
        ws.game_clock = GameClock(t_seconds=0, scale="exploration")

    success, roll_used, updated_ws, raw_events = evaluate_check(
        world_state=ws,
        actor_id=actor_id,
        skill_name=skill_name,
        dc=dc,
        modifier=modifier,
        target_id=target_id,
        method_tag=method_tag,
        take_10=take_10,
        take_20=take_20,
        rng=rng,
    )

    # Re-sequence event IDs to be monotonic from next_event_id
    from aidm.core.event_log import Event
    events = []
    for i, ev in enumerate(raw_events):
        events.append(Event(
            event_id=next_event_id + i,
            event_type=ev.event_type,
            timestamp=ev.timestamp,
            payload=ev.payload,
        ))

    return success, roll_used, updated_ws, events


def execute_scenario(
    initial_state: WorldState,
    turn_sequence: List[TurnContext],
    doctrines: Dict[str, MonsterDoctrine],
    initial_event_id: int = 0,
    initial_timestamp: float = 0.0
) -> tuple[WorldState, EventLog]:
    """
    Execute a full scenario (multiple turns).

    Args:
        initial_state: Starting world state
        turn_sequence: List of turn contexts to execute
        doctrines: Dict mapping actor_id -> MonsterDoctrine (for monsters only)
        initial_event_id: Starting event ID
        initial_timestamp: Starting timestamp

    Returns:
        Tuple of (final_world_state, event_log)
    """
    world_state = initial_state
    event_log = EventLog()
    current_event_id = initial_event_id
    current_timestamp = initial_timestamp

    for turn_ctx in turn_sequence:
        # Get doctrine for this actor (if monster)
        doctrine = doctrines.get(turn_ctx.actor_id)

        # Execute turn
        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            doctrine=doctrine,
            next_event_id=current_event_id,
            timestamp=current_timestamp
        )

        # Update state and event log
        world_state = turn_result.world_state
        for event in turn_result.events:
            event_log.append(event)

        # Advance counters
        current_event_id += len(turn_result.events)
        current_timestamp += 1.0  # 1 second per turn (arbitrary)

    return world_state, event_log
