# CP-18 Design Acceptance Record

**Packet**: CP-18 Combat Maneuvers
**Status**: DESIGN COMPLETE — IMPLEMENTATION AUTHORIZED
**Date**: 2026-02-08

## Design Acceptance

| Criterion | Status |
|-----------|--------|
| Design document complete | ✅ [CP18_COMBAT_MANEUVERS_DECISIONS.md](CP18_COMBAT_MANEUVERS_DECISIONS.md) |
| Gate safety verified | ✅ G-T1 only (no closed gates crossed) |
| All degradations documented | ✅ See Section 2 below |
| Determinism plan explicit | ✅ RNG consumption order documented per maneuver |
| RAW citations complete | ✅ PHB p.154-160 |
| 5e contamination check passed | ✅ No 5e mechanics contamination |

## Explicit Degradations

The following maneuvers are **intentionally degraded** to maintain gate safety:

### 1. Sunder (Narrative Only)
- **RAW**: Deals damage to weapon/shield HP, can break items
- **CP-18**: Damage logged as event only, NO persistent item state change
- **Reason**: Item HP system not implemented, would require new kernel
- **Upgrade Path**: Item Management kernel (future)

### 2. Disarm (No Persistence)
- **RAW**: Weapon drops, can be picked up, ownership transfers
- **CP-18**: Event emitted, NO persistent item state, defender re-arms next turn (narrative)
- **Reason**: Item ownership/pickup mechanics not implemented
- **Upgrade Path**: Item Entity kernel (future)

### 3. Grapple (Grapple-Lite)
- **RAW**: Bidirectional state (A grapples B, B grappled by A), pinning, escape loops
- **CP-18**: Unidirectional only — Grappled condition on defender, NO condition on attacker
- **Reason**: Full grapple crosses G-T3C (Relational Conditions) — CLOSED gate
- **Upgrade Path**: SKR-005 (Relational Conditions kernel)

### 4. Overrun (Degraded Avoidance)
- **RAW**: Defender can choose to avoid (interactive decision)
- **CP-18**: Avoidance controlled by AI/doctrine, not interactive
- **Reason**: Maintains determinism, avoids interactive decision loop
- **Upgrade Path**: Interactive decision system (future)

## Gate Safety Verification

| Gate | Status | CP-18 Status |
|------|--------|--------------|
| **G-T1** (Tier 1 Mechanics) | ✅ OPEN | **USED** |
| **G-T2A** (Permanent Stat Mutation) | 🔒 CLOSED | ✅ NOT CROSSED |
| **G-T2B** (XP Economy) | 🔒 CLOSED | ✅ NOT CROSSED |
| **G-T3A** (Entity Forking) | 🔒 CLOSED | ✅ NOT CROSSED |
| **G-T3C** (Relational Conditions) | 🔒 CLOSED | ⚠️ MITIGATED via Grapple-lite |
| **G-T3D** (Transformation History) | 🔒 CLOSED | ✅ NOT CROSSED |

## Maneuver Implementation Summary

| Maneuver | Implementation Level | Condition Applied | Gate Status |
|----------|---------------------|-------------------|-------------|
| Bull Rush | Full | None (position change) | ✅ G-T1 |
| Trip | Full | Prone (CP-16) | ✅ G-T1 |
| Overrun | Full (degraded avoidance) | Prone (CP-16) | ✅ G-T1 |
| Sunder | Degraded (narrative) | None | ✅ G-T1 |
| Disarm | Degraded (no persistence) | None | ✅ G-T1 |
| Grapple | Degraded (unidirectional) | Grappled (CP-16) | ✅ G-T1 |

## What Is NOT Authorized

❌ Expansion of Grapple beyond unidirectional condition
❌ Persistent item damage from Sunder
❌ Item ownership transfer from Disarm
❌ Feat integration (Improved X feats)
❌ Skill checks (Escape Artist, etc.)
❌ Trip weapon mechanics
❌ Multi-round grapple state machines

## Implementation Authorization

CP-18 implementation MAY proceed once:
1. ✅ Design document accepted (this record)
2. ⏳ Implementation Instruction Packet created
3. ⏳ Implementation authorized by user

---

**Design Signature:**
- **Designer**: Claude (Design Agent)
- **Date**: 2026-02-08
- **Design Document**: [CP18_COMBAT_MANEUVERS_DECISIONS.md](CP18_COMBAT_MANEUVERS_DECISIONS.md)
- **Status**: ✅ DESIGN ACCEPTED — AWAITING IMPLEMENTATION PACKET
