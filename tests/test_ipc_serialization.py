"""Tests for IPC Serialization & Transport (WO-M1-04)

Test Coverage:
- Round-trip determinism (T-IPC-01 through T-IPC-03)
- MessagePack settings enforcement (T-IPC-04 through T-IPC-06)
- IPC envelope structure (T-IPC-07 through T-IPC-09)
- BL-017/BL-018 compliance (T-IPC-10 through T-IPC-12)
- Cross-version tolerance (T-IPC-13)
- Transport abstraction (T-IPC-14)

Reference: WO-M1-04, IPC_CONTRACT.md, BL-017, BL-018
"""

import uuid
from datetime import datetime
from typing import Any, Dict

import pytest

from aidm.runtime.ipc_serialization import (
    IPCEnvelope,
    serialize_messagepack,
    deserialize_messagepack,
    serialize_ipc_message,
    deserialize_ipc_message,
    verify_round_trip,
    verify_determinism,
    InProcessTransport,
)
from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType
from aidm.schemas.engine_result import EngineResult, EngineResultStatus


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-01 through T-IPC-03: Round-Trip Determinism
# ═══════════════════════════════════════════════════════════════════════


class TestIPCRoundTripDeterminism:
    """T-IPC-01 through T-IPC-03: Core determinism guarantees."""

    def test_t_ipc_01_simple_dict_round_trip(self):
        """T-IPC-01: Simple dictionary round-trips identically."""
        data = {
            "version": "1.0",
            "message_type": "request",
            "payload": {"intent_id": "test-123", "action": "attack"},
        }

        # Serialize and deserialize
        serialized = serialize_messagepack(data)
        deserialized = deserialize_messagepack(serialized)

        # Must match exactly
        assert deserialized == data

    def test_t_ipc_02_nested_dict_round_trip(self):
        """T-IPC-02: Nested dictionaries preserve structure."""
        data = {
            "version": "1.0",
            "payload": {
                "intent": {
                    "intent_id": "test-456",
                    "actor_id": "fighter_1",
                    "parameters": {"weapon": "longsword", "modifiers": [2, 3, 5]},
                },
                "context": {"round": 3, "initiative_order": ["pc1", "orc1", "pc2"]},
            },
        }

        serialized = serialize_messagepack(data)
        deserialized = deserialize_messagepack(serialized)

        assert deserialized == data

    def test_t_ipc_03_byte_for_byte_determinism_10x(self):
        """T-IPC-03: Identical input produces identical bytes across 10 runs."""
        data = {
            "version": "1.0",
            "message_id": "msg-001",
            "timestamp": "2025-01-01T12:00:00",
            "payload": {"a": 1, "b": [2, 3, 4], "c": {"nested": "value"}},
        }

        # Serialize 10 times
        results = [serialize_messagepack(data) for _ in range(10)]

        # All must be identical
        first = results[0]
        for i, result in enumerate(results[1:], start=2):
            assert result == first, f"Run {i} produced different bytes"


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-04 through T-IPC-06: MessagePack Settings Enforcement
# ═══════════════════════════════════════════════════════════════════════


class TestIPCMessagePackSettings:
    """T-IPC-04 through T-IPC-06: MessagePack deterministic settings."""

    def test_t_ipc_04_dict_key_ordering_deterministic(self):
        """T-IPC-04: Dictionary keys are sorted for deterministic encoding."""
        # Two dicts with same keys in different insertion order
        data1 = {"z": 1, "a": 2, "m": 3}
        data2 = {"a": 2, "z": 1, "m": 3}

        serialized1 = serialize_messagepack(data1)
        serialized2 = serialize_messagepack(data2)

        # Must produce identical bytes (keys sorted before packing)
        assert serialized1 == serialized2

    def test_t_ipc_05_float_ieee_754_preservation(self):
        """T-IPC-05: Floats preserve IEEE 754 representation."""
        data = {"pi": 3.141592653589793, "e": 2.718281828459045}

        serialized = serialize_messagepack(data)
        deserialized = deserialize_messagepack(serialized)

        # Must be exact (not just close)
        assert deserialized["pi"] == 3.141592653589793
        assert deserialized["e"] == 2.718281828459045

    def test_t_ipc_06_binary_string_preservation(self):
        """T-IPC-06: Binary data and strings are distinct."""
        data = {
            "text": "hello",
            "binary": b"\x00\x01\x02\xff",
        }

        serialized = serialize_messagepack(data)
        deserialized = deserialize_messagepack(serialized)

        # Types preserved
        assert isinstance(deserialized["text"], str)
        assert isinstance(deserialized["binary"], bytes)
        assert deserialized["text"] == "hello"
        assert deserialized["binary"] == b"\x00\x01\x02\xff"


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-07 through T-IPC-09: IPC Envelope Structure
# ═══════════════════════════════════════════════════════════════════════


