# AI-Driven DM Project — Master Action Log & Implementation Journal

This document is the **canonical execution log** for the AI-Driven D&D 3.5e Dungeon Master project.

It records **decisions, rationale, implementation steps, lock criteria, and verification status** so the full development process is auditable and upload-ready for the project repository.

---

## 0. Canonical Scope & Authority

**Objective:** Establish a single, frozen source of truth before implementation.

### Canonical Documents (Locked)
- AI-Driven Dungeon Master — Master Action Plan
- Phase 3.6 — Combat Engine Specification
- Phase 3.7 — DM Decision Policy Engine
- Deterministic Combat / DM Decision Model audits

**Non-Negotiable Rule:**
> "LLM proposes intent and narration only. All mechanics are resolved by deterministic code."

**Status:** LOCKED

---

## 1. Determinism Foundation (Phase A)

### Purpose
Enable replayability, auditability, and regression testing before any gameplay logic.

### Canonical Principles
- Determinism is a **hard invariant**, not a best-effort goal
- Every outcome must be explainable post-hoc
- Replay must be exact, not approximate

### Components
- **RNGManager** — seeded, hierarchical, stream-isolated
- **Event Log** — append-only, immutable
- **Replay Runner** — state₀ + log → identical outcome

---

### 1.1 RNGManager — Design Contract

**Decision:** Use hierarchical RNG streams derived from a master seed.

**Rationale:**
- Prevents cross-system randomness bleed
- Allows replay, branching, and subsystem isolation

**Design**
- master_seed (campaign/session scoped)
- derive(seed, subsystem_id, entity_id?, turn_index?)

**Standard Streams**
- combat
- policy
- environment
- narration (cosmetic only)

**Rules**
- No direct RNG access outside RNGManager
- RNG passed explicitly into every resolver
- Narration RNG may never affect state

**Lock Criteria**
- Identical master_seed + event order → identical rolls
- Removing narration RNG does not affect outcomes

---

### 1.2 Event Log — Execution Ledger

**Decision:** Event-sourced architecture with append-only log.

**Event Types**
- intent_submitted
- legality_validated / legality_rejected
- operator_resolved
- state_mutated
- duration_ticked
- combat_started / combat_ended

**Required Event Fields**
- event_id (monotonic)
- timestamp
- rng_offset
- operator_type
- entities_involved
- inputs
- rolls
- modifiers (with RuleAtomIDs)
- outcome
- state_diff

**Rules**
- Events are never edited or deleted
- Derived views are rebuilt from events

**Lock Criteria**
- Full state can be reconstructed from log alone
- Logs are diffable across replays

---

### 1.3 Replay Runner — Determinism Proof

**Decision:** Replays are first-class citizens, not debugging tools.

**Replay Contract**
Input:
- Initial WorldState
- Event Log
- Master seed

Output:
- Final WorldState
- Trace comparison report

**Validation Rules**
- Every event must replay cleanly
- Any divergence is a hard failure

**Lock Criteria**
- ≥10 complex combats replay with zero divergence
- Replay detects even single-roll mismatches

**Status:** IN PROGRESS

---

## 2. Canonical World State (Phase B)

**Status:** IN PROGRESS

### Purpose
Define the single, authoritative source of truth for all mutable game data.

This phase freezes **what data exists**, **where it lives**, and **who may read or mutate it**.

---

### 2.1 WorldState — Top-Level Contract

**Decision:** All game data is reachable from `WorldState`.

**Rationale:**
- Prevents hidden state
- Enables full replay from state₀ + event log
- Makes legality and resolution auditable

**WorldState Contains**
- ruleset_version
- rng_state (opaque handle, not raw RNG)
- global_time
- entities (PCs, NPCs, monsters, summons)
- maps / zones
- active_combat (nullable)
- world_flags (weather, planar traits, global effects)
- information_partitions

**Rules**
- No subsystem owns private state outside WorldState
- Any mutation must emit an event + trace

**Lock Criteria**
- Full serialization / deserialization without loss
- Replay runner reconstructs identical WorldState

---

### 2.2 CombatState vs Global State

