# RQ-LENS-001: Data Indexing + Retrieval Contract

**Research Track:** 2 of 7
**Domain:** Lens (Stateful Focus System)
**Status:** FINDINGS RECEIVED (complete)
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt + findings

---

## Problem Statement

The Lens must (a) ingest structured facts about the world as they are created/observed, (b) store them durably with provenance and versioning, and (c) serve exact answers to Box queries with low latency and zero ambiguity. When the data is missing, the Lens must trigger a controlled "fact acquisition" request to Spark, then immediately re-serve to Box — without Spark ever touching Box.

---

## Research Objective

Design a Lens architecture and schema that can act as the sole shared memory between Spark and Box, supporting:

1. Authoritative object facts for deterministic resolution (Box)
2. Narrative/semantic context for generation (Spark)
3. Provenance + auditability for trust (why a value is what it is)
4. Low-latency structured queries during combat and interaction

Must propose concrete schemas, query patterns, invariants, and failure-handling behavior.

---

## Research Sub-Questions

### (1) Define the Lens "Truth Model"

Research and propose a strict model for what Lens stores and how it treats "truth":

- **Fact types:** object geometry, material, state, location, elevation, facing, opacity/solidity, ownership, tags
- **Assertion sources:** Spark assertions, Box-derived facts, player-specified facts, imported canonical references
- **Confidence / quality levels:** when is a fact "authoritative" vs "estimated" vs "unknown"
- **Conflict rules:** what happens if Spark asserts X and later asserts Y
- **Monotonicity:** which facts can change (state) vs must not change (identity, base dimensions unless revised)

Deliverable: a formal "truth hierarchy" and conflict-resolution policy.

### (2) Canonical Identity + Object Lifecycles

Research best practices for:
- Stable IDs for objects across sessions
- Sub-object IDs (chair leg created from chair)
- Merge/split lifecycles (table breaks into debris)
- Referential integrity (no orphan references)
- Event-sourced vs snapshot storage tradeoffs

Deliverable: an ID scheme + lifecycle state machine + examples.

### (3) Schema Design for Fast Mechanical Queries

Research data layouts that let Box query quickly:

Typical Box queries Lens must answer:
- "Give me the full mechanical profile for object O."
- "What occupies squares S?"
- "What blocks LOS between A and B?"
- "What is the height/material/condition of O at time T?"
- "List all objects within radius R of point P."

Compare:
- Relational (SQLite) normalized schemas
- Document/JSON + indexes
- Hybrid: relational core + JSON blobs for "profile payloads"
- Materialized views / denormalized tables for hot queries

Deliverable: a recommended schema + indexes + query examples.

### (4) Versioning + Time Travel (Determinism Support)

Because replay/determinism matters:
- Do we store event logs in Lens, or only in Box?
- How does Lens serve "facts as-of timestamp/turn/initiative count"
- Snapshotting strategy vs append-only
- Performance implications for frequent queries during combat

Deliverable: a versioning strategy that supports replay and audits.

### (5) Missing-Data Protocol ("Fact Acquisition")

Research a rigorous protocol for when Box needs data Lens doesn't have:
1. Box → Lens: query returns MISSING_REQUIRED_FACT
2. Lens → Spark: request for specific missing fields only
3. Spark → Lens: structured response (no prose)
4. Lens validates/normalizes; stores with provenance; re-serves to Box

Define:
- Required fields per object class (table, chair, tree, wall, creature)
- Defaulting rules (allowed vs forbidden defaults)
- Timeout behavior
- Refusal/fallback behavior when Spark can't provide (or shouldn't)

Deliverable: a strict request/response contract + validation rules.

### (6) Provenance + Auditability (Trust layer)

Research how to store and expose:
- Who/what asserted a fact
- Why it changed
- Links to evidence (alignment ledger entries, scene generation step, etc.)
- Minimal "explain" payloads that do not contaminate Spark or slow Box

Deliverable: provenance schema + "explain()" interface design.

### (7) Performance Targets + Caching

Because no graphics overhead exists, you can spend compute — but latency still matters.

Research:
- Hot path caching (object profiles, spatial occupancy tables)
- Invalidation triggers (object moved, destroyed, elevation changed)
- Memory vs disk tradeoffs
- Expected query volume per round and per turn

Deliverable: performance budget + caching plan.

### (8) Output: Lens Architecture Spec

Synthesize into an implementable spec including:
- Data model
- Query API
- Mutation API (Spark writes)
- Versioning
- Missing-data protocol
- Provenance
- Test strategy and invariants ("Lens never returns ambiguous facts to Box")

