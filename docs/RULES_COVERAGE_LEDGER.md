# Rules Coverage Ledger (RCL)
## Canonical Subsystem Coverage Tracker

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Coverage Ledger
**Status:** ACTIVE
**Last Updated:** 2026-02-08
**Audience:** Project Authority, Implementers, Auditors

---

## 1. PURPOSE

The Rules Coverage Ledger (RCL) provides a **single authoritative view** of:

- Which D&D 3.5e mechanics are implemented
- Which CP or kernel owns them
- Their capability-gate status
- Whether coverage is full, degraded, or deferred

This ledger prevents:
- Duplicate work
- Silent omissions
- Accidental scope creep

---

## 2. LEGEND

| Status | Meaning |
|------|--------|
| FULL | Fully implemented per RAW |
| DEGRADED | Partial / placeholder implementation |
| DEFERRED | Explicitly out of scope |
| FORBIDDEN | Blocked by closed capability gate |

---

## 3. MOVEMENT & POSITIONING

| Rule | Coverage | Owner | Notes |
|----|----------|------|-------|
| Normal movement | FULL | Core | Grid-based |
| Difficult terrain | FULL | CP-19 | 2× / 4× cost |
| Running | FULL | Core | Restricted by terrain |
| Charging | FULL | Core | Restricted by terrain |
| 5-foot step | FULL | Core | Restricted by severe terrain |
| Forced movement | FULL | CP-18 / CP-19 | Hazard-aware |
| Steep slopes | DEGRADED | CP-19 | Placeholder DC logic |
| Swimming | DEFERRED | — | Aquatic kernel |
| Climbing | DEFERRED | — | Skill kernel |
| Flight | DEFERRED | — | Movement kernel |

---

## 4. ENVIRONMENT & TERRAIN

| Rule | Coverage | Owner | Notes |
|----|----------|------|-------|
| Terrain movement cost | FULL | CP-19 | Read-only |
| Cover | FULL | CP-19 | Standard / Improved / Total |
| Soft cover | DEGRADED | CP-19 | Simplified geometry |
| Higher ground | FULL | CP-19 | +1 melee |
| Falling damage | FULL | CP-19 | 1d6 / 10 ft |
| Pits & ledges | FULL | CP-19 | Binary hazard |
| Shallow water | DEGRADED | CP-19 | Difficult terrain only |
| Environmental damage | DEFERRED | CP-20 | Design complete |
| Weather | DEFERRED | — | Environmental kernel |
| Terrain destruction | FORBIDDEN | G-T3D | Transformation history |

---

## 5. COMBAT MODIFIERS

| Rule | Coverage | Owner | Notes |
|----|----------|------|-------|
| Flanking | DEGRADED | Core | Simplified |
| Higher ground | FULL | CP-19 | Terrain-based |
| Mounted bonuses | DEGRADED | CP-18A | Full coupling deferred |
| Aid Another | DEFERRED | SKR-005 | Relational kernel |
| Grapple | DEGRADED | Core | Lite implementation |

---

## 6. CONDITIONS & RELATIONS

| Rule | Coverage | Owner | Notes |
|----|----------|------|-------|
| Simple conditions | FULL | CP-16 | Non-relational |
| Relational conditions | FORBIDDEN | G-T3C | Requires SKR-005 |
| Transformation history | FORBIDDEN | G-T3D | Kernel not open |

---

## 7. DAMAGE & EFFECTS

| Rule | Coverage | Owner | Notes |
|----|----------|------|-------|
| Weapon damage | FULL | Core | Deterministic |
| Falling damage | FULL | CP-19 | RNG isolated |
| Environmental damage | DEFERRED | CP-20 | Design ready |
| Ongoing damage | FORBIDDEN | G-T2A | Stat mutation |

---

## 8. MAGIC & SPELLS

| Rule | Coverage | Owner | Notes |
|----|----------|------|-------|
| Spellcasting | DEFERRED | — | Kernel required |
| Magical terrain | FORBIDDEN | G-T3D | Terrain history |
| Summons | FORBIDDEN | G-T3A | Entity forking |

---

## 9. MAINTENANCE RULES

- Update this ledger **whenever a CP closes**
- Do not silently change coverage status
- All FORBIDDEN entries require gate authorization
- DEGRADED entries must name their deferral target

---

## 10. CONCLUSION

The Rules Coverage Ledger is the **ground truth** for what the engine does
and does not support.

All future planning, audits, and CP proposals must reference this document.

---

## END OF RULES COVERAGE LEDGER
