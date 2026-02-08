# AIDM Project Action Plan (REVISED)
## Governance-Driven Deterministic Rules Engine

**Version:** 2.0 (Post-Audit Revision)
**Date:** 2026-02-08
**Status:** ✅ CANONICAL (Supersedes Master Plan v1.0)
**Authority:** Binding Project Specification (Post-DR-001)

---

## STATUS NOTICE

This document supersedes `AIDM_PROJECT_MASTER_PLAN.md` v1.0 following comprehensive ruleset audit findings.

**Key Changes:**
- Capability Gate architecture introduced
- Spellcasting redefined as three distinct deliverables
- Structural Kernel Register (SKR) established
- Decision Record DR-001 locks scoped spellcasting approach

**Compliance:** Adheres to PROJECT_COHERENCE_DOCTRINE.md (§5 Fail-Closed, §7 Event Sourcing, §8 Schema-First)

---

## Table of Contents

1. [Capability Gates (Canonical Model)](#1-capability-gates-canonical-model)
2. [Capability Tier Definitions](#2-capability-tier-definitions)
3. [Governance Decisions (Binding)](#3-governance-decisions-binding)
4. [Development Roadmap (Gate-Driven)](#4-development-roadmap-gate-driven)
5. [Structural Kernel Register (SKR)](#5-structural-kernel-register-skr)
6. [Explicitly Deferred Features](#6-explicitly-deferred-features)
7. [Risk Register](#7-risk-register)
8. [Success Metrics & Gates](#8-success-metrics--gates)

---

## 1. Capability Gates (Canonical Model)

### 1.1 Organizing Principle

**Capability Gates** are explicit architectural thresholds that determine what mechanics are legal to implement.

**Core Rule (Mandatory):**

> No instruction packet (CP-XX) may introduce behavior that crosses a capability gate unless the gate is explicitly declared OPEN in this plan.

This mirrors the PROJECT_COHERENCE_DOCTRINE.md §5 fail-closed philosophy: unknown mechanics are **rejected by default**.

### 1.2 Gate Lifecycle

**CLOSED (Default):**
- Mechanics requiring this gate are FORBIDDEN
- Implementation attempts MUST be rejected at design review
- Tests validating gated mechanics MUST NOT merge

**OPENING (In Progress):**
- Required kernel(s) under active development
- Design docs approved, implementation in progress
- Gate opens when kernel passes PBHA (Packet Boundary Health Audit)

**OPEN:**
- Kernel implemented, tested, and frozen
- Mechanics using this gate are now LEGAL
- Gate remains open permanently (no rollback)

### 1.3 Current Gate Status

| Gate ID | Gate Name | Status | Unlocked By | Opens When |
|---------|-----------|--------|-------------|------------|
| **G-T1** | Tier 1 Mechanics | ✅ OPEN | CP-09–CP-18A-T&V | Already open |
| **G-T2A** | Permanent Stat Mutation | 🔒 CLOSED | SKR-002 | TBD |
| **G-T2B** | XP Economy | 🔒 CLOSED | SKR-008 | TBD |
| **G-T3A** | Entity Forking | 🔒 CLOSED | SKR-001 | TBD |
| **G-T3B** | Agency Delegation | 🔒 CLOSED | SKR-003 | TBD |
| **G-T3C** | Relational Conditions | 🔒 CLOSED | SKR-005 | TBD |
| **G-T3D** | Transformation History | 🔒 CLOSED | SKR-010 | TBD |

---

### 1.4 Gate Enforcement Mechanics (Mandatory)

Each capability gate has mechanical enforcement criteria that determine when it can open and what behaviors it controls.

#### G-T1: Tier 1 Mechanics (✅ OPEN)

**Required Kernels:**
- CP-09 (Combat Structure)
- CP-10 (Attack Resolution)
- CP-14 (Diagonal Constraints)
- CP-15 (Attacks of Opportunity)
- CP-16 (Condition Modifiers)
- CP-17 (Saving Throws & Defensive Resolution)
- CP-18A-T&V (Targeting & Visibility)

**Prohibited Mechanics While CLOSED:**
- N/A (gate already OPEN)

**Acceptance Condition:**
- PBHA passed for all listed kernels
- Test proof: 564 passing tests in < 2 seconds
- Event sourcing verified across all kernels

**Status:** ✅ OPEN (all criteria met)

---

#### G-T2A: Permanent Stat Mutation (🔒 CLOSED)

**Required Kernels:**
- SKR-002 (Permanent Stat Modification Kernel)

**Prohibited Mechanics While CLOSED:**
- Ability score drain (permanent STR/DEX/CON/INT/WIS/CHA reduction)
- Permanent ability score buffs (Wish-granted stat increases)
- Feeblemind spell (INT → 1, permanent)
- Restoration spell (permanent penalty removal)
- Any effect that modifies base ability scores permanently

**Acceptance Condition for OPEN:**
- SKR-002 design document approved (invariants, schema, events, API)
- Schema implementation complete with validation tests
- Permanent modifier separation from temporary (CP-16) verified
- Derived stat recalculation (HP/AC/saves) tested
- PBHA passed with 10× deterministic replay
- Test proof: All SKR-002 tests pass, runtime < 2 seconds maintained

**Opens When:** SKR-002 kernel frozen

---

#### G-T2B: XP Economy (🔒 CLOSED)

**Required Kernels:**
- SKR-008 (XP Economy & Permanence Kernel)

**Prohibited Mechanics While CLOSED:**
- XP expenditure (item creation, Wish, Permanency)
- XP-cost spells (any spell with XP component cost)
- Item creation feats (all XP-based crafting)
- Resurrection with level loss (XP cost for recipient)
- Any permanent XP cost mechanic

**Acceptance Condition for OPEN:**
- SKR-008 design document approved
- XP expenditure schema separate from XP earning
- Permanence logging in event stream verified
- Non-recoverable XP cost enforcement tested
- PBHA passed with 10× deterministic replay
- Test proof: All SKR-008 tests pass, runtime < 2 seconds maintained

**Opens When:** SKR-008 kernel frozen

---

#### G-T3A: Entity Forking (🔒 CLOSED)

**Required Kernels:**
- SKR-001 (Entity Forking & Lineage Kernel)

**Prohibited Mechanics While CLOSED:**
- Entity creation from templates (Simulacrum, Clone)
- Summoning spells (Summon Monster I-IX, all variants)
- Animate Dead and all undead creation
- Planar Binding (entity creation from other planes)
- Any spell or effect creating new entities with lineage tracking

**Acceptance Condition for OPEN:**
- SKR-001 design document approved
- Parent/child entity relationship schema defined
- Template modifier application (e.g., Simulacrum -2 abilities) tested
- Forked entity lifecycle rules (no leveling, defeat destroys) verified
- Independent lifecycle management (child outlives parent) tested
- PBHA passed with 10× deterministic replay
- Test proof: All SKR-001 tests pass, runtime < 2 seconds maintained

**Opens When:** SKR-001 kernel frozen

---

#### G-T3B: Agency Delegation (🔒 CLOSED)

**Required Kernels:**
- SKR-003 (Agency Delegation & Control Kernel)

**Prohibited Mechanics While CLOSED:**
- Dominate Person/Monster spells
- Charm spells (all variants)
- Geas/Quest (compulsion effects)
- Suggestion (external control)
- Any effect transferring entity control to another actor

**Acceptance Condition for OPEN:**
- SKR-003 design document approved
- Control transfer schema defined (original controller, new controller, duration)
- Agency restoration mechanics tested
- External control event logging verified
- PBHA passed with 10× deterministic replay
- Test proof: All SKR-003 tests pass, runtime < 2 seconds maintained

**Opens When:** SKR-003 kernel frozen

---

#### G-T3C: Relational Conditions (🔒 CLOSED)

**Required Kernels:**
- SKR-005 (Relational Conditions Kernel)

**Prohibited Mechanics While CLOSED:**
- Grapple mechanics (grappled, grappling conditions)
- Mounted combat (mount/rider coupling)
- Pinned condition (requires grapple prerequisite)
- Any condition requiring entity-to-entity relationship tracking

**Acceptance Condition for OPEN:**
- SKR-005 design document approved
- Relational condition schema defined (entity A → entity B)
- Condition lifecycle coupled to relationship verified
- Multi-entity condition resolution tested (e.g., mount death breaks rider condition)
- PBHA passed with 10× deterministic replay
- Test proof: All SKR-005 tests pass, runtime < 2 seconds maintained

**Opens When:** SKR-005 kernel frozen

---

#### G-T3D: Transformation History (🔒 CLOSED)

**Required Kernels:**
- SKR-010 (Transformation History Kernel)

**Prohibited Mechanics While CLOSED:**
- Polymorph spells (all variants)
- Petrification (Flesh to Stone, restoration)
- Reincarnate (body change with form history)
- Awaken (permanent form/type change)
- Any effect requiring form stacking or restoration depth tracking

**Acceptance Condition for OPEN:**
- SKR-010 design document approved
- Transformation history stack schema defined
- Form restoration mechanics tested (restore to previous form)
- Nested transformation handling verified (polymorph → petrify → restore)
- PBHA passed with 10× deterministic replay
- Test proof: All SKR-010 tests pass, runtime < 2 seconds maintained

**Opens When:** SKR-010 kernel frozen

---

## 2. Capability Tier Definitions

### 2.1 Tier Model (Mandatory Classification)

Every feature, spell, or subsystem MUST be tagged with exactly ONE tier.

#### Tier 1 — Atomic & Local Mechanics ✅ OPEN

**Characteristics:**
- Single-entity effects only
- No permanent base stat mutation
- No entity creation or forking
- No external agency or control
- No transformation history required

**Examples:**
- Direct damage (Fireball, Magic Missile)
- Temporary buffs/debuffs (Bless, Bane, Haste without time mechanics)
- Healing (Cure Wounds, Heal)
- Detection (Detect Magic, See Invisibility)
- Utility (Light, Prestidigitation)

**Architecture Requirements:**
- Uses existing event-sourcing (CP-09)
- Uses existing targeting (CP-18A-T&V)
- Uses existing condition system (CP-16)

**Gate Required:** G-T1 (already OPEN)

---

#### Tier 2 — Persistent Local Mutation 🔒 CLOSED

**Characteristics:**
- Permanent stat changes (reversible via explicit mechanics)
- XP expenditure (permanent costs)
- No entity creation (modifications only)
- Single entity lifecycle

**Examples:**
- Ability drain/buff (permanent STR reduction)
- Feeblemind (INT → 1, permanent until Restoration)
- Item creation (XP cost, permanent item)
- Resurrection (XP cost for recipient, permanent level loss)
- Restoration spells (reverse permanent penalties)

**Architecture Requirements:**
- **SKR-002:** Permanent Stat Modification Kernel
- **SKR-008:** XP Economy & Permanence Kernel

**Gates Required:** G-T2A + G-T2B (both CLOSED)

---

#### Tier 3 — Entity Lifecycle & Agency 🔒 CLOSED

**Characteristics:**
- Entity creation, forking, or templating
- Transformation history (form stacking)
- External control or agency delegation
- Multi-entity coupling (relational conditions)
- Timeline manipulation

**Examples:**
- Summoning (Summon Monster I-IX, Planar Binding)
- Entity forking (Simulacrum, Clone, Animate Dead)
- Polymorph (form changes, restoration depth)
- Dominate/Charm (external control)
- Grapple/Mounted Combat (relational conditions)
- Time Stop (timeline branching)

**Architecture Requirements:**
- **SKR-001:** Entity Forking & Lineage Kernel
- **SKR-003:** Agency Delegation & Control Kernel
- **SKR-005:** Relational Conditions Kernel
- **SKR-010:** Transformation History Kernel
- **SKR-007:** Timeline Branching Kernel (Tier 3+)

**Gates Required:** G-T3A through G-T3D (all CLOSED)

---

### 2.2 Tier Assignment Rules

**Rule 1: Fail-Closed Classification**
- If uncertain which tier → assign HIGHER tier (more restrictive)
- Rationale: Prevents premature implementation of complex mechanics

**Rule 2: No Mixed-Tier Features**
- If feature requires ANY Tier 3 capability → entire feature is Tier 3
- Example: Polymorph + Petrification interaction requires Tier 3 (transformation history)

**Rule 3: Explicit Downgrade Only**
- Tier assignments can be lowered ONLY via decision record
- Must document why original classification was incorrect

---

## 3. Governance Decisions (Binding)

### DR-001: Spellcasting Scope Lock

**Decision Date:** 2026-02-08
**Decision Maker:** Project Authority (Post-Audit)
**Status:** ✅ APPROVED

#### Decision

**Adopt scoped spellcasting approach:**
- Implement CP-18A with Tier 1 spells ONLY (~250 spells)
- Defer Tier 2/3 spells until required kernels are implemented
- No stubs, no placeholders, no fake implementations

#### Rationale

Comprehensive audit (AIDM_CORE_RULESET_AUDIT) identified:
- 141 spells require kernel infrastructure not yet built
- Implementing without kernels violates event-sourcing invariants
- Risk of non-deterministic edge cases and replay hash instability

#### Constraints

1. **Tier 1 Spell Enforcement:**
   - No spell crossing into Tier 2/3 may be implemented in CP-18A
   - Spell classification list REQUIRED as part of CP-18A deliverable
   - Design review MUST verify tier compliance

2. **Explicit Exclusion List:**
   - All summoning spells → deferred to post-SKR-001
   - All polymorph variants → deferred to post-SKR-010
   - All dominate/charm → deferred to post-SKR-003
   - All ability drain → deferred to post-SKR-002
   - All resurrection → deferred to post-SKR-008
   - All item creation → deferred to post-SKR-008

3. **Exception Protocol:**
   - Requests to implement Tier 2/3 spells require NEW audit
   - Must produce NEW decision record (DR-002+)
   - No silent exceptions

#### Success Criteria

- CP-18A delivers ~200-250 working Tier 1 spells
- All excluded spells documented in DEFERRED section
- No event-sourcing violations introduced
- Test suite maintains < 2 second runtime (Doctrine §3)

---

### DR-002: Kernel Prioritization (Tier 0 vs Tier 1)

**Decision Date:** 2026-02-08
**Decision Maker:** Project Authority
**Status:** ✅ APPROVED

#### Decision

**Implement Tier 0 Kernels ONLY for initial Tier 2/3 unlock:**
- SKR-002 (Permanent Stat Modification) — Tier 0
- SKR-008 (XP Economy & Permanence) — Tier 0
- SKR-001 (Entity Forking & Lineage) — Tier 0

**Defer Tier 1 Kernels to post-1.0:**
- SKR-003 (Agency Delegation) — Tier 1
- SKR-005 (Relational Conditions) — Tier 1
- SKR-010 (Transformation History) — Tier 1

#### Rationale

**80/20 Rule:** Tier 0 kernels unlock 80% of desired Tier 2/3 spells with 50% of kernel complexity.

**Risk Management:** Prove kernel development velocity with simplest kernels first (SKR-002 is lowest-risk).

#### Constraints

1. **Tier 0 kernels MUST implement before ANY Tier 2/3 spells**
2. **Each kernel requires:**
   - Design document (invariants, state schema, events, API)
   - Schema-first development (Doctrine §8)
   - PBHA passing before merge
   - Test suite runtime < 2 seconds maintained

---

## 4. Development Roadmap (Gate-Driven)

### 4.1 Phase 1: Foundation ✅ COMPLETE

**Status:** All gates OPEN, all packets frozen

| Packet | Description | Gate | Status |
|--------|-------------|------|--------|
| CP-09 | Combat Structure (initiative, turns, rounds) | G-T1 | ✅ Frozen |
| CP-10 | Attack Resolution (d20, damage, HP) | G-T1 | ✅ Frozen |
| CP-14 | Diagonal Constraints (movement) | G-T1 | ✅ Frozen |
| CP-15 | Attacks of Opportunity Kernel | G-T1 | ✅ Frozen |
| CP-16 | Condition Modifiers | G-T1 | ✅ Frozen |
| CP-17 | Turn Timers & Durations | G-T1 | ✅ Frozen |
| CP-18A-T&V | Targeting & Visibility Kernel | G-T1 | ✅ Frozen |

**Deliverable:** Deterministic combat engine with 564 passing tests (~1.68s runtime)

---

### 4.2 Phase 2: Tier 1 Spellcasting (CURRENT)

#### CP-18A: Spellcasting Core (Tier 1 Only)

**Status:** 🚧 NEXT PACKET
**Gate Required:** G-T1 (OPEN)
**Timeline:** TBD (pending DR-001 execution approval)

**Scope:**
- Damage spells (~80 spells): Fireball, Lightning Bolt, Magic Missile, etc.
- Healing spells (~25 spells): Cure Wounds series, Heal, etc.
- Buff/debuff spells (~60 spells): Bless, Bane, Shield, Mage Armor, Haste (no time mechanics)
- Detection spells (~30 spells): Detect Magic, Detect Evil, See Invisibility
- Utility spells (~50 spells): Light, Prestidigitation, Mage Hand, Mending

**Total Coverage:** ~245 spells (60-70% of common gameplay)

**Explicit Exclusions (Tier 2/3):**
- ❌ All summoning (requires SKR-001)
- ❌ All polymorph (requires SKR-010)
- ❌ All dominate/charm (requires SKR-003)
- ❌ All ability drain (requires SKR-002)
- ❌ All resurrection (requires SKR-008)
- ❌ All item creation (requires SKR-008)

**Deliverables:**
1. Spell schema (CastSpellIntent, SpellEffect events)
2. Spell slot tracking (prepared vs spontaneous casting)
3. Spell resistance checks
4. Concentration mechanics
5. 245+ spell implementations with tests
6. **Tier classification manifest** (required by DR-001)

**Acceptance Criteria:**
- All implemented spells tagged Tier 1 (no violations)
- Targeting integrates with CP-18A-T&V
- Deterministic replay verified (10× identical results)
- Test suite < 2 seconds (Doctrine §3)
- PBHA passes (no event-sourcing violations)

---

### 4.3 Phase 3: Tier 0 Kernel Development (PARALLEL)

**Status:** 🔒 BLOCKED (awaiting DR-001 execution approval)
**Gates Opening:** G-T2A, G-T2B, G-T3A

#### CP-18B: Permanent Stat Modification Kernel (SKR-002)

**Priority:** TIER 0 (Highest)
**Opens Gate:** G-T2A
**Timeline:** TBD

**Unlocks:**
- Ability drain attacks (Shadow, Wraith, Spectre, Vampire)
- Feeblemind spell
- Restoration spell
- Permanent ability buffs (Wish-granted stat increases)

**Design Requirements (Doctrine §8 - Schema First):**
1. **Invariants Defined:**
   - Base stats immutable (never change directly)
   - Permanent modifiers stored separately from temporary (CP-16)
   - Derived stats (HP, AC, saves) always reflect current ability scores
   - Restoration spells can reverse permanent penalties

2. **State Schema:**
```python
{
  "base_abilities": {"str": 16, "dex": 14, ...},  # Immutable
  "ability_modifiers": {
    "permanent": {"str": -2, ...},  # Drain/buff
    "temporary": {"str": 4, ...}    # Existing CP-16
  },
  "current_abilities": {...}  # Computed: base + permanent + temporary
}
```

3. **Event Types:**
   - `ability_drain` (permanent penalty application)
   - `ability_restored` (permanent penalty removal)
   - `derived_stats_recalculated` (HP/AC/saves update)

4. **Validation Rules:**
   - Permanent modifier cannot reduce ability score below 1
   - CON drain → HP max recalculation
   - DEX drain → AC recalculation

5. **Tests:**
   - Unit: Drain application, restoration, computation
   - Integration: Drain → HP recalc, drain → AC recalc
   - Replay: 10× determinism with drain/restore sequences
   - Edge: Drain to 0 (death condition), restore > drained

**Acceptance Criteria:**
- Shadow touch applies permanent STR drain
- Restoration spell removes drain
- HP max recalculates when CON drained
- PBHA passes
- G-T2A gate OPENS

---

#### CP-18C: XP Economy & Permanence Kernel (SKR-008)

**Priority:** TIER 0
**Opens Gate:** G-T2B
**Timeline:** TBD (after SKR-002)

**Unlocks:**
- Item creation feats (permanent XP cost)
- Permanency spell
- Wish spell (5000 XP cost)
- Resurrection spells (XP cost for recipient)

**Design Requirements:**
1. **Invariants:**
   - XP expenditure is permanent (non-recoverable)
   - XP costs logged separately from encounter XP
   - Item creation success is deterministic given materials + XP
   - Restoration does NOT refund XP costs

2. **State Schema:**
```python
{
  "xp_current": 10000,
  "xp_lifetime_earned": 10000,
  "xp_lifetime_spent": 0,  # Permanent costs only
  "xp_expenditure_log": [
    {"source": "permanency_spell", "cost": 1500, "timestamp": ...}
  ]
}
```

3. **Event Types:**
   - `xp_expended` (permanent cost)
   - `xp_earned` (encounter rewards)
   - `item_created` (links to XP expenditure)

**Acceptance Criteria:**
- Item creation consumes XP permanently
- Wish spell costs 5000 XP
- XP expenditure logged in event stream
- PBHA passes
- G-T2B gate OPENS

---

#### CP-18D: Entity Forking & Lineage Kernel (SKR-001)

**Priority:** TIER 0
**Opens Gate:** G-T3A
**Timeline:** TBD (after SKR-002 and SKR-008)

**Unlocks:**
- Simulacrum spell
- Clone spell
- Summon Monster I-IX
- Animate Dead
- Planar Binding

**Design Requirements:**
1. **Invariants:**
   - Parent entity → child entity relationship tracked
   - Forked entities have independent lifecycle (can outlive parent)
   - Template modifications (e.g., Simulacrum -2 all abilities) stored explicitly
   - Child entities cannot level up (frozen at creation)

2. **State Schema:**
```python
{
  "entity_id": "simulacrum_fighter_001",
  "lineage": {
    "parent_id": "fighter_PC",
    "creation_method": "simulacrum_spell",
    "template_modifiers": {"str": -2, "dex": -2, ...}
  },
  "lifecycle_rules": {
    "can_level": false,
    "can_heal_naturally": false,
    "defeat_destroys": true  # No resurrection
  }
}
```

3. **Event Types:**
   - `entity_forked` (child created from parent)
   - `lineage_established` (parent/child link)
   - `template_applied` (ability score penalties, etc.)

**Acceptance Criteria:**
- Simulacrum creates child entity with -2 to all abilities
- Summon Monster creates temporary child entity
- Animate Dead creates permanent undead child
- PBHA passes
- G-T3A gate OPENS

---

### 4.4 Phase 4: Tier 2/3 Spell Unlock (AFTER KERNELS)

**Status:** 🔒 BLOCKED (gates closed)
**Timeline:** TBD (after CP-18B, CP-18C, CP-18D complete)

#### CP-18E: Spellcasting Extensions

**Gates Required:**
- G-T2A (OPEN) ← SKR-002
- G-T2B (OPEN) ← SKR-008
- G-T3A (OPEN) ← SKR-001

**Unlocked Spells (~140 additional):**
- Summoning: Summon Monster I-IX, Summon Nature's Ally I-IX
- Transformation: Polymorph variants (requires SKR-010 later)
- Control: Dominate spells (requires SKR-003 later)
- Resurrection: Raise Dead, Resurrection, True Resurrection
- Item Creation: Permanency, crafting feats
- Ability Modification: Feeblemind, Restoration, Heal (ability damage)

**Deliverable:** Full spellcasting system (~385 total spells)

---

## 5. Structural Kernel Register (SKR)

### 5.1 Kernel Catalog

| ID | Kernel Name | Tier | Priority | Blocks # | Status |
|----|-------------|------|----------|----------|--------|
| **SKR-002** | Permanent Stat Modification | T0 | CRITICAL | 16 | 🔒 Design |
| **SKR-008** | XP Economy & Permanence | T0 | CRITICAL | 14 | 🔒 Design |
| **SKR-001** | Entity Forking & Lineage | T0 | CRITICAL | 18 | 🔒 Design |
| **SKR-003** | Agency Delegation & Control | T1 | HIGH | 23 | 🔒 Deferred |
| **SKR-005** | Relational Conditions | T1 | HIGH | 9 | 🔒 Deferred |
| **SKR-010** | Transformation History | T1 | HIGH | 11 | 🔒 Deferred |
| **SKR-004** | Interrupt & Readied Actions | T2 | MEDIUM | 12 | 🔒 Deferred |
| **SKR-011** | Negative Levels & Level Drain | T2 | MEDIUM | 9 | 🔒 Deferred |
| **SKR-007** | Timeline Branching | T3 | LOW | 6 | 🔒 Deferred |
| **SKR-009** | Entity Suspension & Rejuvenation | T3 | LOW | 7 | 🔒 Deferred |
| **SKR-012** | Service Contracts & Obligations | T3 | LOW | 8 | 🔒 Deferred |

**Total Subsystems Blocked:** 141

---

### 5.2 Kernel Development Protocol (Doctrine §8 Compliance)

**MANDATORY SEQUENCE for ALL kernels:**

#### 1. Design Document (REQUIRED BEFORE CODE)

**BLOCKING REQUIREMENT:** No SKR kernel may enter implementation until its design document is approved and referenced by ID.

This mirrors PROJECT_COHERENCE_DOCTRINE.md §8 (Data-Only Schemas First): schemas define contracts before algorithms.

**Design Document MUST Contain:**

**A. Invariants Section:**
- List all properties that MUST remain true across all state transitions
- Define what cannot change (immutability constraints)
- Specify validation rules and boundary conditions
- Example: "Base ability scores are immutable; modifiers stored separately"

**B. State Schema Section:**
- Define entity-level state changes (what fields added to Entity?)
- Define world-level state changes (new tables, registries, indices?)
- Specify data types, optionality, defaults
- Provide schema code snippets (dataclass definitions)
- Example: `{"permanent_modifiers": {"str": -2}, "temporary_modifiers": {...}}`

**C. Event Types Section:**
- List all new event types this kernel emits
- Define event payloads (what data each event carries)
- Specify event ordering (does event A always precede event B?)
- Document causal chains (event X triggers event Y)
- Example: `ability_drain → derived_stats_recalculated`

**D. API Surface Section:**
- Define public functions other systems call
- Specify function signatures (parameters, return types)
- Document integration points (which existing modules call this?)
- Example: `apply_permanent_stat_modifier(entity_id, stat, modifier)`

**E. Integration Points Section:**
- List all modules this kernel depends on
- List all modules that will depend on this kernel
- Specify data flow (what crosses module boundaries?)
- Identify potential conflicts with existing systems

**F. Test Strategy Section:**
- Define unit test categories (what gets isolated testing?)
- Define integration test scenarios (what workflows get end-to-end testing?)
- Specify replay test requirements (how many deterministic runs?)
- List edge cases to test (boundary conditions, error paths)
- Example: "Test drain to 0 (death), restore exceeding drain amount"

**Design Document Approval Criteria:**
- All six sections (A–F) completed
- No contradictions with existing kernels
- No violations of PROJECT_COHERENCE_DOCTRINE.md
- Referenced by unique ID (e.g., SKR-002-DESIGN-v1.0)

**ENFORCEMENT:** Design review MUST reject kernel implementation attempts without approved design document.

---

#### 2. Schema Implementation

**After design document approved:**
- Write schema module (`aidm/schemas/[kernel_name].py`)
- Implement dataclasses, enums, validation rules
- Write schema tests (validation, serialization, roundtrips)
- Integrate schema into bundles (if applicable)
- Update bundle validator to recognize new event types

**Acceptance:** Schema tests pass, no implementation logic yet

---

#### 3. Algorithm Implementation

**After schema tests pass:**
- Implement kernel functions (`aidm/core/[kernel_name].py`)
- Write unit tests (isolated function behavior)
- Write integration tests (multi-module workflows)
- Verify event emission (all mutations flow through events)

**Acceptance:** All tests pass, test runtime < 2 seconds maintained

---

#### 4. PBHA (Packet Boundary Health Audit)

**Before merge:**
- Determinism verified (10× replay produces identical results)
- Event sourcing verified (all state mutations via events)
- Test runtime < 2 seconds maintained (no performance regression)
- No regressions in existing tests (all 564+ tests still pass)
- Capability gate acceptance criteria met (see Section 1.4)

**Acceptance:** PBHA checklist complete, all criteria PASS

---

#### 5. Gate Opens

**After PBHA passes:**
- Kernel marked FROZEN (no further changes without new design doc)
- Capability gate status updated to ✅ OPEN
- Dependent mechanics now LEGAL to implement
- Design document archived as reference

---

**ENFORCEMENT RULES:**

1. **Design-Before-Code (Mandatory):**
   - No code review until design document approved
   - No implementation commits without design doc reference in commit message
   - Pull requests without design doc ID are auto-rejected

2. **No Kernel Merges Without PBHA:**
   - CI pipeline blocks merge if PBHA checklist incomplete
   - Manual override requires decision record (DR-XXX)

3. **Gates Remain CLOSED Until All Criteria Met:**
   - Section 1.4 defines acceptance condition for each gate
   - No exceptions without new decision record
   - Attempted implementation of gated mechanics rejected at design review

---

## 6. Explicitly Deferred Features

### 6.1 Purpose of This Section

This section eliminates ambiguity and expectation mismatch by cataloging features that are:

1. **Mechanically blocked** by closed capability gates
2. **Architecturally incompatible** with current kernel infrastructure
3. **Intentionally deferred** to control scope and maintain system stability

**Key Principle:** These are NOT missing features or bugs—they are FORBIDDEN mechanics until the blocking gate opens.

**Enforcement:** Implementation attempts for deferred features MUST be rejected at design review with reference to the blocking gate ID.

---

### 6.2 Category: Summoning (ALL variants — Gate G-T3A CLOSED)

**Blocking Gate:** G-T3A (Entity Forking)
**Blocking Kernel:** SKR-001 (Entity Forking & Lineage Kernel)

**Prohibited Mechanics:**
- All Summon Monster spells (I through IX)
- All Summon Nature's Ally spells (I through IX)
- Planar Ally spells (Lesser, standard, Greater)
- Planar Binding spells (Lesser, standard, Greater)
- Gate spell (creature summoning variant)
- Elemental summoning (Summon Monster variants)
- Celestial/Fiendish templating on summoned creatures

**Reason for Deferral:**
- Requires entity creation from templates with lineage tracking
- Parent/child relationship management not implemented
- Template modifier application (HD scaling, alignment templates) requires kernel support
- Summoned entity lifecycle (dismissal, duration expiry, death) requires dedicated state machine

**Opens When:** SKR-001 kernel passes PBHA and G-T3A opens

**Subsystems Blocked:** 18 (per audit)

---

### 6.3 Category: Polymorph & Transformation (ALL variants — Gate G-T3D CLOSED)

**Blocking Gate:** G-T3D (Transformation History)
**Blocking Kernel:** SKR-010 (Transformation History Kernel)

**Prohibited Mechanics:**
- Polymorph spell (base and all variants)
- Baleful Polymorph
- Polymorph Any Object
- Shapechange
- Wild Shape (Druid class feature)
- Alternate Form (monster ability)
- Flesh to Stone / Stone to Flesh (petrification)
- Reincarnate (body transformation with history)
- Awaken (permanent creature type change)

**Reason for Deferral:**
- Requires transformation history stack (form A → form B → restore to A)
- Nested transformation resolution (polymorph → petrify → restore order)
- Ability score replacement (new form's physical stats override original)
- Equipment merging/dropping rules depend on form size/type change
- Restoration depth tracking (どのformに戻すか)

**Opens When:** SKR-010 kernel passes PBHA and G-T3D opens

**Subsystems Blocked:** 11 (per audit)

---

### 6.4 Category: Dominate & Charm (ALL variants — Gate G-T3B CLOSED)

**Blocking Gate:** G-T3B (Agency Delegation)
**Blocking Kernel:** SKR-003 (Agency Delegation & Control Kernel)

**Prohibited Mechanics:**
- Dominate Person
- Dominate Monster
- Dominate Animal
- Charm Person
- Charm Monster
- Charm Animal
- Geas/Quest (compulsion effects)
- Suggestion (Lesser and Greater)
- Mass Charm/Dominate variants
- Vampire domination ability

**Reason for Deferral:**
- Requires control transfer mechanism (original controller → new controller)
- Agency restoration on effect expiry (who regains control?)
- Conflicting orders resolution (dominated by A, then B)
- Memory/awareness rules (does victim remember actions while dominated?)
- Self-harm prohibition enforcement (dominated creatures won't obviously harm themselves)

**Opens When:** SKR-003 kernel passes PBHA and G-T3B opens

**Subsystems Blocked:** 23 (per audit)

---

### 6.5 Category: Resurrection & XP-Cost Mechanics (ALL — Gate G-T2B CLOSED)

**Blocking Gate:** G-T2B (XP Economy)
**Blocking Kernel:** SKR-008 (XP Economy & Permanence Kernel)

**Prohibited Mechanics:**
- Raise Dead (XP cost for recipient, level loss)
- Resurrection
- True Resurrection
- Reincarnate (XP cost)
- Wish spell (5000 XP cost for most uses)
- Miracle spell (XP cost for specific effects)
- All item creation feats (XP cost per GP value)
- Permanency spell (XP cost)
- Clone spell (XP cost)
- Magic Jar (permanent soul transfer)

**Reason for Deferral:**
- Requires permanent XP expenditure tracking (non-recoverable)
- XP cost logging separate from XP earning
- Recipient-pays XP cost (not caster) for some spells
- Level loss mechanics (Raise Dead: -1 level, permanent until Restoration)
- Item creation XP audit (1/25th GP value consumed as XP)

**Opens When:** SKR-008 kernel passes PBHA and G-T2B opens

**Subsystems Blocked:** 14 (per audit)

---

### 6.6 Category: Permanent Ability Score Modification (ALL — Gate G-T2A CLOSED)

**Blocking Gate:** G-T2A (Permanent Stat Mutation)
**Blocking Kernel:** SKR-002 (Permanent Stat Modification Kernel)

**Prohibited Mechanics:**
- Ability score drain (Shadow STR drain, Vampire CON drain, Wraith CON drain, Spectre STR drain)
- Feeblemind spell (INT/CHA → 1, permanent until Restoration)
- Restoration spells (Lesser, standard, Greater — reverse permanent penalties)
- Wish-granted permanent ability score increases (+1 inherent bonus)
- Tome/Manual magic items (+1 to +5 inherent bonus to one ability)
- Ability score burn (permanent reduction for magical effects)

**Reason for Deferral:**
- Requires separation of permanent vs temporary modifiers (distinct from CP-16 temporary conditions)
- Derived stat recalculation (CON drain → HP max recalc, DEX drain → AC recalc)
- Restoration depth (can only remove drain, not boost above original)
- Death condition on ability score reaching 0
- Permanent modifier persistence across rests/durations

**Opens When:** SKR-002 kernel passes PBHA and G-T2A opens

**Subsystems Blocked:** 16 (per audit)

---

### 6.7 Category: Relational Conditions (Grapple/Mounted — Gate G-T3C CLOSED)

**Blocking Gate:** G-T3C (Relational Conditions)
**Blocking Kernel:** SKR-005 (Relational Conditions Kernel)

**Prohibited Mechanics:**
- Grapple (grappling/grappled condition pair)
- Improved Grapple feat
- Pinned condition (requires grapple prerequisite)
- Mounted combat (mount/rider coupling)
- Ride skill checks
- Mounted charge
- Spirited Charge feat
- Trample attack (mount tramples, rider controls)
- Any condition requiring entity-to-entity relationship

**Reason for Deferral:**
- Requires relational condition schema (entity A grappling entity B)
- Bidirectional condition coupling (grappler + grappled both affected)
- Relationship lifecycle (grapple breaks → both conditions removed)
- Third-party interaction (entity C attacks grappler → check for grapple break)
- Multi-entity condition resolution (mount death → rider falls)

**Opens When:** SKR-005 kernel passes PBHA and G-T3C opens

**Subsystems Blocked:** 9 (per audit)

---

### 6.8 Category: Timeline Manipulation (Explicit Long-Term Defer)

**Blocking Gate:** (Future gate, not yet defined)
**Blocking Kernel:** SKR-007 (Timeline Branching Kernel — Tier 3, LOW priority)

**Prohibited Mechanics:**
- Time Stop spell (Wiz 9 only, ultra-rare)
- Temporal Stasis
- Haste spell with timeline mechanics (currently Tier 1 implementation possible without timeline branching)
- Slow spell with timeline mechanics

**Reason for Deferral:**
- Requires timeline branching (subgame state for Time Stop caster)
- Action queue management (caster gets N actions, then timeline merges)
- Interaction prohibition enforcement (caster cannot affect other entities during Time Stop)
- State snapshot + rollback mechanism
- Extreme architectural complexity for minimal gameplay value (Time Stop is 9th-level wizard spell, rare in practice)

**Opens When:** TBD (post-1.0, demand-driven)

**Subsystems Blocked:** 6 (per audit)

**Explicit Policy:** Will NOT implement unless user demand justifies development cost.

---

### 6.9 Category: Interrupt & Readied Actions (Deferred — Tier 2)

**Blocking Gate:** (Future gate, not yet defined)
**Blocking Kernel:** SKR-004 (Interrupt & Readied Actions Kernel — Tier 2, MEDIUM priority)

**Prohibited Mechanics:**
- Readied Action (delay action until trigger)
- Counterspelling (reactive spell interruption)
- Contingency spell (trigger-based automatic casting)
- Attacks of Opportunity triggered by non-movement (e.g., spell casting)
- Immediate actions (3.5e rapid response)

**Reason for Deferral:**
- Requires interrupt queue (actions triggering mid-resolution)
- Trigger condition evaluation (when does readied action fire?)
- Action rollback (if trigger never occurs, ready is wasted)
- Priority resolution (multiple entities ready on same trigger)
- Current AoO system (CP-15) handles movement-triggered only

**Opens When:** TBD (post-1.0, after Tier 0 kernels)

**Subsystems Blocked:** 12 (per audit)

---

### 6.10 Category: Negative Levels & Level Drain (Deferred — Tier 2)

**Blocking Gate:** (Future gate, not yet defined)
**Blocking Kernel:** SKR-011 (Negative Levels & Level Drain Kernel — Tier 2, MEDIUM priority)

**Prohibited Mechanics:**
- Energy drain attacks (Vampire, Wraith, Spectre, Wight)
- Negative levels (temporary and permanent)
- Enervation spell (1d4 negative levels)
- Energy Drain spell (2d4 negative levels)
- Restoration spell (negative level removal)
- Death condition at negative levels equal to HD

**Reason for Deferral:**
- Requires negative level state (distinct from ability drain)
- Derived stat recalculation (negative level → HP/BAB/saves reduction)
- Temporary vs permanent negative level transition (24 hours)
- Level-dependent ability loss (spells per day, class features)
- Death condition at -HD negative levels

**Opens When:** TBD (post-1.0, after SKR-002)

**Subsystems Blocked:** 9 (per audit)

---

### 6.11 Category: Out of Scope (Per Doctrine — NEVER)

These mechanics are PERMANENTLY out of scope per PROJECT_COHERENCE_DOCTRINE.md and will NOT be implemented:

**❌ Epic Level Rules (21+):**
- Not part of PHB/DMG/MM core ruleset
- Epic Level Handbook is separate supplement
- Architectural assumptions break at 20+ (ability scores unbounded, etc.)

**❌ Psionics:**
- Separate subsystem (Expanded Psionics Handbook)
- Fundamentally different resource model (power points vs spell slots)
- Not required for core 3.5e gameplay

**❌ Artifacts:**
- DM discretion extreme (no systematic rules)
- Powers are narrative, not mechanical
- Cannot be deterministically modeled

**❌ Homebrew Rules:**
- Violates RAW (Rules As Written) fidelity objective
- Introduces non-auditable variance
- User can mod via external tooling if desired

---

### 6.12 Deferral Enforcement Policy

**Design Review Rejection Criteria:**

If a proposed feature matches ANY category in Sections 6.2–6.11, it MUST be rejected with:

1. **Blocking gate ID** (e.g., G-T3A)
2. **Blocking kernel ID** (e.g., SKR-001)
3. **Reference to this section** (e.g., "See Action Plan v2 §6.2")

**Exception Protocol:**

To override a deferral:

1. Produce NEW decision record (DR-XXX)
2. Document why gate/kernel is no longer required
3. Prove no event-sourcing violations introduced
4. Pass PBHA with new feature included

**No silent exceptions. No placeholders. No stubs.**

---

**END OF EXPLICITLY DEFERRED FEATURES**

---

## 7. Risk Register

### 7.1 Architectural Risks

#### RISK-001: Kernel Complexity Underestimated

**Probability:** MEDIUM
**Impact:** HIGH (timeline slip, scope reduction)

**Mitigation:**
- Implement SKR-002 first (simplest kernel) to establish baseline velocity
- Design-first approach (Doctrine §8) prevents implementation churn
- PBHA gates prevent merging broken kernels

**Trigger:** First kernel takes >6 weeks
**Response:** Re-scope to fewer kernels, defer more spells to post-1.0

---

#### RISK-002: Tier 1 Spells Insufficient for User Validation

**Probability:** LOW
**Impact:** MEDIUM (need to fast-track kernels)

**Mitigation:**
- Survey target users on critical spell priorities
- If Summon Monster is must-have, prioritize SKR-001
- Allow user feedback to drive kernel sequencing

**Trigger:** Users demand Tier 2/3 spells before 1.0
**Response:** Accelerate highest-demand kernel (likely SKR-001 or SKR-003)

---

#### RISK-003: Interaction Hazards in Tier 1 Spells

**Probability:** LOW
**Impact:** LOW (audit pre-identified)

**Mitigation:**
- Cross-reference every Tier 1 spell against audit interaction hazards
- Explicit exclusion list for edge cases (Haste without time mechanics, etc.)
- Comprehensive spell×spell interaction testing

**Trigger:** Spell causes non-deterministic behavior
**Response:** Move spell to Tier 2/3, add to kernel requirements

---

### 7.2 Schedule Risks

#### RISK-004: Kernel Development Timeline Optimistic

**Probability:** MEDIUM
**Impact:** MEDIUM (delay Tier 2/3 spell unlock)

**Mitigation:**
- Build 50% time buffer into kernel estimates
- Parallel kernel development where possible (SKR-002 + SKR-008)
- De-scope Tier 1 kernels if Tier 0 slips

**Trigger:** Tier 0 kernels take >16 weeks combined
**Response:** Ship 1.0 with Tier 1 spells only, defer Tier 2/3 to post-1.0

---

### 7.3 Scope Risks

#### RISK-005: Feature Creep from Full 3.5e Ruleset

**Probability:** HIGH
**Impact:** HIGH (timeline explosion, architectural debt)

**Mitigation:**
- Capability gates ENFORCE scope boundaries (fail-closed)
- Decision records REQUIRED for exceptions (DR-002+)
- Explicit deferral list prevents "we'll add this later" scope creep

**Trigger:** Request to implement Tier 2/3 feature without kernel
**Response:** Reject at design review, cite gate closure

---

## 8. Success Metrics & Gates

### 8.1 Capability-Based Milestones

**MVP (Minimum Viable Product):**
- **Definition:** G-T1 OPEN, CP-18A complete
- **Capability:** Combat + Tier 1 spells (~245 spells)
- **Timeline:** TBD (DR-001 execution pending)
- **Playable For:** Combat-heavy campaigns, dungeon crawls

**1.0 Release:**
- **Definition:** G-T2A, G-T2B, G-T3A OPEN, CP-18E complete
- **Capability:** Combat + All spells (~385 spells)
- **Timeline:** TBD (after Tier 0 kernels)
- **Playable For:** Full 3.5e campaigns

**1.5 Release (Post-1.0):**
- **Definition:** G-T3B, G-T3C, G-T3D OPEN
- **Capability:** Advanced combat (grapple, mounted), transformation, control
- **Timeline:** TBD (Tier 1 kernels)
- **Playable For:** Complete 3.5e tactical depth

---

### 8.2 Quality Gates (All Releases)

**MANDATORY (Doctrine Compliance):**
- ✅ Test suite < 2 seconds (§3)
- ✅ Event sourcing verified (§7)
- ✅ Fail-closed design (§5)
- ✅ Schema-first development (§8)
- ✅ PBHA passes (determinism, no regressions)

**FORBIDDEN:**
- ❌ LLM runtime dependency (§1)
- ❌ Non-deterministic edge cases
- ❌ Silent fallbacks or defaults
- ❌ Crossing closed capability gates

---

## ENFORCEMENT

### Who Enforces This Plan?

1. **Design Review:** Verify tier compliance, gate status before implementation
2. **Code Review:** Verify schema-first, fail-closed, event-sourcing adherence
3. **PBHA Audits:** Verify determinism, no regressions before merge
4. **Decision Records:** Lock scope changes, require explicit approval

### Deviation Protocol

**If deviation required:**
1. Document rationale in new decision record (DR-003+)
2. Update this plan if gate/tier structure changes permanently
3. Ensure PROJECT_STATE_DIGEST.md updated
4. Add tests to enforce new constraint

---

## APPENDICES

### Appendix A: Audit Reference

**Full Audit:** `AIDM_CORE_RULESET_AUDIT_EXECUTIVE_SUMMARY.md`

**Key Findings:**
- 67 HIGH-risk subsystems identified
- 72+ interaction hazards documented
- 12 structural kernels required
- 141 subsystems blocked by missing kernels

### Appendix B: Glossary

**Capability Gate:** Architectural threshold that determines legal mechanics
**Tier 0 Kernel:** Critical kernel blocking 80% of Tier 2/3 spells
**Tier 1 Kernel:** High-value kernel, deferrable to post-1.0
**Decision Record (DR):** Binding governance decision with rationale
**PBHA:** Packet Boundary Health Audit (determinism + regression check)
**SKR:** Structural Kernel Register (catalog of required kernels)

---

**END OF REVISED ACTION PLAN**

**Status:** ✅ CANONICAL
**Next Action:** Approve DR-001, greenlight CP-18A implementation
