"""Deterministic replay runner for event-sourced simulations.

BOUNDARY LAW (BL-012): reduce_event() is the canonical state reducer. All
game state mutations in resolvers must emit events, and event application
must go through this reducer for replay to work.

WHY: If state is mutated outside this reducer, replay diverges — the event
log records what happened, but direct mutation bypasses the log.

WHAT BREAKS IF VIOLATED: Replay verification, 10x determinism guarantee,
audit trail integrity, session save/load.

SINGLE SOURCE OF TRUTH for: Event-to-state reduction.
CANONICAL OWNER: aidm.core.replay_runner (this file).

AC-09 COMPLIANCE: This module implements reducers for all state-mutating events.
AC-10 COMPLIANCE: Replay produces identical state_hash for identical event logs.
"""

from typing import Dict, Any, List, Set
from dataclasses import dataclass
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.rng_manager import RNGManager
from aidm.core.rng_protocol import RNGProvider


# ============================================================================
# Event Type Classification
# ============================================================================

# State-mutating events (require reducer handlers for AC-09)
MUTATING_EVENTS: Set[str] = {
    # Entity management
    "add_entity",
    "remove_entity",
    "set_entity_field",

    # HP and damage
    "hp_changed",
    "damage_applied",
    "entity_defeated",

    # Position and movement
    "move",

    # Combat state
    "combat_started",
    "combat_round_started",
    "turn_start",
    "turn_end",
    "flat_footed_cleared",

    # Initiative
    "initiative_rolled",

    # Conditions
    "condition_applied",

    # Mounted combat
    "rider_mounted",
    "rider_dismounted",

    # Permanent stats
    "permanent_stat_modified",
    "permanent_stat_restored",

    # Derived stats and death
    "derived_stats_recalculated",
    "ability_score_death",
}

# Informational events (no state mutation, AC-09 exempted)
#
# CLASSIFICATION POLICY (WO-M1-05):
# An event is informational if:
# 1. It records a narrative moment with no state change (e.g., "attack_roll")
# 2. State mutation has already occurred via a separate mutating event
#    (e.g., "bull_rush_success" is informational because the position change
#    was already recorded by a "move" event)
#
# FUTURE MIGRATION RULE:
# If an informational event begins to directly mutate state (e.g., a maneuver
# result event starts setting entity fields without emitting a mutating event),
# it MUST be migrated to MUTATING_EVENTS and given an explicit reducer handler.
#
# WHY MANEUVER RESULTS ARE INFORMATIONAL:
# Events like "bull_rush_success", "disarm_success", etc. are currently
# informational because:
# - Position changes are recorded by "move" events
# - Condition changes are recorded by "condition_applied" events
# - HP changes are recorded by "hp_changed" events
# - The maneuver result event itself is a narrative marker that doesn't
#   directly mutate state—it reports that a sequence of state-mutating
#   events has completed successfully.
#
INFORMATIONAL_EVENTS: Set[str] = {
    # Informational/narrative
    "no-op",
    "attack_roll",
    "damage_roll",
    "save_rolled",
    "rule_lookup",
    "intent_validation_failed",
    "policy_evaluation_failed",
    "targeting_failed",

    # Declarations (no immediate state change, movement_declared explicitly non-mutating per work order)
    "action_declared",
    "movement_declared",
    "mounted_move_declared",
    "spell_cast",
    "attack",

    # Maneuver declarations (state changes come from success/failure events)
    "bull_rush_declared",
    "disarm_declared",
    "grapple_declared",
    "overrun_declared",
    "sunder_declared",
    "trip_declared",

    # Maneuver results (informational, state already changed by other events)
    "bull_rush_success",
    "bull_rush_failure",
    "disarm_success",
    "disarm_failure",
    "grapple_success",
    "grapple_failure",
    "overrun_success",
    "overrun_failure",
    "overrun_avoided",
    "sunder_success",
    "sunder_failure",
    "trip_success",
    "trip_failure",
    "counter_disarm_success",
    "counter_disarm_failure",
    "counter_trip_success",
    "counter_trip_failure",

    # AoO and triggers
    "aoo_triggered",
    "aoo_blocked_by_cover",
    "fall_triggered",
    "hazard_triggered",

    # Full attack flow
    "full_attack_start",
    "full_attack_end",
    "num_hits",

    # Checks and rolls
    "opposed_check",
    "ride_check",
    "touch_attack_roll",
    "spell_resistance_checked",
    "save_negated",
    "unconscious_saddle_check",

    # Environmental
    "environmental_damage",
    "falling_damage",

    # Meta
    "tactic_selected",
    "action_aborted",
}