---

## Research Findings

### Preamble

The integration of generative intelligence with deterministic simulation environments represents one of the most significant engineering hurdles in modern computational design. This report proposes the architecture for the Lens, a specialized intermediary layer designed to act as the authoritative shared memory between a narrative generation engine (Spark) and a deterministic mechanical simulation engine (Box). The primary objective of the Lens is to solve the **librarian problem**: the efficient ingestion, durable storage, and low-latency retrieval of structured facts. The Lens must ensure that Box receives unambiguous mechanical profiles for physical resolution while providing Spark with the semantic and narrative context required for continuous world-building. This design prioritizes provenance, versioning, and a rigorous truth model to support deterministic replay and explainable reasoning within complex, multi-agent virtual environments.

---

### Finding 1: The Lens Truth Model and Conflict Resolution Policy

The foundational layer of the Lens architecture is its Truth Model, which defines how the system handles multi-source factual assertions. In a multi-agent simulation where data is provided by a variety of sources — including generative AI, mechanical engines, and manual overrides — conflicts are an inherent characteristic of the data stream. The Lens treats truth discovery as an iterative process of identifying the most trustworthy value among competing observations.

#### Classification of Fact Types and Monotonicity Rules

Data within the Lens is partitioned into specific fact types, each governed by distinct monotonicity rules that dictate how and when a value may be modified.

| Fact Category | Primary Attributes | Assertion Source | Monotonicity Rule |
|---|---|---|---|
| **Core Identity** | Unique GUID, Entity Class, Base Template | Canonical Ref / Spark | **Immutable**; identity anchors are permanent |
| **Base Geometry** | Dimensions, Mass, Volume, Center of Gravity | Canonical Ref / Box | **Static**; requires structural revision event to change |
| **Material Profile** | Composition, Density, Hardness, Flammability | Canonical Ref / Spark | **Static**; base material identity is immutable |
| **Spatial State** | X, Y, Z, Elevation, Facing, Velocity | Box (Mechanical) | **Monotonic**; changes only via validated physics ticks |
| **Mechanical State** | Health, Temperature, Opacity, Solidity | Box / Lens Default | **Dynamic**; tracks temporal degradation or change |
| **Narrative Context** | Ownership, Tags, Semantic History, "Vibe" | Spark (Narrative) | **Fluid**; subject to generative revision within constraints |

The principle of monotonicity ensures that while an object's location or health may change as time progresses, its fundamental identity remains anchored. Cryptographic ledgers and strong embodiment constraints are utilized to ensure that the duplication of an agent or object results in a distinct new entity rather than a seamless, ambiguous clone.

#### The Formal Truth Hierarchy

To resolve conflicts when multiple sources assert different values for the same attribute, the Lens implements a weighted truth hierarchy:

$$T(v) = \frac{\sum_{s \in S(v)} w(s)}{\sum_{s \in S(O)} w(s)}$$

Where T(v) is the confidence in value v, w(s) is the weight of source s, and S(O) is the set of all sources asserting values for object O.

| Authority Tier | Source Type | Authority Domain | Conflict Resolution Policy |
|---|---|---|---|
| **Tier 1 (Highest)** | Box Engine | Physics, Occupancy, Collision | Absolute authority on spatial and mechanical facts |
| **Tier 1 (Highest)** | Canonical Ref | Base Material Constants, Logic Rules | Overrides any dynamic assertion on core properties |
| **Tier 2 (Privileged)** | Player Input | Intent, Social Contract, Ownership | Overrides Spark for narrative ownership |
| **Tier 3 (Generative)** | Spark Generator | Semantic Tags, Narrative Flair, Details | Subservient to Tier 1 and Tier 2 constraints |
| **Tier 4 (Estimated)** | Lens Defaulting | Missing Data Infilling | Placeholder; superseded by any Tier 1-3 assertion |

#### Conflict Resolution and Source Dependency

The Lens must account for source dependency, where one source may copy information from another, potentially inflating the confidence of a false value. In the context of Spark and Box, dependency analysis is simplified by the directional flow of data. Spark may generate a fact based on a Box-derived observation, but the Lens marks the Box observation as the primary ancestor.

When Spark asserts a fact X and later asserts Y, the Lens applies a **temporal recency bias** unless X was marked as a "Static" property. If Spark asserts a fact that contradicts a Tier 1 (Box) fact — such as asserting a door is "open" when Box has resolved a "jammed" state — the Lens rejects the Spark assertion and triggers a **synchronization event** to Spark, forcing the narrative to adapt to the mechanical reality.

