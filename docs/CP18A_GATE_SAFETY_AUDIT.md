# CP-18A — Gate Safety Audit Note

**Document Type:** Capability Gate Safety Verification
**Date:** 2026-02-08
**Packet:** CP-18A (Mounted Combat & Rider–Mount Coupling)
**Auditor:** Design Agent
**Status:** ✅ GATE-SAFE

---

## 1. Executive Summary

**Conclusion:** CP-18A design does NOT require opening any closed capability gate.

CP-18A Mounted Combat operates fully within G-T1 (Tier 1 Mechanics) by:
1. Using existing entity storage patterns (no entity forking)
2. Avoiding permanent stat mutations (no ability drain/damage)
3. Implementing unidirectional coupling (no relational condition graphs)
4. Deferring all gate-crossing features explicitly

---

## 2. Gate Status Review

### 2.1 Open Gates (Available for Use)

| Gate | Status | CP-18A Usage |
|------|--------|--------------|
| **G-T1** (Tier 1 Mechanics) | ✅ OPEN | **USED** — Core mounted combat within this gate |

### 2.2 Closed Gates (Must Not Cross)

| Gate | Status | CP-18A Status | Verification |
|------|--------|---------------|--------------|
| **G-T2A** (Permanent Stat Mutation) | 🔒 CLOSED | ✅ NOT CROSSED | No ability drain/damage, no permanent modifiers |
| **G-T2B** (XP Economy) | 🔒 CLOSED | ✅ NOT CROSSED | No XP costs, no item creation, no permanency |
| **G-T3A** (Entity Forking) | 🔒 CLOSED | ✅ NOT CROSSED | No mount cloning, no simulacrum-class effects |
| **G-T3C** (Relational Conditions) | 🔒 CLOSED | ✅ NOT CROSSED | See Section 3 for detailed analysis |
| **G-T3D** (Transformation History) | 🔒 CLOSED | ✅ NOT CROSSED | No polymorph, no form tracking |

---

## 3. Detailed Gate Analysis

### 3.1 G-T3C (Relational Conditions) — Critical Analysis

**Gate Definition:** Conditions that create bidirectional state dependencies between entities where:
- Condition on Entity A affects Entity B's state
- Entity B's state changes affect Entity A
- Circular or recursive propagation is possible

**Why Mounted Combat Could Appear to Cross This Gate:**

At first glance, rider-mount coupling resembles relational conditions:
- Rider depends on mount for position
- Mount's conditions (prone, defeated) affect rider
- Both entities are "related"

**Why CP-18A Does NOT Cross G-T3C:**

1. **Unidirectional Dependency:**
   - Mount → Rider: Mount conditions trigger rider dismount
   - Rider → Mount: Rider actions direct mount movement
   - **NO circular propagation:** Rider dismounting does not trigger mount state changes

2. **No Condition Graph:**
   - Rider does not "have" mount's conditions
   - Mount does not "have" rider's conditions
   - Each entity's condition dict is independent

3. **Explicit Decoupling Points:**
   - Dismount cleanly severs coupling (removes `mounted_state` and `rider_id`)
   - No dangling references possible
   - No orphaned condition chains

4. **Position Derivation ≠ Condition Relation:**
   - Rider's position derived from mount is **data lookup**, not condition
   - No position "condition" that could propagate

**Grapple Contrast (What WOULD Cross G-T3C):**

Grapple creates true relational conditions:
- Grappler is grappling Target
- Target is grappled by Grappler
- Ending grapple on either affects both
- Grapple checks involve both simultaneously

CP-18A explicitly defers mounted grapple to post-SKR-005.

### 3.2 G-T2A (Permanent Stat Mutation)

**Gate Definition:** Mechanics that permanently modify entity ability scores or derived stats in ways that cannot be cleanly reversed by event replay.

**CP-18A Analysis:**
- No ability score modifications
- No permanent bonuses/penalties
- Higher ground bonus is situational modifier (not stored on entity)
- All mounted combat effects are condition-based and reversible

**Status:** ✅ NOT CROSSED

### 3.3 G-T3A (Entity Forking)

**Gate Definition:** Creating new entities that share lineage, properties, or lifecycle with existing entities.

**CP-18A Analysis:**
- No entity creation
- Mount is pre-existing entity
- Rider is pre-existing entity
- Coupling creates references only, not new entities

**Status:** ✅ NOT CROSSED

---

## 4. Safety Assumptions

The following assumptions MUST remain true for CP-18A to stay gate-safe:

### 4.1 Coupling Model Assumptions

