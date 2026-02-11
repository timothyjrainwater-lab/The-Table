# Completion Report: WO-002 Cover Resolution

**Work Order:** WO-002 — Cover Resolution
**Agent:** Sonnet-B (Claude 4.5 Sonnet)
**Date Completed:** 2026-02-11
**Status:** COMPLETE

---

## Executive Summary

Successfully implemented the corner-to-corner cover resolution system for the Box geometric engine. The implementation follows RAW 3.5e PHB p.150-152 and RQ-BOX-001 Finding 3, tracing lines from attacker corners to defender corners to determine cover degree.

---

## Deliverables

### 1. `aidm/core/cover_resolver.py` (420 lines)

**Core Components:**

| Component | Description |
|-----------|-------------|
| `CoverDegree` enum | NO_COVER, HALF_COVER, THREE_QUARTERS_COVER, TOTAL_COVER |
| `CoverResult` dataclass | Immutable result with cover degree, AC/Reflex bonuses, line counts |
| `get_square_corners()` | Returns 4 corners (NW, NE, SE, SW) of a grid cell |
| `get_cells_along_line()` | Float-based line traversal to find intersected cells |
| `get_border_crossings()` | Identifies grid borders crossed by a line |
| `trace_corner_line()` | Checks if a corner-to-corner line is blocked |
| `get_footprint_squares()` | Returns all squares occupied by Large+ creatures |
| `calculate_cover()` | Main algorithm: 4×4 corner traces, count blocked, map to degree |
| `calculate_cover_from_positions()` | Convenience wrapper for Medium vs Medium |
| `has_cover()` | Quick check: any cover? |
| `has_total_cover()` | Quick check: total cover? |

**Cover Threshold Table (per dispatch spec):**

| Lines Blocked (of 16) | Cover Degree | AC Bonus | Reflex Bonus |
|-----------------------|--------------|----------|--------------|
| 0-4 | No Cover | +0 | +0 |
| 5-8 | Half Cover | +2 | +1 |
| 9-12 | Three-Quarters | +5 | +2 |
| 13-16 | Total Cover | Untargetable | N/A |

**Integration Points:**
- Imports `Position` from `aidm.schemas.position`
- Imports `PropertyMask`, `PropertyFlag`, `Direction`, `SizeCategory` from `aidm.schemas.geometry`
- Imports `BattleGrid` from `aidm.core.geometry_engine`
- Uses `PropertyMask.blocks_loe()` and `PropertyMask.blocks_los()` for blocking checks

### 2. `tests/test_cover_resolver.py` (58 tests, 580 lines)

**Test Coverage by Category:**

| Category | Tests | Description |
|----------|-------|-------------|
| CoverDegree enum | 2 | Enum values and count |
| CoverResult dataclass | 3 | Creation, immutability, serialization |
| Cover thresholds | 4 | Verify threshold ranges and bonuses |
| get_square_corners() | 3 | Corner positions and ordering |
| get_cells_along_line() | 4 | Horizontal, vertical, diagonal, same-point |
| get_border_crossings() | 3 | Border crossing detection |
| trace_corner_line() | 5 | Empty grid, solid cell, grate, border wall, glass |
| get_footprint_squares() | 6 | All size categories from Small to Colossal |
| calculate_cover() - no cover | 3 | Empty grid, adjacent, diagonal adjacent |
| calculate_cover() - partial | 2 | Partial obstruction scenarios |
| calculate_cover() - total | 2 | Full wall, blocks targeting |
| calculate_cover() - Large+ | 3 | Large vs Medium, Medium vs Large, Large vs Large |
| Convenience wrappers | 2 | calculate_cover_from_positions() tests |
| Quick checks | 4 | has_cover(), has_total_cover() |
| Material-specific | 2 | Glass (LOS vs LOE), iron grate (permeable) |
| Border wall cover | 1 | Border walls (not cell contents) |
| Edge cases | 3 | Same position, grid boundary, out of bounds |
| Bonus values | 4 | PHB-compliant AC and Reflex bonuses |
| Determinism | 2 | Same input → same output |
| **Total** | **58** | |

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `calculate_cover()` implemented | ✅ | `aidm/core/cover_resolver.py:290-373` |
| Corner-to-corner algorithm | ✅ | Traces 16 lines (4×4 corners) per call |
| Cover thresholds correct | ✅ | 0-4=none, 5-8=half, 9-12=¾, 13-16=total |
| AC/Reflex bonuses correct | ✅ | Half: +2/+1, ¾: +5/+2, Total: blocks |
| Large+ creature support | ✅ | Optimal square selection for multi-cell entities |
| PropertyMask integration | ✅ | Uses blocks_loe() and blocks_los() |
| Border wall support | ✅ | Checks border_masks for crossed borders |
| Material types handled | ✅ | Glass (solid), grate (permeable), etc. |
| Tests: 20+ required | ✅ | 58 tests |
| Tests: all passing | ✅ | 58 passed in 0.18s |
| Full suite: no regressions | ✅ | 2130 passed (up from ~2072 baseline) |

