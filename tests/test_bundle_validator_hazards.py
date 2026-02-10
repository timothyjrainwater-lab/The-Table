"""Tests for hazard-based bundle validation."""

import pytest
from aidm.schemas.bundles import SessionBundle, SceneCard
from aidm.schemas.hazards import EnvironmentalHazard
from aidm.schemas.exposure import EnvironmentalCondition
from aidm.core.bundle_validator import validate_session_bundle


def test_bundle_with_hazards_passes():
    """Bundle validation should accept valid hazards."""
    hazard = EnvironmentalHazard(
        id="forest_fire",
        name="Forest Fire",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="1d6 fire damage"
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Burning Forest",
        description="Forest on fire",
        environmental_hazards=[hazard]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_duplicate_hazard_ids_blocks():
    """Bundle validation should block duplicate hazard IDs."""
    hazard1 = EnvironmentalHazard(
        id="fire",
        name="Fire 1",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="fire"
    )

    hazard2 = EnvironmentalHazard(
        id="fire",  # Duplicate ID
        name="Fire 2",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="fire"
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Test",
        description="test",
        environmental_hazards=[hazard1, hazard2]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("duplicate_hazard_id" in note for note in cert.notes)


def test_bundle_condition_missing_hazard_ref_blocks():
    """Bundle validation should block conditions referencing non-existent hazards."""
    condition = EnvironmentalCondition(
        type="heat",
        hazard_ref="nonexistent_hazard"
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Test",
        description="test",
        environmental_conditions=[condition]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("missing_hazard_ref" in note for note in cert.notes)


def test_bundle_condition_with_valid_hazard_ref_passes():
    """Bundle validation should accept conditions with valid hazard references."""
    hazard = EnvironmentalHazard(
        id="extreme_heat",
        name="Extreme Heat",
        interval_unit="hour",
        interval_value=1,
        effect_type="damage",
        description="1d6 heat damage"
    )

    condition = EnvironmentalCondition(
        type="heat",
        hazard_ref="extreme_heat"
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Desert",
        description="Hot desert",
        environmental_hazards=[hazard],
        environmental_conditions=[condition]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_hazard_with_visibility_tags_passes():
    """Bundle validation should accept hazards with visibility tags."""
    hazard = EnvironmentalHazard(
        id="smoke",
        name="Thick Smoke",
        interval_unit="round",
        interval_value=1,
        effect_type="mixed",
        description="Smoke damage and concealment",
        visibility_tags=["heavy_obscurement"]
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Smoky Room",
        description="Filled with smoke",
        environmental_hazards=[hazard]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_hazard_with_terrain_tags_passes():
    """Bundle validation should accept hazards with terrain tags."""
    hazard = EnvironmentalHazard(
        id="ice",
        name="Slippery Ice",
        interval_unit="round",
        interval_value=1,
        effect_type="condition",
        description="Ice surface",
        terrain_tags=["slippery", "difficult_terrain"]
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Frozen Lake",
        description="Ice covered",
        environmental_hazards=[hazard]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_without_hazards_passes():
    """Bundle validation should pass for bundles without hazards."""
    scene = SceneCard(
        scene_id="scene_1",
        title="Safe Room",
        description="No hazards"
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_multiple_hazards_all_validated():
    """Bundle validation should check all hazards in scene."""
    hazard1 = EnvironmentalHazard(
        id="fire",
        name="Fire",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="fire"
    )

    hazard2 = EnvironmentalHazard(
        id="smoke",
        name="Smoke",
        interval_unit="round",
        interval_value=1,
        effect_type="visibility",
        description="smoke"
    )

    # Condition references non-existent hazard
    condition = EnvironmentalCondition(
        type="toxic_fumes",
        hazard_ref="poison_gas"  # Doesn't exist
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Burning Building",
        description="Fire and smoke",
        environmental_hazards=[hazard1, hazard2],
        environmental_conditions=[condition]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("missing_hazard_ref" in note and "poison_gas" in note for note in cert.notes)


def test_bundle_hazard_with_dmg_citation_missing_page_blocks():
    """Bundle validation should block DMG citations without page."""
    hazard = EnvironmentalHazard(
        id="lava",
        name="Lava",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="20d6 fire damage",
        citation={"source_id": "fed77f68501d"}  # DMG ID without page
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Lava Chamber",
        description="Lava flows",
        environmental_hazards=[hazard]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("dmg_citation_missing_page" in note for note in cert.notes)


def test_bundle_hazard_with_dmg_citation_with_page_passes():
    """Bundle validation should accept DMG citations with page."""
    hazard = EnvironmentalHazard(
        id="lava",
        name="Lava",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="20d6 fire damage",
        citation={"source_id": "fed77f68501d", "page": 304}
    )

    scene = SceneCard(
        scene_id="scene_1",
        title="Lava Chamber",
        description="Lava flows",
        environmental_hazards=[hazard]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_multiple_scenes_hazards_validated():
    """Bundle validation should validate hazards across all scenes."""
    hazard1 = EnvironmentalHazard(
        id="fire",
        name="Fire",
        interval_unit="round",
        interval_value=1,
        effect_type="damage",
        description="fire"
    )

    hazard2 = EnvironmentalHazard(
        id="cold",
        name="Cold",
        interval_unit="hour",
        interval_value=1,
        effect_type="damage",
        description="cold"
    )

    scene1 = SceneCard(
        scene_id="scene_1",
        title="Fire Room",
        description="Burning",
        environmental_hazards=[hazard1]
    )

    scene2 = SceneCard(
        scene_id="scene_2",
        title="Ice Room",
        description="Freezing",
        environmental_hazards=[hazard2]
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene1, scene2]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"
