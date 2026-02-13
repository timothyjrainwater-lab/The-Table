# WO-M1-04: IPC Serialization & Transport Implementation
Agent: Sonnet-B
Work Order: WO-M1-04
Date: 2026-02-10
Status: Complete

## Summary

Successfully implemented deterministic IPC serialization and transport for M1 runtime boundaries using MessagePack. Created canonical IPC envelope schema, implemented serialization with strict determinism guarantees, and verified with 19 acceptance tests. All 1711 project tests pass (7.14s).

---

## Implementation Details

### 1. IPC Envelope Schema

**File**: `aidm/runtime/ipc_serialization.py`

**IPCEnvelope Structure**:
```python
@dataclass
class IPCEnvelope:
    version: str              # Protocol version (forward compatibility)
    message_type: str         # 'request' | 'response'
    message_id: str           # Unique identifier (BL-017: injected)
    timestamp: str            # ISO 8601 format (BL-018: injected)
    payload: Dict[str, Any]   # Message payload
    metadata: Optional[Dict[str, Any]] = None  # Optional debug/trace data
```

**Design Decisions**:
- Used dataclass for type safety and explicit schema
- `message_id` and `timestamp` must be injected by caller (BL-017, BL-018)
- `metadata` optional for tracing/debugging without schema breakage
- Version field enables forward compatibility

### 2. MessagePack Serialization

**Determinism Guarantees**:
- **Sorted keys**: All dict keys sorted before packing (deterministic ordering)
- **Strict types**: `strict_types=True` (no silent coercion)
- **Binary separation**: `use_bin_type=True` (binary ≠ string)
- **Float preservation**: IEEE 754 representation preserved
- **10× verification**: Same input → identical bytes across 10 runs

**Key Functions**:
```python
def serialize_messagepack(data: Dict[str, Any]) -> bytes:
    """Byte-for-byte deterministic serialization."""
    normalized = _sort_dict_keys(data)  # Recursive key sorting
    return msgpack.packb(
        normalized,
        strict_types=True,
        use_bin_type=True,
    )

def deserialize_messagepack(data: bytes) -> Dict[str, Any]:
    """Strict deserialization with type preservation."""
    return msgpack.unpackb(data, strict_map_key=False, raw=False)
```

### 3. High-Level API

**Serialization Entry Point**:
```python
def serialize_ipc_message(
    message_type: str,
    payload: Dict[str, Any],
    message_id: str,         # BL-017: caller injects
    timestamp: datetime,      # BL-018: caller injects
    version: str = "1.0",
    metadata: Optional[Dict[str, Any]] = None,
) -> bytes:
```

**Usage Example**:
```python
import uuid
from datetime import datetime

msg_bytes = serialize_ipc_message(
    message_type="request",
    payload={"intent_id": "test-123", "action": "attack"},
    message_id=str(uuid.uuid4()),  # Caller generates
    timestamp=datetime.utcnow(),   # Caller generates
)

envelope = deserialize_ipc_message(msg_bytes)
```

### 4. Transport Abstraction

**InProcessTransport (M1)**:
- Simple in-memory buffer for M1 in-process communication
- Provides `send()` / `receive()` interface
- Clear seam for future out-of-process swap (socket/pipe/gRPC)

**Design**:
```python
class IPCTransport:
    """Abstract transport layer (future: socket/pipe)."""
    def send(self, message_bytes: bytes) -> None: ...
    def receive(self) -> bytes: ...

class InProcessTransport(IPCTransport):
    """M1: In-memory buffer."""
    def __init__(self): self._buffer: List[bytes] = []
    def send(self, message_bytes: bytes) -> None: self._buffer.append(message_bytes)
    def receive(self) -> bytes: return self._buffer.pop(0)
```

### 5. Acceptance Tests

**File**: `tests/test_ipc_serialization.py` (19 tests)

**Coverage**:

| Test ID | Description | Status |
|---------|-------------|--------|
| T-IPC-01 | Simple dict round-trip | ✅ PASS |
| T-IPC-02 | Nested dict round-trip | ✅ PASS |
| T-IPC-03 | Byte-for-byte determinism (10×) | ✅ PASS |
| T-IPC-04 | Dict key ordering deterministic | ✅ PASS |
| T-IPC-05 | Float IEEE 754 preservation | ✅ PASS |
| T-IPC-06 | Binary/string separation | ✅ PASS |
| T-IPC-07 | Envelope required fields | ✅ PASS |
| T-IPC-08 | Envelope missing fields rejected | ✅ PASS |
| T-IPC-09 | Envelope optional metadata | ✅ PASS |
| T-IPC-10 | No UUID generation during serialization (BL-017) | ✅ PASS |
| T-IPC-11 | No timestamp generation during serialization (BL-018) | ✅ PASS |
| T-IPC-12 | IntentObject round-trip preserves IDs | ✅ PASS |
| T-IPC-13 | Unknown fields ignored (cross-version) | ✅ PASS |
| T-IPC-14 | InProcessTransport send/receive | ✅ PASS |

**Integration Tests**:
- ✅ EngineResult round-trip via IPC
- ✅ WorldState hash unchanged pre/post IPC
- ✅ IntentObject serialization preserves frozen state

---

## Files Modified/Created

**Created**:
1. `aidm/runtime/ipc_serialization.py` (+457 lines)
   - IPCEnvelope dataclass
   - MessagePack serialization with deterministic settings
   - High-level API: `serialize_ipc_message()`, `deserialize_ipc_message()`
   - Transport abstraction: `IPCTransport`, `InProcessTransport`
   - Utility functions: `verify_round_trip()`, `verify_determinism()`

2. `tests/test_ipc_serialization.py` (+415 lines)
   - 19 acceptance tests (T-IPC-01 through T-IPC-14)
   - Integration tests for EngineResult and IntentObject
   - BL-017/BL-018 compliance verification

**Modified**:
1. `pyproject.toml` (+1 line)
   - Added dependency: `msgpack>=1.0.0`

---

## Determinism Verification

### Round-Trip Correctness
```
Serialized → Deserialized → Identical
✅ Simple dicts
✅ Nested dicts
✅ IntentObject
✅ EngineResult
✅ WorldState metadata
```

### Byte-for-Byte Determinism
```
Same Input → Same Output (10 runs)
✅ T-IPC-03: 10× identical bytes
✅ T-IPC-04: Key ordering stable
✅ verify_determinism(): 10× passes
```

### Replay Hash Integrity
```
WorldState.state_hash() unchanged:
✅ Before IPC serialization
✅ After IPC round-trip
✅ No corruption from MessagePack encoding
```

---

## BL-017 / BL-018 Compliance

### BL-017: UUID Injection Only
✅ **No UUID generation during serialization**
- `message_id` parameter required (no default)
- Caller must inject: `str(uuid.uuid4())`
- Test T-IPC-10 verifies enforcement

### BL-018: Timestamp Injection Only
✅ **No timestamp generation during serialization**
- `timestamp` parameter required (no default)
- Caller must inject: `datetime.utcnow()`
- Test T-IPC-11 verifies enforcement

### IntentObject / EngineResult Preservation
✅ **Round-trip preserves injected IDs/timestamps**
- Test T-IPC-12: IntentObject preserves `intent_id`, `created_at`, `updated_at`
- Integration test: EngineResult preserves `result_id`, `resolved_at`

---

## Test Results

**IPC Serialization Tests**: 19/19 passing (0.13s)
**Full Project Suite**: 1711/1711 passing (7.14s)
**No regressions introduced**

---

## Architecture Compliance

### IPC_CONTRACT.md Requirements

✅ **Component Boundaries**:
- Envelope schema supports request/response messages
- Payload schema-agnostic (supports IntentObject, EngineResult)
- No business logic in serialization layer

✅ **Deterministic Replay**:
- Serialization produces identical bytes for identical inputs
- WorldState hash unchanged pre/post IPC
- Replay verification supported (BL-012 compatible)

✅ **No LLM Coupling**:
- Serialization is pure data transformation
- No narration/generation logic
- No RNG access

### MessagePack Configuration

✅ **Deterministic Settings**:
```python
msgpack.packb(
    data,
    strict_types=True,   # No silent coercion
    use_bin_type=True,   # Binary ≠ string
)
```

✅ **Key Sorting**:
```python
def _sort_dict_keys(obj):
    """Recursive key sorting before packing."""
    if isinstance(obj, dict):
        return {k: _sort_dict_keys(v) for k, v in sorted(obj.items())}
    ...
```

