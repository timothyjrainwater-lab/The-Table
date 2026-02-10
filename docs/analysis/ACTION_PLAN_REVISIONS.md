# AIDM Inbox - Action Plan Revisions

**Analysis Date:** 2026-02-10
**Analyst:** Agent C
**Scope:** Concrete proposals to reconcile gaps, resolve conflicts, and create executable action plan

---

## Executive Summary

This document proposes **structural revisions** to transform the inbox documents from design vision into executable roadmap. The current state is conceptually strong but operationally incomplete. These revisions prioritize research validation, scope triage, and integration clarity.

**Revision Strategy:**
1. Add missing foundational specs (canonical IDs, indexing, hardware)
2. Triage features into MVP vs post-launch
3. Sequence research → design → implementation
4. Consolidate redundant content
5. Add integration and failure mode specifications

---

## Phase 0: Document Restructuring

### Recommended Document Hierarchy

```
docs/
├── 0_ARCHITECTURE/
│   ├── CORE_PRINCIPLES.md (from Chronological Record)
│   ├── MECHANICS_VS_PRESENTATION.md (from Generative Presentation)
│   └── DETERMINISM_CONTRACT.md (NEW - explicit boundaries)
│
├── 1_CONSTRAINTS/
│   ├── ACCESSIBILITY.md (consolidate from 4 docs)
│   ├── HARDWARE_BASELINE.md (NEW - Steam survey + budgets)
│   └── SCOPE_BOUNDARIES.md (from Generative Presentation, Section 9-11)
│
├── 2_SYSTEMS/
│   ├── CANONICAL_ID_SCHEMA.md (NEW - critical missing spec)
│   ├── INDEXED_MEMORY.md (NEW - architecture and query interface)
│   ├── ASSET_PIPELINE.md (consolidate from 3 docs)
│   ├── VOICE_ARCHITECTURE.md (consolidate from 4 docs)
│   ├── PLAYER_MODELING.md (from existing spec)
│   └── UI_LAYOUT.md (NEW - integration of chat/ledger/artifacts)
│
├── 3_FEATURES/
│   ├── PLAYER_ARTIFACTS.md (from existing spec)
│   ├── TEACHING_LEDGER.md (from existing spec)
│   ├── ONBOARDING_UX.md (from Secondary Pass, Section 7)
│   └── PREP_PHASE.md (NEW - pipeline and timeline)
│
├── 4_RESEARCH/
│   ├── RESEARCH_TRACKS.md (from Chronological Record, Phase 11)
│   ├── LLM_VALIDATION.md (NEW - needs results)
│   ├── IMAGE_CRITIQUE.md (NEW - needs results)
│   ├── STT_TTS_VALIDATION.md (NEW - needs results)
│   └── HARDWARE_PROFILING.md (NEW - needs results)
│
└── 5_ROADMAP/
    ├── MVP_SCOPE.md (NEW - M0 definition)
    ├── MILESTONE_MAPPING.md (NEW - M0 through M4)
    └── IMPLEMENTATION_CHECKLIST.md (from Secondary Pass Audit)
```

---

## Phase 1: Document-Specific Revisions

### 1. Chronological Design Record

**Current Status:** Historical baseline (81 lines)
**Recommendation:** PRESERVE as-is, relocate to `0_ARCHITECTURE/CORE_PRINCIPLES.md`

**Rationale:** This document is the foundational "why" - do not modify.

**Add Cross-References:**
- Link each phase to detailed specs in other docs
- Example: "Phase 6 — Memory → See `2_SYSTEMS/INDEXED_MEMORY.md`"

---

### 2. Generative Presentation & Localization Architecture

**Current Status:** Locked requirements (127 lines)
**Recommendation:** SPLIT into 3 documents

**Split Plan:**

**A. `0_ARCHITECTURE/MECHANICS_VS_PRESENTATION.md`**
- Sections 1-2: Foundational Principle, Canonical Core
- Sections 9-11: Explicit Non-Goals, Risk Controls, Development Action Items

