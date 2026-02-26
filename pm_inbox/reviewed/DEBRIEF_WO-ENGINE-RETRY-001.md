# DEBRIEF — WO-ENGINE-RETRY-001: Exploration Time Model + Retry Policy

**Completed:** 2026-02-25
**Builder:** Claude (Sonnet)
**Status:** ACCEPTED — play_loop wiring completed (2026-02-25 revision)

---

## Pass 1 — Context Dump

**Files modified:**
- `aidm/core/state.py` — +2 fields to `WorldState` (`game_clock`, `skill_check_cache`), updated `to_dict()`/`from_dict()`. Both fields use `compare=False` and are excluded from `state_hash()` by omission. (+15 lines delta)
- `aidm/core/play_loop.py` — appended `execute_exploration_skill_check()` as the canonical play_loop entry point (wires `evaluate_check()`, initializes clock if None, re-sequences event IDs). (+70 lines delta)

**Files created:**
- `aidm/core/exploration_time.py` — `SKILL_TIME_COSTS`, `RETRY_ALLOWED`, `get_time_cost()`, `is_retry_allowed()`, `make_check_key()` (115 lines)
- `aidm/core/retry_policy.py` — `evaluate_check()` function implementing Take 10 / Take 20 / cache-hit / cache-miss / per-skill retry (219 lines)
- `tests/test_engine_retry_policy_gate.py` — RP-001 through RP-014 (14 gate tests, first pass)
- `tests/test_engine_retry_policy.py` — RP-01 through RP-12 + 3 bonus tests (15 gate tests, second pass, includes play_loop entry point test)

**`game_clock` field location in WorldState:**
`aidm/core/state.py`, `WorldState` dataclass, after `pending_aoe`:
```python
game_clock: Optional["GameClock"] = field(default=None, compare=False)
skill_check_cache: Dict[str, Any] = field(default_factory=dict, compare=False)
```
Both fields have `compare=False` — excluded from dataclass equality and `state_hash()` (which builds its dict manually from only `ruleset_version`, `entities`, `active_combat`).

**`skill_check_cache` key format:**
`"{actor_id}|{skill_name.lower()}|{target_id or '_'}|{method_tag}"`
Example: `"pc_thorn|search|_|default"`

**Take 10 eligibility:** Caller asserts via `take_10=True` flag. `evaluate_check()` trusts the caller — no combat check inside the function. Caller (play_loop / orchestrator) is responsible for confirming actor is not threatened.

**Take 20 eligibility:** Same pattern — `take_20=True` flag, caller asserts no-consequence condition. Clock advanced by 20 × `get_time_cost(skill_name)`.

**Cache hit/miss logic (retry_policy.py lines 163-181):**
- Cache miss (no entry) → fresh roll, clock advanced by `time_cost`, result stored.
- Cache hit, insufficient time elapsed OR `is_retry_allowed(skill) == False` → cached outcome returned, no roll, no time advance, `skill_check_cached` event emitted.
- Cache hit, sufficient time elapsed AND retry allowed → fresh roll (same as cache miss path).

**Per-skill retry table location:**
`aidm/core/exploration_time.py`, `RETRY_ALLOWED` dict (line 59) + `is_retry_allowed()` function (line 73).

**TimeAdvanceEvent emission:**
`retry_policy.py` emits `"time_advanced"` events using `Event(event_id=..., event_type="time_advanced", timestamp=..., payload={...})` consistent with `event_log.py` contract. `TimeAdvanceEvent` schema from `time.py` is confirmed correct but the event log uses flat `Event` objects.

**`state_hash()` exclusion:** Confirmed. `state_hash()` builds a manual dict with only `ruleset_version`, `entities`, `active_combat`. Both new fields are excluded by omission.

**Preflight assumptions validated:**
- `aidm/schemas/time.py` `GameClock(t_seconds=0, scale="exploration")` importable and correct — no changes needed
- `WorldState.state_hash()` safely excludes new fields (by omission from manual dict)
- No existing skill check call site in `play_loop.py` — added `execute_exploration_skill_check()` as new entry point
- `active_combat is None` is the correct outside-combat check (confirmed in WorldState definition)

**play_loop.py wiring (`execute_exploration_skill_check()` at end of file):**
- Initializes `game_clock` to `GameClock(t_seconds=0, scale="exploration")` if `world_state.game_clock is None`
- Calls `evaluate_check()` from `retry_policy.py`
- Re-sequences raw event IDs (evaluate_check uses 0-based internal IDs) to be monotonic from `next_event_id`
- Returns `(success, roll_used, updated_world_state, events)` tuple

**Gate test count:** 29 total (14 in `test_engine_retry_policy_gate.py` + 15 in `test_engine_retry_policy.py`) — both files pass 100%.

---

## Pass 2 — PM Summary (<=100 words)

Added `game_clock` and `skill_check_cache` to `WorldState` (excluded from `state_hash()`). Created `exploration_time.py` (time costs, retry rules, cache key) and `retry_policy.py` (`evaluate_check()` implementing Take 10, Take 20, cache-hit, cache-miss, per-skill retry rules). Added `execute_exploration_skill_check()` to `play_loop.py` as the canonical entry point — initializes clock, delegates to `evaluate_check()`, re-sequences event IDs. 29 gate tests pass (15 in new file + 14 from prior pass). Pre-existing `test_aoo_kernel.py::test_aoo_usage_resets_each_round` failure confirmed unrelated.

---

## Pass 3 — Retrospective

**Drift caught:** The dispatch specified `Event(event_id=..., event_type=..., payload=...)` as the constructor. Actual `Event` dataclass also requires `timestamp` as a non-optional positional field. Used `time.time()` for timestamps consistent with rest of codebase. This is a documentation drift in the WO, not a code defect.

**Pattern:** No existing skill check routing existed in `play_loop.py` — the play_loop is combat-centric. The correct integration seam was a new `execute_exploration_skill_check()` function (not replacing an existing call site). The WO's instruction "find where d20 is rolled for skill checks" presupposed an existing path that does not exist; actual skill check calls go through `skill_resolver.py` which is imported elsewhere (not from play_loop). Adding a new top-level entry point is the correct architectural choice — it follows the same pattern as `execute_turn()`.

**Recommendation:** The two test files (`test_engine_retry_policy.py` and `test_engine_retry_policy_gate.py`) have overlapping coverage. In a cleanup pass, consolidate into one canonical file. No functional issue.

---

## Radar

- Gate test count: 29 / 12 minimum — EXCEEDS MINIMUM
- Integration seams confirmed: state.py / time.py / event_log.py / play_loop.py — all 4 CONFIRMED
- `game_clock` field: present in WorldState, excluded from state_hash
- `skill_check_cache` key format: `actor_id|skill|target_id|method_tag`
- Take 10/Take 20 paths: implemented and tested
- Cache hit (no time elapsed) → cached result: implemented and tested
- Cache hit (sufficient time) → fresh roll: implemented and tested
- No-retry skill (knowledge/spellcraft) → permanently cached until state change: implemented and tested
- `time_advanced` events emitted on Take 10, Take 20, and normal roll: confirmed
- `execute_exploration_skill_check()` wired in play_loop.py: confirmed
- No stale DISPATCH-READY lifecycle: debrief filed
