# PM Synthesis Memo — WO-RESEARCH-SPRINT-001 Findings

**From:** PM (Aegis)
**To:** Operator (Thunder)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Status:** SYNTHESIS COMPLETE — SUCCESS CRITERION 3 MET
**Scope:** Architectural roadmap derived from all 11 research deliverables

---

## 1. Executive Summary

All 11 research questions have been answered. The findings converge on a single architectural conclusion: **the bone layer is sound, the skin layer is structurally ready but operationally disconnected, and the bridge between them has 5 critical gaps.**

The engine is content-independent by construction (RQ-001). The event log uses bone-layer IDs exclusively (RQ-008). The presentation semantics schema is well-designed (RQ-002, RQ-003). Hardware tiering does not affect mechanical outcomes (RQ-009, RQ-011). Cross-world communication is architecturally possible via the content_id layer (RQ-010). Versioning infrastructure is absent but the replay model is inherently safe for Type A fixes (RQ-007).

The single highest-impact finding across the entire sprint: **GAP-B-001 — `NarrativeBrief.presentation_semantics` is always `None` at runtime.** Three independent research agents (RQ-002, RQ-003, RQ-005) converged on this same conclusion. It is ~10 lines of code. It unlocks all downstream Layer B consumption.

---

## 2. Cross-Cutting Findings (Ranked by Impact)

### Finding 1: GAP-B-001 Is the Single Highest-Impact Fix
- **Source:** RQ-002, RQ-003, RQ-005 (independent convergence)
- **What:** The Lens assembler does not populate `NarrativeBrief.presentation_semantics` from the `PresentationSemanticsRegistry`. It is always `None`.
- **Impact:** All Layer B data (delivery mode, staging, VFX tags, scale, contraindications) is invisible to Spark at runtime. Narration quality, containment validation, tonal consistency, and player trust are all degraded.
- **Fix:** ~10 lines in `assemble_narrative_brief()`.
- **PM Recommendation:** Immediate WO. Highest priority, lowest risk.

### Finding 2: NarrativeBrief Width Is the Primary Schema Bottleneck
- **Source:** RQ-003 (stress test: 9 of 20 FAIL)
- **What:** NarrativeBrief is a single-event, single-target, single-condition pipe. D&D 3.5e produces compound moments (AoE with differential saves, AoO during bull rush, sneak attack on flanked+grappled target).
- **Impact:** 9 of 20 stress-test scenarios cannot be represented. Narration either contradicts or omits critical detail.
- **Fix:** Schema extensions — `additional_targets`, `causal_chain_id`, `active_conditions`, spatial context flags.
- **PM Recommendation:** P1 WO after GAP-B-001. Medium effort, high impact on narration fidelity.

### Finding 3: Content Independence Is Architecturally Validated
- **Source:** RQ-001 (47 deps audited), RQ-004 (containment), RQ-008 (event log)
- **What:** Zero resolver modules contain game-system branching. All 47 D&D dependencies are data-driven. Event sourcing uses bone-layer IDs exclusively. Containment principles are universal.
- **Impact:** The extraction path from "D&D 3.5e engine" to "content-independent engine" is data migration, not refactoring. 0 resolver modules need logic changes. ~285 vocabulary artifacts need migration. 14 universal containment rules survive any world.
- **PM Recommendation:** This validates the entire multi-world vision. No immediate WO — this is a future milestone (post-MVP).

### Finding 4: The `ui_description` Gap Is the MVP Bottleneck
- **Source:** RQ-002, RQ-006
- **What:** `ui_description` in the presentation semantics is always `None`. Without it, rulebooks are empty, ability tooltips are blank, and worlds feel like spreadsheets. The text generation pipeline is a stub producing D&D parameter dumps.
- **Impact:** The dividing line between "engine" and "game."
- **Fix:** Hybrid Strategy C — deterministic core for enum fields + optional LLM creative layer for `ui_description` and `residue`. Template families defined (5 archetypes). Progressive revelation via discovery tiers.
- **PM Recommendation:** P2 WO — depends on GAP-B-001 and NarrativeBrief width fixes. This is the quality ceiling for the presentation layer.

