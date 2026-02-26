# WO-ENGINE-DIVINE-GRACE-001
## Wire Paladin Divine Grace — CHA Modifier to All Saves

**Priority:** HIGH
**Classification:** FEATURE
**Gate ID:** ENGINE-DIVINE-GRACE
**Minimum gate tests:** 8
**Source:** PHB p.44 — "Divine Grace: A paladin adds her Charisma modifier (if positive) to all saving throws."
**Dispatch:** ENGINE BATCH B

---

## Target Lock

Wire paladin's CHA modifier as a bonus to all three save types (Fort, Ref, Will) inside `get_save_bonus()` in `aidm/core/save_resolver.py`. Applies only when paladin_level ≥ 2 (PHB p.44 — gained at 2nd level). CHA mod of 0 or negative yields no bonus (PHB: "if positive").

---

## Binary Decisions

1. **Where does the bonus apply?** Inside `get_save_bonus()` — the same function where `feat_save_bonus` was added by WO-ENGINE-SAVE-FEATS-001. Append a `divine_grace_bonus` block after `feat_save_bonus`, before `total_bonus`. Applies to all three save types unconditionally (PHB p.44 does not restrict by save type).

2. **Paladin level threshold?** Level ≥ 2 (PHB p.44). Read from `entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)`.

3. **CHA mod floor?** Zero. If CHA mod ≤ 0, bonus is 0. PHB is explicit: "if positive."

4. **Stacking?** Additive with `feat_save_bonus` and `inspire_courage_bonus`. No conflict.

---

## Contract Spec

### `aidm/core/save_resolver.py` — `get_save_bonus()`

After the `feat_save_bonus` block (lines ~127–133), before `total_bonus` assignment, insert:

```python
# WO-ENGINE-DIVINE-GRACE-001: Paladin Divine Grace — CHA mod to all saves (PHB p.44)
# Gained at paladin level 2+. Bonus is 0 if CHA mod is not positive.
divine_grace_bonus = 0
_paladin_level = entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
if _paladin_level >= 2:
    _cha_mod = entity.get(EF.CHA_MOD, 0)
    if _cha_mod > 0:
        divine_grace_bonus = _cha_mod
```

Update `total_bonus`:
```python
total_bonus = base_save + ability_mod + condition_save_mod + inspire_courage_bonus + feat_save_bonus + divine_grace_bonus
```

### `tests/test_engine_divine_grace_gate.py` — NEW FILE

Minimum 8 gate tests, IDs DG-001 through DG-008:

| Test | Assertion |
|------|-----------|
| DG-001 | Paladin level 2, CHA 14 (mod +2): Fort save includes +2 |
| DG-002 | Paladin level 2, CHA 14 (mod +2): Ref save includes +2 |
| DG-003 | Paladin level 2, CHA 14 (mod +2): Will save includes +2 |
| DG-004 | Paladin level 2, CHA 10 (mod 0): no Divine Grace bonus on any save |
| DG-005 | Paladin level 2, CHA 8 (mod -1): no Divine Grace bonus (negative CHA mod ignored) |
| DG-006 | Paladin level 1: no Divine Grace bonus (not yet gained) |
| DG-007 | Non-paladin with CHA 18: no Divine Grace bonus |
| DG-008 | Paladin level 2, CHA 14: Divine Grace stacks correctly with Great Fortitude (+2 feat + +2 grace = +4 total on Fort) |

---

## Implementation Plan

1. Read `aidm/core/save_resolver.py` lines 60–140.
2. Locate the `feat_save_bonus` block (ends around line 133) and `total_bonus` assignment.
3. Insert `divine_grace_bonus` block between them.
4. Update `total_bonus` to include `divine_grace_bonus`.
5. Write `tests/test_engine_divine_grace_gate.py` with DG-001 through DG-008.
6. Run gate suite: `python -m pytest tests/test_engine_divine_grace_gate.py -v`.
7. Run regression: `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py`.
8. Confirm 0 new failures.

---

## Integration Seams

- **`aidm/core/save_resolver.py`** — `get_save_bonus()` only. No other file changes.
- **`aidm/schemas/entity_fields.py`** — `EF.CLASS_LEVELS`, `EF.CHA_MOD` already defined. No new constants needed.
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — not relevant for this WO (no events emitted from `get_save_bonus`).
- **Class feature pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)` — confirmed pattern per Architectural Invariants.

---

## Assumptions to Validate

1. Confirm `EF.CHA_MOD` is a defined constant in `entity_fields.py` (expected: yes — used by multiple resolvers).
2. Confirm `get_save_bonus()` is the sole save bonus calculation path (expected: yes — `resolve_save()` calls it at line ~272).
3. Confirm no existing `divine_grace` field or bonus anywhere in `save_resolver.py` (expected: grep returns nothing — verified pre-dispatch).

---

## Preflight

Before writing any code:
- `grep -n "divine_grace\|CHA_MOD\|cha_mod" aidm/core/save_resolver.py` — confirm no existing implementation
- `grep -n "CHA_MOD" aidm/schemas/entity_fields.py` — confirm constant exists
- `python -m pytest tests/test_engine_save_feats_gate.py -v` — confirm SF gate still clean (regression baseline for this file)

---

## Delivery Footer

- Files modified: `aidm/core/save_resolver.py`, `tests/test_engine_divine_grace_gate.py` (new)
- Gate: ENGINE-DIVINE-GRACE, minimum 8 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-DIVINE-GRACE-001.md`

### Debrief Template

```
# DEBRIEF — WO-ENGINE-DIVINE-GRACE-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** ENGINE-DIVINE-GRACE
**Date:** [DATE]

## Pass 1 — Per-File Breakdown
[Files modified, changes made, key findings]

## Pass 2 — PM Summary (≤100 words)
[Summary]

## Pass 3 — Retrospective
[Drift caught, patterns, open findings]

## Radar
[Gate results, confirmations]
```

### Audio Cue
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
