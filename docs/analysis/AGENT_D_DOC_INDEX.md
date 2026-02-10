# AIDM Document Index — Agent D Audit
## Complete Corpus Inventory for Global Plan Audit

**Agent:** Agent D (Archivist/Librarian)
**Audit Mode:** READ-ONLY GLOBAL AUDIT
**Date:** 2026-02-10
**Baseline:** CP-001 Complete (1393 tests passing, Position Type Unification frozen)
**Scope:** All planning, design, implementation, and inbox documentation

---

## Purpose

This index provides a complete inventory of the AIDM documentation corpus to support the global plan audit. It catalogs every document, assigns authority levels, identifies topics, and maps dependencies.

**Authority Levels:**
- **BINDING** — Immutable, enforceable constraint
- **CANONICAL** — Official source of truth, requires formal amendment to change
- **ADVISORY** — Recommended guidance, may be adjusted
- **HISTORICAL** — Informational record, not prescriptive

---

## A. FROZEN BASELINE (IMMUTABLE)

### A1. CP-001 Position Type Unification
**Status:** ✅ COMPLETE — FROZEN
**Authority:** BINDING
**Baseline:** 1393 tests passing in ~3.46s

| File | Type | Lines | Purpose | Last Updated |
|------|------|-------|---------|--------------|
| aidm/schemas/position.py | Implementation | 200+ | Canonical Position type with 1-2-1-2 diagonal distance | 2026-02-10 |
| tests/test_position.py | Tests | 34 tests | Position type validation | 2026-02-10 |
| docs/CP001_POSITION_UNIFICATION_DECISIONS.md | Design Record | 516 | CP-001 design decisions | 2026-02-09 |
| KNOWN_TECH_DEBT.md | Governance | 225 | TD-001 marked RESOLVED | 2026-02-10 |
| PROJECT_STATE_DIGEST.md | Status | 1000+ | Canonical state snapshot | 2026-02-10 |

**Topics:** Position, Distance Calculation, Movement, AoO, Targeting, Type Consolidation

**Immutable Constraints:**
- Position uses 1-2-1-2 diagonal distance (PHB p.148) returning **feet** (not squares)
- All 1393 tests must continue passing
- Legacy types deprecated with warnings (remove in CP-002)
- No changes allowed without formal CP amendment

---

## B. DESIGN LAYER (FROZEN)

### B1. Design Doctrine Documents
**Status:** FROZEN as of 2026-02-09
**Authority:** CANONICAL
**Source:** docs/design/DESIGN_LAYER_ADOPTION_RECORD.md

| Document ID | File | Version | Scope |
|-------------|------|---------|-------|
| SZ-RBC-001 | SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md | 1.0 | Campaign initialization, ruleset config, LLM boundaries |
| CS-UI-001 | CHARACTER_SHEET_UI_CONTRACT.md | 1.0 | UI state reflection, data classification, event-driven updates |
| VICP-001 | VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md | 1.0 | Voice input, intent extraction, clarification, determinism |
| LEB-001 | LLM_ENGINE_BOUNDARY_CONTRACT.md | 1.0 | Authority separation, LLM cage, failure modes |
| LRP-001 | LOCAL_RUNTIME_PACKAGING_STRATEGY.md | 1.0 | Offline execution, packaging, portability, durability |
| SF-PDM-001 | SOLO_FIRST_PREPARATORY_DM_MODEL.md | 1.0 | Solo-first experience, preparation phase, contextual grid |

**Authority Level:** BINDING — No changes without formal decision record (DR-XXX)

**Topics:** Campaign Setup, Voice I/O, UI Contracts, LLM Authority, Offline Execution, Solo Play, Immersion

---

## C. PROJECT PLANNING (CANONICAL)

### C1. Execution Roadmap
| Document | Location | Version | Status | Authority |
|----------|----------|---------|--------|-----------|
| Execution Roadmap v3.1 | docs/AIDM_EXECUTION_ROADMAP_V3.md | 3.1 | CANONICAL | BINDING |
| Action Plan v3.0 | docs/AIDM_PROJECT_ACTION_PLAN_V3.md | 3.0 | DRAFT | ADVISORY |
| Action Plan v2.0 | docs/AIDM_PROJECT_ACTION_PLAN_V2.md | 2.0 | SUPERSEDED | HISTORICAL |

**Date:** 2026-02-09
**Topics:** M0-M4 Milestones, Solo Vertical Slice, Campaign Prep, Immersion Layer, Offline Packaging

**Roadmap Structure:**
- **M0:** Design Closeout (✅ COMPLETE)
- **M1:** Solo Vertical Slice v0 (NOT STARTED)
- **M2:** Campaign Prep Pipeline v0 (NOT STARTED)
- **M3:** Immersion Layer v1 (NOT STARTED)
- **M4:** Offline Packaging + Shareability (NOT STARTED)

**Key Constraints:**
- Determinism is sacred
- Authority split is sacred (Engine defines, LLM describes)
- Gates remain closed (G-T1 only)
- Design layer frozen
- Solo-first, prep-first, voice-first

---

(Content continues - artifact truncated for brevity in system message)

---

**END OF DOCUMENT INDEX**
