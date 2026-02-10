# CLI Invocation Assumptions for Sonnet D

**Work Order:** WO-M1-RUNTIME-WIRING-02
**Agent:** Sonnet A
**Date:** 2026-02-10
**For:** Sonnet D (final runtime vertical slice implementation)

---

## Command Line Entry Point

Based on M1.5 Runtime Experience Design (§1.1):

```bash
python -m aidm.runtime.runner --campaign <campaign_id>
```

**Expected module location:** `aidm/runtime/runner.py`

---

## Bootstrap Sequence (for Wiring)

The following sequence is **ready and tested** via fixtures in `tests/fixtures/runtime/`:

### Step 1: Load Campaign Data

```python
from aidm.core.campaign_store import CampaignStore
from aidm.runtime.bootstrap import SessionBootstrap

store = CampaignStore(root_dir=Path.home() / ".aidm" / "campaigns")

manifest, initial_state, event_log, session_log = SessionBootstrap.load_campaign_data(
    store, campaign_id
)
```

**Returns:**
- `manifest`: `CampaignManifest` (from `manifest.json`)
- `initial_state`: `WorldState` (from `start_state.json`)
- `event_log`: `EventLog` (from `events.jsonl`)
- `session_log`: `CoreSessionLog` (from `intents.jsonl`)

**Raises:**
- `BootstrapError` if campaign not found or files corrupt

---

### Step 2: Detect Partial Write

```python
from aidm.runtime.bootstrap import SessionBootstrap

recovery = SessionBootstrap.detect_partial_write(event_log)

if recovery.incomplete_turn_detected:
    print(f"[AIDM] PARTIAL WRITE RECOVERY: {recovery.recovery_details}")
    print(f"[AIDM]   Discarding {recovery.events_discarded} events after last turn_end")
    # Truncate event_log.events to recovery.last_complete_turn_index
```

**Returns:** `PartialWriteRecoveryResult`

**Use case:** Emergency exit (Ctrl+C) may leave incomplete turn in `events.jsonl`

---

### Step 3: Check Log Synchronization

```python
sync_result = SessionBootstrap.check_log_sync(event_log, session_log)

if not sync_result.in_sync:
    raise BootstrapError(
        f"Log desynchronization detected:\n"
        f"  Event log: {sync_result.event_log_turns} complete turns\n"
        f"  Session log: {sync_result.session_log_resolved} resolved intents\n"
        f"  Details: {sync_result.details}"
    )

print(f"[AIDM] Verifying log synchronization...")
print(f"[AIDM]   Event log: {sync_result.event_log_turns} complete turns")
print(f"[AIDM]   Session log: {sync_result.session_log_resolved} resolved intents")
print(f"[AIDM]   ✓ Logs synchronized")
```

**Returns:** `LogSyncCheckResult`

**Invariant:** `turn_end` count in event log >= resolved intent count in session log

**Why:** Goblin turns produce `turn_end` events but no player intents (AI-driven).

---

### Step 4: Replay Event Log

```python
from aidm.core.replay_runner import run as replay_runner
from aidm.core.rng_manager import RNGManager

rng_manager = RNGManager(master_seed=manifest.master_seed)

replay_report = replay_runner(
    initial_state=initial_state,
    event_log=event_log,
    rng_manager=rng_manager,
)

if not replay_report.success:
    raise BootstrapError(f"Replay failed: {replay_report.error}")

reconstructed_state = replay_report.final_state

print(f"[AIDM] Replaying event log...")
print(f"[AIDM]   Found {len(event_log.events)} events ({replay_report.turns_replayed} complete turns)")
print(f"[AIDM]   Turn 1 (goblin_1) ✓")
print(f"[AIDM]   Turn 2 (pc_fighter) ✓")
print(f"[AIDM] Replay complete.")
print(f"[AIDM] Final state hash: {reconstructed_state.state_hash()}")
```

**Returns:** `ReplayReport` with `final_state: WorldState`

**Guardrail:** Replay does NOT consume RNG (events contain roll results). See OPUS_WO-M1-RUNTIME-02_GUARDRAILS.md §Footgun F-08.

---

### Step 5: Initialize RuntimeSession

```python
from aidm.runtime.session import RuntimeSession
from datetime import datetime

session = RuntimeSession(
    world_state=reconstructed_state,
    rng_manager=rng_manager,
    engine_resolver=<your resolver>,  # Wire to engine
    session_id=manifest.campaign_id,
    started_at=datetime.now(),  # Session start time (not persisted in state)
)

print(f"[AIDM] Session ready.")
print(f"[AIDM] Next turn: <current_actor_id> (Turn {reconstructed_state.active_combat['turn_counter']})")
```

---

### Step 6: Enter Turn Loop

```python
while True:
    user_input = input("> ")

    if user_input.strip() == "/exit":
        break

    # Create intent from user input
    intent = session.create_intent(
        actor_id=<current_actor_id>,
        source_text=user_input,
        intent_id=<deterministic_id>,  # BL-017: inject, don't generate
        timestamp=<deterministic_timestamp>,  # BL-018: inject, don't generate
    )

    # Clarify if needed (blocking)
    if intent.status == IntentStatus.PENDING:
        # ... clarification loop ...
        pass

    # Resolve via engine
    result = session.resolve_intent(intent)

    # Log intent + result
    session.log_intent_result(intent, result)

    # Update world state
    session.apply_result(result)

    # Display outcome
    print(f"[RESOLVE] {result.summary}")

    # Narrate (optional, non-authoritative)
    if narration_service:
        narration = narration_service.generate_narration(result)
        print(narration)

    # Advance turn
    # ... turn logic ...
```

---

### Step 7: Exit and Save

