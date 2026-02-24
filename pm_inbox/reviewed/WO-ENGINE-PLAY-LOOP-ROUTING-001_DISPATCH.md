# WO-ENGINE-PLAY-LOOP-ROUTING-001 — Wire Class Feature Intents into execute_turn

**Issued:** 2026-02-24
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** MEDIUM (FINDING-PLAY-LOOP-ROUTING-001 — functional gap; class features silently no-op in live play)
**WO type:** BUG (routing gap — intents fall through execute_turn without resolving)
**Gate:** ENGINE-PLAY-LOOP-ROUTING (10 tests)

---

## 1. Target Lock

Five intent types are imported and recognized for actor-ID extraction in `play_loop.py` but have **no elif routing branch** in the `execute_turn` dispatch chain. When a player or monster submits one of these intents, it silently falls through to the monster-policy block or the PC stub block and emits garbage events. No resolution occurs.

**Affected intents:**
| Intent | Resolver | Function |
|--------|----------|----------|
| `RageIntent` | `rage_resolver.activate_rage()` | Barbarian rage activation |
| `SmiteEvilIntent` | `smite_evil_resolver.resolve_smite_evil()` | Paladin smite |
| `BardicMusicIntent` | `bardic_music_resolver.resolve_bardic_music()` | Bard inspire courage |
| `WildShapeIntent` | `wild_shape_resolver.resolve_wild_shape()` | Druid form change |
| `RevertFormIntent` | `wild_shape_resolver.resolve_revert_form()` | Druid revert |

**Why gate tests still pass:** All ENGINE-BARBARIAN-RAGE, ENGINE-SMITE-EVIL, ENGINE-BARDIC-MUSIC, and ENGINE-WILD-SHAPE gate tests call resolvers directly — they never go through `execute_turn`. The gap is invisible to those gates. This WO adds integration-level tests that go through `execute_turn`.

**Confirmed by PM inspection 2026-02-24:** The routing chain runs from line 1867 to line 2663. None of these five intents appear in an `elif isinstance(...)` branch.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | One WO or five micro-WOs? | **One WO.** All five are identical in structure: read actor ID, call resolver, extend events, update world_state. Total scope is ~50 lines of routing branches. |
| 2 | Where in the elif chain? | After `EnergyDrainAttackIntent` (line ~1936) and before `FullAttackIntent`. Group all five class-feature intents together with a block comment. |
| 3 | Should SmiteEvilIntent also wire a follow-up attack? | **No.** `resolve_smite_evil()` already calls `resolve_attack()` internally — it returns a full event list including the attack. The routing branch just calls the resolver and extends events. |
| 4 | Concentration break check after smite? | **Yes** — same pattern as AttackIntent. `resolve_smite_evil()` returns hp_changed events; check concentration on damaged entity. |
| 5 | Does WildShapeIntent routing conflict with WO-ENGINE-NATURAL-ATTACK-001? | **No.** Natural attack WO adds `NaturalAttackIntent`. This WO adds `WildShapeIntent` / `RevertFormIntent`. Different branches, parallel-safe. |
| 6 | RNG required? | `activate_rage` does not take `rng`. `resolve_smite_evil` takes `rng`. `resolve_bardic_music` does not take `rng`. `resolve_wild_shape` / `resolve_revert_form` do not take `rng`. Wire accordingly. |
| 7 | AoO check needed? | **No new AoO logic.** Wild Shape, Rage, Bardic Music are standard actions that do not provoke in 3.5e (PHB p.142 — free actions and standard non-movement actions do not provoke). The AoO block above the routing chain has already fired; these just slot into the existing routing chain after it. |

---

## 3. Contract Spec

### Routing branches to add in `play_loop.py` execute_turn

Insert after the `EnergyDrainAttackIntent` block (~line 1936), before the `FullAttackIntent` block:

```python
        # WO-ENGINE-PLAY-LOOP-ROUTING-001: Class feature intent routing
        elif isinstance(combat_intent, RageIntent):
            from aidm.core.rage_resolver import validate_rage, activate_rage
            _rage_actor = world_state.entities.get(combat_intent.actor_id, {})
            _rage_err = validate_rage(_rage_actor, world_state)
            if _rage_err:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": combat_intent.actor_id,
                        "intent_type": "RageIntent",
                        "reason": _rage_err,
                    },
                ))
                current_event_id += 1
            else:
                _rage_events, world_state = activate_rage(
                    actor_id=combat_intent.actor_id,
                    world_state=world_state,
                    next_event_id=current_event_id,
                    timestamp=timestamp + 0.1,
                )
                events.extend(_rage_events)
                current_event_id += len(_rage_events)
            narration = "rage_activated"

        elif isinstance(combat_intent, SmiteEvilIntent):
            from aidm.core.smite_evil_resolver import resolve_smite_evil
            _smite_events, world_state = resolve_smite_evil(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_smite_events)
            current_event_id += len(_smite_events)
            # Concentration break on any damage dealt
            for _hp_ev in [e for e in _smite_events if e.event_type == "hp_changed"]:
                _dmg = abs(_hp_ev.payload.get("delta", 0))
                if _dmg > 0:
                    _conc_evs, world_state = _check_concentration_break(
                        caster_id=_hp_ev.payload.get("entity_id"),
                        damage_dealt=_dmg,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.15,
                    )
                    events.extend(_conc_evs)
                    current_event_id += len(_conc_evs)
            narration = "smite_evil_resolved"

        elif isinstance(combat_intent, BardicMusicIntent):
            from aidm.core.bardic_music_resolver import resolve_bardic_music
            _bardic_events, world_state = resolve_bardic_music(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_bardic_events)
            current_event_id += len(_bardic_events)
            narration = "bardic_music_resolved"

        elif isinstance(combat_intent, WildShapeIntent):
            from aidm.core.wild_shape_resolver import resolve_wild_shape
            _ws_events, world_state = resolve_wild_shape(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_ws_events)
            current_event_id += len(_ws_events)
            narration = "wild_shape_resolved"

        elif isinstance(combat_intent, RevertFormIntent):
            from aidm.core.wild_shape_resolver import resolve_revert_form
            _rv_events, world_state = resolve_revert_form(
                intent=combat_intent,
                world_state=world_state,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(_rv_events)
            current_event_id += len(_rv_events)
            narration = "revert_form_resolved"
```

**No other files need to change.** The actor-ID extraction block (lines 1462-1466) already covers all five intents. The target-validation block does not apply (these are non-attack intents). The imports at the top of play_loop.py already include all five intent classes.

---

## 4. Implementation Plan

### Step 1 — `aidm/core/play_loop.py` only
Insert the five elif branches as shown in Section 3. No other files touched.

Verify insertion point:
- Find `elif isinstance(combat_intent, EnergyDrainAttackIntent):` — insert **after** its block closes
- Find `elif isinstance(combat_intent, FullAttackIntent):` — insert **before** it
- If WO-ENGINE-NATURAL-ATTACK-001 has already landed, `NaturalAttackIntent` will be in this section too — insert class-feature block before or after it, order does not matter

### Step 2 — Tests (`tests/test_engine_play_loop_routing_gate.py`)
Gate: ENGINE-PLAY-LOOP-ROUTING — 10 tests, all going through `execute_turn` (not calling resolvers directly)