**B. `2_SYSTEMS/CANONICAL_ID_SCHEMA.md` (NEW)**
- Expand Section 1 into full specification
- Define ID format (e.g., `item.hand_crossbow`, `spell.fireball`)
- Define namespace rules, collision prevention, assignment process
- Add examples and validation logic

**C. `2_SYSTEMS/SKIN_PACK_SYSTEM.md` (NEW)**
- Expand Sections 3-4 into full specification
- Define skin pack schema (YAML/JSON)
- Define validation rules and import process
- Add example skin packs (fantasy, sci-fi)

**D. `2_SYSTEMS/LOCALIZATION.md` (NEW)**
- Expand Sections 5-6 into full specification
- Define language pack schema
- Define alias table structure
- Add disambiguation strategy

**Rationale:** Single 127-line doc covers 4 distinct systems. Split for clarity.

---

### 3. Minimal UI Addendum

**Current Status:** Locked UX requirements (47 lines)
**Recommendation:** MERGE into consolidated accessibility doc

**Merge Plan:**

**Target: `1_CONSTRAINTS/ACCESSIBILITY.md`**
- Pull text interaction requirements (Section: Text Interaction Layer)
- Pull visual accessibility (Section: Visual Accessibility Requirements)
- Pull from Player Artifacts (accessibility section)
- Pull from Teaching Ledger (accessibility section)
- Pull from Secondary Pass Audit (Section 8)

**Result:** Single 60-80 line accessibility governance document

**Rationale:** 4 docs repeat accessibility requirements. Consolidate once.

---

### 4. Player Artifacts

**Current Status:** Feature spec (82 lines)
**Recommendation:** ENHANCE with integration details

**Add Sections:**

**Section 4: Integration Points**
- Notebook ↔ DM Memory: Can DM read notes? Can DM reference them? Answer: No (player-owned)
- Handbook ↔ Knowledge Tome: Cross-references? Shared search? Answer: Yes (handbook is reference, tome is discovery)
- UI Layout: Separate tabs? Radial menu? Contextual access?

**Section 5: Failure Modes**
- What if player notebook grows too large? (performance)
- What if handbook search fails? (fallback to DM explanation)
- What if knowledge tome has stale entries? (versioning)

**Section 6: Milestone Assignment**
- Notebook: M0 (core immersion)
- Handbook: M1 (reference can be external initially)
- Knowledge Tome: M1 (progressive detail is post-MVP)

**Rationale:** Spec is complete but lacks integration and scoping.

---

### 5. Player Modeling & Adaptive DM Behavior

**Current Status:** Feature spec (79 lines)
**Recommendation:** ENHANCE with validation and failure modes

**Add Sections:**

**Section: Bootstrapping Strategy**
- Cold start: Explicit calibration questions during onboarding
- Warm running: Implicit inference over 3-5 sessions
- Confidence scoring: High-confidence tags persist, low-confidence decay

**Section: Failure Modes**
- Misread preference: User expresses frustration → immediate override
- Conflicting signals: Speed preference + explanation requests → prioritize explicit
- Profile drift: User changes over time → allow natural evolution

**Section: Privacy and Transparency**
- User can view player model tags
- User can reset or adjust tags conversationally
- No tracking beyond local profile

**Section: Milestone Assignment**
- Basic calibration (3 dimensions): M0
- Adaptive output (tone/verbosity): M0
- Implicit inference and decay: M1

**Rationale:** Adaptive systems need explicit failure handling and phasing.

---

### 6. Secondary Pass Audit

**Current Status:** Implementation checklist (217 lines)
**Recommendation:** REORGANIZE as milestone-mapped roadmap

**Reorganization Plan:**

**A. Extract M0-Critical Items → `5_ROADMAP/MVP_SCOPE.md`**
- Canonical ID schema (Section 1.1)
- Voice-first onboarding (Section 7)
- Basic player modeling (Section 7.3)
- Teaching ledger (Section implied)
- Text accessibility (Section 8)

**B. Extract M1+ Items → `5_ROADMAP/MILESTONE_MAPPING.md`**
- Asset logging/reuse (Section 2.2)
- Sound palette generation (Section 5)
- Implicit player inference (Section 7.3)
- Knowledge tome progression (Section implied)

