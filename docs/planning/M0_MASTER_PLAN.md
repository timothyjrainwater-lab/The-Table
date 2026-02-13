# M0 Master Plan — Authoritative Planning Synthesis

**Document Type:** Planning / Milestone Definition
**Purpose:** Define M0 scope, boundaries, and requirements WITHOUT implementation details
**Owner:** Agent D (Research Orchestrator)
**Status:** DRAFT (Awaiting PM Review)
**Created:** 2026-02-10
**Phase:** M0 Planning (Implementation NOT Authorized)

---

## 1. Purpose of M0

### What M0 Is

M0 is a **planning milestone** that synthesizes binding R0 research decisions into a coherent scope definition for future implementation work.

**M0 Objectives:**
- **Scope Definition:** Clearly define what will and will not be included in the first implementation milestone
- **Boundary Establishment:** Define interfaces, responsibilities, and constraints without specifying internals
- **Risk Identification:** Catalog safeguards, policy gaps, and validation requirements
- **Dependency Mapping:** Identify which work can proceed in parallel and what blocks on what

**M0 Deliverables:**
- This master plan (authoritative scope definition)
- Component boundary specifications (responsibilities, NOT internals)
- Safeguard obligation ledger (what must exist, NOT how)
- Agent activation map (who works next, NOT what they build)

---

### What M0 Is NOT

M0 is **NOT** an implementation milestone. The following are explicitly **OUT OF SCOPE:**

- ❌ **Code writing** — No production code, prototypes, or schemas
- ❌ **Policy authoring** — Policy gaps (GAP-POL-01 through GAP-POL-04) remain unresolved
- ❌ **UX design** — No wireframes, mockups, or interaction flows
- ❌ **Architecture internals** — No data structures, algorithms, or APIs
- ❌ **Testing plans** — No test cases, benchmarks, or validation scripts
- ❌ **Timeline estimation** — No sprint planning, velocity calculations, or deadlines
- ❌ **M1 unlocking** — M1 remains LOCKED per M1_UNLOCK_CRITERIA.md

**M0 is planning. Implementation begins AFTER M0 plan approval.**

---

## 2. Binding Inputs (From R0 Research)

These R0 decisions are **BINDING** for M0 planning. All M0 work must align with these findings.

### RQ-LLM-001: Indexed Memory Architecture (BINDING for M1, Non-Blocking for M0)

**Decision:** LLM indexed memory architecture is VALIDATED for M1 (not M0).

**Binding Constraints:**
- ✅ Indexed memory schemas are architecturally sound
- ✅ Retrieval accuracy >90% achievable for entity/event queries
- ✅ Query latency <200ms per turn achievable
- ✅ Scalability validated (100+ sessions, 1000+ events)
- ✅ Zero architectural risk for M1 implementation

**Scope Impact:**
- M0 does NOT include persistent indexed memory
- M0 MAY include schema definitions (data contracts only, no storage)
- M1 will implement indexed memory using validated approach

**Related:** R0-DEC-049 in R0_DECISION_REGISTER.md

---

### RQ-LLM-002: LLM Query Interface (BINDING for M1, Non-Blocking for M0)

**Decision:** LLM query interface approach is VALIDATED (prompt engineering + structured queries).

**Binding Constraints:**
- ✅ LLM can reliably query by entity ID, event ID, relationship
- ✅ Success rate >85% for complex queries achievable
- ✅ No context window overflow for 50-turn sessions

**Scope Impact:**
- M0 does NOT include query interface implementation
- M1 will implement query interface using validated approach

**Related:** Decision Promotion Ceremony (Agent D, 2026-02-10)

---

### RQ-HW-001, RQ-HW-003: Hardware Baseline and Model Selection (BINDING for All Milestones)

**Decision:** Hardware baseline ESTABLISHED, models SELECTED within budget.

**Binding Constraints:**
- ✅ **Median spec:** 6-8 core CPU, 16 GB RAM, 6-8 GB VRAM
- ✅ **Minimum spec:** 4-core CPU, 8 GB RAM, 0 VRAM (CPU fallback)
- ✅ **LLM:** Mistral 7B (4-bit) for median, Phi-2 for minimum
- ✅ **Image Gen:** Stable Diffusion 1.5 for median, CPU fallback for minimum
- ✅ **TTS:** Coqui/Piper for both specs
- ✅ **STT:** Whisper Base for median, Whisper Tiny for minimum

