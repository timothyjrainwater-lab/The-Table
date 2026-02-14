# WO-VERIFY-G — Domain G: Initiative & Turn Structure Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Parallel wave 1
**Risk:** LOW | **Effort:** Small | **Breaks:** 0 (read-only audit)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-D, B, C, E, F, H, I
**Lifecycle:** NEW

---

## Target Lock

Verify every formula in the initiative system and action economy budget against SRD 3.5e. 10 formulas across 3 files.

**Goal:** Verification record for every formula. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain G for formula list.
3. For each formula, read code, look up SRD 3.5e, produce verification record.
4. Use d20srd.org — "Combat > Initiative", "Combat > Actions in Combat".
5. Write all records to `docs/verification/DOMAIN_G_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain G row.
7. Add entry to Iteration Log.
8. Commit: `verify: Domain G — Initiative & Turn Structure (10 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs.**

---

## Formulas To Verify

### aidm/core/initiative.py (3 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 72 | `d20 + dex_mod + misc_mod` | SRD: Combat > Initiative |
| 75 | `total = d20 + dex + misc` | SRD: Combat > Initiative |
| 104 | Sort key: `(-total, -dex_mod, actor_id)` | SRD: Combat > Initiative Ties |

**Key checks:**
- Initiative = d20 + DEX mod + misc. SRD confirms. Verify "misc" only includes Improved Initiative (+4) and not other unintended sources.
- Tie-breaking: SRD says ties are broken by higher DEX modifier. If still tied, roll off (or GM decides). Code uses actor_id as final tiebreaker (lexicographic). Verify this is an acceptable deterministic substitute for the roll-off.

### play.py — ActionBudget (6 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 71-86 | Action cost table (14 action types) | SRD: Combat > Actions in Combat |
| 92-96 | Budget defaults: 1 standard, 1 move, 1 swift, no full-round | SRD: Combat > Action Types |
| 110 | Standard → move trade (can use standard as second move) | SRD: Combat > Move Actions |
| 112 | Full-round requires: standard + move + not already moved | SRD: Combat > Full-Round Actions |

**Key checks:**
- Action cost mapping: Verify each action type's cost matches SRD. Attack=standard, cast=standard (usually), move=move, full attack=full-round. Check all 14 entries.
- Standard→move trade: SRD says "In some situations, you may trade actions for other actions (e.g., you can take a move action instead of a standard action)." Verify the trade rules are correct.
- Full-round prerequisite: SRD says a full-round action consumes both your standard and move action. You cannot full-attack if you've already moved (except 5-foot step). Verify.
- Swift action: SRD says one swift action per turn. Verify.

### aidm/core/combat_controller.py (1 formula)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 249 | `round = previous + 1` | Basic round increment |

---

## Output Format

Write `docs/verification/DOMAIN_G_VERIFICATION.md` using the standard structure.
