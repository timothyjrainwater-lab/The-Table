# CP-19B — Failure-Path Hazard Resolution
## Corrective Instruction Packet for Implementing Agent ("Clog")

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Packet ID:** CP-19B
**Type:** Corrective Patch (Post-Implementation)
**Status:** AUTHORIZED UPON RECEIPT
**Applies To:** CP-19 (Environment & Terrain)
**Audience:** Implementing Agent (Clog)

---

## 1. PURPOSE (READ FIRST)

This packet authorizes and specifies a **minimal corrective patch** to CP-19
to address **forced-movement failure paths that bypass hazard resolution**.

The intent is to:

- Restore semantic consistency between **success and failure** forced movement
- Ensure pits and ledges trigger falling **regardless of maneuver outcome**
- Preserve determinism, ordering, and gate safety
- Freeze CP-19 only after this correction is applied and verified

This packet **does not expand CP-19 scope**.

---

## 2. PROBLEM STATEMENT (AUTHORITATIVE)

### Identified Critical Gap

In CP-19, forced movement **success paths** correctly route through:

```
resolve_forced_movement_with_hazards()
```

However, two **failure paths bypass hazard checks entirely**:

| Maneuver | File | Approx. Lines | Current Behavior |
|--------|------|---------------|------------------|
| Bull Rush (failure) | `maneuver_resolver.py` | ~367–426 | Attacker pushed back 5 ft, no hazard check |
| Overrun (failure) | `maneuver_resolver.py` | ~852–924 | Attacker pushed back 5 ft, no hazard check |

**Impact:**
If a pit or ledge exists behind the attacker, the entity is moved into it
without triggering falling damage or hazard events.

This violates:
- CP-19 forced-movement semantics
- DMG expectations
- Internal invariants already used by success paths

---

## 3. AUTHORITY

This packet is **self-authorizing** once issued.

No additional approval is required **provided all changes remain within scope**.

Any deviation requires escalation.

---

## 4. SCOPE (STRICT)

### 4.1 In Scope

- Route **failure-path pushback movement** through the existing hazard resolver
- Apply to:
  - Bull Rush failure pushback
  - Overrun failure pushback
- Add **two targeted tests** validating hazard triggering
- Update CP-19 acceptance artifacts after verification

### 4.2 Explicitly Out of Scope

- No new mechanics
- No new terrain types
- No refactors
- No geometry changes
- No RNG changes
- No new schemas or event types

---

## 5. FILE TOUCH BOUNDARY (HARD)

### Files You MAY Modify

- `aidm/core/maneuver_resolver.py`
- `tests/test_terrain_cp19_core.py`
- `tests/test_terrain_cp19_integration.py`
- CP-19 documentation status markers

### Files You MUST NOT Touch

- `play_loop.py`
- `terrain_resolver.py`
- Any schema files
- Any unrelated resolvers

Touching any other file **requires escalation**.

---

## 6. REQUIRED CODE CHANGE (EXACT)

### Current (Incorrect) Pattern

```python
# Failure branch
new_pos = push_back(attacker, 5)
apply_position_update(new_pos)
# END — no hazard resolution
```

### Required (Correct) Pattern

```python
resolve_forced_movement_with_hazards(
    entity_id=attacker_id,
    origin_pos=current_pos,
    direction=reverse_push_direction,
    distance=5,
    context="bull_rush_failure" | "overrun_failure"
)
```

**Invariant:**

> ALL forced movement — success OR failure — MUST pass through the same
> hazard-aware resolution path.

---

## 7. ORDERING & DETERMINISM CONSTRAINTS

You MUST preserve the following order:

1. AoOs (already resolved)
2. Maneuver outcome determination
3. Forced movement evaluation
4. Hazard resolution (pit / ledge)
5. Falling damage (if applicable)

Rules:

* No mid-movement interrupts
* No new RNG usage
* Falling damage uses existing `"combat"` stream only

---

## 8. TESTING REQUIREMENTS

### 8.1 New Required Tests

You must add **at least two tests**:

#### Test 1 — Bull Rush Failure Into Pit

* Attacker fails Bull Rush
* Pit exists behind attacker
* Expected:

  * `fall_triggered`
  * `falling_damage`
  * Attacker ends at pit bottom

#### Test 2 — Overrun Failure Into Ledge

* Attacker fails Overrun by ≥5
* Ledge exists behind attacker
* Expected:

  * Forced movement off ledge
  * Falling damage applied

### 8.2 Regression Requirements

* All existing tests must still pass
* Total runtime remains < 2 seconds
* 10× deterministic replay remains stable

---

## 9. ACCEPTANCE CRITERIA

This packet is complete when:

* [ ] Both failure paths route through hazard resolver
* [ ] Falling damage triggers correctly on failure pushback
* [ ] No new RNG streams introduced
* [ ] No unauthorized file touches
* [ ] All tests pass
* [ ] CP-19 documents marked FINAL

---

## 10. ESCALATION CONDITIONS (STOP)

Stop and escalate if:

* Hazard resolution requires geometry changes
* A third forced-movement bypass is discovered
* Fix appears to require touching `play_loop.py`
* Any capability gate boundary becomes unclear

---

## 11. FINAL FREEZE DIRECTIVE

Once this packet is implemented and verified:

* CP-19 is **FINAL and FROZEN**
* No further CP-19 changes permitted without a new packet
* Project may advance to CP-20 or kernel work

---

## END OF CP-19B INSTRUCTION PACKET
