# AIDM Drift & Conflict Log — Agent D Audit
## Factual Issue Register

**Agent:** Agent D (Archivist/Librarian)
**Audit Mode:** READ-ONLY GLOBAL AUDIT
**Date:** 2026-02-10
**Purpose:** Document detected inconsistencies, conflicts, and drift without proposing solutions

---

## Classification System

| Type | Definition | Example |
|------|------------|---------|
| **TERMINOLOGY_DRIFT** | Same concept, different names | "Skin Pack" vs "Presentation Plugin" |
| **SEQUENCING_CONFLICT** | Contradictory execution order | "Feature X in M1" vs "Feature X in M3" |
| **ASSUMPTION_MISMATCH** | Incompatible baseline assumptions | Doc A assumes feature exists, Doc B doesn't mention it |
| **SCOPE_AMBIGUITY** | Unclear boundaries | "Required" vs "Optional" unclear |
| **GOVERNANCE_GAP** | Missing authority claim | Multiple docs claim binding status without reconciliation |

---

## SECTION 1: TERMINOLOGY DRIFT

### DRIFT-01: Presentation Asset Names
**Type:** TERMINOLOGY_DRIFT
**Severity:** MEDIUM
**Risk:** Confusion during implementation

**Documents Involved:**
- Generative Presentation Architecture (Inbox) → "Skin Pack"
- Chronological Design Record (Inbox) → "Presentation Plugin", "Language Pack", "Voice Pack"
- Secondary Pass Audit (Inbox) → Uses all terms interchangeably

**Nature of Drift:**
- "Skin Pack" appears 8 times across 2 documents
- "Presentation Plugin" appears 3 times in 1 document
- "Language Pack" appears 5 times across 2 documents
- "Voice Pack" appears 2 times in 1 document
- Unclear whether these are synonyms or distinct concepts

**Why This Matters:**
Implementation may create 4 separate systems when only 1-2 are intended, OR implement 1 system when 4 distinct ones are needed.

**NO PROPOSED FIX** (out of scope)

---

### DRIFT-02: Player Adaptation System Names
**Type:** TERMINOLOGY_DRIFT
**Severity:** LOW
**Risk:** Documentation inconsistency

**Documents Involved:**
- Player Modeling Specification (Inbox) → "Player Modeling"
- Secondary Pass Audit (Inbox) → "Player Categorization"
- Chronological Design Record (Inbox) → "Persistent Profiling"

**Nature of Drift:**
All three documents describe the same system (adaptive DM behavior based on player preferences) using different primary terms.

**Why This Matters:**
Minimal — context makes equivalence clear. Minor documentation polish needed.

---

### DRIFT-03: UI Window Terminology
**Type:** TERMINOLOGY_DRIFT
**Severity:** MEDIUM
**Risk:** Implementation creates wrong components

**Documents Involved:**
- Minimal UI Design Addendum (Inbox) → "Text Window", "Chat Window"
- Transparent Mechanics Ledger Spec (Inbox) → "Mechanics Output Window", "Ledger"

**Nature of Drift:**
Unclear whether these are:
1. Two distinct windows (chat for I/O, ledger for mechanics)
2. One window with two purposes
3. Same window with ambiguous naming

**Why This Matters:**
Implementation may create 1 window when 2 are needed, or 2 windows when 1 is intended.

---

## SECTION 2: SEQUENCING CONFLICTS

### CONFLICT-01: No Conflicts Detected
**Status:** ✅ CLEAN

All canonical documents (Design Layer + Roadmap) have consistent sequencing. No document claims "Feature X must happen before Feature Y" while another claims the reverse.

**Note:** Inbox documents do NOT specify sequencing, only claim features are "required" or "locked."

---

## SECTION 3: ASSUMPTION MISMATCHES

### MISMATCH-01: Canonical IDs Assumption
**Type:** ASSUMPTION_MISMATCH
**Severity:** HIGH
**Risk:** Architectural gap

**Documents Involved:**
- Generative Presentation Architecture (Inbox) — **Assumes Canonical IDs exist**
  - Quote: "All mechanically relevant entities must be defined by stable, language-agnostic identifiers"
