# WO-ENGINE-WILDSHAPE-DURATION-001 — Wild Shape Duration: Round-Counter Auto-Revert

**Issued:** 2026-02-24
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** LOW (FINDING-WILDSHAPE-DURATION-001 — functional gap; DM must manually trigger revert when duration expires)
**WO type:** BUG (missing enforcement)
**Gate:** ENGINE-WILDSHAPE-DURATION (10 tests)

---

## 1. Target Lock

**What works:** `EF.WILD_SHAPE_HOURS_REMAINING` is set to `druid_level` at transform (line 196 of `wild_shape_resolver.py`) and zeroed at revert (line 279). The field exists and is correctly bookmarked.

**What's missing:** `WILD_SHAPE_HOURS_REMAINING` is never decremented. The druid stays transformed indefinitely unless the DM manually issues a `RevertFormIntent`. PHB p.37: Wild Shape lasts `druid_level` hours. There is no time infrastructure in the engine — combat operates in rounds, not hours.

**Root cause (confirmed by PM inspection):**
- No `tick_wild_shape_duration()` function exists
- No round-end hook checks `WILD_SHAPE_ACTIVE`
- The field is purely decorative at present

**Infrastructure approach (approved — no real time system):**
Wild Shape duration is expressed as hours, but the engine has no wall-clock or hour system. The approved proxy: `WILD_SHAPE_ROUNDS_REMAINING = druid_level × 10` (10 rounds ≈ 1 minute, × druid_level hours is very loose, but the intent is *the effect eventually ends without DM intervention*). This is not a strict PHB conversion — it is a combat-session proxy that guarantees auto-revert without requiring a full time infrastructure. Noted in the event payload for traceability.

