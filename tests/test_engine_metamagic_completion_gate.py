"""Gate tests: WO-ENGINE-METAMAGIC-COMPLETION-001

Enlarge Spell (PHB p.94) and Widen Spell (PHB p.100) added to metamagic registry.
Completes 9/9 PHB metamagic feats.

MMC-001 – MMC-008 (8 tests)
"""
import pytest

from aidm.core.metamagic_resolver import (
    METAMAGIC_SLOT_COST,
    _FEAT_NAMES,
    _VALID_METAMAGIC,
    validate_metamagic,
    compute_effective_slot_level,
)
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# MMC-001: "enlarge" in METAMAGIC_SLOT_COST with cost == 1
# ---------------------------------------------------------------------------

def test_mmc_001_enlarge_slot_cost():
    """MMC-001: Enlarge Spell slot cost is 1."""
    assert "enlarge" in METAMAGIC_SLOT_COST
    assert METAMAGIC_SLOT_COST["enlarge"] == 1


# ---------------------------------------------------------------------------
# MMC-002: "widen" in METAMAGIC_SLOT_COST with cost == 3
# ---------------------------------------------------------------------------

def test_mmc_002_widen_slot_cost():
    """MMC-002: Widen Spell slot cost is 3."""
    assert "widen" in METAMAGIC_SLOT_COST
    assert METAMAGIC_SLOT_COST["widen"] == 3


# ---------------------------------------------------------------------------
# MMC-003: "enlarge" in _FEAT_NAMES → "Enlarge Spell"
# ---------------------------------------------------------------------------

def test_mmc_003_enlarge_feat_name():
    """MMC-003: Enlarge maps to 'Enlarge Spell' feat name."""
    assert "enlarge" in _FEAT_NAMES
    assert _FEAT_NAMES["enlarge"] == "Enlarge Spell"


# ---------------------------------------------------------------------------
# MMC-004: "widen" in _FEAT_NAMES → "Widen Spell"
# ---------------------------------------------------------------------------

def test_mmc_004_widen_feat_name():
    """MMC-004: Widen maps to 'Widen Spell' feat name."""
    assert "widen" in _FEAT_NAMES
    assert _FEAT_NAMES["widen"] == "Widen Spell"


# ---------------------------------------------------------------------------
# MMC-005: "enlarge" in _VALID_METAMAGIC
# ---------------------------------------------------------------------------

def test_mmc_005_enlarge_valid():
    """MMC-005: 'enlarge' is in the valid metamagic frozenset."""
    assert "enlarge" in _VALID_METAMAGIC


# ---------------------------------------------------------------------------
# MMC-006: "widen" in _VALID_METAMAGIC
# ---------------------------------------------------------------------------

def test_mmc_006_widen_valid():
    """MMC-006: 'widen' is in the valid metamagic frozenset."""
    assert "widen" in _VALID_METAMAGIC


# ---------------------------------------------------------------------------
# MMC-007: len(METAMAGIC_SLOT_COST) == 9 (all 9 PHB metamagic feats)
# ---------------------------------------------------------------------------

def test_mmc_007_total_count():
    """MMC-007: Registry has exactly 9 metamagic feats (complete PHB set)."""
    assert len(METAMAGIC_SLOT_COST) == 9
    assert len(_FEAT_NAMES) == 9
    assert len(_VALID_METAMAGIC) == 9


# ---------------------------------------------------------------------------
# MMC-008: compute_effective_slot_level tests for enlarge and widen
# ---------------------------------------------------------------------------

def test_mmc_008_effective_slot_level():
    """MMC-008: Effective slot level computation for enlarge (+1) and widen (+3)."""
    # Fireball (L3) + Enlarge → slot 4
    assert compute_effective_slot_level(3, ["enlarge"]) == 4
    # Fireball (L3) + Widen → slot 6
    assert compute_effective_slot_level(3, ["widen"]) == 6
    # Fireball (L3) + Enlarge + Empower → slot 6 (3+1+2)
    assert compute_effective_slot_level(3, ["enlarge", "empower"]) == 6
    # Caster with Enlarge Spell feat passes validation
    caster = {EF.FEATS: ["Enlarge Spell"]}
    assert validate_metamagic(["enlarge"], caster) is None
    # Caster without Enlarge Spell feat fails validation
    caster_no_feat = {EF.FEATS: ["Extend Spell"]}
    assert validate_metamagic(["enlarge"], caster_no_feat) == "missing_metamagic_feat"