**Decision:** Combat is a bounded execution context layered onto WorldState.

**CombatState Contains**
- encounter_id
- round_number
- initiative_order
- active_turn_index
- spatial_snapshot
- temporal_hooks
- reinforcement_timers
- encounter_tags (tutorial, apex, chase, etc.)

**Rules**
- CombatState exists only while combat is active
- Entry/exit emits combat_started / combat_ended events

**Lock Criteria**
- Entering combat snapshots required data explicitly
- Exiting combat leaves no dangling combat-only fields

---

### 2.3 CreatureState — Entity Contract

**Decision:** Every creature uses the same schema (PCs, NPCs, monsters).

**CreatureState Fields**
- id, name, type, subtype, size
- position (tile, elevation)
- movement_modes (land, fly, swim, etc.)
- senses (vision, blindsight, etc.)
- AC_breakdown (normal, touch, flat-footed)
- saves (Fort, Ref, Will)
- HP {current, max, temp} *(DM-only)*
- defenses (DR, ER, immunities, SR)
- attack_routines
- damage_expressions
- action_economy (standard, move, swift, immediate, AoOs_remaining)
- conditions[]
- resources (spell slots, charges, rage rounds, etc.)
- morale / doctrine

**Rules**
- No derived values stored unless required by RAW
- Presentation layers may not read DM-only fields

**Lock Criteria**
- All combat operators read exclusively from CreatureState

---

### 2.4 Condition & Effect State

**ConditionState**
- condition_id
- source
- mechanical_effects (modifiers, permissions)
- stacking_rules
- duration_remaining
- removal_triggers

**EffectState**
- effect_id
- source
- targets
- save_DC / attack_bonus
- duration_model
- ongoing_effects

**Rules**
- Conditions are mechanical bundles, not labels
- No narrative-only conditions

---

### 2.5 Information Partitions

**Decision:** Explicit separation of knowledge domains.

**Partitions**
- Engine View: full deterministic state
- DM-Private View: exact HP, beliefs, hidden entities
- Player View: visible positions, conditions, descriptive health

**Rules**
- Player-facing layers cannot access DM-private fields
- LLM narration constrained to Player View only

**Lock Criteria**
- Attempted cross-partition access raises hard error

---

### 2.6 Schema Freeze Policy

Once Phase B is marked **LOCKED**:
- Field additions require justification + version bump
- Field removals require migration path

---

## 3. Rules Engine Core (Phase C)

**Status:** IN PROGRESS

### Purpose
Execute all RAW mechanics without LLM involvement.

### Hard Rules
- Illegal actions are rejected **pre-resolution**
- All operators are **pure functions**
- Every outcome is traceable to **Rule Atoms**

---

### 3.1 Authoritative Legality Checker — Contract (FIRST IMPLEMENTATION)

**Decision:** The legality checker is the single source of truth for what can be attempted.

**Rationale:**
- Prevents policy/LLM from proposing illegal actions
- Allows "legal menu" generation for voice-first play
- Enables fail-closed behavior with explicit reasons

#### 3.1.1 Inputs
- `WorldState`
- `Intent` (schema-validated)
- `Context` (combat/noncombat, visibility partition, acting entity)

#### 3.1.2 Outputs
- `LegalResult`
  - `is_legal: bool`
  - `reasons: [code]` *(empty if legal)*
  - `requirements: [Requirement]` *(what must be satisfied)*
  - `derived: {}` *(computed targeting sets, paths, AoO triggers, etc.)*

#### 3.1.3 Rejection Policy
- **Fail closed**: if any required data is missing → illegal with reason `missing_state`
- Reasons are structured (machine-actionable), not prose

**Reason Code Taxonomy (initial)**
- `schema_invalid`
- `missing_state`
- `no_action_slot`
- `condition_restriction`
- `range_illegal`
- `los_blocked`
- `loe_blocked`
- `target_invalid`
- `path_illegal`
- `provokes_aoo_illegal` *(used when intent forbids provoking)*
- `component_missing` *(spell/material/focus)*
- `concentration_required`
- `prereq_missing`

