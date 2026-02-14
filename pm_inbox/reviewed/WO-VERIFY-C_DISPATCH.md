# WO-VERIFY-C — Domain C: Saves & Spells Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Parallel wave 1
**Risk:** LOW | **Effort:** Small-Medium | **Breaks:** 0 (read-only audit)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-D, B, E, F, G, H, I
**Lifecycle:** NEW

---

## Target Lock

Verify every formula in the saving throw and spell resolution systems against SRD 3.5e. 21 formulas across 2 files.

**Goal:** Verification record for every formula. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain C for formula list.
3. For each formula, read the code, look up SRD 3.5e, produce a verification record.
4. Use d20srd.org — "Saving Throws", "Magic Overview", "Combat: Saving Throws".
5. Write all records to `docs/verification/DOMAIN_C_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain C row.
7. Add entry to Iteration Log.
8. Commit: `verify: Domain C — Saves & Spells (21 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs. Record them and move on.**

---

## Formulas To Verify

### aidm/core/save_resolver.py (10 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 86-100 | Fort→CON_MOD, Ref→DEX_MOD, Will→WIS_MOD | SRD: Saving Throws |
| 112 | `total_save = base + ability_mod + condition_mod` | SRD: Saving Throws |
| 159-162 | SR check: `d20 + caster_level >= SR` | SRD: Spell Resistance |
| 252-253 | `save_total = d20 + save_bonus` | SRD: Saving Throws |
| 259 | Natural 1 always fails | SRD: Saving Throws |
| 261 | Natural 20 always succeeds | SRD: Saving Throws |
| 264 | `success = total >= dc` | SRD: Saving Throws |
| 335 | `final_damage = int(base * multiplier)` | SRD: Saving Throws (half damage) |
| 340 | `hp_after = hp_before - final_damage` | HP application |

**Key checks:**
- SR check: SRD says `d20 + caster level >= SR`. Verify the code uses caster level, not spell level or other modifier.
- Save bonus: SRD specifies `base save + ability mod + magic mod + misc mod`. Code has `base + ability + condition`. Verify whether "condition" captures all applicable modifiers or if there are missing terms.
- Half damage: `int()` truncation — verify rounding direction. SRD doesn't specify rounding for half damage explicitly; standard d20 rounding is "round down" which `int()` does for positive numbers.

### aidm/core/spell_resolver.py (11 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 383-389 | `spell_dc = 10 + ability_mod + spell_level` | SRD: Magic Overview > DCs |
| 747 | `base_roll = randint(1, 20)` | SRD: Saving Throws |
| 749 | `total = base_roll + save_bonus + cover_bonus` | SRD: Saving Throws |
| 753-758 | Nat 20 auto-success, nat 1 auto-fail, else total >= dc | SRD: Saving Throws |
| 816 | `damage // 2` (save for half) | SRD: Saving Throws |
| 818 | `damage = 0` (save negates) | SRD: Saving Throws |
| 871 | `caster_level_bonus = min(caster_level, spell_level * 5)` | SRD: Cure spells |
| 872 | `total += caster_level_bonus` | SRD: Cure spells |
| 876 | `actual_healing = min(total, max_hp - current_hp)` | Cannot exceed max HP |
| 1035 | `dc = 10 + damage_taken` (concentration check) | SRD: Concentration |

**Key checks:**
- Spell DC: SRD says `10 + spell level + relevant ability modifier`. Code has `dc_base + spell_level` where dc_base = `10 + ability_mod`. Verify the construction is equivalent.
- Cure spell caster level cap: SRD says "1d8+1/level (max +5)" for Cure Light Wounds. The formula `min(caster_level, spell_level * 5)` produces max +5 for level 1 spells, max +10 for level 2, etc. Verify this scaling is correct per SRD for each cure spell level.
- Concentration DC: SRD says DC = 10 + damage dealt + spell level for casting defensively. Code has `10 + damage_taken` without spell level. Check if this is for the "damaged while casting" case (DC = 10 + damage) vs "casting defensively" case (DC = 15 + spell level).
- Cover bonus to Reflex saves: Verify that cover applies to Reflex saves per SRD.

---

## Output Format

Write `docs/verification/DOMAIN_C_VERIFICATION.md` using the standard structure.
