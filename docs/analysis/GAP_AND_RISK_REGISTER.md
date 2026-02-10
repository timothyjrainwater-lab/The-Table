# AIDM Inbox - Gap and Risk Register

**Analysis Date:** 2026-02-10
**Analyst:** Agent C
**Scope:** Execution risk assessment and gap identification across inbox documents

---

## Executive Summary

The inbox documents articulate a **bold and coherent vision** but exhibit **critical gaps in execution planning, feasibility validation, and risk mitigation**. Many architectural assumptions lack research validation, and several "locked" requirements have no clear implementation path.

**Risk Level:** 🟡 MEDIUM-HIGH
- Core architecture is sound
- Feature ambition exceeds validated capability
- Resource constraints unaddressed
- Integration complexity underestimated

---

## Research Conclusions with No Execution Path

### 1. Image Critique / Quality Gating

**Research Conclusion (Chronological Record, Phase 4):**
> Image generation without image quality evaluation is unacceptable.
> Generation must be paired with critique/quality evaluation step.

**Secondary Pass Audit, Section 3.2:**
> Quality evaluation should cover: readability, subject centering, artifacting, style adherence, anchor identity match

**Gap:**
- No critic model identified or validated
- No fallback if critique fails
- No quality threshold defined (what's "acceptable"?)
- No human-in-the-loop option specified

**Execution Path Status:** ❌ MISSING

**Impact:** Image generation cannot proceed to implementation without this.

---

### 2. LLM Indexed Memory Querying

**Research Conclusion (Chronological Record, Phase 6):**
> LLM queries indexed records instead of holding state.
> Truth lives outside the LLM.

**Secondary Pass Audit, Section 6:**
> Maintain structured records: entity cards, relationships, event timeline, open threads, inventory, consequences

**Gap:**
- No indexing architecture defined
- No query interface specified
- No LLM prompt engineering for reliable structured retrieval
- No research validating that LLMs can reliably query external indices

**Execution Path Status:** ❌ MISSING (core assumption unvalidated)

**Impact:** Memory system cannot be implemented without this architecture.

---

### 3. Multilingual STT/TTS

**Research Conclusion (Chronological Record, Phase 9):**
> Players may speak or type in multiple languages.
> Alias tables map localized input to canonical IDs.

**Generative Presentation Architecture, Section 6:**
> Multi-language input is an explicit requirement.
> Input resolved via alias tables to canonical IDs.

**Gap:**
- No multilingual STT model selected or validated
- No alias table schema defined
- No disambiguation strategy for homonyms across languages
- No TTS model validated for multiple languages with quality control

**Execution Path Status:** ❌ MISSING

**Impact:** Multilingual support blocked until research validates feasibility.

---

### 4. Hardware and Optimization Baseline

**Research Conclusion (Chronological Record, Phase 10):**
> System must run on median consumer hardware.
> Steam Hardware Survey identified as reference baseline.

**Secondary Pass Audit, Section 10:**
> Evaluate combined resource budgets across LLM + STT + TTS + image + critique.
> Plan GPU/CPU fallback paths.

**Gap:**
- No actual hardware spec extracted from Steam survey
- No resource budget defined (VRAM, RAM, CPU, GPU time)
- No model selection constrained by hardware
- No fallback paths designed

**Execution Path Status:** ❌ MISSING (research required)

**Impact:** Model selection and optimization strategy blocked.

---

### 5. Prep-Time Budget and Pipeline

**Research Conclusion (Secondary Pass Audit, Section 7.7):**
> DM sets expectation for prep time (e.g., ~1 hour)

**Gap:**
- No breakdown of prep phase tasks (what happens in that hour?)
- No resource allocation (which assets generated when?)
- No failure mode (what if prep exceeds budget?)
- No validation that 1 hour is sufficient for quality asset generation

**Execution Path Status:** ⚠️ UNDERSPECIFIED

**Impact:** Prep phase design blocked until pipeline defined.

---

## Action Plan Steps with No Research Justification

### 1. Voice Persona Switching (Secondary Pass Audit, Section 7.2)

**Requirement:**
> DM persona selection within first 30 seconds.
> User requests different persona; DM confirms switch.

**Missing Justification:**
- How many personas are supported? (2? 10? 100?)
- Are personas pre-generated or runtime-generated?
- What are the parameters of a persona? (tone, accent, gender, speed?)
- Can TTS models switch personas reliably?

**Research Needed:** TTS persona flexibility and quality validation

---

### 2. Dice Customization (Secondary Pass Audit, Section 7.6)

**Requirement:**
> DM asks dice preferences: big vs small, color, effects.
> Customization persists; allows later changes in conversation.

**Missing Justification:**
- Are dice assets pre-rendered or generated?
- If generated, what's the generation time? (must be < 5 seconds for onboarding)
- What are the bounds of customization? (colors? shapes? materials?)
- Does this conflict with prep-first generation strategy?

**Research Needed:** Asset generation speed and scope bounds

---

### 3. Knowledge Tome Progressive Detail (Player Artifacts, Section 3)

**Requirement:**
> Entries evolve: "Goblin — small, aggressive" → "Fast, lightly armored" → "Defense appears around 15"

**Missing Justification:**
- What triggers progression? (encounter count? explicit investigation?)
- How is partial knowledge stored and retrieved?
- How does this integrate with the LLM's contextual knowledge?
- Can the system distinguish between "player knows" vs "character knows"?

**Research Needed:** Knowledge state management and progression logic

---

### 4. Session Recap and Memory Proof (Secondary Pass Audit, Section 6.3)

**Requirement:**
> On launch, DM can recap prior sessions.
> DM can reference specific moments (e.g., "three goblins; arrow hit").

**Missing Justification:**
- How are "notable moments" identified and tagged?
- What's the summarization strategy for multi-hour sessions?
- How does the LLM retrieve and narrate from event logs?
- What if the player disagrees with the recap?

**Research Needed:** Event summarization and narrative retrieval

---

## Areas of Hand-Waving

### 1. "Canonical IDs Solve Everything"

**Pattern:** Documents assert that canonical IDs enable:
- Deterministic replay
- Multilingual input
- Skin pack swapping
- LLM memory indexing
- Ledger display

**Hand-Wave:** No document defines:
- ID format or structure
- ID namespace management
- ID collision prevention
- How IDs are assigned during content import

**Risk:** Core architectural assumption without implementation specification.

---

### 2. "Generative Assets are Deterministic"

**Pattern:** Documents claim:
- Mechanics are deterministic
- Presentation is generative
- Therefore, presentation changes don't affect determinism

**Hand-Wave:**
- Generative AI (LLM, image, TTS) is inherently non-deterministic
- "Seeding" randomness only works for numeric RNG, not neural networks
- Caching solves continuity but doesn't guarantee determinism

**Risk:** Conflation of mechanical determinism with presentation determinism.

---

### 3. "Quality Gates Prevent Bad Assets"

**Pattern:** Documents assert:
- Image critique prevents bad images
- If quality fails, regenerate
- Bounded attempts prevent infinite loops

**Hand-Wave:**
- What if all attempts fail?
- What if critique model is wrong?
- What's the user experience during regeneration?
- How long do players wait?

**Risk:** No fallback or failure mode defined.

---

### 4. "Player Modeling Adapts Automatically"

**Pattern:** Documents assert:
- System infers preferences from behavior
- DM adapts tone, verbosity, and pacing
- Explicit overrides trump inference

**Hand-Wave:**
- How long does calibration take? (1 session? 10?)
- What if inference is wrong? (annoyance risk)
- How is confidence tracked and decayed?
- Can the system distinguish between "player is tired today" vs "player prefers speed"?

**Risk:** Adaptive behavior may frustrate rather than delight.

---

### 5. "Prep Phase is Fire-and-Forget"

**Pattern:** Documents assert:
- Most generation happens during prep
- Player sees prep progress and gets excited
- Prep handoff is clean

**Hand-Wave:**
- What if prep fails? (image gen errors, TTS failures)
- Can player interrupt prep? (e.g., change campaign settings mid-prep)
- What if prep exceeds time budget?
- Is prep resumable if interrupted?

**Risk:** Prep phase may become a blocking failure mode.

---

## Risk Classification

### Determinism Risks

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|------------------|
| Generative assets introduce non-determinism | HIGH | HIGH | ⚠️ Acknowledged but not resolved |
| LLM output varies between replays | HIGH | HIGH | ❌ Not addressed |
| Cached assets diverge over time | MEDIUM | MEDIUM | ⚠️ Partial (canonical ID keying) |
| Player modeling affects outcomes | MEDIUM | LOW | ✅ Mitigated (presentation only) |

**Analysis:** Documents claim determinism but rely on non-deterministic systems. Caching solves continuity but not true determinism.

---

### Scope Creep Risks

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|------------------|
| "Reskinning all genres" becomes implicit promise | HIGH | MEDIUM | ✅ Mitigated (explicit non-goal) |
| Feature list grows beyond MVP | HIGH | HIGH | ❌ Not mitigated (no prioritization) |
| Multilingual support delays launch | MEDIUM | HIGH | ❌ Not mitigated (required for M0?) |
| Player artifacts expand in complexity | MEDIUM | MEDIUM | ⚠️ Partial (boundaries defined) |
| Sound palette generation added late | LOW | MEDIUM | ✅ Mitigated (prep-phase scoped) |

**Analysis:** Documents set explicit non-goals, but lack MVP scoping. Everything is "binding" and "locked."

---

### Tech Debt Risks

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|------------------|
| No canonical ID schema leads to refactor | HIGH | HIGH | ❌ Critical gap |
| No indexing architecture leads to LLM context overflow | HIGH | HIGH | ❌ Critical gap |
| Alias table complexity explodes with languages | MEDIUM | MEDIUM | ⚠️ Acknowledged but not designed |
| Asset caching grows unbounded | MEDIUM | MEDIUM | ❌ No cache eviction strategy |
| Player model schema evolves, breaks saves | MEDIUM | LOW | ❌ No versioning mentioned |

**Analysis:** Core systems lack foundational specs. High refactor risk if implemented without design.

---

### Coordination Risks

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|------------------|
| UI layout conflicts (chat vs ledger vs artifacts) | HIGH | HIGH | ❌ No layout integration spec |
| Player modeling conflicts with explicit settings | MEDIUM | MEDIUM | ⚠️ Partial (overrides mentioned) |
| Prep phase timing affects onboarding UX | MEDIUM | MEDIUM | ❌ Not sequenced |
| Voice output competes with text output | LOW | LOW | ✅ Mitigated (voice-first, text fallback) |

**Analysis:** Systems designed in isolation without integration planning.

---

### User Experience Risks

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|------------------|
| Prep phase 1 hour feels too long | HIGH | MEDIUM | ❌ Unvalidated assumption |
| Image quality failures break immersion | HIGH | MEDIUM | ⚠️ Quality gates help but no fallback |
| Player modeling misreads preferences | MEDIUM | HIGH | ⚠️ Overrides exist but may frustrate |
| Dice customization feels gimmicky | LOW | MEDIUM | ✅ Low stakes (cosmetic only) |
| Teaching ledger feels like homework | MEDIUM | LOW | ✅ Mitigated (passive, optional) |

**Analysis:** Several UX assumptions untested. Prep phase and player modeling are highest risk.

---

## Dependency Mapping

### Critical Path Dependencies

```
Canonical ID Schema (MISSING)
    ├── Skin Pack System
    ├── Alias Table System
    ├── Event Logging
    ├── Knowledge Tome
    └── Teaching Ledger

LLM Indexed Memory Architecture (MISSING)
    ├── Session Recap
    ├── DM Explanations
    ├── Knowledge Retrieval
    └── Consequence Justification

Image Generation + Critique (MISSING)
    ├── NPC Portraits
    ├── Location Backgrounds
    └── Item Icons

Multilingual STT/TTS (MISSING)
    ├── Voice Input/Output
    ├── Alias Resolution
    └── Localization

Hardware Resource Budget (MISSING)
    ├── Model Selection
    ├── Optimization Strategy
    └── CPU/GPU Fallback Paths

Prep Phase Pipeline (UNDERSPECIFIED)
    ├── Onboarding Handoff
    ├── Asset Generation Sequence
    └── Progress Indication
```

---

### Circular Dependencies

**Issue 1: Onboarding UX ↔ Prep Phase**
- Onboarding requires DM persona demo (needs TTS)
- TTS selection requires hardware budget (needs research)
- Research requires prep phase validation (needs pipeline design)
- Pipeline design requires onboarding time budget

**Resolution:** Break cycle by defining onboarding asset scope separately from full prep.

**Issue 2: Player Modeling ↔ Adaptive Output**
- Player modeling requires observing behavior
- Behavior observation requires interpretation (LLM)
- LLM needs player model tags to adapt output
- Output adaptation is what behavior is measured against

**Resolution:** Bootstrap with explicit calibration, then refine implicitly.

---

### Orphaned Components

**Components with no integration point:**
- Player Notebook (how does it integrate with DM memory? Can DM read it?)
- Knowledge Tome vs Handbook (separate UIs? cross-references?)
- Chat Window vs Teaching Ledger (same panel? different panels?)
- Sound Palette (how does it integrate with image generation timeline?)

---

## Research Validation Requirements

### Must Validate Before M0 Planning

| Research Track | Validation Required | Current Status |
|----------------|-------------------|----------------|
| **LLM** | Constraint adherence, multilingual, indexed memory retrieval | ❌ No results |
| **Image Gen** | Quality, speed, style consistency | ❌ No results |
| **Image Critique** | Accuracy, failure modes, fallbacks | ❌ No results |
| **STT** | Multilingual accuracy, disambiguation | ❌ No results |
| **TTS** | Naturalness, persona switching, control | ❌ No results |
| **Hardware** | Resource budgets, CPU/GPU fallback | ❌ No results |

**Blocker Status:** 🔴 CRITICAL - No research deliverables present to validate feasibility.

---

## Gap Summary

| Gap Type | Count | Severity |
|----------|-------|----------|
| **Research Conclusions Without Execution Path** | 5 | CRITICAL |
| **Action Plan Steps Without Justification** | 4 | HIGH |
| **Hand-Waving / Unspecified Details** | 5 | HIGH |
| **Missing Dependency Specifications** | 6 | CRITICAL |
| **Orphaned Integration Points** | 4 | MEDIUM |
| **Unvalidated Assumptions** | 8+ | HIGH |

---

## Risk Summary

| Risk Category | Total Risks | Critical | High | Medium | Low |
|--------------|-------------|----------|------|--------|-----|
| **Determinism** | 4 | 2 | 2 | 0 | 0 |
| **Scope Creep** | 5 | 1 | 1 | 2 | 1 |
| **Tech Debt** | 5 | 2 | 0 | 3 | 0 |
| **Coordination** | 4 | 1 | 0 | 2 | 1 |
| **User Experience** | 5 | 1 | 1 | 2 | 1 |
| **TOTAL** | 23 | 7 | 4 | 9 | 3 |

**Overall Risk Level:** 🟡 MEDIUM-HIGH

---

## Critical Blockers for M0 Planning

1. **Canonical ID Schema** - Required by 5+ systems, completely undefined
2. **LLM Indexed Memory** - Core assumption, no architecture or research validation
3. **Image Critique System** - Explicit requirement, no model identified
4. **Hardware Resource Budget** - Affects all model selection, no spec defined
5. **Research Phase Deliverables** - Mentioned as gating requirement, absent from inbox

**Recommendation:** Pause action plan development until these 5 blockers are resolved.

---

**Next Phase:** ACTION_PLAN_REVISIONS.md will propose concrete updates to reconcile gaps.
