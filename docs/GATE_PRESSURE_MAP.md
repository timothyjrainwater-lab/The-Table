# Capability Gate Pressure Map
## Cross-CP / Kernel Dependency & Risk Analysis

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Planning
**Status:** ACTIVE
**Audience:** Project Authority, Architects, Implementers

---

## 1. PURPOSE

This document maps **game mechanics and planned work items** to their
**required capability gates**, highlighting:

- Which mechanics are currently legal
- Which are blocked
- Where degraded implementations are masking future gate pressure
- Where premature CP work would cause rework or violations

It is intended to guide **sequencing decisions**, not implementation details.

---

## 2. CAPABILITY GATES (REFERENCE)

| Gate | Meaning |
|----|--------|
| G-T1 | Tier-1 Mechanics (stateless, non-relational) |
| G-T2A | Permanent Stat Mutation |
| G-T3A | Entity Forking / Creation |
| G-T3C | Relational Conditions |
| G-T3D | Transformation History / Persistence |

---

## 3. CURRENTLY OPEN GATES

| Gate | Status | Notes |
|----|--------|------|
| G-T1 | OPEN | Primary development lane |

All others are **CLOSED**.

---

## 4. MECHANIC → GATE PRESSURE MAP

### 4.1 Movement & Environment

| Mechanic | Gate Required | Current Status | Notes |
|--------|---------------|----------------|------|
| Difficult terrain | G-T1 | FULL | CP-19 |
| Falling damage | G-T1 | FULL | CP-19 |
| Environmental damage (one-shot) | G-T1 | DEFERRED | CP-20 |
| Persistent hazards (fire, acid) | G-T2A | FORBIDDEN | Requires ongoing damage |
| Terrain destruction | G-T3D | FORBIDDEN | Transformation history |

---

### 4.2 Combat Modifiers

| Mechanic | Gate Required | Current Status | Notes |
|--------|---------------|----------------|------|
| Higher ground | G-T1 | FULL | CP-19 |
| Cover | G-T1 | FULL | CP-19 |
| Flanking (true) | G-T3C | FORBIDDEN | Relational |
| Aid Another | G-T3C | FORBIDDEN | Relational |
| Mounted coupling (full) | G-T3C | DEGRADED | CP-18A workaround |

---

### 4.3 Conditions & Control

| Mechanic | Gate Required | Current Status | Notes |
|--------|---------------|----------------|------|
| Simple conditions (prone, stunned) | G-T1 | FULL | CP-16 |
| Grapple (true) | G-T3C | FORBIDDEN | Relational |
| Ongoing status damage | G-T2A | FORBIDDEN | Stat mutation |
| Area control zones | G-T3C | FORBIDDEN | Relational participants |

---

### 4.4 Damage & Effects

| Mechanic | Gate Required | Current Status | Notes |
|--------|---------------|----------------|------|
| Weapon damage | G-T1 | FULL | Core |
| Falling damage | G-T1 | FULL | CP-19 |
| Environmental damage (one-shot) | G-T1 | DEFERRED | CP-20 |
| Damage over time | G-T2A | FORBIDDEN | Persistent mutation |

---

### 4.5 Magic & Spells

| Mechanic | Gate Required | Current Status | Notes |
|--------|---------------|----------------|------|
| Instant spells (MM, CLW) | G-T1 + kernels | DEFERRED | Needs spell kernel |
| Summons | G-T3A | FORBIDDEN | Entity creation |
| Battlefield control spells | G-T3C/D | FORBIDDEN | Zones + persistence |
| Buff durations | G-T2A | FORBIDDEN | Ongoing stat changes |

---

## 5. HIDDEN PRESSURE POINTS

### 5.1 Degraded Mechanics Masking Gates
- Grapple-lite
- Flanking-lite
- Mounted-lite

These **reduce gate pressure temporarily** but **increase future rework cost**.

### 5.2 High-Risk Temptations
- "Just add a duration"
- "Just remember the last state"
- "Just link two entities"

These phrases usually indicate **imminent gate violations**.

---

## 6. STRATEGIC GUIDANCE

### Safe to Advance Now
- CP-20 (environmental damage, discrete)
- More Tier-1 terrain or combat refinements

### Requires Gate Opening
- Full grapple
- True flanking
- Spellcasting beyond trivial instants

### Should Be Avoided Until Kernels Exist
- Persistent environments
- Relational auras or zones
- Spell-created terrain

---

## 7. CONCLUSION

The Gate Pressure Map makes clear:

- **Tier-1 is nearly saturated**
- **SKR-005 (Relational Conditions)** is the next major unlock
- CP-20 is the last high-value, low-risk Tier-1 expansion

This document should be consulted **before proposing any new CP**.

---

## END OF CAPABILITY GATE PRESSURE MAP
