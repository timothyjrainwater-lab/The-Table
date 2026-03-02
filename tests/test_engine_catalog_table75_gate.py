"""Gate tests for WO-ENGINE-CATALOG-TABLE75-COMPLETENESS-001.

CT75-001..008 — PHB Table 7-5 (p.116) ranged/thrown weapons added to equipment_catalog.json.
Weapons: crossbow_heavy, hand_crossbow, light_hammer, throwing_axe, bola.
net excluded (entangle mechanic deferred — FINDING-ENGINE-NET-CATALOG-SPECIAL-001).
"""
import json
import os
import pytest

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "aidm", "data")

with open(os.path.join(_DATA_DIR, "equipment_catalog.json"), encoding="utf-8") as _f:
    _CATALOG = json.load(_f)["weapons"]


# ---------------------------------------------------------------------------
# CT75-001: crossbow_heavy present; damage_dice=="1d10", grip_hands==2
# ---------------------------------------------------------------------------
def test_ct75_001_crossbow_heavy_damage_and_grip():
    assert "crossbow_heavy" in _CATALOG, "CT75-001: crossbow_heavy must be in catalog (PHB Table 7-5 p.116)"
    entry = _CATALOG["crossbow_heavy"]
    assert entry.get("damage_dice") == "1d10", (
        f"CT75-001: crossbow_heavy damage_dice must be '1d10' (PHB p.116), got {entry.get('damage_dice')!r}"
    )
    assert entry.get("grip_hands") == 2, (
        f"CT75-001: crossbow_heavy grip_hands must be 2 (two-handed ranged), got {entry.get('grip_hands')!r}"
    )


# ---------------------------------------------------------------------------
# CT75-002: crossbow_heavy critical_range==19, proficiency_group=="martial", range_increment_ft==120
# ---------------------------------------------------------------------------
def test_ct75_002_crossbow_heavy_crit_prof_range():
    entry = _CATALOG["crossbow_heavy"]
    assert entry.get("critical_range") == 19, (
        f"CT75-002: crossbow_heavy critical_range must be 19 (19-20/×2, PHB p.116), got {entry.get('critical_range')!r}"
    )
    assert entry.get("proficiency_group") == "martial", (
        f"CT75-002: crossbow_heavy proficiency_group must be 'martial' (PHB p.116), got {entry.get('proficiency_group')!r}"
    )
    assert entry.get("range_increment_ft") == 120, (
        f"CT75-002: crossbow_heavy range_increment_ft must be 120 (PHB p.116), got {entry.get('range_increment_ft')!r}"
    )


# ---------------------------------------------------------------------------
# CT75-003: hand_crossbow present; damage_dice=="1d4", grip_hands==1, proficiency_group=="exotic"
# ---------------------------------------------------------------------------
def test_ct75_003_hand_crossbow_fields():
    assert "hand_crossbow" in _CATALOG, "CT75-003: hand_crossbow must be in catalog (PHB Table 7-5 p.116)"
    entry = _CATALOG["hand_crossbow"]
    assert entry.get("damage_dice") == "1d4", (
        f"CT75-003: hand_crossbow damage_dice must be '1d4' (PHB p.116), got {entry.get('damage_dice')!r}"
    )
    assert entry.get("grip_hands") == 1, (
        f"CT75-003: hand_crossbow grip_hands must be 1 (one-handed ranged), got {entry.get('grip_hands')!r}"
    )
    assert entry.get("proficiency_group") == "exotic", (
        f"CT75-003: hand_crossbow proficiency_group must be 'exotic' (PHB p.116), got {entry.get('proficiency_group')!r}"
    )


# ---------------------------------------------------------------------------
# CT75-004: hand_crossbow critical_range==19, range_increment_ft==30
# ---------------------------------------------------------------------------
def test_ct75_004_hand_crossbow_crit_range():
    entry = _CATALOG["hand_crossbow"]
    assert entry.get("critical_range") == 19, (
        f"CT75-004: hand_crossbow critical_range must be 19 (19-20/×2, PHB p.116), got {entry.get('critical_range')!r}"
    )
    assert entry.get("range_increment_ft") == 30, (
        f"CT75-004: hand_crossbow range_increment_ft must be 30 (PHB p.116), got {entry.get('range_increment_ft')!r}"
    )


