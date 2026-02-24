# WO-ENGINE-DEATH-DYING-001 — Death, Dying, and Stabilization (PHB p.145)

**Issued:** 2026-02-24
**Authority:** Thunder approval
**Gate:** ENGINE-DEATH-DYING (new gate, defined below)
**Parallel-safe:** Yes — touches `entity_fields.py` (new constants), `attack_resolver.py` + `full_attack_resolver.py` (defeat check), `play_loop.py` (tick hook + apply functions). No overlap with active WOs (CONCENTRATION-001, GRAPPLE-PIN-001, SPELL-PREP-001 do not touch defeat logic).

---

## 1. Target Lock

All three defeat call sites (`attack_resolver.py:480`, `full_attack_resolver.py:792`, `play_loop.py:637`) use:

```python
if hp_after <= 0:
    entity[EF.DEFEATED] = True
    emit("entity_defeated")
```

**PHB 3.5e p.145** defines a three-band HP model:

| HP | State | Effect |
|----|-------|--------|
| 1+ | Conscious | Normal play |
| 0 | Disabled | Can take only one move or standard action per turn; taking any action deals 1 damage |
| −1 to −9 | Dying | Unconscious, loses 1 HP per round. Each round: DC 10 Fort save to stabilize. Stabilized at 1 HP after full rest. |
| −10 or below | Dead | Dead. No recovery without magic (Raise Dead, etc.) |

**Current behavior**: `hp ≤ 0` → instantly `DEFEATED`. There is no dying range, no bleed-out, no stabilization, no disability. A monster dropped to −3 is mechanically identical to one dropped to −300.

**Done means:** The three bands are enforced. `DISABLED` at 0, `DYING` at −1 to −9 with 1 HP/round bleed and Fort stabilization roll, `DEAD` at −10+. `entity_defeated` is only emitted at confirmed death or at the start of a combat where a creature is unambiguously out. The `tick_round()` hook in `play_loop.py` drives the dying bleed. Gate ENGINE-DEATH-DYING 12/12.

---

## 2. PHB 3.5e Rule (p.145)

> **Disabled (0 HP):** A character with exactly 0 hit points is disabled. A disabled character may take a single move or standard action each round. Taking any standard action (or any other strenuous action) deals 1 point of damage after completing the action.

> **Dying (−1 to −9 HP):** A dying character is unconscious and losing hit points. At the end of each round (or the start of her next turn), the dying character must make a DC 10 Fortitude save. If she fails, she loses 1 hit point. If she succeeds, she is stable. A stable dying character no longer loses hit points.

> **Dead (−10 HP or lower):** The character is dead.

