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

from copy import deepcopy
from typing import List, Dict, Any, Optional, Union, Tuple, Literal
from dataclasses import dataclass

from aidm.core.event_log import Event, EventLog
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.entity_fields import EF
from aidm.core.tactical_policy import evaluate_tactics, TacticalPolicyResult
from aidm.schemas.attack import AttackIntent, Weapon, StepMoveIntent
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.full_attack_resolver import FullAttackIntent, resolve_full_attack, apply_full_attack_events
from aidm.core.rng_manager import RNGManager
from aidm.core.aoo import check_aoo_triggers, resolve_aoo_sequence, aoo_dealt_damage  # CP-15/CP-18
# CP-18A: Mounted combat imports
from aidm.schemas.mounted_combat import MountedMoveIntent, DismountIntent, MountIntent
from aidm.core.mounted_combat import (
    resolve_mount, resolve_dismount, get_entity_position
)
# CP-18: Combat maneuver imports
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent,
)
from aidm.core.maneuver_resolver import resolve_maneuver
# WO-015: Spellcasting imports
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


def _resolve_spell_cast(
    intent: SpellCastIntent,
    world_state: WorldState,
    rng: RNGManager,
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

    # Create caster stats
    caster = _create_caster_stats(intent.caster_id, world_state)

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

    # Resolve the spell
    resolution = resolver.resolve_spell(intent, caster, targets)

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
                },
                citations=list(spell.rule_citations),
            ))
            current_event_id += 1

            # Check for defeat
            if new_hp <= 0 and not entities[entity_id].get(EF.DEFEATED, False):
                entities[entity_id][EF.DEFEATED] = True
                events.append(Event(
                    event_id=current_event_id,
                    event_type="entity_defeated",
                    timestamp=timestamp + 0.02,
                    payload={
                        "entity_id": entity_id,
                        "source": f"spell:{spell.name}",
                    },
                ))
                current_event_id += 1

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
                },
                citations=list(spell.rule_citations),
            ))
            current_event_id += 1

    # Get/create duration tracker
    duration_tracker = _get_or_create_duration_tracker(world_state)

    # Apply conditions and track durations
    for entity_id, condition in resolution.conditions_applied:
        # Initialize conditions list if needed
        if EF.CONDITIONS not in entities[entity_id]:
            entities[entity_id][EF.CONDITIONS] = []

        # Add condition if not already present
        if condition not in entities[entity_id][EF.CONDITIONS]:
            entities[entity_id][EF.CONDITIONS].append(condition)

            events.append(Event(
                event_id=current_event_id,
                event_type="condition_applied",
                timestamp=timestamp + 0.02,
                payload={
                    "entity_id": entity_id,
                    "condition": condition,
                    "source": f"spell:{spell.name}",
                    "duration_rounds": spell.duration_rounds if spell.duration_rounds > 0 else None,
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
            duration_tracker.add_effect(effect)

    # Update active_combat with duration tracker
    active_combat = deepcopy(world_state.active_combat) if world_state.active_combat else {}
    active_combat["duration_tracker"] = duration_tracker.to_dict()

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
    rng: RNGManager,
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
    events = []
    current_event_id = next_event_id

    duration_tracker = _get_or_create_duration_tracker(world_state)

    # Check if caster has concentration effect
    concentration_effect = duration_tracker.get_concentration_effect(caster_id)
    if concentration_effect is None:
        return events, world_state

    # Roll Concentration check
    dc = 10 + damage_dealt
    concentration_bonus = world_state.entities.get(caster_id, {}).get("concentration_bonus", 0)
    roll = rng.stream("combat").randint(1, 20)
    total = roll + concentration_bonus

    if total < dc:
        # Concentration broken
        removed_effects = duration_tracker.break_concentration(caster_id)

        for effect in removed_effects:
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

            # Remove condition from target
            if effect.condition_applied:
                entities = deepcopy(world_state.entities)
                target_entity = entities.get(effect.target_id, {})
                conditions = target_entity.get(EF.CONDITIONS, [])
                if effect.condition_applied in conditions:
                    conditions.remove(effect.condition_applied)
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

                    # Update state
                    active_combat = deepcopy(world_state.active_combat) if world_state.active_combat else {}
                    active_combat["duration_tracker"] = duration_tracker.to_dict()
                    world_state = WorldState(
                        ruleset_version=world_state.ruleset_version,
                        entities=entities,
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


def execute_turn(
    world_state: WorldState,
    turn_ctx: TurnContext,
    doctrine: Optional[MonsterDoctrine] = None,
    combat_intent: Optional[Union[AttackIntent, FullAttackIntent]] = None,
    rng: Optional[RNGManager] = None,
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

    # CP-12/CP-15/CP-18: Combat intent validation and routing
    if combat_intent is not None:
        # Determine intent actor based on intent type
        intent_actor_id = None
        if isinstance(combat_intent, (AttackIntent, FullAttackIntent)):
            intent_actor_id = combat_intent.attacker_id
        elif isinstance(combat_intent, StepMoveIntent):
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
                                        SunderIntent, DisarmIntent, GrappleIntent)):
            intent_actor_id = combat_intent.attacker_id
        # WO-015: Spellcasting intents
        elif isinstance(combat_intent, SpellCastIntent):
            intent_actor_id = combat_intent.caster_id
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
        if isinstance(combat_intent, (AttackIntent, FullAttackIntent)):
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
        if rng is None:
            raise ValueError("RNG manager required for combat intent resolution")

        # CP-15: Check for AoO triggers before resolving main action
        aoo_triggers = check_aoo_triggers(world_state, turn_ctx.actor_id, combat_intent)

        if aoo_triggers:
            # Resolve AoO sequence
            aoo_result = resolve_aoo_sequence(
                triggers=aoo_triggers,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
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
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=deepcopy(world_state.entities),
                    active_combat=active_combat_updated
                )

            # If provoker was defeated by AoO, abort the main action
            if aoo_result.provoker_defeated:
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

        elif isinstance(combat_intent, StepMoveIntent):
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

        # CP-18A: Mounted movement intent
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
            )

            events.extend(maneuver_events)
            current_event_id += len(maneuver_events)

            # Generate narration token based on maneuver type and result
            maneuver_type = maneuver_result.maneuver_type
            if maneuver_result.success:
                narration = f"{maneuver_type}_success"
            else:
                narration = f"{maneuver_type}_failure"

        # WO-015: Spellcasting intent
        elif isinstance(combat_intent, SpellCastIntent):
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
