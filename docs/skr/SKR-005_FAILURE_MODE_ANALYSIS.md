# SKR-005 — Relational Conditions Kernel
## Failure Mode Analysis & Mitigation Mapping

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Kernel:** SKR-005 (Relational Conditions)
**Document Type:** Architecture Risk Analysis
**Status:** DESIGN SUPPORT (NO IMPLEMENTATION)
**Audience:** Architects, Auditors, Project Authority

---

## 1. PURPOSE

This document enumerates **known failure modes** common to relational-condition
systems and maps each to **explicit mitigations** already proposed (or required)
by the SKR-005 design.

Its goal is to:
- Reduce the risk of a failed gate opening
- Make audit expectations explicit
- Prevent partial or unsafe implementations

---

## 2. CONTEXT

Relational mechanics introduce **bidirectional or multi-entity coupling**.
Without disciplined structure, they are a primary source of:
- Determinism failure
- Orphaned state
- Replay divergence
- Non-local side effects

SKR-005 exists to control this risk.

---

## 3. FAILURE MODE CATALOG

### FM-01: Partial Teardown

**Description**
One participant exits a relation while the other remains affected.

**Example**
Grapple ends for attacker but defender remains "grappled".

**Impact**
- Broken invariants
- Stuck or phantom conditions

**Mitigation**
- Atomic teardown: relation removal clears all derived effects
- No per-entity teardown logic allowed

---

### FM-02: Orphaned Relations

**Description**
A relation record remains after all participants are invalid.

**Example**
Relation persists after one entity is defeated or removed.

**Impact**
- Memory leaks
- Replay mismatch

**Mitigation**
- Automatic teardown on entity removal
- Central registry validates participants every tick

---

### FM-03: Implicit Coupling via Entity Fields

**Description**
Entities store references to each other directly.

**Example**
`entity["grappled_by"] = other_id`

**Impact**
- Hidden relational state
- Bypasses kernel guarantees

**Mitigation**
- Entities store only relation IDs
- All participant resolution occurs via kernel lookup

---

### FM-04: Asymmetric State Transitions

**Description**
State changes applied to one participant earlier than others.

**Example**
Attacker becomes "free" before defender.

**Impact**
- Non-deterministic outcomes
- Order-sensitive bugs

**Mitigation**
- Single relation state machine
- State transitions applied centrally

---

### FM-05: Implicit Propagation

**Description**
Side effects propagate without explicit events.

**Example**
Condition modifiers applied automatically when relation changes.

**Impact**
- Hidden logic paths
- Audit blind spots

**Mitigation**
- Event-driven propagation only
- No direct writes during relation updates

---

### FM-06: Relation Identity Drift

**Description**
Relation IDs depend on creation order or memory address.

**Example**
UUID generated nondeterministically.

**Impact**
- Replay divergence

**Mitigation**
- Deterministic relation ID generation
- Sorted participant list hashing

---

### FM-07: Nested Relations

**Description**
One relation depends on another relation.

**Example**
Aid Another nested inside Grapple.

**Impact**
- Exponential complexity
- Teardown ambiguity

**Mitigation**
- Flat relation model
- No relation-to-relation dependencies

---

## 4. MITIGATION COVERAGE MATRIX

| Failure Mode | Covered by SKR-005? |
|------------|---------------------|
| FM-01 Partial Teardown | ✅ |
| FM-02 Orphaned Relations | ✅ |
| FM-03 Implicit Coupling | ✅ |
| FM-04 Asymmetry | ✅ |
| FM-05 Implicit Propagation | ✅ |
| FM-06 Identity Drift | ✅ |
| FM-07 Nested Relations | ✅ (forbidden) |

---

## 5. AUDIT CHECKPOINTS (REQUIRED)

Before opening **G-T3C**, auditors must confirm:

- All mitigations above are explicitly implemented
- No relational state exists outside kernel
- Determinism tests include relation creation/removal
- Failure teardown paths are symmetric

---

## 6. CONCLUSION

Relational mechanics are **high-risk but high-value**.
This analysis demonstrates that SKR-005, if implemented as designed,
can safely control those risks.

Deviation from these mitigations is not acceptable.

---

## END OF SKR-005 FAILURE MODE ANALYSIS
