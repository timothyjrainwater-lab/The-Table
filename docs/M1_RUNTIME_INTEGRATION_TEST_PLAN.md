# M1 Runtime Integration Test Plan

**Document ID:** M1-TEST-PLAN-001
**Version:** 1.0
**Date:** 2026-02-10
**Status:** CANONICAL (M1 Implementation)
**Authority:** Binding for M1 Runtime Bootstrap Implementation

---

## 1. PURPOSE

This document defines the **integration test matrix** for M1 runtime bootstrap, establishing:
- Fixture definitions for "tiny campaign" test data
- Complete test matrix covering happy paths and failure modes
- Assertions required for each test scenario
- Test organization and naming conventions
- Coverage requirements for bootstrap implementation

**Design-only**: This is test specification. No code is written in this document.

---

## 2. SCOPE

### 2.1 Components Under Test

This test plan covers:
- Campaign load sequence (`CampaignStore.load_campaign`)
- WorldState reconstruction via replay (`reconstruct_world_state`)
- Session start contract (`RuntimeSession.start_new_session`)
- Session resume contract (`RuntimeSession.resume_from_campaign`)
- Partial write recovery (incomplete turn handling)
- Failure detection (corruption, hash mismatch, gaps)

### 2.2 What This Plan Does NOT Cover

Out of scope:
- Unit tests for individual functions (covered by existing unit test suites)
- Intent lifecycle tests (covered by `test_intent_lifecycle.py`)
- Engine resolution tests (covered by CP-* test suites)
- UI rendering tests (covered by `test_character_sheet_ui.py`)
- LLM integration tests (covered by M1 narration tests)

---

## 3. FIXTURE STRATEGY

### 3.1 Tiny Campaign Fixture

**Definition**: A minimal, fully functional campaign for integration testing.

**Fixture Name**: `tiny_campaign_fixture`

**Contents**:
```python
@pytest.fixture
def tiny_campaign_fixture(tmp_path):
    """Create a minimal campaign for integration testing.

    Returns:
        dict with:
            - campaign_dir: Path to campaign directory
            - manifest: CampaignManifest
            - start_state: Initial WorldState
            - master_seed: int
    """
    campaign_id = str(uuid.uuid4())
    master_seed = 12345

    # Minimal Session Zero config
    session_zero = SessionZeroConfig(
        ruleset_id="RAW_3.5",
        alignment_mode="inferred",
        preparation_depth="minimal",
        voice_enabled=False,
    )

    # Minimal start state (one PC, one enemy)
    start_state = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                "name": "Roderick",
                "hp": 30,
                "max_hp": 30,
                "team": "party",
                "ac": 16,
                "init_bonus": 1,
            },
            "goblin_1": {
                "name": "Goblin Scout",
                "hp": 6,
                "max_hp": 6,
                "team": "monsters",
                "ac": 15,
                "init_bonus": 1,
            },
        },
        active_combat=None,  # Combat not started yet
    )

    # Create campaign via CampaignStore
    store = CampaignStore(tmp_path)
    manifest = store.create_campaign(
        campaign_id=campaign_id,
        session_zero=session_zero,
        title="Tiny Test Campaign",
        created_at=datetime(2025, 1, 1, 12, 0, 0).isoformat(),
        seed=master_seed,
    )

    # Write start_state.json
    start_state_path = tmp_path / campaign_id / "start_state.json"
    with open(start_state_path, "w") as f:
        json.dump(start_state.to_dict(), f, indent=2, sort_keys=True)

    return {
        "campaign_dir": tmp_path / campaign_id,
        "manifest": manifest,
        "start_state": start_state,
        "master_seed": master_seed,
    }
```

### 3.2 Event Log Builder Fixture

**Definition**: Helper to build event logs for testing.

**Fixture Name**: `event_log_builder`

