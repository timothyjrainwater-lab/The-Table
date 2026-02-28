"""Gate tests — WO-DATA-FEATS-PREREQS-001
DATA-FEATS-PREREQS gate: 8 tests (FP-001 – FP-008)

Verifies that prerequisite tuples are correctly populated in the data-layer
feat registry (aidm/data/feat_definitions.py).
"""

import pytest
from aidm.data.feat_definitions import FEAT_REGISTRY


# FP-001: power_attack has STR 13 prerequisite
def test_fp_001_power_attack_str_prereq():
    prereqs = FEAT_REGISTRY["power_attack"].prerequisites
    assert any("STR 13" in p for p in prereqs), (
        f"power_attack prereqs missing 'STR 13': {prereqs}"
    )


# FP-002: cleave requires Power Attack (by name)
def test_fp_002_cleave_requires_power_attack():
    prereqs = FEAT_REGISTRY["cleave"].prerequisites
    assert any("Power Attack" in p for p in prereqs), (
        f"cleave prereqs missing 'Power Attack': {prereqs}"
    )


# FP-003: dodge has DEX 13 prerequisite
def test_fp_003_dodge_dex_prereq():
    prereqs = FEAT_REGISTRY["dodge"].prerequisites
    assert any("DEX 13" in p for p in prereqs), (
        f"dodge prereqs missing 'DEX 13': {prereqs}"
    )


# FP-004: point_blank_shot has no prerequisites
def test_fp_004_point_blank_shot_no_prereqs():
    prereqs = FEAT_REGISTRY["point_blank_shot"].prerequisites
    assert len(prereqs) == 0, (
        f"point_blank_shot should have no prereqs, got: {prereqs}"
    )


# FP-005: rapid_shot requires DEX 13 and Point Blank Shot
def test_fp_005_rapid_shot_prereqs():
    prereqs = FEAT_REGISTRY["rapid_shot"].prerequisites
    assert any("DEX 13" in p for p in prereqs), (
        f"rapid_shot prereqs missing 'DEX 13': {prereqs}"
    )
    assert any("Point Blank Shot" in p for p in prereqs), (
        f"rapid_shot prereqs missing 'Point Blank Shot': {prereqs}"
    )


# FP-006: whirlwind_attack has BAB +4 prerequisite (PHB p.102)
def test_fp_006_whirlwind_attack_bab_prereq():
    prereqs = FEAT_REGISTRY["whirlwind_attack"].prerequisites
    assert any("BAB +4" in p for p in prereqs), (
        f"whirlwind_attack prereqs missing 'BAB +4': {prereqs}"
    )


# FP-007: diehard requires Endurance
def test_fp_007_diehard_requires_endurance():
    prereqs = FEAT_REGISTRY["diehard"].prerequisites
    assert any("Endurance" in p for p in prereqs), (
        f"diehard prereqs missing 'Endurance': {prereqs}"
    )


# FP-008: coverage — at least 40 feats in the data registry
def test_fp_008_coverage():
    count = len(FEAT_REGISTRY)
    assert count >= 40, (
        f"Expected >= 40 feats in FEAT_REGISTRY, got {count}"
    )
