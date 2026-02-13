# RQ-BOX-001: Grid-Based Geometric Engine

**Research Track:** 1 of 7
**Domain:** Box (Deterministic Engine)
**Status:** FINDINGS RECEIVED
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

### Preamble

The development of a robust computational model for discrete geometric reasoning on a 5-foot grid requires a fundamental shift away from the probabilistic and continuous methods common in real-time physics engines. To achieve deterministic, exact resolution based on the D&D 3.5e "Rules as Written" (RAW) framework, a system must prioritize geometric truth over visual realism, ensuring that every calculation for cover, line of sight (LOS), and line of effect (LOE) is mathematically absolute and reproducible. This model integrates high-performance data-oriented architecture with sophisticated spatial indexing and discrete algorithmic traversal to manage complex battlefield metadata, including height, size, material, and facing.

---

### Finding 1: Data-Oriented Design and Memory Locality

The efficiency of a grid-based reasoning engine is inextricably linked to how data is structured in physical memory. Traditional object-oriented design (OOD) paradigms suffer from significant performance degradation due to "cache misses" when the system must perform iterative sweeps over thousands of battlefield cells. Modern CPUs operate significantly faster than system RAM, meaning the time spent waiting for data to be retrieved from main memory — the "memory wall" — is the primary bottleneck in rule resolution.

#### Cache Hierarchies and Line Alignment

Data-oriented design (DOD) optimizes performance by organizing data according to its usage patterns rather than its conceptual relationships. CPUs retrieve data from RAM in fixed-size "cache lines," typically 64 bytes. When the system accesses a specific metadata field, the entire cache line is pulled into the L1 cache. If subsequent operations require data on the same cache line, a "cache hit" occurs, resulting in processing speeds up to 50x faster than a "cache miss."

| Memory Level | Relative Latency | Capacity (Typical) | Design Goal |
|---|---|---|---|
| L1 Cache | 1-4 cycles | 32-128 KB | Instant access for hot loops |
| L2 Cache | 10-12 cycles | 256 KB - 1 MB | Buffer for L1 misses |
| L3 Cache | 30-40 cycles | 4-32 MB | Shared across cores |
| Main RAM | 150-300 cycles | 8-128 GB | Bulk data storage |

The model achieves this efficiency through a **Structure of Arrays (SoA)** memory layout. Instead of storing position, height, and health together in per-object classes (scattered across the heap), the system maintains separate, contiguous arrays for Heights, MaterialMasks, and Positions. When the LOS system iterates through the battlefield, it reads only from the Heights array, ensuring every byte pulled into the cache line is utilized.

#### Entity-Component-System (ECS) as Macro-Architecture

The model utilizes the **ECS pattern** to manage battlefield metadata:

- **Entity:** A simple unique integer identifier (UID) acting as an index into component arrays
- **Component:** Plain Old Data (POD) structures containing specific metadata facets
- **System:** Deterministic functions that transform data by iterating over entities with specific component signatures

This decomposition allows environmental changes as simple metadata mutations. If a "Wall" is destroyed, the DestructionSystem merely updates the corresponding indices in the Opacity_Mask and Solid_Mask arrays, immediately altering the geometric properties of the grid without complex object destruction logic.

---

### Finding 2: Discrete Metadata Representation

Every battlefield element must possess physical metadata defining its interaction with the 5-foot grid. This metadata is stored as "Blittable" data — types with identical representation in memory and on disk — facilitating rapid serialization for turn-based state snapshots.

#### Physical Metadata Components

| Component | Metadata Field | Data Type | RAW 3.5e Relevance |
|---|---|---|---|
| Transform | GridCoord | Vector3Int | Snap-to-grid position (X, Y, Z) |
| Geometry | SizeCategory | Enum8 | Footprint on grid (Fine to Colossal) |
| Spatial | PhysicalHeight | Uint16 | Verticality for LOS and cover checks |
| Orientation | Facing | Uint8 | 45-degree increments for defensive bonuses |
| Material | Hardness | Uint8 | Damage reduction for objects |
| Durability | HitPoints | Uint16 | Structural integrity and state transitions |
| Properties | PropertyMask | Uint32 | Bitmask for LOS, LOE, and movement flags |

