# Global Audit Document Index
## Corpus Intake & Classification

**Audit Session:** GLOBAL-AUDIT-001
**Date:** 2026-02-10
**Status:** ANALYSIS COMPLETE
**CP-001 Status:** ✅ FROZEN (1393 tests passing, TD-001 resolved)

---

## Purpose

This document indexes all design artifacts ingested during the Global Plan Audit to:
1. Establish single source of truth for design corpus
2. Classify documents by authority level and lifecycle stage
3. Map dependencies between design docs and action plans
4. Identify orphaned, duplicate, or conflicting documents

---

## Index Classification Legend

| Symbol | Meaning |
|--------|---------|
| 🟢 | Canonical (frozen, authoritative) |
| 🟡 | Draft (pending approval) |
| 🔵 | Historical (informational, not binding) |
| 🟣 | Inbox (unprocessed design input) |
| ⚫ | Duplicate (superceded or redundant) |

---

## A. Canonical Engineering Documents (Frozen)

### A1. Implementation Baseline
| Document | Location | Status | Last Updated |
|----------|----------|--------|--------------|
| Position Type (CP-001) | `aidm/schemas/position.py` | 🟢 FROZEN | 2026-02-10 |
| Position Tests | `tests/test_position.py` | 🟢 FROZEN | 2026-02-10 |
| CP-001 Design Record | `docs/CP001_POSITION_UNIFICATION_DECISIONS.md` | 🟢 FROZEN | 2026-02-10 |
| Project State Digest | `PROJECT_STATE_DIGEST.md` | 🟢 CANONICAL | 2026-02-10 |
| Known Tech Debt | `KNOWN_TECH_DEBT.md` | 🟢 CANONICAL | 2026-02-10 |

**Summary:** CP-001 completed all 5 phases. Position type uses 1-2-1-2 diagonal distance (PHB p.148) returning feet (not squares). Legacy types deprecated with warnings. 1393 tests passing in 3.46s. TD-001 resolved.

### A2. Design Layer Documents
| Document | Location | Status | Version |
|----------|----------|--------|---------|
| Execution Roadmap | `docs/AIDM_EXECUTION_ROADMAP_V3.md` | 🟢 CANONICAL | v3.1 |
| Action Plan | `docs/AIDM_PROJECT_ACTION_PLAN_V3.md` | 🟡 DRAFT | v3.0 |
| Design Layer Adoption Record | (referenced, not yet read) | 🟢 FROZEN | - |

**Status:** Execution Roadmap v3.1 is CANONICAL. Action Plan v3.0 is DRAFT (pending PM sign-off).

---

## B. Inbox Design Corpus (New Artifacts)

### B1. Architectural Foundation Documents
| Document | Location | Type | Priority |
|----------|----------|------|----------|
| Chronological Design Record | `inbox/extracted/...Design Record...txt` | 🟣 Historical | HIGH |
| Generative Presentation Architecture | `inbox/extracted/...Localization Architecture...txt` | 🟣 Requirements | CRITICAL |
| Secondary Pass Audit Checklist | `inbox/extracted/...Secondary Pass Audit...txt` | 🟣 Checklist | HIGH |

**Summary:** These three docs capture the AIDM's foundational architectural separation (mechanics vs presentation), generative asset strategy, and detailed implementation micro-requirements.

### B2. Feature Specification Documents
| Document | Location | Type | Priority |
|----------|----------|------|----------|
| Player Artifacts Specification | `inbox/extracted/...Player Artifacts...txt` | 🟣 Requirements | MEDIUM |
| Player Modeling Specification | `inbox/extracted/...Player Modeling...txt` | 🟣 Requirements | MEDIUM |
| Transparent Mechanics Ledger | `inbox/extracted/...Transparent Mechanics...txt` | 🟣 Requirements | MEDIUM |
| Minimal UI Design Addendum | `inbox/extracted/...Minimal Ui...txt` | 🟣 Requirements | LOW |

**Summary:** These four docs define player-facing UX systems that complement the voice-first philosophy: notebook/handbook/knowledge tome, adaptive DM behavior, mechanics output window, and text accessibility.

