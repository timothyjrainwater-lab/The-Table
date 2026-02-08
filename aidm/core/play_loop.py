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
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Literal
from dataclasses import dataclass

from aidm.core.event_log import Event, EventLog
from aidm.core.state import WorldState
from aidm.schemas.doctrine import MonsterDoctrine
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
            actor_team = actor_entity.get("team", "monsters")
            # Find all entities on different team
            for entity_id, entity in world_state.entities.items():
                if entity_id != actor_id:
                    entity_team = entity.get("team", "unknown")
                    if entity_team != actor_team and entity_team != "unknown":
                        target_ids.append(entity_id)

    # Sort lexicographically for determinism
    sorted_targets = sorted(target_ids)

    # Pick first valid target (exists and not defeated)
    target_id = None
    for tid in sorted_targets:
        if tid in world_state.entities:
            entity = world_state.entities[tid]
            if not entity.get("defeated", False):
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


def execute_turn(
    world_state: WorldState,
    turn_ctx: TurnContext,
    doctrine: Optional[MonsterDoctrine] = None,
    combat_intent: Optional[Union[AttackIntent, FullAttackIntent]] = None,
    rng: Optional[RNGManager] = None,
    next_event_id: int = 0,
    timestamp: float = 0.0
) -> TurnResult:
    """
    Execute a single turn in the play loop.

    CP-12 INTEGRATION:
    - Accepts optional combat_intent (AttackIntent or FullAttackIntent)
    - Routes combat intents to CP-10/CP-11 resolvers
    - Validates intent (actor match, target exists, target not defeated)
    - Returns status + narration token

    BACKWARD COMPATIBILITY:
    - If combat_intent is None, uses policy-based resolution (CP-09 behavior)
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

    Returns:
        TurnResult with status, updated state, events, and narration token
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
            if target.get("defeated", False):
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
            if target.get("defeated", False):
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
                active_combat_updated = world_state.active_combat.copy()
                active_combat_updated["aoo_used_this_round"] = aoo_used
                world_state = WorldState(
                    ruleset_version=world_state.ruleset_version,
                    entities=world_state.entities.copy(),
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

            # Generate narration token
            narration = "full_attack_complete"

        elif isinstance(combat_intent, StepMoveIntent):
            # CP-15: Movement stub (full movement resolution deferred to CP-16)
            # AoOs have already been resolved above; movement itself is a stub
            events.append(Event(
                event_id=current_event_id,
                event_type="movement_declared",
                timestamp=timestamp + 0.1,
                payload={
                    "actor_id": combat_intent.actor_id,
                    "from_pos": {"x": combat_intent.from_pos.x, "y": combat_intent.from_pos.y},
                    "to_pos": {"x": combat_intent.to_pos.x, "y": combat_intent.to_pos.y},
                    "note": "CP-15 movement stub (full resolution deferred to CP-16)"
                }
            ))
            current_event_id += 1
            narration = "movement_stub"

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
            entities = world_state.entities.copy()
            mount_id = combat_intent.mount_id
            if mount_id in entities:
                updated_mount = entities[mount_id].copy()
                updated_mount["position"] = combat_intent.to_pos.to_dict()
                entities[mount_id] = updated_mount
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
    active_combat = world_state.active_combat.copy() if world_state.active_combat else {}
    active_combat["turn_counter"] = turn_ctx.turn_index + 1

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities.copy(),
        active_combat=active_combat
    )

    return TurnResult(
        status="ok",
        world_state=updated_state,
        events=events,
        turn_index=turn_ctx.turn_index,
        narration=narration
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