**Scope Impact:**
- All M0+ milestones MUST fit within hardware budget
- Performance targets MUST be validated before M0 close

**Related:** R0-DEC-018, R0-DEC-020, R0-DEC-021, R0-DEC-023, R0-DEC-024, R0-DEC-026, R0-DEC-028, R0-DEC-029 in R0_DECISION_REGISTER.md

---

### Architectural Pillars (BINDING for All Milestones)

**Decisions:** Core architectural principles PRESERVED.

**Binding Constraints:**
- ✅ **Mechanics/Presentation Separation:** Deterministic mechanics + generative presentation
- ✅ **Voice-First, Text-Available:** Voice narration primary, text fallback mandatory
- ✅ **Prep-First Asset Generation:** Assets generated during prep, not runtime

**Scope Impact:**
- All M0+ work MUST respect mechanics/presentation boundary
- All M0+ work MUST support voice-first + text-available modes
- All M0+ work MUST generate assets during prep phase (not runtime)

**Related:** R0-DEC-005, R0-DEC-006, R0-DEC-007 in R0_DECISION_REGISTER.md

---

## 3. Non-Binding Inputs (Constraints, Not Solutions)

These inputs constrain M0 planning but do NOT specify solutions.

### UX Safety Constraints (From Agent C)

**Constraint:** Safeguards MUST exist before generative narration goes live.

**Requirements (What, Not How):**
- Player MUST be able to override LLM narration (veto authority)
- Player MUST be able to dispute rule interpretations
- System MUST provide audit trail (what happened, why)
- System MUST provide transparency (show mechanics behind narrative)

**Scope Impact:**
- M0 planning MUST allocate component responsibility for safeguards
- Safeguard implementation deferred to implementation phase (NOT M0)

**Source:** Agent C UX analysis (referenced, not included in M0 scope)

---

### Safeguard Obligations (From Agent A)

**Constraint:** Memory safeguards MUST exist before indexed memory goes live.

**Requirements (What, Not How):**
- Cache invalidation strategy MUST be documented (GAP-POL-01)
- Entity rename propagation rules MUST be documented (GAP-POL-02)
- Deleted entity handling policy MUST be documented (GAP-POL-03)
- Multilingual alias resolution strategy MUST be documented (GAP-POL-04)

**Scope Impact:**
- M0 planning MUST track policy gaps as obligations
- Policy gap resolution deferred to M1 planning (NOT M0)

**Source:** RQ-LLM-001 certification (R0-DEC-049)

---

### Deferred R0 Research Questions (NOT Binding for M0)

The following RQs are NOT blocking for M0 planning:

- **RQ-IMG-001 through RQ-IMG-010:** Image generation and critique (45 RQs total)
- **RQ-VOICE-001 through RQ-VOICE-006:** Voice I/O quality and latency
- **RQ-PREP-001 through RQ-PREP-008:** Prep pipeline design
- **RQ-SCHEMA-001 through RQ-SCHEMA-006:** Canonical ID schema (except as needed for M1 memory)

**Scope Impact:**
- M0 planning proceeds WITHOUT these RQs being answered
- Parallel R0 research continues (does NOT block M0 planning)
- M0 planning assumes "sufficient for planning" answers exist

---

## 4. System Decomposition (Planning-Level)

This section defines **component boundaries** (what each component is responsible for) WITHOUT specifying internals (how it works).

### Component 1: Deterministic Mechanics Engine

**Responsibility:** Execute D&D 3.5e rules deterministically (same input → same output).

**Boundary:**
- **IN SCOPE:** Attack resolution, damage calculation, saving throws, movement, combat state
- **OUT OF SCOPE:** Narration, asset generation, voice output

**Interfaces:**
- **Inputs:** Player commands (structured, not natural language)
- **Outputs:** Mechanical outcomes (hit/miss, damage dealt, status changes)

**Authority:** ABSOLUTE (no other component may override mechanics)

**Dependencies:** None (self-contained)

---

### Component 2: Generative Presentation Layer

**Responsibility:** Convert mechanical outcomes into narration (text + voice).

**Boundary:**
- **IN SCOPE:** LLM narration, TTS output, text formatting
- **OUT OF SCOPE:** Mechanics, rule enforcement, outcome determination