### Finding 5: Versioning Must Be Designed Before Any World Ships
- **Source:** RQ-007
- **What:** Zero version-tracking infrastructure exists. A campaign created under engine 0.1.0 loads silently under 0.2.0 with no warning. If reducer logic changed, replay silently diverges.
- **Impact:** Any world distributed without version gates is a ticking time bomb for save corruption.
- **Fix:** 3 minimum viable changes: (1) validate `engine_version` on campaign load, (2) add `bone_engine_version` to WorldState (with hash-safe default), (3) add `event_schema_version` to Event.
- **Key Insight:** All 30 WRONG verdicts are Type A (bug fixes). Events record results, not formulas. Type A fixes do NOT alter replay. The entire fix sprint can ship as PATCH 0.1.1 with zero migration.
- **PM Recommendation:** P1 WO. Must land before any world bundle is distributed, even internally.

### Finding 6: Hardware Tiering Is Mechanical-Safe
- **Source:** RQ-009 (voice latency), RQ-011 (component modularity)
- **What:** Atmospheric components (STT, TTS, narration, image) degrade gracefully across hardware tiers without affecting mechanical outcomes. The `SPARK_SWAPPABLE_INVARIANT` holds. STT dominates 50-80% of voice pipeline latency. Tier 0 cannot reliably hit conversational pace.
- **Impact:** A $300 laptop and a $3,000 workstation produce identical mechanical outcomes. The workstation gets better narration, voice quality, and images.
- **Gaps:** RNG has no Protocol interface (P0 for modularity). Pathfinding and AoE geometry are monolithic (P1). 6 swappability gaps total.
- **PM Recommendation:** RNG Protocol extraction is P1 (mechanical-critical). Other modularity gaps are P2-P3.

---

## 3. Architectural Changes Needed

### 3.1 Immediate (Unblocks Everything Downstream)

| ID | Change | Source | Effort | Risk |
|----|--------|--------|--------|------|
| **ARCH-001** | Populate `NarrativeBrief.presentation_semantics` from registry | RQ-002/003/005 | ~10 lines | LOW |
| **ARCH-002** | Widen NarrativeBrief: multi-target + causal chain + conditions | RQ-003 | Medium | MEDIUM |
| **ARCH-003** | Add `TruthChannel` fields for Layer B serialization to Spark | RQ-003 | Low | LOW |

### 3.2 Foundation (Before Any External Distribution)

| ID | Change | Source | Effort | Risk |
|----|--------|--------|--------|------|
| **ARCH-004** | Campaign load version gate (validate `engine_version`) | RQ-007 | Low | LOW |
| **ARCH-005** | `event_schema_version` field on Event (default "1") | RQ-007 | Low | LOW |
| **ARCH-006** | EventLog JSONL metadata header (engine version) | RQ-007 | Low | LOW |
| **ARCH-007** | Version source of truth (`aidm/version.py` or `__init__`) | RQ-007 | Low | LOW |
| **ARCH-008** | Compile-time validation pass (CT-001/002/003) | RQ-005 | Low-Medium | LOW |
| **ARCH-009** | `RNGProvider` Protocol extraction | RQ-011 | Medium | MEDIUM |

### 3.3 Quality Layer (MVP Polish)

| ID | Change | Source | Effort | Risk |
|----|--------|--------|--------|------|
| **ARCH-010** | `NarrationValidator` (RV-001/002/008 — hit/miss, defeat, save) | RQ-005 | Medium | LOW |
| **ARCH-011** | `ui_description` generation pipeline (template families) | RQ-002/006 | HIGH | MEDIUM |
| **ARCH-012** | Rulebook text generation (5 archetype templates) | RQ-006 | HIGH | MEDIUM |
| **ARCH-013** | Sentence-boundary TTS chunking (TD-023 fix) | RQ-009 | ~200 lines | LOW |

### 3.4 Experience Layer (Post-MVP)

| ID | Change | Source | Effort | Risk |
|----|--------|--------|--------|------|
| **ARCH-014** | Transparency Gem renderer (FilteredSTP → player) | RQ-005 | Medium | LOW |
| **ARCH-015** | Skin preset gallery + VocabularyRegistry swap | RQ-008 | Medium | LOW |
| **ARCH-016** | Mechanical fingerprint computation (compile-time) | RQ-010 | Low | LOW |
| **ARCH-017** | Shareable world bundle format | RQ-010 | Low-Medium | LOW |
| **ARCH-018** | Containment vocabulary parameterization (~285 artifacts) | RQ-004 | HIGH | MEDIUM |

---

## 4. Schema Extensions Needed

