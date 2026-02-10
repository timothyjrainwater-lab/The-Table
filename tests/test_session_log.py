"""Tests for M1 Session Log and Replay Harness.

Tests:
- SessionLog append and serialization
- Intent-result correlation
- Replay verification
- 10× replay verification
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from aidm.core.session_log import (
    SessionLog,
    SessionLogEntry,
    ReplayHarness,
    ReplayVerificationResult,
    verify_result_match,
    create_test_resolver,
)
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.intent_lifecycle import (
    IntentObject,
    IntentStatus,
    ActionType,
)
from aidm.schemas.engine_result import (
    EngineResult,
    EngineResultStatus,
    EngineResultBuilder,
    RollResult,
    StateChange,
)


class TestSessionLogEntry:
    """Tests for SessionLogEntry."""

    def test_create_entry(self):
        """Should create entry with intent and result."""
        intent = IntentObject(
            intent_id="test-intent-001",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="I attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        builder = EngineResultBuilder(intent_id=intent.intent_id)
        result = builder.build(result_id="test-result-001", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        entry = SessionLogEntry(intent=intent, result=result)

        assert entry.intent.intent_id == intent.intent_id
        assert entry.result.intent_id == intent.intent_id

    def test_entry_with_no_result(self):
        """Should allow entry without result (retracted intent)."""
        intent = IntentObject(
            intent_id="test-intent-002",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.RETRACTED,
            source_text="I attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        entry = SessionLogEntry(intent=intent, result=None)

        assert entry.intent is not None
        assert entry.result is None

    def test_entry_serialization(self):
        """Entry should serialize correctly."""
        intent = IntentObject(
            intent_id="test-intent-003",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="I attack the goblin",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
        )

        builder = EngineResultBuilder(intent_id=intent.intent_id)
        builder.set_narration_token("attack_hit")
        result = builder.build(result_id="test-result-003", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        entry = SessionLogEntry(intent=intent, result=result)
        data = entry.to_dict()

        assert "intent" in data
        assert "result" in data
        assert data["intent"]["actor_id"] == "fighter_1"
        assert data["result"]["narration_token"] == "attack_hit"

    def test_entry_roundtrip(self):
        """Entry should survive JSON roundtrip."""
        intent = IntentObject(
            intent_id="test-intent-004",
            actor_id="wizard_1",
            action_type=ActionType.CAST_SPELL,
            status=IntentStatus.PENDING,
            source_text="I cast fireball",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        builder = EngineResultBuilder(intent_id=intent.intent_id)
        result = builder.build(result_id="test-result-004", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        entry = SessionLogEntry(intent=intent, result=result)

        json_str = json.dumps(entry.to_dict())
        restored = SessionLogEntry.from_dict(json.loads(json_str))

        assert restored.intent.actor_id == "wizard_1"
        assert restored.result.intent_id == intent.intent_id


class TestSessionLog:
    """Tests for SessionLog."""

    def test_create_empty_log(self):
        """Should create empty session log."""
        log = SessionLog()

        assert len(log) == 0
        assert log.master_seed == 0

    def test_append_entry(self):
        """Should append entries to log."""
        log = SessionLog(master_seed=12345)

        intent = IntentObject(
            intent_id="test-intent-005",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        builder = EngineResultBuilder(intent_id=intent.intent_id)
        result = builder.build(result_id="test-result-005", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        log.append(intent, result)

        assert len(log) == 1
        assert log.entries[0].intent.actor_id == "fighter_1"

    def test_get_by_intent_id(self):
        """Should find entry by intent ID."""
        log = SessionLog()

        intent1 = IntentObject(
            intent_id="intent_aaa",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        intent2 = IntentObject(
            intent_id="intent_bbb",
            actor_id="wizard_1",
            action_type=ActionType.CAST_SPELL,
            status=IntentStatus.PENDING,
            source_text="cast",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        log.append(intent1, EngineResultBuilder(intent_id="intent_aaa").build(result_id="test-result-006a", resolved_at=datetime(2025, 1, 1, 12, 0, 0)))
        log.append(intent2, EngineResultBuilder(intent_id="intent_bbb").build(result_id="test-result-006b", resolved_at=datetime(2025, 1, 1, 12, 0, 0)))

        found = log.get_by_intent_id("intent_bbb")
        assert found is not None
        assert found.intent.actor_id == "wizard_1"

        not_found = log.get_by_intent_id("intent_zzz")
        assert not_found is None

    def test_jsonl_serialization(self):
        """Session log should serialize to JSONL."""
        log = SessionLog(master_seed=42, initial_state_hash="abc123")

        intent = IntentObject(
            intent_id="test-intent-007",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        log.append(intent, EngineResultBuilder(intent_id=intent.intent_id).build(result_id="test-result-007", resolved_at=datetime(2025, 1, 1, 12, 0, 0)))

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = Path(f.name)

        try:
            log.to_jsonl(path)

            # Read and verify
            with open(path, "r") as f:
                lines = f.readlines()

            assert len(lines) == 2  # Metadata + 1 entry

            # First line is metadata
            metadata = json.loads(lines[0])
            assert metadata["master_seed"] == 42
            assert metadata["initial_state_hash"] == "abc123"

        finally:
            path.unlink()

    def test_jsonl_roundtrip(self):
        """Session log should survive JSONL roundtrip."""
        log = SessionLog(master_seed=99, initial_state_hash="xyz789")

        for i in range(3):
            intent = IntentObject(
                intent_id=f"intent_{i}",
                actor_id=f"actor_{i}",
                action_type=ActionType.END_TURN,
                status=IntentStatus.PENDING,
                source_text=f"action {i}",
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                updated_at=datetime(2025, 1, 1, 12, 0, 0),
            )
            log.append(intent, EngineResultBuilder(intent_id=f"intent_{i}").build(result_id=f"test-result-008-{i}", resolved_at=datetime(2025, 1, 1, 12, 0, 0)))

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = Path(f.name)

        try:
            log.to_jsonl(path)
            restored = SessionLog.from_jsonl(path)

            assert restored.master_seed == 99
            assert restored.initial_state_hash == "xyz789"
            assert len(restored) == 3
            assert restored.entries[1].intent.actor_id == "actor_1"

        finally:
            path.unlink()


class TestVerifyResultMatch:
    """Tests for verify_result_match function."""

    def test_identical_results_match(self):
        """Identical results should match."""
        builder1 = EngineResultBuilder(intent_id="test", rng_offset=0)
        builder1.add_roll("attack", "1d20", 15, 5, 20)
        builder1.add_state_change("goblin", "hp", 10, 5)
        result1 = builder1.build(result_id="test-result-009a", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        builder2 = EngineResultBuilder(intent_id="test", rng_offset=0)
        builder2.add_roll("attack", "1d20", 15, 5, 20)
        builder2.add_state_change("goblin", "hp", 10, 5)
        result2 = builder2.build(result_id="test-result-009b", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        matches, details = verify_result_match(result1, result2)
        assert matches is True
        assert details == ""

    def test_status_mismatch(self):
        """Different status should not match."""
        result1 = EngineResultBuilder(intent_id="test").build(result_id="test-result-010a", resolved_at=datetime(2025, 1, 1, 12, 0, 0))
        result2 = EngineResultBuilder(intent_id="test").build_failure("reason", result_id="test-result-010b", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        matches, details = verify_result_match(result1, result2)
        assert matches is False
        assert "Status mismatch" in details

    def test_rng_offset_mismatch(self):
        """Different RNG offsets should not match."""
        builder1 = EngineResultBuilder(intent_id="test", rng_offset=0)
        builder1.add_roll("attack", "1d20", 15, 5, 20)
        result1 = builder1.build(result_id="test-result-011a", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        builder2 = EngineResultBuilder(intent_id="test", rng_offset=0)
        builder2.add_roll("attack", "1d20", 15, 5, 20)
        builder2.add_roll("damage", "1d8", 5, 2, 7)  # Extra roll
        result2 = builder2.build(result_id="test-result-011b", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        matches, details = verify_result_match(result1, result2)
        assert matches is False
        # Will fail on roll count or RNG offset

    def test_roll_value_mismatch(self):
        """Different roll values should not match."""
        builder1 = EngineResultBuilder(intent_id="test", rng_offset=0)
        builder1.add_roll("attack", "1d20", 15, 5, 20)
        result1 = builder1.build(result_id="test-result-012a", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        builder2 = EngineResultBuilder(intent_id="test", rng_offset=0)
        builder2.add_roll("attack", "1d20", 12, 5, 17)  # Different natural
        result2 = builder2.build(result_id="test-result-012b", resolved_at=datetime(2025, 1, 1, 12, 0, 0))

        matches, details = verify_result_match(result1, result2)
        assert matches is False
        assert "natural mismatch" in details


class TestReplayHarness:
    """Tests for ReplayHarness."""

    def create_test_world(self) -> WorldState:
        """Create a simple test world state."""
        return WorldState(
            ruleset_version="3.5e",
            entities={
                "fighter_1": {"hp": 30, "team": "party"},
                "goblin_1": {"hp": 10, "team": "monsters"},
            },
        )

    def test_replay_empty_session(self):
        """Should verify empty session."""
        resolver = create_test_resolver()
        world = self.create_test_world()
        harness = ReplayHarness(resolver, world, master_seed=12345)

        log = SessionLog(master_seed=12345)

        result = harness.replay_session(log)

        assert result.verified is True
        assert result.entries_checked == 0

    def test_replay_single_entry(self):
        """Should replay single entry."""
        resolver = create_test_resolver()
        world = self.create_test_world()
        rng = RNGManager(12345)

        # Create an intent
        intent = IntentObject(
            intent_id="test-intent-013",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="I attack the goblin",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
            method="longsword",
        )
        intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 12, 0, 1))

        # Resolve it
        original_result = resolver(intent, world, rng)

        # Log it
        log = SessionLog(master_seed=12345)
        log.append(intent, original_result)

        # Replay
        harness = ReplayHarness(resolver, world, master_seed=12345)
        verification = harness.replay_session(log)

        assert verification.verified is True
        assert verification.entries_checked == 1

    def test_10x_verification_passes(self):
        """10× verification should pass for deterministic resolver."""
        resolver = create_test_resolver()
        world = self.create_test_world()
        rng = RNGManager(42)

        # Create and resolve multiple intents
        log = SessionLog(master_seed=42)

        for i in range(5):
            intent = IntentObject(
                intent_id=f"test-intent-014-{i}",
                actor_id="fighter_1",
                action_type=ActionType.ATTACK,
                status=IntentStatus.PENDING,
                source_text=f"attack {i}",
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                updated_at=datetime(2025, 1, 1, 12, 0, 0),
                target_id="goblin_1",
            )
            intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 12, 0, 1))
            result = resolver(intent, world, rng)
            log.append(intent, result)

            # NOTE: Replay harness is non-mutating (reducer-only pattern).
            # Do NOT apply state changes here - replay uses the same initial state.

        # Run 10× verification (same initial world state for each replay)
        harness = ReplayHarness(resolver, world, master_seed=42)
        all_passed, results = harness.verify_10x(log)

        assert all_passed is True
        assert len(results) == 10
        for r in results:
            assert r.verified is True

    def test_retracted_intents_skipped(self):
        """Retracted intents should be skipped in replay."""
        resolver = create_test_resolver()
        world = self.create_test_world()

        log = SessionLog()

        # Add a retracted intent (no result)
        retracted = IntentObject(
            intent_id="test-intent-015",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.RETRACTED,
            source_text="I attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        log.append(retracted, None)

        harness = ReplayHarness(resolver, world, master_seed=0)
        result = harness.replay_session(log)

        # Should pass (retracted entry skipped)
        assert result.verified is True
        assert result.entries_checked == 1


class TestCreateTestResolver:
    """Tests for the test resolver factory."""

    def test_resolver_produces_result(self):
        """Test resolver should produce valid EngineResult."""
        resolver = create_test_resolver()
        world = WorldState(
            ruleset_version="3.5e",
            entities={"goblin_1": {"hp": 10}},
        )
        rng = RNGManager(12345)

        intent = IntentObject(
            intent_id="test-intent-016",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
        )

        result = resolver(intent, world, rng)

        assert result is not None
        assert result.status == EngineResultStatus.SUCCESS
        assert len(result.rolls) >= 1  # At least attack roll

    def test_resolver_is_deterministic(self):
        """Test resolver should be deterministic."""
        resolver = create_test_resolver()
        world = WorldState(
            ruleset_version="3.5e",
            entities={"goblin_1": {"hp": 10}},
        )

        intent = IntentObject(
            intent_id="test-intent-017",
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="attack",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            target_id="goblin_1",
        )

        # Run twice with same seed
        rng1 = RNGManager(99999)
        result1 = resolver(intent, world, rng1)

        rng2 = RNGManager(99999)
        result2 = resolver(intent, world, rng2)

        # Should match
        matches, _ = verify_result_match(result1, result2)
        assert matches is True