---

### Finding 2: Canonical Identity and Object Lifecycle Management

A robust identification scheme is necessary to maintain referential integrity across simulation sessions and complex physical transformations such as object fragmentation or merging. The Lens implements an Identity Lifecycle Management (ILM) framework.

#### The Generational Unique Identifier (GUID)

The Lens employs a Generational GUID that encodes metadata regarding the object's origin and structural version:

```
GUID = {Epoch, SourceID, Sequence, Generation}
```

- **Epoch:** Represents the simulation session start time
- **SourceID:** Identifies the engine or process that initiated the creation
- **Sequence:** A unique integer within the creation batch
- **Generation:** An incrementing counter that tracks structural shifts (e.g., splitting into pieces)

This allows the system to distinguish between a "Chair" and a "Chair Leg" while maintaining a traceable link between the two.

#### Object Lifecycle State Machine (JML Paradigm)

The lifecycle of an object is managed through the **Joiner-Mover-Leaver (JML) paradigm**, adapted for a mechanical simulation environment:

1. **Creation (Joiner):** A new identity is established. The Lens validates the base mechanical profile against canonical templates. If Spark creates an object, it must provide a minimum set of "Narrative Tags" that the Lens then uses to fetch mechanical defaults.

2. **State Management (Mover):** As the simulation progresses, the object's dynamic attributes (position, health) are updated. The GUID remains stable, but the internal version number increments.

3. **Transformation (Split/Merge):**
   - **Split:** When a table breaks into debris, the parent GUID is marked as "Deactivated/Parent." New GUIDs are created for the debris pieces. Each child GUID contains a `parent_id` reference to the original table, ensuring referential integrity.
   - **Merge:** When two objects are joined (e.g., a rider mounting a horse), a composite entity may be created or a "Parent-Child" relationship established in the hierarchy.

4. **Deactivation (Leaver):** When an object is destroyed or removed from the active scene, its GUID is moved to a "Historical" index. This prevents "ghost accounts" or orphaned references from lingering in the active spatial index.

#### Hierarchical Relationships and Sub-objects

The Lens utilizes a `hierarchyid` data type to represent part-whole relationships efficiently. This allows the system to store hierarchical data in a compact format while supporting fast subtree queries. For example, a "Building" object can have children "Floor," "Room," and "Wall." A query to "Find all objects within Building B" can be resolved using a depth-first search on the `hierarchyid` index, which colocates children with their parents in the physical storage layer.

---

### Finding 3: Schema Design for High-Frequency Mechanical Queries

The Lens must serve exact answers to Box queries with **single-digit millisecond latency**. The recommended architecture is a **hybrid model** combining a normalized relational core with denormalized JSON profile payloads.

#### The Recommended Hybrid Schema

The schema separates "Hot" spatial and identification data from "Cold" narrative metadata:

| Table Name | Storage Format | Primary Columns | Query Optimization |
|---|---|---|---|
| **Active_Entities** | Relational (Fixed) | GUID, ClassID, TemplateID | Primary key index for rapid lookup |
| **Spatial_Index** | Quadtree / R-Tree | GUID, X, Y, Z, AABB_Min, AABB_Max | Optimized for "What is near P?" |
| **Mechanical_Profile** | Denormalized JSON | GUID, Profile_Blob, Last_Updated | Pre-calculated profiles for Box |
| **State_Log** | Append-Only (Event) | EventID, GUID, Tick, Delta_Data | Optimized for sequential write/replay |
| **Narrative_Context** | Document (JSON) | GUID, Tags, History_Blob | Indexed for keyword and semantic search |

#### Spatial Indexing: Quadtree vs. R-Tree

For a dynamic simulation, the Lens employs a **Quadtree** (or Octree for 3D) for the active scene. Quadtrees divide the space into equal subsets, which is computationally simpler for moving entities.

- **Camera Culling:** The Quadtree allows Box to process only the tiles and objects within the relevant area, ignoring distant objects.
- **Collision Detection:** Reduces iterations from O(n²) to O(n log n) by ensuring objects only check for collisions with neighbors in the same subspace.
- **Performance:** In a system with 20-30 dynamic particles, a Quadtree can improve performance by over 1000% compared to brute-force spatial checks.

#### Typical Query Implementation Patterns

The Lens provides specific API endpoints optimized for Box's mechanical requirements:

