# RAW Fidelity Audit
## D&D 3.5e Rules Alignment & Documented Deviations

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Rules Audit
**Status:** ACTIVE
**Audience:** Project Authority, Auditors, Implementers

---

## 1. PURPOSE

This audit documents where the AIDM engine:

- **Implements D&D 3.5e RAW faithfully**
- **Intentionally deviates** (degraded or deferred)
- **Explicitly forbids mechanics** due to closed capability gates

Its goals are to:
- Prevent silent rules drift
- Avoid accidental 5e contamination
- Ensure every deviation is intentional, documented, and justified

This document is **authoritative**.

---

## 2. AUDIT METHODOLOGY

Each rules area is evaluated and classified as one of:

- **FULL** — Faithful to RAW
- **DEGRADED** — Partial or simplified, documented
- **DEFERRED** — Not implemented yet
- **FORBIDDEN** — Blocked by closed capability gate

Every non-FULL entry must reference a CP or kernel decision.

---

## 3. MOVEMENT & POSITIONING

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Normal movement | PHB 144–147 | FULL | Grid-based |
| Difficult terrain | PHB 148–150 | FULL | CP-19 |
| Running | PHB 144 | FULL | Terrain-restricted |
| Charging | PHB 154 | FULL | Terrain-restricted |
| 5-ft step | PHB 144 | FULL | Terrain-restricted |
| Forced movement | PHB 154 | FULL | CP-18/19 |
| Steep slopes | DMG 89–90 | DEGRADED | Placeholder DC |
| Swimming | PHB 84 | DEFERRED | Aquatic kernel |
| Climbing | PHB 69 | DEFERRED | Skill kernel |
| Flight | PHB 304 | DEFERRED | Movement kernel |

---

## 4. ENVIRONMENT & TERRAIN

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Cover | PHB 150–152 | FULL | CP-19 |
| Higher ground | PHB 151 | FULL | CP-19 |
| Falling damage | DMG 304 | FULL | CP-19 |
| Pits & ledges | DMG 71–72 | FULL | CP-19 |
| Shallow water | DMG 89 | DEGRADED | No swimming |
| Environmental damage | DMG 303–304 | DEFERRED | CP-20 |
| Weather effects | DMG 93–95 | DEFERRED | Environmental kernel |
| Terrain destruction | DMG various | FORBIDDEN | G-T3D |

---

## 5. COMBAT MODIFIERS

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Higher ground | PHB 151 | FULL | Terrain-based |
| Cover bonuses | PHB 150 | FULL | CP-19 |
| Flanking | PHB 157 | DEGRADED | Simplified |
| Aid Another | PHB 154 | DEFERRED | SKR-005 |
| Mounted combat | PHB 157 | DEGRADED | CP-18A |

---

## 6. CONDITIONS & CONTROL

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Prone | PHB 311 | FULL | CP-16 |
| Stunned | PHB 315 | FULL | CP-16 |
| Grapple | PHB 155–157 | DEGRADED | Lite only |
| Trip | PHB 158 | FULL | CP-18 |
| Bull Rush | PHB 154 | FULL | CP-18 |
| Overrun | PHB 157 | FULL | CP-18 |
| Relational conditions | — | FORBIDDEN | G-T3C |

---

## 7. DAMAGE & EFFECTS

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Weapon damage | PHB 134 | FULL | Core |
| Falling damage | DMG 304 | FULL | CP-19 |
| Environmental damage | DMG 303 | DEFERRED | CP-20 |
| Damage over time | DMG various | FORBIDDEN | G-T2A |

---

## 8. MAGIC & SPELLS

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Spellcasting | PHB 170+ | DEFERRED | Spell kernel |
| Summoning | PHB 285 | FORBIDDEN | G-T3A |
| Magical terrain | PHB spells | FORBIDDEN | G-T3D |
| Buff durations | PHB spells | FORBIDDEN | G-T2A |

---

## 9. CONTAMINATION CHECK (5e AVOIDANCE)

Confirmed **absent**:
- Advantage / disadvantage
- Concentration mechanic
- Short/long rests
- "Heavily obscured" terminology
- Bounded accuracy assumptions

All mechanics align with **3.5e math and semantics**.

---

## 10. CONCLUSION

This audit confirms:

- The engine is **faithful to D&D 3.5e RAW** where implemented
- All deviations are **intentional and documented**
- No silent rules drift is present
- Future work must update this audit on completion

This document must be updated **whenever a CP closes**.

---

## END OF RAW FIDELITY AUDIT
