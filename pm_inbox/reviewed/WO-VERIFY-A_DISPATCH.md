# WO-VERIFY-A — Domain A: Attack Resolution Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Wave 2 — dispatched AFTER WO-VERIFY-D (Domain D) completes
**Risk:** MEDIUM | **Effort:** Large (53 formulas, complex formula chains) | **Breaks:** 0 (read-only audit)
**Depends on:** WO-VERIFY-D must complete first (condition modifiers feed into attack resolution)
**Parallel with:** Nothing — this is the final, most critical domain
**Lifecycle:** NEW

---

## Target Lock

Verify every formula in the attack resolution system — single attacks, full attacks, sneak attack, damage reduction, flanking, concealment, ranged combat, reach, and cover resolution — against SRD 3.5e. 53 formulas across 9 files. This domain has the highest known bug density (BUG-1, BUG-2, BUG-3, BUG-4 all live here or feed from here).

**Goal:** Verification record for every formula. No code changes. Confirm known bugs and find any new ones.

---

## Prerequisite

Before starting this WO, read the Domain D verification results at `docs/verification/DOMAIN_D_VERIFICATION.md`. Any WRONG verdicts in condition modifiers may cascade into attack resolution. Note any relevant findings.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain A for formula list.
3. Read `docs/verification/DOMAIN_D_VERIFICATION.md` for condition modifier findings.
4. For each formula, read code, look up SRD 3.5e, produce verification record.
5. Use d20srd.org — "Combat > Attack Roll", "Combat > Damage", "Combat > Critical Hits", "Combat > Cover", "Special Attacks > Sneak Attack".
6. Write all records to `docs/verification/DOMAIN_A_VERIFICATION.md`.
7. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain A row.
8. Add entry to Iteration Log.
9. Commit: `verify: Domain A — Attack Resolution (53 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs. Record them and move on.**

---

## Known Bugs To Confirm

These were found in the Action Economy Audit. Confirm each during verification:

| Bug ID | Location | Description |
|--------|----------|-------------|
| BUG-1 | attack_resolver.py:363, full_attack_resolver.py:298 | Two-handed weapons should apply `int(STR * 1.5)` damage, code uses flat STR |
| BUG-2 | full_attack_resolver.py:546-595 | Full attack loop doesn't break on target defeat, all iteratives execute |
| BUG-3 | Condition→attack pipeline | Prone AC modifier is -4 flat, should be -4 melee / +4 ranged |
| BUG-4 | Condition→attack pipeline | Helpless AC modifier is -4 flat, should be -4 melee / 0 ranged |

---

## Formulas To Verify

### aidm/core/attack_resolver.py (18 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 113 | `roll_dice()` = multiple `randint(1, die_size)` | SRD: Damage |
| 241 | `base_ac = target.get(EF.AC, 10)` — default 10 | SRD: Armor Class |
| 243 | `target_ac = base_ac + condition_ac + cover_ac` | SRD: AC Modifiers |
| 247 | `d20 = randint(1, 20)` | SRD: Attack Roll |
| 249-256 | `attack_bonus = intent.attack_bonus + condition_mod + mounted + elevation + feat_mod + flanking` | SRD: Attack Roll Modifiers |
| 257 | `total = d20 + attack_bonus` | SRD: Attack Roll |
| 260 | `is_threat = d20 >= weapon.critical_range` | SRD: Critical Hits |
| 267 | Natural 1 always misses | SRD: Attack Roll |
| 269 | Natural 20 always hits | SRD: Attack Roll |
| 272 | `hit = total >= target_ac` | SRD: Attack Roll |
| 278 | Confirmation roll: `d20` | SRD: Critical Hits |
| 280 | `confirmation_total = d20 + attack_bonus` | SRD: Critical Hits |
| 282 | `is_critical = confirmation >= target_ac` | SRD: Critical Hits |
| 355 | `str_modifier = attacker.get(EF.STR_MOD, 0)` | SRD: Damage |
| 363 | `base_damage = dice + weapon_bonus + str_mod` (BUG-1: no 1.5x for two-handed) | SRD: Damage |
| 365 | `modified_damage = base + condition_damage + feat_damage` | SRD: Damage Modifiers |
| 369 | `crit_damage = max(0, modified * crit_multiplier)` | SRD: Critical Hits |
| 371 | `normal_damage = max(0, modified)` | SRD: Damage (minimum 0) |
| 382 | `total += sneak_attack` (not multiplied on crit) | SRD: Sneak Attack |
| 389 | `final = apply_dr(total, dr_amount)` | SRD: Damage Reduction |
| 424 | `hp_after = hp_before - final` | HP application |
| 442 | `defeated = hp_after <= 0` | SRD: Hit Points |

**Key checks:**
- STR to damage: SRD says melee = STR mod, two-handed = STR × 1.5 (round down), off-hand = STR × 0.5. Code uses flat STR. Known BUG-1.
- Ranged damage: SRD says no STR to damage for ranged (except composite bows, thrown weapons, slings). Code adds STR to all damage. Potential additional bug.
- Critical damage: SRD says multiply ALL damage EXCEPT bonus dice (sneak attack, flaming, etc.). Code multiplies `base_damage_with_modifiers` then adds SA. Verify the multiplication scope is correct — does it include condition modifiers and feat modifiers in the multiplied portion?
- Damage minimum: SRD says minimum 1 point of damage on a successful hit (before DR). Code uses `max(0, ...)`. This may be wrong — verify whether the SRD minimum-1 rule applies.
- Natural 20/1: SRD confirms 20 always hits, 1 always misses. But verify: does a natural 20 automatically confirm the crit, or just auto-hit? (SRD: auto-hit only, confirmation still required.)

### aidm/core/full_attack_resolver.py (8 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 97-121 | `calculate_iterative_attacks()`: [BAB, BAB-5, BAB-10, ...] while >= 1 | SRD: Full Attack |
| 297-299 | Damage formula (same as single attack) | SRD: Damage |
| 303 | Critical damage formula (same as single attack) | SRD: Critical Hits |
| 499 | `target_ac` computation (same as single attack) | SRD: AC |
| 548-555 | Iterative attack bonus with all modifiers | SRD: Full Attack |
| 595 | `hp_after = hp_before - total_damage` (accumulated, not per-attack) | BUG-2 |

**Key checks:**
- Iterative attacks: SRD says at BAB +6, get second attack at BAB-5. At +11, third at BAB-10. At +16, fourth at BAB-15. Maximum 4 attacks. Verify the loop stops at 4.
- BUG-2 confirmation: Damage accumulates across all attacks, defeat check happens once at end. SRD implies each attack is resolved sequentially with immediate HP application.
- All single-attack formula checks apply to the per-attack computation in full attack.

### aidm/core/sneak_attack.py (3 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 55 | `MAX_RANGE = 30` ft | SRD: Rogue > Sneak Attack |
| 82 | `num_dice = (rogue_level + 1) // 2` | SRD: Rogue > Sneak Attack |
| 202 | `rolls = [randint(1, 6) for _ in range(num_dice)]` — d6 per die | SRD: Rogue > Sneak Attack |

