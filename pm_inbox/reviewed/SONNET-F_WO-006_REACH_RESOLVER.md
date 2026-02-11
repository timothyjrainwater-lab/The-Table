# WO-006 Completion Report: Reach Weapons and Threatened Squares

**Agent:** Sonnet-F (Claude 4.5 Sonnet)
**Date:** 2026-02-11
**Status:** COMPLETE

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| aidm/core/reach_resolver.py | 451 | Reach and threatened area logic |
| tests/test_reach_resolver.py | 545 | Full test suite (58 tests) |

**Total:** 996 lines

---

## Test Results

### New Tests: 58 passed
- TestGetNaturalReach: 14 tests
- TestGetWeaponReach: 2 tests
- TestDiscreteDistance: 6 tests
- TestGetOccupiedSquares: 3 tests
- TestThreatenedSquares5ftReach: 4 tests
- TestThreatenedSquares10ftReach: 2 tests
- TestThreatenedSquares15ftReach: 1 test
- TestReachWeaponRules: 4 tests
- TestIsSquareThreatened: 6 tests
- TestCanThreaten: 6 tests
- TestGetThreatenedSquaresForEntity: 3 tests
- TestEdgeCases: 4 tests
- TestCountVerification: 3 tests

### Full Suite Verification
```
2346 passed, 43 warnings in 9.88s
```
**Zero regressions.** All existing tests continue to pass.

---

## Implementation Summary

### Core Functions Implemented

1. **get_natural_reach(size, is_long)** — Returns natural reach in feet
   - Tall creatures (bipedal): Fine-Tiny 0ft, Small-Medium 5ft, Large 10ft, etc.
   - Long creatures (quadruped): Reduced reach per PHB table

2. **get_weapon_reach(base_reach_ft, weapon_reach_ft)** — Weapon reach calculation
   - Reach weapons replace natural reach, don't add to it

3. **get_threatened_squares(entity_pos, size, reach_ft, ...)** — All threatened squares
   - For 5ft reach: 8 adjacent squares
   - For 10ft reach: distance 1-2 squares
   - Large+ creatures threaten from all occupied squares

4. **get_threatened_squares_for_entity(grid, entity_id, reach_ft)** — Grid convenience
   - Looks up entity position/size from BattleGrid

5. **is_square_threatened(entity_pos, size, reach_ft, target_pos)** — Single square check
   - Efficient for specific position queries

6. **can_threaten(attacker_pos, attacker_size, reach_ft, target_pos, target_size)** — Creature vs creature
   - Checks if attacker threatens any square occupied by target

7. **get_aoo_eligible_squares(...)** — AoO-specific threatened squares
   - Key rule: Reach weapons don't threaten adjacent (PHB p.157)
   - Natural reach 5ft + weapon reach 10ft = threatens distance 2 only

### Helper Functions

- **_discrete_distance(pos1, pos2)** — Chebyshev distance in squares
- **_get_occupied_squares(entity_pos, size)** — Footprint calculation
- **_get_minimum_distance_to_occupied(...)** — Multi-square creature distance
- **_get_ring_at_distance(...)** — Exact distance ring for reach weapons

---

## Design Decisions

1. **Chebyshev vs Movement Distance**: Used Chebyshev (max of dx, dy) for reach/threat calculations per 3.5e discrete distance rules, distinct from Position.distance_to() which uses 1-2-1-2 for actual movement costs.

2. **Reach Weapon vs Natural Reach**: Implemented separate get_aoo_eligible_squares() function to handle the key rule that reach weapons don't threaten adjacent squares. The main get_threatened_squares() handles natural reach (threatens all squares up to reach).

3. **Multi-square Footprints**: Large+ creatures threaten from all occupied squares using minimum distance to any occupied square.

4. **Deterministic Ordering**: Threatened squares sorted by (x, y) for reproducible results.

5. **No Modification of aoo.py**: Per WO-006 constraint, existing aoo.py was not modified. reach_resolver.py provides functions that can be integrated with aoo.py in a future work order.

---

## Acceptance Criteria Checklist

- [x] All new tests pass (58/58)
- [x] All existing tests pass (2346 total, zero regressions)
- [x] Natural reach correct per size (Fine-Colossal, tall/long variants)
- [x] Reach weapons don't threaten adjacent (get_aoo_eligible_squares)
- [x] Large creatures threaten from all squares (_get_minimum_distance_to_occupied)
- [x] Distance uses 3.5e discrete rules (Chebyshev distance)
- [x] Threatened square count matches expected (verified in tests)

---

## Future Integration Notes

The reach_resolver module is designed to integrate with:
- **aoo.py** — Replace hardcoded 5ft reach with get_threatened_squares()
- **geometry_engine.py** — Uses BattleGrid entity tracking for convenience functions
- **Future reach weapon equipment** — get_aoo_eligible_squares() handles weapon reach

No modifications to existing files were made per WO-006 constraints.

---

## References

- PHB p.137: Attacks of Opportunity
- PHB p.149: Size and Reach Table
- PHB p.157: Reach Weapons