| Assumption | Why Required | Violation Consequence |
|------------|--------------|----------------------|
| Rider-mount coupling is bidirectional references only | Prevents relational condition graph | If conditions propagate bidirectionally, G-T3C violated |
| Dismount atomically clears both references | Prevents orphaned state | Dangling references could create inconsistency |
| Position is derived, not stored on rider when mounted | Prevents position drift | Dual position storage could desync |

### 4.2 Condition Handling Assumptions

| Assumption | Why Required | Violation Consequence |
|------------|--------------|----------------------|
| Mount conditions trigger rider effects (one-way) | Prevents circular propagation | Two-way triggering creates infinite loops |
| Rider conditions do not modify mount | Maintains entity independence | Condition bleeding crosses G-T3C |
| No condition on one entity adds condition to other | Prevents relational condition pattern | Condition chaining is SKR-005 territory |

### 4.3 Skill System Assumptions

| Assumption | Why Required | Violation Consequence |
|------------|--------------|----------------------|
| Ride checks use placeholder modifier | Skill system not implemented | Real skill modifiers require skill kernel |
| No skill-based permanent effects | No XP/permanence | Skill training costs would cross G-T2B |

---

## 5. Future Work That Would Break Assumptions

The following features CANNOT be added without opening gates:

### 5.1 Would Require G-T3C (Relational Conditions)

- **Mounted Grapple:** Grappler-target relationship while mounted
- **Share Pain:** Damage to mount partially applied to rider
- **Life Link:** Mount and rider share HP pool
- **Telepathic Bond:** Mental condition sharing

### 5.2 Would Require G-T2A (Permanent Stat Mutation)

- **Mount Training (permanent):** Changing mount from untrained to war-trained
- **Bonded Mount (paladin):** Permanent stat bonuses on special mount
- **Ability Damage from Fall:** Permanent Dex damage from dismount

### 5.3 Would Require G-T3A (Entity Forking)

- **Phantom Steed:** Creating a mount entity from nothing
- **Mount Duplication:** Cloning mounts
- **Split Consciousness:** Rider mind affecting mount

### 5.4 Would Require G-T2B (XP Economy)

- **Create Magical Mount:** XP cost for permanent mount
- **Enhance Mount:** Permanent magical enhancement

---

## 6. Spellcasting Remains Blocked

**Explicit Confirmation:** CP-18A does NOT enable mounted spellcasting.

- Mounted spellcasting rules (PHB p.157) are noted but NOT designed
- Concentration checks while mounted are OUT OF SCOPE
- Spell area effects from mounted position are OUT OF SCOPE
- All spell-related mounted combat deferred to post-spellcasting CP

**Gate Status:** Spellcasting gates remain fully closed. CP-18A design does not assume or require any spellcasting capability.

---

## 7. Determinism Preservation

CP-18A maintains determinism guarantees:

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Event-sourced state changes | ✅ MET | All coupling changes via events |
| Deterministic RNG usage | ✅ MET | "combat" stream for all rolls |
| Replay-safe ordering | ✅ MET | Explicit event sequences documented |
| No floating point | ✅ MET | All values integer-based |
| No non-deterministic data structures | ✅ MET | Lists used, not sets |

---

## 8. Audit Conclusion

### 8.1 Gate Safety Statement

**I affirm that CP-18A (Mounted Combat & Rider–Mount Coupling) as designed:**

1. ✅ Does NOT require opening G-T2A (Permanent Stat Mutation)
2. ✅ Does NOT require opening G-T2B (XP Economy)
3. ✅ Does NOT require opening G-T3A (Entity Forking)
4. ✅ Does NOT require opening G-T3C (Relational Conditions)
5. ✅ Does NOT require opening G-T3D (Transformation History)
6. ✅ Operates fully within G-T1 (Tier 1 Mechanics)
7. ✅ Maintains all determinism guarantees
8. ✅ Keeps spellcasting fully blocked

### 8.2 Implementation Authorization

An implementing agent MAY proceed with CP-18A implementation under the following conditions:

1. Follow the design document exactly
2. Do not add features beyond documented scope
3. Validate bidirectional coupling consistency
4. Run determinism verification tests (10× replay)
5. Do not implement any deferred/blocked features

### 8.3 Gate Violation Response

If during implementation any of the following occur:

- Condition propagation becomes circular → STOP, report G-T3C violation
- Entity creation becomes necessary → STOP, report G-T3A violation
- Permanent stat changes needed → STOP, report G-T2A violation
- XP costs required → STOP, report G-T2B violation

**Remediation:** Propose degraded alternative that stays within G-T1.

---

**Audit Signature:**
- **Auditor:** Claude (Design Agent)
- **Date:** 2026-02-08
- **Confidence:** 0.95 (High confidence in gate safety)
- **Status:** ✅ APPROVED FOR IMPLEMENTATION

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Authority:** Binding (Governance-Critical)
