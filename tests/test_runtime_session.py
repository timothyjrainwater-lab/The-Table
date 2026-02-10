"""Tests for M1 Runtime Session and Replay.

Tests the IPC_CONTRACT.md execution model:
- Intent lifecycle through RuntimeSession
- Session logging with JSONL persistence
- Replay verification (determinism)
- 10× replay verification
"""

import pytest
import json
import uuid
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

from aidm.runtime.session import (
    RuntimeSession,
    SessionLog,
    IntentEntry,
    ReplayResult,
    replay_session,
    verify_10x_replay,
)
from aidm.schemas.intent_lifecycle import (
    IntentObject,
    IntentStatus,
    ActionType,
)
from aidm.schemas.engine_result import (
    EngineResult,
    EngineResultStatus,
    EngineResultBuilder,
)
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager


# =============================================================================
# Test Fixtures
# =============================================================================

def create_test_state() -> WorldState:
    """Create a minimal test world state."""
    return WorldState(
        ruleset_version="test-1.0",
        entities={
            "fighter_1": {"hp": 20, "team": "party"},
            "goblin_1": {"hp": 10, "team": "monsters"},
        },
    )


def mock_engine_resolver(
    intent: IntentObject,
    state: WorldState,
    rng: RNGManager,
) -> Tuple[EngineResult, WorldState]:
    """Mock engine resolver for testing.

    Simulates attack resolution with deterministic RNG.
    """
    combat_rng = rng.stream("combat")

    builder = EngineResultBuilder(
        intent_id=intent.intent_id,
        rng_offset=combat_rng.call_count,
    )

    if intent.action_type == ActionType.ATTACK:
        # Simulate attack roll
        attack_roll = combat_rng.randint(1, 20)
        builder.add_roll(
            roll_type="attack",
            dice="1d20",
            natural_roll=attack_roll,
            modifiers=5,
            total=attack_roll + 5,
        )

        # Determine hit (target AC 15)
        hit = (attack_roll + 5) >= 15

        builder.add_event({
            "type": "attack_roll",
            "attacker": intent.actor_id,
            "target": intent.target_id,
            "natural": attack_roll,
            "total": attack_roll + 5,
            "hit": hit,
        })

        if hit:
            # Simulate damage roll
            damage_roll = combat_rng.randint(1, 8)
            builder.add_roll(
                roll_type="damage",
                dice="1d8",
                natural_roll=damage_roll,
                modifiers=2,
                total=damage_roll + 2,
            )

            total_damage = damage_roll + 2
            target = state.entities.get(intent.target_id, {})
            old_hp = target.get("hp", 0)
            new_hp = max(0, old_hp - total_damage)

            builder.add_state_change(
                entity_id=intent.target_id,
                field="hp",
                old_value=old_hp,
                new_value=new_hp,
            )

            builder.add_event({
                "type": "damage_dealt",
                "target": intent.target_id,
                "damage": total_damage,
                "old_hp": old_hp,
                "new_hp": new_hp,
            })

            builder.set_narration_token("attack_hit")

            # Update state
            entities = state.entities.copy()
            entities[intent.target_id] = {**target, "hp": new_hp}
            state = WorldState(
                ruleset_version=state.ruleset_version,
                entities=entities,
            )
        else:
            builder.set_narration_token("attack_miss")

        return builder.build(result_id=str(uuid.uuid4()), resolved_at=datetime(2025, 1, 1, 12, 0, 0)), state

    elif intent.action_type == ActionType.END_TURN:
        builder.add_event({"type": "turn_ended", "actor": intent.actor_id})
        builder.set_narration_token("turn_ended")
        return builder.build(result_id=str(uuid.uuid4()), resolved_at=datetime(2025, 1, 1, 12, 0, 0)), state

    else:
        return builder.build_failure(f"Unsupported action: {intent.action_type}", result_id=str(uuid.uuid4()), resolved_at=datetime(2025, 1, 1, 12, 0, 0)), state


# =============================================================================
# IntentEntry Tests
# =============================================================================