- Design Layer (BINDING) — **Does NOT mention Canonical IDs**
- Roadmap (BINDING) — **Does NOT mention Canonical IDs**

**Nature of Mismatch:**
Inbox document builds entire architecture (Skin Packs, localization, alias tables) on assumption that Canonical IDs are implemented. Design Layer and Roadmap do NOT reference this concept.

**Why This Matters:**
IF Canonical IDs do NOT exist in codebase, Inbox architecture cannot be implemented without foundational work NOT in Roadmap.

---

### MISMATCH-02: Player Modeling Existence
**Type:** ASSUMPTION_MISMATCH
**Severity:** MEDIUM
**Risk:** Scope creep

**Documents Involved:**
- Player Modeling Specification (Inbox) — **Claims "core system"**
- Roadmap M1 (BINDING) — **Does NOT mention player modeling**
- Roadmap M2 (BINDING) — **Does NOT mention player profile schema**

**Nature of Mismatch:**
Inbox document claims player modeling is "not a UX flourish" and "core system," implying it's required. Roadmap does NOT include player modeling in any milestone.

**Why This Matters:**
IF player modeling is truly "core," Roadmap is incomplete. IF it's NOT core, Inbox document overclaims authority.

---

### MISMATCH-03: Image Critique Gate
**Type:** ASSUMPTION_MISMATCH
**Severity:** MEDIUM
**Risk:** Quality vs velocity tradeoff

**Documents Involved:**
- Chronological Design Record (Inbox) — **Claims critique gate required**
  - Quote: "Image generation without image quality evaluation is unacceptable"
- Secondary Pass Audit (Inbox) — **Claims hard requirement**
  - Quote: "Image generation must be paired with critique/quality evaluation"
- Roadmap M3 (BINDING) — **Does NOT mention critique**
- Design Layer (BINDING) — **Does NOT mention critique**

**Nature of Mismatch:**
Inbox documents treat image critique as immovable constraint. Design Layer and Roadmap do NOT include critique in M3 deliverables.

**Why This Matters:**
IF critique is truly required, M3 deliverables are underspecified. IF it's NOT required, Inbox documents overstate constraint.

---

### MISMATCH-04: Player Artifacts (Notebook/Handbook/Tome)
**Type:** ASSUMPTION_MISMATCH
**Severity:** MEDIUM
**Risk:** Missing M3 deliverables

**Documents Involved:**
- Player Artifacts Specification (Inbox) — **Claims "core experiential systems"**
  - Quote: "These artifacts are not optional UX elements"
- Roadmap M3 (BINDING) — **Does NOT mention notebook, handbook, or knowledge tome**

**Nature of Mismatch:**
Inbox document claims these are foundational, non-optional. Roadmap M3 (Immersion Layer) does NOT include them in deliverables.

**Why This Matters:**
IF artifacts are truly non-optional, Roadmap M3 is incomplete. IF they're optional, Inbox document overclaims.

---

### MISMATCH-05: Skin Packs in M2
**Type:** ASSUMPTION_MISMATCH
**Severity:** HIGH
**Risk:** Architectural gap

**Documents Involved:**
- Generative Presentation Architecture (Inbox) — **Defines Skin Pack schema, import validation**
- Roadmap M2 (BINDING) — **Does NOT mention Skin Packs**

**Nature of Mismatch:**
Inbox document defines Skin Packs as core presentation architecture. Roadmap M2 (Campaign Prep) does NOT include Skin Pack schema or import validation in deliverables.

**Why This Matters:**
IF Skin Packs are required for prep-phase asset generation (as Inbox implies), M2 is underspecified. IF they're NOT required, Inbox document is out of scope.

---

## SECTION 4: SCOPE AMBIGUITY

### AMBIGUITY-01: "Locked" vs "Binding"
**Type:** SCOPE_AMBIGUITY
**Severity:** HIGH
**Risk:** Governance confusion

**Documents Involved:**
- All 7 Inbox documents use "locked" or "binding" in their claimed status

