# WO-003 Completion Report: LOS/LOE Resolution

**Assigned To:** Sonnet-C (Claude 4.5 Sonnet)
**Issued By:** Opus (PM)
**Date Completed:** 2026-02-11
**Status:** Complete

---

## 1. Files Created with Line Counts

| File | Lines | Description |
|------|-------|-------------|
| `aidm/core/los_resolver.py` | 644 | LOS/LOE resolution with 3D Bresenham, height occlusion |
| `tests/test_los_resolver.py` | 690 | Comprehensive test suite (43 tests) |
| **Total** | **1,334** | |

---

## 2. Test Count and Pass/Fail Status

### New Tests: 43 passed

```
tests/test_los_resolver.py::TestBresenham3D::test_horizontal_line_same_y_same_z PASSED
tests/test_los_resolver.py::TestBresenham3D::test_horizontal_line_negative_direction PASSED
tests/test_los_resolver.py::TestBresenham3D::test_vertical_line_same_x_same_z PASSED
tests/test_los_resolver.py::TestBresenham3D::test_z_axis_line PASSED
tests/test_los_resolver.py::TestBresenham3D::test_diagonal_line_2d_same_z PASSED
tests/test_los_resolver.py::TestBresenham3D::test_3d_diagonal PASSED
tests/test_los_resolver.py::TestBresenham3D::test_single_point_start_equals_end PASSED
tests/test_los_resolver.py::TestBresenham3D::test_integer_arithmetic_only PASSED
tests/test_los_resolver.py::TestBresenham3D::test_includes_start_and_end PASSED
tests/test_los_resolver.py::TestBresenham3D::test_asymmetric_deltas PASSED
tests/test_los_resolver.py::TestCheckLOS::test_clear_los_across_empty_grid PASSED
tests/test_los_resolver.py::TestCheckLOS::test_los_blocked_by_opaque_cell PASSED
tests/test_los_resolver.py::TestCheckLOS::test_los_blocked_by_opaque_border PASSED
tests/test_los_resolver.py::TestCheckLOS::test_los_not_blocked_by_solid_only_cell PASSED
tests/test_los_resolver.py::TestCheckLOS::test_los_not_blocked_by_opaque_permeable_cell PASSED
tests/test_los_resolver.py::TestCheckLOS::test_height_occlusion_short_observer_behind_tall_wall PASSED
tests/test_los_resolver.py::TestCheckLOS::test_height_clear_tall_observer_over_short_wall PASSED
tests/test_los_resolver.py::TestCheckLOS::test_elevation_difference_affects_los PASSED
tests/test_los_resolver.py::TestCheckLOE::test_clear_loe_across_empty_grid PASSED
tests/test_los_resolver.py::TestCheckLOE::test_loe_blocked_by_solid_cell PASSED
tests/test_los_resolver.py::TestCheckLOE::test_loe_blocked_by_solid_border PASSED
tests/test_los_resolver.py::TestCheckLOE::test_loe_not_blocked_by_opaque_only_cell PASSED
tests/test_los_resolver.py::TestCheckLOE::test_loe_not_blocked_by_solid_permeable PASSED
tests/test_los_resolver.py::TestCheckLOE::test_loe_blocked_through_glass_wall PASSED
tests/test_los_resolver.py::TestBarrierTruthTable::test_stone_wall_blocks_both PASSED
tests/test_los_resolver.py::TestBarrierTruthTable::test_glass_wall_blocks_loe_only PASSED
tests/test_los_resolver.py::TestBarrierTruthTable::test_magical_darkness_blocks_neither PASSED
tests/test_los_resolver.py::TestBarrierTruthTable::test_iron_grate_blocks_neither PASSED
tests/test_los_resolver.py::TestEntityConvenienceFunctions::test_check_los_between_entities PASSED
tests/test_los_resolver.py::TestEntityConvenienceFunctions::test_check_loe_between_entities PASSED
tests/test_los_resolver.py::TestEntityConvenienceFunctions::test_entity_los_blocked_by_wall PASSED
tests/test_los_resolver.py::TestEntityConvenienceFunctions::test_entity_not_found_raises_error PASSED
tests/test_los_resolver.py::TestEntityConvenienceFunctions::test_default_entity_height PASSED
tests/test_los_resolver.py::TestEdgeCases::test_adjacent_cells_distance_1 PASSED
tests/test_los_resolver.py::TestEdgeCases::test_same_cell_distance_0 PASSED
tests/test_los_resolver.py::TestEdgeCases::test_out_of_bounds_observer PASSED
tests/test_los_resolver.py::TestEdgeCases::test_out_of_bounds_target PASSED
tests/test_los_resolver.py::TestEdgeCases::test_diagonal_los_clear PASSED
tests/test_los_resolver.py::TestEdgeCases::test_negative_elevation PASSED
tests/test_los_resolver.py::TestResultSerialization::test_los_result_to_dict_clear PASSED
tests/test_los_resolver.py::TestResultSerialization::test_los_result_to_dict_blocked PASSED
tests/test_los_resolver.py::TestResultSerialization::test_loe_result_to_dict PASSED
tests/test_los_resolver.py::TestResultSerialization::test_result_is_frozen PASSED
```