At round-end (when the last actor's turn completes), decrement `WILD_SHAPE_ROUNDS_REMAINING` for every entity with `WILD_SHAPE_ACTIVE=True`. When it reaches 0, call `resolve_revert_form()` programmatically.

**PHB reference:** PHB p.37 — "The druid can remain in the new form indefinitely but can choose to resume her normal form at will. ... [Wild Shape lasts] a number of hours equal to the druid's level."

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | New EF field or reuse WILD_SHAPE_HOURS_REMAINING? | New field: `EF.WILD_SHAPE_ROUNDS_REMAINING` (int). Keep `WILD_SHAPE_HOURS_REMAINING` unchanged — it's the PHB-faithful value, retained for display/reference. The new field is the operational counter. |
| 2 | What is the initial round count? | `druid_level × 10`. Set at transform in `resolve_wild_shape()`, alongside the existing `WILD_SHAPE_HOURS_REMAINING` assignment. |
| 3 | Where is the tick hook? | Round-end block in `play_loop.py` — inside the `if current_position == last_actor_index:` block, after `resolve_dying_tick()`. Same pattern as dying tick. |
| 4 | What happens when counter reaches 0? | Call `resolve_revert_form()` with a synthetic `RevertFormIntent`. Emit `wild_shape_expired` event (not `wild_shape_end` — distinct from voluntary revert). |
| 5 | Does `resolve_revert_form()` need changes? | No. The function already handles revert correctly. The duration tick just calls it with a synthetic intent. |
| 6 | Synthetic RevertFormIntent construction? | `RevertFormIntent(actor_id=entity_id)` — same as a player-issued revert. The resolver is agnostic to why it was called. The `wild_shape_expired` event is emitted by the tick function *before* calling resolve_revert_form (or instead — see below). |
| 7 | wild_shape_expired vs wild_shape_end? | `tick_wild_shape_duration()` emits `wild_shape_expired` with the actor_id and reason `duration_expired`. Then calls `resolve_revert_form()` which emits `wild_shape_end`. Both events appear in sequence. Consumers can distinguish voluntary revert (only `wild_shape_end`) from timeout (both `wild_shape_expired` + `wild_shape_end`). |
| 8 | Multi-druid support? | Yes. Tick iterates all entities with `WILD_SHAPE_ACTIVE=True`. Each is checked and decremented independently. |
| 9 | What if WILD_SHAPE_ROUNDS_REMAINING is missing on an already-transformed entity? | Treat as `druid_level × 10` (reconstruct). Guard: `if entity.get(EF.WILD_SHAPE_ROUNDS_REMAINING, None) is None: entity[EF.WILD_SHAPE_ROUNDS_REMAINING] = druid_level * 10`. This handles any entity transformed before this WO lands. |

---

## 3. Contract Spec

### New EF constant in `aidm/schemas/entity_fields.py`

```python
WILD_SHAPE_ROUNDS_REMAINING = "wild_shape_rounds_remaining"
# int: countdown timer for Wild Shape duration (combat proxy).
# Initialized at transform to druid_level * 10.
# Decremented each round-end by tick_wild_shape_duration() in play_loop.py.
# When it reaches 0, auto-revert is triggered.
# WILD_SHAPE_HOURS_REMAINING (int) is the PHB-faithful display value; unchanged.
```

### Modification: `resolve_wild_shape()` in `aidm/core/wild_shape_resolver.py`

In the Wild Shape bookkeeping block (after line 196 where `WILD_SHAPE_HOURS_REMAINING` is set), add:

```python
actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = druid_level * 10
```

### Modification: `resolve_revert_form()` in `aidm/core/wild_shape_resolver.py`

In the clear Wild Shape state block (near line 279 where `WILD_SHAPE_HOURS_REMAINING` is zeroed), add:

```python
actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = 0
```

### New function: `tick_wild_shape_duration()` in `aidm/core/wild_shape_resolver.py`

```python
def tick_wild_shape_duration(
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Decrement Wild Shape round counter for all transformed druids.

    Called at round-end by play_loop.py. When WILD_SHAPE_ROUNDS_REMAINING
    reaches 0, triggers auto-revert via resolve_revert_form().
    """
    events: List[Event] = []
    ws = deepcopy(world_state)
    current_event_id = next_event_id

    for entity_id, entity in ws.entities.items():
        if not entity.get(EF.WILD_SHAPE_ACTIVE, False):
            continue

        druid_level = entity.get(EF.CLASS_LEVELS, {}).get("druid", 1)

        # Reconstruct counter if missing (entity transformed before WO landed)
        if entity.get(EF.WILD_SHAPE_ROUNDS_REMAINING, None) is None:
            entity[EF.WILD_SHAPE_ROUNDS_REMAINING] = druid_level * 10

        rounds_left = entity.get(EF.WILD_SHAPE_ROUNDS_REMAINING, 1) - 1
        entity[EF.WILD_SHAPE_ROUNDS_REMAINING] = rounds_left

        if rounds_left <= 0:
            # Emit expiry notice before revert
            events.append(Event(
                event_id=current_event_id,
                event_type="wild_shape_expired",
                timestamp=timestamp,
                payload={
                    "actor_id": entity_id,
                    "reason": "duration_expired",
                    "form_was": entity.get(EF.WILD_SHAPE_FORM, ""),
                },
                citations=[],
            ))
            current_event_id += 1

            # Rebuild WorldState with decremented counter before calling revert
            ws = WorldState(
                ruleset_version=ws.ruleset_version,
                entities=ws.entities,
                active_combat=ws.active_combat,
            )

            # Synthetic revert intent — identical to a player-issued revert
            from aidm.schemas.intents import RevertFormIntent
            synthetic_intent = RevertFormIntent(actor_id=entity_id)
            revert_events, ws = resolve_revert_form(
                intent=synthetic_intent,
                world_state=ws,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.01,
            )
            events.extend(revert_events)
            current_event_id += len(revert_events)

    return events, ws
```

### Modification: `play_loop.py` — round-end wire

In the round-end block, after the `resolve_dying_tick()` block and before the `updated_state` rebuild:

```python
            # WO-ENGINE-WILDSHAPE-DURATION-001: Wild Shape duration auto-revert
            _has_ws = any(
                e.get(EF.WILD_SHAPE_ACTIVE, False)
                for e in world_state.entities.values()
            )
            if _has_ws:
                from aidm.core.wild_shape_resolver import tick_wild_shape_duration
                _wsd_events, world_state = tick_wild_shape_duration(
                    world_state=world_state,
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.6,
                )
                events.extend(_wsd_events)
                current_event_id += len(_wsd_events)
```

Note: `timestamp + 0.6` places this after dying tick (`+ 0.5`) and before updated_state rebuild. Offset is minor — just avoids timestamp collision in the same round-end block.

---

## 4. Implementation Plan

### Step 1 — `aidm/schemas/entity_fields.py`
Add `WILD_SHAPE_ROUNDS_REMAINING = "wild_shape_rounds_remaining"` alongside the other Wild Shape EF constants.

### Step 2 — `aidm/core/wild_shape_resolver.py`
1. In `resolve_wild_shape()`: set `actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = druid_level * 10` (one line, after `WILD_SHAPE_HOURS_REMAINING` assignment)
2. In `resolve_revert_form()`: clear `actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = 0` (one line, alongside `WILD_SHAPE_HOURS_REMAINING = 0`)
3. Add `tick_wild_shape_duration()` function (~35 lines)

### Step 3 — `aidm/core/play_loop.py`
Wire `tick_wild_shape_duration()` in the round-end block, after `resolve_dying_tick()`, using the lazy-import + any_check pattern.

### Step 4 — Tests (`tests/test_engine_wildshape_duration_gate.py`)
Gate: ENGINE-WILDSHAPE-DURATION — 10 tests

| Test | Description |
|------|-------------|
| WSD-01 | Transform sets `WILD_SHAPE_ROUNDS_REMAINING = druid_level × 10` |
| WSD-02 | Tick decrements counter by 1 each round-end |
| WSD-03 | Counter reaches 0 → `wild_shape_expired` emitted → `wild_shape_end` follows |
| WSD-04 | After auto-revert: `WILD_SHAPE_ACTIVE=False`, `WILD_SHAPE_ROUNDS_REMAINING=0`, restored stats |
| WSD-05 | Level 5 druid: starts at 50 rounds; level 10 druid: starts at 100 rounds |
| WSD-06 | Voluntary revert mid-duration: `WILD_SHAPE_ROUNDS_REMAINING` zeroed, no expiry event |
| WSD-07 | Two druids in same combat: independent counters, independent expiry |
| WSD-08 | Missing counter reconstruct: entity with `WILD_SHAPE_ACTIVE=True` but no `ROUNDS_REMAINING` → treated as `druid_level × 10` (not immediate expiry) |
| WSD-09 | No tick when no transformed entities (`_has_ws` guard — no import, no iteration) |
| WSD-10 | Regression: ENGINE-WILD-SHAPE 10/10 unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/schemas/entity_fields.py` — 1 new constant
- `aidm/core/wild_shape_resolver.py` — `tick_wild_shape_duration()` new function; 2 one-line additions in existing functions
- `aidm/core/play_loop.py` — round-end wire (~8 lines)

**Files NOT touched:**
- `aidm/schemas/intents.py` — `RevertFormIntent` already exists; synthetic instantiation inside tick function
- `WILD_SHAPE_FORMS` schema — unchanged

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
NOT `id=`, `type=`, `data=`.

**Entity field pattern (mandatory):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("druid", 1)
entity.get(EF.WILD_SHAPE_ROUNDS_REMAINING, None)
entity.get(EF.WILD_SHAPE_ACTIVE, False)
```

**Round-end guard pattern (established by dying_resolver):**
```python
_has_ws = any(e.get(EF.WILD_SHAPE_ACTIVE, False) for e in world_state.entities.values())
if _has_ws:
    from aidm.core.wild_shape_resolver import tick_wild_shape_duration
    ...
```

**Timestamp offset convention (round-end block):**
- `duration_tracker.tick_round()`: base timestamp
- `resolve_dying_tick()`: `timestamp + 0.5`
- `tick_wild_shape_duration()`: `timestamp + 0.6`

**WorldState rebuild:** `tick_wild_shape_duration()` must rebuild WorldState before calling `resolve_revert_form()` when expiry occurs, so the revert sees the updated entity dict. Pattern identical to `tick_inspire_courage()` any_mutated pattern.

---

## Assumptions to Validate

1. `EF.WILD_SHAPE_ACTIVE` exists and is set to `True` at transform — confirmed by ENGINE-WILD-SHAPE gate tests
2. `EF.WILD_SHAPE_HOURS_REMAINING` exists and is set at transform — confirmed by PM inspection (line 196)
3. `resolve_revert_form()` takes `(intent, world_state, next_event_id, timestamp)` — confirmed by PM inspection
4. `RevertFormIntent` is importable from `aidm.schemas.intents` — confirmed by existing play_loop routing
5. Round-end block fires when `current_position == last_actor_index` — confirmed by PM inspection (line ~2907)
6. `EF.CLASS_LEVELS` dict contains `"druid"` key for druid entities — confirmed by ENGINE-WILD-SHAPE gate pattern

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_cp24.py tests/test_maneuvers_core.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_wildshape_duration_gate.py -v
python -m pytest tests/test_engine_wildshape_hp_gate.py -x -q  # run alongside if both dispatched
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

ENGINE-WILD-SHAPE 10/10 unchanged. ENGINE-WILDSHAPE-DURATION 10/10 new.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/schemas/entity_fields.py` — `WILD_SHAPE_ROUNDS_REMAINING` constant
- [ ] `aidm/core/wild_shape_resolver.py` — `tick_wild_shape_duration()` + 2 one-line additions
- [ ] `aidm/core/play_loop.py` — round-end wire (~8 lines)
- [ ] `tests/test_engine_wildshape_duration_gate.py` — 10/10

**Gate:** ENGINE-WILDSHAPE-DURATION 10/10
**Regression bar:** ENGINE-WILD-SHAPE 10/10 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-WILDSHAPE-DURATION-001.md` on completion.

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