# ---------------------------------------------------------------------------
# CT75-005: light_hammer present; damage_dice=="1d4", grip_hands==1,
# proficiency_group=="simple", range_increment_ft==20
# ---------------------------------------------------------------------------
def test_ct75_005_light_hammer_fields():
    assert "light_hammer" in _CATALOG, "CT75-005: light_hammer must be in catalog (PHB Table 7-5 p.116)"
    entry = _CATALOG["light_hammer"]
    assert entry.get("damage_dice") == "1d4", (
        f"CT75-005: light_hammer damage_dice must be '1d4' (PHB p.116), got {entry.get('damage_dice')!r}"
    )
    assert entry.get("grip_hands") == 1, (
        f"CT75-005: light_hammer grip_hands must be 1, got {entry.get('grip_hands')!r}"
    )
    assert entry.get("proficiency_group") == "simple", (
        f"CT75-005: light_hammer proficiency_group must be 'simple' (PHB p.116), got {entry.get('proficiency_group')!r}"
    )
    assert entry.get("range_increment_ft") == 20, (
        f"CT75-005: light_hammer range_increment_ft must be 20 ft (PHB p.116), got {entry.get('range_increment_ft')!r}"
    )


# ---------------------------------------------------------------------------
# CT75-006: throwing_axe present; damage_dice=="1d6", grip_hands==1,
# proficiency_group=="martial", range_increment_ft==10
# ---------------------------------------------------------------------------
def test_ct75_006_throwing_axe_fields():
    assert "throwing_axe" in _CATALOG, "CT75-006: throwing_axe must be in catalog (PHB Table 7-5 p.116)"
    entry = _CATALOG["throwing_axe"]
    assert entry.get("damage_dice") == "1d6", (
        f"CT75-006: throwing_axe damage_dice must be '1d6' (PHB p.116), got {entry.get('damage_dice')!r}"
    )
    assert entry.get("grip_hands") == 1, (
        f"CT75-006: throwing_axe grip_hands must be 1, got {entry.get('grip_hands')!r}"
    )
    assert entry.get("proficiency_group") == "martial", (
        f"CT75-006: throwing_axe proficiency_group must be 'martial' (PHB p.116), got {entry.get('proficiency_group')!r}"
    )
    assert entry.get("range_increment_ft") == 10, (
        f"CT75-006: throwing_axe range_increment_ft must be 10 ft (PHB p.116), got {entry.get('range_increment_ft')!r}"
    )


# ---------------------------------------------------------------------------
# CT75-007: bola present; damage_dice=="1d4", grip_hands==1,
# proficiency_group=="exotic", range_increment_ft==10
# ---------------------------------------------------------------------------
def test_ct75_007_bola_fields():
    assert "bola" in _CATALOG, "CT75-007: bola must be in catalog (PHB Table 7-5 p.116)"
    entry = _CATALOG["bola"]
    assert entry.get("damage_dice") == "1d4", (
        f"CT75-007: bola damage_dice must be '1d4' (PHB p.116), got {entry.get('damage_dice')!r}"
    )
    assert entry.get("grip_hands") == 1, (
        f"CT75-007: bola grip_hands must be 1, got {entry.get('grip_hands')!r}"
    )
    assert entry.get("proficiency_group") == "exotic", (
        f"CT75-007: bola proficiency_group must be 'exotic' (PHB p.116), got {entry.get('proficiency_group')!r}"
    )
    assert entry.get("range_increment_ft") == 10, (
        f"CT75-007: bola range_increment_ft must be 10 ft (PHB p.116), got {entry.get('range_increment_ft')!r}"
    )


# ---------------------------------------------------------------------------
# CT75-008: Canary — all 5 new keys simultaneously present in catalog
# ---------------------------------------------------------------------------
def test_ct75_008_canary_all_five_keys_present():
    expected = {"crossbow_heavy", "hand_crossbow", "light_hammer", "throwing_axe", "bola"}
    present = expected & set(_CATALOG.keys())
    missing = expected - present
    assert not missing, (
        f"CT75-008 CANARY: All 5 Table 7-5 weapons must be in catalog. Missing: {sorted(missing)}"
    )