**C. Extract Research Requirements → `4_RESEARCH/RESEARCH_TRACKS.md`**
- Section 11: Research Phase Requirements
- Section 3: Image critique validation
- Section 4: Voice validation
- Section 10: Hardware profiling

**D. Keep as Implementation Checklist → `5_ROADMAP/IMPLEMENTATION_CHECKLIST.md`**
- Sections 1-12 remain as acceptance criteria
- Add milestone tags to each item

**Rationale:** Audit mixes MVP, post-MVP, and research. Needs triage.

---

### 7. Teaching Ledger

**Current Status:** Feature spec (52 lines)
**Recommendation:** ENHANCE with UI integration details

**Add Sections:**

**Section: UI Layout**
- Placement: Right sidebar or bottom panel?
- Relationship to chat window: Separate or integrated?
- Collapsible? Always visible? Contextual?

**Section: Content Filtering**
- Verbosity levels: Minimal (results only) / Standard (breakdowns) / Detailed (all modifiers)
- User can adjust conversationally or via setting

**Section: Replay and Export**
- Can user copy ledger text? (yes, for accessibility)
- Can user export session log? (M1 feature)

**Section: Milestone Assignment**
- Basic ledger (rolls + modifiers): M0
- Passive education (explanations): M0
- Replay/export: M1

**Rationale:** Ledger needs UI integration and scoping.

---

## Phase 2: New Document Requirements

### 1. CANONICAL_ID_SCHEMA.md (CRITICAL)

**Purpose:** Define the format, structure, and management of canonical IDs

**Required Sections:**
1. **ID Format**
   - Namespace-qualified: `<category>.<subcategory>.<name>`
   - Examples: `weapon.ranged.hand_crossbow`, `spell.evocation.fireball`, `condition.grappled`
   - Lowercase, underscore-separated, ASCII-safe

2. **Category Namespaces**
   - Predefined: `weapon`, `armor`, `spell`, `feat`, `condition`, `action`, `monster`, `item`, `npc`, `location`, `event`
   - Extensible via import schema

3. **ID Assignment**
   - Core IDs: Hard-coded in engine
   - Imported IDs: Assigned during import, validated for uniqueness
   - Generated IDs: Hash-based for procedural content

4. **Collision Prevention**
   - Import validation rejects duplicate IDs
   - Namespace isolation (e.g., `adventure.custom.fireball` vs `spell.evocation.fireball`)

5. **Versioning**
   - IDs never change once assigned
   - Deprecated IDs marked but retained for backwards compatibility

**Status:** CRITICAL BLOCKER for M0 planning

---

### 2. INDEXED_MEMORY.md (CRITICAL)

**Purpose:** Define memory architecture and LLM query interface

**Required Sections:**
1. **Memory Structure**
   - Entity Cards: NPCs, locations, factions, items
   - Event Timeline: Turn-by-turn action log
   - Relationships: NPC-NPC, NPC-location, faction-faction
   - Open Threads: Plot hooks, unresolved questions
   - State: Inventory, conditions, HP, position

2. **Indexing Strategy**
   - Key-value store (SQLite? JSON files? In-memory?)
   - Full-text search for narrative queries
   - Structured queries for state lookups

3. **LLM Query Interface**
   - Prompt engineering: How does LLM request information?
   - Example: "What do I know about the goblin we met in the tavern?"
   - Response format: Structured data vs narrative summary

4. **Retrieval Strategy**
   - Recency bias: Recent events prioritized
   - Relevance scoring: Keyword matching, entity links
   - Context window management: Load only relevant records

5. **Failure Modes**
   - Index corruption: Rebuild from event log
   - Query ambiguity: Request clarification from player
   - Missing data: DM acknowledges gap, fills from context

**Status:** CRITICAL BLOCKER for M0 planning

---

### 3. HARDWARE_BASELINE.md (CRITICAL)

**Purpose:** Define hardware requirements and resource budgets

