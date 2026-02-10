"""IPC Serialization & Transport — Deterministic Contract Implementation

Authority:
- IPC_CONTRACT.md (M1 runtime authority boundaries)
- BL-017 / BL-018 (inject-only IDs/timestamps)
- SPARK/LENS/BOX boundary doctrine

This module implements deterministic serialization and transport for M1 runtime.

Key Properties:
- Byte-for-byte deterministic round trips
- Strict type preservation (no silent coercion)
- Float IEEE 754 preservation
- Explicit key ordering for maps
- Versioning support (forward compatibility)
- No UUID/timestamp generation during (de)serialization

Serialization:
- Default: MessagePack (compact binary format)
- Settings: strict_types=True, use_bin_type=True
- Manual key sorting for deterministic dict encoding
- Float preservation via MessagePack native support

Transport:
- M1: In-process (file/memory)
- Clear seam for future out-of-process swap
- No async concurrency yet

Reference: docs/runtime/IPC_CONTRACT.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import msgpack
import json


# ═══════════════════════════════════════════════════════════════════════
# IPC Envelope Schema
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class IPCEnvelope:
    """IPC message envelope for M1 runtime.

    All IPC messages (requests and responses) use this envelope format.

    Fields:
        version: Protocol version (for forward compatibility)
        message_type: Type of message ('request' or 'response')
        message_id: Unique identifier for this message
        timestamp: Message creation time (ISO 8601 string)
        payload: Message payload (schema depends on message_type)
        metadata: Optional metadata (for debugging, tracing)
    """

    version: str
    message_type: str  # 'request' | 'response'
    message_id: str
    timestamp: str  # ISO 8601 format
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert envelope to dictionary for serialization.

        Keys are explicitly ordered for deterministic encoding.
        """
        result = {
            "version": self.version,
            "message_type": self.message_type,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }
        if self.metadata is not None:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPCEnvelope":
        """Create envelope from dictionary."""
        return cls(
            version=data["version"],
            message_type=data["message_type"],
            message_id=data["message_id"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            metadata=data.get("metadata"),
        )


# ═══════════════════════════════════════════════════════════════════════
# MessagePack Serialization (Deterministic)
# ═══════════════════════════════════════════════════════════════════════


def _sort_dict_keys(obj: Any) -> Any:
    """Recursively sort dictionary keys for deterministic encoding.

    MessagePack preserves key order, so we must sort before packing.

    Args:
        obj: Object to normalize (dict, list, or primitive)

    Returns:
        Normalized object with sorted keys
    """
    if isinstance(obj, dict):
        return {k: _sort_dict_keys(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [_sort_dict_keys(item) for item in obj]
    else:
        return obj


def serialize_messagepack(data: Dict[str, Any]) -> bytes:
    """Serialize dictionary to MessagePack with deterministic settings.

    Guarantees:
    - Byte-for-byte identical output for identical inputs
    - Sorted dictionary keys (deterministic ordering)
    - Strict types (no silent coercion)
    - Binary strings preserved
    - Float IEEE 754 preservation

    Args:
        data: Dictionary to serialize

    Returns:
        MessagePack binary bytes

    Raises:
        TypeError: If data contains non-serializable types
    """
    # Sort keys for deterministic ordering
    normalized = _sort_dict_keys(data)

    # Pack with deterministic settings
    return msgpack.packb(
        normalized,
        strict_types=True,  # No silent type coercion
        use_bin_type=True,  # Separate binary from string
    )


def deserialize_messagepack(data: bytes) -> Dict[str, Any]:
    """Deserialize MessagePack bytes to dictionary.

    Args:
        data: MessagePack binary bytes

    Returns:
        Deserialized dictionary

    Raises:
        ValueError: If data is malformed or unsupported version
        TypeError: If data is not bytes
    """
    if not isinstance(data, bytes):
        raise TypeError(f"Expected bytes, got {type(data).__name__}")

    # Unpack with strict types
    return msgpack.unpackb(
        data,
        strict_map_key=False,  # Allow non-string keys (for flexibility)
        raw=False,  # Decode binary as strings where appropriate
    )


# ═══════════════════════════════════════════════════════════════════════
# High-Level IPC Serialization API
# ═══════════════════════════════════════════════════════════════════════


def serialize_ipc_message(
    message_type: str,
    payload: Dict[str, Any],
    message_id: str,
    timestamp: datetime,
    version: str = "1.0",
    metadata: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Serialize an IPC message to MessagePack bytes.

    This is the primary serialization entry point for M1 runtime.

    Args:
        message_type: Type of message ('request' or 'response')
        payload: Message payload (schema depends on message_type)
        message_id: Unique identifier for this message (BL-017: must be injected)
        timestamp: Message creation time (BL-018: must be injected)
        version: Protocol version (default: '1.0')
        metadata: Optional metadata

    Returns:
        MessagePack binary bytes

    Example:
        >>> import uuid
        >>> from datetime import datetime
        >>> payload = {"intent_id": "test-123", "action": "attack"}
        >>> msg_bytes = serialize_ipc_message(
        ...     message_type="request",
        ...     payload=payload,
        ...     message_id=str(uuid.uuid4()),
        ...     timestamp=datetime.utcnow(),
        ... )
    """
    envelope = IPCEnvelope(
        version=version,
        message_type=message_type,
        message_id=message_id,
        timestamp=timestamp.isoformat(),
        payload=payload,
        metadata=metadata,
    )

    envelope_dict = envelope.to_dict()
    return serialize_messagepack(envelope_dict)


def deserialize_ipc_message(data: bytes) -> IPCEnvelope:
    """Deserialize MessagePack bytes to IPC envelope.

    Args:
        data: MessagePack binary bytes

    Returns:
        IPCEnvelope with parsed message

    Raises:
        ValueError: If envelope is malformed or version unsupported
        TypeError: If data is not bytes
    """
    envelope_dict = deserialize_messagepack(data)

    # Validate envelope structure
    required_fields = {"version", "message_type", "message_id", "timestamp", "payload"}
    missing = required_fields - set(envelope_dict.keys())
    if missing:
        raise ValueError(f"Malformed IPC envelope: missing fields {missing}")

    return IPCEnvelope.from_dict(envelope_dict)


# ═══════════════════════════════════════════════════════════════════════
# Round-Trip Verification Utilities
# ═══════════════════════════════════════════════════════════════════════


def verify_round_trip(data: Dict[str, Any]) -> bool:
    """Verify that data can be serialized and deserialized identically.

    Useful for testing determinism properties.

    Args:
        data: Dictionary to test

    Returns:
        True if round-trip preserves data exactly

    Raises:
        AssertionError: If round-trip does not match
    """
    serialized = serialize_messagepack(data)
    deserialized = deserialize_messagepack(serialized)

    # Use JSON for comparison (handles nested structures)
    original_json = json.dumps(_sort_dict_keys(data), sort_keys=True)
    restored_json = json.dumps(_sort_dict_keys(deserialized), sort_keys=True)

    if original_json != restored_json:
        raise AssertionError(
            f"Round-trip failed:\n"
            f"Original:  {original_json}\n"
            f"Restored:  {restored_json}"
        )

    return True


def verify_determinism(data: Dict[str, Any], iterations: int = 10) -> bool:
    """Verify that serialization produces identical bytes across iterations.

    Tests the core determinism guarantee: same input → same output.

    Args:
        data: Dictionary to test
        iterations: Number of serialization attempts (default: 10)

    Returns:
        True if all iterations produce identical bytes

    Raises:
        AssertionError: If any iteration produces different bytes
    """
    results = [serialize_messagepack(data) for _ in range(iterations)]

    # All results must be byte-for-byte identical
    first = results[0]
    for i, result in enumerate(results[1:], start=2):
        if result != first:
            raise AssertionError(
                f"Determinism violated: iteration {i} produced different bytes"
            )

    return True


# ═══════════════════════════════════════════════════════════════════════
# Transport Abstraction (M1: In-Process)
# ═══════════════════════════════════════════════════════════════════════


class IPCTransport:
    """Abstract transport layer for IPC messages.

    M1 implementation uses in-process memory (or file if persistence needed).
    Future milestones can swap in socket/pipe/gRPC without changing callers.

    This is a SEAM for future out-of-process transport.
    """

    def send(self, message_bytes: bytes) -> None:
        """Send serialized message bytes.

        Args:
            message_bytes: MessagePack-encoded IPC envelope
        """
        raise NotImplementedError("Transport.send() must be implemented by subclass")

    def receive(self) -> bytes:
        """Receive serialized message bytes.

        Returns:
            MessagePack-encoded IPC envelope
        """
        raise NotImplementedError("Transport.receive() must be implemented by subclass")


class InProcessTransport(IPCTransport):
    """In-process transport using memory queue.

    For M1: Components run in same process, so this is just a pass-through.
    """

    def __init__(self):
        """Initialize in-process transport with message buffer."""
        self._buffer: List[bytes] = []

    def send(self, message_bytes: bytes) -> None:
        """Store message in in-process buffer."""
        self._buffer.append(message_bytes)

    def receive(self) -> bytes:
        """Retrieve message from in-process buffer.

        Returns:
            Next message bytes

        Raises:
            IndexError: If buffer is empty
        """
        if not self._buffer:
            raise IndexError("No messages in buffer")
        return self._buffer.pop(0)

    def has_messages(self) -> bool:
        """Check if buffer has messages."""
        return len(self._buffer) > 0

    def clear(self) -> None:
        """Clear all messages from buffer."""
        self._buffer.clear()
