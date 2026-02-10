# WO-M1-RUNTIME-02 Implementation Guardrails

**Author:** Opus (Agent 46) — Principal Engineer Audit
**Date:** 2026-02-10
**Mode:** REVIEW-ONLY (no code, no tests, no file edits)
**Inputs:** WO-M1-RUNTIME-01 design (Session Bootstrap + Replay Policy), M2 persistence freeze, BL-017/018/020/012/008

---

## 1. DO / DON'T List (20 Bullets)

### DO

1. **DO use `deepcopy(start_state)` before replay.** The initial WorldState loaded from `start_state.json` must not be mutated by the replay loop. `replay_runner.run()` already does this; any code that calls `reduce_event()` directly must follow the same discipline.

2. **DO call `reduce_event()` as the ONLY state mutation path during replay.** No resolver (`resolve_attack`, `evaluate_tactics`, etc.) may be called during replay. Replay is reduction, not re-execution.

3. **DO validate event ID monotonicity before replaying.** If `events.jsonl` contains gaps or out-of-order IDs, raise `BootstrapError` immediately — do not attempt partial replay.

4. **DO inject all IDs and timestamps from the caller.** `RuntimeSession.create_intent()` already takes `intent_id` and `timestamp` as required parameters. The bootstrap layer must follow the same pattern: never call `uuid.uuid4()` or `datetime.utcnow()` inside bootstrap logic.

5. **DO wrap WorldState in `FrozenWorldStateView` at any non-engine return boundary.** If `RuntimeSession` exposes `world_state` to callers outside `aidm/core/`, it must be the frozen proxy.

6. **DO perform log sync verification (`turn_end` count == resolved intent count) on resume.** This is already implemented in `SessionBootstrap.check_log_sync()`. Do not remove or weaken it.

7. **DO handle empty event logs gracefully.** A new campaign has an empty `events.jsonl`. This is valid — skip replay and return the initial state directly.

8. **DO persist events as append-only JSONL.** Each event is one line. Partial writes leave an incomplete line that is detectable as a JSON parse error. Never rewrite `events.jsonl` in its entirety during normal operation.

9. **DO store `initial_state_hash` in `SessionLog` at session start.** This is the expected hash for replay verification on resume.

10. **DO fail hard and loud on corruption.** `EventLogCorruptionError`, `StateReconstructionError`, and `ReplayFailureError` must halt execution. Never degrade gracefully or attempt repair.

### DON'T

11. **DON'T add fields to `CampaignManifest`, `SessionZeroConfig`, `EventLog`, or `SessionLog` schemas.** M2 schemas are FROZEN (see PSD §Frozen Contracts). If the bootstrap needs metadata, store it in a separate runtime-only data structure.

12. **DON'T persist WorldState directly to disk.** Only `start_state.json` (initial state) and `events.jsonl` (event log) are persisted. Reconstructed state is transient, computed on every resume via replay (BL-020 §8.3).

13. **DON'T call `uuid.uuid4()` or `datetime.utcnow()` / `datetime.now()` anywhere in `aidm/runtime/bootstrap.py`.** All IDs and timestamps must be injected by the caller (BL-017, BL-018).

14. **DON'T create snapshot files or checkpoints for M1.** Snapshot optimization is explicitly deferred to M2. Full replay is the only reconstruction path.

15. **DON'T use `time.time()` for replay timing or logging.** Wall-clock time in runtime metadata is acceptable only if injected, never auto-captured. For performance measurement, use `time.perf_counter()` and keep it out of any persisted data.

16. **DON'T let replay consume RNG.** `reduce_event()` receives `rng_manager` but must NOT draw from any stream during replay. Events already contain roll results. If any reducer calls `rng.stream(...).randint(...)`, that is a BL-012 violation.

17. **DON'T silently skip unknown event types during replay verification.** The current `reduce_event()` has a silent `else: pass` for unknown events. This is forward-compatible but must be logged during explicit replay verification to catch event schema drift.

18. **DON'T import from `aidm.narration`, `aidm.immersion`, or `aidm.spark` in `aidm/runtime/`.** The runtime bootstrap layer is engine-adjacent; it must not create presentation dependencies (BL-001 through BL-004 by analogy).

