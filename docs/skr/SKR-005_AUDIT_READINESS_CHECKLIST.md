# SKR-005 — Audit Readiness Checklist
## Pre-Implementation Gate-Opening Verification

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Kernel:** SKR-005 (Relational Conditions)
**Document Type:** Audit Checklist (BINDING)
**Status:** ACTIVE
**Date:** 2026-02-09
**Audience:** Auditors, Project Authority, Future Implementers

---

## 1. PURPOSE

This checklist defines the **mandatory verification criteria** that must be
satisfied before opening capability gate G-T3C and authorizing SKR-005
implementation.

It is designed for use by:
- External auditors evaluating kernel readiness
- Project Authority making gate-opening decisions
- Implementing agents verifying prerequisites

This document is **binding**. All items must be verified before proceeding.

---

## 2. CHECKLIST USAGE

### Verification Levels

| Symbol | Meaning |
|--------|---------|
| [ ] | Not verified |
| [P] | Partially verified (requires follow-up) |
| [X] | Fully verified |

### Completion Requirement

- **All items must be [X]** before gate opening is authorized
- **[P] items require documented remediation plan**
- **[ ] items block authorization**

---

## 3. DESIGN COMPLETENESS

### 3.1 Core Design Documents

- [ ] SKR-005_RELATIONAL_CONDITIONS_DESIGN.md exists and is canonical
- [ ] Design document covers all required sections:
  - [ ] Problem statement
  - [ ] Data model (RelationRecord, entity references)
  - [ ] Event model (creation, state change, removal)
  - [ ] Determinism invariants
  - [ ] Teardown rules
  - [ ] Gate enforcement rules
  - [ ] Non-goals (explicit exclusions)
  - [ ] Upgrade path (degraded → full)

### 3.2 Failure Mode Coverage

- [ ] SKR-005_FAILURE_MODE_ANALYSIS.md exists
- [ ] All known failure modes are cataloged:
  - [ ] FM-01: Partial teardown
  - [ ] FM-02: Orphaned relations
  - [ ] FM-03: Implicit coupling via entity fields
  - [ ] FM-04: Asymmetric state transitions
  - [ ] FM-05: Implicit propagation
  - [ ] FM-06: Relation identity drift
  - [ ] FM-07: Nested relations
- [ ] Each failure mode has explicit mitigation mapped to design

---

## 4. DETERMINISM REQUIREMENTS

### 4.1 Invariant Specification

- [ ] All core determinism invariants are documented:
  - [ ] Single authoritative execution order
  - [ ] Explicit event emission
  - [ ] No hidden RNG consumption
  - [ ] Replay-safe state transitions
  - [ ] Symmetric teardown paths
  - [ ] No implicit cross-entity coupling

### 4.2 Relation-Specific Invariants

- [ ] Relation creation order is explicitly defined
- [ ] Participant list sorting is deterministic
- [ ] Relation ID generation is deterministic (no UUIDs, no timestamps)
- [ ] No cascading updates outside event system
- [ ] All propagation is event-driven

### 4.3 Threat Pattern Awareness

- [ ] DETERMINISM_THREAT_PATTERNS.md includes:
  - [ ] DTP-04: Relational State Leakage
  - [ ] DTP-06: Partial Teardown
- [ ] Threat patterns reference SKR-005 mitigations

---

## 5. FAILURE-MODE COVERAGE EXPECTATIONS

### 5.1 Atomic Teardown

- [ ] Design specifies: relation removal clears ALL derived effects
- [ ] Design specifies: no per-entity teardown logic allowed
- [ ] Design specifies: entity defeat triggers automatic relation teardown

### 5.2 Orphan Prevention

- [ ] Design specifies: central registry validates participants
- [ ] Design specifies: invalid participant triggers relation removal
- [ ] Design specifies: no dangling relation references permitted

### 5.3 State Isolation

- [ ] Design specifies: entities store only relation IDs
- [ ] Design specifies: all participant resolution via kernel lookup
- [ ] Design specifies: no entity-to-entity direct references

---

## 6. REQUIRED TEST CATEGORIES

### 6.1 Relation Lifecycle Tests

- [ ] Relation creation produces correct events
- [ ] Relation state change produces correct events
- [ ] Relation removal produces correct events
- [ ] Derived effects applied after relation creation
- [ ] Derived effects removed after relation removal

### 6.2 Teardown Tests

