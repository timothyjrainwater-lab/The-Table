"""Gate tests for Conditions Format Robustness (WO-ENGINE-AI-WO4).
Gate IDs: CF-001 through CF-008.

Closes:
- FINDING-ENGINE-FLAT-FOOTED-COND-FORMAT-001: {flat_footed: {}} causes KeyError → condition dropped
- FINDING-ENGINE-CONDITIONS-LEGACY-FORMAT-001: list format silently returns 0
"""

import pytest
from aidm.core.conditions import get_condition_modifiers, _normalize_condition_dict
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import ConditionInstance, create_flat_footed_condition


def _make_ws_with_conditions(entity_id: str, conditions: dict) -> WorldState:
    """Build minimal WorldState with given conditions dict."""
    entity = {
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 10,
        EF.CONDITIONS: conditions,
        EF.DEFEATED: False,
    }
    return WorldState(
        ruleset_version="3.5",
        entities={entity_id: entity},
        active_combat=None,
    )


# --- CF-001: {flat_footed: {}} → loses_dex_to_ac = True ---

def test_cf_001_flat_footed_empty_dict_parsed():
    """CF-001: {'flat_footed': {}} → get_condition_modifiers returns loses_dex_to_ac=True."""
    ws = _make_ws_with_conditions("e1", {"flat_footed": {}})
    mods = get_condition_modifiers(ws, "e1")
    assert mods.loses_dex_to_ac is True, (
        f"Expected loses_dex_to_ac=True, got {mods.loses_dex_to_ac}"
    )


# --- CF-002: {flat_footed: <full serialized dict>} → same result ---

def test_cf_002_flat_footed_full_dict_parsed():
    """CF-002: well-formed serialized flat_footed condition → same loses_dex_to_ac=True."""
    ff = create_flat_footed_condition("test", 0)
    ws = _make_ws_with_conditions("e1", {"flat_footed": ff.to_dict()})
    mods = get_condition_modifiers(ws, "e1")
    assert mods.loses_dex_to_ac is True


# --- CF-003: legacy list format → returns 0 (documented behavior, no crash) ---

def test_cf_003_legacy_list_returns_zero():
    """CF-003: legacy list format conditions → zero modifiers (FINDING-ENGINE-CONDITIONS-LEGACY-FORMAT-001)."""
    ws = _make_ws_with_conditions("e1", ["flat_footed"])
    mods = get_condition_modifiers(ws, "e1")
    assert mods.loses_dex_to_ac is False
    assert mods.ac_modifier == 0


# --- CF-004: unknown condition with {} → safely returns 0 (no crash) ---

def test_cf_004_unknown_condition_empty_dict_safe():
    """CF-004: unknown condition id with {} → no crash, condition skipped (0 modifiers)."""
    ws = _make_ws_with_conditions("e1", {"zorp_condition": {}})
    mods = get_condition_modifiers(ws, "e1")
    assert mods.ac_modifier == 0


# --- CF-005: multiple conditions: flat_footed:{} + valid condition → aggregate ---

def test_cf_005_mixed_conditions_aggregate():
    """CF-005: flat_footed:{} combined with another condition → loses_dex_to_ac=True from flat_footed."""
    from aidm.schemas.conditions import create_shaken_condition
    shaken_dict = create_shaken_condition("test", 0).to_dict()
    ws = _make_ws_with_conditions("e1", {
        "flat_footed": {},
        "shaken": shaken_dict,
    })
    mods = get_condition_modifiers(ws, "e1")
    # flat_footed → loses_dex_to_ac=True
    assert mods.loses_dex_to_ac is True
    # shaken → attack_modifier=-2
    assert mods.attack_modifier == -2


# --- CF-006: well-formed dict regression — behavior unchanged ---

def test_cf_006_well_formed_dict_unchanged():
    """CF-006: well-formed flat_footed dict → loses_dex_to_ac=True (regression test)."""
    ff_dict = create_flat_footed_condition("source", 0).to_dict()
    ws = _make_ws_with_conditions("e1", {"flat_footed": ff_dict})
    mods = get_condition_modifiers(ws, "e1")
    assert mods.loses_dex_to_ac is True


# --- CF-007: _normalize_condition_dict returns identity for non-empty dict ---

def test_cf_007_normalize_passthrough_non_empty():
    """CF-007: _normalize_condition_dict with non-empty dict returns original dict unchanged."""
    original = {"condition_type": "stunned", "some_field": True}
    result = _normalize_condition_dict("stunned", original)
    assert result is original  # identity preserved


# --- CF-008: _normalize_condition_dict injects condition_type for empty dict ---

def test_cf_008_normalize_injects_type_for_empty_dict():
    """CF-008: _normalize_condition_dict({}) → {'condition_type': condition_id}."""
    result = _normalize_condition_dict("flat_footed", {})
    assert result == {"condition_type": "flat_footed"}
