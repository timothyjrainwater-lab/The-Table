"""Tests for EventLog citations support."""

import pytest
from aidm.core.event_log import Event, EventLog
from aidm.schemas.citation import Citation
from pathlib import Path
import tempfile


def test_event_citations_default_empty_list():
    """Event citations should default to empty list."""
    event = Event(
        event_id=0,
        event_type="attack",
        timestamp=1.0,
        payload={}
    )

    assert event.citations == []


def test_event_with_citations():
    """Event should support citations list."""
    citation = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=157,
        span="Grapple rules"
    )

    event = Event(
        event_id=0,
        event_type="grapple_check",
        timestamp=1.0,
        payload={"attacker": "player", "target": "goblin"},
        citations=[citation.to_dict()]
    )

    assert len(event.citations) == 1
    assert event.citations[0]["source_id"] == "681f92bc94ff"
    assert event.citations[0]["page"] == 157


def test_eventlog_citations_serialization():
    """EventLog should serialize citations to JSONL correctly."""
    log = EventLog()

    citation1 = Citation(source_id="681f92bc94ff", short_name="PHB", page=157)
    citation2 = Citation(source_id="fed77f68501d", short_name="DMG", page=42)

    event1 = Event(
        event_id=0,
        event_type="grapple",
        timestamp=1.0,
        payload={"action": "initiate"},
        citations=[citation1.to_dict()]
    )

    event2 = Event(
        event_id=1,
        event_type="damage_roll",
        timestamp=2.0,
        payload={"damage": 5},
        citations=[citation1.to_dict(), citation2.to_dict()]
    )

    log.append(event1)
    log.append(event2)

    # Serialize to JSONL
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        log.to_jsonl(path)

        # Read back
        loaded_log = EventLog.from_jsonl(path)

        assert len(loaded_log) == 2
        assert loaded_log[0].citations == event1.citations
        assert loaded_log[1].citations == event2.citations
        assert len(loaded_log[1].citations) == 2


def test_eventlog_backward_compatible_no_citations():
    """EventLog should handle events without citations field (backward compat)."""
    log = EventLog()

    event = Event(
        event_id=0,
        event_type="move",
        timestamp=1.0,
        payload={"from": [0, 0], "to": [1, 0]}
        # No citations field
    )

    log.append(event)

    # Should have empty citations list
    assert event.citations == []

    # Serialize and deserialize
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        log.to_jsonl(path)

        loaded_log = EventLog.from_jsonl(path)
        assert loaded_log[0].citations == []


def test_event_citations_json_deterministic():
    """Event with citations should serialize deterministically."""
    citation = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=157
    )

    event1 = Event(
        event_id=0,
        event_type="test",
        timestamp=1.0,
        payload={},
        citations=[citation.to_dict()]
    )

    event2 = Event(
        event_id=0,
        event_type="test",
        timestamp=1.0,
        payload={},
        citations=[citation.to_dict()]
    )

    # Should serialize identically
    import json
    json1 = json.dumps(event1.to_dict(), sort_keys=True)
    json2 = json.dumps(event2.to_dict(), sort_keys=True)

    assert json1 == json2
