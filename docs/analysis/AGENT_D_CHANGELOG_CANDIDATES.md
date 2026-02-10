# AIDM Changelog Candidates — Agent D Audit
## Non-Prescriptive Areas Requiring Orchestrator Review

**Agent:** Agent D (Archivist/Librarian)
**Audit Mode:** READ-ONLY GLOBAL AUDIT
**Date:** 2026-02-10
**Purpose:** Flag areas that MAY require updates without prescribing solutions

---

## Purpose & Scope

This document identifies areas where:
1. Inbox research contradicts or extends canonical documentation
2. Design assumptions appear outdated
3. Sequencing or scope gaps may cause implementation blockers
4. Authority claims require reconciliation

**This is NOT a plan revision.** It uses neutral language:
- "May require review"
- "Potentially outdated"
- "Assumption not restated elsewhere"

---

## CATEGORY 1: INBOX DOCUMENTS AWAITING ADOPTION DECISION

### CANDIDATE-01: Generative Presentation Architecture
**Inbox Document:** Generative Presentation & Localization Architecture – Locked Requirements.txt
**Claimed Status:** "Binding input for Action Plan"
**Actual Status:** ADVISORY (not adopted)

**Content Summary:**
- Canonical IDs (language-agnostic identifiers)
- Skin Packs (data-driven presentation bundles)
- Generative renaming/rephrasing constraints
- Multilingual input via alias tables
- Voice profiles as presentation plugins
- Import/extensibility model

**Affected Milestones:** M2 (asset generation), M3 (immersion layer)

**Why This May Require Review:**
- Inbox defines foundational architecture (Canonical IDs, Skin Packs) NOT mentioned in Design Layer or Roadmap
- IF this architecture is needed, M2 deliverables may be underspecified
- IF this architecture is NOT needed, Inbox document should be archived as research artifact

**Orchestrator Questions:**
1. Are Canonical IDs required for AIDM architecture?
2. Are Skin Packs part of M2 Campaign Prep Pipeline?
3. Is multilingual support in scope for M1-M4?

---

### CANDIDATE-02: Player Modeling Specification
**Inbox Document:** Player Modeling & Adaptive DM Behavior – Persistent Profiling Specification.txt
**Claimed Status:** "Elevates player modeling to a core system"
**Actual Status:** ADVISORY (not adopted)

**Content Summary:**
- Persistent player profiling (experience level, pacing, explanation depth, tone, modality)
- Explicit + implicit tagging mechanism
- Adaptive DM output (language complexity, narrative density, tonality, intervention frequency)
- Guardrails (presentation only, reversible)

**Affected Milestones:** M1 (narration v0), M2 (player profile storage)

**Why This May Require Review:**
- Roadmap M1 includes "Narration v0" but does NOT mention adaptation based on player profile
- IF player modeling is "core," M1/M2 deliverables may be incomplete
- IF it's NOT core, Inbox document overclaims authority

**Orchestrator Questions:**
1. Is adaptive narration required for M1?
2. Does M2 need player profile storage?
3. Is this a post-M4 enhancement?

---

### CANDIDATE-03: Player Artifacts Specification
**Inbox Document:** Player Artifacts – Notebook, Handbook, And Knowledge Tome Specification.txt
**Claimed Status:** "Locks player-owned artifacts as core experiential systems"
**Actual Status:** ADVISORY (not adopted)

**Content Summary:**
- Player Notebook (freeform drawing, handwritten text, doodles)
- Player Handbook (searchable rules reference)
- Knowledge Tome (progressive, character-earned knowledge)

**Affected Milestones:** M3 (immersion layer)

**Why This May Require Review:**
- Roadmap M3 does NOT mention notebook, handbook, or knowledge tome
- Inbox claims these are "not optional UX elements"
- IF truly non-optional, M3 deliverables may be incomplete

