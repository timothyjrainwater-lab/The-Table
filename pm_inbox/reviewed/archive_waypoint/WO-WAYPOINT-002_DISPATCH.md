# WO-WAYPOINT-002: Condition Action Denial — play_loop Must Enforce `actions_prohibited`

**Classification:** CODE (engine fix + gate tests)
**Priority:** Critical path — truth leak. A paralyzed actor must be mechanically denied by the engine, not by author restraint.
**Dispatched by:** Slate (PM)
**Date:** 2026-02-21
**Origin:** FINDING-WAYPOINT-01 from WO-WAYPOINT-001 debrief. Branch B confirmed: play_loop resolved an attack for a paralyzed entity without blocking it.

---

## Objective

When an entity has a condition that sets `actions_prohibited = True` (e.g., paralyzed, stunned, unconscious), `execute_turn()` must reject any action intent submitted for that entity. The rejection must be deterministic, logged as an event, and replayable.

**The rule:** If the actor cannot act, the engine says no. Not the test author. Not the scenario designer. The engine.

---

## Scope

### IN SCOPE

1. **Gate check in `execute_turn()`** — Before routing to any resolver (attack, spell, etc.), call the condition modifier function on the actor. If `actions_prohibited` is True, return a rejection result and emit a rejection event. Do not call any resolver.
2. **Rejection event** — Emit an event (suggested type: `action_denied`) with payload containing `entity_id`, `reason` (e.g., "paralyzed"), and the denied intent type. This event must appear in the EventLog and be replayable.
3. **Gate tests** — New test file `tests/test_waypoint_002.py` with gate tests verifying the enforcement.
4. **Waypoint scenario regression** — The existing `tests/test_waypoint_001.py` W-2 gate currently asserts Branch B behavior (attack resolves despite paralysis). After this WO, the Bandit Captain's attack in Turn 2 will be blocked. The builder must update W-2 to assert Branch A behavior instead. This is the ONLY allowed modification to existing test files.

### OUT OF SCOPE

- No changes to condition definitions or the condition modifier system.
- No changes to how conditions are applied or removed.
- No changes to spell_resolver, attack_resolver, or feat_resolver internals.
- No new condition types.
- No changes to replay_runner (the new event type must be handled by existing event passthrough or a minimal reducer addition if needed).
- No changes to NarrativeBrief or any Lens module.
- No changes to doctrine files.

---

## Design

### Gate Check Location

The check goes in `execute_turn()` in the module that handles play loop routing — confirm path is `aidm/core/play_loop.py` before writing. The check must be:

1. **Before** any intent routing (before the attack/spell/etc. resolver is called).
2. **After** basic validation (actor exists, etc.).
3. Uses the same condition modifier function that already computes `actions_prohibited` — confirm the function name and import path. Expected: something in `aidm/core/conditions.py` that accepts an entity dict and returns modifiers including `actions_prohibited`.

### Rejection Result

The function should return early with a result indicating the action was denied. The exact return structure depends on what `execute_turn()` currently returns — the builder must read the function signature and return a result consistent with the existing contract. Suggested: return the same structure as an invalid-intent result with a `status` of `"action_denied"` and a `reason` field.

### Rejection Event

Emit an event to the EventLog before returning. Suggested payload:

```python
{
    "event_type": "action_denied",
    "entity_id": actor_id,
    "reason": "actions_prohibited",  # or the specific condition name(s)
    "denied_intent_type": intent.__class__.__name__,
    "conditions": [list of condition names that have actions_prohibited=True]
}
```

The builder should determine the most appropriate event emission pattern by reading how `execute_turn()` currently emits events (it likely delegates to resolvers, but the denial happens before resolver dispatch).

### Replay Compatibility