| Schema | Extension | Source |
|--------|-----------|--------|
| `NarrativeBrief` | `additional_targets: tuple`, `causal_chain_id: Optional[str]`, `chain_position: int`, `active_conditions: tuple`, `actor_conditions: tuple`, `is_flanking: bool`, `has_cover: bool`, `is_aoo: bool`, `is_readied: bool` | RQ-003 |
| `Event` | `event_schema_version: str = "1"` | RQ-007 |
| `RuleTextSlots` | `usage_constraints`, `interaction_notes`, `mechanical_summary_vague` | RQ-006 |
| `RuleEntry` | `discovery_text` (per-tier text variants) | RQ-006 |
| `VocabularyEntry` | `fingerprint: Optional[str]` | RQ-010 |
| `AdapterCapability` | New frozen dataclass (adapter metadata) | RQ-011 |

---

## 5. Updated Roadmap — Four Horizons

### Horizon 0: Gate Lift (IMMEDIATE — before RED block lift)
**Goal:** Ship version 0.1.1 (all 30 bug fixes) with minimum version safety.

| WO | Description | Deps | Effort |
|----|-------------|------|--------|
| WO-GAP-B-001 | Connect Layer B to pipeline (~10 lines) | None | LOW |
| WO-VERSION-MVP | 3 minimum viable version changes (campaign gate, event schema version, version source of truth) | None | LOW |
| Governance session | 6 CE items + Rule 22 + relay convention | None | LOW |

**Gate criterion:** GAP-B-001 fixed + version MVP landed + governance session complete → Operator lifts RED block.

### Horizon 1: Narration Fidelity (Next Sprint)
**Goal:** NarrativeBrief can represent real D&D combat. Narration cannot contradict mechanical truth.

| WO | Description | Deps | Effort |
|----|-------------|------|--------|
| WO-BRIEF-WIDTH | NarrativeBrief schema extension (multi-target, causal chains, conditions) | GAP-B-001 | MEDIUM |
| WO-NARRATION-VALIDATOR | NarrationValidator P0 rules (hit/miss, defeat, save — RV-001/002/008) | GAP-B-001 | MEDIUM |
| WO-COMPILE-VALIDATE | Compile-time Layer A vs Layer B cross-validation (CT-001/002/003) | None | LOW-MEDIUM |
| WO-TTS-CHUNKING | Sentence-boundary TTS chunking (TD-023 fix, ~200 lines) | None | LOW |
| WO-RNG-PROTOCOL | RNGProvider Protocol extraction | None | MEDIUM |
| WO-WEAPON-PLUMBING-001 | is_ranged + disarm mods + sunder grip (existing) | RED block lift | MEDIUM |

### Horizon 2: World Quality (Following Sprint)
**Goal:** A compiled world feels like a game, not a spreadsheet.

| WO | Description | Deps | Effort |
|----|-------------|------|--------|
| WO-RULEBOOK-GEN | Template-based rulebook text generation (5 archetype families) | GAP-B-001 | HIGH |
| WO-UI-DESC | `ui_description` generation pipeline (deterministic + optional LLM) | GAP-B-001, RULEBOOK-GEN | HIGH |
| WO-DISCOVERY-TIERS | Progressive revelation (5 ability knowledge tiers) | RULEBOOK-GEN | MEDIUM |
| WO-NARRATION-VALIDATOR-P1 | Remaining runtime validation rules (RV-003 through RV-007) | WO-NARRATION-VALIDATOR | MEDIUM |
| WO-PATHFIND-PROTOCOL | PathfindingEngine + AoEGeometry Protocol extraction | None | MEDIUM |
| WO-VERSION-FULL | Full version safety (YAML contracts, JSONL header, replay --version-check) | WO-VERSION-MVP | MEDIUM |
| WO-CONTAIN-PARAM | Containment vocabulary parameterization (GrammarShield + ContradictionChecker) | None | HIGH |

### Horizon 3: Experience + Community (Future Milestone)
**Goal:** Players can verify, customize, and share.

| WO Cluster | Description | Deps | Effort |
|------------|-------------|------|--------|
| Transparency Gem | FilteredSTP renderer + player-facing audit UI | H1 complete | MEDIUM |
| Crystal Ball | On-demand mechanical drill-down for any narration moment | Transparency Gem | HIGH |
| Skin Gallery | Curated preset selector + VocabularyRegistry swap | H2 complete | MEDIUM |
| Community Tools | Mechanical fingerprints + shareable bundles + cross-world comparison | H2 complete | HIGH |
| Replay Journal | Post-session narration-to-mechanics aligned review | Transparency Gem + narration persistence | HIGH |
| Tome Annotations | Rulebook live history (RuleEntry-to-EngineResult index) | Transparency Gem | MEDIUM |

