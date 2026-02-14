# WO-VERIFY-D — Domain D: Conditions & Modifiers Verification

**Dispatch Authority:** PM (Opus)
**Priority:** FIRST — all other domains may depend on condition modifier correctness
**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 (read-only audit, no code changes)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-B, C, E, F, G, H, I

---

## Target Lock

Verify every numeric modifier value and aggregation formula in the condition system against SRD 3.5e. This domain has 57 formulas across 2 files. The condition modifiers are consumed by every combat resolver — if these numbers are wrong, everything downstream is wrong.

**Goal:** A verification record for every formula. Verdicts: CORRECT, WRONG, AMBIGUOUS, or UNCITED. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for the verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain D section for the formula list.
3. For each formula below, read the code at the specified line, look up the SRD 3.5e rule, and produce a verification record.
4. Use d20srd.org or equivalent SRD reference. The SRD is the IP-clean version of the rules — use it, not PHB page numbers (those are cited for convenience but the SRD text is authoritative).
5. Write all verification records to `docs/verification/DOMAIN_D_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain D row with counts.
7. Add an entry to the Iteration Log table.
8. Commit with message: `verify: Domain D — Conditions & Modifiers (57 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs. Record them and move on.**

---

## Files To Verify

### File 1: `aidm/schemas/conditions.py` — 42 formulas (condition modifier values)

Every condition factory function creates a `ConditionModifiers` dataclass with specific numeric values. Verify each value against SRD 3.5e Conditions Summary table.

| Line | Condition | Field | Value | SRD Reference |
|------|-----------|-------|-------|---------------|
| 208 | Prone | ac_modifier | -4 | SRD Conditions: Prone |
| 209 | Prone | attack_modifier | -4 | SRD Conditions: Prone |
| 210 | Prone | standing_triggers_aoo | True | SRD Conditions: Prone |
| 232 | Flat-Footed | loses_dex_to_ac | True | SRD Combat: Flat-Footed |
| 254 | Grappled | dex_modifier | -4 | SRD Conditions: Grappled |
| 255 | Grappled | movement_prohibited | True | SRD Conditions: Grappled |
| 281 | Helpless | ac_modifier | -4 | SRD Conditions: Helpless |
| 282 | Helpless | loses_dex_to_ac | True | SRD Conditions: Helpless |
| 283 | Helpless | auto_hit_if_helpless | True | SRD Conditions: Helpless |
| 284 | Helpless | actions_prohibited | True | SRD Conditions: Helpless |
| 306 | Stunned | ac_modifier | -2 | SRD Conditions: Stunned |
| 307 | Stunned | loses_dex_to_ac | True | SRD Conditions: Stunned |
| 308 | Stunned | actions_prohibited | True | SRD Conditions: Stunned |
| 328 | Dazed | actions_prohibited | True | SRD Conditions: Dazed |
| 352 | Shaken | attack_modifier | -2 | SRD Conditions: Shaken |
| 353 | Shaken | fort_save_modifier | -2 | SRD Conditions: Shaken |
| 354 | Shaken | ref_save_modifier | -2 | SRD Conditions: Shaken |
| 355 | Shaken | will_save_modifier | -2 | SRD Conditions: Shaken |
| 380 | Sickened | attack_modifier | -2 | SRD Conditions: Sickened |
| 381 | Sickened | damage_modifier | -2 | SRD Conditions: Sickened |
| 382 | Sickened | fort_save_modifier | -2 | SRD Conditions: Sickened |
| 383 | Sickened | ref_save_modifier | -2 | SRD Conditions: Sickened |
| 384 | Sickened | will_save_modifier | -2 | SRD Conditions: Sickened |
| 406 | Frightened | attack_modifier | -2 | SRD Conditions: Frightened |
| 407 | Frightened | fort_save_modifier | -2 | SRD Conditions: Frightened |
| 408 | Frightened | ref_save_modifier | -2 | SRD Conditions: Frightened |
| 409 | Frightened | will_save_modifier | -2 | SRD Conditions: Frightened |
| 428 | Panicked | fort_save_modifier | -2 | SRD Conditions: Panicked |
| 429 | Panicked | ref_save_modifier | -2 | SRD Conditions: Panicked |
| 430 | Panicked | will_save_modifier | -2 | SRD Conditions: Panicked |
| 431 | Panicked | loses_dex_to_ac | True | SRD Conditions: Panicked |
| 450 | Nauseated | actions_prohibited | True | SRD Conditions: Nauseated |
| 467 | Fatigued | attack_modifier | -1 | SRD Conditions: Fatigued |
| 468 | Fatigued | dex_modifier | -2 | SRD Conditions: Fatigued |
| 485 | Exhausted | attack_modifier | -3 | SRD Conditions: Exhausted |
| 486 | Exhausted | dex_modifier | -6 | SRD Conditions: Exhausted |
| 504 | Paralyzed | ac_modifier | -4 | SRD Conditions: Paralyzed |
| 505 | Paralyzed | loses_dex_to_ac | True | SRD Conditions: Paralyzed |
| 506 | Paralyzed | auto_hit_if_helpless | True | SRD Conditions: Paralyzed |
| 507 | Paralyzed | actions_prohibited | True | SRD Conditions: Paralyzed |
| 508 | Paralyzed | movement_prohibited | True | SRD Conditions: Paralyzed |
| 541-545 | Unconscious | ac_modifier=-4, loses_dex, auto_hit, actions_prohibited, movement_prohibited | SRD Conditions: Unconscious |

**IMPORTANT edge cases to check:**
- Prone: SRD says -4 AC vs melee, +4 AC vs ranged. Code stores -4 flat. Does the code handle the melee/ranged split anywhere? (Known BUG-3 — confirm and record)
- Helpless: SRD says melee attacks get +4 (effectively -4 AC), ranged get no bonus. Code stores -4 flat. (Known BUG-4 — confirm and record)
- Fatigued: SRD says -2 STR, -2 DEX. Code translates -2 STR as -1 attack_modifier. Verify the STR→attack derivation is correct (STR mod changes by 1 per 2 points of STR change).
- Exhausted: SRD says -6 STR, -6 DEX. Code has attack_modifier=-3. Same derivation check.
- Stunned: SRD says -2 AC. Verify this is correct (SRD: "loses Dex bonus to AC" + "-2 penalty to AC"). The -2 is a separate penalty on top of losing Dex.
- Grappled: SRD says -4 DEX. Verify this is the full modifier or if the condition has additional effects not captured.
- Shaken/Frightened: Both have -2 to attacks, saves, skill checks, ability checks. Code captures attacks and saves but NOT skill checks or ability checks. Record if missing.
- Sickened: Same — -2 penalty on attacks, damage, saves, skill checks, ability checks. Verify all captured.

### File 2: `aidm/core/conditions.py` — 15 formulas (aggregation logic)

The `get_condition_modifiers()` function aggregates all active conditions into a single `ConditionModifiers` result. Verify:

| Line | Formula | SRD Rule |
|------|---------|----------|
| 65-71 | Seven zero-init accumulators (ac, attack, damage, dex, fort, ref, will) | N/A (init) |
| 92-98 | Additive stacking: each condition's modifier is added to running total | SRD: Most condition penalties stack. Verify which types stack and which don't |
| 100-104 | Boolean OR: movement_prohibited, actions_prohibited, standing_triggers_aoo, auto_hit, loses_dex | SRD: Any one of these conditions being active should trigger the effect |

**CRITICAL stacking question:** SRD 3.5e has specific rules about modifier stacking. Same-type bonuses generally don't stack (only highest applies). Same-type penalties DO stack. The code uses simple addition for everything. Verify whether this is correct per SRD stacking rules, or if the aggregation logic needs to distinguish bonus types.

---

## Output Format

Write `docs/verification/DOMAIN_D_VERIFICATION.md` with this structure:

```markdown
# Domain D Verification — Conditions & Modifiers
**Verified by:** [agent model]
**Date:** [date]
**Formulas verified:** 57
**Summary:** X CORRECT, Y WRONG, Z AMBIGUOUS, W UNCITED

## Verification Records

### aidm/schemas/conditions.py

FORMULA ID: D-conditions-schema-208
FILE: aidm/schemas/conditions.py
LINE: 208
CODE: ac_modifier=-4
RULE SOURCE: SRD Conditions: Prone
EXPECTED: [what SRD says]
ACTUAL: ac_modifier=-4
VERDICT: [CORRECT/WRONG/AMBIGUOUS]
NOTES: [if applicable]

[...repeat for all 42 formulas...]

### aidm/core/conditions.py

[...repeat for all 15 formulas...]

## Bug List

[If any WRONG verdicts, list them with fix descriptions]

## Ambiguity Register

[If any AMBIGUOUS verdicts, document the ambiguity and the chosen interpretation]
```
