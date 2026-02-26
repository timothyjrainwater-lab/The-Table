# Work Order: WO-ENGINE-EVASION-ARMOR-001
**Artifact ID:** WO-ENGINE-EVASION-ARMOR-001
**Batch:** E (Dispatch #14 — Chisel)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.50 (Rogue Evasion), p.56 (Improved Evasion), p.41 (Monk Evasion)

---

## Summary

Evasion and Improved Evasion are live in `spell_resolver.py` (WO-ENGINE-EVASION-001, Batch B R1). The entity fields (`EF.EVASION`, `EF.IMPROVED_EVASION`) and damage-reduction logic are implemented and tested.

One restriction was explicitly deferred at the time: **Evasion does not function when the character is wearing medium or heavy armor.** The blocker was that no armor type field existed on the entity. `EF.ARMOR_TYPE` ("none" | "light" | "medium" | "heavy") landed in Batch D via WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001.

This WO closes that deferred gap.

**PHB rule (p.50):** "A rogue can avoid even magical and unusual attacks with great agility. [...] This ability can only be used if the rogue is wearing light armor or no armor."

Same restriction applies to Monk Evasion (PHB p.41).

---

## Scope

**Files in scope:**
- `aidm/core/spell_resolver.py` — add armor check before applying Evasion/Improved Evasion zero-damage

**Files read-only (verify, do not modify):**
- `aidm/schemas/entity_fields.py` — confirm `EF.ARMOR_TYPE` values are "none" | "light" | "medium" | "heavy"
- `aidm/chargen/builder.py` — confirm `EF.ARMOR_TYPE` is set at chargen for relevant classes

**Files out of scope:**
- `aidm/chargen/builder.py` — do not modify; chargen already handles armor field assignment
- All test files except the new gate file for this WO

---

## Assumptions to Validate (verify before writing)

1. Confirm `EF.EVASION` / `EF.IMPROVED_EVASION` check in `spell_resolver.py` is at approximately lines 889–902 (two sites: saved=True and saved=False branches).
2. Confirm `EF.ARMOR_TYPE` field is present on entities and set to one of {"none", "light", "medium", "heavy"}.
3. Confirm the evasion block currently reads only `EF.EVASION` / `EF.IMPROVED_EVASION` with no armor guard — that is the gap.
4. Confirm there is no pre-existing test that already covers this restriction (search `tests/` for `evasion` + `armor`).

---

## Implementation

### In `spell_resolver.py`:

At both evasion check sites, add a guard: evasion only applies if `armor_type` is `"none"` or `"light"`.

**Site 1 — saved=True, Evasion (line ~892):**
```python
# Before:
if _target_raw.get(EF.EVASION, False) or _target_raw.get(EF.IMPROVED_EVASION, False):
    total = 0

# After:
_armor = _target_raw.get(EF.ARMOR_TYPE, "none")
_evasion_active = _armor in ("none", "light")
if _evasion_active and (_target_raw.get(EF.EVASION, False) or _target_raw.get(EF.IMPROVED_EVASION, False)):
    total = 0
```

**Site 2 — saved=False, Improved Evasion (line ~901):**
```python
# Before:
if _target_raw.get(EF.IMPROVED_EVASION, False):
    total = total // 2

# After:
_armor = _target_raw.get(EF.ARMOR_TYPE, "none")
if _armor in ("none", "light") and _target_raw.get(EF.IMPROVED_EVASION, False):
    total = total // 2
```

These are the only two changes required. No new imports, no schema changes, no new fields.

---

## Acceptance Criteria

Write a gate test file `tests/test_engine_evasion_armor_001_gate.py` with the following cases:

| ID | Scenario | Expected |
|----|----------|----------|
| EA-001 | Rogue with Evasion, no armor — hits AoE, saves Reflex | 0 damage |
| EA-002 | Rogue with Evasion, light armor — hits AoE, saves Reflex | 0 damage |
| EA-003 | Rogue with Evasion, medium armor — hits AoE, saves Reflex | half damage (evasion suppressed) |
| EA-004 | Rogue with Evasion, heavy armor — hits AoE, saves Reflex | half damage (evasion suppressed) |
| EA-005 | Monk with Evasion, no armor — saves Reflex | 0 damage |
| EA-006 | Monk with Evasion, medium armor — saves Reflex | half damage (evasion suppressed) |
| EA-007 | Rogue with Improved Evasion, no armor — fails Reflex | half damage |
| EA-008 | Rogue with Improved Evasion, medium armor — fails Reflex | full damage (improved evasion suppressed) |

8 tests total. Gate label: ENGINE-EVASION-ARMOR-001.

---

## Pass 3 Checklist

Builder must report:
1. Confirm both evasion sites were found at expected lines (or document actual lines).
2. Confirm `EF.ARMOR_TYPE` defaulting — what happens if the field is absent (should default to "none", which means evasion is active — correct for creatures with no armor set).
3. Flag if any other resolver (AoO, save_resolver, etc.) has an evasion check that was missed — this WO only scoped `spell_resolver.py`.
4. Note any creature data entries that have `EF.EVASION = True` but no `EF.ARMOR_TYPE` set — these will default to "none" (evasion active), which is correct but note it.

---

## Session Close Condition

- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_evasion_armor_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 EA tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/`
