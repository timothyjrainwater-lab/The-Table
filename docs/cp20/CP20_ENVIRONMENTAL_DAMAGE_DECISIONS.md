# CP-20 — Discrete Environmental Damage & Contact Hazards
## Design Decisions (DESIGN-ONLY)

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-20
**Status:** DESIGN COMPLETE (NOT IMPLEMENTED)
**Date:** 2026-02-08
**Depends on:** CP-19 (Environment & Terrain), CP-15 (AoO), CP-16 (Conditions)
**Capability Gates:** G-T1 ONLY

---

## 1. PURPOSE

CP-20 extends CP-19 by introducing **discrete, single-resolution environmental
damage sources** that trigger on **contact or entry**, without persistence,
time advancement, or terrain modification.

This packet is **design-only** and does not authorize implementation.

---

## 2. DESIGN GOALS

1. Add encounter richness without opening new gates
2. Preserve strict determinism
3. Avoid time-based or persistent effects
4. Integrate cleanly with CP-19 terrain queries
5. Maintain AoO → Movement → Environment ordering

---

## 3. IN-SCOPE FEATURES

### 3.1 Contact Hazards (One-Shot)

These hazards apply damage **once per triggering event**:

| Hazard Type | Trigger | Damage |
|-----------|---------|--------|
| Fire square | Enter / pushed into | 1d6 fire |
| Acid pool (shallow) | Enter | 1d6 acid |
| Lava edge (adjacent fall-in) | Enter | 2d6 fire |
| Spiked pit | Fall into pit | Fall dmg + 1d6 piercing |

Rules:
- Damage applied immediately
- No ongoing damage
- No saving throws (unless explicitly specified later)

---

## 4. HAZARD SEMANTICS

### 4.1 Trigger Timing

- Hazards trigger during **environmental resolution**
- Hazards are evaluated **per square entered**
- First hazard encountered resolves immediately

### 4.2 Forced Movement

- Forced movement (Bull Rush, Overrun, etc.) may trigger hazards
- Forced movement uses existing CP-19 hazard resolution pipeline

---

## 5. RNG & DETERMINISM

- RNG used only for:
  - Environmental damage dice
- RNG stream:
  - `"combat"` ONLY
- No RNG for:
  - Hazard detection
  - Trigger timing

---

## 6. EXPLICIT NON-GOALS

The following are **out of scope** for CP-20:

- Damage over time
- Burning, ongoing acid, or persistent effects
- Terrain alteration (melting, spreading, collapsing)
- Environmental conditions (smoke, heat exposure)
- Saving throws vs hazards (placeholder only)
- Spell-created hazards

---

## 7. CAPABILITY GATE ANALYSIS

| Gate | Status | Notes |
|----|-------|-------|
| G-T1 | OPEN | Used |
| G-T2A | CLOSED | No stat mutation |
| G-T3A | CLOSED | No hazard entities |
| G-T3C | CLOSED | No relational state |
| G-T3D | CLOSED | No terrain history |

No gate pressure introduced.

---

## 8. FUTURE EXTENSION PATH

When future kernels open:

- G-T2A → ongoing environmental damage
- G-T3D → terrain transformation
- Spellcasting kernel → magical hazards

---

## 9. ACCEPTANCE CRITERIA (FOR FUTURE IMPLEMENTATION)

- Environmental damage triggers deterministically
- Forced movement integrates correctly
- No persistence introduced
- All tests pass < 2s
- 10× replay determinism verified

---

## 10. CONCLUSION

CP-20 defines a **safe, deterministic next step** for environmental interaction,
delivering increased tactical depth while preserving architectural discipline.

---

## END OF CP-20 DESIGN DECISIONS