**Orchestrator Questions:**
1. Are these artifacts part of M3 Immersion Layer?
2. Are they post-M4 enhancements?
3. Should they be removed from scope entirely?

---

### CANDIDATE-04: Transparent Mechanics Ledger
**Inbox Document:** Transparent Mechanics Output & Teaching Ledger – Design Specification.txt
**Claimed Status:** "Locks the Mechanics Output Window as a core trust system"
**Actual Status:** ADVISORY (not adopted)

**Content Summary:**
- Mechanics output panel (dice results, modifiers, stat values, success/failure)
- Trust & fairness proof (visible dice, deterministic proof)
- Teaching function (passive education through visible mechanics)

**Affected Milestones:** M1 (character sheet UI v0)

**Why This May Require Review:**
- Roadmap M1.13 mentions "Implement basic character sheet UI" but does NOT explicitly mention mechanics ledger window
- Inbox claims ledger is distinct from character sheet
- Unclear if M1.13 includes ledger OR if ledger is separate deliverable

**Orchestrator Questions:**
1. Is mechanics ledger part of M1.13 character sheet UI?
2. Is it a separate M1 deliverable?
3. Is it implicit and doesn't need explicit callout?

---

### CANDIDATE-05: Secondary Pass Audit Checklist
**Inbox Document:** Secondary Pass Audit – Fine-detail Capture & Implementation Checklist.txt
**Claimed Status:** "Checklist during planning and ticket writing"
**Actual Status:** ADVISORY (not integrated)

**Content Summary:**
- 70+ micro-requirements across 12 sections
- Asset logging & reuse, image critique checklists, sound palette generation
- Onboarding details (DM persona selection, dice customization, character creation flow)
- Daily launch interaction, ceremony consent, dice animation quality

**Affected Milestones:** All (M1-M4)

**Why This May Require Review:**
- Checklist contains detailed acceptance criteria NOT in Roadmap milestone deliverables
- Many items are UX nuances that may be overlooked without explicit checklist integration
- Currently disconnected from Roadmap

**Orchestrator Questions:**
1. Should these micro-requirements be integrated into milestone acceptance criteria?
2. Are they implementation guidance (not blocking)?
3. Which items (if any) are hard requirements?

---

### CANDIDATE-06: Minimal UI Design Addendum
**Inbox Document:** Minimal UI, Text Interaction, And Visual Accessibility – Design Addendum.txt
**Claimed Status:** "Locks minimal UI presence"
**Actual Status:** ADVISORY (not adopted)

**Content Summary:**
- Text interaction layer (chat window, always available, non-intrusive)
- Clickable text (assistive affordances for spell names, items, conditions)
- Visual accessibility (font customization, color accessibility, high-contrast modes)

**Affected Milestones:** M1 (text input), M3 (accessibility)

**Why This May Require Review:**
- Roadmap M1.4 mentions "Text input with structured fallback" but does NOT detail chat window design
- Roadmap M3 does NOT mention accessibility requirements explicitly
- Accessibility is fragmented across 4 Inbox documents (see DRIFT_AND_CONFLICT_LOG.md)

**Orchestrator Questions:**
1. Are accessibility requirements part of M1 or M3?
2. Should there be a consolidated accessibility checklist?
3. Is this already implicit in Design Layer (CHARACTER_SHEET_UI_CONTRACT.md)?

---

### CANDIDATE-07: Chronological Design Record
**Inbox Document:** Chronological Design Record – From Core Insight To Research Phase.txt
**Claimed Status:** "Authoritative understanding of AIDM's design trajectory"
**Actual Status:** HISTORICAL (informational)

**Content Summary:**
- 11 phases of architectural evolution
- Phase 1: Mechanics vs Presentation separation
- Phase 4: Image quality evaluation requirement
- Phase 7: Voice-first interface (TTS > STT priority)
- Phase 11: Research phase gating rules

**Affected Milestones:** None directly

