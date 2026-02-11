# Intent Lifecycle Contract
## M1 Intent Object Specification

**Document ID:** INTENT-001
**Version:** 1.0
**Date:** 2026-02-09
**Status:** CANONICAL (M1)
**Reference:** VICP-001 (Voice Intent & Clarification Protocol)

---

## 1. PURPOSE

This document defines the **Intent Object** and its lifecycle for M1.

An Intent represents a player's declared action before mechanical resolution.

---

## 2. INTENT STATUS LIFECYCLE

```
┌──────────┐     ┌─────────────┐     ┌───────────┐     ┌──────────┐
│ PENDING  │────→│ CLARIFYING  │────→│ CONFIRMED │────→│ RESOLVED │
└──────────┘     └─────────────┘     └───────────┘     └──────────┘
     │                 │                   │                │
     │  Raw input      │  Missing fields   │  Frozen for    │  Engine
     │  received       │  need answers     │  resolution    │  processed
     │                 │                   │                │
     │                 ↓                   │                │
     │           ┌──────────┐              │                │
     │           │ RETRACTED│              │                │
     │           └──────────┘              │                │
     │                 ↑                   │                │
     └─────────────────┘                   │                │
           (player cancels)                │                │
                                           │                │
                                    IMMUTABLE BOUNDARY ─────┘
```

---

## 3. STATUS DEFINITIONS

### 3.1 PENDING

- Intent created from raw input
- Not yet validated
- May transition to CLARIFYING or CONFIRMED

### 3.2 CLARIFYING

- Intent has missing required fields
- Waiting for player response
- May transition to CONFIRMED or RETRACTED
- **Player may retract**

### 3.3 CONFIRMED

- All required fields populated
- **FROZEN** — no further modifications
- Ready for engine resolution
- **Player may NOT retract**

### 3.4 RESOLVED

- Engine has processed the intent
- EngineResult is attached
- Terminal state

### 3.5 RETRACTED

- Player cancelled before confirmation
- No mechanical effect
- Logged for debugging only

---

## 4. INTENT OBJECT SCHEMA

### 4.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `intent_id` | str (UUID) | Unique identifier |
| `actor_id` | str | Entity performing the action |
| `action_type` | ActionType | Category of action |
| `status` | IntentStatus | Current lifecycle state |
| `source_text` | str | Original player input |
| `created_at` | datetime | When intent was created |
| `updated_at` | datetime | Last modification time |

### 4.2 Optional Fields (Context-Dependent)

| Field | Type | Description |
|-------|------|-------------|
| `target_id` | str | Target entity (if applicable) |
| `target_location` | Location | Target position (if applicable) |
| `method` | str | Weapon, spell, ability used |
| `parameters` | dict | Additional action-specific data |
| `declared_goal` | str | Narrative intent (optional) |

### 4.3 Resolution Fields (Set by Engine)

| Field | Type | Description |
|-------|------|-------------|
| `result_id` | str | Reference to EngineResult |
| `resolved_at` | datetime | When resolution completed |

---

## 5. ACTION TYPES (M1 SCOPE)

For M1, the following action types are supported:

| ActionType | Description | Required Fields |
|------------|-------------|-----------------|
| `ATTACK` | Melee or ranged attack | target_id, method |
| `MOVE` | Movement to location | target_location |
| `USE_ABILITY` | Use class/racial ability | method, parameters |
| `END_TURN` | End current turn | (none) |

Additional action types will be added in future milestones.

---

## 6. TRANSITION RULES

### 6.1 PENDING → CLARIFYING

**Trigger:** Required fields are missing

```python
if not intent.has_required_fields():
    intent.status = IntentStatus.CLARIFYING
```

### 6.2 PENDING → CONFIRMED

**Trigger:** All required fields present and valid

```python
if intent.has_required_fields() and intent.is_valid():
    intent.status = IntentStatus.CONFIRMED
    intent.freeze()  # IMMUTABLE FROM THIS POINT
```

### 6.3 CLARIFYING → CONFIRMED

**Trigger:** Player provides missing information

```python
intent.update_fields(player_response)
if intent.has_required_fields() and intent.is_valid():
    intent.status = IntentStatus.CONFIRMED
    intent.freeze()
```

### 6.4 CLARIFYING → RETRACTED

**Trigger:** Player cancels or timeout

```python
if player_cancels or timeout_expired:
    intent.status = IntentStatus.RETRACTED
```

### 6.5 CONFIRMED → RESOLVED

**Trigger:** Engine completes resolution (ENGINE ONLY)

```python
# ONLY the engine may perform this transition
result = engine.resolve(intent, state)
intent.result_id = result.result_id
intent.status = IntentStatus.RESOLVED
```

---

## 7. IMMUTABILITY RULES

### 7.1 Before CONFIRMED

- Fields may be modified
- Status may change
- Intent may be retracted

### 7.2 After CONFIRMED

- **NO FIELDS MAY BE MODIFIED**
- Status may only transition to RESOLVED
- Intent cannot be retracted
- Any attempt to modify raises error

```python
class Intent:
    def freeze(self):
        self._frozen = True

    def __setattr__(self, name, value):
        if getattr(self, '_frozen', False) and name != 'status':
            if name == 'status' and value != IntentStatus.RESOLVED:
                raise IntentFrozenError("Cannot modify frozen intent")
            elif name != 'status' and name != 'result_id' and name != 'resolved_at':
                raise IntentFrozenError("Cannot modify frozen intent")
        super().__setattr__(name, value)
```

---

## 8. LOGGING REQUIREMENTS

### 8.1 All Intents Logged

Every intent must be logged regardless of final status:

- CONFIRMED/RESOLVED: Authoritative for replay
- RETRACTED: Debug information only
- CLARIFYING: Historical record of clarification

### 8.2 Log Entry Format

```python
{
    "type": "intent",
    "intent_id": "...",
    "status": "CONFIRMED",
    "actor_id": "fighter_1",
    "action_type": "ATTACK",
    "target_id": "goblin_3",
    "method": "longsword",
    "source_text": "I attack the goblin with my sword",
    "created_at": "2026-02-09T12:00:00Z",
    "confirmed_at": "2026-02-09T12:00:01Z"
}
```

---

## 9. REPLAY BEHAVIOR

During replay:

1. Read logged intent (already CONFIRMED)
2. Skip intent extraction
3. Skip clarification
4. Pass directly to engine
5. Verify result matches logged result

```python
def replay_intent(logged_intent: Intent, state: WorldState) -> EngineResult:
    assert logged_intent.status == IntentStatus.CONFIRMED
    result = engine.resolve(logged_intent, state)
    # Result must be deterministic
    return result
```

---

## 10. CLARIFICATION QUESTIONS

When intent status is CLARIFYING, the system must ask the player for missing information.

### 10.1 Question Format

Questions must be:
- Phrased naturally (as a DM would ask)
- Specific about what's missing
- Not leading toward any particular answer

### 10.2 Timeout Behavior

If player does not respond within configured timeout:
- Intent transitions to RETRACTED
- System announces: "I didn't catch that — let me know when you're ready."
- No partial action is resolved

---

## END OF INTENT LIFECYCLE CONTRACT
