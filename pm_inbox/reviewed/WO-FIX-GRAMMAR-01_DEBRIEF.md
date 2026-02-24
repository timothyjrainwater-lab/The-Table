# WO-FIX-GRAMMAR-01 — Debrief

**Status:** COMPLETE
**Date:** 2026-02-23
**Finding:** FINDING-GRAMMAR-01 → **RESOLVED**

---

## 1. Exact Line Changed

**File:** `play.py` line 647

**Before:**
```python
lines.append(f"  [RESOLVE] {condition.replace('_', ' ')}: {duration} rounds remaining")
```

**After:**
```python
lines.append(f"  [RESOLVE] {condition.replace('_', ' ').title()}: {duration} rounds remaining")
```

One `.title()` call appended. No logic impact.

---

## 2. Search Result — All `replace('_', ' ')` Hits in play.py

Only **1 hit** found. It is the fixed line (line 647). No other condition display sites used the old pattern.

Line 641 was already correct: `condition.replace("_", " ").title()` (spell-sourced conditions, pre-existing).

---

## 3. Gate K Count

**Gate K: 69/69 passed** (67 original + 2 new GRAMMAR-01 regression tests).

New tests appended to `tests/test_unknown_gate_k.py`:
- `TestGrammar01ConditionDisplay::test_condition_title_case` — PASS
- `TestGrammar01ConditionDisplay::test_condition_underscore_replaced` — PASS

---

## 4. Full Suite

Full suite (with standard ignores): **836 passed, 1 failed (pre-existing), 12 skipped**.

The 1 failure (`test_boundary_law.py::TestBL001_SparkMustNotImportCore::test_no_spark_to_lens_imports`) is a pre-existing `dm_persona.py` import boundary violation — not introduced by this WO and not within scope.

---

## 5. Deliverables

- [x] `play.py` line 647: `.title()` appended to condition formatting
- [x] No other condition display sites left using old pattern (0 other hits)
- [x] 2 regression tests appended to Gate K test file (no new files created)
- [x] Gate K: 69/69 green
- [x] FINDING-GRAMMAR-01: RESOLVED
