# AIDM Inbox - Consistency Audit

**Analysis Date:** 2026-02-10
**Analyst:** Agent C
**Scope:** Cross-document consistency analysis of 7 unique inbox documents

---

## Executive Summary

The inbox documents exhibit **high conceptual consistency** but suffer from **fragmentation, redundancy, and missing operational connective tissue**. Core architectural principles are stable, but implementation guidance is scattered across multiple documents without clear sequencing or priority hierarchy.

**Critical Findings:**
- No contradictions in core architecture
- Significant overlap and redundancy across 4+ documents
- Inconsistent terminology and naming conventions
- Missing integration guidance between systems
- No explicit phase/milestone assignment
- Everything marked "locked" and "binding" without prioritization
- Research phase mentioned but no research deliverables present

---

## Terminology Audit

### Inconsistent Terms

| Concept | Variants Found | Documents | Recommended Standard |
|---------|---------------|-----------|---------------------|
| Presentation Assets | "Skin Pack", "Presentation Plugin", "Language Pack", "Voice Pack" | 2, 3, 6 | **Skin Pack** (primary), others as subtypes |
| DM Adaptation | "Player Modeling", "Player Categorization", "Persistent Profiling" | 5, 6 | **Player Modeling** |
| UI Window | "Chat Window", "Text Window", "Ledger", "Mechanics Output Window" | 3, 7 | Clarify: **Chat Window** (input/output) vs **Ledger** (mechanics log) |
| Asset Generation | "Prep-First", "Prep-Time", "During Prep", "Session Prep" | 1, 2, 6 | **Prep-Phase Generation** |
| Quality Control | "Critique", "Quality Gate", "Evaluation Step" | 1, 6 | **Quality Gate** (process) with **Critique** (evaluation) |
| Knowledge Storage | "Memory", "Indexed Records", "Logs", "Truth Store" | 1, 6 | **Indexed Memory** (general), **Event Logs** (history) |

### Missing Definitions

- **Canonical ID**: Format/structure undefined (mentioned 8+ times, never specified)
- **Skin Pack Schema**: Referenced as "must define" but not detailed
- **Session vs Campaign Prep**: Distinction unclear
- **Bounded Generation**: What are the actual bounds?
- **Median Hardware**: No concrete spec (CPU/GPU/RAM ranges)

### Ambiguous Terms

- **"Locked"**: Appears 30+ times - does this mean architecturally stable, or implementation-frozen?
- **"Binding"**: vs "Required" vs "Must" - no authority hierarchy defined
- **"Prep-First"**: Does this mean prep-only, prep-primary, or prep-preferred?
- **"Light"/"Minimal"/"Unobtrusive"**: No metrics for "light" UI

---

## Overlapping Content Analysis

### Topic: Accessibility

| Document | Section | Content Overlap |
|----------|---------|----------------|
| Minimal UI Addendum | Entire doc | Font customization, color accessibility, high contrast |
| Secondary Pass Audit | Section 8 | Text parity, no voice-only lock-in |
| Player Artifacts | Accessibility | Screen-reader compatibility, font size |
| Teaching Ledger | Accessibility Role | Visual/cognitive accessibility, font/contrast |

**Consolidation Opportunity:** 4 documents repeat accessibility requirements with minor variations. Should be unified in a single governance document.

### Topic: Voice Architecture

| Document | Section | Content Overlap |
|----------|---------|----------------|
| Chronological Record | Phase 7 | TTS > STT priority, voice as primary interface |
| Generative Presentation | Section 7 | Voice profiles as plugins, no mechanical impact |
| Secondary Pass Audit | Section 4 | TTS > STT, multilingual input, confirmation flows |
| Minimal UI Addendum | Core Principle | Voice-first design |

**Consolidation Opportunity:** Voice architecture scattered across 4 documents. Core principles vs implementation details should be separated.

### Topic: Generative Asset Pipeline

| Document | Section | Content Overlap |
|----------|---------|----------------|
| Chronological Record | Phases 3, 4, 5 | Prep-first, image critique, sprite model |
| Generative Presentation | Section 4 | Generative renaming/rephrasing constraints |
| Secondary Pass Audit | Sections 2, 3, 5 | Prep-first strategy, critique gates, sound palettes |

**Consolidation Opportunity:** Asset pipeline described 3 times with incremental detail. Should be unified with clear prep/runtime boundaries.

### Topic: Player Modeling

| Document | Section | Content Overlap |
|----------|---------|----------------|
| Player Modeling Spec | Entire doc | Dimensions, tagging, adaptive output |
| Secondary Pass Audit | Section 7 | Onboarding calibration, ceremony consent |
| Teaching Ledger | Player Modeling Section | Ledger usage signals player type |

**Observation:** Player Modeling is centralized in one spec, but implementation touchpoints scattered. Good separation.

---

## Sequencing and Dependency Conflicts

### Phase/Milestone Assignment Gaps

