# SKR Dependency Graph
## Kernel → Capability Packet Unlock Mapping

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Architecture / Dependency Analysis
**Status:** ACTIVE
**Audience:** Project Authority, Architects, Roadmap Owners

---

## 1. PURPOSE

This document defines the **explicit dependency relationships** between
**System Kernels (SKRs)** and **Capability Packets (CPs)**.

Its goals are to:
- Prevent designing features that cannot be implemented
- Clarify which kernels unlock the most downstream value
- Guide gate-opening decisions with concrete payoff analysis

---

## 2. KERNEL OVERVIEW

| Kernel | Gate | Purpose |
|------|------|---------|
| SKR-005 | G-T3C | Relational Conditions |
| SKR-010 | G-T3D | Transformation History |
| SKR-001 | G-T3A | Entity Forking / Creation |
| SKR-020 | G-T2A | Persistent Stat Mutation |
| Spell Kernel | Mixed | Spellcasting framework |

---

## 3. PRIMARY DEPENDENCY GRAPH

### 3.1 SKR-005 — Relational Conditions (Highest Leverage)

**Unlocks:**
- True grapple
- True flanking
- Aid Another
- Proper mounted rider–mount coupling
- Multi-entity combat maneuvers
- Many non-damaging spells

**Blocked Without It:**
- Any mechanic involving ≥2 participants
- Any shared tactical state

**Dependency Cost:** High (design + audit)
**Payoff:** Very High

---

### 3.2 SKR-010 — Transformation History

**Unlocks:**
- Terrain destruction
- Persistent hazards
- Buff/debuff durations
- Environmental state changes

**Blocked Without It:**
- Ongoing effects
- Any "remembers last turn" mechanic

**Dependency Cost:** Very High
**Payoff:** High (but later)

---

### 3.3 SKR-001 — Entity Forking

**Unlocks:**
- Summons
- Minions
- Spawned hazards
- Illusions with presence

**Blocked Without It:**
- Creature creation
- Independent conjured entities

**Dependency Cost:** High
**Payoff:** Medium–High

---

### 3.4 SKR-020 — Persistent Stat Mutation

**Unlocks:**
- Damage over time
- Buff durations
- Debuff stacks
- Exhaustion/fatigue

**Blocked Without It:**
- Most spell durations
- Environmental exposure

**Dependency Cost:** High
**Payoff:** Medium

---

### 3.5 Spellcasting Kernel (Composite)

**Depends On:**
- SKR-005 (relations)
- SKR-010 (durations)
- SKR-020 (stat mutation)
- SKR-001 (summons)

**Unlocks:**
- Full spellcasting system

**Dependency Cost:** Extreme
**Payoff:** Very High (but last)

---

## 4. CP DEPENDENCY SUMMARY

| CP | Depends On | Status |
|---|------------|-------|
| CP-18 | — | COMPLETE |
| CP-19 | — | COMPLETE |
| CP-20 | — | READY |
| CP-21 | — | OPTIONAL |
| Grapple CP | SKR-005 | BLOCKED |
| Spellcasting CP | All kernels | BLOCKED |

---

## 5. STRATEGIC SEQUENCING RECOMMENDATION

### Recommended Order
1. **Finish Tier-1 line** (CP-20, small CP-21 if desired)
2. **Open SKR-005 (G-T3C)** — highest leverage kernel
3. Delay SKR-010 until terrain/spells demand it
4. Open SKR-001 only when summoning is needed
5. Spellcasting last

### Rationale
- SKR-005 unlocks the most mechanics with the least persistence risk
- Other kernels compound complexity rapidly
- Premature spellcasting multiplies failure modes

---

## 6. CONCLUSION

The dependency graph makes clear:

- **SKR-005 is the next architectural inflection point**
- Tier-1 expansion is nearly exhausted
- Kernel sequencing must be intentional or rework cost explodes

This document should be consulted **before any gate-opening proposal**.

---

## END OF SKR DEPENDENCY GRAPH
