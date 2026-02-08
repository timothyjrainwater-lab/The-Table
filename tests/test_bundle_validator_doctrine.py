"""Tests for doctrine-based bundle validation."""

import pytest
from aidm.schemas.bundles import SessionBundle, EncounterSpec
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.core.bundle_validator import validate_session_bundle


def test_encounter_with_creatures_but_no_doctrine_blocks():
    """Bundle validation should fail when encounter has creatures but no doctrines."""
    encounter = EncounterSpec(
        encounter_id="goblin_ambush",
        name="Goblin Ambush",
        creatures=[{"type": "goblin", "count": 3}],
        monster_doctrines_by_id={}  # Empty - should block
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter],
        doctrine_required=True
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("missing_monster_doctrine" in note for note in cert.notes)


def test_encounter_with_doctrine_passes():
    """Bundle validation should pass when encounter has proper doctrines."""
    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=9,
        creature_type="humanoid",
        tags=["cowardly"],
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )

    encounter = EncounterSpec(
        encounter_id="goblin_ambush",
        name="Goblin Ambush",
        creatures=[{"type": "goblin", "count": 3}],
        monster_doctrines_by_id={"goblin": doctrine}
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter],
        doctrine_required=True
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "ready"
    assert len(cert.notes) == 0


def test_doctrine_missing_citation_for_mm_source_blocks():
    """Bundle validation should fail when MM source has no citations."""
    doctrine = MonsterDoctrine(
        monster_id="orc",
        source="MM",
        int_score=9,
        wis_score=8,
        creature_type="humanoid",
        tags=[],
        citations=[]  # Missing citations for MM source
    )

    encounter = EncounterSpec(
        encounter_id="orc_patrol",
        name="Orc Patrol",
        creatures=[{"type": "orc", "count": 4}],
        monster_doctrines_by_id={"orc": doctrine}
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("doctrine_missing_citation" in note for note in cert.notes)


def test_doctrine_invalid_int_score_blocks():
    """Bundle validation should fail for invalid INT scores."""
    doctrine = MonsterDoctrine(
        monster_id="test_creature",
        source="MM",
        int_score=0,  # Invalid (< 1)
        wis_score=10,
        creature_type="beast",
        tags=[],
        citations=[{"source_id": "test", "page": 1}]
    )

    encounter = EncounterSpec(
        encounter_id="test_enc",
        name="Test Encounter",
        creatures=[{"type": "test", "count": 1}],
        monster_doctrines_by_id={"test_creature": doctrine}
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("doctrine_invalid_scores" in note for note in cert.notes)


def test_doctrine_invalid_wis_score_blocks():
    """Bundle validation should fail for invalid WIS scores."""
    doctrine = MonsterDoctrine(
        monster_id="test_creature",
        source="MM",
        int_score=10,
        wis_score=-1,  # Invalid
        creature_type="beast",
        tags=[],
        citations=[{"source_id": "test", "page": 1}]
    )

    encounter = EncounterSpec(
        encounter_id="test_enc",
        name="Test Encounter",
        creatures=[{"type": "test", "count": 1}],
        monster_doctrines_by_id={"test_creature": doctrine}
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("doctrine_invalid_scores" in note for note in cert.notes)


def test_doctrine_not_required_skips_validation():
    """Bundle validation should skip doctrine checks when doctrine_required=False."""
    encounter = EncounterSpec(
        encounter_id="goblin_ambush",
        name="Goblin Ambush",
        creatures=[{"type": "goblin", "count": 3}],
        monster_doctrines_by_id={}  # No doctrines
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter],
        doctrine_required=False  # Disabled
    )

    cert = validate_session_bundle(bundle)

    # Should pass because doctrine not required
    assert cert.status == "ready"


def test_encounter_without_creatures_skips_doctrine_check():
    """Bundle validation should skip doctrine check for encounters without creatures."""
    encounter = EncounterSpec(
        encounter_id="trap_room",
        name="Trap Room",
        creatures=[],  # No creatures
        monster_doctrines_by_id={}
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter],
        doctrine_required=True
    )

    cert = validate_session_bundle(bundle)

    # Should pass because no creatures = no doctrine needed
    assert cert.status == "ready"


def test_multiple_doctrines_all_validated():
    """Bundle validation should check all doctrines in encounter."""
    doctrine1 = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=9,
        creature_type="humanoid",
        tags=[],
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )

    doctrine2 = MonsterDoctrine(
        monster_id="orc",
        source="MM",
        int_score=9,
        wis_score=8,
        creature_type="humanoid",
        tags=[],
        citations=[]  # Missing - should block
    )

    encounter = EncounterSpec(
        encounter_id="mixed_encounter",
        name="Mixed Encounter",
        creatures=[{"type": "goblin", "count": 2}, {"type": "orc", "count": 1}],
        monster_doctrines_by_id={"goblin": doctrine1, "orc": doctrine2}
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "blocked"
    assert any("doctrine_missing_citation" in note for note in cert.notes)


def test_doctrine_with_none_int_passes():
    """Bundle validation should allow None INT score (mindless creatures)."""
    doctrine = MonsterDoctrine(
        monster_id="zombie",
        source="MM",
        int_score=None,  # Mindless
        wis_score=10,
        creature_type="undead",
        tags=["mindless_feeder"],
        citations=[{"source_id": "e390dfd9143f", "page": 265}]
    )

    encounter = EncounterSpec(
        encounter_id="zombie_horde",
        name="Zombie Horde",
        creatures=[{"type": "zombie", "count": 5}],
        monster_doctrines_by_id={"zombie": doctrine}
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        encounter_specs=[encounter]
    )

    cert = validate_session_bundle(bundle)

    assert cert.status == "ready"
