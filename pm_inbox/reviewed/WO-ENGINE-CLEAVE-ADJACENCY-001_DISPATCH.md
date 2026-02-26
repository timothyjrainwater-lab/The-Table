# WO-ENGINE-CLEAVE-ADJACENCY-001
## Fix Cleave Target Selection — Validate Adjacency Position Check

**Priority:** MEDIUM
**Classification:** BUG
**Gate ID:** ENGINE-CLEAVE-ADJACENCY
**Minimum gate tests:** 6
**Source:** PHB p.92 — "Cleave: If you deal a creature enough damage to make it drop (typically by dropping it to below 0 hit points or killing it), you get an immediate, extra melee attack against another creature *adjacent to* the creature you just attacked."
**Dispatch:** ENGINE BATCH C

---

## Target Lock

`_find_cleave_target()` in `aidm/core/attack_resolver.py` (lines 68–90) returns the first living enemy that isn't the killed target — but does **not** validate position adjacency. PHB p.92 restricts the Cleave bonus attack to enemies *adjacent to* the dropped creature (not adjacent to the attacker). The fix: before returning a candidate entity, verify that the killed entity's position is adjacent to the candidate's position using `Position.is_adjacent_to()`. No other file changes required.

**Note:** PHB p.92 says adjacent to the *dropped foe*, not adjacent to the attacker. The adjacency check should be: `killed_pos.is_adjacent_to(candidate_pos)`.

---

## Binary Decisions

1. **Adjacency relative to whom?** PHB p.92: "another creature adjacent to the creature you just attacked." This means adjacent to the *killed creature*, not the attacker. Use `killed_entity_pos.is_adjacent_to(candidate_pos)`.

2. **What if position data is missing?** If either the killed entity or the candidate lacks a `EF.POSITION` field (e.g., abstract/theater-of-mind combat), the check should fail open — allow the Cleave to proceed without adjacency restriction rather than silently refusing it. This preserves existing behavior in non-gridded encounters.

3. **`Position.is_adjacent_to()` is already defined** at `aidm/schemas/position.py:75–87` (8-directional, 5-ft squares). No new code needed for the adjacency logic itself.

4. **Great Cleave uses same path.** `_find_cleave_target()` is called identically for both Cleave and Great Cleave. Both benefit from the fix.

---

## Contract Spec

### `aidm/core/attack_resolver.py` — `_find_cleave_target()`

Replace the current loop body (which returns the first living non-team entity) with adjacency-validated selection:

```python
def _find_cleave_target(attacker_id: str, killed_id: str, world_state: WorldState):
    """Find an adjacent enemy to target with a Cleave bonus attack.

    PHB p.92: target must be adjacent to the *killed* creature, not the attacker.
    Falls back to no adjacency check if position data is unavailable.
    """
    attacker = world_state.entities.get(attacker_id)
    killed = world_state.entities.get(killed_id)
    if attacker is None:
        return None

    attacker_team = attacker.get(EF.TEAM, "")
    killed_pos = None
    if killed is not None:
        _killed_pos_raw = killed.get(EF.POSITION)
        if _killed_pos_raw is not None:
            from aidm.schemas.position import Position
            killed_pos = Position(**_killed_pos_raw) if isinstance(_killed_pos_raw, dict) else _killed_pos_raw

    for eid, entity in world_state.entities.items():
        if eid == attacker_id or eid == killed_id:
            continue
        if entity.get(EF.DEFEATED, False):
            continue
        if entity.get(EF.HP_CURRENT, 0) <= 0:
            continue
        if entity.get(EF.TEAM, "") == attacker_team:
            continue
        # Adjacency check: must be adjacent to the killed creature
        if killed_pos is not None:
            _cand_pos_raw = entity.get(EF.POSITION)
            if _cand_pos_raw is not None:
                from aidm.schemas.position import Position
                _cand_pos = Position(**_cand_pos_raw) if isinstance(_cand_pos_raw, dict) else _cand_pos_raw
                if not killed_pos.is_adjacent_to(_cand_pos):
                    continue  # Not adjacent to killed creature — skip
        return eid
    return None
```

