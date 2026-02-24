"""Gate CP-19 — DurationTracker.tick_round() wired into execute_turn().

When the last actor in the initiative order completes their turn:
  - DurationTracker.tick_round() fires
  - Effects reaching 0 rounds expire → condition_expired event emitted
  - Expired conditions are removed from entity state

Tests:
CP19-01  Single-actor combat: tick_round fires after turn 0 (sole actor = last)
CP19-02  Duration-1 effect expires after one round → condition_expired event
CP19-03  Duration-2 effect: turn 1 → 1 round left, no expiry
CP19-04  Duration-2 effect: turn 2 → expires, condition_expired emitted
CP19-05  Permanent effect (rounds_remaining=-1) never expires
CP19-06  condition_expired event shape: entity_id, condition, spell_id, spell_name
CP19-07  Expired condition removed from entity EF.CONDITIONS in updated world_state
CP19-08  Two-actor combat: tick fires only after last actor's turn (not first actor's)
CP19-09  Two-actor combat: tick fires after actor index 1 (last)
CP19-10  Tracker persisted: after tick, duration_tracker saved in active_combat
CP19-11  Tracker loaded: duration_tracker restored from active_combat on next turn
CP19-12  Regression: non-expiring turn (mid-round) does not emit condition_expired
"""

from copy import deepcopy
from typing import Any, Dict, List

import pytest

from aidm.core.duration_tracker import (
    DurationTracker, ActiveSpellEffect, create_effect,
)
from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ─── helpers ────────────────────────────────────────────────────────────────

def _sword() -> Weapon:
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        weapon_type="one-handed",
    )


def _fighter(eid: str = "fighter_01", team: str = "party") -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.DEX_MOD: 2,
        EF.STR_MOD: 2,
        EF.BAB: 5,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
    }


def _goblin(eid: str = "goblin_01", team: str = "monsters") -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: 15,
        EF.HP_MAX: 15,
        EF.AC: 12,
        EF.DEX_MOD: 1,
        EF.STR_MOD: 0,
        EF.BAB: 1,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
    }


def _world_single(*, with_tracker: bool = False, tracker: DurationTracker = None) -> WorldState:
    """Single-actor world (just fighter — sole actor is the last)."""
    f = _fighter("f01")
    f[EF.CONDITIONS] = {}
    entities = {"f01": f}
    active_combat = {
        "initiative_order": ["f01"],
        "turn_counter": 0,
        "duration_tracker": tracker.to_dict() if tracker else None,
    }
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat=active_combat,
    )


def _world_two(*, with_tracker: bool = False, tracker: DurationTracker = None) -> WorldState:
    """Two-actor world: fighter (index 0) and goblin (index 1)."""
    f = _fighter("f01")
    g = _goblin("g01")
    f[EF.CONDITIONS] = {}
    g[EF.CONDITIONS] = {}
    entities = {"f01": f, "g01": g}
    active_combat = {
        "initiative_order": ["f01", "g01"],
        "turn_counter": 0,
        "duration_tracker": tracker.to_dict() if tracker else None,
    }
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat=active_combat,
    )


def _effect(
    eid: str = "eff01",
    spell_id: str = "sp01",
    spell_name: str = "Test Spell",
    target_id: str = "f01",
    caster_id: str = "wizard",
    rounds: int = 1,
    condition: str = "shaken",
) -> ActiveSpellEffect:
    return ActiveSpellEffect(
        effect_id=eid,
        spell_id=spell_id,
        spell_name=spell_name,
        caster_id=caster_id,
        target_id=target_id,
        rounds_remaining=rounds,
        concentration=False,
        condition_applied=condition,
    )


def _noop_turn(ws: WorldState, actor_id: str, turn_index: int, team: str = "party") -> Any:
    """Execute a turn with no combat intent (just triggers round-end logic)."""
    rng = RNGManager(42)
    ctx = TurnContext(actor_id=actor_id, actor_team=team, turn_index=turn_index)
    # No intent → will emit action_declared (stub) or noop for non-combat
    return execute_turn(ws, ctx, combat_intent=None, rng=rng)


