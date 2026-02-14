# WO-VERIFY-H — Domain H: Skill System Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Parallel wave 1
**Risk:** LOW | **Effort:** Small | **Breaks:** 0 (read-only audit)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-D, B, C, E, F, G, I

---

## Target Lock

Verify every formula in the skill check resolution system against SRD 3.5e. 6 formulas in 1 file.

**Goal:** Verification record for every formula. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain H for formula list.
3. For each formula, read code, look up SRD 3.5e, produce verification record.
4. Use d20srd.org — "Using Skills".
5. Write all records to `docs/verification/DOMAIN_H_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain H row.
7. Add entry to Iteration Log.
8. Commit: `verify: Domain H — Skill System (6 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs.**

---

## Formulas To Verify

### aidm/core/skill_resolver.py (6 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 161 | `d20_roll = randint(1, 20)` | SRD: Using Skills |
| 170 | `total = d20 + ability_mod + ranks + circumstance - acp` | SRD: Skill Checks |
| 173 | `success = total >= dc` | SRD: Skill Checks |
| 233-234 | Opposed check: both sides roll d20 | SRD: Opposed Checks |
| 241-249 | Opposed totals: `d20 + ability + ranks + circumstance - acp` for each | SRD: Opposed Checks |
| 254 | `actor_wins = actor_total >= opponent_total` (ties to active checker) | SRD: Opposed Checks |

**Key checks:**
- Skill check formula: SRD says `1d20 + skill modifier` where skill modifier = `ability mod + ranks + misc modifiers`. Code separates out ACP as a subtraction. Verify ACP only applies to skills with `armor_check_penalty=True`.
- Opposed checks tie-breaking: SRD says ties on opposed checks mean neither side succeeds, OR the side with the higher modifier wins. Code gives ties to the active checker. Flag this as AMBIGUOUS with both SRD interpretations.
- Circumstance modifier: Verify this is a valid SRD modifier type for skill checks.

---

## Output Format

Write `docs/verification/DOMAIN_H_VERIFICATION.md` using the standard structure.