**No other files modified.** The adjacency fix is entirely within `_find_cleave_target()`.

### `tests/test_engine_cleave_adjacency_gate.py` — NEW FILE

Minimum 6 gate tests, IDs CA-001 through CA-006:

| Test | Assertion |
|------|-----------|
| CA-001 | Cleave: adjacent enemy present — bonus attack triggers against adjacent target |
| CA-002 | Cleave: no adjacent enemies — bonus attack does not trigger (returns None) |
| CA-003 | Cleave: two candidates, only one adjacent — selects the adjacent one |
| CA-004 | Cleave: no position data on any entity — falls back, returns first living enemy (legacy behavior preserved) |
| CA-005 | Great Cleave: adjacency also enforced (same code path) |
| CA-006 | Regression: Cleave triggers correctly when killed entity and candidate both have valid positions |

---

## Implementation Plan

1. Read `aidm/core/attack_resolver.py` lines 68–90 (`_find_cleave_target()`).
2. Read `aidm/schemas/position.py` lines 75–87 (`Position.is_adjacent_to()`).
3. Confirm how `EF.POSITION` is stored on entities (dict with x/y, or Position instance).
4. Replace `_find_cleave_target()` body with adjacency-validated version.
5. Write `tests/test_engine_cleave_adjacency_gate.py` with CA-001 through CA-006.
6. Run gate suite: `python -m pytest tests/test_engine_cleave_adjacency_gate.py -v`.
7. Run regression: `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py`.
8. Confirm 0 new failures.

---

## Integration Seams

- **`aidm/core/attack_resolver.py`** — `_find_cleave_target()` only. Lines 68–90. No other changes.
- **`aidm/schemas/position.py`** — `Position.is_adjacent_to()` at line 75–87. Read only, no changes.
- **`aidm/schemas/entity_fields.py`** — `EF.POSITION`, `EF.TEAM`, `EF.DEFEATED`, `EF.HP_CURRENT` all defined. No new constants.
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — not relevant (no new events emitted from target selection).
- **Class feature pattern:** Not applicable — Cleave/Great Cleave checked via `EF.FEATS` in `can_use_cleave()` (not modified here).

---

## Assumptions to Validate

1. Confirm `EF.POSITION` is the correct field name for entity position (expected: yes — used in AoO and cover resolvers).
2. Confirm `Position.is_adjacent_to()` takes another `Position` instance (expected: yes — at `position.py:75`).
3. Confirm `EF.POSITION` value is stored as dict `{"x": N, "y": N}` or as a `Position` instance (expected: dict — validate from entity schema before writing).
4. Confirm existing Cleave tests pass before this fix (regression baseline).

---

## Preflight

Before writing any code:
- `grep -n "POSITION\|EF.POSITION" aidm/core/attack_resolver.py` — confirm position field usage pattern
- `grep -n "is_adjacent_to" aidm/schemas/position.py` — confirm method signature
- `grep -n "EF.POSITION" aidm/core/aoo.py | head -5` — see how aoo.py reads position (reference pattern)
- `python -m pytest tests/ -q -k "cleave" --tb=short` — baseline Cleave test results

---

## Delivery Footer

- Files modified: `aidm/core/attack_resolver.py`, `tests/test_engine_cleave_adjacency_gate.py` (new)
- Gate: ENGINE-CLEAVE-ADJACENCY, minimum 6 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-CLEAVE-ADJACENCY-001.md`

### Debrief Template

```
# DEBRIEF — WO-ENGINE-CLEAVE-ADJACENCY-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** ENGINE-CLEAVE-ADJACENCY
**Date:** [DATE]

## Pass 1 — Per-File Breakdown
[Files modified, changes made, key findings]

## Pass 2 — PM Summary (≤100 words)
[Summary]

## Pass 3 — Retrospective
[Drift caught, patterns, open findings]

## Radar
[Gate results, confirmations]
```

### Audio Cue
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
