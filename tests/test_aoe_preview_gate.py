"""Tests for WO-BURST-003-AOE-001: Confirm-Gated AoE Spell Overlay.

Gate: 10 tests.  All must pass.
"""

import io
import sys
from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from aidm.core.aoe_rasterizer import AoEShape, AoEDirection, create_aoe_result
from aidm.core.pending_aoe import PendingAoE
from aidm.core.sensor_events import AOE_PREVIEW_CONFIRMED, AOE_PREVIEW_CANCELLED
from aidm.core.state import WorldState
from aidm.schemas.position import Position
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ws() -> WorldState:
    """Minimal WorldState with two entities for testing."""
    ws = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "kael": {
                "name": "Kael",
                EF.TEAM: "party",
                EF.HP_CURRENT: 30, EF.HP_MAX: 30,
                EF.AC: 16, EF.BAB: 5,
                EF.POSITION: {"x": 0, "y": 1},
                EF.DEFEATED: False,
                "spell_dc_base": 13,
                "caster_level": 5,
            },
            "goblin_a": {
                "name": "Goblin Scout A",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 6, EF.HP_MAX: 6,
                EF.AC: 12, EF.BAB: 1,
                EF.POSITION: {"x": 0, "y": -1},
                EF.DEFEATED: False,
            },
        },
        active_combat={"initiative_order": ["kael", "goblin_a"], "round_index": 0},
    )
    return ws


def _make_pending(ws: WorldState) -> PendingAoE:
    origin = Position(x=0, y=0)
    aoe_result = create_aoe_result(AoEShape.BURST, origin, {"radius_ft": 20})
    return PendingAoE(
        spell_name="Fireball",
        caster_id="kael",
        origin_x=0,
        origin_y=0,
        aoe_result=aoe_result,
        save_dc=14,
    )


# ---------------------------------------------------------------------------
# T-01: PendingAoE is frozen and has correct fields
# ---------------------------------------------------------------------------

def test_t01_pending_aoe_frozen_and_fields():
    origin = Position(x=3, y=-1)
    aoe_result = create_aoe_result(AoEShape.BURST, origin, {"radius_ft": 20})

    pending = PendingAoE(
        spell_name="Fireball",
        caster_id="elara",
        origin_x=3,
        origin_y=-1,
        aoe_result=aoe_result,
        save_dc=16,
    )

    # Check fields
    assert pending.spell_name == "Fireball"
    assert pending.caster_id == "elara"
    assert pending.origin_x == 3
    assert pending.origin_y == -1
    assert pending.aoe_result is aoe_result
    assert pending.save_dc == 16

    # Frozen: mutation must raise
    with pytest.raises((FrozenInstanceError, AttributeError)):
        pending.spell_name = "Cone of Cold"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T-02: _show_aoe_preview produces output with * markers and @ origin
# ---------------------------------------------------------------------------

def test_t02_show_aoe_preview_markers():
    from play import _show_aoe_preview
    ws = _make_ws()

    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        new_ws = _show_aoe_preview(ws, "kael", "fireball", "fireball", 0, 0)
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    assert new_ws is not None, "_show_aoe_preview returned None for a known AoE spell"
    assert "*" in output, "AoE squares should be marked with *"
    assert "@" in output, "Origin should be marked with @"


# ---------------------------------------------------------------------------
# T-03: Entity in AoE square shows ! marker, not *
# ---------------------------------------------------------------------------

def test_t03_entity_in_aoe_shows_danger_marker():
    from play import _show_aoe_preview
    ws = _make_ws()
    # goblin_a at (0, -1) — fireball origin (0, 0), radius 20ft (4 squares)
    # (0, -1) is within a 20ft burst from (0, 0)
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        new_ws = _show_aoe_preview(ws, "kael", "fireball", "fireball", 0, 0)
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    assert new_ws is not None
    # The goblin is in the AoE — its square should show "!"
    assert "!" in output, "Entity in AoE should show ! danger marker"


