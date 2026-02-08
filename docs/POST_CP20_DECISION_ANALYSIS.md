# Post-CP-20 Decision Analysis
## Strategic Options After Tier-1 Completion

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Analysis / Decision Support (NON-BINDING)
**Status:** ANALYSIS COMPLETE
**Date:** 2026-02-09
**Audience:** Project Authority

---

## 1. PURPOSE

This document provides **decision-grade analysis** for the project's next steps
after CP-20 completes. It does not authorize implementation or open any gates.

It answers:
- What Tier-1 mechanics remain that are valuable and gate-safe?
- What evidence indicates Tier-1 is "done enough"?
- What risks increase if Tier-1 continues too long?
- What benefits are blocked until SKR-005 exists?

---

## 2. EXECUTIVE SUMMARY

**Finding:** Tier-1 expansion is effectively saturated after CP-20.

- Remaining G-T1 candidates provide diminishing value
- Multiple degraded mechanics are accumulating technical debt
- SKR-005 (Relational Conditions) is the highest-leverage next step
- Delaying kernel work increases rework cost without proportional benefit

**Recommendation Options (for Project Authority decision):**

| Option | Description | Risk | Value |
|--------|-------------|------|-------|
| A | Stop Tier-1, pivot to SKR-005 | Low | High |
| B | Execute one small CP-21, then pivot | Very Low | Medium |
| C | Continue Tier-1 expansion | Medium | Low |

---

## 3. TIER-1 MECHANICS REMAINING

### 3.1 Candidates That Are Valuable and Gate-Safe

| Mechanic | Value | Risk | Reference |
|----------|-------|------|-----------|
| Ready/Delay refinement | Low-Medium | Very Low | CP21 Feasibility §3.1 |
| Initiative tie-breaking | Low | Very Low | CP21 Feasibility §3.3 |
| Reach/threatened area clarity | Medium | Low (with discipline) | CP21 Feasibility §3.2 |

### 3.2 Candidates Explicitly Rejected (Gate Violations)

| Mechanic | Required Gate | Status |
|----------|---------------|--------|
| Full flanking | G-T3C | FORBIDDEN |
| True grapple | G-T3C | FORBIDDEN |
| Aid Another | G-T3C | FORBIDDEN |
| Persistent hazards | G-T2A | FORBIDDEN |
| Terrain destruction | G-T3D | FORBIDDEN |

### 3.3 Assessment

The remaining G-T1 candidates are:
- **Low-impact:** Mostly invisible to players
- **Polish-oriented:** Rules cleanup, not new capabilities
- **Diminishing:** Each successive CP provides less tactical expansion

---

## 4. EVIDENCE THAT TIER-1 IS "DONE ENOUGH"

### 4.1 Coverage Indicators

Per the Rules Coverage Ledger:

| Category | FULL | DEGRADED | DEFERRED | FORBIDDEN |
|----------|------|----------|----------|-----------|
| Movement | 6 | 1 | 3 | 0 |
| Environment | 6 | 2 | 2 | 1 |
| Combat Modifiers | 2 | 3 | 1 | 0 |
| Conditions | 1 | 0 | 0 | 2 |
| Damage | 3 | 0 | 1 | 1 |

**Observation:** FULL coverage dominates in Movement and Environment.
DEGRADED entries cluster around **relational mechanics** (flanking, grapple, mounted).

### 4.2 Gate Pressure Indicators

Per the Gate Pressure Map:

- 3 DEGRADED mechanics directly await G-T3C (SKR-005)
- 0 new G-T1 mechanics would reduce this pressure
- Continuing G-T1 does not unlock any blocked mechanics

### 4.3 Test and Runtime Evidence

- 751 tests pass in <2s (post-CP-20)
- No known determinism violations
- No open escalations

### 4.4 Conclusion

Tier-1 has delivered its primary value. Further expansion yields:
- Marginal tactical depth
- No unblocking of higher-value mechanics
- Increasing opportunity cost

---

## 5. RISKS OF PROLONGED TIER-1 EXPANSION

### 5.1 Technical Debt Accumulation

Each DEGRADED mechanic represents a future rework obligation:

| Mechanic | Current State | Rework Trigger |
|----------|---------------|----------------|
| Grapple-lite | Simplified | SKR-005 |
| Flanking-lite | Simplified | SKR-005 |
| Mounted-lite | Degraded coupling | SKR-005 |

