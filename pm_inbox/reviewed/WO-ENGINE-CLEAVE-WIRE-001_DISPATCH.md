# WO-ENGINE-CLEAVE-WIRE-001 — Wire Cleave Feat into Combat Pipeline

**Type:** Builder WO
**Gate:** ENGINE-CLEAVE
**Tests:** 10 (CL-01 through CL-10)
**Depends on:** Nothing (feat_resolver.py logic already exists)
**Blocks:** Nothing
**Priority:** MEDIUM — closes a wiring gap; logic is present but never called

---

## 1. Target Lock

`aidm/core/feat_resolver.py` contains two complete Cleave functions:
- `can_use_cleave(entity, killed_enemy_id, world_state) -> bool` — returns True if entity has Cleave feat, has not already cleaved this turn, and an adjacent enemy exists after a kill
- `get_cleave_limit(entity) -> Optional[int]` — returns None for Cleave (unlimited per turn) or 1 for Great Cleave (one cleave per turn)

Neither function is called anywhere in `attack_resolver.py`, `full_attack_resolver.py`, or `play_loop.py`. Cleave attacks never fire during combat.

**PHB spec (p.92):** When you reduce a creature to 0 HP or below with a melee attack, you may immediately make a bonus melee attack against another adjacent opponent at the same attack bonus. Great Cleave: same as Cleave but limited to one per round (PHB p.94, errata: Great Cleave removes the one-per-round limit — see BD-01).

**Deliver:** Wire `can_use_cleave()` and the resulting bonus attack into `attack_resolver.py` and `full_attack_resolver.py` at the point where a kill is detected. Add a `cleave_used` flag to prevent double-firing on the same turn. Gate ENGINE-CLEAVE 10/10.

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | Cleave vs Great Cleave: what's the RAW distinction? | PHB p.92 Cleave: once per round max. PHB p.94 Great Cleave: no once-per-round limit (prerequisite chain: Cleave → Great Cleave). `get_cleave_limit()` already encodes this correctly (None = unlimited, 1 = once). Use it verbatim. |
| BD-02 | Where is kill detected in the single attack path? | In `attack_resolver.py`, after `hp_changed` event is emitted. If `new_hp <= 0`, check `can_use_cleave()`. |
| BD-03 | Where is kill detected in the full attack path? | In `full_attack_resolver.py`, after each individual attack's damage is applied. If kill detected, check `can_use_cleave()` before proceeding to next iterative attack. |
| BD-04 | How is "already cleaved this turn" tracked? | New key `active_combat["cleave_used_this_turn"]`: a set of entity IDs that have already used their one Cleave per turn. Cleared at the actor's turn start (same as charge_ac, fight_defensively patterns). |
| BD-05 | Does Cleave bonus attack consume action economy? | No. It is a bonus attack granted by the feat — no action slot required. It is not a full attack. It fires once immediately after the kill within the same turn. |
| BD-06 | Does Cleave bonus attack provoke AoO? | No. It is part of the existing attack action, not a new action. |
| BD-07 | Does Cleave stack with full attack (iterative attacks)? | Yes. Cleave fires after any kill during a full attack sequence. If a second kill occurs during the Cleave attack, Great Cleave allows another bonus attack (subject to the unlimited/once limit). |
| BD-08 | What event is emitted for the Cleave attack? | The Cleave attack uses the standard attack resolution and emits a normal `attack_roll` event. An additional `cleave_triggered` event is emitted before the bonus attack, carrying `attacker_id`, `killed_target_id`, `cleave_target_id`. |
| BD-09 | What if no adjacent enemy exists after the kill? | `can_use_cleave()` returns False. No event emitted. No attack. Silent no-op — same as feat not present. |
| BD-10 | RNG determinism: does Cleave consume additional RNG rolls? | Yes — one d20 attack roll + damage rolls per Cleave attack. Consumption must be in-order with the existing stream: kill detected → `cleave_triggered` event → Cleave attack rolls (contiguous with the attack that caused the kill). |

---

## 3. Contract Spec

### 3.1 New field in `active_combat`

```python
# In play_loop.py at combat_start initialization:
active_combat["cleave_used_this_turn"] = set()

# In turn_start cleanup (alongside charge_ac, fight_defensively clearing):
active_combat["cleave_used_this_turn"] = set()
```

### 3.2 New event: `cleave_triggered`

```python
{
    "event_type": "cleave_triggered",
    "payload": {
        "attacker_id": str,           # Entity using Cleave
        "killed_target_id": str,       # Entity just reduced to 0 HP
        "cleave_target_id": str,       # Adjacent enemy to be attacked
        "feat": "cleave" | "great_cleave",  # Which feat triggered it
    }
}
```

Emitted immediately before the bonus attack rolls. The bonus attack itself uses the existing `attack_roll` event (no new event type for the attack outcome).

### 3.3 Wire point in `attack_resolver.py`

After kill detection (new_hp <= 0):
```python
# After emitting hp_changed (kill), before returning:
from aidm.core.feat_resolver import can_use_cleave, get_cleave_limit

if can_use_cleave(attacker_entity, target_id, world_state):
    cleave_limit = get_cleave_limit(attacker_entity)
    already_cleaved = attacker_id in world_state.active_combat.get("cleave_used_this_turn", set())
    if cleave_limit is None or not already_cleaved:
        # Mark as used (for Cleave's once-per-round limit; Great Cleave ignores this)
        if cleave_limit == 1:
            world_state.active_combat["cleave_used_this_turn"].add(attacker_id)
        # Emit cleave_triggered event
        # Find adjacent enemy (first in world_state.entities with opposing faction, adjacent position)
        cleave_target_id = _find_cleave_target(attacker_id, killed_target_id, world_state)
        if cleave_target_id:
            # Resolve bonus attack against cleave_target_id using same weapon + attack bonus
            ...
```