#### 3.1.4 Legality Surface Area (must cover)
- Action economy availability (standard/move/full/swift/immediate/AoO)
- Conditions that restrict actions (stunned, grappled, prone, etc.)
- Target legality (type, visibility, allegiance rules if any)
- Range/Reach
- LoS / LoE
- AoO triggers (movement and certain actions)
- Movement/path legality (terrain cost, squeezing, blocked squares)
- Spell requirements (components, targets, SR applicability is *resolution gate*, not legality unless RAW says cannot attempt)

#### 3.1.5 Event + Trace Requirements
Every legality check emits:
- `legality_validated` or `legality_rejected`
- A trace containing:
  - intent summary
  - evaluated constraints
  - derived sets (valid targets, valid squares)
  - explicit rejection codes

**Lock Criteria**
- 100% of engine resolution entrypoints require a passing legality result
- Legal menu generator uses legality outputs (no separate logic)
- Replay runner reproduces legality outcomes identically

---

### 3.2 Intent Schema — Minimal Starting Set (to support legality)

**Decision:** Start with a small, expandable intent set mapped to Rule Atoms.

**Initial Intent Types**
- `move` (path-based)
- `melee_attack` (single attack)
- `ranged_attack` (single attack)
- `cast_spell` (single spell, single target or AoE descriptor)
- `total_defense`
- `withdraw`
- `ready_action`
- `delay`

**Rules**
- Intents are structural JSON only (no prose)
- Any missing field is a schema failure

**Lock Criteria**
- Each intent type can be validated without calling a resolver
- Each intent type has canonical "legal menu" generation rules

---

### 3.3 Next Operator After Legality
Once legality is stable, implement:
1) **Modifier & Stacking Engine**
2) **Attack & Damage Resolution**

---

### Implementation Order (Phase C)
1. Authoritative Legality Checker ✅ (IN PROGRESS)
2. Modifier & Stacking Engine
3. Attack & Damage Resolution
4. Saving Throws (no auto-fail on nat 1)
5. Movement, AoO, Positioning
6. Spell & Effect Resolution
7. Condition & Duration Engine
8. Death, Dying, Stabilization

---

## 4. Combat Engine (Phase 3.6)

### Purpose
Formalize combat as a deterministic execution contract.

### Core Loop
- Combat start → initiative → turn loop → end conditions

### Resolution Ordering
1. Target legality
2. Primary roll
3. Immunities
4. Concealment / miss chance
5. Spell resistance
6. Damage / effects
7. Mitigation
8. Reactions
9. State update + duration tick

### Presentation Policy
- No numeric HP to players
- Descriptive health states only

**Status:** PLANNED

---

## 5. DM Decision Policy Engine (Phase 3.7)

### Purpose
Model expert DM enemy decision-making without violating rules integrity.

### Inputs
- Encounter goals
- Tactical state
- Belief-based PC profiles
- Monster doctrine & morale

### Outputs
- Selected legal action
- Scoring breakdown
- Telegraphing hints

### Guardrails
- No infinite hard-lock loops
- No un-telegraphed lethal spikes
- Preserve counterplay when feasible

**Status:** PLANNED

---

## 6. Testing & Validation

### Strategy
- Unit tests per Rule Atom
- Golden Transcript replay tests
- Determinism regression on every change

### Transcript Sources
- Hand-curated RAW scenarios
- AI-generated + manually verified cases

**Status:** PLANNED

---

## 7. Voice & Narrative Layer (Deferred)

### Purpose
Player interaction and presentation only.

### Constraints
- Voice → intent → validation → engine → narration
- LLM never invents mechanics

**Status:** DEFERRED UNTIL ENGINE LOCK

---

## 8. Open Questions (Tracked)

- Final implementation language (Python / Rust / TS)
- ASR + TTS model selection
- Exploration & social system formalization

---

## 9. Change Log

- 2026-02-07: Initial canonical execution log created

---

## 10. Lock Policy

Once a section is marked **LOCKED**, changes require:
1. Written justification
2. Impact analysis
3. Version bump

This document is the living execution spine for the project.
