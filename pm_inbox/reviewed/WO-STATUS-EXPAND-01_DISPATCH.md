# WO-STATUS-EXPAND-01 — Expanded Status Display

**Dispatch Authority:** PM (Opus)
**Priority:** Wave B — parallel dispatch (after Wave A completes)
**Risk:** LOW | **Effort:** Small | **Breaks:** 0 expected (additive)
**Depends on:** Wave A complete (especially WO-CONDFIX-01 for condition display)

---

## Target Lock

`show_status()` (play.py:343-351) only displays HP and position. Players can't see AC, conditions, saves, BAB, or ability modifiers — all of which exist in entity data.

**Goal:** Compact one-line-per-entity status showing HP, AC, BAB, and active conditions.

---

## Binary Decisions (Locked)

1. **One line per entity.** No multi-line character sheets (that's WO-CHARSHEET-CLI-01).
2. **Fields shown:** HP, AC, BAB, position, active conditions. Nothing else.
3. **Condition format:** `*condition*` appended after position. Multiple conditions comma-separated.
4. **Defeated entities still hidden** (existing behavior preserved).

---

## Contract Spec

### File Scope (2 files)

| File | Action | Lines |
|------|--------|-------|
| `play.py` | Modify `show_status()` (lines 343-351) | Add AC, BAB, conditions to display |
| `tests/test_play_cli.py` | Add ~5 new tests | Expanded status content assertions |

### Implementation Detail

**Current display (play.py:343-351):**
```
  Aldric                HP 28/28  (3,3)
```

**Target display:**
```
  Aldric                HP 28/28  AC 18  BAB +3  (3,3)
  Goblin Warrior        HP 5/5    AC 15  BAB +1  (3,5)  *prone, shaken*
```

**Modified `show_status()`:**
```python
def show_status(ws: WorldState) -> None:
    for eid in sorted(ws.entities):
        e = ws.entities[eid]
        if e.get(EF.DEFEATED, False):
            continue
        hp = e.get(EF.HP_CURRENT, "?")
        mx = e.get(EF.HP_MAX, "?")
        ac = e.get(EF.AC, "?")
        bab = e.get(EF.BAB, 0)
        pos = e.get(EF.POSITION, {})
        pos_str = f"({pos.get('x','?')},{pos.get('y','?')})"

        # Active conditions
        conditions = e.get(EF.CONDITIONS, {})
        if isinstance(conditions, dict) and conditions:
            cond_str = ", ".join(sorted(conditions.keys()))
            cond_display = f"  *{cond_str}*"
        else:
            cond_display = ""

        bab_str = f"+{bab}" if bab >= 0 else str(bab)
        print(f"  {e.get('name', eid):20s}  HP {hp}/{mx}  AC {ac}  BAB {bab_str}  {pos_str}{cond_display}")
```

### Frozen Contracts

None touched.

---

## Implementation Sequencing

1. Modify `show_status()` to include AC, BAB, and conditions
2. AC from `EF.AC`, BAB from `EF.BAB`, conditions from `EF.CONDITIONS` (dict keys)
3. Add tests:
   - `test_status_shows_ac` — "AC" appears in output
   - `test_status_shows_bab` — "BAB" appears in output
   - `test_status_shows_conditions` — condition name appears when entity has conditions
   - `test_status_no_conditions_no_asterisks` — clean output when no conditions
   - `test_status_still_hides_defeated` — defeated entities excluded
4. Run existing test `test_status_produces_output` — should still pass (still contains "HP")
5. Run full suite

---

## Acceptance Criteria

1. AC and BAB visible in status output
2. Conditions shown when present (e.g., `*prone*`)
3. No conditions clutter when none are active
4. Existing `test_status_produces_output` still passes
5. ~5 new tests pass

---

## Regression Watch

- `test_status_produces_output` asserts `"HP" in output` — still true, passes.
- Transcript tests may see wider status lines — but they compare full-run output between two identical runs, so both will have wider lines. Should pass.

---

## Agent Instructions

- Read `AGENT_ONBOARDING_CHECKLIST.md` and `AGENT_DEVELOPMENT_GUIDELINES.md` before starting
- This WO modifies ONLY `show_status()` in `play.py`. Do NOT add multi-line character sheets or detailed stat blocks.
- Conditions are stored as dict `{condition_id: {dict}}` after WO-CONDFIX-01. Use `conditions.keys()` for display names.
- Keep the display compact — one line per entity, no wrapping
- Run full suite before declaring completion
