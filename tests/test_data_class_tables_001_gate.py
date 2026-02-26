"""Gate tests for DATA-CLASS-TABLES-001 — Class Progression Registry.

Gate label: DATA-CLASS-TABLES-001
Tests: CT-001 through CT-008
"""
import pytest
from aidm.data.class_definitions import (
    MONK_UDAM_BY_LEVEL,
    CLASS_FEATURE_GRANTS,
    rage_uses_per_day,
    sneak_attack_dice,
)


# CT-001: Monk UDAM at level 1 is (1d4, 1d6) — small/medium (PHB p.41)
def test_ct_001_monk_udam_level_1():
    assert MONK_UDAM_BY_LEVEL[1] == ("1d4", "1d6")


# CT-002: Monk UDAM at level 20 is (2d8, 2d10) (PHB p.41)
def test_ct_002_monk_udam_level_20():
    assert MONK_UDAM_BY_LEVEL[20] == ("2d8", "2d10")


# CT-003: rage_uses_per_day(1) == 1 (PHB p.25 Table 3-4)
def test_ct_003_rage_uses_level_1():
    assert rage_uses_per_day(1) == 1


# CT-004: rage_uses_per_day(4) == 2 (PHB p.25)
def test_ct_004_rage_uses_level_4():
    assert rage_uses_per_day(4) == 2


# CT-005: rage_uses_per_day(20) == 6 (PHB p.25)
def test_ct_005_rage_uses_level_20():
    assert rage_uses_per_day(20) == 6


# CT-006: sneak_attack_dice(1) == 1 (PHB p.50: level 1 = 1d6)
def test_ct_006_sneak_attack_level_1():
    assert sneak_attack_dice(1) == 1


# CT-007: sneak_attack_dice(10) == 5 (PHB p.50: level 10 = 5d6)
def test_ct_007_sneak_attack_level_10():
    assert sneak_attack_dice(10) == 5


# CT-008: barbarian rage is granted at level 1
def test_ct_008_barbarian_rage_grant_level():
    assert CLASS_FEATURE_GRANTS["barbarian"]["rage"] == 1
