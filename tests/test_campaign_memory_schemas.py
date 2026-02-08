"""Tests for campaign memory and evidence ledger schemas."""

import pytest
import json
from aidm.schemas.campaign_memory import (
    SessionLedgerEntry,
    CharacterEvidenceEntry,
    EvidenceLedger,
    ClueCard,
    ThreadRegistry
)


def test_session_ledger_entry_basic():
    """SessionLedgerEntry should store basic session data."""
    entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Party explored dungeon",
        facts_added=["Found ancient map", "Defeated goblin warband"],
        state_changes=["Cleric gained level 3"]
    )

    assert entry.session_id == "session_001"
    assert entry.campaign_id == "campaign_alpha"
    assert entry.session_number == 1
    assert len(entry.facts_added) == 2
    assert len(entry.state_changes) == 1


def test_session_ledger_entry_empty_session_id_rejected():
    """SessionLedgerEntry should reject empty session_id."""
    with pytest.raises(ValueError, match="session_id cannot be empty"):
        SessionLedgerEntry(
            session_id="",
            campaign_id="campaign_alpha",
            session_number=1,
            created_at="2025-01-15T10:00:00Z",
            summary="test"
        )


def test_session_ledger_entry_empty_campaign_id_rejected():
    """SessionLedgerEntry should reject empty campaign_id."""
    with pytest.raises(ValueError, match="campaign_id cannot be empty"):
        SessionLedgerEntry(
            session_id="session_001",
            campaign_id="",
            session_number=1,
            created_at="2025-01-15T10:00:00Z",
            summary="test"
        )


def test_session_ledger_entry_invalid_session_number_rejected():
    """SessionLedgerEntry should reject session_number < 1."""
    with pytest.raises(ValueError, match="session_number must be >= 1"):
        SessionLedgerEntry(
            session_id="session_001",
            campaign_id="campaign_alpha",
            session_number=0,
            created_at="2025-01-15T10:00:00Z",
            summary="test"
        )


def test_session_ledger_entry_empty_summary_rejected():
    """SessionLedgerEntry should reject empty summary."""
    with pytest.raises(ValueError, match="summary cannot be empty"):
        SessionLedgerEntry(
            session_id="session_001",
            campaign_id="campaign_alpha",
            session_number=1,
            created_at="2025-01-15T10:00:00Z",
            summary=""
        )


def test_session_ledger_entry_with_event_id_range():
    """SessionLedgerEntry should support event_id_range."""
    entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Session summary",
        event_id_range=(0, 42)
    )

    assert entry.event_id_range == (0, 42)


def test_session_ledger_entry_invalid_event_id_range_rejected():
    """SessionLedgerEntry should reject invalid event_id_range."""
    with pytest.raises(ValueError, match="event_id_range end must be >= start"):
        SessionLedgerEntry(
            session_id="session_001",
            campaign_id="campaign_alpha",
            session_number=1,
            created_at="2025-01-15T10:00:00Z",
            summary="test",
            event_id_range=(10, 5)
        )


def test_session_ledger_entry_serialization():
    """SessionLedgerEntry should serialize deterministically."""
    entry = SessionLedgerEntry(
        session_id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        summary="Party cleared dungeon",
        facts_added=["Found treasure", "Defeated boss"],
        state_changes=["Wizard learned fireball"],
        event_id_range=(0, 50),
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    )

    data = entry.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = SessionLedgerEntry.from_dict(json.loads(json_str))

    assert restored.session_id == entry.session_id
    assert restored.campaign_id == entry.campaign_id
    assert restored.session_number == entry.session_number
    assert restored.summary == entry.summary
    assert restored.facts_added == entry.facts_added
    assert restored.state_changes == entry.state_changes
    assert restored.event_id_range == entry.event_id_range


def test_character_evidence_entry_basic():
    """CharacterEvidenceEntry should store basic evidence data."""
    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="paladin_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="Spared defeated bandit chief"
    )

    assert evidence.id == "evidence_001"
    assert evidence.character_id == "paladin_1"
    assert evidence.evidence_type == "mercy_shown"
    assert evidence.description == "Spared defeated bandit chief"


def test_character_evidence_entry_empty_id_rejected():
    """CharacterEvidenceEntry should reject empty id."""
    with pytest.raises(ValueError, match="id cannot be empty"):
        CharacterEvidenceEntry(
            id="",
            character_id="paladin_1",
            session_id="session_001",
            evidence_type="mercy_shown",
            description="test"
        )


def test_character_evidence_entry_invalid_evidence_type_rejected():
    """CharacterEvidenceEntry should reject invalid evidence_type."""
    with pytest.raises(ValueError, match="evidence_type must be one of"):
        CharacterEvidenceEntry(
            id="evidence_001",
            character_id="paladin_1",
            session_id="session_001",
            evidence_type="invalid_type",
            description="test"
        )


