# WO-ENGINE-WITHDRAW-DELAY-001 — Withdraw Action + Delay Action (PHB p.144/160)

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-WITHDRAW-DELAY (new gate, defined below)

---

## 1. Target Lock

PHB p.144 and p.160 define two special combat actions currently absent from the engine:

**Withdraw (PHB p.144):**
- Full-round action (consumes both standard + move slots)
- Actor moves up to their speed away from combat
- The first square departed does NOT provoke an AoO — this is the defining mechanical property of Withdraw vs. a double move
- Subsequent squares departed during the withdrawal DO still provoke AoOs normally
- The actor cannot attack during the same round (full-round action precludes standard action attacks)
- Double move is NOT Withdraw — a double move does not suppress the first-square AoO

**Delay (PHB p.160):**
- Actor voluntarily chooses to act later in the initiative order
- They declare a new initiative count (must be lower than their current count)
- Their position in `active_combat["initiative_order"]` is updated permanently for the remainder of the encounter
- If multiple actors delay to the same count, their original relative order is preserved
- Delaying to 0 or below is legal — actor acts last in the round but still within it
- Delay is not a standard action per se: it replaces the actor's entire turn with a re-queue

**Done means:** `WithdrawIntent` + `DelayIntent` + `withdraw_delay_resolver.py` + `withdrew_actors` set in `active_combat` + AoO suppression on first-square departure in `aoo.py` + initiative reordering in `resolve_delay()` + action economy registration + `withdraw_declared` / `delay_declared` events + Gate ENGINE-WITHDRAW-DELAY 10/10.

---

## 2. PHB Rules

> **Withdraw (PHB p.144):** Using a withdraw action, you can move up to double your speed. The first square you move out of is not considered threatened by any opponent you can see, and therefore doesn't trigger attacks of opportunity.

> **Delay (PHB p.160):** By choosing to delay, you take no action and then act normally on whatever initiative count you decide to act on. You can act on any initiative count lower than the one you rolled. You don't have to declare when you delay — you just wait. When you do act, your initiative count drops to whatever count you acted on and stays there for the rest of the encounter.

Key rulings:
- Withdraw's first-square AoO suppression applies only to enemies the withdrawing actor **can see** — for this WO, all enemies are visible (no concealment/blindness system yet); suppress unconditionally.
- Delay's new initiative is **permanent** for the encounter, not just one round.
- Delay to the same count as a non-delayed actor: the non-delayed actor acts first (PHB p.160 "original order preserved"). This means the delaying actor is inserted **after** any actors already at that count in `initiative_order`.
- Withdraw does not grant a free 5-foot step — the actor moves up to their speed as part of the full-round action.
- A character who withdraws cannot also 5-foot step in the same turn (full-round action precludes it).

**Scope for this WO:**
- `WithdrawIntent` — direction hint string, AoO suppression on first square departure
- `DelayIntent` — new_initiative integer, permanent reorder of `initiative_order`
- `withdrew_actors` tracking set in `active_combat`, cleared at turn end
- AoO suppression hook in `aoo.py` `check_aoo_triggers()`: skip trigger generation if actor is in `withdrew_actors` AND the intent is their first square departure
- Full-round action budget consumed by Withdraw
- Delay does not consume an action slot — it re-queues the actor; handled outside the normal budget path

---

## 3. New Entity Fields

None. State is tracked at the `active_combat` level, not the entity level.

`active_combat["withdrew_actors"]` — `list[str]` (serialized as list; treated as set at runtime). Stores actor_ids who have declared Withdraw this turn. Cleared at turn end for each actor in the set.

No `EF` constant is added. The `WITHDREW_THIS_TURN` sentinel described in the brief is tracked via `active_combat["withdrew_actors"]` to avoid polluting entity fields with transient per-turn state.

---

## 4. Implementation Spec

### 4.1 New Intents (intents.py)