**Required Sections:**
1. **Minimum Spec**
   - CPU: 4 cores, 2.5 GHz (based on Steam survey median)
   - RAM: 8 GB
   - GPU: Optional (must have CPU fallback)
   - VRAM: 4 GB if GPU used
   - Disk: 10 GB for engine + 50 GB for generated assets

2. **Recommended Spec**
   - CPU: 8 cores, 3.5 GHz
   - RAM: 16 GB
   - GPU: RTX 3060 / RX 6600 equivalent
   - VRAM: 8 GB

3. **Resource Budget per Turn**
   - LLM inference: 2-5 seconds (CPU) / 0.5-1 second (GPU)
   - Image generation: Prep-phase only (not per-turn)
   - TTS generation: 1-2 seconds per utterance
   - STT processing: Real-time (< 500ms lag)

4. **Model Selection Constraints**
   - LLM: 7B params max (fits 8GB RAM)
   - Image: Stable Diffusion 1.5 / SDXL (fits 4GB VRAM)
   - TTS: Coqui XTTS / Piper (fits 2GB RAM)
   - STT: Whisper base/small (fits 1GB RAM)

5. **Fallback Paths**
   - No GPU: CPU-only inference (slower but functional)
   - Low RAM: Reduce batch size, swap models
   - Low disk: Limit asset cache size, purge old sessions

**Status:** CRITICAL BLOCKER for model selection

---

### 4. DETERMINISM_CONTRACT.md (HIGH PRIORITY)

**Purpose:** Explicitly define what is and isn't deterministic

**Required Sections:**
1. **Deterministic Components**
   - Rules engine: Given inputs, always same outputs
   - Randomness: Seeded RNG, logged, replayable
   - State transitions: No hidden state
   - Replay: Event log → identical mechanical outcomes

2. **Non-Deterministic Components (Intentional)**
   - LLM narration: Same mechanics, different words
   - Image generation: Same prompt, different outputs
   - TTS: Same text, slight prosody variation
   - Caching mitigates but doesn't eliminate variation

3. **Presentation Continuity (Separate from Determinism)**
   - NPC portraits cached (stable identity)
   - Voice profiles locked per session (stable delivery)
   - Terminology locked per session (stable language)
   - Continuity ≠ Determinism (important distinction)

4. **Replay Guarantees**
   - Mechanical replay: Exact outcomes (dice, damage, success/failure)
   - Narrative replay: May vary (LLM regenerates)
   - User expectation: Mechanical consistency, narrative flexibility

**Status:** HIGH PRIORITY - clarifies confusion in current docs

---

### 5. UI_LAYOUT.md (HIGH PRIORITY)

**Purpose:** Define spatial integration of chat, ledger, and artifacts

**Required Sections:**
1. **Layout Proposal**
   ```
   ┌──────────────────────────────────────┐
   │  [DM Narration / Scene View]         │
   │                                      │
   │  [NPC Portrait] [Background Plate]   │
   │                                      │
   └──────────────────────────────────────┘
   ┌─────────────┬────────────────────────┐
   │ Chat Window │   [Action Buttons]     │
   │ (input/out) │                        │
   └─────────────┴────────────────────────┘
   ┌─────────────┬────────────────────────┐
   │ Ledger      │   [Artifacts Tab Bar]  │
   │ (mechanics) │   Notebook | Handbook  │
   └─────────────┴────────────────────────┘
   ```

2. **Component Relationships**
   - Chat Window: Primary I/O, always visible
   - Ledger: Collapsible sidebar, opt-in visibility
   - Artifacts: Tabbed panel, contextual access
   - Scene View: Top focus, minimal UI competition

3. **Responsive Behavior**
   - Small screens: Stack vertically, collapsible panels
   - Large screens: Side-by-side layout
   - Voice-only mode: Minimize all panels, show only scene

4. **Accessibility**
   - Keyboard navigation: Tab order follows layout
   - Screen reader: Announces panel focus changes
   - Font scaling: Panels resize without breaking layout

**Status:** HIGH PRIORITY - prevents integration conflicts

---

### 6. MVP_SCOPE.md (CRITICAL)

**Purpose:** Define M0 (launch) scope with ruthless triage

