"""Tests for Citation schema."""

import pytest
import json
from aidm.schemas.citation import Citation, build_citation
from aidm.core.rule_lookup import SearchHit


def test_citation_creation_minimal():
    """Citation should be creatable with just source_id."""
    citation = Citation(source_id="681f92bc94ff")

    assert citation.source_id == "681f92bc94ff"
    assert citation.short_name is None
    assert citation.page is None


def test_citation_creation_full():
    """Citation should support all optional fields."""
    citation = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=10,
        span="Constitution section",
        rule_id="ability_scores.constitution",
        obsidian_uri="obsidian://vault/Rule%20%E2%80%94%20Constitution"
    )

    assert citation.source_id == "681f92bc94ff"
    assert citation.short_name == "PHB"
    assert citation.page == 10
    assert citation.span == "Constitution section"
    assert citation.rule_id == "ability_scores.constitution"
    assert citation.obsidian_uri is not None


def test_citation_json_roundtrip():
    """Citation should serialize and deserialize correctly."""
    original = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=157,
        span="Grapple rules"
    )

    # To dict
    data = original.to_dict()

    assert data["source_id"] == "681f92bc94ff"
    assert data["short_name"] == "PHB"
    assert data["page"] == 157
    assert data["span"] == "Grapple rules"

    # Stable key ordering check (source_id first)
    keys = list(data.keys())
    assert keys[0] == "source_id"

    # JSON roundtrip
    json_str = json.dumps(data, sort_keys=True)
    restored_data = json.loads(json_str)

    # From dict
    restored = Citation.from_dict(restored_data)

    assert restored.source_id == original.source_id
    assert restored.short_name == original.short_name
    assert restored.page == original.page
    assert restored.span == original.span


def test_citation_to_dict_omits_none_fields():
    """Citation.to_dict should only include non-None fields."""
    citation = Citation(source_id="681f92bc94ff", page=10)

    data = citation.to_dict()

    assert "source_id" in data
    assert "page" in data
    assert "short_name" not in data  # None, should be omitted
    assert "span" not in data
    assert "rule_id" not in data
    assert "obsidian_uri" not in data


def test_citation_str_with_short_name():
    """Citation __str__ should produce readable format with short name."""
    citation = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=157,
        span="Grapple"
    )

    result = str(citation)

    assert "PHB" in result
    assert "p. 157" in result
    assert "Grapple" in result


def test_citation_str_without_short_name():
    """Citation __str__ should use abbreviated sourceId if no short name."""
    citation = Citation(
        source_id="681f92bc94ff",
        page=157
    )

    result = str(citation)

    assert "681f92bc" in result  # First 8 chars
    assert "p. 157" in result


def test_citation_str_minimal():
    """Citation __str__ should work with only source_id."""
    citation = Citation(source_id="681f92bc94ff")

    result = str(citation)

    assert "681f92bc" in result


def test_citation_from_dict_minimal():
    """Citation.from_dict should work with minimal data."""
    data = {"source_id": "681f92bc94ff"}

    citation = Citation.from_dict(data)

    assert citation.source_id == "681f92bc94ff"
    assert citation.short_name is None
    assert citation.page is None


def test_citation_json_serialization_deterministic():
    """Citation JSON serialization should be deterministic."""
    citation = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=157,
        span="Grapple"
    )

    # Serialize multiple times
    json1 = json.dumps(citation.to_dict(), sort_keys=True)
    json2 = json.dumps(citation.to_dict(), sort_keys=True)

    assert json1 == json2  # Must be identical


def test_build_citation_from_searchhit():
    """build_citation() should convert SearchHit to Citation."""
    hit = SearchHit(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=157,
        snippet="Grappling rules apply when...",
        score=42.0
    )

    citation = build_citation(hit)

    assert citation.source_id == "681f92bc94ff"
    assert citation.short_name == "PHB"
    assert citation.page == 157
    assert citation.span is None  # Not included in SearchHit
    assert citation.rule_id is None
    assert citation.obsidian_uri is None

