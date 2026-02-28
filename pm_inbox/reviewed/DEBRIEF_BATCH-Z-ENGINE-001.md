# DEBRIEF: Batch Z — Engine Field Contract Drift Fixes

**Lifecycle:** ARCHIVE
**Commit:** `37a51ed`
**Gate file count:** 4 files, 32 tests (CW-001–008, SDF-001–008, MBF-001–008, SSU-001–008)
**Gate result:** 32/32 PASS + 254/254 regression PASS (16 stale tests updated for Type 2 contract)

---

## Pass 1 — Context Dump

### WO1: ENGINE-CONCENTRATION-WRITE-001

**Files changed:**
- `aidm/chargen/builder.py` — lines 899, 1150: Added `EF.CONCENTRATION_BONUS: skill_ranks.get("concentration", 0) + modifiers["con"]` to both single-class and multiclass entity assembly paths.
- `aidm/core/play_loop.py` — line 1336: Fixed bare string `"concentration_bonus"` → `EF.CONCENTRATION_BONUS`.

**Before:** `EF.CONCENTRATION_BONUS` never written at chargen. All casters had effective +0 for all 5 concentration check sites (damage, grapple, vigorous motion, defensive casting, entangle).

**After:** Concentration bonus = ranks + CON_MOD baked at chargen. Read sites consume the correct value.

**Consumption chain:** builder.py:899/1150 (write) → play_loop.py:706/752/795/1336/2357 (5 read sites) → concentration check outcome changes → CW-001–008 gate tests prove effect.

### WO2: ENGINE-SAVE-DOUBLE-COUNT-FIX-001

**Files changed:**
- `aidm/core/save_resolver.py` — lines 104-111: Removed `ability_map` dict and `ability_mod` variable. Removed `ability_mod` from total_bonus calculation at line 168. Added WO comment explaining Type 2 field contract.

**Before:** `get_save_bonus()` read `EF.SAVE_*` (which contains base + ability_mod baked at chargen) then added `ability_mod` again from `EF.CON_MOD/DEX_MOD/WIS_MOD` → inflated saves by exactly the ability modifier.

**After:** `get_save_bonus()` treats `EF.SAVE_*` as Type 2 (base + ability_mod baked). Only adds situational deltas: conditions, feats, Divine Grace, racial bonuses, inspire courage.

**Consumption chain:** builder.py chargen (write baked save) → save_resolver.py:168 (read, no re-add) → correct save total → SDF-001–008 prove no double-count.

**Stale test fix:** 16 existing tests in `test_engine_save_feats_gate.py` (10) and `test_engine_divine_grace_gate.py` (6) used synthetic entities with unbaked save values. Updated helpers to auto-bake ability_mod into `EF.SAVE_*` per Type 2 contract.

### WO3: ENGINE-MANEUVER-BAB-FIX-001

**Files changed:**
- `aidm/core/maneuver_resolver.py` — line 142: `_get_bab()` changed from `entity.get(EF.ATTACK_BONUS, entity.get(EF.BAB, 0))` to `entity.get(EF.BAB, 0)`.

**Before:** `_get_bab()` read `EF.ATTACK_BONUS` (BAB+STR composite) as "BAB" proxy. All maneuver opposed checks then added STR separately → STR double-counted in grapple, trip, disarm, bull rush, overrun.

**After:** `_get_bab()` reads `EF.BAB` (Type 1 component — BAB only). 11 call sites across 5 maneuver types all go through this single function.

**Parity check:** All 11 call sites verified: grapple (line 575), trip (1208/1216), disarm (1450/1455), bull rush (1710/1749), overrun (1942/1947), pin (2067/2072).

**Consumption chain:** builder.py chargen (write EF.BAB) → maneuver_resolver.py:_get_bab() (read) → opposed check uses BAB only → MBF-001–008 prove no STR double-count.

### WO4: ENGINE-SPELL-SAVE-UNIFY-001