**Key checks:**
- Dice progression: Level 1 = 1d6, Level 3 = 2d6, Level 5 = 3d6, etc. Formula `(level + 1) // 2` gives: L1=1, L2=1, L3=2, L4=2, L5=3. Verify this matches SRD (every odd rogue level).
- Range limit: SRD says sneak attack works with ranged weapons within 30ft. Verify.

### aidm/core/damage_reduction.py (6 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 45-53 | Energy and physical type sets | SRD: Damage Reduction |
| 99 | `effective_magic = magic_flag or enhancement >= 1` | SRD: DR/magic |
| 156 | Epic bypass: `enhancement >= 6` | SRD: Epic DR (DMG) |
| 182 | `reduced = min(dr, damage)` — can't reduce below 0 | SRD: DR |
| 187 | `final = damage - reduced` | SRD: DR |

**Key checks:**
- DR bypass: SRD says +1 or better weapons bypass DR/magic. Enhancement >= 1 qualifies. Verify.
- Epic bypass at +6: This is a DMG rule. Verify the threshold.
- DR can't make damage negative: Verify `min(dr, damage)` prevents this.

### aidm/core/flanking.py (3 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 44 | `FLANKING_BONUS = 2` | SRD: Combat > Flanking |
| 49 | `MIN_FLANKING_ANGLE = 135.0` degrees | SRD: Combat > Flanking |
| 119-130 | Angle calculation via dot product | Geometry |

