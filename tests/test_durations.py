"""Tests for effect duration schemas."""

import pytest
import json
from aidm.schemas.durations import EffectDuration, DurationUnit


def test_effect_duration_rounds():
    """EffectDuration should support rounds unit."""
    effect = EffectDuration(
        unit="rounds",
        value=10,
        start_t_seconds=0
    )

    assert effect.unit == "rounds"
    assert effect.value == 10
    assert effect.start_t_seconds == 0


def test_effect_duration_minutes():
    """EffectDuration should support minutes unit."""
    effect = EffectDuration(
        unit="minutes",
        value=5,
        start_t_seconds=100
    )

    assert effect.unit == "minutes"
    assert effect.value == 5


def test_effect_duration_hours():
    """EffectDuration should support hours unit."""
    effect = EffectDuration(
        unit="hours",
        value=2,
        start_t_seconds=1000
    )

    assert effect.unit == "hours"
    assert effect.value == 2


def test_effect_duration_days():
    """EffectDuration should support days unit."""
    effect = EffectDuration(
        unit="days",
        value=1,
        start_t_seconds=5000
    )

    assert effect.unit == "days"
    assert effect.value == 1


def test_effect_duration_until_discharged():
    """EffectDuration should support until_discharged unit."""
    effect = EffectDuration(
        unit="until_discharged",
        value=None,
        start_t_seconds=0
    )

    assert effect.unit == "until_discharged"
    assert effect.value is None


def test_effect_duration_permanent():
    """EffectDuration should support permanent unit."""
    effect = EffectDuration(
        unit="permanent",
        value=None,
        start_t_seconds=0
    )

    assert effect.unit == "permanent"
    assert effect.value is None


def test_effect_duration_invalid_unit_rejected():
    """EffectDuration should reject invalid unit."""
    with pytest.raises(ValueError, match="unit must be one of"):
        EffectDuration(
            unit="invalid",
            value=10,
            start_t_seconds=0
        )


def test_effect_duration_time_unit_requires_value():
    """EffectDuration should require value for time-based units."""
    with pytest.raises(ValueError, match="value required for unit 'rounds'"):
        EffectDuration(
            unit="rounds",
            value=None,
            start_t_seconds=0
        )


def test_effect_duration_time_unit_zero_value_rejected():
    """EffectDuration should reject zero value for time-based units."""
    with pytest.raises(ValueError, match="value must be >= 1"):
        EffectDuration(
            unit="minutes",
            value=0,
            start_t_seconds=0
        )


def test_effect_duration_time_unit_negative_value_rejected():
    """EffectDuration should reject negative value for time-based units."""
    with pytest.raises(ValueError, match="value must be >= 1"):
        EffectDuration(
            unit="hours",
            value=-5,
            start_t_seconds=0
        )


def test_effect_duration_discharged_rejects_value():
    """EffectDuration should reject value for until_discharged."""
    with pytest.raises(ValueError, match="value must be None"):
        EffectDuration(
            unit="until_discharged",
            value=10,
            start_t_seconds=0
        )


def test_effect_duration_permanent_rejects_value():
    """EffectDuration should reject value for permanent."""
    with pytest.raises(ValueError, match="value must be None"):
        EffectDuration(
            unit="permanent",
            value=5,
            start_t_seconds=0
        )


def test_effect_duration_negative_start_time_rejected():
    """EffectDuration should reject negative start time."""
    with pytest.raises(ValueError, match="start_t_seconds must be >= 0"):
        EffectDuration(
            unit="rounds",
            value=10,
            start_t_seconds=-1
        )


def test_effect_duration_with_end_time():
    """EffectDuration should support computed end time."""
    effect = EffectDuration(
        unit="rounds",
        value=10,
        start_t_seconds=100,
        ends_at_t_seconds=160
    )

    assert effect.ends_at_t_seconds == 160


