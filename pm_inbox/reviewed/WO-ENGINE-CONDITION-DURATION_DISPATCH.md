# WO-ENGINE-CONDITION-DURATION — CP-19 Condition Duration Auto-Expiry

**Issued:** 2026-02-23
**Authority:** CP-16 data layer + CP-17/CP-18 enforcement gates. `DurationTracker.tick_round()` exists and is fully implemented but is never called at round end. Conditions never expire automatically.
**Gate:** CP-19 (new gate). Target: 12 tests.
**Blocked by:** Nothing. Parallel with CP-17 and CP-18. `DurationTracker` module is complete and independently testable.
**Track:** Engine parallel track — no conflict with UI or chargen WOs.

---

## 1. Target Lock

`duration_tracker.py` contains a complete `DurationTracker` class with:
- `tick_round()` — decrements all non-permanent effects, returns list of expired `ActiveSpellEffect` objects
- `remove_effect(effect_id)` — removes from internal tracking structures
- `from_dict()` / `to_dict()` — serialization for WorldState persistence

`play_loop.py` uses the tracker to add effects during spell casting (lines ~512-557) and to break concentration when casters take damage (lines ~619-685). However, `tick_round()` is never called anywhere in the file.

**Consequence:** Conditions from spells with `duration_rounds > 0` are permanent in practice. A `shaken` condition from a 1-round spell lasts the entire encounter.

CP-19 wires `tick_round()` into the turn-end path so that at the end of each actor's turn, effects with that actor as target (or effects where the round boundary is crossed) decrement and expire. When an effect expires, the condition is removed from the entity and a `condition_expired` event is emitted.

---

## 2. Round Boundary Definition

PHB: "A round is 6 seconds. Each character gets one turn per round." For simplicity and determinism:

**Expiry model:** After the LAST actor in the initiative order completes their turn, the round increments. At that point, `tick_round()` fires for all tracked effects.

**Implementation:** In `execute_turn()`, after the final `turn_end` event is emitted, check whether the current actor is the last in initiative order. If yes, call `tick_round()`, process expired effects, remove conditions, emit `condition_expired` events, persist updated tracker back to `active_combat`.

---

## 3. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Trigger point | End of last actor's turn in initiative order | PHB round boundary. Single call per round — no per-turn ticking complexity. |
| 2 | "Last actor" detection | `turn_ctx.turn_index % len(initiative_order) == len(initiative_order) - 1` | Initiative order length is available in `active_combat["initiative_order"]`. Handles multi-round encounters. |
| 3 | Expiry action | Remove condition from entity dict + emit `condition_expired` sensor event | Mirrors existing `condition_removed` pattern (concentration break path, line ~664). |
| 4 | Event type | `"condition_expired"` (distinct from `"condition_removed"`) | Reason differentiation: expired vs. manually removed vs. concentration break. |
| 5 | No active_combat | If `active_combat` is None (out-of-combat), tick is skipped silently | Duration tracking only meaningful in combat. |
| 6 | Permanent effects | `is_permanent()` → `rounds_remaining == -1`. `tick_round()` already skips these (line ~202 in duration_tracker.py). | No change needed. |
| 7 | Tracker persistence | After `tick_round()`, serialize updated tracker back to `active_combat["duration_tracker"]` | Existing serialization pattern already in place for concentration breaks. |
| 8 | Multiple conditions per effect | An `ActiveSpellEffect` has one `condition_applied` field. Multiple conditions = multiple effects. Each expires independently. | Existing data model constraint — no change needed. |

---

## 4. Contract Spec

### 4.1 Round-end expiry hook in `execute_turn()`

```python
# play_loop.py — after turn_end event is appended, before return

# CP-19: Round-end condition expiry
active_combat_data = world_state.active_combat or {}
initiative_order = active_combat_data.get("initiative_order", [])
if initiative_order:
    last_actor_index = (len(initiative_order) - 1)
    current_position = turn_ctx.turn_index % len(initiative_order) if len(initiative_order) > 0 else 0
    if current_position == last_actor_index:
        # End of round — tick duration tracker
        duration_tracker = _get_or_create_duration_tracker(world_state)
        expired_effects = duration_tracker.tick_round()

        if expired_effects:
            entities = deepcopy(world_state.entities)
            for effect in expired_effects:
                if effect.condition_applied and effect.target_id in entities:
                    target_conditions = entities[effect.target_id].get(EF.CONDITIONS, {})
                    if isinstance(target_conditions, dict) and effect.condition_applied in target_conditions:
                        del target_conditions[effect.condition_applied]
                        events.append(Event(
                            event_id=current_event_id,
                            event_type="condition_expired",
                            timestamp=timestamp + 0.25,
                            payload={
                                "entity_id": effect.target_id,
                                "condition": effect.condition_applied,
                                "spell_id": effect.spell_id,
                                "spell_name": effect.spell_name,
                                "reason": "duration_elapsed",
                            },
                        ))
                        current_event_id += 1

            # Persist updated tracker and mutated entities
            active_combat_data = deepcopy(active_combat_data)
            active_combat_data["duration_tracker"] = duration_tracker.to_dict()
            updated_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=entities,
                active_combat=active_combat_data,
            )
```