def test_character_evidence_entry_all_evidence_types():
    """CharacterEvidenceEntry should accept all valid evidence types."""
    types = [
        "harm_inflicted", "harm_prevented", "mercy_shown", "betrayal",
        "loyalty", "theft", "deception", "obedience_authority",
        "defiance_authority", "self_sacrifice", "self_interest",
        "respect_life", "disregard_life", "promise_made", "promise_broken"
    ]

    for evidence_type in types:
        evidence = CharacterEvidenceEntry(
            id=f"evidence_{evidence_type}",
            character_id="pc_1",
            session_id="session_001",
            evidence_type=evidence_type,
            description=f"Test {evidence_type}"
        )
        assert evidence.evidence_type == evidence_type


def test_character_evidence_entry_with_alignment_tags():
    """CharacterEvidenceEntry should support alignment_axis_tags."""
    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="paladin_1",
        session_id="session_001",
        evidence_type="obedience_authority",
        description="Followed lawful orders",
        alignment_axis_tags=["lawful", "good"]
    )

    assert "lawful" in evidence.alignment_axis_tags
    assert "good" in evidence.alignment_axis_tags


def test_character_evidence_entry_invalid_alignment_tag_rejected():
    """CharacterEvidenceEntry should reject invalid alignment_axis_tags."""
    with pytest.raises(ValueError, match="alignment_axis_tag must be one of"):
        CharacterEvidenceEntry(
            id="evidence_001",
            character_id="pc_1",
            session_id="session_001",
            evidence_type="mercy_shown",
            description="test",
            alignment_axis_tags=["invalid_tag"]
        )


def test_character_evidence_entry_all_alignment_tags():
    """CharacterEvidenceEntry should accept all valid alignment_axis_tags."""
    tags = ["lawful", "neutral_lc", "chaotic", "good", "neutral_ge", "evil"]

    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="test",
        alignment_axis_tags=tags
    )

    assert evidence.alignment_axis_tags == tags


def test_character_evidence_entry_with_targets():
    """CharacterEvidenceEntry should support targets."""
    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="harm_inflicted",
        description="Attacked enemy combatants",
        targets=["goblin_1", "goblin_2"]
    )

    assert len(evidence.targets) == 2
    assert "goblin_1" in evidence.targets


def test_character_evidence_entry_with_references():
    """CharacterEvidenceEntry should support location/faction/deity references."""
    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="cleric_1",
        session_id="session_001",
        evidence_type="loyalty",
        description="Defended temple",
        location_ref="temple_of_pelor",
        faction_ref="church_of_pelor",
        deity_ref="pelor"
    )

    assert evidence.location_ref == "temple_of_pelor"
    assert evidence.faction_ref == "church_of_pelor"
    assert evidence.deity_ref == "pelor"


def test_character_evidence_entry_serialization():
    """CharacterEvidenceEntry should serialize deterministically."""
    evidence = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="paladin_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="Spared enemy",
        event_id=42,
        targets=["bandit_1"],
        location_ref="forest_clearing",
        faction_ref="bandits",
        deity_ref="heironeous",
        alignment_axis_tags=["lawful", "good"],
        citations=[{"source_id": "test", "page": 1}]
    )

    data = evidence.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = CharacterEvidenceEntry.from_dict(json.loads(json_str))

    assert restored.id == evidence.id
    assert restored.character_id == evidence.character_id
    assert restored.evidence_type == evidence.evidence_type
    assert restored.description == evidence.description
    assert restored.event_id == evidence.event_id
    assert restored.targets == evidence.targets
    assert restored.alignment_axis_tags == evidence.alignment_axis_tags


def test_evidence_ledger_basic():
    """EvidenceLedger should store evidence entries."""
    evidence1 = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="mercy_shown",
        description="test"
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence1]
    )

    assert ledger.campaign_id == "campaign_alpha"
    assert len(ledger.entries) == 1


def test_evidence_ledger_deterministic_ordering():
    """EvidenceLedger should enforce deterministic ordering."""
    evidence1 = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_2",
        session_id="session_002",
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

    # Should be sorted by (character_id, session_id, id)
    assert ledger.entries[0].character_id == "pc_1"
    assert ledger.entries[1].character_id == "pc_2"


def test_evidence_ledger_serialization():
    """EvidenceLedger should serialize deterministically."""
    evidence1 = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="harm_prevented",
        description="Saved villager"
    )

    ledger = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence1]
    )

    data = ledger.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = EvidenceLedger.from_dict(json.loads(json_str))

    assert restored.campaign_id == ledger.campaign_id
    assert len(restored.entries) == len(ledger.entries)
    assert restored.entries[0].id == ledger.entries[0].id