#### Facing and Relative Orientation

While standard 3.5e does not strictly enforce facing for all creatures, it is vital for environmental objects like shields, crenellations, or one-way viewing portals. The model encodes facing using 3 bits of a single byte, allowing for 8-way orientation (N, NE, E, SE, S, SW, W, NW). This defines a local coordinate system for the entity, allowing systems to resolve "Front," "Side," and "Rear" sectors based on the relative angle to an attacker.

A character standing behind a 5-foot-wide pillar may have no cover against an attack from their front-right diagonal, but total cover from an attack from their rear. Integrating facing into metadata enables deterministic directional bonus resolution.

---

### Finding 3: Deterministic Cover Resolution

RAW 3.5e cover is determined through a strictly geometric process involving tracing lines between grid corners.

#### The Corner-to-Corner Traversal Algorithm

To resolve cover from a ranged attack, the engine follows a four-step sequence:

1. **Attacker Corner Optimization:** Evaluate all four corners of the attacker's 5-foot square. The attacker chooses the "Optimal Corner" providing the clearest line of sight to the target.

2. **Target Corner Identification:** Identify the four corners of the target's square (or any one square the target occupies if larger than Medium).

3. **Bresenham Ray-Casting:** For each target corner, cast a ray from the optimal attacker corner using a **3D adaptation of the Bresenham line algorithm**, determining every grid cell and grid border the line passes through.

4. **Obstruction Scoring:** Check metadata of every cell and border intersected. An obstruction occurs if a cell contains a solid object, a creature, or a border designated as "Blocking."

#### Cover Resolution Table

| Lines Blocked | Cover Degree | AC Bonus | Reflex Bonus |
|---|---|---|---|
| 0 | No Cover | +0 | +0 |
| 1-2 | Half Cover | +2 | +1 |
| 3 | Three-Quarters | +5 | +2 |
| 4 | Total Cover | Blocked | Blocked |

#### Large Creatures and Reach Attacks

Large or larger creatures occupy multiple grid squares. For ranged attacks, the attacker picks any one square the target occupies. For **melee reach attacks** (e.g., 10-foot polearm), the check runs from all corners of the attacker's square to all corners of the target's square. If any line is blocked, the target has cover.

For Large-vs-Large combat, this involves a comprehensive **16 × 16 geometric sweep**.

---

### Finding 4: Height-Aware Line of Sight (LOS) and Line of Effect (LOE)

The distinction between LOS and LOE is a pillar of 3.5e RAW. LOS determines visibility (subject to concealment), while LOE determines whether a physical force or spell can reach a target.

#### The Height Map and Voxel Traversal System

The model represents verticality using a **discrete height map** — a 2D matrix where each entry H(x,y) stores the top elevation of the highest solid object in that grid cell, supplemented by a "Voxel" layer for objects not filling an entire square (tables, narrow pillars).

Visibility is resolved through 3D grid traversal. Given observer A at height h_A and target B at height range [h_B_min, h_B_max]:

$$Z_{ray}(i) = h_A + i \cdot \frac{h_B - h_A}{D}$$

Where D is the total distance in squares. The ray is blocked if Z_ray(i) ≤ H(x,y) for any solid object.

#### LOE Resolution with Property Masks

LOE is canceled by solid barriers but unaffected by darkness or fog. The critical "One Square Foot Opening" rule: a solid barrier with a hole of at least 1 sq ft does not block LOE for that 5-foot wall segment.

The model handles this through a **32-bit Property_Mask** assigned to grid borders and cells:

- **Bit 0: Solidity** — Set to 1 if physically solid
- **Bit 1: Opacity** — Set to 1 if blocks visual light
- **Bit 2: Permeability** — Set to 1 if allows LOE despite being solid (e.g., grate)

