# WO-FIX-GRAMMAR-01 — Condition Display Consistency Fix

**Issued:** 2026-02-23
**Authority:** FINDING-GRAMMAR-01 (open since playtest), PM dispatch
**Gate:** None — zero-gate fix. Regression guard only: existing Gate K (67/67) must stay green.
**Blocked by:** Nothing.
**Track:** Hotfix — parallel-safe with all active WOs.

---

## 1. Target Lock

Fix the cosmetic inconsistency in `play.py` where condition names are formatted differently from spell names. Conditions use `replace('_', ' ')` (no title-case), spells use `.title()`. The result: conditions display as `"prone"` while spells display as `"Magic Missile"`. Standardize conditions to `.replace('_', ' ').title()` so both render with capital first letters.

This is FINDING-GRAMMAR-01. One line change. No logic impact. Close the finding.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Formatting target | `.replace('_', ' ').title()` | Matches spell display convention; consistent with existing pattern |
| 2 | Scope | Condition display only (`play.py` line 641 area) | Do not touch spell formatting — it already uses `.title()` |
| 3 | Test requirement | 1 regression test (before/after output assertion) | Evidence of fix; zero-gate WO still needs a test |
| 4 | Gate impact | None — Gate K must stay 67/67 | Confirm in preflight |

---

## 3. Contract Spec

### 3.1 The Bug

In `play.py` around line 641, condition names are displayed without title-casing:

```python
# Current (broken) — displays "prone", "frightened", "stunned"
condition_str = condition.replace('_', ' ')
```

Spell names elsewhere use `.title()`:

```python
# Existing spell display — displays "Magic Missile", "Cure Light Wounds"
spell_str = spell_name.replace('_', ' ').title()
```

### 3.2 The Fix

```python
# Fixed — displays "Prone", "Frightened", "Stunned"
condition_str = condition.replace('_', ' ').title()
```

**Exact change:** append `.title()` to the condition formatting expression. One character cluster added.

### 3.3 Test Requirement

Add to `tests/test_narration_gate_k.py` (or equivalent Gate K test file — append, do not create new file):

```python
class TestGrammar01ConditionDisplay:
    """GRAMMAR-01: Condition names display with title-case."""

    def test_condition_title_case(self):
        """Conditions format as 'Prone' not 'prone'."""
        # Import the formatting function or test via output string
        # Exact assertion depends on how condition_str is surfaced —
        # if it's a helper function, test it directly.
        # If it's inline, test the output of the affected code path.
        result = format_condition("attack_hit")   # adjust to actual call
        assert result[0].isupper(), f"Condition should be title-cased, got: {result!r}"

    def test_condition_underscore_replaced(self):
        """Underscores replaced with spaces in conditions."""
        result = format_condition("spell_resistance")
        assert "_" not in result
        assert result == "Spell Resistance"
```

**Note to builder:** If there is no extractable `format_condition()` helper, test via the output string of the affected call path. The assertion is: `condition.replace('_', ' ').title()` produces `"Prone"` from `"prone"`, `"Spell Resistance"` from `"spell_resistance"`.

---

## 4. Implementation Plan

1. Read `aidm/core/play.py` around line 641. Locate the exact condition formatting expression.
2. Change `condition.replace('_', ' ')` → `condition.replace('_', ' ').title()` (or equivalent if expression differs).
3. Verify no other condition display sites in `play.py` use the old pattern — search for `replace('_', ' ')` and check each hit.
4. Append 1–2 regression tests to existing Gate K test file. Do not create a new test file.
5. Run preflight: `pytest tests/test_narration_gate_k.py -v` — must be 67/67 + new tests PASS.
6. Confirm no other gate files regressed.

---

## 5. Deliverables Checklist

- [ ] `play.py` line 641 area: `.title()` appended to condition formatting
- [ ] No other condition display sites left using old pattern
- [ ] 1–2 regression tests appended to Gate K test file
- [ ] Gate K still passes (67+N/67+N)
- [ ] FINDING-GRAMMAR-01 marked RESOLVED in debrief

---

## 6. Integration Seams

- **Only file modified:** `aidm/core/play.py` (one expression)
- **Test file:** append only to existing Gate K test file — no new test files
- **No other modules touched:** this is a display-only change; no data model, no engine logic
- **Gate K guard:** `pytest tests/test_narration_gate_k.py` must stay green

---

## 7. Preflight

```bash
pytest tests/test_narration_gate_k.py -v
pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

Both must exit 0.

---

## 8. Debrief Focus

1. **Exact line changed** — paste before/after.
2. **Search result** — how many other `replace('_', ' ')` hits exist in `play.py`? Were any of them condition display sites that also needed the fix?
3. **Gate K count** — confirm 67+N/67+N.

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
