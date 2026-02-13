# CP-19 — Environment & Terrain Decisions
## Feedback & Gap Analysis Report

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-19
**Report Type:** Post-Implementation Review
**Date:** 2026-02-08
**Status:** REVIEW COMPLETE

---

## 1. PURPOSE

This document records **post-implementation feedback**, identifies **gaps and
limitations**, and distinguishes between:

- **Critical correctness issues** (must be fixed)
- **Intentional degradations** (documented, acceptable)
- **Deferred improvements** (out of scope for CP-19)

This report is binding for CP-19 finalization.

---

## 2. SUMMARY ASSESSMENT

| Category | Assessment |
|--------|------------|
| Functional completeness | ✅ |
| Determinism | ✅ |
| Gate compliance | ✅ (G-T1 only) |
| Integration correctness | ✅ |
| Documentation clarity | ⚠️ Minor updates needed |
| Failure-path correctness | ⚠️ Critical gap identified |

---

## 3. CRITICAL GAPS (MUST ADDRESS)

### Gap ID: CP19-GAP-01
**Severity:** CRITICAL
**Status:** FIX REQUIRED

#### Description
Failure-path forced movement for **Bull Rush** and **Overrun** updates entity
position directly without invoking hazard resolution.

If a pit or ledge exists behind the attacker, the entity may enter it without
triggering falling damage or hazard events.

#### Affected Locations

| Maneuver | File | Approx. Lines |
|--------|------|---------------|
| Bull Rush failure | `aidm/core/maneuver_resolver.py` | ~367–426 |
| Overrun failure | `aidm/core/maneuver_resolver.py` | ~852–924 |

#### Why This Matters
- Breaks internal forced-movement invariants
- Violates DMG expectations
- Creates asymmetry between success and failure semantics

#### Resolution
Addressed by **CP-19B — Failure-Path Hazard Resolution**.

---

## 4. MEDIUM-PRIORITY OBSERVATIONS (DOCUMENTED, NOT BLOCKING)

### 4.1 Movement Cost Validation

- `play_loop.py` does not validate that sufficient movement remains after terrain
  cost is applied.
- Deferred intentionally to avoid refactoring play loop mid-cycle.
- Acceptable for CP-19.

### 4.2 Soft Cover Geometry

- Soft cover uses simplified adjacency-based logic.
- Does not compute full corner-to-corner line-of-sight.
- Acceptable simplification for deterministic Tier-1 mechanics.

---

## 5. INTENTIONAL DEGRADATIONS (CONFIRMED)

| Feature | Limitation | Rationale |
|-------|------------|-----------|
| Steep slopes | Placeholder DC 10 logic | Skill system deferred |
| Shallow water | No swimming | Aquatic kernel deferred |
| Concealment | Not implemented | Visibility kernel deferred |
| Weather | Not implemented | Environmental kernel deferred |
| Persistent terrain | Forbidden | Would cross G-T3D |

These are **design decisions**, not defects.

---

## 6. DOCUMENTATION NOTES

- Some CP-19 documents remain marked **DRAFT**
- Finalization is required after CP-19B merge
- Cross-linking between Progress / Feedback / Acceptance docs recommended

---

## 7. FINAL RECOMMENDATION

- **DO NOT** freeze CP-19 until CP-19B is implemented
- After CP-19B:
  - Upgrade acceptance to FINAL
  - Freeze CP-19 permanently
  - Proceed to CP-20

---

## END OF CP-19 FEEDBACK REPORT
