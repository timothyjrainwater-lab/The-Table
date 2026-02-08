# AIDM Project Master Plan
## Deterministic D&D 3.5e AI Dungeon Master Engine

> **STATUS NOTE (2026-02-08):**
> This document is under rewrite following a governance-critical audit (AIDM_CORE_RULESET_AUDIT).
> Assumptions about monolithic spellcasting implementation are invalidated.
> **This plan is NON-CANONICAL until reissued with capability gate structure.**
>
> **Authority:** Deferred to revised version (pending DR-001 approval)

**Version:** 1.0 (SUPERSEDED - Rewrite In Progress)
**Last Updated:** 2026-02-08 (Original), 2026-02-08 (Status Note Added)
**Status:** ⚠️ UNDER REVISION
**Original Authority:** Binding Project Specification (NOW SUSPENDED)

---

## Table of Contents

1. [Project Vision & Objectives](#1-project-vision--objectives)
2. [Architecture Overview](#2-architecture-overview)
3. [Core Design Principles](#3-core-design-principles)
4. [Three-Layer Architecture](#4-three-layer-architecture)
5. [Development Phases & Roadmap](#5-development-phases--roadmap)
6. [Governance Framework](#6-governance-framework)
7. [Current Status (CP-09–CP-17)](#7-current-status-cp-09cp-17)
8. [Near-Term Roadmap (CP-18A–CP-18C)](#8-near-term-roadmap-cp-18acp-18c)
9. [Medium-Term Roadmap (CP-18–CP-20)](#9-medium-term-roadmap-cp-18cp-20)
10. [Long-Term Vision (Phases 3.7–5.0)](#10-long-term-vision-phases-3750)
11. [Risk Register](#11-risk-register)
12. [Success Metrics](#12-success-metrics)

---

## 1. Project Vision & Objectives

### 1.1 Vision Statement

Build a production-grade, deterministic D&D 3.5e combat and campaign engine that:
- Executes RAW (Rules As Written) with mathematical correctness
- Provides AI-driven DM decision-making with explicit fairness guarantees
- Supports adventure ingestion from published modules
- Maintains campaign continuity across multi-session play
- Preserves full auditability and deterministic replay

### 1.2 Primary Objectives

**Objective 1: Rules Fidelity**
Implement D&D 3.5e PHB/DMG/MM mechanics with citation-backed correctness, ensuring every resolution is traceable to source material.

**Objective 2: Deterministic Execution**
Guarantee that identical input (seed + intents) produces identical outcomes, enabling replay, debugging, and multiplayer synchronization.

**Objective 3: Fairness-Aware AI**
Build a DM policy engine that optimizes for player agency, dramatic pacing, and fiction-consistency—not just optimal tactics.

**Objective 4: Campaign Persistence**
Support long-term narrative coherence through alignment tracking, divine influence modeling, and session-linked memory.

**Objective 5: Adventure Compilation**
Enable ingestion of published adventure modules (OCR/PDF) with autonomous prep-time rulings and deterministic runtime execution.

### 1.3 Non-Goals (Explicit Exclusions)

- **No UI/UX development:** Interface contracts only; frontends are external
- **No homebrew rules:** RAW fidelity is non-negotiable
- **No real-time multiplayer:** Determinism enables async sync, but networking is out-of-scope
- **No campaign planning tools:** Module authoring is supported, but scheduling/session-management is external

---

## 2. Architecture Overview

### 2.1 Three-Layer Design

The AIDM engine is composed of three distinct layers:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Campaign & Adventure Management               │
│  - Adventure Ingestion (OCR → Module Pack)              │
│  - Campaign Memory & Alignment Tracking                 │
│  - Divine Influence & Moral Trajectory                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: DM Decision Policy Engine                     │
│  - Belief-State Tracking (Bayesian Updates)             │
│  - Multi-Objective Action Selection                     │
│  - Fairness Telemetry & Guardrails                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Deterministic Rules Engine (CP-09–CP-20)      │
│  - Event-Sourced Combat Resolution                      │
│  - RAW-Faithful Mechanics (PHB/DMG/MM)                  │
│  - RNG Stream Isolation & Replay Guarantees             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Layer Responsibilities

**Layer 1 (Rules Engine):**
- Pure deterministic resolution of game mechanics
- Event sourcing (all state changes via append-only event log)
- RNG isolation (combat, initiative, saves use independent streams)
- No AI decision-making—only validation and execution

**Layer 2 (Policy Engine):**
- Selects monster/NPC actions from legal action sets
- Optimizes for: Danger + Agency + Pace + Fairness + Fiction
- Maintains belief distributions over hidden information (HP, saves, resistances)
- Enforces fairness guardrails (no hard-locks, telegraphed lethality, counterplay preservation)

**Layer 3 (Campaign Management):**
- Compiles adventure modules (PDF → deterministic Module Pack)
- Tracks alignment drift and divine favor
- Maintains session-linked narrative memory
- Provides DM assistant mode (rules lookup, simulation, review)

### 2.3 Data Flow

```
┌──────────────┐
│ Adventure    │
│ Module (PDF) │
└──────┬───────┘
       │ OCR Ingestion (Layer 3)
       ↓
┌──────────────┐
│ Module Pack  │  ← Deterministic, Immutable Artifact
│ + Rulings    │
│   Ledger     │
└──────┬───────┘
       │ Runtime Execution
       ↓
┌──────────────┐
│ Policy       │  ← Selects Actions (Layer 2)
│ Engine       │
└──────┬───────┘
       │ Legal Intents
       ↓
┌──────────────┐
│ Rules Engine │  ← Resolves Actions (Layer 1)
│ (CP-09–20)   │
└──────┬───────┘
       │ Events + State Deltas
       ↓
┌──────────────┐
│ Event Log    │  ← Append-Only, Replay-Authoritative
└──────────────┘
```

---

## 3. Core Design Principles

### 3.1 Determinism-First

**Principle:** Identical inputs must produce identical outputs.

**Implementation:**
- RNG streams are seeded and isolated (combat, initiative, saves)
- Event ordering is strictly defined (AoO → attack → damage → save → outcome)
- All state mutations occur via event application (no hidden side effects)

**Verification:**
- 10× replay tests for every packet (same seed → same event log hash)
- State hash stability tests (deterministic across save sequences)

### 3.2 Rules-As-Written Fidelity

**Principle:** Every mechanic must be traceable to PHB/DMG/MM source material.

**Implementation:**
- All events include citations (source_id + page number)
- Rulings Ledger documents any interpretations or ambiguities
- No homebrew unless explicitly flagged and optional

**Verification:**
- Citation coverage tests (every event must have source reference)
- PHB/DMG/MM coverage audit (all mechanics tracked in Rules Coverage Ledger)

### 3.3 Event Sourcing & Auditability

**Principle:** All state changes must be derived from an append-only event log.

**Implementation:**
- WorldState is immutable (copy-on-write)
- Events are append-only with strictly increasing IDs and monotonic timestamps
- State can be reconstructed by replaying events from any point

**Verification:**
- Replay tests (state reconstruction from event log)
- Event log immutability tests (no retroactive edits)

### 3.4 Fail-Closed Design

**Principle:** Missing or invalid data should fail safely, not silently.

**Implementation:**
- Missing entities return zero modifiers (not errors)
- Invalid intents are rejected with explicit reasons
- Unknown conditions are ignored (logged as warnings)

**Verification:**
- Negative tests (verify graceful handling of missing data)
- Validation tests (illegal actions rejected before execution)

### 3.5 Separation of Concerns

**Principle:** Rules execution, AI decision-making, and narrative presentation are independent layers.

**Implementation:**
- Rules Engine (Layer 1) never makes choices—only validates and executes
- Policy Engine (Layer 2) never mutates state—only selects from legal actions
- Narrative adapters (external) consume events—never interpret mechanics

**Verification:**
- Layer isolation tests (Policy Engine cannot bypass Rules Engine validation)
- API contract tests (each layer exposes clean interfaces)

---

## 4. Three-Layer Architecture

### 4.1 Layer 1: Deterministic Rules Engine

**Status:** In Development (CP-09–CP-17 Complete, CP-18A–CP-20 Planned)

#### 4.1.1 Completed Packets (CP-09–CP-17)

| Packet | Name | Status | Test Coverage | LOC |
|--------|------|--------|---------------|-----|
| CP-09 | WorldState & Event Log | ✅ Frozen | 9 tests | 150 |
| CP-10 | Attack Resolution | ✅ Frozen | 16 tests | 280 |
| CP-14 | Initiative & Action Economy | ✅ Frozen | 12 tests | 220 |
| CP-15 | Attacks of Opportunity | ✅ Frozen | 14 tests | 310 |
| CP-16 | Conditions & Status Effects | ✅ Frozen | 14 tests | 340 |
| CP-17 | Saving Throws | ✅ Frozen | 26 tests | 396 |

**Total:** 91 tests passing, ~1,700 LOC

#### 4.1.2 Core Subsystems

**A) Event Log & State Management**
- Immutable WorldState (entities, active_combat, ruleset_version)
- Event schema (event_id, event_type, timestamp, payload, citations)
- State hash computation (deterministic serialization)

**B) Combat Resolution**
- Attack rolls (d20 + modifiers vs AC)
- Damage computation (dice + static bonuses, critical multipliers)
- HP tracking (current, max, defeat detection)

**C) Initiative & Turn Order**
- Initiative rolls (d20 + DEX modifier)
- Round advancement (turn rotation, duration ticking)
- Action economy validation (standard/move/full/swift/immediate)

**D) Attacks of Opportunity**
- Threat zone calculation (reach + positioning)
- AoO trigger detection (movement, ranged attacks, spellcasting)
- AoO resolution (interrupt → original action completion or abort)

**E) Conditions & Modifiers**
- Condition application (prone, flat-footed, grappled, stunned, shaken, sickened, etc.)
- Modifier aggregation (AC, attack, damage, saves, movement)
- Condition propagation (duration tracking, removal triggers)

**F) Saving Throws**
- Fort/Ref/Will saves (base + ability modifier + condition modifiers)
- Natural 1/20 handling (auto-fail/succeed)
- Spell Resistance (SR) checks (d20 + caster level vs SR)
- Save outcomes (SUCCESS / FAILURE / PARTIAL with damage scaling)

#### 4.1.3 RNG Isolation

| Stream | Used For | Consumption Pattern |
|--------|----------|---------------------|
| `"combat"` | Attack rolls, damage rolls | Variable (depends on attack count) |
| `"initiative"` | Initiative rolls | 1 per combatant per combat |
| `"saves"` | Save rolls, SR checks | 1–2 per save (1 if no SR, 2 if SR check) |

**Guarantee:** RNG streams are independent (save rolls do not affect combat stream state).

#### 4.1.4 Event Ordering Contract

All combat effects resolve in strict order:

1. **Target Legality** (range, LoS/LoE, type restrictions)
2. **Primary Roll** (attack, save, or opposed check)
3. **Immunity Checks** (type-based immunities)
4. **Concealment / Miss Chance** (if applicable)
5. **Spell Resistance** (if applicable)
6. **Damage / Effect Calculation** (dice + modifiers, multipliers)
7. **Mitigation** (DR, ER, hardness)
8. **Reaction Triggers** (AoOs, readied actions, immediate effects)
9. **State Update** (HP, conditions, positions, resources)
10. **Duration Ticking** (start-of-turn / end-of-turn effects)

**Guarantee:** No step may be reordered without explicit packet amendment.

---

### 4.2 Layer 2: DM Decision Policy Engine

**Status:** Planned (Phase 3.7, post-CP-20)

#### 4.2.1 Design Overview

The Policy Engine is a **multi-objective optimizer** that selects monster/NPC actions to balance:
- **Danger:** Threaten PCs without guaranteed TPK
- **Agency:** Preserve meaningful player choices and counterplay
- **Pace:** Maintain decision density and avoid resolution latency
- **Fairness:** Avoid hard-locks, telegraph lethality, ease off when variance spikes
- **Fiction:** Respect monster intelligence, morale, and doctrine

#### 4.2.2 Input Feature Set

At each decision point, the policy receives:

**A) Encounter-Level Features**
- Purpose (tutorial / resource-tax / boss / chase / puzzle-combat)
- Win conditions (kill / delay / escape / protect / disrupt)
- Expected duration (target rounds)
- Reinforcement triggers and timers

**B) Side-Level Features**
- Action economy (effective actions/round after control effects)
- Threat distribution (who is dealing damage/control)
- Resource posture (observed spell slots, charges, HP bands)
- Morale state (disciplined / cowardly / fanatical / cunning)

**C) Per-PC Inferred Features (Belief-Based)**
- Defense profile (AC/touch/flat-footed bands, save bands)
- Vulnerability flags (low Will, immobility, lack of ranged attacks)
- Offense profile (DPR band, control potency)
- Mobility profile (flight, teleport, escape tools)
- Role signature (striker / controller / support / tank / scout)

**D) Per-Monster Features**
- Doctrine / goal (protect leader, kill healer, delay, steal, escape)
- Burst potential and limited-use ability tracking
- Control suite (stun, grapple, fear, trip, etc.)
- Survivability (AC, DR, ER, SR, escape tools)
- Position leverage (reach, AoOs, flight advantage)

**E) Local Tactical Features**
- Distances and reachable squares
- Threatened squares and AoO risk
- Line of Sight (LoS) and Line of Effect (LoE) availability
- Cover and concealment vs key attackers
- Flank opportunities and choke points
- Buff/debuff timers (remaining rounds)

#### 4.2.3 Utility Function

$$U = w_1 \cdot \text{Danger} + w_2 \cdot \text{Agency} + w_3 \cdot \text{Pace} + w_4 \cdot \text{RulesIntegrity} + w_5 \cdot \text{FictionIntegrity}$$

Weights are set by encounter purpose and monster doctrine.

**Quantifiable Proxies:**
- **Danger:** PC drop probability (1–2 rounds), resource burn rate, action denial risk
- **Agency:** Counterplay availability, telegraphing strength, outcome sensitivity to player choices
- **Pace:** Decision density, swing moments frequency, resolution latency (avoid complex stalls)

#### 4.2.4 Candidate Generation

Given current state, enumerate **only rules-legal candidates**:
- **Damage line:** Focus fire, burst damage
- **Control line:** Deny key actions, forced repositioning
- **Reposition line:** Gain cover, break LoE, set flanks, choke control
- **Objective line:** Interact, escape, trigger hazard
- **Defensive line:** Withdraw, total defense, heal, buff
- **Exit line:** Flee, surrender, bargain when morale breaks

**Contract:** All candidates must be validated by the combat legality checker (Layer 1) before scoring.

#### 4.2.5 Scoring & Selection

For each legal action $a$, compute:
- $P_{\text{success}}(a)$ using discrete d20 math (exact counts, no approximations)
- $\text{EV}_{\text{damage}}(a)$ or $\text{EV}_{\text{effect}}(a)$ including mitigation and miss gates
- $\Delta \text{ActionEconomy}(a)$ (expected actions denied/preserved next round)
- $\Delta \text{PositionLeverage}(a)$ (cover, flanks, AoO advantage, LoE denial)
- $\Delta \text{Survival}(a)$ (monster survival probability change)
- $\text{Counterplay}(a)$ (does this leave meaningful responses?)
- $\text{Complexity}(a)$ (penalize slow adjudication)
- $\text{FictionFit}(a)$ (doctrine, intelligence, morale constraints)

**Selection Policy:**
- **Argmax** when clearly dominant
- **Softmax** over top-k when close (temperature/"spice" parameter)
- Personality affects aggression/caution balance

**Result:** Variety without breaking fairness.

#### 4.2.6 Belief-State Tracking

The policy operates under incomplete information:
- Unknown HP (by design)
- Unknown saves, DR, ER, SR initially

**Conservative Update Rules:**
- Use evidence thresholds (no single-result shifts)
- Weight updates by likelihood under current belief (surprising outcomes update more, but bounded)
- Apply decay/smoothing (early observations do not permanently lock in)
- Track sample size per hypothesis (e.g., fire resistance requires ≥2–3 relevant observations)
- Treat crits, concealment misses, and failed confirmations as high-variance signals (down-weight)

**Example:**
- If fire spell repeatedly deals reduced damage → increase belief in fire resistance
- If Will saves repeatedly fail → lower Will band belief

**Contract:** Beliefs influence scoring but never override RAW legality.

#### 4.2.7 Fairness Guardrails

**Hard Constraints (Must Not Violate):**
- No repeated hard-lock loops (stun/pin/fear chain) without counterplay unless encounter is explicitly apex
- No un-telegraphed lethal spikes as default policy
- Always preserve at least one viable response line when feasible

**Soft Penalties (Discourage But Allow When Justified):**
- Penalize action denial if it reduces player turns for multiple rounds
- Penalize focus fire if it produces early drops in non-apex fights
- Penalize high-adjudication-complexity if pacing budget is tight

**Fairness Telemetry (Inputs the Policy Must Track):**
- **Early-drop risk:** ≥2 PCs down within first N rounds
- **Counterplay deficit:** No viable responses detected
- **Variance spike:** Extreme crit streaks or swing events
- **Confusion signal:** Repeated player clarification prompts

**Ease-off Mechanisms (Fiction-Consistent):**
- Morale breaks / tactical retreat
- Target switching consistent with monster intelligence
- Overconfidence or misplays that remain believable
- Shift from denial to pressure (zone control, reposition, objective play)

**Contract:** Guardrails are part of scoring as explicit penalties/constraints—not optional advice.

---

### 4.3 Layer 3: Campaign & Adventure Management

**Status:** Planned (Phases 4–5, post-Policy-Engine)

#### 4.3.1 Adventure Ingestion (Two-Phase Model)

**Phase A: Ingestion & Compilation (Non-Authoritative)**

**Inputs:**
- OCR PDF of adventure module
- Optional user configuration (fidelity level, tone, danger level)

**Allowed Behaviors:**
- Natural-language interpretation of prose
- Extraction of encounters, locations, NPCs, hooks
- Invention of missing mechanical details (DCs, monster counts, treasure placement)
- Re-sequencing or restructuring scenes for internal coherence

**Ruling Policy:**
- If a "true RAW answer" cannot be derived, the system must make a ruling
- The system must not defer endlessly or request user arbitration by default

**Outputs:**
- **Module Pack** (structured, versioned, deterministic artifact)
- **Rulings Ledger** (append-only record of interpretations):
  - Source excerpt reference (page/section when available)
  - Nature of ambiguity
  - Chosen ruling
  - Rationale

**Contract:** Module Pack becomes the authoritative artifact for runtime.

**Phase B: Runtime Execution (Authoritative & Deterministic)**

At runtime:
- The engine does **not** reinterpret the PDF
- The engine does **not** invent new rules or rulings
- The engine executes the Module Pack exactly like any other authored scenario

**Contract:** Any further ambiguity must be handled by preconfigured runtime policies or explicit, logged runtime rulings (rare, surfaced clearly).

#### 4.3.2 Module Pack Definition (v0)

A Module Pack is treated as authored campaign content.

**Minimum Required Sections:**
- **Metadata** (title, source, ingestion timestamp, version)
- **Global Assumptions** (tone, lethality, interpretation policies)
- **Scene Graph** (locations, transitions)
- **Encounters** (monsters, tactics hints, triggers)
- **NPCs** (stats or references, motivations)
- **Treasure & Rewards**
- **Rulings Ledger** (append-only)

**Contract:** Module Packs are immutable once runtime begins.

#### 4.3.3 Play Lanes (Unified Runtime)

The system supports three play lanes that differ only in content source:

| Lane | Content Source | Authorship |
|------|----------------|------------|
| **Sandbox Lane** | Procedurally generated | System-generated (deterministic seeds + world facts) |
| **Scenario-Setting Lane** | Manually authored Module Packs | Human or system-generated |
| **Adventure-Book Lane** | Module Packs from OCR/PDF ingestion | Published adventure modules |

**Contract:** All lanes share the same deterministic runtime, combat engine, event log, and replay guarantees.

#### 4.3.4 Campaign Memory & Alignment Tracking

**Alignment Evidence Records (Schema-Only, Phase A):**
- Session-linked evidence entries (immutable)
- Linkage to session ledgers (event IDs, timestamps)
- Validation rules (fail-closed)

**Alignment Drift Evaluation (Analytical Layer, Phase B):**
- Periodic evaluation (session-windowed, not real-time)
- Trend detection rules (sustained patterns, not single events)
- Threshold definitions (configurable per table)
- Player-facing explanation format (traceable to evidence)

**Divine Influence & Religious Consequences (Phase C):**
- Deity value and alignment expectation data
- Favor / disfavor tracking (behavior-based evaluation)
- Narrative signaling rules (warnings before mechanical consequences)
- Mechanical consequence hooks (RAW-aligned, citation-backed)

**Contract:** No action is blocked by alignment systems. Alignment influences world response, not permissions.

#### 4.3.5 DM Assistant Mode

**Purpose:** Support human-run games or module preparation (not replace deterministic engine).

**Capabilities:**
- **Rules Lookup** with citation
- **Outcome Simulation** ("What if this encounter runs?")
- **Ingestion Review** (inspect rulings, edit Module Packs)
- **Non-Binding Tactical Advice**

**Restrictions:**
- Cannot mutate canonical WorldState without explicit command
- Cannot silently apply rulings during runtime

---

## 5. Development Phases & Roadmap

### 5.1 Phase Overview

| Phase | Name | Status | Duration (Est.) |
|-------|------|--------|-----------------|
| **Phase 0** | Vertical Slice | ✅ Complete | 2 weeks |
| **Phase 1** | Core Combat Kernels (CP-09–CP-17) | ✅ Complete | 3 months |
| **Phase 2** | Cross-Cutting Kernels (CP-18A–CP-18C) | 🔄 In Progress | 3 months |
| **Phase 3** | High-Level Systems (CP-18–CP-20) | 📋 Planned | 4 months |
| **Phase 3.7** | DM Policy Engine | 📋 Planned | 3 months |
| **Phase 4** | Adventure Ingestion | 📋 Planned | 4 months |
| **Phase 5** | Campaign Memory & Alignment | 📋 Planned | 3 months |

**Total Estimated Timeline:** 18–22 months from project start

### 5.2 Phase 1: Core Combat Kernels (Complete)

**Goal:** Build deterministic, event-sourced combat resolution with replay guarantees.

**Deliverables:**
- ✅ CP-09: WorldState & Event Log
- ✅ CP-10: Attack Resolution
- ✅ CP-14: Initiative & Action Economy
- ✅ CP-15: Attacks of Opportunity
- ✅ CP-16: Conditions & Status Effects
- ✅ CP-17: Saving Throws

**Exit Criteria:**
- All tests passing (91/91)
- Deterministic replay verified (10× same seed → same hash)
- RNG streams isolated (combat, initiative, saves independent)
- Event ordering contract enforced (AoO → attack → damage → save)

**Status:** ✅ Complete (2026-02-08)

---

## 6. Governance Framework

### 6.1 Packet Boundary Health Audit (PBHA)

**Purpose:** Verify packet freeze-readiness before declaring a packet complete.

**Trigger:** When a packet's acceptance tests pass and implementation is complete.

**Audit Areas:**
1. **Correctness:** All acceptance tests pass, edge cases covered
2. **Determinism:** 10× replay test passes, state hash stability verified
3. **Integration:** No regressions in dependent packets
4. **Continuity:** Next packet(s) unblocked, no deferred work leaked

**Output:** PASS (freeze packet) or FAIL (blocking defects identified).

**Authority:** PBHA findings are binding; packets cannot freeze until PASS.

### 6.2 Cross-Cutting Mechanics Audit (CCMA)

**Purpose:** Detect RAW subsystems that violate engine assumptions if treated as emergent behavior.

**Trigger:**
- A new interaction class is introduced
- A packet alters assumptions about actor identity, position, or action ownership

**Scope:**
- Examine PHB, DMG, MM mechanics
- Identify subsystems that:
  - Span two or more kernels
  - Introduce composite or coupled actors
  - Cause bidirectional state propagation

**Required Outputs:**
- Updated Rules Coverage Ledger (RCL)
- Gap Register (uncovered or mis-sequenced subsystems)
- Sequencing proposal for newly discovered packets

**Authority:** CCMA findings are binding once merged.

### 6.3 Rules Coverage Ledger (RCL)

**Definition:** Canonical, append-only project artifact that enumerates all RAW mechanical subsystems relevant to runtime play.

**Each Entry Must Include:**
- Subsystem name
- Source reference (PHB / DMG / MM section)
- Classification: `atomic` | `cross-cutting` | `dm-discretion`
- Coverage status: `implemented` | `partial` | `deferred` | `out_of_scope`
- Owning packet (CP-## or amendment)
- Determinism risk: `low` | `medium` | `high`
- Notes (edge cases, propagation rules, known hazards)

**Governance Rule:** No packet may be frozen unless all subsystems it touches are present in the RCL with explicit coverage status.

**Authority:** Silence is forbidden. Every subsystem must have a declared disposition.

### 6.4 Structural Kernel Register (SKR)

**Definition:** Required project artifact listing all known structural kernels.

**Each Entry Must Include:**
- Kernel name
- Status: `Implemented` | `Planned` | `Deferred`
- Owning packet (CP-##)
- Blocking status (which packets depend on this kernel)
- Description (what assumptions it violates)

**Governance Rule:** Future packet design must reference the SKR explicitly.

**Current Known Kernels (SCA-MM-1 Findings):**

| Kernel | Status | Owner | Blocking |
|--------|--------|-------|----------|
| Mounted Combat / Composite Actors | 📋 Planned | CP-18A | Spells, Maneuvers |
| Targeting & Visibility (LoS, cover, concealment, invisibility) | 📋 Planned | CP-18B | Spells |
| Forced Movement & Collision | 📋 Planned | CP-18C | Maneuvers |
| Flight & 3D Positioning | 🔮 Deferred | CP-19+ | Environmental |
| Grapple (Full RAW) | 🔮 Deferred | CP-19+ | Maneuvers |
| Charge (Full RAW) | 🔮 Deferred | CP-19+ | Maneuvers |
| Swarm Traits | 🔮 Deferred | CP-19+ | Monster Abilities |
| Incorporeal Targeting Exceptions | 🔮 Deferred | CP-19+ | Monster Abilities |
| Environmental Mode Replacement (underwater) | 🔮 Deferred | CP-19+ | Environmental |
| Triggered Reactions (Death Throes) | 🔮 Deferred | CP-19+ | Monster Abilities |

### 6.5 Frozen Packet Policy

**Definition:** A "frozen" packet is locked against behavioral changes but may be extended via backward-compatible additions.

**Safe Extensions:**
- Add new fields (with defaults)
- Add new optional parameters
- Add new event types

**Breaking Changes (Forbidden):**
- Alter existing event schemas
- Change function signatures
- Modify resolution order

**Governance:** Breaking changes require a major version bump (AIDM 2.0) and compatibility shim.

---

## 7. Current Status (CP-09–CP-17)

### 7.1 Implementation Summary

**Completed Packets:** CP-09, CP-10, CP-14, CP-15, CP-16, CP-17
**Test Coverage:** 91 tests passing (20 save + 6 integration + 14 condition + 16 attack + 12 initiative + 9 state + 14 AoO)
**Lines of Code:** ~1,700 LOC (core engine only)
**Determinism Verified:** 10× replay tests passing for all packets
**RNG Isolation Verified:** Combat, initiative, saves streams independent

### 7.2 Key Subsystems Operational

- ✅ Event-sourced state management (WorldState, Event Log)
- ✅ Attack resolution (d20 vs AC, damage, critical hits)
- ✅ Initiative & action economy (round advancement, turn rotation)
- ✅ Attacks of Opportunity (threat zones, trigger detection, interrupt resolution)
- ✅ Conditions (prone, flat-footed, grappled, stunned, shaken, sickened, dazed, helpless)
- ✅ Saving throws (Fort/Ref/Will, Natural 1/20, Spell Resistance, partial saves)

### 7.3 Architectural Achievements

**Deterministic Replay:**
- Identical seed → identical event log hash (verified across all packets)
- State reconstruction from event log (replay from any point)

**RNG Isolation:**
- Combat stream (attack rolls, damage rolls)
- Initiative stream (initiative rolls)
- Saves stream (save rolls, SR checks)
- No cross-contamination (verified via isolation tests)

**Event Ordering:**
- AoO → Attack → Damage → Save → Outcome (strict contract enforced)
- No mid-turn interrupts (AoO resolution completes before original action)

**Fail-Closed Design:**
- Missing entities return zero modifiers (not errors)
- Invalid intents rejected with explicit reasons
- Unknown conditions ignored (logged as warnings)

### 7.4 Known Limitations (Deferred)

**Deferred to CP-18+:**
- Poison (secondary saves, incubation, multi-phase tracking)
- Disease (incubation, stat degradation over time)
- Attack riders (poison-on-hit, automatic save triggers)
- Evasion feat (Reflex save → zero damage)

**Deferred to CP-19+:**
- Triggered Reactions (Death Throes, reactive abilities)
- Duration tracking (rounds/minutes/hours/days)
- Delayed event scheduling

**Explicitly Out-of-Scope (CP-20+):**
- Readied actions (interrupt-driven execution, natural-language triggers)
- Delay actions (initiative reshuffling mid-round)

---

## 8. Near-Term Roadmap (CP-18A–CP-18C)

### 8.1 CP-18A: Mounted Combat & Rider–Mount Coupling

**Status:** 📋 Next Up
**Duration:** 3–4 weeks (estimated)
**Prerequisites:** CP-14, CP-15, CP-16, CP-17 (all complete)

**Scope (Non-Negotiable):**
- Rider–mount coupling state
- Controlled vs independent mounts
- Shared movement and AoO routing
- Mounted attack modifiers and charge rules
- Save and condition propagation (mount ↔ rider)
- Dismount and fall resolution

**Explicit Non-Goals:**
- Exotic mounts (phasm, nightmare, etc.)
- Mounted spellcasting edge cases
- Ride skill optimization beyond legality checks

**Acceptance Criteria:**
- ≥15 unit tests (coupling, movement, AoO, saves, conditions)
- ≥5 integration tests (full mounted combat scenarios)
- Determinism verified (10× replay)
- RNG isolation maintained
- Backward compatibility (all CP-09–CP-17 tests pass)

**Blocking:** CP-18B (Targeting), CP-18 (Maneuvers) depend on composite actor model.

---

### 8.2 CP-18B: Targeting & Visibility Kernel

**Status:** 📋 Planned
**Duration:** 4–5 weeks (estimated)
**Prerequisites:** CP-18A (Mounted Combat)

**Scope (Minimal Viable):**
- Line of Sight (LoS) and Line of Effect (LoE)
- Cover (partial vs total)
- Concealment (miss chance)
- Area targeting (cone, line, burst, emanation)
- Threatened square calculation (reach + positioning)

**Deferred to CP-19+:**
- Invisibility (observational state is hard)
- Blindsight, tremorsense, scent (sensory modes)
- Illusions and disbelief (epistemic state)

**Acceptance Criteria:**
- ≥20 unit tests (LoS, LoE, cover, concealment, area targeting)
- ≥6 integration tests (full targeting scenarios)
- Determinism verified (10× replay)
- RNG isolation maintained
- Backward compatibility

**Blocking:** CP-18 (Spells) depend on area targeting and LoS/LoE.

---

### 8.3 CP-18C: Forced Movement & Collision

**Status:** 📋 Planned
**Duration:** 3–4 weeks (estimated)
**Prerequisites:** CP-18A (Mounted Combat), CP-18B (Targeting)

**Scope:**
- Bull rush (forced linear movement)
- Overrun (forced movement through space)
- Trip (forced prone condition)
- Collision detection (solid obstacles, other creatures)
- Fall damage (vertical forced movement)
- Push effects (generic forced repositioning)

**Deferred to CP-19+:**
- Grapple (complex state machine, pin/escape sequences)
- Drag/reposition maneuvers

**Acceptance Criteria:**
- ≥15 unit tests (bull rush, overrun, trip, collision, fall)
- ≥5 integration tests (forced movement chains)
- Determinism verified (10× replay)
- RNG isolation maintained
- Backward compatibility

**Blocking:** CP-18 (Maneuvers) depend on forced movement mechanics.

---

## 9. Medium-Term Roadmap (CP-18–CP-20)

### 9.1 CP-18: Combat Maneuvers (Non-Grapple)

**Status:** 📋 Planned
**Duration:** 4–5 weeks (estimated)
**Prerequisites:** CP-18A, CP-18B, CP-18C

**Scope:**
- Disarm (remove weapon from opponent)
- Sunder (attack object/weapon)
- Feint (opposed Bluff vs Sense Motive, deny DEX to AC)
- Aid Another (grant +2 bonus to ally)
- Total Defense (standard action, +4 dodge to AC)

**Deferred to CP-19+:**
- Grapple (full state machine: start, maintain, pin, escape, damage)

**Acceptance Criteria:**
- ≥20 unit tests (each maneuver + opposed checks)
- ≥8 integration tests (maneuver chains)
- Determinism verified
- RNG isolation maintained
- Backward compatibility

---

### 9.2 CP-19: Spellcasting (Minimal Viable)

**Status:** 📋 Planned
**Duration:** 6–8 weeks (estimated)
**Prerequisites:** CP-18B (Targeting & Visibility)

**Scope (Minimal):**
- **CP-19A:** Single-target touch/ranged touch spells (no area, no duration)
  - *Magic Missile*, *Scorching Ray*, *Cure Light Wounds*, *Inflict Light Wounds*
- **CP-19B:** Area-effect spells (requires CP-18B Targeting)
  - *Fireball*, *Lightning Bolt*, *Sleep*, *Color Spray*
- **CP-19C:** Duration & delayed effects (persistent spells)
  - *Bless*, *Bane*, *Shield*, *Mage Armor*, *Poison* (secondary saves)

**Deferred to CP-20+:**
- Spell slots & preparation (Vancian magic)
- Concentration checks
- Counterspelling
- Spell-like abilities (SLAs)
- Supernatural abilities (Su)

**Acceptance Criteria:**
- ≥30 unit tests (spell resolution, area targeting, duration tracking)
- ≥10 integration tests (spell + save + condition chains)
- Determinism verified
- RNG isolation maintained
- Backward compatibility

---

### 9.3 CP-20: Full Spellcasting System

**Status:** 📋 Planned
**Duration:** 8–10 weeks (estimated)
**Prerequisites:** CP-19A, CP-19B, CP-19C

**Scope:**
- Spell slots & preparation (Vancian magic)
- Spell components (V/S/M/F/DF)
- Concentration checks (casting defensively, damage interruption)
- Dispelling & counterspelling
- Metamagic (Empower, Maximize, Quicken, etc.)
- Spell-like abilities (SLAs)
- Supernatural abilities (Su)

**Acceptance Criteria:**
- ≥40 unit tests (spell slots, preparation, concentration, dispelling)
- ≥12 integration tests (full spellcasting scenarios)
- Determinism verified
- RNG isolation maintained
- Backward compatibility

---

## 10. Long-Term Vision (Phases 3.7–5.0)

### 10.1 Phase 3.7: DM Decision Policy Engine

**Status:** 📋 Planned (post-CP-20)
**Duration:** 3–4 months (estimated)

**Deliverables:**
1. **Minimal Viable Policy (Month 1)**
   - Legal action enumeration
   - Argmax selection (no beliefs)
   - Hard fairness guardrails (no hard-locks, no un-telegraphed lethality)

2. **Belief-State Tracking (Month 2)**
   - Bayesian updates for hidden stats (AC, saves, DR, ER)
   - Conservative learning (down-weight dice variance)
   - Sample size thresholds (≥2–3 observations before belief shift)

3. **Multi-Objective Optimization (Month 3)**
   - Utility function tuning (Danger + Agency + Pace + Fairness + Fiction)
   - Softmax selection (temperature/"spice" parameter)
   - Personality modeling (aggression/caution balance)

4. **Fairness Telemetry & Guardrails (Month 4)**
   - Early-drop detection (≥2 PCs down within first N rounds)
   - Counterplay deficit monitoring (no viable responses)
   - Variance spike handling (extreme crit streaks)
   - Ease-off mechanisms (morale breaks, target switching, misplays)

**Validation:**
- Run 100+ deterministic combats with varied seeds
- Validate policy behavior (no TPKs, agency preserved, pacing maintained)
- Tune fairness thresholds based on playtest feedback

---

### 10.2 Phase 4: Adventure Ingestion

**Status:** 📋 Planned (post-Phase 3.7)
**Duration:** 4–5 months (estimated)

**Deliverables:**
1. **Module Pack Schema (Month 1)**
   - Define structure (metadata, scenes, encounters, NPCs, treasure, rulings ledger)
   - Manual authoring support (validate schema before OCR)

2. **OCR/PDF Extraction (Months 2–3)**
   - Named entity recognition (NPCs, locations, items)
   - Coreference resolution ("he" = which NPC?)
   - Spatial reasoning (dungeon layout from prose)
   - Mechanical extraction (DCs, monster counts, treasure)

3. **Rulings Engine (Month 4)**
   - Autonomous prep-time rulings (interpret ambiguities)
   - Rulings Ledger generation (source excerpt + chosen ruling + rationale)
   - Best-effort output (document uncertainties, don't defer endlessly)

4. **Runtime Execution (Month 5)**
   - Module Pack execution (deterministic, no live interpretation)
   - Integration with Policy Engine (Layer 2)
   - Validation (identical Module Pack → identical event log)

**Validation:**
- Ingest 3–5 published adventure modules (varied complexity)
- Compare human-authored vs OCR-ingested Module Packs
- Validate determinism (same Module Pack → same outcomes)

---

### 10.3 Phase 5: Campaign Memory & Alignment

**Status:** 📋 Planned (post-Phase 4)
**Duration:** 3–4 months (estimated)

**Deliverables:**
1. **Alignment Evidence Records (Month 1)**
   - Schema definition (session-linked, immutable)
   - Linkage to event log (event IDs, timestamps)
   - Validation rules (fail-closed)

2. **Alignment Drift Evaluation (Month 2)**
   - Periodic evaluation (session-windowed)
   - Trend detection (sustained patterns, not single events)
   - Threshold definitions (configurable per table)
   - Player-facing explanation format (traceable to evidence)

3. **Divine Influence & Religious Consequences (Month 3)**
   - Deity value and alignment expectation data
   - Favor / disfavor tracking (behavior-based)
   - Narrative signaling (warnings before mechanical consequences)
   - Mechanical consequence hooks (RAW-aligned, citation-backed)

4. **DM Assistant Mode (Month 4)**
   - Rules lookup with citation
   - Outcome simulation ("What if this encounter runs?")
   - Ingestion review (inspect rulings, edit Module Packs)
   - Non-binding tactical advice

**Validation:**
- Run 10-session campaign with alignment tracking enabled
- Validate explanations (all drift traceable to evidence)
- Tune thresholds (avoid arbitrary or punitive feel)

---

## 11. Risk Register

### 11.1 High-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Policy Engine complexity overwhelms tuning** | Medium | High | Start with minimal viable policy (argmax only); add beliefs/fairness incrementally |
| **Adventure Ingestion NLP accuracy insufficient** | Medium | Medium | Accept best-effort output; use Rulings Ledger to document uncertainties |
| **Cross-cutting kernel interactions cause regressions** | Low | High | Sequential implementation (no parallelization); PBHA after each kernel |
| **Alignment system feels arbitrary or punitive** | Medium | Medium | Start notification-only (no mechanical consequences); make thresholds configurable |

### 11.2 Medium-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Test suite maintenance overhead** | Medium | Medium | Add test categorization (smoke/integration/replay); run subsets selectively |
| **Determinism constraints limit feature velocity** | Low | Medium | Trust the architecture; determinism is non-negotiable |
| **Spell system scope creep** | Medium | Medium | Decompose CP-19 into sub-packets (CP-19A/B/C); ship incrementally |

### 11.3 Low-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Governance overhead slows development** | Low | Low | Governance proven lightweight; PBHA/CCMA only when triggered |
| **RAW edge cases cause implementation paralysis** | Low | Medium | Use Rulings Ledger to document interpretations; avoid gold-plating |

---

## 12. Success Metrics

### 12.1 Technical Metrics

**Determinism:**
- ✅ 10× replay test passes for every packet (same seed → same hash)
- ✅ RNG isolation verified (no cross-stream contamination)
- ✅ Event ordering contract enforced (no violations detected)

**Test Coverage:**
- ✅ ≥90% unit test coverage for core engine
- ✅ ≥80% integration test coverage for cross-packet interactions
- ✅ Zero flaky or order-dependent tests

**Performance:**
- 🎯 Legality check: <5 ms per action (target)
- 🎯 Resolution function: <10 ms average (target)
- 🎯 Full monster turn (policy + legality + resolution): <50 ms (target)

**Code Quality:**
- ✅ All events include citations (source_id + page number)
- ✅ All packets documented with decision rationale
- ✅ Zero silent failures (fail-closed design enforced)

### 12.2 Architectural Metrics

**Packet Governance:**
- ✅ PBHA conducted for every packet freeze (CP-09–CP-17: 6/6)
- ✅ CCMA triggered and executed when new interaction classes introduced
- ✅ Rules Coverage Ledger (RCL) maintained with explicit coverage status
- ✅ Structural Kernel Register (SKR) maintained with deferral tracking

**Backward Compatibility:**
- ✅ All frozen packets maintain backward compatibility
- ✅ Extensions follow safe pattern (new fields with defaults, optional parameters)
- ✅ Zero breaking changes without major version bump

### 12.3 User Experience Metrics (Post-Phase 3.7)

**Fairness:**
- 🎯 Early-drop rate <10% in non-apex encounters (target)
- 🎯 Counterplay preservation ≥90% (target)
- 🎯 Variance spike mitigation (ease-off triggered when appropriate) (target)

**Engagement:**
- 🎯 Decision density ≥80% (meaningful choices per turn) (target)
- 🎯 Resolution latency <2 seconds average (target)
- 🎯 Confusion signal rate <5% (repeated clarifications) (target)

**Campaign Continuity (Post-Phase 5):**
- 🎯 Alignment drift explanations traceable to evidence (100% target)
- 🎯 Divine influence triggers narratively telegraphed (≥90% target)
- 🎯 Session memory retrieval accuracy ≥95% (target)

---

## Appendices

### A. Glossary

**AIDM:** AI Dungeon Master (project name)
**AoO:** Attacks of Opportunity
**CCMA:** Cross-Cutting Mechanics Audit
**CP-##:** Combat Packet (numbered sequentially)
**DMG:** Dungeon Master's Guide (D&D 3.5e)
**LoE:** Line of Effect
**LoS:** Line of Sight
**MM:** Monster Manual (D&D 3.5e)
**PBHA:** Packet Boundary Health Audit
**PHB:** Player's Handbook (D&D 3.5e)
**RAW:** Rules As Written
**RCL:** Rules Coverage Ledger
**RNG:** Random Number Generator
**SKR:** Structural Kernel Register
**SR:** Spell Resistance

### B. Document Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-08 | Initial consolidated master plan | Claude Sonnet 4.5 |

### C. Related Documents

- [CP-17 Saves Decisions](CP17_SAVES_DECISIONS.md)
- [Project Knowledge Synthesis](PROJECT_KNOWLEDGE_SYNTHESIS.md)
- Research Corpus (35 documents, see `Research/Merged/`)

---

**END OF MASTER PLAN**
