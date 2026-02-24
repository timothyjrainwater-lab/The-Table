# WO-ENGINE-REST-001 — Rest Mechanics + Slot Recovery

**Issued:** 2026-02-23
**Authority:** PM — Thunder approval (parallel backend track)
**Sequence:** Parallel with WO-ENGINE-SPELL-SLOTS-001. Depends on SPELL-SLOTS-001 for slot recovery to be meaningful (slots must exist to restore).
**Gate:** ENGINE-REST (new gate, defined below)

---

## 1. Target Lock

`RestIntent` is parsed by the intent layer but routes nowhere — no resolver exists. Casters that run out of spell slots have no recovery path. This WO implements the full rest resolution pipeline: new `rest_resolver.py`, short rest and long rest mechanics per PHB p.130, spell slot recovery on long rest, HP recovery via hit dice on short rest. Gates that the rest system is wired, tested, and fail-closed.

**Done means:** Player says "rest" → intent parsed as `RestIntent(rest_type="overnight")` → `rest_resolver.py` executes → spell slots restored to character-gen values → HP recovered (full on overnight, hit-dice-based on short) → `rest_completed` event emitted. Gate ENGINE-REST passes.

---

## 2. PHB Reference (D&D 3.5e)

D&D 3.5e uses **"rest" = 8 hours sleep** for spell recovery (PHB p.130, p.158):

| Rest type | HP recovery | Spell slots |
|-----------|-------------|-------------|
| Overnight (8h sleep) | Natural healing: level × CON bonus (min 1 HP) per night | **Full recovery** — all slots restored to max |
| Extended rest (full day bed rest) | 2× natural healing rate | Full recovery |
| Short rest (catnap, < 8h) | 0 HP from rest | 0 slots (3.5e has no short-rest slot mechanic unlike 5e) |

**Note:** 3.5e does NOT have short-rest slot recovery. Short rest in 3.5e = partial rest period, restores nothing mechanical (some class features like bardic music refresh). This WO implements the 3.5e model: only overnight/full_day rests restore spells.

---

## 3. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| New file | `aidm/core/rest_resolver.py` |
| RestIntent routing | In `execute_turn()` in `play_loop.py` — same pattern as SpellCastIntent |
| Rest resolution guard | Must NOT be in active combat (`world_state.in_combat == True` → REST_DENIED) |
| Overnight rest HP | `level × max(1, con_bonus)` where `con_bonus = (CON - 10) // 2` |
| Slot recovery | Restore `EF.SPELL_SLOTS` to values from `EF.SPELL_SLOTS_MAX` (see §4.3) |
| SPELL_SLOTS_MAX field | NEW EF constant — set at chargen equal to initial SPELL_SLOTS. Not decremented during play. |
| Dual-caster rest | Restore both `EF.SPELL_SLOTS` and `EF.SPELL_SLOTS_2` |
| Prepared casters | Overnight rest allows re-preparation: reset `EF.SPELLS_PREPARED` to match `EF.SPELLS_KNOWN` (maximum preparation) |
| Spontaneous casters | No re-preparation needed (they always know their spells) |
| Result type | `RestResult` dataclass — events list + updated world_state |
| Events emitted | `rest_completed` (always) + `spell_slots_restored` (if caster) + `hp_restored` (if HP recovered) |
| Combat guard event | `rest_denied` with `reason: "combat_active"` |
| Gate runner | pytest |

---

## 4. Implementation Spec

### 4.1 New file: `aidm/core/rest_resolver.py`