19. **DON'T use `print()` for user-facing messages.** The current `resume_from_campaign()` at line 417 uses `print(f"PARTIAL WRITE RECOVERY: ...")`. Replace with `logging.warning()` or a structured callback — `print()` in library code is a code smell.

20. **DON'T run 10× verification by default on every resume.** The 10× replay verification (AC-10) should be opt-in via a `verify_determinism: bool` flag, not mandatory. Normal resume needs one replay only. The current implementation runs 11 replays per resume (1 normal + 10 verification) — this will scale badly.

---

## 2. Footguns Checklist

### Footgun F-01: Partial Write Leaves Orphaned Intent

**Scenario:** Power loss after events are written to `events.jsonl` but before `intents.jsonl` is updated.

**Detection:** `check_log_sync()` catches this — `turn_end` count > resolved intent count.

**Mitigation:** On resume, if log sync fails after partial write recovery, truncate event log further to match intent log. Current code raises `BootstrapError` on desync, which is correct. Do NOT auto-repair by backfilling intents.

### Footgun F-02: Log Desync from Non-Atomic Dual-Write

**Scenario:** `events.jsonl` and `intents.jsonl` are two separate files. Any crash between writing to the first and the second creates desync.

**Mitigation:** Write events first, then intents. On resume, events are authoritative. If intents have fewer entries than events have `turn_end` events, the extra events belong to an unlogged intent — discard them via partial write recovery. Never write intents first.

**Write ordering contract:** `events.jsonl` THEN `intents.jsonl` — this order is not arbitrary.

### Footgun F-03: Injected Timestamps vs Replay Timestamps

**Scenario:** `IntentEntry.logged_at` uses an injected timestamp. On replay, the same intent is re-processed. If any code compares `datetime.now()` to `logged_at`, the comparison will differ between original play and replay.

**Mitigation:** Never compare wall-clock time to persisted timestamps in any code path that runs during both live play and replay. Timestamps are for audit only.

### Footgun F-04: `session_log.py` ReplayHarness BL Violations

**Scenario:** `aidm/core/session_log.py:410-411` calls `uuid.uuid4()` and `datetime.utcnow()` inside `ReplayHarness`. These are known BL-017/BL-018 violations pre-seeded for WO-M2-01.

**Mitigation:** Do NOT fix these in WO-M1-RUNTIME-02. They are scheduled for WO-M2-01 scope. The bootstrap layer must not call `ReplayHarness` directly — use `replay_runner.run()` instead, which is clean.

### Footgun F-05: Hash Verification After Partial Write Recovery

**Scenario:** Partial write recovery truncates the event log. The expected hash from `SessionLog` was computed from the full (pre-truncation) event log. Hash verification will fail.

**Mitigation:** After partial write recovery, skip hash verification or recompute expected hash from the truncated replay. The current `resume_from_campaign()` computes `expected_hash` from the final state of the current replay, so it self-validates. This is correct but tautological — it only proves this single replay is self-consistent, not that it matches a previously recorded hash. Document this limitation.

### Footgun F-06: `RuntimeSession` Has Two Incompatible `SessionLog` Types

**Scenario:** `aidm/runtime/session.py` defines its own `SessionLog` class. `aidm/core/session_log.py` also has a `SessionLog` (called `CoreSessionLog` in bootstrap). These are DIFFERENT classes with DIFFERENT schemas.

**Mitigation:** The bootstrap layer must translate between them. The current code (bootstrap.py:464-472) creates a new `RuntimeSessionLog` and discards `CoreSessionLog` entries. This means intent history is lost on resume. If intent history must survive resume, the translation must be implemented. Document the decision either way.

### Footgun F-07: `RuntimeSession.world_state` Is Mutable

**Scenario:** `RuntimeSession.world_state` is a raw `WorldState`, not a `FrozenWorldStateView`. Any code with access to the `RuntimeSession` can mutate game state directly, bypassing the event log.

**Mitigation:** `RuntimeSession` is engine-boundary code (it calls `engine_resolver` which produces new state). Internal mutation is authorized. But if `RuntimeSession` exposes `world_state` as a public attribute to non-engine consumers, it must wrap in `FrozenWorldStateView` first. Add a `@property` that returns the frozen view for external access, keeping the raw reference internal.

### Footgun F-08: RNG State Not Advanced to Correct Offset After Replay