### B3. Duplicate Detection
| Document | Status | Note |
|----------|--------|------|
| Player Modeling (1).txt | ⚫ DUPLICATE | Identical to Player Modeling.txt |

---

## C. Document Cross-References & Dependencies

### C1. Roadmap → Inbox Mapping

**Roadmap M1 (Solo Vertical Slice)** depends on:
- ✅ Character Sheet UI Contract (referenced in roadmap)
- ✅ Voice Intent & Clarification Protocol (referenced in roadmap)
- ✅ LLM-Engine Boundary Contract (referenced in roadmap)
- ⚠️ **Player Modeling Specification** (Inbox) — affects narration adaptation
- ⚠️ **Transparent Mechanics Ledger** (Inbox) — affects sheet UI design

**Roadmap M2 (Campaign Prep Pipeline)** depends on:
- ✅ Session Zero Ruleset (referenced in roadmap)
- ✅ Solo-First Preparatory DM Model (referenced in roadmap)
- ⚠️ **Generative Presentation Architecture** (Inbox) — defines asset generation strategy
- ⚠️ **Secondary Pass Audit Checklist** (Inbox) — contains prep-time micro-requirements

**Roadmap M3 (Immersion Layer)** depends on:
- ✅ Local Runtime Packaging Strategy (referenced in roadmap)
- ⚠️ **Generative Presentation Architecture** (Inbox) — image/audio generation contracts
- ⚠️ **Player Artifacts Specification** (Inbox) — notebook, handbook, knowledge tome
- ⚠️ **Minimal UI Design Addendum** (Inbox) — text accessibility requirements
- ⚠️ **Chronological Design Record** (Inbox) — voice-first priority, image critique gate

**Roadmap M4 (Offline Packaging)** depends on:
- ✅ Local Runtime Packaging Strategy (referenced in roadmap)
- ⚠️ **Chronological Design Record** (Inbox) — hardware reality check constraints

### C2. Inbox Internal Dependencies

```
Chronological Design Record (foundational)
    └─ establishes: mechanics/presentation separation
    └─ feeds into → Generative Presentation Architecture

Generative Presentation Architecture (architectural)
    └─ defines: Skin Packs, canonical IDs, import rules
    └─ feeds into → Secondary Pass Audit Checklist

Secondary Pass Audit Checklist (implementation)
    └─ contains: micro-requirements for all systems
    └─ feeds into → all M1-M4 milestones

Player Modeling + Transparent Ledger + Minimal UI + Player Artifacts
    └─ all feed into → M1/M3 UX implementation
```

---

## D. Orphaned & Unlinked Documents

### D1. Documents NOT Referenced in Roadmap

The following Inbox documents contain requirements that are NOT explicitly mentioned in the Execution Roadmap v3.1 or Action Plan v3.0:

1. **Player Artifacts Specification**
   - Defines: Notebook (freeform drawing), Handbook (rules reference), Knowledge Tome (progressive discovery)
   - Missing from: M1 deliverables (Character Sheet UI v0)
   - Missing from: M3 deliverables (no mention of player-owned artifacts)

2. **Player Modeling Specification**
   - Defines: Persistent player profiling, adaptive DM behavior, 5 player dimensions
   - Missing from: M1 deliverables (Narration v0 has no mention of adaptation)
   - Missing from: M2 deliverables (no player profile schema)

3. **Transparent Mechanics Ledger**
   - Defines: Mechanics output window, trust/fairness proof, teaching system
   - Mentioned in: M1.13 "Implement basic character sheet UI" (but no detail)
   - Gap: No explicit ledger window in M1 deliverables

4. **Minimal UI Design Addendum**
   - Defines: Text interaction layer, clickable elements, accessibility
   - Mentioned implicitly: M1.4 "Text input with structured fallback"
   - Gap: No explicit chat window or accessibility checklist in M3

5. **Generative Presentation Architecture**
   - Defines: Skin Packs, canonical IDs, alias tables, import safety
   - Missing from: M2 deliverables (no Skin Pack schema or import validation)
   - Missing from: M3 deliverables (no mention of Skin Pack architecture)

