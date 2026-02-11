# Execution Plan — 2026-02-11

**Status:** APPROVED — PO reviewed and approved 2026-02-11
**Author:** Opus (PM)
**Source:** Synthesis of 5 delivered research tracks, codebase survey (2003 tests, 112 source files), doctrine/governance review, PO secondary opinion integration
**Context:** Thunder declared existing roadmap "trash." This plan replaces it as the active execution order based on ground truth.

---

## Project Governance

**Product Owner (PO):** Thunder — Design decisions, implementation vision, research delivery. Does not control coding.
**Project Manager (PM):** Opus — Full PM authority. Work order creation, coding direction, agent coordination, execution management.

PM issues work orders autonomously. PO consulted for design decisions and vision changes only.

---

## Current State Summary

### What Exists (Code — Working)

| Layer | Capability | Tests |
|---|---|---|
| **BOX** | Melee combat: attacks, saves, maneuvers (6 types), AoO, mounted combat, terrain, conditions (16 types), environmental hazards | ~500 |
| **BOX** | Deterministic RNG, event sourcing, state hashing (SHA-256), replay verification (10x) | ~130 |
| **Intent** | Declare→Point→Confirm lifecycle, intent validation, legality checker | ~50 |
| **Campaign** | Persistence, prep pipeline, asset management, archive export/import | ~100 |
| **Narration** | Template-based (55 templates), guardrailed (FREEZE-001, BL-003) | ~80 |
| **Immersion** | Full adapter framework (STT/TTS/Image/Audio) with stubs, attribution tracking, determinism canary | ~250 |
| **SPARK** | Adapter framework (LlamaCpp), model registry, boundary laws (BL-001/002) | ~7 |
| **Runtime** | CLI vertical slice (M1.5), session management, bootstrap, replay | ~150 |
| **Schemas** | 30+ schema files, full data contracts with validation | ~200 |
| **Total** | 112 source files, ~32,400 lines | **2003 passing** |

### What Doesn't Exist (Code — Designed but Not Implemented)

| System | Research Coverage | Code Status |
|---|---|---|
| Geometric engine (cover/LOS/LOE/AoE) | RQ-BOX-001: 13 findings | **Zero code** |
| Lens indexing system | RQ-LENS-001: 8 findings | **Zero code** |
| Spellcasting resolution | Partial (intent schema exists) | **Zero code** |
| Ranged attacks | None | **Zero code** |
| Feats | None | **Zero code** |
| Skills | Schema exists | **Zero code** |
| Real LLM integration | RQ-PERF-001 partial (Grammar Shield) | **Stubs only** |
| Real immersion backends | Adapter framework exists | **Stubs only** |

### Research Track Status

| Track | Status | Key Deliverable |
|---|---|---|
| RQ-BOX-001 (Geometric Engine) | DELIVERED | Bresenham, property masks, AoE rasterization, FSMs, spatial indexing |
| RQ-LENS-001 (Data Indexing) | DELIVERED | Hybrid schema, JIT fact acquisition, PROV-DM provenance, event sourcing |
| RQ-INTERACT-001 (Voice-First) | DELIVERED | ActionIntent schema, ghost confirmation, lean-up map, timing targets |
| RQ-TRUST-001 (Show Your Work) | DELIVERED | STPs, combat receipts, one-way valve, tri-gem modes, PBT harness |
| RQ-PERF-001 (Compute Budgeting) | PARTIAL | MsgPack schema, Grammar Shield, pytest determinism suite |
| RQ-SPARK-001 (Structured Emission) | NOT DELIVERED | Scene Fact Pack schema, prompting patterns, validation loops |
| RQ-NARR-001 (Narrative Balance) | NOT DELIVERED | Allowed output space, truth packet interface, tone control |

---

## Execution Order (7 Steps)

### Step 1: Complete the Box Geometric Engine

**Rationale:** Everything downstream (trust, transparency, narration, Lens queries) depends on Box being able to resolve the full tactical combat that 3.5e demands. You can't generate a Structured Truth Packet for a fireball if Box can't resolve a fireball.

**Work order sequence:**

1. **Geometric engine core** — Uniform grid data structure, PropertyMask (Uint32) on cells and borders, border metadata. This is the data layer that cover/LOS/LOE reads from. (RQ-BOX-001 Findings 1-2, 6-7)

