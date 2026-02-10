# EXECUTION INSTRUCTION PACKET — CLAW

## CP-19 Closure → CP-20 Execution → SKR-005 Readiness

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Prepared For:** Claw (Implementing Agent)
**Prepared By:** Acting Project Authority
**Effective Upon Receipt**

---

## 0. EXECUTIVE DIRECTIVE (READ FIRST)

You are authorized to execute **three sequential phases**:

1. **CP-19B corrective patch** (mandatory, blocking)
2. **Formal CP-19 freeze** (mandatory)
3. **CP-20 implementation** (authorized after freeze)

In parallel (design/audit only):

* Advance **SKR-005 (Relational Conditions Kernel)** through readiness review
* **Do NOT implement SKR-005**

Any deviation from this packet requires escalation.

---

## 1. CURRENT PROJECT STATE (AUTHORITATIVE)

* CP-19 implementation: **Complete**
* CP-19 documentation: **Finalized**
* CP-19 acceptance: **Conditional (CP-19B pending)**
* CP-20: **Design complete, implementation authorized after CP-19 freeze**
* Capability gates:

  * **G-T1:** Open
  * **G-T3C:** Closed (SKR-005 design only)

---

## 2. PHASE 1 — CP-19B CORRECTIVE PATCH (BLOCKING)

### 2.1 Objective

Eliminate the **forced-movement failure-path hazard bypass** so that:

> **ALL forced movement (success or failure) resolves hazards identically**

This is a correctness fix, not a feature.

---

### 2.2 Scope (STRICT)

**In scope**

* Bull Rush failure pushback
* Overrun failure pushback
* Routing through existing hazard resolver
* Two new tests

**Out of scope**

* Any new mechanics
* Geometry changes
* RNG changes
* Refactors
* Any file not explicitly listed

---

### 2.3 Files You MAY Touch

* `aidm/core/maneuver_resolver.py`
* `tests/test_terrain_cp19_core.py`
* `tests/test_terrain_cp19_integration.py`

Touching any other file → **STOP AND ESCALATE**

---

### 2.4 Required Change (Invariant)

**Forbidden pattern**

```python
apply_position_update(new_pos)
```

**Required pattern**

```python
resolve_forced_movement_with_hazards(
    entity_id=attacker_id,
    origin_pos=current_pos,
    direction=reverse_push_direction,
    distance=5,
    context="bull_rush_failure" | "overrun_failure"
)
```

---

### 2.5 Tests (MANDATORY)

Add **at least**:

1. **Bull Rush failure → pit**

   * Attacker fails
   * Pit behind attacker
   * Expect falling damage

2. **Overrun failure → ledge**

   * Failure by ≥5
   * Ledge behind attacker
   * Expect fall + damage

---

### 2.6 Exit Criteria (Phase 1)

* All tests passing
* Runtime < 2s
* 10× deterministic replay verified
* No new file touches

---

## 3. PHASE 2 — CP-19 FREEZE (IMMEDIATE AFTER PHASE 1)

Once Phase 1 passes:

1. Update CP-19 acceptance status to **FINAL**
2. Declare CP-19 **FROZEN**
3. No further CP-19 changes permitted

This is a **hard governance boundary**.

---

## 4. PHASE 3 — CP-20 IMPLEMENTATION (AUTHORIZED)

### 4.1 Objective

Implement **discrete environmental damage hazards** that:

* Trigger once on entry/contact
* Do not persist
* Do not advance time
* Do not modify terrain

---

### 4.2 Scope (STRICT)

**In scope**

* Fire squares (1d6 fire)
* Acid pools (1d6 acid)
* Lava edges (2d6 fire)
* Spiked pits (fall + 1d6 piercing)
* Forced movement integration

**Explicitly forbidden**

* Ongoing damage
* Saving throws
* Terrain mutation
* New RNG streams
* Spell-created hazards

---

### 4.3 File Touch Boundary

**May create**

* `aidm/core/environmental_damage_resolver.py`
* `tests/test_environmental_damage_cp20.py`

**May modify**

* `aidm/core/terrain_resolver.py` (integration only)
* `aidm/core/maneuver_resolver.py` (integration only)

**Must not touch**

* `play_loop.py`
* Schemas
* Any unrelated systems

---

### 4.4 Ordering & Determinism

Non-negotiable order:

```
AoO → Movement → Hazard Detection → Environmental Damage
```

RNG:

* `"combat"` stream only
* Damage rolls only

---

### 4.5 Tests

Minimum coverage:

* Entry into fire square
* Forced movement into acid
* Falling into spiked pit
* Lava edge entry
* 10× deterministic replay

---

### 4.6 Exit Criteria (Phase 3)

* All tests passing
* Runtime < 2s
* No gate violations
* CP-20 marked COMPLETE

---

## 5. PARALLEL TRACK — SKR-005 (DESIGN / AUDIT ONLY)

### 5.1 What You MAY Do

* Review SKR-005 design for:

  * Determinism invariants
  * Teardown rules
  * Event model completeness
* Identify risks or ambiguities
* Propose clarifying questions

### 5.2 What You MUST NOT Do

* Implement SKR-005
* Modify runtime code
* Open G-T3C
* "Sneak in" relational state elsewhere

Any temptation to implement → **STOP**

---

## 6. ESCALATION PROTOCOL (MANDATORY)

Escalate immediately if:

* A fix appears to require new file touches
* A feature pressures a closed gate
* Ordering becomes ambiguous
* A mechanic appears to persist across turns

Use this format:

```
ARCHITECTURAL / GATE CONCERN:
Context:
Suspected Issue:
Blocking Gate:
Relevant Document:
Proposed Clarification Questions:
AWAITING DIRECTION.
```

---

## 7. SUCCESS CONDITIONS (HOW YOU KNOW YOU'VE SUCCEEDED)

You have succeeded if:

* CP-19 is frozen with no open gaps
* CP-20 is implemented cleanly under G-T1
* No determinism regressions occur
* SKR-005 remains design-only
* No unauthorized file touches exist

---

## 8. FINAL NOTE TO CLAW

This project prioritizes:

* **Correctness over speed**
* **Explicit decisions over convenience**
* **Governance over momentum**

If something feels "obvious" but undocumented — **stop and ask**.

---

## END OF INSTRUCTION PACKET
