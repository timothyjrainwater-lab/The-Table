"""Tests for Engine Result schema.

Tests the IPC_CONTRACT.md Section 3.4 Engine output:
- EngineResult immutability
- Serialization/deserialization roundtrip
- RollResult and StateChange tracking
- EngineResultBuilder usage
"""

import pytest
import json
from datetime import datetime

from aidm.schemas.engine_result import (
    EngineResult,
    EngineResultStatus,
    EngineResultFrozenError,
    EngineResultBuilder,
    RollResult,
    StateChange,
)


class TestEngineResultStatus:
    """Tests for EngineResultStatus enum."""

    def test_status_values(self):
        """EngineResultStatus should have correct string values."""
        assert EngineResultStatus.SUCCESS.value == "success"
        assert EngineResultStatus.FAILURE.value == "failure"
        assert EngineResultStatus.ABORTED.value == "aborted"


class TestRollResult:
    """Tests for RollResult dataclass."""

    def test_create_roll_result(self):
        """Should create roll result with all fields."""
        roll = RollResult(
            roll_type="attack",
            dice="1d20",
            natural_roll=15,
            modifiers=5,
            total=20,
            rng_offset=0,
            context={"target_ac": 18},
        )

        assert roll.roll_type == "attack"
        assert roll.dice == "1d20"
        assert roll.natural_roll == 15
        assert roll.modifiers == 5
        assert roll.total == 20
        assert roll.rng_offset == 0
        assert roll.context == {"target_ac": 18}

    def test_roll_result_serialization(self):
        """RollResult should serialize correctly."""
        roll = RollResult(
            roll_type="damage",
            dice="2d6+3",
            natural_roll=8,
            modifiers=3,
            total=11,
            rng_offset=5,
        )

        data = roll.to_dict()
        assert data["roll_type"] == "damage"
        assert data["natural_roll"] == 8
        assert data["total"] == 11
        assert "context" not in data  # Should omit None

    def test_roll_result_roundtrip(self):
        """RollResult should survive JSON roundtrip."""
        roll = RollResult(
            roll_type="attack",
            dice="1d20",
            natural_roll=18,
            modifiers=7,
            total=25,
            rng_offset=3,
            context={"weapon": "longsword"},
        )

        json_str = json.dumps(roll.to_dict())
        restored = RollResult.from_dict(json.loads(json_str))

        assert restored.roll_type == roll.roll_type
        assert restored.natural_roll == roll.natural_roll
        assert restored.total == roll.total
        assert restored.context == roll.context


class TestStateChange:
    """Tests for StateChange dataclass."""

    def test_create_state_change(self):
        """Should create state change record."""
        change = StateChange(
            entity_id="fighter_1",
            field="hp",
            old_value=20,
            new_value=12,
        )

        assert change.entity_id == "fighter_1"
        assert change.field == "hp"
        assert change.old_value == 20
        assert change.new_value == 12

    def test_state_change_roundtrip(self):
        """StateChange should survive JSON roundtrip."""
        change = StateChange(
            entity_id="goblin_1",
            field="defeated",
            old_value=False,
            new_value=True,
        )

        json_str = json.dumps(change.to_dict())
        restored = StateChange.from_dict(json.loads(json_str))

        assert restored.entity_id == change.entity_id
        assert restored.field == change.field
        assert restored.old_value == change.old_value
        assert restored.new_value == change.new_value


class TestEngineResultImmutability:
    """Tests for EngineResult immutability after creation."""

    def test_result_is_frozen_after_creation(self):
        """EngineResult should be frozen immediately after creation."""
        result = EngineResult(
            intent_id="intent_123",
            status=EngineResultStatus.SUCCESS,
        )

        # Attempt to modify should raise
        with pytest.raises(EngineResultFrozenError, match="immutable"):
            result.status = EngineResultStatus.FAILURE

    def test_cannot_modify_any_field(self):
        """No field on EngineResult can be modified."""
        result = EngineResult(
            intent_id="intent_123",
            narration_token="attack_hit",
        )

        with pytest.raises(EngineResultFrozenError):
            result.intent_id = "different"

        with pytest.raises(EngineResultFrozenError):
            result.narration_token = "attack_miss"

        with pytest.raises(EngineResultFrozenError):
            result.events = []


