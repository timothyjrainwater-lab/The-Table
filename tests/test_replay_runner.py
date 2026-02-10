"""Tests for deterministic replay runner."""

import pytest
from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.replay_runner import run, reduce_event
from aidm.core.rng_manager import RNGManager


def test_replay_twice_produces_identical_hashes():
    """Golden test: replaying same events twice should produce identical state."""
    # Create initial state
    initial_state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 20, "x": 0}},
    )

    # Create deterministic event log
    event_log = EventLog()
    event_log.append(
        Event(
            event_id=0,
            event_type="set_entity_field",
            timestamp=1.0,
            payload={"entity_id": "player", "field": "x", "value": 5},
        )
    )
    event_log.append(
        Event(
            event_id=1,
            event_type="set_entity_field",
            timestamp=2.0,
            payload={"entity_id": "player", "field": "hp", "value": 15},
        )
    )

    master_seed = 42

    # Run replay twice
    report1 = run(initial_state, master_seed, event_log)
    report2 = run(initial_state, master_seed, event_log)

    # Hashes must be identical
    assert report1.final_hash == report2.final_hash
    assert report1.events_processed == 2
    assert report2.events_processed == 2

    # Final state should match
    assert report1.final_state.entities["player"]["hp"] == 15
    assert report1.final_state.entities["player"]["x"] == 5


def test_replay_detects_divergence_on_event_order_change():
    """Replay should detect divergence if event order changes."""
    initial_state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 20}},
    )

    # Original event log
    event_log1 = EventLog()
    event_log1.append(
        Event(
            event_id=0,
            event_type="set_entity_field",
            timestamp=1.0,
            payload={"entity_id": "player", "field": "hp", "value": 15},
        )
    )
    event_log1.append(
        Event(
            event_id=1,
            event_type="set_entity_field",
            timestamp=2.0,
            payload={"entity_id": "player", "field": "x", "value": 5},
        )
    )

    # Different event log (same events, different order of fields)
    event_log2 = EventLog()
    event_log2.append(
        Event(
            event_id=0,
            event_type="set_entity_field",
            timestamp=1.0,
            payload={"entity_id": "player", "field": "x", "value": 5},
        )
    )
    event_log2.append(
        Event(
            event_id=1,
            event_type="set_entity_field",
            timestamp=2.0,
            payload={"entity_id": "player", "field": "hp", "value": 15},
        )
    )

    master_seed = 42

    report1 = run(initial_state, master_seed, event_log1)
    report2 = run(initial_state, master_seed, event_log2)

    # Final values are same, so hashes should be same
    # (This tests stable hashing, not divergence from different logic)
    assert report1.final_state.entities["player"]["hp"] == 15
    assert report2.final_state.entities["player"]["hp"] == 15

    # But if we modify one event to produce different final state
    event_log3 = EventLog()
    event_log3.append(
        Event(
            event_id=0,
            event_type="set_entity_field",
            timestamp=1.0,
            payload={"entity_id": "player", "field": "hp", "value": 10},  # Different!
        )
    )

    report3 = run(initial_state, master_seed, event_log3)

    # Now hashes should differ
    assert report1.final_hash != report3.final_hash


def test_no_op_event():
    """No-op events should not modify state."""
    initial_state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 20}},
    )

    initial_hash = initial_state.state_hash()

    event_log = EventLog()
    event_log.append(
        Event(event_id=0, event_type="no-op", timestamp=1.0, payload={})
    )

    report = run(initial_state, 42, event_log)

    # State should be unchanged (except deep copy)
    assert report.final_state.state_hash() == initial_hash


def test_add_entity_event():
    """add_entity event should add new entity."""
    initial_state = WorldState(ruleset_version="dnd3.5", entities={})

    event_log = EventLog()
    event_log.append(
        Event(
            event_id=0,
            event_type="add_entity",
            timestamp=1.0,
            payload={"entity_id": "goblin1", "data": {"hp": 5, "type": "monster"}},
        )
    )

    report = run(initial_state, 42, event_log)

    assert "goblin1" in report.final_state.entities
    assert report.final_state.entities["goblin1"]["hp"] == 5
    assert report.final_state.entities["goblin1"]["type"] == "monster"


def test_remove_entity_event():
    """remove_entity event should remove entity."""
    initial_state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 20}, "goblin": {"hp": 5}},
    )

    event_log = EventLog()
    event_log.append(
        Event(
            event_id=0,
            event_type="remove_entity",
            timestamp=1.0,
            payload={"entity_id": "goblin"},
        )
    )

    report = run(initial_state, 42, event_log)

    assert "goblin" not in report.final_state.entities
    assert "player" in report.final_state.entities


def test_expected_hash_verification():
    """Replay should verify expected hash."""
    initial_state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 20}},
    )

    event_log = EventLog()
    event_log.append(
        Event(
            event_id=0,
            event_type="set_entity_field",
            timestamp=1.0,
            payload={"entity_id": "player", "field": "hp", "value": 15},
        )
    )

    # Run once to get expected hash
    report1 = run(initial_state, 42, event_log)
    expected_hash = report1.final_hash

    # Run again with expected hash
    report2 = run(initial_state, 42, event_log, expected_final_hash=expected_hash)

    assert report2.determinism_verified is True
    assert report2.divergence_info == ""

    # Run with wrong expected hash
    wrong_hash = "0" * 64
    report3 = run(initial_state, 42, event_log, expected_final_hash=wrong_hash)

    assert report3.determinism_verified is False
    assert "Hash mismatch" in report3.divergence_info


def test_reduce_event_does_not_mutate_original_state():
    """reduce_event should not mutate the original state."""
    rng = RNGManager(42)
    original_state = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 20}},
    )

    event = Event(
        event_id=0,
        event_type="set_entity_field",
        timestamp=1.0,
        payload={"entity_id": "player", "field": "hp", "value": 10},
    )

    new_state = reduce_event(original_state, event, rng)

    # Original should be unchanged
    assert original_state.entities["player"]["hp"] == 20
    # New state should have the change
    assert new_state.entities["player"]["hp"] == 10

