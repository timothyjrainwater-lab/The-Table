# Inter-Process Communication Contract
## M1 Runtime Authority Boundaries

**Document ID:** IPC-001
**Version:** 1.0
**Date:** 2026-02-09
**Status:** CANONICAL (M1)
**Authority:** Binding for M1 implementation

---

## 1. PURPOSE

This document defines the **runtime communication protocol** for M1,
establishing clear authority boundaries between components.

It answers:
- What data flows between components?
- Who owns what data?
- What cannot be overridden?

---

## 2. RUNTIME FLOW (CANONICAL)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │────→│   INTENT    │────→│   ENGINE    │
│  (Text/Voice)     │   MANAGER   │     │  (Resolver) │
└─────────────┘     └─────────────┘     └─────────────┘
                          │                    │
                          │ Intent             │ Result
                          ↓                    ↓
                    ┌─────────────┐     ┌─────────────┐
                    │  CLARIFIER  │     │  EVENT LOG  │
                    │  (Optional) │     │ (Authoritative)
                    └─────────────┘     └─────────────┘
                                               │
                          ┌────────────────────┤
                          │                    │
                          ↓                    ↓
                    ┌─────────────┐     ┌─────────────┐
                    │  NARRATOR   │     │     UI      │
                    │  (LLM/Template)   │  (Sheet)    │
                    └─────────────┘     └─────────────┘
```

---

## 3. COMPONENT RESPONSIBILITIES

### 3.1 Input Layer

**Responsibility:** Capture raw player input (text or voice)

**Outputs:**
- Raw text string
- Optional: voice transcription

**Cannot:**
- Interpret mechanics
- Modify intent
- Access game state

---

### 3.2 Intent Manager

**Responsibility:** Transform raw input into structured Intent

**Inputs:**
- Raw text from Input Layer
- Current game state (read-only)

**Outputs:**
- IntentObject (pending → clarifying → confirmed)

**Cannot:**
- Resolve mechanics
- Modify game state
- Override engine decisions

**Lifecycle Authority:**
- Owns intent status transitions
- Freezes intent before engine handoff
- Logs all intent state changes

---

### 3.3 Clarifier (Optional)

**Responsibility:** Request additional information from player

**Inputs:**
- Incomplete IntentObject
- Current game state (read-only)

**Outputs:**
- Clarification questions (text)
- Updated IntentObject fields

**Cannot:**
- Guess missing information
- Assume defaults silently
- Proceed without confirmation

**Note:** May use LLM for natural phrasing, but LLM cannot decide mechanics.

---

### 3.4 Engine (Resolver)

**Responsibility:** Resolve confirmed intents deterministically

**Inputs:**
- Frozen IntentObject (status: confirmed)
- Current WorldState

**Outputs:**
- EngineResult (authoritative)
- Events to log

**Authority:**
- SOLE mechanical authority
- Determines success/failure
- Computes all effects
- Manages RNG streams

**Cannot:**
- Be overridden by any other component
- Produce different results for same input

---

### 3.5 Event Log

**Responsibility:** Store authoritative record of all state changes

**Inputs:**
- IntentObjects (all states)
- EngineResults
- State snapshots (optional)

**Outputs:**
- Replay stream
- Historical queries

**Properties:**
- Append-only
- Immutable once written
- Authoritative for replay

---

### 3.6 Narrator

**Responsibility:** Produce human-readable description of outcomes

**Inputs:**
- EngineResult (read-only)
- Scene context (read-only)

**Outputs:**
- Narration text

**Cannot:**
- Alter outcomes
- Add mechanical effects
- Override engine results
- Modify game state

**Fallback:** If LLM unavailable, use deterministic templates.

---

### 3.7 UI (Character Sheet)

**Responsibility:** Display current state to player

**Inputs:**
- Event stream (subscribe)
- Current state (read-only)

**Outputs:**
- Visual representation
- No game logic

**Cannot:**
- Modify state
- Interpret mechanics
- Override derived values

---

## 4. DATA BOUNDARIES

### 4.1 Read-Only Data

The following data is read-only for all components except its owner:

| Data | Owner | Readers |
|------|-------|---------|
| WorldState | Engine | All |
| IntentObject | Intent Manager | Engine, Clarifier, Log |
| EngineResult | Engine | Narrator, UI, Log |
| Event Log | Log | All (replay) |

### 4.2 Write Authority

| Data | Write Authority |
|------|-----------------|
| WorldState | Engine ONLY |
| IntentObject | Intent Manager ONLY |
| EngineResult | Engine ONLY |
| Event Log | Engine + Intent Manager |
| Narration | Narrator (non-authoritative) |

---

## 5. NON-OVERRIDABLE RULES

### 5.1 Engine Output Cannot Be Overridden

```
RULE: Once the Engine produces an EngineResult, no component may:
  - Modify the result
  - Substitute a different result
  - Reinterpret the result mechanically
  - Prevent the result from being logged
```

### 5.2 Replay Does Not Depend on IPC Timing

```
RULE: Replay must produce identical results regardless of:
  - Component execution order
  - Timing variations
  - LLM availability
  - UI state
```

### 5.3 LLM Boundary Is Explicit and Narrow

```
RULE: LLM may only be used for:
  - Intent extraction (proposing structure, not deciding)
  - Clarification phrasing (natural language, not mechanics)
  - Narration (describing, not altering)

LLM may NEVER:
  - Decide mechanical outcomes
  - Modify frozen intents
  - Override engine results
  - Access RNG streams
```

---

## 6. EXECUTION MODEL (M1)

For M1, all components run **in-process** as synchronous modules.

```python
# M1 Execution Model (Pseudocode)
def process_player_input(raw_input: str, state: WorldState) -> tuple[EngineResult, str]:
    # 1. Create intent
    intent = intent_manager.create_intent(raw_input, state)

    # 2. Clarify if needed
    while intent.status == IntentStatus.CLARIFYING:
        question = clarifier.get_question(intent, state)
        response = get_player_response(question)  # blocks
        intent = intent_manager.update_intent(intent, response)

    # 3. Freeze intent
    intent = intent_manager.confirm_intent(intent)

    # 4. Resolve (ENGINE AUTHORITY)
    result = engine.resolve(intent, state)

    # 5. Log (AUTHORITATIVE)
    event_log.append(intent, result)

    # 6. Update state
    state = engine.apply_result(state, result)

    # 7. Narrate (NON-AUTHORITATIVE)
    narration = narrator.narrate(result, state)

    # 8. Update UI
    ui.update(state)

    return result, narration
```

Future milestones may introduce async/subprocess boundaries, but the authority rules remain unchanged.

---

## 7. TESTING REQUIREMENTS

### 7.1 Boundary Tests

- Verify Engine output cannot be modified post-resolution
- Verify Narrator receives read-only result
- Verify UI cannot write to state

### 7.2 Replay Tests

- Verify replay produces identical results without LLM
- Verify replay produces identical results with different timing
- Verify replay uses logged intents, not re-extraction

---

## 8. ESCALATION

If during implementation you encounter:

- A need for LLM to decide mechanics
- A need to modify engine output
- A need to add state outside event log

**STOP. ESCALATE. DO NOT PATCH.**

---

## END OF IPC CONTRACT
