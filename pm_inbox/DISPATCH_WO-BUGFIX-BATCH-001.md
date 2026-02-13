# Instruction Packet: Bugfix Agent

**Work Order:** WO-BUGFIX-BATCH-001 (Cross-Cutting Bugfix Batch)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1
**Deliverable Type:** Code fixes + tests

---

## YOUR TASK

Fix four known issues identified in the post-landing audit (OPUS_AUDIT_POSTLAND_001.md). All are trivial — one-line to few-line fixes with clear specifications.

---

## Deliverable 1: STM Clear-on-Transition (Audit Risk #10)

**File:** `aidm/immersion/clarification_loop.py` (or wherever STMContext lives)

**Problem:** `STMContext` has no `clear()` or transition-triggered reset method. After a scene transition, "attack him" could resolve against an entity from the *previous* room.

**Fix:**
1. Find where `STMContext` is defined
2. Add a `clear()` method that resets all tracked referents
3. Wire `clear()` to scene transition events in scene_manager.py (call `stm.clear()` when `current_scene` changes)
4. Add test: after scene transition, previously-tracked entity names do NOT resolve

**Acceptance:**
- `STMContext.clear()` exists and resets state
- Scene transition triggers `clear()`
- Test proves pronoun carryover is blocked across transitions

---

## Deliverable 2: Clarification Loop Max Rounds (Audit Risk #4)

**File:** `aidm/immersion/clarification_loop.py`

**Problem:** No `max_rounds` enforcement. Contract §4.6 specifies max 3 rounds, then RETRACTED. Infinite clarification loops are theoretically possible.

**Fix:**
1. Add `max_rounds: int = 3` parameter to the clarification loop
2. Track round count
3. After `max_rounds` exceeded, return intent with status RETRACTED (not keep asking)
4. Add test: after 3 failed clarifications, intent is RETRACTED

**Acceptance:**
- Clarification loop respects `max_rounds`
- Default is 3
- Test proves RETRACTED status after limit

---

## Deliverable 3: AoO weapon_data Type Guard (Audit Risk #3)

**File:** `aidm/core/aoo.py` (around line 544)

**Problem:** `.get()` called on `weapon_data` without checking if it's actually a dict. If `weapon_data` is a string (e.g., `"longsword"`), `.get()` raises `AttributeError`.

**Fix:**
1. Find the `.get()` call on `weapon_data` near line 544
2. Add guard: `if weapon_data is None or not isinstance(weapon_data, dict): continue`
3. Add test: pass string weapon_data, verify no crash

**Acceptance:**
- String weapon_data does not crash
- None weapon_data does not crash
- Dict weapon_data still works as before
- Existing AoO tests still pass

---

## Deliverable 4: Intent Bridge Candidate Ordering (Delta D-01)

**File:** `aidm/interaction/intent_bridge.py`

**Problem:** `_resolve_entity_name()` returns candidates in dict insertion order, not lexicographic order. Contract §2.3 requires sorted candidates.

**Fix:**
1. Find `_resolve_entity_name()` (or equivalent entity resolution method)
2. Add `sorted()` call on candidate list before returning
3. Find the xfail test in `tests/spec/test_intent_bridge_contract_compliance.py` (TestCandidateOrdering::test_bridge_candidates_sorted_lexicographically)
4. Remove the `xfail` marker — the test should now pass

**Acceptance:**
- Candidates are returned in lexicographic order
- xfail test now passes (remove xfail marker)
- All existing intent bridge tests still pass

---

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `pm_inbox/OPUS_AUDIT_POSTLAND_001.md` | Audit findings (Risks #3, #4, #10, Delta D-01) |
| 2 | `aidm/immersion/clarification_loop.py` | Clarification loop implementation |
| 2 | `aidm/core/aoo.py` | AoO resolver |
| 2 | `aidm/interaction/intent_bridge.py` | Intent bridge |
| 2 | `tests/spec/test_intent_bridge_contract_compliance.py` | xfail test to fix |

## STOP CONDITIONS

- If `STMContext` does not exist as a class/module, STOP and report — the audit may have referenced a planned component.
- If removing the xfail causes other tests to fail, STOP and report.
- If the AoO `.get()` call is not at line 544 (file may have changed), search for all `.get()` calls on `weapon_data` in aoo.py and guard all of them.

## DELIVERY

- All fixes applied directly to source files
- All new tests pass
- Full test suite (`pytest --tb=short -q`) run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-BUGFIX-BATCH-001_completion.md`

## RULES

- Do NOT refactor surrounding code. Fix only the identified issues.
- Do NOT add docstrings or comments to code you didn't change.
- Follow existing code style in each file.
- All new tests must follow existing test patterns in their respective test files.

---

END OF INSTRUCTION PACKET
