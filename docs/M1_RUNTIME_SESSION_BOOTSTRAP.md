# M1 Runtime Session Bootstrap Contract

**Document ID:** M1-BOOT-001
**Version:** 1.0
**Date:** 2026-02-10
**Status:** CANONICAL (M1)
**Authority:** Binding for M1 Solo Vertical Slice

---

## 1. PURPOSE

This document defines the **runtime session bootstrap contract** for M1, establishing:
- Campaign load sequence from persisted state
- WorldState reconstruction rules
- Session start contract for initial play
- Session resume contract for continued play
- Failure modes and error handling
- Explicit boundaries (what the runtime MUST NOT do)

**Design-only**: This is architectural specification. No code changes are proposed.

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 Component Relationships

```
┌────────────────────────────────────────────────────────────┐
│                     M1 RUNTIME FLOW                        │
└────────────────────────────────────────────────────────────┘

Campaign Load:
    CampaignStore.load_campaign(campaign_id)
        → CampaignManifest
        → Load start_state.json
        → Load events.jsonl (EventLog)
        → Validate schema/version
        → Hash verification

Session Bootstrap (NEW or RESUME):
    IF new session:
        → Construct WorldState from start_state.json
        → Initialize RNGManager(master_seed)
        → Create empty SessionLog
        → Engine entry: play_loop.execute_turn()

    IF resume session:
        → Replay events.jsonl → reconstruct WorldState
        → Initialize RNGManager(master_seed)
        → Load SessionLog from intents.jsonl
        → Verify state hash matches
        → Engine entry: play_loop.execute_turn()

Session Execution:
    play_loop.execute_turn(world_state, turn_ctx, intent, rng)
        → Emit events to EventLog
        → Apply events to WorldState
        → Return TurnResult
        → Log intent + result to SessionLog
        → Persist events.jsonl, intents.jsonl

Session End:
    → Write final events.jsonl
    → Write final intents.jsonl
    → (Optional) Write start_state_snapshot.json for resume
```

### 2.2 Data Flow Authority

| Data | Owner | Source | Authoritative |
|------|-------|--------|---------------|
| `CampaignManifest` | CampaignStore | manifest.json | Yes |
| `WorldState` (initial) | Engine (reducer) | start_state.json or replay | Yes |
| `EventLog` | Engine (resolver) | events.jsonl | Yes (append-only) |
| `SessionLog` | RuntimeSession | intents.jsonl | Yes (replay uses this) |
| `RNGManager` | Engine | master_seed | Yes |

**Critical Rule**: WorldState is NEVER persisted directly (violates BL-020). Only start_state.json (initial) or replay from events.jsonl.

---

## 3. CAMPAIGN LOAD SEQUENCE

### 3.1 Load Campaign Manifest

**Entry Point**: `CampaignStore.load_campaign(campaign_id)`

**Steps**:
1. Locate campaign directory: `{root_dir}/{campaign_id}/`
2. Read `manifest.json`
3. Parse JSON → `CampaignManifest`
4. Validate manifest:
   - `campaign_id` matches directory name
   - `engine_version` is compatible (M1: `0.1.0`)
   - `config_schema_version` is supported (`1.0`)
   - `session_zero` config is valid
   - `paths` point to expected files

**Success**: Returns `CampaignManifest`
**Failure**: Raises `CampaignStoreError`

### 3.2 Load Initial WorldState

**Source**: `start_state.json`

**Steps**:
1. Read `{campaign_dir}/start_state.json`
2. Parse JSON → WorldState.from_dict()
3. Validate state:
   - `ruleset_version` matches manifest `session_zero.ruleset_id`
   - Required fields present (`entities`, `active_combat` if combat state)
4. Compute state hash: `initial_state_hash = state.state_hash()`
5. Store hash in SessionLog for replay verification

**Success**: Returns `WorldState`
**Failure**: Raises error if file missing, corrupt, or schema mismatch

**Critical Note**: `start_state.json` is ONLY used for campaign creation. Resume uses replay.

### 3.3 Load Event Log

**Source**: `events.jsonl`

**Steps**:
1. Read `{campaign_dir}/events.jsonl`
2. Parse JSONL → `EventLog.from_jsonl()`
3. Validate log:
   - Event IDs are monotonically increasing (BL-008)
   - No missing IDs in sequence
   - All events have valid `event_type`, `timestamp`, `payload`
4. Count events: `event_count = len(event_log)`

**Success**: Returns `EventLog`
**Failure**: Raises error if corrupt, ID gaps, or ordering violation

**Empty Log**: Valid for new campaigns (no events yet)