---

## 3. Full Suite Verification

```
python -m pytest tests/ -v --tb=short
===================== 2173 passed, 43 warnings in 10.56s ======================
```

**Zero regressions.** All existing tests continue to pass.

---

## 4. Design Decisions Made

### 4.1 Bresenham 3D Algorithm

- **Integer-only arithmetic**: Uses bit-shifting (`<< 1`) for multiplication by 2, and addition/subtraction only
- **Primary axis selection**: Algorithm determines which axis (X, Y, or Z) has the largest delta and uses that as the driving axis
- **Error accumulators**: Uses P_y and P_z accumulators per RQ-BOX-001 Finding 13 for deterministic stepping

### 4.2 Height Occlusion Logic

Per RQ-BOX-001 Finding 4:
- Observer effective Z = observer_cell.elevation + observer_height
- Target effective Z = target_cell.elevation + target_height
- At each cell traversed: blocked if `Z_ray < cell.elevation + cell.height`
- Uses integer arithmetic throughout (no floating point division)

### 4.3 Border Checking

- When ray crosses from cell A to cell B, checks the border on cell A in the direction of movement
- Direction determined by step delta (e.g., moving +X means crossing East border)
- Final border crossing to target cell is checked separately

### 4.4 Result Dataclasses

- Both `LOSResult` and `LOEResult` are frozen dataclasses for immutability
- Include `to_dict()` method for serialization
- Store observer_pos and target_pos for context in results

### 4.5 Entity Convenience Functions

- Default entity height: 5 feet (Medium humanoid eye level)
- Entity lookup via `grid._entities` dictionary
- Raises `KeyError` if entity not found (fail fast, not silent)

---

## 5. Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All new tests pass | ✅ | 43/43 tests passing |
| All existing tests pass | ✅ | 2173 passed, zero regressions |
| bresenham_3d uses integer arithmetic only | ✅ | `test_integer_arithmetic_only` verifies all outputs are `int` |
| LOS correctly distinguishes OPAQUE from SOLID | ✅ | `test_los_not_blocked_by_solid_only_cell` |
| LOE correctly distinguishes SOLID from OPAQUE | ✅ | `test_loe_not_blocked_by_opaque_only_cell` |
| Height occlusion works correctly | ✅ | `test_height_occlusion_*` and `test_height_clear_*` |
| Stone wall blocks both LOS and LOE | ✅ | `test_stone_wall_blocks_both` |
| Glass wall blocks LOE only | ✅ | `test_glass_wall_blocks_loe_only` |
| Magical darkness blocks neither | ✅ | `test_magical_darkness_blocks_neither` |
| Iron grate blocks neither | ✅ | `test_iron_grate_blocks_neither` |

---

## 6. Issues Discovered

None. Implementation proceeded smoothly using the WO-001 deliverables (PropertyMask, BattleGrid, GridCell).

---

## 7. API Summary

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `bresenham_3d` | `(start: Tuple[int,int,int], end: Tuple[int,int,int]) -> List[Tuple[int,int,int]]` | 3D Bresenham line algorithm |
| `check_los` | `(grid, observer_pos, observer_height, target_pos, target_height) -> LOSResult` | Height-aware LOS check |
| `check_loe` | `(grid, observer_pos, observer_height, target_pos, target_height) -> LOEResult` | Height-aware LOE check |
| `check_los_between_entities` | `(grid, observer_id, target_id, observer_height=5, target_height=5) -> LOSResult` | Entity convenience wrapper |
| `check_loe_between_entities` | `(grid, observer_id, target_id, observer_height=5, target_height=5) -> LOEResult` | Entity convenience wrapper |

### Result Types

```python
@dataclass(frozen=True)
class LOSResult:
    is_clear: bool
    blocking_position: Optional[Position]
    blocking_reason: Optional[str]  # "cell_opaque", "border_opaque", "height_occlusion"
    observer_pos: Position
    target_pos: Position

@dataclass(frozen=True)
class LOEResult:
    is_clear: bool
    blocking_position: Optional[Position]
    blocking_reason: Optional[str]  # "cell_solid", "border_solid"
    observer_pos: Position
    target_pos: Position
```

---

## 8. Integration Points

This module integrates with:
- `aidm.schemas.geometry.PropertyMask` — for `blocks_los()` and `blocks_loe()` checks
- `aidm.core.geometry_engine.BattleGrid` — for cell/border access and entity tracking
- `aidm.schemas.geometry.GridCell` — for elevation and height properties
- `aidm.schemas.position.Position` — for all position coordinates

---

## 9. Deliverables Summary

| Deliverable | Location | Status |
|-------------|----------|--------|
| Implementation | `aidm/core/los_resolver.py` | ✅ Complete (644 lines) |
| Tests | `tests/test_los_resolver.py` | ✅ Complete (690 lines, 43 tests) |
| Completion Report | `pm_inbox/SONNET-C_WO-003_LOS_LOE_RESOLVER.md` | ✅ This document |

---

**Work Order Complete.** Ready for PM review.
