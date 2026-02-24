"""Gate ENGINE-GRAPPLE-PIN — WO-ENGINE-GRAPPLE-PIN-001: Pinned Condition.

Tests:
GP-01: GrappleIntent against non-grappled target => normal grapple path (no pin)
GP-02: GrappleIntent against already-grappled target, check succeeds => pin_established
GP-03: GrappleIntent against already-grappled target, check fails => pin_attempt_failed
GP-04: After pin_established: target has PINNED, NOT GRAPPLED
GP-05: After pin_established: target has loses_dex_to_ac=True and ac_modifier_melee=-4
GP-06: PinEscapeIntent, check succeeds => pin_escape_success, target reverts to GRAPPLED
GP-07: PinEscapeIntent, check fails => pin_escape_failed, target still PINNED
GP-08: PinEscapeIntent when not pinned => pin_escape_invalid event
GP-09: grapple_pairs persists through pin escalation
GP-10: Zero regressions on CP-22 gate
"""

from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.conditions import apply_condition, has_condition
from aidm.core.maneuver_resolver import resolve_grapple, resolve_pin_escape
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.conditions import (
    ConditionType,
    create_grappled_condition,
    create_grappling_condition,
    create_pinned_condition,
)
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import GrappleIntent, PinEscapeIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pos(x: int = 0, y: int = 0) -> dict:
    return {"x": x, "y": y}


def _fighter(
    eid: str = "fighter",
    team: str = "party",
    bab: int = 5,
    str_mod: int = 3,
    dex_mod: int = 1,
    size: str = "medium",
    ac: int = 16,
    hp: int = 50,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEX_MOD: dex_mod,
        EF.STR_MOD: str_mod,
        EF.BAB: bab,
        "bab": bab,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: _pos(0, 0),
        EF.SIZE_CATEGORY: size,
    }


def _orc(
    eid: str = "orc",
    team: str = "monsters",
    bab: int = 3,
    str_mod: int = 2,
    dex_mod: int = 0,
    size: str = "medium",
    ac: int = 14,
    hp: int = 20,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEX_MOD: dex_mod,
        EF.STR_MOD: str_mod,
        EF.BAB: bab,
        "bab": bab,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: _pos(1, 0),
        EF.SIZE_CATEGORY: size,
    }


def _world(*entity_dicts, grapple_pairs=None) -> WorldState:
    entities = {e[EF.ENTITY_ID]: e for e in entity_dicts}
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": [e[EF.ENTITY_ID] for e in entity_dicts],
            "aoo_used_this_round": [],
            "grapple_pairs": grapple_pairs if grapple_pairs is not None else [],
        },
    )


def _world_with_grapple(attacker_id: str = "fighter", target_id: str = "orc") -> WorldState:
    """World state where grapple is already established."""
    ws = _world(
        _fighter(eid=attacker_id),
        _orc(eid=target_id),
        grapple_pairs=[[attacker_id, target_id]],
    )
    ws = apply_condition(ws, target_id, create_grappled_condition("grapple_attack", 0))
    ws = apply_condition(ws, attacker_id, create_grappling_condition("grapple_attack", 0))
    return ws


def _world_with_pin(attacker_id: str = "fighter", target_id: str = "orc") -> WorldState:
    """World state where pin is established (target pinned, pair still exists)."""
    ws = _world(
        _fighter(eid=attacker_id),
        _orc(eid=target_id),
        grapple_pairs=[[attacker_id, target_id]],
    )
    ws = apply_condition(ws, target_id, create_pinned_condition("grapple_pin", 0))
    ws = apply_condition(ws, attacker_id, create_grappling_condition("grapple_attack", 0))
    return ws


def _find_seed_for_pin_success(ws: WorldState, attacker_id: str, target_id: str, max_seed: int = 200) -> int:
    """Find a seed where the pin attempt succeeds (attacker wins opposed check)."""
    intent = GrappleIntent(attacker_id=attacker_id, target_id=target_id)
    for seed in range(max_seed):
        rng = RNGManager(seed)
        events, _, result = resolve_grapple(intent, ws, rng, 0, 0.0)
        event_types = [e.event_type for e in events]
        if "pin_established" in event_types:
            return seed
    raise RuntimeError(f"Could not find pin success seed in range 0-{max_seed}")


def _find_seed_for_pin_failure(ws: WorldState, attacker_id: str, target_id: str, max_seed: int = 200) -> int:
    """Find a seed where the pin attempt fails (defender wins opposed check)."""
    intent = GrappleIntent(attacker_id=attacker_id, target_id=target_id)
    for seed in range(max_seed):
        rng = RNGManager(seed)
        events, _, result = resolve_grapple(intent, ws, rng, 0, 0.0)
        event_types = [e.event_type for e in events]
        if "pin_attempt_failed" in event_types:
            return seed
    raise RuntimeError(f"Could not find pin failure seed in range 0-{max_seed}")