**Contents**:
```python
@pytest.fixture
def event_log_builder():
    """Factory for creating test event logs.

    Usage:
        builder = event_log_builder()
        builder.add_attack_roll("pc_fighter", "goblin_1", natural=15, total=20)
        builder.add_damage("goblin_1", old_hp=6, new_hp=1)
        builder.add_turn_end("pc_fighter")
        event_log = builder.build()
    """
    class EventLogBuilder:
        def __init__(self):
            self.events = []
            self.next_event_id = 0

        def add_attack_roll(self, attacker_id, target_id, natural, total):
            self.events.append(Event(
                event_id=self.next_event_id,
                event_type="attack_roll",
                timestamp=self.next_event_id * 1.0,
                payload={
                    "attacker": attacker_id,
                    "target": target_id,
                    "natural": natural,
                    "total": total,
                    "hit": total >= 15,  # Assume AC 15
                }
            ))
            self.next_event_id += 1

        def add_damage(self, entity_id, old_hp, new_hp):
            self.events.append(Event(
                event_id=self.next_event_id,
                event_type="hp_changed",
                timestamp=self.next_event_id * 1.0,
                payload={
                    "entity_id": entity_id,
                    "old_hp": old_hp,
                    "new_hp": new_hp,
                    "delta": new_hp - old_hp,
                }
            ))
            self.next_event_id += 1

        def add_turn_end(self, actor_id):
            self.events.append(Event(
                event_id=self.next_event_id,
                event_type="turn_end",
                timestamp=self.next_event_id * 1.0,
                payload={"actor": actor_id}
            ))
            self.next_event_id += 1

        def build(self) -> EventLog:
            log = EventLog()
            for event in self.events:
                log.append(event)
            return log

    return EventLogBuilder
```

### 3.3 Minimal Session Log Fixture

**Definition**: Helper to create session logs with intents.

**Fixture Name**: `session_log_builder`

**Contents**:
```python
@pytest.fixture
def session_log_builder():
    """Factory for creating test session logs.

    Usage:
        builder = session_log_builder(master_seed=12345)
        builder.add_resolved_intent("attack_001", "pc_fighter", ActionType.ATTACK)
        session_log = builder.build()
    """
    class SessionLogBuilder:
        def __init__(self, master_seed=0, initial_state_hash=""):
            self.log = SessionLog(
                master_seed=master_seed,
                initial_state_hash=initial_state_hash
            )

        def add_resolved_intent(self, intent_id, actor_id, action_type):
            intent = IntentObject(
                intent_id=intent_id,
                actor_id=actor_id,
                action_type=action_type,
                status=IntentStatus.PENDING,
                source_text="test action",
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                updated_at=datetime(2025, 1, 1, 12, 0, 0),
            )
            intent.transition_to(IntentStatus.CONFIRMED, timestamp=datetime(2025, 1, 1, 12, 0, 1))
            intent.transition_to(IntentStatus.RESOLVED, timestamp=datetime(2025, 1, 1, 12, 0, 2))

            result = EngineResultBuilder(intent_id=intent_id).build(
                result_id=str(uuid.uuid4()),
                resolved_at=datetime(2025, 1, 1, 12, 0, 2)
            )

            self.log.append(intent, result)

        def build(self) -> SessionLog:
            return self.log

    return SessionLogBuilder
```

---

## 4. INTEGRATION TEST MATRIX

### 4.1 Happy Path: New Session Start

**Test Name**: `test_bootstrap_new_session_start`

**Scenario**: Load a new campaign with no events, start session.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Ensure `events.jsonl` is empty
3. Ensure `intents.jsonl` is empty

**Execution**:
```python
session = RuntimeSession.start_new_session(manifest)
```

**Assertions**:
- [ ] `session.world_state` matches `start_state` (deep equality)
- [ ] `session.world_state.state_hash()` equals expected initial hash
- [ ] `session.rng` is initialized with `master_seed=12345`
- [ ] `session.session_log` is empty (`len(session_log) == 0`)
- [ ] `session.campaign_id` equals `manifest.campaign_id`
- [ ] No exceptions raised

**Coverage**: Section 5 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Session Start Contract)

---

### 4.2 Happy Path: Resume from Campaign with Events

**Test Name**: `test_bootstrap_resume_from_campaign_with_events`

**Scenario**: Resume a campaign that has 3 completed turns.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Use `event_log_builder` to create 3 turns:
   - Turn 1: pc_fighter attacks goblin_1 (hit, damage)
   - Turn 2: goblin_1 attacks pc_fighter (miss)
   - Turn 3: pc_fighter attacks goblin_1 (hit, damage, goblin dies)
