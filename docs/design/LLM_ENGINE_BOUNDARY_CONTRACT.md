# LLM–Engine Boundary Contract
## Defining Authority, Freedom, and Responsibility in the AIDM System

**Document ID:** LEB-001
**Version:** 1.0
**Status:** ADOPTED
**Scope:** Authority · Safety · Determinism · Creative Freedom

**Project:** AIDM — Deterministic D&D 3.5e Engine + Local Open-Source LLM
**Document Type:** Core Architecture Contract

---

## 1. PURPOSE

This document defines the **hard boundary** between:

- The **LLM (creative DM layer)**, and
- The **deterministic rules engine (mechanical authority)**

Its purpose is to:
- Preserve true creative freedom
- Prevent rule drift or improvisation
- Maintain determinism and replayability
- Ensure trust between player and system

This is the most important contract in the entire project.

---

## 2. CORE AXIOM (NON-NEGOTIABLE)

> **The LLM may describe reality.
> The engine defines reality.**

Any violation of this axiom invalidates the system.

---

## 3. AUTHORITY SEPARATION

### 3.1 The Engine Is the Sole Mechanical Authority

The engine alone may:
- Resolve actions
- Roll dice
- Apply modifiers
- Enforce ordering
- Update world state
- Determine success, failure, or consequence

No other component may alter mechanical truth.

---

### 3.2 The LLM Is the Narrative & Interpretive Layer

The LLM may:
- Interpret player intent
- Ask clarification questions
- Narrate outcomes
- Generate NPC dialogue
- Write campaigns, locations, lore
- Maintain conversational continuity
- Explain results in natural language

The LLM **must never**:
- Invent modifiers
- Adjust rolls
- Change distances
- Override outcomes
- "Soften" consequences
- Apply hidden bonuses or penalties

---

## 4. ALLOWED LLM BEHAVIORS (EXPLICIT)

The LLM is explicitly allowed to:

- Be expressive, emotional, dark, humorous, or strange
- Portray evil characters, gods, and worlds
- Narrate grim or uncomfortable consequences
- Generate morally ambiguous or extreme scenarios
- Roleplay without ideological filtering *within campaign rules*

Creative freedom is a **feature**, not a risk.

---

## 5. FORBIDDEN LLM BEHAVIORS (EXPLICIT)

The LLM must never:

1. Decide whether an action "should" be allowed
2. Refuse an in-fiction action for moral or ideological reasons
3. Invent mechanical exceptions
4. Resolve ambiguity silently
5. Override Session Zero configuration
6. Hide or rewrite engine output
7. Change outcomes for narrative convenience

If the LLM violates these, trust is broken.

---

## 6. REFUSAL AUTHORITY (CRITICAL)

### 6.1 The LLM Is Not a Refusal Authority

The LLM may not refuse an action unless:

- The **engine** determines it is impossible, or
- The **ruleset/session config** explicitly forbids it

All refusals must be traceable to:
- Ruleset manifest
- Physical constraints
- Session Zero boundaries

No "I'm not allowed to…" language is permitted.

---

## 7. AMBIGUITY RESOLUTION RULE

If multiple valid interpretations exist:

- The LLM must ask
- The engine must not guess
- No default assumptions are allowed

Conversation resolves ambiguity, not inference.

---

## 8. NARRATION OBLIGATIONS

When narrating outcomes, the LLM must:

- Reflect the engine's result accurately
- Include consequences faithfully
- Avoid editorializing outcomes
- Avoid moral commentary unless in-character

Narration may explain *what happened*, not *why it was good or bad*.

---

## 9. LLM CONTEXT MANAGEMENT

### 9.1 Context Window Contents

The LLM receives:
- Summarized world state (not raw event logs)
- Current scene and participants
- Recent conversation history
- Session Zero configuration summary

Raw event logs are provided only when explicitly requested for debugging.

### 9.2 Narration Regeneration

Narration may be regenerated without re-resolving the mechanical action.
The engine result is authoritative; the narration is presentation.

### 9.3 Error Attribution

If the LLM misinterprets player intent:
- The engine result is authoritative
- Clarification may be triggered
- Narration may be regenerated
- The mechanical outcome is not reversed

---

## 10. LLM FAILURE MODES & FALLBACKS (CRITICAL)

The system must handle LLM failures gracefully.

### 10.1 Timeout

If the LLM does not respond within the configured timeout:
- Fall back to structured input mode
- Present the player with explicit options
- Continue without narrative embellishment

### 10.2 Invalid Output

If the LLM produces output that cannot be parsed or violates contract:
- Engine rejects the output
- Request is retried or clarification is requested
- No mechanical action proceeds without valid intent

### 10.3 Unexpected Refusal

If the LLM refuses an action that is permitted by Session Zero:
- Treat this as an error, not authority
- Log the refusal for debugging
- Retry with rephrased context or fall back to structured input

### 10.4 Degraded Mode

If the LLM is unavailable or repeatedly failing:
- The system may enter "degraded mode"
- Text-based structured input replaces voice
- Narration is minimal or omitted
- Mechanical resolution continues normally

The engine never blocks on LLM availability.

---

## 11. LOGGING & AUDIT REQUIREMENTS

For every resolved action, the system must log:

- Raw player input
- Clarification exchanges
- Final intent object
- Engine resolution
- LLM narration (or narration seed + style summary)
- Ruleset references

The LLM must not summarize away critical details.

---

## 12. FAILURE MODES THIS CONTRACT PREVENTS

Without this boundary:
- The LLM becomes a hidden DM fiat engine
- Players lose trust
- Replay diverges
- Rules arguments resurface

With this boundary:
- Creativity flourishes safely
- Consequences feel earned
- The world feels solid

---

## 13. PHILOSOPHICAL NOTE (INTENT)

This contract is not about limiting intelligence.

It exists to ensure that:
- Freedom comes from consistent reality
- Imagination thrives when physics are stable
- Story has weight because outcomes are real

---

## 14. SUMMARY OF NON-NEGOTIABLES

1. Engine defines mechanics
2. LLM defines expression
3. No ideological refusals
4. No narrative overrides
5. All outcomes are logged
6. Authority is explicit
7. Failure modes are graceful, not blocking

---

## 15. NEXT DEPENDENT DOCUMENT

The final required artifact to complete the foundation is:

- `LOCAL_RUNTIME_PACKAGING_STRATEGY.md`

This defines how all of this becomes a **single-machine, shareable system**.

---

## 16. BOUNDARY LAW: BL-021 — Events Record Results, Not Formulas

Event payloads must contain **resolved values only** — never formulas, expressions,
calculations, or computation instructions. The engine computes; the event records the
outcome. If a payload key suggests a formula (e.g., `formula`, `expression`,
`calculation`, `equation`, `compute`), the event is encoding process instead of result,
which violates the engine's authority boundary and breaks replay determinism.

**Enforced by:** `tests/test_boundary_law.py` — structural scan of all event payload
schemas in `MUTATING_EVENTS` and `INFORMATIONAL_EVENTS`.

---

## END OF LLM–ENGINE BOUNDARY CONTRACT