def _find_seed_for_escape_success(ws: WorldState, initiator_id: str, pinner_id: str, max_seed: int = 200) -> int:
    """Find a seed where pin escape succeeds."""
    intent = PinEscapeIntent(attacker_id=initiator_id, target_id=pinner_id)
    for seed in range(max_seed):
        rng = RNGManager(seed)
        events, _, result = resolve_pin_escape(intent, ws, rng, 0, 0.0)
        if result.success:
            return seed
    raise RuntimeError(f"Could not find pin escape success seed in range 0-{max_seed}")


def _find_seed_for_escape_failure(ws: WorldState, initiator_id: str, pinner_id: str, max_seed: int = 200) -> int:
    """Find a seed where pin escape fails."""
    intent = PinEscapeIntent(attacker_id=initiator_id, target_id=pinner_id)
    for seed in range(max_seed):
        rng = RNGManager(seed)
        events, _, result = resolve_pin_escape(intent, ws, rng, 0, 0.0)
        if not result.success:
            return seed
    raise RuntimeError(f"Could not find pin escape failure seed in range 0-{max_seed}")


# ---------------------------------------------------------------------------
# GP-01: Normal grapple path for non-grappled target
# ---------------------------------------------------------------------------

def test_gp01_normal_grapple_no_pin_on_fresh_target():
    """GrappleIntent against a non-grappled target takes normal path (grapple_established, not pin)."""
    ws = _world(_fighter(), _orc())  # No grapple_pairs, no conditions
    rng = RNGManager(0)  # Seed 0 produces grapple success
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "grapple_established" in event_types, f"Expected grapple_established, got: {event_types}"
    assert "pin_established" not in event_types, "Should NOT pin on fresh target"
    assert "pin_attempt_failed" not in event_types


# ---------------------------------------------------------------------------
# GP-02: Pin established on success against already-grappled target
# ---------------------------------------------------------------------------

def test_gp02_pin_established_on_success_vs_grappled_target():
    """Second GrappleIntent against already-grappled target with check success => pin_established."""
    ws = _world_with_grapple()
    seed = _find_seed_for_pin_success(ws, "fighter", "orc")
    rng = RNGManager(seed)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "pin_established" in event_types, f"Expected pin_established, got: {event_types}"
    assert "grapple_established" not in event_types, "Should NOT emit grapple_established on pin path"


# ---------------------------------------------------------------------------
# GP-03: Pin attempt failed when check fails
# ---------------------------------------------------------------------------

def test_gp03_pin_attempt_failed_on_check_loss():
    """Second GrappleIntent against already-grappled target with check failure => pin_attempt_failed."""
    # Make orc very strong to ensure check failure
    ws = _world(
        _fighter(bab=1, str_mod=0),
        _orc(bab=6, str_mod=8, size="large"),
        grapple_pairs=[["fighter", "orc"]],
    )
    ws = apply_condition(ws, "orc", create_grappled_condition("grapple_attack", 0))
    ws = apply_condition(ws, "fighter", create_grappling_condition("grapple_attack", 0))

    seed = _find_seed_for_pin_failure(ws, "fighter", "orc")
    rng = RNGManager(seed)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "pin_attempt_failed" in event_types, f"Expected pin_attempt_failed, got: {event_types}"
    assert "pin_established" not in event_types


# ---------------------------------------------------------------------------
# GP-04: Target has PINNED (not GRAPPLED) after pin_established
# ---------------------------------------------------------------------------

def test_gp04_target_has_pinned_not_grappled_after_pin():
    """After pin_established, target has PINNED condition and GRAPPLED is removed."""
    ws = _world_with_grapple()
    seed = _find_seed_for_pin_success(ws, "fighter", "orc")
    rng = RNGManager(seed)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    # Must have PINNED
    assert has_condition(new_ws, "orc", ConditionType.PINNED.value), \
        f"Target must have PINNED condition. Conditions: {new_ws.entities['orc'].get(EF.CONDITIONS, {})}"
    # Must NOT have GRAPPLED (pinned supersedes)
    assert not has_condition(new_ws, "orc", ConditionType.GRAPPLED.value), \
        "Target must NOT have GRAPPLED condition after pin"


# ---------------------------------------------------------------------------
# GP-05: Pinned condition has correct helpless modifiers
# ---------------------------------------------------------------------------

