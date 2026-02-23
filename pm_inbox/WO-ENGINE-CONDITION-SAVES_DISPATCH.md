# WO-ENGINE-CONDITION-SAVES — CP-18 Condition Save Modifiers

**Issued:** 2026-02-23
**Authority:** CP-17 gate (condition enforcement). Save modifier fields in `ConditionModifiers` (`fort_save_modifier`, `ref_save_modifier`, `will_save_modifier`) are populated by `get_condition_modifiers()` but never applied in `_resolve_save()`.
**Gate:** CP-18 (new gate). Target: 10 tests.
**Blocked by:** Nothing. Parallel with CP-17. Conditions data layer (CP-16) is live. `get_condition_modifiers()` already computes save modifier aggregates.
**Track:** Engine parallel track — no conflict with UI or chargen WOs.

---

## 1. Target Lock

`spell_resolver.py:_resolve_save()` currently computes:

```python
save_bonus = target.get_save_bonus(save_type)
total_roll = base_roll + save_bonus + cover_bonus
```

`TargetStats.get_save_bonus()` returns the entity's static save bonus (Fort/Ref/Will). It does NOT include condition-derived modifiers.

The `ConditionModifiers` dataclass has:
- `fort_save_modifier`: int — aggregated from all active conditions (e.g. shaken: -2, sickened: -2)
- `ref_save_modifier`: int
- `will_save_modifier`: int

`get_condition_modifiers(world_state, target_id)` is already importable from `aidm.core.conditions`. The modifier values are computed and returned correctly — they are simply never read by `_resolve_save()`.

CP-18 wires those modifiers into the save resolution path.

---

## 2. Condition Save Modifier Reference (PHB)

| Condition | Fort | Ref | Will |
|---|---|---|---|
| Shaken | -2 | -2 | -2 (all saves) |
| Frightened | -2 | -2 | -2 (all saves) |
| Panicked | -2 | -2 | -2 (all saves) |
| Sickened | -2 | -2 | -2 (all saves) |
| Exhausted | -2 | -2 | -2 (all saves) |
| Fatigued | 0 | 0 | 0 |
| Cowering | -2 | -2 | -2 |

These are already encoded in `conditions.py` condition data. The `get_condition_modifiers()` aggregation sums them correctly for stacked conditions. No change to conditions.py needed.

---

## 3. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Where to apply | In `_resolve_save()` — query `get_condition_modifiers()` on target, add save-type modifier to `total_roll` | Single choke point. All save resolution passes through this method. |
| 2 | `TargetStats` access | Pass `world_state` into `_resolve_save()` or call `get_condition_modifiers()` before calling `_resolve_save()` and add result to call signature | Option B: pass `condition_save_mod: int = 0` param to `_resolve_save()`. Caller computes modifier; resolver stays pure. |
| 3 | STP transparency | Add condition modifier to `modifiers` list in save STP so the structured truth packet shows the penalty | Consistent with cover_bonus pattern already in the method. |
| 4 | Natural 1/20 override | Natural 1 = always fail, natural 20 = always succeed. Condition modifiers do NOT override this. | PHB p.177. Already implemented — condition modifier only affects `total_roll`, not the nat-1/nat-20 branch. |
| 5 | Zero modifier case | If `condition_save_mod == 0`, STP modifiers list unchanged (no noise entry) | Clean output when no conditions active. |
| 6 | Gate name | CP-18 | Numeric continuation of CP-17. |

---

## 4. Contract Spec

### 4.1 `_resolve_save()` signature change

```python
def _resolve_save(
    self,
    target: TargetStats,
    save_type: SaveType,
    dc: int,
    caster_id: str,
    cover_bonus: int = 0,
    condition_save_mod: int = 0,    # NEW — aggregated condition penalty/bonus
    citations: Tuple[str, ...] = (),
) -> Tuple[bool, int, StructuredTruthPacket]:
```

### 4.2 Modifier application in `_resolve_save()`

