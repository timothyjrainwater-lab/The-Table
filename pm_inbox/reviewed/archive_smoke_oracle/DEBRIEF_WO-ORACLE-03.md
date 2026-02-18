# DEBRIEF: WO-ORACLE-03 — Compactions + Cold Boot + Gate C

**WO:** WO-ORACLE-03
**Status:** COMPLETE
**Commit:** `ae59a02` (hash changes on amend — verify with `git log --oneline -1`)

---

## 1. Scope Accuracy

The WO specified 6 changes and 22 success criteria. All changes implemented, all criteria met. 24 Gate C tests written (exceeding the 22 minimum). No files outside `aidm/oracle/` and `tests/` were modified — the boundary gate did not need updating (all new files are in existing `aidm/oracle/`).

**Files created (4):** `aidm/oracle/save_snapshot.py` (SaveSnapshot + create_snapshot()), `aidm/oracle/compaction.py` (Compaction + CompactionRegistry + make_compaction()), `aidm/oracle/cold_boot.py` (cold_boot() + Oracle event reducer + 3 exception classes), `tests/test_oracle_gate_c.py` (24 Gate C tests across 6 categories).

**Files modified (0):** No existing files were changed. The Oracle event reducer was built as a parallel path to replay_runner.py's reduce_event(), as the WO anticipated. EventLog was not modified — event range filtering is done inline via list comprehension over event_log.events.

## 2. Discovery Log

**Before implementation:**
- Confirmed all Phase 1 store digest APIs: `FactsLedger.digest()`, `UnlockState.digest()`, `StoryStateLog.digest()`. All return `canonical_hash()` of sorted contents.
- Confirmed `reduce_event()` in replay_runner.py operates on WorldState, not Oracle stores. Built a parallel `_reduce_oracle_event()` that maps events to FactsLedger/UnlockState/StoryStateLog mutations.
- Confirmed EventLog has `to_jsonl()` but no range query. Rather than modifying EventLog (outside WO scope), implemented range filtering inline in `_compute_event_log_hash()`.
- Confirmed `compile_working_set()` importable from `aidm.oracle.working_set` with expected signature.
- Confirmed boundary gate already has oracle registered at rank 0 — no update needed.

**During implementation:**
- Defined 3 Oracle-specific event types: `oracle_fact_created`, `oracle_unlock`, `oracle_story_init`. These are parallel to the game events in replay_runner but operate on Oracle stores. The story state events (`scene_start`, `scene_end`, `mode_changed`, `world_id_set`) are shared with StoryStateLog.apply().
- The `_compute_event_log_hash()` function is duplicated in save_snapshot.py and cold_boot.py. Both must produce identical hashes. They use the same algorithm: `json.dumps(event.to_dict(), sort_keys=True)` per event, joined by newlines, SHA-256 of the bytes. This duplication is intentional — each module is self-contained.

## 3. Methodology Challenge

**EventLog range queries without modifying EventLog.** The WO says "No Lens/Director changes" and the EventLog is in `aidm/core/`. Modifying it would add a seam the WO doesn't authorize. Instead, both `save_snapshot.py` and `cold_boot.py` iterate `event_log.events` with inline range filtering. This works because EventLog exposes an `.events` property returning a list copy. If performance becomes an issue with large logs, a `range_events()` method should be added to EventLog in a future WO.

**Oracle reducer design: new event types vs. reusing existing events.** The existing events (`hp_changed`, `attack_roll`, etc.) mutate WorldState, not Oracle stores. Oracle stores need their own event vocabulary (`oracle_fact_created`, `oracle_unlock`, `oracle_story_init`). The spec says "Replay events through reduce_event() (existing replay_runner.py)" but that function takes WorldState. A parallel reducer is the correct architecture — Oracle stores and WorldState are different state representations.

## 4. Field Manual Entry

**Oracle event reducer is parallel to replay_runner, not an extension.** `replay_runner.reduce_event()` maps events to WorldState mutations (73 mutating types). `cold_boot._reduce_oracle_event()` maps events to Oracle store mutations (3 Oracle-specific types + 4 shared story types). These are different state representations of the same game. Don't try to merge them — they serve different purposes and will diverge further as Oracle stores grow.
