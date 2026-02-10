# CP-21 Disqualification Criteria
## Conditions Under Which CP-21 Should NOT Proceed

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Decision Guardrails
**Status:** ACTIVE (Analysis-Only)

---

## 1. PURPOSE

This document defines **explicit disqualification criteria** for a potential
CP-21, intended to prevent:

- Momentum-driven scope creep
- Reintroduction of degraded mechanics
- Delaying necessary kernel work (SKR-005)

The goal is to make it *easier to say "no"* to CP-21 unless it clearly adds value
under Tier-1 constraints.

---

## 2. GOVERNING PRINCIPLE

CP-21 should proceed **only if it delivers net new value** that:

- Is strictly Tier-1 (G-T1 compliant)
- Does not duplicate or preempt SKR-005 responsibilities
- Does not require rework once relational infrastructure exists

If these cannot be proven, CP-21 is disqualified.

---

## 3. HARD DISQUALIFIERS (ANY ONE IS SUFFICIENT)

CP-21 must be rejected if **any** of the following are true:

### DQ-01: Relational Dependency
- The proposal requires:
  - ≥2 entities in a shared mechanical state, or
  - Bidirectional effects, or
  - Participant lists

**Rationale:** Requires G-T3C / SKR-005.

---

### DQ-02: Persistence or Duration
- The proposal introduces:
  - Ongoing effects
  - State that survives turns implicitly
  - "Until" semantics

**Rationale:** Pressures G-T2A or G-T3D.

---

### DQ-03: Kernel Overlap
- The proposal overlaps with mechanics already mapped to:
  - SKR-005
  - SKR-010
  - SKR-020

**Rationale:** Kernel work should not be pre-implemented piecemeal.

---

### DQ-04: Degraded Re-Implementation
- The proposal improves a "lite" mechanic that:
  - Will be replaced post-kernel
  - Cannot reach full correctness without relations

**Rationale:** Creates throwaway work.

---

### DQ-05: Low Marginal Value
- The proposal:
  - Affects rare edge cases only, or
  - Provides cosmetic clarity without mechanical impact

**Rationale:** Tier-1 returns are already diminished.

---

## 4. SOFT DISQUALIFIERS (REQUIRE STRONG JUSTIFICATION)

These do not automatically reject CP-21, but require **exceptional rationale**:

### SDQ-01: Pure Polish
- Documentation-only or minor rule clarification
- No new tests required

### SDQ-02: Complexity Without Capability
- Adds branching or logic without unlocking new play

---

## 5. EXAMPLES

### Likely Disqualified
- "Improve flanking math"
- "Enhance grapple-lite"
- "Persistent overwatch"
- "Opportunity zones"

### Potentially Acceptable (But Narrow)
- Initiative tie-breaking formalization
- Ready/delay trigger clarification

Even these must pass all disqualifier checks.

---

## 6. DECISION CHECKLIST (USE BEFORE PROPOSING CP-21)

Before drafting CP-21, all must be answered "NO":

- Does this require relational state?
- Does this require persistence?
- Will this be replaced by SKR-005?
- Does this introduce future rework?

If any answer is "YES" → CP-21 is disqualified.

---

## 7. STRATEGIC INTENT

This document exists to:
- Protect architectural integrity
- Make kernel pivots easier
- Avoid sunk-cost fallacies

Rejecting CP-21 is a **success condition**, not a failure.

---

## 8. CONCLUSION

CP-21 should be the *exception*, not the default.

Unless a proposal clearly survives these criteria, the correct move is to
**pause Tier-1 expansion and pivot to kernel work**.

---

## END OF CP-21 DISQUALIFICATION CRITERIA
