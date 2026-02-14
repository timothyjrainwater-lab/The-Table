# WO-VERIFY-B — Domain B: Combat Maneuvers Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Parallel wave 1
**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 (read-only audit)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-D, C, E, F, G, H, I

---

## Target Lock

Verify every formula in the combat maneuver system (bull rush, trip, disarm, grapple, sunder, overrun) and the size modifier table against SRD 3.5e. 27 formulas across 2 files.

**Goal:** Verification record for every formula. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain B for formula list.
3. For each formula, read the code, look up SRD 3.5e, produce a verification record.
4. Use d20srd.org — search for "Special Attacks" and "Combat Modifiers" sections.
5. Write all records to `docs/verification/DOMAIN_B_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain B row.
7. Add entry to Iteration Log.
8. Commit: `verify: Domain B — Combat Maneuvers (27 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs. Record them and move on.**

---

## Formulas To Verify

### aidm/core/maneuver_resolver.py (18 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 98-104 | `touch_ac = 10 + dex_mod + size_mod` | SRD: Special Attacks > Bull Rush / Trip / Grapple |
| 127-128 | Opposed d20 rolls (attacker and defender) | SRD: Special Attacks |
| 131 | `attacker_wins = attacker_total > defender_total` (ties to defender) | SRD: Opposed Checks |
| 254 | `charge_bonus = 2 if is_charge else 0` | SRD: Bull Rush |
| 255 | `attacker_modifier = str + size + charge_bonus` | SRD: Bull Rush |
| 260 | `defender_modifier = str + size + stability` | SRD: Bull Rush |
| 280-281 | `push = 5 + (margin // 5) * 5` | SRD: Bull Rush |
| 501 | `touch_attack_bonus = bab + str + size` | SRD: Trip |
| 542 | `trip_attacker = str + size` | SRD: Trip |
| 546-549 | `trip_defender = max(str, dex) + size + stability` | SRD: Trip |
| 859 | `prone_threshold = margin <= -5` (failed tripper falls prone) | SRD: Trip |
| 1004 | `sunder_modifier = bab + str + size` | SRD: Sunder |
| 1027 | `damage_roll = randint(1, 8)` — verify this is correct sunder damage | SRD: Sunder |
| 1029 | `total_damage = max(0, roll + bonus)` | SRD: Sunder |
| 1168 | `disarm_modifier = bab + str + size` | SRD: Disarm |
| 1173 | `defender_disarm = bab + str + size` | SRD: Disarm |
| 1382 | `grapple_touch = bab + str + size` | SRD: Grapple |
| 1421-1426 | Grapple check: attacker/defender = bab + str + size | SRD: Grapple |

**Key checks:**
- Bull rush push distance: SRD says pushed back 5ft + 5ft per 5 points of margin. Verify the `margin // 5` formula handles this correctly.
- Trip: SRD says defender uses STR or DEX (whichever higher). Code uses `max(str, dex)`. Confirm.
- Trip failure: SRD says if you fail by 10 or more, you are tripped instead. Code checks `margin <= -5`. VERIFY — is it -5 or -10?
- Grapple: SRD grapple check = BAB + STR mod + special size modifier. Verify the size modifier used is the GRAPPLE size modifier (which differs from the combat maneuver size modifier in some interpretations).
- Sunder: The `1d8` damage — verify this is placeholder or rule-accurate. SRD sunder damage uses the attacker's weapon damage, not a flat 1d8.
- Touch AC for maneuvers: Verify which maneuvers require a touch attack first vs direct opposed checks.

### aidm/schemas/maneuvers.py (9 formulas — size modifier table)

| Line | Size | Modifier | SRD Reference |
|------|------|----------|---------------|
| 28 | Fine | -16 | SRD: Table Special Size Modifier |
| 29 | Diminutive | -12 | SRD: Table Special Size Modifier |
| 30 | Tiny | -8 | SRD: Table Special Size Modifier |
| 31 | Small | -4 | SRD: Table Special Size Modifier |
| 32 | Medium | 0 | SRD: Table Special Size Modifier |
| 33 | Large | +4 | SRD: Table Special Size Modifier |
| 34 | Huge | +8 | SRD: Table Special Size Modifier |
| 35 | Gargantuan | +12 | SRD: Table Special Size Modifier |
| 36 | Colossal | +16 | SRD: Table Special Size Modifier |

**Key check:** These are SPECIAL size modifiers (grapple/bull rush/trip), NOT standard size modifiers (attack/AC). Verify the table is the special size modifier table, not the regular one. SRD has two different size modifier progressions.

---

## Output Format

Write `docs/verification/DOMAIN_B_VERIFICATION.md` using the same structure as defined in WO-VERIFY-D (Summary, Records, Bug List, Ambiguity Register).