```python
@dataclass
class WithdrawIntent:
    """Intent to perform the Withdraw action this round.

    PHB p.144: Full-round action. Actor moves up to speed away from combat.
    The first square departed does not provoke an AoO. Subsequent squares
    provoke normally. Cannot attack in the same round.

    WO-ENGINE-WITHDRAW-DELAY-001
    """
    actor_id: str
    direction: str  # Narrative hint: "away", "north", "toward exit", etc.
                    # Actual movement adjudicated narratively; only the
                    # AoO-suppression on first square has mechanical effect.

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "withdraw", "actor_id": self.actor_id, "direction": self.direction}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WithdrawIntent":
        return cls(actor_id=data["actor_id"], direction=data.get("direction", "away"))


@dataclass
class DelayIntent:
    """Intent to delay and act at a lower initiative count.

    PHB p.160: Actor chooses to act later. New initiative count must be
    strictly less than their current count. The new count is permanent
    for the remainder of the encounter.

    WO-ENGINE-WITHDRAW-DELAY-001
    """
    actor_id: str
    new_initiative: int  # Must be < actor's current initiative count

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "delay", "actor_id": self.actor_id, "new_initiative": self.new_initiative}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DelayIntent":
        return cls(actor_id=data["actor_id"], new_initiative=int(data["new_initiative"]))
```

Add both to the Intent union type and `parse_intent()` dispatcher in `intents.py`.

### 4.2 New Resolver: aidm/core/withdraw_delay_resolver.py

```python
"""Withdraw and Delay action resolvers.

Implements PHB p.144 (Withdraw) and PHB p.160 (Delay).

WO-ENGINE-WITHDRAW-DELAY-001
"""

from typing import List
from aidm.core.event_log import Event
from aidm.core.state import WorldState


def resolve_withdraw(
    world_state: WorldState,
    actor_id: str,
    direction: str,
    events: List[Event],
    next_event_id: int,
    timestamp: float,
) -> tuple[WorldState, int]:
    """Declare a Withdraw action for actor_id.

    Marks the actor in active_combat["withdrew_actors"] so that aoo.py
    can suppress the first-square departure AoO. Emits withdraw_declared.
    Full-round action slot is consumed by action_economy (registered in
    _build_action_types); this resolver does not touch the budget directly.

    PHB p.144: First square departed is AoO-free; subsequent squares provoke.

    Returns:
        Updated WorldState and next available event_id.
    """
    # Add actor to withdrew_actors set in active_combat
    new_active_combat = dict(world_state.active_combat)
    withdrew = list(new_active_combat.get("withdrew_actors", []))
    if actor_id not in withdrew:
        withdrew.append(actor_id)
    new_active_combat["withdrew_actors"] = withdrew

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_active_combat,
    )

    events.append(Event(
        event_id=next_event_id,
        event_type="withdraw_declared",
        timestamp=timestamp,
        payload={
            "actor_id": actor_id,
            "direction": direction,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 144}],
    ))

    return world_state, next_event_id + 1


def resolve_delay(
    world_state: WorldState,
    actor_id: str,
    new_initiative: int,
    events: List[Event],
    next_event_id: int,
    timestamp: float,
) -> tuple[WorldState, int]:
    """Re-queue actor_id at new_initiative in the initiative order.

    Guards: new_initiative must be strictly less than the actor's current
    position in initiative_order (earlier index = higher initiative). Emits
    delay_declared with old and new initiative values.

    PHB p.160: If new_initiative ties with an existing non-delayed actor,
    the delaying actor is inserted AFTER them (original order preserved).

    Returns:
        Updated WorldState and next available event_id.
    """
    new_active_combat = dict(world_state.active_combat)
    initiative_order = list(new_active_combat.get("initiative_order", []))
    initiative_scores = dict(new_active_combat.get("initiative_scores", {}))

    # Guard: actor must be in initiative order
    if actor_id not in initiative_order:
        # Emit nothing; caller should handle as no-op
        return world_state, next_event_id

    old_initiative = initiative_scores.get(actor_id, 0)

    # Guard: new_initiative must be < current (cannot delay upward)
    if new_initiative >= old_initiative:
        events.append(Event(
            event_id=next_event_id,
            event_type="delay_invalid",
            timestamp=timestamp,
            payload={
                "actor_id": actor_id,
                "old_initiative": old_initiative,
                "new_initiative": new_initiative,
                "reason": "new_initiative must be less than current initiative",
            },
        ))
        return world_state, next_event_id + 1

    # Remove actor from current position
    initiative_order.remove(actor_id)

    # Update score
    initiative_scores[actor_id] = new_initiative

    # Insert after all actors whose score >= new_initiative (ties: original
    # order preserved — non-delayed actors at the same count act first).
    insert_at = len(initiative_order)  # default: end
    for i, eid in enumerate(initiative_order):
        if initiative_scores.get(eid, 0) < new_initiative:
            insert_at = i
            break

    initiative_order.insert(insert_at, actor_id)

    new_active_combat["initiative_order"] = initiative_order
    new_active_combat["initiative_scores"] = initiative_scores

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_active_combat,
    )

    events.append(Event(
        event_id=next_event_id,
        event_type="delay_declared",
        timestamp=timestamp,
        payload={
            "actor_id": actor_id,
            "old_initiative": old_initiative,
            "new_initiative": new_initiative,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 160}],
    ))

    return world_state, next_event_id + 1
```

