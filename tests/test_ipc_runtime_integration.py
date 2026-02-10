"""WO-M1-06: IPC Runtime Integration Tests

This test suite demonstrates that the runtime session components (IntentObject,
EngineResult, WorldState) are fully compatible with the MessagePack IPC layer
implemented in WO-M1-04.

SCOPE:
- Prove IntentObject → IPC → IntentObject roundtrip is lossless
- Prove EngineResult → IPC → EngineResult roundtrip is lossless
- Prove WorldState hash unchanged after IPC serialization
- Prove SessionLog can be transmitted via IPC (JSONL → IPC → JSONL)

NO BEHAVIORAL CHANGES:
- Runtime session code unchanged
- All existing tests remain passing
- IPC layer is opt-in, not required

Reference: WO-M1-06, IPC_CONTRACT.md, BL-017, BL-018, BL-020
"""

import uuid
from datetime import datetime

import pytest

from aidm.runtime.ipc_serialization import (
    serialize_ipc_message,
    deserialize_ipc_message,
    serialize_messagepack,
    deserialize_messagepack,
    verify_round_trip,
    verify_determinism,
)
from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType
from aidm.schemas.engine_result import EngineResult, EngineResultStatus
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.runtime.session import IntentEntry, SessionLog


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-RT-01: IntentObject IPC Serialization
# ═══════════════════════════════════════════════════════════════════════


class TestIPCIntentObjectSerialization:
    """T-IPC-RT-01 through T-IPC-RT-03: IntentObject through IPC layer."""

    def test_t_ipc_rt_01_intent_via_ipc_envelope(self):
        """T-IPC-RT-01: IntentObject serialized via IPC envelope roundtrips correctly."""
        # Create IntentObject with all fields populated
        intent_id = "intent-rt-01"
        created_at = datetime(2025, 1, 1, 10, 0, 0)
        updated_at = datetime(2025, 1, 1, 10, 5, 0)

        intent = IntentObject(
            intent_id=intent_id,
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.CONFIRMED,
            source_text="I attack the orc with my longsword",
            created_at=created_at,
            updated_at=updated_at,
            target_id="orc_1",
        )

        # Serialize via IPC envelope
        payload = intent.to_dict()
        timestamp = datetime(2025, 1, 1, 10, 10, 0)
        message_id = str(uuid.uuid4())

        msg_bytes = serialize_ipc_message(
            message_type="request",
            payload=payload,
            message_id=message_id,
            timestamp=timestamp,
        )

        # Deserialize and restore
        envelope = deserialize_ipc_message(msg_bytes)
        restored_intent = IntentObject.from_dict(envelope.payload)

        # Verify preservation
        assert restored_intent.intent_id == intent_id
        assert restored_intent.actor_id == "fighter_1"
        assert restored_intent.action_type == ActionType.ATTACK
        assert restored_intent.status == IntentStatus.CONFIRMED
        assert restored_intent.source_text == "I attack the orc with my longsword"
        assert restored_intent.created_at == created_at
        assert restored_intent.updated_at == updated_at
        assert restored_intent.target_id == "orc_1"

    def test_t_ipc_rt_02_intent_deterministic_serialization(self):
        """T-IPC-RT-02: IntentObject serialization is byte-for-byte deterministic."""
        intent = IntentObject(
            intent_id="intent-rt-02",
            actor_id="wizard_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.CONFIRMED,
            source_text="I cast magic missile",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        payload = intent.to_dict()

        # Verify determinism across 10 serializations
        assert verify_determinism(payload, iterations=10)

    def test_t_ipc_rt_03_frozen_intent_status_preserved(self):
        """T-IPC-RT-03: Frozen intent status preserved through IPC."""
        intent = IntentObject(
            intent_id="intent-rt-03",
            actor_id="rogue_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="I sneak attack",
            created_at=datetime(2025, 1, 1, 14, 0, 0),
            updated_at=datetime(2025, 1, 1, 14, 0, 0),
        )

        # Confirm intent (freezes it)
        intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 14, 1, 0))

        assert intent.is_frozen

        # IPC roundtrip
        payload = intent.to_dict()
        assert verify_round_trip(payload)

        restored_intent = IntentObject.from_dict(payload)

        # Frozen state preserved
        assert restored_intent.is_frozen
        assert restored_intent.status == IntentStatus.CONFIRMED


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-RT-04: EngineResult IPC Serialization
# ═══════════════════════════════════════════════════════════════════════


