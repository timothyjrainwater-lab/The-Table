# WO-ENGINE-STABILIZE-ALLY-001 — Stabilization by Ally: DC 15 Heal Check

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** MEDIUM (FINDING-COVERAGE-MAP-001 rank #18 — standard rescue action does not work)
**WO type:** BUG (missing mechanic)
**Gate:** ENGINE-STABILIZE-ALLY (10 tests)

---

## 1. Target Lock

**What works:** `dying_resolver.py` handles the DYING condition and self-stabilization (Fort save each round). `resolve_skill_check()` in `skill_resolver.py` is fully functional — signature `(entity, skill_id, dc, rng, circumstance_modifier=0)` returning `SkillCheckResult`. The Heal skill is defined in `aidm/schemas/skills.py`.

**What's missing:** PHB p.152 (Heal skill) — "First Aid: You can administer first aid to a dying character (one with –1 or fewer hit points). If your Heal check succeeds (DC 15), the character becomes stable." No `StabilizeIntent` exists. No routing in `play_loop.py`. The standard ally rescue action does nothing.

**Root cause:** Never implemented. Requires a new intent, a new small resolver, a single routing entry in play_loop.py.

**PHB references:**
- PHB p.152: Heal skill, First Aid — DC 15 stabilizes a dying character
- PHB p.145: Dying characters (−1 to −9 HP) — can be stabilized by an ally's Heal check
- Note: This is not the same as healing HP. Stabilize stops the dying bleed; HP remain negative.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | New intent name? | `StabilizeIntent` — distinct from `AidAnotherIntent` (which is attack/AC assist). Stabilize is a specific Heal skill application on a dying target. |
| 2 | Trained-only restriction? | Heal is NOT trained-only in PHB 3.5. Any character can attempt it. `skill_resolver.py` enforces `trained_only` from the skill definition — confirm Heal's trained_only flag is False. |
| 3 | Does the target need to be DYING? | Yes. If target is not in the DYING state (−1 to −9 HP), intent is rejected with `stabilize_invalid_target` event. |
| 4 | Does success heal HP? | No — PHB explicit. Stabilize stops the bleed (sets `EF.STABLE = True`, clears the dying tick). HP remains wherever it was. |
| 5 | Does this cost an action? | PHB p.152: First Aid is a standard action. `StabilizeIntent` costs a standard action from the helper's action budget. |
| 6 | Can you stabilize yourself? | No — PHB p.152 requires "you can administer first aid to a dying character," implying another creature. Reject `intent.actor_id == intent.target_id`. |
| 7 | Where does the new resolver live? | Inline in a new file `aidm/core/stabilize_resolver.py` — small, ~40 lines. Follows the pattern of `aid_another_resolver.py`. |
| 8 | How does stabilization interact with dying_resolver? | On success: set `EF.STABLE = True` on the target entity in world_state. The `tick_dying()` function in play_loop already checks `EF.STABLE` and skips the HP bleed if True. No changes needed to dying_resolver. |

---

## 3. Contract Spec

### New intent: `StabilizeIntent` in `aidm/schemas/intents.py`

```python
@dataclass(frozen=True)
class StabilizeIntent:
    """PHB p.152: First Aid — DC 15 Heal check to stabilize a dying ally."""
    actor_id: str
    target_id: str
    action_type: str = "standard"
```

### New resolver: `aidm/core/stabilize_resolver.py`

```python
from aidm.schemas.intents import StabilizeIntent
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import ConditionType
from aidm.core.skill_resolver import resolve_skill_check
from aidm.schemas.events import Event
from typing import List, Tuple

STABILIZE_DC = 15

def resolve_stabilize(
    intent: StabilizeIntent,
    world_state,
    rng,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], object]:
    """Resolve a Heal check to stabilize a dying ally (PHB p.152)."""
    events = []
    current_event_id = next_event_id
    ws = world_state  # mutate a copy if WorldState is immutable

    actor = ws.entities.get(intent.actor_id)
    target = ws.entities.get(intent.target_id)

    # Reject: self-stabilization
    if intent.actor_id == intent.target_id:
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_invalid",
            timestamp=timestamp,
            payload={"actor_id": intent.actor_id, "reason": "cannot_stabilize_self"},
            citations=["PHB p.152"],
        ))
        return events, ws

    # Reject: target not dying
    target_hp = target.get(EF.HP_CURRENT, 0)
    is_dying = target_hp < 0 and target_hp >= -9 and not target.get(EF.STABLE, False)
    if not is_dying:
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_invalid",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "reason": "target_not_dying",
                "target_hp": target_hp,
            },
            citations=["PHB p.152"],
        ))
        return events, ws

    # Heal check: DC 15
    result = resolve_skill_check(actor, "heal", STABILIZE_DC, rng)

    if result.success:
        # Stabilize: set STABLE flag — dying tick will skip this entity
        ws.entities[intent.target_id][EF.STABLE] = True
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_success",
            timestamp=timestamp + 0.1,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "heal_roll": result.d20_roll,
                "heal_bonus": result.ability_modifier + result.skill_ranks,
                "heal_total": result.total,
                "dc": STABILIZE_DC,
                "target_hp": target_hp,
            },
            citations=["PHB p.152"],
        ))
    else:
        events.append(Event(
            event_id=current_event_id,
            event_type="stabilize_failed",
            timestamp=timestamp + 0.1,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "heal_roll": result.d20_roll,
                "heal_bonus": result.ability_modifier + result.skill_ranks,
                "heal_total": result.total,
                "dc": STABILIZE_DC,
                "target_hp": target_hp,
            },
            citations=["PHB p.152"],
        ))

    return events, ws
```

### Modification: `aidm/core/play_loop.py` — intent routing

Add routing entry after the `AidAnotherIntent` block (~line 2044):

```python
elif isinstance(combat_intent, StabilizeIntent):
    # WO-ENGINE-STABILIZE-ALLY-001: PHB p.152 First Aid
    from aidm.core.stabilize_resolver import resolve_stabilize
    _stab_events, world_state = resolve_stabilize(
        intent=combat_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.1,
    )
    events.extend(_stab_events)
    current_event_id += len(_stab_events)
```

### Action economy: `aidm/core/action_economy.py`

Add `StabilizeIntent` to the `_ACTION_TYPES` mapping as `"standard"`:

```python
StabilizeIntent: "standard",
```

---

## 4. Implementation Plan

### Step 1 — `aidm/schemas/intents.py`
Add `StabilizeIntent` dataclass (~5 lines).

### Step 2 — `aidm/core/stabilize_resolver.py`
New file, ~60 lines. Follow `aid_another_resolver.py` as structural template.

### Step 3 — `aidm/core/play_loop.py`
Add `elif isinstance(combat_intent, StabilizeIntent)` routing block (~8 lines). Import `StabilizeIntent` in the intent imports block at top of file.

### Step 4 — `aidm/core/action_economy.py`
Add `StabilizeIntent: "standard"` to `_ACTION_TYPES`.

### Step 5 — Tests (`tests/test_engine_stabilize_ally_gate.py`)
Gate: ENGINE-STABILIZE-ALLY — 10 tests

| Test | Description |
|------|-------------|
| SA-01 | Actor makes Heal DC 15, succeeds: target EF.STABLE = True |
| SA-02 | Actor makes Heal DC 15, fails: target EF.STABLE remains False, still bleeding |
| SA-03 | `stabilize_success` event payload: actor_id, target_id, heal_roll, heal_total, dc=15, target_hp |
| SA-04 | `stabilize_failed` event payload: same fields |
| SA-05 | Target not dying (HP > 0): `stabilize_invalid` event, reason=target_not_dying |
| SA-06 | Target already stable: `stabilize_invalid` event |
| SA-07 | Self-stabilization attempt: `stabilize_invalid` event, reason=cannot_stabilize_self |
| SA-08 | Action budget: StabilizeIntent costs a standard action from actor |
| SA-09 | After stabilize success: dying tick skips target (EF.STABLE = True guard in play_loop) |
| SA-10 | Regression: ENGINE-AID-ANOTHER 10/10 unchanged, ENGINE-DEATH-DYING gate unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/schemas/intents.py` — `StabilizeIntent` dataclass (~5 lines)
- `aidm/core/stabilize_resolver.py` — new file (~60 lines)
- `aidm/core/play_loop.py` — routing elif block (~8 lines) + import
- `aidm/core/action_economy.py` — 1-line mapping entry

**Files NOT touched:**
- `aidm/core/dying_resolver.py` — unchanged; EF.STABLE already respected
- `aidm/core/skill_resolver.py` — called as-is, no changes
- `aidm/schemas/skills.py` — Heal skill already defined

**Event constructor signature (mandatory):**
```python
Event(
    event_id=<int>,
    event_type=<str>,
    payload=<dict>,
    timestamp=<float>,
    citations=[],
)
```

**WorldState mutation pattern:** If `WorldState` is immutable (frozen dataclass), use `deepcopy` and rebuild — confirm from existing resolvers. If mutable, direct dict assignment is fine.

**Skill check pattern:**
```python
from aidm.core.skill_resolver import resolve_skill_check
result = resolve_skill_check(actor, "heal", dc=15, rng=rng)
result.success  # bool
result.total    # int
result.d20_roll # int
```

**EF.STABLE field:** Confirm it exists and that the dying tick checks it. From briefing: `EF.STABLE` is confirmed in `aidm/schemas/entity_fields.py` and used by `dying_resolver.py`.

---

## Assumptions to Validate

1. Heal skill (`"heal"`) is in `aidm/schemas/skills.py` and is NOT trained-only — confirm before writing
2. `EF.STABLE = True` on the target entity causes dying tick to skip that entity — confirm from `play_loop.py` dying tick block
3. `WorldState.entities` is mutable (dict assignment works) — confirm from existing resolver patterns
4. `SkillCheckResult` has `d20_roll`, `total`, `ability_modifier`, `skill_ranks` fields — confirmed from skill_resolver inspection
5. `AidAnotherIntent` routing block is at approximately line 2044 — confirm exact line before inserting elif

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_aid_another.py tests/test_engine_gate_death_dying.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_stabilize_ally_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/schemas/intents.py` — `StabilizeIntent` dataclass
- [ ] `aidm/core/stabilize_resolver.py` — new resolver (~60 lines)
- [ ] `aidm/core/play_loop.py` — routing elif + import
- [ ] `aidm/core/action_economy.py` — `StabilizeIntent: "standard"` mapping
- [ ] `tests/test_engine_stabilize_ally_gate.py` — 10/10

**Gate:** ENGINE-STABILIZE-ALLY 10/10
**Regression bar:** ENGINE-AID-ANOTHER 10/10, ENGINE-DEATH-DYING gate unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-STABILIZE-ALLY-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown, key findings, open findings table
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — drift caught, patterns, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