```python
"""
rest_resolver.py — D&D 3.5e rest mechanics.

Implements PHB p.130 rest rules:
- Overnight rest (8h): full spell slot recovery + natural HP healing
- Full day rest: double natural healing rate, still full slots
- Short rest (< 8h): 3.5e has no mechanical benefit for spells/HP

Called from play_loop.execute_turn() on RestIntent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent
from aidm.core.world_state import WorldState


# PHB p.130 — natural healing per full night's rest
# HP gained = character level × max(1, CON modifier)
# Full day bed rest = double rate


@dataclass
class RestResult:
    """Result of a rest resolution."""
    events: List[Dict[str, Any]] = field(default_factory=list)
    world_state: Optional[WorldState] = None
    narration: Optional[str] = None


def resolve_rest(
    intent: RestIntent,
    world_state: WorldState,
    actor_id: str,
    next_event_id: int = 0,
    timestamp: float = 0.0,
) -> RestResult:
    """
    Resolve a RestIntent for the given actor.

    Fail-closed on:
    - Active combat (rest denied)
    - Actor not found in world_state
    """
    events: List[Dict[str, Any]] = []

    # ── Combat guard ──────────────────────────────────────────────────────────
    if getattr(world_state, "in_combat", False):
        events.append({
            "event_id": next_event_id,
            "event_type": "rest_denied",
            "payload": {
                "actor_id": actor_id,
                "reason": "combat_active",
            },
            "timestamp": timestamp,
        })
        return RestResult(events=events, world_state=world_state)

    # ── Actor lookup ──────────────────────────────────────────────────────────
    entity_states = world_state.entity_states
    actor = entity_states.get(actor_id)
    if actor is None:
        events.append({
            "event_id": next_event_id,
            "event_type": "rest_denied",
            "payload": {
                "actor_id": actor_id,
                "reason": "actor_not_found",
            },
            "timestamp": timestamp,
        })
        return RestResult(events=events, world_state=world_state)

    # ── Determine rest quality ────────────────────────────────────────────────
    is_full_rest = intent.rest_type in ("overnight", "full_day")
    is_double_rate = intent.rest_type == "full_day"

    # ── HP recovery (natural healing) ────────────────────────────────────────
    hp_restored = 0
    if is_full_rest:
        hp_current = actor.get(EF.HP_CURRENT, 0)
        hp_max = actor.get(EF.HP_MAX, 0)
        level = actor.get(EF.LEVEL, 1)
        con_score = actor.get(EF.CON, 10)
        con_mod = (con_score - 10) // 2
        heal_per_night = level * max(1, con_mod)
        if is_double_rate:
            heal_per_night *= 2
        hp_restored = min(heal_per_night, hp_max - hp_current)
        if hp_restored > 0:
            actor[EF.HP_CURRENT] = hp_current + hp_restored
            events.append({
                "event_id": next_event_id,
                "event_type": "hp_restored",
                "payload": {
                    "actor_id": actor_id,
                    "amount": hp_restored,
                    "new_hp": actor[EF.HP_CURRENT],
                    "source": "natural_rest",
                },
                "timestamp": timestamp,
            })
            next_event_id += 1

    # ── Spell slot recovery ───────────────────────────────────────────────────
    if is_full_rest:
        slots_restored = _restore_spell_slots(actor, actor_id, next_event_id, timestamp)
        events.extend(slots_restored)
        if slots_restored:
            next_event_id += len(slots_restored)

    # ── Condition cleanup (overnight rest clears fatigue, minor conditions) ───
    # 3.5e: rest removes exhaustion→fatigue; fatigued is removed by 8h sleep (PHB p.300)
    conditions = actor.get(EF.CONDITIONS, [])
    removed_conditions = []
    for cond in list(conditions):
        if cond in ("fatigued", "exhausted"):
            if is_full_rest:
                conditions.remove(cond)
                removed_conditions.append(cond)
    if removed_conditions:
        actor[EF.CONDITIONS] = conditions

    # ── rest_completed event ──────────────────────────────────────────────────
    events.append({
        "event_id": next_event_id,
        "event_type": "rest_completed",
        "payload": {
            "actor_id": actor_id,
            "rest_type": intent.rest_type,
            "hp_restored": hp_restored,
            "conditions_cleared": removed_conditions,
        },
        "timestamp": timestamp,
    })

    return RestResult(
        events=events,
        world_state=world_state,
        narration=_rest_narration(intent.rest_type, hp_restored),
    )


def _restore_spell_slots(
    actor: Dict[str, Any],
    actor_id: str,
    next_event_id: int,
    timestamp: float,
) -> List[Dict[str, Any]]:
    """
    Restore all spell slots to max values (from SPELL_SLOTS_MAX).
    Also resets SPELLS_PREPARED for prepared casters.
    Returns list of spell_slots_restored events.
    """
    events = []

    # Primary slots
    slots_max: Optional[Dict[int, int]] = actor.get(EF.SPELL_SLOTS_MAX)
    if slots_max is not None:
        actor[EF.SPELL_SLOTS] = dict(slots_max)  # restore to max
        events.append({
            "event_id": next_event_id,
            "event_type": "spell_slots_restored",
            "payload": {
                "actor_id": actor_id,
                "caster_class": actor.get(EF.CASTER_CLASS, "unknown"),
                "slots": dict(slots_max),
            },
            "timestamp": timestamp,
        })
        next_event_id += 1

    # Secondary slots (dual-caster)
    slots_max_2: Optional[Dict[int, int]] = actor.get(EF.SPELL_SLOTS_MAX_2)
    if slots_max_2 is not None:
        actor[EF.SPELL_SLOTS_2] = dict(slots_max_2)
        events.append({
            "event_id": next_event_id,
            "event_type": "spell_slots_restored",
            "payload": {
                "actor_id": actor_id,
                "caster_class": actor.get(EF.CASTER_CLASS_2, "unknown"),
                "slots": dict(slots_max_2),
            },
            "timestamp": timestamp,
        })
        next_event_id += 1

    # Prepared caster spell re-preparation (wizard, cleric, druid)
    PREPARED_CASTERS = {"wizard", "cleric", "druid", "ranger", "paladin"}
    caster_class = actor.get(EF.CASTER_CLASS, "")
    if caster_class in PREPARED_CASTERS:
        # On long rest, prepared casters may re-prepare — reset to full known list
        spells_known = actor.get(EF.SPELLS_KNOWN, {})
        if spells_known:
            actor[EF.SPELLS_PREPARED] = {
                level: list(spells)
                for level, spells in spells_known.items()
            }

    return events


def _rest_narration(rest_type: str, hp_restored: int) -> str:
    """Return brief narration string for rest result."""
    if rest_type == "overnight":
        base = "You take a full night's rest."
    elif rest_type == "full_day":
        base = "You rest for a full day."
    else:
        base = "You take a brief rest."

    if hp_restored > 0:
        return f"{base} You recover {hp_restored} hit points and your spells return."
    else:
        return f"{base} Your spells return."
```