**Key checks:**
- SRD flanking: +2 to attack. Verify this is an untyped bonus (not morale, insight, etc.) — matters for stacking.
- 135° minimum angle: SRD says flanking requires allies on opposite sides. The geometric definition of "opposite sides" is commonly interpreted as 135°+ angle through target. Verify this is an accepted interpretation.

### aidm/core/concealment.py (2 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 67 | `miss_chance = min(best, 100)` cap at 100% | SRD: Concealment |
| 90 | `d100 <= miss_chance` means miss | SRD: Concealment |

**Key checks:**
- SRD concealment: 20% miss chance (standard), 50% (total). Roll percentile — if result is within miss chance, attack misses. Verify the comparison direction is correct (low roll = miss, not high roll = miss).

### aidm/core/ranged_resolver.py (4 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 27 | `PENALTY_PER_INCREMENT = -2` | SRD: Ranged Attacks |
| 29-30 | `MAX_INCREMENTS = 10 (projectile), 5 (thrown)` | SRD: Ranged Attacks |
| 159 | `increment = ((distance - 1) // range_ft) + 1` | SRD: Range Increments |
| 200 | `penalty = (increment - 1) * -2` | SRD: Range Penalties |

**Key checks:**
- Range penalty: SRD says -2 per increment after the first. First increment = no penalty. Verify `(increment - 1) * -2` produces 0 for first increment, -2 for second, etc.
- Max increments: SRD says 10 for projectile (bow), 5 for thrown. Verify.

### aidm/core/reach_resolver.py (5 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 26-36 | Reach by size (tall): Fine=0 through Colossal=30 | SRD: Reach |
| 39-49 | Reach by size (long): differs for Large+ | SRD: Reach |
| 116-118 | Chebyshev distance for reach measurement | Grid geometry |
| 195 | `reach_squares = reach_ft // 5` | Grid conversion |
| 234 | `threatened = 1 <= dist <= reach_squares` | SRD: Threatened Squares |

**Key checks:**
- Reach tables: SRD has different reach for Tall vs Long creatures. Large Tall = 10ft, Large Long = 5ft. Huge Tall = 15ft, Huge Long = 10ft. Verify all entries.
- Threatened squares: SRD says a creature threatens all squares it can reach with a melee weapon. Minimum distance 1 (can't threaten own square). Verify.
- Chebyshev vs actual grid distance: Reach in d20 uses the grid distance (counting squares), not Euclidean. Verify Chebyshev is the correct metric for reach (it is — unlike movement which uses the 5/10/5 rule, reach uses simple square counting).

### aidm/core/cover_resolver.py (4 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 96 | 0-4 lines blocked = No Cover (ac=0, ref=0) | SRD: Cover |
| 97 | 5-8 lines blocked = Half Cover (ac=2, ref=1) | SRD: Cover |
| 98 | 9-12 lines blocked = Three-Quarters (ac=5, ref=2) | SRD: Cover |
| 99 | 13-16 lines blocked = Total Cover | SRD: Cover |

**Key checks:**
- Half cover: SRD says +4 AC, +2 Reflex. Code says ac=2, ref=1. THIS MAY BE WRONG — verify carefully.
- Three-quarters cover: SRD says +7 AC, +3 Reflex (improved cover). Code says ac=5, ref=2. VERIFY.
- The line-blocked thresholds are an implementation detail (corner-to-corner line drawing). Verify the mapping is reasonable for the grid system used.

---

## Output Format

Write `docs/verification/DOMAIN_A_VERIFICATION.md` using the standard structure. Include a section cross-referencing Domain D findings.