3. Write events to `events.jsonl`
4. Use `session_log_builder` to create 3 resolved intents
5. Write intents to `intents.jsonl`
6. Compute expected final state hash

**Execution**:
```python
session = RuntimeSession.resume_from_campaign(manifest)
```

**Assertions**:
- [ ] `session.world_state.state_hash()` equals expected final hash
- [ ] `session.world_state.entities["goblin_1"]["hp"]` equals expected HP after 3 turns
- [ ] `len(session.session_log)` equals 3
- [ ] `session.session_log.master_seed` equals 12345
- [ ] Replay verification passes (10× replay produces identical hash)
- [ ] No exceptions raised

**Coverage**: Section 6.1 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Resume Mid-Campaign)

---

### 4.3 Determinism: 10× Replay Verification

**Test Name**: `test_bootstrap_10x_replay_determinism`

**Scenario**: Verify that resuming the same campaign 10 times produces identical state hash.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Create event log with 5 turns (varied events: attacks, saves, damage, conditions)
3. Write events to `events.jsonl`
4. Compute expected hash from first replay

**Execution**:
```python
hashes = []
for i in range(10):
    session = RuntimeSession.resume_from_campaign(manifest)
    hashes.append(session.world_state.state_hash())
```

**Assertions**:
- [ ] `len(set(hashes)) == 1` (all hashes identical)
- [ ] All hashes equal expected hash from first replay
- [ ] No exceptions raised in any replay

**Coverage**: Section 4.1 of M1_RUNTIME_REPLAY_POLICY.md (10× Replay Requirement, AC-10)

---

### 4.4 Failure: Corrupt Event Log (JSON Parse Error)

**Test Name**: `test_bootstrap_detects_corrupt_event_log_json`

**Scenario**: Attempt to resume a campaign with corrupted `events.jsonl` (invalid JSON).

**Setup**:
1. Use `tiny_campaign_fixture`
2. Write invalid JSON to `events.jsonl`:
   ```
   {"event_id": 0, "event_type": "attack_roll", ...}
   {"event_id": 1, CORRUPT LINE - missing quotes
   {"event_id": 2, "event_type": "hp_changed", ...}
   ```

**Execution**:
```python
with pytest.raises(EventLogCorruptionError) as exc_info:
    session = RuntimeSession.resume_from_campaign(manifest)
```

**Assertions**:
- [ ] `EventLogCorruptionError` is raised
- [ ] Error message contains "corrupted" or "parse error"
- [ ] Error message contains line number (line 2)
- [ ] Session is NOT created (fail-fast)

**Coverage**: Section 7.1 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Corrupt Event Log)

---

### 4.5 Failure: Event ID Gap

**Test Name**: `test_bootstrap_detects_event_id_gap`

**Scenario**: Attempt to resume a campaign with missing event IDs.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Use `event_log_builder` to create events with IDs: 0, 1, 2, 4, 5 (missing 3)
3. Write events to `events.jsonl`

**Execution**:
```python
with pytest.raises(EventLogCorruptionError) as exc_info:
    session = RuntimeSession.resume_from_campaign(manifest)
```

**Assertions**:
- [ ] `EventLogCorruptionError` is raised
- [ ] Error message contains "gap detected" or "missing event_id"
- [ ] Error message specifies expected ID (3) and found ID (4)
- [ ] Session is NOT created

**Coverage**: Section 3.3 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Load Event Log validation)

---

### 4.6 Failure: State Hash Mismatch

**Test Name**: `test_bootstrap_detects_state_hash_mismatch`

**Scenario**: Attempt to resume a campaign where replay produces different hash than expected.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Create event log with 2 turns
3. Write events to `events.jsonl`
4. Create session log with `initial_state_hash` = correct hash
5. Manually inject wrong expected final hash in test harness
6. Write session log to `intents.jsonl`

**Execution**:
```python
with pytest.raises(StateReconstructionError) as exc_info:
    session = RuntimeSession.resume_from_campaign(
        manifest,
        expected_final_hash="wrong_hash_abc123..."
    )
```

**Assertions**:
- [ ] `StateReconstructionError` is raised
- [ ] Error message contains "hash mismatch"
- [ ] Error message includes expected hash and actual hash
- [ ] Session is NOT created

