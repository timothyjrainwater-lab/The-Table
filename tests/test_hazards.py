"""Tests for environmental hazard schemas."""

import pytest
import json
from aidm.schemas.hazards import (
    HazardIntervalUnit,
    HazardEffectType,
    EnvironmentalHazard,
    HazardStage,
    HazardProgression
)


def test_hazard_interval_unit_enum():
    """HazardIntervalUnit should have all time units."""
    assert HazardIntervalUnit.ROUND.value == "round"
    assert HazardIntervalUnit.MINUTE.value == "minute"
    assert HazardIntervalUnit.HOUR.value == "hour"
    assert HazardIntervalUnit.DAY.value == "day"


def test_hazard_effect_type_enum():
    """HazardEffectType should have all effect types."""
    assert HazardEffectType.DAMAGE.value == "damage"
    assert HazardEffectType.CONDITION.value == "condition"
    assert HazardEffectType.VISIBILITY.value == "visibility"
    assert HazardEffectType.MIXED.value == "mixed"


def test_environmental_hazard_basic():
    """EnvironmentalHazard should store basic hazard data."""
    hazard = EnvironmentalHazard(
        id="forest_fire",
        name="Forest Fire",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="1d6 fire damage per round"
    )

    assert hazard.id == "forest_fire"
    assert hazard.name == "Forest Fire"
    assert hazard.interval_unit == "round"
    assert hazard.interval_value == 1
    assert hazard.effect_type == "damage"
    assert hazard.escalates is False


def test_environmental_hazard_empty_id_rejected():
    """EnvironmentalHazard should reject empty id."""
    with pytest.raises(ValueError, match="id cannot be empty"):
        EnvironmentalHazard(
            id="",
            name="Test",
            interval_unit="round",
            interval_value=1,
            effect_type="damage",
            description="test"
        )


def test_environmental_hazard_empty_name_rejected():
    """EnvironmentalHazard should reject empty name."""
    with pytest.raises(ValueError, match="name cannot be empty"):
        EnvironmentalHazard(
            id="test",
            name="",
            interval_unit="round",
            interval_value=1,
            effect_type="damage",
            description="test"
        )


def test_environmental_hazard_invalid_interval_unit_rejected():
    """EnvironmentalHazard should reject invalid interval_unit."""
    with pytest.raises(ValueError, match="interval_unit must be one of"):
        EnvironmentalHazard(
            id="test",
            name="Test",
            interval_unit="invalid",
            interval_value=1,
            effect_type="damage",
            description="test"
        )


def test_environmental_hazard_zero_interval_value_rejected():
    """EnvironmentalHazard should reject interval_value < 1."""
    with pytest.raises(ValueError, match="interval_value must be >= 1"):
        EnvironmentalHazard(
            id="test",
            name="Test",
            interval_unit="round",
            interval_value=0,
            effect_type="damage",
            description="test"
        )


def test_environmental_hazard_invalid_effect_type_rejected():
    """EnvironmentalHazard should reject invalid effect_type."""
    with pytest.raises(ValueError, match="effect_type must be one of"):
        EnvironmentalHazard(
            id="test",
            name="Test",
            interval_unit="round",
            interval_value=1,
            effect_type="invalid",
            description="test"
        )


def test_environmental_hazard_with_escalation():
    """EnvironmentalHazard should support escalation."""
    hazard = EnvironmentalHazard(
        id="suffocation",
        name="Suffocation",
        interval_unit="round",
        interval_value=1,
        effect_type="condition",
        description="Escalating suffocation stages",
        escalates=True,
        max_stages=3
    )

    assert hazard.escalates is True
    assert hazard.max_stages == 3


def test_environmental_hazard_max_stages_validation():
    """EnvironmentalHazard should validate max_stages when escalates=True."""
    with pytest.raises(ValueError, match="max_stages must be >= 1"):
        EnvironmentalHazard(
            id="test",
            name="Test",
            interval_unit="round",
            interval_value=1,
            effect_type="damage",
            description="test",
            escalates=True,
            max_stages=0
        )


def test_environmental_hazard_with_visibility_tags():
    """EnvironmentalHazard should support visibility tags."""
    hazard = EnvironmentalHazard(
        id="smoke",
        name="Smoke",
        interval_unit="round",
        interval_value=1,
        effect_type="mixed",
        description="Smoke damage and concealment",
        visibility_tags=["heavy_obscurement"]
    )

    assert "heavy_obscurement" in hazard.visibility_tags


def test_environmental_hazard_with_terrain_tags():
    """EnvironmentalHazard should support terrain tags."""
    hazard = EnvironmentalHazard(
        id="ice",
        name="Ice",
        interval_unit="round",
        interval_value=1,
        effect_type="condition",
        description="Slippery ice",
        terrain_tags=["slippery", "difficult_terrain"]
    )

    assert "slippery" in hazard.terrain_tags
    assert "difficult_terrain" in hazard.terrain_tags


def test_environmental_hazard_with_citation():
    """EnvironmentalHazard should support citation."""
    hazard = EnvironmentalHazard(
        id="lava",
        name="Lava",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="20d6 fire damage",
        citation={"source_id": "fed77f68501d", "page": 304}
    )

    assert hazard.citation is not None
    assert hazard.citation["page"] == 304


