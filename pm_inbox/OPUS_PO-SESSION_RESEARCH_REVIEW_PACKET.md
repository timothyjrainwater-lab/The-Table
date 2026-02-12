# PO Session Research Review Packet

**Agent:** Opus
**Source:** PO design session (2026-02-12) — full research output
**Date:** 2026-02-12
**Status:** Complete — All Deliverables Ready for PM Review

---

## Executive Summary

Thunder (PO) conducted a multi-hour design session on 2026-02-12 that produced **two doctrinal decisions** and **five research artifacts**. This packet consolidates everything the PM needs to review, approve, and sequence.

**No implementation is authorized.** All artifacts are specs, research briefs, or doctrine. Implementation WOs cannot be dispatched until the PM reviews this packet and decides on sequencing.

### Artifacts Produced

| # | Artifact | File | Type | PM Action |
|---|----------|------|------|-----------|
| 1 | Lens-Spark Context Orchestration Sprint | `docs/specs/RQ-LENS-SPARK-001_CONTEXT_ORCHESTRATION_SPRINT.md` | Research Sprint Spec | Review & approve sequencing |
| 2 | House Policy Governance Doctrine | `pm_inbox/OPUS_PO-SESSION_POLICY_GOVERNANCE_DOCTRINE.md` §2 | Architectural Doctrine | Review & codify in governance |
| 3 | RAW Silence Catalog | `docs/specs/RQ-BOX-002_RAW_SILENCE_CATALOG.md` | Research Brief | Review & approve |
| 4 | Object Identity Model | `docs/specs/RQ-BOX-003_OBJECT_IDENTITY_MODEL.md` | Research Brief | Review & approve |
| 5 | Contradiction Surface Mapping | `docs/specs/RQ-LENS-002_CONTRADICTION_SURFACE_MAPPING.md` | Research Brief | Review & approve |
| 6 | Community RAW Argument Survey | `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md` | Research Supplement | Review (feeds into RQ-BOX-002) |
| 7 | MANIFESTO.md — No-Opaque-DM Doctrine | `MANIFESTO.md` lines 174-176 | Doctrine (already committed by PO) | Acknowledge |

---

## Section 1: Doctrinal Decisions (Review & Codify)

### 1.1 The No-Opaque-DM Doctrine

**Already in MANIFESTO.md (lines 174-176).** PO added this directly during the session. It is now canonical project doctrine.

**Core constraint:** Every outcome that affects game state traces to exactly two sources:
1. **Rules As Written** (3.5e SRD/PHB/DMG/MM, encoded as deterministic resolvers)
2. **House Policy** (pre-declared, bounded, template-instantiated, logged, player-inspectable)

There is no third source. The system is forbidden from:
- Creating new judgment categories at runtime
- Applying "common sense" as a computational input
- Exercising discretion or weighing interpretations silently
- Any form of hidden, uninspectable authority over game state

