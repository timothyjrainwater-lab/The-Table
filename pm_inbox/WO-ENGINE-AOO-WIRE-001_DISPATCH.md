# WO-ENGINE-AOO-WIRE-001 — AoO Ranged/Spell Triggers (CP-23)

**Issued:** 2026-02-23
**Authority:** Engine audit gap — `check_aoo_triggers()` stubs ranged and spell triggers as TODO CP-15. PHB p.137: using a ranged weapon in a threatened square and casting a spell in a threatened square both provoke AoO. Currently neither fires.
**Gate:** CP-23 (new). Target: 10 tests.
**Blocked by:** CP-17 (AoO infrastructure — `resolve_aoo_sequence()` must be live). CP-17 ACCEPTED ✅.

---

## 1. Gap

`check_aoo_triggers()` in `aidm/combat/aoo_resolver.py` has two stubs:

```python
# TODO CP-15: ranged attack in threatened square triggers AoO
# TODO CP-15: casting spell in threatened square triggers AoO
```

Both stubs return without firing an AoO. PHB rules:
- **Ranged in threatened square:** Drawing and firing a ranged weapon while an enemy threatens your square → AoO from all threatening enemies (unless Combat Reflexes and not already used).
- **Casting in threatened square:** Casting any spell with a casting time of 1 standard action or longer → AoO from all threatening enemies. (Exceptions: Concentration check can substitute if defender is wounded mid-cast, but that's CP-24 territory.)

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Detection | In `check_aoo_triggers()`, check `intent_type` of current action. `RangedAttackIntent` → check if actor is threatened. `CastSpellIntent` (standard action spell) → check if actor is threatened. |
| 2 | Threatened check | Actor is threatened if any enemy occupies an adjacent square AND that enemy has not used all AoO allocations for the round. Use existing `_get_threatening_enemies(actor_id, world_state)` helper. |
| 3 | AoO resolution | Call existing `resolve_aoo_sequence()` with list of threatening enemies. Already handles attack roll + damage. |
| 4 | Spell concentration | If actor takes damage from AoO during cast: concentration check DC = 10 + damage. On fail: spell lost, intent returns `spell_interrupted`. On pass: spell proceeds. This is the full rule — implement it. |
| 5 | Scope | All ranged attacks + all standard-action spells. Quickened spells (free action) do not provoke — check `CastSpellIntent.quickened` flag if present, else assume standard. |

## 3. Contract Spec

### check_aoo_triggers() additions

```python
def check_aoo_triggers(intent, actor_id, world_state) -> list[AoOResult]:
    triggers = []

    if isinstance(intent, RangedAttackIntent):
        if _is_threatened(actor_id, world_state):
            triggers.extend(_resolve_threatening_aoos(actor_id, world_state))

    if isinstance(intent, CastSpellIntent) and not getattr(intent, 'quickened', False):
        if _is_threatened(actor_id, world_state):
            aoo_results = _resolve_threatening_aoos(actor_id, world_state)
            triggers.extend(aoo_results)
            # concentration check if any AoO hit
            total_damage = sum(r.damage for r in aoo_results if r.hit)
            if total_damage > 0:
                triggers.append(_concentration_check(actor_id, total_damage, world_state))

    return triggers
```

### Events emitted

| Event | When |
|-------|------|
| `aoo_triggered` | AoO fires (existing) |
| `spell_interrupted` | Concentration check failed |
| `concentration_check` | DC + roll result (informational) |

## 4. Test Spec (Gate CP-23 — 10 tests)

File: `tests/test_engine_gate_cp23.py` (new)

| ID | Test |
|----|------|
| CP23-01 | Ranged attack in threatened square → `aoo_triggered` event fires |
| CP23-02 | Ranged attack NOT in threatened square → no AoO |
| CP23-03 | Spell cast (standard action) in threatened square → `aoo_triggered` fires |
| CP23-04 | Spell cast NOT in threatened square → no AoO |
| CP23-05 | Quickened spell → no AoO regardless of threatened status |
| CP23-06 | AoO hit during cast, damage > 0 → `concentration_check` event emitted |
| CP23-07 | Concentration check fail → `spell_interrupted` event, spell not resolved |
| CP23-08 | Concentration check pass (high roll) → spell proceeds normally |
| CP23-09 | Multiple threatening enemies each get AoO opportunity (Combat Reflexes scope: one per enemy unless CR feat) |
| CP23-10 | Zero regressions on CP-17 gate (15/15) and existing AoO tests |

## 5. Implementation Plan

1. Read `aidm/combat/aoo_resolver.py` (full — stubs + existing machinery), `aidm/schemas/intents.py` (`RangedAttackIntent`, `CastSpellIntent`)
2. Implement ranged trigger: `isinstance(intent, RangedAttackIntent)` + `_is_threatened()` check → `resolve_aoo_sequence()`
3. Implement spell trigger: `isinstance(intent, CastSpellIntent)` + not quickened + threatened → AoO → concentration check
4. Add `_concentration_check(actor_id, damage, world_state)` helper: DC = 10 + damage, actor's Concentration skill + d20
5. Emit `spell_interrupted` on fail, proceed on pass
6. Write 10 tests to `tests/test_engine_gate_cp23.py`
7. `pytest tests/test_engine_gate_cp23.py -v` — 10/10 PASS
8. `pytest tests/ -x -q` — zero new regressions

## 6. Deliverables

- [ ] `RangedAttackIntent` in threatened square → AoO fires
- [ ] `CastSpellIntent` (standard action) in threatened square → AoO fires
- [ ] Quickened spells exempt
- [ ] Concentration check on AoO hit during cast
- [ ] `spell_interrupted` event on check failure
- [ ] Gate CP-23: 10/10 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `aidm/combat/aoo_resolver.py` only (stubs → implementation)
- **Do not modify:** `attack_resolver.py`, `spell_resolver.py`, UI files
- **Deferred:** Withdrawal action (avoids AoO on first square), Combat Reflexes multi-AoO (CP-24)

## Preflight

```bash
pytest tests/test_engine_gate_cp23.py -v
pytest tests/ -x -q --ignore=tests/test_engine_gate_cp23.py
```
