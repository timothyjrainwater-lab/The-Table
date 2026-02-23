# WO-ENGINE-LEVELUP-WIRE — XP Award and Level-Up Post-Combat Dispatcher

**Issued:** 2026-02-23
**Authority:** `experience_resolver.py` has `award_xp()` and `apply_level_up()` fully implemented but not called anywhere. `check_level_up()` is a stub returning `None`. XP and level progression are completely disconnected from the event loop.
**Gate:** XP-01 (new gate). Target: 14 tests.
**Blocked by:** Nothing. CHARGEN PHASE 3 COMPLETE — `level_up()` delta builder and `apply_level_up()` resolver both ship-ready.
**Track:** Engine parallel track — no conflict with UI, chargen, or condition WOs.

---

## 1. Target Lock

After an entity is defeated in combat, `entity_defeated` events exist in the event log but no XP is awarded, no level-up check runs, and no `level_up_applied` events are emitted. The gap covers three items:

1. **`check_level_up()` stub** — `experience_resolver.py:160` returns `None` unconditionally. Must implement XP threshold lookup against `LEVEL_THRESHOLDS` table and return `LevelUpResult` when threshold is crossed.
2. **Post-combat XP dispatcher** — A function called after each turn (or after `entity_defeated` events) that awards XP to surviving party members and checks for level-ups.
3. **Level-up event emission** — When `apply_level_up()` is called, the caller must emit a `level_up_applied` event carrying the delta for narration and UI sync.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | XP award trigger | After entity_defeated event within execute_turn() — check if any entity was defeated this turn and award XP | Single integration point. No separate pass needed. |
| 2 | XP amount | PHB Table 3-1: CR-based XP per encounter. Standard XP = 300 × CR / party_size, adjusted by party level vs. CR difference | Implement full Table 3-1 lookup. |
| 3 | Party detection | All entities on opposing team that are alive at end of turn = surviving party | World state has TEAM field on all entities. |
| 4 | Level-up check timing | After XP award — check all XP recipients immediately | Same turn, same event batch. |
| 5 | Level-up class selection | For multiclass: level up the favored class if equal XP penalty would apply; otherwise, the class with fewest levels | PHB p.60 simplified. Store in entity `EF.FAVORED_CLASS`. |
| 6 | `check_level_up()` completion | Return `LevelUpResult` when `entity.get(EF.XP, 0) >= LEVEL_THRESHOLDS[entity.get(EF.LEVEL, 1) + 1]` | XP threshold table already in experience_resolver.py. |
| 7 | Events emitted | `xp_awarded` event per entity + `level_up_applied` event if level crossed | Consistent with sensor event pattern. |
| 8 | Level cap | No level-up event if entity already at level 20 | PHB cap. |

---

## 3. Contract Spec

### 3.1 Complete `check_level_up()` in `experience_resolver.py`

```python
def check_level_up(entity: Dict[str, Any]) -> Optional[LevelUpResult]:
    current_level = entity.get(EF.LEVEL, 1)
    current_xp = entity.get(EF.XP, 0)
    if current_level >= 20:
        return None
    next_threshold = LEVEL_THRESHOLDS.get(current_level + 1)
    if next_threshold is None or current_xp < next_threshold:
        return None
    return LevelUpResult(
        entity_id=entity.get(EF.ENTITY_ID, "unknown"),
        old_level=current_level,
        new_level=current_level + 1,
        xp_at_levelup=current_xp,
        threshold_met=next_threshold,
    )
```

### 3.2 `_award_xp_for_defeat()` helper in `play_loop.py`

Called from `execute_turn()` when an `entity_defeated` event is generated:

```python
def _award_xp_for_defeat(
    world_state: WorldState,
    defeated_entity_id: str,
    events: List[Event],
    current_event_id: int,
    timestamp: float,
) -> Tuple[WorldState, int]:
    """Award XP to opposing team entities and check for level-ups."""
    defeated = world_state.entities.get(defeated_entity_id, {})
    defeated_team = defeated.get(EF.TEAM, "")
    defeated_cr = defeated.get(EF.CHALLENGE_RATING, 0)

    # Identify surviving opposing party
    survivors = [
        (eid, e) for eid, e in world_state.entities.items()
        if e.get(EF.TEAM) != defeated_team
        and not e.get(EF.DEFEATED, False)
        and eid != defeated_entity_id
    ]
    if not survivors:
        return world_state, current_event_id

    xp_per_entity = _calculate_xp(defeated_cr, len(survivors))
    entities = deepcopy(world_state.entities)

    for eid, entity in survivors:
        updated_entity = award_xp(entities[eid], xp_per_entity)
        entities[eid] = updated_entity

        events.append(Event(
            event_id=current_event_id,
            event_type="xp_awarded",
            timestamp=timestamp + 0.3,
            payload={
                "entity_id": eid,
                "xp_amount": xp_per_entity,
                "source": f"defeat:{defeated_entity_id}",
                "new_total": updated_entity.get(EF.XP, 0),
            },
        ))
        current_event_id += 1

        level_result = check_level_up(updated_entity)
        if level_result:
            leveled_entity, apply_result = apply_level_up(updated_entity, _best_class_to_level(updated_entity))
            entities[eid] = leveled_entity
            events.append(Event(
                event_id=current_event_id,
                event_type="level_up_applied",
                timestamp=timestamp + 0.31,
                payload={
                    "entity_id": eid,
                    "old_level": level_result.old_level,
                    "new_level": level_result.new_level,
                    "hp_gained": apply_result.hp_gained,
                    "class_leveled": apply_result.class_name,
                    "new_bab": apply_result.new_bab,
                },
            ))
            current_event_id += 1

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
    )
    return updated_state, current_event_id
```

