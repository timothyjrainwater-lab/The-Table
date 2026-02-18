# WO-UI-DRIFT-GUARD — Add Missing UI-G5 Drift Guard Tests

**Lifecycle:** DISPATCH-READY
**Spec authority:** Operator directive (WO-UI-02 verdict feedback)
**Prerequisite WOs:** WO-UI-02 (Gate G — ACCEPTED at `7449bc5`)
**Branch:** master (from commit `7449bc5`)

---

## Scope

Add the 3 Operator-mandated drift guard tests that were specified in WO-UI-02 but not implemented. These are static-scan / import-scan tests only. **No production code changes.** The invariants likely hold today — this WO makes them enforced.

**In scope:**
1. Test: ObjectPositionUpdate is not registered as an event type in EventLog or replay_runner
2. Test: `aidm/ui/table_objects.py` does not import from `aidm/oracle/`, `aidm/core/event_log.py`, or `aidm/core/replay_runner.py`
3. Test: Zone constraint rejection code in `aidm/ui/table_objects.py` produces no user-facing explanation strings (static scan for tooltip/popover/error-message patterns)

**NOT in scope:**
- Any production code changes
- Any frontend changes
- Any new features

---

## Hard Stop Conditions

1. **If the invariants are already violated.** If any of the 3 tests would fail against the current codebase, stop and report the violation. Do not fix production code — report the specific violation to PM for triage.

---

## Contract Changes

### Change 1: 3 drift guard tests appended to Gate G
**Location:** `tests/test_ui_gate_g.py`
**What:** Append 3 tests to the existing Gate G test file under a new `UI-G5` section.

Tests:
1. **No canonical path** — Scan `aidm/core/event_log.py` and `aidm/core/replay_runner.py` for any reference to `ObjectPositionUpdate` or `TableObjectState`. Neither type should appear as a registered event type, reducer case, or import.

2. **No backflow imports** — Read the import statements of `aidm/ui/table_objects.py` (and any other `aidm/ui/*.py` files created by WO-UI-01 and WO-UI-02). Confirm none import from `aidm/oracle/`, `aidm/core/event_log`, `aidm/core/replay_runner`, `aidm/core/provenance`, `aidm/lens/`, or `aidm/immersion/`. The UI boundary layer must not depend on canonical state layers.

3. **No teaching strings** — Static scan of `aidm/ui/table_objects.py` for patterns: `tooltip`, `popover`, `error_message`, `explanation`, `reason`, `because`, `cannot`, `can't`, `invalid.*zone.*message`, or any string that would constitute a user-facing explanation of a zone rejection. Zone validation must return a boolean or None — not a message.

---

## Binary Decisions

1. **Tests go in the existing `test_ui_gate_g.py`.** Do not create a new test file. These are Gate G tests that should have been there from the start.

2. **Static scan approach.** Use `ast.parse` + import inspection or simple string scanning of the source file. Either approach is acceptable — builder's choice on technique.

3. **If a test fails, stop.** Do not modify production code to make it pass. Report the violation.

---

## Integration Seams

None. This WO touches only `tests/test_ui_gate_g.py`.

---

## Assumptions to Validate

1. **`aidm/ui/table_objects.py` exists and has no backflow imports.** Builder should confirm before writing tests.
2. **`ObjectPositionUpdate` does not appear in event_log.py or replay_runner.py.** Builder should grep before writing the test.

---

## Success Criteria (3 tests, all must pass)

1. ObjectPositionUpdate/TableObjectState not registered in EventLog or replay_runner (UI-G5)
2. `aidm/ui/` modules do not import from Oracle/EventLog/replay_runner/Lens/Immersion (UI-G5)
3. Zone validation code contains no user-facing explanation strings (UI-G5)

Regression: Gates A-G (121 tests total) must all still pass. 0 regressions allowed. Final count: 124 gate tests.

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-UI-DRIFT-GUARD.md` with 4 mandatory sections. 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-UI-DRIFT-GUARD to verdicts table (leave verdict blank; PM fills in).
3. `git add` test file + debrief + briefing.
4. Commit with descriptive message.
5. Add commit hash to debrief header.
6. Amend commit to include the hash.

**Debrief hash rule (Field Manual #19):** Commit first, read hash from `git log --oneline -1`, write to debrief, then amend.
