# WO-ORACLE-03: Compactions + Cold Boot (Oracle Phase 3)

**Status:** DISPATCH-READY
**Phase:** Oracle Phase 3 of 3
**Gate:** Gate C — Cold Boot Byte-Equality + Compaction Reproducibility + No-Backflow Enforcement
**Depends on:** WO-ORACLE-01 (`4c5526a`), WO-ORACLE-02 (`4245e38`), DOCTRINE_07_SESSION_LIFECYCLE_V0.txt
**Blocked by:** Nothing (Session Lifecycle spec now exists)

---

## Target Lock

Build the cold boot pipeline and compaction infrastructure: a SaveSnapshot that records Oracle state at a boundary, a cold_boot() function that rebuilds byte-identical state from a snapshot + event log, and a CompactionRegistry that manages reproducible non-canon accelerators.

**One-line success:** Delete everything except the snapshot and event log. Rebuild. Get identical bytes. Gate C green.

---

## Binary Decisions

1. **SaveSnapshot lives in Oracle layer.** It is an Oracle artifact recording Oracle state.
2. **Compaction and CompactionRegistry live in Oracle layer.** They own non-canon derived views.
3. **cold_boot() lives in Oracle layer.** It reconstructs Oracle state from Oracle artifacts.
4. **No pending state restoration.** PENDING_ROLL/CONSENT/HANDOUT require UI interaction layer — deferred to a future WO. SaveSnapshot includes a pending_state field but cold_boot() does not restore it in Phase 3.
5. **No Spark/Director/Lens wiring.** Phase 3 proves Oracle-internal consistency only. Downstream consumers are unchanged.
6. **Use canonical_short_hash for all new content-addressed IDs.** Per PIN-1/PIN-2 in Lens spec. Do NOT use compute_value_hash for Oracle artifact IDs.
7. **Compaction output is deterministic template-based, not LLM-based.** Phase 3 compactions use the existing SessionSegmentSummary pattern (deterministic templates). LLM-based compactions require Spark integration — deferred.

---

## Contract Spec

### Change 1: SaveSnapshot dataclass (new, in `aidm/oracle/`)

Frozen dataclass matching Session Lifecycle spec §2:

```
SaveSnapshot:
  snapshot_id: str              # canonical_short_hash(canonical_bytes)
  save_type: str                # SCENE | SESSION | CAMPAIGN
  timestamp_event_id: int       # monotonic event ID at snapshot boundary (NOT wall-clock)
  facts_ledger_digest: str      # SHA-256 of canonical FactsLedger bytes
  unlock_state_digest: str      # SHA-256 of canonical UnlockState bytes
  story_state_digest: str       # SHA-256 of canonical StoryState bytes
  working_set_digest: str       # SHA-256 of WorkingSet bytes
  event_log_range: tuple        # (first_event_id, last_event_id) inclusive
  event_log_hash: str           # SHA-256 of JSONL bytes in range
  pending_state: None           # Phase 3: always None (pending state deferred)
  pins_snapshot: dict           # frozen via MappingProxyType in __post_init__
  compaction_ids: tuple         # IDs of valid compactions at boundary
  canonical_bytes: bytes        # computed
  bytes_hash: str               # SHA-256 of canonical_bytes
```

No wall-clock timestamps. The `timestamp_event_id` is the event boundary marker.

### Change 2: Compaction dataclass (new, in `aidm/oracle/`)

Frozen dataclass matching Session Lifecycle spec §4.1:

```
Compaction:
  compaction_id: str            # canonical_short_hash(input_handles_bytes + compaction_policy_id)
  purpose: str                  # RECAP | SYNOPSIS | SEGMENT_SUMMARY
  compaction_policy_id: str
  input_handles: tuple          # fact_ids consumed (frozen)
  output_bytes: bytes           # canonical JSON output
  output_hash: str              # SHA-256 of output_bytes
  allowmention_handles: tuple   # subset safe for Lens output (frozen)
```

### Change 3: CompactionRegistry (new, in `aidm/oracle/`)

Registry that manages compaction lifecycle:

```
CompactionRegistry:
  register(compaction) -> None          # add compaction, reject duplicate IDs
  invalidate(fact_ids) -> list[str]     # mark compactions stale whose input_handles overlap
  rebuild(compaction_id, source_facts, policy) -> Compaction  # regenerate from sources
  verify_all() -> list[tuple[str, bool]]  # assert output_hash matches for all compactions
  get(compaction_id) -> Compaction
  all_compactions() -> list[Compaction]
  active_ids() -> tuple[str, ...]       # non-stale compaction IDs
```

Stale compactions are marked, not deleted. Rebuild produces a new Compaction with identical output_bytes if inputs unchanged (G4 gate).

### Change 4: create_snapshot() function (new, in `aidm/oracle/`)

`create_snapshot(facts_ledger, unlock_state, story_state, working_set, event_log, event_range, pins, compaction_registry, save_type) -> SaveSnapshot`