# ---------------------------------------------------------------------------
# T-04: Entity NOT in AoE shows normal symbol (no !)
# ---------------------------------------------------------------------------

def test_t04_entity_outside_aoe_no_danger_marker():
    from play import _show_aoe_preview
    ws = _make_ws()
    # Move goblin far away — outside the 4-square burst radius
    ws.entities["goblin_a"][EF.POSITION] = {"x": 20, "y": 20}

    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        # Fireball at (0, 0) radius 20ft (4 squares) — goblin at (20,20) is out
        new_ws = _show_aoe_preview(ws, "kael", "fireball", "fireball", 0, 0)
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    assert new_ws is not None
    # The goblin should not produce a ! in the displayed area
    # (It might not even appear in the grid bounds, but definitely no !)
    # We check that "Entities at risk: none" appears
    assert "none" in output.lower() or "!" not in output


# ---------------------------------------------------------------------------
# T-05: Confirm prompt string is exactly "Confirm AoE? [yes/cancel]: "
# ---------------------------------------------------------------------------

def test_t05_confirm_prompt_exact_string():
    from play import _show_aoe_preview
    ws = _make_ws()

    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        new_ws = _show_aoe_preview(ws, "kael", "fireball", "fireball", 0, 0)
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    assert new_ws is not None
    assert "Confirm AoE? [yes/cancel]: " in output


# ---------------------------------------------------------------------------
# T-06: Parser returns ("aoe_confirm", None) for "yes" when pending_aoe active
# ---------------------------------------------------------------------------

def test_t06_parser_yes_returns_aoe_confirm():
    from play import parse_input
    ws = _make_ws()
    ws.pending_aoe = _make_pending(ws)

    action_type, data = parse_input("yes", ws)
    assert action_type == "aoe_confirm"
    assert data is None


# ---------------------------------------------------------------------------
# T-07: Parser returns ("aoe_cancel", None) for "cancel" when pending_aoe active
# ---------------------------------------------------------------------------

def test_t07_parser_cancel_returns_aoe_cancel():
    from play import parse_input
    ws = _make_ws()
    ws.pending_aoe = _make_pending(ws)

    for cancel_word in ("cancel", "no", "n", "back"):
        action_type, data = parse_input(cancel_word, ws)
        assert action_type == "aoe_cancel", f"Expected aoe_cancel for '{cancel_word}', got '{action_type}'"
        assert data is None


# ---------------------------------------------------------------------------
# T-08: Parser returns ("aoe_cancel", None) for any other input when pending_aoe active
# ---------------------------------------------------------------------------

def test_t08_parser_other_input_cancels_when_pending():
    from play import parse_input
    ws = _make_ws()
    ws.pending_aoe = _make_pending(ws)

    for random_input in ("attack goblin", "move 1 1", "help", "status", "map", "look"):
        action_type, data = parse_input(random_input, ws)
        assert action_type == "aoe_cancel", (
            f"Expected aoe_cancel for '{random_input}' when pending_aoe active, got '{action_type}'"
        )
        assert data is None


# ---------------------------------------------------------------------------
# T-09: clear_pending_aoe() sets pending_aoe to None
# ---------------------------------------------------------------------------

def test_t09_clear_pending_aoe():
    ws = _make_ws()
    pending = _make_pending(ws)
    ws.pending_aoe = pending

    assert ws.pending_aoe is not None

    cleared = ws.clear_pending_aoe()
    assert cleared.pending_aoe is None
    # Original is unchanged (deepcopy)
    assert ws.pending_aoe is pending


# ---------------------------------------------------------------------------
# T-10: Sensor event constants exist and have correct values
# ---------------------------------------------------------------------------

def test_t10_sensor_event_constants():
    assert AOE_PREVIEW_CONFIRMED == "aoe_preview_confirmed"
    assert AOE_PREVIEW_CANCELLED == "aoe_preview_cancelled"

    # They must be distinct strings
    assert AOE_PREVIEW_CONFIRMED != AOE_PREVIEW_CANCELLED