**PM action:** Acknowledge as canonical. Consider whether it needs a standalone governance document beyond the MANIFESTO.md paragraph, or whether the PM brief (artifact #2) serves as the detailed specification.

### 1.2 The Two-Loop Governance Model

**Runtime (Loop 1 — sacred, frozen):**
- Only RAW + existing trigger families govern
- Instance instantiation within families only (never family creation)
- If no family covers a situation: RAW applies, or FAIL_CLOSED
- No learning, no invention, no approximation

**Offline Evolution (Loop 2 — between versions):**
- Analyze FAIL_CLOSED logs from sessions
- Identify patterns justifying new trigger families
- Design bounded templates (inputs, outputs, stop conditions)
- Ship in a new versioned release
- **Rule of Three:** New family only if pattern appears in multiple independent sessions, can't be expressed as existing family instance, and bounded template is definable

**PM action:** Confirm this model. It constrains how future WOs involving Box governance are designed.

### 1.3 Initial Trigger Family Candidates

Ten families identified (9 original + 1 from edge case discussion):

| # | Trigger Family | Description | Priority |
|---|----------------|-------------|----------|
| 1 | CONTAINMENT_PLAUSIBILITY | Does item physically fit in container | High |
| 2 | RETRIEVAL_ACCESSIBILITY | Action cost to access stored item | Medium |
| 3 | CONCEALMENT_PLAUSIBILITY | Can item be hidden on person | Low |
| 4 | ENVIRONMENTAL_INTERACTION | Can tool/weapon affect object (hardness/material) | High |
| 5 | SPATIAL_CLEARANCE | Can creature/item fit in space | Medium |
| 6 | STACKING_NESTING_LIMITS | Bags inside bags, containers inside containers | Low |
| 7 | FRAGILITY_BREAKAGE | Does rough handling damage item | Medium |
| 8 | READINESS_STATE | "At hand" vs "stowed" and action cost | Medium |
| 9 | MOUNT_COMPATIBILITY | Can creature serve as mount for rider | Low |
| 10 | STRUCTURAL_LOAD_BEARING | Can object support weight across span | Low |

**PM action:** These are candidates. The Template Family Registry (not yet created) will formalize them. RQ-BOX-002 determines whether this list is complete.

---

## Section 2: RQ-LENS-SPARK-001 — Context Orchestration Sprint

**File:** `docs/specs/RQ-LENS-SPARK-001_CONTEXT_ORCHESTRATION_SPRINT.md`

### What It Is

A feature freeze + protocol hardening sprint. PO's thesis: Lens cannot currently guarantee multi-turn coherence. The system will appear to work for 20 turns and silently unravel over 200. Failures will be misattributed to assets (TTS, image, model quality) when the real cause is context orchestration.

### Five Deliverables

| # | Deliverable | New Code? | Dependencies |
|---|-------------|-----------|-------------|
| 1 | **PromptPack v1 Wire Format** | Yes — new dataclass, refactors DMPersona + ContextAssembler + GuardedNarrationService | WO-032, WO-041 |
| 2 | **Memory Retrieval Policy** | Yes — ranking function, RetrievedItem provenance, hard caps | WO-032 (ContextAssembler) |
| 3 | **Summarization Stability** | Yes — SessionSegmentSummary, template-based, drift detection | WO-039 (SessionOrchestrator) |
| 4 | **Contradiction Handling** | Yes — ContradictionChecker, keyword dictionaries, retry policy | WO-032, WO-041, WO-046 |
| 5 | **Evaluation Harness** | Yes — 4 scenarios, 8 metrics, model comparison | All of above |

### Proposed Implementation Sequence

- **Phase 1:** PromptPack + ContradictionChecker (deliverables 1 + 4)
- **Phase 2:** Retrieval Policy + Summarization (deliverables 2 + 3)
- **Phase 3:** Evaluation Harness (deliverable 5)

### Exit Gate

All scenarios pass with:
- Contradiction rate <1%
- Mechanics leak rate 0%
- Budget stability 100%
- Determinism 100%

Only then: proceed to asset integration.

### Prerequisites

All prerequisite WOs are INTEGRATED: WO-032, WO-039, WO-040, WO-041, WO-045, WO-046.

### PM Decision Required

1. **Approve the feature freeze.** No new asset integration (beyond current Kokoro TTS wiring) until exit gate passes.
2. **Approve the implementation sequence.** Phase 1 → 2 → 3, or alternative ordering.
3. **Decide on WO granularity.** Is this one mega-WO or broken into per-deliverable WOs?

---

## Section 3: Research Briefs (Review & Approve)

### 3.1 RQ-BOX-002: RAW Silence Catalog

**File:** `docs/specs/RQ-BOX-002_RAW_SILENCE_CATALOG.md`

**Purpose:** Systematic audit of where 3.5e RAW is silent, ambiguous, or contradictory. Maps each silence to a trigger family. Must complete before the Template Family Registry can be finalized.

**Current state:** 10 silence entries cataloged (SIL-001 through SIL-010). Six audit domains defined. Methodology, classification taxonomy, and output format specified.

**Key findings so far:**
- SIL-001: Container capacity ignores volume/shape (CONTAINMENT_PLAUSIBILITY)
- SIL-002: No load-bearing formula for objects (STRUCTURAL_LOAD_BEARING)
- SIL-004: Object identity under damage undefined (deferred to RQ-BOX-003)
- SIL-007: **PHB vs DMG directly contradict** on enhancement bonus to hardness/HP — affects every magic item
- SIL-008: Armor excluded from enhancement bonus table — +5 full plate trivially destroyed
- SIL-010: "Ruined" object state physically undefined (deferred to RQ-BOX-003)

**Supplemented by:** RQ-BOX-002-A (Community RAW Argument Survey) — mined EN World, Giant in the Playground, and other forums for community-identified RAW problems. Added 4 new catalog entries.

**PM decision:** Approve the research methodology and initial catalog. This is a living document — entries will be added as the audit proceeds domain by domain.

### 3.2 RQ-BOX-003: Object Identity Model

**File:** `docs/specs/RQ-BOX-003_OBJECT_IDENTITY_MODEL.md`

**Purpose:** Define when one object becomes many. Prerequisite for correct spell targeting (mending, make whole, fabricate), sunder resolution, and at least 6 of the 10 trigger families.

**Key design decisions proposed:**
- `ObjectState` frozen dataclass with integrity states: intact → damaged → broken → destroyed → fragments
- State transition graph with explicit triggers and irreversibility constraints
- Spell interaction rules (mending targets one object; fragments are separate objects)
- 5 consumer systems mapped: SpellResolver, sunder, trigger families, inventory, NarrativeBrief

**6 open questions requiring PO or PM input:**
1. Destruction threshold (HP 0 = broken or destroyed?)
2. Fragment inheritance (material yes, dimensions?)
3. Dimension granularity (size category only, or full dimensions?)
4. Broken vs destroyed state distinction (recommendation: keep distinct — House Policy)
5. Magic item destruction (special rules accommodation)
6. Fragment count formula (fixed, material-dependent, or damage-dependent?)

**Motivating edge case (PO ruling):** Mending cannot join two severed rope halves. They are two objects. Mending repairs one object. Test case captured with GIVEN/WHEN/THEN format.

**PM decision:** Approve the schema direction. Open questions 1, 3, 4, and 6 are the most architecturally impactful — recommend resolving before implementation WO is dispatched.

### 3.3 RQ-LENS-002: Contradiction Surface Mapping

**File:** `docs/specs/RQ-LENS-002_CONTRADICTION_SURFACE_MAPPING.md`

**Purpose:** Empirical validation of the keyword dictionaries defined in RQ-LENS-SPARK-001 Deliverable 4. Run 300+ narrations against scripted NarrativeBriefs. Measure actual contradiction rates. Build confusion matrices for keyword-based detection.

**Methodology:**
- 40 distinct scripted NarrativeBrief configurations across 5 categories
- 10 narrations per brief at temperature 0.8 (300-400 total)
- Manual classification of each narration for contradictions
- Confusion matrix per keyword dictionary (precision, recall, F1)
- Novel pattern discovery for contradictions not covered by existing taxonomy

**Key outputs:**
- Validated/revised keyword dictionaries
- Baseline contradiction rate (before ContradictionChecker exists)
- Novel contradiction pattern catalog
- Detection threshold recommendations

**Sequencing constraint:** Requires a local LLM model available for generation. Independent of RQ-BOX-002 and RQ-BOX-003.

**PM decision:** Approve the methodology. This research should sequence **before** ContradictionChecker implementation (RQ-LENS-SPARK-001 Phase 1) to avoid building a detector calibrated against assumptions rather than data.

### 3.4 RQ-BOX-002-A: Community RAW Argument Survey

**File:** `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md`

**Purpose:** Mine 3.5e community forums for RAW arguments to inform the RAW Silence Catalog. This is a supplement to RQ-BOX-002, not a standalone research question.

**Five categories surveyed:**
- **A: Object Hardness/HP/Sunder** — PHB vs DMG contradiction, armor exclusion, adamantine balance, low object HP. Highest-impact findings.
- **B: Polymorph/Wild Shape** — Equipment melding, component pouch, form stacking. All deferred (out of v1 scope). WotC officially declared the subsystem broken.
- **C: Grapple/Unarmed/AoO** — Square threatening, Flurry in grapple, monk weapon classification. Box resolver decisions, not trigger family candidates.
- **D: Simulacrum** — Level percentage, spellcasting, infinite loop, entity identity. All deferred (level 7 spell, out of v1 scope).
- **E: Famous Exploits** — Locate City Nuke, Peasant Railgun, Void Bomb. Illustrative of design principles, not actionable silences.

**Four design principles reinforced:**
1. RAW is not physics — trigger families provide bounded answers, not physical simulation
2. Contradictions require a design-time choice, not runtime judgment
3. "Broken" interactions are still RAW — No-Opaque-DM applies
4. Scope discipline protects against complexity explosion

**PM decision:** Acknowledge. The 4 new silence entries (SIL-007 through SIL-010) are already integrated into RQ-BOX-002. The design principles reinforce existing project doctrine.

---

## Section 4: Sequencing Recommendation

### Dependency Graph

```
MANIFESTO.md (No-Opaque-DM Doctrine)
  └── Already committed by PO. No action needed.

RQ-BOX-002 (RAW Silence Catalog)
  ├── Feeds into: Template Family Registry (not yet created)
  ├── Feeds into: FAIL_CLOSED Logging Schema (not yet created)
  └── Related: RQ-BOX-003 (shares SIL-004, SIL-010)

RQ-BOX-003 (Object Identity Model)
  ├── Feeds into: SpellResolver (mending, make whole, fabricate)
  ├── Feeds into: Sunder resolution
  ├── Feeds into: 6 trigger families
  └── Related: RQ-BOX-002 (shares SIL-004, SIL-010)

RQ-LENS-SPARK-001 (Context Orchestration Sprint)
  ├── Phase 1: PromptPack + ContradictionChecker
  │   └── Informed by: RQ-LENS-002 (should run before implementation)
  ├── Phase 2: Retrieval + Summarization
  └── Phase 3: Evaluation Harness

RQ-LENS-002 (Contradiction Surface Mapping)
  ├── Requires: Local LLM model
  ├── Informs: RQ-LENS-SPARK-001 Phase 1
  └── Independent of: RQ-BOX-002, RQ-BOX-003
```

### Recommended Execution Order

**Track A (Box Governance) — can run in parallel with Track B:**
1. RQ-BOX-002 audit continues (domain by domain)
2. RQ-BOX-003 open questions resolved by PO/PM
3. Template Family Registry spec (new artifact, derived from RQ-BOX-002)
4. FAIL_CLOSED Logging Schema (new artifact)

**Track B (Lens-Spark Hardening) — can run in parallel with Track A:**
1. RQ-LENS-002 empirical study (before implementation)
2. RQ-LENS-SPARK-001 Phase 1 (PromptPack + ContradictionChecker)
3. RQ-LENS-SPARK-001 Phase 2 (Retrieval + Summarization)
4. RQ-LENS-SPARK-001 Phase 3 (Evaluation Harness)

**Tracks A and B are independent.** Neither blocks the other. Both represent architectural hardening before feature expansion.

### What Cannot Proceed Until This Review Is Complete

- No implementation WOs can be dispatched for any of these deliverables
- No asset integration (TTS beyond Kokoro, image, music) until RQ-LENS-SPARK-001 exit gate passes
- No trigger family implementation until RQ-BOX-002 audit confirms the family list
- No ObjectState implementation until RQ-BOX-003 open questions are resolved

---

## Section 5: PM Action Item Checklist

| # | Action | Artifact | Urgency |
|---|--------|----------|---------|
| 1 | **Approve feature freeze** until RQ-LENS-SPARK-001 exit gate passes | RQ-LENS-SPARK-001 | High |
| 2 | **Acknowledge No-Opaque-DM Doctrine** as canonical project constraint | MANIFESTO.md | High |
| 3 | **Approve RQ-LENS-SPARK-001** implementation sequence (Phase 1→2→3) | RQ-LENS-SPARK-001 | High |
| 4 | **Approve RQ-BOX-002** methodology and initial catalog | RQ-BOX-002 | Medium |
| 5 | **Approve RQ-BOX-003** schema direction and prioritize open questions | RQ-BOX-003 | Medium |
| 6 | **Approve RQ-LENS-002** methodology; sequence before ContradictionChecker impl | RQ-LENS-002 | Medium |
| 7 | **Acknowledge RQ-BOX-002-A** community survey findings (4 new SIL entries) | RQ-BOX-002-A | Low |
| 8 | **Decide WO granularity** for RQ-LENS-SPARK-001 (1 mega-WO or per-deliverable) | RQ-LENS-SPARK-001 | Medium |
| 9 | **Decide on SIL-007 resolution** (PHB vs DMG enhancement bonus — recommend PHB) | RQ-BOX-002 | Low (not blocking v1) |
| 10 | **Resolve RQ-BOX-003 open questions** (especially §5.1 destruction threshold, §5.4 broken vs destroyed) | RQ-BOX-003 | Low (not blocking current work) |

---

## Appendix: File Index

All artifacts produced during the 2026-02-12 PO session:

```
MANIFESTO.md                                         (lines 174-176 added by PO)
pm_inbox/OPUS_PO-SESSION_POLICY_GOVERNANCE_DOCTRINE.md   (PM brief — session summary)
pm_inbox/OPUS_PO-SESSION_RESEARCH_REVIEW_PACKET.md       (THIS FILE — PM review packet)
docs/specs/RQ-LENS-SPARK-001_CONTEXT_ORCHESTRATION_SPRINT.md
docs/specs/RQ-BOX-002_RAW_SILENCE_CATALOG.md
docs/specs/RQ-BOX-003_OBJECT_IDENTITY_MODEL.md
docs/specs/RQ-LENS-002_CONTRADICTION_SURFACE_MAPPING.md
docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md
```

Total: 8 files. ~2,500 lines of specification and research.
No code was written. No tests were added. No implementation was started.
All artifacts are DRAFT status pending PM review.
