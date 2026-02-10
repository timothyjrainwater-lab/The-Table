# AIDM Topic Index — Agent D Audit
## Reverse Index for Document Retrieval

**Agent:** Agent D (Archivist/Librarian)
**Audit Mode:** READ-ONLY GLOBAL AUDIT
**Date:** 2026-02-10
**Purpose:** Enable topic-based document retrieval

---

## How to Use This Index

This index maps topics to documents. For each topic, you can find:
- Which documents reference it
- Sections/pages where applicable
- Consistency notes (aligned, divergent, or conflicting)

---

## A. CORE MECHANICS TOPICS

### A1. Position & Distance
**Documents:**
- CP-001 Design Decisions (BINDING) — Entire document
- aidm/schemas/position.py (BINDING) — Implementation
- tests/test_position.py (BINDING) — Tests
- KNOWN_TECH_DEBT.md (CANONICAL) — TD-001 resolution

**Status:** ✅ CONSISTENT — 1-2-1-2 diagonal distance returning feet

---

### A2. Movement
**Documents:**
- CP-001 (BINDING) — Position movement
- CP-19 Environment & Terrain (FROZEN) — Terrain effects on movement
- Play Loop (FROZEN) — Movement resolution

**Status:** ✅ CONSISTENT — No conflicts detected

---

### A3. Attacks of Opportunity (AoO)
**Documents:**
- CP-015 (FROZEN) — AoO design decisions
- CP-001 (BINDING) — Position adjacency for AoO
- aidm/core/aoo.py — Implementation
- KNOWN_TECH_DEBT.md — TD-005 (ranged/spellcasting triggers blocked)

**Status:** ⚠️ INCOMPLETE — Ranged/spellcasting AoO blocked by gates

---

### A4. Determinism
**Documents:**
- Execution Roadmap v3.1 (BINDING) — "Determinism is sacred"
- All Design Layer docs (BINDING) — Determinism requirements
- Determinism Audit Playbook (CANONICAL) — Verification procedures
- Determinism Threat Patterns (ADVISORY) — Known risks
- DETERMINISM_THREAT_MODEL_CP18_CP19.md (ADVISORY) — CP-18/19 risks

**Status:** ✅ CONSISTENT — Universal principle across all docs

---

## B. PRESENTATION & IMMERSION TOPICS

### B1. Mechanics vs Presentation Separation
**Documents:**
- Chronological Design Record (Inbox, ADVISORY) — Phase 1: foundational insight
- Generative Presentation Architecture (Inbox, ADVISORY) — Entire document
- LLM_ENGINE_BOUNDARY_CONTRACT.md (Design Layer, BINDING) — Authority separation

**Status:** ✅ CONSISTENT — Core architectural principle

**Key Quote:** "If mechanics are stable, fiction is interchangeable."

---

### B2. Voice Interface
**Documents:**
- VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md (Design Layer, BINDING) — Voice input, intent extraction
- Chronological Design Record (Inbox, ADVISORY) — Phase 7: TTS > STT priority
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Section 4: Voice strategy
- Minimal UI Design Addendum (Inbox, ADVISORY) — Voice-first principle

**Status:** ✅ CONSISTENT — Voice is PRIMARY, text is MANDATORY FALLBACK

---

### B3. Generative Assets
**Documents:**
- Chronological Design Record (Inbox, ADVISORY) — Phases 3-5, 8: Asset generation
- Generative Presentation Architecture (Inbox, ADVISORY) — Section 4: Generative renaming
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Sections 2, 3, 5: Asset pipeline
- SOLO_FIRST_PREPARATORY_DM_MODEL.md (Design Layer, BINDING) — Prep phase

**Status:** ⚠️ DIVERGENT — Inbox details NOT in Design Layer

**Gap:** Inbox describes prep-first generation, image critique gates, sound palettes. Design Layer mentions prep phase but NOT asset details.

---

### B4. Image Generation
**Documents:**
- Chronological Design Record (Inbox, ADVISORY) — Phase 4: Image quality risk, Phase 5: Sprite model
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Section 3: Critique gates
- Roadmap M3 (BINDING) — "Images are atmospheric only"

**Status:** ⚠️ CONFLICT — Inbox claims critique gate required, Roadmap omits

---

### B5. Audio & Sound
**Documents:**
- Chronological Design Record (Inbox, ADVISORY) — Phase 8: Sound as prep-time pipeline
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Section 5: Sound palette generation
- Roadmap M3 (BINDING) — Audio pipeline deliverable

