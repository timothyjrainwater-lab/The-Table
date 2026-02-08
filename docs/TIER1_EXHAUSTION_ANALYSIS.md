# Tier-1 Exhaustion Analysis
## Assessing Remaining Value Under G-T1 Constraints

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Capability Tier:** Tier-1 (G-T1)
**Document Type:** Strategic Analysis (Non-Binding)

---

## 1. PURPOSE

This document evaluates whether **Tier-1 (G-T1)** mechanics are effectively
**exhausted**, meaning that additional CPs would yield diminishing returns
without opening new capability gates.

It exists to prevent:
- Endless "one more CP" drift
- Accidental overlap with kernel responsibilities
- Late discovery that work should have been kernelized

---

## 2. DEFINITION: "TIER-1 EXHAUSTION"

Tier-1 is considered *exhausted* when:

1. Remaining unimplemented mechanics are:
   - Low impact, or
   - Better solved by kernel infrastructure
2. New CP proposals increasingly:
   - Re-encode degraded workarounds, or
   - Add polish without unlocking new gameplay
3. Risk of rework exceeds value delivered

---

## 3. CURRENT STATE SNAPSHOT

### Completed Tier-1 Coverage
- Core combat loop
- Attacks of Opportunity
- Combat maneuvers
- Terrain, environment, hazards
- Discrete environmental damage

### Remaining Tier-1 Candidates
- Ready / delay refinements
- Initiative tie-breaking formalization
- Minor AoO edge clarifications

These are **polish-level**, not capability-expanding.

---

## 4. VALUE CURVE ANALYSIS

| Area | Marginal Value | Notes |
|----|----------------|------|
| New combat options | Low | Mostly relational |
| Terrain refinements | Very Low | Already saturated |
| Initiative polish | Medium | Determinism benefit only |
| Reaction timing polish | Medium | Mostly clarity |

The curve has **flattened sharply** after CP-20.

---

## 5. RISK ANALYSIS OF CONTINUING TIER-1

### 5.1 Architectural Risk
- Degraded mechanics become entrenched
- Kernel work becomes harder due to workaround debt

### 5.2 Governance Risk
- CP scope creep
- Blurred line between Tier-1 and Tier-3 responsibilities

### 5.3 Opportunity Cost
- Time spent on Tier-1 delays foundational unlocks

---

## 6. SIGNALS THAT TIER-1 IS "DONE ENOUGH"

The following signals are now present:

- CPs increasingly small and corrective
- Major remaining mechanics blocked by G-T3C
- Stable runtime and determinism baseline
- Clean freeze discipline demonstrated twice

This strongly indicates **Tier-1 exhaustion**.

---

## 7. STRATEGIC OPTIONS

### Option A — Stop Tier-1 Now
- Declare Tier-1 effectively complete
- Pivot to kernel readiness

**Pros:** Clean architecture, no rework
**Cons:** Short-term slowdown

### Option B — One Final Polish CP
- Execute a minimal CP-21 (initiative / ready)
- Explicitly mark it as terminal Tier-1 work

**Pros:** Closure, clarity
**Cons:** Risk of "just one more"

---

## 8. RECOMMENDATION (ANALYSIS ONLY)

Tier-1 is **functionally exhausted**.

Any further work should be:
- Extremely narrow, or
- Deferred until SKR-005 exists

This document does **not** mandate a decision, but provides the evidence.

---

## 9. CONCLUSION

CP-20 represents a **natural capstone** for Tier-1 mechanics.

Further progress now depends less on *what* to add and more on *how* to add it
safely — which is the role of kernels, not CPs.

---

## END OF TIER-1 EXHAUSTION ANALYSIS
