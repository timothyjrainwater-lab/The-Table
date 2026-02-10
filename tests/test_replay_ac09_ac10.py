"""AC-09 and AC-10 compliance tests for replay_runner."""


# ============================================================================
# AC-09: Mutating Event Coverage (WO-M1-01 Acceptance Criterion)
# ============================================================================

def test_ac09_all_mutating_events_have_handlers():
    """AC-09: Every mutating event type must have a reducer handler.

    ACCEPTANCE CRITERION:
    - Every event type in MUTATING_EVENTS must have an explicit handler in reduce_event()
    - Missing handler = test FAILS

    WHY: If a mutating event lacks a handler, replay diverges from live execution.
    The event log records that something changed, but replay ignores it.
    """
    from aidm.core.replay_runner import get_missing_handlers

    missing = get_missing_handlers()

    assert len(missing) == 0, (
        f"AC-09 FAILED: {len(missing)} mutating events lack reducer handlers:\n"
        f"{sorted(missing)}\n\n"
        f"Every event in MUTATING_EVENTS must have a handler in reduce_event().\n"
        f"Add handlers for missing events to pass AC-09."
    )


def test_ac09_dynamic_intent_events_exempted():
    """AC-09: Dynamic intent.* events are explicitly exempted.

    ACCEPTANCE CRITERION:
    - Events matching pattern "intent_{action}" (e.g., intent_attack, intent_move) are dynamic
    - They should NOT be in MUTATING_EVENTS or INFORMATIONAL_EVENTS

    WHY: intent_{action} events are generated at runtime for each action type
    and cannot be statically enumerated. Note: intent_validation_failed is NOT
    a dynamic intent event - it's a static validation failure event.
    """
    from aidm.core.replay_runner import MUTATING_EVENTS, INFORMATIONAL_EVENTS, DYNAMIC_INTENT_PREFIX

    # Check that no truly dynamic intent events (intent_{action}) are statically listed
    # Note: We only flag events that look like dynamic action intents
    # (intent_validation_failed, policy_evaluation_failed are NOT dynamic intent events)

    # Create a list of events that look like dynamic intent actions
    # (start with "intent_" but are not known static events like intent_validation_failed)
    known_static_events_with_intent_prefix = {"intent_validation_failed"}

    for event_type in MUTATING_EVENTS:
        if event_type.startswith(DYNAMIC_INTENT_PREFIX):
            if event_type not in known_static_events_with_intent_prefix:
                assert False, (
                    f"AC-09 FAILED: Dynamic intent event '{event_type}' found in MUTATING_EVENTS.\n"
                    f"Intent action events are dynamic and should not be statically listed."
                )

    for event_type in INFORMATIONAL_EVENTS:
        if event_type.startswith(DYNAMIC_INTENT_PREFIX):
            if event_type not in known_static_events_with_intent_prefix:
                assert False, (
                    f"AC-09 FAILED: Dynamic intent event '{event_type}' found in INFORMATIONAL_EVENTS.\n"
                    f"Intent action events are dynamic and should not be statically listed."
                )


def test_ac09_movement_declared_is_informational():
    """AC-09: movement_declared is explicitly non-mutating (per work order).

    ACCEPTANCE CRITERION:
    - movement_declared must be in INFORMATIONAL_EVENTS
    - movement_declared must NOT be in MUTATING_EVENTS

    WHY: Work order explicitly states: "movement_declared stays informational (no position mutation)"
    Position changes occur via the "move" event, not movement_declared.
    """
    from aidm.core.replay_runner import MUTATING_EVENTS, INFORMATIONAL_EVENTS

    assert "movement_declared" in INFORMATIONAL_EVENTS, (
        "AC-09 FAILED: movement_declared must be in INFORMATIONAL_EVENTS (work order requirement)"
    )

    assert "movement_declared" not in MUTATING_EVENTS, (
        "AC-09 FAILED: movement_declared must NOT be in MUTATING_EVENTS (work order requirement)"
    )


# ============================================================================
# AC-10: Replay Hash Equivalence (WO-M1-01 Acceptance Criterion)
# ============================================================================

