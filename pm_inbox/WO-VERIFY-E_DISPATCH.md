# WO-VERIFY-E — Domain E: Movement & Terrain Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Parallel wave 1
**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 (read-only audit)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-D, B, C, F, G, H, I

---

## Target Lock

Verify every formula in the movement, terrain, mounted combat, and position systems against SRD 3.5e. 34 formulas across 5 files. Movement v1 was recently implemented — this verifies the new code.

**Goal:** Verification record for every formula. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain E for formula list.
3. For each formula, read code, look up SRD 3.5e, produce verification record.
4. Use d20srd.org — "Movement, Position, and Distance", "Mounted Combat", "Terrain and Obstacles".
5. Write all records to `docs/verification/DOMAIN_E_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain E row.
7. Add entry to Iteration Log.
8. Commit: `verify: Domain E — Movement & Terrain (34 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs.**

---

## Formulas To Verify

### aidm/core/movement_resolver.py (2 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 85-95 | `_step_cost()`: diagonal 5/10/5 alternation, base * terrain_mult | SRD: Movement > Diagonals |
| 228 | `speed_ft = entity.get(EF.BASE_SPEED, 30)` default 30 | SRD: Movement > Speed |

**Key check:** 5/10/5 diagonal — SRD says every second diagonal costs 10ft (the "5-10-5-10" rule). Verify the alternation logic. The first diagonal costs 5, second costs 10, third costs 5, etc. The counter should reset per-move, not persist globally.

### aidm/core/terrain_resolver.py (13 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 241 | Improved cover: ac=8, ref=4 | SRD: Combat > Cover |
| 251 | Standard cover: ac=4, ref=2 | SRD: Combat > Cover |
| 262 | Soft cover: ac=4, ref=0 | SRD: Combat > Cover |
| 390-400 | Elevation calculation (entity + terrain) | SRD: terrain rules |
| 424-447 | Higher ground bonus: +1 attack if higher | SRD: Combat Modifiers |
| 560-567 | Fall damage: `dice = min(distance // 10, 20)`, d6 per 10ft, max 20d6 | SRD: Environment > Falling |
| 619 | Water fall: `dice = max(0, (distance - 20) // 10)` | SRD: Environment > Falling into Water |
| 644 | Fall damage rolls: d6 | SRD: Environment > Falling |
| 762 | `push_squares = push_distance // 5` | Grid conversion |

**Key checks:**
- Cover AC bonuses: SRD has specific values. Improved cover = +8 AC, +4 Ref. Standard = +4 AC, +2 Ref. Soft = +4 AC only vs melee, no Ref. Verify all three.
- Higher ground: SRD says +1 attack bonus for higher ground. Verify that's all it grants (some interpretations add other benefits).
- Fall damage: SRD says 1d6 per 10ft, max 20d6. Verify the intentional fall -10ft reduction is correct per SRD.
- Water fall: SRD says DC 15 Swim/Dive check to take no damage for first 20ft, then 1d3 nonlethal per 10ft after that. Code uses `(distance - 20) // 10` d6 — verify whether this matches SRD (d3 nonlethal vs d6 lethal is a significant difference).

### aidm/core/mounted_combat.py (12 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 417-421 | Ride check: `d20 + 5 >= 15` (soft fall) | SRD: Mounted Combat |
| 445 | Fall damage from mount: `1d6` | SRD: Mounted Combat |
| 499 | `hp_after = max(0, current_hp - damage)` | HP floor at 0 |
| 546-549 | Stay mounted: 75% military saddle, 50% riding | SRD: Mounted Combat |
| 667 | SIZE_ORDER ordinals (6 entries) | SRD: Size categories |
| 716-717 | Mount size > target size gives bonus | SRD: Mounted Combat |
| 734 | `can_full_attack = mount_moved <= 5` | SRD: Mounted Combat |

**Key checks:**
- Ride modifier hardcoded at 5 — this is a placeholder, flag as UNCITED if no entity skill data feeds it.
- Stay mounted percentages: SRD says Ride check DC 5 to stay in saddle, not percentage. Verify whether the percentage model is correct or a deviation.
- Full attack restriction: SRD says you can only full attack if mount takes no more than a 5-foot step. Verify `<= 5` maps correctly.

### aidm/schemas/attack.py — FullMoveIntent (5 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 207 | `speed_ft = 30` default | SRD: Movement > Speed |
| 251-263 | `path_cost_ft()` 5/10/5 diagonal same as movement_resolver | SRD: Movement > Diagonals |

### aidm/schemas/position.py (2 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 60-73 | `distance_to()` with diagonal counting | SRD: Movement > Measuring Distance |
| 87 | `is_adjacent_to()` Chebyshev <= 1 | SRD: Combat > Threatened Squares |

**Key check:** The `distance_to()` formula uses `(diagonal_pairs * 15) + (remaining * 5) + (orthogonal * 5)`. Verify this produces the same results as the 5/10/5 rule for all cases.

---

## Output Format

Write `docs/verification/DOMAIN_E_VERIFICATION.md` using the standard structure.
