"""Gate tests for WO-ENGINE-CONDITIONS-LEGACY-FIX-001.

CLF-001..008 — get_condition_modifiers() raises ValueError on non-dict conditions.
Closes FINDING-ENGINE-CONDITIONS-LEGACY-FIX-001.
CP-16 conditions kernel: conditions data must be dict[str, ConditionInstance].
"""
import pytest
from aidm.core.conditions import get_condition_modifiers
from aidm.core.state import WorldState
from aidm.schemas.conditions import ConditionModifiers
from aidm.schemas.entity_fields import EF


def _make_ws(conditions_value):
    """Build a minimal WorldState with one entity whose EF.CONDITIONS = conditions_value."""
    entity = {EF.CONDITIONS: conditions_value}
    return WorldState(
        ruleset_version="3.5",
        entities={"actor_1": entity},
    )


def _make_ws_no_conditions():
    """WorldState with entity that has no EF.CONDITIONS key set."""
    return WorldState(
        ruleset_version="3.5",
        entities={"actor_1": {}},
    )


def _make_ws_missing_entity():
    """WorldState with no entities at all."""
    return WorldState(ruleset_version="3.5", entities={})


# ---------------------------------------------------------------------------
# CLF-001: list format ["prone"] → ValueError raised
# ---------------------------------------------------------------------------
def test_clf_001_list_format_raises():
    ws = _make_ws(["prone"])
    with pytest.raises(ValueError):
        get_condition_modifiers(ws, "actor_1")


# ---------------------------------------------------------------------------
# CLF-002: string format "prone" → ValueError raised
# ---------------------------------------------------------------------------
def test_clf_002_string_format_raises():
    ws = _make_ws("prone")
    with pytest.raises(ValueError):
        get_condition_modifiers(ws, "actor_1")


# ---------------------------------------------------------------------------
# CLF-003: integer format → ValueError raised
# ---------------------------------------------------------------------------
def test_clf_003_int_format_raises():
    ws = _make_ws(42)
    with pytest.raises(ValueError):
        get_condition_modifiers(ws, "actor_1")


# ---------------------------------------------------------------------------
# CLF-004: ValueError message names the bad type for list input
# ---------------------------------------------------------------------------
def test_clf_004_error_message_names_type():
    ws = _make_ws(["prone"])
    with pytest.raises(ValueError, match="list"):
        get_condition_modifiers(ws, "actor_1")


# ---------------------------------------------------------------------------
# CLF-005: ValueError message includes actor_id
# ---------------------------------------------------------------------------
def test_clf_005_error_message_includes_actor_id():
    ws = _make_ws(["prone"])
    with pytest.raises(ValueError, match="actor_1"):
        get_condition_modifiers(ws, "actor_1")


# ---------------------------------------------------------------------------
# CLF-006: valid dict conditions → no exception, returns ConditionModifiers
# ---------------------------------------------------------------------------
def test_clf_006_valid_dict_no_exception():
    ws = _make_ws({"prone": {}})
    # Should not raise — empty-dict condition handled via factory lookup
    result = get_condition_modifiers(ws, "actor_1")
    assert isinstance(result, ConditionModifiers)


# ---------------------------------------------------------------------------
# CLF-007: empty dict conditions → zero ConditionModifiers, no exception
# ---------------------------------------------------------------------------
def test_clf_007_empty_dict_returns_zero():
    ws = _make_ws({})
    result = get_condition_modifiers(ws, "actor_1")
    assert isinstance(result, ConditionModifiers)
    assert result.ac_modifier == 0
    assert result.attack_modifier == 0


# ---------------------------------------------------------------------------
# CLF-008: missing entity → zero ConditionModifiers (not ValueError)
# ---------------------------------------------------------------------------
def test_clf_008_missing_entity_returns_zero():
    ws = _make_ws_missing_entity()
    result = get_condition_modifiers(ws, "nonexistent")
    assert isinstance(result, ConditionModifiers)
    assert result.ac_modifier == 0
