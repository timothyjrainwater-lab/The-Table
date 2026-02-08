# Voice Intent & Clarification Protocol
## Translating Human Speech into Deterministic Action Without Breaking Immersion

**Document ID:** VICP-001
**Version:** 1.0
**Status:** ADOPTED
**Scope:** Voice Input · Intent Parsing · Clarification · Targeting · Determinism

**Project:** AIDM — Deterministic D&D 3.5e Engine + Local Open-Source LLM
**Document Type:** Core Interaction Protocol

---

## 1. PURPOSE

This document defines how **freeform spoken player input** is transformed into
**structured, deterministic intent** suitable for mechanical resolution,
*without* requiring menus, buttons, or explicit command syntax.

The goal is to:
- Preserve natural tabletop conversation
- Avoid "computer game" interaction patterns
- Prevent the LLM from becoming a rules authority
- Ensure replayability and auditability

---

## 2. CORE PRINCIPLE

> **Players speak in natural language.
> The system clarifies like a human DM.
> The engine resolves mechanics.**

Voice is not a command language.
It is a **conversation**.

---

## 3. INTENT, NOT COMMANDS

### 3.1 Intent-Centric Design

Players do not issue commands like:
- "MoveAction(target=grid[4,6])"

They say things like:
- "I rush the goblin by the door and try to shove him back."

The system's job is to extract:
- **What the player is trying to do**
- Not *how they think the rules work*

---

## 4. INTENT STRUCTURE (INTERNAL)

Every action must resolve to a structured **Intent Object** before reaching the engine.

### 4.1 Required Intent Fields

An intent must define:
- `actor` (who is acting)
- `action_type` (move, attack, cast, manipulate, etc.)
- `primary_target` (entity, location, or area)
- `method` (weapon, spell, maneuver, body, etc.)
- `constraints` (distance, line of sight, conditions)
- `declared_goal` (optional, narrative intent)

No mechanical resolution occurs until these are unambiguous.

---

### 4.2 Intent Status Lifecycle

Every intent passes through a defined lifecycle:

```
pending → clarifying → confirmed → resolved
```

- **pending**: Intent received but not yet validated
- **clarifying**: Missing required fields; awaiting player response
- **confirmed**: All fields populated; frozen for resolution
- **resolved**: Engine has processed; outcome logged

Once an intent reaches `confirmed`, the LLM may not alter it.

---

## 5. CLARIFICATION AS CONVERSATION (CRITICAL)

### 5.1 When Clarification Is Required

Clarification is required if:
- Multiple valid targets exist
- Distance or positioning matters
- Action could resolve in multiple rule-meaningful ways
- The intent would violate physical constraints

### 5.2 How Clarification Must Sound

Clarification must:
- Be phrased like a DM at a table
- Avoid rules jargon unless asked
- Never feel like a form or prompt

Examples:
- "Which goblin — the one near the brazier or the one by the door?"
- "Are you trying to push him off the ledge, or just back a few steps?"
- "That would put you in melee range — is that okay?"

---

## 6. NO SILENT ASSUMPTIONS

The system must never:
- Guess targeting
- Infer positioning
- Assume rule interpretations

If ambiguity exists, **the system must ask**.

Silence is not consent.

---

## 7. POINTING & VISUAL DISAMBIGUATION

### 7.1 Minimal Visual Interaction

The only required visual interaction is **pointing**.

Players may:
- Say "here" while pointing
- Click/tap a square or token
- Gesture (if supported)

This supplies:
- `location_reference` or `target_reference`

No other UI interaction is required.

---

## 8. CONFIRMATION WITHOUT BREAKING FLOW

### 8.1 Soft Confirmation

Once intent is clear, the system may respond with a **natural confirmation**:

> "Alright — you move up to the goblin by the door and attempt to bull rush him toward the ledge."

This is not a modal confirmation.
It is table talk.

If the player objects, they correct it verbally.

---

## 9. RETRACTION AND TIMEOUT

### 9.1 Intent Retraction

A player may retract intent at any time **before** the intent reaches `confirmed` status.

Once confirmed and handed to the engine, retraction is not permitted.
The action proceeds to resolution.

### 9.2 Clarification Timeout

If a player does not respond to a clarification request:
- After a configurable timeout, the action **cancels gracefully**
- The system announces: "I didn't catch that — let me know when you're ready."
- No partial action is resolved
- No penalty is applied

Timeout behavior is a UX concern, not a mechanical one.

---

## 10. ENGINE HANDOFF (HARD BOUNDARY)

Once intent is fully specified:
- The intent object is frozen
- The LLM may not alter it
- The deterministic engine resolves the outcome

The LLM must not:
- Modify rolls
- Adjust modifiers
- Soften outcomes

It may only **narrate the result returned**.

---

## 11. FAILURE & IMPOSSIBILITY HANDLING

### 11.1 Physical Impossibility

If an action is impossible:
- The system explains *why* in-world

Example:
- "You can't reach that far this round — it's beyond your movement."

### 11.2 Rule-Based Impossibility

If disallowed by ruleset:
- The system cites the rule or variant

Example:
- "In this campaign, that class can't use that ability."

No ideological language is permitted.

---

## 12. LOGGING & REPLAY REQUIREMENTS

Every resolved intent must be logged with:
- Original spoken/text input
- Clarification exchanges
- Final structured intent
- Engine result
- Ruleset references

This enables:
- Replay
- Debugging
- Trust

### 12.1 Partial Intent Logging

Intents that fail to reach `confirmed` (due to timeout, retraction, or impossibility)
may be logged for debugging purposes.

Partial intent logs are **non-authoritative** and do not affect world state.

---

## 13. MULTIPLAYER COORDINATION (SCOPE NOTE)

This protocol is designed for **solo-first** play.

Multiplayer coordination (simultaneous declarations, turn order disputes, etc.)
is explicitly out of scope for this document and will be addressed in a future
multiplayer coordination protocol if/when multiplayer is implemented.

---

## 14. FAILURE MODES THIS PROTOCOL PREVENTS

Without this protocol:
- The LLM guesses
- Players feel railroaded
- Outcomes feel arbitrary
- Determinism erodes

With this protocol:
- Conversation stays natural
- Authority stays clear
- The game feels fair

---

## 15. SUMMARY OF NON-NEGOTIABLES

1. Voice is the primary interface
2. Clarification is conversational, not mechanical
3. No silent assumptions
4. Intent must be fully specified before resolution
5. The engine is the final authority
6. Retraction allowed until confirmation
7. Timeout cancels gracefully

---

## 16. NEXT DEPENDENT DOCUMENTS

This protocol feeds directly into:
- `LLM_ENGINE_BOUNDARY_CONTRACT.md`
- `LOCAL_RUNTIME_PACKAGING_STRATEGY.md`

---

## END OF VOICE INTENT & CLARIFICATION PROTOCOL