2. **Cover resolution** — Corner-to-corner Bresenham traversal, 4-degree cover table, large creature sweeps (16x16). Integrate with existing terrain_resolver.py cover logic. (RQ-BOX-001 Finding 3)

3. **LOS/LOE** — Height map, 3D voxel traversal, property mask bitwise resolution (Solid/Opaque/Permeable). Distinct LOS vs LOE paths. (RQ-BOX-001 Finding 4)

4. **AoE rasterization** — Burst/cone/line templates, 50% coverage rule, conservative rasterization for lines, pre-computed pattern bitmaps. (RQ-BOX-001 Finding 5)

5. **Ranged attacks** — Distance penalties, cover interaction with ranged, range increments. Currently melee-only.

6. **Reach weapons** — Variable threatened square radius (10ft polearms). Currently hardcoded to 5ft.

7. **Combat Reflexes feat** — Multiple AoO/round. Currently limited to 1. Table-stakes for 3.5e tactical play.

**Decision point:** Profile after sub-step 3 (LOS/LOE). Pure Python with numpy may suffice for 10-20 combatants. C extension needed if targeting 50+ combatants or <10ms pairwise visibility.

---

### Step 2: Build the Core Lens

**Rationale:** The Lens is the data membrane between Spark and Box. It must exist before LLM integration is safe. Without it, Spark writes directly to game state — violating the core doctrine.

**Work order sequence:**

1. **Object property indexing** — Hybrid schema (Active_Entities, Spatial_Index, Mechanical_Profile). MsgPack with integer-key mapping from PERF-001. (RQ-LENS-001 Findings 3, 7; RQ-PERF-001 Finding 1)

2. **JIT Fact Acquisition** — Box→Lens→Spark→Lens→Box protocol for missing data. Pydantic validation middleware. Fallback to DEFAULT_ROOM_TEMPLATES. (RQ-LENS-001 Finding 5; RQ-PERF-001 Finding 2)

3. **Provenance tracking** — W3C PROV-DM implementation. `wasGeneratedBy`, `wasAttributedTo`, `wasDerivedFrom`. Every fact tagged with source tier (Box/Canonical > Player > Spark > Default). (RQ-LENS-001 Finding 6)

4. **Event sourcing integration** — Connect Lens snapshots to Box's existing event log. Adaptive snapshotting per LENS-001 Finding 4. Fixed-point arithmetic for determinism.

5. **Generational GUIDs + JML lifecycle** — Object identity, split/merge handling, hierarchyid for part-whole relationships. (RQ-LENS-001 Finding 2)

---

### Step 3: Begin Spark Integration

**Rationale:** With Box computing real results and Lens indexing world state, LLM integration becomes safe and useful rather than dangerous.

**Work order sequence:**

1. **Real Spark model loading** — Wire up llama-cpp-python or Ollama to existing SparkAdapter framework. Grammar Shield strategy (stop sequences, schema pre-fill, Pydantic validation). Existing M2 governance docs (Spark Swappability) apply here. (RQ-PERF-001 Finding 2)

2. **Structured Truth Packets** — Implement STP schema from TRUST-001. Extend existing event log to include explain packets. Cover, AoE, damage, and die roll STPs. (RQ-TRUST-001 Findings 1-2)

3. **Constrained scene generation** — Spark populates Room Schemas, not prose. Lens validates and indexes. Awaiting RQ-SPARK-001 findings for full Scene Fact Pack schema.

---

### Step 4: First Vertical Slice (Tavern Combat)

**Rationale:** Prove the Box→Lens→Spark pipeline works end-to-end before expanding scope. A single tavern combat encounter exercises geometric resolution, Lens indexing, and Spark narration in a controlled scenario.

**Success criteria:**
- 3-5 combatants in a single-room encounter
- Melee + ranged attacks resolve through geometric engine
- Cover and LOS computed correctly via property masks
- Spark narrates outcomes from STPs (not templates)
- Lens indexes all entities and provides query interface
- Full replay produces identical results
- All existing tests continue to pass

**This step is an explicit gate.** Nothing after Step 4 proceeds until the vertical slice demonstrates correct end-to-end behavior.

---

### Step 5: Spellcasting + Expanded Combat

