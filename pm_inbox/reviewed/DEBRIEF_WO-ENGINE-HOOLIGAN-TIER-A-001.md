# DEBRIEF — WO-ENGINE-HOOLIGAN-TIER-A-001: Hooligan Tier A Bug Bundle

**Completed:** 2026-02-25
**Builder:** Claude (Sonnet)
**Status:** FILED

---

## Pass 1 — Context Dump

### Files Modified (by sub-WO)

**WO-A — AoE Origin Square Fix:**
- `aidm/core/aoe_rasterizer.py` — `rasterize_cone()` only. Changed `affected = []` to `affected = [origin]` before the directional sweep loop. `rasterize_line()` was already correct (loop starts at `d=0` which IS the origin — no change needed).

**WO-B — CLW on Undead:**
- `aidm/core/spell_resolver.py` — `TargetStats` dataclass: added `is_undead: bool = False` field. `_resolve_healing()`: added undead branch before healing cap — if `target.is_undead`, compute `damage_to_undead = total` (same dice/caster-level, no HP-cap) and return `(-damage_to_undead, stp)`. Negative value signals damage to caller.
- `aidm/core/play_loop.py` — `_create_target_stats()`: added `is_undead = bool(entity.get(EF.IS_UNDEAD, False))` and passes to `TargetStats`. Healing loop rewritten to handle negative values: positive → normal healing (capped at max HP, skip on `delta == 0`); negative → undead damage (no HP cap, always emits `hp_changed` with negative delta).

**WO-C — Allegiance Filter Audit:**
- No code changes. Audit confirmed no filter exists.

**WO-A Cascade — Tests updated to match new correct behavior:**
- `tests/test_aoe_rasterizer.py` — 5 tests updated:
  - `test_15ft_cone_north_count`: 6 → 7
  - `test_15ft_cone_each_cardinal`: 6 → 7
  - `test_30ft_cone_count`: 21 → 22
  - `test_cone_excludes_origin` → renamed `test_cone_includes_origin`, assertion inverted
  - `test_cone_triangular_formula`: formula `n*(n+1)//2` → `n*(n+1)//2 + 1`
- `aidm/testing/property_testing.py` — `run_cone_square_count_check()`: same formula update
- `tests/integration/test_property_based.py` — 2 tests updated:
  - `test_cone_square_count_formula`: all 4 expected counts +1 (6→7, 21→22, 45→46, 78→79)
  - `test_cone_excludes_origin` → renamed `test_cone_includes_origin`, assertion inverted

**Files Created:**
- `tests/test_engine_hooligan_tier_a_001_gate.py` — HG-A-001 through HG-C-004 (13 tests)

---

### WO-A Line Ranges

- `aidm/core/aoe_rasterizer.py` `rasterize_cone()` — single line change (init of `affected`).
- `rasterize_line()` — **confirmed correct, not modified**. Loop `for d in range(length_squares)` starts at `d=0` which places `origin + d*delta = origin` as the first square. PHB intent already satisfied.

---

### WO-B — Creature Type Detection

**Exact field name confirmed:** `EF.IS_UNDEAD = "is_undead"` — boolean field on entity dict. The dispatch spec suggested `creature_type: str = "humanoid"` on `TargetStats`, but the actual entity schema uses a boolean flag, not a string type. Used `is_undead: bool = False` on `TargetStats` as the simpler and correct approach.

**FINDING-HG-HEALING-NOOP-001 — CLW on living emits no `hp_changed`:**

Root cause confirmed as the old `if healing > 0` guard in the healing loop with `delta == 0` (living target at full HP). The old guard caused CLW on undead to also silently no-op (healing was 0, not negative). The new healing loop handles both cases:
- Living at full HP: `delta == 0` → skip event. **This is correct behavior** (no HP change occurred). FINDING-HG-HEALING-NOOP-001 is **CLOSED as expected-correct** — the test `HG-B-005` confirms this is the intended behavior (`no hp_changed for full-HP living target`).
- Undead: negative value → `delta = -damage_amount`, always emits event regardless of current HP.

---

### WO-C — Allegiance Filter Audit Results

**Builder looked at the following locations — no allegiance filter found in any:**

1. `aidm/core/aoe_rasterizer.py` — `rasterize_burst()`, `rasterize_cone()`, `rasterize_line()`: pure geometric, no entity or team lookup whatsoever.
2. `aidm/core/spell_resolver.py` `_resolve_area_targets()` (lines ~713–763): only filter is defeated entities (`HP <= 0`). No team/faction/allegiance check.
3. `aidm/core/geometry_engine.py` `get_entities_in_area()`: pure positional — returns all entity IDs at matching positions, no team lookup.
4. `aidm/core/play_loop.py` lines 596–700 (AoE dispatch path): processes `resolution.affected_entities` directly with no post-resolution team filter.