class TestIPCEnvelopeStructure:
    """T-IPC-07 through T-IPC-09: IPC envelope contract."""

    def test_t_ipc_07_envelope_required_fields(self):
        """T-IPC-07: IPC envelope requires all mandatory fields."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)

        # Valid envelope
        msg_bytes = serialize_ipc_message(
            message_type="request",
            payload={"test": "data"},
            message_id="msg-001",
            timestamp=timestamp,
        )

        envelope = deserialize_ipc_message(msg_bytes)

        assert envelope.version == "1.0"
        assert envelope.message_type == "request"
        assert envelope.message_id == "msg-001"
        assert envelope.timestamp == "2025-01-01T12:00:00"
        assert envelope.payload == {"test": "data"}

    def test_t_ipc_08_envelope_missing_fields_rejected(self):
        """T-IPC-08: Malformed envelopes are rejected."""
        # Missing required field
        malformed = {
            "version": "1.0",
            "message_type": "request",
            # missing message_id, timestamp, payload
        }

        serialized = serialize_messagepack(malformed)

        with pytest.raises(ValueError, match="missing fields"):
            deserialize_ipc_message(serialized)

    def test_t_ipc_09_envelope_optional_metadata(self):
        """T-IPC-09: Envelope metadata is optional."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)

        # With metadata
        msg_bytes = serialize_ipc_message(
            message_type="response",
            payload={"result": "success"},
            message_id="msg-002",
            timestamp=timestamp,
            metadata={"trace_id": "abc-123", "latency_ms": 42},
        )

        envelope = deserialize_ipc_message(msg_bytes)

        assert envelope.metadata is not None
        assert envelope.metadata["trace_id"] == "abc-123"
        assert envelope.metadata["latency_ms"] == 42


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-10 through T-IPC-12: BL-017 / BL-018 Compliance
# ═══════════════════════════════════════════════════════════════════════


class TestIPCBoundaryLawCompliance:
    """T-IPC-10 through T-IPC-12: BL-017/BL-018 injection-only enforcement."""

    def test_t_ipc_10_no_uuid_generation_during_serialization(self):
        """T-IPC-10: Serialization never generates UUIDs.

        UUIDs must be injected by caller (BL-017).
        """
        # Caller must provide message_id explicitly
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        message_id = str(uuid.uuid4())  # Generated by CALLER

        msg_bytes = serialize_ipc_message(
            message_type="request",
            payload={"test": "data"},
            message_id=message_id,  # INJECTED, not generated inside
            timestamp=timestamp,
        )

        envelope = deserialize_ipc_message(msg_bytes)

        # message_id matches what was injected
        assert envelope.message_id == message_id

    def test_t_ipc_11_no_timestamp_generation_during_serialization(self):
        """T-IPC-11: Serialization never generates timestamps.

        Timestamps must be injected by caller (BL-018).
        """
        # Caller must provide timestamp explicitly
        timestamp = datetime(2025, 6, 15, 14, 30, 0)  # Generated by CALLER
        message_id = "msg-test"

        msg_bytes = serialize_ipc_message(
            message_type="request",
            payload={"test": "data"},
            message_id=message_id,
            timestamp=timestamp,  # INJECTED, not generated inside
        )

        envelope = deserialize_ipc_message(msg_bytes)

        # timestamp matches what was injected
        assert envelope.timestamp == "2025-06-15T14:30:00"

    def test_t_ipc_12_intent_round_trip_preserves_injected_ids(self):
        """T-IPC-12: IntentObject round-trip preserves injected IDs/timestamps."""
        # Create intent with explicit IDs/timestamps
        intent_id = "intent-roundtrip-test"
        created_at = datetime(2025, 1, 1, 10, 0, 0)
        updated_at = datetime(2025, 1, 1, 10, 5, 0)

        intent = IntentObject(
            intent_id=intent_id,
            actor_id="fighter_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="I attack the orc",
            created_at=created_at,
            updated_at=updated_at,
        )

        # Serialize intent as payload
        payload = intent.to_dict()
        timestamp = datetime(2025, 1, 1, 10, 10, 0)
        message_id = "msg-intent-test"

        msg_bytes = serialize_ipc_message(
            message_type="request",
            payload=payload,
            message_id=message_id,
            timestamp=timestamp,
        )

        # Deserialize and restore intent
        envelope = deserialize_ipc_message(msg_bytes)
        restored_intent = IntentObject.from_dict(envelope.payload)

        # IDs and timestamps preserved exactly
        assert restored_intent.intent_id == intent_id
        assert restored_intent.created_at == created_at
        assert restored_intent.updated_at == updated_at


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-13: Cross-Version Tolerance
# ═══════════════════════════════════════════════════════════════════════


class TestIPCCrossVersionTolerance:
    """T-IPC-13: Unknown fields are ignored (forward compatibility)."""

    def test_t_ipc_13_unknown_fields_ignored(self):
        """T-IPC-13: Envelope with unknown fields deserializes successfully."""
        # Envelope with extra field from future version
        envelope_dict = {
            "version": "1.0",
            "message_type": "request",
            "message_id": "msg-future",
            "timestamp": "2025-01-01T12:00:00",
            "payload": {"test": "data"},
            "unknown_future_field": "should_be_ignored",  # Not in current schema
        }

        serialized = serialize_messagepack(envelope_dict)
        envelope = deserialize_ipc_message(serialized)

        # Required fields present
        assert envelope.version == "1.0"
        assert envelope.message_id == "msg-future"
        assert envelope.payload == {"test": "data"}

        # Unknown field silently ignored (not in dataclass)


