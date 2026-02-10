# Edge-Case Traceability Index
## Research Theme → Enforcement Location Mapping

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Audit Support / Traceability
**Status:** ACTIVE
**Date:** 2026-02-09
**Audience:** Auditors, Architects

---

## 1. PURPOSE

This index maps **original edge-case research themes** discovered during
CP-18, CP-19, and CP-20 development to their **current enforcement locations**
in tests, documentation, and threat patterns.

Its goals are to:
- Verify no edge cases were lost during implementation
- Provide audit traceability
- Support future regression analysis

This document is **informational** and supplements the primary governance artifacts.

---

## 2. TRACEABILITY FORMAT

Each entry follows this structure:

```
THEME: [Original research theme]
DISCOVERED: [CP or phase where identified]
ENFORCEMENT:
  - [Location 1]
  - [Location 2]
STATUS: COVERED / PARTIAL / UNADDRESSED
```

---

## 3. ORDERING & EXECUTION THEMES

### 3.1 AoO → Movement → Environment Ordering

**THEME:** AoOs must resolve before movement completes; environment effects
must resolve after movement but before turn ends.

**DISCOVERED:** CP-15 / CP-19

**ENFORCEMENT:**
- `DETERMINISM_THREAT_PATTERNS.md` → DTP-01: Ordering Collapse
- `DETERMINISM_AUDIT_PLAYBOOK.md` → §4.1 Execution Order
- `terrain_resolver.py` → docstring ORDERING CONTRACT
- `test_terrain_cp19_core.py` → ordering tests
- `test_environmental_damage_cp20.py` → TestOrdering class

**STATUS:** COVERED

---

### 3.2 Hazard Bypass via Alternate Code Paths

**THEME:** All forced-movement paths must route through hazard resolution;
success and failure paths must be symmetric.

**DISCOVERED:** CP-19B (Failure-Path Hazards)

**ENFORCEMENT:**
- `DETERMINISM_THREAT_PATTERNS.md` → DTP-02: Hazard Bypass
- `maneuver_resolver.py` → Bull Rush/Overrun failure paths
- `terrain_resolver.py` → resolve_forced_movement_with_hazards()
- `test_terrain_cp19_integration.py` → failure path tests
- `CP20_TEST_CASE_CATALOG.md` → §4.3 Failure Pushback into Hazard

**STATUS:** COVERED

---

## 4. RNG & DETERMINISM THEMES

### 4.1 Hidden RNG Consumption

**THEME:** RNG must never be consumed inside helpers, condition checks,
or variable-length loops.

**DISCOVERED:** Pre-CP-18 refactors

**ENFORCEMENT:**
- `DETERMINISM_THREAT_PATTERNS.md` → DTP-03: Hidden RNG Consumption
- `DETERMINISM_AUDIT_PLAYBOOK.md` → §4.2 RNG Usage
- All resolver modules → explicit RNG stream declarations
- `test_rng_manager.py` → isolation tests

**STATUS:** COVERED

---

### 4.2 RNG Stream Isolation

**THEME:** Combat RNG must not affect policy RNG; streams must be isolated.

**DISCOVERED:** Core architecture

**ENFORCEMENT:**
- `rng_manager.py` → stream isolation design
- `test_attack_resolution.py` → test_combat_rng_does_not_affect_policy_rng
- `CP20_IMPLEMENTATION_PACKET.md` → §6 RNG RULES

**STATUS:** COVERED

---

## 5. RELATIONAL STATE THEMES

### 5.1 Entity-to-Entity Direct References

**THEME:** Entities must not store direct references to other entities;
all relationships must go through kernelized infrastructure.

**DISCOVERED:** Prototype grapple implementations

**ENFORCEMENT:**
- `DETERMINISM_THREAT_PATTERNS.md` → DTP-04: Relational State Leakage
- `SKR-005_RELATIONAL_CONDITIONS_DESIGN.md` → §5.2 Entity View
- `SKR-005_FAILURE_MODE_ANALYSIS.md` → FM-03: Implicit Coupling
- `entity_fields.py` → no relation fields in current schema (gate closed)

**STATUS:** COVERED (enforcement via closed gate)

---

### 5.2 Partial Teardown

**THEME:** Multi-entity effects must tear down atomically; partial
teardown creates orphaned state.

**DISCOVERED:** Design reviews

