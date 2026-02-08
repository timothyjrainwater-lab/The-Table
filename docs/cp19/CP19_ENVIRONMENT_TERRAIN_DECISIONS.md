# CP-19 — Environment & Terrain Decisions
## Design Decisions (AUTHORITATIVE)

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-19
**Status:** DESIGN COMPLETE / IMPLEMENTED
**Date:** 2026-02-08
**Depends on:** CP-15 (AoO), CP-16 (Conditions), CP-18 (Combat Maneuvers), CP-18A (Mounted Combat)
**Capability Gates:** G-T1 ONLY

---

## 1. DESIGN GOALS

CP-19 introduces **environment and terrain mechanics** that:

1. Modify movement and combat **without persistence**
2. Remain **fully deterministic**
3. Integrate cleanly with AoO, maneuvers, and attacks
4. Avoid relational state, time loops, or terrain history
5. Remain strictly within **Tier-1 (G-T1)** capabilities

---

## 2. CORE PRINCIPLES

- **Read-only terrain:** Terrain is queried, never modified
- **Single-resolution effects:** All environmental effects resolve immediately
- **Explicit ordering:** AoO → Movement → Environment
- **No implicit state:** All effects are event-sourced
- **Degrade, don't defer:** Partial implementation preferred over omission

---

## 3. TERRAIN & MOVEMENT

### 3.1 Difficult Terrain

| Terrain | Movement Cost |
|-------|----------------|
| Normal | 1× |
| Difficult | 2× |
| Severe | 4× |

Rules:
- Highest multiplier wins (no stacking multiplication)
- Difficult or worse terrain:
  - Prohibits running and charging
- Severe terrain:
  - Prohibits 5-foot steps

---

## 4. COVER SYSTEM

### 4.1 Cover Types

| Type | AC | Reflex | AoO Blocked |
|----|----|--------|-------------|
| Standard | +4 | +2 | Yes |
| Improved | +8 | +4 | Yes |
| Total | N/A | N/A | Yes (blocks targeting) |
| Soft | +4 (melee only) | +0 | No |

### 4.2 Design Decisions

- Cover is computed at **attack declaration**
- Cover blocks AoO execution except soft cover
- Simplified geometry used for determinism

---

## 5. ELEVATION & HIGHER GROUND

- Elevation stored per entity
- Higher ground grants:
  - +1 melee attack bonus
- Terrain elevation stacks with mounted bonuses

---

## 6. FALLING DAMAGE

- Damage: 1d6 per 10 ft fallen
- Maximum: 20d6
- Intentional jumps:
  - First 10 ft free (placeholder)
- RNG isolated to `"combat"` stream

---

## 7. HAZARDS

### 7.1 Supported Hazards

- Pits
- Ledges / drop-offs
- Shallow water (movement penalty only)

### 7.2 Hazard Resolution

- Hazards trigger immediately upon entry
- Forced movement evaluates hazards **per square**
- First hazard encountered aborts remaining movement

---

## 8. FORCED MOVEMENT INTEGRATION

- Bull Rush and Overrun integrate with hazard resolution
- Success and failure paths are treated uniformly (post CP-19B)
- Push direction and distance are deterministic

---

## 9. EXPLICIT NON-GOALS

The following are **explicitly out of scope**:

- Terrain modification or destruction
- Environmental persistence
- Weather systems
- Concealment
- Swimming, climbing, flight
- Spell-created terrain

---

## 10. CAPABILITY GATE ANALYSIS

| Gate | Status | Rationale |
|----|-------|-----------|
| G-T1 | OPEN | Used |
| G-T2A | CLOSED | No stat mutation |
| G-T3A | CLOSED | No entities |
| G-T3C | CLOSED | No relational terrain |
| G-T3D | CLOSED | No terrain history |

No gate pressure introduced.

---

## 11. CONCLUSION

CP-19 provides deterministic, gate-safe environment and terrain mechanics
that materially improve combat realism while preserving architectural discipline.

---

## END OF CP-19 DESIGN DECISIONS
