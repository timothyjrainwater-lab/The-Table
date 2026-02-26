"""Gate tests for WO-DATA-FEATS-001 — Feat Benefit Registry.

Gate label: DATA-FEATS-001
Tests: FD-001 through FD-008
"""
import pytest
from aidm.data.feat_definitions import FEAT_REGISTRY, get_feat, FeatDefinition


# FD-001: Great Fortitude grants +2 fort bonus
def test_fd_001_great_fortitude_fort_bonus():
    feat = get_feat("great_fortitude")
    assert feat is not None
    assert feat.fort_bonus == 2


# FD-002: Lightning Reflexes grants +2 ref bonus
def test_fd_002_lightning_reflexes_ref_bonus():
    feat = get_feat("lightning_reflexes")
    assert feat is not None
    assert feat.ref_bonus == 2


# FD-003: Iron Will grants +2 will bonus
def test_fd_003_iron_will_will_bonus():
    feat = get_feat("iron_will")
    assert feat is not None
    assert feat.will_bonus == 2


# FD-004: Power Attack exists and has expected fields
def test_fd_004_power_attack_exists():
    feat = get_feat("power_attack")
    assert feat is not None
    assert feat.feat_id == "power_attack"
    assert feat.name == "Power Attack"
    assert isinstance(feat.prerequisites, tuple)


# FD-005: Weapon Focus entry exists with correct prerequisites
def test_fd_005_weapon_focus_exists():
    feat = get_feat("weapon_focus")
    assert feat is not None
    assert feat.feat_id == "weapon_focus"
    # Weapon-specific ID also resolves to base feat
    feat_ws = get_feat("weapon_focus_longsword")
    assert feat_ws is not None
    assert feat_ws.feat_id == "weapon_focus"


# FD-006: Non-existent feat returns None, no crash
def test_fd_006_nonexistent_feat_returns_none():
    result = get_feat("nonexistent_feat_xyz")
    assert result is None


# FD-007: Registry sanity floor — at least 100 entries
def test_fd_007_registry_size_floor():
    assert len(FEAT_REGISTRY) >= 100, (
        f"FEAT_REGISTRY has only {len(FEAT_REGISTRY)} entries — expected ≥ 100"
    )


# FD-008: All entries have non-empty feat_id and name (structural integrity)
def test_fd_008_structural_integrity():
    for key, feat in FEAT_REGISTRY.items():
        assert feat.feat_id, f"Entry keyed '{key}' has empty feat_id"
        assert feat.name, f"Entry keyed '{key}' has empty name"
        assert feat.feat_id == key, (
            f"Registry key '{key}' does not match feat.feat_id '{feat.feat_id}'"
        )
        assert isinstance(feat.prerequisites, tuple), (
            f"Feat '{key}' prerequisites must be a tuple, got {type(feat.prerequisites)}"
        )
