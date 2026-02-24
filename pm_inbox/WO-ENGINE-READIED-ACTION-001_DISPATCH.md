# WO-ENGINE-READIED-ACTION-001 — Readied Action (PHB p.160)

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-READIED-ACTION (new gate, defined below)

---

## 1. Target Lock

PHB p.160: A character can ready a standard action to trigger when a specified condition occurs before their next turn. Common uses: interrupt a spellcaster, attack when an enemy enters range, shoot when a door opens.

Mechanically:
- **Ready** is a standard action (the "readied" state costs the standard action slot)
- The character specifies a **trigger** (a condition in natural language or structured form) and an **action** (attack, spell, move)
- When the trigger fires, the readied action resolves **before** the triggering actor completes their action (interrupts)
- If the trigger never fires, the readied action is lost at the start of the character's next turn
- Cannot ready a full-round action (only a standard action)

**Done means:** `ReadyActionIntent` + `ReadiedActionQueue` in `WorldState.active_combat` + trigger evaluation in `execute_turn()` + `readied_action_triggered` / `readied_action_expired` events + Gate ENGINE-READIED-ACTION 10/10.

---

## 2. PHB Rule (p.160)

> "Readying an Action: You can ready a standard action by choosing to delay the action until some triggering event. Then, any time before your next action, you may take the readied action in response to that event. In effect, you are delaying your action until after the triggering event occurs. Your initiative result changes. For the rest of the encounter, your initiative result is the number before the trigger occurred."

Key rulings:
- Trigger fires **between** the trigger event and its resolution — e.g., readied "attack when enemy casts" fires after the enemy commits to casting but before the spell resolves
- If the readied character uses their action reactively, their **initiative drops** to just after the triggering actor's count
- Readied action against a spellcaster: if the attack hits and deals damage, caster must make concentration check (already implemented)
- Cannot ready a move action or full-round action — only standard action

**Scope for this WO:**
- Ready a melee or ranged attack (`ReadyAttackTrigger`)
- Ready a spell cast (`ReadySpellTrigger`)
- Trigger condition: enemy **starts casting**, enemy **moves into range**, or enemy **enters a specified square**
- Initiative drop on trigger fire: deferred (complex to model, low-value for DM-run game)
- Trigger evaluation: fire when the trigger condition is matched during any other actor's `execute_turn()`

---

## 3. New Entity Fields

None. Readied actions are stored in `WorldState.active_combat["readied_actions"]`, not on entities.

---

## 4. Implementation Spec

### 4.1 New Intent: `ReadyActionIntent` (intents.py)

```python
@dataclass
class ReadyActionIntent:
    """Intent to ready a standard action for a trigger condition.

    PHB p.160: Ready is a standard action. The actor specifies a trigger
    and an action to execute when the trigger fires.

    WO-ENGINE-READIED-ACTION-001
    """

    actor_id: str
    """Entity ID of the actor readying the action."""

    trigger_type: Literal["enemy_casts", "enemy_enters_range", "enemy_enters_square"]
    """What condition fires the readied action."""

    trigger_target_id: Optional[str] = None
    """For enemy_casts/enemy_enters_range: specific enemy to watch. None = any enemy."""

    trigger_square: Optional[dict] = None
    """For enemy_enters_square: {x: int, y: int} of the watched square."""

    trigger_range_ft: float = 5.0
    """For enemy_enters_range: fire when enemy comes within this many feet."""

    readied_intent: Optional[dict] = None
    """Serialized intent to execute when trigger fires.
    Must be a serialized AttackIntent or CastSpellIntent dict.
    None = raise ValueError (fail-closed)."""

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data) -> "ReadyActionIntent": ...
```

Add to Intent union and `parse_intent()` dispatcher.

### 4.2 `ReadiedActionQueue` in `active_combat`

Add to `active_combat` dict when first readied action is registered:

```python
# active_combat["readied_actions"] = list of dicts:
{
    "actor_id": str,
    "trigger_type": str,          # "enemy_casts" | "enemy_enters_range" | "enemy_enters_square"
    "trigger_target_id": str | None,
    "trigger_square": dict | None, # {x, y}
    "trigger_range_ft": float,
    "readied_intent": dict,        # serialized intent
    "registered_at_event_id": int
}
```

### 4.3 `readied_action_resolver.py` (new file)

```python
# aidm/core/readied_action_resolver.py

def register_readied_action(
    world_state: WorldState,
    intent: ReadyActionIntent,
    event_id: int
) -> WorldState:
    """Add readied action to active_combat queue. Fail-closed on invalid intent."""

def check_readied_triggers(
    world_state: WorldState,
    current_actor_id: str,
    trigger_event_type: str,  # "cast_spell" | "move" | "step_move"
    event_payload: dict,
    rng: RNGProvider,
    current_event_id: int,
) -> Tuple[WorldState, List[dict], int]:
    """Check all readied actions for trigger conditions.

    Called from execute_turn() at the START of each actor's action resolution,
    before the action resolves. Returns (updated_world_state, new_events, next_event_id).

    Trigger evaluation:
    - enemy_casts: fires when current_actor_id is an enemy of the readying actor
      AND trigger_event_type is "cast_spell" (the intent type being resolved)
    - enemy_enters_range: fires when current_actor_id is an enemy AND their
      current position is within trigger_range_ft of the readying actor's position
    - enemy_enters_square: fires when current_actor_id is an enemy AND their
      destination position matches trigger_square {x, y}

    When trigger fires:
    1. Execute the readied_intent (deserialize + route through resolve_attack or resolve_spell_cast)
    2. Emit readied_action_triggered event
    3. Remove the readied action from queue (consumed)
    4. Continue with the original triggering actor's action

    When actor's own turn starts and readied action is still in queue:
    1. Emit readied_action_expired event
    2. Remove from queue (readied_intent is lost)
    """

def expire_readied_actions(
    world_state: WorldState,
    actor_id: str,
    current_event_id: int
) -> Tuple[WorldState, List[dict], int]:
    """Called at start of actor's own turn — expire any pending readied actions for them."""
```