### 4.3 `play_loop.py` — Intent Routing

**A. WithdrawIntent routing** (alongside other full-round intents such as ChargeIntent):

```python
elif isinstance(combat_intent, WithdrawIntent):
    world_state, current_event_id = resolve_withdraw(
        world_state=world_state,
        actor_id=combat_intent.actor_id,
        direction=combat_intent.direction,
        events=events,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.05,
    )
    narration = "withdraw_declared"
```

**B. DelayIntent routing** (before standard intent dispatch — Delay skips the normal action budget):

```python
elif isinstance(combat_intent, DelayIntent):
    world_state, current_event_id = resolve_delay(
        world_state=world_state,
        actor_id=combat_intent.actor_id,
        new_initiative=combat_intent.new_initiative,
        events=events,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.05,
    )
    narration = "delay_declared"
    # Delay ends the actor's turn immediately — fall through to turn_end
```

**C. Turn-end clearance of `withdrew_actors`** (alongside existing per-turn cleanup such as `charge_ac` expiry):

```python
# WO-ENGINE-WITHDRAW-DELAY-001: Clear withdrew_actors entry at turn end
_active = dict(world_state.active_combat)
_withdrew = list(_active.get("withdrew_actors", []))
if turn_ctx.actor_id in _withdrew:
    _withdrew.remove(turn_ctx.actor_id)
    _active["withdrew_actors"] = _withdrew
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=_active,
    )
```

This block runs at turn-end for every actor (no event emitted — the clearance is silent housekeeping).

### 4.4 `aoo.py` — First-Square AoO Suppression for Withdraw

In `check_aoo_triggers()`, add a suppression guard immediately after the `StepMoveIntent` branch identifies `provoking_action = "movement_out"`:

```python
if isinstance(intent, StepMoveIntent):
    provoking_action = "movement_out"
    from_pos = intent.from_pos
    to_pos = intent.to_pos
    provoker_id = intent.actor_id

    # WO-ENGINE-WITHDRAW-DELAY-001: Suppress first-square AoO for withdrawing actors.
    # PHB p.144: The first square left during a Withdraw does not provoke AoO.
    # "First square" is inferred by membership in withdrew_actors — the resolver
    # adds the actor on declaration; aoo.py sees it on the first movement step only
    # (the actor is removed at turn end, not after each step).
    active_combat = world_state.active_combat
    if active_combat is not None:
        withdrew_actors = set(active_combat.get("withdrew_actors", []))
        if provoker_id in withdrew_actors:
            # First departure is suppressed. Mark first square as consumed by
            # removing actor from the set so subsequent steps provoke normally.
            new_active_combat = dict(active_combat)
            new_withdrew = list(withdrew_actors)
            new_withdrew.remove(provoker_id)
            new_active_combat["withdrew_actors"] = new_withdrew
            # NOTE: world_state mutation here is local to the trigger-check call;
            # the updated active_combat propagates through the returned trigger list
            # being empty for this step. Caller must update world_state accordingly.
            return []  # No AoO triggers for first withdrawal square
```

