# WO-VERIFY-F — Domain F: Character Progression & Economy Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Parallel wave 1
**Risk:** LOW | **Effort:** Large (77 formulas, mostly table verification) | **Breaks:** 0 (read-only audit)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-D, B, C, E, G, H, I

---

## Target Lock

Verify every formula in the experience, encumbrance, leveling, feat prerequisite, and skill property systems against SRD 3.5e. 77 formulas across 4 files. Primarily table lookups — tedious but mechanical.

**Goal:** Verification record for every formula. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain F for formula list.
3. For each formula, read code, look up SRD 3.5e, produce verification record.
4. Use d20srd.org — "Experience and Levels", "Carrying Capacity", "Feats", "Skills Summary".
5. Write all records to `docs/verification/DOMAIN_F_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain F row.
7. Add entry to Iteration Log.
8. Commit: `verify: Domain F — Character Progression (77 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs.**

---

## Formulas To Verify

### aidm/core/experience_resolver.py (10 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 61 | `cr_delta = int(cr) - party_level` | SRD: Encounters > Challenge Rating |
| 65 | `base_xp = XP_TABLE.get(key)` | SRD: Table > Experience Awards |
| 69 | `adjusted_xp = int(base_xp * (4.0 / party_size))` | SRD: Experience > Party Size Adjustment |
| 113 | `offending = highest - level > 1` (multiclass XP penalty) | SRD: Multiclass Characters |
| 117 | `penalty = max(0, 1.0 - 0.2 * count)` | SRD: Multiclass Characters |
| 219 | `hp_roll = randint(1, hit_die)` | SRD: Gaining Levels |
| 220 | `hp_gained = max(1, roll + con_mod)` | SRD: Gaining Levels |
| 227 | `skill_points = max(1, base + int_mod)` | SRD: Gaining Levels |
| 230 | `feat_slot = (level % 3 == 0)` | SRD: Gaining Levels |
| 235 | `ability_increase = (level % 4 == 0)` | SRD: Gaining Levels |

**Key checks:**
- XP party size adjustment: SRD says divide evenly among party members. The `4.0 / party_size` scaling — verify whether this is accurate (assumes 4-person baseline).
- Multiclass penalty: SRD says -20% per offending class. Verify the `0.2 * count` formula.
- HP minimum 1: SRD says minimum 1 HP per level regardless of CON penalty. Verify.
- Feat every 3rd level: SRD says 1st, 3rd, 6th, 9th, 12th, etc. `level % 3 == 0` gives 3, 6, 9, 12... but misses level 1. Verify how level 1 feat is handled.
- Ability increase every 4th level: SRD says 4th, 8th, 12th, 16th, 20th. `level % 4 == 0` matches. Verify.

### aidm/core/encumbrance.py (18 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 32-61 | Carrying capacity table (STR 1-29) | SRD: Table > Carrying Capacity |
| 89-90 | STR 30+ extrapolation: `4^((str-20)//10)` | SRD: Carrying Capacity > Heavier Loads |
| 128-134 | Load thresholds (light/medium/heavy/overloaded) | SRD: Encumbrance |
| 157-183 | Load penalties: max Dex, check penalty, speed, run multiplier | SRD: Table > Carrying Loads |

**Key checks:**
- Carrying capacity table: Cross-reference every value in the table against SRD Table: Carrying Capacity. There are 29 entries — verify all 87 values (light, medium, heavy for each STR score).
- STR 30+ formula: SRD says for every 10 points above 20, multiply by 4. Verify the formula produces correct values for STR 30 (×4 of STR 20), 40 (×16 of STR 20), etc.
- Load penalties table: Verify max Dex, armor check penalty, speed reduction, and run multiplier for each load level.
- Speed reduction: SRD says 30ft→20ft for medium/heavy load, 20ft→15ft. Verify both entries.

### aidm/schemas/leveling.py (30+ formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 21-40 | XP thresholds levels 1-20 | SRD: Table > Experience and Level |
| 67-85 | Class data (Fighter, Rogue, Cleric, Wizard) | SRD: Classes |
| 99-101 | BAB progressions (full, 3/4, 1/2) for levels 1-20 | SRD: Classes > Base Attack Bonus |
| 105-106 | Save progressions (good, poor) for levels 1-20 | SRD: Classes > Saving Throws |
| 150-308 | XP award table (100+ entries) | SRD: Table > Experience Awards |

**Key checks:**
- XP thresholds: Verify all 20 values against SRD.
- BAB progressions: Full (1/level), 3/4 (0.75/level, rounded), 1/2 (0.5/level, rounded). Verify each of the 60 values (20 per progression).
- Save progressions: Good = 2 + level/2, Poor = level/3 (rounded). Verify each of the 40 values.
- Class data: Hit die, BAB type, good saves, skill points per level — verify all 4 classes.
- XP table: This is a large table. Verify at minimum: levels 1-5 for all CR deltas, and spot-check levels 10, 15, 20.

### aidm/schemas/feats.py (12 formulas — prerequisites)

| Feat | Prerequisites | SRD Reference |
|------|--------------|---------------|
| Power Attack | STR 13, BAB 1 | SRD: Feats > Power Attack |
| Cleave | STR 13, Power Attack | SRD: Feats > Cleave |
| Great Cleave | STR 13, BAB 4, Cleave | SRD: Feats > Great Cleave |
| Dodge | DEX 13 | SRD: Feats > Dodge |
| Mobility | DEX 13, Dodge | SRD: Feats > Mobility |
| Spring Attack | DEX 13, BAB 4, Dodge, Mobility | SRD: Feats > Spring Attack |
| TWF | DEX 15 | SRD: Feats > Two-Weapon Fighting |
| Improved TWF | DEX 17, BAB 6, TWF | SRD: Feats > Improved TWF |
| Greater TWF | DEX 19, BAB 11, Improved TWF | SRD: Feats > Greater TWF |
| Weapon Focus | BAB 1 (implied) | SRD: Feats > Weapon Focus |
| Weapon Specialization | Weapon Focus, Fighter 4 | SRD: Feats > Weapon Specialization |
| Improved Initiative | none | SRD: Feats > Improved Initiative |

### aidm/schemas/skills.py (7 formulas — skill properties)

Verify key ability, ACP applicability, and trained-only status for: Tumble, Concentration, Hide, Move Silently, Spot, Listen, Balance.

---

## Output Format

Write `docs/verification/DOMAIN_F_VERIFICATION.md` using the standard structure.