| Barrier Type | Solid | Opaque | Permeable | LOS Result | LOE Result |
|---|---|---|---|---|---|
| Stone Wall | 1 | 1 | 0 | Blocked | Blocked |
| Glass Wall | 1 | 0 | 0 | Clear | Blocked |
| Magical Dark | 0 | 1 | 1 | Blocked | Clear |
| Iron Grate | 1 | 0 | 1 | Clear | Clear |

By using **bitwise AND** operations, the system resolves complex interactions (casting a spell through a glass window in a dark room) in constant time O(1) per grid step.

---

### Finding 5: Discrete AoE Rasterization

Spells and effects in 3.5e are projected onto the grid as a collection of 5-foot squares. The model must "rasterize" geometric shapes into grid units based on the **RAW 50% coverage rule**.

#### Cone Template Generation

The 3.5e cone is an isosceles triangle where width at any point equals distance from origin. The point of origin must be a grid intersection.

The rasterizer determines affected squares by iterating over a candidate bounding box and applying the coverage test: a square is included if at least 50% of its area is enveloped.

For efficiency, the system uses **pre-computed "Pattern Bitmaps"** for common AoE shapes at cardinal and 45-degree angles. For arbitrary angles, the model calculates expected square count N using:

$$N = \frac{L}{5} \cdot \frac{(\frac{L}{5} + 1)}{2}$$

where L is cone length in feet. This serves as an invariant check to ensure rotating a cone does not change its total area.

#### The "Pi = 4" Problem and Discrete Metrics

A 3.5e "Circle" is effectively an octagon due to the 5'/10'/5' diagonal movement cost. The model calculates discrete distance:

$$D_{discrete} = 5 \cdot \max(|\Delta X|, |\Delta Y|) + 5 \cdot \min(|\Delta X|, |\Delta Y|)$$

This ensures area effects perfectly match character movement ranges, maintaining internal consistency.

---

### Finding 6: Deterministic Finite State Machines for Environmental Change

Environmental changes (door destruction, pillar collapse) are handled by **Deterministic Finite State Machines (FSM)**, preventing non-deterministic results from rigid-body physics.

#### Material Hardness and Structural Integrity

Every destructible object possesses Material components (Hardness as damage reduction, HitPoints). RAW specifies objects take half damage from fire/electricity and quarter damage from cold.

| Substance | Hardness | HP per Inch | Typical Thickness | Total HP |
|---|---|---|---|---|
| Glass | 1 | 1 | 1/2 inch | 1 |
| Paper | 0 | 2 | N/A | 1 |
| Wood | 5 | 10 | 3 inches | 30 |
| Stone | 8 | 15 | 4 inches | 60 |
| Iron/Steel | 10 | 30 | 1 inch | 30 |

#### Structural State Transitions

| State | Trigger | Effect |
|---|---|---|
| **Intact** | Default | Full solidity and opacity |
| **Damaged** | HP < 100% | No geometric change; visual indicators |
| **Broken** | HP < 50% | Transitions to "Partial Cover"; Opacity/Solidity masks updated |
| **Destroyed** | HP = 0 | Removed from Static_Hash; replaced by "Debris" entities as Difficult Terrain with full LOS/LOE |

Transition logic is entirely algebraic and deterministic. **"Precomputed Fractures"** define the destroyed state of specific objects as pre-defined metadata templates, avoiding real-time mesh slicing while ensuring consistent tactical consequences.

---

### Finding 7: Spatial Querying and Indexing

Even in a turn-based system, high-performance spatial queries support AI pathfinding, visibility sweeps, and AoE resolution.

#### Monotonic Logical Grids (MLG)

For near-neighbor calculations (e.g., which creatures provide "Soft Cover" along a flight path), the model implements **Monotonic Logical Grids**. These maintain entities in compact arrays where indices correspond to ordinal position along a coordinate axis.

By basing neighbor searches on a "Maximum Index Offset" (N_c) rather than physical distance, the engine permits efficient vectorization. Close objects are indexed via contiguous memory, allowing the system to query all participants for a Fireball resolution by scanning a predictable memory slice.