**Why This May Require Review:**
- Historical context for Design Layer decisions
- Contains rationale for design choices NOT captured elsewhere
- May be useful for onboarding or audit trails

**Orchestrator Questions:**
1. Should this be archived as design history?
2. Should key insights be extracted into Design Layer amendments?
3. Can this be ignored (all decisions already reflected in canonical docs)?

---

## CATEGORY 2: DESIGN LAYER GAPS

### CANDIDATE-08: Image Critique Gate Not in Design Layer
**Inbox Claims:** "Image generation without critique is unacceptable" (Chronological Record, Secondary Audit)
**Design Layer Status:** NOT MENTIONED
**Roadmap Status:** NOT MENTIONED

**Why This May Require Review:**
- IF image critique is truly immovable constraint, Design Layer and Roadmap M3 are underspecified
- IF it's NOT required, Inbox documents overstate constraint

**Affected Milestones:** M3 (image pipeline)

**Orchestrator Questions:**
1. Is image critique required?
2. If yes, should Design Layer be amended?
3. If no, should Inbox claims be disregarded?

---

### CANDIDATE-09: Canonical IDs Not in Design Layer
**Inbox Claims:** Canonical IDs are foundational for Skin Packs, localization, alias tables (Generative Presentation Architecture)
**Design Layer Status:** NOT MENTIONED
**Roadmap Status:** NOT MENTIONED

**Why This May Require Review:**
- Entire Inbox architecture depends on Canonical IDs
- IF Canonical IDs do NOT exist in codebase, Inbox architecture cannot be implemented
- IF they DO exist, Design Layer should document them

**Affected Milestones:** M2 (asset generation), M3 (localization)

**Orchestrator Questions:**
1. Do Canonical IDs exist in current codebase?
2. If yes, should Design Layer document them?
3. If no, is Inbox architecture out of scope?

---

### CANDIDATE-10: Research Phase Not in Roadmap
**Inbox Claims:** Research phase is "mandatory before implementation lock-in" for LLM, image gen, STT, TTS, hardware (Chronological Record, Secondary Audit)
**Roadmap Status:** NOT MENTIONED

**Why This May Require Review:**
- Inbox claims research is mandatory BUT Roadmap M1-M4 do NOT include research phase
- IF research is truly mandatory, M1-M4 cannot proceed without research completion
- IF it's NOT mandatory, Inbox overclaims

**Affected Milestones:** All (M1-M4)

**Orchestrator Questions:**
1. Is research phase blocking M1-M4?
2. Is research implicit within milestone work?
3. Can M1-M4 proceed with placeholder models (defer research)?

---

## CATEGORY 3: ROADMAP GAPS

### CANDIDATE-11: M1 Narration v0 — Adaptation Not Mentioned
**Roadmap M1 Deliverable:** "Narration v0: If LLM present, narrate from engine events; if missing/timeout, deterministic template narration"
**Inbox Extension:** Player Modeling Spec claims narration should adapt based on player profile (language complexity, narrative density, tonality, intervention frequency)

**Why This May Require Review:**
- M1 Narration v0 does NOT mention adaptation
- IF adaptation is required, M1 deliverable may be incomplete
- IF it's NOT required, M1 deliverable is correct

**Orchestrator Questions:**
1. Is adaptive narration part of M1?
2. Is it a post-M1 enhancement?
3. Can M1 Narration v0 be fixed-tone (defer adaptation to M2)?

---

### CANDIDATE-12: M2 Campaign Prep — Skin Pack Schema Not Mentioned
**Roadmap M2 Deliverable:** Campaign creation contract, prep job orchestration, asset store + reuse rules, world export/import
**Inbox Extension:** Generative Presentation Architecture defines Skin Pack schema, import validation

**Why This May Require Review:**
- M2 mentions "asset store" but does NOT mention Skin Pack schema
- IF Skin Packs are required for asset organization, M2 may be underspecified
- IF they're NOT required, Inbox architecture is out of scope

