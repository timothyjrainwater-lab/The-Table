# Completion Report: WO-BUGFIX-BATCH-001

**Work Order:** WO-BUGFIX-BATCH-001 (Cross-Cutting Bugfix Batch)
**Completed By:** Opus
**Date:** 2026-02-13
**Status:** COMPLETE — All 4 deliverables fixed + tested

---

## Full Test Suite Results

```
4745 passed, 7 failed, 11 skipped (98.26s)
```

The 7 failures are **pre-existing** in `tests/immersion/test_chatterbox_tts.py` — caused by `ModuleNotFoundError: No module named 'torch.nn'` (PyTorch environment issue, unrelated to this WO).

All 179 tests in directly-affected files pass (0 regressions).

---

## Deliverable 1: STM Clear-on-Transition (Audit Risk #10)

**Files Modified:**
- `aidm/immersion/voice_intent_parser.py` — Added `STMContext.clear()` method
- `aidm/lens/scene_manager.py` — Added optional `stm` parameter to `__init__()`, wired `stm.clear()` on successful scene transition
- `tests/test_scene_manager.py` — Added `test_stm_cleared_on_scene_transition`

**What Changed:**
- `STMContext.clear()` resets all 6 attributes: `last_target`, `last_location`, `last_action`, `last_weapon`, `last_spell`, `history`
- `SceneManager.__init__()` now accepts `stm: Optional[Any] = None`
- `SceneManager.transition_scene()` calls `stm.clear()` after successful transition (before return)
- Backward compatible: `stm=None` (default) means no clearing — all existing SceneManager usage unaffected

**Test:** Proves that after scene transition, `last_target`, `last_weapon`, `last_action`, `last_spell`, `last_location`, and `history` are all reset to None/empty.

---

## Deliverable 2: Clarification Loop Max Rounds (Audit Risk #4)

**Files Modified:**
- `aidm/immersion/clarification_loop.py` — Added `ClarificationLoop` class and `ClarificationResult` dataclass

**Files Created:**
- `tests/immersion/test_clarification_loop.py` — 9 tests

**What Changed:**
- `ClarificationLoop(max_rounds=3)` tracks round count across `attempt()` calls
- After `max_rounds` exceeded, `attempt()` returns `ClarificationResult(retracted=True)`
- `reset()` method clears round count for reuse
- Existing `ClarificationEngine` is unchanged — `ClarificationLoop` wraps it

**Tests (9):**
- Default max_rounds is 3
- Custom max_rounds
- Resolved on first attempt
- Clarification returned within limit
- RETRACTED after 3 failed rounds (4th attempt)
- RETRACTED after max_rounds=1
- Resolved before max_rounds (no retraction)
- Reset clears round count
- Round count tracks attempts

---

## Deliverable 3: AoO weapon_data Type Guard (Audit Risk #3)

**Files Modified:**
- `aidm/core/aoo.py` — Changed `weapon_data is None` guard to `weapon_data is None or not isinstance(weapon_data, dict)`
- `tests/test_aoo_kernel.py` — Added 3 tests

**What Changed:**
- Single-line fix at the existing `weapon_data` guard (line ~538)
- Before: `if weapon_data is None: continue`
- After: `if weapon_data is None or not isinstance(weapon_data, dict): continue`
- String weapon_data (e.g. `"longsword"`) no longer causes `AttributeError` on `.get()`

**Tests (3):**
- `test_string_weapon_data_does_not_crash` — String weapon_data → no crash, no attack resolved
- `test_none_weapon_data_does_not_crash` — Missing weapon field → no crash, no attack resolved
- `test_dict_weapon_data_still_works` — Dict weapon_data → AoO triggers and resolves normally

---

## Deliverable 4: Intent Bridge Candidate Ordering (Delta D-01)

**Files Modified:**
- `aidm/interaction/intent_bridge.py` — Added `sorted()` on all candidate lists in `_resolve_entity_name()`
- `tests/spec/test_intent_bridge_contract_compliance.py` — Removed `@pytest.mark.xfail` from `test_bridge_candidates_sorted_lexicographically`

**What Changed:**
- 4 candidate lists in `_resolve_entity_name()` now sorted by `key=lambda n: n.lower()`:
  1. Empty name → available targets list
  2. Multiple exact matches → candidates tuple
  3. Multiple partial matches → candidates tuple
  4. No matches → available targets list
- xfail marker removed — test now passes

**Test:** `TestCandidateOrdering::test_bridge_candidates_sorted_lexicographically` — previously xfail (strict), now passes.

---

## Summary

| # | Deliverable | Risk/Delta | Fix | Tests Added |
|---|------------|-----------|-----|-------------|
| 1 | STM Clear-on-Transition | Risk #10 | `clear()` method + wired to scene transition | 1 |
| 2 | Clarification Loop Max Rounds | Risk #4 | `ClarificationLoop` class with `max_rounds=3` | 9 |
| 3 | AoO weapon_data Type Guard | Risk #3 | `isinstance(weapon_data, dict)` guard | 3 |
| 4 | Intent Bridge Candidate Ordering | Delta D-01 | `sorted()` on candidates + xfail removal | 0 (existing test un-xfailed) |

**Total new tests:** 13
**All existing tests:** Unbroken (179/179 in affected files)