class TestEngineResultBuilder:
    """Tests for EngineResultBuilder."""

    def test_builder_basic_usage(self):
        """Builder should create valid EngineResult."""
        builder = EngineResultBuilder(intent_id="intent_456")

        result = builder.build()

        assert result.intent_id == "intent_456"
        assert result.status == EngineResultStatus.SUCCESS
        assert len(result.events) == 0
        assert len(result.rolls) == 0

    def test_builder_add_events(self):
        """Builder should accumulate events."""
        builder = EngineResultBuilder(intent_id="intent_789")

        builder.add_event({"type": "attack_roll", "hit": True})
        builder.add_event({"type": "damage_dealt", "amount": 8})

        result = builder.build()

        assert len(result.events) == 2
        assert result.events[0]["type"] == "attack_roll"
        assert result.events[1]["amount"] == 8

    def test_builder_add_rolls(self):
        """Builder should accumulate rolls with correct RNG tracking."""
        builder = EngineResultBuilder(intent_id="intent_abc", rng_offset=10)

        builder.add_roll(
            roll_type="attack",
            dice="1d20",
            natural_roll=18,
            modifiers=5,
            total=23,
        )
        builder.add_roll(
            roll_type="damage",
            dice="1d8+2",
            natural_roll=6,
            modifiers=2,
            total=8,
        )

        result = builder.build()

        assert len(result.rolls) == 2
        assert result.rolls[0].rng_offset == 10
        assert result.rolls[1].rng_offset == 11
        assert result.rng_initial_offset == 10
        assert result.rng_final_offset == 12

    def test_builder_add_state_changes(self):
        """Builder should accumulate state changes."""
        builder = EngineResultBuilder(intent_id="intent_def")

        builder.add_state_change(
            entity_id="goblin_1",
            field="hp",
            old_value=10,
            new_value=2,
        )

        result = builder.build()

        assert len(result.state_changes) == 1
        assert result.state_changes[0].entity_id == "goblin_1"
        assert result.state_changes[0].new_value == 2

    def test_builder_set_narration_token(self):
        """Builder should set narration token."""
        builder = EngineResultBuilder(intent_id="intent_ghi")

        builder.set_narration_token("critical_hit")

        result = builder.build()

        assert result.narration_token == "critical_hit"

    def test_builder_add_metadata(self):
        """Builder should accumulate metadata."""
        builder = EngineResultBuilder(intent_id="intent_jkl")

        builder.add_metadata("actor", "fighter_1")
        builder.add_metadata("target", "goblin_1")

        result = builder.build()

        assert result.metadata == {"actor": "fighter_1", "target": "goblin_1"}

    def test_builder_build_failure(self):
        """Builder should create failure result."""
        builder = EngineResultBuilder(intent_id="intent_mno")

        result = builder.build_failure("Target not found")

        assert result.status == EngineResultStatus.FAILURE
        assert result.failure_reason == "Target not found"

    def test_builder_build_aborted(self):
        """Builder should create aborted result."""
        builder = EngineResultBuilder(intent_id="intent_pqr")

        result = builder.build_aborted("Defeated by AoO")

        assert result.status == EngineResultStatus.ABORTED
        assert result.failure_reason == "Defeated by AoO"

    def test_builder_cannot_modify_after_build(self):
        """Builder should reject modifications after build()."""
        builder = EngineResultBuilder(intent_id="intent_stu")

        builder.build()

        with pytest.raises(ValueError, match="Cannot modify"):
            builder.add_event({"type": "late_event"})

        with pytest.raises(ValueError, match="Cannot modify"):
            builder.add_roll("attack", "1d20", 10, 0, 10)

    def test_builder_cannot_build_twice(self):
        """Builder should reject second build() call."""
        builder = EngineResultBuilder(intent_id="intent_vwx")

        builder.build()

        with pytest.raises(ValueError, match="only be called once"):
            builder.build()

    def test_builder_chaining(self):
        """Builder methods should support chaining."""
        result = (
            EngineResultBuilder(intent_id="intent_chain", rng_offset=0)
            .add_event({"type": "attack_roll"})
            .add_roll("attack", "1d20", 15, 5, 20)
            .add_state_change("goblin_1", "hp", 10, 5)
            .set_narration_token("attack_hit")
            .add_metadata("critical", False)
            .build()
        )

        assert len(result.events) == 1
        assert len(result.rolls) == 1
        assert len(result.state_changes) == 1
        assert result.narration_token == "attack_hit"


