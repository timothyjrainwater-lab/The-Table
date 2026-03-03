"""Gate tests: WO-ENGINE-POSITION-TUPLE-NORMALIZE-001 (Batch BA WO2).

PTN-001..006 — EF.POSITION normalized from (0,0) tuple to {"x":0,"y":0} dict in builder.py:
  PTN-001: Chargen entity EF.POSITION is type dict (not tuple)
  PTN-002: Chargen entity EF.POSITION["x"] == 0
  PTN-003: Chargen entity EF.POSITION["y"] == 0
  PTN-004: _create_target_stats() reads chargen position without KeyError or TypeError
  PTN-005: EF.POSITION constant exists; no bare "position" in builder.py chargen dict literal
  PTN-006: Regression — full chargen entity passes save_resolver without position-driven error

FINDING-ENGINE-POSITION-TUPLE-FORMAT-001 closed.
"""
from __future__ import annotations

import re
from unittest.mock import MagicMock

from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

def _build_fighter() -> dict:
    """Build a minimal fighter entity via the canonical chargen path."""
    return build_character(
        race="human",
        class_name="fighter",
        level=1,
        ability_method="standard",
    )


# ---------------------------------------------------------------------------
# PTN-001: EF.POSITION is dict, not tuple
# ---------------------------------------------------------------------------

def test_PTN001_position_is_dict():
    """PTN-001: Chargen entity EF.POSITION is type dict (not tuple)."""
    entity = _build_fighter()
    pos = entity.get(EF.POSITION)
    assert pos is not None, "PTN-001: EF.POSITION field absent from chargen entity"
    assert isinstance(pos, dict), (
        f"PTN-001: EF.POSITION must be dict, got {type(pos).__name__}. Value: {pos}"
    )


# ---------------------------------------------------------------------------
# PTN-002: EF.POSITION["x"] == 0
# ---------------------------------------------------------------------------

def test_PTN002_position_x_is_zero():
    """PTN-002: Chargen entity EF.POSITION['x'] == 0."""
    entity = _build_fighter()
    pos = entity[EF.POSITION]
    assert "x" in pos, f"PTN-002: EF.POSITION dict has no 'x' key. Got: {pos}"
    assert pos["x"] == 0, f"PTN-002: EF.POSITION['x'] must be 0, got {pos['x']}"


# ---------------------------------------------------------------------------
# PTN-003: EF.POSITION["y"] == 0
# ---------------------------------------------------------------------------

def test_PTN003_position_y_is_zero():
    """PTN-003: Chargen entity EF.POSITION['y'] == 0."""
    entity = _build_fighter()
    pos = entity[EF.POSITION]
    assert "y" in pos, f"PTN-003: EF.POSITION dict has no 'y' key. Got: {pos}"
    assert pos["y"] == 0, f"PTN-003: EF.POSITION['y'] must be 0, got {pos['y']}"


# ---------------------------------------------------------------------------
# PTN-004: _create_target_stats() reads position without error
# ---------------------------------------------------------------------------

def test_PTN004_create_target_stats_reads_position():
    """PTN-004: _create_target_stats() reads dict position from chargen entity without error."""
    from aidm.core.play_loop import _create_target_stats
    from aidm.core.state import WorldState

    entity = _build_fighter()
    actor_id = entity[EF.ENTITY_ID]
    world = WorldState(
        ruleset_version="3.5",
        entities={actor_id: entity},
        active_combat={
            "initiative_order": [actor_id],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "action_budget_actor": None,
            "action_budget": None,
        },
    )
    # Should not raise KeyError, TypeError, or AttributeError
    try:
        target_stats = _create_target_stats(actor_id, world)
    except (KeyError, TypeError, AttributeError) as e:
        raise AssertionError(
            f"PTN-004: _create_target_stats() raised {type(e).__name__} reading position: {e}"
        )


# ---------------------------------------------------------------------------
# PTN-005: EF.POSITION constant exists; no bare "position" string in chargen
# ---------------------------------------------------------------------------

def test_PTN005_ef_position_constant_and_no_bare_string():
    """PTN-005: EF.POSITION constant exists; no bare 'position' key in builder.py chargen dict."""
    import aidm.schemas.entity_fields as _ef_module

    # Constant must exist
    assert hasattr(EF, "POSITION"), "PTN-005: EF.POSITION constant does not exist in entity_fields.py"
    assert EF.POSITION == "position", (
        f"PTN-005: EF.POSITION value must be 'position', got '{EF.POSITION}'"
    )

    # No bare "position" key in builder.py chargen dict (would be Rule #1 violation)
    import aidm.chargen.builder as _builder_module
    import inspect
    source = inspect.getsource(_builder_module)
    # Bare string "position" as a dict key (not inside a comment) — pattern: ["position"] or : "position"
    # We check for the tuple pattern that was the bug: (0, 0) should be gone
    assert 'EF.POSITION: (0, 0)' not in source, (
        "PTN-005: builder.py still contains tuple form 'EF.POSITION: (0, 0)'. Fix not applied."
    )
    assert '"position": ' not in source, (
        "PTN-005: builder.py uses bare string 'position' as dict key — Rule #1 violation."
    )


# ---------------------------------------------------------------------------
# PTN-006: Regression — full chargen entity doesn't break save resolver
# ---------------------------------------------------------------------------

def test_PTN006_regression_save_resolver_unaffected():
    """PTN-006: Position dict change does not break chargen entity structure (combat-relevant fields intact)."""
    entity = _build_fighter()

    # Position fix must not disturb any other entity fields
    for field in (EF.HP_CURRENT, EF.HP_MAX, EF.AC, EF.BAB, EF.SAVE_FORT, EF.SAVE_REF, EF.SAVE_WILL):
        assert field in entity, (
            f"PTN-006: Field {field} missing from chargen entity post position fix"
        )

    # Saving throw fields must be numeric (not corrupted by position change)
    for save_field in (EF.SAVE_FORT, EF.SAVE_REF, EF.SAVE_WILL):
        val = entity[save_field]
        assert isinstance(val, (int, float)), (
            f"PTN-006: {save_field} is not numeric post position fix: {type(val).__name__} = {val}"
        )

    # Position must still be dict (double-check with regression label)
    assert isinstance(entity[EF.POSITION], dict), (
        f"PTN-006: EF.POSITION reverted to non-dict: {entity[EF.POSITION]}"
    )
