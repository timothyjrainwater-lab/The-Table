"""Gate CP-22 - WO-ENGINE-GRAPPLE-001: Full Grapple Implementation.

Tests:
CP22-01: GrappleResult dataclass exists with correct fields
CP22-02: Touch attack miss => grapple_touch_miss event, no grapple established
CP22-03: Touch attack hit + opposed check win => grapple_established event
CP22-04: Touch attack hit + opposed check loss => grapple_check_fail event
CP22-05: grappled condition applied to target on success
CP22-06: grappling condition applied to initiator on success
CP22-07: WorldState.active_combat[grapple_pairs] updated on success
CP22-08: Size modifier applied (large initiator vs medium target: +4 advantage)
CP22-09: Initiator wins tied opposed check (PHB rule)
CP22-10: Escape: target opposed check win => grapple_broken + both conditions cleared
CP22-11: Escape: target opposed check loss => grapple persists
CP22-12: grappling condition blocks 5-foot step (ACTION_DENIED if attempted)
CP22-13: GrappleIntent resolves via standard execute_turn() call path
CP22-14: Zero regressions - CP-17 tests still pass
"""

from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.conditions import apply_condition, has_condition
from aidm.core.maneuver_resolver import (
    GrappleResult,
    resolve_grapple,
    resolve_grapple_escape,
)
from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import Weapon
from aidm.schemas.conditions import (
    ConditionType,
    create_grappled_condition,
    create_grappling_condition,
)
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import GrappleEscapeIntent, GrappleIntent
from aidm.schemas.position import Position


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


# ---------------------------------------------------------------------------
# CP22-01: GrappleResult dataclass exists with correct fields
# ---------------------------------------------------------------------------

def test_cp22_01_grapple_result_dataclass():
    """GrappleResult has all required fields and is frozen."""
    gr = GrappleResult(
        success=True,
        touch_hit=True,
        initiator_roll=15,
        defender_roll=8,
        initiator_id="fighter",
        target_id="orc",
        events=[],
    )
    assert gr.success is True
    assert gr.touch_hit is True
    assert gr.initiator_roll == 15
    assert gr.defender_roll == 8
    assert gr.initiator_id == "fighter"
    assert gr.target_id == "orc"
    assert gr.events == []

    # Must be immutable (frozen=True) — direct attribute assignment raises FrozenInstanceError
    with pytest.raises((AttributeError, TypeError)):
        gr.success = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CP22-02: Touch attack miss => grapple_touch_miss event
# ---------------------------------------------------------------------------

def test_cp22_02_touch_miss_emits_grapple_touch_miss():
    """Touch attack miss emits grapple_touch_miss, grapple not established."""
    ws = _world(_fighter(), _orc(ac=30))
    rng = RNGManager(8)  # Seed 8: touch roll too low for AC 30
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "grapple_touch_miss" in event_types, f"Expected grapple_touch_miss, got: {event_types}"
    assert "grapple_established" not in event_types
    assert result.success is False
    assert not has_condition(new_ws, "orc", "grappled")
    assert not has_condition(new_ws, "fighter", "grappling")


# ---------------------------------------------------------------------------
# CP22-03: Touch hit + opposed win => grapple_established
# ---------------------------------------------------------------------------

def test_cp22_03_success_emits_grapple_established():
    """Touch hit + opposed check win emits grapple_established."""
    ws = _world(_fighter(), _orc())
    rng = RNGManager(0)  # Seed 0 produces grapple success
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "grapple_established" in event_types, f"Expected grapple_established, got: {event_types}"
    assert result.success is True
    # Backward-compat alias must also be emitted
    assert "grapple_success" in event_types


# ---------------------------------------------------------------------------
# CP22-04: Touch hit + opposed loss => grapple_check_fail
# ---------------------------------------------------------------------------

def test_cp22_04_opposed_loss_emits_grapple_check_fail():
    """Opposed check loss emits grapple_check_fail."""
    # Strong large orc ensures check loss
    ws = _world(_fighter(), _orc(bab=8, str_mod=10, size="large"))
    rng = RNGManager(0)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "grapple_check_fail" in event_types, f"Expected grapple_check_fail, got: {event_types}"
    assert "grapple_established" not in event_types
    assert result.success is False


# ---------------------------------------------------------------------------
# CP22-05: grappled condition applied to target on success
# ---------------------------------------------------------------------------

