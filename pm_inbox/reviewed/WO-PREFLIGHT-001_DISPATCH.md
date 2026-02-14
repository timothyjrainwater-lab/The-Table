# WO-PREFLIGHT-001: Pre-Gate-Lift Inspection

**Authority:** PM (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Status:** READY for dispatch
**Scope:** Read-only inspection — NO code changes permitted
**Estimated file touches:** 0 (audit only)

---

## Target Lock

Before the Operator lifts the RED block, verify the codebase is in the state the tracking surfaces claim. This is a trust-but-verify pass. The builder runs the test suite, spot-checks critical fix WO commits, and confirms no regressions or orphaned state.

**Goal:** A single PASS/FAIL report with evidence. If PASS, Operator lifts the RED block. If FAIL, the report lists exactly what's wrong.

---

## Inspection Checklist

### 1. Test Suite Verification
- Run `python -m pytest tests/ -x -q` from project root
- Report: total passed, failed, skipped
- Expected: 5,532 passed, 0 failed, 24 skipped
- If any failures: list each failing test with the error message. STOP — do not proceed to other checks.

### 2. Tree Cleanliness
- Run `git status`
- Report: any modified tracked files, any unexpected untracked files
- Expected: clean tree (only known untracked: `docs/research/VOICE_*.md`, `pm_inbox/research/`)

### 3. Fix WO Spot-Check (sample 4 of 13)
For each commit below, verify the fix is present in the current HEAD code:

**a) WO-FIX-01 — STR grip multiplier (a386b81)**
- Read `aidm/core/attack_resolver.py`, find the grip multiplier calculation
- Confirm: two-handed weapons apply `int(str_modifier * 1.5)`, not flat `str_modifier`
- Read `aidm/core/full_attack_resolver.py`, confirm same logic exists there

**b) WO-FIX-03 — Prone/Helpless AC melee vs ranged (df3a958)**
- Read `aidm/core/attack_resolver.py`, find the condition AC modifier consumption
- Confirm: code differentiates `ac_modifier_melee` from `ac_modifier_ranged` based on `is_ranged` context flag
- Note: `is_ranged` is currently hardcoded `False` — this is known and expected

**c) WO-FIX-12 — XP table levels 11-20 (b52d8d8)**
- Read `aidm/schemas/leveling.py`, find the XP_TABLE
- Confirm: levels 11-20 have hardcoded entries (not computed)
- Spot-check 3 values: `(11, -1)` should be 500, `(15, 0)` should be base value, `(20, -1)` should be a graduated descent value

**d) WO-AMBFIX-001 — Opposed ties initiator wins (f517592)**
- Read `aidm/core/maneuver_resolver.py`, find the opposed check comparison
- Confirm: initiator wins on tie (`>=` not `>`)
- Read `aidm/core/terrain_resolver.py` (or wherever 5ft step threshold lives)
- Confirm: difficult terrain threshold is `>= 2` not `>= 4`

### 4. AMBIGUOUS Decision Log Completeness
- Read `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md`
- Confirm: all 28 verdicts have a non-blank DECISION field
- Confirm: Quick Reference table has a Decision column with all entries filled

### 5. Bone-Layer Checklist Gate Status
- Read `docs/verification/BONE_LAYER_CHECKLIST.md`
- Confirm: all 9 domains show COMPLETE
- Confirm: completion gate items are checked except RED block lift

### 6. PSD Consistency
- Read `PROJECT_STATE_DIGEST.md` header comment
- Confirm: no RED BLOCK language in the LAST UPDATED line
- Confirm: test count shows 5,532
- Confirm: Tier 0 bugs table shows INTEGRATED

### 7. Hygiene Test
- Run `python -m pytest tests/test_pm_inbox_hygiene.py -v`
- Report: pass/fail for each test class (PMIH-001 through PMIH-004)
- Expected: PMIH-001/002/003 PASS, PMIH-004 XFAIL (retrospective requirement — MEMOs without retrospectives already archived)

---

## Builder Protocol

- **READ-ONLY. Do NOT modify any files.**
- If a check fails, report it but do not fix it.
- If a spot-check value doesn't match, quote the actual value found.
- Run both test commands in full — do not skip or abbreviate output.

---

## Completion Report Format

```
PRE-GATE-LIFT INSPECTION REPORT

TEST SUITE: [PASS/FAIL] — [passed]/[failed]/[skipped]
TREE STATUS: [CLEAN/DIRTY] — [details if dirty]

SPOT-CHECKS:
  WO-FIX-01 (grip multiplier): [PASS/FAIL] — [evidence]
  WO-FIX-03 (prone/helpless AC): [PASS/FAIL] — [evidence]
  WO-FIX-12 (XP table): [PASS/FAIL] — [evidence]
  WO-AMBFIX-001 (ties + 5ft step): [PASS/FAIL] — [evidence]

DECISION LOG: [COMPLETE/INCOMPLETE] — [count of blank fields if any]
CHECKLIST GATE: [PASS/FAIL] — [details]
PSD CONSISTENCY: [PASS/FAIL] — [details]
HYGIENE TESTS: [PASS/FAIL] — [details]

OVERALL: [PASS/FAIL]
```

If OVERALL is PASS, the Operator can lift the RED block with confidence.
If OVERALL is FAIL, list every failed item for PM to triage.