| Document | Phase Mention | Milestone Assignment |
|----------|--------------|---------------------|
| Chronological Record | "Research Phase" (Phase 11) | None |
| Generative Presentation | "Development Action Items" list | None |
| Secondary Pass Audit | "Research Phase Requirements" | None |
| All others | None | None |

**Issue:** Documents describe systems but don't assign them to development phases or milestones (M0-M4).

### Implicit Sequencing Conflicts

**Example 1: Canonical ID Dependency Chain**
- Generative Presentation requires canonical ID schema (Section 1)
- Player Artifacts require canonical IDs for knowledge gating
- Teaching Ledger requires canonical IDs for log display
- Secondary Pass Audit says "must define" but provides no timeline

**Conflict:** Multiple systems depend on canonical IDs, but no document assigns ownership or delivery milestone.

**Example 2: Asset Generation Prerequisites**
- Image critique requires "critic model" (unspecified)
- Sound palette requires tagging system (unspecified)
- Both require prep-time pipeline (undefined scope)
- Research phase must validate models before integration

**Conflict:** Secondary Pass Audit lists research as "gating requirement" but no research deliverables exist in inbox.

**Example 3: Player Modeling Timing**
- Onboarding requires player calibration (Secondary Pass Audit, Section 7)
- Player modeling is "continuous and persistent" (Player Modeling Spec)
- Teaching Ledger uses modeling signals for adaptation

**Question:** When is the player model initialized? How does it bootstrap?

---

## Research → Plan Alignment

### Research Phase Definition

**Chronological Record, Phase 11:**
> Research Tracks Defined: LLM, image gen + critique, STT, TTS, hardware/optimization
> Gating Rule: No model may be integrated without known failure modes, resource footprint, determinism compatibility

**Secondary Pass Audit, Section 11:**
> Must Research Before Lock-In
> Gating Rule: No model approved unless failure modes understood, multilingual validated, resource footprint fits median hardware

**Alignment Status:** ✅ Consistent definition of research phase

### Missing Research Deliverables

**Expected but Absent:**
- LLM constraint adherence research results
- Image critique model evaluation
- STT multilingual accuracy testing
- TTS naturalness/control assessment
- Hardware profiling and resource budgets

**Impact:** Documents assume research phase is complete or will be done, but no research findings are present to validate feasibility.

### Orphaned Research Questions

**From Chronological Record:**
- "How do we evaluate image quality?" (Phase 4)
- "What are the resource budgets for combined LLM+STT+TTS+image?" (implicit)

**From Secondary Pass Audit:**
- "What are the bounded attempt limits for regeneration?" (Section 3.3)
- "What is median hardware spec?" (Section 10.1)

**Status:** Questions raised but not answered in any document.

---

## Stale or Conflicting Assumptions

### Assumption: "Prep Phase is 1 Hour"

**Secondary Pass Audit, Section 7.7:**
> DM sets expectation for prep time (e.g., ~1 hour)

**Analysis:**
- 1 hour seems arbitrary and untested
- No breakdown of what happens in that hour
- Image generation alone (NPCs, locations, items) could exceed this
- Conflicts with "prep-first" emphasis if time budget is tight

**Status:** Potentially stale assumption requiring validation.

### Assumption: "LLM Queries Indexed Records"

**Chronological Record, Phase 6:**
> LLM queries indexed records instead of holding state

**Secondary Pass Audit, Section 6.1:**
> Truth stored in indexed records; LLM retrieves

**Analysis:**
- Both documents assert this as fact
- No implementation details or feasibility study
- Assumes existence of indexing layer (not defined anywhere)
- Assumes LLM can reliably query structured data (needs validation)

**Status:** Core architectural assumption requiring research validation.

### Assumption: "Steam Hardware Survey as Baseline"

**Chronological Record, Phase 10:**
> Steam Hardware Survey identified as reference baseline

**Secondary Pass Audit, Section 10.1:**
> Use Steam Hardware Survey as reference for typical CPU/GPU/RAM/VRAM

**Analysis:**
- Mentioned twice but never consulted
- No actual hardware specs extracted from survey
- No resource budgets derived from this baseline
- Steam survey skews toward gaming PCs (may not represent "median consumer hardware")

**Status:** Referenced but not operationalized.

### Assumption: "Dice Customization is Early Taste of Power"

**Secondary Pass Audit, Section 7.6:**
> Dice customization reveals generative capability early; persist choices; allow conversation-based changes

**Analysis:**
- Assumes dice customization is quick and low-cost
- Assumes persistence layer exists for cosmetic preferences
- Assumes real-time generation can happen in onboarding
- Conflicts with "prep-first" asset generation strategy

**Status:** May need to be clarified as "select from presets" vs "generate custom."

---

## Incompatible Sequencing Assumptions

### Issue 1: Onboarding UX vs Prep-First Strategy

