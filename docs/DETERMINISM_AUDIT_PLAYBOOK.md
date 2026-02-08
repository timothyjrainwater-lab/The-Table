# Determinism Audit Playbook
## Standard Review Protocol for AIDM Development

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Audit Playbook
**Status:** ACTIVE
**Audience:** Auditors, Implementers, Project Authority

---

## 1. PURPOSE

This playbook defines the **standard determinism audit process** for all
Capability Packets (CPs), kernels (SKRs), and refactors.

Its goals are to:
- Detect determinism risks early
- Standardize audit expectations
- Reduce subjective judgment during reviews
- Prevent replay drift and hidden coupling

This document is **procedural and binding**.

---

## 2. WHEN AN AUDIT IS REQUIRED

A determinism audit is **mandatory** when any of the following occur:

- New CP implementation
- Modification of execution order
- Introduction of RNG usage
- Forced movement logic
- Multi-entity interaction
- Kernel design or implementation
- Refactors touching ≥2 subsystems

If unsure, **audit anyway**.

---

## 3. CORE DETERMINISM INVARIANTS

All approved mechanics MUST satisfy:

1. **Single authoritative execution order**
2. **Explicit event emission**
3. **No hidden RNG consumption**
4. **Replay-safe state transitions**
5. **Symmetric teardown paths**
6. **No implicit cross-entity coupling**

Violation of any invariant is a **hard failure**.

---

## 4. AUDIT CHECKLIST (MANDATORY)

### 4.1 Execution Order

- [ ] Is the execution order explicitly defined?
- [ ] Is it global (not conditional)?
- [ ] Is it documented?
- [ ] Are all branches following the same order?

**Red Flags**
- Order depends on outcome
- Order varies by entity type
- Environment resolves mid-movement

---

### 4.2 RNG Usage

- [ ] Is RNG used at all?
- [ ] Are all RNG calls explicit?
- [ ] Is the RNG stream named?
- [ ] Is RNG consumption order fixed?

**Red Flags**
- RNG inside helpers
- RNG inside condition checks
- RNG inside loops with variable length

---

### 4.3 State Mutation

- [ ] Are all state changes event-driven?
- [ ] Is state mutation localized?
- [ ] Is teardown explicit?

**Red Flags**
- State mutated without event
- Partial teardown paths
- Implicit persistence

---

### 4.4 Branch Symmetry

- [ ] Do success and failure paths behave symmetrically?
- [ ] Do alternate code paths reuse core resolvers?

**Red Flags**
- One branch bypasses shared logic
- Early returns skipping cleanup
- Duplicate logic with slight variation

---

### 4.5 Cross-Entity Effects

- [ ] Are multiple entities involved?
- [ ] Is relational state avoided or kernelized?

**Red Flags**
- Entity A storing Entity B directly
- Implicit participant lists
- Untracked shared state

---

## 5. REQUIRED TESTING EVIDENCE

An audit is **not complete** without:

- Passing full test suite
- Determinism replay test (minimum 10×)
- Explicit edge-case tests for:
  - Forced movement
  - Failure paths
  - Boundary conditions

---

## 6. COMMON FAILURE MODES (REFERENCE)

| Pattern | Description | Example |
|------|------------|--------|
| Ordering collapse | Mixed resolution order | AoO after fall |
| Hazard bypass | Alternate path skips resolver | CP-19 failure gap |
| RNG drift | Variable RNG consumption | Loop-based rolls |
| Partial teardown | Only one side cleared | Grapple exit |
| Hidden persistence | State remembered implicitly | Terrain damage |

---

## 7. ESCALATION STANDARD

If a violation or uncertainty is detected:

```
ARCHITECTURAL / DETERMINISM CONCERN:
Context:
Observed Pattern:
Violated Invariant:
Relevant Code / Doc:
Proposed Questions:
AWAITING DIRECTION.
```

Do **not** proceed until resolved.

---

## 8. AUDIT OUTCOMES

An audit results in one of:

- **PASS** — No issues
- **PASS WITH CONDITIONS** — Minor, documented follow-ups
- **FAIL** — Must fix before proceeding

Only **PASS** or **PASS WITH CONDITIONS** may advance.

---

## 9. MAINTENANCE RULE

This playbook is **living**:
- Update when new threat patterns are discovered
- Reference fixing CPs when issues are resolved
- Never delete historical failures

---

## 10. CONCLUSION

Determinism is not accidental — it is enforced.
This playbook ensures enforcement is **repeatable, explicit, and objective**.

---

## END OF DETERMINISM AUDIT PLAYBOOK