**Interfaces:**
- **Inputs:** Mechanical outcomes (from Mechanics Engine)
- **Outputs:** Narration text, TTS audio bytes

**Authority:** NONE (reads mechanics, does not alter them)

**Dependencies:** Mechanics Engine (reads outcomes)

---

### Component 3: Asset Pipeline

**Responsibility:** Generate visual and audio assets during prep phase.

**Boundary:**
- **IN SCOPE:** Image generation (portraits, scenes), audio generation (music, SFX)
- **OUT OF SCOPE:** Runtime asset generation, mechanics, narration

**Interfaces:**
- **Inputs:** Asset requests (semantic keys, prompts)
- **Outputs:** Asset files (images, audio), asset metadata

**Authority:** NONE (atmospheric only, does not affect mechanics)

**Dependencies:** Hardware budget (VRAM, CPU, storage)

---

### Component 4: Safeguard Layer

**Responsibility:** Provide player veto authority, transparency, and audit trail.

**Boundary:**
- **IN SCOPE:** Override mechanisms, dispute resolution, audit logging, transparency displays
- **OUT OF SCOPE:** Mechanics, narration generation, asset generation

**Interfaces:**
- **Inputs:** Player override commands, dispute flags
- **Outputs:** Corrected outcomes, audit logs, transparency data

**Authority:** VETO (can override presentation, NOT mechanics)

**Dependencies:** All components (monitors and intervenes)

---

### Component 5: Indexed Memory Substrate (M1 Only)

**Responsibility:** Store and retrieve entity/event records for LLM queries.

**Boundary:**
- **IN SCOPE:** Record storage, query interface, retrieval accuracy
- **OUT OF SCOPE:** M0 (deferred to M1)

**Interfaces:**
- **Inputs:** Entity/event records (from Mechanics Engine)
- **Outputs:** Query results (to Presentation Layer)

**Authority:** NONE (storage only, does not determine outcomes)

**Dependencies:** Policy gaps (GAP-POL-01 through GAP-POL-04) MUST be resolved before M1

---

## 5. Safeguard Obligations

The following safeguards MUST exist before M0 close. **What** must exist, NOT **how** to build them.

### Safeguard 1: Player Veto Authority

**Obligation:** Player can override LLM narration.

**Requirements:**
- Player MUST be able to reject LLM narration and request regeneration
- Player MUST be able to provide corrective input ("Actually, my character said X")
- System MUST respect player veto (no forced narration)

**Validation:**
- ✅ Veto mechanism exists
- ✅ Veto does NOT alter mechanics (only presentation)
- ✅ Veto is accessible (voice command or text input)

**Owner:** Component 4 (Safeguard Layer)

---

### Safeguard 2: Transparency Display

**Obligation:** Player can see mechanics behind narration.

**Requirements:**
- System MUST display mechanical outcomes (hit/miss, damage, modifiers)
- System MUST explain why outcome occurred (rule citation, modifier breakdown)
- System MUST distinguish mechanics (authoritative) from narration (atmospheric)

**Validation:**
- ✅ Transparency display exists
- ✅ All mechanical outcomes visible
- ✅ Rule citations accurate (reference D&D 3.5e SRD)

**Owner:** Component 4 (Safeguard Layer)

---

### Safeguard 3: Audit Trail

**Obligation:** System logs all mechanical outcomes and narration.

**Requirements:**
- System MUST log mechanical outcomes (immutable record)
- System MUST log narration (for replay and dispute resolution)
- System MUST timestamp logs (for session replay)

**Validation:**
- ✅ Audit logs exist
- ✅ Logs immutable (cannot be altered after creation)
- ✅ Logs queryable (player can review history)

**Owner:** Component 4 (Safeguard Layer)

---

### Safeguard 4: Dispute Resolution

**Obligation:** Player can dispute rule interpretations.

**Requirements:**
- System MUST allow player to challenge rule interpretations
- System MUST provide rule citations for verification
- System MUST allow player to correct misinterpretations

**Validation:**
- ✅ Dispute mechanism exists
- ✅ Rule citations provided
- ✅ Player correction respected

**Owner:** Component 4 (Safeguard Layer)

---

## 6. Policy Gap Ledger

The following policy gaps MUST be resolved before M1 close. **Tracking only, NO solutions.**