---

## 6. Quality Gates for World Compiler

Derived from RQ-002, RQ-005, RQ-006:

| Gate | Check | Blocks |
|------|-------|--------|
| **QG-1** | All `content_id` entries have non-None `ui_description` | World release |
| **QG-2** | Compile-time validation pass (CT-001 through CT-007) produces 0 FAIL results | World compilation |
| **QG-3** | All abilities with combat_role_tags have matching presentation semantics entries | World compilation |
| **QG-4** | Vocabulary coverage ≥ 100% (every content_id in content pack has a VocabularyEntry) | World release |
| **QG-5** | Shareable bundle generation succeeds and bundle validates against schema | World release |
| **QG-6** | Version stamp present in world metadata (engine version, schema version, compiler version) | World compilation |

---

## 7. Versioning and Patch Management Policy

Derived from RQ-007:

### Semantic Versioning
- **MAJOR** = Type C (schema-breaking). Old saves cannot load without migration.
- **MINOR** = Type B (behavior-changing). Old saves load, but game behavior differs. HARD STOP + options.
- **PATCH** = Type A (backward-compatible bug fixes). Warn and proceed.

### Immediate Decision
All 30 WRONG verdicts are Type A. The entire fix sprint ships as **PATCH 0.1.0 → 0.1.1**. No migration required. Events record results, not formulas — replay is safe.

### Policy Rules
1. Every version bump gets a YAML version contract document in `docs/versions/`.
2. Campaign load MUST compare `engine_version` to running engine version.
3. Type B changes require explicit user opt-in (HARD STOP with options: ARCHIVE / RESTART / MIGRATE).
4. Type C changes require migration tooling before shipping.
5. The "events record results" invariant is DOCTRINE — never store formulas in events.

---

## 8. Component Modularity and Hardware Tiering Strategy

Derived from RQ-009, RQ-011:

### Atmospheric Components (Swap-Ready Today)
| Component | Tier 0 | Tier 1 | Tier 2 |
|-----------|--------|--------|--------|
| STT | Keyboard input | Whisper small.en (CPU) | Whisper large-v3 (GPU) |
| TTS | Text display | Kokoro (CPU) | Chatterbox (GPU) |
| Image | Stub/none | Pre-generated library | SDXL (GPU) |
| Narration | Templates | 3B LLM (CPU) | 7-14B LLM (GPU) |

### Mechanical Components (Need Protocol Extraction)
| Component | Priority | Status |
|-----------|----------|--------|
| RNG | P0 | Monolithic, no Protocol |
| Pathfinding | P1 | Embedded in targeting |
| AoE Geometry | P1 | Embedded in targeting |

### Cardinal Rule
`SPARK_SWAPPABLE_INVARIANT`: All tiers produce IDENTICAL mechanical outcomes. Only sensory presentation differs.

### Voice Loop Feasibility
- Tier 0: Cannot reliably hit conversational pace (3-13s range).
- Tier 1+: Achievable with streaming TTS + template narration (1.7-5.5s perceived).
- STT is the irreducible bottleneck (50-80% of total pipeline time).

---

## 9. PM Decisions

### 9.1 GAP-B-001 Gets Its Own WO
Not bundled with anything. Highest impact, lowest risk, lowest effort. Ships immediately.

### 9.2 Version MVP Is Gate-Lift Prerequisite
The engine should not leave the RED block without knowing how to identify itself. Three minimal changes land before gate lift.

### 9.3 Horizons Are Sequential, Not Parallel
Each Horizon depends on the previous. No skipping. H0 → H1 → H2 → H3.

### 9.4 Content Independence Is Deferred
RQ-001 validates the architecture. RQ-004 maps the migration. But the extraction work (~285 vocabulary artifacts, 6 WOs, 9-13 days) is not on the critical path for the D&D 3.5e product. It belongs in a future milestone when multi-world support is prioritized.

### 9.5 Dynamic Skin Swapping Is Free Architecture
RQ-008 confirms the three-layer architecture already supports multi-skin. MVP approach: Curated Preset Selector at session boundary (Approach D). No core re-engineering required. This is a Horizon 3 UX feature, not an architectural change.