#### Comparison of Spatial Indexing Techniques

| Algorithm | Query Complexity | Use Case in Model | Determinism |
|---|---|---|---|
| Uniform Grid | O(1) | Direct 5-ft cell access | Absolute |
| Quadtree | O(log N) | Sparse static environment indexing | Recursive |
| Spatial Hash | O(1) amortized | Dynamic creature tracking | Collision-prone |
| Monotonic Grid | O(N_c) | Neighbor/Cover checks | Invariant |
| Implicit Bitmask | O(1) | Instant collision/LOS checks | Bitwise |

The model primarily relies on the **Uniform Grid** for 5-foot cell property lookups and the **Monotonic Logical Grid** for complex multi-entity rule resolution.

---

### Finding 8: The Resolve Loop

Each turn is managed by a centralized "Rule Resolver" ensuring atomic and ordered state changes.

#### Resolve Loop Sequence

1. **Snapshot Phase:** Current state of all component arrays captured as a read-only buffer. Actions resolved in the same tick see the same geometric state, preventing artifacts.

2. **Reasoning Phase:** All LOS, LOE, and Cover queries execute against the snapshot. Purely read-only — can be heavily parallelized across CPU cores.

3. **Resolution Phase:** 3.5e logic (attack rolls, saving throws, damage application) applied to geometric results.

4. **Commit Phase:** Mutations applied to active metadata buffers. Environmental changes written to bitmasks, entity positions updated in spatial hash for next turn.

#### Message Consumer/Producer Pattern

For asynchronous or networked turn entry, the model uses a message consumer/producer pattern. Players produce "Action Messages" (e.g., `Move(UID, TargetGridCoord)`), queued in the system. The Rule Resolver consumes messages in defined priority order (initiative-based) to ensure deterministic outcome regardless of message arrival order.

---

### Finding 9: 3.5e Grid Minutiae

#### Line Spell Rasterization

A Lightning Bolt (100-foot, 5-foot-wide line from caster) uses **"Conservative Rasterization"** — affecting every square where the geometric line intersects any part of the 5-foot unit, not just squares whose center is hit. This preserves "Geometric Truth": a bolt of lightning cannot squeeze between two adjacent enemies.

| Metric | RAW 3.5e Definition | Computational Implementation |
|---|---|---|
| Orthogonal Dist. | 5 feet per square | 1 unit step |
| Diagonal Dist. | 5/10/5 feet | Integer-weighted DDA |
| Line Width | 5 feet | Conservative Rasterization |
| Cone Width | Width = Distance | Flat-bottomed Triangle |
| Burst Radius | OCTAGON (Discrete) | D_discrete ≤ R |

#### 3D Diagonals and Double-Weighted Steps

For 3D diagonals (moving across X, Y, and Z simultaneously), the model applies the "5-ft., 10-ft." rule to all axes. A double-diagonal step (5 ft North, 5 ft East, 5 ft Up) is calculated as a single diagonal step in XY followed by a vertical step, costing 15 feet if it is the second diagonal in a sequence.

This maintains "numerological perfection" — players and AI calculate distances without the Pythagorean theorem, avoiding irrational numbers and floating-point ambiguity.

---

### Finding 10: Advanced Voxelization and Intra-Tile Positioning

#### Intra-Tile Positioning for Small Creatures

Creatures of size Tiny, Diminutive, and Fine take up less than one 5-foot square. The model subdivides each cell into a **3 × 3 sub-grid of 20-inch "Intra-tile" sectors**. This tracks the exact position of a Tiny familiar within a wizard's square, determining if the familiar is "front" (offering cover) or "rear" (protected).

#### The 1-Square-Foot Rule and Border Metadata

Each of the four edges of a 5-foot square possesses its own Property_Mask:

- **Standard Wall:** Border mask Solid=1, Opaque=1
- **Arrow Slit:** Border mask Solid=1, Opaque=0, Permeable=1
- **Open Space:** Border mask Solid=0, Opaque=0