**Coverage**: Section 7.4 of M1_RUNTIME_SESSION_BOOTSTRAP.md (State Hash Mismatch)

---

### 4.7 Recovery: Partial Write (Truncate After Last Turn End)

**Test Name**: `test_bootstrap_recovers_from_partial_write`

**Scenario**: Resume a campaign where last turn was incomplete (crash during turn execution).

**Setup**:
1. Use `tiny_campaign_fixture`
2. Create event log:
   - Turn 1: complete (attack_roll, hp_changed, turn_end)
   - Turn 2: complete (attack_roll, hp_changed, turn_end)
   - Turn 3: **incomplete** (attack_roll, hp_changed, **NO turn_end**)
3. Write events to `events.jsonl`
4. Create session log with 3 intents (last intent has no result)
5. Write session log to `intents.jsonl`

**Execution**:
```python
session = RuntimeSession.resume_from_campaign(manifest)
```

**Assertions**:
- [ ] Session resumes successfully
- [ ] WorldState reflects state after Turn 2 (last complete turn)
- [ ] Turn 3 events are **discarded** (incomplete turn ignored)
- [ ] Session log contains 2 entries (Turn 3 intent discarded)
- [ ] Warning logged: "Last turn incomplete, resuming from turn 2"
- [ ] User can re-execute Turn 3 action (state is consistent)

**Coverage**: Section 6.2 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Handling Partially Written Session Logs)

---

### 4.8 Failure: Version Mismatch (Incompatible Engine)

**Test Name**: `test_bootstrap_rejects_incompatible_engine_version`

**Scenario**: Attempt to load a campaign created with a future engine version.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Modify `manifest.json` to set `engine_version = "0.2.0"`
3. Current runtime: `0.1.0`

**Execution**:
```python
with pytest.raises(CampaignStoreError) as exc_info:
    manifest = CampaignStore.load_campaign(campaign_id)
```

**Assertions**:
- [ ] `CampaignStoreError` is raised
- [ ] Error message contains "incompatible engine version"
- [ ] Error message specifies required version (0.2.0) and current (0.1.0)
- [ ] Campaign is NOT loaded

**Coverage**: Section 7.2 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Version Mismatch)

---

### 4.9 Boundary: Empty Campaign (No Events, No Intents)

**Test Name**: `test_bootstrap_empty_campaign_is_valid`

**Scenario**: Resume a newly created campaign that has never had a turn executed.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Ensure `events.jsonl` contains only metadata (no events)
3. Ensure `intents.jsonl` contains only metadata (no intents)

**Execution**:
```python
session = RuntimeSession.resume_from_campaign(manifest)
```

**Assertions**:
- [ ] Session resumes successfully
- [ ] `session.world_state` matches `start_state` (no replay needed)
- [ ] `len(session.session_log)` equals 0
- [ ] `session.world_state.state_hash()` equals initial state hash
- [ ] No exceptions raised

**Coverage**: Section 3.3 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Empty Log is valid)

---

### 4.10 Integration: Full Resume → Execute Turn → Save → Resume Again

**Test Name**: `test_bootstrap_full_resume_execute_save_resume_cycle`

**Scenario**: Full integration test of resume → play → save → resume cycle.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Create event log with 2 turns
3. Write events and intents to disk

**Execution**:
```python
# First resume
session1 = RuntimeSession.resume_from_campaign(manifest)
initial_hash = session1.world_state.state_hash()

# Execute one more turn
intent = session1.create_intent(
    actor_id="pc_fighter",
    source_text="I attack",
    action_type=ActionType.ATTACK,
    intent_id="attack_003",
    timestamp=datetime(2025, 1, 1, 12, 0, 0),
    target_id="goblin_1",
    method="longsword",
)
session1.confirm_intent(intent, timestamp=datetime(2025, 1, 1, 12, 0, 1))
result, narration = session1.resolve(intent, timestamp=datetime(2025, 1, 1, 12, 0, 2))

# Save session
session1.save_to_disk(manifest.paths)

# Second resume
session2 = RuntimeSession.resume_from_campaign(manifest)
final_hash = session2.world_state.state_hash()
```

