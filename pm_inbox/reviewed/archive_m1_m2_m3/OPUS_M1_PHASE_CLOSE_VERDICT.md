# M1 Phase-Close Sanity Audit

**Agent:** Opus
**Date:** 2026-02-10
**Status:** Complete

---

## Verdict: A) M1 is clean for M2

The deterministic replay loop, serialization layer, and immutability enforcement are sound. Nothing blocks persistence, save/load, or replay-from-disk.

---

## Evidence (5 areas reviewed)

- **AC-09 (Reducer Coverage):** All 20 MUTATING_EVENTS have explicit handlers in `reduce_event()`. `get_missing_handlers()` verifies at test time. PASS.
- **AC-10 (Replay Determinism):** `run()` deepcopies initial state, `reduce_event()` deepcopies per-event. `state_hash()` uses `json.dumps(sort_keys=True)` + SHA-256. 10x replay tests green. PASS.
- **BL-017/018 (Inject-Only):** No violations inside the deterministic loop (reducers, resolvers, event emission). Violations exist in peripheral code — see risks below.
- **BL-020 (WorldState Immutability):** `FrozenWorldStateView` correctly wraps with `MappingProxyType` recursively. No unauthorized mutations found in production paths. PASS.
- **IPC Readiness:** MessagePack with `_sort_dict_keys()` pre-sort, `strict_types=True`. WorldState/Event/EngineResult all have `to_dict()`/`from_dict()`. EventLog has `to_jsonl()`/`from_jsonl()`. No pickle/shelve anywhere. PASS.

---

## Risks (3, none blocking)

1. **BL-017/018 violations in campaign_store.py** (lines 81, 99) — `uuid.uuid4()` and `datetime.now()` used for campaign creation. These are outside the replay loop so they don't threaten determinism, but M2 persistence tests that replay campaign creation will need injected IDs/timestamps. Fix scope: 1 file, ~5 lines.

2. **BL-020 violation in session_log.py** (line 303) — `ReplayHarness.replay_session()` mutates WorldState directly. This is a verification utility, not a production path, and operates on a deepcopy. But if ReplayHarness is ever used as a real replay path, it bypasses the canonical reducer. Fix scope: route through `reduce_event()` instead of raw dict mutation.

3. **Event.citations mutable default** (event_log.py line 27) — Uses `None` + `__post_init__` instead of `field(default_factory=list)`. Mitigated today, but a latent footgun if Event is ever shallow-copied. Fix scope: 1 line.

---

## Bottom Line

The deterministic core (replay runner, reducers, state hashing, IPC serialization, event log persistence) is solid. The three risks are all peripheral, low-severity, and fixable in a single lightweight work order before M2 implementation begins. No architectural changes needed.
