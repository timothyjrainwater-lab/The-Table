"""Gate tests: WO-ENGINE-RUN-FEAT-SPEED-001 (Batch AZ WO3).

RUN-001..006 — Run feat ×5 multiplier in play_loop.py:
  RUN-001: Entity without Run feat, base_speed=30 → distance_ft=120 (×4)
  RUN-002: Entity with Run feat, base_speed=30 → distance_ft=150 (×5)
  RUN-003: Entity without Run feat, base_speed=20 → distance_ft=80
  RUN-004: Entity with Run feat, base_speed=20 → distance_ft=100
  RUN-005: Regression — run blocked when fatigued (existing guard unchanged)
  RUN-006: Coverage map updated — Run feat row references WO-ENGINE-RUN-FEAT-SPEED-001

PHB p.101: Run feat — multiply base speed by 5 (not 4) when taking Run action.
AUDIT-015 finding closed.
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock

from aidm.core.play_loop import execute_turn
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RunIntent
from aidm.schemas.conditions import create_fatigued_condition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rng(roll: int = 10):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _make_turn_ctx(actor_id: str = "hero"):
    ctx = MagicMock()
    ctx.actor_id = actor_id
    ctx.turn_index = 0
    ctx.actor_team = "players"
    return ctx


def _world_with_runner(actor_id: str = "hero", base_speed: int = 30,
                       feats: list = None, conditions: dict = None) -> WorldState:
    actor = {
        EF.ENTITY_ID: actor_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 15,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: "players",
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: feats if feats is not None else [],
        EF.DEX_MOD: 2,
        EF.BASE_SPEED: base_speed,
    }
    active_combat = {
        "initiative_order": [actor_id],
        "aoo_used_this_round": [],
        "aoo_count_this_round": {},
        "action_budget_actor": None,
        "action_budget": None,
    }
    return WorldState(
        ruleset_version="3.5",
        entities={actor_id: actor},
        active_combat=active_combat,
    )


def _run_distance(world: WorldState, actor_id: str = "hero") -> int:
    """Execute a run action and return the distance_ft from entity_moved event."""
    intent = RunIntent(actor_id=actor_id)
    turn_ctx = _make_turn_ctx(actor_id)
    result = execute_turn(
        world_state=world,
        turn_ctx=turn_ctx,
        doctrine=None,
        combat_intent=intent,
        rng=_make_rng(),
        next_event_id=1,
        timestamp=1.0,
    )
    moved_events = [
        e for e in result.events
        if (hasattr(e, "event_type") and e.event_type == "entity_moved")
        or (isinstance(e, dict) and e.get("event_type") == "entity_moved")
    ]
    assert moved_events, "entity_moved event not found in run result"
    evt = moved_events[0]
    if hasattr(evt, "payload"):
        return evt.payload["distance_ft"]
    return evt["payload"]["distance_ft"]


# ---------------------------------------------------------------------------
# RUN-001: No Run feat, speed=30 → 120 ft (×4)
# ---------------------------------------------------------------------------

def test_RUN001_no_feat_speed30_times4():
    """RUN-001: Entity without Run feat, base_speed=30 → distance_ft=120 (×4)."""
    world = _world_with_runner(base_speed=30, feats=[])
    dist = _run_distance(world)
    assert dist == 120, (
        f"RUN-001: Without Run feat, run distance must be base_speed×4=120. Got {dist}"
    )


# ---------------------------------------------------------------------------
# RUN-002: Run feat, speed=30 → 150 ft (×5)
# ---------------------------------------------------------------------------

def test_RUN002_run_feat_speed30_times5():
    """RUN-002: Entity with Run feat, base_speed=30 → distance_ft=150 (×5)."""
    world = _world_with_runner(base_speed=30, feats=["run"])
    dist = _run_distance(world)
    assert dist == 150, (
        f"RUN-002: With Run feat, run distance must be base_speed×5=150. Got {dist}"
    )


# ---------------------------------------------------------------------------
# RUN-003: No Run feat, speed=20 → 80 ft
# ---------------------------------------------------------------------------

def test_RUN003_no_feat_speed20_times4():
    """RUN-003: Entity without Run feat, base_speed=20 → distance_ft=80."""
    world = _world_with_runner(base_speed=20, feats=[])
    dist = _run_distance(world)
    assert dist == 80, (
        f"RUN-003: Without Run feat, speed=20 → 80 ft (×4). Got {dist}"
    )


# ---------------------------------------------------------------------------
# RUN-004: Run feat, speed=20 → 100 ft
# ---------------------------------------------------------------------------

def test_RUN004_run_feat_speed20_times5():
    """RUN-004: Entity with Run feat, base_speed=20 → distance_ft=100."""
    world = _world_with_runner(base_speed=20, feats=["run"])
    dist = _run_distance(world)
    assert dist == 100, (
        f"RUN-004: With Run feat, speed=20 → 100 ft (×5). Got {dist}"
    )


# ---------------------------------------------------------------------------
# RUN-005: Regression — fatigued entity cannot run
# ---------------------------------------------------------------------------

def test_RUN005_fatigued_blocks_run():
    """RUN-005: Regression — fatigued entity cannot run (existing guard unchanged)."""
    world = _world_with_runner(
        base_speed=30,
        feats=["run"],  # Run feat present but fatigued blocks regardless
    )
    # EF.FATIGUED is a direct entity field (bool), not a conditions dict entry
    from aidm.schemas.entity_fields import EF as _EF
    world.entities["hero"][_EF.FATIGUED] = True
    intent = RunIntent(actor_id="hero")
    turn_ctx = _make_turn_ctx("hero")
    result = execute_turn(
        world_state=world,
        turn_ctx=turn_ctx,
        doctrine=None,
        combat_intent=intent,
        rng=_make_rng(),
        next_event_id=1,
        timestamp=1.0,
    )
    # Should produce action_denied or no entity_moved event
    moved_events = [
        e for e in result.events
        if (hasattr(e, "event_type") and e.event_type == "entity_moved")
        or (isinstance(e, dict) and e.get("event_type") == "entity_moved")
    ]
    assert len(moved_events) == 0, (
        f"RUN-005: Fatigued entity must not run. Got entity_moved events: {moved_events}"
    )


# ---------------------------------------------------------------------------
# RUN-006: Coverage map updated
# ---------------------------------------------------------------------------

def test_RUN006_coverage_map_updated():
    """RUN-006: ENGINE_COVERAGE_MAP.md references WO-ENGINE-RUN-FEAT-SPEED-001."""
    cov_path = os.path.join(os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md")
    with open(cov_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "WO-ENGINE-RUN-FEAT-SPEED-001" in content, (
        "RUN-006: ENGINE_COVERAGE_MAP.md must contain 'WO-ENGINE-RUN-FEAT-SPEED-001'"
    )
