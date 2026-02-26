# WO-ENGINE-CONDITION-DURATION-001 — Condition Duration Tracking + Auto-Expiry
## Status: DISPATCH-READY
## Priority: HIGH
## Closes: FINDING-ENGINE-CONDITION-DURATION-001

---

## Context

CP-16 (CONDITIONS-BLIND-DEAF-001) explicitly deferred duration tracking with the comment in `ConditionInstance`:

```python
# CP-16 SCOPE:
# - No duration tracking (manual removal only)
# - No automatic expiration (deferred to CP-17+)
```

The result: every condition applied to an entity persists indefinitely until the applying resolver also removes it. A 1-round stun from a critical hit lasts forever. CONFUSED lasts until manually cleared. ENTANGLED from a spell lasts past its duration.

**What already exists (do NOT re-implement):**
- `DurationTracker.tick_round()` — decrements spell effect `rounds_remaining`, removes expired spell effects, and exposes `effect.condition_applied` for removal from entity. This handles SPELL-SOURCED conditions. DO NOT CHANGE THIS PATH.
- `conditions.py:remove_condition()` — pure function, removes condition by type from entity dict.
- `play_loop.py:2972` — `tick_round()` call at end-of-round; handles expired spell effects at lines 2992-2996.

**The gap this WO fills:**
Non-spell conditions (GRAPPLED, STUNNED from a hit, PRONE, ENTANGLED from a non-tracked source, etc.) have no `rounds_remaining` field at all. They can only be removed by the code that applied them or by manual logic. This WO adds an opt-in duration field to `ConditionInstance` and a tick that auto-expires conditions whose duration runs out.

---

## Section 0 — Assumptions to Validate (read before coding)

1. Read `aidm/schemas/conditions.py` — confirm `ConditionInstance` has no `duration_rounds` field. Confirm `to_dict()` / `from_dict()` pattern.
2. Read `aidm/core/conditions.py` — confirm `remove_condition()` signature. Confirm `apply_condition()`.
3. Read `aidm/core/play_loop.py` lines 2960-3020 — confirm the `tick_round()` call site, the expired-effect loop, and how conditions are removed from entities post-expiry. This is the integration point.
4. Read the condition factory functions (e.g., `create_stunned_condition()`, `create_prone_condition()`, `create_entangled_condition()` in `save_resolver.py` or wherever they live) — confirm their return types. These will need `duration_rounds` added where PHB specifies a fixed duration.
5. Read `aidm/schemas/entity_fields.py` — confirm `EF.CONDITIONS` = `"conditions"`.

**Preflight gate:** Run full test suite before any change. Record pass count.

---

## Section 1 — Target Lock

After this WO:
- `ConditionInstance` has an optional `duration_rounds: Optional[int] = None` field. `None` = permanent (current behavior, no change). Integer = rounds remaining before auto-expiry.
- A new `tick_conditions(world_state, events, current_event_id, timestamp) -> tuple[WorldState, list, int]` function in `aidm/core/conditions.py` decrements `duration_rounds` for all entities' timed conditions, removes expired ones, and emits `condition_expired` events.
- `tick_conditions()` is called at end-of-round in `play_loop.py`, in the same block as `duration_tracker.tick_round()` (lines 2971-3018).
- PHB-correct durations wired into the condition factories for the most common timed conditions (see Section 3).
- FINDING-ENGINE-CONDITION-DURATION-001 CLOSED.

---

