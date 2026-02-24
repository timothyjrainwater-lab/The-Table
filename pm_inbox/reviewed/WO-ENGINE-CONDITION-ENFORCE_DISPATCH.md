# WO-ENGINE-CONDITION-ENFORCE — CP-17 Condition Enforcement

**Issued:** 2026-02-23
**Authority:** CP-17 deferred gate. Conditions system CP-16 is data-only — enforcement explicitly deferred here.
**Gate:** CP-17 (new gate). Target: 15 tests.
**Blocked by:** Nothing. CP-16 ACCEPTED. Condition schema, apply/remove/query all live.
**Track:** Engine parallel track — no conflict with UI or chargen WOs.

---

## 1. Target Lock

CP-16 delivered a complete condition data model: 14 conditions, mechanical modifiers, apply/remove/query functions. The `ConditionModifiers` dataclass has `actions_prohibited`, `movement_prohibited`, `standing_triggers_aoo`, `auto_hit_if_helpless`, and `loses_dex_to_ac` flags — all metadata-only with no enforcement.

CP-17 wires those flags into the resolvers:

1. **Action gate** — stunned/dazed/nauseated/paralyzed/unconscious entities cannot act. `execute_turn()` already has a partial gate (line ~820). Harden it to cover all `actions_prohibited` conditions.
2. **Prone AoO** — standing from prone provokes an AoO. `standing_triggers_aoo` flag must be checked when a prone entity attempts to stand.
3. **Helpless auto-hit** — melee attacks against helpless entities automatically hit (no attack roll). `auto_hit_if_helpless` flag must short-circuit attack resolution.
4. **Loses DEX to AC** — flat-footed, helpless, stunned entities lose DEX bonus to AC. `loses_dex_to_ac` flag must be checked in AC calculation.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Action gate location | `execute_turn()` in `play_loop.py` — early exit before action dispatch | Single choke point. No resolver changes needed. |
| 2 | Prone AoO trigger | In `execute_turn()` when action is `stand` — call `trigger_aoo()` if `standing_triggers_aoo` | Reuse existing AoO infrastructure (CP-15). |
| 3 | Helpless auto-hit | In `attack_resolver.py` — skip attack roll, set hit=True before damage calc | Localised to attack resolution path only. |
| 4 | Loses DEX to AC | In `ac_calculator.py` or equivalent — query `get_condition_modifiers()`, skip DEX mod if flag set | Already has condition modifier query pattern. |
| 5 | Enforcement error output | Emit `ACTION_DENIED` sensor event with `reason="condition:{condition_type}"` | Consistent with existing denial pattern. |
| 6 | Scope | CP-14 action types: standard, move, full. Free actions not gated. | PHB p.144: free actions not restricted by most conditions. |

---

## 3. Contract Spec

### 3.1 Action Gate (execute_turn)

```python
# play_loop.py — early in execute_turn(), after action is parsed
condition_mods = get_condition_modifiers(world_state, actor_id)

if condition_mods.actions_prohibited:
    # Emit denial sensor event
    sensor_fn(SensorEvent(
        event_type="ACTION_DENIED",
        actor_id=actor_id,
        reason=f"condition:{_get_prohibiting_condition(world_state, actor_id)}"
    ))
    return _noop_turn_result(world_state, turn_ctx)
```

### 3.2 Prone Stand AoO

```python
# play_loop.py — when action_type resolves to "stand" intent
if has_condition(world_state, actor_id, "prone"):
    condition_mods = get_condition_modifiers(world_state, actor_id)
    if condition_mods.standing_triggers_aoo:
        world_state = trigger_aoo_for_standing(world_state, actor_id, rng)
```

### 3.3 Helpless Auto-Hit

```python
# attack_resolver.py — before attack roll
target_mods = get_condition_modifiers(world_state, target_id)
if target_mods.auto_hit_if_helpless:
    hit = True  # Skip roll entirely
    # Melee only — PHB p.153
    if intent.attack_type != "melee":
        hit = None  # Still roll for ranged vs helpless
```

### 3.4 Loses DEX to AC

```python
# AC calculation path
condition_mods = get_condition_modifiers(world_state, entity_id)
dex_mod = entity.get(EF.DEX_MOD, 0)
effective_dex_mod = 0 if condition_mods.loses_dex_to_ac else dex_mod
```

---

## 4. Test Spec (Gate CP-17 — 15 tests)

| ID | Test | Assertion |
|----|------|-----------|
| CP17-01 | Stunned entity attempts action | `ACTION_DENIED` event emitted, turn returns noop |
| CP17-02 | Dazed entity attempts standard action | `ACTION_DENIED` emitted |
| CP17-03 | Paralyzed entity attempts action | `ACTION_DENIED` emitted |
| CP17-04 | Unconscious entity attempts action | `ACTION_DENIED` emitted |
| CP17-05 | Prone entity stands — no enemies adjacent | No AoO triggered |
| CP17-06 | Prone entity stands — enemy adjacent | AoO triggered against standing entity |
| CP17-07 | Helpless entity targeted by melee | Attack hits without roll (auto_hit=True) |
| CP17-08 | Helpless entity targeted by ranged | Attack still rolls (ranged vs helpless still rolls) |
| CP17-09 | Flat-footed entity attacked | DEX mod not applied to AC |
| CP17-10 | Stunned entity attacked | DEX mod not applied to AC |
| CP17-11 | Normal entity attacked | DEX mod applied normally |
| CP17-12 | Entity with no conditions | No enforcement, normal action flow |
| CP17-13 | Condition removed mid-combat | Next turn: no longer gated |
| CP17-14 | ACTION_DENIED sensor event shape | Contains actor_id, reason with condition name |
| CP17-15 | Regression: existing attack tests | All prior attack resolver tests still PASS |

---

## 5. Implementation Plan

1. **Read** `aidm/core/play_loop.py` — locate `execute_turn()`, find existing actions_prohibited gate (~line 820), understand action dispatch flow
2. **Read** `aidm/core/attack_resolver.py` — locate attack roll section, understand hit/miss flow
3. **Read** AC calculation path — locate where DEX mod is applied to AC
4. **Edit** `play_loop.py` — harden action gate, add prone-stand AoO hook
5. **Edit** `attack_resolver.py` — helpless auto-hit, loses_dex_to_ac
6. **Write** `tests/test_engine_gate_cp17.py` — 15 tests
7. **Run** `pytest tests/test_engine_gate_cp17.py -v` — all pass
8. **Run** full regression — zero new failures

---

## 6. Deliverables Checklist

- [ ] `play_loop.py`: action gate covers all `actions_prohibited` conditions
- [ ] `play_loop.py`: prone stand triggers AoO when `standing_triggers_aoo` set
- [ ] `attack_resolver.py`: helpless target auto-hit (melee only)
- [ ] AC path: `loses_dex_to_ac` flag suppresses DEX mod
- [ ] `ACTION_DENIED` sensor event emitted with condition reason
- [ ] `tests/test_engine_gate_cp17.py` — 15/15 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `aidm/core/play_loop.py`, `aidm/core/attack_resolver.py`, AC calculation file (TBD — read first)
- **Do not modify:** `aidm/core/conditions.py` — data layer stays clean
- **Do not modify:** condition schema or EF constants
- **Reuse:** `get_condition_modifiers()`, `has_condition()`, `trigger_aoo()` (CP-15)

## 8. Preflight

```bash
pytest tests/test_engine_gate_cp17.py -v
pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```