Steps:
1. Compute digest of each Oracle store's canonical bytes
2. Compute event_log_hash from JSONL bytes in range
3. Collect active compaction IDs from registry
4. Assemble SaveSnapshot dataclass
5. Serialize to canonical JSON
6. Compute snapshot_id = canonical_short_hash(canonical_bytes)
7. Return frozen SaveSnapshot

### Change 5: cold_boot() function (new, in `aidm/oracle/`)

`cold_boot(snapshot, event_log) -> tuple[FactsLedger, UnlockState, StoryState, WorkingSet]`

Steps:
1. Assert event_log_hash matches stored hash — HARD FAIL on mismatch
2. Assert pins_snapshot matches current environment — HARD FAIL on mismatch (G6)
3. Initialize empty Oracle stores
4. Replay events through the existing event reduction mechanism (the module that implements `reduce_event()` — confirm actual function/file before coding)
5. After replay, compute digests of all stores
6. Assert facts_ledger_digest matches — HARD FAIL on mismatch
7. Assert unlock_state_digest matches — HARD FAIL on mismatch
8. Assert story_state_digest matches — HARD FAIL on mismatch
9. Rebuild WorkingSet via compile_working_set() (Phase 2)
10. Assert working_set_digest matches — HARD FAIL on mismatch
11. Return reconstructed stores

All assertion failures raise a specific exception (e.g., `ColdBootDigestMismatchError`) with diagnostic info (which digest failed, expected vs actual).

### Change 6: Gate C tests (new test file)

Minimum 22 tests across these categories:

**Cold boot byte-equality (Gate C core):**
1. `test_cold_boot_roundtrip` — create stores, save snapshot, cold boot from snapshot, assert all digests match
2. `test_cold_boot_after_events` — append events, save, cold boot, assert state identical
3. `test_cold_boot_working_set_digest` — cold boot reconstructs WorkingSet with matching digest
4. `test_cold_boot_10x` — cold boot 10 times, all produce identical digests
5. `test_cold_boot_fails_on_corrupted_event_log` — tamper with event, assert HARD FAIL
6. `test_cold_boot_fails_on_digest_mismatch` — modify a fact post-snapshot, assert HARD FAIL

**Compaction reproducibility (G4):**
7. `test_compaction_deterministic` — same inputs + policy, assert identical output_bytes
8. `test_compaction_deterministic_10x` — 10 generations, all identical
9. `test_compaction_rebuild_matches_original` — register, invalidate, rebuild, assert output_hash matches
10. `test_compaction_delete_rebuild_identical` — delete all, rebuild all, assert all output_hashes match
11. `test_compaction_no_canon_writes` — assert compaction creation does not modify FactsLedger
12. `test_compaction_no_canon_writes_on_rebuild` — assert rebuild does not modify FactsLedger

**CompactionRegistry:**
13. `test_registry_register_and_get` — basic CRUD
14. `test_registry_invalidate_on_source_change` — change source fact, assert compaction marked stale
15. `test_registry_verify_all_passes` — all compactions valid, verify returns all True
16. `test_registry_verify_detects_corruption` — tamper with output_bytes, verify returns False
17. `test_registry_rejects_duplicate_id` — register same ID twice, assert rejection

**Pin assertion (G6):**
18. `test_pin_assertion_passes_matching_pins` — cold boot with matching pins succeeds
19. `test_pin_assertion_fails_on_mismatch` — cold boot with different pins HARD FAILs
20. `test_pin_assertion_fails_deterministically` — error message includes which pin mismatched

**SaveSnapshot integrity:**
21. `test_snapshot_frozen` — all container fields frozen (tuple/MappingProxyType)
22. `test_snapshot_canonical_json_no_floats` — float injection raises TypeError

---

## Integration Seams

1. **Oracle stores → create_snapshot():** The snapshot function reads Phase 1 stores (FactsLedger, UnlockState, StoryState) and Phase 2 artifacts (WorkingSet). Confirm the digest/hash computation APIs exist on each store — they may have canonical_bytes methods or require calling canonical_json() on the store contents.

2. **EventLog → cold_boot():** The cold boot reads from the existing EventLog (aidm/core/event_log.py). Confirm the API for reading an event range and serializing to JSONL bytes. The existing replay_runner provides `reduce_event()` — confirm it can be called on Oracle store objects, not just WorldState.

3. **compile_working_set() → cold_boot():** After replay, cold_boot calls compile_working_set() from Phase 2 to rebuild the WorkingSet. Confirm the Phase 2 compiler is importable from `aidm/oracle/working_set.py` and accepts the reconstructed stores.

4. **SessionSegmentSummary → CompactionRegistry:** The existing SessionSegmentSummary (aidm/lens/segment_summarizer.py) is the closest existing compaction. Phase 3 does NOT wrap it — CompactionRegistry manages Oracle-layer compactions independently. The existing summarizer remains in Lens layer. Future integration may bridge them.

