"""Tests for timer and deadline schemas."""

import pytest
import json
from aidm.schemas.timers import Deadline, TimerStatus, DeadlineVisibility


def test_deadline_basic():
    """Deadline should store id, name, due time, consequence, and visibility."""
    deadline = Deadline(
        id="ritual_completes",
        name="Dark Ritual Completes",
        due_at_t_seconds=1000,
        failure_consequence="Cultists summon demon",
        visibility="hinted"
    )

    assert deadline.id == "ritual_completes"
    assert deadline.name == "Dark Ritual Completes"
    assert deadline.due_at_t_seconds == 1000
    assert deadline.failure_consequence == "Cultists summon demon"
    assert deadline.visibility == "hinted"


def test_deadline_empty_id_rejected():
    """Deadline should reject empty id."""
    with pytest.raises(ValueError, match="id cannot be empty"):
        Deadline(
            id="",
            name="Test",
            due_at_t_seconds=100,
            failure_consequence="Bad things",
            visibility="explicit"
        )


def test_deadline_empty_name_rejected():
    """Deadline should reject empty name."""
    with pytest.raises(ValueError, match="name cannot be empty"):
        Deadline(
            id="test",
            name="",
            due_at_t_seconds=100,
            failure_consequence="Bad things",
            visibility="explicit"
        )


def test_deadline_negative_time_rejected():
    """Deadline should reject negative due time."""
    with pytest.raises(ValueError, match="due_at_t_seconds must be >= 0"):
        Deadline(
            id="test",
            name="Test",
            due_at_t_seconds=-1,
            failure_consequence="Bad things",
            visibility="explicit"
        )


def test_deadline_invalid_visibility_rejected():
    """Deadline should reject invalid visibility."""
    with pytest.raises(ValueError, match="visibility must be one of"):
        Deadline(
            id="test",
            name="Test",
            due_at_t_seconds=100,
            failure_consequence="Bad things",
            visibility="invalid"
        )


def test_deadline_all_visibility_levels():
    """Deadline should accept all valid visibility levels."""
    visibilities: list[DeadlineVisibility] = ["hidden", "hinted", "explicit"]
    for vis in visibilities:
        deadline = Deadline(
            id=f"test_{vis}",
            name="Test",
            due_at_t_seconds=100,
            failure_consequence="Bad things",
            visibility=vis
        )
        assert deadline.visibility == vis


def test_deadline_with_citations():
    """Deadline should support citations."""
    deadline = Deadline(
        id="test",
        name="Test",
        due_at_t_seconds=100,
        failure_consequence="Bad things",
        visibility="explicit",
        citations=[{"source_id": "681f92bc94ff", "page": 42}]
    )

    assert len(deadline.citations) == 1
    assert deadline.citations[0]["page"] == 42


def test_deadline_serialization():
    """Deadline should serialize deterministically."""
    deadline = Deadline(
        id="guards_arrive",
        name="Guards Arrive",
        due_at_t_seconds=300,
        failure_consequence="Guards catch party in vault",
        visibility="hidden",
        citations=[{"source_id": "test", "page": 10}]
    )

    data = deadline.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = Deadline.from_dict(json.loads(json_str))

    assert restored.id == deadline.id
    assert restored.name == deadline.name
    assert restored.due_at_t_seconds == deadline.due_at_t_seconds
    assert restored.failure_consequence == deadline.failure_consequence
    assert restored.visibility == deadline.visibility
    assert restored.citations == deadline.citations


def test_deadline_serialization_omits_empty_citations():
    """Deadline serialization should omit empty citations."""
    deadline = Deadline(
        id="test",
        name="Test",
        due_at_t_seconds=100,
        failure_consequence="Bad things",
        visibility="explicit"
    )

    data = deadline.to_dict()
    # Should not have citations key if empty
    assert "citations" not in data


def test_timer_status_basic():
    """TimerStatus should track remaining time and expiry."""
    status = TimerStatus(remaining_seconds=100, is_expired=False)
    assert status.remaining_seconds == 100
    assert status.is_expired is False


def test_timer_status_expired():
    """TimerStatus should indicate expiry."""
    status = TimerStatus(remaining_seconds=-10, is_expired=True)
    assert status.remaining_seconds == -10
    assert status.is_expired is True


def test_timer_status_serialization():
    """TimerStatus should serialize deterministically."""
    status = TimerStatus(remaining_seconds=50, is_expired=False)
    data = status.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TimerStatus.from_dict(json.loads(json_str))

    assert restored.remaining_seconds == status.remaining_seconds
    assert restored.is_expired == status.is_expired


def test_timer_status_compute_not_expired():
    """TimerStatus.compute should calculate status for active deadline."""
    deadline = Deadline(
        id="test",
        name="Test",
        due_at_t_seconds=1000,
        failure_consequence="Bad",
        visibility="explicit"
    )

    status = TimerStatus.compute(current_t_seconds=500, deadline=deadline)

    assert status.remaining_seconds == 500
    assert status.is_expired is False


def test_timer_status_compute_expired():
    """TimerStatus.compute should indicate expiry when time passed."""
    deadline = Deadline(
        id="test",
        name="Test",
        due_at_t_seconds=1000,
        failure_consequence="Bad",
        visibility="explicit"
    )

    status = TimerStatus.compute(current_t_seconds=1500, deadline=deadline)

    assert status.remaining_seconds == -500
    assert status.is_expired is True


def test_timer_status_compute_exactly_expired():
    """TimerStatus.compute should indicate expiry at exact time."""
    deadline = Deadline(
        id="test",
        name="Test",
        due_at_t_seconds=1000,
        failure_consequence="Bad",
        visibility="explicit"
    )

    status = TimerStatus.compute(current_t_seconds=1000, deadline=deadline)

    assert status.remaining_seconds == 0
    assert status.is_expired is True  # Expired at exactly the due time


def test_deadline_roundtrip():
    """Deadline should roundtrip correctly."""
    original = Deadline(
        id="test_deadline",
        name="Test Deadline",
        due_at_t_seconds=5000,
        failure_consequence="Something bad happens",
        visibility="hinted",
        citations=[{"source_id": "abc123", "page": 99}]
    )

    data = original.to_dict()
    restored = Deadline.from_dict(data)

    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.due_at_t_seconds == original.due_at_t_seconds
    assert restored.failure_consequence == original.failure_consequence
    assert restored.visibility == original.visibility
    assert restored.citations == original.citations