- **Full Mechanical Profile:** `SELECT Profile_Blob FROM Mechanical_Profile WHERE GUID = ?` — Returns the complete set of physical constants in a single operation, avoiding the N+1 problem.
- **Occupancy Query:** `SELECT GUID FROM Spatial_Index WHERE ST_Intersects(AABB, ?)` — Identifies all objects occupying a specific set of squares or volume.
- **Line of Sight (LOS):** The Lens utilizes a ray-casting algorithm against the spatial index to identify all potential occluders between two points. It then checks the opacity and solidity fields in the Mechanical_Profile of each candidate to determine if the LOS is blocked.

---

### Finding 4: Versioning and Determinism Support

Replayability and auditability are core requirements. The system adopts an **event-sourcing strategy** combined with **periodic state snapshotting**.

#### Event Sourcing and the Append-Only Log

Every state change in the Lens is recorded as an immutable event in an append-only store:

- **Immutability:** Once an event is written, it is never modified, ensuring the integrity of the audit trail.
- **Performance:** Append-only operations eliminate the contention issues common in traditional CRUD operations, improving write scalability.
- **Determinism:** By ensuring that the order of events is strictly preserved, the Lens guarantees that replaying the events will always yield the same final state.

#### Snapshotting Strategy for Low-Latency Replay

Replaying thousands of events is computationally expensive. The Lens takes snapshots at regular intervals (e.g., every 100 ticks):

$$State(T) = Snapshot(T_{last}) + \sum_{i=T_{last}+1}^{T} Event_i$$

When a query for "Object O at Time T" is received, the Lens loads the most recent snapshot prior to T and applies only the subsequent events. The snapshot frequency is **adaptive** — "Hot" aggregates with high transaction volumes are snapshotted more frequently than static environmental objects.

#### Determinism Constraints

To maintain bit-for-bit determinism across different hardware platforms:

- **Fixed-Point Arithmetic:** The simulation avoids floating-point types, which can produce varying results on different CPUs/GPUs due to implementation-defined rounding.
- **Ordered Data Structures:** The Lens avoids hash maps for critical logic paths, preferring sorted dictionaries or arrays to ensure that iteration order is consistent.
- **Fixed Timesteps:** The simulation logic runs at a fixed timestep (e.g., 20Hz), ensuring that the delta-time between updates is not a variable input to the simulation.

---

### Finding 5: The Missing-Data Protocol (JIT Fact Acquisition)

A primary innovation of the Lens is its ability to handle "unknown" data through a reactive, just-in-time (JIT) acquisition protocol.

#### The Fact Acquisition Contract

The protocol follows a strict request-response pattern:

1. **Request (Lens → Spark):** The Lens detects a `MISSING_REQUIRED_FACT`. It sends a structured request to Spark, including the GUID, the specific FieldNames required, and the MechanicalContext (e.g., "The object is currently being hit by a heavy mace").

2. **Generation (Spark):** Spark performs a "Critical Semantic Audit" to ensure the generated data is logically sound. It must return a validated JSON object conforming to a specific schema (e.g., using Pydantic or Zod).

3. **Validation (Lens):** The Lens validates the response. If Spark asserts that a wooden chair has a density of 10,000 kg/m³, the Lens identifies this as a "hallucination" and applies a clipping function or rejects the value in favor of a canonical default.

4. **Storage and Response:** The fact is stored in the Mechanical_Profile with a provenance tag marking it as "Spark-Generated." The Lens then immediately serves the profile to Box.

#### Required Fields and Defaulting Rules per Object Class

| Object Class | Required Fields for Box | Allowed Defaults | Forbidden Defaults |
|---|---|---|---|
| **Furniture** | Material, Weight, Breakage_Threshold | Template-based (Oak, Pine) | Entity GUID |
| **Structure** | Thickness, Solidity, Opacity, Flammability | Industry Standards (Brick, Stone) | Spatial Coordinates |
| **Creature** | HP, Speed, Size, Facing, Strength | Species Averages | Individual Identity |
| **Environment** | Foliage_Density, Ground_Friction | Biome Defaults | Physical Laws |

The defaulting engine uses **"Implicit Inheritance."** If a "Table" object is missing a material fact, the Lens checks if the parent "Tavern_Room" has a defined "Building_Material" (e.g., "Heavy Oak") and inherits that value.

---

### Finding 6: Provenance and Auditability (The Trust Layer)

The provenance layer provides the "Why" behind every value in the Lens. The Lens adopts the **W3C PROV-DM** conceptual model as its basis for provenance tracking.

#### PROV-DM Implementation

The Lens tracks relationships between **Entities** (data points), **Activities** (simulation events), and **Agents** (Spark, Box, or Users):

