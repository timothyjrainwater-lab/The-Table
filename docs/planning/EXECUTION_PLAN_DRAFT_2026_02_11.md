# Execution Plan Draft — 2026-02-11

**Status:** DRAFT — Awaiting PO review and approval
**Author:** Opus (Acting PM)
**Source:** Synthesis of 5 delivered research tracks, codebase survey (2003 tests, 112 source files), doctrine/governance review
**Context:** Thunder declared existing roadmap "trash." This plan proposes a replacement execution order based on ground truth.

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

## Proposed Execution Order

### Phase 1: Complete the Rules Engine (Box)

**Rationale:** Everything downstream (trust, transparency, narration, Lens queries) depends on Box being able to resolve the full tactical combat that 3.5e demands. You can't generate a Structured Truth Packet for a fireball if Box can't resolve a fireball.

**Priority order:**

1. **Geometric engine core** — Uniform grid data structure, PropertyMask (Uint32) on cells and borders, border metadata. This is the data layer that cover/LOS/LOE reads from. (RQ-BOX-001 Findings 1-2, 6-7)

2. **Cover resolution** — Corner-to-corner Bresenham traversal, 4-degree cover table, large creature sweeps (16x16). Integrate with existing terrain_resolver.py cover logic. (RQ-BOX-001 Finding 3)

3. **LOS/LOE** — Height map, 3D voxel traversal, property mask bitwise resolution (Solid/Opaque/Permeable). Distinct LOS vs LOE paths. (RQ-BOX-001 Finding 4)

4. **AoE rasterization** — Burst/cone/line templates, 50% coverage rule, conservative rasterization for lines, pre-computed pattern bitmaps. (RQ-BOX-001 Finding 5)

5. **Ranged attacks** — Distance penalties, cover interaction with ranged, range increments. Currently melee-only.

6. **Spellcasting resolution** — Spell targeting (single/area/self), save effects, damage types, duration tracking, concentration. Largest single gap in the engine.

7. **Reach weapons** — Variable threatened square radius (10ft polearms). Currently hardcoded to 5ft.

8. **Combat Reflexes feat** — Multiple AoO/round. Currently limited to 1. This feat is table-stakes for 3.5e tactical play.

**Architectural decision required:** Python pure vs. C extension for geometry hot path. The research describes cache-line-aligned SoA with SIMD vectorization. Python with numpy/bitarray may be sufficient for 10-20 combatant scenarios. Decision point: profile after step 3 (cover resolution) and decide whether to drop to C for the inner loop.

---

### Phase 2: Build the Lens

**Rationale:** The Lens is the data membrane between Spark and Box. It must exist before LLM integration is safe. Without it, Spark writes directly to game state — violating the core doctrine.

**Priority order:**

1. **Object property indexing** — Hybrid schema (Active_Entities, Spatial_Index, Mechanical_Profile). MsgPack with integer-key mapping from PERF-001. This is what Box queries for cover/LOS checks. (RQ-LENS-001 Findings 3, 7; RQ-PERF-001 Finding 1)

2. **JIT Fact Acquisition** — Box→Lens→Spark→Lens→Box protocol for missing data. Pydantic validation middleware. Fallback to DEFAULT_ROOM_TEMPLATES. (RQ-LENS-001 Finding 5; RQ-PERF-001 Finding 2)

3. **Provenance tracking** — W3C PROV-DM implementation. `wasGeneratedBy`, `wasAttributedTo`, `wasDerivedFrom`. Every fact tagged with source tier (Box/Canonical > Player > Spark > Default). (RQ-LENS-001 Finding 6)

4. **Event sourcing integration** — Connect Lens snapshots to Box's existing event log. Adaptive snapshotting per LENS-001 Finding 4. Fixed-point arithmetic for determinism.

5. **Generational GUIDs + JML lifecycle** — Object identity, split/merge handling, hierarchyid for part-whole relationships. (RQ-LENS-001 Finding 2)

---

### Phase 3: Spark Integration + Trust Layer

**Rationale:** With Box computing real results and Lens indexing world state, LLM integration becomes safe and useful rather than dangerous.

**Priority order:**

1. **Real Spark model loading** — Wire up llama-cpp-python or Ollama to existing SparkAdapter framework. Grammar Shield strategy (stop sequences, schema pre-fill, Pydantic validation). (RQ-PERF-001 Finding 2)

2. **Structured Truth Packets** — Implement STP schema from TRUST-001. Extend existing event log to include explain packets. Cover, AoE, damage, and die roll STPs. (RQ-TRUST-001 Findings 1-2)

3. **Constrained scene generation** — Spark populates Room Schemas, not prose. Lens validates and indexes. Awaiting RQ-SPARK-001 findings for full Scene Fact Pack schema.

4. **Narration upgrade** — Replace 55 templates with guarded LLM narration. One-Way Knowledge Valve: Box→STP→Lens→NarrativeBrief→Spark. Existing guardrail framework (FREEZE-001, BL-003) already supports this. (RQ-TRUST-001 Finding 5; awaiting RQ-NARR-001 findings)

5. **Determinism test harness** — Implement the pytest suite from PERF-001 (`test_determinism_drift`, `test_reproducibility_from_log`, SHA256 Gold Master). (RQ-PERF-001 Finding 3)

---

### Deferred (Not in Phases 1-3)

| Item | Reason | When |
|---|---|---|
| Real immersion backends (TTS/STT/Image) | Stub framework correct; integration task, not architecture | When game actually runs end-to-end |
| Voice-first interaction (RQ-INTERACT-001) | Intent system already works; voice parsing is frontend | After Phase 3 core is stable |
| Transparency modes (Ruby/Sapphire/Diamond) | UX polish on STP system | After STPs implemented |
| Table-native UX (combat receipts, ghost stencils) | Requires rendering layer | After immersion backends |
| Equipment management, encumbrance | Content completeness, not architectural | Incrementally |
| Skills, feats (beyond Combat Reflexes) | Content completeness | Incrementally |
| Experience, leveling | Content completeness | Incrementally |
| Dialogue, social encounters | Different gameplay mode | After combat is complete |

---

## Open Questions for PO Decision

1. **Python vs C for geometry hot path** — Profile after Phase 1 step 3 and decide. Pure Python with numpy may suffice for target scale (10-20 combatants). C extension needed if targeting 50+ combatants or <10ms pairwise visibility.

2. **Remaining research deliveries** — RQ-SPARK-001 (structured fact emission) directly affects Phase 2/3 design. RQ-NARR-001 (narrative balance) affects Phase 3 step 4. When can these be delivered?

3. **Milestone naming** — The existing M0-M4 structure doesn't map to this plan. Options:
   - Rewrite M0-M4 to match these phases
   - Abandon M-numbering, use phase names (Box Completion, Lens Build, Spark Integration)
   - Keep M-numbering but redefine scope

4. **Existing M2 (Spark Swappability)** — The governance framework for M2 is already complete. It fits inside Phase 3 step 1. Should the existing M2 governance docs be preserved as-is or folded into the new structure?

---

## Cross-References

- `docs/research/DEEP_RESEARCH_INGESTION_STATUS.md` — Research track status
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Binding architectural axioms
- `docs/governance/M1_UNLOCK_CRITERIA.md` — Existing phase gate model
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Operational architecture
- `KNOWN_TECH_DEBT.md` — Intentional deferrals (do not fix without approval)