def test_clue_card_basic():
    """ClueCard should store clue data."""
    clue = ClueCard(
        id="clue_001",
        session_id="session_001",
        discovered_by=["pc_1", "pc_2"],
        description="Ancient rune on stone",
        status="unresolved"
    )

    assert clue.id == "clue_001"
    assert clue.session_id == "session_001"
    assert len(clue.discovered_by) == 2
    assert clue.status == "unresolved"


def test_clue_card_empty_id_rejected():
    """ClueCard should reject empty id."""
    with pytest.raises(ValueError, match="id cannot be empty"):
        ClueCard(
            id="",
            session_id="session_001",
            description="test"
        )


def test_clue_card_empty_session_id_rejected():
    """ClueCard should reject empty session_id."""
    with pytest.raises(ValueError, match="session_id cannot be empty"):
        ClueCard(
            id="clue_001",
            session_id="",
            description="test"
        )


def test_clue_card_invalid_status_rejected():
    """ClueCard should reject invalid status."""
    with pytest.raises(ValueError, match="status must be one of"):
        ClueCard(
            id="clue_001",
            session_id="session_001",
            status="invalid_status"
        )


def test_clue_card_all_statuses():
    """ClueCard should accept all valid statuses."""
    statuses = ["unresolved", "partial", "resolved"]

    for status in statuses:
        clue = ClueCard(
            id=f"clue_{status}",
            session_id="session_001",
            status=status
        )
        assert clue.status == status


def test_clue_card_with_links():
    """ClueCard should support links to related clues."""
    clue = ClueCard(
        id="clue_001",
        session_id="session_001",
        description="Mysterious symbol",
        links=["clue_002", "npc_villain_1", "location_temple"]
    )

    assert len(clue.links) == 3
    assert "clue_002" in clue.links


def test_clue_card_serialization():
    """ClueCard should serialize deterministically."""
    clue = ClueCard(
        id="clue_001",
        session_id="session_001",
        discovered_by=["pc_1"],
        description="Secret passage",
        status="partial",
        links=["clue_002"],
        citations=[{"source_id": "test", "page": 1}]
    )

    data = clue.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = ClueCard.from_dict(json.loads(json_str))

    assert restored.id == clue.id
    assert restored.session_id == clue.session_id
    assert restored.discovered_by == clue.discovered_by
    assert restored.status == clue.status
    assert restored.links == clue.links


def test_thread_registry_basic():
    """ThreadRegistry should store clue cards."""
    clue1 = ClueCard(
        id="clue_001",
        session_id="session_001",
        description="Ancient map"
    )

    registry = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue1]
    )

    assert registry.campaign_id == "campaign_alpha"
    assert len(registry.clues) == 1


def test_thread_registry_deterministic_ordering():
    """ThreadRegistry should enforce deterministic ordering by id."""
    clue1 = ClueCard(id="clue_003", session_id="session_001")
    clue2 = ClueCard(id="clue_001", session_id="session_001")
    clue3 = ClueCard(id="clue_002", session_id="session_001")

    registry = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue1, clue2, clue3]
    )

    # Should be sorted by id
    assert registry.clues[0].id == "clue_001"
    assert registry.clues[1].id == "clue_002"
    assert registry.clues[2].id == "clue_003"


def test_thread_registry_serialization():
    """ThreadRegistry should serialize deterministically."""
    clue1 = ClueCard(
        id="clue_001",
        session_id="session_001",
        description="Mystery clue"
    )

    registry = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue1]
    )

    data = registry.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = ThreadRegistry.from_dict(json.loads(json_str))

    assert restored.campaign_id == registry.campaign_id
    assert len(restored.clues) == len(registry.clues)
    assert restored.clues[0].id == registry.clues[0].id


def test_evidence_ledger_roundtrip():
    """EvidenceLedger should roundtrip correctly."""
    evidence1 = CharacterEvidenceEntry(
        id="evidence_001",
        character_id="pc_1",
        session_id="session_001",
        evidence_type="loyalty",
        description="Defended ally",
        alignment_axis_tags=["good"]
    )

    original = EvidenceLedger(
        campaign_id="campaign_alpha",
        entries=[evidence1]
    )

    data = original.to_dict()
    restored = EvidenceLedger.from_dict(data)

    assert restored.campaign_id == original.campaign_id
    assert len(restored.entries) == len(original.entries)
    assert restored.entries[0].evidence_type == original.entries[0].evidence_type


def test_thread_registry_roundtrip():
    """ThreadRegistry should roundtrip correctly."""
    clue1 = ClueCard(
        id="clue_001",
        session_id="session_001",
        description="Mysterious artifact",
        status="partial",
        links=["clue_002"]
    )

    original = ThreadRegistry(
        campaign_id="campaign_alpha",
        clues=[clue1]
    )

    data = original.to_dict()
    restored = ThreadRegistry.from_dict(data)

    assert restored.campaign_id == original.campaign_id
    assert len(restored.clues) == len(original.clues)
    assert restored.clues[0].status == original.clues[0].status