**Status:** ✅ ALIGNED — Roadmap M3 mentions audio, Inbox provides detail

---

## C. USER EXPERIENCE TOPICS

### C1. Player Modeling & Adaptation
**Documents:**
- Player Modeling Specification (Inbox, ADVISORY) — Entire document
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Section 7: Onboarding calibration
- Teaching Ledger Spec (Inbox, ADVISORY) — Player Modeling section

**Status:** ❌ NOT IN ROADMAP — Player modeling NOT mentioned in Roadmap M1-M4

---

### C2. Player Artifacts (Notebook/Handbook/Tome)
**Documents:**
- Player Artifacts Specification (Inbox, ADVISORY) — Entire document

**Status:** ❌ NOT IN ROADMAP — Player artifacts NOT mentioned in Roadmap M1-M4

---

### C3. Character Sheet UI
**Documents:**
- CHARACTER_SHEET_UI_CONTRACT.md (Design Layer, BINDING) — UI contract
- Roadmap M1 (BINDING) — M1.13: Character sheet UI v0
- Player Artifacts Spec (Inbox, ADVISORY) — Notebook/handbook as supplements

**Status:** ⚠️ PARTIAL — Design Layer defines contract, Inbox adds artifacts NOT in Roadmap

---

### C4. Mechanics Transparency (Ledger)
**Documents:**
- Transparent Mechanics Ledger Spec (Inbox, ADVISORY) — Entire document
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Teaching through ledger
- Roadmap M1 (BINDING) — M1.13: Character sheet UI (implicit)

**Status:** ⚠️ IMPLICIT — Roadmap mentions "sheet" but NOT explicit ledger window

---

### C5. Accessibility
**Documents:**
- Minimal UI Design Addendum (Inbox, ADVISORY) — Entire document
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Section 8: Accessibility
- Player Artifacts Spec (Inbox, ADVISORY) — Accessibility section
- Teaching Ledger Spec (Inbox, ADVISORY) — Accessibility role

**Status:** ⚠️ FRAGMENTED — Accessibility repeated in 4 docs, not consolidated

---

### C6. Text Interaction
**Documents:**
- Minimal UI Design Addendum (Inbox, ADVISORY) — Chat window, clickable text
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Text parity
- Roadmap M1 (BINDING) — M1.4: Text input with structured fallback

**Status:** ✅ ALIGNED — Roadmap mentions text, Inbox provides detail

---

## D. ARCHITECTURE TOPICS

### D1. Canonical IDs
**Documents:**
- Generative Presentation Architecture (Inbox, ADVISORY) — Section 1: Canonical IDs
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Canonical IDs implied

**Status:** ❌ NOT IN DESIGN LAYER — Canonical IDs NOT mentioned in frozen Design Layer

**Gap:** Inbox defines Canonical IDs as "language-agnostic identifiers" but format/structure undefined. Design Layer does NOT reference this concept.

---

### D2. Skin Packs
**Documents:**
- Generative Presentation Architecture (Inbox, ADVISORY) — Section 3: Skin Packs
- Chronological Design Record (Inbox, ADVISORY) — Phase 2: Reskinning

**Status:** ❌ NOT IN ROADMAP — Skin Packs NOT mentioned in Roadmap M1-M4

---

### D3. Localization
**Documents:**
- Generative Presentation Architecture (Inbox, ADVISORY) — Sections 5-6: Localization
- Chronological Design Record (Inbox, ADVISORY) — Phase 9: Multilingual support

**Status:** ❌ NOT IN ROADMAP — Localization NOT mentioned in Roadmap M1-M4

---

### D4. LLM Authority Boundary
**Documents:**
- LLM_ENGINE_BOUNDARY_CONTRACT.md (Design Layer, BINDING) — Entire document
- Execution Roadmap v3.1 (BINDING) — "LLM cage"
- Chronological Design Record (Inbox, ADVISORY) — Phase 1: Authority split

**Status:** ✅ CONSISTENT — Universal principle

---

### D5. Campaign Preparation
**Documents:**
- SOLO_FIRST_PREPARATORY_DM_MODEL.md (Design Layer, BINDING) — Prep phase
- Roadmap M2 (BINDING) — Campaign Prep Pipeline
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Sections 2, 7: Prep details
- Chronological Design Record (Inbox, ADVISORY) — Phases 3-8: Prep-first generation

**Status:** ⚠️ DIVERGENT — Roadmap M2 defines prep deliverables, Inbox adds micro-requirements NOT in M2

---

## E. IMPLEMENTATION TOPICS

