"""Tests for terrain schemas."""

import pytest
import json
from aidm.schemas.terrain import (
    TerrainTag,
    TraversalCheckType,
    TraversalRequirement
)


def test_terrain_tag_enum_values():
    """TerrainTag enum should have all terrain types."""
    assert TerrainTag.DIFFICULT_TERRAIN.value == "difficult_terrain"
    assert TerrainTag.SLIPPERY.value == "slippery"
    assert TerrainTag.MUDDY.value == "muddy"
    assert TerrainTag.SHALLOW_WATER.value == "shallow_water"
    assert TerrainTag.DEEP_WATER.value == "deep_water"
    assert TerrainTag.DENSE_FOREST.value == "dense_forest"
    assert TerrainTag.WALL_SMOOTH.value == "wall_smooth"
    assert TerrainTag.WALL_ROUGH.value == "wall_rough"
    assert TerrainTag.BLOCKING_SOLID.value == "blocking_solid"
    assert TerrainTag.HALF_COVER.value == "half_cover"
    assert TerrainTag.THREE_QUARTERS_COVER.value == "three_quarters_cover"


def test_traversal_check_type_literals():
    """TraversalCheckType literal should include all check types."""
    climb: TraversalCheckType = "climb"
    balance: TraversalCheckType = "balance"
    swim: TraversalCheckType = "swim"
    jump: TraversalCheckType = "jump"

    assert climb == "climb"
    assert swim == "swim"


def test_traversal_requirement_basic():
    """TraversalRequirement should be creatable with basic fields."""
    req = TraversalRequirement(
        check_type="climb",
        dc_base=15,
        dc_modifiers=[]
    )

    assert req.check_type == "climb"
    assert req.dc_base == 15
    assert req.citation is None


def test_traversal_requirement_with_modifiers():
    """TraversalRequirement should support DC modifiers."""
    req = TraversalRequirement(
        check_type="balance",
        dc_base=10,
        dc_modifiers=["slippery: +2", "rope: -5"]
    )

    assert len(req.dc_modifiers) == 2
    assert "slippery: +2" in req.dc_modifiers


def test_traversal_requirement_with_citation():
    """TraversalRequirement should support citation."""
    req = TraversalRequirement(
        check_type="swim",
        dc_base=15,
        dc_modifiers=["rough water: +5"],
        citation={"source_id": "681f92bc94ff", "page": 77}
    )

    assert req.citation is not None
    assert req.citation["page"] == 77


def test_traversal_requirement_serialization():
    """TraversalRequirement should serialize deterministically."""
    req = TraversalRequirement(
        check_type="climb",
        dc_base=20,
        dc_modifiers=["wet surface: +3"],
        citation={"source_id": "681f92bc94ff", "page": 69}
    )

    data = req.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TraversalRequirement.from_dict(json.loads(json_str))

    assert restored.check_type == req.check_type
    assert restored.dc_base == req.dc_base
    assert restored.dc_modifiers == req.dc_modifiers
    assert restored.citation == req.citation


def test_traversal_requirement_roundtrip():
    """TraversalRequirement should roundtrip correctly."""
    original = TraversalRequirement(
        check_type="jump",
        dc_base=12,
        dc_modifiers=["long distance: +5"],
        citation={"source_id": "681f92bc94ff", "page": 77}
    )

    data = original.to_dict()
    restored = TraversalRequirement.from_dict(data)

    assert restored.check_type == original.check_type
    assert restored.dc_base == original.dc_base
    assert restored.dc_modifiers == original.dc_modifiers
    assert restored.citation == original.citation


def test_traversal_requirement_to_dict_omits_none_citation():
    """TraversalRequirement.to_dict() should omit None citation."""
    req = TraversalRequirement(
        check_type="climb",
        dc_base=15,
        dc_modifiers=[]
    )

    data = req.to_dict()

    assert "check_type" in data
    assert "dc_base" in data
    assert "dc_modifiers" in data
    assert "citation" not in data  # Should be omitted when None


def test_traversal_requirement_from_dict_handles_missing_citation():
    """TraversalRequirement.from_dict() should handle missing citation."""
    data = {
        "check_type": "swim",
        "dc_base": 10,
        "dc_modifiers": []
    }

    req = TraversalRequirement.from_dict(data)

    assert req.citation is None


def test_traversal_requirement_deterministic_serialization():
    """TraversalRequirement serialization should be deterministic."""
    req = TraversalRequirement(
        check_type="balance",
        dc_base=15,
        dc_modifiers=["ice: +5", "pole: -2"]
    )

    json1 = json.dumps(req.to_dict(), sort_keys=True)
    json2 = json.dumps(req.to_dict(), sort_keys=True)

    assert json1 == json2
