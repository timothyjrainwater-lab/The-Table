"""Tests for bundle schemas."""

import pytest
from aidm.schemas.bundles import (
    SessionBundle,
    CampaignBundle,
    SceneCard,
    NpcCard,
    EncounterSpec,
    ReadinessCertificate
)


def test_session_bundle_creation():
    """SessionBundle should be creatable with minimal fields."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z"
    )

    assert bundle.id == "session_001"
    assert bundle.campaign_id == "campaign_alpha"
    assert bundle.session_number == 1
    assert len(bundle.scene_cards) == 0
    assert len(bundle.npc_cards) == 0
    assert len(bundle.encounter_specs) == 0


def test_session_bundle_with_scene_cards():
    """SessionBundle should support scene cards."""
    scene = SceneCard(
        scene_id="tavern_1",
        title="The Prancing Pony",
        description="A cozy tavern with a roaring fireplace",
        key_npcs=["innkeeper_bob"],
        exits=["to_street", "to_cellar"]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    assert len(bundle.scene_cards) == 1
    assert bundle.scene_cards[0].title == "The Prancing Pony"


def test_session_bundle_with_npc_cards():
    """SessionBundle should support NPC cards."""
    npc = NpcCard(
        npc_id="innkeeper_bob",
        name="Bob the Innkeeper",
        role="questgiver",
        stats={"hp": 10, "ac": 12},
        personality="Jovial and helpful",
        goals=["Protect his tavern", "Help travelers"]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        npc_cards=[npc]
    )

    assert len(bundle.npc_cards) == 1
    assert bundle.npc_cards[0].name == "Bob the Innkeeper"


def test_session_bundle_with_encounters():
    """SessionBundle should support encounter specs."""
    encounter = EncounterSpec(
        encounter_id="goblin_ambush",
        name="Goblin Ambush",
        creatures=[
            {"type": "goblin", "count": 3, "hp": 7}
        ],
        terrain="forest",
        trigger_condition="players leave road"
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter]
    )

    assert len(bundle.encounter_specs) == 1
    assert bundle.encounter_specs[0].name == "Goblin Ambush"


def test_session_bundle_serialization():
    """SessionBundle should serialize to dict correctly."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        assets={"token_goblin": "assets/goblin.png"},
        citations=[{"source_id": "681f92bc94ff", "page": 10}]
    )

    bundle_dict = bundle.to_dict()

    assert bundle_dict["id"] == "session_001"
    assert bundle_dict["session_number"] == 1
    assert "token_goblin" in bundle_dict["assets"]
    assert len(bundle_dict["citations"]) == 1


def test_campaign_bundle_creation():
    """CampaignBundle should be creatable."""
    campaign = CampaignBundle(
        id="campaign_alpha",
        title="Rise of the Dragon",
        created_at="2025-01-01T00:00:00Z",
        sources_used=["681f92bc94ff", "fed77f68501d"],
        world_facts=["Dragons rule the north", "Magic is rare"]
    )

    assert campaign.title == "Rise of the Dragon"
    assert len(campaign.sources_used) == 2
    assert len(campaign.world_facts) == 2


def test_readiness_certificate_ready_status():
    """ReadinessCertificate should support 'ready' status."""
    cert = ReadinessCertificate(
        bundle_id="session_001",
        status="ready"
    )

    assert cert.status == "ready"
    assert len(cert.missing_assets) == 0
    assert len(cert.missing_citations) == 0


def test_readiness_certificate_blocked_status():
    """ReadinessCertificate should support 'blocked' status with issues."""
    cert = ReadinessCertificate(
        bundle_id="session_001",
        status="blocked",
        missing_assets=["assets/missing_token.png"],
        missing_citations=["Citation 0: missing source_id"],
        notes=["Bundle has critical issues"]
    )

    assert cert.status == "blocked"
    assert len(cert.missing_assets) == 1
    assert len(cert.missing_citations) == 1
    assert len(cert.notes) == 1


def test_readiness_certificate_serialization():
    """ReadinessCertificate should serialize to dict."""
    cert = ReadinessCertificate(
        bundle_id="session_001",
        status="ready",
        notes=["All checks passed"]
    )

    cert_dict = cert.to_dict()

    assert cert_dict["bundle_id"] == "session_001"
    assert cert_dict["status"] == "ready"
    assert len(cert_dict["notes"]) == 1