def test_cp22_05_grappled_condition_applied_to_target():
    """On grapple success, target receives grappled condition."""
    ws = _world(_fighter(), _orc())
    rng = RNGManager(0)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    assert result.success is True
    assert has_condition(new_ws, "orc", "grappled"), "Target should have grappled condition"


# ---------------------------------------------------------------------------
# CP22-06: grappling condition applied to initiator on success
# ---------------------------------------------------------------------------

def test_cp22_06_grappling_condition_applied_to_initiator():
    """On grapple success, initiator receives grappling condition."""
    ws = _world(_fighter(), _orc())
    rng = RNGManager(0)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    assert result.success is True
    assert has_condition(new_ws, "fighter", "grappling"), "Initiator should have grappling condition"


# ---------------------------------------------------------------------------
# CP22-07: grapple_pairs updated in active_combat on success
# ---------------------------------------------------------------------------

def test_cp22_07_grapple_pairs_updated_on_success():
    """On success, active_combat[grapple_pairs] gets [attacker_id, target_id]."""
    ws = _world(_fighter(), _orc())
    rng = RNGManager(0)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    assert result.success is True
    assert new_ws.active_combat is not None
    pairs = new_ws.active_combat.get("grapple_pairs", [])
    assert ["fighter", "orc"] in pairs, f"Expected [fighter, orc] in pairs, got: {pairs}"


# ---------------------------------------------------------------------------
# CP22-08: Size modifier applied (large +4 vs medium 0)
# ---------------------------------------------------------------------------

def test_cp22_08_size_modifier_applied_to_grapple_check():
    """Large initiator gets +4 grapple check advantage over medium defender."""
    from aidm.schemas.maneuvers import get_size_modifier

    large_mod = get_size_modifier("large")
    medium_mod = get_size_modifier("medium")

    assert large_mod == 4, f"Expected 4, got {large_mod}"
    assert medium_mod == 0, f"Expected 0, got {medium_mod}"
    assert large_mod - medium_mod == 4

    # Large ogre vs medium halfling - ogre wins with high probability
    ws = _world(
        _fighter(eid="ogre", team="monsters", bab=4, str_mod=5, size="large", ac=14),
        _orc(eid="halfling", team="party", bab=3, str_mod=-1, size="medium", ac=16),
    )
    wins = 0
    for seed in range(50):
        rng = RNGManager(seed)
        intent = GrappleIntent(attacker_id="ogre", target_id="halfling")
        evts, new_ws, res = resolve_grapple(intent, ws, rng, 0, 0.0)
        if res.success:
            wins += 1
    # Large attacker with high STR should win majority
    assert wins > 25, f"Large attacker won only {wins}/50 - size modifier may not be applied"


# ---------------------------------------------------------------------------
# CP22-09: Initiator wins tied opposed check
# ---------------------------------------------------------------------------

def test_cp22_09_initiator_wins_tie():
    """When opposed grapple check is tied, initiator wins (PHB p.156)."""
    # Use equal modifiers for both (BAB=0, STR=0, size=medium)
    # Seed 43 produces a tie on the opposed grapple check
    ws = _world(
        _fighter(bab=0, str_mod=0, size="medium"),
        _orc(bab=0, str_mod=0, size="medium"),
    )
    rng = RNGManager(43)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")
    events, new_ws, result = resolve_grapple(intent, ws, rng, 0, 0.0)

    # Verify it was a tie by checking the opposed_check event
    opposed_events = [e for e in events if e.event_type == "opposed_check"]
    assert len(opposed_events) == 1
    payload = opposed_events[0].payload
    att_total = payload["attacker_total"]
    def_total = payload["defender_total"]
    assert att_total == def_total, f"Expected tie, got {att_total} vs {def_total}"

    # Initiator must win on tie
    assert result.success is True, "Initiator should win on tie"
    assert "grapple_established" in [e.event_type for e in events]


# ---------------------------------------------------------------------------
# CP22-10: Escape success => grapple_broken + both conditions cleared
# ---------------------------------------------------------------------------

