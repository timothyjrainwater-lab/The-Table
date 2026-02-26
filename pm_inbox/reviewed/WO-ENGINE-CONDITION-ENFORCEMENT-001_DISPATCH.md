# WO-ENGINE-CONDITION-ENFORCEMENT-001 — Wire Condition Enforcement into Movement + Action Economy
## Status: DISPATCH-READY
## Priority: HIGH
## Closes: FINDING-ENGINE-CONDITION-ENFORCEMENT-001 (partial — movement + action prohibition; AoO flat_footed deferred)

---

## Context

CP-16 (CONDITIONS-BLIND-DEAF-001) deliberately left condition enforcement deferred. The `ConditionModifiers` dataclass documents this explicitly:

```python
# Metadata-only flags (NO ENFORCEMENT in CP-16)
movement_prohibited: bool = False
"""Metadata: movement restricted (enforcement deferred to CP-17+)"""

actions_prohibited: bool = False
"""Metadata: actions restricted (enforcement deferred to CP-17+)"""

loses_dex_to_ac: bool = False
"""Metadata: loses Dex bonus to AC (enforcement deferred to CP-17+)"""
```

This WO is CP-17. Three enforcement wires:

1. **Movement gate** — `movement_resolver.py` must check `movement_prohibited` on actor's active conditions before allowing movement
2. **Action gate** — `action_economy.py` `can_use()` must check `actions_prohibited` on actor's active conditions before granting standard/full-round actions
3. **Dex-to-AC gate** — `attack_resolver.py` must strip Dex bonus from targets with `loses_dex_to_ac=True`

**What's already in place:**
- `EF.CONDITIONS = "conditions"` — entity dict key that holds list of `ConditionInstance` dicts
- `ConditionInstance` has a `modifiers` field containing a `ConditionModifiers` with all boolean flags
- `ConditionModifiers.movement_prohibited`, `.actions_prohibited`, `.loses_dex_to_ac` are populated correctly for GRAPPLED, STUNNED, PARALYZED, PRONE, BLINDED, HELPLESS per the CP-16 condition registry
- `conditions.py` has `ConditionModifiers` + `ConditionInstance` importable

---

## Section 0 — Assumptions to Validate (read before coding)

1. Read `aidm/schemas/conditions.py` — confirm `ConditionInstance` structure (specifically `modifiers.movement_prohibited`, `modifiers.actions_prohibited`, `modifiers.loses_dex_to_ac`). Confirm how conditions are deserialized from entity dict (`ConditionInstance.from_dict()` or similar).
2. Read `aidm/core/movement_resolver.py` — confirm no existing condition gate. Find the entry point function that validates movement before returning a result.
3. Read `aidm/core/action_economy.py` — confirm `can_use()` structure. Confirm where `ActionEconomy` is instantiated relative to condition state.
4. Read `aidm/core/attack_resolver.py` — find where target AC (Dex bonus) is computed. Confirm `loses_dex_to_ac` is not already checked.
5. Confirm how to iterate active conditions on an entity: `entity.get(EF.CONDITIONS, [])` → list of dicts → each needs to be deserialized or accessed as dict.

**Preflight gate:** Run full test suite before any change. Record pass count.

---

## Section 1 — Target Lock

After this WO:
- Entity with `movement_prohibited=True` condition (e.g., GRAPPLED, PARALYZED) cannot move — movement attempt returns failure event, not silent success
- Entity with `actions_prohibited=True` condition (e.g., STUNNED, PARALYZED) cannot take standard or full-round actions — `can_use("standard")` returns False
- Entity with `loses_dex_to_ac=True` condition (e.g., HELPLESS, BLINDED, STUNNED) loses Dex bonus to AC when being attacked
- Free actions and move actions remain unaffected by `actions_prohibited` (PHB: stunned lose standard + move, but free actions debated — use conservative: free actions still allowed)
- FINDING-ENGINE-CONDITION-ENFORCEMENT-001 partial-closed (AoO flat_footed deferred — separate WO)

---

