"""Tests for EventLog append-only ledger."""

import pytest
from pathlib import Path
import tempfile
import os
from aidm.core.event_log import Event, EventLog


def test_event_creation():
    """Event can be created with required fields."""
    event = Event(
        event_id=0,
        event_type="attack",
        timestamp=1234567890.0,
        payload={"attacker": "goblin", "target": "player"},
        rng_offset=5,
    )

    assert event.event_id == 0
    assert event.event_type == "attack"
    assert event.payload["attacker"] == "goblin"


def test_append_enforces_monotonic_event_id():
    """EventLog must enforce monotonic event IDs."""
    log = EventLog()

    # First event with ID 0 should succeed
    event0 = Event(
        event_id=0, event_type="start", timestamp=1.0, payload={}
    )
    log.append(event0)

    # Next event must be ID 1
    event1 = Event(
        event_id=1, event_type="move", timestamp=2.0, payload={}
    )
    log.append(event1)

    assert len(log) == 2

    # Trying to append ID 1 again should fail
    duplicate_event = Event(
        event_id=1, event_type="attack", timestamp=3.0, payload={}
    )

    with pytest.raises(ValueError, match="monotonic"):
        log.append(duplicate_event)


def test_append_rejects_non_sequential_ids():
    """EventLog rejects non-sequential event IDs."""
    log = EventLog()

    event0 = Event(
        event_id=0, event_type="start", timestamp=1.0, payload={}
    )
    log.append(event0)

    # Skipping from 0 to 5 should fail
    event5 = Event(
        event_id=5, event_type="move", timestamp=2.0, payload={}
    )

    with pytest.raises(ValueError, match="must be 1"):
        log.append(event5)


def test_jsonl_roundtrip():
    """JSONL serialization should be stable and complete."""
    log = EventLog()

    events = [
        Event(event_id=0, event_type="start", timestamp=1.0, payload={"game": "dnd"}),
        Event(
            event_id=1,
            event_type="attack",
            timestamp=2.0,
            payload={"attacker": "goblin", "damage": 5},
            rng_offset=3,
        ),
        Event(event_id=2, event_type="end", timestamp=3.0, payload={}),
    ]

    for event in events:
        log.append(event)

    # Write to temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        log.to_jsonl(path)

        # Verify file exists
        assert path.exists()

        # Read back
        loaded_log = EventLog.from_jsonl(path)

        assert len(loaded_log) == len(log)

        for original, loaded in zip(log.events, loaded_log.events):
            assert original.event_id == loaded.event_id
            assert original.event_type == loaded.event_type
            assert original.timestamp == loaded.timestamp
            assert original.payload == loaded.payload
            assert original.rng_offset == loaded.rng_offset


def test_jsonl_is_diff_friendly():
    """JSONL output should use sorted keys for git-friendly diffs."""
    log = EventLog()

    event = Event(
        event_id=0,
        event_type="test",
        timestamp=1.0,
        payload={"z": 1, "a": 2, "m": 3},  # Unsorted keys
    )
    log.append(event)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        log.to_jsonl(path)

        # Read raw file content
        content = path.read_text()

        # Keys should be sorted alphabetically in JSON
        # event_id should come before event_type, payload, rng_offset, timestamp
        assert content.index('"event_id"') < content.index('"event_type"')
        assert content.index('"event_type"') < content.index('"payload"')


def test_event_log_indexing():
    """EventLog should support indexing."""
    log = EventLog()

    events = [
        Event(event_id=0, event_type="start", timestamp=1.0, payload={}),
        Event(event_id=1, event_type="middle", timestamp=2.0, payload={}),
        Event(event_id=2, event_type="end", timestamp=3.0, payload={}),
    ]

    for event in events:
        log.append(event)

    assert log[0].event_type == "start"
    assert log[1].event_type == "middle"
    assert log[2].event_type == "end"


def test_event_to_dict_from_dict():
    """Event serialization should roundtrip correctly."""
    original = Event(
        event_id=42,
        event_type="spell_cast",
        timestamp=999.5,
        payload={"spell": "fireball", "level": 3},
        rng_offset=10,
    )

    data = original.to_dict()
    restored = Event.from_dict(data)

    assert restored.event_id == original.event_id
    assert restored.event_type == original.event_type
    assert restored.timestamp == original.timestamp
    assert restored.payload == original.payload
    assert restored.rng_offset == original.rng_offset
