# RQ-NARR-001: AI Narrative Balance — Spark Creativity Bounded by Box Truth

**Research Track:** 7 of 7
**Domain:** AI Narrative Balance
**Status:** QUESTION FILED — Awaiting Research Findings
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Problem Statement

Spark must feel like a real DM: responsive, vivid, adaptive. But Spark must never:

- Contradict Box outcomes
- Imply a different mechanical reality than what Box resolved
- "Smooth over" errors by inventing causes
- Drift into rule adjudication

At the same time, Box must never generate narration. The Lens must supply Spark with the right slice of truth so Spark can narrate accurately without being overloaded.

**This is a control and contract problem:** what Spark is allowed to say, when, and based on what inputs.

---

## Research Objective

Design a robust system that guarantees Spark narration remains:

1. Consistent with Box state and outcomes
2. Bounded by Lens-provided truth
3. Stylistically "DM-like" without becoming a rules arbiter
4. Resilient under edge cases (surprises, missing data, complex combat)

Deliver concrete contracts, guardrails, prompting patterns, and evaluation methods.

---

## Research Sub-Questions

### (1) Define Spark's Allowed Output Space

Research how to formally separate:
- **Descriptive narration** (allowed)
- **Interpretation of intent** (allowed, but must confirm)
- **Mechanical adjudication** (forbidden)
- **Retconning** (forbidden)
- **Explaining Box math** (forbidden unless reading a Box receipt)

Deliverable: a clear allowed/forbidden taxonomy with examples.

### (2) "Truth Packet" Interface from Lens → Spark

Research how Spark should receive state:

Compact, structured summaries of:
- Positions, visible objects, elevations
- Current conditions/status effects
- The most recent Box resolution event (what happened)
- Any explain/receipt snippets that Spark may paraphrase

Key: Spark must not infer beyond packet boundaries.

Deliverable: truth packet schema + size budgeting rules.

### (3) Narration Templates Bound to Box Events

Research a template-driven narration approach:

Box produces canonical event labels:
- HIT, MISS, SAVE_SUCCESS, AOO_TRIGGERED, COVER_APPLIED, etc.

Spark selects narration templates conditioned on:
- Event label
- Scene tone
- Character voice

This keeps narration expressive but mechanically anchored.

Deliverable: event label set + template strategy.

### (4) Confirmation Gates for Player Intent

Research "narrative-first" confirmation patterns:
1. Spark proposes interpretation
2. Lens shows geometry overlays (if needed)
3. Player confirms
4. Box executes

Spark must never assume a target square or exact path if ambiguity exists.

Deliverable: confirmation protocol + patterns for common cases (AoE, movement, line attacks).

### (5) Handling Unknowns and Missing Facts

Research how Spark should behave when Lens returns "unknown":
- Ask for clarification conversationally
- Request fact completion via Lens protocol
- Never fabricate dimensions/positions
- Use "DM stall pacing" ("give me a moment") correctly

Deliverable: unknown-handling playbook.

### (6) Tone Control vs Truth Control

Research how to allow style variation (grim, whimsical, Mercer-like, terse) without changing truth:
- Separate "style prompt" from "truth packet"
- Forbid style layer from adding mechanics
- Ensure style does not imply different outcomes ("barely missed" vs "missed by a mile" must match margins if disclosed)

Deliverable: tone architecture and constraints.

### (7) Evaluation: Detecting Narrative Truth Violations

Research methods to automatically detect when Spark narration violates Box truth:
- Contract checks (mentions an entity that isn't present)
- Outcome mismatch checks (says "you hit" when Box says MISS)
- Geometry mismatch checks ("behind the pillar" when no pillar blocks LOE)
- Regression tests using scripted combats

Deliverable: evaluation rubric + automated tests.

### (8) Output: Narrative Integrity Spec

Synthesize into:
- Allowed/forbidden rules
- Truth packet schema
- Event labels + narration templates approach
- Confirmation gates
- Unknown-handling
- Tone separation
- Evaluation strategy

---

## Research Findings

**STATUS: NOT YET DELIVERED**

---

## Cross-References

- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Spark never refuses, Spark has no authority
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Lens→Spark context assembly
- `docs/narration/guarded_narration_service.py` — Existing narration guardrails implementation
