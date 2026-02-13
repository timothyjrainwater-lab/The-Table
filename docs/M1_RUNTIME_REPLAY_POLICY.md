# M1 Runtime Replay Policy

**Document ID:** M1-REPLAY-001
**Version:** 1.0
**Date:** 2026-02-10
**Status:** CANONICAL (M1)
**Authority:** Binding for M1 Solo Vertical Slice

---

## 1. PURPOSE

This document defines the **replay policy** for M1 runtime, establishing:
- Replay-on-load policy (always replay vs snapshot + delta)
- Determinism verification requirements (10× replay)
- Relationship between SessionLog, EventLog, and ReplayHarness
- Safety guarantees for long-running campaigns
- Hard failure conditions and enforcement

**Design-only**: This is architectural specification. No code changes are proposed.

---

## 2. REPLAY POLICY OVERVIEW

### 2.1 Core Principle

**Replay is the single source of truth for WorldState reconstruction.**

All session resumes MUST reconstruct WorldState by replaying events through the reducer (BL-012). Direct state serialization is forbidden (BL-020).

### 2.2 Replay Types

| Replay Type | When Used | Purpose |
|-------------|-----------|---------|
| **Full Replay** | Session resume | Reconstruct WorldState from start_state.json + events.jsonl |
| **Verification Replay** | Testing, audit | Verify determinism (10× replay produces identical state) |
| **Partial Replay** | M2+ optimization | Snapshot + delta replay (NOT in M1 scope) |

---

## 3. REPLAY-ON-LOAD POLICY

### 3.1 M1 Policy: Always Full Replay

**Rule**: Every session resume MUST perform full replay from `start_state.json`.

**No Exceptions**:
- No snapshot optimization
- No delta replay
- No partial replay from checkpoint

**Why**:
- Guarantees state correctness
- Prevents snapshot corruption
- Enforces reducer-only mutation path (BL-012)
- Enables audit trail verification

**Trade-off**:
- Longer campaigns → longer replay time
- Acceptable for M1 (short sessions, ~50-100 turns)
- M2 will introduce snapshot optimization

### 3.2 Replay Execution Path

**Reducer-Only Path**:
```python
def reconstruct_world_state(
    start_state: WorldState,
    event_log: EventLog,
    master_seed: int
) -> WorldState:
    \"\"\"Reconstruct WorldState via reducer-only replay.

    NO RESOLVER EXECUTION.
    NO EVENT EMISSION.
    NO RNG CONSUMPTION (beyond what's recorded in events).
    \"\"\"
    from aidm.core.replay_runner import reduce_event
    from copy import deepcopy

    rng = RNGManager(master_seed)
    current_state = deepcopy(start_state)

    # Replay each event through reducer
    for event in event_log.events:
        current_state = reduce_event(current_state, event, rng)

    return current_state
```

**Critical**: `reduce_event()` is the ONLY function called. No resolvers, no policy evaluation, no intent processing.

### 3.3 Replay Ordering Guarantees

**BL-008 Enforcement**:
- Events MUST be applied in strict `event_id` order
- No gaps allowed (monotonic ID sequence)
- No reordering permitted

**Replay Loop**:
```python
for event in event_log.events:
    assert event.event_id == expected_id, \"Event ID gap detected\"
    current_state = reduce_event(current_state, event, rng)
    expected_id += 1
```

**Failure**: Event log corrupted → hard failure (see Section 6.1)

---

## 4. DETERMINISM VERIFICATION

### 4.1 10× Replay Requirement

**Rule (AC-10)**: Any event log MUST produce identical `state_hash` when replayed 10 times.

**When Verified**:
- **Development**: All test suites run 10× replay verification
- **Testing**: Pre-release validation runs 10× on sample campaigns
- **Production**: Optional (user can request via `--verify-replay` flag)

**Test Format**:
```python
def test_10x_replay_produces_identical_hashes():
    \"\"\"AC-10: Replay produces identical state_hash 10 times.\"\"\"
    initial_state = load_start_state()
    event_log = EventLog.from_jsonl(\"events.jsonl\")
    master_seed = manifest.master_seed

    hashes = []
    for run in range(10):
        final_state = reconstruct_world_state(initial_state, event_log, master_seed)
        hashes.append(final_state.state_hash())

    unique_hashes = set(hashes)
    assert len(unique_hashes) == 1, (
        f\"Replay produced {len(unique_hashes)} different hashes. \"
        f\"Expected: 1 (perfect determinism). Got: {unique_hashes}\"
    )
```

### 4.2 What Constitutes Hard Failure