# Dynamic event types (exempt from AC-09, generated at runtime)
# Format: intent_{action_type} (e.g., intent_attack, intent_move)
DYNAMIC_INTENT_PREFIX = "intent_"


@dataclass
class ReplayReport:
    """Report of replay execution with verification results."""

    final_state: WorldState
    final_hash: str
    events_processed: int
    determinism_verified: bool
    divergence_info: str = ""


# ============================================================================
# Event Reducer (AC-09: All mutating events must have handlers)
# ============================================================================

def reduce_event(state: WorldState, event: Event, rng_manager: RNGProvider) -> WorldState:
    """
    Single reducer function that applies an event to state.

    This is the ONLY function that mutates state based on events.
    All game logic mutations must go through here.

    AC-09 COMPLIANCE: Every mutating event type in MUTATING_EVENTS must have
    a handler below. Missing handlers = test failure.

    AC-10 COMPLIANCE: Deterministic reduction ensures identical state_hash
    for identical event sequences.
    """
    # Deep copy to avoid mutation
    new_state = deepcopy(state)

    event_type = event.event_type
    payload = event.payload

    # ========================================================================
    # MUTATING EVENT HANDLERS
    # ========================================================================

    # Entity Management
    # ------------------------------------------------------------------------

    if event_type == "add_entity":
        # Add a new entity
        entity_id = payload.get("entity_id")
        entity_data = payload.get("data", {})

        if entity_id:
            new_state.entities[entity_id] = entity_data

    elif event_type == "remove_entity":
        # Remove an entity
        entity_id = payload.get("entity_id")

        if entity_id and entity_id in new_state.entities:
            del new_state.entities[entity_id]

    elif event_type == "set_entity_field":
        # Set a field on an entity
        entity_id = payload.get("entity_id")
        field = payload.get("field")
        value = payload.get("value")

        if entity_id and field:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}
            new_state.entities[entity_id][field] = value

    # HP and Damage
    # ------------------------------------------------------------------------

    elif event_type == "hp_changed":
        # Update entity HP
        # Payload: entity_id, hp_after (or new_hp), hp_before, delta, source
        entity_id = payload.get("entity_id")

        # Accept both hp_after and new_hp (work order requirement)
        hp_after = payload.get("hp_after") or payload.get("new_hp")

        if entity_id and hp_after is not None:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}
            new_state.entities[entity_id]["hp"] = hp_after

    elif event_type == "damage_applied":
        # Apply damage to entity (may be redundant with hp_changed, but handle it)
        entity_id = payload.get("entity_id")
        damage = payload.get("damage", 0)

        if entity_id and entity_id in new_state.entities:
            current_hp = new_state.entities[entity_id].get("hp", 0)
            new_state.entities[entity_id]["hp"] = max(0, current_hp - damage)

    elif event_type == "entity_defeated":
        # Mark entity as defeated
        entity_id = payload.get("entity_id")

        if entity_id and entity_id in new_state.entities:
            new_state.entities[entity_id]["defeated"] = True
            new_state.entities[entity_id]["hp"] = 0

    # Position and Movement
    # ------------------------------------------------------------------------

    elif event_type == "move":
        # Update entity position
        entity_id = payload.get("entity_id")
        new_position = payload.get("new_position")  # {x, y}

        if entity_id and new_position:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}
            new_state.entities[entity_id]["position"] = new_position

    # Combat State
    # ------------------------------------------------------------------------

    elif event_type == "combat_started":
        # Initialize combat state
        if new_state.active_combat is None:
            new_state.active_combat = {}

        new_state.active_combat["active"] = True
        new_state.active_combat["round"] = 0
        new_state.active_combat["participants"] = payload.get("participants", [])
        new_state.active_combat["initiative_order"] = payload.get("initiative_order", [])

    elif event_type == "combat_round_started":
        # Increment round counter
        if new_state.active_combat is None:
            new_state.active_combat = {}

        round_number = payload.get("round", 1)
        new_state.active_combat["round"] = round_number

    elif event_type == "turn_start":
        # Mark entity's turn as active
        entity_id = payload.get("entity_id")

        if new_state.active_combat is None:
            new_state.active_combat = {}

        new_state.active_combat["current_turn"] = entity_id

    elif event_type == "turn_end":
        # Clear current turn
        if new_state.active_combat is None:
            new_state.active_combat = {}

        new_state.active_combat["current_turn"] = None

    elif event_type == "flat_footed_cleared":
        # Clear flat-footed condition
        entity_id = payload.get("entity_id")

        if entity_id and entity_id in new_state.entities:
            new_state.entities[entity_id]["flat_footed"] = False

    # Initiative
    # ------------------------------------------------------------------------

    elif event_type == "initiative_rolled":
        # Store initiative roll for entity
        entity_id = payload.get("entity_id")
        initiative = payload.get("initiative")

        if entity_id and initiative is not None:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}
            new_state.entities[entity_id]["initiative"] = initiative

    # Conditions
    # ------------------------------------------------------------------------

    elif event_type == "condition_applied":
        # Apply condition to entity
        entity_id = payload.get("entity_id")
        condition = payload.get("condition")
        duration = payload.get("duration")

        if entity_id and condition:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}

            if "conditions" not in new_state.entities[entity_id]:
                new_state.entities[entity_id]["conditions"] = []

            condition_data = {"name": condition}
            if duration is not None:
                condition_data["duration"] = duration

            new_state.entities[entity_id]["conditions"].append(condition_data)

    # Mounted Combat
    # ------------------------------------------------------------------------

    elif event_type == "rider_mounted":
        # Mount rider on mount
        rider_id = payload.get("rider_id")
        mount_id = payload.get("mount_id")

        if rider_id and mount_id:
            if rider_id not in new_state.entities:
                new_state.entities[rider_id] = {}
            if mount_id not in new_state.entities:
                new_state.entities[mount_id] = {}

            new_state.entities[rider_id]["mounted"] = True
            new_state.entities[rider_id]["mount_id"] = mount_id
            new_state.entities[mount_id]["rider_id"] = rider_id

    elif event_type == "rider_dismounted":
        # Dismount rider from mount
        rider_id = payload.get("rider_id")
        mount_id = payload.get("mount_id")

        if rider_id and rider_id in new_state.entities:
            new_state.entities[rider_id]["mounted"] = False
            new_state.entities[rider_id].pop("mount_id", None)

        if mount_id and mount_id in new_state.entities:
            new_state.entities[mount_id].pop("rider_id", None)

    # Permanent Stats
    # ------------------------------------------------------------------------

    elif event_type == "permanent_stat_modified":
        # Modify permanent ability score
        entity_id = payload.get("entity_id")
        stat = payload.get("stat")  # e.g., "str", "dex", "con"
        modifier = payload.get("modifier")
        new_value = payload.get("new_value")

        if entity_id and stat:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}

            if "permanent_stats" not in new_state.entities[entity_id]:
                new_state.entities[entity_id]["permanent_stats"] = {}

            if new_value is not None:
                new_state.entities[entity_id]["permanent_stats"][stat] = new_value
            elif modifier is not None:
                current = new_state.entities[entity_id]["permanent_stats"].get(stat, 10)
                new_state.entities[entity_id]["permanent_stats"][stat] = current + modifier

    elif event_type == "permanent_stat_restored":
        # Restore permanent stat to base value
        entity_id = payload.get("entity_id")
        stat = payload.get("stat")
        base_value = payload.get("base_value")

        if entity_id and stat and base_value is not None:
            if entity_id not in new_state.entities:
                new_state.entities[entity_id] = {}

            if "permanent_stats" not in new_state.entities[entity_id]:
                new_state.entities[entity_id]["permanent_stats"] = {}

            new_state.entities[entity_id]["permanent_stats"][stat] = base_value

    # Derived Stats and Death
    # ------------------------------------------------------------------------

    elif event_type == "derived_stats_recalculated":
        # Recalculate and update derived stats (AC, saves, attack bonuses, etc.)
        # Payload: entity_id, recalculated_stats (list), hp_max_new (optional)
        from aidm.schemas.entity_fields import EF

        entity_id = payload.get("entity_id")
        # Accept both payload field names (fallback for compatibility)
        recalculated_stats = payload.get("recalculated_stats") or payload.get("derived_stats", {})
        hp_max_new = payload.get("hp_max_new")

        if entity_id and entity_id in new_state.entities:
            # Apply hp_max_new if present (CON changes)
            if hp_max_new is not None:
                new_state.entities[entity_id][EF.HP_MAX] = hp_max_new

            # If recalculated_stats is a dict, apply each stat
            if isinstance(recalculated_stats, dict):
                for stat_name, stat_value in recalculated_stats.items():
                    new_state.entities[entity_id][stat_name] = stat_value

    elif event_type == "ability_score_death":
        # Mark entity as defeated due to ability score reaching 0
        # Payload: entity_id, ability, final_score, cause
        from aidm.schemas.entity_fields import EF

        entity_id = payload.get("entity_id")

        if entity_id and entity_id in new_state.entities:
            # Set canonical defeat field only (EF.DEFEATED)
            new_state.entities[entity_id][EF.DEFEATED] = True

    # ========================================================================
    # INFORMATIONAL EVENTS (No-op, explicitly exempt from AC-09)
    # ========================================================================

    elif event_type in INFORMATIONAL_EVENTS:
        # Informational events do not mutate state
        pass

    # ========================================================================
    # DYNAMIC INTENT EVENTS (Exempt from AC-09, generated at runtime)
    # ========================================================================

    elif event_type.startswith(DYNAMIC_INTENT_PREFIX):
        # Dynamic intent events (e.g., intent_attack, intent_move) are informational
        pass

    # ========================================================================
    # UNKNOWN EVENTS (Fail-safe: ignore unknown events)
    # ========================================================================

    else:
        # Unknown event types are ignored (fail-safe)
        # This allows forward compatibility with new event types
        pass

    return new_state