**Assertions**:
- [ ] `session2.world_state.state_hash()` equals `final_hash` from session1 after turn 3
- [ ] `len(session2.session_log)` equals 3 (2 original + 1 new)
- [ ] Session2 replay produces same state as session1 after turn 3
- [ ] No exceptions raised
- [ ] Events persisted correctly (`events.jsonl` has 3 complete turns)
- [ ] Intents persisted correctly (`intents.jsonl` has 3 resolved intents)

**Coverage**: Full end-to-end integration of M1 bootstrap + execution + persistence

---

### 4.11 Failure: Missing start_state.json

**Test Name**: `test_bootstrap_fails_if_start_state_missing`

**Scenario**: Attempt to load a campaign with missing `start_state.json`.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Delete `start_state.json` file

**Execution**:
```python
with pytest.raises(CampaignStoreError) as exc_info:
    session = RuntimeSession.resume_from_campaign(manifest)
```

**Assertions**:
- [ ] `CampaignStoreError` is raised
- [ ] Error message contains "start_state.json not found" or "missing initial state"
- [ ] Session is NOT created

**Coverage**: Section 3.4 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Schema and Version Checks)

---

### 4.12 Boundary: Campaign with 100+ Events (Performance Check)

**Test Name**: `test_bootstrap_handles_large_event_log_within_budget`

**Scenario**: Resume a campaign with 100+ events, verify replay completes within time budget.

**Setup**:
1. Use `tiny_campaign_fixture`
2. Use `event_log_builder` to create 100 turns (300+ events)
3. Write events to `events.jsonl`

**Execution**:
```python
import time
start = time.time()
session = RuntimeSession.resume_from_campaign(manifest)
duration_ms = (time.time() - start) * 1000
```

**Assertions**:
- [ ] Session resumes successfully
- [ ] Replay duration < 5000ms (5 seconds, per Section 7.1 of REPLAY_POLICY)
- [ ] `session.world_state.state_hash()` is consistent across 3 replays
- [ ] No performance degradation (linear time complexity)

**Coverage**: Section 7.1 of M1_RUNTIME_REPLAY_POLICY.md (M1 Constraints, performance)

---

### 4.13 Failure: Corrupt intents.jsonl (Incomplete Intent)

**Test Name**: `test_bootstrap_handles_corrupt_intents_log_gracefully`

**Scenario**: Resume a campaign where `intents.jsonl` has an intent with no result (incomplete).

**Setup**:
1. Use `tiny_campaign_fixture`
2. Create event log with 2 complete turns
3. Create session log with 2 intents + 1 incomplete intent (no result)
4. Write logs to disk

**Execution**:
```python
session = RuntimeSession.resume_from_campaign(manifest)
```

**Assertions**:
- [ ] Session resumes successfully (partial write recovery)
- [ ] Incomplete intent is **ignored** (not loaded into session log)
- [ ] `len(session.session_log)` equals 2 (only complete intents)
- [ ] Warning logged: "Discarded incomplete intent"
- [ ] WorldState reflects state after 2 complete turns

**Coverage**: Section 6.2 of M1_RUNTIME_SESSION_BOOTSTRAP.md (Handling Partially Written Session Logs)

---

## 5. TEST ORGANIZATION

### 5.1 Test File Structure

**File**: `tests/test_m1_runtime_bootstrap_integration.py`