**Orchestrator Questions:**
1. Are Skin Packs part of M2 asset store?
2. Is M2 asset store simpler (just files, no schema)?
3. Is Skin Pack architecture deferred to post-M4?

---

### CANDIDATE-13: M3 Immersion Layer — Player Artifacts Not Mentioned
**Roadmap M3 Deliverable:** Voice pipeline, image pipeline, audio pipeline, contextual grid
**Inbox Extension:** Player Artifacts Spec defines notebook, handbook, knowledge tome

**Why This May Require Review:**
- M3 Immersion Layer does NOT mention notebook, handbook, or knowledge tome
- Inbox claims these are "core experiential systems" and "not optional UX elements"
- IF they're truly core, M3 may be incomplete

**Orchestrator Questions:**
1. Are player artifacts part of M3?
2. Are they post-M4 enhancements?
3. Should they be removed from scope?

---

### CANDIDATE-14: M3 Immersion Layer — Accessibility Not Explicit
**Roadmap M3 Acceptance Criteria:** "Offline voice I/O functional, audio transitions, images atmospheric, grid contextual, licensing/attribution"
**Inbox Extension:** Minimal UI Addendum, Secondary Audit, Player Artifacts Spec, Teaching Ledger Spec all mention accessibility (font size, color, contrast, screen readers)

**Why This May Require Review:**
- Accessibility is fragmented across 4 Inbox documents
- M3 acceptance criteria do NOT explicitly mention accessibility
- Unclear if accessibility is implicit OR missing

**Orchestrator Questions:**
1. Is accessibility part of M3 acceptance criteria?
2. Should there be a consolidated accessibility checklist?
3. Is it already covered by Design Layer (CHARACTER_SHEET_UI_CONTRACT.md)?

---

## CATEGORY 4: AUTHORITY RECONCILIATION

### CANDIDATE-15: Inbox "Locked" Claims Require Adoption Decision
**Issue:** All 7 Inbox documents claim "locked," "binding," or "authoritative" status WITHOUT formal adoption into canonical documentation.

**Documents:**
- Generative Presentation Architecture
- Player Modeling Specification
- Player Artifacts Specification
- Transparent Mechanics Ledger
- Minimal UI Design Addendum
- Secondary Pass Audit Checklist
- Chronological Design Record

**Why This May Require Review:**
- Inbox docs are currently ADVISORY (not BINDING)
- Treating them as BINDING creates governance violation
- Requires Orchestrator decision: Adopt (make BINDING), Integrate (extract key parts), or Archive (historical reference)

**Orchestrator Questions:**
1. Which Inbox documents should be formally adopted?
2. Which should be integrated into existing canonical docs?
3. Which should be archived as research artifacts?

---

## CATEGORY 5: OUTDATED OR INCOMPLETE INFORMATION

### CANDIDATE-16: Action Plan v3.0 Status Unclear
**Current Status:** DRAFT (per Execution Roadmap v3.1)
**Issue:** Action Plan v3.0 has NOT been formally approved or superseded

**Why This May Require Review:**
- Execution Roadmap v3.1 superseded Action Plan v2.0
- Action Plan v3.0 is marked DRAFT
- Unclear if v3.0 will ever be finalized OR if Roadmap v3.1 is sufficient

**Orchestrator Questions:**
1. Does Action Plan v3.0 need PM sign-off?
2. Is Execution Roadmap v3.1 sufficient (no Action Plan needed)?
3. Should Action Plan v3.0 be archived?

---

### CANDIDATE-17: Hardware Baseline Ambiguity
**Inbox Claims:** "Steam Hardware Survey" as baseline (Chronological Record, Secondary Audit)
**Roadmap M4:** Provides hardware tiers (Baseline, Recommended, Enhanced) BUT doesn't specify which is "target"