### 3.3 `xp_awarded` event shape

```python
{
    "entity_id": str,
    "xp_amount": int,
    "source": str,         # e.g. "defeat:goblin_01"
    "new_total": int,
}
```

### 3.4 `level_up_applied` event shape

```python
{
    "entity_id": str,
    "old_level": int,
    "new_level": int,
    "hp_gained": int,
    "class_leveled": str,
    "new_bab": int,
}
```

---

## 4. Test Spec (Gate XP-01 — 14 tests)

Write `tests/test_engine_gate_xp01.py`:

| ID | Test | Assertion |
|----|------|-----------|
| XP-01 | `check_level_up()` with XP below threshold | Returns None |
| XP-02 | `check_level_up()` with XP at exact threshold | Returns LevelUpResult with correct new_level |
| XP-03 | `check_level_up()` at level 20 | Returns None (cap) |
| XP-04 | `award_xp()` adds to existing XP total | Entity XP increases correctly |
| XP-05 | `execute_turn()` with entity_defeated: `xp_awarded` event emitted | Event present in TurnResult.events |
| XP-06 | XP amount correct for CR 1 vs. 2-person party | Per PHB Table 3-1 adjusted split |
| XP-07 | Only surviving opposing team members get XP | Defeated entity team does not receive XP |
| XP-08 | Level threshold crossing triggers `level_up_applied` event | Event present when XP crosses threshold |
| XP-09 | `level_up_applied` event has correct hp_gained > 0 | Delta properly computed |
| XP-10 | Entity at level 20 receives XP but no level_up_applied | Cap enforced; xp_awarded still fires |
| XP-11 | No surviving party — no xp_awarded event | Empty survivor list handled gracefully |
| XP-12 | Entity HP_MAX and HP_CURRENT updated after level-up | World state entity reflects new HP |
| XP-13 | Multiple defeats same turn | XP awarded once per defeat event |
| XP-14 | Regression: existing execute_turn() tests for attack resolution | All PASS — XP path only activates on entity_defeated |

---

## 5. Implementation Plan

1. **Read** `aidm/core/experience_resolver.py` — locate `check_level_up()` stub (line 160), `LEVEL_THRESHOLDS` dict, `LevelUpResult` dataclass, `apply_level_up()` signature
2. **Read** `aidm/core/play_loop.py` — locate `entity_defeated` event emission (search for `"entity_defeated"`), confirm current event structure
3. **Edit** `aidm/core/experience_resolver.py` — implement `check_level_up()` (complete stub)
4. **Edit** `aidm/core/play_loop.py`:
   - Import `award_xp`, `check_level_up`, `apply_level_up` from experience_resolver
   - Add `_award_xp_for_defeat()` helper
   - Add `_calculate_xp(cr, party_size)` helper (PHB Table 3-1)
   - Add `_best_class_to_level(entity)` helper (favored class or max-level class)
   - After each `entity_defeated` event emission in execute_turn(), call `_award_xp_for_defeat()`
5. **Write** `tests/test_engine_gate_xp01.py` — 14 tests
6. **Run** `pytest tests/test_engine_gate_xp01.py -v` — all pass
7. **Run** full regression — zero new failures

---

## 6. Deliverables Checklist

- [ ] `check_level_up()` implemented (no longer a stub)
- [ ] `_award_xp_for_defeat()` helper in `play_loop.py`
- [ ] `xp_awarded` events emitted after entity_defeated
- [ ] `level_up_applied` events emitted when threshold crossed
- [ ] `tests/test_engine_gate_xp01.py` — 14/14 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `aidm/core/experience_resolver.py`, `aidm/core/play_loop.py`
- **Do not modify:** `aidm/chargen/builder.py`, `aidm/chargen/companions.py`
- **Reuse:** `award_xp()`, `apply_level_up()`, `EF.XP`, `EF.LEVEL`, `EF.TEAM`, `EF.CHALLENGE_RATING`

## 8. Note: Companion Wiring Already Complete

`spawn_companion()` is already wired into `execute_turn()` for `SummonCompanionIntent`. No separate companion-wire WO is needed. WO-ENGINE-COMPANION-WIRE is superseded by this finding.

## 9. Preflight

```bash
pytest tests/test_engine_gate_xp01.py -v
pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```
