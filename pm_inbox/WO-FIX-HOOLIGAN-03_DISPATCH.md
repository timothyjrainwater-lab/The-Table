# WO-FIX-HOOLIGAN-03 — RV-001 Compound Narration Actor Attribution

**Issued:** 2026-02-23
**Authority:** FINDING-HOOLIGAN-03 MEDIUM OPEN. RV-001 false positive on compound actions.
**Gate:** Existing Gate K tests (67/67) must still pass. Target: fix false positive, add 3 regression tests.
**Blocked by:** Nothing.

---

## 1. Target Lock

RV-001 (`_check_rv001_hit_miss` in `aidm/narration/narration_validator.py`) scans the **entire narration text** for miss-language or hit-language keywords. In compound narrations — where multiple actors act in the same turn — language from one actor's action triggers a false positive on another actor's action.

**Example false positive:**
```
brief.action_type = "attack_hit"
text = "Kael swings his longsword, connecting with a slashing blow to the goblin's arm.
        Simultaneously, Seraphine's Shield spell activates, deflecting an incoming strike."
```
RV-001 flags FAIL because "deflect" (a miss-language word) appears anywhere in the text — even though it describes a different actor's spell, not Kael's hit.

**Root cause:** `_check_rv001_hit_miss()` scans `text` globally. No sentence or actor attribution.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Fix scope | Sentence-level scoping: check only the first sentence (or sentences) that describe the primary action | Brief has one `action_type` — the primary actor's action is narrated first; compound actions follow |
| 2 | Sentence split | Split on `. ` (period + space) and check only sentence[0] for RV-001 | Simple, testable, no NLP dependency |
| 3 | Fallback | If text has no period, check full text (current behavior — single-action turns unaffected) | Preserves existing behavior for single sentences |
| 4 | Scope marker | Do NOT try to parse actor names — attribution is structural (position), not semantic | Avoids fragile name extraction; sentence order is reliable |

---

## 3. Contract Spec

### 3.1 Current code (narration_validator.py lines 212-243)

```python
def _check_rv001_hit_miss(self, text: str, brief: Any) -> List[RuleViolation]:
    violations = []
    action = getattr(brief, "action_type", "")

    if "attack_hit" in action or "critical" in action:
        for pattern in _MISS_PATTERNS:
            match = pattern.search(text)   # ← scans full text
            ...
    elif "attack_miss" in action:
        for pattern in _HIT_PATTERNS:
            match = pattern.search(text)   # ← scans full text
            ...
    return violations
```

### 3.2 Fixed code

```python
def _check_rv001_hit_miss(self, text: str, brief: Any) -> List[RuleViolation]:
    """RV-001: Hit/Miss Consistency.

    Scopes check to the first sentence only (primary action narration).
    Compound narrations may contain language from secondary actors in
    later sentences — those must not trigger false positives.
    """
    violations = []
    action = getattr(brief, "action_type", "")

    # Scope to first sentence — primary action is narrated first.
    # If no period found, check full text (single-sentence narrations, unchanged behavior).
    first_sentence = text.split(". ")[0] if ". " in text else text

    if "attack_hit" in action or "critical" in action:
        for pattern in _MISS_PATTERNS:
            match = pattern.search(first_sentence)   # ← scoped
            if match:
                violations.append(RuleViolation(
                    rule_id="RV-001",
                    severity="FAIL",
                    detail=f"Hit narration contains miss-language: '{match.group()}'",
                ))
                break

    elif "attack_miss" in action:
        for pattern in _HIT_PATTERNS:
            match = pattern.search(first_sentence)   # ← scoped
            if match:
                violations.append(RuleViolation(
                    rule_id="RV-001",
                    severity="FAIL",
                    detail=f"Miss narration contains hit-language: '{match.group()}'",
                ))
                break

    return violations
```

---

## 4. Implementation Plan

1. **Read** `aidm/narration/narration_validator.py` — locate `_check_rv001_hit_miss()` exactly
2. **Apply** the fix: change both `pattern.search(text)` calls to `pattern.search(first_sentence)`, add the `first_sentence` extraction line above both blocks
3. **Run** existing Gate K tests: `pytest tests/test_narration_validator_gate_k.py -v` — all 67 must still pass
4. **Add** 3 regression tests to `tests/test_narration_validator_gate_k.py`:
   - `test_rv001_compound_hit_no_false_positive` — compound text with hit + secondary "deflect" does NOT flag
   - `test_rv001_compound_miss_no_false_positive` — compound text with miss + secondary "strike" does NOT flag
   - `test_rv001_single_sentence_still_catches_real_violation` — single sentence with wrong language still flags (regression guard)
5. **Run** `pytest tests/test_narration_validator_gate_k.py -v` — 70/70 pass (67 + 3 new)
6. **Run** `pytest tests/ --tb=no -q` — zero regressions

---

## 5. Deliverables Checklist

- [ ] `aidm/narration/narration_validator.py`: `_check_rv001_hit_miss()` scoped to first sentence
- [ ] Gate K: 70/70 (67 original + 3 new regression tests)
- [ ] FINDING-HOOLIGAN-03: RESOLVED
- [ ] Zero regressions vs 6,536 baseline

---

## 6. Integration Seams

- Change is confined to `_check_rv001_hit_miss()` only — two lines changed, one line added
- Do NOT modify `_MISS_PATTERNS` or `_HIT_PATTERNS` — the patterns are correct, only the scope is wrong
- Do NOT change any other RV-* check methods
- Gate K test file: add 3 tests, do not modify existing 67

---

## 7. Preflight

```bash
pytest tests/test_narration_validator_gate_k.py -v   # 70/70
pytest tests/ --tb=no -q                              # zero new failures
```

---

## 8. Debrief Focus

1. **Test K-68 through K-70** — paste the exact compound narration strings used in the 3 new tests. Confirm "deflect" (or equivalent) in sentence 2+ does not trigger.
2. **First-sentence boundary** — does `. ` (period-space) correctly split 3.5e combat narration in practice? Note any edge cases found.

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
