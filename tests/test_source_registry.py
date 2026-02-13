"""Tests for SourceRegistry."""

import pytest
from pathlib import Path
from aidm.core.source_registry import (
    SourceRegistry,
    SourceNotFoundError,
    TextNotAvailableError,
    PageNotFoundError
)


def test_source_registry_loads():
    """SourceRegistry should load provenance.json successfully."""
    registry = SourceRegistry("sources/provenance.json")

    assert len(registry) == 647
    assert "681f92bc94ff" in registry  # PHB
    assert "fed77f68501d" in registry  # DMG
    assert "e390dfd9143f" in registry  # MM


def test_source_registry_get_source():
    """SourceRegistry should retrieve source metadata by ID."""
    registry = SourceRegistry("sources/provenance.json")

    phb = registry.get_source("681f92bc94ff")

    assert phb["title"] == "Player's Handbook"
    assert phb["short_name"] == "PHB"
    assert phb["pages"] == 322
    assert phb["text_extracted"] is True
    assert phb["reuse_decision"] == "reuse_strong"


def test_source_registry_get_source_not_found():
    """SourceRegistry should raise SourceNotFoundError for invalid ID."""
    registry = SourceRegistry("sources/provenance.json")

    with pytest.raises(SourceNotFoundError, match="nonexistent"):
        registry.get_source("nonexistent123")


def test_source_registry_reads_phb_page_10_nonempty():
    """SourceRegistry should read PHB page 10 with non-empty content."""
    registry = SourceRegistry("sources/provenance.json")

    page_10 = registry.get_text_page("681f92bc94ff", 10)

    assert len(page_10) > 0
    assert "Constitution" in page_10 or "Dexterity" in page_10  # Page 10 is abilities section


def test_source_registry_get_text_page_core_rulebooks():
    """SourceRegistry should read pages from all core rulebooks."""
    registry = SourceRegistry("sources/provenance.json")

    # PHB page 1
    phb_page_1 = registry.get_text_page("681f92bc94ff", 1)
    assert len(phb_page_1) > 0

    # DMG page 1
    dmg_page_1 = registry.get_text_page("fed77f68501d", 1)
    assert len(dmg_page_1) > 0

    # MM page 1
    mm_page_1 = registry.get_text_page("e390dfd9143f", 1)
    assert len(mm_page_1) > 0


def test_source_registry_text_not_available():
    """SourceRegistry should raise TextNotAvailableError for sources without text."""
    registry = SourceRegistry("sources/provenance.json")

    # Find a source without extracted text
    source_without_text = None
    for source_id, source in registry.sources.items():
        if not source.get("text_extracted"):
            source_without_text = source_id
            break

    assert source_without_text is not None, "Should have sources without extracted text"

    with pytest.raises(TextNotAvailableError):
        registry.get_text_page(source_without_text, 1)


def test_source_registry_page_not_found():
    """SourceRegistry should raise PageNotFoundError for invalid page number."""
    registry = SourceRegistry("sources/provenance.json")

    # PHB has 322 pages, page 999 doesn't exist
    with pytest.raises(PageNotFoundError, match="Page 999"):
        registry.get_text_page("681f92bc94ff", 999)


def test_source_registry_invalid_page_number():
    """SourceRegistry should raise ValueError for page numbers < 1."""
    registry = SourceRegistry("sources/provenance.json")

    with pytest.raises(ValueError, match="must be >= 1"):
        registry.get_text_page("681f92bc94ff", 0)

    with pytest.raises(ValueError, match="must be >= 1"):
        registry.get_text_page("681f92bc94ff", -1)


def test_source_registry_list_sources_with_text():
    """SourceRegistry should list all sources with extracted text."""
    registry = SourceRegistry("sources/provenance.json")

    sources_with_text = registry.list_sources_with_text()

    assert len(sources_with_text) >= 3  # At least PHB, DMG, MM
    assert all(s["text_extracted"] for s in sources_with_text)


def test_source_registry_list_core_sources():
    """SourceRegistry should list core rulebooks."""
    registry = SourceRegistry("sources/provenance.json")

    core_sources = registry.list_core_sources()

    assert len(core_sources) >= 3  # At least PHB, DMG, MM
    assert any(s.get("short_name") == "PHB" for s in core_sources)
    assert any(s.get("short_name") == "DMG" for s in core_sources)
    assert any(s.get("short_name") == "MM" for s in core_sources)


def test_source_registry_get_by_short_name():
    """SourceRegistry should retrieve sources by short name."""
    registry = SourceRegistry("sources/provenance.json")

    phb = registry.get_source_by_short_name("PHB")
    assert phb is not None
    assert phb["title"] == "Player's Handbook"
    assert phb["sourceId"] == "681f92bc94ff"

    dmg = registry.get_source_by_short_name("DMG")
    assert dmg is not None
    assert dmg["title"] == "Dungeon Master's Guide"

    mm = registry.get_source_by_short_name("MM")
    assert mm is not None
    assert mm["title"] == "Monster Manual"

    # Non-existent short name
    assert registry.get_source_by_short_name("XYZ") is None


def test_source_registry_get_page_count():
    """SourceRegistry should return page counts."""
    registry = SourceRegistry("sources/provenance.json")

    assert registry.get_page_count("681f92bc94ff") == 322  # PHB
    assert registry.get_page_count("fed77f68501d") == 322  # DMG
    assert registry.get_page_count("e390dfd9143f") == 322  # MM


def test_source_registry_missing_provenance_file():
    """SourceRegistry should raise FileNotFoundError if provenance missing."""
    with pytest.raises(FileNotFoundError, match="Provenance file not found"):
        SourceRegistry("nonexistent/provenance.json")
