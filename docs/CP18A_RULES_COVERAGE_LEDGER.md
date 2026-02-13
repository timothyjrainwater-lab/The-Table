# CP-18A — Mounted Combat Rules Coverage Ledger

**Status:** DESIGNED (CP-18A)
**Date:** 2026-02-08
**Authority:** Binding (supplements AIDM_CORE_RULESET_AUDIT.md)

---

## 1. Purpose

This document provides the **Rules Coverage Ledger (RCL) entries** for all mounted combat subsystems designed in CP-18A. Each entry documents:

- Subsystem identification
- PHB/DMG reference
- Classification (atomic/cross-cutting/dm-discretion)
- Coverage status
- Determinism risk assessment
- Deferred edge cases

---

## 2. Ledger Entries

### 2.1 Core Mounted Combat

| Field | Value |
|-------|-------|
| **Subsystem Name** | Mounted Combat (Core) |
| **Source** | PHB p.157 |
| **Classification** | cross-cutting |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | MEDIUM — Requires explicit position derivation |
| **Implementation Status** | Schema designed, not implemented |
| **Deferred Edge Cases** | Independent mounts (SKR-003), exotic mounts (SKR-010) |
| **Notes** | Rider-mount coupling model fully specified. Position derived from mount. |

---

### 2.2 Rider–Mount Coupling

| Field | Value |
|-------|-------|
| **Subsystem Name** | Rider–Mount Coupling |
| **Source** | PHB p.157 (implied) |
| **Classification** | cross-cutting |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Bidirectional references, consistency invariant |
| **Implementation Status** | Schema designed (MountedState, RIDER_ID backref) |
| **Deferred Edge Cases** | None |
| **Notes** | Explicit `mounted_state` on rider, `rider_id` on mount. Validated consistency. |

---

### 2.3 Controlled Mount Movement

| Field | Value |
|-------|-------|
| **Subsystem Name** | Controlled Mount Movement |
| **Source** | PHB p.157 |
| **Classification** | cross-cutting |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Uses existing movement/AoO pipeline |
| **Implementation Status** | MountedMoveIntent designed |
| **Deferred Edge Cases** | Full movement legality (terrain, obstacles) deferred to movement system |
| **Notes** | Mount moves, rider carried. AoOs provoked by mount only. |

---

### 2.4 Uncontrolled Mount (DC 20 Ride)

| Field | Value |
|-------|-------|
| **Subsystem Name** | Uncontrolled Mount Handling |
| **Source** | PHB p.157, Ride skill p.80-81 |
| **Classification** | atomic |
| **Coverage Status** | ⚠️ PARTIALLY DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Standard skill check |
| **Implementation Status** | Concept documented, skill system not implemented |
| **Deferred Edge Cases** | DC 20 Ride check resolution (requires skill system) |
| **Notes** | Light/heavy horses require move action + Ride check. Failure = full-round wasted. |

---

### 2.5 Mounted AoO Provocation

| Field | Value |
|-------|-------|
| **Subsystem Name** | Mounted AoO Provocation |
| **Source** | PHB p.137-138, p.157 |
| **Classification** | cross-cutting |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Extends existing CP-15 AoO system |
| **Implementation Status** | Integration pattern designed |
| **Deferred Edge Cases** | Ranged attack while mounted (needs ranged system), spellcasting while mounted (blocked) |
| **Notes** | Movement AoOs target mount only. Rider actions (ranged, spell) target rider. |

---

### 2.6 Higher Ground Bonus

| Field | Value |
|-------|-------|
| **Subsystem Name** | Mounted Higher Ground Bonus |
| **Source** | PHB p.157 |
| **Classification** | atomic |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Simple size comparison |
| **Implementation Status** | get_mounted_attack_bonus() designed |
| **Deferred Edge Cases** | None |
| **Notes** | +1 melee attack vs creatures smaller than mount who are on foot. |

---

### 2.7 Single Attack Restriction

| Field | Value |
|-------|-------|
| **Subsystem Name** | Mounted Single Attack Restriction |
| **Source** | PHB p.157 |
| **Classification** | atomic |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Distance check |
| **Implementation Status** | can_rider_full_attack() designed |
| **Deferred Edge Cases** | None |
| **Notes** | If mount moves >5 feet, rider limited to single melee attack. |

---

### 2.8 Mounted Charge

