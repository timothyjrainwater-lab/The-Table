"""Gate tests: WO-ENGINE-WS-FORMULA-FIX-001

ENGINE-WS-FORMULA-FIX: Wild Shape unlock level L4→L5, uses/day formula
replaced with PHB Table 3-14 lookup table.

WSFF-001 – WSFF-008 (8 tests)
"""
import pytest

from aidm.chargen.builder import build_character
from aidm.core.wild_shape_resolver import (
    _has_wild_shape_feature,
    _get_wild_shape_uses,
    validate_wild_shape,
)
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _druid(level):
    """Build a druid entity via chargen."""
    return build_character("human", "druid", level=level)


def _druid_dict(level):
    """Build a minimal druid entity dict for resolver tests."""
    return {
        EF.ENTITY_ID: "druid1",
        EF.CLASS_LEVELS: {"druid": level},
        EF.WILD_SHAPE_USES_REMAINING: _get_wild_shape_uses(level),
        EF.WILD_SHAPE_ACTIVE: False,
        EF.CONDITIONS: {},
    }


# ---------------------------------------------------------------------------
# WSFF-001: Druid L4 → wild shape uses = 0, transform attempt rejected
# ---------------------------------------------------------------------------

def test_wsff_001_level_4_cannot_wild_shape():
    """WSFF-001: Druid L4 → wild shape uses = 0, unlock level not met."""
    entity = _druid(level=4)
    # Chargen should NOT set WILD_SHAPE_USES_REMAINING at L4
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 0
    # Resolver gate rejects
    assert _has_wild_shape_feature(entity) is False
    assert _get_wild_shape_uses(4) == 0


# ---------------------------------------------------------------------------
# WSFF-002: Druid L5 → wild shape uses = 1
# ---------------------------------------------------------------------------

def test_wsff_002_level_5_one_use():
    """WSFF-002: Druid L5 → wild shape uses = 1 (PHB p.37)."""
    entity = _druid(level=5)
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 1
    assert _has_wild_shape_feature(entity) is True
    assert _get_wild_shape_uses(5) == 1


# ---------------------------------------------------------------------------
# WSFF-003: Druid L7 → wild shape uses = 3 (was 2 under old formula)
# ---------------------------------------------------------------------------

def test_wsff_003_level_7_three_uses():
    """WSFF-003: Druid L7 → 3 uses/day (old formula gave 2)."""
    entity = _druid(level=7)
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 3
    assert _get_wild_shape_uses(7) == 3


# ---------------------------------------------------------------------------
# WSFF-004: Druid L10 → wild shape uses = 4
# ---------------------------------------------------------------------------

def test_wsff_004_level_10_four_uses():
    """WSFF-004: Druid L10 → 4 uses/day."""
    entity = _druid(level=10)
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 4
    assert _get_wild_shape_uses(10) == 4


# ---------------------------------------------------------------------------
# WSFF-005: Druid L14 → wild shape uses = 5
# ---------------------------------------------------------------------------

def test_wsff_005_level_14_five_uses():
    """WSFF-005: Druid L14 → 5 uses/day."""
    entity = _druid(level=14)
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 5
    assert _get_wild_shape_uses(14) == 5


# ---------------------------------------------------------------------------
# WSFF-006: Druid L18 → wild shape uses = 6
# ---------------------------------------------------------------------------

def test_wsff_006_level_18_six_uses():
    """WSFF-006: Druid L18 → 6 uses/day (max)."""
    entity = _druid(level=18)
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 6
    assert _get_wild_shape_uses(18) == 6


# ---------------------------------------------------------------------------
# WSFF-007: Druid L9 → uses = 3 (boundary: same as L7, not 4)
# ---------------------------------------------------------------------------

def test_wsff_007_level_9_boundary_three():
    """WSFF-007: Druid L9 → 3 uses/day (boundary: not yet 4)."""
    entity = _druid(level=9)
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 3
    assert _get_wild_shape_uses(9) == 3


# ---------------------------------------------------------------------------
# WSFF-008: Druid L13 → uses = 4 (boundary: same as L10, not 5)
# ---------------------------------------------------------------------------

def test_wsff_008_level_13_boundary_four():
    """WSFF-008: Druid L13 → 4 uses/day (boundary: not yet 5)."""
    entity = _druid(level=13)
    assert entity.get(EF.WILD_SHAPE_USES_REMAINING, 0) == 4
    assert _get_wild_shape_uses(13) == 4
