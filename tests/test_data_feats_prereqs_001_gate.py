"""Gate tests for WO-DATA-FEATS-PREREQS-001 — Feat Prerequisite Registry.

Gate label: DATA-FEATS-PREREQS
Tests: FP-001 through FP-008

Verifies that FeatDefinition.prerequisites tuples are populated correctly
for PHB feats with prerequisites. Prerequisites are stored as human-readable
string tuples (e.g. ("STR 13", "Power Attack")).
"""

import pytest
from aidm.data.feat_definitions import FEAT_REGISTRY


# ---------------------------------------------------------------------------
# FP-001: power_attack requires STR 13
# ---------------------------------------------------------------------------
def test_fp_001_power_attack_str_prereq():
    """power_attack requires STR 13 (PHB p.98)."""
    feat = FEAT_REGISTRY["power_attack"]
    assert any("STR 13" in p for p in feat.prerequisites), (
        f"Expected 'STR 13' in power_attack.prerequisites, got {feat.prerequisites}"
    )


# ---------------------------------------------------------------------------
# FP-002: cleave requires power_attack feat
# ---------------------------------------------------------------------------
def test_fp_002_cleave_requires_power_attack():
    """cleave requires Power Attack (PHB p.92)."""
    feat = FEAT_REGISTRY["cleave"]
    prereqs_lower = [p.lower() for p in feat.prerequisites]
    assert any("power attack" in p for p in prereqs_lower), (
        f"Expected 'Power Attack' in cleave.prerequisites, got {feat.prerequisites}"
    )


# ---------------------------------------------------------------------------
# FP-003: improved_disarm requires combat_expertise
# ---------------------------------------------------------------------------
def test_fp_003_improved_disarm_requires_combat_expertise():
    """improved_disarm requires Combat Expertise (PHB p.95)."""
    feat = FEAT_REGISTRY["improved_disarm"]
    prereqs_lower = [p.lower() for p in feat.prerequisites]
    assert any("combat expertise" in p for p in prereqs_lower), (
        f"Expected 'Combat Expertise' in improved_disarm.prerequisites, "
        f"got {feat.prerequisites}"
    )


# ---------------------------------------------------------------------------
# FP-004: rapid_shot requires DEX 13 and point_blank_shot
# ---------------------------------------------------------------------------
def test_fp_004_rapid_shot_dex_and_point_blank():
    """rapid_shot requires DEX 13 and Point Blank Shot (PHB p.100)."""
    feat = FEAT_REGISTRY["rapid_shot"]
    prereqs = feat.prerequisites
    prereqs_lower = [p.lower() for p in prereqs]

    assert any("dex 13" in p for p in prereqs_lower), (
        f"Expected 'DEX 13' in rapid_shot.prerequisites, got {prereqs}"
    )
    assert any("point blank shot" in p for p in prereqs_lower), (
        f"Expected 'Point Blank Shot' in rapid_shot.prerequisites, got {prereqs}"
    )


# ---------------------------------------------------------------------------
# FP-005: great_fortitude has no prerequisites
# ---------------------------------------------------------------------------
def test_fp_005_great_fortitude_no_prereqs():
    """great_fortitude has no prerequisites (PHB p.94)."""
    feat = FEAT_REGISTRY["great_fortitude"]
    assert len(feat.prerequisites) == 0, (
        f"Expected empty prerequisites for great_fortitude, got {feat.prerequisites}"
    )


# ---------------------------------------------------------------------------
# FP-006: greater_spell_penetration requires spell_penetration
# ---------------------------------------------------------------------------
def test_fp_006_greater_spell_penetration_requires_spell_penetration():
    """greater_spell_penetration requires Spell Penetration (PHB p.94)."""
    feat = FEAT_REGISTRY["greater_spell_penetration"]
    prereqs_lower = [p.lower() for p in feat.prerequisites]
    assert any("spell penetration" in p for p in prereqs_lower), (
        f"Expected 'Spell Penetration' in greater_spell_penetration.prerequisites, "
        f"got {feat.prerequisites}"
    )


# ---------------------------------------------------------------------------
# FP-007: diehard requires endurance
# ---------------------------------------------------------------------------
def test_fp_007_diehard_requires_endurance():
    """diehard requires Endurance (PHB p.93)."""
    feat = FEAT_REGISTRY["diehard"]
    prereqs_lower = [p.lower() for p in feat.prerequisites]
    assert any("endurance" in p for p in prereqs_lower), (
        f"Expected 'Endurance' in diehard.prerequisites, got {feat.prerequisites}"
    )


# ---------------------------------------------------------------------------
# FP-008: coverage — at least 20 feats have non-empty prerequisites
# ---------------------------------------------------------------------------
def test_fp_008_prereq_coverage_at_least_20():
    """At least 20 feats in FEAT_REGISTRY have non-empty prerequisites."""
    feats_with_prereqs = [
        feat_id for feat_id, feat in FEAT_REGISTRY.items()
        if feat.prerequisites
    ]
    assert len(feats_with_prereqs) >= 20, (
        f"Expected at least 20 feats with prerequisites, "
        f"found only {len(feats_with_prereqs)}: {feats_with_prereqs}"
    )