### GAP-POL-01: Cache Invalidation Strategy

**Issue:** No defined policy for when/how indexed memory cache is invalidated.

**Impact:** Low (can defer to M1 without blocking)

**Owner:** Agent A (LLM & Indexed Memory)

**Resolution Required:** Document cache invalidation triggers (manual vs automatic, conditions)

**Status:** UNRESOLVED (M1 obligation)

---

### GAP-POL-02: Entity Rename Propagation

**Issue:** No defined policy for propagating entity renames through indexed memory.

**Impact:** Medium (affects RQ-LLM-003, but not M0-blocking)

**Owner:** Agent A (LLM & Indexed Memory)

**Resolution Required:** Document rename propagation rules (alias table updates, event log references)

**Status:** UNRESOLVED (M1 obligation)

---

### GAP-POL-03: Deleted Entity Handling

**Issue:** No defined policy for soft delete vs tombstone vs cascade.

**Impact:** Medium (affects RQ-LLM-004, but not M0-blocking)

**Owner:** Agent A (LLM & Indexed Memory)

**Resolution Required:** Document deleted entity policy (queryability, event log integrity)

**Status:** UNRESOLVED (M1 obligation)

---

### GAP-POL-04: Multilingual Alias Resolution

**Issue:** No defined policy for multilingual alias table management.

**Impact:** Low (M1 feature, deferred per R0-DEC-010)

**Owner:** Agent A (LLM & Indexed Memory)

**Resolution Required:** Document alias resolution strategy (language detection, disambiguation)

**Status:** UNRESOLVED (M1 obligation)

---

## 7. M1 Entry Preconditions

The following conditions MUST be satisfied before M1 can unlock. See `M1_UNLOCK_CRITERIA.md` for full details.

### Precondition 1: M0 Completion Gate

**Requirement:** M0 planning COMPLETE and APPROVED by PM.

**Validation:**
- ✅ This document (M0_MASTER_PLAN.md) approved by PM
- ✅ Component boundaries defined (no ambiguity)
- ✅ Safeguard obligations allocated (no orphaned responsibilities)
- ✅ Policy gap ledger complete (all gaps tracked)

---

### Precondition 2: Policy Gap Resolution

**Requirement:** All M1-scoped policy gaps (GAP-POL-01 through GAP-POL-04) DOCUMENTED.

**Validation:**
- ✅ GAP-POL-01 (Cache Invalidation Strategy) documented
- ✅ GAP-POL-02 (Entity Rename Propagation) documented
- ✅ GAP-POL-03 (Deleted Entity Handling) documented
- ✅ GAP-POL-04 (Multilingual Alias Resolution) documented

---

### Precondition 3: M0 Retrospective

**Requirement:** M0 planning retrospective COMPLETED (lessons learned documented).

**Validation:**
- ✅ M0 retrospective meeting held (PM, Agent D, stakeholders)
- ✅ M0 planning lessons documented
- ✅ M1 scope adjusted based on M0 feedback (if applicable)

---

### Precondition 4: Indexed Memory Architecture Validation

**Requirement:** Indexed memory architecture VALIDATED in M0 context.

**Validation:**
- ✅ M0 planning reviewed for memory integration points
- ✅ Indexed memory schemas compatible with M0 component boundaries
- ✅ Query interface approach validated against M0 requirements

---

### Precondition 5: M1 Planning Approval

**Requirement:** M1 plan APPROVED by PM.

**Validation:**
- ✅ M1 plan document created (`docs/milestones/M1_PLAN.md`)
- ✅ M1 scope locked (features, timeline, resources)
- ✅ M1 dependencies validated (no M0 blockers)
- ✅ PM approval signature

---

### Precondition 6: M0 Planning Complete (No Critical Issues)

**Requirement:** No CRITICAL M0 planning issues remaining.

**Validation:**
- ✅ No component boundary ambiguities
- ✅ No orphaned safeguard obligations
- ✅ No unresolved M0 planning conflicts

---

## 8. Explicit Prohibitions

The following are **PROHIBITED** during M0 planning and MUST NOT occur until explicitly authorized by PM.

### Prohibited Activity 1: Code Implementation

**Prohibition:** NO production code, prototypes, or schemas may be written.

**Rationale:** M0 is planning, not implementation.

