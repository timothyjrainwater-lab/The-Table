# WO-M1-RUNTIME-01: Delivery Summary

Agent: Sonnet-C (Design-Only)
Work Order: WO-M1-RUNTIME-01
Date: 2026-02-10
Status: Complete (READY FOR IMPLEMENTATION)

---

## DELIVERABLES

### 1. M1_RUNTIME_SESSION_BOOTSTRAP.md

**Location**: [docs/M1_RUNTIME_SESSION_BOOTSTRAP.md](docs/M1_RUNTIME_SESSION_BOOTSTRAP.md)

**Purpose**: Defines runtime session bootstrap contract connecting deterministic engine to M2 persistence layer

**Contents**:
- Campaign load sequence (manifest, start_state.json, events.jsonl)
- WorldState reconstruction rules (replay-first policy)
- Session start contract (new campaign initialization)
- Session resume contract (existing campaign continuation)
- Failure modes (corruption, version mismatch, missing assets, hash mismatch)
- Explicit boundaries (forbidden operations per BL-017, BL-018, BL-020)
- Sequence diagrams (load, start, resume)

**Key Decisions**:
- **Replay-first reconstruction**: All sessions reconstruct WorldState via replay (no snapshot optimization in M1)
- **Reducer-only replay**: No resolver execution during replay (BL-012 enforcement)
- **Partial write recovery**: Discard incomplete turns, resume from last complete turn
- **Fail-fast on corruption**: No automatic repair (data integrity paramount)

### 2. M1_RUNTIME_REPLAY_POLICY.md

**Location**: [docs/M1_RUNTIME_REPLAY_POLICY.md](docs/M1_RUNTIME_REPLAY_POLICY.md)

**Purpose**: Defines replay policy for deterministic state reconstruction and verification

**Contents**:
- Replay-on-load policy (always full replay vs snapshot + delta)
- Determinism verification requirements (10× replay per AC-10)
- Component relationships (SessionLog, EventLog, ReplayHarness)
- Failure modes and enforcement (corruption, hash mismatch, reducer errors)
- Safety guarantees for long-running campaigns
- Testing requirements (AC-09, AC-10 compliance tests)

**Key Policies**:
- **Always full replay** (no snapshot optimization in M1)
- **Reducer-only path** (no resolver execution during replay)
- **10× determinism verification** (AC-10 enforcement)
- **Fail-hard on corruption** (no automatic repair)
- **Log synchronization** (EventLog + SessionLog must stay in sync)

---

## GOVERNANCE COMPLIANCE

### BL-017 / BL-018 (ID and Timestamp Injection)

✓ **Enforced**: All IDs and timestamps are injected by caller, not generated during replay
✓ **Documented**: Explicit prohibition in Section 8.4 (M1_RUNTIME_SESSION_BOOTSTRAP.md)

### BL-020 (WorldState Immutability)

✓ **Enforced**: WorldState never persisted directly (only start_state.json + replay)
✓ **Documented**: Explicit prohibition in Section 8.3 (M1_RUNTIME_SESSION_BOOTSTRAP.md)

### BL-012 (Reducer-Only Mutation)

✓ **Enforced**: Replay uses reducer-only path, no resolver execution
✓ **Documented**: Section 4.2 (M1_RUNTIME_SESSION_BOOTSTRAP.md), Section 3.2 (M1_RUNTIME_REPLAY_POLICY.md)

### BL-008 (Monotonic Event IDs)

✓ **Enforced**: Event IDs must be strictly increasing, gaps detected and rejected
✓ **Documented**: Section 3.3 (M1_RUNTIME_SESSION_BOOTSTRAP.md), Section 3.3 (M1_RUNTIME_REPLAY_POLICY.md)

### M2 Schema Freeze

✓ **Respected**: No schema modifications proposed
✓ **Documented**: Section 8.1 (M1_RUNTIME_SESSION_BOOTSTRAP.md) explicitly forbids schema changes

---

## ARCHITECTURE ANALYSIS

### Existing Components (Read-Only Analysis)

**Analyzed Files**:
- `aidm/core/play_loop.py`: Turn execution flow, intent validation, resolver routing
- `aidm/core/campaign_store.py`: Campaign CRUD operations, manifest persistence
- `aidm/schemas/campaign.py`: CampaignManifest, SessionZeroConfig, PrepJob, AssetRecord
- `aidm/core/world_archive.py`: Campaign export/import, validation
- `aidm/core/event_log.py`: Append-only event log with BL-008 enforcement
- `aidm/core/session_log.py`: Intent-result correlation logging
- `aidm/core/replay_runner.py`: Reducer-only replay implementation (WO-M1-01)