### 4.2 New EF constants

In `aidm/schemas/entity_fields.py`, add alongside `SPELL_SLOTS`:

```python
SPELL_SLOTS_MAX = "spell_slots_max"    # Dict[int, int] — max slots (set at chargen, never mutated)
SPELL_SLOTS_MAX_2 = "spell_slots_max_2"  # Dict[int, int] — secondary caster max slots
```

### 4.3 Wire SPELL_SLOTS_MAX at chargen

In `aidm/chargen/builder.py`, in `_merge_spellcasting()`, when setting `EF.SPELL_SLOTS`, simultaneously set `EF.SPELL_SLOTS_MAX`:

```python
# After calculating spell_slots:
EF.SPELL_SLOTS: spell_slots,
EF.SPELL_SLOTS_MAX: dict(spell_slots),   # snapshot for rest recovery
```

Same for secondary caster:
```python
EF.SPELL_SLOTS_2: secondary_slots,
EF.SPELL_SLOTS_MAX_2: dict(secondary_slots),
```

### 4.4 Wire RestIntent in `execute_turn()`

In `play_loop.py`, in the `execute_turn()` intent routing block, add a `RestIntent` branch (parallel pattern to `SpellCastIntent`):

```python
elif isinstance(combat_intent, RestIntent):
    from aidm.core.rest_resolver import resolve_rest
    rest_result = resolve_rest(
        intent=combat_intent,
        world_state=world_state,
        actor_id=turn_ctx.actor_id,
        next_event_id=current_event_id,
        timestamp=timestamp,
    )
    events.extend(rest_result.events)
    world_state = rest_result.world_state
    narration_text = rest_result.narration
```

