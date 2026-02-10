"""Tests for bundle validator."""

import pytest
import tempfile
from pathlib import Path
from aidm.core.bundle_validator import validate_session_bundle
from aidm.schemas.bundles import SessionBundle


def test_valid_bundle_passes_validation():
    """validate_session_bundle() should pass valid bundles."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "ready"
    assert len(cert.missing_assets) == 0
    assert len(cert.missing_citations) == 0


def test_missing_id_is_noted():
    """validate_session_bundle() should note missing bundle id."""
    bundle = SessionBundle(
        id="",  # Empty ID
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("missing 'id'" in note for note in cert.notes)


def test_missing_campaign_id_is_noted():
    """validate_session_bundle() should note missing campaign_id."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="",  # Empty campaign_id
        session_number=1,
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("missing 'campaign_id'" in note for note in cert.notes)


def test_invalid_session_number_is_noted():
    """validate_session_bundle() should note invalid session numbers."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=0,  # Invalid (< 1)
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("Invalid session_number" in note for note in cert.notes)


def test_missing_asset_file_is_detected():
    """validate_session_bundle() should detect missing asset files."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        assets={"token": "nonexistent/path/to/token.png"}
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert len(cert.missing_assets) > 0
    assert "token" in cert.missing_assets[0]


def test_existing_asset_file_passes():
    """validate_session_bundle() should pass for existing asset files."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp_path = tmp.name

    try:
        bundle = SessionBundle(
            id="session_001",
            campaign_id="campaign_alpha",
            session_number=1,
            created_at="2025-01-15T10:00:00Z",
            assets={"token": tmp_path}
        )

        cert = validate_session_bundle(bundle)

        assert cert.status == "ready"
        assert len(cert.missing_assets) == 0
    finally:
        Path(tmp_path).unlink()


def test_http_urls_not_validated_as_files():
    """validate_session_bundle() should not validate HTTP URLs as file paths."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        assets={"portrait": "https://example.com/portrait.png"}
    )

    cert = validate_session_bundle(bundle)

    # Should not check HTTP URLs as file paths
    assert cert.status == "ready"
    assert len(cert.missing_assets) == 0


def test_citation_missing_source_id_detected():
    """validate_session_bundle() should detect citations without source_id."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        citations=[
            {"page": 10}  # Missing source_id
        ]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert len(cert.missing_citations) > 0
    assert "source_id" in cert.missing_citations[0]


def test_citation_invalid_page_detected():
    """validate_session_bundle() should detect invalid page numbers."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        citations=[
            {"source_id": "681f92bc94ff", "page": 0}  # Invalid page
        ]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert len(cert.missing_citations) > 0
    assert "invalid page" in cert.missing_citations[0]


def test_valid_citations_pass():
    """validate_session_bundle() should pass valid citations."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        citations=[
            {"source_id": "681f92bc94ff", "short_name": "PHB", "page": 157},
            {"source_id": "fed77f68501d"},  # Page is optional
        ]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "ready"
    assert len(cert.missing_citations) == 0


def test_non_dict_citation_detected():
    """validate_session_bundle() should detect non-dict citations."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        citations=["invalid_citation"]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert len(cert.missing_citations) > 0
    assert "not a dictionary" in cert.missing_citations[0]