```python
base_roll = self._save_rng.randint(1, 20)
save_bonus = target.get_save_bonus(save_type)
total_roll = base_roll + save_bonus + cover_bonus + condition_save_mod  # CHANGED

modifiers = []
if cover_bonus > 0:
    modifiers.append(("cover", cover_bonus))
if condition_save_mod != 0:                                              # NEW
    modifiers.append(("condition", condition_save_mod))
```

### 4.3 Caller site pattern

Every call to `_resolve_save()` that has access to `world_state` and `target_id` must compute and pass the modifier:

```python
# Before calling _resolve_save():
condition_mods = get_condition_modifiers(world_state, target.entity_id)
if save_type == SaveType.FORTITUDE:
    cond_mod = condition_mods.fort_save_modifier
elif save_type == SaveType.REFLEX:
    cond_mod = condition_mods.ref_save_modifier
else:
    cond_mod = condition_mods.will_save_modifier

saved, roll_total, stp = self._resolve_save(
    target=target,
    save_type=save_type,
    dc=dc,
    caster_id=caster_id,
    cover_bonus=cover_bonus,
    condition_save_mod=cond_mod,
    citations=citations,
)
```

---

## 5. Test Spec (Gate CP-18 — 10 tests)

Write `tests/test_engine_gate_cp18.py`:

| ID | Test | Assertion |
|----|------|-----------|
| CP18-01 | Target with `shaken` condition saves vs. Fort DC 15 | Roll total includes -2 modifier; target fails save they would have passed without condition |
| CP18-02 | Target with no conditions saves vs. Fort DC 15 | Roll total unmodified; base behavior preserved |
| CP18-03 | Target with `sickened` saves vs. Will DC 12 | Will save total = roll + will_save + (-2) |
| CP18-04 | STP `modifiers` when condition active | STP contains `("condition", -2)` entry |
| CP18-05 | STP `modifiers` when no condition | STP does NOT contain `"condition"` entry |
| CP18-06 | Natural 20 with shaken | saved = True despite -2 modifier (nat 20 always succeeds) |
| CP18-07 | Natural 1 with high save + no conditions | saved = False (nat 1 always fails) |
| CP18-08 | Stacked conditions (shaken + sickened) | save modifier = -4 (two -2 penalties sum correctly) |
| CP18-09 | Frightened condition | All three save types (fort/ref/will) each get -2 |
| CP18-10 | Regression: existing save resolution tests | All prior SpellResolver save tests PASS |

---

## 6. Implementation Plan

1. **Read** `aidm/core/spell_resolver.py` — locate `_resolve_save()` (line ~737), count all caller sites of `_resolve_save()` in the file
2. **Read** `aidm/core/conditions.py` — confirm `get_condition_modifiers()` import path and return type
3. **Edit** `aidm/core/spell_resolver.py`:
   - Add `condition_save_mod: int = 0` param to `_resolve_save()`
   - Add modifier to `total_roll` computation
   - Add `("condition", condition_save_mod)` to STP modifiers when non-zero
   - At each `_resolve_save()` caller site: query `get_condition_modifiers()`, compute save-type-specific modifier, pass to call
4. **Write** `tests/test_engine_gate_cp18.py` — 10 tests
5. **Run** `pytest tests/test_engine_gate_cp18.py -v` — all pass
6. **Run** full regression — zero new failures

---

## 7. Deliverables Checklist

- [ ] `_resolve_save()` has `condition_save_mod: int = 0` parameter
- [ ] `total_roll` includes `condition_save_mod`
- [ ] STP `modifiers` includes `("condition", mod)` when mod != 0
- [ ] All caller sites pass condition save modifier
- [ ] `tests/test_engine_gate_cp18.py` — 10/10 PASS
- [ ] Zero regressions

## 8. Integration Seams

- **Files modified:** `aidm/core/spell_resolver.py` only
- **Do not modify:** `aidm/core/conditions.py` — data layer stays clean
- **Reuse:** `get_condition_modifiers()` — already used in CP-17 enforcement

## 9. Preflight

```bash
pytest tests/test_engine_gate_cp18.py -v
pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```
