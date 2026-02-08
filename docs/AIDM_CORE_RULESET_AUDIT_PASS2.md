# AIDM Core Ruleset Audit — Pass 2 (CCMA) Continuation

## CRITICAL CCMA FINDINGS (Top 20 Highest-Risk Mechanics)

This document continues the comprehensive audit with detailed CCMA analysis of the most critical hazards.

---

### CCMA-001: Simulacrum (Wiz 7)
**Source:** PHB p.279
**Risk Level:** CRITICAL (Tier 0 - Reference Hazard)

**Engine Assumptions Violated:**
1. **Entity Uniqueness** — Creates a duplicate entity with partial abilities
2. **Immutable Base Stats** — Template has permanent -2 to all ability scores
3. **XP Economy** — 100 XP per HD cost is permanent, non-recoverable
4. **Lifecycle Independence** — Simulacrum exists independently but is not "alive" (can't heal naturally)

**Entities/States Coupled:**
- Caster ↔ Simulacrum (creation dependency)
- Template entity ↔ Simulacrum (ability score reference with penalty)
- XP pool ↔ Entity creation (permanent expenditure)

**What Breaks if Implemented Late:**
- Entity registry assumes all entities have independent origins
- Ability score system assumes no permanent penalties outside ability drain
- XP tracking assumes XP is only spent on leveling (monotonic)
- Healing/recovery assumes all entities follow same rules

**Required Infrastructure:**
- **Entity Lineage Tracking Kernel** — parent/child relationships
- **Template System** — entity created from another entity with modifications
- **Permanent XP Expenditure Log** — non-recoverable resource tracking
- **Lifecycle Classification** — "construct-like" vs "living" healing rules

**Sequencing Constraints:**
- MUST implement before any spellcasting engine goes live
- REQUIRES entity forking kernel (new CP)
- BLOCKS: Clone, Astral Projection, Create Undead, Planar Binding

---

### CCMA-002: Ability Drain (Permanent)
**Source:** PHB p.307, MM p.305
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Event Reversibility** — Ability drain is permanent until magically restored
2. **Base Stats Immutability** — Current architecture treats ability scores as static
3. **Derived Stats Recalculation** — HP, AC, attack bonuses must recalculate when base changes

**Entities/States Coupled:**
- Ability score ↔ HP max (CON drain affects HP)
- Ability score ↔ AC (DEX drain affects AC)
- Ability score ↔ Attack bonus (STR drain affects melee attack)
- Ability score ↔ Save DCs (CHA/WIS/INT drain affects spellcasting)

**What Breaks if Implemented Late:**
- CP-16 (Conditions) assumes temporary modifiers only
- HP tracking assumes `hp_max` is constant except level changes
- Replay system assumes ability scores don't change mid-session

**Required Infrastructure:**
- **Permanent Ability Modification Log** — track drain separately from damage
- **Bidirectional Recalculation Engine** — ability score changes trigger derived stat updates
- **Restoration Spell Integration** — requires spell system to reference drain log

**Sequencing Constraints:**
- MUST implement before monsters with drain attacks (Shadow, Wraith, Spectre, Vampire)
- REQUIRES expansion of CP-16 or new kernel
- BLOCKS: Energy Drain, Feeblemind, Restoration spells

---

### CCMA-003: Grapple
**Source:** PHB p.156
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Single-Actor Actions** — Grapple is a multi-phase, multi-actor resolution
2. **Action Economy Independence** — Grappler and grappled have coupled action restrictions
3. **State Independence** — "Grappled" condition requires tracking WHO is grappling you

**Entities/States Coupled:**
- Grappler ↔ Grappled (bidirectional state, both have condition)
- Grappler's position ↔ Grappled's position (forced movement propagation)
- Grappler's action economy ↔ Grappled's escape attempts (contested checks)

**What Breaks if Implemented Late:**
- CP-16 (Conditions) assumes conditions are unary (entity has condition, not "entity A grapples entity B")
- Movement system assumes independent position changes
- Action resolution assumes single-actor intent

**Required Infrastructure:**
- **Relational Condition System** — conditions with entity references (grappled_by: entity_id)
- **Multi-Actor Resolution Kernel** — opposed check sequences
- **Pin Substates** — grapple → pin progression tracking

**Sequencing Constraints:**
- REQUIRES relational condition system (CP-16 expansion or new CP)
- BLOCKS: Constrict, Improved Grab, Swallow Whole (monster abilities)
- SIMILAR HAZARD: Mounted Combat (rider+mount coupling)

---

### CCMA-004: Readied Actions
**Source:** PHB p.160
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Turn-Based Resolution** — Readied actions interrupt other actors' turns
2. **Initiative Order Immutability** — Ready changes your initiative to just before trigger
3. **Conditional Execution** — Requires monitoring game state for trigger conditions

**Entities/States Coupled:**
- Readying actor's turn ↔ Triggering actor's turn (interrupt insertion)
- Readying actor's action ↔ World state (condition monitoring)
- Initiative order ↔ Runtime state (mutable turn order)

**What Breaks if Implemented Late:**
- CP-09 (Combat Structure) assumes fixed initiative order
- Action resolution assumes atomic turn execution
- Event log assumes chronological ordering without insertions

**Required Infrastructure:**
- **Interrupt Queue System** — out-of-turn action storage
- **Trigger Condition Monitor** — watch for specified game state changes
- **Dynamic Initiative Reordering** — modify turn order mid-round

**Sequencing Constraints:**
- REQUIRES major CP-09 overhaul OR separate interrupt kernel
- BLOCKS: Counterspelling, Contingency, Immediate Actions (Swift/Immediate split)
- HIGH COMPLEXITY: Nested triggers (readied action triggers another readied action)

---

### CCMA-005: Time Stop (Wiz 9)
**Source:** PHB p.294
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Single Timeline** — Time Stop gives caster 1d4+1 additional turns in a "paused" timeline
2. **Turn Ordering** — Other entities frozen, time passes differently for caster
3. **Effect Duration** — Ongoing effects don't progress during timestop for non-casters

**Entities/States Coupled:**
- Caster's timeline ↔ World timeline (divergence)
- Caster's actions ↔ Other entities (one-way interaction: caster can't affect others)
- Duration tracking ↔ Active entity (some effects tick, others don't)

**What Breaks if Implemented Late:**
- CP-09 assumes single turn sequencing
- CP-17 (Turn Timers) assumes uniform time progression
- Effect duration assumes all entities experience time identically

**Required Infrastructure:**
- **Timeline Branching System** — parallel time streams
- **Effect Suspension Rules** — which effects tick during timestop
- **Deferred Interaction Resolution** — actions that take effect after timestop ends

**Sequencing Constraints:**
- REQUIRES timeline kernel (completely new)
- BLOCKS: Temporal Stasis, Haste/Slow (time manipulation hierarchy)
- EXTREME COMPLEXITY: Spell effect resolution during divergent timelines

---

### CCMA-006: Dominated Agency (Dominate Person/Monster)
**Source:** PHB p.224
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Autonomous Agency** — Entity decisions made externally by dominating caster
2. **Intent Origin** — Action intents come from controller, not controlled entity
3. **Condition as Control Override** — "Dominated" is not just a modifier, it's agency transfer

**Entities/States Coupled:**
- Controlled entity's decisions ↔ Controller's decisions (external agency)
- Controlled entity's knowledge ↔ Controller's knowledge (epistemic transfer?)
- Controlled entity's action economy ↔ Controller's mental action (commands)

**What Breaks if Implemented Late:**
- Policy engine assumes entity ID → decision mapping is 1:1
- Intent generation assumes entity originates its own intents
- CP-16 (Conditions) assumes conditions modify, not replace, agency

**Required Infrastructure:**
- **Agency Delegation System** — entity acts on behalf of another
- **Control Hierarchy** — who controls whom, nesting rules
- **Epistemic Boundary Rules** — what controlled entity can/can't reveal

**Sequencing Constraints:**
- REQUIRES agency kernel before charm/dominate spells
- BLOCKS: Charm spells (weaker version), Planar Binding, Suggestion
- SIMILAR HAZARD: Planar Ally (negotiated service), Geas/Quest (compulsion)

---

### CCMA-007: Find Familiar (Wiz 1)
**Source:** PHB p.232
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Entity Independence** — Master and familiar share HP pool (1:2 ratio)
2. **Composite Actor** — Two entities, but damage to one affects both
3. **Telepathic Link** — Epistemic state sharing (senses, communication)

**Entities/States Coupled:**
- Master HP ↔ Familiar HP (damage to familiar → master takes half)
- Master senses ↔ Familiar senses (caster can see through familiar)
- Master position ↔ Familiar position (deliver touch spells remotely)

**What Breaks if Implemented Late:**
- HP tracking assumes single entity owns its HP
- Damage resolution assumes target is only affected entity
- Targeting assumes caster casts from own position

**Required Infrastructure:**
- **Shared Resource Pool System** — HP mirroring/splitting
- **Proxy Sensing Kernel** — remote perception
- **Touch Spell Delivery** — alternate origin point for spell effects

**Sequencing Constraints:**
- REQUIRES composite actor kernel before wizard spellcasting
- BLOCKS: Psicrystal (similar), Animal Companion (weaker version)
- MEDIUM COMPLEXITY: Familiar death consequences (1d6 days no familiar, CON loss)

---

### CCMA-008: Energy Drain (Negative Levels)
**Source:** MM p.310, PHB p.293
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Temporary vs Permanent** — Negative levels are temporary at first, become permanent if not removed
2. **Level Loss Mechanics** — Negative levels reduce effective level, not actual level
3. **Death Threshold** — Negative levels equal to HD = instant death

**Entities/States Coupled:**
- Negative level count ↔ Effective character level (affects saves, HP, attack)
- Negative level count ↔ HD (death condition)
- Negative level timer ↔ Permanence (24 hours → Fort save or permanent)

**What Breaks if Implemented Late:**
- XP/level system assumes levels only increase
- CP-17 (Turn Timers) doesn't handle permanence transitions
- Death condition assumes HP <= 0, not level-based death

**Required Infrastructure:**
- **Negative Level Tracking** — separate from ability drain
- **Permanence Transition System** — temporary → permanent conversion
- **Level-Based Death Check** — new defeat condition

**Sequencing Constraints:**
- REQUIRES before Vampire, Wraith, Spectre, Wight attacks
- BLOCKS: Restoration spells (must remove negative levels)
- SIMILAR HAZARD: Ability Drain (also has permanent transition)

---

### CCMA-009: Planar Binding (Outsider Control)
**Source:** PHB p.262
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Service Contracts** — Bound outsider serves caster, but can negotiate/resist
2. **Summoning vs Controlling** — Entity exists independently but is compelled
3. **Charisma Check for Control** — Contested check determines if binding succeeds

**Entities/States Coupled:**
- Summoned outsider ↔ Caster (service obligation)
- Summoned outsider's will ↔ Caster's Charisma (control check)
- Summoned outsider's duration ↔ Service completion (dismissal condition)

**What Breaks if Implemented Late:**
- Entity creation assumes entities are autonomous or fully controlled (no middle ground)
- Duration tracking assumes time-based, not task-based
- Agency assumes binary (controlled or independent)

**Required Infrastructure:**
- **Service Contract System** — task-based entity obligations
- **Negotiation Rules** — contested checks for control degree
- **Task Completion Monitoring** — detect when service obligation is fulfilled

**Sequencing Constraints:**
- REQUIRES agency delegation + contract kernel
- BLOCKS: Planar Ally (divine variant), Gate (calling option)
- EXTREME COMPLEXITY: Outsider can work against caster if control fails

---

### CCMA-010: Lich Phylactery (Rejuvenation)
**Source:** MM p.166
**Risk Level:** CRITICAL

**Engine Assumptions Violated:**
1. **Entity Permanence** — Lich destroyed → auto-resurrects at phylactery in 1d10 days
2. **Death as Terminal State** — Death is reversible without external magic
3. **Object Dependency** — Entity lifecycle tied to separate object's existence

**Entities/States Coupled:**
- Lich entity ↔ Phylactery object (lifecycle dependency)
- Lich death event ↔ Phylactery location (respawn point)
- Lich destruction ↔ Phylactery destruction (only way to truly kill)

**What Breaks if Implemented Late:**
- Entity defeat assumes "defeated" is terminal state
- Resurrection assumes external spell required
- Object destruction doesn't affect entity states

**Required Infrastructure:**
- **Object-Entity Binding System** — lifecycle dependencies
- **Rejuvenation Rules** — auto-resurrection mechanics
- **True Death Conditions** — defeat phylactery → permanent death

**Sequencing Constraints:**
- REQUIRES entity lifecycle expansion
- BLOCKS: Ghost rejuvenation (similar), Tarrasque regeneration
- SIMILAR HAZARD: Construct with control amulet (object-entity binding)

---

## CCMA Summary — Top 10 Critical Hazards

| Rank | Hazard | Kernel Required | Blocks # Other Mechanics |
|------|--------|----------------|--------------------------|
| 1 | **Simulacrum** | Entity Forking + XP Costs | 15+ (all entity creation) |
| 2 | **Ability Drain** | Permanent Stat Modification | 12+ (all drain/restore) |
| 3 | **Readied Actions** | Interrupt System | 8+ (counterspell, contingency) |
| 4 | **Grapple** | Relational Conditions | 6+ (all coupled-state combat) |
| 5 | **Dominated Agency** | Agency Delegation | 14+ (all control effects) |
| 6 | **Time Stop** | Timeline Branching | 4+ (all time manipulation) |
| 7 | **Find Familiar** | Composite Actors | 5+ (all shared-resource actors) |
| 8 | **Energy Drain** | Negative Levels | 8+ (all level drain/restoration) |
| 9 | **Planar Binding** | Service Contracts | 7+ (all summoning with obligation) |
| 10 | **Lich Phylactery** | Rejuvenation/Lifecycle | 4+ (all auto-resurrection) |

**CRITICAL FINDING:**
These 10 hazards collectively block implementation of **80+ subsystems**. They must be addressed in sequenced kernel development, not as incidental logic.

---

## Pass 2 Status

**Completed:** 10 of 67 HIGH-risk CCMA audits
**Finding:** All 10 require new kernel infrastructure
**None can be safely implemented as "incidental logic"**

**Recommendation:**
Create **Structural Kernel Register (SKR)** with mandatory sequencing before proceeding to spell implementation.

---

*Continuing to Pass 3 (Interaction Scan)...*
