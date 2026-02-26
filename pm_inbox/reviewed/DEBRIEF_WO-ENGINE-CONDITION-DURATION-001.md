# DEBRIEF — WO-ENGINE-CONDITION-DURATION-001
## Condition Duration Tracking + Auto-Expiry
**Status:** ACCEPTED
**Date:** 2026-02-25
**Implemented by:** Builder (Claude Sonnet 4.6)

---

## Pass 1 — Context Dump

### Files Modified

| File | Lines Modified | Change |
|------|---------------|--------|
| `aidm/schemas/conditions.py` | 181–203 (ConditionInstance) | Added `duration_rounds: Optional[int] = None` field; updated `to_dict()` to emit key only when not None; updated `from_dict()` to read with default None |
| `aidm/schemas/conditions.py` | 341–358 (create_stunned_condition) | Added `duration_rounds=1` |
| `aidm/schemas/conditions.py` | 363–379 (create_dazed_condition) | Added `duration_rounds=1` |
| `aidm/schemas/conditions.py` | 485–502 (create_nauseated_condition) | Added `duration_rounds=1` |
| `aidm/core/conditions.py` | 15 (imports) | Added `Tuple` to typing import |
| `aidm/core/conditions.py` | 241–321 (new function) | Implemented `tick_conditions()` — ARCH-TICK-001 two-pass |
| `aidm/core/play_loop.py` | 47 (imports) | Extended to import `tick_conditions` alongside `get_condition_modifiers` |
| `aidm/core/play_loop.py` | 2976–2979 (end-of-round block) | Wired `tick_conditions()` call |

### Condition Factories Updated

| Factory | duration_rounds set | PHB Reference |
|---------|---------------------|---------------|
| `create_stunned_condition()` | `1` | PHB p.302: "stunned for 1 round" |
| `create_dazed_condition()` | `1` | PHB p.300: "dazed for 1 round" |
| `create_nauseated_condition()` | `1` | PHB p.301: "1 round per hit" |
| `create_prone_condition()` | `None` (permanent) | Stand-up action removes it |
| `create_grappled_condition()` | `None` (permanent) | Escape action removes it |
| `create_grappling_condition()` | `None` (permanent) | Escape action removes it |

### tick_conditions() Call Position

`aidm/core/play_loop.py` **line 2977** — inside the end-of-round block (`if current_position == last_actor_index:`), after the dying tick block (lines 2963–2974), before the `updated_state = WorldState(...)` final rebuild (line 2981).

### Gate Test Results

All 10 tests in `tests/test_engine_condition_duration_001_gate.py` pass:

| ID | Test | Result |
|----|------|--------|
| CD-001 | STUNNED expires after one tick | PASS |
| CD-002 | DAZED expires after one tick | PASS |
| CD-003 | NAUSEATED expires after one tick | PASS |
| CD-004 | PRONE (duration_rounds=None) survives tick | PASS |
| CD-005 | GRAPPLED (duration_rounds=None) survives tick | PASS |
| CD-006 | condition_expired event payload is correct | PASS |
| CD-007 | Two entities, same condition, tick independently | PASS |
| CD-008 | 2-round condition: present after tick 1, absent after tick 2 | PASS |
| CD-009 | Entity with no conditions — noop | PASS |
| CD-010 | ARCH-TICK-001: original WorldState not mutated | PASS |

### Regression Gate

| Baseline (before change, excluding gate file) | After change |
|-----------------------------------------------|-------------|
| 131 failed, 7703 passed, 44 skipped | 131 failed, 7713 passed, 44 skipped |

Failure count is identical. The 10 new gate tests added to the passed count. No regressions introduced.

Note: The instruction baseline of "28 failures" was from a prior session with a different ignore list. The actual reproducible baseline on the current test suite (same ignore list) is 131 pre-existing failures, all unrelated to this WO (UI layout, posture audit, weapon plumbing canary, WebSocket dead-verb — all pre-existing import errors or missing file references).

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-CONDITION-DURATION-001 is CLOSED. `ConditionInstance` now carries an optional `duration_rounds` field (None = permanent). A new `tick_conditions()` function in `aidm/core/conditions.py` applies ARCH-TICK-001 two-pass decrement-then-remove at end of round. It is wired into `play_loop.py` at line 2977 (end-of-round block, after dying tick). STUNNED, DAZED, NAUSEATED factories set `duration_rounds=1` per PHB. PRONE and GRAPPLED remain permanent. All 10 gate tests (CD-001–010) pass. No regression.

