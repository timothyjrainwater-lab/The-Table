# DEBRIEF — WO-ENGINE-CONDITION-ENFORCEMENT-001: Wire Condition Enforcement

**Completed:** 2026-02-25
**Builder:** Claude (Sonnet)
**Status:** FILED

---

## Pass 1 — Context Dump

### Files Modified (by sub-WO)

**CE-A — Movement gate (new code):**
- `aidm/core/movement_resolver.py` — `build_full_move_intent()` (lines ~215–225): Added `movement_prohibited` gate at top of function, after entity/position validation, before `from_pos` construction. Uses local import of `get_condition_modifiers`. Returns `(None, "movement_prohibited_by_condition")` on block.
- `aidm/core/play_loop.py` — `StepMoveIntent` branch (~line 2288): Replaced hardcoded `"grappling"/"grappled"` name check (CP-22) with generic `movement_prohibited` flag check via `get_condition_modifiers()`. Now covers all conditions with `movement_prohibited=True` (not just grapple/grappling by name).
- `aidm/core/play_loop.py` — `FullMoveIntent` branch (~line 2355): Added `movement_prohibited` gate before AoO loop, emits `action_denied` + `turn_end`, returns `TurnResult(status="action_denied")`.

**CE-B — Action gate (already wired, confirmed):**
- `aidm/core/play_loop.py` line 1330: WO-WAYPOINT-002 gate already present. Blocks all intents when any condition has `actions_prohibited=True`. No code change needed.

**CE-C — Dex-to-AC gate (already wired, confirmed):**
- `aidm/core/attack_resolver.py` lines 315–320 and 787–790: CP-17 comment present, `loses_dex_to_ac` check already in both `resolve_attack()` paths. No code change needed.

**Files Created:**
- `tests/test_engine_condition_enforcement_001_gate.py` — CE-001 through CE-010 (12 tests total)

---

### Option Used for Action Gate

**Option C** (check at call site in play_loop.py). The gate was already in place at `play_loop.py:1330` as WO-WAYPOINT-002, checking all intents before routing. No signature change to `ActionBudget.can_use()`.

---

### Condition Deserialization Pattern

Conditions on entity dict are stored as **dict keyed by condition type string** (`EF.CONDITIONS = "conditions"` → `{condition_type_value: {condition_dict...}}`). The existing `get_condition_modifiers()` in `aidm/core/conditions.py` iterates this dict and calls `ConditionInstance.from_dict(condition_dict)` for each entry. This function is the canonical query interface and was used for CE-A and CE-B gate checks.

---

### Pre-flight Survey Findings

| Component | Status Before WO | Action Taken |
|-----------|-----------------|--------------|
| CE-A `movement_prohibited` in `build_full_move_intent()` | NOT wired | Added gate |
| CE-A `movement_prohibited` in `StepMoveIntent` (play_loop) | Partially wired (hardcoded grapple/grappling names) | Replaced with flag-based check |
| CE-A `movement_prohibited` in `FullMoveIntent` (play_loop) | NOT wired | Added gate |
| CE-B `actions_prohibited` in play_loop | Already wired (WO-WAYPOINT-002, line 1330) | Confirmed, no change |
| CE-C `loses_dex_to_ac` in attack_resolver | Already wired (CP-17 comment, line 315+787) | Confirmed, no change |

---

### Gate Counts per Sub-WO

| Sub-WO | Tests | Result |
|--------|-------|--------|
| CE-A movement (CE-001, CE-002, CE-003, CE-001b, CE-002b) | 5 | 5/5 PASS |
| CE-B actions (CE-004, CE-005, CE-006) | 3 | 3/3 PASS |
| CE-C Dex-to-AC (CE-007, CE-008, CE-009) | 3 | 3/3 PASS |
| CE-010 (movement_prohibited ≠ actions_prohibited) | 1 | 1/1 PASS |
| **Total gate** | **12** | **12/12 PASS** |

---

### Regression Gate

- Baseline: 7926 collected
- Pre-existing failures confirmed before changes: 2 (`test_all_condition_types_have_factories`, `test_aoo_usage_resets_each_round`)
- Post-change: 258/260 PASS in focused suite (test_conditions_kernel, test_aoo_kernel, test_engine_condition_enforcement_001_gate, test_engine_hooligan_tier_a_001_gate, test_engine_skill_modifier, wildshape gates, concealment, expanded_spells, aoe_rasterizer, property_based). Same 2 pre-existing failures. No new failures introduced.

---