### 4.2 `condition_expired` event shape

```python
{
    "entity_id": str,         # target whose condition expired
    "condition": str,         # condition name (e.g. "shaken")
    "spell_id": str,          # originating spell
    "spell_name": str,        # human-readable spell name
    "reason": "duration_elapsed"
}
```

---

## 5. Test Spec (Gate CP-19 — 12 tests)

Write `tests/test_engine_gate_cp19.py`:

| ID | Test | Assertion |
|----|------|-----------|
| CP19-01 | 1-round spell applied at turn 0, 2 actors — condition still present at start of round 1 | Entity still has condition after first actor's turn |
| CP19-02 | 1-round spell, 2 actors — `condition_expired` emitted after last actor turn | Round-end tick fires; event present in result |
| CP19-03 | Expired condition removed from entity dict | Entity has no `shaken` key after expiry |
| CP19-04 | `condition_expired` event shape | Contains entity_id, condition, spell_name, reason |
| CP19-05 | 2-round spell, 2 actors — survives round 1, expires after round 2 | Condition present after 2 full turns; gone after 4 |
| CP19-06 | Permanent effect (rounds_remaining=-1) | Never expires; entity retains condition after 5 rounds |
| CP19-07 | Duration tracker persisted to active_combat | `active_combat["duration_tracker"]` reflects updated rounds_remaining |
| CP19-08 | No active_combat | `execute_turn()` without active_combat — no crash, no tick |
| CP19-09 | Multiple spells on same target | Each effect expires independently on its own round |
| CP19-10 | Condition removed by other means first | If condition already absent when effect expires, no crash (no double-remove) |
| CP19-11 | CP-17 regression: `action_denied` still fires for stunned entity | Existing gate CP-17 behavior unaffected |
| CP19-12 | Regression: concentration break still emits `condition_removed` | Concentration path unchanged |

---

## 6. Implementation Plan

1. **Read** `aidm/core/play_loop.py` — locate `execute_turn()` return path (after `turn_end` event, before final `return TurnResult`). Identify `turn_ctx.turn_index`, `initiative_order` access pattern.
2. **Read** `aidm/core/duration_tracker.py` — confirm `tick_round()` return type and `to_dict()` serialization shape.
3. **Edit** `aidm/core/play_loop.py`:
   - Add round-end expiry hook after `turn_end` event emission
   - Wire `_get_or_create_duration_tracker()` → `tick_round()` → condition removal → `condition_expired` events
   - Persist updated tracker and entities to `updated_state`
4. **Write** `tests/test_engine_gate_cp19.py` — 12 tests
5. **Run** `pytest tests/test_engine_gate_cp19.py -v` — all pass
6. **Run** full regression — zero new failures

---

## 7. Deliverables Checklist

- [ ] Round-end expiry hook in `execute_turn()` fires on last actor's turn
- [ ] `DurationTracker.tick_round()` called once per round
- [ ] Expired conditions removed from entity dict
- [ ] `condition_expired` events emitted with correct payload
- [ ] Updated tracker serialized to `active_combat["duration_tracker"]`
- [ ] `tests/test_engine_gate_cp19.py` — 12/12 PASS
- [ ] Zero regressions (concentration break path untouched)

## 8. Integration Seams

- **Files modified:** `aidm/core/play_loop.py` only
- **Do not modify:** `aidm/core/duration_tracker.py` — already complete
- **Do not modify:** `aidm/core/conditions.py` — data layer stays clean
- **Reuse:** `_get_or_create_duration_tracker()`, `DurationTracker.tick_round()`, `DurationTracker.to_dict()`, existing `condition_removed` event pattern

## 9. Preflight

```bash
pytest tests/test_engine_gate_cp19.py -v
pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```
