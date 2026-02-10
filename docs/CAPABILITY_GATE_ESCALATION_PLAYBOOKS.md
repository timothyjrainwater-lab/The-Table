# Capability Gate Escalation Playbooks

**Project:** Deterministic D&D 3.5e AI Dungeon Master (AIDM)
**Authority:** Governance (Design-Blocking)
**Status:** Canonical Reference
**Applies To:** All CPs ≥ CP-18

---

## 0. PURPOSE

This document defines **how and when closed capability gates may be escalated**, and—critically—what **must NOT be approximated** before escalation.

Its goal is to prevent:

* Ad-hoc gate debates
* Partial or leaky implementations
* Silent violations hidden behind "temporary" logic

This document **does not open any gates**.

---

## 1. GLOBAL RULES (BINDING)

1. A closed gate may only be opened by **explicit decision record**.
2. Partial approximations of gated functionality are **forbidden** unless explicitly listed as a degraded alternative.
3. If pressure is discovered mid-CP:

   * STOP
   * RECORD the pressure
   * DEFER or DEGRADE

---

## 2. G-T2A — Permanent Stat Mutation

### What This Gate Protects

* Ability score changes
* Persistent bonuses/penalties
* Level-based stat growth

### Common Pressure Signals

* Ability damage/drain
* Long-duration buffs
* Environmental fatigue/exhaustion

### Evidence Required to Open

* Stat persistence kernel
* Rollback / replay safety guarantees
* Clear lifetime model for mutations

### Allowed Degradations

* Situational modifiers (applied and removed in one action)
* Narrative-only effects

### Explicitly Forbidden Before Opening

* Storing modified stats in entity state
* Carrying modifiers across turns/scenes

---

## 3. G-T2B — XP Economy

### What This Gate Protects

* XP gain/loss
* Level progression
* Item creation costs

### Common Pressure Signals

* Reward calculation logic
* Scaling difficulty systems
* Crafting or permanence costs

### Evidence Required to Open

* XP accounting kernel
* Deterministic reward model
* Anti-farming safeguards

### Allowed Degradations

* Narrative XP only
* Fixed progression scenarios (no accumulation)

### Explicitly Forbidden Before Opening

* Incrementing XP counters
* Partial level-up logic

---

## 4. G-T3A — Entity Forking

### What This Gate Protects

* Summons
* Clones
* Independent environmental entities

### Common Pressure Signals

* Summoned creatures
* Spawned hazards
* Illusions with agency

### Evidence Required to Open

* Entity lifecycle kernel
* Cleanup and ownership rules
* Deterministic spawn ordering

### Allowed Degradations

* Narrative-only entities
* Effects resolved without new entities

### Explicitly Forbidden Before Opening

* Creating persistent entities
* Shadow entities without lifecycle control

---

## 5. G-T3C — Relational Conditions

### What This Gate Protects

* Bidirectional state
* Shared condition graphs
* Multi-entity persistence

### Common Pressure Signals

* Full grapple
* Mount–rider mutual conditions
* Environmental entanglement

### Evidence Required to Open

* Relational condition kernel (SKR-005)
* Graph management + cycle detection
* Deterministic update ordering

### Allowed Degradations

* Unidirectional conditions
* Terminal effects (dismount, knockdown)

### Explicitly Forbidden Before Opening

* Bidirectional condition flags
* Condition inheritance chains

---

## 6. G-T3D — Transformation History

### What This Gate Protects

* Polymorph
* Size/type changes
* Form history stacking

### Common Pressure Signals

* Shapechange
* Size-altering effects
* Terrain-driven transformations

### Evidence Required to Open

* Transformation history kernel
* Reversion rules
* Stacking resolution

### Allowed Degradations

* Narrative form changes
* Temporary numeric modifiers only

### Explicitly Forbidden Before Opening

* Recording form history
* Partial polymorph logic

---

## 7. HOW TO USE THIS DOCUMENT

When designing a CP:

1. Identify which gates are pressured
2. Consult the relevant section
3. Choose **degrade, defer, or escalate**
4. Record the decision explicitly

Silence is not allowed.

---

## 8. FINAL NOTE

Capability gates exist to **protect determinism and correctness**.

They are not obstacles to bypass—they are contracts to respect.