---

## 5. Event Schema

**`rest_completed`:**
```json
{
  "event_type": "rest_completed",
  "payload": {
    "actor_id": "string",
    "rest_type": "overnight | full_day",
    "hp_restored": 0,
    "conditions_cleared": []
  }
}
```

**`rest_denied`:**
```json
{
  "event_type": "rest_denied",
  "payload": {
    "actor_id": "string",
    "reason": "combat_active | actor_not_found"
  }
}
```

**`spell_slots_restored`:**
```json
{
  "event_type": "spell_slots_restored",
  "payload": {
    "actor_id": "string",
    "caster_class": "wizard",
    "slots": {"1": 4, "2": 3, "3": 2}
  }
}
```

**`hp_restored`:**
```json
{
  "event_type": "hp_restored",
  "payload": {
    "actor_id": "string",
    "amount": 5,
    "new_hp": 22,
    "source": "natural_rest"
  }
}
```

---

## 6. Gate Spec

**Gate name:** `ENGINE-REST`
**Test file:** `tests/test_engine_rest_gate.py`

| # | Test | Check |
|---|------|-------|
| R-01 | Overnight rest with depleted slots → `spell_slots_restored` event, slots back to max | `actor[EF.SPELL_SLOTS][1] == max_slots[1]` |
| R-02 | Overnight rest with damaged HP → `hp_restored` event, HP increases | `new_hp == old_hp + heal_amount` |
| R-03 | Overnight rest at full HP → no `hp_restored` event | 0 HP events |
| R-04 | Rest during active combat → `rest_denied` with reason "combat_active" | event_type == "rest_denied" |
| R-05 | Full day rest → double HP healing rate | `hp_restored == 2 × overnight_rate` |
| R-06 | Non-caster rests → `rest_completed` event, no `spell_slots_restored` | no slot events for fighter |
| R-07 | Overnight rest clears `fatigued` condition | condition absent post-rest |
| R-08 | Dual-caster rests → both `SPELL_SLOTS` and `SPELL_SLOTS_2` restored | both slots at max |
| R-09 | Prepared caster (wizard) rests → `SPELLS_PREPARED` reset to match `SPELLS_KNOWN` | all known spells now prepared |
| R-10 | `rest_completed` event always emitted last | event_type of last event == "rest_completed" |
| R-11 | `SPELL_SLOTS_MAX` set at chargen for wizard L5 → correct slot table | max values match PHB table |
| R-12 | `SPELL_SLOTS_MAX` unchanged after two full rests (immutable baseline) | max == initial == post-rest |

**Test count target:** 12 checks → Gate `ENGINE-REST` 12/12.

---

## 7. Dependencies

- `EF.SPELL_SLOTS_MAX` / `EF.SPELL_SLOTS_MAX_2` — new constants (this WO adds them to entity_fields.py)
- `EF.SPELL_SLOTS` — existing; mutated on decrement (WO-ENGINE-SPELL-SLOTS-001) and restored here
- `RestIntent` — existing in intents.py (`rest_type: "overnight" | "full_day"`)
- `WorldState.in_combat` — existing field on WorldState
- `WorldState.entity_states` — existing dict
- No external libraries required

---

## 8. What This WO Does NOT Do

- Does not implement prepared spell selection UI (re-preparation is automatic: all known spells become prepared)
- Does not implement class feature recovery on rest (bardic music charges, paladin smite recharge) — future WO
- Does not implement hit dice mechanics (5e concept — not applicable in 3.5e; rest HP is automatic)
- Does not enforce rest interruption (combat starting during rest — out of scope)
- Does not implement "8-hour watch" party rest mechanics

---

## 9. Preflight

```bash
cd f:/DnD-3.5
python -m pytest tests/test_engine_rest_gate.py -v
# All 12 checks must pass.
# Run full suite: python -m pytest tests/ -x --tb=short
# Zero new regressions expected.
```
