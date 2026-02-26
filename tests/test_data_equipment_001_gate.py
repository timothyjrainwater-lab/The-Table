"""Gate tests for WO-DATA-EQUIPMENT-001 — Armor and Weapon Catalog.

Gate label: DATA-EQUIPMENT-001
Tests: EQ-001 through EQ-008
"""
import pytest
from aidm.data.equipment_definitions import ARMOR_REGISTRY, ArmorDefinition


# EQ-001: Leather armor ASF is 10%
def test_eq_001_leather_armor_asf():
    assert ARMOR_REGISTRY["leather_armor"].arcane_spell_failure == 10


# EQ-002: Chain shirt max DEX bonus is 4
def test_eq_002_chain_shirt_max_dex():
    assert ARMOR_REGISTRY["chain_shirt"].max_dex_bonus == 4


# EQ-003: Full plate armor check penalty is -6
def test_eq_003_full_plate_acp():
    assert ARMOR_REGISTRY["full_plate"].armor_check_penalty == -6


# EQ-004: Full plate ASF is 35%
def test_eq_004_full_plate_asf():
    assert ARMOR_REGISTRY["full_plate"].arcane_spell_failure == 35


# EQ-005: Chain shirt is light armor
def test_eq_005_chain_shirt_type():
    assert ARMOR_REGISTRY["chain_shirt"].armor_type == "light"


# EQ-006: Full plate is heavy armor
def test_eq_006_full_plate_type():
    assert ARMOR_REGISTRY["full_plate"].armor_type == "heavy"


# EQ-007: Registry sanity floor — at least 10 armor types
def test_eq_007_registry_size_floor():
    assert len(ARMOR_REGISTRY) >= 10, (
        f"ARMOR_REGISTRY has only {len(ARMOR_REGISTRY)} entries — expected ≥ 10"
    )


# EQ-008: Non-existent armor key raises KeyError (no silent crash)
def test_eq_008_nonexistent_key_raises():
    try:
        _ = ARMOR_REGISTRY["nonexistent_armor_xyz"]
        assert False, "Expected KeyError for unknown armor key"
    except KeyError:
        pass  # Expected behavior