**Examples:**
- Generative Presentation Architecture: "This document formalizes and **locks** the architectural requirements"
- Player Artifacts Spec: "This document **locks** player-owned artifacts as core experiential systems"
- Player Modeling Spec: "This document elevates player categorization... to a **core system**"
- Transparent Mechanics Ledger: "This document **locks** the Mechanics Output Window as a core trust system"

**Nature of Ambiguity:**
Inbox documents claim "locked" or "binding" status, but:
1. They have NOT been formally adopted into canonical documentation
2. They are NOT referenced in Design Layer (BINDING)
3. They are NOT referenced in Roadmap (BINDING)
4. No formal decision record (DR-XXX) exists for their adoption

**Why This Matters:**
Creates authority confusion. Implementers may treat Inbox as BINDING when it's actually ADVISORY pending adoption.

---

### AMBIGUITY-02: "Prep-First" vs "Prep-Only"
**Type:** SCOPE_AMBIGUITY
**Severity:** MEDIUM
**Risk:** Implementation misinterpretation

**Documents Involved:**
- Chronological Design Record (Inbox) → "Prep-First"
- Secondary Pass Audit (Inbox) → "During Prep"
- Generative Presentation Architecture (Inbox) → No timing specified

**Nature of Ambiguity:**
"Prep-First" could mean:
1. Asset generation happens ONLY during prep (never at runtime)
2. Asset generation happens PRIMARILY during prep (runtime fallback allowed)
3. Asset generation happens PREFERABLY during prep (runtime generation acceptable)

**Why This Matters:**
Changes implementation complexity and runtime architecture significantly.

---

### AMBIGUITY-03: Canonical ID Format Undefined
**Type:** SCOPE_AMBIGUITY
**Severity:** HIGH
**Risk:** Implementation deadlock

**Documents Involved:**
- Generative Presentation Architecture (Inbox) — Mentions Canonical IDs 8+ times, NEVER defines format

**Nature of Ambiguity:**
Document claims: "All mechanically relevant entities must be defined by stable, language-agnostic identifiers"

**Unanswered Questions:**
- Format? (UUID, integer, string, composite key?)
- Namespace? (item.hand_crossbow, item_hand_crossbow, 12345?)
- Versioning? (If ID changes, how is migration handled?)
- Collision resolution? (What if two entities want same ID?)

**Why This Matters:**
Cannot implement Skin Packs, alias tables, or localization without Canonical ID specification.

---

### AMBIGUITY-04: "Median Hardware" Undefined
**Type:** SCOPE_AMBIGUITY
**Severity:** MEDIUM
**Risk:** Hardware targeting mismatch

**Documents Involved:**
- Chronological Design Record (Inbox) — "Steam Hardware Survey was identified as the reference baseline"
- Secondary Pass Audit (Inbox) — "Median hardware"
- Roadmap M4 (BINDING) — Provides hardware tiers table

**Nature of Ambiguity:**
Inbox claims "median hardware" but:
1. Steam Hardware Survey covers wide range (low-end to high-end)
2. "Median" is ambiguous (median CPU? GPU? RAM? All three?)
3. Roadmap M4 provides tiers BUT doesn't specify which is "baseline"

**Why This Matters:**
Model selection, optimization targets, and performance budgets depend on hardware baseline clarity.

---

## SECTION 5: GOVERNANCE GAPS

### GAP-01: Inbox Authority Claims Without Adoption
**Type:** GOVERNANCE_GAP
**Severity:** CRITICAL
**Risk:** Implementation proceeds without authorization

**Documents Involved:**
- All 7 Inbox documents

**Nature of Gap:**
Inbox documents claim "locked," "binding," "authoritative" status BUT:
1. NOT referenced in DOCUMENTATION_AUTHORITY_INDEX.md (CANONICAL)
2. NOT referenced in Design Layer (BINDING)
3. NOT referenced in Roadmap (BINDING)
4. No formal adoption record exists

**Why This Matters:**
Without formal adoption, Inbox docs are ADVISORY. Treating them as BINDING creates governance violation.

**Current Status:** ADVISORY pending Orchestrator approval

---