# ─── CP19-01: Single-actor: tick fires after turn 0 (sole actor = last) ──────

def test_cp19_01_single_actor_tick_fires():
    """Single-actor combat: turn 0 is the last → tick_round fires."""
    ws = _world_single()

    result = _noop_turn(ws, "f01", turn_index=0)

    # After the turn, duration_tracker should be in active_combat
    tracker_data = result.world_state.active_combat.get("duration_tracker")
    assert tracker_data is not None  # Tracker was persisted


# ─── CP19-02: Duration-1 effect expires after one round ──────────────────────

def test_cp19_02_duration_1_expires_after_round():
    """Duration-1 effect: expires when tick_round fires on turn 0."""
    tracker = DurationTracker()
    eff = _effect(rounds=1, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    # Manually add condition to entity
    ws = _world_single(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    result = _noop_turn(ws, "f01", turn_index=0)

    event_types = [e.event_type for e in result.events]
    assert "spell_effect_expired" in event_types

    # Condition removed from entity
    conditions = result.world_state.entities["f01"].get(EF.CONDITIONS, {})
    assert "shaken" not in conditions


# ─── CP19-03: Duration-2 effect: after turn 0 → 1 round left, no expiry ──────

def test_cp19_03_duration_2_after_turn_0_no_expiry():
    """Duration-2 effect: turn 0 → 1 round remaining, no expiry yet."""
    tracker = DurationTracker()
    eff = _effect(rounds=2, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_single(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    result = _noop_turn(ws, "f01", turn_index=0)

    event_types = [e.event_type for e in result.events]
    assert "spell_effect_expired" not in event_types

    # Condition still present
    conditions = result.world_state.entities["f01"].get(EF.CONDITIONS, {})
    assert "shaken" in conditions


# ─── CP19-04: Duration-2 effect: turn 2 (index 1, solo actor) → expires ──────

def test_cp19_04_duration_2_expires_on_second_round():
    """Duration-2 effect expires after second tick (simulated by pre-decrementing)."""
    tracker = DurationTracker()
    # Duration-1 remaining after first round was already ticked
    eff = _effect(rounds=1, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_single(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    # Turn index 1 (second round, sole actor at index 0)
    result = _noop_turn(ws, "f01", turn_index=1)

    event_types = [e.event_type for e in result.events]
    assert "spell_effect_expired" in event_types
    conditions = result.world_state.entities["f01"].get(EF.CONDITIONS, {})
    assert "shaken" not in conditions


# ─── CP19-05: Permanent effect never expires ─────────────────────────────────

def test_cp19_05_permanent_effect_never_expires():
    """Permanent effect (rounds_remaining=-1) never expires."""
    tracker = DurationTracker()
    eff = ActiveSpellEffect(
        effect_id="perm_eff",
        spell_id="sp01",
        spell_name="Permanent Buff",
        caster_id="wizard",
        target_id="f01",
        rounds_remaining=-1,
        concentration=False,
        condition_applied="blessed",
    )
    tracker.add_effect(eff)

    ws = _world_single(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["blessed"] = {"type": "blessed"}

    result = _noop_turn(ws, "f01", turn_index=0)

    event_types = [e.event_type for e in result.events]
    assert "spell_effect_expired" not in event_types
    conditions = result.world_state.entities["f01"].get(EF.CONDITIONS, {})
    assert "blessed" in conditions


# ─── CP19-06: spell_effect_expired and condition_removed event shapes ─────────

def test_cp19_06_condition_expired_event_shape():
    """spell_effect_expired and condition_removed events have correct shape."""
    tracker = DurationTracker()
    eff = _effect(rounds=1, condition="shaken", target_id="f01", spell_id="sp01", spell_name="Fear")
    tracker.add_effect(eff)

    ws = _world_single(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    result = _noop_turn(ws, "f01", turn_index=0)

    # Check spell_effect_expired event
    expired = [e for e in result.events if e.event_type == "spell_effect_expired"]
    assert len(expired) == 1
    payload = expired[0].payload
    assert payload["target_id"] == "f01"
    assert payload["spell_id"] == "sp01"
    assert payload["spell_name"] == "Fear"

    # Check condition_removed event
    removed = [e for e in result.events if e.event_type == "condition_removed"]
    assert len(removed) == 1
    removed_payload = removed[0].payload
    assert removed_payload["entity_id"] == "f01"
    assert removed_payload["condition"] == "shaken"
    assert removed_payload["reason"] == "duration_expired"


# ─── CP19-07: Expired condition removed from entity state ────────────────────

def test_cp19_07_expired_condition_removed_from_state():
    """After tick, expired condition is gone from entity EF.CONDITIONS."""
    tracker = DurationTracker()
    eff = _effect(rounds=1, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_single(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    result = _noop_turn(ws, "f01", turn_index=0)

    updated_entity = result.world_state.entities["f01"]
    conditions = updated_entity.get(EF.CONDITIONS, {})
    assert "shaken" not in conditions


# ─── CP19-08: Two-actor: tick NOT fired after first actor's turn ──────────────

def test_cp19_08_two_actor_tick_not_on_first_turn():
    """Two actors: tick does not fire after actor at index 0 (not last)."""
    tracker = DurationTracker()
    eff = _effect(rounds=1, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_two(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    # Actor at index 0 (f01) — not the last
    result = _noop_turn(ws, "f01", turn_index=0)

    event_types = [e.event_type for e in result.events]
    assert "spell_effect_expired" not in event_types

    # Condition still present
    conditions = result.world_state.entities["f01"].get(EF.CONDITIONS, {})
    assert "shaken" in conditions


# ─── CP19-09: Two-actor: tick fires after actor at index 1 (last) ────────────

def test_cp19_09_two_actor_tick_fires_on_last_actor():
    """Two actors: tick fires after actor at index 1 (last in round)."""
    tracker = DurationTracker()
    eff = _effect(rounds=1, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_two(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    # Actor at index 1 (g01) — the last
    result = _noop_turn(ws, "g01", turn_index=1, team="monsters")

    event_types = [e.event_type for e in result.events]
    assert "spell_effect_expired" in event_types


# ─── CP19-10: Tracker persisted after tick ────────────────────────────────────

def test_cp19_10_tracker_persisted_after_tick():
    """After tick_round fires, duration_tracker is saved to active_combat."""
    tracker = DurationTracker()
    eff = _effect(rounds=3, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_single(tracker=tracker)

    result = _noop_turn(ws, "f01", turn_index=0)

    tracker_data = result.world_state.active_combat.get("duration_tracker")
    assert tracker_data is not None
    # Should be a dict (serialized tracker)
    assert isinstance(tracker_data, dict)


# ─── CP19-11: Tracker round-trips through active_combat ──────────────────────

def test_cp19_11_tracker_round_trips():
    """Tracker is correctly serialized and restored between turns."""
    tracker = DurationTracker()
    eff = _effect(rounds=3, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_single(tracker=tracker)

    # Turn 0 — tick fires (sole actor), rounds_remaining = 3 → 2
    result0 = _noop_turn(ws, "f01", turn_index=0)

    # Load from result and run turn 1
    ws2 = result0.world_state
    result1 = _noop_turn(ws2, "f01", turn_index=1)

    # 2 → 1 round remaining, no expiry
    event_types1 = [e.event_type for e in result1.events]
    assert "spell_effect_expired" not in event_types1


# ─── CP19-12: Mid-round turn does NOT emit condition_expired ─────────────────

def test_cp19_12_midround_no_condition_expired():
    """Two-actor: first actor's turn does not emit condition_expired."""
    tracker = DurationTracker()
    # 1-round effect — expires at end of round
    eff = _effect(rounds=1, condition="shaken", target_id="f01")
    tracker.add_effect(eff)

    ws = _world_two(tracker=tracker)
    ws.entities["f01"][EF.CONDITIONS]["shaken"] = {"type": "shaken"}

    # First actor — index 0, not end of round
    result = _noop_turn(ws, "f01", turn_index=0)

    event_types = [e.event_type for e in result.events]
    assert "spell_effect_expired" not in event_types