# ============================================================================
# Replay Runner
# ============================================================================

def run(
    initial_state: WorldState,
    master_seed: int,
    event_log: EventLog,
    expected_final_hash: str = None,
) -> ReplayReport:
    """
    Run deterministic replay of event log.

    Args:
        initial_state: Starting world state
        master_seed: Master RNG seed for deterministic randomness
        event_log: Sequence of events to apply
        expected_final_hash: Optional expected hash for verification

    Returns:
        ReplayReport with final state and verification results
    """
    rng_manager = RNGManager(master_seed)
    current_state = deepcopy(initial_state)

    events_processed = 0

    for event in event_log.events:
        current_state = reduce_event(current_state, event, rng_manager)
        events_processed += 1

    final_hash = current_state.state_hash()

    # Verify determinism if expected hash provided
    determinism_verified = True
    divergence_info = ""

    if expected_final_hash is not None:
        if final_hash != expected_final_hash:
            determinism_verified = False
            divergence_info = (
                f"Hash mismatch: expected {expected_final_hash}, got {final_hash}"
            )

    return ReplayReport(
        final_state=current_state,
        final_hash=final_hash,
        events_processed=events_processed,
        determinism_verified=determinism_verified,
        divergence_info=divergence_info,
    )


# ============================================================================
# AC-09: Mutating Event Coverage Verification
# ============================================================================

def get_missing_handlers() -> Set[str]:
    """
    Identify mutating events that lack reducer handlers (AC-09 compliance check).

    Returns:
        Set of event types in MUTATING_EVENTS that don't have explicit handlers
    """
    # This function is used by tests to verify AC-09 compliance
    # It checks that all MUTATING_EVENTS have corresponding reducer logic

    # For static analysis, we verify handlers exist by checking the reduce_event source
    import inspect
    source = inspect.getsource(reduce_event)

    missing = set()
    for event_type in MUTATING_EVENTS:
        # Check if event_type appears in an if/elif condition in reduce_event
        if f'event_type == "{event_type}"' not in source:
            missing.add(event_type)

    return missing