### 4.4 `execute_turn()` wiring (play_loop.py)

Two insertion points:

**A. At turn start (after `turn_start` event, before intent routing):**
```python
# Expire any readied actions for this actor (their previous ready is consumed)
world_state, expire_events, current_event_id = expire_readied_actions(
    world_state, turn_ctx.actor_id, current_event_id
)
events.extend(expire_events)
```

**B. Before each intent resolves (before the `isinstance` dispatch chain):**
```python
# Check if this intent fires any readied actions
world_state, readied_events, current_event_id = check_readied_triggers(
    world_state,
    current_actor_id=turn_ctx.actor_id,
    trigger_event_type=type(combat_intent).__name__,
    event_payload=combat_intent.to_dict() if hasattr(combat_intent, 'to_dict') else {},
    rng=rng,
    current_event_id=current_event_id,
)
events.extend(readied_events)
```

**C. When `ReadyActionIntent` is routed:**
```python
elif isinstance(combat_intent, ReadyActionIntent):
    world_state = register_readied_action(world_state, combat_intent, current_event_id)
    events.append({
        "event_id": current_event_id,
        "event_type": "readied_action_registered",
        "payload": {
            "actor_id": combat_intent.actor_id,
            "trigger_type": combat_intent.trigger_type,
            "trigger_target_id": combat_intent.trigger_target_id,
        }
    })
    current_event_id += 1
```

### 4.5 Action Economy

Add to `_build_action_types()` in `action_economy.py`:
```python
_try_add(mapping, "aidm.schemas.intents", "ReadyActionIntent", "standard")
```

### 4.6 New Event Types

| Event | When | Key Payload Fields |
|-------|------|--------------------|
| `readied_action_registered` | `ReadyActionIntent` processed | actor_id, trigger_type, trigger_target_id |
| `readied_action_triggered` | Trigger condition fires | actor_id, trigger_type, triggering_actor_id, resolved_intent_type |
| `readied_action_expired` | Actor's turn starts with unused ready | actor_id, trigger_type |

---

## 5. Regression Risk

- **LOW for new code path:** Readied action queue only activates when `ReadyActionIntent` is emitted. No existing tests use it.
- **LOW for trigger check:** `check_readied_triggers()` is called at top of `execute_turn()` but is a no-op when `active_combat["readied_actions"]` is empty or absent (existing flows).
- **MEDIUM for `expire_readied_actions()`:** Called at turn start for every actor. Guard: check `active_combat` is not None and `readied_actions` list is non-empty before iterating.
- Gold masters: may need regeneration if turn-start event sequence changes. Minimize by only emitting `readied_action_expired` when there is actually an entry to expire (never emit if queue is empty).

---

## 6. What This WO Does NOT Do

- No initiative count drop on trigger fire (deferred — complex, low DM-run value)
- No "delay action" (separate from ready — deferred)
- No trigger type "ally takes damage" or "any creature moves" (too broad — deferred)
- No readying a move action or full-round action
- No persistent readied actions across rounds (one round only per PHB)
- No trigger conditions based on skill checks (Spot/Listen)
- No ranged readied attack beyond first trigger (one trigger = one attack)

---

## 7. Gate Spec

**Gate name:** `ENGINE-READIED-ACTION`
**Test file:** `tests/test_engine_gate_readied_action.py` (new file)

| # | Test | Check |
|---|------|-------|
| RA-01 | ReadyActionIntent registers in active_combat queue | `readied_action_registered` event emitted; queue has 1 entry |
| RA-02 | Readied attack fires when enemy casts — trigger_type=enemy_casts | Enemy starts casting; readied attack resolves before spell; `readied_action_triggered` emitted |
| RA-03 | Readied attack damage forces concentration check | Hit resolves; `concentration_check_required` event in output |
| RA-04 | Readied attack fires when enemy enters range — trigger_type=enemy_enters_range | Enemy moves into 5ft; readied attack fires; `readied_action_triggered` emitted |
| RA-05 | Readied action does NOT fire if trigger condition not met | Enemy moves but stays out of range; no trigger; no `readied_action_triggered` |
| RA-06 | Readied action expires at actor's next turn start | Actor's next turn: `readied_action_expired` emitted; queue cleared |
| RA-07 | ReadyActionIntent costs standard action slot | Action budget: `standard` used; subsequent standard action → ACTION_DENIED |
| RA-08 | Readied action consumed on trigger — not re-used | Trigger fires once; second trigger from same actor does not re-fire |
| RA-09 | enemy_enters_square trigger — fires on position match | Enemy moves to watched square; trigger fires |
| RA-10 | Zero regressions suite-wide | Full suite: no new failures |

**Test count target:** ENGINE-READIED-ACTION 10/10.

---

## 8. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# After implementation
python -m pytest tests/test_engine_gate_readied_action.py -v
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
