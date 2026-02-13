"""Tests for campaign bundle validator (campaign memory)."""

import pytest
from aidm.schemas.bundles import CampaignBundle
from aidm.schemas.campaign_memory import (
    SessionLedgerEntry,
    CharacterEvidenceEntry,
    EvidenceLedger,
    ClueCard,
    ThreadRegistry
)
from aidm.core.bundle_validator import validate_campaign_bundle


def test_valid_campaign_bundle_passes():
    """Valid campaign bundle should pass validation."""
    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_campaign_bundle_missing_id_noted():
    """Campaign bundle missing id should be noted."""
    bundle = CampaignBundle(
        id="",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("missing 'id'" in note for note in cert.notes)


def test_campaign_bundle_missing_title_noted():
    """Campaign bundle missing title should be noted."""
    bundle = CampaignBundle(
        id="campaign_alpha",
        title="",
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("missing 'title'" in note for note in cert.notes)


def test_session_ledger_duplicate_session_id_blocks():
    """Session ledger with duplicate session_id should block."""
    entry1 = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1"
    )

    entry2 = SessionLedgerEntry(
        session_id="session_001",  # Duplicate
        campaign_id="campaign_alpha",
        session_number=2,
        created_at="2025-01-16T10:00:00Z",
        summary="Session 2"
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[entry1, entry2]
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("Duplicate session_id" in note and "session_001" in note for note in cert.notes)


def test_session_ledger_unique_session_ids_passes():
    """Session ledger with unique session_ids should pass."""
    entry1 = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1"
    )

    entry2 = SessionLedgerEntry(
        session_id="session_002",
        campaign_id="campaign_alpha",
        session_number=2,
        created_at="2025-01-16T10:00:00Z",
        summary="Session 2"
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[entry1, entry2]
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_evidence_ledger_duplicate_evidence_id_blocks():
    """Evidence ledger with duplicate evidence IDs should block."""
    evidence1 = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="test1"
    )

    evidence2 = CharacterEvidenceEntry(
        id="evidence_001",  # Duplicate
        character_id="pc_2",
        session_id="session_001",
        evidence_type="loyalty",
        description="test2"
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence1, evidence2]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        evidence_ledger=ledger
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("Duplicate evidence entry ID" in note and "evidence_001" in note for note in cert.notes)


def test_evidence_ledger_unique_evidence_ids_passes():
    """Evidence ledger with unique evidence IDs should pass."""
    evidence1 = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="test1"
    )

    evidence2 = CharacterEvidenceEntry(
        id="evidence_002",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="loyalty",
        description="test2"
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence1, evidence2]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        evidence_ledger=ledger
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_evidence_invalid_session_ref_blocks():
    """Evidence referencing non-existent session should block."""
    session_entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1"
    )

    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_999",  # Not in ledger
        evidence_type="mercy_shown",
        description="test"
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[session_entry],
        evidence_ledger=ledger
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("invalid_session_ref" in note and "session_999" in note for note in cert.notes)


def test_evidence_valid_session_ref_passes():
    """Evidence referencing valid session should pass."""
    session_entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1"
    )

    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="test"
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[session_entry],
        evidence_ledger=ledger
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_evidence_event_id_outside_range_blocks():
    """Evidence with event_id outside session range should block."""
    session_entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1",
        event_id_range=(0, 50)
    )

    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="test",
        event_id=100  # Outside range [0, 50]
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[session_entry],
        evidence_ledger=ledger
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("event_id" in note and "outside session range" in note for note in cert.notes)


def test_evidence_event_id_within_range_passes():
    """Evidence with event_id within session range should pass."""
    session_entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1",
        event_id_range=(0, 50)
    )

    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="test",
        event_id=25  # Within range [0, 50]
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[session_entry],
        evidence_ledger=ledger
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_thread_registry_duplicate_clue_id_blocks():
    """Thread registry with duplicate clue IDs should block."""
    clue1 = ClueCard(
        id="clue_001",
        session_id="session_001",
        description="Clue 1"
    )

    clue2 = ClueCard(
        id="clue_001",  # Duplicate
        session_id="session_001",
        description="Clue 2"
    )

    registry = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue1, clue2]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        thread_registry=registry
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("Duplicate clue ID" in note and "clue_001" in note for note in cert.notes)


def test_thread_registry_unique_clue_ids_passes():
    """Thread registry with unique clue IDs should pass."""
    clue1 = ClueCard(
        id="clue_001",
        session_id="session_001",
        description="Clue 1"
    )

    clue2 = ClueCard(
        id="clue_002",
        session_id="session_001",
        description="Clue 2"
    )

    registry = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue1, clue2]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        thread_registry=registry
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_clue_invalid_session_ref_blocks():
    """Clue referencing non-existent session should block."""
    session_entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1"
    )

    clue = ClueCard(
        id="clue_001",
        session_id="session_999",  # Not in ledger
        description="Mystery clue"
    )

    registry = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[session_entry],
        thread_registry=registry
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert any("invalid_session_ref" in note and "session_999" in note for note in cert.notes)


def test_clue_valid_session_ref_passes():
    """Clue referencing valid session should pass."""
    session_entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1"
    )

    clue = ClueCard(
        id="clue_001",
        session_id="session_001",
        description="Mystery clue"
    )

    registry = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[session_entry],
        thread_registry=registry
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_campaign_bundle_without_ledgers_passes():
    """Campaign bundle without ledgers should pass."""
    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "ready"


def test_campaign_bundle_multiple_violations():
    """Campaign bundle with multiple violations should report all."""
    session_entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session 1"
    )

    # Duplicate session
    session_dup = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=2,
        created_at="2025-01-16T10:00:00Z",
        summary="Session 2"
    )

    # Evidence with invalid session ref
    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_999",
        evidence_type="mercy_shown",
        description="test"
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence]
    )

    bundle = CampaignBundle(
        id="campaign_alpha",
        title="Test Campaign",
        created_at="2025-01-15T10:00:00Z",
        session_ledger=[session_entry, session_dup],
        evidence_ledger=ledger
    )

    cert = validate_campaign_bundle(bundle)
    assert cert.status == "blocked"
    assert len(cert.notes) >= 2
    assert any("Duplicate session_id" in note for note in cert.notes)
    assert any("invalid_session_ref" in note for note in cert.notes)