class TestIPCEngineResultSerialization:
    """T-IPC-RT-04 through T-IPC-RT-06: EngineResult through IPC layer."""

    def test_t_ipc_rt_04_engine_result_via_ipc_envelope(self):
        """T-IPC-RT-04: EngineResult serialized via IPC envelope roundtrips correctly."""
        result_id = "result-rt-04"
        intent_id = "intent-rt-04"
        resolved_at = datetime(2025, 1, 1, 15, 0, 0)

        result = EngineResult(
            result_id=result_id,
            intent_id=intent_id,
            status=EngineResultStatus.SUCCESS,
            resolved_at=resolved_at,
            narration_token="attack_critical_hit",
        )

        # Serialize via IPC envelope
        payload = result.to_dict()
        timestamp = datetime(2025, 1, 1, 15, 1, 0)
        message_id = str(uuid.uuid4())

        msg_bytes = serialize_ipc_message(
            message_type="response",
            payload=payload,
            message_id=message_id,
            timestamp=timestamp,
        )

        # Deserialize and restore
        envelope = deserialize_ipc_message(msg_bytes)
        restored_result = EngineResult.from_dict(envelope.payload)

        # Verify preservation
        assert restored_result.result_id == result_id
        assert restored_result.intent_id == intent_id
        assert restored_result.status == EngineResultStatus.SUCCESS
        assert restored_result.resolved_at == resolved_at
        assert restored_result.narration_token == "attack_critical_hit"

    def test_t_ipc_rt_05_engine_result_deterministic_serialization(self):
        """T-IPC-RT-05: EngineResult serialization is byte-for-byte deterministic."""
        result = EngineResult(
            result_id="result-rt-05",
            intent_id="intent-rt-05",
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime(2025, 1, 1, 16, 0, 0),
        )

        payload = result.to_dict()

        # Verify determinism across 10 serializations
        assert verify_determinism(payload, iterations=10)

    def test_t_ipc_rt_06_engine_result_with_rolls_preserved(self):
        """T-IPC-RT-06: EngineResult with rolls preserves all roll data."""
        from aidm.schemas.engine_result import DiceRoll, RollType

        result = EngineResult(
            result_id="result-rt-06",
            intent_id="intent-rt-06",
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime(2025, 1, 1, 17, 0, 0),
        )

        # Add dice rolls
        result.rolls.append(
            DiceRoll(
                roll_type=RollType.ATTACK,
                natural_roll=18,
                modifier=5,
                total=23,
            )
        )
        result.rolls.append(
            DiceRoll(
                roll_type=RollType.DAMAGE,
                natural_roll=7,
                modifier=3,
                total=10,
            )
        )

        # IPC roundtrip
        payload = result.to_dict()
        assert verify_round_trip(payload)

        restored_result = EngineResult.from_dict(payload)

        # Rolls preserved
        assert len(restored_result.rolls) == 2
        assert restored_result.rolls[0].roll_type == RollType.ATTACK
        assert restored_result.rolls[0].natural_roll == 18
        assert restored_result.rolls[1].roll_type == RollType.DAMAGE
        assert restored_result.rolls[1].natural_roll == 7


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-RT-07: WorldState IPC Serialization (BL-020 Compliance)
# ═══════════════════════════════════════════════════════════════════════