class TestEngineResultSerialization:
    """Tests for EngineResult serialization."""

    def test_to_dict_includes_required_fields(self):
        """to_dict should include all required fields."""
        builder = EngineResultBuilder(intent_id="intent_serial")
        builder.add_roll("attack", "1d20", 17, 3, 20)
        result = builder.build()

        data = result.to_dict()

        assert data["result_id"] == result.result_id
        assert data["intent_id"] == "intent_serial"
        assert data["status"] == "success"
        assert "resolved_at" in data
        assert len(data["rolls"]) == 1

    def test_to_dict_omits_none_fields(self):
        """to_dict should omit None optional fields."""
        builder = EngineResultBuilder(intent_id="intent_minimal")
        result = builder.build()

        data = result.to_dict()

        assert "narration_token" not in data
        assert "failure_reason" not in data
        assert "metadata" not in data

    def test_roundtrip_serialization(self):
        """EngineResult should survive JSON roundtrip."""
        builder = EngineResultBuilder(intent_id="intent_roundtrip", rng_offset=5)
        builder.add_event({"type": "attack_roll", "hit": True})
        builder.add_roll("attack", "1d20", 18, 7, 25, {"weapon": "longsword"})
        builder.add_state_change("goblin_1", "hp", 15, 7)
        builder.set_narration_token("attack_hit")
        builder.add_metadata("critical", False)
        result = builder.build()

        json_str = json.dumps(result.to_dict(), sort_keys=True)
        restored = EngineResult.from_dict(json.loads(json_str))

        assert restored.intent_id == "intent_roundtrip"
        assert restored.status == EngineResultStatus.SUCCESS
        assert len(restored.events) == 1
        assert len(restored.rolls) == 1
        assert restored.rolls[0].natural_roll == 18
        assert len(restored.state_changes) == 1
        assert restored.narration_token == "attack_hit"
        assert restored.metadata == {"critical": False}
        assert restored.rng_initial_offset == 5

    def test_roundtrip_preserves_immutability(self):
        """Deserialized EngineResult should be frozen."""
        builder = EngineResultBuilder(intent_id="intent_frozen")
        result = builder.build()

        json_str = json.dumps(result.to_dict())
        restored = EngineResult.from_dict(json.loads(json_str))

        with pytest.raises(EngineResultFrozenError):
            restored.status = EngineResultStatus.FAILURE

    def test_roundtrip_failure_result(self):
        """Failed EngineResult should roundtrip correctly."""
        builder = EngineResultBuilder(intent_id="intent_fail")
        result = builder.build_failure("Invalid target")

        json_str = json.dumps(result.to_dict())
        restored = EngineResult.from_dict(json.loads(json_str))

        assert restored.status == EngineResultStatus.FAILURE
        assert restored.failure_reason == "Invalid target"


class TestEngineResultDeterminism:
    """Tests for determinism requirements per IPC contract."""

    def test_rng_offset_tracking(self):
        """RNG offsets should be tracked for replay verification."""
        builder = EngineResultBuilder(intent_id="intent_det", rng_offset=100)

        builder.add_roll("attack", "1d20", 15, 5, 20)
        builder.add_roll("damage", "1d8", 6, 2, 8)
        builder.add_roll("damage", "1d6", 4, 0, 4)

        result = builder.build()

        assert result.rng_initial_offset == 100
        assert result.rng_final_offset == 103
        assert result.rolls[0].rng_offset == 100
        assert result.rolls[1].rng_offset == 101
        assert result.rolls[2].rng_offset == 102

    def test_result_id_uniqueness(self):
        """Each EngineResult should have unique result_id."""
        builder1 = EngineResultBuilder(intent_id="intent_1")
        builder2 = EngineResultBuilder(intent_id="intent_2")

        result1 = builder1.build()
        result2 = builder2.build()

        assert result1.result_id != result2.result_id
        assert len(result1.result_id) == 36  # UUID format
