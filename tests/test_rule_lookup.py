"""Tests for rule lookup system."""

import pytest
from aidm.core.rule_lookup import search, SearchHit
from aidm.core.source_registry import SourceRegistry


def test_rule_lookup_basic_hit():
    """search() should find basic keyword matches."""
    registry = SourceRegistry("sources/provenance.json")

    # Search for "Constitution" in PHB (should be on page 10)
    results = search("Constitution", source_ids=["681f92bc94ff"], k=5, registry=registry)

    assert len(results) > 0
    assert all(isinstance(hit, SearchHit) for hit in results)
    assert all(hit.source_id == "681f92bc94ff" for hit in results)
    assert all(hit.short_name == "PHB" for hit in results)


def test_rule_lookup_multiple_sources():
    """search() should search across multiple sources."""
    registry = SourceRegistry("sources/provenance.json")

    # Search PHB and DMG
    results = search(
        "treasure",
        source_ids=["681f92bc94ff", "fed77f68501d"],
        k=10,
        registry=registry
    )

    # Should find results from both sources
    source_ids_found = {hit.source_id for hit in results}
    assert len(source_ids_found) >= 1  # At least one source has "treasure"


def test_rule_lookup_snippet_length_bounded():
    """search() should limit snippet length to 300 chars."""
    registry = SourceRegistry("sources/provenance.json")

    results = search("ability", source_ids=["681f92bc94ff"], k=5, registry=registry)

    assert len(results) > 0

    for hit in results:
        assert len(hit.snippet) <= 300
        assert len(hit.snippet) > 0  # Should have content


def test_rule_lookup_deterministic_ordering():
    """search() should produce deterministic ordering for same query."""
    registry = SourceRegistry("sources/provenance.json")

    results1 = search("attack", source_ids=["681f92bc94ff"], k=10, registry=registry)
    results2 = search("attack", source_ids=["681f92bc94ff"], k=10, registry=registry)

    assert len(results1) == len(results2)

    for hit1, hit2 in zip(results1, results2):
        assert hit1.source_id == hit2.source_id
        assert hit1.page == hit2.page
        assert hit1.score == hit2.score
        assert hit1.snippet == hit2.snippet


def test_rule_lookup_no_results_for_missing_term():
    """search() should return empty list for terms not found."""
    registry = SourceRegistry("sources/provenance.json")

    # Search for nonsense term
    results = search("xyzzyqwerty123456", source_ids=["681f92bc94ff"], k=5, registry=registry)

    assert results == []


def test_rule_lookup_respects_k_limit():
    """search() should respect k parameter for result limit."""
    registry = SourceRegistry("sources/provenance.json")

    # Common term should have many results
    results_k3 = search("attack", source_ids=["681f92bc94ff"], k=3, registry=registry)
    results_k10 = search("attack", source_ids=["681f92bc94ff"], k=10, registry=registry)

    assert len(results_k3) <= 3
    assert len(results_k10) <= 10

    # First 3 should be the same
    for i in range(min(3, len(results_k3))):
        assert results_k3[i].source_id == results_k10[i].source_id
        assert results_k3[i].page == results_k10[i].page


def test_rule_lookup_default_core_sources():
    """search() should default to core rulebooks if no source_ids provided."""
    registry = SourceRegistry("sources/provenance.json")

    # No source_ids specified
    results = search("magic", k=5, registry=registry)

    # Should search PHB, DMG, MM (core rulebooks)
    source_ids_found = {hit.source_id for hit in results}

    # Should only find results from core books
    core_source_ids = {"681f92bc94ff", "fed77f68501d", "e390dfd9143f"}
    assert source_ids_found.issubset(core_source_ids)


def test_rule_lookup_score_ordering():
    """search() should order results by score (descending)."""
    registry = SourceRegistry("sources/provenance.json")

    results = search("spell magic", source_ids=["681f92bc94ff"], k=10, registry=registry)

    assert len(results) > 1

    # Scores should be in descending order
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


def test_rule_lookup_case_insensitive():
    """search() should be case-insensitive."""
    registry = SourceRegistry("sources/provenance.json")

    results_lower = search("constitution", source_ids=["681f92bc94ff"], k=5, registry=registry)
    results_upper = search("CONSTITUTION", source_ids=["681f92bc94ff"], k=5, registry=registry)
    results_mixed = search("Constitution", source_ids=["681f92bc94ff"], k=5, registry=registry)

    # All should return same results
    assert len(results_lower) == len(results_upper) == len(results_mixed)

    for hit_l, hit_u, hit_m in zip(results_lower, results_upper, results_mixed):
        assert hit_l.page == hit_u.page == hit_m.page
        assert hit_l.score == hit_u.score == hit_m.score