For an arrow slit, the LOE check passes (Permeable bit set), but any cover check calculates **"Improved Cover" (+8 AC)** because the opening is less than 50% of the border width.

#### Hierarchical Bitmasks for Large Dungeons

In complex multi-level dungeons with millions of grid cells, **hierarchical bitmasks** prune the search space for LOS/LOE. A "Root Bitmask" represents a 16 × 16 × 16 cube of grid cells. If a cube is entirely empty, its bit is 0, allowing the Bresenham traverser to skip 4,096 cells in a single operation. Only when a ray enters a non-zero cube does the engine descend into individual cell metadata.

This "Implicit Grid" approach combines O(1) array lookup speed with tree memory efficiency, ensuring large-scale simulations resolve pairwise visibility for all combatants in **under 10 milliseconds**.

---

### Finding 11: Material Bitmasks for Rule Resolution

Each material type has a specific bitmask in the MaterialProperty array:

| Material Bit | Property | Computational Impact |
|---|---|---|
| Bit 0 | Flammable | Object catches fire from energy damage |
| Bit 1 | Fragile | Object takes double damage from impact |
| Bit 2 | Conductive | Electricity damage arcs to adjacent cells |
| Bit 3 | Crystalline | Vulnerable to sonic damage |
| Bit 4 | Dense | Provides Total Cover even if damaged |

When a Fireball affects an area, the MaterialSystem scans the PropertyMask of every cell. If a square contains a "Flammable" object, the system initiates a "Burning" state in that entity's FSM, reducing HP each turn until it transitions to "Destroyed."

---

### Finding 12: Action Grid Computation

The culmination of the model is the **"Action Grid"** — a queryable representation of all valid moves and attacks available to a unit.

#### Dijkstra-Based Action Pathing

During a unit's turn, the model runs a **Dijkstra algorithm** over the grid from the unit's position, incorporating all geometric reasoning in real-time:

- **Movement Cost:** Query Property_Mask for "Difficult Terrain" or "Hazardous" flags
- **Engagement Check:** Identify adjacent squares with hostile entities for "Threatened Area" constraints
- **Attack Reach:** Cast LOS/LOE rays from every reachable square to all potential targets

The result is a comprehensive map pre-calculating every RAW possibility before action selection — not only deterministic but deeply informative for tactical decision-making.

---

### Finding 13: 3D Bresenham Integer Arithmetic

The precise integer arithmetic of the 3D Bresenham algorithm is the key to maintaining determinism. For a line between (x₀, y₀, z₀) and (x₁, y₁, z₁), the engine tracks two error variables, P_y and P_z.

If X is the driving axis (largest Δ):
- Initial P_y = 2Δy - Δx
- Initial P_z = 2Δz - Δx

At each step, if P_y > 0, the Y coordinate is incremented and P_y is reduced by 2Δx; otherwise, P_y is increased by 2Δy. Same logic for P_z.

By using **only addition, subtraction, and bit-shifting** (multiplication by 2), the engine executes with extreme speed and avoids non-deterministic rounding errors inherent in floating-point division. A line of effect resolved on a Windows server yields identical results on an ARM client — critical for deterministic replay.

---

### Conclusion

The computational model successfully translates the qualitative, narrative-driven rules of D&D 3.5e into a rigorous, data-oriented framework. By abandoning continuous physics in favor of discrete geometric reasoning, the system eliminates the "blurriness" of traditional LOS systems where a projectile might pass through a wall due to collision detection error.

The model provides **"Numerological Perfection"** where map control and spacing are the primary drivers of success. Hierarchical bitmasks and monotonic logical grids ensure this detail does not compromise performance, allowing large-scale battles where every creature, object, and environmental effect is a first-class citizen in the resolution loop. This approach prioritizes the **"Geometric Truth"** demanded by turn-based strategy, providing a predictable and deeply tactical battlefield simulation.

---

## Cross-References

- `docs/design/BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md` — Box battlefield specification
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Layer interaction contracts
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Authority model (Box is sole mechanical authority)
