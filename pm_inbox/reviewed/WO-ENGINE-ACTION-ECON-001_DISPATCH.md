# WO-ENGINE-ACTION-ECON-001 — Action Economy Gate (CP-24)

**Issued:** 2026-02-23
**Authority:** Engine audit gap — no gate validates that entities cannot exceed their per-round action budget. PHB p.127: each entity gets 1 standard, 1 move, 1 swift, unlimited free actions per round. Currently nothing prevents two standard actions in one turn.
**Gate:** CP-24 (new). Target: 12 tests.
**Blocked by:** CP-17 (action gate infrastructure). CP-17 ACCEPTED ✅.

---

## 1. Gap

`execute_turn()` routes intents but does not track per-round action consumption. An entity can theoretically execute two `AttackIntent`s (both standard actions) in one turn. No `ACTION_DENIED` fires for economy violations. PHB action types:

| Type | Budget | Examples |
|------|--------|---------|
| Standard | 1/round | Attack, cast spell, use item, charge (replaces move too) |
| Move | 1/round | Move speed, draw weapon, stand from prone |
| Swift | 1/round | Some spells, quickened spells |
| Free | Unlimited | Drop item, speak, 5-foot step (replaces move) |
| Full-round | Uses std+move | Full attack, run, coup de grace |

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Tracking structure | `ActionBudget` dataclass on `WorldState` per active turn: `{standard_used: bool, move_used: bool, swift_used: bool, full_round_used: bool}`. Reset at turn start. |
| 2 | Intent → action type map | `ACTION_TYPES: dict[type, str]` in `action_economy.py`. Maps intent class → `standard|move|swift|free|full_round`. |
| 3 | Enforcement | At top of intent resolution in `execute_turn()`: check budget. If slot used → emit `ACTION_DENIED` with `reason: "action_economy"`. |
| 4 | Full-round | Consuming `full_round` also marks `standard_used = True` and `move_used = True` (PHB: full-round replaces both). |
| 5 | 5-foot step | Free action but mutually exclusive with move action in same turn. Track `five_foot_step_used` separately. If `move_used` already, deny 5-foot step and vice versa. |
| 6 | Charge | Standard+move in one action. Mark both used. |

## 3. Contract Spec

### ActionBudget

```python
@dataclass
class ActionBudget:
    standard_used: bool = False
    move_used: bool = False
    swift_used: bool = False
    full_round_used: bool = False
    five_foot_step_used: bool = False

    def can_use(self, action_type: str) -> bool: ...
    def consume(self, action_type: str) -> None: ...
```

### ACTION_TYPES mapping (representative)

```python
ACTION_TYPES = {
    AttackIntent: 'standard',
    CastSpellIntent: 'standard',      # quickened → 'swift'
    MoveIntent: 'move',
    FullAttackIntent: 'full_round',
    FiveFootStepIntent: 'five_foot_step',
    DrawWeaponIntent: 'move',
    StandFromProneIntent: 'move',
    GrappleIntent: 'standard',
    GrappleEscapeIntent: 'standard',
}
```

### Events

| Event | When |
|-------|------|
| `ACTION_DENIED` | Economy slot already consumed. `reason: "action_economy"`, `slot: "standard"` etc. |

## 4. Test Spec (Gate CP-24 — 12 tests)

File: `tests/test_engine_gate_cp24.py` (new)

| ID | Test |
|----|------|
| CP24-01 | `ActionBudget` dataclass exists with correct fields |
| CP24-02 | `can_use('standard')` → False after standard consumed |
| CP24-03 | Second `AttackIntent` in same turn → `ACTION_DENIED` with `reason: action_economy` |
| CP24-04 | Standard + move both allowed in same turn |
| CP24-05 | `FullAttackIntent` marks standard + move both used |
| CP24-06 | After full-round, move action denied |
| CP24-07 | Swift action consumed → second swift denied |
| CP24-08 | Quickened spell uses swift slot, not standard |
| CP24-09 | 5-foot step after move → denied |
| CP24-10 | Move after 5-foot step → denied |
| CP24-11 | Budget resets at turn start (new turn allows full budget) |
| CP24-12 | Zero regressions on CP-17 (15/15) and existing execute_turn tests |

## 5. Implementation Plan

1. Read `aidm/core/play_loop.py` (`execute_turn()` — full turn resolution flow), `aidm/schemas/intents.py` (all intent types)
2. Create `aidm/combat/action_economy.py`: `ActionBudget` dataclass + `ACTION_TYPES` map + `check_economy()` function
3. Add `current_budget: Optional[ActionBudget]` to `WorldState` (None when not in turn)
4. At turn start in `execute_turn()`: initialize budget
5. Before each intent resolution: `check_economy(intent, budget)` → if denied, emit `ACTION_DENIED`, return early
6. After intent resolves: `budget.consume(action_type)`
7. Quickened spell check: `if getattr(intent, 'quickened', False)` → `action_type = 'swift'`
8. Write 12 tests to `tests/test_engine_gate_cp24.py`
9. `pytest tests/test_engine_gate_cp24.py -v` — 12/12 PASS
10. `pytest tests/ -x -q` — zero new regressions

## 6. Deliverables

- [ ] `ActionBudget` dataclass in `aidm/combat/action_economy.py`
- [ ] `ACTION_TYPES` intent → slot map
- [ ] Budget initialized at turn start, reset each turn
- [ ] Economy enforcement before intent resolution in `execute_turn()`
- [ ] `ACTION_DENIED` with `reason: action_economy` on violation
- [ ] Full-round consumes standard + move
- [ ] 5-foot step / move mutual exclusion
- [ ] Gate CP-24: 12/12 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `aidm/core/play_loop.py` (budget init + check + consume), `aidm/core/worldstate.py` (`current_budget` field), new `aidm/combat/action_economy.py`
- **Do not modify:** Individual resolver files (`attack_resolver.py`, `spell_resolver.py`), UI files
- **Note:** This WO makes previously silent bugs into hard denials. Gold master regeneration likely required for any test that assumed two standard actions were silently ignored.

## Preflight

```bash
pytest tests/test_engine_gate_cp24.py -v
pytest tests/ -x -q --ignore=tests/test_engine_gate_cp24.py
```