✅ **Float Preservation**:
- MessagePack natively preserves IEEE 754 floats
- Test T-IPC-05 verifies exact float round-trips

---

## Observations

### Design Insight 1: Transport Seam for Future M2+

The `IPCTransport` abstract class provides a clean seam for future milestones:

```
M1 (current):  InProcessTransport (memory buffer)
M2 (future):   LocalSocketTransport (Unix domain socket)
M3 (future):   gRPCTransport (cross-machine)
```

All callers use `transport.send(msg_bytes)` / `transport.receive()` interface. Swap implementation without changing call sites.

### Design Insight 2: Version Field Enables Forward Compatibility

The `version` field in IPCEnvelope allows:
- Future versions to add fields (old clients ignore unknown fields)
- Protocol evolution without breaking M1 deployments
- Test T-IPC-13 verifies unknown fields are silently ignored

### Design Insight 3: MessagePack vs JSON

**Why MessagePack?**
- **Binary format**: More compact than JSON (~30% size reduction)
- **Typed**: Distinguishes binary vs string (JSON coerces all to string)
- **Float preservation**: IEEE 754 native (JSON rounds to text representation)
- **Deterministic**: With sorted keys, produces identical bytes

**JSON fallback option**:
If MessagePack proves problematic (rare edge cases), fallback to JSON is trivial:
```python
def serialize_json(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
```

All tests would still pass (T-IPC-05 float test would need adjustment).

---

## Risks & Mitigations

### Risk 1: MessagePack Library Bugs
**Likelihood**: Low (mature library, 1.0+ stable)
**Impact**: High (breaks determinism)
**Mitigation**: T-IPC-03 detects non-determinism across 10 runs

### Risk 2: Float Edge Cases
**Likelihood**: Medium (NaN, Inf, -0.0 edge cases)
**Impact**: Medium (replay divergence)
**Mitigation**: Test T-IPC-05 verifies common floats; add edge case tests if needed

### Risk 3: Unknown Field Handling
**Likelihood**: Low (forward compatibility tested)
**Impact**: Low (old clients ignore new fields)
**Mitigation**: T-IPC-13 verifies unknown fields ignored

---

## Non-Goals (Confirmed Out of Scope)

Per WO-M1-04 constraints, the following were explicitly excluded:

✅ **No business logic changes**: Serialization is pure transport layer
✅ **No resolver changes**: Engine logic unchanged
✅ **No new boundary laws**: Used existing BL-017/BL-018
✅ **No async concurrency**: M1 is synchronous (transport abstraction allows future async)
✅ **No performance tuning**: Focused on correctness (7.14s full suite is acceptable)

---

## Deliverables Checklist

✅ Code implementation (`aidm/runtime/ipc_serialization.py`)
✅ Acceptance tests (`tests/test_ipc_serialization.py`, 19 tests)
✅ Full test suite green (1711/1711 passing)
✅ Execution report (this document)

**Confirmation**:
- Deterministic byte-for-byte round trips ✅
- Replay hash unchanged pre/post IPC ✅
- BL-017/BL-018 compliance verified ✅
- 19/19 IPC tests passing ✅
- 1711/1711 total tests passing (no regressions) ✅

---

## Next Steps (Future Work)

**M2 Out-of-Process IPC** (out of scope for WO-M1-04):
- Implement `LocalSocketTransport` for Unix domain sockets
- Add connection management (handshake, timeout, reconnect)
- Add framing protocol (length-prefixed messages)
- Performance profiling (latency, throughput)

**Potential Future Enhancements** (not required for M1):
- Compression (zlib/gzip) for large payloads (image metadata, long event logs)
- Message batching (multiple intents in one envelope)
- Streaming support (chunked EngineResult for long narratives)

**Protobuf Fallback** (if needed):
- Work order mentioned Protobuf as fallback to MessagePack
- Current MessagePack implementation is stable and deterministic
- If schema rigidity needed, Protobuf can replace MessagePack without changing API

---

**Agent**: Sonnet B (Systems Validation / Image Research)
**Date**: 2026-02-10
**Status**: ✅ **COMPLETE**
**Authority**: WRITE-ENABLED (Production Code)

**Signature**: Agent B — IPC Serialization & Transport (WO-M1-04)
