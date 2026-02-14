# WO-VERIFY-I — Domain I: Geometry, Size & Support Systems Verification

**Dispatch Authority:** PM (Opus)
**Priority:** Parallel wave 1
**Risk:** LOW | **Effort:** Small-Medium | **Breaks:** 0 (read-only audit)
**Depends on:** Nothing
**Parallel with:** WO-VERIFY-D, B, C, E, F, G, H
**Lifecycle:** NEW

---

## Target Lock

Verify every formula in the geometry, size, terrain schema, combat reflexes, environmental damage, AoO constants, play_loop defaults, saves schema, and feat modifier systems against SRD 3.5e. 18 formulas across 10 files. These are support systems — constants, defaults, and utility computations consumed by the core resolvers.

**Goal:** Verification record for every formula. No code changes.

---

## Execution Instructions

1. Read `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md` Section 6 for verification record format.
2. Read `docs/verification/FORMULA_INVENTORY.md` Domain I for formula list.
3. For each formula, read code, look up SRD 3.5e, produce verification record.
4. Use d20srd.org — "Combat > Size", "Environment", "Feats", etc.
5. Write all records to `docs/verification/DOMAIN_I_VERIFICATION.md`.
6. Update `docs/verification/BONE_LAYER_CHECKLIST.md` Domain I row.
7. Add entry to Iteration Log.
8. Commit: `verify: Domain I — Geometry & Size (18 formulas, X wrong, Y ambiguous)`

**DO NOT fix any bugs.**

---

## Formulas To Verify

### aidm/schemas/geometry.py (3 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 291-301 | Footprint by size: Fine=1, Diminutive=1, Tiny=1, Small=1, Medium=1, Large=4, Huge=9, Gargantuan=16, Colossal=25 (squares) | SRD: Combat > Size |
| 310-311 | `grid_size = int(sqrt(footprint))` | Grid dimension from footprint |

**Key check:** SRD says Large=10ft (2×2), Huge=15ft (3×3), Gargantuan=20ft (4×4), Colossal=30ft+ (6×6). Colossal footprint should be 36 squares (6×6=36), not 25 (5×5). Verify against SRD size table.

### aidm/schemas/bestiary.py (10 formulas — defaults)

| Line | Value | SRD Reference |
|------|-------|---------------|
| 141 | hp_typical = 0 | Default |
| 142 | ac_total = 10 | SRD: AC base 10 |
| 143 | ac_touch = 10 | SRD: Touch AC |
| 144 | ac_flat_footed = 10 | SRD: Flat-Footed AC |
| 145-153 | speed=0, bab=0, saves=0, cr=0 | Defaults (verify sensible) |

### aidm/schemas/terrain.py (5 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 48 | Standard cover: +4 AC, +2 Reflex | SRD: Combat > Cover |
| 49 | Improved cover: +8 AC, +4 Reflex | SRD: Combat > Cover |
| 50 | Total cover: untargetable | SRD: Combat > Cover |
| 51 | Soft cover: +4 AC melee only, no AoO block | SRD: Combat > Cover |
| 116 | `movement_cost = 1` (1=normal, 2=difficult) | SRD: Movement > Terrain |

**Note:** These are also verified in Domain E's terrain_resolver.py. If the other agent has already verified the cover values, confirm consistency. If not, verify independently.

### aidm/core/combat_reflexes.py (2 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 90 | Without feat: 1 AoO per round | SRD: Combat > Attacks of Opportunity |
| 93 | With Combat Reflexes: `max(1, 1 + dex_mod)` AoOs | SRD: Feats > Combat Reflexes |

**Key check:** SRD says Combat Reflexes grants additional AoOs equal to DEX modifier. Total = 1 + DEX mod (minimum 1). Code has `max(1, 1 + dex_mod)`. Verify the formula handles negative DEX correctly (should still get 1).

### aidm/core/environmental_damage_resolver.py (4 formulas)

| Line | Hazard | Damage | SRD Reference |
|------|--------|--------|---------------|
| 48 | Fire | 1d6 fire | SRD: Environment > Fire |
| 49 | Acid | 1d6 acid | SRD: Environment > Acid |
| 50 | Lava | 2d6 fire | SRD: Environment > Lava |
| 51 | Spiked pit | 1d6 piercing | SRD: Environment > Pits |

**Key check:** Lava damage in SRD is 2d6 per round for exposure, 20d6 for immersion. Verify which case the code implements and if the value matches.

### aidm/core/aoo.py (2 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 430 | `tumble_dc = 15` | SRD: Skills > Tumble |
| 506 | Mobility feat AC modifier via feat_resolver | SRD: Feats > Mobility |

### aidm/core/play_loop.py (5 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 185 | `caster_level = 5` default | Uncited test default |
| 188 | `spell_dc_base = 13` (10+3) default | Uncited test default |
| 486 | `new_hp = min(old_hp + healing, max_hp)` | Cannot exceed max HP |
| 618-623 | Concentration: `d20 + bonus >= 10 + damage` | SRD: Skills > Concentration |

### aidm/schemas/saves.py (2 formulas)

| Line | Formula | SRD Reference |
|------|---------|---------------|
| 109 | `damage_multiplier = 1.0` default | SRD: Saves |
| 117 | Valid multipliers: {0.0, 0.5, 1.0} | SRD: Saves (negates=0, half=0.5, full=1.0) |

### aidm/core/feat_resolver.py (16 formulas)

| Line | Feat | Modifier | SRD Reference |
|------|------|----------|---------------|
| 158 | Weapon Focus | +1 attack | SRD: Feats > Weapon Focus |
| 165 | PBS attack | +1 (ranged ≤ 30ft) | SRD: Feats > Point Blank Shot |
| 169 | Rapid Shot | -2 attack | SRD: Feats > Rapid Shot |
| 174 | Power Attack | -penalty to attack | SRD: Feats > Power Attack |
| 206 | Weapon Spec | +2 damage | SRD: Feats > Weapon Specialization |
| 213 | PBS damage | +1 (ranged ≤ 30ft) | SRD: Feats > Point Blank Shot |
| 223 | PA two-handed | +penalty×2 damage | SRD: Feats > Power Attack |
| 225 | PA one-handed | +penalty×1 damage | SRD: Feats > Power Attack |
| 257 | Dodge | +1 AC | SRD: Feats > Dodge |
| 265 | Mobility | +4 AC vs movement AoO | SRD: Feats > Mobility |
| 283 | Improved Initiative | +4 initiative | SRD: Feats > Improved Initiative |
| 332-335 | Cleave/Great Cleave limits | SRD: Feats > Cleave/Great Cleave |
| 386-415 | TWF penalty/extra attack tables | SRD: Feats > TWF |

**Key checks:**
- Power Attack two-handed: SRD says 2:1 ratio (trade 1 attack for 2 damage) for two-handed. Code has `penalty * 2`. Verify this is the SRD rule and not the Pathfinder version (Pathfinder changed this to 3:1 for two-handed which may be the intended correction).
- TWF penalties: Without feat (-6/-10 or -4/-8 with light offhand). With feat (-2/-2). Verify all combinations.
- Rapid Shot: SRD says one extra attack at highest BAB at -2 to all attacks. Code only has -2. Verify the extra attack is handled elsewhere.

---

## Output Format

Write `docs/verification/DOMAIN_I_VERIFICATION.md` using the standard structure.