The `action_denied` event must survive round-trip through `EventLog.to_jsonl()` / `from_jsonl()`. If `replay_runner.reduce_event()` has a handler dispatch (e.g., by event_type), the builder must verify that an unrecognized event type either passes through safely or add a minimal no-op handler for `action_denied`. The event should NOT modify state — it's informational only (the actor's conditions are already in state).

---

## Gate Tests (`tests/test_waypoint_002.py`)

### WP2-0: Paralyzed Entity Cannot Attack

Set up: Create an entity with the `paralyzed` condition active. Submit an `AttackIntent` for that entity via `execute_turn()`.

| Assert | What it proves |
|--------|---------------|
| Return result indicates action denied (not a normal attack resolution) | Engine blocked the action |
| No `attack_roll` event emitted | Resolver was never called |
| An `action_denied` event (or equivalent) emitted with the entity_id | Denial is logged |

### WP2-1: Paralyzed Entity Cannot Cast Spells

Same setup as WP2-0 but submit a `SpellCastIntent` instead.

| Assert | What it proves |
|--------|---------------|
| Return result indicates action denied | Engine blocked the spell |
| No `spell_cast` event emitted | Spell resolver was never called |
| An `action_denied` event emitted | Denial is logged |

### WP2-2: Entity Without actions_prohibited Can Act Normally

Set up: Create an entity with NO conditions (or a condition that does NOT set `actions_prohibited`). Submit an `AttackIntent`.

| Assert | What it proves |
|--------|---------------|
| Return result is a normal attack resolution (hit or miss) | Gate check does not block healthy entities |
| `attack_roll` event emitted | Resolver was called |
| No `action_denied` event emitted | No false denial |

### WP2-3: Denial Event Survives Replay Round-Trip

Execute a scenario that produces an `action_denied` event. Write the EventLog to JSONL, read it back. Verify the `action_denied` event is present with correct payload.

| Assert | What it proves |
|--------|---------------|
| `action_denied` event present in reloaded log | Event survives serialization |
| Payload fields match original | No data loss in round-trip |

### WP2-4: Waypoint Scenario Regression — Branch A Now Active

Re-run the WO-WAYPOINT-001 scenario (same seed, same fixtures, same 3 turns). Turn 2 (Bandit Captain paralyzed, submits AttackIntent) must now be blocked.

| Assert | What it proves |
|--------|---------------|
| Turn 2 returns action denied | FINDING-WAYPOINT-01 is resolved |
| No `attack_roll` event from Bandit Captain in Turn 2 | Engine prevented the attack |
| All other WO-WAYPOINT-001 gates still pass (W-0 canary, W-1 replay, W-3 transcript, W-4 time) | No regressions on existing Waypoint proof |

**Note:** W-0 currently checks for `attack_roll` in event types — this still passes because Kael's attack in Turn 1 produces an `attack_roll`. The canary should also check for `action_denied` as a new expected event type.

---

## Modification to Existing Tests

**`tests/test_waypoint_001.py` — W-2 update (MANDATORY):**