### 3.4 Schema and Version Checks

**Checks**:
- `manifest.engine_version` compatible with current runtime (`0.1.0` for M1)
- `manifest.config_schema_version` supported (`1.0`)
- `session_zero.ruleset_id` matches expected ruleset (`RAW_3.5`)
- All required files exist:
  - `manifest.json` ✓
  - `events.jsonl` ✓ (may be empty)
  - `intents.jsonl` ✓ (may be empty)
  - `start_state.json` ✓

**Failure Modes**: See Section 7.

---

## 4. WORLDSTATE RECONSTRUCTION RULES

### 4.1 Replay vs Snapshot Policy

**Rule 1: Replay-First for All Sessions**

For M1, WorldState is ALWAYS reconstructed via replay:
- New session: `start_state.json` → apply `events.jsonl` (empty = no replay needed)
- Resume session: `start_state.json` → apply `events.jsonl` (full replay)

**Snapshots are NOT used for state reconstruction** (M1 constraint).

**Rationale**:
- Guarantees state correctness (no snapshot corruption)
- Enforces reducer-only mutation path (BL-012)
- Enables replay verification (AC-10)

**M2+ Optimization** (out of scope for M1):
- Snapshot + delta replay for long campaigns
- Periodic state checkpoints
- Incremental replay from last checkpoint

### 4.2 Replay Ordering Guarantees

**Replay Execution**:
```python
def reconstruct_world_state(
    start_state: WorldState,
    event_log: EventLog,
    master_seed: int
) -> WorldState:
    \"\"\"Reconstruct WorldState by replaying events.\"\"\"
    rng = RNGManager(master_seed)
    current_state = deepcopy(start_state)

    for event in event_log.events:
        current_state = reduce_event(current_state, event, rng)

    return current_state
```

**Guarantees**:
- Events applied in strict `event_id` order (BL-008)
- RNG stream initialized with `master_seed` (deterministic)
- Reducer-only path (no resolver re-execution)
- Deep copy prevents mutation of input state

### 4.3 State Hash Verification

**After replay**:
```python
reconstructed_state = reconstruct_world_state(start_state, event_log, master_seed)
final_hash = reconstructed_state.state_hash()

# Verify hash matches expected (if available from SessionLog)
if expected_hash and final_hash != expected_hash:
    raise StateReconstructionError(
        f\"State hash mismatch: expected {expected_hash}, got {final_hash}\"
    )
```

**Hash Sources**:
- `SessionLog.initial_state_hash`: Hash of start_state.json (for verification)
- Computed hash after replay: Verifies replay correctness

**Failure**: State diverged (events corrupted, schema mismatch, or nondeterministic reducer)

---

## 5. SESSION START CONTRACT

### 5.1 Inputs Required to Begin Session 1

**Preconditions**:
1. Campaign loaded: `CampaignManifest` available
2. Initial state loaded: `start_state.json` → `WorldState`
3. Empty event log: `events.jsonl` exists but empty
4. Master seed: `manifest.master_seed` (integer)

**Bootstrap Sequence**:
```python
def start_new_session(manifest: CampaignManifest) -> RuntimeSession:
    # 1. Load initial state
    start_state = load_start_state(manifest.paths.root / \"start_state.json\")

    # 2. Initialize RNG
    rng = RNGManager(manifest.master_seed)

    # 3. Create empty session log
    session_log = SessionLog(
        master_seed=manifest.master_seed,
        initial_state_hash=start_state.state_hash()
    )

    # 4. Create runtime session
    session = RuntimeSession(
        world_state=start_state,
        rng=rng,
        session_log=session_log,
        campaign_id=manifest.campaign_id
    )

    return session
```

### 5.2 Engine Entry Point

**Entry**: `play_loop.execute_turn()`

**Signature**:
```python
def execute_turn(
    world_state: WorldState,
    turn_ctx: TurnContext,  # (turn_index, actor_id, actor_team)
    doctrine: Optional[MonsterDoctrine] = None,
    combat_intent: Optional[Union[AttackIntent, FullAttackIntent]] = None,
    rng: Optional[RNGManager] = None,
    next_event_id: int = 0,
    timestamp: float = 0.0
) -> TurnResult
```

**Returns**: `TurnResult` with:
- `status`: \"ok\" | \"invalid_intent\" | \"requires_clarification\"
- `world_state`: Updated WorldState
- `events`: List[Event] emitted during turn
- `narration`: Optional narration token

**Post-Turn Actions**:
1. Append events to `EventLog`
2. Write events to `events.jsonl` (append-only)
3. Log intent + result to `SessionLog`
4. Write intent + result to `intents.jsonl` (append-only)