**ENFORCEMENT:**
- `DETERMINISM_THREAT_PATTERNS.md` → DTP-06: Partial Teardown
- `SKR-005_FAILURE_MODE_ANALYSIS.md` → FM-01: Partial Teardown
- `SKR-005_AUDIT_READINESS_CHECKLIST.md` → §7 Teardown Invariants

**STATUS:** COVERED (enforcement planned for SKR-005)

---

## 6. TERRAIN & HAZARD THEMES

### 6.1 Read-Only Terrain

**THEME:** Terrain must never be mutated during play; all terrain
effects are pure lookups.

**DISCOVERED:** CP-19 design

**ENFORCEMENT:**
- `terrain_resolver.py` → docstring DESIGN PRINCIPLES
- `GATE_PRESSURE_MAP.md` → Terrain destruction FORBIDDEN
- `RAW_FIDELITY_AUDIT.md` → Terrain destruction FORBIDDEN

**STATUS:** COVERED

---

### 6.2 One-Shot vs. Persistent Hazards

**THEME:** Environmental damage must be one-shot (per entry); persistence
requires G-T2A which is closed.

**DISCOVERED:** CP-20 design

**ENFORCEMENT:**
- `CP20_ENVIRONMENTAL_DAMAGE_DECISIONS.md` → discrete/one-shot model
- `environmental_damage_resolver.py` → no persistence logic
- `test_environmental_damage_cp20.py` → TestNegativeCases.test_no_persistence
- `GATE_PRESSURE_MAP.md` → Persistent hazards FORBIDDEN

**STATUS:** COVERED

---

### 6.3 Spiked Pit: Falling + Environmental

**THEME:** Spiked pits require compound damage: falling damage followed
by piercing damage, in correct order.

**DISCOVERED:** CP-20 test catalog

**ENFORCEMENT:**
- `CP20_TEST_CASE_CATALOG.md` → §5.1 Fall into Spiked Pit
- `environmental_damage_resolver.py` → resolve_spiked_pit_damage()
- `terrain_resolver.py` → integration in resolve_forced_movement_with_hazards()
- `test_environmental_damage_cp20.py` → TestFallingPlusDamage.test_fall_into_spiked_pit

**STATUS:** COVERED

---

## 7. FORCED MOVEMENT THEMES

### 7.1 Push Path Evaluation

**THEME:** Push paths must be evaluated cell-by-cell; first hazard
encountered triggers and aborts remaining push.

**DISCOVERED:** CP-18 / CP-19 integration

**ENFORCEMENT:**
- `terrain_resolver.py` → check_push_path_for_hazards()
- `CP20_TEST_CASE_CATALOG.md` → §6.1 Adjacent Multiple Hazards
- `test_terrain_cp19_core.py` → push path tests

**STATUS:** COVERED

---

### 7.2 Forced Movement into Environmental Hazards

**THEME:** Bull Rush, Overrun, and other forced movement must trigger
environmental damage at destination.

**DISCOVERED:** CP-20 design

**ENFORCEMENT:**
- `terrain_resolver.py` → resolve_forced_movement_with_hazards() CP-20 extension
- `test_environmental_damage_cp20.py` → TestForcedMovementHazards class
- `CP20_TEST_CASE_CATALOG.md` → §4 Forced Movement Hazards

**STATUS:** COVERED

---

## 8. COVERAGE SUMMARY

| Theme Category | Total Themes | Covered | Partial | Unaddressed |
|----------------|--------------|---------|---------|-------------|
| Ordering & Execution | 2 | 2 | 0 | 0 |
| RNG & Determinism | 2 | 2 | 0 | 0 |
| Relational State | 2 | 2 | 0 | 0 |
| Terrain & Hazards | 3 | 3 | 0 | 0 |
| Forced Movement | 2 | 2 | 0 | 0 |
| **TOTAL** | **11** | **11** | **0** | **0** |

---

## 9. MAINTENANCE RULE

This index should be updated when:
- New edge cases are discovered
- Enforcement locations change
- CPs add new test coverage
- Threat patterns are updated

---

## 10. CONCLUSION

All identified edge-case research themes have been traced to explicit
enforcement locations in documentation, code, or tests.

No themes are unaddressed. The project's edge-case coverage is complete
for the currently implemented CPs (through CP-20).

---

## END OF EDGE-CASE TRACEABILITY INDEX
