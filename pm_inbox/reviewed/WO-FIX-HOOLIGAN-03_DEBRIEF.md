# WO-FIX-HOOLIGAN-03 — Debrief

**WO:** WO-FIX-HOOLIGAN-03 — RV-001 Compound Narration Actor Attribution
**Completed:** 2026-02-23
**Status:** RESOLVED — FINDING-HOOLIGAN-03 closed

---

## 1. Deliverables

| Item | Status |
|---|---|
| `aidm/narration/narration_validator.py`: `_check_rv001_hit_miss()` scoped to first sentence | DONE |
| 3 regression tests added to `tests/test_narration_validator.py` | DONE |
| FINDING-HOOLIGAN-03 | RESOLVED |
| Zero regressions vs baseline | CONFIRMED |

---

## 2. Change Summary

**File:** `aidm/narration/narration_validator.py`, `_check_rv001_hit_miss()` (lines 212–243)

One line added, two lines changed:

```python
# Before (both blocks scanned full text):
match = pattern.search(text)

# After (both blocks scoped to first sentence):
first_sentence = text.split(". ")[0] if ". " in text else text
match = pattern.search(first_sentence)
```

No other methods touched. `_MISS_PATTERNS` and `_HIT_PATTERNS` unchanged.

---

## 3. Test Results

| Suite | Before | After |
|---|---|---|
| `test_narration_validator.py` | 46/46 | 49/49 |
| Full regression | 6,699 passed, 11 pre-existing failures | 6,702 passed, 11 pre-existing failures |
| New failures | — | 0 |

---

## 4. Debrief Focus (per §8)

### 4.1 K-68 through K-70 — Compound narration strings used

**K-68** (`test_rv001_compound_hit_no_false_positive`):
```
"kael swings his longsword, connecting with a slashing blow to the goblin's arm. "
"simultaneously, seraphine's shield spell activates, deflecting an incoming strike."
```
`action_type = "attack_hit"`. Word "deflecting" appears in sentence 2 (secondary actor's spell).
Result before fix: would flag FAIL. Result after fix: PASS — sentence 2 not scanned.

**K-69** (`test_rv001_compound_miss_no_false_positive`):
```
"aldric's sword sweeps wide, missing the orc completely. "
"the ground trembles as torgar's warhammer strikes the flagstone nearby."
```
`action_type = "attack_miss"`. Word "strikes" (HIT_KEYWORDS) appears in sentence 2 (secondary actor).
Result before fix: would flag FAIL. Result after fix: PASS — sentence 2 not scanned.

**K-70** (`test_rv001_single_sentence_still_catches_real_violation`):
```
"aldric's sword is deflected by the goblin's armor without connecting."
```
`action_type = "attack_hit"`. Word "deflected" (MISS_KEYWORDS) in sentence 1, no period.
Fallback: no `. ` found → `first_sentence = text` (full text). Still flags FAIL. Regression guard confirmed.

### 4.2 First-sentence boundary — `. ` in practice

The `. ` split (period + space) works correctly for 3.5e combat narration. Compound turns follow a consistent structural pattern: primary action first, secondary actions in subsequent sentences separated by `. `.

One edge case noted: multi-word miss keywords with internal spaces (e.g. `"goes wide"`, `"bites into"`, `"finds its mark"`) are compiled with `re.escape()` rather than word-boundary anchors — this is pre-existing behavior in `_compile_keywords()`, unrelated to this fix.

Abbreviations like `"vs. "` could theoretically cause a spurious split, but this pattern does not appear in idiomatic 3.5e combat narration output.

---

## 5. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
