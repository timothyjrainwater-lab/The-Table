# Determinism Threat Patterns
## Canonical Risk Catalog & Mitigation Guide

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Living Reference
**Status:** ACTIVE
**Last Updated:** 2026-02-08
**Audience:** Implementers, Auditors, Architects

---

## 1. PURPOSE

This document catalogs **recurring determinism threat patterns** discovered during
CP-18 and CP-19 implementation, along with **approved mitigations**.

Its purpose is to:
- Prevent regressions
- Shorten future review cycles
- Provide a shared vocabulary for escalation

---

## 2. CORE DETERMINISM INVARIANTS

All mechanics must satisfy:

1. **Single authoritative execution order**
2. **Explicit event emission**
3. **No hidden RNG consumption**
4. **Replay-safe state transitions**
5. **No implicit cross-entity coupling**

Violations of these invariants are considered **high-severity risks**.

---

## 3. THREAT PATTERN CATALOG

### DTP-01: Ordering Collapse

**Pattern:**
Interleaving AoOs, movement, and environment effects.

**Example:**
Applying falling damage mid-movement before AoOs resolve.

**Mitigation:**
Enforce strict ordering:
```
AoO → Movement → Environment
```

**Observed In:**
Early CP-19 drafts

---

### DTP-02: Hazard Bypass via Alternate Code Paths

**Pattern:**
Some forced-movement paths route through hazard resolution; others do not.

**Example:**
Bull Rush success resolves hazards; failure pushback does not.

**Mitigation:**
Single hazard-aware forced-movement entry point.

**Observed In:**
CP-19 failure paths (fixed by CP-19B)

---

### DTP-03: Hidden RNG Consumption

**Pattern:**
RNG used implicitly inside helpers or condition checks.

**Example:**
Rolling damage during movement cost evaluation.

**Mitigation:**
- Centralize RNG usage
- Declare RNG stream explicitly
- Audit helper functions

**Observed In:**
Pre-CP-18 refactors

---

### DTP-04: Relational State Leakage

**Pattern:**
Entities storing references to each other directly.

**Example:**
Attacker stores defender ID as part of condition state.

**Mitigation:**
Use relational kernels (e.g., SKR-005) only.

**Observed In:**
Prototype grapple implementations

---

### DTP-05: Implicit Persistence

**Pattern:**
State that "sticks around" without explicit lifecycle.

**Example:**
Terrain that remembers prior damage.

**Mitigation:**
- Read-only terrain
- Event-sourced effects only

**Observed In:**
Early hazard experiments

---

### DTP-06: Partial Teardown

**Pattern:**
Removing only part of a multi-entity effect.

**Example:**
Clearing grapple on one entity but not the other.

**Mitigation:**
Atomic teardown rules (all-or-nothing).

**Observed In:**
Design reviews (prevention only)

---

## 4. REVIEW CHECKLIST (MANDATORY)

Before approving a CP or kernel:

- [ ] All execution order is explicit
- [ ] All RNG usage is declared and isolated
- [ ] No alternate code paths bypass core resolvers
- [ ] No entity stores relational state directly
- [ ] All teardown paths are symmetric

---

## 5. ESCALATION GUIDANCE

Escalate immediately if:
- A new mechanic touches ≥2 entities
- A mechanic appears to "remember" prior turns
- RNG usage is hard to localize
- Execution order becomes conditional or dynamic

Use the standard architectural escalation template.

---

## 6. MAINTENANCE RULE

This document is **living**:
- New threat patterns must be added when discovered
- Resolved patterns should reference their fixing CP
- Do not delete historical entries

---

## 7. CONCLUSION

Determinism failures are **systemic, not local**.
Capturing patterns early prevents expensive rework later.

This document is a first-class governance artifact.

---

## END OF DETERMINISM THREAT PATTERNS
