"""Tests for ruling helpers."""

import pytest
from aidm.core.ruling_helpers import make_rule_lookup_event
from aidm.core.rule_lookup import SearchHit


def test_rule_lookup_event_has_citations():
    """make_rule_lookup_event() should attach citations from hits."""
    hits = [
        SearchHit(
            source_id="681f92bc94ff",
            short_name="PHB",
            page=157,
            snippet="Grappling rules...",
            score=10.0
        ),
        SearchHit(
            source_id="fed77f68501d",
            short_name="DMG",
            page=42,
            snippet="Combat modifiers...",
            score=8.0
        ),
        SearchHit(
            source_id="e390dfd9143f",
            short_name="MM",
            page=100,
            snippet="Monster abilities...",
            score=5.0
        )
    ]

    event = make_rule_lookup_event(
        query="grapple",
        hits=hits,
        event_id=42,
        timestamp=1.0
    )

    # Check event structure
    assert event.event_id == 42
    assert event.event_type == "rule_lookup"
    assert event.timestamp == 1.0

    # Check payload
    assert event.payload["query"] == "grapple"
    assert event.payload["results_count"] == 3
    assert len(event.payload["top_sources"]) == 3

    # Check citations
    assert len(event.citations) == 3
    assert event.citations[0]["source_id"] == "681f92bc94ff"
    assert event.citations[0]["short_name"] == "PHB"
    assert event.citations[0]["page"] == 157

    assert event.citations[1]["source_id"] == "fed77f68501d"
    assert event.citations[1]["page"] == 42

    assert event.citations[2]["source_id"] == "e390dfd9143f"
    assert event.citations[2]["page"] == 100


def test_rule_lookup_event_respects_max_citations():
    """make_rule_lookup_event() should limit citations to max_citations."""
    hits = [
        SearchHit(
            source_id=f"source{i:012x}",
            short_name=f"S{i}",
            page=i,
            snippet=f"snippet {i}",
            score=float(10 - i)
        )
        for i in range(10)
    ]

    event = make_rule_lookup_event(
        query="test",
        hits=hits,
        event_id=1,
        timestamp=1.0,
        max_citations=2
    )

    # Should only have 2 citations
    assert len(event.citations) == 2
    assert event.payload["results_count"] == 10  # Full count in payload
    assert len(event.payload["top_sources"]) == 2  # But only top 2 summarized


def test_rule_lookup_event_empty_hits():
    """make_rule_lookup_event() should handle empty hits list."""
    event = make_rule_lookup_event(
        query="nonexistent",
        hits=[],
        event_id=1,
        timestamp=1.0
    )

    assert event.event_type == "rule_lookup"
    assert event.payload["query"] == "nonexistent"
    assert event.payload["results_count"] == 0
    assert len(event.payload["top_sources"]) == 0
    assert len(event.citations) == 0


def test_rule_lookup_event_payload_includes_scores():
    """make_rule_lookup_event() payload should include relevance scores."""
    hits = [
        SearchHit(
            source_id="681f92bc94ff",
            short_name="PHB",
            page=157,
            snippet="test",
            score=42.5
        )
    ]

    event = make_rule_lookup_event(
        query="test",
        hits=hits,
        event_id=1,
        timestamp=1.0
    )

    assert event.payload["top_sources"][0]["score"] == 42.5