**Stabilization:** A dying creature can be stabilized by another creature spending a full-round action making DC 15 Heal check (not in this WO scope — deferred), OR by natural Fort save success. Once stable: no further HP loss, but still unconscious at negative HP. Recovers 1 HP after 1 hour of uninterrupted rest (not this WO's scope — rest_resolver handles above-0 recovery).

**Disabled action damage (0 HP):** Strenuous standard action deals 1 HP to the disabled character, dropping them to −1 (dying). Move-only actions are safe.

---

## 3. New Entity Fields

Add to `aidm/schemas/entity_fields.py`:

```python
# --- Death / Dying (WO-ENGINE-DEATH-DYING-001) ---
DYING = "dying"                # Bool: True if HP between -1 and -9 (inclusive)
STABLE = "stable"              # Bool: True if formerly dying, now stable (no longer bleeding)
DISABLED = "disabled"          # Bool: True if HP == 0 (disabled, not dying)
```

**`DEFEATED` semantics change:** `DEFEATED = True` now means **dead** (HP ≤ −10) or removed from play. Previously it meant "HP ≤ 0". This is the critical semantic shift. `DYING` entities are NOT defeated — they are still in combat as valid targets (and can still be healed).

---

## 4. Implementation Spec

### 4.1 New module: `aidm/core/dying_resolver.py`

Pure function — no side effects. Returns events only.

```python
"""Dying and stabilization resolver. WO-ENGINE-DEATH-DYING-001.

PHB p.145: Three HP bands — disabled (0), dying (-1 to -9), dead (-10+).
Dying creatures lose 1 HP/round unless they pass DC 10 Fort save.
"""

from dataclasses import dataclass
from typing import List, Tuple, Any, Dict

from aidm.schemas.entity_fields import EF
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider


def classify_hp(hp: int) -> str:
    """Classify HP value into PHB death band.

    Returns: 'conscious', 'disabled', 'dying', or 'dead'
    """
    if hp >= 1:
        return 'conscious'
    elif hp == 0:
        return 'disabled'
    elif hp >= -9:
        return 'dying'
    else:
        return 'dead'


def resolve_hp_transition(
    entity_id: str,
    old_hp: int,
    new_hp: int,
    source: str,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], Dict[str, Any]]:
    """Resolve state transition when an entity's HP changes.

    Emits appropriate state transition events based on old→new HP band.
    Returns (events, entity_field_updates) — caller applies field updates.

    PHB p.145: Transitions are:
    - Any → disabled (new_hp == 0): entity_disabled event
    - Any → dying (-1 to -9): entity_dying event + apply UNCONSCIOUS condition
    - Any → dead (-10+): entity_defeated event (true death)
    - Dying → conscious (healing): entity_revived event, clear DYING/STABLE
    - Disabled → dying (strenuous action): entity_dying event

    Args:
        entity_id: Entity whose HP changed
        old_hp: HP before change
        new_hp: HP after change
        source: Source of change (e.g., "attack_damage", "bleed")
        world_state: Current world state
        next_event_id: Next event ID for sequencing
        timestamp: Event timestamp

    Returns:
        (events, field_updates): events to emit, dict of EF fields to apply
    """
    events = []
    field_updates: Dict[str, Any] = {}
    eid = next_event_id

    old_band = classify_hp(old_hp)
    new_band = classify_hp(new_hp)

    if old_band == new_band:
        return events, field_updates  # No transition

    if new_band == 'disabled':
        field_updates[EF.DISABLED] = True
        field_updates[EF.DYING] = False
        field_updates[EF.STABLE] = False
        events.append(Event(
            event_id=eid, event_type="entity_disabled", timestamp=timestamp,
            payload={"entity_id": entity_id, "hp": new_hp, "source": source},
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    elif new_band == 'dying':
        field_updates[EF.DYING] = True
        field_updates[EF.DISABLED] = False
        field_updates[EF.STABLE] = False
        field_updates[EF.DEFEATED] = False  # NOT dead yet
        events.append(Event(
            event_id=eid, event_type="entity_dying", timestamp=timestamp,
            payload={"entity_id": entity_id, "hp": new_hp, "source": source},
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    elif new_band == 'dead':
        field_updates[EF.DYING] = False
        field_updates[EF.DISABLED] = False
        field_updates[EF.STABLE] = False
        field_updates[EF.DEFEATED] = True  # Actually dead
        events.append(Event(
            event_id=eid, event_type="entity_defeated", timestamp=timestamp,
            payload={
                "entity_id": entity_id, "hp": new_hp,
                "source": source, "cause": "dead",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    elif new_band == 'conscious' and old_band in ('dying', 'disabled'):
        # Healed out of danger
        field_updates[EF.DYING] = False
        field_updates[EF.DISABLED] = False
        field_updates[EF.STABLE] = False
        field_updates[EF.DEFEATED] = False
        events.append(Event(
            event_id=eid, event_type="entity_revived", timestamp=timestamp,
            payload={"entity_id": entity_id, "hp": new_hp, "source": source},
            citations=[{"source_id": "681f92bc94ff", "page": 145}],
        ))

    return events, field_updates


def resolve_dying_tick(
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Process dying bleed for all dying entities at end of round.

    PHB p.145: Each dying entity loses 1 HP unless they pass DC 10 Fort save.
    On save success: entity becomes stable (no further HP loss).
    On save fail: lose 1 HP. If new HP ≤ −10: dead.

    Called from play_loop.py at end-of-round tick (after tick_round()).

    RNG consumption: one "combat" stream d20 per dying entity, in entity_id
    alphabetical order (deterministic).

    Args:
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Event timestamp

    Returns:
        (events, updated_world_state)
    """
    from copy import deepcopy

    events = []
    current_event_id = next_event_id
    entities = {k: deepcopy(v) for k, v in world_state.entities.items()}

    # Alphabetical order for determinism
    dying_entities = sorted(
        eid for eid, e in entities.items()
        if e.get(EF.DYING, False) and not e.get(EF.STABLE, False)
    )

    for entity_id in dying_entities:
        entity = entities[entity_id]
        fort_save = entity.get(EF.SAVE_FORT, 0)

        roll = rng.stream("combat").randint(1, 20)
        total = roll + fort_save
        dc = 10

        if total >= dc:
            # Stabilized — no more HP loss
            entity[EF.STABLE] = True
            events.append(Event(
                event_id=current_event_id,
                event_type="entity_stabilized",
                timestamp=timestamp,
                payload={
                    "entity_id": entity_id,
                    "hp": entity.get(EF.HP_CURRENT, -1),
                    "roll": roll,
                    "fort_save": fort_save,
                    "total": total,
                    "dc": dc,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}],
            ))
            current_event_id += 1
        else:
            # Bleed: lose 1 HP
            old_hp = entity.get(EF.HP_CURRENT, -1)
            new_hp = old_hp - 1
            entity[EF.HP_CURRENT] = new_hp

            events.append(Event(
                event_id=current_event_id,
                event_type="hp_changed",
                timestamp=timestamp,
                payload={
                    "entity_id": entity_id,
                    "old_hp": old_hp,
                    "new_hp": new_hp,
                    "delta": -1,
                    "source": "dying_bleed",
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}],
            ))
            current_event_id += 1

            # Check if now dead
            if new_hp <= -10:
                entity[EF.DYING] = False
                entity[EF.DEFEATED] = True
                events.append(Event(
                    event_id=current_event_id,
                    event_type="entity_defeated",
                    timestamp=timestamp + 0.01,
                    payload={
                        "entity_id": entity_id,
                        "hp": new_hp,
                        "source": "dying_bleed",
                        "cause": "dead",
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 145}],
                ))
                current_event_id += 1

            events.append(Event(
                event_id=current_event_id,
                event_type="dying_fort_failed",
                timestamp=timestamp + 0.01,
                payload={
                    "entity_id": entity_id,
                    "hp": new_hp,
                    "roll": roll,
                    "fort_save": fort_save,
                    "total": total,
                    "dc": dc,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 145}],
            ))
            current_event_id += 1

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
        narrative_context=world_state.narrative_context,
        scene_type=world_state.scene_type,
    )
    return events, updated_state
```

### 4.2 Replace defeat check in `attack_resolver.py` (line ~480)

**Old:**
```python
if hp_after <= 0:
    events.append(Event(... event_type="entity_defeated" ...))
```

**New:**
```python
from aidm.core.dying_resolver import resolve_hp_transition
trans_events, field_updates = resolve_hp_transition(
    entity_id=intent.target_id,
    old_hp=hp_before,
    new_hp=hp_after,
    source="attack_damage",
    world_state=world_state,
    next_event_id=current_event_id,
    timestamp=timestamp + 0.3,
)
events.extend(trans_events)
current_event_id += len(trans_events)
# field_updates applied in apply_attack_events()
# Store field_updates in event payload for apply phase
if field_updates:
    events.append(Event(
        event_id=current_event_id,
        event_type="_field_update",  # internal, not surfaced to UI
        timestamp=timestamp + 0.31,
        payload={"entity_id": intent.target_id, "updates": field_updates},
    ))
    current_event_id += 1
```

**Simpler approach** (preferred for minimal diff): pass `field_updates` as return value from `resolve_attack()`, apply in `apply_attack_events()`. See §4.5.

### 4.3 Replace defeat check in `full_attack_resolver.py` (line ~792)

Same pattern as §4.2 — replace `if hp_after <= 0: entity_defeated` with `resolve_hp_transition()`.

### 4.4 Replace defeat check in `play_loop.py:_resolve_spell_cast()` (line ~637)

Same pattern. Spell damage goes through the same transition logic.

### 4.5 Update `apply_attack_events()` and `apply_full_attack_events()`

Both functions handle `entity_defeated` by setting `DEFEATED = True`. Extend to handle new event types:

```python
elif event.event_type == "entity_disabled":
    entity_id = event.payload["entity_id"]
    if entity_id in entities:
        entities[entity_id][EF.DISABLED] = True
        entities[entity_id][EF.DYING] = False

elif event.event_type == "entity_dying":
    entity_id = event.payload["entity_id"]
    if entity_id in entities:
        entities[entity_id][EF.DYING] = True
        entities[entity_id][EF.DISABLED] = False
        entities[entity_id][EF.DEFEATED] = False

elif event.event_type == "entity_revived":
    entity_id = event.payload["entity_id"]
    if entity_id in entities:
        entities[entity_id][EF.DYING] = False
        entities[entity_id][EF.DISABLED] = False
        entities[entity_id][EF.STABLE] = False

# entity_defeated: unchanged — sets DEFEATED = True
```

### 4.6 Wire `resolve_dying_tick()` in `play_loop.py`

In the end-of-round block (currently calls `duration_tracker.tick_round()`), append dying tick immediately after:

```python
# After duration_tracker.tick_round():
from aidm.core.dying_resolver import resolve_dying_tick
dying_events, world_state = resolve_dying_tick(
    world_state=world_state,
    rng=rng,
    next_event_id=current_event_id,
    timestamp=timestamp + 0.5,
)
events.extend(dying_events)
current_event_id += len(dying_events)
```

**RNG guard:** `resolve_dying_tick` must only be called when `rng is not None`. If `rng` is None (e.g., `RestIntent` turn) and there are dying entities, skip the bleed tick (rest scenario handles recovery separately).

### 4.7 Defeated check update in `play_loop.py`

The target validation check `if target.get(EF.DEFEATED, False)` at lines ~1320 and ~1391 must remain: a `DEAD` entity is defeated, attack on it is invalid. Dying entities (`EF.DYING = True`) have `EF.DEFEATED = False` — they are valid targets (can be healed or coup-de-graced).

### 4.8 XP award guard

`_award_xp_for_defeat()` currently fires on every `entity_defeated` event. This is correct — XP is earned when an entity dies, not when they go unconscious. `entity_dying` does NOT trigger XP. No change needed.

---

## 5. Event Types (New)

| Event type | Emitted when |
|------------|-------------|
| `entity_disabled` | HP drops to exactly 0 |
| `entity_dying` | HP drops to −1 through −9 |
| `entity_stabilized` | Dying entity passes DC 10 Fort save at end of round |
| `dying_fort_failed` | Dying entity fails Fort save (loses 1 HP this round) |
| `entity_revived` | Dying/disabled entity healed above 0 HP |
| `entity_defeated` | HP drops to −10 or below (true death) — **semantics unchanged from existing gate specs** |

**`entity_defeated` is preserved** with identical payload structure. Existing gates that assert `entity_defeated` on any HP ≤ 0 will need updating — see §6 regression note.

---

## 6. Regression Risk and Gold Master Impact

**High impact:** All existing tests that drop a target to exactly 0 HP and assert `entity_defeated` will now receive `entity_disabled` or `entity_dying` instead. This is the intended behavior but requires:

1. Gold master files (`tests/fixtures/gold_masters/*.jsonl`) — regeneration required after the fix. Builder runs `python tests/_gen_v12.py` or equivalent to regenerate 30/30 gold masters.
2. CP gates that assert `entity_defeated` on 0-HP: update assertions to accept `entity_disabled` or `entity_dying` instead.
3. CP-10 (attack resolution) tests: must now distinguish between "target incapacitated" (disabled/dying) and "target dead" (defeated).

**Mitigation:** Builder should run the full suite immediately after §4.2/4.3/4.4 changes, before attempting §4.6. The defeat-check replacement is the high-regression-risk step. Gate target counts may shift as tests are updated.

---

## 7. Gate Spec

**Gate name:** `ENGINE-DEATH-DYING`
**Test file:** `tests/test_engine_death_dying_gate.py`

| # | Test | Check |
|---|------|-------|
| DD-01 | Attack drops target to 0 HP → `entity_disabled` event (not `entity_defeated`) | event_type == "entity_disabled" |
| DD-02 | Attack drops target to −3 HP → `entity_dying` event, `EF.DYING == True`, `EF.DEFEATED == False` | dying=True, defeated=False |
| DD-03 | Attack drops target to −10 HP exactly → `entity_defeated` event, `EF.DEFEATED == True` | event_type == "entity_defeated" |
| DD-04 | Attack drops target to −15 HP → `entity_defeated` event (dead regardless of depth) | defeated=True |
| DD-05 | Dying entity end-of-round: Fort save fails → `dying_fort_failed` + `hp_changed` (delta=−1) | 2 events emitted |
| DD-06 | Dying entity end-of-round: Fort save succeeds → `entity_stabilized`, `EF.STABLE == True`, no HP loss | stable=True, hp unchanged |
| DD-07 | Stable entity end-of-round: no bleed tick (not in dying loop) | no `dying_fort_failed` event |
| DD-08 | Dying entity bleed to −10 → `entity_defeated` emitted mid-bleed-tick | defeated event in dying_tick output |
| DD-09 | Healing a dying entity to 1+ HP → `entity_revived` event, `EF.DYING == False` | revived event, dying cleared |
| DD-10 | Dying entity is a valid attack target (`EF.DEFEATED == False`) | validation does not reject target |
| DD-11 | Dead entity (`EF.DEFEATED == True`) rejected as attack target | `intent_validation_failed` event |
| DD-12 | Zero regressions on CP-22 + CP-23 + XP-01 gates after gold master regeneration | full suite pass |

**Test count target:** 12 checks → Gate `ENGINE-DEATH-DYING` 12/12.

**Gold master note:** Builder must regenerate gold masters after implementing this WO. The `entity_defeated` → `entity_dying`/`entity_disabled` split will invalidate current gold masters. Run `python tests/_gen_v12.py` (or the applicable generation script) once per gold master scenario.

---

## 8. What This WO Does NOT Do

- Does not implement the Disabled action damage (strenuous standard action at 0 HP deals 1 damage — deferred, requires action-type classification at resolution time)
- Does not implement Heal skill checks to stabilize (DC 15 Heal — no skill check system yet)
- Does not implement recovery from negative HP (rest_resolver handles HP recovery from rest; recovery from −3 to 1 HP after 1 hour deferred)
- Does not implement nonlethal damage (separate HP pool, `NONLETHAL_DAMAGE` field — different WO)
- Does not implement death saving throws (5e concept — not in 3.5e)
- Does not change `EF.DEFEATED` semantics for monsters/NPCs that have no Fort save — they bleed and die at −10 the same as PCs

---

## 9. Preflight

```bash
cd f:/DnD-3.5

# After implementing attack_resolver.py + full_attack_resolver.py changes:
python -m pytest tests/test_engine_gate_cp17.py tests/test_engine_gate_cp22.py tests/test_engine_gate_cp23.py -v
# Expect some failures — defeat assertions need updating

# Regenerate gold masters:
python tests/_gen_v12.py   # or applicable script
python -m pytest tests/test_play_loop_spellcasting.py -v

# Run new gate:
python -m pytest tests/test_engine_death_dying_gate.py -v
# DD-01 through DD-12 must pass.

# Full suite:
python -m pytest tests/ -x --tb=short
# Zero new regressions beyond expected gold-master update.
```
