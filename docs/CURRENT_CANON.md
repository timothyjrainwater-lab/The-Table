# CURRENT CANON -- Authoritative Document Index

**Effective Date:** 2026-02-12 (RWO-003: Documentation Canonicalization)
**Author:** Opus (PM)
**Purpose:** A single reference that tells any agent which documents are authoritative, which are historical, and how to resolve conflicts between them.

---

## Primary State Snapshot

**`PROJECT_STATE_DIGEST.md`** (repo root) is the single source of truth for what is implemented, tested, and locked. When any other document contradicts the PSD, the PSD wins.

The PSD is updated at the close of every integrated work order. Its header contains the last-updated timestamp and the current test count.

---

## Document Precedence (Highest to Lowest)

When two documents disagree, the higher-ranked source prevails:

| Rank | Source | Rationale |
|------|--------|-----------|
| 1 | **PROJECT_STATE_DIGEST.md** | Canonical state snapshot, updated every WO integration |
| 2 | **Code + Tests** (`aidm/`, `tests/`) | Ground truth -- if PSD says X but code does Y, file a drift bug |
| 3 | **EXECUTION_PLAN_V2_POST_AUDIT.md** | Active execution plan, approved by PO 2026-02-11 |
| 4 | **README.md** | User-facing documentation (may lag behind PSD) |
| 5 | **PROJECT_COHERENCE_DOCTRINE.md** | Historical governance -- scope boundaries were set in Feb 2025 and some have been superseded by later implementation |

---

## Canonical Document Registry

### Tier 1 -- Authoritative (Current)

These documents reflect the current state of the project and are actively maintained.

