# CP-19 — Environment & Terrain Decisions
## Acceptance Record (FINAL)

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-19
**Acceptance Status:** CONDITIONALLY ACCEPTED → FINAL UPON CP-19B MERGE
**Date:** 2026-02-08
**Reviewer Role:** Project Authority
**Scope Type:** Tier-1 Mechanics Only (G-T1)

---

## 1. ACCEPTANCE SUMMARY

CP-19 implements deterministic, read-only environment and terrain mechanics
integrated with movement, attacks, Attacks of Opportunity, and combat maneuvers.

All core objectives of CP-19 are met. One narrowly scoped correctness gap was
identified post-implementation and is addressed by **CP-19B**.

Upon completion of CP-19B, this packet is **FINAL and FROZEN**.

---

## 2. ACCEPTANCE CHECKLIST

### Core Functionality

- [x] Difficult terrain modifies movement cost (1× / 2× / 4×)
- [x] Cover system applies correct AC and Reflex bonuses
- [x] Cover blocks AoO execution (except soft cover)
- [x] Higher ground grants +1 melee attack bonus
- [x] Falling damage calculated as 1d6 / 10 ft (max 20d6)
- [x] Pits and ledges trigger falling on entry
- [x] Forced movement integrates with terrain and hazards

### Integration

- [x] Integrated with attack resolver
- [x] Integrated with AoO logic
- [x] Integrated with CP-18 maneuvers
- [x] Mounted combat interactions preserved

### Determinism

- [x] No hidden RNG usage
- [x] Falling damage uses `"combat"` RNG stream only
- [x] 10× deterministic replay verified
- [x] Event ordering preserved (AoO → Movement → Environment)

### Testing

- [x] 728 total tests passing
- [x] Tier-1 unit tests complete
- [x] Tier-2 integration tests complete
- [x] Runtime < 2 seconds

---

## 3. IDENTIFIED POST-IMPLEMENTATION GAP

### Gap ID: CP19-GAP-01

**Description:**
Failure-path forced movement for Bull Rush and Overrun bypasses hazard resolution,
allowing entities to enter pits or fall off ledges without triggering falling damage.

**Severity:** Critical correctness gap
**Root Cause:** Failure branches directly updated position without calling
`resolve_forced_movement_with_hazards()`.

**Resolution:**
Addressed by **CP-19B — Failure-Path Hazard Resolution**.

---

## 4. CONDITIONAL ACCEPTANCE STATUS

| Condition | Status |
|---------|--------|
| CP-19B implemented | ⬜ Pending |
| CP-19B tests passing | ⬜ Pending |
| No new regressions | ⬜ Pending |

Once all conditions are met, CP-19 acceptance is upgraded to **FINAL** automatically.

---

## 5. CAPABILITY GATE VERIFICATION

| Gate | Status | Verification |
|-----|-------|-------------|
| G-T1 | OPEN | Used |
| G-T2A | CLOSED | No permanent stat mutation |
| G-T2B | CLOSED | No XP economy |
| G-T3A | CLOSED | No entity creation |
| G-T3C | CLOSED | No relational terrain state |
| G-T3D | CLOSED | No terrain history |

No gate violations detected.

---

## 6. FREEZE DIRECTIVE

Upon successful merge of CP-19B:

- CP-19 is **FINAL**
- CP-19 is **FROZEN**
- No further changes permitted without a new CP
- Project may advance to CP-20

---

## 7. ACCEPTANCE SIGN-OFF

**Accepted By:** Project Authority
**Acceptance Mode:** Conditional → Automatic Finalization
**Date:** Upon CP-19B verification

---

## END OF CP-19 ACCEPTANCE RECORD
