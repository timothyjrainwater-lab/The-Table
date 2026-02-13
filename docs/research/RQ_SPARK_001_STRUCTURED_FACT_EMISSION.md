# RQ-SPARK-001: World Modeling → Structured Fact Emission

**Research Track:** 3 of 7
**Domain:** Spark (Generative Intelligence)
**Status:** QUESTION FILED — Awaiting Research Findings
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Problem Statement

Spark's job is not just "narrate." It must generate world state (scenes, objects, NPCs, affordances) and output that world knowledge in a way the Lens can safely ingest as structured, mechanically useful facts — with minimal ambiguity, consistent units, and predictable schemas. The hard part is getting Spark to reliably emit the right facts (dimensions, materials, placement, elevations, object classes) without drifting into prose or inventing unstable details.

---

## Research Objective

Develop a robust methodology for prompting, constraining, validating, and correcting Spark outputs so it can:

1. Generate rich scenes/NPCs/items, and
2. Emit a deterministic, schema-valid "Scene Fact Pack" suitable for Lens ingestion,

with bounded hallucination risk and clear handling of unknowns.

Must propose schemas, prompting patterns, validation loops, and fallback behaviors.

---

## Research Sub-Questions

### (1) Define "Scene Fact Pack" Schema

Research how to define a minimal-but-sufficient schema for scenes:

- **Scene metadata:** scene_id, tags, biome/indoors, lighting, time, theme
- **Object list:** object_id, class, material, dimensions (L/W/H), weight (optional), position (grid), elevation, facing, solidity/opacity, mobility, condition
- **Creature list:** creature_id, size, space/reach, position/elevation, stance (standing/prone), relevant equipment that affects geometry (tower shield, etc.)
- **Affordances:** "can be flipped," "can be climbed," "provides cover," "flammable," etc. (as flags, not prose)

Deliverable: recommended schema + "required vs optional" per object class.

### (2) Units, Defaults, and "Unknown" Discipline

Research best practices to force stable numeric outputs:

- Standardize units (feet/inches; grid squares)
- When Spark lacks certainty, it must emit UNKNOWN not guesses
- Allowed default ranges by object archetype (tavern table, bar stool, oak door) and how to label them as ASSUMED_STANDARD
- Prevent "detail drift" across regenerations

Deliverable: unit policy + default policy + unknown policy.

### (3) Prompting Patterns for Reliable Structured Generation

Research methods to maximize schema adherence:

- JSON schema enforcement strategies
- "Two-pass generation": (a) narrative scene draft, (b) facts-only extraction
- "Archetype library" prompting: tables/chairs/doors/windows as reusable canonical templates
- Self-checking prompts and constraint reinforcement ("only output JSON")

Deliverable: prompting templates + best practices that reduce invalid outputs.

### (4) Validation + Repair Loop (Lens-side) without Cross-Talk

Research how to pair Spark with a strict validator:

- JSON schema validation + type checking
- Range validation (table height must be plausible)
- Consistency checks (object positions don't overlap illegally)
- Repair protocol: validator requests only the invalid fields, Spark re-emits minimal patch

Deliverable: validation rules + patch/repair protocol.

### (5) Scene Layout Generation on a Grid (No Graphics Assumptions)

Research approaches for Spark to generate placements that are:

- Grid-consistent
- Tactically plausible (doors, furniture, lanes)
- Not requiring 3D rendering
- Compatible with Box resolution (clear squares, blocking objects)

Compare:
- Procedural room grammars
- Constraint solving (simple SAT/ILP style constraints)
- Heuristic placement algorithms

Deliverable: recommended scene layout method + constraints list.

### (6) Improvisation: "On-demand Fact Completion"

When players do unexpected things, Lens may ask Spark for missing facts:

Research how Spark should respond:
- Minimal patch output (no prose)
- Use archetype templates where possible
- Mark uncertainty explicitly
- Avoid retroactive contradictions of prior facts

Deliverable: "fact completion" protocol and examples.

### (7) NPC + Encounter Generation with Mechanical Affordances

Spark can generate NPCs and encounters, but must output:

- Stat block identifiers / references (not homebrew unless allowed)
- Intent/role tags (brawler, archer, controller)
- Environment ties (uses cover, uses elevation)
- Constraints consistent with Box's capabilities

Deliverable: encounter emission format and constraints.

### (8) Output: Spark→Lens Reliability Playbook

Synthesize into a practical playbook:
- Schema(s)
- Prompting templates
- Validation + repair loop
- Archetype library strategy
- Constraints and forbidden behaviors
- Metrics for reliability (schema pass rate, contradiction rate)

---

## Research Findings

**STATUS: NOT YET DELIVERED**

---

## Cross-References

- `docs/research/RQ_LENS_001_DATA_INDEXING.md` — Lens ingestion contract (complementary)
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Spark→Lens interface contract
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Spark has no authority; generates only