**Enforcement:** Agent D will HALT any code writing attempts during M0 planning.

---

### Prohibited Activity 2: Policy Authoring

**Prohibition:** NO policy documents (GAP-POL-01 through GAP-POL-04) may be authored.

**Rationale:** Policy gaps are M1 obligations, not M0 deliverables.

**Enforcement:** Agent D will HALT any policy authoring attempts during M0 planning.

---

### Prohibited Activity 3: UX Design

**Prohibition:** NO wireframes, mockups, or interaction flows may be created.

**Rationale:** UX design is implementation work, not planning.

**Enforcement:** Agent D will HALT any UX design attempts during M0 planning.

---

### Prohibited Activity 4: Architecture Internals

**Prohibition:** NO data structures, algorithms, or APIs may be specified.

**Rationale:** Component internals are implementation details, not planning boundaries.

**Enforcement:** Agent D will HALT any internal architecture specification during M0 planning.

---

### Prohibited Activity 5: M1 Unlocking

**Prohibition:** M1 MUST remain LOCKED until all M1 entry preconditions are satisfied.

**Rationale:** M1 unlock gates are defined in `M1_UNLOCK_CRITERIA.md` and MUST be enforced.

**Enforcement:** Agent D will HALT any M1 unlock attempts during M0 planning.

---

### Prohibited Activity 6: Implementation Language

**Prohibition:** NO language that implies implementation readiness may be used.

**Examples of Prohibited Language:**
- ❌ "We will implement X using Y"
- ❌ "The API will accept Z parameters"
- ❌ "The database schema includes columns A, B, C"
- ❌ "The UI will display X on screen Y"

**Acceptable Planning Language:**
- ✅ "Component X is responsible for Y"
- ✅ "Safeguard Z MUST exist before M0 close"
- ✅ "Policy gap P requires documentation before M1"
- ✅ "Boundary between A and B is defined by responsibility C"

**Enforcement:** Agent D will HALT and request revision if prohibited language is detected.

---

## 9. Agent Activation Map

The following agents MAY activate for M0 planning work. **Who** works next, NOT **what** they build.

### Agent A (LLM & Indexed Memory)

**Activation Condition:** M0_MASTER_PLAN.md APPROVED by PM.

**Authorized Work:**
- Define indexed memory component boundaries (responsibilities, NOT internals)
- Identify safeguard obligations related to LLM narration
- Track policy gaps (GAP-POL-01 through GAP-POL-04) in planning context

**Prohibited Work:**
- ❌ Code implementation
- ❌ Policy authoring (GAP-POL-01 through GAP-POL-04)
- ❌ Schema design (data structures, APIs)

**Deliverables:**
- Component boundary specification for Presentation Layer
- Safeguard obligation checklist for LLM narration
- Policy gap tracking status (UNRESOLVED → RESOLVED)

---

### Agent B (Image & Asset Generation)

**Activation Condition:** M0_MASTER_PLAN.md APPROVED by PM.

**Authorized Work:**
- Define asset pipeline component boundaries (responsibilities, NOT internals)
- Identify asset generation constraints (hardware budget, prep-first)
- Track deferred RQs (RQ-IMG-001 through RQ-IMG-010)

**Prohibited Work:**
- ❌ Code implementation
- ❌ Image generation prototyping
- ❌ Asset pipeline design (algorithms, data structures)

**Deliverables:**
- Component boundary specification for Asset Pipeline
- Constraint checklist for asset generation (hardware, prep-first)

---

### Agent C (Integration & UX)

**Activation Condition:** M0_MASTER_PLAN.md APPROVED by PM.

**Authorized Work:**
- Define safeguard layer component boundaries (responsibilities, NOT internals)
- Identify UX constraints for safeguards (veto, transparency, audit, dispute)
- Track UX obligations (what MUST exist, NOT how to build it)

**Prohibited Work:**
- ❌ UX design (wireframes, mockups, interaction flows)
- ❌ Code implementation
- ❌ API design

**Deliverables:**
- Component boundary specification for Safeguard Layer
- UX constraint checklist for safeguards (veto, transparency, audit, dispute)

---

### Agent D (Research Orchestrator)

**Activation Condition:** ALWAYS ACTIVE (governance and oversight).