def test_environmental_hazard_serialization():
    """EnvironmentalHazard should serialize deterministically."""
    hazard = EnvironmentalHazard(
        id="cold",
        name="Extreme Cold",
        interval_unit="hour",
        interval_value=1,
        effect_type="damage",
        description="1d6 cold damage per hour",
        citation={"source_id": "fed77f68501d", "page": 303}
    )

    data = hazard.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = EnvironmentalHazard.from_dict(json.loads(json_str))

    assert restored.id == hazard.id
    assert restored.name == hazard.name
    assert restored.interval_unit == hazard.interval_unit
    assert restored.interval_value == hazard.interval_value
    assert restored.effect_type == hazard.effect_type


def test_environmental_hazard_serialization_omits_none_fields():
    """EnvironmentalHazard serialization should omit None/empty fields."""
    hazard = EnvironmentalHazard(
        id="test",
        name="Test",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="test"
    )

    data = hazard.to_dict()

    assert "id" in data
    assert "escalates" in data
    assert "max_stages" not in data  # Should be omitted
    assert "citation" not in data  # Should be omitted


def test_hazard_stage_basic():
    """HazardStage should store stage data."""
    stage = HazardStage(
        stage_index=0,
        notes="Nonlethal damage"
    )

    assert stage.stage_index == 0
    assert stage.notes == "Nonlethal damage"
    assert stage.citation is None


def test_hazard_stage_negative_index_rejected():
    """HazardStage should reject negative stage_index."""
    with pytest.raises(ValueError, match="stage_index must be >= 0"):
        HazardStage(
            stage_index=-1,
            notes="test"
        )


def test_hazard_stage_empty_notes_rejected():
    """HazardStage should reject empty notes."""
    with pytest.raises(ValueError, match="notes cannot be empty"):
        HazardStage(
            stage_index=0,
            notes=""
        )


def test_hazard_stage_with_citation():
    """HazardStage should support citation."""
    stage = HazardStage(
        stage_index=1,
        notes="Lethal damage begins",
        citation={"source_id": "681f92bc94ff", "page": 304}
    )

    assert stage.citation is not None
    assert stage.citation["page"] == 304


def test_hazard_stage_serialization():
    """HazardStage should serialize deterministically."""
    stage = HazardStage(
        stage_index=2,
        notes="Unconsciousness",
        citation={"source_id": "test", "page": 10}
    )

    data = stage.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = HazardStage.from_dict(json.loads(json_str))

    assert restored.stage_index == stage.stage_index
    assert restored.notes == stage.notes
    assert restored.citation == stage.citation


def test_hazard_progression_basic():
    """HazardProgression should store progression data."""
    progression = HazardProgression(
        hazard_id="suffocation",
        stages=[
            HazardStage(stage_index=0, notes="Holding breath"),
            HazardStage(stage_index=1, notes="Nonlethal damage")
        ]
    )

    assert progression.hazard_id == "suffocation"
    assert len(progression.stages) == 2


def test_hazard_progression_empty_hazard_id_rejected():
    """HazardProgression should reject empty hazard_id."""
    with pytest.raises(ValueError, match="hazard_id cannot be empty"):
        HazardProgression(
            hazard_id="",
            stages=[HazardStage(stage_index=0, notes="test")]
        )


def test_hazard_progression_empty_stages_rejected():
    """HazardProgression should reject empty stages."""
    with pytest.raises(ValueError, match="stages cannot be empty"):
        HazardProgression(
            hazard_id="test",
            stages=[]
        )


def test_hazard_progression_non_increasing_indices_rejected():
    """HazardProgression should reject non-increasing stage indices."""
    with pytest.raises(ValueError, match="must be strictly increasing"):
        HazardProgression(
            hazard_id="test",
            stages=[
                HazardStage(stage_index=0, notes="stage 0"),
                HazardStage(stage_index=0, notes="stage 0 again")
            ]
        )


def test_hazard_progression_decreasing_indices_rejected():
    """HazardProgression should reject decreasing stage indices."""
    with pytest.raises(ValueError, match="must be strictly increasing"):
        HazardProgression(
            hazard_id="test",
            stages=[
                HazardStage(stage_index=2, notes="stage 2"),
                HazardStage(stage_index=1, notes="stage 1")
            ]
        )


def test_hazard_progression_serialization():
    """HazardProgression should serialize deterministically."""
    progression = HazardProgression(
        hazard_id="starvation",
        stages=[
            HazardStage(stage_index=0, notes="Hungry"),
            HazardStage(stage_index=1, notes="Starving"),
            HazardStage(stage_index=2, notes="Critical")
        ]
    )

    data = progression.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = HazardProgression.from_dict(json.loads(json_str))

    assert restored.hazard_id == progression.hazard_id
    assert len(restored.stages) == len(progression.stages)
    for i, stage in enumerate(progression.stages):
        assert restored.stages[i].stage_index == stage.stage_index
        assert restored.stages[i].notes == stage.notes


def test_hazard_progression_roundtrip():
    """HazardProgression should roundtrip correctly."""
    original = HazardProgression(
        hazard_id="drowning",
        stages=[
            HazardStage(stage_index=0, notes="Holding breath", citation={"source_id": "test", "page": 1}),
            HazardStage(stage_index=1, notes="Drowning", citation={"source_id": "test", "page": 2})
        ]
    )

    data = original.to_dict()
    restored = HazardProgression.from_dict(data)

    assert restored.hazard_id == original.hazard_id
    assert len(restored.stages) == len(original.stages)
    for i in range(len(original.stages)):
        assert restored.stages[i].stage_index == original.stages[i].stage_index
        assert restored.stages[i].notes == original.stages[i].notes
        assert restored.stages[i].citation == original.stages[i].citation
