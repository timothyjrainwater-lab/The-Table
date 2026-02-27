# FINDING-AUDIT-FEAT-PREREQ-001 — Feat Prerequisite Data Errors

**ID:** FINDING-AUDIT-FEAT-PREREQ-001
**Severity:** LOW
**Status:** OPEN
**Found by:** AUDIT-WO-006 (2026-02-27)
**Lifecycle:** NEW

---

## Description

Three feat prerequisite data entries have errors vs PHB:

## Evidence

| Feat | Code Prereqs | PHB Prereqs | Error |
|------|-------------|-------------|-------|
| Power Attack | STR 13, BAB +1 | BAB +1 only | Overconstrained — STR 13 not a PHB prereq |
| Cleave | STR 13, Power Attack | STR 13, Power Attack, BAB +1 | Missing BAB +1 |
| Weapon Focus | BAB +1 | Proficiency with weapon, BAB +1 | Missing proficiency check |

**PHB Citations:**
- Power Attack (p.89): "Benefit: ... Prerequisites: Str 13." Wait — PHB p.89 DOES list Str 13 for Power Attack. Re-reading: "Prerequisites: Str 13." The audit agent may have been incorrect. BAB +1 is also listed. Need re-verification.
- Cleave (p.91): "Prerequisites: Power Attack, Str 13, base attack bonus +1." Code missing BAB +1.
- Weapon Focus (p.102): "Prerequisites: Proficiency with selected weapon, base attack bonus +1." Code missing proficiency.

## Correction (Power Attack)

PHB p.89 lists Power Attack prerequisites as "Str 13" AND implied BAB from context. Actually PHB p.89: "Prerequisite: Str 13." (Str 13 IS listed.) So code may be correct for Power Attack — the overconstrained finding may be wrong. **Needs manual re-verification against physical PHB p.89.**

## Impact

LOW — Chargen prerequisite checks use this data. Overconstrained = prevents valid build. Missing = allows invalid build. Neither affects combat resolution.

## Fix

Verify each entry against PHB hardcopy. Fix Cleave (add BAB +1) and Weapon Focus (add proficiency check or document deliberate omission). Revisit Power Attack after manual PHB check.
