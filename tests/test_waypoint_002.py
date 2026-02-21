"""WO-WAYPOINT-002: Condition Action Denial — Gate Tests.

Proves that execute_turn() rejects action intents when the actor has
a condition with actions_prohibited=True. The engine says no.

GATE TESTS:
  WP2-0: Paralyzed entity cannot attack
  WP2-1: Paralyzed entity cannot cast spells
  WP2-2: Entity without actions_prohibited can act normally
  WP2-3: Denial event survives replay round-trip
  WP2-4: Waypoint scenario regression — Branch A now active
"""

import json
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aidm.core.event_log import Event, EventLog
from aidm.core.play_loop import execute_turn, TurnContext, TurnResult
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.core import replay_runner
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.spell_resolver import SpellCastIntent
from aidm.schemas.conditions import (
    create_paralyzed_condition, create_prone_condition,
)
from aidm.schemas.entity_fields import EF

# ---------------------------------------------------------------------------
# Re-use Waypoint 001 fixtures and scenario
# ---------------------------------------------------------------------------
from tests.test_waypoint_001 import (
    build_initial_state,
    run_scenario,
    normalize_events,
    WAYPOINT_SEED,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_paralyzed_entity(entity_id: str = "test_fighter") -> Dict[str, Any]:
    """Create a minimal entity dict with the paralyzed condition applied."""
    paralyzed = create_paralyzed_condition(source="test", applied_at_event_id=0)
    return {
        "entity_id": entity_id,
        "name": "Test Fighter",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        "ac": 15,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: "party",
        EF.POSITION: {"x": 0, "y": 0},
        EF.DEFEATED: False,
        EF.CONDITIONS: {
            "paralyzed": paralyzed.to_dict(),
        },
    }


def make_healthy_entity(entity_id: str = "test_fighter") -> Dict[str, Any]:
    """Create a minimal entity dict with no conditions."""
    return {
        "entity_id": entity_id,
        "name": "Test Fighter",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        "ac": 15,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: "party",
        EF.POSITION: {"x": 0, "y": 0},
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
    }


def make_target_entity(entity_id: str = "target_dummy") -> Dict[str, Any]:
    """Create a minimal target entity."""
    return {
        "entity_id": entity_id,
        "name": "Target Dummy",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        "ac": 10,
        EF.ATTACK_BONUS: 0,
        EF.TEAM: "monsters",
        EF.POSITION: {"x": 5, "y": 0},
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
    }


def make_attack_intent(attacker_id: str, target_id: str) -> AttackIntent:
    """Create a basic AttackIntent."""
    return AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        attack_bonus=5,
        weapon=Weapon(
            damage_dice="1d8",
            damage_bonus=0,
            damage_type="slashing",
        ),
    )


def make_spell_intent(caster_id: str, target_id: str) -> SpellCastIntent:
    """Create a basic SpellCastIntent."""
    return SpellCastIntent(
        caster_id=caster_id,
        spell_id="hold_person",
        target_entity_id=target_id,
    )