def test_cp22_10_escape_success_clears_conditions_and_pair():
    """Successful escape emits grapple_broken and removes both conditions."""
    ws = _world_with_grapple()
    assert has_condition(ws, "orc", "grappled")
    assert has_condition(ws, "fighter", "grappling")

    rng = RNGManager(0)  # Seed 0: escape succeeds
    events, new_ws = resolve_grapple_escape("orc", "fighter", ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "grapple_broken" in event_types, f"Expected grapple_broken, got: {event_types}"

    # Count condition_removed events
    cond_removed = [e for e in events if e.event_type == "condition_removed"]
    assert len(cond_removed) == 2, f"Expected 2 condition_removed events, got {len(cond_removed)}"

    removed_types = {e.payload.get("condition_type") for e in cond_removed}
    assert "grappled" in removed_types
    assert "grappling" in removed_types

    # Conditions must be removed from world state
    assert not has_condition(new_ws, "orc", "grappled")
    assert not has_condition(new_ws, "fighter", "grappling")

    # grapple_pairs must be cleared
    pairs = new_ws.active_combat.get("grapple_pairs", [])
    assert ["fighter", "orc"] not in pairs and ["orc", "fighter"] not in pairs


# ---------------------------------------------------------------------------
# CP22-11: Escape failure => grapple persists
# ---------------------------------------------------------------------------

def test_cp22_11_escape_failure_grapple_persists():
    """Failed escape emits grapple_escape_failed; conditions remain."""
    ws = _world_with_grapple()
    rng = RNGManager(1)  # Seed 1: escape fails
    events, new_ws = resolve_grapple_escape("orc", "fighter", ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "grapple_escape_failed" in event_types, f"Expected grapple_escape_failed, got: {event_types}"
    assert "grapple_broken" not in event_types

    # Conditions must remain
    assert has_condition(new_ws, "orc", "grappled")
    assert has_condition(new_ws, "fighter", "grappling")

    # grapple_pairs must remain
    pairs = new_ws.active_combat.get("grapple_pairs", [])
    assert ["fighter", "orc"] in pairs


# ---------------------------------------------------------------------------
# CP22-12: grappling condition blocks 5-foot step
# ---------------------------------------------------------------------------

def test_cp22_12_grappling_blocks_5_foot_step():
    """Entity with grappling condition cannot 5-foot step (ACTION_DENIED)."""
    from aidm.schemas.attack import StepMoveIntent

    ws = _world(_fighter(), _orc())
    # Apply grappling condition to the fighter
    ws = apply_condition(ws, "fighter", create_grappling_condition("grapple_attack", 0))

    rng = RNGManager(0)
    ctx = TurnContext(actor_id="fighter", actor_team="party", turn_index=0)
    step_intent = StepMoveIntent(
        actor_id="fighter",
        from_pos=Position(x=0, y=0),
        to_pos=Position(x=1, y=0),
    )

    result = execute_turn(ws, ctx, combat_intent=step_intent, rng=rng)

    assert result.status == "action_denied", f"Expected action_denied, got: {result.status}"
    event_types = [e.event_type for e in result.events]
    assert "action_denied" in event_types

    # Verify correct reason
    denied_events = [e for e in result.events if e.event_type == "action_denied"]
    reasons = [e.payload.get("reason") for e in denied_events]
    assert "grappling_no_step" in reasons, f"Expected grappling_no_step reason, got: {reasons}"


# ---------------------------------------------------------------------------
# CP22-13: GrappleIntent resolves via execute_turn()
# ---------------------------------------------------------------------------

def test_cp22_13_grapple_intent_routes_through_execute_turn():
    """GrappleIntent correctly routed through execute_turn() call path."""
    ws = _world(_fighter(), _orc())
    rng = RNGManager(0)
    ctx = TurnContext(actor_id="fighter", actor_team="party", turn_index=0)
    intent = GrappleIntent(attacker_id="fighter", target_id="orc")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    assert result is not None
    event_types = [e.event_type for e in result.events]
    assert "grapple_declared" in event_types, f"Expected grapple_declared, got: {event_types}"
    # Seed 0 with this world state produces success
    assert "grapple_established" in event_types, f"Expected grapple_established, got: {event_types}"


# ---------------------------------------------------------------------------
# CP22-14: Zero regressions - CP-17 tests still pass
# ---------------------------------------------------------------------------

def test_cp22_14_no_regressions_cp17():
    """Verify CP-17 tests all still pass via subprocess."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_engine_gate_cp17.py", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd="f:/DnD-3.5",
    )

    assert result.returncode == 0, (
        "CP-17 regression tests failed: " + result.stdout + result.stderr
    )