**Sections**:
```python
"""M1 Runtime Bootstrap Integration Tests.

Tests the full bootstrap contract from M1_RUNTIME_SESSION_BOOTSTRAP.md
and M1_RUNTIME_REPLAY_POLICY.md.

Test Groups:
- Happy Path: New session start, resume with events
- Determinism: 10× replay verification
- Failure Detection: Corrupt logs, missing files, version mismatch
- Recovery: Partial write recovery, incomplete intents
- Integration: Full resume → execute → save → resume cycle
"""

# =============================================================================
# Fixtures (Section 3)
# =============================================================================

@pytest.fixture
def tiny_campaign_fixture(tmp_path): ...

@pytest.fixture
def event_log_builder(): ...

@pytest.fixture
def session_log_builder(): ...

# =============================================================================
# Happy Path Tests (4.1, 4.2)
# =============================================================================

class TestBootstrapHappyPath:
    def test_bootstrap_new_session_start(self, tiny_campaign_fixture): ...
    def test_bootstrap_resume_from_campaign_with_events(self, tiny_campaign_fixture): ...

# =============================================================================
# Determinism Tests (4.3)
# =============================================================================

class TestBootstrapDeterminism:
    def test_bootstrap_10x_replay_determinism(self, tiny_campaign_fixture): ...

# =============================================================================
# Failure Detection Tests (4.4-4.6, 4.8, 4.11)
# =============================================================================

class TestBootstrapFailureDetection:
    def test_bootstrap_detects_corrupt_event_log_json(self, tiny_campaign_fixture): ...
    def test_bootstrap_detects_event_id_gap(self, tiny_campaign_fixture): ...
    def test_bootstrap_detects_state_hash_mismatch(self, tiny_campaign_fixture): ...
    def test_bootstrap_rejects_incompatible_engine_version(self, tiny_campaign_fixture): ...
    def test_bootstrap_fails_if_start_state_missing(self, tiny_campaign_fixture): ...

# =============================================================================
# Recovery Tests (4.7, 4.13)
# =============================================================================

class TestBootstrapRecovery:
    def test_bootstrap_recovers_from_partial_write(self, tiny_campaign_fixture): ...
    def test_bootstrap_handles_corrupt_intents_log_gracefully(self, tiny_campaign_fixture): ...

# =============================================================================
# Boundary Tests (4.9, 4.12)
# =============================================================================

class TestBootstrapBoundaryConditions:
    def test_bootstrap_empty_campaign_is_valid(self, tiny_campaign_fixture): ...
    def test_bootstrap_handles_large_event_log_within_budget(self, tiny_campaign_fixture): ...

# =============================================================================
# Integration Tests (4.10)
# =============================================================================

class TestBootstrapFullIntegration:
    def test_bootstrap_full_resume_execute_save_resume_cycle(self, tiny_campaign_fixture): ...
```

### 5.2 Test Naming Convention

**Pattern**: `test_bootstrap_{action}_{condition}`

**Examples**:
- `test_bootstrap_new_session_start` (action: new session, condition: start)
- `test_bootstrap_resume_from_campaign_with_events` (action: resume, condition: with events)
- `test_bootstrap_detects_corrupt_event_log_json` (action: detects, condition: corrupt log)
- `test_bootstrap_recovers_from_partial_write` (action: recovers, condition: partial write)

---

## 6. COVERAGE REQUIREMENTS

### 6.1 Code Paths Covered

**Must Cover**:
- ✓ `CampaignStore.load_campaign()` → manifest validation
- ✓ `load_start_state()` → WorldState deserialization
- ✓ `EventLog.from_jsonl()` → event log parsing + validation
- ✓ `SessionLog.from_jsonl()` → session log parsing
- ✓ `reconstruct_world_state()` → full replay from start_state
- ✓ `RuntimeSession.start_new_session()` → new session bootstrap
- ✓ `RuntimeSession.resume_from_campaign()` → resume with replay
- ✓ `verify_10x_replay()` → determinism verification
- ✓ Partial write recovery logic → discard incomplete turns
- ✓ Corruption detection → event ID gaps, JSON parse errors
- ✓ Hash mismatch detection → state reconstruction error

### 6.2 Acceptance Criteria Mapping

| Test | Acceptance Criteria | Reference |
|------|---------------------|-----------|
| 4.1 | New session starts with correct state | M1-BOOT Section 5.1 |
| 4.2 | Resume reconstructs state via replay | M1-BOOT Section 6.1 |
| 4.3 | 10× replay produces identical hash | AC-10, REPLAY Section 4.1 |
| 4.4 | Corrupt JSON detected and failed | M1-BOOT Section 7.1 |
| 4.5 | Event ID gaps detected | M1-BOOT Section 3.3 |
| 4.6 | Hash mismatch detected | M1-BOOT Section 7.4 |
| 4.7 | Partial write recovery works | M1-BOOT Section 6.2 |
| 4.8 | Version mismatch rejected | M1-BOOT Section 7.2 |
| 4.9 | Empty campaign is valid | M1-BOOT Section 3.3 |
| 4.10 | Full cycle works end-to-end | M1 integration |
| 4.11 | Missing start_state fails | M1-BOOT Section 3.4 |
| 4.12 | Large campaigns within budget | REPLAY Section 7.1 |
| 4.13 | Incomplete intents recovered | M1-BOOT Section 6.2 |