---

## Algorithm Details

### Corner-to-Corner Cover Resolution

1. **Get attacker's optimal square** (closest to defender for Large+ creatures)
2. **Get defender's optimal square** (closest to attacker for Large+ creatures)
3. **Extract 4 corners** from each square (NW, NE, SE, SW)
4. **Trace 16 lines** (each attacker corner to each defender corner)
5. **For each line:**
   - Find all cells the line passes through (`get_cells_along_line()`)
   - Check each cell's `cell_mask.blocks_loe()` or `blocks_los()`
   - Find all border crossings (`get_border_crossings()`)
   - Check each border's `border_mask.blocks_loe()` or `blocks_los()`
   - Mark line as blocked if any check returns True
6. **Count blocked lines** and map to cover degree via threshold table

### Float-Based Line Traversal

The implementation uses floating-point coordinates for corners (cell center ± 0.5) and samples along the line to find intersected cells. This handles:
- Diagonal lines that graze cell corners
- Lines parallel to grid edges
- Very short lines (adjacent cells)

---

## Design Decisions

1. **Immutable CoverResult**: Frozen dataclass for determinism and event logging
2. **Check type parameter**: Supports both LOE (default) and LOS checks
3. **Optimal square selection**: For Large+ creatures, uses closest square to opponent
4. **Proportional scaling**: If total lines ≠ 16, thresholds scale proportionally
5. **No dependency on WorldState**: Pure geometric calculation on BattleGrid

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `aidm/core/cover_resolver.py` | 420 | Cover calculation algorithms |
| `tests/test_cover_resolver.py` | 580 | Comprehensive test suite |

---

## Test Results

```
tests/test_cover_resolver.py: 58 passed in 0.18s
Full suite: 2130 passed, 43 warnings in 9.87s
```

---

## Dependencies

**Uses (from WO-001):**
- `aidm.schemas.geometry.PropertyMask`
- `aidm.schemas.geometry.PropertyFlag`
- `aidm.schemas.geometry.Direction`
- `aidm.schemas.geometry.SizeCategory`
- `aidm.core.geometry_engine.BattleGrid`

**Uses (existing):**
- `aidm.schemas.position.Position`

---

## Known Limitations

1. **2D only**: Height/elevation not factored into cover (deferred to WO-003 LOS/LOE)
2. **No soft cover**: Creatures providing soft cover not implemented (future work)
3. **No improved cover**: Arrow slits and similar structures not distinguished

---

## Next Steps

WO-002 is complete. Recommended next:
- **WO-003**: LOS/LOE Resolution (will add 3D height checks)
- **WO-004**: AoE Rasterization
- **WO-005**: Ranged Attacks (will use this cover system)

---

**Status:** COMPLETE — Awaiting PM review

**Submitted:** 2026-02-11
**Agent:** Sonnet-B