**Files changed:**
- `aidm/core/play_loop.py` — lines 252-278: Replaced raw `EF.SAVE_*` reads in `_create_target_stats()` with calls to `save_resolver.get_save_bonus()`. Used lazy import to avoid circular dependency. Kept negative level penalty (save_resolver doesn't handle it). Removed enchantment-specific block (save_resolver handles it via `school=` param).

**Before:** `_create_target_stats()` read raw `EF.SAVE_*` fields, missing: Divine Grace, save feats (Great Fortitude, Iron Will, Lightning Reflexes), Inspire Courage morale bonus, halfling +1 all saves, dwarf +2 vs spells, elf +2 vs enchantment, condition modifiers (shaken/sickened).

**After:** Routes through canonical `save_resolver.get_save_bonus()` with `save_descriptor="spell"` and `school=` parameter. All bonuses flow through single path.

**Consumption chain:** save_resolver.get_save_bonus() (canonical path) → play_loop._create_target_stats() (consumer) → TargetStats includes all bonuses → SSU-001–008 prove parity.

---

## Pass 2 — PM Summary (100 words)

Batch Z closes the "Computed Field Contract Drift" pattern across 4 stat families. WO1 wires `CONCENTRATION_BONUS` at chargen (was always 0). WO2 strips ability_mod double-count from `save_resolver` (saves were inflated by 1-5 points). WO3 fixes maneuver BAB to use `EF.BAB` not `EF.ATTACK_BONUS` (STR double-counted in all 5 maneuver types). WO4 unifies spell target saves through canonical save_resolver (was missing 8+ bonus sources). 32/32 gate tests pass. 16 stale synthetic tests updated for Type 2 field contract. No regressions across 254 related gate tests.

---

## Pass 3 — Retrospective

**Kernel touches:** This WO touches KERNEL-01 (save_resolver canonical path) — save_resolver is now the single source of truth for all save calculations including spell target saves. No parallel save computation path remains.

**Out-of-scope findings:**

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-POSITION-TUPLE-FORMAT-001 | LOW | OPEN | Chargen stores position as tuple `(0, 0)` but `_create_target_stats()` expects dict/Position. Test workaround in place; should be normalized at chargen. |
| FINDING-ENGINE-NEGATIVE-LEVEL-SAVE-001 | LOW | OPEN | Negative level penalty to saves applied in `_create_target_stats()` but not in `save_resolver.get_save_bonus()`. Minor inconsistency — only affects spell target saves vs general saves. |

---

## Coverage Map Update

4 rows updated, 1 row added in `docs/ENGINE_COVERAGE_MAP.md`:
- **Fortitude/Reflex/Will save base calculation** (3 rows): Updated notes for Type 2 field contract + WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001
- **Concentration checks (damage during casting)**: Added note for EF.CONCENTRATION_BONUS wired at chargen + WO-ENGINE-CONCENTRATION-WRITE-001
- **Grapple — opposed checks**: Added note for _get_bab() Type 1 fix + WO-ENGINE-MANEUVER-BAB-FIX-001
- **Spell target saves (TargetStats)**: NEW ROW — routes through save_resolver + WO-ENGINE-SPELL-SAVE-UNIFY-001

---

## Consume-Site Confirmation

| WO | Write Site | Read Site | Gate Test |
|----|-----------|-----------|-----------|
| WO1 | builder.py:899/1150 | play_loop.py:706/752/795/1336/2357 | CW-001–008 |
| WO2 | builder.py chargen (baked save) | save_resolver.py:168 (no re-add) | SDF-001–008 |
| WO3 | builder.py chargen (EF.BAB) | maneuver_resolver.py:_get_bab() | MBF-001–008 |
| WO4 | save_resolver.get_save_bonus() | play_loop._create_target_stats() | SSU-001–008 |

No CONSUME_DEFERRED fields introduced.
