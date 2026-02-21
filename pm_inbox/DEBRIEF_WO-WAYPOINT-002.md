# DEBRIEF: WO-WAYPOINT-002 — Condition Action Denial

**Builder:** Claude Opus 4.6
**Date:** 2026-02-21
**Status:** COMPLETE — all gates pass, zero regressions

---

## 0. Scope Accuracy

Delivered exactly what was asked. ONE gate check added to `execute_turn()` in `aidm/core/play_loop.py`, before resolver dispatch. No changes to condition definitions, resolver internals, or condition application/removal. The `action_denied` event was added to `INFORMATIONAL_EVENTS` in `replay_runner.py` (explicit classification, not relying on the unknown-event fallback). Updated `tests/test_waypoint_001.py` W-0 and W-2 for Branch A. Created `tests/test_waypoint_002.py` with 18 gate tests (WP2-0 through WP2-4). No deviations from the dispatch.

## 1. Discovery Log

Six conditions set `actions_prohibited=True`: **paralyzed, stunned, dazed, nauseated, helpless, unconscious**. All are now correctly blocked by the single gate check — the WO only required paralyzed verification, but the boolean OR aggregation in `get_condition_modifiers()` means all six are mechanically enforced. No code-path-specific handling was needed per condition.

The `test_kael_hp_unchanged_after_turn0` in W-2 previously allowed Kael's HP to be <=45 (anticipating Branch B damage). With Branch A active, Kael takes zero damage from the blocked Turn 2, so the assertion was tightened to `== 45`.

The `normalize_events()` helper in `test_waypoint_001.py` needed an `action_denied` handler to include the event in normalized views (entity_id, reason, denied_intent_type). Without this, W-1 replay comparison would silently drop the new event from both sides — technically passing but hiding information.

## 2. Methodology Challenge

The gate check placement required inserting between `turn_start` emission and the large `if combat_intent is not None:` routing block. The key insight was that the check must also block the `elif doctrine is not None` (monster policy) and `else` (PC stub) branches — not just the `combat_intent` path. Placing it before the entire routing trident ensures ALL action paths are gated, not just explicit combat intents.

Identifying which conditions caused the prohibition required walking the raw condition dicts rather than using `get_condition_modifiers()` (which only returns the aggregated boolean). The payload includes the specific condition names for auditability.

## 3. Field Manual Entry

**When adding a gate check to `execute_turn()`, place it above the three-way routing trident** (combat_intent / doctrine / else). The function is structured as a single long method with three major branches. A gate check at the top (after `turn_start`, before routing) catches all three paths. A gate check inside only one branch is a partial fix that will leak actions through the other branches.

## 4. Builder Radar

- **Trap.** The `replay_runner.reduce_event()` has a fail-safe fallback for unknown events (line 491), but the `get_missing_handlers()` compliance checker (line 556) only checks `MUTATING_EVENTS`. If `action_denied` were accidentally added to `MUTATING_EVENTS` instead of `INFORMATIONAL_EVENTS`, the compliance check would demand a reducer handler that doesn't exist, failing the AC-09 test.
- **Drift.** The `normalize_events()` function in `test_waypoint_001.py` is a growing if/elif chain with manual field extraction per event type. Each new event type requires a manual update. A schema-driven normalization approach would prevent silent drops.
- **Near stop.** A4 validation was close — the module docstring in `conditions.py` says "NO ENFORCEMENT LOGIC IN THIS MODULE" and "enforcement deferred to CP-17+". The WO-WAYPOINT-002 enforcement lives in `play_loop.py` (which is correct), but a reader might misinterpret the docstring as meaning `actions_prohibited` doesn't exist yet. It does — it's computed, just not previously enforced.
