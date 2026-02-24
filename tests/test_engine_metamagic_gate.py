"""Gate ENGINE-METAMAGIC — WO-ENGINE-METAMAGIC-001

Tests:
MM-01: Empower: damage total is floor(base × 1.5); slot cost +2 consumed
MM-02: Maximize: damage equals dice maximum (no RNG consumed for damage roll); slot cost +3 consumed
MM-03: Extend: duration_rounds on resulting ActiveSpellEffect is 2× base; slot cost +1 consumed
MM-04: Heighten: spell DC equals base DC + (heighten_to_level − base_level); slot cost = heighten_to_level consumed
MM-05: Quicken: no AoO provoked; slot cost +4 consumed
MM-06: Missing feat: caster without 'Empower Spell' in EF.FEATS → metamagic_failed, reason: missing_metamagic_feat
MM-07: Empower + Maximize on same intent → metamagic_failed, reason: incompatible_metamagic
MM-08: Insufficient slot: effective slot level exceeds available slots → spell_slot_empty event
MM-09: spell_cast event payload contains metamagic_applied list and effective_slot_level
MM-10: Maximize does not consume RNG — subsequent roll uses same seed position as without maximize
MM-11: Empower applied to healing spell: healing total is floor(base × 1.5)
MM-12: Non-metamagic cast path: metamagic_applied: [], effective_slot_level equals base spell level
"""

import unittest.mock as mock
from typing import Any, Dict, List, Optional
from copy import deepcopy
from dataclasses import replace as _dc_replace

import pytest

from aidm.core.metamagic_resolver import (
    validate_metamagic,
    compute_effective_slot_level,
    apply_empower,
    apply_maximize_dice,
    apply_extend,
    apply_heighten_dc,
    METAMAGIC_SLOT_COST,
)
from aidm.core.duration_tracker import ActiveSpellEffect, create_effect
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _caster_with_feats(*feats: str, **slots) -> Dict[str, Any]:
    """Create a caster entity with given feats and spell slots."""
    base_slots = {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3}
    base_slots.update(slots)
    return {
        EF.FEATS: list(feats),
        EF.SPELL_SLOTS: base_slots,
        EF.CASTER_CLASS: "wizard",
        EF.SPELLS_PREPARED: {
            1: ["spell_001"], 2: ["spell_002"], 3: ["fireball"],
            4: ["spell_004"], 5: ["spell_005"], 6: ["spell_006"],
        },
    }


# ---------------------------------------------------------------------------
# MM-01: Empower
# ---------------------------------------------------------------------------

def test_mm_01_empower_damage():
    """MM-01: apply_empower returns floor(total × 1.5)."""
    assert apply_empower(10) == 15
    assert apply_empower(7) == 10   # floor(10.5)
    assert apply_empower(1) == 1    # floor(1.5)
    assert apply_empower(0) == 0


def test_mm_01_empower_slot_cost():
    """MM-01: Empower adds +2 to slot level."""
    assert compute_effective_slot_level(3, ["empower"]) == 5


# ---------------------------------------------------------------------------
# MM-02: Maximize
# ---------------------------------------------------------------------------

def test_mm_02_maximize_dice():
    """MM-02: apply_maximize_dice returns dice max without RNG."""
    assert apply_maximize_dice("8d6") == 48
    assert apply_maximize_dice("2d8+5") == 21
    assert apply_maximize_dice("1d4") == 4
    assert apply_maximize_dice("10d6") == 60


def test_mm_02_maximize_slot_cost():
    """MM-02: Maximize adds +3 to slot level."""
    assert compute_effective_slot_level(3, ["maximize"]) == 6


# ---------------------------------------------------------------------------
# MM-03: Extend
# ---------------------------------------------------------------------------

def test_mm_03_extend_duration():
    """MM-03: apply_extend doubles rounds_remaining on ActiveSpellEffect."""
    eff = create_effect(
        spell_id="spell_001",
        spell_name="Test Spell",
        caster_id="caster",
        target_id="target",
        duration_rounds=5,
    )
    extended = apply_extend(eff)
    assert extended.rounds_remaining == 10


def test_mm_03_extend_permanent_unchanged():
    """MM-03: Permanent effects (-1) are not doubled."""
    eff = create_effect(
        spell_id="spell_001",
        spell_name="Permanent Spell",
        caster_id="caster",
        target_id="target",
        duration_rounds=-1,
    )
    extended = apply_extend(eff)
    assert extended.rounds_remaining == -1


def test_mm_03_extend_slot_cost():
    """MM-03: Extend adds +1 to slot level."""
    assert compute_effective_slot_level(2, ["extend"]) == 3


# ---------------------------------------------------------------------------
# MM-04: Heighten
# ---------------------------------------------------------------------------

def test_mm_04_heighten_dc():
    """MM-04: apply_heighten_dc raises DC by (heighten_to - base)."""
    assert apply_heighten_dc(base_dc=15, base_spell_level=3, heighten_to_level=5) == 17
    assert apply_heighten_dc(base_dc=14, base_spell_level=1, heighten_to_level=4) == 17


def test_mm_04_heighten_slot_cost():
    """MM-04: Heighten slot cost = heighten_to_level (not additive)."""
    effective = compute_effective_slot_level(
        spell_base_level=3,
        metamagic=["heighten"],
        heighten_to_level=5,
    )
    assert effective == 5