**Required Sections:**
1. **M0 Core Features (Must-Have for Launch)**
   - Canonical ID system
   - Deterministic rules engine
   - Voice-first onboarding (single DM persona)
   - Basic player modeling (3 dimensions: experience, pacing, explanation depth)
   - Teaching ledger (basic roll display)
   - Chat window (text I/O)
   - NPC portraits (generated during prep, cached)
   - Background plates (generated during prep, cached)
   - Session memory (indexed records, basic recap)
   - Accessibility (text-only mode, font scaling)

2. **M0 Deferred Features (Post-Launch)**
   - Player notebook (M1 - nice-to-have, not critical)
   - Knowledge tome (M1 - progressive detail is enhancement)
   - Handbook (M1 - can use external reference initially)
   - DM persona switching (M1 - single persona sufficient for launch)
   - Dice customization (M1 - cosmetic enhancement)
   - Sound palette (M1 - audio is enhancement)
   - Multilingual input (M1 - English-only launch, expand later)
   - Implicit player modeling (M1 - explicit calibration sufficient for M0)

3. **M0 Research Validation Gates**
   - LLM: Constraint adherence, indexed memory retrieval, English narration
   - Image: Quality sufficient for portraits/backgrounds, critique validation
   - TTS: Single English voice, acceptable quality
   - STT: English input, confirmation flows
   - Hardware: Fits minimum spec (4 cores, 8GB RAM, optional GPU)

4. **M0 Success Criteria**
   - Single-session campaign playable end-to-end
   - Voice-first interaction functional
   - Text fallback always available
   - Dice rolls visible and trustworthy
   - Prep phase completes in < 10 minutes (adjusted from 1 hour)

**Status:** CRITICAL - defines launch scope

---

## Phase 3: Content Consolidation Matrix

| Topic | Current Documents | Proposed Target | Action |
|-------|------------------|----------------|--------|
| **Accessibility** | Minimal UI, Player Artifacts, Teaching Ledger, Secondary Pass (4) | `1_CONSTRAINTS/ACCESSIBILITY.md` | MERGE |
| **Voice Architecture** | Chronological, Generative Presentation, Secondary Pass, Minimal UI (4) | `2_SYSTEMS/VOICE_ARCHITECTURE.md` | CONSOLIDATE |
| **Asset Pipeline** | Chronological, Generative Presentation, Secondary Pass (3) | `2_SYSTEMS/ASSET_PIPELINE.md` | CONSOLIDATE |
| **Player Modeling** | Player Modeling Spec, Secondary Pass, Teaching Ledger (3) | `2_SYSTEMS/PLAYER_MODELING.md` | ENHANCE |
| **Onboarding UX** | Secondary Pass Section 7 (1) | `3_FEATURES/ONBOARDING_UX.md` | EXTRACT |
| **Canonical IDs** | Generative Presentation Section 1 (1) | `2_SYSTEMS/CANONICAL_ID_SCHEMA.md` | EXPAND (NEW) |

---

## Phase 4: Sequencing and Dependency Resolution

### Revised Development Sequence

**Phase R0: Research Validation (Prerequisite to M0 Planning)**
1. Hardware baseline definition (Steam survey analysis)
2. Model selection (LLM, image, TTS, STT within hardware budget)
3. Image critique validation (identify model, test failure modes)
4. Indexed memory prototype (validate LLM retrieval)
5. Multilingual feasibility study (defer to M1 if infeasible)

**Status:** MUST COMPLETE before M0 planning begins

---

**Phase M0-Pre: Foundational Systems**
1. Canonical ID schema definition and implementation
2. Indexed memory architecture and implementation
3. Event logging and replay infrastructure
4. Skin pack schema and validation

**Dependencies:** None (foundational)

---

**Phase M0-Core: Mechanical Systems**
1. Rules engine (deterministic combat, actions, conditions)
2. LLM integration (constrained narration, memory queries)
3. Asset generation pipeline (prep-phase portraits + backgrounds)
4. Image quality gate (critique + bounded regeneration)

**Dependencies:** M0-Pre complete

---