---

## 6. SESSION RESUME CONTRACT

### 6.1 Resume Mid-Campaign

**Scenario**: Campaign exists, has events, player wants to continue

**Resume Sequence**:
```python
def resume_existing_session(manifest: CampaignManifest) -> RuntimeSession:
    # 1. Load initial state
    start_state = load_start_state(manifest.paths.root / \"start_state.json\")

    # 2. Load and replay events
    event_log = EventLog.from_jsonl(manifest.paths.root / \"events.jsonl\")
    world_state = reconstruct_world_state(start_state, event_log, manifest.master_seed)

    # 3. Verify state hash
    expected_hash = compute_expected_hash()  # From SessionLog or stored
    actual_hash = world_state.state_hash()
    if expected_hash and actual_hash != expected_hash:
        raise StateReconstructionError(\"State hash mismatch after replay\")

    # 4. Initialize RNG
    rng = RNGManager(manifest.master_seed)

    # 5. Load session log
    session_log = SessionLog.from_jsonl(manifest.paths.root / \"intents.jsonl\")

    # 6. Create runtime session
    session = RuntimeSession(
        world_state=world_state,
        rng=rng,
        session_log=session_log,
        campaign_id=manifest.campaign_id
    )

    return session
```

### 6.2 Handling Partially Written Session Logs

**Problem**: Power loss, crash, or Ctrl+C during turn execution → incomplete writes

**Detection**:
- `intents.jsonl` has more entries than `events.jsonl` has turn_end events
- Last event in `events.jsonl` is not `turn_end`

**Recovery Policy**:
1. **Replay up to last complete turn**:
   - Find last `turn_end` event in `events.jsonl`
   - Discard events after last `turn_end`
   - Replay up to (and including) last `turn_end`

2. **Discard incomplete intent**:
   - If `intents.jsonl` has intent with no corresponding result → discard
   - Resume expects complete intent-result pairs only

3. **Log corruption warning**:
   - Inform user: \"Last turn incomplete, resuming from turn N\"
   - Recommend: \"Re-execute last action\" (user must re-submit intent)

**Example**:
```
events.jsonl:
    event_id=0: turn_start
    event_id=1: attack_roll
    event_id=2: hp_changed
    # MISSING: turn_end (crash occurred here)

intents.jsonl:
    intent_id=abc123, status=RESOLVED
    # Incomplete: has intent but no result

Recovery:
    Discard events 0-2
    Discard intent abc123
    Resume from start_state.json
    Replay up to last complete turn (none in this case)
```

---

## 7. FAILURE MODES

### 7.1 Corrupt Event Log

**Detection**:
- JSON parse error in `events.jsonl`
- Missing required fields (`event_id`, `event_type`, `payload`)
- Event ID gaps or out-of-order IDs (violates BL-008)

**Response**:
- **FAIL**: Raise `EventLogCorruptionError`
- **DO NOT** attempt repair (data integrity violation)
- **User Action Required**: Restore from backup or archive

**Log Message**:
```
ERROR: Event log corrupted at line 47
  Expected event_id=47, found event_id=49 (gap detected)
  Campaign cannot be loaded. Restore from backup or contact support.
```

### 7.2 Version Mismatch

**Detection**:
- `manifest.engine_version` is incompatible (e.g., `0.2.0` when runtime is `0.1.0`)
- `manifest.config_schema_version` is unsupported (e.g., `2.0` when runtime supports `1.0`)

**Response**:
- **WARN** if minor version mismatch (`0.1.0` vs `0.1.1`) → allow load with warning
- **FAIL** if major version mismatch (`0.1.0` vs `0.2.0`) → refuse load

**Log Message**:
```
ERROR: Campaign requires engine version 0.2.0
  Current runtime: 0.1.0
  Campaign cannot be loaded. Upgrade engine or use compatible version.
```

### 7.3 Missing Assets

**Detection**:
- `manifest.paths.assets` directory missing
- Referenced asset files in AssetRecord not found

**Response**:
- **Per `regen_policy`**:
  - `REGEN_ON_MISS`: Create placeholder file, log warning
  - `FAIL_ON_MISS`: Raise `AssetMissingError`

**M1 Constraint**: All assets are PLACEHOLDER (zero-byte), so missing assets are non-blocking

### 7.4 State Hash Mismatch

**Detection**:
- After replay, `world_state.state_hash()` != `session_log.expected_hash`

**Response**:
- **FAIL**: Raise `StateReconstructionError`
- **DO NOT** proceed (determinism violation)