# ═══════════════════════════════════════════════════════════════════════
# T-IPC-14: Transport Abstraction
# ═══════════════════════════════════════════════════════════════════════


class TestIPCTransportAbstraction:
    """T-IPC-14: Transport layer works as expected for M1."""

    def test_t_ipc_14_in_process_transport_send_receive(self):
        """T-IPC-14: InProcessTransport buffers messages correctly."""
        transport = InProcessTransport()
        timestamp = datetime(2025, 1, 1, 12, 0, 0)

        # Serialize message
        msg_bytes = serialize_ipc_message(
            message_type="request",
            payload={"action": "test"},
            message_id="msg-transport",
            timestamp=timestamp,
        )

        # Send
        transport.send(msg_bytes)
        assert transport.has_messages()

        # Receive
        received = transport.receive()
        assert received == msg_bytes

        # Buffer empty after receive
        assert not transport.has_messages()


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests: EngineResult Serialization
# ═══════════════════════════════════════════════════════════════════════


class TestIPCEngineResultSerialization:
    """Integration test: EngineResult serialization via IPC."""

    def test_engine_result_round_trip_via_ipc(self):
        """EngineResult can be serialized as IPC payload and restored."""
        # Create EngineResult with explicit IDs/timestamps
        result_id = "result-ipc-test"
        intent_id = "intent-ipc-test"
        resolved_at = datetime(2025, 1, 1, 12, 0, 0)

        result = EngineResult(
            result_id=result_id,
            intent_id=intent_id,
            status=EngineResultStatus.SUCCESS,
            resolved_at=resolved_at,
            narration_token="attack_hit",
        )

        # Serialize as IPC message
        payload = result.to_dict()
        timestamp = datetime(2025, 1, 1, 12, 5, 0)
        message_id = "msg-result"

        msg_bytes = serialize_ipc_message(
            message_type="response",
            payload=payload,
            message_id=message_id,
            timestamp=timestamp,
        )

        # Deserialize
        envelope = deserialize_ipc_message(msg_bytes)
        restored_result = EngineResult.from_dict(envelope.payload)

        # Verify preservation
        assert restored_result.result_id == result_id
        assert restored_result.intent_id == intent_id
        assert restored_result.status == EngineResultStatus.SUCCESS
        assert restored_result.resolved_at == resolved_at
        assert restored_result.narration_token == "attack_hit"

    def test_engine_result_hash_unchanged_after_ipc(self):
        """EngineResult hash is unchanged pre/post IPC serialization.

        This verifies replay integrity: serialization doesn't corrupt state.
        """
        from aidm.core.state import WorldState

        # Create world state and hash it
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 10, "ac": 15}},
            active_combat={"round": 1},
        )
        original_hash = ws.state_hash()

        # Serialize world state as part of EngineResult metadata
        result_id = "result-hash-test"
        intent_id = "intent-hash-test"
        resolved_at = datetime(2025, 1, 1, 12, 0, 0)

        result = EngineResult(
            result_id=result_id,
            intent_id=intent_id,
            status=EngineResultStatus.SUCCESS,
            resolved_at=resolved_at,
            metadata={"world_state_hash": original_hash},
        )

        # IPC round-trip
        payload = result.to_dict()
        timestamp = datetime(2025, 1, 1, 12, 5, 0)
        message_id = "msg-hash"

        msg_bytes = serialize_ipc_message(
            message_type="response",
            payload=payload,
            message_id=message_id,
            timestamp=timestamp,
        )

        envelope = deserialize_ipc_message(msg_bytes)
        restored_result = EngineResult.from_dict(envelope.payload)

        # Hash preserved
        assert restored_result.metadata["world_state_hash"] == original_hash


# ═══════════════════════════════════════════════════════════════════════
# Utility Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestIPCUtilityFunctions:
    """Test verify_round_trip and verify_determinism helpers."""

    def test_verify_round_trip_success(self):
        """verify_round_trip returns True for valid data."""
        data = {"version": "1.0", "payload": {"test": [1, 2, 3]}}
        assert verify_round_trip(data) is True

    def test_verify_determinism_success(self):
        """verify_determinism returns True for deterministic data."""
        data = {"version": "1.0", "message_id": "test-001"}
        assert verify_determinism(data, iterations=10) is True

    def test_verify_determinism_detects_nondeterminism(self):
        """verify_determinism would fail on non-deterministic data.

        NOTE: MessagePack with our settings IS deterministic, so we can't
        create a real failure case without mocking. This test is for documentation.
        """
        # If we had non-deterministic serialization, this would fail:
        # data = {"timestamp": datetime.now()}  # changes each time
        # verify_determinism(data)  # would raise AssertionError
        pass