### 6.3 Minimum Pass Criteria

**All tests must pass** for M1 runtime bootstrap to be considered complete:
- 13 integration tests (4.1-4.13)
- 100% pass rate required
- No flaky tests (determinism enforcement)
- Runtime budget: All tests complete in <30 seconds total

---

## 7. IMPLEMENTATION NOTES

### 7.1 Test Execution Order

**Recommended Order**:
1. Happy path tests (4.1, 4.2) — establish baseline
2. Boundary tests (4.9, 4.12) — edge cases
3. Failure detection tests (4.4-4.6, 4.8, 4.11) — negative cases
4. Recovery tests (4.7, 4.13) — graceful degradation
5. Determinism tests (4.3) — core guarantee
6. Full integration test (4.10) — end-to-end verification

### 7.2 Fixture Reuse

**Fixtures are composable**:
- `tiny_campaign_fixture` provides base campaign
- `event_log_builder` adds events as needed
- `session_log_builder` adds intents as needed
- Tests modify fixture data per scenario (corruption, gaps, etc.)

### 7.3 Assertion Libraries

**Use existing patterns**:
- `pytest.raises()` for expected exceptions
- `assert` statements for positive assertions
- Deep equality checks for WorldState comparison
- Hash comparison for determinism verification

### 7.4 Test Data Management

**Test data is ephemeral**:
- All tests use `tmp_path` fixture (pytest built-in)
- Campaign directories created per test (isolated)
- No persistent test data (clean slate per run)
- No test database (filesystem only)

---

## 8. EXPLICIT NON-GOALS

### 8.1 What This Test Plan Does NOT Require

**NOT Required**:
- ❌ Unit tests for `reduce_event()` (covered by existing unit tests)
- ❌ UI rendering tests (out of scope for bootstrap)
- ❌ LLM narration tests (separate test suite)
- ❌ Intent extraction tests (covered by intent lifecycle tests)
- ❌ Engine resolution tests (covered by CP-* test suites)
- ❌ Asset generation tests (M3 scope)
- ❌ Snapshot optimization tests (M2+ scope, not in M1)

### 8.2 Deferred to Future Milestones

**M2+ Tests**:
- Snapshot + delta replay (M2 optimization)
- Multi-session campaign tests (M2 persistence)
- Asset regeneration tests (M2 asset store)
- Prep job orchestration tests (M2 prep pipeline)

**M3+ Tests**:
- Voice I/O integration (M3 immersion layer)
- Image generation tests (M3 immersion layer)
- Audio transitions tests (M3 immersion layer)

---

## 9. SUMMARY

**READY FOR IMPLEMENTATION**: Yes

**Test Matrix**:
- 13 integration tests defined
- 3 fixtures provided (tiny_campaign, event_log_builder, session_log_builder)
- Happy path + failure detection + recovery + determinism coverage
- Full end-to-end integration test included

**Coverage**:
- ✓ New session start (4.1)
- ✓ Resume with events (4.2)
- ✓ 10× replay determinism (4.3, AC-10)
- ✓ Corruption detection (4.4, 4.5, 4.6)
- ✓ Partial write recovery (4.7)
- ✓ Version mismatch (4.8)
- ✓ Empty campaign (4.9)
- ✓ Full cycle integration (4.10)
- ✓ Missing files (4.11)
- ✓ Large campaigns (4.12)
- ✓ Incomplete intents (4.13)

**Acceptance Criteria Met**:
- ✓ AC-10: 10× replay produces identical hash (Test 4.3)
- ✓ Replay-first reconstruction (Tests 4.2, 4.10)
- ✓ Fail-fast on corruption (Tests 4.4, 4.5, 4.6)
- ✓ Partial write recovery (Tests 4.7, 4.13)
- ✓ Version compatibility (Test 4.8)

**Open Questions**: None

**Blocked By**: None

---

**Document Status**: CANONICAL (M1 Implementation)
**Next Step**: Implement integration tests in `tests/test_m1_runtime_bootstrap_integration.py` (implementation work order)