**Rationale:** With the vertical slice proving the pipeline, add the largest missing rules system. Spellcasting is deferred to here (rather than Step 1) because the vertical slice validates the integration pattern first.

**Work order sequence:**

1. **Spellcasting resolution** — Spell targeting (single/area/self), save effects, damage types, duration tracking, concentration. Largest single gap in the engine.

2. **Narration upgrade** — Replace 55 templates with guarded LLM narration. One-Way Knowledge Valve: Box→STP→Lens→NarrativeBrief→Spark. Existing guardrail framework (FREEZE-001, BL-003) already supports this. (RQ-TRUST-001 Finding 5; awaiting RQ-NARR-001 findings)

3. **Determinism test harness expansion** — Implement the full pytest suite from PERF-001 (`test_determinism_drift`, `test_reproducibility_from_log`, SHA256 Gold Master) covering spellcasting scenarios. (RQ-PERF-001 Finding 3)

---

### Step 6: Full Integration Testing + Performance

**Rationale:** Validate the complete system under realistic combat load before adding polish layers.

**Work order sequence:**

1. **Multi-encounter stress test** — Multiple combat scenarios (dungeon crawl, open field, multi-level), 10-20 combatants, mixed melee/ranged/spell

2. **Performance profiling** — Identify hot paths, validate latency targets (Box query <50ms p95, Lens query <20ms p95, full action resolution <3s p95)

3. **Replay regression suite** — 1000-turn determinism gate, Gold Master recordings, version-to-version replay compatibility

4. **Property-based testing** — "Thousand-Fold Fireball" CI test for geometry edge cases (RQ-TRUST-001 Finding 7)

---

### Step 7: Immersion Integration

**Rationale:** With the core pipeline stable and tested, wire up the real immersion backends to the existing adapter framework.

**Work order sequence:**

1. **Real immersion backends** — TTS/STT/Image generation connected to existing adapter framework (stubs replaced with real implementations)

2. **Voice-first interaction** — Wire RQ-INTERACT-001 findings into intent parsing pipeline

3. **Transparency modes** — Implement Tri-Gem Socket (Ruby/Sapphire/Diamond) on top of STP system

4. **Table-native UX** — Combat receipts, ghost stencils, Judge's Lens (RQ-TRUST-001 Findings 3-4)

---

### Deferred (Not in Steps 1-7)

| Item | Reason | When |
|---|---|---|
| Equipment management, encumbrance | Content completeness, not architectural | Incrementally |
| Skills, feats (beyond Combat Reflexes) | Content completeness | Incrementally |
| Experience, leveling | Content completeness | Incrementally |
| Dialogue, social encounters | Different gameplay mode | After combat is complete |

---

## Open Questions

1. **Python vs C for geometry hot path** — Profile after Step 1 sub-step 3 and decide. Pure Python with numpy may suffice for target scale (10-20 combatants). C extension needed if targeting 50+ combatants or <10ms pairwise visibility.

2. **Remaining research deliveries** — RQ-SPARK-001 (structured fact emission) directly affects Step 3. RQ-NARR-001 (narrative balance) affects Step 5. PM will proceed with available information and integrate findings when delivered.

3. **Existing M2 governance** — M2 Spark Swappability governance docs preserved and applied during Step 3 sub-step 1.

---

## Work Order Tracking

| WO ID | Step | Description | Status | Doc |
|---|---|---|---|---|
| WO-001 | 1.1 | Box Geometric Engine Core | READY FOR DISPATCH | `docs/planning/WO-001_BOX_GEOMETRIC_ENGINE_CORE.md` |
| WO-002 | 1.2 | Cover Resolution | PENDING | — |
| WO-003 | 1.3 | LOS/LOE Resolution | PENDING | — |
| WO-004 | 1.4 | AoE Rasterization | PENDING | — |
| WO-005 | 1.5 | Ranged Attacks | PENDING | — |

---

## Cross-References

- `docs/research/DEEP_RESEARCH_INGESTION_STATUS.md` — Research track status
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Binding architectural axioms
- `docs/governance/M1_UNLOCK_CRITERIA.md` — Existing phase gate model
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Operational architecture
- `KNOWN_TECH_DEBT.md` — Intentional deferrals (do not fix without approval)
