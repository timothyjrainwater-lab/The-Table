# RQ-INTERACT-001: Voice-First, Click-Second Interaction

**Research Track:** 5 of 7
**Domain:** Player Interaction
**Status:** QUESTION FILED — Awaiting Research Findings
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Problem Statement

Player intent should be expressed primarily in natural language to the DM. Direct map manipulation exists, but as a secondary path. The system must translate ambiguous human intent into precise mechanical actions without forcing the player into UI workflows, and without letting misinterpretation corrupt Box resolution.

**This is not a speech-to-command problem.**
This is an intent interpretation → confirmation → mechanical execution pipeline that preserves the feeling of talking to a DM.

---

## Research Objective

Design an interaction model where:

1. Player speaks/types intent in natural language
2. System interprets it into structured "Action Intents"
3. DM confirms interpretation visually and conversationally
4. Box executes only after confirmation
5. Direct map interaction remains available but never primary

Provide concrete strategies for intent parsing, ambiguity handling, confirmation UX, and map interaction that preserve immersion and mechanical precision.

---

## Research Sub-Questions

### (1) Intent → Structured Action Translation

Research how to reliably convert:

> "I want to cast fireball and try to catch all three goblins"

into:

```
action: CAST_SPELL
spell: FIREBALL
targeting_mode: AREA
desired_targets: [goblin1, goblin2, goblin3]
```

Focus on:
- Semantic parsing techniques for tabletop commands
- Handling vague phrases ("around them", "near the door", "behind the table")
- Maintaining context across turns

Deliverable: intent schema + parsing strategy.

### (2) Ambiguity Resolution via DM Confirmation

Research how to design a loop where:
- System proposes a geometric interpretation
- Highlights it on the map
- Asks for confirmation in natural language

Example: "Here? Or here?"

This is critical for trust.

Deliverable: confirmation loop pattern + examples.

### (3) Lean-Up Map Interaction Model

Research how to design a minimal interaction pattern where:
- Player "leans up" to the map
- Cursor becomes a geometric tool (radius, ray, movement path)
- No UI overlays or toolbars are needed
- Returning to seat restores prior state

Deliverable: interaction grammar for map mode.

### (4) Character Sheet as Action Surface

Research how to make the character sheet serve as:
- Spell/ability trigger surface
- Contextual info display
- Alternative to voice input

Without becoming an MMO hotbar.

Deliverable: interaction principles + examples.

### (5) Error Handling Without Breaking Immersion

Research how to handle mis-parses:
- DM asks clarification questions
- Avoid system error messages
- Keep interaction conversational

Deliverable: recovery patterns.

### (6) Timing and Responsiveness Expectations

Research acceptable latency for:
- Intent parsing
- Confirmation rendering
- Box resolution

So the conversation feels natural.

Deliverable: timing targets + pacing rules.

### (7) Accessibility and Fallback Paths

Research:
- When players prefer clicking vs speaking
- How to support both without UI creep
- How to maintain metaphor consistency

Deliverable: dual-mode design rules.

### (8) Output: Interaction Playbook

Synthesize into:
- Intent schema
- Confirmation loop model
- Map interaction grammar
- Character sheet interaction rules
- Error recovery patterns
- Latency targets

---

## Research Findings

**STATUS: NOT YET DELIVERED**

---

## Cross-References

- `docs/design/TABLE_SURFACE_UI_SPECIFICATION.md` — Table interaction model, lean-up mechanic
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Intent processing flow
- `docs/research/RQ_VOICE_001_BENCHMARK_RESULTS.md` — Voice pipeline benchmarks