def test_gp05_pinned_condition_has_helpless_modifiers():
    """After pin_established, target's PINNED condition has helpless profile."""
    ws = _world_with_grapple()
    seed = _find_seed_for_pin_success(ws, "fighter", "orc")
    rng = RNGManager(seed)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    assert has_condition(new_ws, "orc", ConditionType.PINNED.value)
    conditions = new_ws.entities["orc"].get(EF.CONDITIONS, {})
    pinned = conditions.get(ConditionType.PINNED.value)
    assert pinned is not None

    # Conditions are stored as dicts (via ConditionInstance.to_dict())
    mods = pinned.get("modifiers") if isinstance(pinned, dict) else pinned.modifiers
    if isinstance(mods, dict):
        assert mods.get("loses_dex_to_ac") is True, "Pinned must set loses_dex_to_ac=True"
        assert mods.get("ac_modifier_melee") == -4, f"Expected ac_modifier_melee=-4, got {mods.get('ac_modifier_melee')}"
    else:
        assert mods.loses_dex_to_ac is True, "Pinned must set loses_dex_to_ac=True"
        assert mods.ac_modifier_melee == -4, f"Expected ac_modifier_melee=-4, got {mods.ac_modifier_melee}"


# ---------------------------------------------------------------------------
# GP-06: PinEscapeIntent success => pin_escape_success, reverts to GRAPPLED
# ---------------------------------------------------------------------------

def test_gp06_pin_escape_success_reverts_to_grappled():
    """PinEscapeIntent with check success: pin_escape_success, target reverts to GRAPPLED."""
    ws = _world_with_pin()
    seed = _find_seed_for_escape_success(ws, "orc", "fighter")
    rng = RNGManager(seed)
    intent = PinEscapeIntent(attacker_id="orc", target_id="fighter")
    events, new_ws, result = resolve_pin_escape(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "pin_escape_success" in event_types, f"Expected pin_escape_success, got: {event_types}"
    assert result.success is True

    # Target reverts to GRAPPLED, not PINNED
    assert has_condition(new_ws, "orc", ConditionType.GRAPPLED.value), \
        "Escaped entity should revert to GRAPPLED"
    assert not has_condition(new_ws, "orc", ConditionType.PINNED.value), \
        "PINNED condition must be removed on successful escape"


# ---------------------------------------------------------------------------
# GP-07: PinEscapeIntent failure => pin_escape_failed, still PINNED
# ---------------------------------------------------------------------------

def test_gp07_pin_escape_failure_stays_pinned():
    """PinEscapeIntent with check failure: pin_escape_failed, still PINNED."""
    ws = _world_with_pin()
    seed = _find_seed_for_escape_failure(ws, "orc", "fighter")
    rng = RNGManager(seed)
    intent = PinEscapeIntent(attacker_id="orc", target_id="fighter")
    events, new_ws, result = resolve_pin_escape(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "pin_escape_failed" in event_types, f"Expected pin_escape_failed, got: {event_types}"
    assert result.success is False

    # Target still PINNED
    assert has_condition(new_ws, "orc", ConditionType.PINNED.value), \
        "Target must still be PINNED after failed escape"


# ---------------------------------------------------------------------------
# GP-08: PinEscapeIntent when not pinned => pin_escape_invalid
# ---------------------------------------------------------------------------

def test_gp08_pin_escape_invalid_when_not_pinned():
    """PinEscapeIntent against entity that is not pinned => pin_escape_invalid."""
    ws = _world_with_grapple()  # Orc is GRAPPLED, not PINNED
    rng = RNGManager(0)
    intent = PinEscapeIntent(attacker_id="orc", target_id="fighter")
    events, new_ws, result = resolve_pin_escape(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "pin_escape_invalid" in event_types, f"Expected pin_escape_invalid, got: {event_types}"
    assert result.success is False


# ---------------------------------------------------------------------------
# GP-09: grapple_pairs persists through pin escalation
# ---------------------------------------------------------------------------

def test_gp09_grapple_pairs_persists_through_pin():
    """After pin_established, grapple_pairs entry remains unchanged."""
    ws = _world_with_grapple()
    seed = _find_seed_for_pin_success(ws, "fighter", "orc")
    rng = RNGManager(seed)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    assert new_ws.active_combat is not None
    pairs = new_ws.active_combat.get("grapple_pairs", [])
    assert ["fighter", "orc"] in pairs, f"Expected [fighter, orc] in pairs, got: {pairs}"


# ---------------------------------------------------------------------------
# GP-10: Zero regressions on CP-22 gate
# ---------------------------------------------------------------------------

def test_gp10_no_regressions_cp22():
    """Verify CP-22 tests all still pass via subprocess."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_engine_gate_cp22.py", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd="f:/DnD-3.5",
    )

    assert result.returncode == 0, (
        "CP-22 regression tests failed:\n" + result.stdout + result.stderr
    )
