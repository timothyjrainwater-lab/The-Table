"""Gate tests for WO-JUDGMENT-VALIDATOR-001.

JV-001..008 — Phase 1 judgment validator: mechanic legality + data-driven DC bounds.
PHB p.65 (DC table), PHB p.7 (ability scores).
"""
import json
import os
import pytest
from aidm.core.ruling_validator import (
    _DC_MIN,
    _DC_MAX,
    _VALID_MECHANICS,
    validate_ruling_artifact,
)
from aidm.schemas.ruling_artifact import RulingArtifactShadow


def _valid_artifact(**kwargs) -> RulingArtifactShadow:
    """Minimal valid artifact — all required fields populated."""
    defaults = dict(
        player_action_raw="I attempt to jump the gap",
        route_class="named",
        routing_confidence="certain",
    )
    defaults.update(kwargs)
    return RulingArtifactShadow(**defaults)


# ---------------------------------------------------------------------------
# JV-001: DC bounds loaded from srd_dc_ranges.json — not hardcoded
# ---------------------------------------------------------------------------
def test_jv_001_dc_bounds_data_driven():
    # Cross-check against the actual file — proves load, not coincidence
    data_dir = os.path.join(os.path.dirname(__file__), "..", "aidm", "data")
    with open(os.path.join(data_dir, "srd_dc_ranges.json"), encoding="utf-8") as f:
        file_data = json.load(f)
    assert _DC_MIN == file_data["dc_min"], f"_DC_MIN={_DC_MIN} does not match file dc_min={file_data['dc_min']}"
    assert _DC_MAX == file_data["dc_max"], f"_DC_MAX={_DC_MAX} does not match file dc_max={file_data['dc_max']}"
    assert _DC_MIN == 5
    assert _DC_MAX == 40


# ---------------------------------------------------------------------------
# JV-002: _VALID_MECHANICS non-empty and contains "jump"
# ---------------------------------------------------------------------------
def test_jv_002_valid_mechanics_loaded():
    assert len(_VALID_MECHANICS) >= 49, (
        f"_VALID_MECHANICS has {len(_VALID_MECHANICS)} entries; expected >= 49 (49 SRD skills + ability scores)"
    )
    assert "jump" in _VALID_MECHANICS, "'jump' must be in _VALID_MECHANICS (from srd_skills.json)"


# ---------------------------------------------------------------------------
# JV-003: ability_or_skill=None — mechanic check skipped → pass
# ---------------------------------------------------------------------------
def test_jv_003_no_mechanic_field_passes():
    artifact = _valid_artifact(ability_or_skill=None)
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "pass", f"expected 'pass' with no mechanic field, got {verdict!r}: {reasons}"


# ---------------------------------------------------------------------------
# JV-004: ability_or_skill="Jump" — valid skill → pass
# ---------------------------------------------------------------------------
def test_jv_004_valid_skill_passes():
    artifact = _valid_artifact(ability_or_skill="Jump")
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "pass", f"expected 'pass' for valid skill 'Jump', got {verdict!r}: {reasons}"
    assert not any("unrecognized" in r for r in reasons)


# ---------------------------------------------------------------------------
# JV-005: ability_or_skill="Strength" — valid ability score → pass
# ---------------------------------------------------------------------------
def test_jv_005_ability_score_passes():
    artifact = _valid_artifact(ability_or_skill="Strength")
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "pass", f"expected 'pass' for 'Strength', got {verdict!r}: {reasons}"


# ---------------------------------------------------------------------------
# JV-006: ability_or_skill="NONE" — no-roll sentinel → pass
# ---------------------------------------------------------------------------
def test_jv_006_none_sentinel_passes():
    artifact = _valid_artifact(ability_or_skill="NONE")
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "pass", f"expected 'pass' for sentinel 'NONE', got {verdict!r}: {reasons}"


# ---------------------------------------------------------------------------
# JV-007: ability_or_skill="flurbozle" — unrecognized → fail
# ---------------------------------------------------------------------------
def test_jv_007_unrecognized_mechanic_fails():
    artifact = _valid_artifact(ability_or_skill="flurbozle")
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "fail", f"expected 'fail' for unrecognized mechanic, got {verdict!r}"
    assert any("unrecognized" in r for r in reasons), (
        f"expected 'unrecognized' in reasons, got: {reasons}"
    )


# ---------------------------------------------------------------------------
# JV-008: dc=45 + valid mechanic → needs_clarification (Phase 0 path intact)
# ---------------------------------------------------------------------------
def test_jv_008_high_dc_needs_clarification():
    artifact = _valid_artifact(dc=45, ability_or_skill="bluff")
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "needs_clarification", (
        f"expected 'needs_clarification' for dc=45, got {verdict!r}: {reasons}"
    )