6. **Secondary Pass Audit Checklist**
   - Defines: 70+ micro-requirements across all systems
   - Status: NOT integrated into any milestone acceptance criteria
   - Risk: HIGH — checklist contains critical constraints (e.g., image critique gate, prep-time asset logging, dice animation quality)

7. **Chronological Design Record**
   - Defines: 11 phases of architectural evolution
   - Status: Historical/informational
   - Risk: LOW — roadmap already reflects Phase 11 outcomes

---

## E. Authority Conflicts & Supersession

### E1. Conflicting Statements

**NONE DETECTED.** The Inbox documents and Roadmap are architecturally aligned. All Inbox docs elaborate on or add detail to the Roadmap's high-level milestones.

### E2. Supersession Relationships

- **Execution Roadmap v3.1** supersedes **Action Plan v2.0** (explicitly stated)
- **Action Plan v3.0** is DRAFT and awaiting PM sign-off (may supersede Roadmap v3.1 if approved)
- **Inbox documents** do NOT supersede the Roadmap — they are inputs awaiting integration

---

## F. Recommended Document Actions

| Document | Action | Priority | Rationale |
|----------|--------|----------|-----------|
| Generative Presentation Architecture | **INTEGRATE** into M2 | CRITICAL | Defines asset generation strategy, Skin Packs, import rules |
| Secondary Pass Audit Checklist | **EXTRACT** to acceptance criteria | CRITICAL | Contains 70+ micro-requirements missing from milestones |
| Player Modeling Specification | **ADD** to M1/M2 | HIGH | Required for adaptive narration (M1) and player profile storage (M2) |
| Transparent Mechanics Ledger | **ADD** to M1 | HIGH | Required for trust/fairness proof alongside Character Sheet UI |
| Player Artifacts Specification | **ADD** to M3 | MEDIUM | Defines notebook/handbook/knowledge tome (UX artifacts) |
| Minimal UI Design Addendum | **ADD** to M1/M3 | MEDIUM | Accessibility and text interaction requirements |
| Chronological Design Record | **ARCHIVE** as historical | LOW | Informational only; outcomes already reflected in Roadmap |
| Player Modeling (1).txt | **DELETE** | LOW | Duplicate of Player Modeling.txt |

---

## G. Unread Referenced Documents

The following documents are referenced in the Execution Roadmap but have NOT been read during this audit:

1. `docs/design/SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md`
2. `docs/design/CHARACTER_SHEET_UI_CONTRACT.md`
3. `docs/design/VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md`
4. `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md`
5. `docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md`
6. `docs/design/SOLO_FIRST_PREPARATORY_DM_MODEL.md`
7. `docs/design/DESIGN_LAYER_ADOPTION_RECORD.md`
8. `docs/NEXT_STEPS_EXECUTION_PACKET_PM.md`
9. `docs/POST_CP20_DECISION_ANALYSIS.md`
10. `docs/skr/SKR-005_GATE_OPENING_DECISION_MEMO.md`

**Note:** These are referenced as canonical in the Roadmap. If they exist, they should be included in the audit. If they do NOT exist, this is a CRITICAL GAP (referenced documents missing).

---

## H. Corpus Statistics

| Category | Count |
|----------|-------|
| Frozen Engineering Docs | 5 |
| Canonical Planning Docs | 1 |
| Draft Planning Docs | 1 |
| Inbox Design Docs (unique) | 7 |
| Duplicates | 1 |
| Referenced but Unread | 10 |
| **Total Documents Indexed** | **25** |

---

## I. Next Audit Steps

1. ✅ **DOC_INDEX.md** — Complete (this document)
2. ⏭️ **CONSTRAINT_LEDGER.md** — Identify immovable constraints from all docs
3. ⏭️ **CONSISTENCY_AUDIT.md** — Cross-check Roadmap vs Inbox for drift/conflicts
4. ⏭️ **GAP_AND_RISK_REGISTER.md** — Identify missing requirements, determinism risks
5. ⏭️ **ACTION_PLAN_REVISIONS.md** — Propose concrete diffs to integrate Inbox into Roadmap
6. ⏭️ **SYNTHESIS_AND_RECOMMENDATIONS.md** — CP-002 go/no-go decision surface

---

**END OF DOCUMENT INDEX**
