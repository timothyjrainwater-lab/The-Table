# SKR-005 — Relational Conditions Kernel
## Design Specification (DESIGN-ONLY, NO IMPLEMENTATION)

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Kernel ID:** SKR-005
**Status:** DESIGN COMPLETE (GATE-CONTROLLING)
**Date:** 2026-02-08
**Capability Gate:** G-T3C (Relational Conditions)
**Audience:** Architects, Auditors, Future Implementers

---

## 1. PURPOSE

SKR-005 defines the **Relational Conditions Kernel**, the foundational
infrastructure required to safely represent **bidirectional or multi-entity
conditions** (e.g., grappling, flanking, aid another).

This kernel is **purely architectural** and does **not** authorize
implementation of any mechanics that depend on it.

---

## 2. PROBLEM STATEMENT

Certain D&D mechanics create conditions where:

- Two or more entities are mutually dependent
- A state change in one entity must propagate to another
- Removal or alteration of the condition affects all participants

Examples:
- Grapple (attacker ↔ defender)
- Flanking (ally A + ally B ↔ target)
- Aid Another (helper ↔ beneficiary)
- Mounted rider–mount coupling (beyond degraded model)

Without a dedicated kernel, these mechanics create:
- Hidden relational state
- Non-deterministic propagation
- Replay instability

---

## 3. DESIGN GOALS

1. Explicit representation of relationships
2. Deterministic creation and teardown
3. No hidden references or circular state
4. Event-sourced propagation
5. Replay-safe invariants
6. Gate-enforced usage

---

## 4. CORE CONCEPTS

### 4.1 Relational Condition

A **Relational Condition** is a condition that:
- References ≥2 entities
- Has a single authoritative relationship record
- Applies derived effects to participants

Example:
```
GrappleRelation
  * participants: [attacker_id, defender_id]
  * state: "grappling"
```

---

## 5. DATA MODEL (CONCEPTUAL)

### 5.1 Relation Record

```python
@dataclass
class RelationRecord:
    relation_id: str
    relation_type: str
    participants: List[str]
    state: str
```

### 5.2 Entity View

Entities do **not** store relational state directly.
Instead, they store **references**:

```python
entity["relations"] = [relation_id, ...]
```

---

## 6. EVENT MODEL

### Required Events

| Event                    | Purpose                |
| ------------------------ | ---------------------- |
| `relation_created`       | Establish relationship |
| `relation_state_changed` | Update relation        |
| `relation_removed`       | Tear down relation     |

All derived condition effects are recalculated from relation state.

---

## 7. DETERMINISM INVARIANTS

* Relation creation order is explicit
* Participant list is sorted deterministically
* No implicit cascading updates
* All propagation is event-driven

---

## 8. FAILURE & TEARDOWN RULES

* Removing a relation removes all derived effects
* Entity defeat automatically tears down relations
* Partial teardown is forbidden

---

## 9. GATE ENFORCEMENT

### G-T3C (Relational Conditions)

This kernel is the **sole mechanism** allowed to represent:

* Bidirectional conditions
* Multi-entity mechanical dependencies

Any attempt to implement such mechanics **without SKR-005**
is a gate violation.

---

## 10. NON-GOALS

* No UI representation
* No AI reasoning
* No automatic upgrades of degraded mechanics
* No implicit relationship inference

---

## 11. UPGRADE PATH

Once implemented and verified:

* Full Grapple replaces Grapple-lite
* True flanking becomes available
* Aid Another becomes legal
* Mounted combat coupling may be upgraded

---

## 12. CONCLUSION

SKR-005 is a **critical architectural kernel** that unlocks a large
class of D&D mechanics while preserving determinism and auditability.

It must be implemented **only with explicit authorization and full audit**.

---

## END OF SKR-005 DESIGN SPEC