## Section 2 — Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Duration field location | `ConditionInstance.duration_rounds: Optional[int]` | Conditions are the right locus — parallel to `ActiveSpellEffect.rounds_remaining`. Avoids a parallel tracking dict. |
| `None` vs `0` for permanent | `None` = permanent; `0` = expired this tick | Clear semantics. `None` means "no expiry." `0` means "just expired" — remove immediately. |
| Decrement timing | End of actor's LAST turn in round (same block as `tick_round()` at play_loop:2972) | Matches CP-19 convention. Consistent expiry model. |
| ARCH-TICK-001 compliance | Two-pass: collect expired, then remove | Required per ARCH-TICK-001 (locked invariant). Do NOT mutate entity dict while iterating it. |
| Condition factories to update | STUNNED (1 round), DAZED (1 round), NAUSEATED (1 round), ENTANGLED (builder locates duration from spell), CONFUSED (builder locates duration from spell). PRONE = permanent (stand-up action removes it). GRAPPLED/GRAPPLING = permanent (escape action removes it). BLINDED/DEAFENED = builder checks spell duration. | See PHB references in Section 3. |
| Event type | `condition_expired` — already in use by CP-19 for spell-effect expiry. Add `source: "condition_tick"` to payload to distinguish from spell-effect expiry. | Reuse existing event type rather than a new one. |
| Interaction with spell-effect path | NO change to the spell-effect path. Two independent expiry systems. A condition applied by a spell is tracked by BOTH (spell duration controls removal via DurationTracker; condition's own `duration_rounds` is a second gate). Builder must ensure no double-removal: if spell effect expires first, condition is removed; if condition `duration_rounds` hits zero first, condition is removed and spell effect lingers (probably fine — spell ended its condition). | Acceptable — spell-effect path is authoritative for spell durations. |

---

## Section 3 — Contract Spec

### 3.1 `ConditionInstance` field addition

In `aidm/schemas/conditions.py`, add to `ConditionInstance` dataclass:

```python
duration_rounds: Optional[int] = None
"""Rounds remaining before auto-expiry. None = permanent (removed only by resolver logic).
PHB: STUNNED 1 round, DAZED 1 round, NAUSEATED 1 round per hit.
Set on application; decremented by tick_conditions() each round.
"""
```

Update `to_dict()` — include `duration_rounds` if not None:
```python
d = {...existing fields...}
if self.duration_rounds is not None:
    d["duration_rounds"] = self.duration_rounds
return d
```

Update `from_dict()` — read `duration_rounds` with default None:
```python
duration_rounds=data.get("duration_rounds", None)
```

### 3.2 `tick_conditions()` function in `aidm/core/conditions.py`

```python
def tick_conditions(
    world_state: WorldState,
    events: list,
    current_event_id: int,
    timestamp: str,
) -> tuple[WorldState, list, int]:
    """Decrement duration_rounds on all timed conditions across all entities.

    Two-pass per ARCH-TICK-001:
    Pass 1 — collect (entity_id, condition_type_str) pairs whose duration_rounds hits 0.
    Pass 2 — remove those conditions and emit condition_expired events.

    Returns updated (world_state, events, current_event_id).
    """
    from aidm.core.event_log import Event
    from aidm.schemas.conditions import ConditionInstance

    # Pass 1: collect expired conditions
    to_expire = []  # list of (entity_id, condition_type_str, condition_dict)

    for entity_id, entity in world_state.entities.items():
        conditions = entity.get(EF.CONDITIONS, {})
        if not isinstance(conditions, dict):
            continue
        for cond_type_str, cond_dict in conditions.items():
            if not isinstance(cond_dict, dict):
                continue
            dur = cond_dict.get("duration_rounds")
            if dur is None:
                continue  # permanent
            new_dur = dur - 1
            if new_dur <= 0:
                to_expire.append((entity_id, cond_type_str, cond_dict))
            else:
                # Decrement in-place in the dict (will be committed via Pass 2 WorldState rebuild)
                cond_dict["duration_rounds"] = new_dur

    if not to_expire:
        return world_state, events, current_event_id

    # Pass 2: remove expired conditions and emit events
    new_entities = {eid: dict(e) for eid, e in world_state.entities.items()}
    for entity_id, cond_type_str, cond_dict in to_expire:
        conditions = dict(new_entities[entity_id].get(EF.CONDITIONS, {}))
        conditions.pop(cond_type_str, None)
        new_entities[entity_id] = dict(new_entities[entity_id])
        new_entities[entity_id][EF.CONDITIONS] = conditions

        events.append(Event(
            event_id=current_event_id,
            event_type="condition_expired",
            timestamp=timestamp,
            payload={
                "entity_id": entity_id,
                "condition_type": cond_type_str,
                "source": cond_dict.get("source", "unknown"),
                "reason": "condition_tick",
            },
        ))
        current_event_id += 1

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=new_entities,
        active_combat=world_state.active_combat,
    )
    return world_state, events, current_event_id
```

**Builder must verify:** the WorldState constructor signature (keyword args `ruleset_version`, `entities`, `active_combat` — confirm against existing call sites nearby).

### 3.3 Wiring in `play_loop.py`

In the existing end-of-round block (currently around line 2971):

```python
# Existing:
expired_effects = duration_tracker.tick_round()
# ... existing loop handling expired spell effects ...

# NEW — add after existing spell-effect expiry loop:
from aidm.core.conditions import tick_conditions as _tick_conditions
world_state, events, current_event_id = _tick_conditions(
    world_state, events, current_event_id, timestamp
)
```

Position: AFTER the spell-effect expired loop (lines 2992-2996), BEFORE `world_state = WorldState(...)` rebuild that persists the tracker (line ~3018).

### 3.4 Condition factories — duration_rounds injection

Builder must locate each factory function and add `duration_rounds` where PHB specifies a fixed duration. Known durations:

| Condition | PHB Duration | duration_rounds value |
|-----------|-------------|----------------------|
| STUNNED | 1 round (PHB p.302) | `1` |
| DAZED | 1 round (PHB p.300) | `1` |
| NAUSEATED | 1 round per hit (PHB p.301) | `1` |
| TURNED | Duration until rebuked/new day | `None` (permanent — removed by condition_ended or cleric action) |
| ENTANGLED | Spell duration (builder checks) | Per spell — if spell-tracked, leave `None`; if not, add duration |
| CONFUSED | Spell duration (builder checks) | Same as above |
| BLINDED/DEAFENED from condition | 1 round if from ability check; else spell | Builder determines per factory |
| PRONE | Permanent until stand-up | `None` |
| GRAPPLED/GRAPPLING | Permanent until escape | `None` |
| PARALYZED | Spell duration | Leave `None` if spell-tracked |

**Builder priority:** STUNNED, DAZED, NAUSEATED are the most critical (1-round conditions that currently persist forever). Wire these first. Others: builder's judgment on scope.

**Note:** Conditions applied via `apply_condition()` from spell resolvers that are ALSO tracked by DurationTracker can safely have `duration_rounds=None` — the DurationTracker handles their expiry. Only conditions NOT tracked by a spell effect need `duration_rounds` set.

---

## Section 4 — Implementation Plan

1. **Read** `conditions.py` (schemas), `conditions.py` (core), `play_loop.py` lines 2960-3020, condition factory locations — confirm all patterns.
2. **Add** `duration_rounds: Optional[int] = None` to `ConditionInstance` + update `to_dict()`/`from_dict()`.
3. **Implement** `tick_conditions()` in `aidm/core/conditions.py`.
4. **Wire** `tick_conditions()` call in `play_loop.py` end-of-round block.
5. **Update** STUNNED, DAZED, NAUSEATED factory functions to pass `duration_rounds=1`.
6. **Run** full test suite — record pass count, confirm no regression.
7. **Write** gate test file `tests/test_engine_condition_duration_001_gate.py` — minimum 10 tests.

### Gate test spec (minimum 10)

| ID | Test | Pass condition |
|----|------|----------------|
| CD-001 | STUNNED condition applied with duration_rounds=1; after one tick, condition removed | condition absent from entity |
| CD-002 | DAZED condition applied with duration_rounds=1; after tick, removed | condition absent |
| CD-003 | NAUSEATED condition applied with duration_rounds=1; after tick, removed | condition absent |
| CD-004 | Permanent condition (PRONE, duration_rounds=None) survives tick | condition still present |
| CD-005 | GRAPPLED (duration_rounds=None) survives tick | condition still present |
| CD-006 | condition_expired event emitted with correct payload on expiry | event_type=condition_expired, entity_id, condition_type, source, reason=condition_tick |
| CD-007 | Two entities with same condition type — both tick independently | each decrements correctly |
| CD-008 | Entity with 2-round condition: after 1 tick = present (duration_rounds=1), after 2nd tick = absent | round-by-round correct |
| CD-009 | Entity with NO conditions: tick_conditions() is a no-op (no error, no events) | clean return |
| CD-010 | Regression: existing spell-effect expiry (DurationTracker path) still works after change | spell condition still expires via DurationTracker |

---

## Integration Seams

| Component | File | Notes |
|-----------|------|-------|
| `ConditionInstance` | `aidm/schemas/conditions.py` | Add `duration_rounds: Optional[int] = None` + serialization |
| `tick_conditions()` | `aidm/core/conditions.py` | New function — two-pass per ARCH-TICK-001 |
| End-of-round hook | `aidm/core/play_loop.py` ~line 2972 | After spell-effect expired loop, before WorldState persist |
| STUNNED factory | Builder locates (`save_resolver.py` or `condition_combat_resolver.py`) | Add `duration_rounds=1` |
| DAZED factory | Builder locates | Add `duration_rounds=1` |
| NAUSEATED factory | Builder locates | Add `duration_rounds=1` |
| `remove_condition()` | `aidm/core/conditions.py:176` | Already exists — use it in Pass 2 OR inline dict.pop (builder picks) |
| `Event` constructor | `aidm/core/event_log.py` | `Event(event_id=, event_type=, timestamp=, payload=)` — NOT `id=`, `type=`, `data=` |
| `WorldState` | `aidm/schemas/world_state.py` | Confirm constructor kwargs before rebuilding |

---

## Architectural Invariants

**ARCH-TICK-001 (locked):** Two-pass design mandatory. Pass 1: collect mutation targets. Pass 2: apply mutations. No mid-loop WorldState reassignment. `tick_conditions()` must follow this pattern — the pseudocode above is correct.

**ARCH-TICK-001 audit:** Before submitting debrief, confirm `tick_conditions()` does NOT mutate entities during Pass 1 iteration. The only safe writes during Pass 1 are to local variables.

---

## Out of Scope

- Stacking conditions (same type applied twice) — CP-16 note says identical conditions overwrite. No change.
- Condition save-to-remove (e.g., repeat Fort saves to end PARALYZED) — separate WO.
- `TURNED` condition expiry — removed by cleric action, not timer. Leave `duration_rounds=None`.
- ENTANGLED/CONFUSED from spell DurationTracker — leave `duration_rounds=None` unless builder confirms the specific factory is NOT wired to a spell effect.

---

## Debrief Required

**File to:** `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-CONDITION-DURATION-001.md`

**Pass 1 — Context dump:**
- List every file modified with line ranges
- State which condition factories were updated and what `duration_rounds` value was set
- State the exact position of `tick_conditions()` call in play_loop.py (line number)
- Confirm CD-001–010 pass counts
- Confirm regression gate pass count before vs after

**Pass 2 — PM summary ≤100 words**

**Pass 3 — Retrospective:**
- Any conditions where duration was ambiguous (permanent vs. timed)?
- Did the two-pass ARCH-TICK-001 pattern cause any complications?
- Conditions that should have duration_rounds set but were left as None — list them and explain why.

**Radar (one line each):**
- Regression gate: PASS (count before vs after)
- CD-001–010: all PASS
- `ConditionInstance.duration_rounds` field added + serialized: CONFIRMED
- `tick_conditions()` in `aidm/core/conditions.py`: PRESENT
- `tick_conditions()` wired in play_loop end-of-round: CONFIRMED (line number)
- STUNNED duration_rounds=1: CONFIRMED
- DAZED duration_rounds=1: CONFIRMED
- NAUSEATED duration_rounds=1: CONFIRMED
- Permanent conditions (PRONE, GRAPPLED) duration_rounds=None: CONFIRMED
- ARCH-TICK-001 two-pass verified: CONFIRMED
- FINDING-ENGINE-CONDITION-DURATION-001: CLOSED

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Drafted: 2026-02-25 — Slate*