### E1. Session Zero
**Documents:**
- SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md (Design Layer, BINDING) — Entire document
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Section 7: Onboarding as gameplay
- Roadmap M2 (BINDING) — M2.2: Session Zero loader

**Status:** ✅ ALIGNED — Design Layer defines, Roadmap implements, Inbox adds UX detail

---

### E2. Capability Gates
**Documents:**
- Execution Roadmap v3.1 (BINDING) — Gate status table
- CAPABILITY_GATE_ESCALATION_PLAYBOOKS.md (CANONICAL) — Gate management
- GATE_PRESSURE_MAP.md (ADVISORY) — Gate pressure tracking
- Chronological Design Record (Inbox, ADVISORY) — Phase 11: Gating rules

**Status:** ✅ CONSISTENT — G-T1 OPEN, all others CLOSED

---

### E3. Offline Execution
**Documents:**
- LOCAL_RUNTIME_PACKAGING_STRATEGY.md (Design Layer, BINDING) — Entire document
- Execution Roadmap v3.1 (BINDING) — "Local execution: No cloud dependencies"
- Roadmap M4 (BINDING) — Offline Packaging deliverables
- Chronological Design Record (Inbox, ADVISORY) — Phase 10: Hardware reality check

**Status:** ✅ CONSISTENT — Universal constraint

---

### E4. Hardware Requirements
**Documents:**
- Chronological Design Record (Inbox, ADVISORY) — Phase 10: Steam Hardware Survey baseline
- Secondary Pass Audit Checklist (Inbox, ADVISORY) — Section 10: Median hardware
- Roadmap M4 (BINDING) — Hardware tiers table

**Status:** ✅ ALIGNED — Roadmap M4 specifies hardware tiers

---

## F. TOPIC COVERAGE GAPS

### F1. Topics Mentioned in Inbox BUT NOT in Canonical Docs

| Topic | Inbox Docs | Canonical Status |
|-------|------------|------------------|
| Canonical IDs | Generative Presentation Arch | NOT MENTIONED |
| Skin Packs | Generative Presentation Arch | NOT MENTIONED |
| Localization (input/output) | Generative Presentation Arch, Chronological Record | NOT MENTIONED |
| Player Modeling | Player Modeling Spec | NOT MENTIONED |
| Player Artifacts (Notebook/Handbook/Tome) | Player Artifacts Spec | NOT MENTIONED |
| Mechanics Ledger (explicit) | Teaching Ledger Spec | IMPLICIT ONLY |
| Image Critique Gate | Chronological Record, Secondary Audit | NOT MENTIONED |
| Sound Palette Generation | Chronological Record, Secondary Audit | PARTIAL (M3 mentions audio) |
| DM Persona Selection | Secondary Pass Audit | NOT MENTIONED |
| Dice Customization | Secondary Pass Audit | NOT MENTIONED |
| Daily Launch Greeting | Secondary Pass Audit | NOT MENTIONED |

---

### F2. Topics in Canonical Docs NOT Detailed in Inbox

| Topic | Canonical Docs | Inbox Coverage |
|-------|---------------|----------------|
| Intent Lifecycle | VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md | Implicit only |
| Runtime Processes | Roadmap M1 | Not detailed |
| Asset Store Schema | Roadmap M2 | Not detailed |
| World Export/Import | Roadmap M2 | Not detailed |
| Contextual Grid | SOLO_FIRST_PREPARATORY_DM_MODEL.md | Not detailed |

---

## G. RETRIEVAL QUERIES

### Query: "Where is voice architecture defined?"
**Answer:**
1. VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md (Design Layer, BINDING) — Voice input/clarification
2. Chronological Design Record (Inbox, ADVISORY) — Phase 7: TTS > STT priority
3. Secondary Pass Audit (Inbox, ADVISORY) — Section 4: Voice strategy details

### Query: "Is player modeling required?"
**Answer:**
- NOT mentioned in Roadmap M1-M4 (BINDING)
- Defined in Player Modeling Spec (Inbox, ADVISORY)
- **Status:** NOT currently required

### Query: "What is the baseline test count?"
**Answer:**
- CP-001 (BINDING): 1393 tests passing in ~3.46s
- PROJECT_STATE_DIGEST.md (CANONICAL): Confirms 1393 tests

### Query: "Are Skin Packs part of the design?"
**Answer:**
- Defined in Generative Presentation Architecture (Inbox, ADVISORY)
- NOT mentioned in Design Layer (BINDING)
- NOT mentioned in Roadmap (BINDING)
- **Status:** NOT currently in scope

---

**END OF TOPIC INDEX**