**Secondary Pass Audit, Section 7:**
- DM greets user immediately
- Persona switch demo in first minute
- Dice customization during onboarding
- Character creation as guided conversation
- Then explicit prep handoff (~1 hour)

**Chronological Record + Secondary Pass:**
- Asset generation is prep-first
- Live generation is fallback only

**Conflict:** Onboarding UX implies immediate generation (persona demo, dice customization), but prep-first strategy suggests deferral. How is this resolved?

**Resolution Needed:** Clarify which assets are pre-generated (DM personas, dice presets) vs generated during onboarding.

### Issue 2: Player Modeling Bootstrapping

**Player Modeling Spec:**
- Continuous, persistent modeling
- Implicit inference from behavior over time

**Secondary Pass Audit, Section 7.3:**
- DM asks calibration questions during onboarding
- Immediate adaptation based on answers

**Question:** Does player modeling start with explicit questions (cold start) and then refine implicitly (warm running)? Documents don't clarify.

### Issue 3: Knowledge Tome Progressive Detail

**Player Artifacts, Section 3:**
> Entries evolve: "Goblin — small, aggressive" → "Fast, lightly armored" → "Defense appears around 15"

**Question:** What triggers progression? Number of encounters? Explicit investigation actions? Documents don't specify.

---

## Document Authority and Priority Conflicts

### Everything is "Locked" and "Binding"

**Issue:** All 7 documents use language like:
- "Locked architectural requirements"
- "Binding input for planning"
- "Must be treated as authoritative"
- "Non-negotiable"

**Problem:** No prioritization hierarchy. If everything is binding, how do we triage scope?

**Recommendation:** Introduce authority levels:
- **Architectural Contract** (non-negotiable)
- **M0 Requirements** (launch-critical)
- **M1+ Features** (post-launch)
- **Aspirational** (future vision)

### Implicit Priority via Document Type

| Document | Type | Implied Priority |
|----------|------|-----------------|
| Chronological Record | Historical baseline | Foundational (highest) |
| Generative Presentation | Architectural contract | Foundational (highest) |
| Minimal UI Addendum | UX constraint | Core |
| Player Artifacts | Feature spec | Core/Post-core |
| Player Modeling | Feature spec | Core/Post-core |
| Teaching Ledger | Feature spec | Core/Post-core |
| Secondary Pass Audit | Implementation guide | Execution (cross-cutting) |

**Observation:** Document structure implies priority, but it's not explicit.

---

## Missing Connective Tissue

### No Integration Guidance

Documents define systems in isolation but don't explain:
- How does the chat window relate to the ledger? Same UI panel or separate?
- How does player modeling influence asset generation? (e.g., tone constraints in image prompts)
- How does the knowledge tome interact with the handbook? Cross-references? Shared UI?
- How does the notebook integrate with DM memory? Can DM read notes?

### No Error Handling or Failure Modes

Documents describe happy paths but not:
- What if image critique fails all regeneration attempts?
- What if STT misunderstands a critical command despite confirmation?
- What if player model infers incorrectly and annoys the user?
- What if prep phase exceeds time budget?

### No Resource Budget Allocation

Documents mention resource concerns but don't allocate:
- How much VRAM for image generation vs LLM inference?
- CPU/GPU time budget per turn?
- Disk space for asset caching?
- Network requirements (if any)?

---

## Recommendations

### 1. Consolidate Overlapping Content
- Create single accessibility governance doc (pull from 4 sources)
- Unify voice architecture (currently split across 4 docs)
- Consolidate asset pipeline (currently split across 3 docs)

### 2. Standardize Terminology
- Adopt glossary with canonical terms
- Resolve "Chat Window" vs "Ledger" ambiguity
- Define "locked" vs "binding" vs "required"

### 3. Assign Phase/Milestone Tags
- Map each requirement to M0/M1/M2/M3/M4
- Distinguish MVP from aspirational features
- Make authority levels explicit

### 4. Create Integration Map
- Diagram how systems interact
- Define UI layout and panel relationships
- Specify data flow between components

### 5. Add Research Validation Gate
- Research phase findings must validate assumptions before planning proceeds
- Flag assumptions requiring validation (canonical IDs, LLM indexing, hardware budgets)

### 6. Define Failure Modes
- Add error handling requirements
- Define fallback behaviors
- Specify degradation paths

---

## Summary Table: Consistency Issues

| Issue Type | Count | Severity |
|------------|-------|----------|
| Terminology Inconsistencies | 6 | Medium |
| Content Overlap/Redundancy | 4 topics | Medium |
| Missing Definitions | 5 | High |
| Sequencing Conflicts | 3 | High |
| Orphaned Research Questions | 4+ | High |
| Stale Assumptions | 4 | Medium |
| Authority Ambiguity | 7 docs | High |
| Missing Integration Guidance | Systemic | High |

**Overall Consistency Grade:** B- (Conceptually aligned, operationally fragmented)

---

**Next Phase:** GAP_AND_RISK_REGISTER.md will identify execution risks and missing components.