Extending Tier-1 does not reduce this debt; it may increase it if new
mechanics implicitly depend on degraded foundations.

### 5.2 Complexity Creep

Small CPs accumulate:
- Edge cases
- Test surface
- Documentation overhead

Without kernel payoff, this complexity is not amortized.

### 5.3 Delayed Value Delivery

Mechanics blocked by G-T3C represent high player-visible value:
- True flanking (tactical positioning)
- True grapple (control combat)
- Aid Another (party coordination)

Every sprint spent on low-value Tier-1 delays these.

---

## 6. BENEFITS BLOCKED UNTIL SKR-005 EXISTS

### 6.1 Mechanics Requiring Relational Conditions

| Mechanic | Value | Blocked By |
|----------|-------|------------|
| True grapple | High | G-T3C |
| True flanking | High | G-T3C |
| Aid Another | Medium | G-T3C |
| Mounted rider-mount coupling | Medium | G-T3C |
| Multi-entity combat maneuvers | Medium | G-T3C |
| Non-damaging spells (many) | High | G-T3C + Spell Kernel |

### 6.2 Downstream Cascade

Per SKR Dependency Graph:

- SKR-005 is prerequisite for Spellcasting Kernel
- SKR-005 unlocks the largest class of blocked mechanics
- Delaying SKR-005 delays all downstream work

### 6.3 Strategic Implication

SKR-005 is the **architectural inflection point**. The longer it is delayed,
the more value remains unrealized.

---

## 7. DECISION OPTIONS (FOR PROJECT AUTHORITY)

### Option A: Stop Tier-1, Pivot to SKR-005 Immediately

**Action:**
- Close CP-20 (in progress)
- Skip CP-21
- Begin SKR-005 design audit and gate-opening process

**Pros:**
- Fastest path to high-value mechanics
- Reduces technical debt trajectory
- Aligns with strategic priority

**Cons:**
- Leaves some polish work undone
- Requires gate-opening authorization

**Risk Level:** Low (SKR-005 design already complete)

---

### Option B: Execute One Small CP-21, Then Pivot

**Action:**
- Close CP-20
- Execute CP-21 (Ready/Delay refinement or Initiative ordering)
- Then begin SKR-005 process

**Pros:**
- Provides clean "Tier-1 complete" milestone
- Low implementation risk
- Allows final polish

**Cons:**
- Marginal value delivered
- Slightly delays kernel work

**Risk Level:** Very Low

---

### Option C: Continue Tier-1 Expansion

**Action:**
- Execute multiple additional Tier-1 CPs
- Defer kernel work further

**Pros:**
- Avoids gate-opening complexity
- Maintains current development patterns

**Cons:**
- Diminishing returns
- Technical debt increases
- High-value mechanics remain blocked
- Opportunity cost grows

**Risk Level:** Medium (increasing over time)

---

## 8. DECISION CRITERIA FRAMEWORK

The following criteria may guide the decision:

### Favor Option A (Immediate Pivot) If:
- Project priority is feature breadth
- SKR-005 design confidence is high
- Degraded mechanic friction is observable
- Gate-opening authorization is readily available

### Favor Option B (Small CP-21 First) If:
- A clean milestone is valued
- SKR-005 preparation needs additional time
- Team bandwidth is constrained

### Favor Option C (Continue Tier-1) If:
- Gate-opening is not authorized
- Specific Tier-1 mechanics are explicitly requested
- Kernel work is explicitly deferred

---

## 9. QUESTIONS FOR PROJECT AUTHORITY

The following questions, if answered, would resolve the decision:

1. Is there explicit demand for any remaining G-T1 mechanics?
2. Is the project prepared to authorize opening G-T3C?
3. Are the current DEGRADED mechanics causing observable friction?
4. Is there a timeline constraint that favors one option?

---

## 10. CONCLUSION

This analysis finds that:

- **Tier-1 is effectively complete** after CP-20
- **SKR-005 is the next high-value target**
- **Continuing Tier-1 beyond one small CP provides diminishing returns**

The decision between Options A and B is primarily one of pacing and milestone
preference. Option C is not recommended unless external constraints apply.

This document does not authorize any action. It provides analysis only.

---

## END OF POST-CP-20 DECISION ANALYSIS
