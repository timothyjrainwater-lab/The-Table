# RQ-BOX-001: Grid-Based Geometric Engine

**Research Track:** 1 of 7
**Domain:** Box (Deterministic Engine)
**Status:** QUESTION FILED — Awaiting Research Findings
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Research Goal

Design a computational model for discrete geometric reasoning on a grid where battlefield objects have physical metadata (height, size, material, facing), enabling exact RAW 3.5e cover, line of sight, line of effect, elevation, and destructibility calculations without using a traditional physics engine.

---

## Research Sub-Questions

### (1) Grid-Based Spatial Query Structures (NOT world partitioning)

Research data structures optimized for:

Fast queries like:
- "What objects intersect this line?"
- "What objects occupy these squares?"
- "What is between A and B?"

Compare:
- Spatial hashing
- Grid-index maps
- Cell → object adjacency lists

Focus on constant-time geometric queries on a square grid.

### (2) Data-Oriented Object Representation (critical)

Research how ECS / DOD can represent objects with:
- Height
- Size category
- Material
- Facing
- Opacity
- Solidity
- Condition

Goal: object metadata that the Box can query in CPU-cache-friendly bursts during rule checks.

### (3) Exact Cover Geometry Algorithms (core problem)

Research algorithms for:

Determining cover via line intersection through object volumes

Accounting for:
- Relative heights (halfling vs human vs ogre)
- Object height vs character height
- Facing direction
- Partial obstruction

NOT visual raycasting — mathematical ray intersection through grid cells with height metadata.

**This is the heart of the problem.**

### (4) Line of Sight vs Line of Effect on a Height-Aware Grid

Research how to:
- Represent elevation per square
- Compute LOS/LOE across varying elevations
- Handle "under table", "behind chair", "on higher ground"
- Use integer math / grid traversal instead of physics raycasts

### (5) Representing Destructibility as State Transitions (not mesh destruction)

Research modeling objects as:
- Intact → Damaged → Destroyed → Difficult Terrain
- Upright → Prone → Provides directional cover

Focus on state machines and metadata mutation, not physical simulation.

### (6) Efficient Representation of Environmental State

Research bitmasks / flags / compact state encodings so the Box can answer:
- "Does this square provide cover?"
- "Is this square difficult terrain?"
- "Does this object block line of effect?"

With minimal computation.

### (7) Turn-Based Recalculation Strategies

Since this is turn-based:

Research how to:
- Recompute only when state changes
- Cache geometric relationships
- Avoid recomputing cover/LOS every frame (because there are no frames)

### (8) Synthesis: A Box-Friendly Geometric Engine

Research how to combine the above into a framework where:
- No physics engine exists
- No rendering assumptions exist
- Pure geometric reasoning + metadata solves all RAW battlefield rules

---

## Design Constraint (Thunder)

> "This version researches the problem you actually have: A deterministic geometric reasoning engine on a metadata-rich grid. Not: How AAA games simulate destructible worlds in real time. That's not your domain."

---

## Research Findings

**STATUS: NOT YET DELIVERED**

---

## Cross-References

- `docs/design/BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md` — Box battlefield specification
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Layer interaction contracts
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Authority model (Box is sole mechanical authority)