| Test | Description |
|------|-------------|
| PLR-01 | `RageIntent` through `execute_turn` → `rage_start` event emitted, `RAGE_ACTIVE=True` on actor |
| PLR-02 | `RageIntent` on non-barbarian → `intent_validation_failed` event |
| PLR-03 | `SmiteEvilIntent` through `execute_turn` → `smite_declared` + `attack_roll` events emitted |
| PLR-04 | `SmiteEvilIntent` on non-paladin → `intent_validation_failed` event |
| PLR-05 | `BardicMusicIntent` through `execute_turn` → `inspire_courage_start` event, `INSPIRE_COURAGE_ACTIVE=True` |
| PLR-06 | `BardicMusicIntent` on non-bard → `intent_validation_failed` event |
| PLR-07 | `WildShapeIntent` through `execute_turn` → `wild_shape_start` event, `WILD_SHAPE_ACTIVE=True` |
| PLR-08 | `WildShapeIntent` on non-druid → `intent_validation_failed` event |
| PLR-09 | `RevertFormIntent` through `execute_turn` when in Wild Shape → `wild_shape_end` event |
| PLR-10 | `RevertFormIntent` when NOT in Wild Shape → `intent_validation_failed` event |

**Test fixture pattern:** Each test constructs a minimal entity with the appropriate `EF.CLASS_LEVELS`, builds a `WorldState`, builds a `TurnContext`, calls `execute_turn(turn_ctx, world_state, combat_intent=<intent>, rng=rng)`, and asserts on the returned events list. Mirror the pattern from existing gate tests (e.g., `test_engine_gate_barbarian_rage.py`) but route through execute_turn instead of calling the resolver directly.

---

## Integration Seams

**Files touched:**
- `aidm/core/play_loop.py` — 5 elif branches, ~60 lines inserted

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
entity.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)
entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
entity.get(EF.CLASS_LEVELS, {}).get("bard", 0)
entity.get(EF.CLASS_LEVELS, {}).get("druid", 0)
```
`EF.CLASS_FEATURES` does **not** exist.

**RNG:** Only `SmiteEvilIntent` path uses `rng` (passed to `resolve_smite_evil`). The other four do not.

**Resolver return types (confirmed by PM source inspection):**
- `activate_rage(actor_id, world_state, next_event_id, timestamp)` → `(List[Event], WorldState)`
- `resolve_smite_evil(intent, world_state, rng, next_event_id, timestamp)` → `(List[Event], WorldState)`
- `resolve_bardic_music(intent, world_state, next_event_id, timestamp)` → `(List[Event], WorldState)`
- `resolve_wild_shape(intent, world_state, next_event_id, timestamp)` → `(List[Event], WorldState)`
- `resolve_revert_form(intent, world_state, next_event_id, timestamp)` → `(List[Event], WorldState)`

---

## Assumptions to Validate

1. `resolve_smite_evil` is already in scope via `from aidm.core.smite_evil_resolver import ...` — use lazy import (same pattern as other resolvers in the elif chain)
2. `resolve_bardic_music` returns `(events, world_state)` — confirmed by PM source read
3. `validate_rage` is the correct pre-check before `activate_rage` — confirmed (returns error string or None)
4. No additional state is needed at the top of `execute_turn` for these intents (no turn-start cleanup for these features — rage tick and bardic tick already handled at turn-end)

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_barbarian_rage.py tests/test_engine_gate_cp24.py -x -q
```
Green on existing gates before touching play_loop.py.

After implementation:
```bash
python -m pytest tests/test_engine_play_loop_routing_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```
Gate passes at 10/10. No regressions.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/play_loop.py` — 5 elif routing branches inserted
- [ ] `tests/test_engine_play_loop_routing_gate.py` — 10/10

**Gate:** ENGINE-PLAY-LOOP-ROUTING 10/10
**Regression bar:** No new failures. Existing suite ~7,602 passing.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-PLAY-LOOP-ROUTING-001.md` on completion.

**Three-pass format:**

**Pass 1 — Full context dump:**
- Per-file breakdown: every file touched, functions added/modified, line counts
- Key findings: anything discovered during implementation that wasn't in the WO
- Open findings table: any new gaps (ID, severity, description)

**Pass 2 — PM summary (≤100 words):**
- Gate result, regression result, any open findings registered

**Pass 3 — Retrospective:**
- Drift caught (places where you almost used the wrong pattern)
- Pattern notes (anything a future WO author should know)
- Recommendations

Missing debrief or missing Pass 3 Radar = REJECT.

---

## Audio Cue

After filing the debrief:
```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
