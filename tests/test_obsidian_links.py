"""Tests for Obsidian URI helpers."""

import pytest
from aidm.core.obsidian_links import (
    build_obsidian_uri,
    build_rulebook_page_note_path
)
from aidm.schemas.citation import Citation, with_obsidian_uri


def test_build_obsidian_uri_format():
    """build_obsidian_uri() should produce correct URI format."""
    uri = build_obsidian_uri("DnD", "Rulebooks/PHB/PHB_p0010.md")

    assert uri.startswith("obsidian://open?")
    assert "vault=DnD" in uri
    assert "file=Rulebooks" in uri
    assert "PHB_p0010.md" in uri


def test_build_obsidian_uri_url_encoding():
    """build_obsidian_uri() should URL-encode special characters."""
    uri = build_obsidian_uri("My Vault", "Notes/Page 1.md")

    assert "vault=My%20Vault" in uri
    # Note: quote() doesn't encode forward slashes by default (safe characters)
    assert "file=Notes/Page%201.md" in uri


def test_page_note_path_formatting_zero_pad():
    """build_rulebook_page_note_path() should zero-pad page numbers."""
    path = build_rulebook_page_note_path("PHB", 10)
    assert path == "Rulebooks/PHB/PHB_p0010.md"

    path = build_rulebook_page_note_path("DMG", 1)
    assert path == "Rulebooks/DMG/DMG_p0001.md"

    path = build_rulebook_page_note_path("MM", 157)
    assert path == "Rulebooks/MM/MM_p0157.md"


def test_page_note_path_uses_short_name():
    """build_rulebook_page_note_path() should use short name consistently."""
    path = build_rulebook_page_note_path("XGtE", 42)
    assert "XGtE" in path
    assert path.startswith("Rulebooks/XGtE/")
    assert path.endswith("XGtE_p0042.md")


def test_citation_with_obsidian_uri():
    """with_obsidian_uri() should create citation with URI attached."""
    original = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=157,
        span="Grapple rules"
    )

    note_path = build_rulebook_page_note_path("PHB", 157)
    uri = build_obsidian_uri("DnD", note_path)
    enhanced = with_obsidian_uri(original, uri)

    assert enhanced.source_id == "681f92bc94ff"
    assert enhanced.short_name == "PHB"
    assert enhanced.page == 157
    assert enhanced.span == "Grapple rules"
    assert enhanced.obsidian_uri is not None
    assert "obsidian://open?" in enhanced.obsidian_uri
    assert "PHB_p0157.md" in enhanced.obsidian_uri


def test_with_obsidian_uri_preserves_all_fields():
    """with_obsidian_uri() should preserve all original citation fields."""
    original = Citation(
        source_id="681f92bc94ff",
        short_name="PHB",
        page=10,
        span="Constitution",
        rule_id="ability_scores.con"
    )

    enhanced = with_obsidian_uri(original, build_obsidian_uri("MyVault", "test.md"))

    assert enhanced.source_id == original.source_id
    assert enhanced.short_name == original.short_name
    assert enhanced.page == original.page
    assert enhanced.span == original.span
    assert enhanced.rule_id == original.rule_id


def test_obsidian_uri_deterministic():
    """Obsidian URI generation should be deterministic."""
    uri1 = build_obsidian_uri("DnD", "Rulebooks/PHB/PHB_p0010.md")
    uri2 = build_obsidian_uri("DnD", "Rulebooks/PHB/PHB_p0010.md")

    assert uri1 == uri2


def test_page_note_path_handles_large_page_numbers():
    """build_rulebook_page_note_path() should handle 4+ digit page numbers."""
    path = build_rulebook_page_note_path("HUGE", 9999)
    assert path == "Rulebooks/HUGE/HUGE_p9999.md"
