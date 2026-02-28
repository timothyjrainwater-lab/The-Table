"""Gate tests: WO-ENGINE-STILL-MIND-INDOMITABLE-WILL-001

Still Mind (PHB p.41): Monk L3+ gets +2 all saves vs enchantment.
Indomitable Will (PHB p.26): Barbarian L14+ gets +4 Will vs enchantment while raging.

SMI-001 – SMI-008 (8 tests)
"""
import pytest

from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ws(entity_dict, eid="actor"):
    return WorldState(
        ruleset_version="3.5",
        entities={eid: entity_dict},
        active_combat=None,
    )


def _monk(level=3):
    """Minimal monk entity with given level."""
    return {
        EF.CLASS_LEVELS: {"monk": level},
        EF.SAVE_FORT: 4,   # Type 2: base + ability baked
        EF.SAVE_REF: 4,
        EF.SAVE_WILL: 4,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
    }


def _barbarian(level=14, raging=False):
    """Minimal barbarian entity. If raging=True, set TEMPORARY_MODIFIERS."""
    temp_mods = {}
    if raging and level >= 14:
        temp_mods["indomitable_will_active"] = True
        temp_mods["rage_str_bonus"] = 4
        temp_mods["rage_will_bonus"] = 2
    elif raging:
        temp_mods["rage_str_bonus"] = 4
        temp_mods["rage_will_bonus"] = 2
    return {
        EF.CLASS_LEVELS: {"barbarian": level},
        EF.SAVE_FORT: 6,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 2,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.TEMPORARY_MODIFIERS: temp_mods,
        EF.RAGE_ACTIVE: raging,
    }


# ---------------------------------------------------------------------------
# SMI-001: Monk L3 gets +2 Fort vs enchantment school
# ---------------------------------------------------------------------------

def test_smi_001_monk_l3_fort_enchantment():
    """SMI-001: Monk L3 gets +2 Fort vs enchantment."""
    entity = _monk(level=3)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.FORT, school="enchantment")
    # base_fort=4 + still_mind=2 = 6
    assert bonus == 6, f"Expected 6, got {bonus}"


# ---------------------------------------------------------------------------
# SMI-002: Monk L3 gets +2 Will vs enchantment school
# ---------------------------------------------------------------------------

def test_smi_002_monk_l3_will_enchantment():
    """SMI-002: Monk L3 gets +2 Will vs enchantment."""
    entity = _monk(level=3)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, school="enchantment")
    # base_will=4 + still_mind=2 = 6
    assert bonus == 6, f"Expected 6, got {bonus}"


# ---------------------------------------------------------------------------
# SMI-003: Monk L2 does NOT get Still Mind bonus
# ---------------------------------------------------------------------------

def test_smi_003_monk_l2_no_still_mind():
    """SMI-003: Monk L2 — Still Mind not yet available."""
    entity = _monk(level=2)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, school="enchantment")
    # base_will=4 only (no still mind at L2)
    assert bonus == 4, f"Expected 4, got {bonus}"


# ---------------------------------------------------------------------------
# SMI-004: Monk L3 Still Mind stacks with elf racial enchantment +2
# ---------------------------------------------------------------------------

def test_smi_004_still_mind_stacks_with_racial():
    """SMI-004: Monk L3 Still Mind +2 stacks with elf racial +2 = total +4."""
    entity = _monk(level=3)
    entity[EF.SAVE_BONUS_ENCHANTMENT] = 2  # elf racial
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, school="enchantment")
    # base_will=4 + racial_enchantment=2 + still_mind=2 = 8
    assert bonus == 8, f"Expected 8 (4 base + 2 racial + 2 still mind), got {bonus}"


# ---------------------------------------------------------------------------
# SMI-005: Barbarian L14 in rage gets +4 Will vs enchantment
# ---------------------------------------------------------------------------

def test_smi_005_barb_l14_raging_indomitable_will():
    """SMI-005: Barbarian L14 raging gets +4 Will vs enchantment (Indomitable Will)."""
    entity = _barbarian(level=14, raging=True)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, school="enchantment")
    # base_will=2 + indomitable_will=4 = 6
    assert bonus == 6, f"Expected 6 (2 base + 4 IW), got {bonus}"


# ---------------------------------------------------------------------------
# SMI-006: Barbarian L14 NOT in rage — no Indomitable Will bonus
# ---------------------------------------------------------------------------

def test_smi_006_barb_l14_not_raging_no_iw():
    """SMI-006: Barbarian L14 not raging — no Indomitable Will bonus."""
    entity = _barbarian(level=14, raging=False)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, school="enchantment")
    # base_will=2 only (not raging, no IW)
    assert bonus == 2, f"Expected 2 (no IW when not raging), got {bonus}"


# ---------------------------------------------------------------------------
# SMI-007: Barbarian L13 in rage — no Indomitable Will (level too low)
# ---------------------------------------------------------------------------

def test_smi_007_barb_l13_raging_no_iw():
    """SMI-007: Barbarian L13 raging — level too low for Indomitable Will."""
    entity = _barbarian(level=13, raging=True)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, school="enchantment")
    # base_will=2 (L13: no IW, rage doesn't set indomitable_will_active)
    assert bonus == 2, f"Expected 2 (L13, no IW), got {bonus}"


# ---------------------------------------------------------------------------
# SMI-008: Barbarian L14 in rage, non-enchantment — no Indomitable Will
# ---------------------------------------------------------------------------

def test_smi_008_barb_l14_raging_non_enchantment_no_iw():
    """SMI-008: Barbarian L14 raging, non-enchantment save — no IW bonus."""
    entity = _barbarian(level=14, raging=True)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, school="evocation")
    # base_will=2 (IW only vs enchantment)
    assert bonus == 2, f"Expected 2 (IW doesn't apply to evocation), got {bonus}"