**Hard Failure Conditions**:
1. **Hash divergence across replays**: Different state_hash values in 10× replay
2. **Event log corruption**: Missing events, ID gaps, parse errors
3. **Schema mismatch**: Event payloads don't match expected structure
4. **Reducer error**: Exception raised during `reduce_event()`

**Response**:
- **STOP**: Do not proceed with session
- **LOG**: Record exact divergence (expected hash vs actual hash)
- **ALERT**: User notification with recovery options

**User Actions**:
- Restore from backup
- Contact support (bug in reducer or event emission)
- Review event log for corruption

### 4.3 Soft Warnings (Non-Blocking)

**Warning Conditions**:
- **Slow replay**: Full replay takes >5 seconds (campaign growing large)
- **Missing metadata**: SessionLog lacks expected hash (non-critical)
- **Asset missing**: Referenced asset file not found (regen_policy handles)

**Response**:
- **LOG**: Warning message
- **PROCEED**: Continue with session
- **SUGGEST**: User action (e.g., \"Consider archiving old campaigns\")

---

## 5. COMPONENT RELATIONSHIPS

### 5.1 SessionLog vs EventLog

| Component | Purpose | Authority | Format |
|-----------|---------|-----------|--------|
| **EventLog** | Records ALL state-mutating events | Authoritative for replay | events.jsonl (Event objects) |
| **SessionLog** | Records intent → result correlation | Authoritative for intent history | intents.jsonl (IntentObject + EngineResult) |

**Relationship**:
- **EventLog** is the source of truth for WorldState reconstruction
- **SessionLog** provides intent-result correlation for replay verification and audit
- **Both must remain in sync**: Each resolved intent emits events → both logs updated

**Divergence Detection**:
```python
def verify_log_sync(event_log: EventLog, session_log: SessionLog) -> bool:
    \"\"\"Verify EventLog and SessionLog are synchronized.\"\"\"
    # Count turn_end events in EventLog
    turn_end_count = sum(1 for e in event_log.events if e.event_type == \"turn_end\")

    # Count resolved intents in SessionLog
    resolved_count = sum(1 for entry in session_log.entries
                        if entry.result is not None)

    # Should match (each resolved intent = one turn)
    if turn_end_count != resolved_count:
        raise LogSyncError(
            f\"Log synchronization error: \"
            f\"{turn_end_count} turn_end events vs {resolved_count} resolved intents\"
        )

    return True
```

### 5.2 ReplayHarness Responsibility

**ReplayHarness**: Test utility for verifying determinism

**Responsibilities**:
- Load event log
- Execute 10× replay
- Compare state hashes
- Report divergence

**NOT Responsible For**:
- Persisting state (that's CampaignStore's job)
- Modifying event log (read-only access)
- Emitting new events (replay is reduction-only)

**Usage**:
```python
from aidm.core.replay_runner import run

# Run 10× replay verification
hashes = []
for i in range(10):
    report = run(initial_state, master_seed, event_log)
    hashes.append(report.final_hash)

assert len(set(hashes)) == 1, \"Replay divergence detected\"
```

### 5.3 Event Emission vs Event Reduction

**Emission** (during live play):
- **Where**: Resolvers (`resolve_attack`, `resolve_full_attack`, etc.)
- **When**: During turn execution
- **Output**: Events added to EventLog
- **RNG**: Consumed during resolution

**Reduction** (during replay):
- **Where**: `reduce_event()` in `replay_runner.py`
- **When**: During session resume / replay verification
- **Output**: Updated WorldState (no new events)
- **RNG**: NOT consumed (events already contain roll results)

**Critical**: These are SEPARATE code paths. Replay NEVER calls resolvers.

---

## 6. FAILURE MODES AND ENFORCEMENT

### 6.1 Event Log Corruption

**Detection**:
- JSON parse error in events.jsonl
- Missing event fields (`event_id`, `event_type`, `payload`)
- Event ID gap (e.g., events 0-47, then 49 → missing 48)
- Out-of-order event IDs

**Response**:
- **FAIL HARD**: Raise `EventLogCorruptionError`
- **DO NOT** attempt repair (data integrity violation)
- **LOG**: Exact corruption location (line number, event_id)

**User Recovery**:
- Restore from backup
- Manual repair (if corruption is understood)
- Contact support (file bug report)

### 6.2 State Hash Mismatch

**Detection**:
- After replay: `final_state.state_hash() != expected_hash`
- Expected hash from SessionLog or previous replay

**Response**:
- **FAIL HARD**: Raise `StateReconstructionError`
- **LOG**: Both hashes for debugging
- **DO NOT** proceed (determinism violation)

**Potential Causes**:
- Nondeterministic reducer (bug in `reduce_event()`)
- Event log corruption (undetected)
- Schema version mismatch (old events, new reducer)

### 6.3 Reducer Exception

**Detection**:
- Exception raised during `reduce_event()` call
- E.g., `KeyError`, `TypeError`, `AttributeError`

**Response**:
- **FAIL HARD**: Raise `ReplayFailureError` with original exception
- **LOG**: Event that caused failure (event_id, event_type, payload)
- **DO NOT** skip event (would corrupt state)

**User Recovery**:
- File bug report (reducer bug)
- Check for schema mismatch (old event format)

### 6.4 RNG Stream Exhaustion

**Detection**:
- RNG stream offset exceeds expected range during replay

**Response**:
- **FAIL HARD**: Raise `RNGStreamExhaustionError`
- **LOG**: Event_id where exhaustion occurred

**Potential Causes**:
- Resolver consumed more RNG during live play than expected
- Reducer trying to consume RNG during replay (BUG)

**Critical**: Reducer must NEVER consume RNG. Events already contain roll results.

---

## 7. SAFETY GUARANTEES FOR LONG-RUNNING CAMPAIGNS

### 7.1 M1 Constraints

**Maximum Campaign Length** (recommended):
- **Turns**: ~100-200 turns
- **Events**: ~1000-2000 events
- **Replay Time**: <5 seconds on typical hardware

**Beyond M1 Limits**:
- Replay time scales linearly with event count
- 10,000 events ≈ 50 seconds replay time
- M2 introduces snapshot optimization

### 7.2 Data Integrity Protections

**Append-Only Logs**:
- `events.jsonl`: Append-only, never modified
- `intents.jsonl`: Append-only, never modified
- **Benefit**: Corruption-resistant (failed writes leave log intact)

**Atomic Writes**:
- Each event written as single JSON line + newline
- Partial write → incomplete line → detected as parse error
- **Recovery**: Discard incomplete line, resume from last complete event

**Backup Strategy** (recommended):
- Periodic copy of campaign directory
- Git-style versioning (each session = commit)
- Export to archive for long-term storage

### 7.3 Forward Compatibility

**Schema Versioning**:
- `manifest.config_schema_version`: Tracks schema version
- Old campaigns remain playable with compatible runtime
- New runtimes can load old campaigns (read-only compatibility)

**Event Schema Evolution**:
- New event types: Added to `MUTATING_EVENTS` or `INFORMATIONAL_EVENTS`
- Old event types: Remain supported (no breaking changes)
- **Migration**: If event schema changes, provide `from_dict_v1()` fallback

**Replay Guarantee**:
- Campaign created in M1 (engine `0.1.0`) remains replayable in M2 (`0.2.0`)
- Runtime must support all historical event schemas

---

## 8. IMPLEMENTATION GUIDANCE (DESIGN-ONLY)

### 8.1 Replay Function Signature

**Recommended**:
```python
def replay_event_log(
    initial_state: WorldState,
    event_log: EventLog,
    master_seed: int,
    verify_hash: bool = False,
    expected_hash: Optional[str] = None
) -> tuple[WorldState, ReplayReport]:
    \"\"\"Replay event log to reconstruct WorldState.

    Args:
        initial_state: Start state (from start_state.json)
        event_log: Event log to replay
        master_seed: Master RNG seed (for determinism)
        verify_hash: If True, perform 10× replay verification
        expected_hash: Expected final hash (for verification)

    Returns:
        (final_state, replay_report)

    Raises:
        EventLogCorruptionError: If event log is corrupt
        StateReconstructionError: If hash mismatch detected
        ReplayFailureError: If reducer raises exception
    \"\"\"
    pass  # Implementation in WO-M1-RUNTIME-02
```

### 8.2 Replay Report Structure

**Recommended**:
```python
@dataclass
class ReplayReport:
    \"\"\"Report of replay execution with verification results.\"\"\"

    final_state: WorldState
    final_hash: str
    events_processed: int
    determinism_verified: bool
    divergence_info: str = \"\"
    replay_duration_ms: float = 0.0
```

### 8.3 Integration with RuntimeSession

**Bootstrap Flow**:
```python
class RuntimeSession:
    @classmethod
    def resume_from_campaign(cls, manifest: CampaignManifest) -> \"RuntimeSession\":
        # 1. Load initial state
        start_state = load_start_state(manifest)

        # 2. Load and replay events
        event_log = EventLog.from_jsonl(manifest.paths.events)
        world_state, report = replay_event_log(
            start_state,
            event_log,
            manifest.master_seed,
            verify_hash=True
        )

        # 3. Verify determinism
        if not report.determinism_verified:
            raise StateReconstructionError(report.divergence_info)

        # 4. Initialize RNG
        rng = RNGManager(manifest.master_seed)

        # 5. Load session log
        session_log = SessionLog.from_jsonl(manifest.paths.intents)

        return cls(
            world_state=world_state,
            rng=rng,
            session_log=session_log,
            campaign_id=manifest.campaign_id
        )
```

---

## 9. EXPLICIT POLICIES

### 9.1 What Replay MUST DO

✓ **Apply events in strict order** (event_id 0, 1, 2, ... N)
✓ **Use reducer-only path** (no resolver calls)
✓ **Preserve deep copy semantics** (no mutation of input state)
✓ **Verify event log integrity** (no gaps, no corruption)
✓ **Produce deterministic output** (same input → same state_hash)

### 9.2 What Replay MUST NOT DO

✗ **Call resolvers** (resolver execution is live-play only)
✗ **Emit new events** (replay applies existing events)
✗ **Consume RNG** (events already contain roll results)
✗ **Modify event log** (read-only access)
✗ **Skip or reorder events** (strict ordering required)
✗ **Generate IDs or timestamps** (BL-017/BL-018 inject-only)

### 9.3 What Replay MAY DO

○ **Verify state hash** (optional verification step)
○ **Log warnings** (slow replay, large campaigns)
○ **Suggest optimizations** (\"Consider snapshot for M2\")

---

## 10. TESTING REQUIREMENTS

### 10.1 Determinism Tests

**Test: AC-10 (10× Replay)**
```python
def test_ac10_replay_10x_produces_identical_hashes():
    \"\"\"AC-10: Replay produces identical state_hash 10 times.\"\"\"
    hashes = []
    for i in range(10):
        report = run(initial_state, master_seed, event_log)
        hashes.append(report.final_hash)

    assert len(set(hashes)) == 1, \"Replay divergence detected\"
```

**Test: AC-09 (Mutating Event Coverage)**
```python
def test_ac09_all_mutating_events_have_handlers():
    \"\"\"AC-09: Every mutating event type must have a reducer handler.\"\"\"
    missing = get_missing_handlers()
    assert len(missing) == 0, f\"Missing handlers: {missing}\"
```

### 10.2 Corruption Detection Tests

**Test: Event ID Gap Detection**
```python
def test_replay_detects_event_id_gaps():
    event_log = EventLog()
    event_log.append(Event(event_id=0, ...))
    event_log.append(Event(event_id=2, ...))  # Gap: missing 1

    with pytest.raises(EventLogCorruptionError):
        replay_event_log(initial_state, event_log, master_seed)
```

**Test: Hash Mismatch Detection**
```python
def test_replay_detects_hash_mismatch():
    expected_hash = \"abc123...\"
    actual_hash = \"def456...\"

    with pytest.raises(StateReconstructionError):
        replay_event_log(
            initial_state,
            event_log,
            master_seed,
            verify_hash=True,
            expected_hash=expected_hash
        )
```

### 10.3 Integration Tests

**Test: Full Campaign Resume**
```python
def test_full_campaign_resume():
    # 1. Create campaign
    manifest = create_campaign(...)

    # 2. Play 10 turns
    for i in range(10):
        execute_turn(...)

    # 3. Save and exit
    save_campaign(manifest)

    # 4. Resume campaign
    session = RuntimeSession.resume_from_campaign(manifest)

    # 5. Verify state hash matches
    assert session.world_state.state_hash() == expected_hash
```

---

## 11. SUMMARY

**READY FOR IMPLEMENTATION**: Yes

**Key Policies**:
1. **Always full replay** (no snapshot optimization in M1)
2. **Reducer-only path** (no resolver execution during replay)
3. **10× determinism verification** (AC-10 enforcement)
4. **Fail-hard on corruption** (no automatic repair)
5. **Log synchronization** (EventLog + SessionLog must stay in sync)

**Critical Guarantees**:
- ✓ Replay produces identical state_hash (determinism)
- ✓ Event log corruption detected (integrity)
- ✓ State reconstruction is authoritative (no snapshot drift)
- ✓ Long campaigns remain safe (append-only logs, atomic writes)

**Components Defined**:
- ✓ Replay-on-load policy (always full replay)
- ✓ Determinism verification (10× replay)
- ✓ SessionLog / EventLog / ReplayHarness relationships
- ✓ Hard failure conditions and enforcement
- ✓ Safety guarantees for long campaigns

**Open Questions**: None (M1 scope is fully defined)

**Blocked By**: None

---

**Document Status**: CANONICAL (M1)
**Next Step**: Implement replay verification in `aidm/core/replay_verification.py` (implementation work order)