### 9.6 Community Tools Are Horizon 3
RQ-010's mechanical fingerprints, shareable bundles, and cross-world tools are valuable but depend on a functioning presentation layer (Horizons 1-2). They are deferred to Horizon 3.

---

## 10. Recommended Immediate Actions

1. **PM drafts WO-GAP-B-001** — ~10 lines, highest impact fix. Immediate dispatch.
2. **PM drafts WO-VERSION-MVP** — 3 minimum viable version changes. Gate-lift prerequisite.
3. **PM drafts Governance Session WO** — 6 CE items + Rule 22 + relay convention. Bundled.
4. **Operator dispatches all three** (parallel-safe).
5. **On completion:** Operator lifts RED block. Roadmap is now H0 → H1 → H2 → H3 as specified above.

---

## 11. Completion Report Response

This memo fulfills success criterion #3 from WO-RESEARCH-SPRINT-001:

| Criterion | Status |
|-----------|--------|
| 1. All 11 deliverables exist in `docs/research/` | **MET** |
| 2. Each deliverable contains concrete recommendations | **MET** |
| 3. PM has reviewed and produced synthesis memo | **MET** (this document) |

**WO-RESEARCH-SPRINT-001 is now COMPLETE.**

---

## Appendix A: Research Deliverable Summary (All 11)

| RQ | Title | Core Answer |
|----|-------|-------------|
| 001 | IP Extraction Audit | 0 resolver logic changes needed. 47 deps all data-driven. Extraction is migration, not refactoring. |
| 002 | Skin Quality Assurance | Hybrid Strategy C (deterministic + optional LLM). `ui_description` is the critical gap. |
| 003 | Skin Coherence Stress Test | 9/20 scenarios FAIL. Compound events break, not content novelty. GAP-B-001 is ~10 lines. |
| 004 | Spark Containment Audit | 14 universal rules survive any world. ~285 vocab artifacts need migration. Principles anchor, vocabulary is pattern set. |
| 005 | Content Trust Verification | 5 gaps in verification bridge. 7 compile-time + 8 runtime validation rules. "The bone cannot lie." |
| 006 | Rulebook Generation Quality | Text pipeline is a stub. ~65% deterministic, ~20% templated, ~15% creative. Schema supports it. |
| 007 | Bone Versioning | Zero version infrastructure. 3 minimum viable changes defined. Type A fixes don't alter replay (events store results). |
| 008 | Dynamic Skin Swapping | Architecture inherently multi-skin. Event log uses bone-layer IDs. VocabularyRegistry swap = skin change. |
| 009 | Voice Loop Latency | STT dominates 50-80%. Tier 1+ achievable with streaming TTS. Tier 0 marginal. |
| 010 | Community Mechanical Literacy | content_id as universal translator. Mechanical fingerprints for cross-world recognition. Shareable bundle format defined. |
| 011 | Component Modularity | 6 atmospheric adapters swap-ready. 6 mechanical gaps (RNG is P0). All tiers produce identical mechanical outcomes. |

---

---

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** This memo was authored by the PM, not a builder. PM-authored memos are not subject to the same three-pass debrief protocol, but PMIH-004 enforces the retrospective section on all MEMO-prefixed files regardless of author. The enforcement is correct — it catches this case — but the PM may not be aware of the requirement since it's documented in builder-facing governance docs.

- **Process feedback:** The research sprint produced 11 deliverables across multiple builder sessions, then the PM synthesized them into a 4-Horizon roadmap. The synthesis-then-roadmap pattern is effective: raw findings → PM judgment → prioritized action plan. The WO structure (dispatch → builder execution → completion report → PM synthesis) worked as designed.

- **Methodology:** The convergence of three independent research agents (RQ-002, RQ-003, RQ-005) on GAP-B-001 as the single highest-impact fix is a strong signal. Independent confirmation from parallel agents is the methodology's strongest validation pattern.

- **Concerns:** The synthesis memo is 300+ lines. That's large for a PM-authored document that the Operator needs to review. The relay block convention helps (Operator gets a one-liner), but when the Operator does read the full document, the length may exceed comfortable review scope.

---

*WO-RESEARCH-SPRINT-001 synthesis complete. The road is mapped. Awaiting Operator action on WO drafting and gate lift.*
