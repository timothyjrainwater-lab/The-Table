# Engine Result Contract
## M1 Engine Output Specification

**Document ID:** ENGINE-001
**Version:** 1.0
**Date:** 2026-02-09
**Status:** CANONICAL (M1)
**Reference:** IPC-001 (Inter-Process Communication Contract)

---

## 1. PURPOSE

This document defines the **EngineResult Object** — the authoritative output of
intent resolution for M1.

An EngineResult represents the mechanical outcome of a player's action after
the Engine has processed it.

---

## 2. AUTHORITY RULES (BINDING)

Per IPC-001:

```
RULE: Once the Engine produces an EngineResult, no component may:
  - Modify the result
  - Substitute a different result
  - Reinterpret the result mechanically
  - Prevent the result from being logged
```

The EngineResult is **immutable** from the moment of creation.

---

## 3. ENGINE RESULT STRUCTURE

### 3.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `result_id` | str (UUID) | Unique identifier for this result |
| `intent_id` | str | Reference to the intent that was resolved |
| `status` | EngineResultStatus | Resolution status (SUCCESS/FAILURE/ABORTED) |
| `resolved_at` | datetime | When resolution completed |
| `events` | List[Dict] | Events emitted during resolution |
| `rolls` | List[RollResult] | All dice rolls consumed |
| `state_changes` | List[StateChange] | Atomic state changes |
| `rng_initial_offset` | int | RNG offset at start of resolution |
| `rng_final_offset` | int | RNG offset after all rolls |

### 3.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `narration_token` | str | Token for narrator layer |
| `failure_reason` | str | Reason if status != SUCCESS |
| `metadata` | Dict | Additional resolution data |

---

## 4. STATUS DEFINITIONS

### 4.1 SUCCESS

- Intent was fully resolved
- All mechanical effects computed
- State changes ready to apply

### 4.2 FAILURE

- Intent could not be resolved
- Validation failed (invalid target, missing fields, etc.)
- No mechanical effects occur

### 4.3 ABORTED

- Resolution started but was interrupted
- Example: Actor defeated by Attack of Opportunity
- Partial effects may have occurred

---

## 5. ROLL RESULT STRUCTURE

Each dice roll is captured for replay verification:

```python
@dataclass
class RollResult:
    roll_type: str      # "attack", "damage", "skill", etc.
    dice: str           # "1d20", "2d6+3", etc.
    natural_roll: int   # Raw die result
    modifiers: int      # Sum of all modifiers
    total: int          # natural_roll + modifiers
    rng_offset: int     # Position in RNG stream
    context: Optional[Dict]  # Additional context
```

---

## 6. STATE CHANGE STRUCTURE

Each state change is an atomic update:

```python
@dataclass
class StateChange:
    entity_id: str   # Entity affected
    field: str       # Field that changed
    old_value: Any   # Value before
    new_value: Any   # Value after
```

---

## 7. IMMUTABILITY ENFORCEMENT

### 7.1 Direct Construction

When created directly, EngineResult is frozen in `__post_init__`:

```python
def __post_init__(self):
    object.__setattr__(self, "_frozen", True)

def __setattr__(self, name, value):
    if getattr(self, "_frozen", False):
        raise EngineResultFrozenError(
            f"EngineResult is immutable. Cannot modify '{name}'."
        )
    object.__setattr__(self, name, value)
```

### 7.2 Builder Pattern

For resolution code, use `EngineResultBuilder`:

```python
builder = EngineResultBuilder(intent_id="...", rng_offset=100)

builder.add_event({"type": "attack_roll", "hit": True})
builder.add_roll("attack", "1d20", 18, 7, 25)
builder.add_state_change("goblin_1", "hp", 15, 7)
builder.set_narration_token("attack_hit")

result = builder.build()  # Frozen immediately
```

After `build()`, the builder cannot be modified.

---

## 8. SERIALIZATION FORMAT

### 8.1 JSON Output

```json
{
    "result_id": "550e8400-e29b-41d4-a716-446655440000",
    "intent_id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "success",
    "resolved_at": "2026-02-09T12:00:00Z",
    "events": [
        {"type": "attack_roll", "hit": true, "natural": 18}
    ],
    "rolls": [
        {
            "roll_type": "attack",
            "dice": "1d20",
            "natural_roll": 18,
            "modifiers": 7,
            "total": 25,
            "rng_offset": 100
        }
    ],
    "state_changes": [
        {
            "entity_id": "goblin_1",
            "field": "hp",
            "old_value": 15,
            "new_value": 7
        }
    ],
    "rng_initial_offset": 100,
    "rng_final_offset": 101,
    "narration_token": "attack_hit"
}
```

---

## 9. REPLAY REQUIREMENTS

During replay:

1. Read logged intent (CONFIRMED)
2. Read logged EngineResult
3. Re-resolve intent with same RNG seed
4. **Verify** new result matches logged result:
   - Same status
   - Same rolls (natural values, totals)
   - Same state changes
   - Same rng_final_offset

```python
def verify_replay(logged_result: EngineResult, replay_result: EngineResult) -> bool:
    if logged_result.status != replay_result.status:
        return False
    if logged_result.rng_final_offset != replay_result.rng_final_offset:
        return False
    if len(logged_result.rolls) != len(replay_result.rolls):
        return False
    for logged, replayed in zip(logged_result.rolls, replay_result.rolls):
        if logged.natural_roll != replayed.natural_roll:
            return False
        if logged.total != replayed.total:
            return False
    return True
```

---

## 10. LOGGING REQUIREMENTS

All EngineResults must be logged regardless of status:

- SUCCESS: Authoritative for replay
- FAILURE: Debug information
- ABORTED: Partial resolution record

Log entries should include:
- Full EngineResult (serialized)
- Associated IntentObject reference

---

## 11. IMPLEMENTATION REFERENCE

```
aidm/schemas/engine_result.py

Classes:
  - EngineResultStatus (Enum)
  - RollResult (dataclass)
  - StateChange (dataclass)
  - EngineResult (dataclass, frozen)
  - EngineResultFrozenError (Exception)
  - EngineResultBuilder (mutable builder)
```

---

## END OF ENGINE RESULT CONTRACT