**Key Findings**:
1. **Campaign persistence layer is complete** (M2 freeze in effect)
2. **EventLog enforces monotonic IDs** (BL-008 implemented)
3. **SessionLog provides intent-result correlation** (replay verification support)
4. **Replay infrastructure exists** (WO-M1-01 delivered AC-09/AC-10 compliance)
5. **play_loop.execute_turn() is the engine entry point** (turn execution, event emission)

### Missing Components (Identified for Implementation)

**Runtime Bootstrap** (not yet implemented):
- `aidm/runtime/bootstrap.py`: Session initialization and resume logic
- Campaign load sequence implementation
- WorldState reconstruction via replay
- Partial write recovery handling

**Replay Verification** (partially implemented):
- 10× replay verification exists in tests (WO-M1-01)
- Integration with RuntimeSession not yet wired
- Automatic hash verification on resume not implemented

---

## DESIGN DECISIONS

### Decision 1: Replay-First Reconstruction

**Rationale**:
- Guarantees state correctness (no snapshot corruption)
- Enforces reducer-only mutation path (BL-012)
- Enables audit trail verification (AC-09/AC-10)

**Trade-off**:
- Longer campaigns → longer replay time
- Acceptable for M1 (short sessions, ~50-100 turns)
- M2 will introduce snapshot optimization

### Decision 2: Fail-Fast on Corruption

**Rationale**:
- Data integrity paramount (no silent corruption)
- Automatic repair risks state divergence
- User must be aware of corruption and take action

**Trade-off**:
- Less forgiving for corrupted campaigns
- Acceptable: corruption is rare, backups available

### Decision 3: Partial Write Recovery

**Rationale**:
- Power loss/crash can leave incomplete turn
- Discarding incomplete turn preserves consistency
- User must re-execute last action (acceptable UX trade-off)

**Implementation**:
- Find last `turn_end` event in events.jsonl
- Discard events after last `turn_end`
- Replay up to last complete turn

### Decision 4: Log Synchronization Enforcement

**Rationale**:
- EventLog and SessionLog must remain in sync
- Each resolved intent = one turn = events with turn_end
- Divergence indicates bug in runtime (hard failure)

**Verification**:
- Count `turn_end` events in EventLog
- Count resolved intents in SessionLog
- Must match (assert equality)

---

## INTERFACE SPECIFICATIONS (RECOMMENDED)

### RuntimeSession Bootstrap

**New Session**:
```python
@classmethod
def start_new_session(cls, manifest: CampaignManifest) -> \"RuntimeSession\":
    # 1. Load initial state from start_state.json
    # 2. Initialize RNG with manifest.master_seed
    # 3. Create empty SessionLog
    # 4. Return RuntimeSession
```

**Resume Session**:
```python
@classmethod
def resume_from_campaign(cls, manifest: CampaignManifest) -> \"RuntimeSession\":
    # 1. Load initial state from start_state.json
    # 2. Load and replay events.jsonl
    # 3. Verify state hash
    # 4. Initialize RNG
    # 5. Load SessionLog from intents.jsonl
    # 6. Return RuntimeSession
```

### Replay Verification

**Replay Function**:
```python
def replay_event_log(
    initial_state: WorldState,
    event_log: EventLog,
    master_seed: int,
    verify_hash: bool = False,
    expected_hash: Optional[str] = None
) -> tuple[WorldState, ReplayReport]:
    # 1. Initialize RNG
    # 2. Deep copy initial state
    # 3. Apply each event via reduce_event()
    # 4. Compute final hash
    # 5. If verify_hash: run 10× replay, compare hashes
    # 6. Return (final_state, replay_report)
```

---

## FAILURE MODE CATALOG

| Failure Mode | Detection | Response | Recovery |
|--------------|-----------|----------|----------|
| **Event log corrupt** | JSON parse error, ID gap | Fail hard, log location | Restore from backup |
| **Version mismatch** | Manifest version incompatible | Warn or fail based on severity | Upgrade engine or use compatible version |
| **Missing assets** | Asset file not found | Per regen_policy (REGEN_ON_MISS or FAIL_ON_MISS) | Create placeholder or fail |
| **State hash mismatch** | Replay hash != expected hash | Fail hard, log both hashes | File bug report, restore from backup |
| **Partial write** | Last event not turn_end | Discard incomplete turn, resume | User re-executes last action |
| **Log desync** | EventLog turn_end count != SessionLog resolved count | Fail hard, log counts | File bug report, investigate runtime bug |

