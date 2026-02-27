"""Gate tests for WO-ENGINE-UNCANNY-DODGE-CLASS-FIX-001.

Verifies:
  - Barbarian L2 retains DEX when flat-footed (PHB p.26 — unchanged)
  - Rogue L4 retains DEX (PHB p.50 — threshold fixed from L2→L4)
  - Rogue L2/L3 no longer retains DEX (KEY regression fix)
  - Ranger has NO uncanny dodge at any level (PHB p.48)
  - Multiclass barbarian 2 / rogue 1 retains DEX via barbarian
  - Non-UD class does not retain DEX

Authority: RAW — PHB p.26, p.48, p.50
"""

import pytest
from aidm.core.attack_resolver import _target_retains_dex_via_uncanny_dodge
from aidm.schemas.entity_fields import EF


def _make_entity(class_levels: dict, conditions: dict | None = None) -> dict:
    return {
        EF.CLASS_LEVELS: class_levels,
        EF.CONDITIONS: conditions or {},
    }


# ---------- UDCF-001: Barbarian L2 retains DEX (correct — unchanged) ----------
def test_udcf_001_barbarian_l2_retains_dex():
    entity = _make_entity({"barbarian": 2})
    assert _target_retains_dex_via_uncanny_dodge(entity) is True


# ---------- UDCF-002: Barbarian L1 does NOT retain DEX (below threshold) ----------
def test_udcf_002_barbarian_l1_no_ud():
    entity = _make_entity({"barbarian": 1})
    assert _target_retains_dex_via_uncanny_dodge(entity) is False


# ---------- UDCF-003: Rogue L4 retains DEX (threshold fix) ----------
def test_udcf_003_rogue_l4_retains_dex():
    entity = _make_entity({"rogue": 4})
    assert _target_retains_dex_via_uncanny_dodge(entity) is True


# ---------- UDCF-004: Rogue L3 does NOT retain DEX (below new threshold — KEY) ----------
def test_udcf_004_rogue_l3_no_ud():
    entity = _make_entity({"rogue": 3})
    assert _target_retains_dex_via_uncanny_dodge(entity) is False


# ---------- UDCF-005: Rogue L2 does NOT retain DEX (was incorrectly retaining — KEY) ----------
def test_udcf_005_rogue_l2_no_ud():
    entity = _make_entity({"rogue": 2})
    assert _target_retains_dex_via_uncanny_dodge(entity) is False


# ---------- UDCF-006: Ranger ANY level does NOT retain DEX (removed — KEY) ----------
def test_udcf_006_ranger_no_ud_any_level():
    for level in [1, 4, 10, 20]:
        entity = _make_entity({"ranger": level})
        assert _target_retains_dex_via_uncanny_dodge(entity) is False, (
            f"Ranger L{level} should NOT have uncanny dodge (PHB p.48)"
        )


# ---------- UDCF-007: Multiclass Barbarian 2 / Rogue 1 retains via barbarian ----------
def test_udcf_007_multiclass_barb2_rogue1():
    entity = _make_entity({"barbarian": 2, "rogue": 1})
    assert _target_retains_dex_via_uncanny_dodge(entity) is True


# ---------- UDCF-008: No UD-eligible class → no DEX retention ----------
def test_udcf_008_no_ud_class():
    entity = _make_entity({"fighter": 10})
    assert _target_retains_dex_via_uncanny_dodge(entity) is False