```python
# On graceful exit (/exit command)
print(f"[AIDM] Saving session state...")

# Persist event log
campaign_dir = store.campaign_dir(campaign_id)
event_log.to_jsonl(campaign_dir / "events.jsonl")

# Persist session log (intents)
session.session_log.to_jsonl(campaign_dir / "intents.jsonl")

print(f"[AIDM]   Events written: events.jsonl ({len(event_log.events)} events)")
print(f"[AIDM]   Intents written: intents.jsonl ({len(session.session_log.entries)} entries)")
print(f"[AIDM]   State hash: {session.world_state.state_hash()}")
print(f"[AIDM] Session saved.")
print(f"[AIDM] Goodbye!")
```

**Write ordering:** `events.jsonl` THEN `intents.jsonl` (see OPUS_WO-M1-RUNTIME-02_GUARDRAILS.md §Footgun F-02)

---

## Integration Test Coverage

The following integration tests are **ready and passing** in `tests/test_runtime_vertical_slice_integration.py`:

| Test ID | Test Name | What It Proves |
|---------|-----------|---------------|
| T-RVS-01 | `test_t_rvs_01_load_empty_campaign` | Empty campaign loads correctly |
| T-RVS-01 | `test_t_rvs_01_detect_no_partial_write_on_empty` | Empty campaign has no partial write |
| T-RVS-02 | `test_t_rvs_02_resume_from_2turns_replay_succeeds` | Resume from 2 turns replays correctly |
| T-RVS-02 | `test_t_rvs_02_log_sync_check_passes_on_2turns` | Log sync check passes (2 turns, 1 intent) |
| T-RVS-03 | `test_t_rvs_03_corrupt_id_gap_raises_bootstrap_error` | Event ID gap causes fail-fast |
| T-RVS-03 | `test_t_rvs_03_corrupt_json_syntax_raises_bootstrap_error` | Invalid JSON causes fail-fast |
| T-RVS-04 | `test_t_rvs_04_partial_write_detected_on_incomplete_turn` | Incomplete turn triggers recovery |
| T-RVS-05 | `test_t_rvs_05_extra_intent_causes_desync` | Extra intent causes log desync |

---

## Fixture Inventory

| Fixture | Location | Use Case |
|---------|----------|----------|
| Tiny campaign (empty) | `tests/fixtures/runtime/tiny_campaign_*_empty.jsonl` | New campaign initialization |
| Tiny campaign (2 turns) | `tests/fixtures/runtime/tiny_campaign_*_2turns.jsonl` | Resume and replay testing |
| Corrupt ID gap | `tests/fixtures/runtime/tiny_campaign_events_corrupt_id_gap.jsonl` | BL-008 fail-fast enforcement |
| Corrupt JSON | `tests/fixtures/runtime/tiny_campaign_events_corrupt_json.jsonl` | JSON parse error handling |

See `tests/fixtures/runtime/README.md` for full fixture documentation.

---

## Assumptions for Final Wiring

1. **Module structure:**
   - `aidm/runtime/runner.py` — CLI entry point (to be created by Sonnet D)
   - `aidm/runtime/bootstrap.py` — Session bootstrap (already exists)
   - `aidm/runtime/session.py` — RuntimeSession (already exists)
   - `aidm/core/campaign_store.py` — CampaignStore (already exists)

2. **Campaign root directory:**
   - Default: `~/.aidm/campaigns/` (configurable via `--root` flag)
   - Each campaign: `<root>/<campaign_id>/`

3. **Error handling:**
   - Fail-fast on corruption (no auto-repair)
   - Clear error messages (see M1.5 Runtime Experience Design §1.3 for examples)
   - Graceful shutdown on Ctrl+C (partial write recovery on next resume)

4. **Determinism requirements:**
   - All IDs and timestamps injected by caller (BL-017, BL-018)
   - No `uuid.uuid4()` or `datetime.now()` in runtime code
   - Replay produces identical state hash (10× verified in tests)

5. **Output formatting:**
   - Text-only, no UI (M1.5 scope)
   - Prefix runtime messages with `[AIDM]` for clarity
   - See M1.5 Runtime Experience Design §2, §3 for expected output format

---

## Key Guardrails (from OPUS_WO-M1-RUNTIME-02_GUARDRAILS.md)

**DO:**
- Use `deepcopy(start_state)` before replay
- Call `reduce_event()` as ONLY state mutation path during replay
- Inject all IDs and timestamps from caller
- Wrap WorldState in `FrozenWorldStateView` at non-engine return boundaries
- Persist events as append-only JSONL
- Fail hard and loud on corruption

**DON'T:**
- Add fields to frozen M2 schemas
- Persist WorldState directly to disk (only `start_state.json` + `events.jsonl`)
- Call `uuid.uuid4()` or `datetime.now()` in bootstrap code
- Use `print()` for user-facing messages (use `logging` instead, or structured output)
- Run 10× verification by default (opt-in only)
- Import from `aidm.narration`, `aidm.immersion`, or `aidm.spark` in `aidm/runtime/`

---

## Next Steps for Sonnet D

1. **Create `aidm/runtime/runner.py`** with CLI argument parsing
2. **Wire bootstrap sequence** (steps 1-5 above)
3. **Implement turn loop** (step 6 above)
4. **Implement exit and save** (step 7 above)
5. **Run integration tests:** `python -m pytest tests/test_runtime_vertical_slice_integration.py -v`
6. **Verify all 1725+ existing tests still pass**
7. **Manual smoke test** with tiny campaign fixture

---

**Document Status:** Complete
**Last Updated:** 2026-02-10
**Contact:** Sonnet A (WO-M1-RUNTIME-WIRING-02)