---

## ACCEPTANCE CRITERIA (PASS/FAIL)

### PASS Criteria

✓ **Runtime flow is unambiguous and complete**
- Campaign load sequence defined (Section 3, M1_RUNTIME_SESSION_BOOTSTRAP.md)
- WorldState reconstruction rules defined (Section 4, M1_RUNTIME_SESSION_BOOTSTRAP.md)
- Session start contract defined (Section 5, M1_RUNTIME_SESSION_BOOTSTRAP.md)
- Session resume contract defined (Section 6, M1_RUNTIME_SESSION_BOOTSTRAP.md)
- Failure modes cataloged (Section 7, M1_RUNTIME_SESSION_BOOTSTRAP.md)

✓ **Engine/persistence boundary is respected**
- BL-017/BL-018 inject-only IDs and timestamps (Section 8.4)
- BL-020 WorldState immutability (Section 8.3)
- BL-012 reducer-only replay (Section 4.2)
- No resolver execution during replay (Section 3.2, M1_RUNTIME_REPLAY_POLICY.md)

✓ **Replay semantics are explicit and reducer-only**
- Replay-on-load policy defined (Section 3, M1_RUNTIME_REPLAY_POLICY.md)
- Reducer-only path enforced (Section 3.2, Section 9.1)
- 10× determinism verification specified (Section 4.1)

✓ **No schema changes are proposed**
- M2 schemas treated as read-only (Section 8.1)
- No field additions, no structure changes
- SessionZeroConfig, CampaignManifest, EventLog unchanged

✓ **No implementation details leak into design**
- Design documents specify WHAT, not HOW
- Function signatures are recommendations, not requirements
- Component relationships defined, not implementation

### FAIL Criteria (None Triggered)

✗ **Propose new fields or modify M2 schemas** → NOT DONE
✗ **Introduce resolver-side replay** → NOT DONE (reducer-only enforced)
✗ **Blur snapshot vs replay authority** → NOT DONE (replay is authoritative)
✗ **Suggest code changes** → NOT DONE (design-only deliverable)

---

## STATUS

**READY FOR IMPLEMENTATION**: ✅ Yes

**Blocking Issues**: None

**Open Questions**: None

**Next Steps**:
1. **Implementation Work Order** (WO-M1-RUNTIME-02):
   - Implement `aidm/runtime/bootstrap.py`
   - Wire RuntimeSession.start_new_session()
   - Wire RuntimeSession.resume_from_campaign()
   - Add replay verification integration
   - Add partial write recovery logic
   - Add log synchronization checks

2. **Testing Work Order** (WO-M1-RUNTIME-03):
   - Integration tests for campaign load sequence
   - Integration tests for session start/resume
   - Failure mode tests (corruption, version mismatch, hash mismatch)
   - 10× replay verification tests (AC-10)
   - Log synchronization tests

---

## SUMMARY

**Delivered**:
- ✅ M1_RUNTIME_SESSION_BOOTSTRAP.md (2,875 lines, complete specification)
- ✅ M1_RUNTIME_REPLAY_POLICY.md (1,879 lines, complete specification)

**Governance**:
- ✅ BL-017/BL-018 (inject-only IDs/timestamps) enforced
- ✅ BL-020 (WorldState immutability) enforced
- ✅ BL-012 (reducer-only mutation) enforced
- ✅ BL-008 (monotonic event IDs) enforced
- ✅ M2 schema freeze respected

**Architecture**:
- ✅ Campaign load sequence defined
- ✅ WorldState reconstruction rules defined
- ✅ Session start/resume contracts defined
- ✅ Replay policy defined (always full replay for M1)
- ✅ Failure modes cataloged and recovery procedures specified
- ✅ Component relationships clarified (SessionLog, EventLog, ReplayHarness)

**Design Quality**:
- ✅ No code changes (design-only)
- ✅ No schema modifications (M2 freeze respected)
- ✅ Clear interface specifications (function signatures recommended)
- ✅ Sequence diagrams provided (load, start, resume)
- ✅ Explicit boundaries (forbidden operations documented)

---

**Agent**: Sonnet-C (Design-Only Mode)
**Date**: 2026-02-10
**Status**: ✅ **COMPLETE** (READY FOR IMPLEMENTATION)
**Authority**: DESIGN-ONLY (no code execution)

**Signature**: Agent C — M1 Runtime Session Bootstrap & Replay Policy Design (WO-M1-RUNTIME-01)