**Implementation note on the suppression mechanism:** The `withdrew_actors` set uses presence-then-removal semantics: actor is added on `WithdrawIntent` declaration; on the first `StepMoveIntent` AoO check, their entry is consumed (removed from the set) and `[]` is returned — no AoO. On subsequent `StepMoveIntent` calls that same turn, the actor is no longer in the set, so AoOs fire normally. The set is fully cleared at turn end regardless.

Because `check_aoo_triggers()` does not currently mutate `world_state`, the suppression path must either (a) mutate through a passed-in mutable dict reference, or (b) have the caller pass a mutable `active_combat` reference. The simplest approach: return a sentinel alongside triggers (e.g. a `withdraw_first_square_consumed: bool` flag) and have the caller update `world_state`. Implementor to choose the cleanest pattern consistent with the existing code. The functional requirement is: first step → no AoO + remove from set; subsequent steps → AoO fires.

### 4.5 `action_economy.py` — Register Intent Types

Add to `_build_action_types()` in `action_economy.py`:

```python
_try_add(mapping, "aidm.schemas.intents", "WithdrawIntent", "full_round")
# DelayIntent: NOT registered — it replaces the turn rather than consuming a slot
# within the turn. play_loop routes it before the action economy check.
```

`WithdrawIntent` as `"full_round"` means `ActionBudget.consume("full_round")` also marks `standard_used = True` and `move_used = True` (existing `consume()` behavior — no change needed).

`DelayIntent` is intentionally excluded from `ACTION_TYPES`. It does not consume an action slot — it re-queues the actor. The play_loop handles it by routing to `resolve_delay()` and immediately emitting `turn_end`, bypassing the action economy check entirely.

### 4.6 `active_combat` Initialization

In `combat_controller.py`, where `active_combat` is built for a new combat, add:

```python
"withdrew_actors": [],  # WO-ENGINE-WITHDRAW-DELAY-001: actors who withdrew this turn
```

This ensures the key exists from combat start and no `get()` fallback is needed at runtime.

### 4.7 New Event Types

| Event | When | Key Payload Fields |
|-------|------|--------------------|
| `withdraw_declared` | `WithdrawIntent` processed by `resolve_withdraw()` | actor_id, direction |
| `delay_declared` | `DelayIntent` processed by `resolve_delay()` | actor_id, old_initiative, new_initiative |
| `delay_invalid` | `DelayIntent` where `new_initiative >= old_initiative` | actor_id, old_initiative, new_initiative, reason |

---

## 5. Regression Risk

- **LOW for new intents:** No existing tests reference WithdrawIntent or DelayIntent.
- **LOW for `withdrew_actors` init:** Added to `active_combat` at combat start with `[]`; all existing `active_combat.get("withdrew_actors", [])` calls are no-ops when the list is empty.
- **LOW for aoo.py guard:** Guard is behind a membership check (`provoker_id in withdrew_actors`). When `withdrew_actors` is empty (all existing tests), the check is False and code falls through unchanged. No AoO behavior changes for non-withdrawing actors.
- **LOW for action economy:** `WithdrawIntent` is registered as `full_round` — consistent with ChargeIntent and FullAttackIntent patterns. `DelayIntent` is excluded; the `free` fallback in `get_action_type()` would apply if it were ever passed (it will not be in the normal routing path).
- **MEDIUM for `resolve_delay()` initiative reorder:** Mutates `active_combat["initiative_order"]` and `initiative_scores`. Risk is confined to the Delay path only. Requires `initiative_scores` to be present in `active_combat` (see note below).
- **Gold masters:** No existing gold-master scenario uses WithdrawIntent or DelayIntent. No events emitted, no `withdrew_actors` membership, no AoO suppression fires. Gold master drift: none expected.

