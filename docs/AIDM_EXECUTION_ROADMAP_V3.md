# AIDM Execution Roadmap v3.0
## Comprehensive Step-by-Step Implementation Plan

**Document ID:** EXEC-ROADMAP-V3
**Version:** 3.0
**Date:** 2026-02-09
**Status:** CANONICAL (Supersedes Action Plan v2.0)
**Authority:** Binding Project Specification

---

## STATUS NOTICE

This document supersedes `AIDM_PROJECT_ACTION_PLAN_V2.md` following:
- Completion of CP-20 (Discrete Environmental Damage)
- Adoption of six core design documents into the authority index
- Strategic realignment toward solo-first, voice-first, prep-first product vision

**Key Changes from v2.0:**
- Design layer is now FROZEN (no new conceptual work)
- Solo-first experience is the explicit target
- Campaign preparation is a first-class phase
- LLM integration contracts are now defined
- Contextual grid (theatre-of-the-mind-first) is mandated
- Full execution sequence is documented step-by-step

---

## Table of Contents

1. [Project State Summary](#1-project-state-summary)
2. [Design Layer Status (FROZEN)](#2-design-layer-status-frozen)
3. [Strategic Alignment Summary](#3-strategic-alignment-summary)
4. [Execution Phases Overview](#4-execution-phases-overview)
5. [Phase 1: Design Consolidation](#5-phase-1-design-consolidation)
6. [Phase 2: Engine Completion](#6-phase-2-engine-completion)
7. [Phase 3: Runtime Skeleton](#7-phase-3-runtime-skeleton)
8. [Phase 4: Solo Play Vertical Slice](#8-phase-4-solo-play-vertical-slice)
9. [Phase 5: Campaign Preparation Pipeline](#9-phase-5-campaign-preparation-pipeline)
10. [Phase 6: Immersion Enhancements](#10-phase-6-immersion-enhancements)
11. [Phase 7: Kernel Expansion (Post-MVP)](#11-phase-7-kernel-expansion-post-mvp)
12. [Detailed Task Breakdown](#12-detailed-task-breakdown)
13. [Capability Gates & Constraints](#13-capability-gates--constraints)
14. [Success Criteria](#14-success-criteria)
15. [Risk Register](#15-risk-register)

---

## 1. PROJECT STATE SUMMARY

### 1.1 What Exists (Completed)

**Deterministic Rules Engine (Layer 1):**
- CP-09 through CP-20: FROZEN
- 751 tests passing in <2 seconds
- Determinism verified (10× replay)
- RNG isolation verified (combat, initiative, saves streams)
- Event sourcing verified (all mutations via events)

**Governance Infrastructure:**
- Capability Gates defined (G-T1 OPEN, G-T2A/G-T2B/G-T3A-D CLOSED)
- 12 Structural Kernel definitions (SKR-001 through SKR-012)
- Freeze/Closure playbook established
- Documentation Authority Index active

**Design Doctrine (NEW - FROZEN):**
- Session Zero Ruleset & Boundary Config
- Character Sheet UI Contract
- Voice Intent & Clarification Protocol
- LLM–Engine Boundary Contract
- Local Runtime Packaging Strategy
- Solo-First Preparatory DM Model

### 1.2 What Does Not Exist Yet

- LLM integration runtime
- Voice I/O subsystem
- Campaign preparation pipeline
- Image/audio generation tooling
- Character sheet UI renderer
- Contextual grid renderer
- Session management
- World export/import

### 1.3 Current Milestone

**Status:** Design layer complete. Engine layer complete for Tier-1. Ready for integration layer.

---

## 2. DESIGN LAYER STATUS (FROZEN)

### 2.1 Canonical Design Documents

| Document | Status | Authority |
|----------|--------|-----------|
| `SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md` | ADOPTED | Binding |
| `CHARACTER_SHEET_UI_CONTRACT.md` | ADOPTED | Binding |
| `VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md` | ADOPTED | Binding |
| `LLM_ENGINE_BOUNDARY_CONTRACT.md` | ADOPTED | Binding |
| `LOCAL_RUNTIME_PACKAGING_STRATEGY.md` | ADOPTED | Binding |
| `SOLO_FIRST_PREPARATORY_DM_MODEL.md` | ADOPTED | Binding |

### 2.2 Design Freeze Rules

**MANDATORY:**
- No new conceptual documents without explicit amendment
- Changes require formal decision record (DR-XXX)
- Implementation must cite design documents
- Conflicts resolved by design document authority

**PERMITTED:**
- Clarification of ambiguous points
- Addition of implementation details that don't contradict doctrine
- Schema definitions that implement design contracts

---

## 3. STRATEGIC ALIGNMENT SUMMARY

### 3.1 Target Experience (Binding)

| Aspect | Decision | Reference |
|--------|----------|-----------|
| Player count | Solo-first | SF-PDM-001 |
| Primary input | Voice | VICP-001 |
| Campaign start | Preparation phase (minutes to hours) | SF-PDM-001 |
| Grid usage | Contextual (combat only) | SF-PDM-001 |
| Default mode | Theatre-of-the-mind | SF-PDM-001 |
| Execution | Fully local, offline-capable | LRP-001 |

### 3.2 Authority Hierarchy (Binding)

When narrating or resolving mechanics, defer in this order:

1. **Deterministic engine output** (Layer 1)
2. **Session Zero ruleset config**
3. **Campaign state & history**
4. **Player intent**
5. **Narrative style preferences**

The LLM is NEVER the mechanical authority.

### 3.3 Non-Negotiables

1. Determinism is absolute (identical inputs → identical outputs)
2. LLM cannot override engine results
3. No cloud dependencies
4. No ideological refusals for valid in-fiction play
5. All state changes via event log
6. Runtime < 2 seconds for test suite

---

## 4. EXECUTION PHASES OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: Design Consolidation (CURRENT)                       │
│  - Commit design documents                                      │
│  - Update authority index                                       │
│  - Freeze design layer                                          │
│  Duration: 1-2 days                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: Engine Completion                                     │
│  - Evaluate SKR-005 gate opening                                │
│  - Optional: CP-21 (minimal polish) OR skip                     │
│  - Prepare for integration layer                                │
│  Duration: 1-2 weeks                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: Runtime Skeleton                                      │
│  - Process boundaries (engine ↔ LLM ↔ voice ↔ UI)               │
│  - Event flow architecture                                      │
│  - Intent → Engine → Narration pipeline                         │
│  Duration: 2-3 weeks                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: Solo Play Vertical Slice                              │
│  - Voice input → structured intent                              │
│  - Engine resolution                                            │
│  - LLM narration output                                         │
│  - Character sheet UI updates                                   │
│  Duration: 4-6 weeks                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: Campaign Preparation Pipeline                         │
│  - DM agent orchestration                                       │
│  - Asset generation (images, audio)                             │
│  - Campaign content creation                                    │
│  - Preparation UX                                               │
│  Duration: 4-6 weeks                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 6: Immersion Enhancements                                │
│  - NPC portraits                                                │
│  - Location backdrops                                           │
│  - Ambient audio                                                │
│  - Contextual grid renderer                                     │
│  Duration: 3-4 weeks                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: Kernel Expansion (Post-MVP)                           │
│  - SKR-005 implementation (if not already)                      │
│  - True grapple, flanking, aid another                          │
│  - Additional kernel work as needed                             │
│  Duration: Ongoing                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. PHASE 1: DESIGN CONSOLIDATION

**Status:** IN PROGRESS
**Duration:** 1-2 days
**Goal:** Lock the design layer, update authority index, prepare for execution

### 5.1 Tasks

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Write all 6 design documents to `docs/design/` | ✅ COMPLETE |
| 1.2 | Update Documentation Authority Index | PENDING |
| 1.3 | Commit design documents | PENDING |
| 1.4 | Declare design layer FROZEN | PENDING |

### 5.2 Acceptance Criteria

- [ ] All 6 design documents exist in `docs/design/`
- [ ] Documentation Authority Index updated with design document references
- [ ] All documents marked ADOPTED
- [ ] Commit message references this roadmap

### 5.3 Deliverables

- `docs/design/*.md` (6 files)
- Updated `docs/DOCUMENTATION_AUTHORITY_INDEX.md`
- This roadmap document

---

## 6. PHASE 2: ENGINE COMPLETION

**Status:** NOT STARTED
**Duration:** 1-2 weeks
**Goal:** Finalize Tier-1 engine work, make gate-opening decision

### 6.1 Decision Point: SKR-005

Before proceeding, Project Authority must decide:

**Option A:** Skip CP-21, begin SKR-005 preparation immediately
- Fastest path to high-value mechanics
- Reduces technical debt

**Option B:** Execute minimal CP-21 (Ready/Delay or Initiative), then pivot
- Clean "Tier-1 complete" milestone
- Low risk

**Option C:** Continue Tier-1 expansion (NOT RECOMMENDED)
- Diminishing returns
- Delays kernel work

See `POST_CP20_DECISION_ANALYSIS.md` for full analysis.

### 6.2 Tasks (If Option A or B)

| Task | Description | Depends On |
|------|-------------|------------|
| 2.1 | Project Authority decision on CP-21/SKR-005 | Phase 1 complete |
| 2.2 | (If Option B) Execute CP-21 | 2.1 |
| 2.3 | Review SKR-005 Audit Readiness Checklist | 2.1 |
| 2.4 | Prepare G-T3C gate-opening proposal | 2.3 |
| 2.5 | Finalize engine state for integration layer | 2.2 or 2.4 |

### 6.3 Acceptance Criteria

- [ ] Engine is stable for integration (no pending Tier-1 work)
- [ ] Gate-opening decision is documented (if applicable)
- [ ] All tests pass (751+)
- [ ] Runtime < 2 seconds maintained

---

## 7. PHASE 3: RUNTIME SKELETON

**Status:** NOT STARTED
**Duration:** 2-3 weeks
**Goal:** Establish process boundaries and communication contracts

### 7.1 Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        RUNTIME SKELETON                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Voice I/O   │───→│  LLM Layer   │───→│   Engine     │      │
│  │  Subsystem   │    │  (Narrator)  │    │  (Resolver)  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ↑                   │                   │               │
│         │                   ↓                   ↓               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Player     │←───│  UI Renderer │←───│  Event Log   │      │
│  │              │    │  (Sheet/Grid)│    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Tasks

| Task | Description | Reference Doc |
|------|-------------|---------------|
| 3.1 | Define inter-process communication protocol | LEB-001 |
| 3.2 | Create Intent Object schema | VICP-001 |
| 3.3 | Create Engine Result schema | LEB-001 |
| 3.4 | Create Narration Request/Response schema | LEB-001 |
| 3.5 | Define LLM context window contract | LEB-001 §9 |
| 3.6 | Define LLM failure mode handlers | LEB-001 §10 |
| 3.7 | Create process launcher/orchestrator skeleton | LRP-001 |
| 3.8 | Implement event routing between components | All |

### 7.3 Schema Definitions Required

**Intent Object (from VICP-001 §4.1):**
```python
@dataclass
class Intent:
    actor: str                  # Entity ID
    action_type: ActionType     # move, attack, cast, etc.
    primary_target: Target      # entity, location, or area
    method: str                 # weapon, spell, maneuver, etc.
    constraints: dict           # distance, LoS, conditions
    declared_goal: str | None   # narrative intent (optional)
    status: IntentStatus        # pending, clarifying, confirmed, resolved
```

**Engine Result:**
```python
@dataclass
class EngineResult:
    intent_id: str
    success: bool
    events: list[Event]         # All events generated
    state_delta: dict           # Summary of state changes
    ruleset_references: list    # Citations
```

**Narration Request:**
```python
@dataclass
class NarrationRequest:
    engine_result: EngineResult
    scene_context: SceneContext
    style_hints: dict           # Tone, verbosity, etc.
```

### 7.4 Acceptance Criteria

- [ ] All schema definitions complete and validated
- [ ] Process communication protocol documented
- [ ] LLM containment verified (cannot mutate state directly)
- [ ] Failure mode handlers implemented
- [ ] Event routing tested

---

## 8. PHASE 4: SOLO PLAY VERTICAL SLICE

**Status:** NOT STARTED
**Duration:** 4-6 weeks
**Goal:** First playable experience: voice → intent → resolution → narration

### 8.1 Scope (Minimal Viable)

This phase delivers the **minimum viable solo combat experience**:

- Player speaks action intent
- System extracts structured intent (or clarifies)
- Engine resolves action
- LLM narrates result
- Character sheet updates
- Turn advances

**Explicitly NOT in scope:**
- Campaign creation
- Asset generation
- Multiple encounters
- Persistence across sessions

### 8.2 Tasks

| Task | Description | Depends On |
|------|-------------|------------|
| 4.1 | Integrate local STT (speech-to-text) | Phase 3 |
| 4.2 | Implement intent extraction from natural language | 4.1, Phase 3 |
| 4.3 | Implement clarification loop | 4.2 |
| 4.4 | Implement intent confirmation flow | 4.3 |
| 4.5 | Connect intent to engine resolution | 4.4 |
| 4.6 | Implement narration generation | 4.5, Phase 3 |
| 4.7 | Integrate local TTS (text-to-speech) | 4.6 |
| 4.8 | Implement basic character sheet UI | Phase 3 |
| 4.9 | Connect UI to event stream | 4.8 |
| 4.10 | Implement turn/round management UI | 4.9 |
| 4.11 | End-to-end integration test | All above |

### 8.3 Intent Lifecycle Implementation

Per VICP-001 §4.2:

```
┌──────────┐     ┌─────────────┐     ┌───────────┐     ┌──────────┐
│ PENDING  │────→│ CLARIFYING  │────→│ CONFIRMED │────→│ RESOLVED │
└──────────┘     └─────────────┘     └───────────┘     └──────────┘
     │                 │                   │                │
     │   Player spoke  │  Missing fields   │  Frozen for    │  Engine
     │   (raw input)   │  need answers     │  resolution    │  processed
```

### 8.4 Acceptance Criteria

- [ ] Player can speak "I attack the goblin with my sword"
- [ ] System extracts intent correctly
- [ ] System asks clarification when ambiguous
- [ ] Engine resolves attack correctly
- [ ] LLM narrates outcome naturally
- [ ] Character sheet reflects state changes
- [ ] Full round of combat completes successfully
- [ ] Timeout gracefully cancels unconfirmed intents
- [ ] Fallback to text input works when voice fails

### 8.5 Hardware Requirements for Testing

Per LRP-001 §6:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| LLM | 7B quantized | 13B |
| RAM | 16GB | 32GB |
| Storage | 20GB | 40GB |
| Voice | CPU-based STT/TTS | GPU-accelerated |

---

## 9. PHASE 5: CAMPAIGN PREPARATION PIPELINE

**Status:** NOT STARTED
**Duration:** 4-6 weeks
**Goal:** DM agent creates campaign content before play begins

### 9.1 Philosophy (from SF-PDM-001)

> A good DM needs time to prepare. A believable AI DM must do the same.

Campaign preparation is NOT instant. It may take minutes to an hour.

### 9.2 DM Agent Responsibilities

The DM Agent orchestrates preparation:

1. **Campaign Design**
   - Premise and themes
   - Factions and power structures
   - Conflicts and hooks

2. **Content Generation**
   - NPCs with backstories
   - Locations with descriptions
   - Encounter scaffolding

3. **Asset Preparation**
   - Request image generation for key NPCs/locations
   - Request audio themes for scenes
   - Cache assets for session use

4. **Session Zero Processing**
   - Load player configuration
   - Apply ruleset variants
   - Establish tone and boundaries

### 9.3 Tasks

| Task | Description | Depends On |
|------|-------------|------------|
| 5.1 | Design campaign data schema | Phase 3 |
| 5.2 | Implement DM Agent orchestrator | 5.1 |
| 5.3 | Implement NPC generation | 5.2 |
| 5.4 | Implement location generation | 5.2 |
| 5.5 | Implement encounter scaffolding | 5.2 |
| 5.6 | Create preparation progress UX | 5.2 |
| 5.7 | Implement asset request system | 5.2 |
| 5.8 | Implement campaign persistence | 5.1 |
| 5.9 | Implement Session Zero loader | 5.1 |
| 5.10 | End-to-end preparation test | All above |

### 9.4 Preparation Depth Presets

Per SF-PDM-001 §3.4:

| Preset | Description | Duration |
|--------|-------------|----------|
| Light | Minimal prep, faster start | 2-5 minutes |
| Standard | Balanced preparation | 10-20 minutes |
| Deep | Thorough, rich assets | 30-60 minutes |

### 9.5 Acceptance Criteria

- [ ] Player can start "new campaign"
- [ ] Preparation phase begins with ambient visuals/audio
- [ ] Progress is visible (optional indicator)
- [ ] Session Zero config is applied
- [ ] NPCs are generated with backstories
- [ ] Locations are generated with descriptions
- [ ] First encounter is ready when preparation completes
- [ ] Campaign persists to disk
- [ ] Player can resume existing campaign

---

## 10. PHASE 6: IMMERSION ENHANCEMENTS

**Status:** NOT STARTED
**Duration:** 3-4 weeks
**Goal:** Add atmospheric elements (images, audio, contextual grid)

### 10.1 Visual Assets

Per SF-PDM-001 §5:

- **NPC Portraits**: Generated during preparation, displayed during dialogue
- **Location Backdrops**: Scene images for theatre-of-the-mind
- **Encounter Imagery**: Atmospheric images for combat setup

Images are NOT interactive UI elements. They anchor imagination.

### 10.2 Audio Assets

Per SF-PDM-001 §6:

- **Ambient Sound**: Background atmosphere (tavern, forest, dungeon)
- **Music Themes**: Exploration, tension, combat
- **Sound Effects**: Impacts, spells, environmental

Audio may be generated locally or sourced from bundled libraries.

### 10.3 Contextual Grid

Per SF-PDM-001 §4:

The grid appears ONLY when spatial precision matters:
- Combat initiation
- Forced movement
- Areas of effect
- Precise positioning

The grid DISAPPEARS when no longer needed. Theatre-of-the-mind is the default.

### 10.4 Tasks

| Task | Description | Depends On |
|------|-------------|------------|
| 6.1 | Integrate local image generation tool | Phase 5 |
| 6.2 | Implement NPC portrait generation | 6.1 |
| 6.3 | Implement location backdrop generation | 6.1 |
| 6.4 | Implement image caching/retrieval | 6.1 |
| 6.5 | Integrate audio playback system | Phase 5 |
| 6.6 | Implement ambient sound selection | 6.5 |
| 6.7 | Implement music theme transitions | 6.5 |
| 6.8 | Bundle initial sound effect library | 6.5 |
| 6.9 | Implement contextual grid renderer | Phase 4 |
| 6.10 | Implement grid show/hide logic | 6.9 |
| 6.11 | Connect grid to combat state | 6.10 |

### 10.5 Acceptance Criteria

- [ ] NPC portraits appear during dialogue
- [ ] Location images display for new scenes
- [ ] Ambient audio plays appropriately
- [ ] Music transitions on scene changes
- [ ] Grid appears when combat starts
- [ ] Grid disappears when combat ends
- [ ] Assets are cached and reused
- [ ] System works without assets (graceful degradation)

---

## 11. PHASE 7: KERNEL EXPANSION (POST-MVP)

**Status:** NOT STARTED
**Duration:** Ongoing
**Goal:** Open capability gates, implement blocked mechanics

### 11.1 Priority Order

Based on SKR Dependency Graph and value analysis:

| Priority | Kernel | Gate | Unlocks |
|----------|--------|------|---------|
| 1 | SKR-005 (Relational Conditions) | G-T3C | True grapple, flanking, aid another |
| 2 | SKR-002 (Permanent Stat Modification) | G-T2A | Ability drain, restoration |
| 3 | SKR-008 (XP Economy) | G-T2B | Item creation, resurrection |
| 4 | SKR-001 (Entity Forking) | G-T3A | Summoning, animate dead |
| 5 | SKR-003 (Agency Delegation) | G-T3B | Dominate, charm |
| 6 | SKR-010 (Transformation History) | G-T3D | Polymorph, petrification |

### 11.2 Kernel Development Protocol

Per Action Plan v2.0 §5.2:

1. **Design Document** (required before code)
   - Invariants
   - State schema
   - Event types
   - API surface
   - Integration points
   - Test strategy

2. **Schema Implementation**
   - Dataclasses and validation
   - Schema tests

3. **Algorithm Implementation**
   - Core logic
   - Unit and integration tests

4. **PBHA (Packet Boundary Health Audit)**
   - 10× determinism replay
   - No regressions
   - Runtime < 2 seconds

5. **Gate Opens**
   - Kernel frozen
   - Gate status updated

### 11.3 Tasks (Per Kernel)

| Task | Description |
|------|-------------|
| 7.X.1 | Complete design document |
| 7.X.2 | Design document review and approval |
| 7.X.3 | Schema implementation |
| 7.X.4 | Schema tests passing |
| 7.X.5 | Algorithm implementation |
| 7.X.6 | Unit tests passing |
| 7.X.7 | Integration tests passing |
| 7.X.8 | PBHA audit |
| 7.X.9 | Gate status update |
| 7.X.10 | Documentation update |

---

## 12. DETAILED TASK BREAKDOWN

### 12.1 Complete Task List (All Phases)

This section provides a linear task list suitable for tracking:

```
PHASE 1: DESIGN CONSOLIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] 1.1  Write SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md
[x] 1.2  Write CHARACTER_SHEET_UI_CONTRACT.md
[x] 1.3  Write VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md
[x] 1.4  Write LLM_ENGINE_BOUNDARY_CONTRACT.md
[x] 1.5  Write LOCAL_RUNTIME_PACKAGING_STRATEGY.md
[x] 1.6  Write SOLO_FIRST_PREPARATORY_DM_MODEL.md
[ ] 1.7  Update DOCUMENTATION_AUTHORITY_INDEX.md
[ ] 1.8  Create this AIDM_EXECUTION_ROADMAP_V3.md
[ ] 1.9  Commit all design documents
[ ] 1.10 Declare design layer FROZEN

PHASE 2: ENGINE COMPLETION
━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 2.1  Project Authority decision: CP-21 vs SKR-005 pivot
[ ] 2.2  (If CP-21) Execute minimal CP-21
[ ] 2.3  Review SKR-005 Audit Readiness Checklist
[ ] 2.4  Prepare G-T3C gate-opening proposal (if applicable)
[ ] 2.5  Finalize engine state for integration

PHASE 3: RUNTIME SKELETON
━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 3.1  Define inter-process communication protocol
[ ] 3.2  Create Intent Object schema
[ ] 3.3  Create Engine Result schema
[ ] 3.4  Create Narration Request/Response schema
[ ] 3.5  Define LLM context window contract
[ ] 3.6  Define LLM failure mode handlers
[ ] 3.7  Create process launcher skeleton
[ ] 3.8  Implement event routing
[ ] 3.9  Write skeleton integration tests
[ ] 3.10 Document process boundaries

PHASE 4: SOLO PLAY VERTICAL SLICE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 4.1  Evaluate and select local STT library
[ ] 4.2  Integrate STT adapter
[ ] 4.3  Implement intent extraction (LLM-based)
[ ] 4.4  Implement clarification loop
[ ] 4.5  Implement intent confirmation flow
[ ] 4.6  Connect intent to engine resolution
[ ] 4.7  Implement narration generation (LLM-based)
[ ] 4.8  Evaluate and select local TTS library
[ ] 4.9  Integrate TTS adapter
[ ] 4.10 Implement basic character sheet UI
[ ] 4.11 Connect UI to event stream
[ ] 4.12 Implement turn/round management
[ ] 4.13 Implement timeout handling
[ ] 4.14 Implement text fallback mode
[ ] 4.15 End-to-end combat integration test
[ ] 4.16 Document vertical slice

PHASE 5: CAMPAIGN PREPARATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 5.1  Design campaign data schema
[ ] 5.2  Implement campaign storage
[ ] 5.3  Implement Session Zero loader
[ ] 5.4  Implement DM Agent orchestrator
[ ] 5.5  Implement NPC generation
[ ] 5.6  Implement location generation
[ ] 5.7  Implement encounter scaffolding
[ ] 5.8  Create preparation progress UX
[ ] 5.9  Implement asset request system
[ ] 5.10 Implement campaign resume flow
[ ] 5.11 End-to-end preparation test
[ ] 5.12 Document preparation pipeline

PHASE 6: IMMERSION ENHANCEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 6.1  Evaluate and select local image generation
[ ] 6.2  Implement image generation adapter
[ ] 6.3  Implement NPC portrait generation
[ ] 6.4  Implement location backdrop generation
[ ] 6.5  Implement image caching
[ ] 6.6  Integrate audio playback system
[ ] 6.7  Implement ambient sound selection
[ ] 6.8  Implement music transitions
[ ] 6.9  Bundle initial sound effects
[ ] 6.10 Implement contextual grid renderer
[ ] 6.11 Implement grid show/hide logic
[ ] 6.12 End-to-end immersion test
[ ] 6.13 Document immersion layer

PHASE 7: KERNEL EXPANSION
━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 7.1  SKR-005 design document finalization
[ ] 7.2  SKR-005 schema implementation
[ ] 7.3  SKR-005 algorithm implementation
[ ] 7.4  SKR-005 PBHA
[ ] 7.5  G-T3C gate opening
[ ] 7.6  (Additional kernels as prioritized)
```

### 12.2 Dependency Graph

```
Phase 1 ─────────────────────────────────────────────────────────→ Phase 2
   │                                                                  │
   │                                                                  │
   └──────────────────────────→ Phase 3 ←─────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ↓              ↓              ↓
               Phase 4        Phase 5        Phase 6
                    │              │              │
                    └──────────────┼──────────────┘
                                   │
                                   ↓
                              Phase 7
```

---

## 13. CAPABILITY GATES & CONSTRAINTS

### 13.1 Current Gate Status

| Gate | Name | Status | Notes |
|------|------|--------|-------|
| G-T1 | Tier 1 Mechanics | ✅ OPEN | All Tier-1 work complete |
| G-T2A | Permanent Stat Mutation | 🔒 CLOSED | Requires SKR-002 |
| G-T2B | XP Economy | 🔒 CLOSED | Requires SKR-008 |
| G-T3A | Entity Forking | 🔒 CLOSED | Requires SKR-001 |
| G-T3B | Agency Delegation | 🔒 CLOSED | Requires SKR-003 |
| G-T3C | Relational Conditions | 🔒 CLOSED | Requires SKR-005 |
| G-T3D | Transformation History | 🔒 CLOSED | Requires SKR-010 |

### 13.2 Constraint Enforcement

All implementation work must respect:

1. **Gate Compliance**: No mechanics that require closed gates
2. **Determinism**: All outputs reproducible from seed + inputs
3. **Event Sourcing**: All state changes via events
4. **LLM Cage**: LLM cannot override engine results
5. **Local Execution**: No cloud dependencies
6. **Runtime**: Test suite < 2 seconds

### 13.3 What's Blocked Until Kernels Exist

| Mechanic | Required Gate | Required Kernel |
|----------|---------------|-----------------|
| True grapple | G-T3C | SKR-005 |
| True flanking | G-T3C | SKR-005 |
| Aid Another | G-T3C | SKR-005 |
| Ability drain | G-T2A | SKR-002 |
| Summoning | G-T3A | SKR-001 |
| Dominate/Charm | G-T3B | SKR-003 |
| Polymorph | G-T3D | SKR-010 |

---

## 14. SUCCESS CRITERIA

### 14.1 Phase 1 Success (Design Consolidation)

- [ ] All design documents committed
- [ ] Authority index updated
- [ ] Design layer declared FROZEN

### 14.2 Phase 4 Success (Solo Play MVP)

- [ ] Player can speak actions naturally
- [ ] System clarifies ambiguous intents
- [ ] Engine resolves actions correctly
- [ ] LLM narrates outcomes appropriately
- [ ] Character sheet updates automatically
- [ ] Full combat encounter completes
- [ ] Voice and text modes both work

### 14.3 Phase 5 Success (Campaign Preparation)

- [ ] New campaign starts preparation phase
- [ ] Preparation time is visible and not "dead"
- [ ] NPCs and locations are generated
- [ ] First encounter is ready
- [ ] Campaign persists and resumes

### 14.4 Phase 6 Success (Immersion)

- [ ] Visual assets display appropriately
- [ ] Audio enhances atmosphere
- [ ] Grid appears only when needed
- [ ] System works without assets (graceful degradation)

### 14.5 Overall Product Success

The product is successful when a player can:

1. **Start a new campaign** with customized Session Zero
2. **Wait through preparation** with ambient atmosphere
3. **Play through an encounter** using voice commands
4. **See the world** through character sheet, portraits, and backdrops
5. **Hear the world** through narration, ambient sound, and music
6. **Trust the world** because outcomes are fair and consistent
7. **Save and resume** without loss of state or progress
8. **Play offline** with no external dependencies

---

## 15. RISK REGISTER

### 15.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM intent extraction accuracy | Medium | High | Robust clarification loop, text fallback |
| Voice recognition quality | Medium | Medium | Multiple STT options, text fallback |
| Local LLM performance | Medium | Medium | Hardware tiers, smaller model options |
| Image generation quality | Low | Low | Pre-generated assets, graceful degradation |

### 15.2 Scope Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Feature creep | High | High | Frozen design layer, strict phase boundaries |
| Kernel complexity underestimated | Medium | High | Start with SKR-005 (most documented) |
| Multiplayer requests | Medium | Low | Explicit solo-first scope, defer cleanly |

### 15.3 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Integration complexity | Medium | Medium | Clean process boundaries, early skeleton |
| Tooling selection delays | Low | Medium | Evaluate multiple options in parallel |
| Testing overhead | Medium | Low | Automated testing, clear acceptance criteria |

---

## APPENDICES

### A. Document References

| Document | Path | Purpose |
|----------|------|---------|
| Session Zero Config | `docs/design/SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md` | Campaign initialization |
| Character Sheet UI | `docs/design/CHARACTER_SHEET_UI_CONTRACT.md` | UI state contract |
| Voice Intent Protocol | `docs/design/VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md` | Input processing |
| LLM-Engine Boundary | `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md` | Authority separation |
| Local Runtime | `docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md` | Deployment |
| Solo-First Model | `docs/design/SOLO_FIRST_PREPARATORY_DM_MODEL.md` | Experience philosophy |
| Action Plan v2.0 | `docs/AIDM_PROJECT_ACTION_PLAN_V2.md` | Previous roadmap (superseded) |
| Post-CP20 Analysis | `docs/POST_CP20_DECISION_ANALYSIS.md` | Tier-1 saturation analysis |

### B. Glossary

| Term | Definition |
|------|------------|
| CP | Capability Packet (implementation unit) |
| SKR | Structural Kernel Register |
| PBHA | Packet Boundary Health Audit |
| G-TX | Capability Gate (e.g., G-T3C) |
| STT | Speech-to-Text |
| TTS | Text-to-Speech |
| LLM | Large Language Model |

### C. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-02-09 | Initial v3 release, incorporates design doctrine |

---

## END OF EXECUTION ROADMAP V3.0

**Status:** CANONICAL
**Next Action:** Complete Phase 1 (commit design documents, update authority index)
