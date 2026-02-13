# WO-011 Completion Report: Combat Reflexes + Multiple AoO

**Completed By:** Sonnet-E (Claude 4.5 Sonnet)
**Date:** 2026-02-11
**Status:** ✅ Complete

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `aidm/core/combat_reflexes.py` | 371 | Combat Reflexes feat and AoO tracking |
| `tests/test_combat_reflexes.py` | 704 | Comprehensive test suite |
| **Total** | **1075** | |

---

## Test Results

### New Tests
- **52 tests** in `test_combat_reflexes.py`
- **All 52 passed** ✅

### Full Suite Verification
- **2632 tests passed** (up from 2265 baseline)
- **0 regressions** ✅
- **43 warnings** (pre-existing deprecation warnings)

---

## Implementation Summary

### AoOTracker Dataclass (frozen=True)

```python
@dataclass(frozen=True)
class AoOTracker:
    entity_id: str
    max_aoo_per_round: int = 1
    aoo_used_this_round: int = 0
    aoo_targets_this_round: FrozenSet[str] = field(default_factory=frozenset)

    def to_dict() -> dict
    def from_dict(data: dict) -> AoOTracker
```

### Core Functions

1. **`get_max_aoo(entity_id, has_combat_reflexes, dex_modifier) -> int`**
   - Without feat: always 1
   - With feat: 1 + dex_modifier (minimum 1)

2. **`can_make_aoo(tracker, target_id) -> bool`**
   - Checks if AoO slots available AND target not already hit this round

3. **`record_aoo(tracker, target_id) -> AoOTracker`**
   - Returns new tracker with incremented count and target added
   - Immutable update pattern

4. **`reset_aoo_for_round(tracker) -> AoOTracker`**
   - Returns new tracker with count=0 and targets cleared

5. **`check_aoo_trigger(mover_id, from_pos, to_pos, threatener_id, threatener_pos, reach_ft, threatener_size) -> bool`**
   - Returns True if leaving a threatened square
   - Integrates with reach_resolver.is_square_threatened()

### AoOManager Class

```python
class AoOManager:
    def register_entity(entity_id, has_combat_reflexes, dex_modifier) -> None
    def get_tracker(entity_id) -> Optional[AoOTracker]
    def start_new_round() -> None
    def check_triggers_for_movement(mover_id, from_pos, to_pos, grid,
                                    reach_by_entity, size_by_entity) -> List[str]
    def attempt_aoo(attacker_id, target_id) -> bool
    def to_dict() -> dict
    def from_dict(data) -> AoOManager
```

---

## Test Coverage

### get_max_aoo (6 tests)
- Without feat always returns 1
- With feat and Dex +0/+3/+5/+10
- Negative Dex gives minimum 1

### AoOTracker (5 tests)
- Creation with defaults
- Creation with specific values
- Serialization roundtrip
- to_dict format
- Immutability (frozen)

### can_make_aoo (6 tests)
- First AoO allowed
- Second blocked (no feat)
- Second allowed (with feat)
- Same target blocked
- Different target allowed
- Max exhausted

### record_aoo (6 tests)
- Increments counter
- Adds target to set
- Returns new tracker
- Preserves entity_id
- Preserves max_aoo
- Multiple recordings

### reset_aoo_for_round (5 tests)
- Clears counter
- Clears target set
- Returns new tracker
- Preserves entity_id
- Preserves max_aoo

### check_aoo_trigger (6 tests)
- Leaving threatened triggers
- Moving within threat area
- Entering doesn't trigger
- Outside doesn't trigger
- 10ft reach at distance 2
- 10ft reach at distance 1

### AoOManager (11 tests)
- Register creates tracker
- Register with Combat Reflexes
- Unknown entity returns None
- start_new_round resets all
- attempt_aoo succeeds and records
- attempt_aoo fails when exhausted
- attempt_aoo fails on same target
- Unknown attacker fails
- check_triggers_for_movement
- Excludes exhausted entities
- Serialization roundtrip

### Reach Integration (3 tests)
- 5ft reach adjacent
- 10ft reach distance 2
- Large creature threatens from all squares

### Edge Cases (4 tests)
- Mover not in own trigger list
- Empty manager operations
- High Dex Combat Reflexes (6 AoO)
- Multiple entities same trigger

---

## Design Decisions

1. **Immutable Trackers**: Used frozen dataclass with FrozenSet for thread safety and clean state management

2. **No aoo.py Modification**: New system is additive - existing aoo.py unchanged

3. **reach_resolver Integration**: Uses `is_square_threatened()` for threat calculation with proper size support

4. **Same-Target Prevention**: FrozenSet tracks targets to prevent double-tapping per PHB p.92

5. **PHB p.92 Compliance**: Combat Reflexes grants 1 + Dex modifier AoO with minimum 1

---

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| All new tests pass | ✅ 52/52 |
| All existing tests pass (zero regressions) | ✅ 2632 passed |
| Combat Reflexes grants extra AoO | ✅ 1 + Dex modifier |
| Same-target prevention works | ✅ FrozenSet tracking |
| Round reset works | ✅ Clears count and targets |
| Integration with reach_resolver | ✅ Uses is_square_threatened |

---

## No Issues Discovered

Implementation completed without issues. All functions integrate cleanly with existing WO-006 reach_resolver.

---

**Ready for PM Review** ✅