| Field | Value |
|-------|-------|
| **Subsystem Name** | Mounted Charge |
| **Source** | PHB p.154, p.157 |
| **Classification** | cross-cutting |
| **Coverage Status** | ⚠️ PARTIALLY DESIGNED (CP-18A) |
| **Determinism Risk** | MEDIUM — Requires charge system integration |
| **Implementation Status** | is_charge flag in MountedMoveIntent |
| **Deferred Edge Cases** | Charge path validation, AC penalty application, lance double damage |
| **Notes** | Double lance damage on charge. Spirited Charge feat (×3) deferred. |

---

### 2.9 Ranged Attacks While Mounted

| Field | Value |
|-------|-------|
| **Subsystem Name** | Mounted Ranged Attacks |
| **Source** | PHB p.157 |
| **Classification** | cross-cutting |
| **Coverage Status** | ⚠️ PARTIALLY DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Penalty application |
| **Implementation Status** | Concept documented |
| **Deferred Edge Cases** | Ranged attack system not implemented. Mounted Archery feat deferred. |
| **Notes** | -4 double move, -8 running. Full attack allowed with ranged while moving. |

---

### 2.10 Condition Propagation (Rider ↔ Mount)

| Field | Value |
|-------|-------|
| **Subsystem Name** | Mounted Condition Propagation |
| **Source** | PHB p.157 (implicit), conditions p.307-312 |
| **Classification** | cross-cutting |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | MEDIUM — Requires condition event hooks |
| **Implementation Status** | Propagation rules fully enumerated |
| **Deferred Edge Cases** | Grappled while mounted (SKR-005) |
| **Notes** | Mount conditions (prone, defeated) force dismount. Rider unconscious triggers fall check. |

---

### 2.11 Voluntary Dismount

| Field | Value |
|-------|-------|
| **Subsystem Name** | Voluntary Dismount |
| **Source** | PHB p.80 (Ride skill), p.143 |
| **Classification** | atomic |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — Simple state transition |
| **Implementation Status** | DismountIntent and resolve_dismount() designed |
| **Deferred Edge Cases** | Fast dismount DC 20 Ride check (skill system) |
| **Notes** | Normal = move action. Fast = free action with DC 20 Ride. |

---

### 2.12 Forced Dismount (Mount Falls)

| Field | Value |
|-------|-------|
| **Subsystem Name** | Forced Dismount / Mount Fall |
| **Source** | PHB p.157 |
| **Classification** | cross-cutting |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | MEDIUM — RNG for Ride check and fall damage |
| **Implementation Status** | trigger_forced_dismount() designed |
| **Deferred Edge Cases** | Ride skill modifier (using placeholder +5) |
| **Notes** | DC 15 Ride for soft fall. Failure = 1d6 damage. |

---

### 2.13 Unconscious Rider Fall Check

| Field | Value |
|-------|-------|
| **Subsystem Name** | Unconscious Rider Saddle Check |
| **Source** | PHB p.157 |
| **Classification** | atomic |
| **Coverage Status** | ✅ DESIGNED (CP-18A) |
| **Determinism Risk** | LOW — d100 roll |
| **Implementation Status** | check_unconscious_fall() designed |
| **Deferred Edge Cases** | None |
| **Notes** | 50% stay (riding saddle), 75% stay (military saddle). Failure = fall + 1d6. |

---

### 2.14 Fight with Warhorse

| Field | Value |
|-------|-------|
| **Subsystem Name** | Fight with Warhorse |
| **Source** | PHB p.80 (Ride skill) |
| **Classification** | atomic |
| **Coverage Status** | ⚠️ NOTED (CP-18A) |
| **Determinism Risk** | LOW — DC 10 Ride, free action |
| **Implementation Status** | Concept noted, not fully designed |
| **Deferred Edge Cases** | Requires monster attack system for mount attacks |
| **Notes** | DC 10 Ride to direct war-trained mount to attack while rider also attacks. |

---

## 3. Mounted Combat Feats (All Deferred)

| Feat | Source | Status | Blocked By |
|------|--------|--------|------------|
| Mounted Combat | PHB p.98 | ❌ DEFERRED | Feat reaction system |
| Mounted Archery | PHB p.98 | ❌ DEFERRED | Ranged attack system |
| Ride-By Attack | PHB p.101 | ❌ DEFERRED | Charge system |
| Spirited Charge | PHB p.101 | ❌ DEFERRED | Charge system, feat chain |
| Trample | PHB p.102-103 | ❌ DEFERRED | Overrun system |

**Notes:** All mounted combat feats require the Ride skill (1 rank) and Mounted Combat feat as prerequisites. The Mounted Combat feat specifically requires a reaction mechanic (once per round, negate hit with Ride check) that is beyond CP-18A scope.

---

## 4. Risk Summary