- [ ] Entity defeat tears down all relations involving that entity
- [ ] Partial teardown is impossible (atomic or nothing)
- [ ] Symmetric teardown: both participants cleared equally
- [ ] Orphan detection: relation with invalid participant is removed

### 6.3 Determinism Tests

- [ ] 10× replay produces identical relation state
- [ ] Relation creation order is reproducible
- [ ] Relation ID generation is reproducible
- [ ] No RNG used in relation management (unless explicitly declared)

### 6.4 Edge Case Tests

- [ ] Multiple relations on same entity
- [ ] Relation involving 3+ participants (if supported)
- [ ] Nested relation attempt rejected (if forbidden)
- [ ] Rapid creation/removal cycles maintain consistency

---

## 7. REQUIRED TEARDOWN INVARIANTS

### 7.1 Teardown Completeness

- [ ] No derived condition persists after relation removal
- [ ] No event references removed relation
- [ ] Entity state reflects removal immediately

### 7.2 Teardown Symmetry

- [ ] If A grapples B, ending grapple clears both A and B
- [ ] No asymmetric intermediate states
- [ ] Order of participant processing does not affect outcome

### 7.3 Cascade Prevention

- [ ] Teardown does not trigger other teardowns (flat model)
- [ ] No relation-to-relation dependencies
- [ ] If cascade is supported, it is explicit and auditable

---

## 8. EVIDENCE OF DEGRADED MECHANIC FRICTION

### 8.1 Documentation Evidence

- [ ] Rules Coverage Ledger shows DEGRADED entries awaiting G-T3C:
  - [ ] Grapple (DEGRADED, awaiting SKR-005)
  - [ ] Flanking (DEGRADED, awaiting SKR-005)
  - [ ] Mounted coupling (DEGRADED, awaiting SKR-005)
- [ ] Gate Pressure Map shows G-T3C as primary blocker

### 8.2 Functional Evidence

- [ ] Degraded grapple does not support true lockdown
- [ ] Degraded flanking does not verify positioning relationship
- [ ] Degraded mounted does not enforce rider-mount coupling
- [ ] Aid Another is completely unavailable

### 8.3 User-Facing Impact

- [ ] Tactical options are visibly limited
- [ ] Party coordination mechanics are absent
- [ ] Control combat is simplified beyond RAW

---

## 9. GATE-OPENING PREREQUISITES

### 9.1 Governance

- [ ] G-T3C is explicitly identified in gate documentation
- [ ] Gate opening requires Project Authority approval
- [ ] Gate opening conditions are documented

### 9.2 Prior Art

- [ ] CP-19 and CP-20 are COMPLETE and FROZEN
- [ ] No open escalations in current development
- [ ] All tests pass (<2s runtime)

### 9.3 Rollback Path

- [ ] Degraded mechanics remain functional as fallback
- [ ] SKR-005 implementation can be reverted without cascade
- [ ] No other systems depend on SKR-005 until verified

---

## 10. AUDITOR SIGN-OFF REQUIREMENTS

### 10.1 Pre-Implementation Audit

Before implementation begins:

- [ ] All design documents reviewed
- [ ] All failure modes acknowledged
- [ ] Test categories agreed upon
- [ ] Teardown invariants confirmed
- [ ] Gate-opening authorized

### 10.2 Post-Implementation Audit

After implementation completes:

- [ ] All test categories pass
- [ ] Determinism replay verified (10×)
- [ ] No orphaned relations in any test
- [ ] No asymmetric teardown observed
- [ ] Performance within bounds (<2s)
- [ ] Gate pressure reduced (DEGRADED → FULL)

---

## 11. ESCALATION TRIGGERS

Immediately escalate if:

- Any failure mode is not covered by design
- Determinism invariant violation observed
- Teardown asymmetry detected
- Implementation requires undocumented gate
- Nested relations become necessary

Use standard escalation template:

```
ARCHITECTURAL / GOVERNANCE CONCERN:
Context:
Observed Issue:
Impacted Gate or CP:
Relevant Documents:
Questions Requiring Direction:
AWAITING DIRECTION.
```

---

## 12. CONCLUSION

This checklist represents the **minimum verification bar** for opening G-T3C
and implementing SKR-005.

All items must be verified. Partial verification is insufficient.

This document should be used as the **literal audit instrument** when the
decision to proceed is made.

---

## END OF SKR-005 AUDIT READINESS CHECKLIST
