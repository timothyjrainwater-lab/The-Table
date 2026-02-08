# CP-20 — Environmental Damage
## Comprehensive Test Case Catalog

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-20
**Document Type:** QA / Test Design
**Status:** ACTIVE
**Audience:** Implementers, Test Authors, Auditors

---

## 1. PURPOSE

This catalog enumerates **all known test scenarios** required to validate
CP-20 (Discrete Environmental Damage & Contact Hazards).

Its goals are to:
- Prevent missed edge cases
- Preserve determinism invariants
- Shorten implementation debug cycles
- Standardize acceptance expectations

This catalog is **binding** for CP-20 testing.

---

## 2. TEST CATEGORIES

Tests are grouped into:

1. **Direct Entry Hazards**
2. **Forced Movement Hazards**
3. **Compound Hazard Interactions**
4. **Integration & Ordering**
5. **Determinism & Replay**

---

## 3. DIRECT ENTRY HAZARDS

### 3.1 Fire Square — Voluntary Entry
- Actor moves into fire square
- Expected:
  - 1d6 fire damage
  - Damage event emitted
  - No persistence

### 3.2 Acid Pool — Voluntary Entry
- Actor moves into shallow acid
- Expected:
  - 1d6 acid damage
  - No saving throw
  - No ongoing damage

### 3.3 Lava Edge — Step-In
- Actor enters lava-edge square
- Expected:
  - 2d6 fire damage
  - Single resolution only

---

## 4. FORCED MOVEMENT HAZARDS

### 4.1 Bull Rush into Fire
- Defender pushed into fire square
- Expected:
  - Fire damage applied
  - Forced movement event preserved

### 4.2 Overrun into Acid
- Defender forced into acid pool
- Expected:
  - Acid damage
  - No double-trigger

### 4.3 Failure Pushback into Hazard
- Attacker fails maneuver
- Pushback enters hazard
- Expected:
  - Damage applies identically to success path

---

## 5. FALLING + DAMAGE COMBINATIONS

### 5.1 Fall into Spiked Pit
- Actor falls into pit with spikes
- Expected:
  - Falling damage
  - +1d6 piercing
  - Correct event ordering

### 5.2 Forced Movement → Fall → Damage
- Bull Rush pushes target off ledge into spiked pit
- Expected:
  - Single fall resolution
  - Correct damage aggregation

---

## 6. COMPOUND & EDGE CASES

### 6.1 Adjacent Multiple Hazards
- Actor pushed through fire into acid
- Expected:
  - First hazard triggers
  - Movement aborts
  - Second hazard ignored

### 6.2 Hazard Adjacent to AoO Threat
- Movement provokes AoO before hazard
- Expected:
  - AoO resolves first
  - Hazard resolves after movement

### 6.3 Mounted Entry into Hazard
- Mount enters fire square
- Expected:
  - Mount takes damage
  - Rider unaffected unless specified

---

## 7. ORDERING ASSERTIONS (MANDATORY)

All tests must verify ordering:

```
AoO
→ Movement / Forced Movement
→ Hazard Detection
→ Environmental Damage
→ Event Emission
```

Any deviation is a **test failure**.

---

## 8. RNG & DETERMINISM TESTS

### 8.1 Replay Stability
- Same scenario run 10×
- Identical state hashes

### 8.2 RNG Consumption
- Damage dice rolled in identical order
- No RNG used outside hazard damage

---

## 9. NEGATIVE TESTS

### 9.1 No Persistence
- Actor remains in hazard square next turn
- Expected:
  - No further damage

### 9.2 No Saving Throws
- No Reflex / Fort / misc checks invoked

---

## 10. COMPLETION CRITERIA

CP-20 testing is complete when:
- All scenarios in this catalog are covered
- No ordering violations exist
- Determinism verified
- Runtime remains < 2s

---

## END OF CP-20 TEST CASE CATALOG