### 3.4 New helper: `_find_cleave_target(attacker_id, killed_id, world_state) -> Optional[str]`

Returns the entity ID of the nearest adjacent enemy of the attacker (excluding the just-killed entity). "Adjacent" = within melee reach (default 5ft = 1 grid square, or reach weapon range). Returns None if no valid target exists.

### 3.5 Same wire point in `full_attack_resolver.py`

Same pattern, applied after each individual attack within the iterative sequence. For Great Cleave (limit=None), multiple Cleave attacks may chain if multiple kills occur. For Cleave (limit=1), only one Cleave attack per turn.

---

## 4. Implementation Plan

1. **Read `aidm/core/feat_resolver.py`** — understand `can_use_cleave()` and `get_cleave_limit()` signatures and return values exactly.

2. **Read `aidm/core/attack_resolver.py`** — find the kill detection point (where `new_hp <= 0` is checked and `hp_changed` + defeat events are emitted). This is the primary wire point.

3. **Read `aidm/core/full_attack_resolver.py`** — find the equivalent kill detection point within the iterative attack loop.

4. **Read `aidm/core/play_loop.py`** — find where `active_combat` is initialized at combat start and where temporary modifiers are cleared at turn start. Add `cleave_used_this_turn` at both locations.

5. **Modify `aidm/core/attack_resolver.py`** — add `_find_cleave_target()` helper + Cleave wire after kill detection.

6. **Modify `aidm/core/full_attack_resolver.py`** — same wire, within iterative attack loop.

7. **Modify `aidm/core/play_loop.py`** — add `cleave_used_this_turn` set to combat init and turn-start cleanup.

8. **Create `tests/test_engine_gate_cleave.py`** — 10 gate tests (CL-01 through CL-10).

9. **Preflight:**
   - `pytest tests/test_engine_gate_cleave.py -v` → 10/10 must pass
   - Full suite: 0 new failures

---

## 5. Gate Tests (ENGINE-CLEAVE 10/10)

File: `tests/test_engine_gate_cleave.py`

| ID | Description |
|----|-------------|
| CL-01 | Cleave feat: kill on attack → `cleave_triggered` event emitted, bonus attack against adjacent enemy |
| CL-02 | Cleave feat: bonus attack resolves as normal `attack_roll` event with same attack bonus as killing blow |
| CL-03 | Cleave feat: once-per-round limit — second kill on same turn does NOT trigger second Cleave |
| CL-04 | Cleave feat: no adjacent enemy after kill → no `cleave_triggered`, no bonus attack |
| CL-05 | Great Cleave feat: second kill triggers second Cleave bonus attack (no once-per-round limit) |
| CL-06 | No feat: entity without Cleave feat kills enemy → no `cleave_triggered`, no bonus attack |
| CL-07 | Cleave within full attack: kill on iterative attack → Cleave fires before next iterative attack |
| CL-08 | `cleave_triggered` event payload contains `attacker_id`, `killed_target_id`, `cleave_target_id`, `feat` |
| CL-09 | `cleave_used_this_turn` cleared at start of next turn — Cleave available again next turn |
| CL-10 | Determinism: 10 replays with same seed produce identical Cleave event sequence |

---

## 6. Delivery Footer

**Files to modify:**
```
aidm/core/attack_resolver.py       ← MODIFY (add _find_cleave_target helper + Cleave wire after kill)
aidm/core/full_attack_resolver.py  ← MODIFY (same Cleave wire within iterative loop)
aidm/core/play_loop.py             ← MODIFY (cleave_used_this_turn init + turn-start clear)
```

**Files to create:**
```
tests/test_engine_gate_cleave.py    ← CREATE (10 gate tests, CL-01 through CL-10)
```

**Commit requirement:**
```
feat: WO-ENGINE-CLEAVE-WIRE-001 — Cleave/Great Cleave bonus attack wired into combat pipeline — Gate ENGINE-CLEAVE 10/10
```

**Preflight:**
```
pytest tests/test_engine_gate_cleave.py -v
```
10/10 must pass. Run full suite — 0 new failures.

---

## 7. Integration Seams

- `can_use_cleave()` and `get_cleave_limit()` are already importable from `aidm.core.feat_resolver` — no new module
- `active_combat` dict pattern is established (charge_ac, fight_defensively, etc.) — `cleave_used_this_turn` follows the same pattern
- RNG consumption: Cleave bonus attack consumes d20 + damage dice in the "combat" stream, contiguously after the killing blow — builder must verify RNG order is preserved for determinism
- `_find_cleave_target()` needs access to entity positions and faction — builder confirms `world_state.entities` has enough data to determine adjacency (grid position) and faction (opposing team)

---

## 8. Assumptions to Validate

- `world_state.entities` contains position data (grid x/y) and faction/team data accessible without a separate geometry call — builder confirms before implementing `_find_cleave_target()`
- Kill detection in `attack_resolver.py` is a single clear location (not scattered) — builder confirms before wiring
- `full_attack_resolver.py` iterates attacks in a loop where a kill can be detected per-iteration — builder confirms the loop structure before wiring

---

## 9. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