class TestIntentEntry:
    """Tests for IntentEntry dataclass."""

    def test_create_entry(self):
        """Should create entry with intent and result."""
        intent = IntentObject(
            intent_id="test-intent-001",
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )
        intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        builder = EngineResultBuilder(intent_id=intent.intent_id)
        result = builder.build(result_id="test-result-001", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        entry = IntentEntry(intent=intent, result=result, logged_at=datetime(2025, 1, 1, 12, 0, 0))

        assert entry.intent.actor_id == "fighter_1"
        assert entry.result is not None
        assert isinstance(entry.logged_at, datetime)

    def test_entry_serialization_roundtrip(self):
        """IntentEntry should survive JSON roundtrip."""
        intent = IntentObject(
            intent_id="test-intent-002",
            actor_id="fighter_1",
            source_text="attack goblin",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="sword",
        )
        intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        builder = EngineResultBuilder(intent_id=intent.intent_id)
        builder.add_event({"type": "test"})
        result = builder.build(result_id="test-result-002", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        entry = IntentEntry(intent=intent, result=result, logged_at=datetime(2025, 1, 1, 12, 0, 0))

        json_str = json.dumps(entry.to_dict())
        restored = IntentEntry.from_dict(json.loads(json_str))

        assert restored.intent.actor_id == "fighter_1"
        assert restored.result is not None
        assert len(restored.result.events) == 1


# =============================================================================
# SessionLog Tests
# =============================================================================

class TestSessionLog:
    """Tests for SessionLog."""

    def test_append_confirmed_intent(self):
        """Should append confirmed intent."""
        log = SessionLog()

        intent = IntentObject(
            intent_id="test-intent-003",
            actor_id="fighter_1",
            source_text="attack",
            action_type=ActionType.END_TURN,
            status=IntentStatus.PENDING,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        entry = IntentEntry(intent=intent, result=None, logged_at=datetime(2025, 1, 1, 12, 0, 0))
        log.append(entry)

        assert len(log) == 1

    def test_reject_pending_intent(self):
        """Should reject pending intent."""
        log = SessionLog()

        intent = IntentObject(
            intent_id="test-intent-004",
            actor_id="fighter_1",
            source_text="attack",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        # Still PENDING

        entry = IntentEntry(intent=intent, result=None, logged_at=datetime(2025, 1, 1, 12, 0, 0))

        with pytest.raises(ValueError, match="CONFIRMED, RESOLVED, or RETRACTED"):
            log.append(entry)

    def test_jsonl_roundtrip(self):
        """SessionLog should survive JSONL roundtrip."""
        log = SessionLog(session_id="test-session", master_seed=12345, started_at=datetime(2025, 1, 1, 12, 0, 0))

        intent = IntentObject(
            intent_id="test-intent-005",
            actor_id="fighter_1",
            source_text="end turn",
            action_type=ActionType.END_TURN,
            status=IntentStatus.PENDING,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        entry = IntentEntry(intent=intent, result=None, logged_at=datetime(2025, 1, 1, 12, 0, 0))
        log.append(entry)

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = Path(f.name)

        try:
            log.to_jsonl(path)
            restored = SessionLog.from_jsonl(path)

            assert restored.session_id == "test-session"
            assert restored.master_seed == 12345
            assert len(restored) == 1
            assert restored.entries[0].intent.actor_id == "fighter_1"
        finally:
            path.unlink()


# =============================================================================
# RuntimeSession Tests
# =============================================================================

class TestRuntimeSession:
    """Tests for RuntimeSession."""

    def test_create_session(self):
        """Should create session with initial state."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            session_id="test",
        )

        assert session.world_state == state
        assert session.log.master_seed == 42

    def test_create_intent(self):
        """Should create intent in PENDING status."""
        state = create_test_state()
        session = RuntimeSession.create(state, master_seed=42)

        intent = session.create_intent(
            actor_id="fighter_1",
            source_text="I attack the goblin",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-006",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        assert intent.actor_id == "fighter_1"
        assert intent.status == IntentStatus.PENDING

    def test_needs_clarification(self):
        """Should detect missing required fields."""
        state = create_test_state()
        session = RuntimeSession.create(state, master_seed=42)

        intent = session.create_intent(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-007",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        assert session.needs_clarification(intent) is True

        intent.target_id = "goblin_1"
        intent.method = "longsword"

        assert session.needs_clarification(intent) is False

    def test_update_intent(self):
        """Should update intent with clarification."""
        state = create_test_state()
        session = RuntimeSession.create(state, master_seed=42)

        intent = session.create_intent(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-008",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        session.update_intent(intent, {
            "target_id": "goblin_1",
            "method": "longsword",
        }, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        assert intent.target_id == "goblin_1"
        assert intent.method == "longsword"

    def test_confirm_intent(self):
        """Should confirm and freeze intent."""
        state = create_test_state()
        session = RuntimeSession.create(state, master_seed=42)

        intent = session.create_intent(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-009",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )

        session.confirm_intent(intent, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        assert intent.status == IntentStatus.CONFIRMED
        assert intent.is_frozen is True

    def test_confirm_incomplete_intent_fails(self):
        """Should reject confirmation of incomplete intent."""
        state = create_test_state()
        session = RuntimeSession.create(state, master_seed=42)

        intent = session.create_intent(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-010",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        with pytest.raises(Exception, match="missing fields"):
            session.confirm_intent(intent, timestamp=datetime(2025, 1, 1, 12, 0, 0))

    def test_retract_intent(self):
        """Should retract and log intent."""
        state = create_test_state()
        session = RuntimeSession.create(state, master_seed=42)

        intent = session.create_intent(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-011",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        session.retract_intent(intent, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        assert intent.status == IntentStatus.RETRACTED
        assert len(session.log) == 1

    def test_full_resolve_flow(self):
        """Should resolve intent and log result."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        intent = session.create_intent(
            actor_id="fighter_1",
            source_text="I attack the goblin",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-012",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )

        session.confirm_intent(intent, timestamp=datetime(2025, 1, 1, 12, 0, 0))
        result, narration = session.resolve(intent, timestamp=datetime(2025, 1, 1, 12, 0, 0))

        assert result.status == EngineResultStatus.SUCCESS
        assert intent.status == IntentStatus.RESOLVED
        assert len(session.log) == 1
        assert narration in ("attack_hit", "attack_miss")


class TestProcessInput:
    """Tests for the full process_input pipeline."""

    def test_process_complete_input(self):
        """Should process input through full pipeline."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        result, narration = session.process_input(
            actor_id="fighter_1",
            source_text="I attack the goblin",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-013",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )

        assert result.status == EngineResultStatus.SUCCESS
        assert len(session.log) == 1

    def test_process_with_clarification(self):
        """Should request clarification for incomplete input."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        clarification_calls = []

        def get_clarification(missing: List[str]) -> Dict[str, Any]:
            clarification_calls.append(missing)
            return {
                "target_id": "goblin_1",
                "method": "longsword",
            }

        result, narration = session.process_input(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-014",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            get_clarification=get_clarification,
        )

        assert len(clarification_calls) == 1
        assert "target_id" in clarification_calls[0]
        assert result.status == EngineResultStatus.SUCCESS

    def test_process_retraction_returns_engine_result(self):
        """Retraction during clarification should return (EngineResult, str)."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        def retract_clarification(missing: List[str]) -> None:
            return None  # Player retracts

        result, narration = session.process_input(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-015",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            get_clarification=retract_clarification,
        )

        assert isinstance(result, EngineResult)
        assert result.status == EngineResultStatus.FAILURE
        assert result.failure_reason == "action_retracted"
        assert narration == "action_retracted"


# =============================================================================
# Replay Tests
# =============================================================================

class TestReplaySession:
    """Tests for replay_session function."""

    def test_replay_matches_original(self):
        """Replay should produce identical results."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        # Run original session
        session.process_input(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-016",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )

        # Replay
        result = replay_session(
            session_log=session.log,
            initial_state=state,
            engine_resolver=mock_engine_resolver,
        )

        assert result.success is True
        assert result.replays_run == 1
        assert len(result.divergences) == 0

    def test_replay_multiple_actions(self):
        """Replay should handle multiple actions."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        # Multiple actions
        session.process_input(
            actor_id="fighter_1",
            source_text="attack 1",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-017",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="sword",
        )
        session.process_input(
            actor_id="fighter_1",
            source_text="attack 2",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-018",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="sword",
        )

        result = replay_session(
            session_log=session.log,
            initial_state=state,
            engine_resolver=mock_engine_resolver,
        )

        assert result.success is True
        assert result.replays_run == 2


class TestVerify10xReplay:
    """Tests for 10× replay verification."""

    def test_10x_replay_success(self):
        """10x replay should succeed for deterministic session."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        session.process_input(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-019",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )

        result = verify_10x_replay(
            session_log=session.log,
            initial_state=state,
            engine_resolver=mock_engine_resolver,
        )

        assert result.success is True
        assert result.replays_run == 10
        assert len(result.divergences) == 0

    def test_10x_replay_detects_nondeterminism(self):
        """10x replay should detect non-deterministic behavior."""
        state = create_test_state()
        session = RuntimeSession.create(
            initial_state=state,
            master_seed=42,
            engine_resolver=mock_engine_resolver,
        )

        session.process_input(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            intent_id="test-intent-020",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )

        call_count = [0]

        def nondeterministic_resolver(
            intent: IntentObject,
            state: WorldState,
            rng: RNGManager,
        ) -> Tuple[EngineResult, WorldState]:
            """Resolver that behaves differently on each call."""
            call_count[0] += 1
            combat_rng = rng.stream("combat")
            builder = EngineResultBuilder(
                intent_id=intent.intent_id,
                rng_offset=combat_rng.call_count,
            )
            # Use different RNG calls based on call count
            if call_count[0] % 2 == 0:
                combat_rng.randint(1, 20)  # Extra roll on even calls
            attack = combat_rng.randint(1, 20)
            builder.add_roll("attack", "1d20", attack, 0, attack)
            return builder.build(result_id=str(uuid.uuid4()), resolved_at=datetime(2025, 1, 1, 12, 0, 0)), state

        result = verify_10x_replay(
            session_log=session.log,
            initial_state=state,
            engine_resolver=nondeterministic_resolver,
        )

        # Should detect divergence
        assert result.success is False
        assert len(result.divergences) > 0