def test_ac10_replay_10x_produces_identical_hashes():
    """AC-10: Replay produces identical state_hash 10 times in a row.

    ACCEPTANCE CRITERION:
    - Given initial state + recorded event log
    - Replay via reducer-only path 10 times
    - All 10 final state_hash values must be IDENTICAL

    WHY: This is the definitive test of deterministic replay. If hashes diverge
    across replays, the reducer is non-deterministic or state mutation is leaking.
    """
    from aidm.core.state import WorldState
    from aidm.core.event_log import Event, EventLog
    from aidm.core.replay_runner import run

    # Create initial state
    initial_state = WorldState(
        ruleset_version="dnd3.5",
        entities={
            "player": {"hp": 50, "initiative": 0, "position": {"x": 0, "y": 0}},
            "goblin": {"hp": 7, "initiative": 0, "position": {"x": 5, "y": 0}},
        },
    )

    # Create event log with various mutating events
    event_log = EventLog()

    # Combat started
    event_log.append(
        Event(
            event_id=0,
            event_type="combat_started",
            timestamp=1.0,
            payload={"participants": ["player", "goblin"], "initiative_order": []},
        )
    )

    # Initiative rolls
    event_log.append(
        Event(
            event_id=1,
            event_type="initiative_rolled",
            timestamp=1.1,
            payload={"entity_id": "player", "initiative": 15},
        )
    )
    event_log.append(
        Event(
            event_id=2,
            event_type="initiative_rolled",
            timestamp=1.2,
            payload={"entity_id": "goblin", "initiative": 10},
        )
    )

    # Round 1 starts
    event_log.append(
        Event(
            event_id=3,
            event_type="combat_round_started",
            timestamp=2.0,
            payload={"round": 1},
        )
    )

    # Player turn
    event_log.append(
        Event(
            event_id=4,
            event_type="turn_start",
            timestamp=2.1,
            payload={"entity_id": "player"},
        )
    )

    # Player moves
    event_log.append(
        Event(
            event_id=5,
            event_type="move",
            timestamp=2.2,
            payload={"entity_id": "player", "new_position": {"x": 3, "y": 0}},
        )
    )

    # Player attacks (damage to goblin)
    event_log.append(
        Event(
            event_id=6,
            event_type="hp_changed",
            timestamp=2.3,
            payload={
                "entity_id": "goblin",
                "hp_before": 7,
                "hp_after": 2,
                "delta": -5,
                "source": "attack_damage",
            },
        )
    )

    # Player turn ends
    event_log.append(
        Event(
            event_id=7,
            event_type="turn_end",
            timestamp=2.4,
            payload={"entity_id": "player"},
        )
    )

    # Goblin turn
    event_log.append(
        Event(
            event_id=8,
            event_type="turn_start",
            timestamp=3.0,
            payload={"entity_id": "goblin"},
        )
    )

    # Goblin attacks (damage to player)
    event_log.append(
        Event(
            event_id=9,
            event_type="hp_changed",
            timestamp=3.1,
            payload={
                "entity_id": "player",
                "hp_before": 50,
                "hp_after": 46,
                "delta": -4,
                "source": "attack_damage",
            },
        )
    )

    # Goblin turn ends
    event_log.append(
        Event(
            event_id=10,
            event_type="turn_end",
            timestamp=3.2,
            payload={"entity_id": "goblin"},
        )
    )

    master_seed = 12345

    # Run replay 10 times
    hashes = []
    for i in range(10):
        report = run(initial_state, master_seed, event_log)
        hashes.append(report.final_hash)

    # All hashes must be identical
    unique_hashes = set(hashes)

    assert len(unique_hashes) == 1, (
        f"AC-10 FAILED: Replay produced {len(unique_hashes)} different hashes across 10 runs.\n"
        f"Expected: 1 unique hash (perfect determinism)\n"
        f"Got: {unique_hashes}\n\n"
        f"This indicates non-deterministic behavior in reduce_event() or state mutation."
    )


def test_ac10_hp_changed_accepts_hp_after_or_new_hp():
    """AC-10: hp_changed handler accepts both hp_after and new_hp (work order requirement).

    ACCEPTANCE CRITERION:
    - hp_changed event must accept both "hp_after" and "new_hp" payload fields
    - Both should produce identical final state

    WHY: Work order explicitly states: "hp_changed handler must accept hp_after OR new_hp"
    """
    from aidm.core.state import WorldState
    from aidm.core.event_log import Event, EventLog
    from aidm.core.replay_runner import run

    initial_state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 50}},
    )

    # Event log with hp_after
    event_log1 = EventLog()
    event_log1.append(
        Event(
            event_id=0,
            event_type="hp_changed",
            timestamp=1.0,
            payload={"entity_id": "player", "hp_after": 45, "delta": -5},
        )
    )

    # Event log with new_hp
    event_log2 = EventLog()
    event_log2.append(
        Event(
            event_id=0,
            event_type="hp_changed",
            timestamp=1.0,
            payload={"entity_id": "player", "new_hp": 45, "delta": -5},
        )
    )

    master_seed = 42

    report1 = run(initial_state, master_seed, event_log1)
    report2 = run(initial_state, master_seed, event_log2)

    # Both should produce identical final state
    assert report1.final_hash == report2.final_hash, (
        "AC-10 FAILED: hp_changed with hp_after vs new_hp produced different hashes.\n"
        f"hp_after hash: {report1.final_hash}\n"
        f"new_hp hash: {report2.final_hash}\n\n"
        f"Work order requirement: handler must accept hp_after OR new_hp."
    )

    # Verify HP actually changed
    assert report1.final_state.entities["player"]["hp"] == 45
    assert report2.final_state.entities["player"]["hp"] == 45
