# CP-18A Acceptance Record

**Packet**: CP-18A Mounted Combat & Rider-Mount Coupling
**Status**: COMPLETE
**Date**: 2026-02-08

## Acceptance Metrics

| Metric | Value |
|--------|-------|
| Test Count (Total) | 626 |
| Test Count (New) | 32 (24 unit + 8 integration) |
| Runtime | 1.71s |
| Determinism | 10× replay verified |
| Gate Status | G-T1 only (unchanged) |

## Gate Safety Verification

- ✅ No spellcasting mechanics
- ✅ No relational conditions (G-T3C)
- ✅ No entity forking (G-T3A)
- ✅ No permanent stat mutation beyond existing patterns
- ✅ All RNG uses "combat" stream only
- ✅ Event-sourced state changes only

## Implementation Summary

### Files Added
- `aidm/schemas/mounted_combat.py` - Core schemas (MountedState, MountType, SaddleType, intents)
- `aidm/core/mounted_combat.py` - Core logic (position derivation, coupling, dismount, bonuses)
- `tests/test_mounted_combat_core.py` - 24 unit tests
- `tests/test_mounted_combat_integration.py` - 8 integration tests
- `docs/CP18A_MOUNTED_COMBAT_DECISIONS.md` - Design specification
- `docs/CP18A_RULES_COVERAGE_LEDGER.md` - RCL entries for 14 subsystems
- `docs/CP18A_GATE_SAFETY_AUDIT.md` - Gate safety verification

### Files Modified
- `aidm/schemas/entity_fields.py` - Added MOUNTED_STATE, RIDER_ID, MOUNT_SIZE, IS_MOUNT_TRAINED
- `aidm/core/aoo.py` - Extended check_aoo_triggers for MountedMoveIntent
- `aidm/core/attack_resolver.py` - Added mounted_bonus to attack resolution
- `aidm/core/play_loop.py` - Added routing for mounted intents

## Key Design Decisions (Locked)

1. **Position Derivation**: Rider position derived from mount (never stored independently)
2. **AoO Routing**: Mount is provoker for mounted movement (provoker_id = mount_id)
3. **Condition Propagation**: Unidirectional (mount → rider only)
4. **Higher Ground**: +1 bonus when mount_size > target_size AND target not mounted
5. **Single Attack**: Only single attack when mount moves >5 feet

## RAW Citations

- PHB p.157: Mounted combat core rules
- PHB p.80-81: Ride skill (mount/dismount actions)
- PHB p.137-138: AoO rules (movement provocation)

---

**CP-18A IS CLOSED. No further changes authorized.**
