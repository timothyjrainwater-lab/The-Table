# CP Completion Review Template
## Standard Close-Out Verification Checklist

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Process Template (REUSABLE)
**Status:** ACTIVE
**Date:** 2026-02-09
**Audience:** Implementers, Auditors, Project Authority

---

## 1. PURPOSE

This template provides a **standard, reusable checklist** for verifying that
a Capability Packet (CP) is ready for closure.

It prevents:
- Functionally complete but procedurally ambiguous CPs
- Missing documentation updates
- Silent gate violations
- Unverified determinism claims

This template is **mandatory** for all CP closures.

---

## 2. TEMPLATE USAGE

### How to Use

1. Copy this template to a new file: `docs/cpXX/CPXX_COMPLETION_REVIEW.md`
2. Replace `[CP-XX]` with actual CP identifier
3. Complete all sections
4. Obtain required sign-offs
5. Archive with CP documentation

### Verification Levels

| Symbol | Meaning |
|--------|---------|
| [ ] | Not verified |
| [P] | Partially verified (documented exception) |
| [X] | Fully verified |

### Completion Requirement

- All items must be **[X]** for closure
- **[P]** items require explicit exception documentation
- **[ ]** items block closure

---

## 3. CP IDENTIFICATION

### 3.1 Basic Information

| Field | Value |
|-------|-------|
| CP Identifier | [CP-XX] |
| CP Title | [Title] |
| Implementation Date | [YYYY-MM-DD] |
| Implementing Agent | [Agent ID or Name] |
| Reviewer | [Reviewer ID or Name] |

### 3.2 Dependencies

| Dependency | Status |
|------------|--------|
| [Required CP] | COMPLETE / IN-PROGRESS |
| [Required CP] | COMPLETE / IN-PROGRESS |

---

## 4. FUNCTIONAL COMPLETENESS

### 4.1 Scope Verification

- [ ] All in-scope items from Implementation Packet are implemented
- [ ] All out-of-scope items remain unimplemented
- [ ] No undocumented features were added

### 4.2 Feature Checklist

| Feature | Status | Notes |
|---------|--------|-------|
| [Feature 1] | [X] / [ ] | |
| [Feature 2] | [X] / [ ] | |
| [Feature 3] | [X] / [ ] | |

### 4.3 Edge Cases

- [ ] All edge cases from Test Case Catalog are covered
- [ ] No known edge cases remain untested
- [ ] Edge case handling matches design specification

---

## 5. DETERMINISM VERIFICATION

### 5.1 Core Invariants

- [ ] Single authoritative execution order verified
- [ ] Explicit event emission for all state changes
- [ ] No hidden RNG consumption
- [ ] Replay-safe state transitions
- [ ] Symmetric teardown paths (if applicable)
- [ ] No implicit cross-entity coupling

### 5.2 Replay Testing

| Test | Result |
|------|--------|
| 10× replay with same seed | IDENTICAL / DIVERGED |
| State hash comparison | MATCH / MISMATCH |
| Event sequence comparison | IDENTICAL / DIFFERENT |

### 5.3 RNG Audit

- [ ] All RNG usage declared in Implementation Packet
- [ ] RNG stream(s) identified: [stream name(s)]
- [ ] RNG consumption order is fixed
- [ ] No RNG inside conditionals with variable paths

---

## 6. GATE COMPLIANCE

### 6.1 Gate Declaration

| Gate | Required? | Status |
|------|-----------|--------|
| G-T1 | YES / NO | OPEN / CLOSED |
| G-T2A | YES / NO | OPEN / CLOSED |
| G-T3A | YES / NO | OPEN / CLOSED |
| G-T3C | YES / NO | OPEN / CLOSED |
| G-T3D | YES / NO | OPEN / CLOSED |

### 6.2 Gate Verification

- [ ] Implementation uses only authorized gates
- [ ] No implicit gate pressure introduced
- [ ] No mechanics requiring closed gates
- [ ] GATE_PRESSURE_MAP.md updated if needed

### 6.3 Gate Violation Check

- [ ] No entity creation without G-T3A
- [ ] No relational state without G-T3C
- [ ] No persistence/history without G-T3D
- [ ] No stat mutation without G-T2A

---

## 7. RUNTIME VERIFICATION

### 7.1 Test Suite

| Metric | Value | Threshold |
|--------|-------|-----------|
| Total tests | [N] | N/A |
| Tests passing | [N] | 100% |
| Tests failing | [N] | 0 |
| Test runtime | [X.XX]s | <2s |

### 7.2 Test Categories

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Determinism tests pass
- [ ] Edge case tests pass
- [ ] Regression tests pass (existing tests unbroken)

### 7.3 Performance

- [ ] Runtime within threshold (<2s)
- [ ] No performance regression from baseline
- [ ] No memory leaks or unbounded growth

---

## 8. DOCUMENTATION UPDATES

### 8.1 Required Updates

- [ ] RULES_COVERAGE_LEDGER.md updated
  - [ ] New FULL entries added
  - [ ] DEFERRED entries moved to appropriate status
- [ ] GATE_PRESSURE_MAP.md updated (if gates affected)
- [ ] RAW_FIDELITY_AUDIT.md updated (if rules coverage changed)
- [ ] DOCUMENTATION_AUTHORITY_INDEX.md updated (if new docs created)

### 8.2 CP-Specific Documentation

- [ ] Implementation Packet exists and is accurate
- [ ] Test Case Catalog exists and is complete
- [ ] Design Decisions document exists (if required)
- [ ] Acceptance Record created (this document)

### 8.3 Code Documentation

- [ ] Module docstrings updated
- [ ] Function docstrings accurate
- [ ] RNG stream documented in module header
- [ ] Ordering contract documented

---

## 9. FREEZE DECLARATION

### 9.1 Freeze Status

- [ ] CP is ready for FREEZE
- [ ] No pending implementation work
- [ ] No pending documentation work
- [ ] No open escalations

### 9.2 Freeze Statement

> CP-[XX] is hereby declared **COMPLETE and FROZEN** as of [YYYY-MM-DD].
>
> All scope items are implemented. All tests pass. All documentation is current.
> No gate violations exist. Determinism is verified.
>
> This CP may not be modified without explicit authorization.

---

## 10. SIGN-OFF

### 10.1 Implementer Sign-Off

| Role | Name/ID | Date | Signature |
|------|---------|------|-----------|
| Implementer | | | [ ] Confirmed |

### 10.2 Reviewer Sign-Off

| Role | Name/ID | Date | Signature |
|------|---------|------|-----------|
| Reviewer | | | [ ] Confirmed |

### 10.3 Project Authority Acknowledgment

| Role | Name/ID | Date | Signature |
|------|---------|------|-----------|
| Project Authority | | | [ ] Acknowledged |

---

## 11. EXCEPTIONS AND NOTES

### 11.1 Documented Exceptions

| Item | Exception | Justification |
|------|-----------|---------------|
| | | |

### 11.2 Follow-Up Items

| Item | Owner | Target |
|------|-------|--------|
| | | |

### 11.3 Additional Notes

[Any additional notes or context]

---

## 12. CONCLUSION

This review confirms that CP-[XX] meets all requirements for closure.

Upon sign-off, the CP transitions to FROZEN status and becomes part of the
canonical project baseline.

---

## END OF CP COMPLETION REVIEW