### GAP-02: Research Phase Mentioned, No Deliverables
**Type:** GOVERNANCE_GAP
**Severity:** MEDIUM
**Risk:** Blocked implementation without research completion

**Documents Involved:**
- Chronological Design Record (Inbox) — Phase 11: "Formal Research Phase Initiated"
- Secondary Pass Audit (Inbox) — Section 11: Research phase requirements

**Nature of Gap:**
Inbox documents claim research phase is "mandatory before implementation lock-in" for:
- LLM (constraint adherence, coherence, multilingual)
- Image generation + image critique
- STT (multilingual, accuracy)
- TTS (naturalness, control)
- Hardware and optimization

**Missing:**
- No research phase in Roadmap
- No research deliverables defined
- No research completion criteria
- No research blocking relationships (which milestones blocked by research?)

**Why This Matters:**
IF research is truly mandatory, Roadmap M1-M4 cannot proceed without research completion. IF it's NOT mandatory, Inbox overclaims.

---

### GAP-03: Multiple Docs, No Consolidation Record
**Type:** GOVERNANCE_GAP
**Severity:** LOW
**Risk:** Documentation maintenance burden

**Documents Involved:**
- 4 Inbox documents repeat accessibility requirements
- 4 Inbox documents describe voice architecture
- 3 Inbox documents describe asset generation

**Nature of Gap:**
High overlap without consolidation plan or single authoritative source.

**Why This Matters:**
Future updates require changing 3-4 documents simultaneously, increasing drift risk.

---

## SECTION 6: DETECTED CONTRADICTIONS

### CONTRADICTION-01: None Detected
**Status:** ✅ CLEAN

No direct contradictions found between canonical documents (Design Layer + Roadmap).

**Note:** Inbox vs Canonical gaps exist (see Section 3: Assumption Mismatches), but those are OMISSIONS not CONTRADICTIONS.

---

## SUMMARY TABLE

| ID | Type | Severity | Documents | Risk |
|----|------|----------|-----------|------|
| DRIFT-01 | Terminology Drift | MEDIUM | Presentation assets | Implementation confusion |
| DRIFT-02 | Terminology Drift | LOW | Player modeling | Documentation polish |
| DRIFT-03 | Terminology Drift | MEDIUM | UI windows | Wrong components |
| MISMATCH-01 | Assumption Mismatch | HIGH | Canonical IDs | Architectural gap |
| MISMATCH-02 | Assumption Mismatch | MEDIUM | Player modeling | Scope creep |
| MISMATCH-03 | Assumption Mismatch | MEDIUM | Image critique | Quality vs velocity |
| MISMATCH-04 | Assumption Mismatch | MEDIUM | Player artifacts | Missing M3 deliverables |
| MISMATCH-05 | Assumption Mismatch | HIGH | Skin Packs | Architectural gap |
| AMBIGUITY-01 | Scope Ambiguity | HIGH | "Locked" claims | Governance confusion |
| AMBIGUITY-02 | Scope Ambiguity | MEDIUM | "Prep-First" | Implementation misinterpretation |
| AMBIGUITY-03 | Scope Ambiguity | HIGH | Canonical ID format | Implementation deadlock |
| AMBIGUITY-04 | Scope Ambiguity | MEDIUM | Median hardware | Hardware targeting |
| GAP-01 | Governance Gap | CRITICAL | Inbox authority | Unauthorized implementation |
| GAP-02 | Governance Gap | MEDIUM | Research phase | Blocked milestones |
| GAP-03 | Governance Gap | LOW | Documentation overlap | Maintenance burden |

**Total Issues:** 15

**Critical:** 1 (GAP-01)
**High:** 4 (MISMATCH-01, MISMATCH-05, AMBIGUITY-01, AMBIGUITY-03)
**Medium:** 8
**Low:** 2

---

## MAINTENANCE NOTES

**Last Updated:** 2026-02-10
**Agent:** Agent D (Archivist)
**Mode:** READ-ONLY
**Next Update:** After Orchestrator review or corpus changes

**This log is factual only.** It documents issues, NOT solutions.

---

**END OF DRIFT & CONFLICT LOG**