---

## Pass 3 — Retrospective

### Ambiguous Durations

- **TURNED**: WO specified `None` (permanent — removed by cleric rebuke or new day). Left as None. The condition has a 10-round narrative duration per PHB p.159, but removal is via explicit resolver action, not a countdown. Adding `duration_rounds=10` would require the DM-facing resolver to correctly start the timer; it was left None per WO scope.
- **ENTANGLED / CONFUSED**: These are applied by spell resolvers that are already tracked by `DurationTracker`. Setting `duration_rounds` would create a double-expiry gate. Left as `None` per the WO's Out of Scope section. If a non-spell source applies ENTANGLED in the future, the factory would need a separate path or the caller would pass `duration_rounds` directly.
- **BLINDED / DEAFENED**: The WO mentioned these could be 1 round from ability checks or spell duration otherwise. All current factories apply them from spell effects (tracked by DurationTracker). Left as `None` for now — safe because the DurationTracker handles expiry for all current use cases.

### ARCH-TICK-001 Complications

The two-pass pattern was straightforward. The key subtlety: Pass 1 mutates `cond_dict["duration_rounds"]` in-place on the deep-copied entities dict (for non-expiring timed conditions). This is safe because we deep-copy the entire `world_state.entities` at the start. Expiring conditions are only removed from `entities_copy` in Pass 2 after iteration is complete.

The test CD-010 validates this: it snapshots the original `ws_original.entities["e1"]` conditions dict before the call and confirms `"stunned"` is still in that snapshot after the call. Since we deep-copy at entry, the original WorldState is never mutated.

### Conditions Left as None with Explanation

| Condition | Reason left as None |
|-----------|---------------------|
| PRONE | PHB: standing up (move action) removes it. No fixed round count. |
| GRAPPLED / GRAPPLING | PHB: escape attempt (grapple check) removes it. No fixed round count. |
| HELPLESS | Arises from paralysis, unconsciousness, binding — removed by the removing event (e.g., spell end). |
| FLAT-FOOTED | Removed by first-action marker, not a timer. |
| STUNNED (via spell) | If applied by a spell tracked by DurationTracker, the tracker controls expiry. The factory's `duration_rounds=1` would still be correct for non-spell stuns. |
| TURNED | Narrative 10-round duration; removal is via active cleric judgment, not a mechanical counter. |
| ENTANGLED | Spell-tracked. DurationTracker handles expiry. |
| CONFUSED | Same as ENTANGLED. |
| BLINDED / DEAFENED | Current factories are spell-sourced. DurationTracker handles expiry. |
| PARALYZED | Spell duration varies by spell. DurationTracker handles it. |
| FATIGUED / EXHAUSTED | Removed by rest (8 hours), not a round counter. |
| SHAKEN / SICKENED | Duration varies by source (spell, fear effect). Not fixed at 1 round. |

---

## Radar

- **Regression gate:** PASS (131 before, 131 after — no new failures; 10 new passing tests added)
- **CD-001–010:** all PASS (10/10)
- **ConditionInstance.duration_rounds field added + serialized:** CONFIRMED (`aidm/schemas/conditions.py` lines 184–203)
- **tick_conditions() in aidm/core/conditions.py:** PRESENT (lines 244–321)
- **tick_conditions() wired in play_loop end-of-round:** CONFIRMED (line 2977)
- **STUNNED duration_rounds=1:** CONFIRMED (`create_stunned_condition()`, `aidm/schemas/conditions.py`)
- **DAZED duration_rounds=1:** CONFIRMED (`create_dazed_condition()`, `aidm/schemas/conditions.py`)
- **NAUSEATED duration_rounds=1:** CONFIRMED (`create_nauseated_condition()`, `aidm/schemas/conditions.py`)
- **Permanent conditions (PRONE, GRAPPLED) duration_rounds=None:** CONFIRMED (factories unchanged; `to_dict()` omits key when None)
- **ARCH-TICK-001 two-pass verified:** CONFIRMED (Pass 1 collects expiries into list; Pass 2 removes from entities_copy and emits events)
- **FINDING-ENGINE-CONDITION-DURATION-001:** CLOSED