5. **Boundary completeness gate:** No new `aidm/` packages are expected (compaction/snapshot go into existing `aidm/oracle/`). The boundary gate should not need updating. If a new subpackage is created, register it per Field Manual #23.

---

## Assumptions to Validate

1. **Oracle store digest APIs:** Confirm FactsLedger, UnlockState, and StoryState have methods (or can be wrapped) to produce canonical bytes for digest computation. Phase 1 stores may serialize their contents — check `canonical_json()` compatibility.

2. **EventLog range queries:** Confirm EventLog supports reading a slice of events by ID range and producing deterministic JSONL bytes for that range. The existing `to_jsonl()` writes the full log — a range-based variant may need to be added.

3. **replay_runner integration:** The existing `reduce_event()` in replay_runner.py reduces events against WorldState. Cold boot needs to reduce events against Oracle stores (FactsLedger, UnlockState, StoryState). These are different objects. Determine whether to: (a) extend reduce_event() to handle Oracle store updates, or (b) write a parallel Oracle-specific reducer that maps events to store mutations. Option (b) is likely correct — Oracle stores track different state than WorldState.

4. **compile_working_set() import:** Confirm `compile_working_set` is importable from `aidm.oracle.working_set` and its signature matches the Phase 2 implementation.

5. **Compaction policy:** Phase 3 needs at least one compaction policy for testing. Use a minimal deterministic policy (e.g., "concatenate fact payloads sorted by stable_key, hash"). This is a test fixture, not a production policy — keep it simple.

6. **No new aidm/ packages needed:** Confirm all new files go into existing `aidm/oracle/`. If the builder decides CompactionRegistry needs its own module, it stays within `aidm/oracle/` (no new top-level package).

---

## Success Criteria (22 minimum)

Gate C is GREEN when all of:
1. `create_snapshot()` exists and is callable
2. `cold_boot()` exists and is callable
3. `Compaction` dataclass exists and is frozen
4. `CompactionRegistry` exists with register/invalidate/rebuild/verify
5. Tests 1-6 pass (cold boot byte-equality — roundtrip, events, 10x, corruption detection)
6. Tests 7-12 pass (compaction reproducibility — determinism, rebuild, no canon writes)
7. Tests 13-17 pass (CompactionRegistry — CRUD, invalidation, verification)
8. Tests 18-20 pass (pin assertion — pass/fail/deterministic error)
9. Tests 21-22 pass (snapshot integrity — frozen, no floats)
10. All existing tests still pass (0 regressions)
11. Gate A (22/22) still GREEN after changes
12. Gate B (23/23) still GREEN after changes
13. SaveSnapshot uses canonical_short_hash for snapshot_id (not compute_value_hash)
14. Compaction uses canonical_short_hash for compaction_id
15. No wall-clock timestamps in any new dataclass
16. No UUIDs or random values in any output
17. Canonical JSON profile matches Phase 1/2 (same separators, same float prohibition)
18. All new dataclasses pass immutability gate
19. cold_boot() raises specific exception on digest mismatch (not generic AssertionError)
20. cold_boot() raises specific exception on pin mismatch
21. Compaction rebuild produces identical output_bytes (provable, not just asserted)
22. At least 22 tests in Gate C test file

---

## Constraints

- **No Spark changes.** Compactions use deterministic templates, not LLM.
- **No Lens/Director changes.** Phase 3 is Oracle-internal consistency.
- **No pending state restoration.** Deferred to future WO (requires UI layer).
- **No wall-clock timestamps.** Anywhere. In any dataclass field.
- **No compute_value_hash for Oracle artifact IDs.** Use canonical_short_hash only (PIN-2 in Lens spec).
- **Floats FORBIDDEN in canonical artifacts** (Field Manual #22).
- **Frozen containers use MappingProxyType** — canonical_json handles this transparently (Field Manual #24).
- **Oracle is read-only to downstream consumers.** cold_boot() and CompactionRegistry write only Oracle stores, never Lens/Spark/Box.
- **This WO creates NO new `aidm/` packages.** All files go in existing `aidm/oracle/`. Boundary gate should not need updating, but verify (Field Manual #23).
- **Compaction rebuild is the gate, not compaction creation.** The test that matters is: delete all compactions, rebuild from source facts + policy, assert identical output. Creation is just the first build.

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-ORACLE-03.md` with 4 mandatory sections (Scope Accuracy, Discovery Log, Methodology Challenge, Field Manual Entry). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-ORACLE-03 verdict row (leave verdict blank for PM to fill).
3. `git add` ALL files: code + tests + debrief + briefing.
4. Commit with message: `feat: WO-ORACLE-03 — Compactions + Cold Boot + Gate C`
5. Add commit hash to debrief header.
6. Amend commit to include hash in debrief.
7. Run `git status` to confirm clean tree.

---

*Drafted by PM (Aegis). Dispatch-ready for Operator.*