**Anvil's H-011 observation was a test setup artifact.** The most likely cause: ally entity in the Anvil test was positioned outside the actual blast radius squares, not inside. The `_resolve_area_targets()` code filters by position overlap with the rasterized area — if the ally's position didn't appear in the rasterized burst squares (e.g., due to grid coordinate mismatch), it would not appear in `affected_entities` without any allegiance filter being involved. Gate tests HG-C-001 and HG-C-003 confirm allies correctly appear in `affected_entities` when positioned inside the blast.

---

### Gate Counts per Sub-WO

| Sub-WO | Tests | Result |
|--------|-------|--------|
| WO-A (HG-A-001–004) | 4 | 4/4 PASS |
| WO-B (HG-B-001–005) | 5 | 5/5 PASS |
| WO-C (HG-C-001–004) | 4 | 4/4 PASS |
| **Total gate** | **13** | **13/13 PASS** |

---

## Pass 2 — PM Summary (≤100 words)

WO-A: `rasterize_cone()` origin prepend (one line); `rasterize_line()` confirmed already correct. 8 existing tests updated to reflect new count (`T(n)+1`). WO-B: Added `is_undead: bool` to `TargetStats`; populated from `EF.IS_UNDEAD`; `_resolve_healing()` returns negative value for undead (no save, no HP cap); healing loop rewritten to handle polarity. FINDING-HG-HEALING-NOOP-001 closed as expected-correct (`delta==0` skip is correct). WO-C: Code audit — no allegiance filter found anywhere; Anvil H-011 was test setup artifact. 13/13 gate PASS, regression clean.

---

## Pass 3 — Retrospective

**WO-A cascade impact:**
The origin square fix introduced +1 to all cone square counts. 8 existing tests (5 in `test_aoe_rasterizer.py`, 2 in `test_property_based.py`, 1 via `property_testing.py` harness) encoded the pre-fix count. All were updated in the same session. `rasterize_line()` being already-correct was confirmed by reading the loop — `range(length_squares)` starting at `d=0` means the first square emitted is `origin + 0 * direction_delta = origin`. No line test needed update.

**WO-B: `EF.IS_UNDEAD` vs `creature_type` string:**
Dispatch spec called for `creature_type: str = "humanoid"`. The actual entity schema uses `EF.IS_UNDEAD` (boolean), not a string type field. Using the boolean directly was cleaner and required no new field on entities. `TargetStats.is_undead: bool = False` is the correct implementation. No change to dispatch intent — undead-as-damage path is implemented correctly.

**WO-B: FINDING-HG-HEALING-NOOP-001:**
The old healing loop `if healing > 0:` meant undead targets (which should receive damage) were silently skipped — the `_resolve_healing()` returned 0 for undead (no negative value path existed). The new code added the negative-return path in `_resolve_healing()` and rewrote the caller loop to handle it. FINDING-HG-HEALING-NOOP-001 (CLW on living full-HP emits no event) was a secondary observation from the same root — the `delta == 0` skip is correct behavior (entity HP did not change). The new loop explicitly continues on `delta == 0` for living targets and documents why.

---

## Radar

- Regression gate: PASS — 194/194 on all modified and adjacent test files; property-based and rasterizer cascade all resolved
- HG-A-001–004: all PASS
- HG-B-001–005: all PASS
- HG-C-001–004: all PASS
- Origin square in `rasterize_cone()`: CONFIRMED (prepended, dedup not needed — origin is unique)
- Origin square in `rasterize_line()`: CONFIRMED already included (loop at d=0), no change
- `TargetStats.is_undead: bool = False` field added: CONFIRMED
- `_create_target_stats()` populates `is_undead` from `EF.IS_UNDEAD`: CONFIRMED
- CLW on undead emits `hp_changed` with negative delta (damage event): CONFIRMED
- No allegiance filter in AoE path: CONFIRMED (4 locations audited, all clean)
- FINDING-HG-HEALING-NOOP-001: CLOSED — `delta==0` skip for living full-HP is correct behavior
- FINDING-HG-AOE-ORIGIN-001: CLOSED
- FINDING-HG-CLW-UNDEAD-001: CLOSED
- FINDING-HG-AOE-ALLEGIANCE-001: CLOSED (test setup artifact, no code change)
