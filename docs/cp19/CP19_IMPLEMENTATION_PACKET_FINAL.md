# CP-19 — Environment & Terrain Decisions
## Implementation Packet (FINAL)

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-19
**Status:** FINAL (Pending CP-19B Corrective Patch)
**Date:** 2026-02-08
**Depends on:** CP-15 (AoO), CP-16 (Conditions), CP-18 (Combat Maneuvers), CP-18A (Mounted Combat)
**Capability Gates:** G-T1 ONLY
**Audience:** Implementing Agents, Auditors

---

## 1. PURPOSE

This document defines the **authoritative implementation contract** for CP-19:
Environment, terrain, elevation, cover, falling damage, and hazard interaction.

CP-19 extends the deterministic combat engine with **read-only terrain queries**
and **single-resolution environmental effects**, without introducing persistence,
relational state, or time advancement.

This packet is **FINAL** and **must not be re-litigated**.

---

## 2. IMPLEMENTATION STATUS

| Aspect | Result |
|------|--------|
| Tests | 728 passing |
| Runtime | 1.92s |
| Determinism | 10× replay verified |
| Gate Safety | G-T1 only |
| Backward Compatibility | Preserved |

> **Note:** CP-19B addresses a narrow failure-path hazard gap.
> CP-19 freeze occurs immediately after CP-19B is merged.

---

## 3. IN-SCOPE FEATURES (IMPLEMENTED)

### 3.1 Movement & Terrain

- Difficult terrain with movement multipliers:
  - Normal (1×)
  - Difficult (2×)
  - Severe (4×)
- Stacking uses **highest multiplier only**
- Run, charge, and 5-ft-step restrictions enforced

### 3.2 Cover System

| Cover Type | AC | Reflex | AoO Blocked |
|-----------|----|--------|-------------|
| Standard | +4 | +2 | Yes |
| Improved | +8 | +4 | Yes |
| Total | N/A | N/A | Yes (targeting blocked) |
| Soft | +4 (melee only) | +0 | No |

- Cover integrated into `attack_resolver.py`
- Cover blocks AoO execution (except soft cover)

### 3.3 Elevation & Higher Ground

- Elevation tracked per entity (`EF.ELEVATION`)
- Higher ground grants:
  - +1 melee attack bonus
- Terrain elevation stacks with mounted elevation bonuses

### 3.4 Falling Damage

- 1d6 per 10 feet fallen
- Maximum 20d6
- Intentional jump: first 10 ft free (placeholder)
- Falling damage uses `"combat"` RNG stream only

### 3.5 Hazards

- Pits (binary fall trigger)
- Ledges / drop-offs
- Shallow water (treated as difficult terrain only)

### 3.6 Forced Movement Integration

- Bull Rush success path resolves hazards
- Overrun success path resolves hazards
- CP-19B patches failure paths to enforce same invariant

---

## 4. EXPLICIT DEGRADATIONS

The following are **intentional limitations**, not bugs:

| Feature | Degradation |
|-------|-------------|
| Steep slopes | Placeholder DC 10 balance logic |
| Shallow water | No swimming; movement penalty only |
| Concealment | Not implemented |
| Weather | Out of scope |
| Persistent terrain changes | Forbidden |

---

## 5. ORDERING & DETERMINISM CONTRACT

### Execution Order (Non-Negotiable)

1. Attacks of Opportunity
2. Movement execution
3. Environmental resolution (hazards, falling)

### RNG Rules

- No RNG used for:
  - Movement cost
  - Cover
  - Elevation
- RNG used only for:
  - Falling damage (`"combat"` stream)

---

## 6. FILE TOUCH MAP (FINAL)

### Created
- `aidm/core/terrain_resolver.py`

### Modified
- `aidm/schemas/terrain.py`
- `aidm/schemas/entity_fields.py`
- `aidm/core/attack_resolver.py`
- `aidm/core/aoo.py`
- `aidm/core/maneuver_resolver.py`

No additional file touches are permitted.

---

## 7. TEST COVERAGE

### Tier-1
- Terrain cost
- Cover bonuses
- Higher ground
- Falling damage
- Hazard detection

### Tier-2
- AoO blocked by cover
- Forced movement into hazards
- Mounted + terrain elevation stacking

### Determinism
- 10× identical replay hashes verified

---

## 8. CAPABILITY GATE SAFETY

| Gate | Status | Notes |
|-----|-------|-------|
| G-T1 | OPEN | Used |
| G-T2A | CLOSED | No stat mutation |
| G-T3A | CLOSED | No entity creation |
| G-T3C | CLOSED | No relational terrain |
| G-T3D | CLOSED | No terrain history |

---

## 9. FINALIZATION RULE

Once CP-19B is merged:

- CP-19 is **FINAL**
- No further changes allowed without new CP
- CP-20 may proceed

---

## END OF CP-19 IMPLEMENTATION PACKET