**Scenario:** After replaying N events, the RNG manager is at some offset. But `resume_from_campaign()` creates a fresh `RNGManager(master_seed)` (bootstrap.py:461), discarding the replay RNG state. The next live turn starts from RNG offset 0 instead of the correct offset.

**Mitigation:** This is a **critical correctness bug waiting to happen**. Two options:
- **Option A (replay-only, current design):** Replay does not consume RNG (events contain roll results). Live play after resume creates fresh RNG. This works ONLY if the `master_seed` + event count uniquely determines the RNG state. Currently, the fresh RNG at offset 0 means the first roll after resume is always the same for the same seed — this may be acceptable for M1 if sessions always start fresh.
- **Option B (correct):** After replay, use the RNG manager that was advanced through the replay to continue live play. This requires the replay runner to advance RNG in the same order as original execution.

**The WO-M1-RUNTIME-01 design specifies Option A** (Section 4.2: "NO RNG CONSUMPTION" during replay). Document that this means post-resume RNG restarts from offset 0, and state is correct only because replay uses stored roll results.

---

## 3. Acceptance Checklist for Final PR

### Tests — Mandatory

| # | Test | What It Proves |
|---|------|---------------|
| 1 | New campaign → start session → execute 1 turn → events persist to `events.jsonl` | Basic lifecycle works |
| 2 | Start session → execute 5 turns → save → resume → `state_hash()` matches pre-save | Resume correctness |
| 3 | Inject corrupt event (ID gap) into `events.jsonl` → resume raises `BootstrapError` | BL-008 enforcement |
| 4 | Truncate `events.jsonl` mid-turn (no `turn_end`) → resume recovers → no crash | Partial write recovery |
| 5 | Add extra intent to `intents.jsonl` (no matching events) → resume raises `BootstrapError` | Log sync enforcement |
| 6 | 10× replay of same campaign produces identical `state_hash` | AC-10 / BL-012 determinism |
| 7 | `BootstrapError` raised if `start_state.json` missing | Fail-fast on missing files |
| 8 | `BootstrapError` raised if manifest version incompatible | Version check works |
| 9 | Empty campaign (0 events) → start new session → no replay needed → session starts | Empty log path works |
| 10 | `bootstrap.py` contains zero calls to `uuid.uuid4()` or `datetime.utcnow()` | BL-017/BL-018 compliance (AST scan) |

### Invariants — Mandatory Verification

| # | Invariant | How to Verify |
|---|-----------|--------------|
| 1 | No new fields added to `CampaignManifest`, `SessionZeroConfig`, `EventLog`, `SessionLog` schemas | `git diff` on `aidm/schemas/campaign.py`, `aidm/core/event_log.py`, `aidm/core/session_log.py` |
| 2 | `aidm/runtime/bootstrap.py` does not import from `aidm.narration`, `aidm.immersion`, `aidm.spark` | AST import scan |
| 3 | No `print()` calls in production code (use `logging` instead) | `grep -n "print(" aidm/runtime/bootstrap.py` |
| 4 | All existing 1725 tests still pass | `python -m pytest tests/ -v --tb=short` |
| 5 | Test runtime remains under 10 seconds total | `python -m pytest tests/ --tb=line -q` |
| 6 | `events.jsonl` write uses append mode (`"a"`) not overwrite (`"w"`) | Code review |
| 7 | Replay path calls `reduce_event()` only — no resolver imports in bootstrap | AST import scan |
| 8 | `RuntimeSession` internal `world_state` is raw; any public-facing property returns `FrozenWorldStateView` | Code review + type annotation check |

---

## STOP Conditions

If the implementing agent proposes ANY of the following, the WO must be returned for re-scoping:

- **STOP-01:** Adding fields to frozen M2 schemas
- **STOP-02:** Calling resolvers during replay
- **STOP-03:** Persisting WorldState directly to disk (bypassing event log)
- **STOP-04:** Using `uuid.uuid4()` or `datetime.utcnow()` in bootstrap code
- **STOP-05:** Relaxing determinism requirements (e.g., skipping hash verification)
- **STOP-06:** Creating snapshot/checkpoint files for M1
- **STOP-07:** Importing from narration/immersion/spark layers

---

*End of guardrail memo.*
