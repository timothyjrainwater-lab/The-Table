# WO-004 Completion Report: AoE Rasterization

**Agent:** Sonnet-D (Claude 4.5 Sonnet)
**Work Order:** WO-004
**Status:** COMPLETE ✅
**Date:** 2026-02-11

---

## Summary

Implemented Area of Effect (AoE) shape rasterization for the Box geometric engine. Converts spell/effect geometric shapes into lists of affected grid squares using RAW 3.5e rules.

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `aidm/core/aoe_rasterizer.py` | 441 | AoE shape algorithms |
| `tests/test_aoe_rasterizer.py` | 391 | Comprehensive test suite |

---

## Test Results

```
tests/test_aoe_rasterizer.py: 55 passed in 0.15s
```

### Test Coverage by Category

| Category | Tests | Status |
|----------|-------|--------|
| Discrete Distance | 4 | ✅ PASS |
| Burst Rasterization | 7 | ✅ PASS |
| Cone Rasterization | 10 | ✅ PASS |
| Line Rasterization | 7 | ✅ PASS |
| Cylinder/Sphere | 2 | ✅ PASS |
| Unified Interface | 10 | ✅ PASS |
| AoEResult Dataclass | 4 | ✅ PASS |
| Invariants | 4 | ✅ PASS |
| Edge Cases | 4 | ✅ PASS |
| AoEDirection | 3 | ✅ PASS |
| **Total** | **55** | ✅ ALL PASS |

### Regression Verification

```
Baseline tests: 2028 passed, 43 warnings in 9.43s
```

No regressions introduced.

---

## Implementation Details

### AoE Shapes Implemented

| Shape | Function | Description |
|-------|----------|-------------|
| BURST | `rasterize_burst()` | Circular spread from origin (Fireball) |
| SPREAD | (via interface) | Same as burst (corner-flow requires grid state) |
| CONE | `rasterize_cone()` | Triangular area (Burning Hands, Cone of Cold) |
| LINE | `rasterize_line()` | 5-foot wide line (Lightning Bolt) |
| CYLINDER | `rasterize_cylinder()` | Burst with height (Flame Strike) |
| SPHERE | `rasterize_sphere()` | 3D burst (2D same as burst) |

### Distance Formula (RQ-BOX-001 Finding 5)

```python
D_discrete = max(|dx|, |dy|) + floor(min(|dx|, |dy|) / 2)
```

This approximates the 3.5e 5/10/5 diagonal movement pattern and produces octagonal shapes for bursts.

### Cone Square Count Formula

Verified against PHB triangular number formula:
```
N = L/5 × (L/5 + 1) / 2
```

| Length | Expected | Actual | Status |
|--------|----------|--------|--------|
| 15 ft  | 6        | 6      | ✅ |
| 30 ft  | 21       | 21     | ✅ |
| 45 ft  | 45       | 45     | ✅ |

### Key Components

1. **AoEDirection (Enum)**: 8-directional for cones/lines (N, NE, E, SE, S, SW, W, NW)
2. **AoEShape (Enum)**: Shape types (BURST, SPREAD, CONE, LINE, CYLINDER, SPHERE)
3. **AoEResult (frozen dataclass)**: Immutable result with to_dict()/from_dict()
4. **discrete_distance()**: 3.5e compliant distance calculation
5. **get_aoe_affected_squares()**: Unified interface for all shapes
6. **create_aoe_result()**: Convenience wrapper returning AoEResult

---

## Design Decisions

### 1. AoEDirection vs geometry.Direction

Created new `AoEDirection` enum with 8 directions rather than modifying the existing 4-direction `geometry.Direction`. This:
- Follows the "no modification of existing files" constraint
- Keeps the two use cases separate (border access vs. targeting)
- Avoids breaking existing code

### 2. Discrete Distance Formula

Used `max + floor(min/2)` instead of the alternative `max + min`. This:
- Better approximates the 5/10/5 pattern at larger distances
- Produces correct octagonal shapes for bursts
- Matches RQ-BOX-001 Finding 5 specification

### 3. Conservative Line Rasterization

For diagonal lines, added adjacent squares that the line touches per RQ-BOX-001 Finding 9. A diagonal 5-foot line affects 3 squares per diagonal step (the main square plus two adjacent).

### 4. Cone Geometry

- Cardinal cones: Symmetric triangular expansion perpendicular to direction
- Diagonal cones: Rotated triangular pattern with perpendicular expansion
- Origin is excluded (cone starts from grid intersection)

---

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| All new tests pass | ✅ 55/55 |
| All existing tests pass | ✅ 2028/2028 |
| Burst produces octagonal shape | ✅ Verified |
| Cone square count matches formula | ✅ Verified |
| Line uses conservative rasterization | ✅ Verified |
| All shapes return Position lists | ✅ Verified |
| No duplicate squares in results | ✅ Verified (invariant test) |

---

## Usage Examples

```python
from aidm.schemas.position import Position
from aidm.core.aoe_rasterizer import (
    AoEShape, AoEDirection, rasterize_burst, rasterize_cone,
    get_aoe_affected_squares, create_aoe_result
)

# Direct function call
fireball_squares = rasterize_burst(Position(x=10, y=10), radius_ft=20)

# Cone spell
cone_squares = rasterize_cone(
    Position(x=5, y=5), AoEDirection.N, length_ft=30
)

# Unified interface
lightning_squares = get_aoe_affected_squares(
    AoEShape.LINE,
    Position(x=0, y=10),
    {"length_ft": 60, "direction": AoEDirection.E, "width_ft": 5}
)

# Get full result object
result = create_aoe_result(
    AoEShape.BURST,
    Position(x=10, y=10),
    {"radius_ft": 20}
)
print(result.square_count)  # Number of affected squares
print(result.to_dict())      # Serialized form
```

---

## Open Issues

None. All acceptance criteria met.

---

## Recommendation

Ready for integration. The AoE rasterizer provides accurate 3.5e-compliant shape calculation for use with the BattleGrid system from WO-001.