def build_two_entity_state(
    actor: Dict[str, Any],
    target: Dict[str, Any],
) -> WorldState:
    """Build a WorldState with two entities."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            actor["entity_id"]: actor,
            target["entity_id"]: target,
        },
        active_combat={
            "round_index": 1,
            "turn_counter": 0,
            "aoo_used_this_round": [],
            "duration_tracker": {"effects": []},
        },
    )


# ===========================================================================
# WP2-0: Paralyzed Entity Cannot Attack
# ===========================================================================


class TestWP2_0_ParalyzedCannotAttack:
    """Paralyzed entity submits AttackIntent — engine must block."""

    def test_returns_action_denied(self):
        """Return result indicates action denied (not a normal attack resolution)."""
        actor = make_paralyzed_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        assert result.status == "action_denied", (
            f"Expected status='action_denied', got '{result.status}'"
        )

    def test_no_attack_roll_emitted(self):
        """No attack_roll event emitted — resolver was never called."""
        actor = make_paralyzed_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        attack_rolls = [e for e in result.events if e.event_type == "attack_roll"]
        assert len(attack_rolls) == 0, (
            f"Expected no attack_roll events, found {len(attack_rolls)}"
        )

    def test_action_denied_event_emitted(self):
        """An action_denied event is emitted with the entity_id."""
        actor = make_paralyzed_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        denied = [e for e in result.events if e.event_type == "action_denied"]
        assert len(denied) == 1, f"Expected 1 action_denied event, found {len(denied)}"

        payload = denied[0].payload
        assert payload["entity_id"] == "fighter"
        assert payload["reason"] == "actions_prohibited"
        assert payload["denied_intent_type"] == "AttackIntent"
        assert "paralyzed" in payload["conditions"]


# ===========================================================================
# WP2-1: Paralyzed Entity Cannot Cast Spells
# ===========================================================================


class TestWP2_1_ParalyzedCannotCast:
    """Paralyzed entity submits SpellCastIntent — engine must block."""

    def test_returns_action_denied(self):
        """Return result indicates action denied for spell cast."""
        actor = make_paralyzed_entity("caster")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_spell_intent("caster", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="caster", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        assert result.status == "action_denied"

    def test_no_spell_cast_emitted(self):
        """No spell_cast event emitted — spell resolver was never called."""
        actor = make_paralyzed_entity("caster")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_spell_intent("caster", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="caster", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        spell_casts = [e for e in result.events if e.event_type == "spell_cast"]
        assert len(spell_casts) == 0

    def test_action_denied_event_emitted(self):
        """An action_denied event is emitted for the spell attempt."""
        actor = make_paralyzed_entity("caster")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_spell_intent("caster", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="caster", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        denied = [e for e in result.events if e.event_type == "action_denied"]
        assert len(denied) == 1
        assert denied[0].payload["denied_intent_type"] == "SpellCastIntent"


# ===========================================================================
# WP2-2: Entity Without actions_prohibited Can Act Normally
# ===========================================================================


class TestWP2_2_HealthyEntityCanAct:
    """Entity with no conditions can act normally — gate check must not block."""

    def test_returns_ok(self):
        """Return result is a normal attack resolution (hit or miss)."""
        actor = make_healthy_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        assert result.status == "ok", f"Expected status='ok', got '{result.status}'"

    def test_attack_roll_emitted(self):
        """attack_roll event is emitted — resolver was called."""
        actor = make_healthy_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        attack_rolls = [e for e in result.events if e.event_type == "attack_roll"]
        assert len(attack_rolls) >= 1, "No attack_roll event emitted for healthy entity"

    def test_no_action_denied_emitted(self):
        """No action_denied event emitted — no false denial."""
        actor = make_healthy_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        denied = [e for e in result.events if e.event_type == "action_denied"]
        assert len(denied) == 0, f"Unexpected action_denied event for healthy entity"

    def test_prone_does_not_block(self):
        """Prone condition does NOT set actions_prohibited — should not block."""
        actor = make_healthy_entity("fighter")
        prone = create_prone_condition(source="test", applied_at_event_id=0)
        actor[EF.CONDITIONS] = {"prone": prone.to_dict()}

        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        assert result.status == "ok", f"Prone should not block actions, got '{result.status}'"


# ===========================================================================
# WP2-3: Denial Event Survives Replay Round-Trip
# ===========================================================================


class TestWP2_3_DenialEventRoundTrip:
    """action_denied event must survive JSONL serialization round-trip."""

    def test_event_survives_serialization(self):
        """Write EventLog with action_denied to JSONL, read it back, verify."""
        actor = make_paralyzed_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        # Build EventLog from result events
        event_log = EventLog()
        for e in result.events:
            event_log.append(e)

        # Write to JSONL and read back
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            jsonl_path = Path(f.name)

        event_log.to_jsonl(jsonl_path)
        reloaded_log = EventLog.from_jsonl(jsonl_path)

        # Find action_denied in reloaded log
        denied_events = [
            e for e in reloaded_log.events if e.event_type == "action_denied"
        ]
        assert len(denied_events) == 1, (
            f"Expected 1 action_denied event in reloaded log, found {len(denied_events)}"
        )

        # Verify payload fields match original
        original = [e for e in event_log.events if e.event_type == "action_denied"][0]
        reloaded = denied_events[0]

        assert reloaded.payload["entity_id"] == original.payload["entity_id"]
        assert reloaded.payload["reason"] == original.payload["reason"]
        assert reloaded.payload["denied_intent_type"] == original.payload["denied_intent_type"]
        assert reloaded.payload["conditions"] == original.payload["conditions"]

    def test_replay_runner_handles_action_denied(self):
        """replay_runner.reduce_event does not crash on action_denied events."""
        actor = make_paralyzed_entity("fighter")
        target = make_target_entity("goblin")
        ws = build_two_entity_state(actor, target)
        rng = RNGManager(master_seed=42)

        intent = make_attack_intent("fighter", "goblin")
        ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        result = execute_turn(
            world_state=ws,
            turn_ctx=ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        # Build EventLog
        event_log = EventLog()
        for e in result.events:
            event_log.append(e)

        # Write and reload
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            jsonl_path = Path(f.name)
        event_log.to_jsonl(jsonl_path)
        reloaded_log = EventLog.from_jsonl(jsonl_path)

        # Replay — should not crash
        report = replay_runner.run(
            initial_state=deepcopy(ws),
            master_seed=42,
            event_log=reloaded_log,
        )

        assert report.events_processed == len(event_log)


# ===========================================================================
# WP2-4: Waypoint Scenario Regression — Branch A Now Active
# ===========================================================================


class TestWP2_4_WaypointRegression:
    """Re-run the WO-WAYPOINT-001 scenario. Turn 2 must now be blocked."""

    def test_turn2_action_denied(self):
        """Turn 2 (Bandit Captain paralyzed) returns action denied."""
        _ws, event_log, _briefs = run_scenario()

        denied_events = [
            e for e in event_log.events
            if e.event_type == "action_denied"
            and e.payload.get("entity_id") == "bandit_captain"
        ]
        assert len(denied_events) >= 1, (
            "FINDING-WAYPOINT-01 NOT resolved: no action_denied for bandit_captain in Turn 2"
        )

    def test_no_bandit_attack_roll(self):
        """No attack_roll event from Bandit Captain in Turn 2."""
        _ws, event_log, _briefs = run_scenario()

        bandit_attacks = [
            e for e in event_log.events
            if e.event_type == "attack_roll"
            and e.payload.get("attacker_id") == "bandit_captain"
        ]
        assert len(bandit_attacks) == 0, (
            f"Expected 0 attack_roll from bandit_captain, found {len(bandit_attacks)}"
        )

    def test_w0_canary_still_passes(self):
        """W-0 canary: all required event types present (including action_denied)."""
        _ws, event_log, _briefs = run_scenario()
        event_types = {e.event_type for e in event_log.events}

        assert "spell_cast" in event_types
        assert "condition_applied" in event_types
        assert "attack_roll" in event_types  # Kael's attack in Turn 1
        assert "skill_check" in event_types
        assert "action_denied" in event_types  # New: bandit_captain denial

    def test_w1_replay_determinism(self):
        """W-1: Live → JSONL → Replay normalized comparison still passes."""
        _ws, event_log, _briefs = run_scenario()

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            jsonl_path = Path(f.name)

        event_log.to_jsonl(jsonl_path)
        reloaded_log = EventLog.from_jsonl(jsonl_path)

        live_norm = normalize_events(event_log.events)
        replay_norm = normalize_events(reloaded_log.events)

        assert live_norm == replay_norm, (
            f"Normalized rule outcomes differ between live and replay.\n"
            f"Live:   {live_norm}\n"
            f"Replay: {replay_norm}"
        )

    def test_w3_transcript_determinism(self):
        """W-3: Same seed → same NarrativeBriefs."""
        _ws1, _log1, briefs1 = run_scenario(seed=WAYPOINT_SEED, timestamp=1.0)
        _ws2, _log2, briefs2 = run_scenario(seed=WAYPOINT_SEED, timestamp=1.0)

        assert len(briefs1) == len(briefs2)
        for i, (b1, b2) in enumerate(zip(briefs1, briefs2)):
            assert b1 == b2, f"Brief for turn {i} differs between runs"

    def test_w4_time_isolation(self):
        """W-4: Timestamps must not affect rule outcomes."""
        _ws1, log1, _b1 = run_scenario(seed=WAYPOINT_SEED, timestamp=1000.0)
        _ws2, log2, _b2 = run_scenario(seed=WAYPOINT_SEED, timestamp=9999.0)

        norm1 = normalize_events(log1.events)
        norm2 = normalize_events(log2.events)

        assert norm1 == norm2