The current W-2 asserts Branch B behavior (Bandit Captain's attack resolves). After this WO, it must assert Branch A (attack denied). The builder must:

1. Change the Turn 2 assertion from "attack resolved" to "action denied."
2. Add `action_denied` to the W-0 canary's expected event types.
3. Verify W-1 normalized view handles `action_denied` events (either include in normalized view or skip as informational — builder's judgment, but must be consistent between live and replay).

This is the ONLY existing test file the builder may modify.

---

## Integration Seams

| Seam | Module | Function | Contract |
|------|--------|----------|----------|
| Play loop | `aidm/core/play_loop.py` | `execute_turn()` | **MODIFIED** — adds actions_prohibited gate check before resolver dispatch |
| Conditions | `aidm/core/conditions.py` | `get_condition_modifiers()` (or equivalent) | READ ONLY — already computes `actions_prohibited` flag |
| Event log | `aidm/core/event_log.py` | `EventLog`, `to_jsonl()`, `from_jsonl()` | READ ONLY — verify new event type round-trips |
| Replay | `aidm/core/replay_runner.py` | `reduce_event()` | POSSIBLY MODIFIED — may need no-op handler for `action_denied` if event dispatch is type-matched |
| Waypoint tests | `tests/test_waypoint_001.py` | W-0, W-2 | MODIFIED — update for Branch A behavior |

---

## Assumptions to Validate

| # | Assumption | How to validate |
|---|-----------|----------------|
| A1 | `get_condition_modifiers()` (or equivalent) returns a dict/object with `actions_prohibited: bool` | Read `aidm/core/conditions.py` |
| A2 | `execute_turn()` has a clear location before resolver dispatch where the check can be inserted | Read `aidm/core/play_loop.py` |
| A3 | `execute_turn()` has access to the actor entity (not just actor_id) at the point where the check is needed | Read `aidm/core/play_loop.py` — it likely resolves actor from WorldState |
| A4 | The paralyzed condition definition sets `actions_prohibited = True` | Read condition definitions (likely in `aidm/core/conditions.py` or `aidm/data/`) |
| A5 | `EventLog.to_jsonl()` handles arbitrary event types (no whitelist) | Read `aidm/core/event_log.py` |
| A6 | `replay_runner.reduce_event()` either ignores unknown event types or has a passthrough | Read `aidm/core/replay_runner.py` |

If any assumption fails, STOP. Document which assumption failed and why.

---

## Stop Conditions

1. **Any assumption (A1-A6) fails.** Stop, document, escalate.
2. **`actions_prohibited` flag does not exist** in the condition modifier system. If the concept exists under a different name, adapt. If it doesn't exist at all, this is a larger change than scoped — stop and escalate.
3. **`execute_turn()` structure doesn't allow a clean gate check** (e.g., intent routing happens before entity resolution). Stop and document the architectural constraint.
4. **Existing Waypoint tests break in unexpected ways** beyond the anticipated W-2 Branch B→A change. Stop and document.
5. **Scope creep** — any temptation to change condition definitions, add new conditions, or modify resolver internals. This WO adds ONE gate check. That's it.

---

## Implementation Order

1. Validate assumptions A1-A6 by reading the integration seam modules
2. Add the `actions_prohibited` gate check in `execute_turn()` with rejection event emission
3. Write WP2-0 (paralyzed cannot attack)
4. Write WP2-1 (paralyzed cannot cast)
5. Write WP2-2 (healthy entity can act)
6. Write WP2-3 (denial event survives replay)
7. Update `tests/test_waypoint_001.py` W-0 and W-2 for Branch A behavior
8. Write WP2-4 (Waypoint regression — full scenario with new enforcement)
9. Verify replay_runner handles `action_denied` (add no-op handler if needed)
10. Run full test suite — 0 regressions on 6,028 existing tests

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit. Message format: `fix: WO-WAYPOINT-002 — enforce actions_prohibited in play_loop, condition action denial`

All new gate tests must pass. Existing 6,028 tests (including updated Waypoint tests) must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-WAYPOINT-002.md`. 500 words max. Five mandatory sections:

0. **Scope Accuracy** — Did you deliver what was asked? Note any deviations.
1. **Discovery Log** — Anything you found that the dispatch didn't anticipate.
2. **Methodology Challenge** — Hardest part and how you solved it.
3. **Field Manual Entry** — One tradecraft tip for the next builder working in this area.
4. **Builder Radar** (mandatory, 3 labeled lines):
   - **Trap.** Hidden dependency or trap for the next WO.
   - **Drift.** Current drift risk.
   - **Near stop.** What got close to triggering a stop condition.

### Debrief Focus Questions

1. **Condition coverage:** Beyond `paralyzed`, which other conditions in the codebase set `actions_prohibited`? Are they all now correctly blocked?
2. **Return contract:** How did you structure the rejection return to stay consistent with `execute_turn()`'s existing return type?