**Phase M0-Interaction: User-Facing Systems**
1. Voice-first onboarding (single persona, calibration)
2. Chat window (text I/O, accessibility)
3. Teaching ledger (basic roll display)
4. Basic player modeling (explicit calibration)
5. UI layout integration (chat + ledger)

**Dependencies:** M0-Core complete

---

**Phase M0-Polish: Launch Readiness**
1. Prep phase UX (progress indication, error handling)
2. Session memory and recap
3. Accessibility validation (text-only mode, screen reader)
4. Performance optimization (within hardware budget)

**Dependencies:** M0-Interaction complete

---

**Phase M1: Post-Launch Enhancements**
1. Player artifacts (notebook, handbook, knowledge tome)
2. DM persona switching
3. Dice customization
4. Sound palette generation
5. Implicit player modeling refinement
6. Multilingual input/output (if feasible)

**Dependencies:** M0 shipped and stable

---

## Phase 5: Governance and Process Updates

### Recommendation 1: Authority Level Clarification

**Replace blanket "locked" and "binding" with:**

| Level | Meaning | Can Change? |
|-------|---------|-------------|
| **ARCHITECTURAL** | Core design principle | Only with major refactor |
| **M0-CRITICAL** | Required for launch | Only with PM approval |
| **M0-DEFERRED** | Post-launch feature | Can be cut or moved to M2+ |
| **ASPIRATIONAL** | Future vision | Can be abandoned |

---

### Recommendation 2: Research Gating Process

**Before any "locked" requirement becomes M0-scoped:**
1. Research track validates feasibility
2. Prototype demonstrates integration
3. Failure modes identified and mitigated
4. Resource budget confirmed within hardware baseline

**Current Status:** Multiple "locked" requirements skip this gate.

---

### Recommendation 3: Continuous Integration Review

**Every 2 weeks during M0 development:**
- Review integration points between systems
- Identify UI layout conflicts early
- Validate resource budgets against hardware
- Adjust scope if necessary (defer to M1)

---

## Phase 6: Critical Path Checklist

**Must Resolve Before M0 Planning:**
- [ ] Define canonical ID schema (format, namespaces, validation)
- [ ] Design indexed memory architecture (storage, retrieval, LLM interface)
- [ ] Extract hardware baseline from Steam survey (CPU, RAM, GPU, VRAM)
- [ ] Allocate resource budgets (LLM, image, TTS, STT time/memory)
- [ ] Validate image critique approach (model selection, failure modes)
- [ ] Prototype prep phase pipeline (asset sequence, timing, progress UX)
- [ ] Clarify UI layout (chat, ledger, artifacts spatial relationships)
- [ ] Triage features into M0 vs M1 (be ruthless)

**Must Resolve During M0 Development:**
- [ ] Integrate LLM with indexed memory (validate retrieval accuracy)
- [ ] Implement image quality gate (critique + bounded regen)
- [ ] Build onboarding UX (persona greeting, calibration, prep handoff)
- [ ] Implement teaching ledger (roll display, modifier breakdown)
- [ ] Validate accessibility (text-only mode, screen reader, font scaling)
- [ ] Optimize performance (stay within hardware budget)
- [ ] Test prep phase (< 10 minutes, error handling)
- [ ] Validate session memory (recap accuracy, consequence explanations)

---

## Summary of Proposed Actions

| Action Type | Count | Examples |
|-------------|-------|----------|
| **SPLIT** | 1 | Generative Presentation → 4 documents |
| **MERGE** | 3 | Accessibility from 4 docs → 1 |
| **ENHANCE** | 4 | Player Artifacts, Player Modeling, Teaching Ledger, Secondary Pass |
| **CREATE (NEW)** | 6 | Canonical IDs, Indexed Memory, Hardware Baseline, Determinism Contract, UI Layout, MVP Scope |
| **REORGANIZE** | 1 | Secondary Pass → Milestone-mapped roadmap |
| **PRESERVE** | 1 | Chronological Record (as foundational history) |

**Total Document Changes:** 16 actions across 7 current docs → ~18 revised docs

---

**Next Phase:** SYNTHESIS_AND_RECOMMENDATIONS.md will provide executive guidance and Go/No-Go decision framework.
