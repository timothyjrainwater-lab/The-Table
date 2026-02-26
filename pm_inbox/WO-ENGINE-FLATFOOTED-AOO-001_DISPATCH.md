# Work Order: WO-ENGINE-FLATFOOTED-AOO-001
**Artifact ID:** WO-ENGINE-FLATFOOTED-AOO-001
**Batch:** H (Dispatch #17)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.136 (Flat-Footed), p.137 (Attacks of Opportunity)

---

## Summary

A flat-footed creature cannot make attacks of opportunity (PHB p.136). Currently `aoo.py` has no check for this condition — a flat-footed entity can freely make AoOs against provoking enemies, which is incorrect.

This finding was first logged as FINDING-ENGINE-FLATFOOTED-AOO-001 in Dispatch #12 (Batch B R1) and has been carried as OPEN since. It closes the gap cleanly: one guard in `aoo.py` before AoO eligibility is granted.

---

## Scope

**Files in scope:**
- `aidm/core/aoo.py` — add flat-footed check to AoO reactor eligibility

**Files read-only (verify, do not modify):**
- `aidm/schemas/conditions.py` — confirm FLAT_FOOTED condition name (confirmed live)
- `aidm/schemas/entity_fields.py` — confirm EF.CONDITIONS field name

**Files out of scope:**
- Flat-footed AC penalty (DEX to AC loss) — already implemented
- Uncanny Dodge (flat-footed immunity) — already implemented in prior batch
- Any other flat-footed penalties

---

## Assumptions to Validate (verify before writing)

1. Confirm `ConditionType.FLAT_FOOTED` is live in conditions.py. **Already confirmed live.**
2. Identify the exact point in `aoo.py` where reactor eligibility is checked — find the guard that determines whether an entity CAN make an AoO (e.g., has AoO uses remaining, is not defeated). Add the flat-footed check here.
3. Confirm that Uncanny Dodge (EF.EVASION or similar) grants flat-footed immunity — if so, a creature with Uncanny Dodge that is technically flat-footed should still be able to make AoOs. Verify whether the flat-footed condition is even applied to Uncanny Dodge holders. Document.
4. Confirm no pre-existing flat-footed AoO suppression in `aoo.py`.

---

## Implementation

### In `aoo.py` — in the reactor eligibility check:

```python
# Flat-footed entities cannot make AoOs (PHB p.136)
reactor_conditions = reactor_entity.get(EF.CONDITIONS, [])
if "flat_footed" in reactor_conditions:
    continue  # Skip this reactor — cannot make AoO while flat-footed
```

This guard should be placed in the loop that iterates over potential AoO reactors, before the AoO attack is resolved.

---

## Acceptance Criteria

Write gate file `tests/test_engine_flatfooted_aoo_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| FF-001 | Flat-footed entity in threatened square; enemy provokes AoO | No AoO from flat-footed entity |
| FF-002 | Non-flat-footed entity in threatened square; enemy provokes AoO | AoO triggers normally |
| FF-003 | Flat-footed entity; Combat Reflexes (multiple AoOs) | Still no AoO — flat-footed blocks regardless of Combat Reflexes |
| FF-004 | Entity loses flat-footed after first action; enemy provokes after | AoO triggers normally (flat-footed cleared) |
| FF-005 | Multiple reactors; one flat-footed, one not | Only non-flat-footed reactor makes AoO |
| FF-006 | Entity with Uncanny Dodge (not flat-footed per class feature); enemy provokes | AoO triggers (Uncanny Dodge means entity isn't flat-footed in the first place) |
| FF-007 | Flat-footed entity; zero AoO uses remaining anyway | No AoO; no crash |
| FF-008 | Entity with no CONDITIONS field | No crash; AoO triggers normally (treat absent as no conditions) |

8 tests total. Gate label: ENGINE-FLATFOOTED-AOO-001.

---

## Pass 3 Checklist

1. Confirm how flat-footed is cleared — does it clear after the first action in initiative, or does it persist? The engine's flat-footed clearing timing is important for this guard to work correctly. Document what was found.
2. Confirm whether Uncanny Dodge prevents the flat-footed condition from being applied at all (preferred) vs. applying the condition but flagging immunity separately. The cleanest PHB reading is that Uncanny Dodge holders are never flat-footed in the first place.
3. Note KERNEL-06 (Termination Doctrine) — the flat-footed state terminates at a precise point in the turn structure (after first action). Document that the engine's clearing logic matches this.
4. Close FINDING-ENGINE-FLATFOOTED-AOO-001 in Pass 3 — this WO was specifically dispatched to resolve that finding.

---

## Session Close Condition

- [ ] `git add aidm/core/aoo.py tests/test_engine_flatfooted_aoo_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 FF tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
