"""Tests for exposure and environmental condition schemas."""

import pytest
import json
from aidm.schemas.exposure import (
    ExposureType,
    EnvironmentalCondition
)


def test_exposure_type_enum():
    """ExposureType should have all exposure types."""
    assert ExposureType.HEAT.value == "heat"
    assert ExposureType.COLD.value == "cold"
    assert ExposureType.SMOKE.value == "smoke"
    assert ExposureType.TOXIC_FUMES.value == "toxic_fumes"
    assert ExposureType.SUFFOCATION.value == "suffocation"
    assert ExposureType.DROWNING.value == "drowning"


def test_environmental_condition_basic():
    """EnvironmentalCondition should store condition data."""
    condition = EnvironmentalCondition(
        type="heat",
        hazard_ref="extreme_heat",
        notes="Desert heat"
    )

    assert condition.type == "heat"
    assert condition.hazard_ref == "extreme_heat"
    assert condition.notes == "Desert heat"
    assert condition.mitigation_sources == []


def test_environmental_condition_invalid_type_rejected():
    """EnvironmentalCondition should reject invalid type."""
    with pytest.raises(ValueError, match="type must be one of"):
        EnvironmentalCondition(
            type="invalid",
            hazard_ref="test"
        )


def test_environmental_condition_empty_hazard_ref_rejected():
    """EnvironmentalCondition should reject empty hazard_ref."""
    with pytest.raises(ValueError, match="hazard_ref cannot be empty"):
        EnvironmentalCondition(
            type="heat",
            hazard_ref=""
        )


def test_environmental_condition_with_mitigation():
    """EnvironmentalCondition should support mitigation sources."""
    condition = EnvironmentalCondition(
        type="cold",
        hazard_ref="extreme_cold",
        mitigation_sources=["cold weather gear", "endure elements spell"]
    )

    assert len(condition.mitigation_sources) == 2
    assert "cold weather gear" in condition.mitigation_sources
    assert "endure elements spell" in condition.mitigation_sources


def test_environmental_condition_with_citation():
    """EnvironmentalCondition should support citation."""
    condition = EnvironmentalCondition(
        type="smoke",
        hazard_ref="thick_smoke",
        citation={"source_id": "fed77f68501d", "page": 304}
    )

    assert condition.citation is not None
    assert condition.citation["page"] == 304


def test_environmental_condition_serialization():
    """EnvironmentalCondition should serialize deterministically."""
    condition = EnvironmentalCondition(
        type="toxic_fumes",
        hazard_ref="poison_gas",
        mitigation_sources=["gas mask", "neutralize poison"],
        notes="Requires Fortitude save",
        citation={"source_id": "test", "page": 10}
    )

    data = condition.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = EnvironmentalCondition.from_dict(json.loads(json_str))

    assert restored.type == condition.type
    assert restored.hazard_ref == condition.hazard_ref
    assert restored.mitigation_sources == condition.mitigation_sources
    assert restored.notes == condition.notes
    assert restored.citation == condition.citation


def test_environmental_condition_serialization_omits_none_citation():
    """EnvironmentalCondition serialization should omit None citation."""
    condition = EnvironmentalCondition(
        type="drowning",
        hazard_ref="underwater"
    )

    data = condition.to_dict()

    assert "type" in data
    assert "hazard_ref" in data
    assert "mitigation_sources" in data
    assert "notes" in data
    assert "citation" not in data  # Should be omitted


def test_environmental_condition_roundtrip():
    """EnvironmentalCondition should roundtrip correctly."""
    original = EnvironmentalCondition(
        type="suffocation",
        hazard_ref="airless_room",
        mitigation_sources=["air supply", "water breathing"],
        notes="No air available",
        citation={"source_id": "681f92bc94ff", "page": 304}
    )

    data = original.to_dict()
    restored = EnvironmentalCondition.from_dict(data)

    assert restored.type == original.type
    assert restored.hazard_ref == original.hazard_ref
    assert restored.mitigation_sources == original.mitigation_sources
    assert restored.notes == original.notes
    assert restored.citation == original.citation


def test_environmental_condition_all_exposure_types():
    """EnvironmentalCondition should accept all valid exposure types."""
    types = ["heat", "cold", "smoke", "toxic_fumes", "suffocation", "drowning"]

    for exp_type in types:
        condition = EnvironmentalCondition(
            type=exp_type,
            hazard_ref="test_hazard"
        )
        assert condition.type == exp_type


def test_environmental_condition_empty_notes_allowed():
    """EnvironmentalCondition should allow empty notes."""
    condition = EnvironmentalCondition(
        type="heat",
        hazard_ref="test",
        notes=""
    )

    assert condition.notes == ""


def test_environmental_condition_empty_mitigation_allowed():
    """EnvironmentalCondition should allow empty mitigation_sources."""
    condition = EnvironmentalCondition(
        type="cold",
        hazard_ref="test",
        mitigation_sources=[]
    )

    assert condition.mitigation_sources == []