## Pass 2 — PM Summary (≤100 words)

CE-A: Added `movement_prohibited` gate to `build_full_move_intent()` (fast-reject before BFS) and both move intent branches in play_loop.py (`FullMoveIntent` new gate; `StepMoveIntent` generalized from hardcoded grapple names to flag-based). CE-B: `actions_prohibited` gate at play_loop:1330 (WO-WAYPOINT-002) already complete — confirmed, no change. CE-C: `loses_dex_to_ac` in attack_resolver lines 315+787 (CP-17) already complete — confirmed, no change. 12/12 gate PASS. FINDING-ENGINE-CONDITION-ENFORCEMENT-001 partially closed (movement + action + dex enforced; flat_footed/auto_hit/standing_aoo deferred).

---

## Pass 3 — Retrospective

**Conditions not covered by the three flags:**

The three flags cover the dispatch scope completely. Additional deferred flags in `ConditionModifiers`:
- `standing_triggers_aoo` — prone stand-up provokes AoO. Out of scope. Requires AoO path integration.
- `auto_hit_if_helpless` — coup de grace eligibility. Partially read in attack_resolver (`if is_melee and defender_modifiers.auto_hit_if_helpless`) but no auto-hit enforcement (just a payload flag). Separate WO.

Conditions with `movement_prohibited=True` in registry: GRAPPLED, GRAPPLING, PARALYZED, UNCONSCIOUS, PINNED. All now blocked by the new gate.
Conditions with `actions_prohibited=True`: HELPLESS, STUNNED, DAZED, NAUSEATED, TURNED, PARALYZED. All already blocked by WO-WAYPOINT-002.

**Existing tests encoding old behavior:**
The CP-22 StepMoveIntent test (`test_aoo_kernel.py::test_aoo_usage_resets_each_round`) was a pre-existing failure unrelated to our change. The `test_conditions_kernel.py::test_all_condition_types_have_factories` failure (missing `blinded` factory) is also pre-existing. No existing test encoded "grappled entity can move via FullMoveIntent freely" — the FullMoveIntent gate was simply absent (not a deliberate permission).

**Recommendation on remaining deferred flags:**
- `auto_hit_if_helpless`: Wire next — the check point in attack_resolver is already identified (line 310). Needs a "set hit=True, skip roll" path before the d20 roll.
- `standing_triggers_aoo`: Lower priority. Requires AoO trigger expansion to standing-from-prone action. File as separate WO when grapple movement WO is addressed.

---

## Radar

- Regression gate: PASS — 258/260 on focused suite; 2 pre-existing failures unchanged
- CE-001–010 (12 tests): all PASS
- CE-001: GRAPPLED movement blocked in `build_full_move_intent()`: CONFIRMED
- CE-001b: GRAPPLED `FullMoveIntent` blocked in play_loop: CONFIRMED
- CE-002: PARALYZED movement blocked: CONFIRMED
- CE-003: Clean entity movement permitted (regression): CONFIRMED
- CE-004: STUNNED standard action blocked: CONFIRMED
- CE-005: PARALYZED standard action blocked: CONFIRMED
- CE-006: Clean entity standard action permitted (regression): CONFIRMED
- CE-007: HELPLESS loses Dex to AC (`dex_penalty=-3`): CONFIRMED
- CE-008: STUNNED loses Dex to AC (`dex_penalty=-3`): CONFIRMED
- CE-009: Clean target keeps Dex bonus (`dex_penalty=0`): CONFIRMED (regression)
- CE-010: GRAPPLED can still attack (movement_prohibited ≠ actions_prohibited): CONFIRMED
- Movement gate wired in `movement_resolver.py:build_full_move_intent()`: CONFIRMED
- Movement gate wired in `play_loop.py:StepMoveIntent` (generalized from CP-22 hardcode): CONFIRMED
- Movement gate wired in `play_loop.py:FullMoveIntent` (new): CONFIRMED
- Action gate wired (play_loop:1330, WO-WAYPOINT-002): CONFIRMED (pre-existing, no change)
- Dex-to-AC gate wired (attack_resolver:315+787, CP-17): CONFIRMED (pre-existing, no change)
- `_get_condition_flags()` helper: N/A — using existing `get_condition_modifiers()` from `aidm/core/conditions.py` (canonical, already imported)
- FINDING-ENGINE-CONDITION-ENFORCEMENT-001: PARTIAL-CLOSED (movement + action + dex enforced; flat_footed AoO, auto_hit_if_helpless, standing_triggers_aoo deferred)
