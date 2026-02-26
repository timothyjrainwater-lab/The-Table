# Work Order: WO-ENGINE-DEFLECTION-BONUS-001
**Artifact ID:** WO-ENGINE-DEFLECTION-BONUS-001
**Batch:** G (Dispatch #16)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.136 (AC Bonus Types), p.221 (Ring of Protection)

---

## Summary

Deflection bonuses to AC come from magical sources — rings of protection, Shield of Faith spell, and similar effects (PHB p.136). Unlike armor or shield bonuses, deflection bonuses apply against all attacks including touch attacks. Multiple deflection bonuses do not stack — only the highest applies.

Currently no `EF.DEFLECTION_BONUS` field exists on entities and `attack_resolver.py` does not apply any deflection component to AC calculations. This means every entity that should have deflection AC (rings of protection, paladin spells, etc.) is getting full-contact from touch attacks that should be deflected.

This WO adds the field and the AC application. It is the field-level prerequisite for the ring of protection magic item WO (future batch).

---

## Scope

**Files in scope:**
- `aidm/schemas/entity_fields.py` — add `EF.DEFLECTION_BONUS` field constant
- `aidm/core/attack_resolver.py` — include deflection bonus in AC calculation against attacks

**Files read-only (verify, do not modify):**
- `aidm/core/spell_resolver.py` — confirm touch attack AC calculation pattern (touch attacks bypass armor/shield/natural armor but NOT deflection)
- `aidm/core/save_resolver.py` — N/A (deflection is AC only, not saves)

**Files out of scope:**
- Magic item equipping system — deflection will be set on entity directly by test setup; full equipping system is a later WO
- Deflection bonus to saves — not a D&D 3.5e mechanic (deflection only applies to AC)

---

## Assumptions to Validate (verify before writing)

1. Confirm `EF.DEFLECTION_BONUS` does NOT already exist in `entity_fields.py`. **Verify before writing.**
2. Confirm how `attack_resolver.py` currently computes target AC — find the exact line(s) where AC is read from entity and used in the `roll >= target_ac` check.
3. Confirm how touch attack AC is computed — touch attacks bypass armor/shield/natural armor, but deflection STILL APPLIES. Verify the touch attack path applies deflection.
4. Confirm no pre-existing deflection field under a different name (e.g., `deflection_ac`, `deflect_bonus`).
5. Confirm stacking rule: only highest deflection bonus applies. If the entity already has `EF.DEFLECTION_BONUS = 2` and a new effect would grant +1, the value stays at 2. Document how this is enforced (runtime max, not additive).

---

## Implementation

### 1. `aidm/schemas/entity_fields.py` — add field:

```python
# --- Deflection Bonus to AC (WO-ENGINE-DEFLECTION-BONUS-001) ---
DEFLECTION_BONUS = "deflection_bonus"
# int: deflection bonus to AC from magical sources (rings of protection, Shield of Faith, etc.)
# PHB p.136: deflection bonuses DO apply vs touch attacks; armor/shield/natural do NOT.
# Multiple deflection bonuses do NOT stack — only highest applies.
# 0 = no deflection bonus (default).
```

### 2. `aidm/core/attack_resolver.py` — in AC calculation:

```python
# Deflection bonus applies to all attacks (including touch attacks) — PHB p.136
_deflection = target.get(EF.DEFLECTION_BONUS, 0)
effective_ac = base_ac + _deflection
```

**For touch attacks specifically:** Verify the touch attack path also adds deflection but strips armor/shield/natural armor. If touch attacks currently just use `base_ac`, that may already exclude armor. Document what's found.

---

## Acceptance Criteria

Write gate file `tests/test_engine_deflection_bonus_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| DB-001 | Entity with DEFLECTION_BONUS=2; attack roll vs AC 12 | Effective AC = 14; attack that hits AC 12 misses |
| DB-002 | Entity with DEFLECTION_BONUS=0; attack | No deflection added; standard AC applies |
| DB-003 | Entity with no DEFLECTION_BONUS field (absent) | No crash; standard AC applies (treat as 0) |
| DB-004 | Touch attack vs entity with DEFLECTION_BONUS=2 | Deflection still applies; touch attack must beat AC + 2 |
| DB-005 | Touch attack vs entity with DEFLECTION_BONUS=0 | No deflection; touch attack uses base touch AC |
| DB-006 | Entity DEFLECTION_BONUS=2; ranged attack | Deflection applies to ranged attacks as well |
| DB-007 | Entity DEFLECTION_BONUS=4 vs attack roll 14; base AC=12 | Miss (14 < 16); confirm deflection correct |
| DB-008 | Stacking: entity already has DEFLECTION_BONUS=3; new effect would set +2 | Value stays 3 (highest wins); no double-add |

8 tests total. Gate label: ENGINE-DEFLECTION-BONUS-001.

---

## Pass 3 Checklist

1. Confirm touch attack AC path — document exactly which AC components apply vs. touch attacks in the current engine. Deflection applies; armor/shield/natural do not. If the current touch attack path doesn't separate these, flag as FINDING.
2. Note the stacking rule enforcement pattern — if tests set `EF.DEFLECTION_BONUS` directly, stacking is the caller's responsibility. Document that a future ring-of-protection equipping WO will need to enforce max() at equip time.
3. Flag KERNEL-14 (Effect Composition) — deflection is the first AC-modifying effect type that stacks differently from armor bonus (non-stacking vs. armor which can only come from one source anyway). The AC composition model needs a full audit at some point.
4. Note any other bonus types missing from the AC model: dodge (partially tracked), sacred, profane, luck — log as FINDING for future batch.

---

## Session Close Condition

- [ ] `git add aidm/schemas/entity_fields.py aidm/core/attack_resolver.py tests/test_engine_deflection_bonus_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 DB tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