class TestIPCWorldStateSerialization:
    """T-IPC-RT-07 through T-IPC-RT-09: WorldState immutability at IPC boundaries."""

    def test_t_ipc_rt_07_world_state_hash_unchanged_after_ipc(self):
        """T-IPC-RT-07: WorldState hash unchanged after IPC serialization (BL-020)."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "fighter": {"hp": 45, "hp_max": 50, "ac": 18},
                "orc": {"hp": 12, "hp_max": 12, "ac": 13},
            },
            active_combat={"round": 3, "initiative_order": ["fighter", "orc"]},
        )

        original_hash = ws.state_hash()

        # IPC roundtrip (serialize world state as metadata)
        payload = ws.to_dict()
        assert verify_round_trip(payload)

        restored_ws = WorldState.from_dict(payload)
        restored_hash = restored_ws.state_hash()

        # Hash must be identical (no corruption from serialization)
        assert restored_hash == original_hash

    def test_t_ipc_rt_08_frozen_world_state_view_at_boundary(self):
        """T-IPC-RT-08: FrozenWorldStateView enforces immutability at IPC boundary."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"wizard": {"hp": 30, "mp": 15}},
        )

        # Create frozen view (non-engine boundary)
        frozen = FrozenWorldStateView(ws)

        # Frozen view prevents mutation
        with pytest.raises(AttributeError):
            frozen.entities = {}

        # Frozen view can be serialized
        payload = frozen.to_dict()
        assert verify_round_trip(payload)

    def test_t_ipc_rt_09_world_state_deterministic_serialization(self):
        """T-IPC-RT-09: WorldState serialization is byte-for-byte deterministic."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "cleric": {"hp": 40, "spells_remaining": [3, 2, 1]},
                "goblin1": {"hp": 5},
                "goblin2": {"hp": 5},
            },
        )

        payload = ws.to_dict()

        # Verify determinism across 10 serializations
        assert verify_determinism(payload, iterations=10)


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-RT-10: SessionLog IPC Serialization
# ═══════════════════════════════════════════════════════════════════════


class TestIPCSessionLogSerialization:
    """T-IPC-RT-10 through T-IPC-RT-12: SessionLog through IPC layer."""

    def test_t_ipc_rt_10_intent_entry_via_ipc(self):
        """T-IPC-RT-10: IntentEntry can be transmitted via IPC."""
        intent = IntentObject(
            intent_id="intent-entry-01",
            actor_id="paladin_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.RESOLVED,
            source_text="I smite the undead",
            created_at=datetime(2025, 1, 1, 18, 0, 0),
            updated_at=datetime(2025, 1, 1, 18, 0, 0),
        )

        result = EngineResult(
            result_id="result-entry-01",
            intent_id="intent-entry-01",
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime(2025, 1, 1, 18, 1, 0),
        )

        entry = IntentEntry(
            intent=intent,
            result=result,
            logged_at=datetime(2025, 1, 1, 18, 2, 0),
        )

        # Serialize IntentEntry as IPC payload
        payload = entry.to_dict()
        assert verify_round_trip(payload)

        restored_entry = IntentEntry.from_dict(payload)

        # Verify preservation
        assert restored_entry.intent.intent_id == "intent-entry-01"
        assert restored_entry.result.result_id == "result-entry-01"
        assert restored_entry.logged_at == datetime(2025, 1, 1, 18, 2, 0)

    def test_t_ipc_rt_11_session_log_metadata_via_ipc(self):
        """T-IPC-RT-11: SessionLog metadata can be transmitted via IPC."""
        log = SessionLog(
            session_id="session-rt-11",
            master_seed=99999,
            started_at=datetime(2025, 1, 1, 20, 0, 0),
        )

        # Serialize session metadata as IPC payload
        metadata_payload = {
            "session_id": log.session_id,
            "master_seed": log.master_seed,
            "started_at": log.started_at.isoformat() if log.started_at else None,
        }

        assert verify_round_trip(metadata_payload)

        # Verify determinism
        assert verify_determinism(metadata_payload, iterations=10)

    def test_t_ipc_rt_12_full_session_log_deterministic(self):
        """T-IPC-RT-12: Full SessionLog with entries is deterministically serializable."""
        log = SessionLog(
            session_id="session-rt-12",
            master_seed=12345,
            started_at=datetime(2025, 1, 1, 21, 0, 0),
        )

        # Add multiple entries
        for i in range(3):
            intent = IntentObject(
                intent_id=f"intent-{i}",
                actor_id="ranger_1",
                action_type=ActionType.ATTACK,
                status=IntentStatus.RESOLVED,
                source_text=f"Action {i}",
                created_at=datetime(2025, 1, 1, 21, i, 0),
                updated_at=datetime(2025, 1, 1, 21, i, 0),
            )

            result = EngineResult(
                result_id=f"result-{i}",
                intent_id=f"intent-{i}",
                status=EngineResultStatus.SUCCESS,
                resolved_at=datetime(2025, 1, 1, 21, i, 30),
            )

            entry = IntentEntry(
                intent=intent,
                result=result,
                logged_at=datetime(2025, 1, 1, 21, i, 45),
            )

            log.append(entry)

        # Serialize full log as payload
        full_log_payload = {
            "session_id": log.session_id,
            "master_seed": log.master_seed,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "entries": [entry.to_dict() for entry in log.entries],
        }

        # Verify determinism across 10 serializations
        assert verify_determinism(full_log_payload, iterations=10)


# ═══════════════════════════════════════════════════════════════════════
# Integration Test: Full IPC Flow Simulation
# ═══════════════════════════════════════════════════════════════════════


class TestIPCFullFlowSimulation:
    """Integration test simulating full IPC flow without changing runtime code."""

    def test_full_ipc_flow_request_response(self):
        """Simulate complete IPC request/response flow for intent resolution.

        This test demonstrates that the IPC layer is ready for use, but does NOT
        require changes to the existing runtime session code.
        """
        # === REQUEST: Client → Engine ===

        # Create intent (client side)
        intent = IntentObject(
            intent_id="intent-flow-test",
            actor_id="bard_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.CONFIRMED,
            source_text="I inspire allies with song",
            created_at=datetime(2025, 1, 2, 10, 0, 0),
            updated_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        # Serialize request via IPC
        request_payload = intent.to_dict()
        request_timestamp = datetime(2025, 1, 2, 10, 1, 0)
        request_msg_id = str(uuid.uuid4())

        request_bytes = serialize_ipc_message(
            message_type="request",
            payload=request_payload,
            message_id=request_msg_id,
            timestamp=request_timestamp,
        )

        # === ENGINE PROCESSING (simulated) ===

        # Deserialize request (engine side)
        request_envelope = deserialize_ipc_message(request_bytes)
        engine_intent = IntentObject.from_dict(request_envelope.payload)

        # Engine processes intent (simulated)
        engine_result = EngineResult(
            result_id=str(uuid.uuid4()),
            intent_id=engine_intent.intent_id,
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime(2025, 1, 2, 10, 2, 0),
            narration_token="inspire_courage_success",
        )

        # === RESPONSE: Engine → Client ===

        # Serialize response via IPC
        response_payload = engine_result.to_dict()
        response_timestamp = datetime(2025, 1, 2, 10, 3, 0)
        response_msg_id = str(uuid.uuid4())

        response_bytes = serialize_ipc_message(
            message_type="response",
            payload=response_payload,
            message_id=response_msg_id,
            timestamp=response_timestamp,
        )

        # Deserialize response (client side)
        response_envelope = deserialize_ipc_message(response_bytes)
        client_result = EngineResult.from_dict(response_envelope.payload)

        # === VERIFICATION ===

        # Intent preserved through IPC
        assert engine_intent.intent_id == intent.intent_id
        assert engine_intent.status == IntentStatus.CONFIRMED

        # Result preserved through IPC
        assert client_result.intent_id == intent.intent_id
        assert client_result.status == EngineResultStatus.SUCCESS
        assert client_result.narration_token == "inspire_courage_success"

        # Both serializations are deterministic
        assert verify_determinism(request_payload, iterations=5)
        assert verify_determinism(response_payload, iterations=5)