## Section 2 — Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Condition access pattern | `entity.get(EF.CONDITIONS, [])` → iterate dicts | Builder confirms exact deserialization pattern |
| Movement gate location | Top of movement validation function in movement_resolver.py | Before pathfinding — fast reject |
| Movement failure result | Return failure (error string or failed MoveResult) — do NOT raise | Consistent with movement_resolver design ("Returns FullMoveIntent or error string — never raises") |
| Action gate location | `can_use()` in action_economy.py | Canonical slot-check function |
| `actions_prohibited` scope | Blocks standard + full_round only | PHB: stunned lose standard action. Move action also lost for stunned per PHB p.302 — block move too. Free actions unconditionally allowed (existing behavior unchanged). |
| Dex-to-AC gate | `attack_resolver.py` — where target Dex bonus is applied to AC | Builder finds exact line |
| AoO flat_footed check | Out of scope — deferred | Requires AoO path refactor. Separate WO. |
| `standing_triggers_aoo` | Out of scope | Same reason. |
| `auto_hit_if_helpless` | Out of scope | Requires attack resolver auto-hit path. Separate WO. |

---

## Section 3 — Contract Spec

### Helper: `_get_condition_flags(entity: dict) -> ConditionModifiers`

Add module-level helper in each modified file (or one shared location — builder's call):

```python
def _get_condition_flags(entity: dict) -> "ConditionModifiers":
    """Aggregate condition modifier flags from all active conditions on entity.

    Returns a single ConditionModifiers with OR'd boolean flags and summed
    numeric modifiers across all active conditions.
    """
    from aidm.schemas.conditions import ConditionInstance, ConditionModifiers
    conditions = entity.get(EF.CONDITIONS, [])
    movement_prohibited = False
    actions_prohibited = False
    loses_dex_to_ac = False
    for c in conditions:
        # c is a dict — builder verifies exact deserialization
        inst = ConditionInstance.from_dict(c) if isinstance(c, dict) else c
        movement_prohibited |= inst.modifiers.movement_prohibited
        actions_prohibited  |= inst.modifiers.actions_prohibited
        loses_dex_to_ac     |= inst.modifiers.loses_dex_to_ac
    return ConditionModifiers(
        movement_prohibited=movement_prohibited,
        actions_prohibited=actions_prohibited,
        loses_dex_to_ac=loses_dex_to_ac,
    )
```

**Builder must verify:** whether conditions on entity dict are stored as dicts (requiring `from_dict`) or already as `ConditionInstance` objects. Use whichever is correct.

### `movement_resolver.py` — movement gate

At the top of the movement validation entry point (builder locates exact function), before pathfinding:

```python
flags = _get_condition_flags(actor_entity)
if flags.movement_prohibited:
    return _movement_failure(actor_id, "movement_prohibited_by_condition")
    # builder uses whatever failure return pattern the file already uses
```

### `action_economy.py` — `can_use()` gate

`ActionEconomy.can_use()` currently has no entity context. Two options — builder picks:

**Option A:** Pass `entity: dict` into `can_use()` as optional param, check conditions inside.

**Option B:** Add a separate `check_conditions(entity: dict)` method; callers call both.

**Option C:** Check conditions at the call site in `play_loop.py` before calling `can_use()`.

Recommend Option C — least invasive, no signature change. Builder locates where `can_use("standard")` / `can_use("full_round")` / `can_use("move")` are called in play_loop.py and adds a condition check before each.

Pattern:
```python
flags = _get_condition_flags(actor_entity)
if flags.actions_prohibited and action_type in ("standard", "full_round", "move"):
    # emit action_denied event or return failure
    ...
```

### `attack_resolver.py` — Dex-to-AC gate

Builder locates where target Dex modifier is applied to AC. If target has `loses_dex_to_ac=True`, set Dex contribution to `min(0, dex_mod)` (cap at 0, never negative — PHB: losing Dex bonus means Dex bonus = 0, not a penalty).

```python
target_flags = _get_condition_flags(target_entity)
effective_dex_bonus = 0 if target_flags.loses_dex_to_ac else target_dex_mod
effective_dex_bonus = max(0, effective_dex_bonus)  # never penalize
```

---

## Section 4 — Implementation Plan

1. **Read** `conditions.py`, `movement_resolver.py`, `action_economy.py`, `attack_resolver.py` — confirm patterns
2. **Implement** `_get_condition_flags()` helper (one copy, placed where most useful — or inline if simpler)
3. **Wire** movement gate in `movement_resolver.py`
4. **Wire** action gate at call sites in `play_loop.py` (Option C) or in `action_economy.py` (Option A/B)
5. **Wire** Dex-to-AC gate in `attack_resolver.py`
6. **Run** full test suite — record pass count, confirm no regression
7. **Write** gate test file `tests/test_engine_condition_enforcement_001_gate.py` — minimum 10 tests

### Gate test spec (minimum 10)

| ID | Test | Pass condition |
|----|------|----------------|
| CE-001 | GRAPPLED entity attempts move → movement fails with condition reason | result indicates failure |
| CE-002 | PARALYZED entity attempts move → movement fails | result indicates failure |
| CE-003 | Entity with no movement_prohibited condition moves normally (regression) | move succeeds |
| CE-004 | STUNNED entity attempts standard action → `can_use("standard")` returns False or action denied | action blocked |
| CE-005 | PARALYZED entity attempts standard action → blocked | action blocked |
| CE-006 | Entity with no actions_prohibited takes standard action normally (regression) | action permitted |
| CE-007 | HELPLESS target attacked → attacker ignores target's Dex bonus to AC (effective Dex contribution = 0) | AC calculation correct |
| CE-008 | STUNNED target attacked → loses_dex_to_ac → Dex contribution = 0 | AC calculation correct |
| CE-009 | Normal unaffected target attacked → Dex bonus applies normally (regression) | Dex bonus present in AC |
| CE-010 | Entity with movement_prohibited=True but actions_prohibited=False can still take standard action | standard action permitted |

---

## Integration Seams

| Component | File | Notes |
|-----------|------|-------|
| `ConditionInstance` | `aidm/schemas/conditions.py` | `from_dict()` for deserialization — builder confirms |
| `ConditionModifiers` | `aidm/schemas/conditions.py` | Boolean flags: `movement_prohibited`, `actions_prohibited`, `loses_dex_to_ac` |
| `EF.CONDITIONS` | `aidm/schemas/entity_fields.py:75` | `"conditions"` — entity dict key |
| Movement entry point | `aidm/core/movement_resolver.py` | Builder locates exact function |
| `can_use()` | `aidm/core/action_economy.py:49` | Extend or gate at call site |
| Dex-to-AC | `aidm/core/attack_resolver.py` | Builder locates exact line |
| `Event` constructor | `aidm/core/event_log.py` | `Event(event_id=, event_type=, timestamp=, payload=)` — not `id=, type=, data=` |

---

## Out of Scope

- `auto_hit_if_helpless` — helpless creatures auto-hit by melee. Requires attack resolver auto-hit path. Separate WO.
- `standing_triggers_aoo` — prone stand-up provokes AoO. Requires AoO path integration. Separate WO.
- AoO `flat_footed` check — AoO triggered by condition. Separate WO.
- `FINDING-ENGINE-CONDITION-DURATION-001` — duration tracking, automatic expiration. Separate WO.
- `FINDING-ENGINE-GRAPPLE-MOVEMENT-001` — grapple pair movement, caster Concentration. Partially addressed by CE-001 (movement block), remainder separate WO.

---

## Debrief Required

**File to:** `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-CONDITION-ENFORCEMENT-001.md`

**Pass 1 — Context dump:**
- List every file modified with line ranges
- State which option was used for action gate (A/B/C)
- State exact deserialization pattern used for conditions (`from_dict` vs direct dict access)
- Confirm CE-001–010 pass counts
- Confirm regression gate pass count before vs after

**Pass 2 — PM summary ≤100 words**

**Pass 3 — Retrospective:**
- Any conditions not covered by the three flags (movement, actions, dex)?
- Did any existing tests encode "grappled entity can move freely" behavior that needed updating?
- Recommendation on remaining deferred flags (`auto_hit_if_helpless`, `standing_triggers_aoo`)

**Radar (one line each):**
- Regression gate: PASS (count before vs after)
- CE-001–010: all PASS
- Movement gate wired in movement_resolver.py: CONFIRMED
- Action gate wired (state location): CONFIRMED
- Dex-to-AC gate wired in attack_resolver.py: CONFIRMED
- `_get_condition_flags()` helper: PRESENT
- GRAPPLED movement blocked: CONFIRMED (CE-001)
- STUNNED standard action blocked: CONFIRMED (CE-004)
- HELPLESS loses Dex to AC: CONFIRMED (CE-007)
- Unaffected entities unchanged (regression): CONFIRMED (CE-003, CE-006, CE-009)
- FINDING-ENGINE-CONDITION-ENFORCEMENT-001: PARTIAL-CLOSED (movement + action + dex enforced; flat_footed/auto_hit/standing_aoo deferred)

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Drafted: 2026-02-25 — Slate*