def test_effect_duration_end_before_start_rejected():
    """EffectDuration should reject end time before start time."""
    with pytest.raises(ValueError, match="ends_at_t_seconds.*must be >=.*start_t_seconds"):
        EffectDuration(
            unit="rounds",
            value=10,
            start_t_seconds=100,
            ends_at_t_seconds=50
        )


def test_effect_duration_with_citation():
    """EffectDuration should support citation."""
    effect = EffectDuration(
        unit="minutes",
        value=10,
        start_t_seconds=0,
        citation={"source_id": "681f92bc94ff", "page": 220}
    )

    assert effect.citation is not None
    assert effect.citation["page"] == 220


def test_effect_duration_serialization():
    """EffectDuration should serialize deterministically."""
    effect = EffectDuration(
        unit="hours",
        value=8,
        start_t_seconds=1000,
        ends_at_t_seconds=29800,
        citation={"source_id": "test", "page": 10}
    )

    data = effect.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = EffectDuration.from_dict(json.loads(json_str))

    assert restored.unit == effect.unit
    assert restored.value == effect.value
    assert restored.start_t_seconds == effect.start_t_seconds
    assert restored.ends_at_t_seconds == effect.ends_at_t_seconds
    assert restored.citation == effect.citation


def test_effect_duration_serialization_omits_none_fields():
    """EffectDuration serialization should omit None fields."""
    effect = EffectDuration(
        unit="rounds",
        value=5,
        start_t_seconds=0
    )

    data = effect.to_dict()

    assert "unit" in data
    assert "value" in data
    assert "start_t_seconds" in data
    assert "ends_at_t_seconds" not in data  # Should be omitted
    assert "citation" not in data  # Should be omitted


def test_effect_duration_compute_end_time_rounds():
    """compute_end_time should calculate end time for rounds."""
    end_time = EffectDuration.compute_end_time(
        start_t_seconds=100,
        unit="rounds",
        value=10
    )

    # 10 rounds * 6 seconds = 60 seconds
    assert end_time == 160


def test_effect_duration_compute_end_time_minutes():
    """compute_end_time should calculate end time for minutes."""
    end_time = EffectDuration.compute_end_time(
        start_t_seconds=0,
        unit="minutes",
        value=5
    )

    # 5 minutes * 60 seconds = 300 seconds
    assert end_time == 300


def test_effect_duration_compute_end_time_hours():
    """compute_end_time should calculate end time for hours."""
    end_time = EffectDuration.compute_end_time(
        start_t_seconds=1000,
        unit="hours",
        value=2
    )

    # 2 hours * 3600 seconds = 7200 seconds
    assert end_time == 8200


def test_effect_duration_compute_end_time_days():
    """compute_end_time should calculate end time for days."""
    end_time = EffectDuration.compute_end_time(
        start_t_seconds=0,
        unit="days",
        value=1
    )

    # 1 day * 86400 seconds = 86400 seconds
    assert end_time == 86400


def test_effect_duration_compute_end_time_until_discharged():
    """compute_end_time should return None for until_discharged."""
    end_time = EffectDuration.compute_end_time(
        start_t_seconds=0,
        unit="until_discharged",
        value=1  # Value ignored for this unit
    )

    assert end_time is None


def test_effect_duration_compute_end_time_permanent():
    """compute_end_time should return None for permanent."""
    end_time = EffectDuration.compute_end_time(
        start_t_seconds=0,
        unit="permanent",
        value=1  # Value ignored for this unit
    )

    assert end_time is None


def test_effect_duration_roundtrip():
    """EffectDuration should roundtrip correctly."""
    original = EffectDuration(
        unit="minutes",
        value=10,
        start_t_seconds=500,
        ends_at_t_seconds=1100,
        citation={"source_id": "abc123", "page": 42}
    )

    data = original.to_dict()
    restored = EffectDuration.from_dict(data)

    assert restored.unit == original.unit
    assert restored.value == original.value
    assert restored.start_t_seconds == original.start_t_seconds
    assert restored.ends_at_t_seconds == original.ends_at_t_seconds
    assert restored.citation == original.citation