### 4.1 LOW Risk Subsystems (Safe to Implement)

| Subsystem | Notes |
|-----------|-------|
| Rider–Mount Coupling | Clean schema, no external dependencies |
| Higher Ground Bonus | Simple size comparison |
| Single Attack Restriction | Distance threshold check |
| Voluntary Dismount | State transition |
| Unconscious Saddle Check | d100 roll |

### 4.2 MEDIUM Risk Subsystems (Careful Implementation)

| Subsystem | Risk Factors |
|-----------|--------------|
| Controlled Mount Movement | Integration with AoO system |
| Mounted Charge | Charge system not yet implemented |
| Condition Propagation | Event hooks required |
| Forced Dismount | RNG usage, skill placeholder |

### 4.3 HIGH Risk Subsystems (Blocked / Deferred)

| Subsystem | Blocked By |
|-----------|------------|
| Independent Mounts | SKR-003 (Agency Delegation) |
| Grapple While Mounted | SKR-005 (Relational Conditions) |
| Exotic Mounts | SKR-010 (Transformation History) |
| Mounted Spellcasting | Spellcasting system blocked |

---

## 5. Determinism Assessment

### 5.1 RNG Consumption Points

| Operation | Stream | Consumption |
|-----------|--------|-------------|
| AoO attacks against mount | `"combat"` | d20 + damage dice |
| Ride check (soft fall) | `"combat"` | d20 |
| Fall damage | `"combat"` | 1d6 |
| Unconscious saddle check | `"combat"` | d100 |

### 5.2 Event Ordering Invariants

1. **Mounted movement events are atomic blocks** — All steps in a move complete before rider actions
2. **AoO resolution precedes continuation** — If AoO defeats mount, movement aborts
3. **Dismount events are terminal** — No further mounted state changes after dismount

### 5.3 State Hash Stability

Mounted combat state contributes to WorldState hash via:
- `entities[rider_id]["mounted_state"]`
- `entities[mount_id]["rider_id"]`
- Position values (via mount only)

**Guarantee:** Identical seed + event sequence = identical final hash.

---

## 6. Integration Touchpoints

### 6.1 CP-15 (AoO)

- `check_aoo_triggers()` extended to recognize `MountedMoveIntent`
- Mount ID used as provoking actor for movement AoOs
- Existing resolution pipeline reused

### 6.2 CP-16 (Conditions)

- Condition application hook for mounted coupling
- Specific conditions trigger dismount (prone, defeated, stunned, paralyzed)
- `handle_mounted_condition_change()` function

### 6.3 CP-17 (Saves)

- No changes to save resolution
- Save effects may cause conditions that trigger dismount

### 6.4 Future Systems

- **Skill System:** Ride checks currently use placeholder modifier
- **Charge System:** Mounted charge bonuses/penalties
- **Feat System:** Mounted Combat feat reaction

---

## 7. Gap Analysis

### 7.1 Gaps Within CP-18A Scope

| Gap | Severity | Mitigation |
|-----|----------|------------|
| Ride skill modifiers | LOW | Placeholder +5, document for skill system |
| Mount attack capability | MEDIUM | `IS_MOUNT_TRAINED` flag, defer attack resolution |
| Charge integration | MEDIUM | `is_charge` flag ready, charge system needed |

### 7.2 Gaps Requiring SKR Development

| Gap | Required SKR | Timeline |
|-----|--------------|----------|
| Independent mounts | SKR-003 | Post-Phase 3 |
| Mounted grapple | SKR-005 | Post-Phase 1 |
| Exotic mounts | SKR-010 | Post-Phase 2 |

---

## 8. Conclusion

**CP-18A Mounted Combat** achieves **~70% RAW coverage** of PHB mounted combat rules within G-T1 constraints:

✅ **Fully Designed:**
- Rider-mount coupling model
- Controlled mount movement
- AoO provocation routing
- Higher ground bonus
- Single attack restriction
- Condition propagation rules
- Dismount (voluntary and forced)
- Unconscious rider handling

⚠️ **Partially Designed (Pending Systems):**
- Uncontrolled mount handling (skill system)
- Mounted charge (charge system)
- Ranged attacks while mounted (ranged system)
- Fight with warhorse (monster attack system)

❌ **Deferred (Gate Blocked):**
- Mounted Combat feat (reaction system)
- Independent mounts (SKR-003)
- Mounted grapple (SKR-005)
- Mounted spellcasting (spellcasting system)

**No capability gates crossed. Spellcasting remains blocked. Design complete.**

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** COMPLETE (Ledger entries finalized)
