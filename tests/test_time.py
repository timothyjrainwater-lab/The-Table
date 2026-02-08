"""Tests for temporal schemas (time tracking and clocks)."""

import pytest
import json
from aidm.schemas.time import (
    TimeScale,
    TimeScaleLiteral,
    TimeSpan,
    GameClock,
    TimeAdvanceEvent,
    ROUND,
    MINUTE,
    HOUR,
    DAY
)


def test_time_scale_enum():
    """TimeScale enum should have expected values."""
    assert TimeScale.COMBAT_ROUND.value == "combat_round"
    assert TimeScale.NARRATIVE.value == "narrative"
    assert TimeScale.EXPLORATION.value == "exploration"


def test_time_span_basic():
    """TimeSpan should store seconds >= 0."""
    span = TimeSpan(seconds=100)
    assert span.seconds == 100


def test_time_span_zero_allowed():
    """TimeSpan should allow zero seconds."""
    span = TimeSpan(seconds=0)
    assert span.seconds == 0


def test_time_span_negative_rejected():
    """TimeSpan should reject negative seconds."""
    with pytest.raises(ValueError, match="seconds must be >= 0"):
        TimeSpan(seconds=-1)


def test_time_span_serialization():
    """TimeSpan should serialize deterministically."""
    span = TimeSpan(seconds=42)
    data = span.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TimeSpan.from_dict(json.loads(json_str))

    assert restored.seconds == span.seconds


def test_time_span_constants():
    """Common time span constants should be available."""
    assert ROUND.seconds == 6
    assert MINUTE.seconds == 60
    assert HOUR.seconds == 3600
    assert DAY.seconds == 86400


def test_game_clock_basic():
    """GameClock should store time and scale."""
    clock = GameClock(t_seconds=100, scale="combat_round")
    assert clock.t_seconds == 100
    assert clock.scale == "combat_round"


def test_game_clock_zero_time():
    """GameClock should allow zero time."""
    clock = GameClock(t_seconds=0, scale="narrative")
    assert clock.t_seconds == 0


def test_game_clock_negative_time_rejected():
    """GameClock should reject negative time."""
    with pytest.raises(ValueError, match="t_seconds must be >= 0"):
        GameClock(t_seconds=-1, scale="combat_round")


def test_game_clock_invalid_scale_rejected():
    """GameClock should reject invalid scale."""
    with pytest.raises(ValueError, match="scale must be one of"):
        GameClock(t_seconds=0, scale="invalid_scale")


def test_game_clock_all_scales():
    """GameClock should accept all valid scales."""
    scales: list[TimeScaleLiteral] = ["combat_round", "narrative", "exploration"]
    for scale in scales:
        clock = GameClock(t_seconds=0, scale=scale)
        assert clock.scale == scale


def test_game_clock_serialization():
    """GameClock should serialize deterministically."""
    clock = GameClock(t_seconds=500, scale="exploration")
    data = clock.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = GameClock.from_dict(json.loads(json_str))

    assert restored.t_seconds == clock.t_seconds
    assert restored.scale == clock.scale


def test_time_advance_event_basic():
    """TimeAdvanceEvent should store delta, reason, and scale."""
    delta = TimeSpan(seconds=60)
    event = TimeAdvanceEvent(
        delta=delta,
        reason="talked_to_shopkeeper",
        scale="narrative"
    )

    assert event.delta.seconds == 60
    assert event.reason == "talked_to_shopkeeper"
    assert event.scale == "narrative"


def test_time_advance_event_serialization():
    """TimeAdvanceEvent should serialize deterministically."""
    delta = TimeSpan(seconds=120)
    event = TimeAdvanceEvent(
        delta=delta,
        reason="traveled_overland",
        scale="exploration"
    )

    data = event.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TimeAdvanceEvent.from_dict(json.loads(json_str))

    assert restored.delta.seconds == event.delta.seconds
    assert restored.reason == event.reason
    assert restored.scale == event.scale


def test_time_advance_event_with_round_delta():
    """TimeAdvanceEvent should work with ROUND constant."""
    event = TimeAdvanceEvent(
        delta=ROUND,
        reason="combat_round_passed",
        scale="combat_round"
    )

    assert event.delta.seconds == 6
    assert event.scale == "combat_round"


def test_time_advance_event_roundtrip():
    """TimeAdvanceEvent should roundtrip correctly."""
    original = TimeAdvanceEvent(
        delta=TimeSpan(seconds=3600),
        reason="long_rest",
        scale="narrative"
    )

    data = original.to_dict()
    restored = TimeAdvanceEvent.from_dict(data)

    assert restored.delta.seconds == original.delta.seconds
    assert restored.reason == original.reason
    assert restored.scale == original.scale


def test_game_clock_monotonic_invariant():
    """GameClock represents monotonic time (validation check)."""
    # This is enforced by validation, not the schema itself
    clock1 = GameClock(t_seconds=100, scale="combat_round")
    clock2 = GameClock(t_seconds=106, scale="combat_round")

    assert clock2.t_seconds > clock1.t_seconds