| Document | Path | Scope | Notes |
|----------|------|-------|-------|
| Project State Digest (PSD) | `PROJECT_STATE_DIGEST.md` | What is built, test counts, module inventory, governance model | Updated every WO integration. 500-line size gate enforced. |
| Execution Plan v2 | `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` | Active 4-phase plan (Brain, Content Breadth, Session Playability, Playtest) | Approved by PO 2026-02-11. Phases 1-3 delivered. |
| Agent Onboarding Checklist | `AGENT_ONBOARDING_CHECKLIST.md` | Step-by-step reading order for new agents | First file any new agent must read. |
| Agent Development Guidelines | `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards, boundary laws, pitfall avoidance | Binding on all implementation work. |
| Agent Communication Protocol | `AGENT_COMMUNICATION_PROTOCOL.md` | How agents flag concerns, gates, scope creep | Binding on all agent communication. |
| Known Tech Debt | `KNOWN_TECH_DEBT.md` | Intentional deferrals and their rationale | Review before assuming something is a bug. |
| Immersion Boundary Contract | `docs/IMMERSION_BOUNDARY.md` | Scope boundary for `aidm/immersion/` layer | Binding. Defines what immersion may and must never do. |
| Spark/Lens/Box Doctrine | `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` | Binding architectural axioms (5 axioms) | Active. No implementation may violate. |
| AD-001: Authority Resolution Protocol | `docs/decisions/AD-001_AUTHORITY_RESOLUTION_PROTOCOL.md` | NeedFact/WorldPatch protocol. Spark MUST NEVER supply mechanical truth. Authority chain: Box > Canonical > Player > Spark. | Binding. All resolvers must implement NeedFact halt. |
| AD-002: Lens Context Orchestration | `docs/decisions/AD-002_LENS_CONTEXT_ORCHESTRATION.md` | Five-channel PromptPack wire protocol (Truth/Memory/Task/Style/OutputContract). Lens as OS for context. | Binding. Drives PromptPack v1 implementation. |
| AD-003: Self-Sufficiency Resolution | `docs/decisions/AD-003_SELF_SUFFICIENCY_RESOLUTION_POLICY.md` | Policy Default Library + Seeded Deterministic Generator. Self-sufficiency through data, not LLM invention. | Binding. Defines fact resolution chain: Scene > PolicyDefault > Generator > PlayerChoice. |
| AD-004: Mechanical Evidence Gate | `docs/decisions/AD-004_MECHANICAL_EVIDENCE_GATE.md` | No mechanical rule enters Box without local corpus evidence. Three layers: evidence-gated test docstrings, subsystem evidence maps, fail-closed resolution. | Binding. Uses Vault OCR corpus (322 PHB pages, 18 sources). |
| AD-005: Physical Affordance Policy | `docs/decisions/AD-005_PHYSICAL_AFFORDANCE_POLICY.md` | Four-layer inventory architecture (Weight/Container/Gear Affordance/Complication). Declared physical facts for RAW-silent properties. HOUSE_POLICY provenance. | Binding. WO-053/054/055/056 implement Layers 1-3. Layer 4 deferred. |
| AD-006: House Policy Governance Doctrine | `docs/decisions/AD-006_HOUSE_POLICY_GOVERNANCE_DOCTRINE.md` | No-Opaque-DM doctrine. Two authorities only (RAW + House Policy). Template Family Registry (closed at runtime, open across versions). Two-Loop Model. FAIL_CLOSED protocol. | Binding. Governs all House Policy creation and instantiation. |
| Evidence Maps | `docs/evidence/*.md` | Per-subsystem structured evidence tables: mechanic → PHB page → Vault path → test → gaps. | Binding. Each resolver must have a corresponding evidence map. |
| README | `README.md` | User-facing project overview, usage examples | May lag behind PSD on test counts and module listings. |

### Tier 2 -- Governance (Partially Superseded)

These documents established foundational rules but contain specific claims that have been overtaken by later implementation. They remain valuable for architectural intent but must not be treated as ground truth for current state.

| Document | Path | Scope | Supersession Notes |
|----------|------|-------|--------------------|
| Project Coherence Doctrine | `PROJECT_COHERENCE_DOCTRINE.md` | Scope boundaries, architectural constraints (Feb 2025) | See HISTORICAL banner. "Production Voice Integration" listed as out-of-scope, but STT/TTS/Image adapters were implemented under M3 Immersion Layer. Test runtime gate (<5s) predates current scale. Core architectural principles remain binding. |
| Design Layer Adoption Record | `docs/design/DESIGN_LAYER_ADOPTION_RECORD.md` | Formal design freeze record | Design documents are frozen. The freeze itself is current. |

### Tier 3 -- Historical (Superseded)

These documents were authoritative at the time they were written but have been fully superseded by later work. They are preserved for context and provenance only.

| Document | Path | Original Scope | Superseded By |
|----------|------|----------------|---------------|
| Vertical Slice V1 | `VERTICAL_SLICE_V1.md` | Phase 0 execution proof -- 1 scene, 1 monster, 3 turns, no combat resolution | Full combat stack (CP-10 through CP-19), Session Orchestrator (WO-039), multi-room dungeons (P2). See HISTORICAL banner. |
| Execution Plan v1 (7-step) | `docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md` | Original 7-step plan, 26 WOs | Execution Plan v2. Status: CLOSED. |
| Roadmap V3 | `docs/AIDM_EXECUTION_ROADMAP_V3.md` | M0-M4 milestone roadmap | Execution Plan v2. Capability gates remain enforced. |

### Tier 4 -- Reference (Non-Authoritative)

These documents provide useful context but are not sources of truth for project state or scope.

| Document | Path | Purpose |
|----------|------|---------|
| CP Decision Docs | `docs/CP*.md`, `docs/cp18/`, `docs/cp19/`, `docs/cp20/` | Design rationale for individual instruction packets |
| Audit Reports | `docs/AUDIT_REPORT.md`, `docs/AIDM_CORE_RULESET_AUDIT*.md` | Point-in-time audit findings |
| Research Docs | `docs/research/R0_*.md`, `docs/R1_*.md` | Research findings (informational) |
| Research Syntheses | `docs/research/RQ_SPARK_001_SYNTHESIS.md`, `docs/research/RQ_NARR_001_SYNTHESIS.md` | Phase 1 research agent deliverables (Spark Emission Contract v1, Narrative Balance Contract v1) |
| System Audits | `docs/audits/5E_CONTAMINATION_AUDIT.md`, `docs/audits/MECHANICAL_COVERAGE_AUDIT.md`, `docs/audits/SEAM_PROTOCOL_ANALYSIS.md` | Phase 1 audit agent deliverables (5e contamination, mechanical coverage, seam analysis) |
| SKR Design Docs | `docs/skr/SKR-*.md` | Structural Kernel Register designs |
| Doc Drift Ledger | `docs/DOC_DRIFT_LEDGER.md` | Known contradictions and their resolutions |

---

## How to Use This Index

**New agent joining the project:**
1. Read `AGENT_ONBOARDING_CHECKLIST.md` first (it tells you the reading order).
2. Read `PROJECT_STATE_DIGEST.md` to understand what exists.
3. If you encounter a claim in any document that contradicts the PSD, the PSD wins.
4. Check `docs/DOC_DRIFT_LEDGER.md` for known contradictions and their resolutions.
5. If you find a new contradiction, add it to the drift ledger.

**Checking if a feature is in scope:**
1. Check PSD "Locked Systems" -- if it is listed there, it is implemented.
2. Check PSD "Non-Goals" -- if it is listed there, it is explicitly excluded.
3. Check Execution Plan v2 "Future Work Queue" -- if it is listed there, it is planned but not yet implemented.
4. If none of the above, consult the PM before implementing.

**Resolving a document conflict:**
1. Apply the precedence table above (PSD > Code > Exec Plan > README > Doctrine).
2. Log the conflict in `docs/DOC_DRIFT_LEDGER.md`.
3. If the conflict is architectural (violates a doctrine principle), escalate to PM.

---

**This document is maintained by the PM. Updates require explicit authorization.**