**Why This May Require Review:**
- Model selection, optimization targets, performance budgets depend on hardware baseline clarity
- "Median" is ambiguous (median CPU? GPU? RAM? All three?)

**Orchestrator Questions:**
1. Which M4 tier is the primary target?
2. Should "Baseline" tier be renamed to "Minimum"?
3. Is "Recommended" tier the actual baseline?

---

### CANDIDATE-18: Canonical ID Format Undefined
**Inbox Claims:** Canonical IDs are "language-agnostic identifiers" (Generative Presentation Architecture)
**Issue:** Format NEVER defined (UUID? Integer? String? Composite key?)

**Why This May Require Review:**
- Cannot implement Skin Packs, alias tables, or localization without Canonical ID specification
- IF Canonical IDs are required, specification is missing
- IF they're NOT required, Inbox architecture is out of scope

**Orchestrator Questions:**
1. Should Canonical ID format be specified?
2. Do Canonical IDs already exist in codebase under different name?
3. Is this concept deferred to post-M4?

---

## SUMMARY TABLE

| ID | Category | Severity | Affected Milestone | Review Question |
|----|----------|----------|-------------------|----------------|
| CANDIDATE-01 | Inbox Adoption | HIGH | M2, M3 | Are Canonical IDs + Skin Packs in scope? |
| CANDIDATE-02 | Inbox Adoption | MEDIUM | M1, M2 | Is player modeling required? |
| CANDIDATE-03 | Inbox Adoption | MEDIUM | M3 | Are player artifacts (notebook/handbook/tome) in scope? |
| CANDIDATE-04 | Inbox Adoption | MEDIUM | M1 | Is mechanics ledger part of M1 character sheet UI? |
| CANDIDATE-05 | Inbox Adoption | MEDIUM | All | Should Secondary Audit checklist be integrated? |
| CANDIDATE-06 | Inbox Adoption | LOW | M1, M3 | Is accessibility already covered? |
| CANDIDATE-07 | Inbox Adoption | LOW | None | Archive Chronological Record as historical? |
| CANDIDATE-08 | Design Layer Gap | MEDIUM | M3 | Is image critique required? |
| CANDIDATE-09 | Design Layer Gap | HIGH | M2, M3 | Do Canonical IDs exist? Should they be documented? |
| CANDIDATE-10 | Design Layer Gap | MEDIUM | All | Is research phase blocking M1-M4? |
| CANDIDATE-11 | Roadmap Gap | MEDIUM | M1 | Is adaptive narration part of M1? |
| CANDIDATE-12 | Roadmap Gap | HIGH | M2 | Are Skin Packs part of M2 asset store? |
| CANDIDATE-13 | Roadmap Gap | MEDIUM | M3 | Are player artifacts part of M3? |
| CANDIDATE-14 | Roadmap Gap | LOW | M3 | Is accessibility explicit in M3 acceptance criteria? |
| CANDIDATE-15 | Authority | CRITICAL | All | Which Inbox docs should be adopted? |
| CANDIDATE-16 | Outdated Info | LOW | None | Is Action Plan v3.0 still needed? |
| CANDIDATE-17 | Incomplete Info | MEDIUM | M4 | Which hardware tier is primary target? |
| CANDIDATE-18 | Incomplete Info | HIGH | M2, M3 | What is Canonical ID format? |

**Total Candidates:** 18

**Critical:** 1 (CANDIDATE-15)
**High:** 4 (CANDIDATE-01, CANDIDATE-09, CANDIDATE-12, CANDIDATE-18)
**Medium:** 10
**Low:** 3

---

## MAINTENANCE NOTES

**Last Updated:** 2026-02-10
**Agent:** Agent D (Archivist)
**Mode:** READ-ONLY
**Next Update:** After Orchestrator decisions or corpus changes

**This document flags issues only.** It does NOT prescribe solutions or revisions.

---

**END OF CHANGELOG CANDIDATES**