| Provenance Attribute | Description | Data Example |
|---|---|---|
| `wasGeneratedBy` | The specific activity ID | ACT-772 (Mace Strike) |
| `wasAttributedTo` | The agent responsible | Box_Physics_Module_v1.2 |
| `wasDerivedFrom` | The prior version of the fact | HP: 100 |
| `atTime` | The simulation tick | Tick: 12405 |
| `evidence_link` | A link to the specific event log entry | LOG-UUID-4451 |

#### The explain(GUID, field) Interface

The Lens exposes an `explain()` interface that returns a human-readable and machine-parseable account of a fact's history. This interface queries the Provenance table to construct a "minimal explain payload." This payload avoids contaminating Box with prose but provides Spark with the history it needs to generate "narrative justification" for mechanical events.

---

### Finding 7: Performance Targets and Caching Architecture

The Lens must handle millions of operations per second with predictable single-digit millisecond latencies.

#### Hot-Path Caching and Hardware Optimization

The Lens operates on a decoupled architecture:

- **L1 Cache (CPU Cache):** Fixed-width mechanical constants for active entities are stored in contiguous memory arrays to maximize cache locality and allow for SIMD processing of physics updates.
- **L2 Cache (Shared Memory):** Communication between the Lens and the engines occurs via high-speed shared memory modules using "Ping-Pong" buffers to avoid access conflicts.
- **Invalidation Triggers:**
  - Spatial Invalidation: Triggered when an object's velocity > 0 or a collision is detected
  - Mechanical Invalidation: Triggered by structural change events (damage, temperature change)
  - Narrative Invalidation: Triggered only when Spark explicitly updates a tag; this rarely affects Box's hot path

#### Performance Budget per Simulation Turn

| Operation Category | Target Latency | Expected Volume (per Turn) |
|---|---|---|
| GUID Lookup | < 0.1ms | 10,000 |
| Spatial Proximity Query | < 1.0ms | 1,000 |
| Raycast / LOS | < 2.0ms | 500 |
| Fact Acquisition (JIT) | < 200ms (Async) | < 10 |
| State Snapshot Save | < 5.0ms (Async) | 1 (per 100 turns) |

To meet these targets, the Lens utilizes the `TCP_NODELAY` setting to disable Nagle's algorithm, preventing the buffering of small state-update packets that can cause unexpected 50ms latency spikes.

---

### Finding 8: Implementation Specification and System Invariants

#### The Mutation API (Spark/Box Writes)

- `upsert_fact(guid, field, value, source_token)`: Updates a fact and records provenance
- `declare_object(template_id, metadata)`: Creates a new entity and fetches defaults
- `transform_object(parent_guid, transformation_type, child_data)`: Handles split/merge lifecycles
- `push_event(guid, event_type, delta)`: Records a deterministic event to the append-only log

#### The Query API (Box/Internal Reads)

- `fetch_profile(guid)`: Returns the current Mechanical JSON blob
- `query_spatial(geometry, filter)`: Returns a list of GUIDs matching the spatial predicate
- `get_historical_state(guid, tick)`: Returns the state of an object at a specific point in time
- `explain_fact(guid, field)`: Returns the provenance lineage for a specific attribute

#### System Invariants

The reliability of the Lens is maintained through core invariants validated during every CI cycle:

1. **Ambiguity Invariant:** The Lens shall never return a NULL or UNKNOWN value to Box for a required field. It must return a value or a deterministic default.
2. **Monotonicity Invariant:** No activity shall modify a fact marked as IMMUTABLE once the initial creation transaction is committed.
3. **Referential Integrity Invariant:** No child object shall exist without a valid `parent_id` reference to an active or historical entity.
4. **Determinism Invariant:** Given an identical starting snapshot and event log, the state reconstruction for any tick T must be bit-for-bit identical across all supported platforms.

#### Testing Strategy

Testing includes **"Stress Replays,"** where the system is subjected to high-volume event logs with simulated network imperfections (jitter, packet loss) to ensure that the TCP_NODELAY and actor-model mitigations maintain single-digit millisecond response times under load. By binding logic, data, and environment into an immutable cryptographic tuple, the Lens provides the necessary veracity and performance to serve as the shared memory of a truly next-generation simulation.

---

## Cross-References

- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Lens operational architecture (6 subsystems)
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Trust and authority axioms
- `docs/research/R0_DETERMINISM_CONTRACT.md` — Determinism requirements
- `docs/research/R0_CANONICAL_ID_SCHEMA.md` — Existing canonical ID research
- `docs/schemas/canonical_ids.py` — Canonical ID implementation
