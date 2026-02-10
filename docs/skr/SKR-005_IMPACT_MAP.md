# SKR-005 Impact Map
## Relational Conditions Kernel — Before/After Capability Analysis

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Kernel:** SKR-005 (Relational Conditions)
**Capability Gate:** G-T3C
**Document Type:** Impact & ROI Analysis (Non-Binding)

---

## 1. PURPOSE

This document maps **exactly which mechanics are blocked, degraded, or awkward**
without relational infrastructure, and how **SKR-005** would change that state.

It exists to:
- Make kernel ROI explicit
- Prevent vague "it unlocks a lot" arguments
- Support a clean G-T3C gate decision

This document does **not** authorize implementation.

---

## 2. BASELINE (CURRENT STATE WITHOUT SKR-005)

### 2.1 Structural Limitation

Under G-T1:
- Entities cannot hold authoritative references to other entities
- Multi-participant state must be flattened or approximated
- Teardown symmetry is difficult to guarantee

As a result, many mechanics are either:
- Simplified ("lite")
- Deferred
- Explicitly forbidden

---

## 3. MECHANIC-BY-MECHANIC IMPACT

### 3.1 Grapple

| Aspect | Without SKR-005 | With SKR-005 |
|-----|-----------------|--------------|
| State ownership | Per-entity flags | Single relation record |
| Teardown | Asymmetric risk | Atomic teardown |
| Determinism | Fragile | Enforced |
| Coverage | DEGRADED | FULL |

**Impact:** High
**Notes:** One of the strongest justifications for SKR-005.

---

### 3.2 Flanking

| Aspect | Without SKR-005 | With SKR-005 |
|-----|-----------------|--------------|
| Participant count | Implicit / heuristic | Explicit participants |
| Edge cases | Numerous | Centralized |
| Determinism | Risky | Stable |
| Coverage | DEGRADED | FULL |

**Impact:** High
**Notes:** True flanking is inherently relational.

---

### 3.3 Aid Another

| Aspect | Without SKR-005 | With SKR-005 |
|-----|-----------------|--------------|
| Link between entities | Impossible | Explicit |
| Bonus lifetime | Awkward | Relation-bound |
| Coverage | DEFERRED | FULL |

**Impact:** Medium–High
**Notes:** Simple mechanically, but unsafe without relations.

---

### 3.4 Mounted Combat (Full Coupling)

| Aspect | Without SKR-005 | With SKR-005 |
|-----|-----------------|--------------|
| Rider–mount state | Loosely coupled | Explicit relation |
| Failure cases | Ad hoc | Centralized |
| Coverage | DEGRADED | FULL |

**Impact:** Medium
**Notes:** Current CP-18A workaround is serviceable but limited.

---

### 3.5 Multi-Entity Maneuvers

| Aspect | Without SKR-005 | With SKR-005 |
|-----|-----------------|--------------|
| Participants | Implicit | Explicit |
| Resolution | Branch-heavy | Kernel-mediated |
| Coverage | PARTIAL | FULL |

**Impact:** Medium
**Notes:** Enables cleaner implementations later.

---

### 3.6 Non-Damaging Spells (Future)

| Aspect | Without SKR-005 | With SKR-005 |
|-----|-----------------|--------------|
| Targets | Single only | Multi-entity |
| Effects | Flattened | Relational |
| Coverage | FORBIDDEN | POSSIBLE |

**Impact:** Very High (future)
**Notes:** Spellcasting depends on this kernel.

---

## 4. AGGREGATE ROI VIEW

### 4.1 What SKR-005 Unlocks Immediately

- Removes need for multiple "lite" mechanics
- Centralizes multi-entity teardown logic
- Reduces determinism risk surface area

### 4.2 What It Prevents

- Ad hoc relational hacks
- Silent coupling between entities
- Future refactors of flattened mechanics

---

## 5. COSTS & TRADEOFFS

### Costs
- Significant design + audit effort
- Higher test complexity
- Slower initial velocity

### Tradeoffs
- Short-term slowdown for long-term safety
- Fewer CPs, but more capable ones

---

## 6. STRATEGIC TAKEAWAY

SKR-005 does **not** merely add features.

It:
- Collapses multiple degraded mechanics into clean implementations
- Reduces future complexity growth
- Establishes a safe pattern for all relational logic

In ROI terms, it is a **force multiplier**, not a feature.

---

## 7. CONCLUSION

If the project intends to progress beyond Tier-1 meaningfully,
**SKR-005 is unavoidable**.

This impact map makes clear **why**, **where**, and **how much** value it delivers,
so the gate decision can be made with eyes open.

---

## END OF SKR-005 IMPACT MAP