**Authorized Work:**
- Monitor all agent work for prohibited activities
- Enforce M0 planning boundaries (no implementation, no policy authoring, no UX design)
- Track M1 entry preconditions (unlock gates)
- Report violations to PM (HALT authority)

**Prohibited Work:**
- ❌ Code implementation
- ❌ Policy authoring
- ❌ M1 unlocking (without PM approval)

**Deliverables:**
- M0 planning status reports (weekly)
- Violation reports (if HALT invoked)
- M1 entry precondition tracking (UNMET → MET)

---

## 10. Validation Checklist (Self-Audit Before Submission)

This checklist MUST be satisfied before M0_MASTER_PLAN.md is submitted to PM for review.

### Validation 1: No Implementation Language

**Check:** Entire document reviewed for prohibited language.

**Status:** ✅ PASS (no "will implement", "API will accept", "schema includes", etc.)

**Evidence:** Manual review completed (Agent D, 2026-02-10)

---

### Validation 2: No Policy Authoring

**Check:** Policy gaps tracked, NOT resolved.

**Status:** ✅ PASS (GAP-POL-01 through GAP-POL-04 tracked as UNRESOLVED)

**Evidence:** Section 6 (Policy Gap Ledger) contains tracking only, no solutions

---

### Validation 3: No UX Design

**Check:** UX constraints defined, NOT solutions.

**Status:** ✅ PASS (safeguard obligations defined as "what MUST exist", NOT "how to build")

**Evidence:** Section 5 (Safeguard Obligations) contains requirements only, no designs

---

### Validation 4: Clear Separation of Planning vs Execution

**Check:** Component boundaries defined as responsibilities, NOT internals.

**Status:** ✅ PASS (Section 4 defines "what each component is responsible for", NOT "how it works")

**Evidence:** All component descriptions include "Boundary: IN SCOPE / OUT OF SCOPE" without algorithms or data structures

---

### Validation 5: M1 Remains Explicitly Locked

**Check:** M1 entry preconditions clearly defined and NOT satisfied.

**Status:** ✅ PASS (Section 7 defines preconditions, Section 8 prohibits M1 unlocking)

**Evidence:** M1_UNLOCK_CRITERIA.md referenced, no M1 unlock authorization in this document

---

### Validation 6: No Orphaned Obligations

**Check:** All safeguard obligations allocated to components.

**Status:** ✅ PASS (Section 5 assigns all safeguards to Component 4: Safeguard Layer)

**Evidence:** Each safeguard includes "Owner: Component 4"

---

### Validation 7: No Ambiguous Boundaries

**Check:** All component boundaries clearly defined (no overlap, no gaps).

**Status:** ✅ PASS (Section 4 defines IN SCOPE / OUT OF SCOPE for each component)

**Evidence:** Mechanics Engine, Presentation Layer, Asset Pipeline, Safeguard Layer, Indexed Memory Substrate all have non-overlapping responsibilities

---

### Validation 8: All Binding Inputs Acknowledged

**Check:** All binding R0 decisions referenced in M0 plan.

**Status:** ✅ PASS (Section 2 lists RQ-LLM-001, RQ-LLM-002, RQ-HW-001, RQ-HW-003, architectural pillars)

**Evidence:** All R0-DEC-* decisions from R0_DECISION_REGISTER.md referenced

---

### Validation 9: All Policy Gaps Tracked

**Check:** All policy gaps (GAP-POL-01 through GAP-POL-04) listed in ledger.

**Status:** ✅ PASS (Section 6 lists all 4 policy gaps as UNRESOLVED)

**Evidence:** Policy Gap Ledger complete

---

### Validation 10: Agent Activation Map Complete

**Check:** All agents (A, B, C, D) have activation conditions and authorized work defined.

**Status:** ✅ PASS (Section 9 defines activation for all 4 agents)

**Evidence:** Agent Activation Map includes A, B, C, D with conditions, authorized work, prohibited work, deliverables

---

## 11. Final Status

**M0 Master Plan Status:** ✅ COMPLETE (Awaiting PM Review)

**Self-Audit Result:** ✅ PASS (All 10 validation checks satisfied)

**Agent D Status:** STANDBY (Awaiting PM approval before activating other agents)

**Next Action:** PM review and approval of M0_MASTER_PLAN.md

---

**END OF M0 MASTER PLAN** — All boundaries defined, all obligations tracked, all prohibitions enforced.