**`initiative_scores` note:** The Delay resolver depends on `active_combat["initiative_scores"]` to know each actor's numeric initiative value (needed to validate `new_initiative < old_initiative` and to sort after reorder). If this dict is not yet populated in `active_combat`, the implementor must either (a) add it to `combat_controller.py` alongside `initiative_order` at combat start, populated from the `initiative_rolls` list returned by `roll_initiative_for_all_actors()`, or (b) compute old initiative from `initiative_order` position as a tie-breaking proxy. Option (a) is strongly preferred for correctness.

---

## 6. What This WO Does NOT Do

- No narrative movement resolution — direction is a hint string only; the engine does not move grid tokens during Withdraw (no Position updates). Token movement is a UI concern.
- No "enemies you can see" filter on Withdraw AoO suppression — all enemies treated as visible (concealment/blindness system deferred).
- No free Withdraw combined with 5-foot step — full-round action precludes it; action economy already handles this.
- No Delay combined with Readied action interaction (deferred).
- No Delay below round 1 (initiative 0 or negative) special handling beyond inserting at end of order — PHB says "act last", which is what insertion at the tail achieves.
- No "re-enter initiative" after Delay for actors who delayed past the end of the round — treated as acting at their new count next round in the reordered list.
- No Combat Reflexes multi-AoO interaction with Withdraw (Combat Reflexes deferred).
- No Withdraw from a grapple — Withdraw requires free movement; grapple escape requires a separate action (GrappleEscapeIntent).

---

## 7. Gate Spec

**Gate name:** `ENGINE-WITHDRAW-DELAY`
**Test file:** `tests/test_engine_gate_withdraw_delay.py` (new file)

| # | Test | Check |
|---|------|-------|
| WD-01 | `WithdrawIntent` class exists in `intents.py` | `from aidm.schemas.intents import WithdrawIntent` succeeds; dataclass has `actor_id` and `direction` fields |
| WD-02 | `DelayIntent` class exists in `intents.py` | `from aidm.schemas.intents import DelayIntent` succeeds; dataclass has `actor_id` and `new_initiative` fields |
| WD-03 | `resolve_withdraw()` emits `withdraw_declared` event | Call `resolve_withdraw()`; assert one event with `event_type == "withdraw_declared"` and correct `actor_id`, `direction` payload |
| WD-04 | `resolve_delay()` emits `delay_declared` with old + new initiative values | Call `resolve_delay()` with valid lower `new_initiative`; assert `delay_declared` event with `old_initiative` and `new_initiative` in payload |
| WD-05 | `resolve_delay()` updates `initiative_order` in `world_state` | After `resolve_delay()`, assert actor appears at correct index in `world_state.active_combat["initiative_order"]` reflecting the new lower count |
| WD-06 | Delay with `new_initiative >= current` is rejected | Call `resolve_delay()` with `new_initiative` equal to or greater than actor's current score; assert `delay_invalid` event emitted; `initiative_order` unchanged |
| WD-07 | Withdraw consumes full-round action slot | After `WithdrawIntent` processed, assert `ActionBudget.full_round_used == True` and `standard_used == True` and `move_used == True` |
| WD-08 | `withdrew_actors` cleared at turn end | After `withdraw_declared`, simulate turn-end pass; assert `actor_id` no longer in `active_combat["withdrew_actors"]` |
| WD-09 | AoO suppressed on withdrawing actor's first square departure | Put actor in `withdrew_actors`; call `check_aoo_triggers()` with a `StepMoveIntent` from that actor; assert empty trigger list returned AND actor removed from `withdrew_actors` |
| WD-10 | Delay to same count as another actor inserts after that actor | Two actors A (init 15) and B (init 10) in order `[A, B]`; A delays to 10; assert new order is `[B, A]` (B acts before A at the tied count) |

**Test count target:** ENGINE-WITHDRAW-DELAY 10/10.

---

## 8. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# After implementation
python -m pytest tests/test_engine_gate_withdraw_delay.py -v
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
