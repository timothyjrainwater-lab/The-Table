"""Gate tests for WO-ENGINE-GRIP-HANDS-SETTER-001.

GHS-001..008 — grip_hands field on ranged two-handed weapons in catalog;
FHS setter updated to check grip_hands in both chargen paths.
PHB Table 7-5 p.116: longbow, shortbow, light crossbow all require two hands.
Note: heavy crossbow absent from catalog — GHS-003 documents the gap.
"""
import json
import os
import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "aidm", "data")

with open(os.path.join(_DATA_DIR, "equipment_catalog.json"), encoding="utf-8") as _f:
    _CATALOG = json.load(_f)["weapons"]


# ---------------------------------------------------------------------------
# GHS-001: catalog["longbow"]["grip_hands"] == 2
# ---------------------------------------------------------------------------
def test_ghs_001_longbow_grip_hands():
    assert _CATALOG["longbow"].get("grip_hands") == 2, (
        f"longbow must have grip_hands=2 (PHB Table 7-5 p.116: two-handed ranged), "
        f"got {_CATALOG['longbow'].get('grip_hands')!r}"
    )


# ---------------------------------------------------------------------------
# GHS-002: catalog["shortbow"]["grip_hands"] == 2
# ---------------------------------------------------------------------------
def test_ghs_002_shortbow_grip_hands():
    assert _CATALOG["shortbow"].get("grip_hands") == 2, (
        f"shortbow must have grip_hands=2 (PHB Table 7-5 p.116: two-handed ranged), "
        f"got {_CATALOG['shortbow'].get('grip_hands')!r}"
    )


# ---------------------------------------------------------------------------
# GHS-003: heavy crossbow absent from catalog — data gap documented
# PHB Table 7-5 p.116: heavy crossbow is also a two-handed ranged weapon.
# Only crossbow_light exists in catalog. Heavy crossbow addition deferred.
# ---------------------------------------------------------------------------
def test_ghs_003_heavy_crossbow_absent_from_catalog():
    assert "heavy_crossbow" not in _CATALOG, (
        "heavy_crossbow unexpectedly appeared in catalog — update GHS-003"
    )
    assert "crossbow_heavy" not in _CATALOG, (
        "crossbow_heavy unexpectedly appeared in catalog — update GHS-003"
    )


# ---------------------------------------------------------------------------
# GHS-004: catalog["crossbow_light"]["grip_hands"] == 2 (key: crossbow_light)
# ---------------------------------------------------------------------------
def test_ghs_004_crossbow_light_grip_hands():
    assert _CATALOG["crossbow_light"].get("grip_hands") == 2, (
        f"crossbow_light must have grip_hands=2 (PHB Table 7-5 p.116: two-handed ranged), "
        f"got {_CATALOG['crossbow_light'].get('grip_hands')!r}"
    )


# ---------------------------------------------------------------------------
# GHS-005: longsword has no grip_hands field — no catalog pollution
# ---------------------------------------------------------------------------
def test_ghs_005_longsword_no_grip_hands_pollution():
    result = _CATALOG.get("longsword", {}).get("grip_hands", 1)
    assert result == 1, (
        f"longsword must not have grip_hands set (defaults to 1), got {result}"
    )


# ---------------------------------------------------------------------------
# GHS-006: chargen — longbow archer gets FREE_HANDS == 0 (corrected from FHS-006)
# ---------------------------------------------------------------------------
def test_ghs_006_longbow_chargen_free_hands_zero():
    entity = build_character("human", "ranger", 5, starting_equipment={"longbow": 1})
    assert entity.get(EF.FREE_HANDS) == 0, (
        f"longbow archer must have FREE_HANDS=0 (grip_hands=2 → both hands occupied), "
        f"got {entity.get(EF.FREE_HANDS)}"
    )


# ---------------------------------------------------------------------------
# GHS-007: regression — dagger wielder gets FREE_HANDS == 1 (unchanged)
# ---------------------------------------------------------------------------
def test_ghs_007_dagger_free_hands_one():
    entity = build_character("human", "fighter", 5, starting_equipment={"dagger": 1})
    assert entity.get(EF.FREE_HANDS) == 1, (
        f"dagger wielder should have FREE_HANDS=1 (one-handed melee, unaffected), "
        f"got {entity.get(EF.FREE_HANDS)}"
    )


# ---------------------------------------------------------------------------
# GHS-008: regression — sling wielder gets FREE_HANDS == 1 (no grip_hands field → default 1)
# ---------------------------------------------------------------------------
def test_ghs_008_sling_free_hands_one():
    entity = build_character("human", "ranger", 5, starting_equipment={"sling": 1})
    assert entity.get(EF.FREE_HANDS) == 1, (
        f"sling wielder should have FREE_HANDS=1 (one-handed ranged, no grip_hands field), "
        f"got {entity.get(EF.FREE_HANDS)}"
    )