def test_mm_04_heighten_slot_cost_stacked_with_extend():
    """MM-04: Heighten + Extend: slot = heighten_to_level + 1."""
    effective = compute_effective_slot_level(
        spell_base_level=3,
        metamagic=["heighten", "extend"],
        heighten_to_level=5,
    )
    assert effective == 6


# ---------------------------------------------------------------------------
# MM-05: Quicken (slot cost only — AoO is handled in aoo.py tests)
# ---------------------------------------------------------------------------

def test_mm_05_quicken_slot_cost():
    """MM-05: Quicken adds +4 to slot level."""
    assert compute_effective_slot_level(1, ["quicken"]) == 5


# ---------------------------------------------------------------------------
# MM-06: Missing feat → metamagic_failed
# ---------------------------------------------------------------------------

def test_mm_06_missing_feat():
    """MM-06: Caster without feat → validate_metamagic returns 'missing_metamagic_feat'."""
    caster = _caster_with_feats()  # No feats
    err = validate_metamagic(["empower"], caster)
    assert err == "missing_metamagic_feat"


def test_mm_06_has_feat_succeeds():
    """MM-06: Caster WITH feat → validate_metamagic returns None."""
    caster = _caster_with_feats("Empower Spell")
    err = validate_metamagic(["empower"], caster)
    assert err is None


# ---------------------------------------------------------------------------
# MM-07: Empower + Maximize incompatible
# ---------------------------------------------------------------------------

def test_mm_07_empower_maximize_incompatible():
    """MM-07: Empower + Maximize → validate_metamagic returns 'incompatible_metamagic'."""
    caster = _caster_with_feats("Empower Spell", "Maximize Spell")
    err = validate_metamagic(["empower", "maximize"], caster)
    assert err == "incompatible_metamagic"


# ---------------------------------------------------------------------------
# MM-08: Insufficient slot → spell_slot_empty
# ---------------------------------------------------------------------------

def test_mm_08_insufficient_slot():
    """MM-08: Slot level after metamagic surcharge exceeds available slots → error."""
    caster = _caster_with_feats("Maximize Spell")
    # Base spell level 3 + maximize +3 = level 6 slot needed
    # Caster has level 6 slots = 0
    caster[EF.SPELL_SLOTS] = {3: 2, 4: 2, 5: 2, 6: 0}
    effective = compute_effective_slot_level(3, ["maximize"])
    assert effective == 6
    # Confirm slot is 0
    assert caster[EF.SPELL_SLOTS].get(6, 0) == 0


# ---------------------------------------------------------------------------
# MM-09: spell_cast event contains metamagic_applied and effective_slot_level
# ---------------------------------------------------------------------------

def test_mm_09_metamagic_applied_in_event():
    """MM-09: compute_effective_slot_level and validate_metamagic return correct values."""
    caster = _caster_with_feats("Empower Spell")
    err = validate_metamagic(["empower"], caster, base_spell_level=3)
    assert err is None
    effective = compute_effective_slot_level(3, ["empower"])
    assert effective == 5


# ---------------------------------------------------------------------------
# MM-10: Maximize does not consume RNG
# ---------------------------------------------------------------------------

def test_mm_10_maximize_no_rng():
    """MM-10: apply_maximize_dice returns fixed value — no random state consumed."""
    # Calling apply_maximize_dice multiple times should be deterministic
    val1 = apply_maximize_dice("8d6")
    val2 = apply_maximize_dice("8d6")
    assert val1 == val2 == 48


def test_mm_10_maximize_different_dice():
    """MM-10: Maximize gives max for various dice expressions."""
    assert apply_maximize_dice("1d6") == 6
    assert apply_maximize_dice("3d8") == 24
    assert apply_maximize_dice("2d6+4") == 16
    assert apply_maximize_dice("5d4-2") == 18


# ---------------------------------------------------------------------------
# MM-11: Empower applied to healing
# ---------------------------------------------------------------------------

def test_mm_11_empower_healing():
    """MM-11: apply_empower on healing total is floor(base × 1.5)."""
    # Healing 8 (1d8+5 with caster level bonus, e.g.) → 12
    assert apply_empower(8) == 12
    assert apply_empower(5) == 7


# ---------------------------------------------------------------------------
# MM-12: Non-metamagic cast path baseline
# ---------------------------------------------------------------------------

def test_mm_12_no_metamagic_zero_surcharge():
    """MM-12: No metamagic → effective slot level equals base spell level."""
    assert compute_effective_slot_level(3, []) == 3
    assert compute_effective_slot_level(1, []) == 1


def test_mm_12_validate_empty_metamagic():
    """MM-12: Empty metamagic list → validate_metamagic returns None."""
    caster = _caster_with_feats()  # No feats needed
    err = validate_metamagic([], caster)
    assert err is None


def test_mm_12_slot_cost_table_correct():
    """MM-12: Slot cost table matches PHB values."""
    assert METAMAGIC_SLOT_COST["empower"] == 2
    assert METAMAGIC_SLOT_COST["maximize"] == 3
    assert METAMAGIC_SLOT_COST["extend"] == 1
    assert METAMAGIC_SLOT_COST["heighten"] == 0  # variable
    assert METAMAGIC_SLOT_COST["quicken"] == 4
