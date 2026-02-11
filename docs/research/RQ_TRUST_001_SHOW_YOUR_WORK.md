# RQ-TRUST-001: "Show Your Work" Without Becoming a Debug UI

**Research Track:** 6 of 7
**Domain:** Trust & Transparency
**Status:** QUESTION FILED — Awaiting Research Findings
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Problem Statement

Your core failure mode is trust collapse: one wrong AoO, one off-by-one square, one bad cover result, and the player suspects the system is cheating or sloppy. You need auditability and explainability that:

- Proves Box is authoritative and correct
- Exposes the minimum necessary reasoning to the player
- Does not add panels, toolbars, or "debug overlays" that break the table metaphor
- Keeps Spark from contaminating mechanical truth

**This is not generic "explainable AI." It's rules engine explainability in an immersive UI.**

---

## Research Objective

Design a trust system that lets players verify outcomes (rolls, distances, LOS/LOE, cover, AoOs, damage vs hardness) with high confidence, using table-native affordances (parchment slips, DM verbal confirmation, minimal overlays) rather than traditional UI.

Must propose concrete mechanisms, data flows, and UX patterns that preserve the "table" experience while making the system provably honest.

---

## Research Sub-Questions

### (1) Define "Trust-Critical Events"

Research and enumerate the event types that most commonly trigger distrust:
- Distance + movement legality
- AoO triggers and threatened squares
- Cover and concealment (including relative height cases)
- LOS vs LOE
- Area-of-effect inclusion/exclusion
- Damage application vs hardness/DR/resistance
- Randomness integrity (dice)

Deliverable: prioritized list + why each matters.

### (2) Minimal Explain Payloads from Box

Research how Box should generate an "explain packet" that is:
- Deterministic
- Concise
- Structured (not prose)
- Replayable

Examples:
- "Fireball: center at (x,y); radius=20ft; included squares=[...]; goblin3 excluded because pillar blocks LOE"
- "Cover: 50% (soft cover) because line passes through table volume above halfling's prone height threshold"

Deliverable: explain schema + examples per event type.

### (3) Table-Native UX for Transparency

Research UI patterns that preserve metaphor:
- DM verbally summarizing key facts
- "Plastic stencil" overlay for AoE (temporary, lean-up only)
- Parchment receipt slips ("Combat Receipt") that can be filed into Tome
- Dice tray as the persistent truth source for randomness
- Optional "ask why" interaction: player taps a result → DM offers the receipt

Deliverable: 3-5 concrete UX patterns + when to use each.

### (4) Audit Trails + Receipts (Non-negotiable for trust)

Research how to store and expose:
- Roll provenance (seed, dice, modifiers, timestamps)
- Rule references (SRD/PHB page refs where applicable)
- The exact geometry inputs used (positions, elevations, object dimensions)

This is for disputes and self-verification.

Deliverable: audit log design + "receipt" generation spec.

### (5) Anti-Hallucination Boundary for Explanations

Research how to ensure Spark never invents mechanical explanations:
- Only Box produces explain packets
- Spark may paraphrase but must not alter facts
- Lens serves explain packets to Spark as read-only material

Deliverable: boundary rules + enforcement patterns.

### (6) Player-Controlled Transparency Levels (Without UI Bloat)

Research a small set of modes (e.g., "default," "high transparency," "tournament mode") that change:
- How often receipts are offered
- Whether AoE overlays are shown automatically
- Whether mechanical citations are included

But must be invoked via table objects (gemstone settings) and stored in Lens.

Deliverable: 2-3 modes + behavior definitions.

### (7) Validation & Regression Strategy to Protect Trust

Research test and verification strategies that materially reduce trust-breaking bugs:
- Property-based tests for geometry edge cases
- Golden test fixtures for combat scenarios
- Fuzzing for AoE/LOS/cover calculations
- Replay verification (10x runs) as a CI gate

Deliverable: test plan specifically tied to trust-critical events.

### (8) Output: Trust Framework Spec

Synthesize into an implementable spec:
- Trust-critical events list
- Explain packet schema
- Receipt/audit log format
- UI delivery patterns (table-native)
- Transparency modes
- Validation gates

---

## Research Findings

**STATUS: NOT YET DELIVERED**

---

## Cross-References

- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Trust repair axiom, provenance labeling standard
- `docs/design/TABLE_SURFACE_UI_SPECIFICATION.md` — Table objects, parchment receipts
- `docs/design/BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md` — Cover, LOS/LOE, AoE calculations