**Log Message**:
```
ERROR: State reconstruction failed
  Expected hash: a1b2c3...
  Actual hash:   d4e5f6...
  Replay diverged. Event log may be corrupted or reducer is nondeterministic.
```

---

## 8. EXPLICIT BOUNDARIES (WHAT THE RUNTIME MUST NOT DO)

### 8.1 MUST NOT Modify M2 Schemas

**Forbidden**:
- Add fields to `CampaignManifest`
- Change `SessionZeroConfig` structure
- Alter `EventLog` or `SessionLog` schema
- Modify `CampaignPaths` layout

**Rationale**: M2 schemas are FROZEN. Changes require new schema version + migration.

### 8.2 MUST NOT Use Resolver for Replay

**Forbidden**:
- Call `resolve_attack()` during replay
- Re-execute `evaluate_tactics()` during replay
- Use any resolver function to reconstruct state

**Rationale**: Replay is reducer-only (BL-012). Resolvers emit events; replay applies existing events.

### 8.3 MUST NOT Persist Raw WorldState

**Forbidden**:
- Write `WorldState` directly to disk
- Serialize `WorldState` as JSON outside start_state.json
- Create snapshot files except start_state.json (initial state only)

**Rationale**: BL-020 immutability at non-engine boundaries. State is reconstructed via replay.

### 8.4 MUST NOT Generate IDs or Timestamps During Replay

**Forbidden**:
- Call `uuid.uuid4()` during replay
- Call `datetime.now()` during replay
- Use any nondeterministic source during replay

**Rationale**: BL-017/BL-018 inject-only IDs and timestamps. Replay uses existing event data.

### 8.5 MUST NOT Modify Event Log During Replay

**Forbidden**:
- Append new events during replay
- Modify event payloads during replay
- Delete or reorder events during replay

**Rationale**: Event log is append-only and immutable for replay (BL-008).

---

## 9. SEQUENCE DIAGRAMS

### 9.1 Campaign Load Sequence

```
User                  CampaignStore          Filesystem
  │                        │                     │
  │─ load_campaign(id) ───>│                     │
  │                        │─ read manifest ────>│
  │                        │<────────────────────│
  │                        │─ read start_state ─>│
  │                        │<────────────────────│
  │                        │─ read events.jsonl ─>│
  │                        │<────────────────────│
  │<─ CampaignManifest ────│                     │
```

### 9.2 Session Start Sequence

```
User          RuntimeSession     Engine (play_loop)    EventLog
  │                 │                    │                  │
  │─ start_new() ──>│                    │                  │
  │                 │─ load_start_state() │                 │
  │                 │─ init RNG          │                  │
  │                 │<───────────────────│                  │
  │<────────────────│                    │                  │
  │─ execute_turn() │                    │                  │
  │                 │─ execute_turn() ──>│                  │
  │                 │                    │─ emit events ───>│
  │                 │                    │─ apply events    │
  │                 │<─ TurnResult ──────│                  │
  │<─ TurnResult ───│                    │                  │
```

### 9.3 Session Resume Sequence

```
User          RuntimeSession     ReplayRunner    EventLog
  │                 │                 │              │
  │─ resume() ─────>│                 │              │
  │                 │─ load_start_state()             │
  │                 │─ load events ────────────────>│
  │                 │─ replay events ───>│            │
  │                 │                 │─ reduce() × N│
  │                 │<─ final_state ───│              │
  │                 │─ verify_hash()   │              │
  │<────────────────│                  │              │
```

---

## 10. SUMMARY

**READY FOR IMPLEMENTATION**: Yes

**Key Decisions**:
1. **Replay-first reconstruction**: All sessions reconstruct WorldState via replay (no snapshot optimization in M1)
2. **Reducer-only replay**: No resolver execution during replay (BL-012 enforcement)
3. **Partial write recovery**: Discard incomplete turns, resume from last complete turn
4. **Fail-fast on corruption**: No automatic repair (data integrity paramount)
5. **M2 schema freeze**: No schema modifications, treat as read-only inputs

**Critical Paths Defined**:
- ✓ Campaign load sequence
- ✓ WorldState reconstruction rules
- ✓ Session start contract (new campaign)
- ✓ Session resume contract (existing campaign)
- ✓ Failure modes and error handling
- ✓ Explicit boundaries (forbidden operations)

**Open Questions**: None (M1 scope is fully defined)

**Blocked By**: None

---

**Document Status**: CANONICAL (M1)
**Next Step**: Implement runtime bootstrap logic in `aidm/runtime/bootstrap.py` (implementation work order)
