# DEBRIEF — WO-ENGINE-WILDSHAPE-HP-001
**Dispatched:** 2026-02-25
**Gate:** ENGINE-WILDSHAPE-HP 10/10 PASS
**Regression:** ENGINE-WILD-SHAPE 10/10 unchanged. No new failures.

---

## Pass 1 — Per-File Breakdown

### `aidm/core/wild_shape_resolver.py`

**Lines changed:** ~187–189 (3 lines replaced with 10 lines)

**Before:**
```python
new_hp_max = max(1, (new_con_mod + 1) * max(1, druid_level))
actor[EF.HP_MAX] = new_hp_max
actor[EF.HP_CURRENT] = min(actor.get(EF.HP_CURRENT, 1), new_hp_max)
```

**After:**
```python
# PHB p.37: HP_MAX adjusts by CON_mod delta × druid level (WO-ENGINE-WILDSHAPE-HP-001)
old_con_mod = saved.get("con_mod", 0)
saved_hp_max = saved.get("hp_max", 1)
current_hp = actor.get(EF.HP_CURRENT, saved_hp_max)
damage_taken = max(0, saved_hp_max - current_hp)
con_delta = new_con_mod - old_con_mod
new_hp_max = max(1, saved_hp_max + con_delta * druid_level)
new_hp_current = max(1, new_hp_max - damage_taken)
actor[EF.HP_MAX] = new_hp_max
actor[EF.HP_CURRENT] = new_hp_current
```

**Key finding:** The spec uses `saved_stats` as the variable name; the existing code uses `saved`. The formula was applied to the correct variable (`saved` was set earlier in the function and contains the same fields). No functional drift — naming difference only.

**Key finding:** `druid_level` was already computed earlier in `resolve_wild_shape()` via `EF.CLASS_LEVELS.get("druid", 1)`. The new HP block reads from the same variable without re-fetching. Correct.

**Open findings table:**

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| WHP-F1 | INFO | Spec variable name `saved_stats` vs code variable `saved` | No impact — correct field reads |

### `tests/test_engine_wildshape_hp_gate.py`

10 tests written covering: CON-unchanged case (wolf), CON+1 (black bear), CON+2 (crocodile), CON-lower (eagle), damage-taken preservation, HP_CURRENT floor, revert HP restoration, level scaling, regression event check, full cycle exact match.

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-WILDSHAPE-HP-001 delivered. Single file change: replaced 3-line placeholder HP formula with PHB p.37 CON-delta formula in `resolve_wild_shape()`. Old formula `(new_con_mod + 1) × druid_level` produced ~50% of correct HP for high-CON forms. New formula `saved_HP_MAX + con_delta × druid_level` preserves damage taken across transform and scales correctly with level. 10/10 new gate tests pass. 10/10 ENGINE-WILD-SHAPE regression clean. One naming drift (saved_stats vs saved) — no functional impact. No schema changes. No new EF constants.

---

## Pass 3 — Retrospective

**Drift caught:**
- None from spec. One naming difference (`saved_stats` vs `saved`) was pre-existing in the codebase and the builder correctly adapted to it without deviating from the formula.

**Patterns:**
- The WO spec noted `druid_level` as a read from `EF.CLASS_LEVELS` — the existing code already computed this earlier in the function. Specs should note when a value is already in scope to avoid redundant re-reads; in this case the builder correctly reused the in-scope variable.
- The `damage_taken` preservation pattern (save HP delta, apply to new pool) is the same pattern used in bardic music and dying resolver. It's becoming a standard idiom in this codebase and could be extracted as a utility if a third HP-adjustment resolver appears.

**Recommendations:**
- `WILD_SHAPE_FORMS` currently has no `hit_dice` field. The PHB-correct formula sidesteps this limitation cleanly. If full HD-based HP calculation is ever needed (e.g., for Polymorph), `hit_dice` will need to be added to the form schema. Flag as FINDING-WILDSHAPE-FORMS-001 if that WO arises.
- The old formula `(new_con_mod + 1) × druid_level` appears to have been written assuming `new_con_mod + 1` approximates HD count. This assumption breaks above level 7 for most forms. The PHB formula is structurally safer.
