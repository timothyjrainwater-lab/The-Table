# WO-019 Completion Report: Property-Based Testing

**Agent**: Sonnet-D
**Date**: 2026-02-11
**Status**: COMPLETE

## Summary

Implemented the property-based testing harness ("Thousand-Fold Fireball" pattern) for validating geometric invariants through randomized inputs across 1000 iterations.

## Deliverables

### 1. aidm/testing/property_testing.py (~500 lines)

**PropertyTestHarness** class with:

- `generate_random_grid(seed, size, obstacle_density)` — Create randomized BattleGrid
- `generate_empty_grid(size)` — Create empty grid for symmetry tests
- `generate_random_positions(grid, count, seed)` — Generate valid positions
- `generate_random_aoe(origin, seed)` — Generate random AoE configurations

Property tests implemented:
- `run_thousand_fold_fireball(iterations)` — Random AoE placements never crash, return valid cells
- `run_cover_symmetry_check(iterations)` — Cover geometry is valid and consistent
- `run_los_reflexivity_check(iterations)` — LOS(A, A) always true
- `run_los_symmetry_check(iterations)` — LOS(A, B) == LOS(B, A) in empty grids
- `run_aoe_containment_check(iterations)` — Origin always in burst AoE
- `run_cone_square_count_check(iterations)` — Cardinal cones match triangular formula
- `run_all_property_tests(iterations)` — Execute all tests in suite

**PropertyTestResult** dataclass with:
- Reproducible failure logging (seed, iteration, context)
- Performance timing
- Serialization support

### 2. tests/integration/test_property_based.py (~650 lines)

48 pytest tests organized into:

| Test Class | Tests | Description |
|------------|-------|-------------|
| TestThousandFoldFireball | 5 | Core robustness tests |
| TestCoverSymmetry | 3 | Cover calculation consistency |
| TestLOSReflexivity | 3 | Self-visibility invariant |
| TestLOSSymmetry | 2 | Bidirectional LOS in empty grids |
| TestAoEContainment | 3 | Origin containment for bursts |
| TestDistanceProperties | 5 | Non-negative, symmetric, reflexive distance |
| TestConeSquareCount | 2 | Triangular number formula |
| TestAllPropertyTests | 2 | Suite runner validation |
| TestPropertyTestHarness | 6 | Harness unit tests |
| TestPropertyTestResult | 3 | Result dataclass tests |
| TestEdgeCases | 6 | Edge case validation |
| TestPerformance | 2 | Timing constraints |
| TestRegressions | 6 | Regression guards |

### 3. Test Markers Registered

Added to `pyproject.toml`:
```toml
markers = [
    "property_based: Property-based randomized tests (1000 iterations, optional skipping)",
    "slow: Tests that take more than 1 second to run",
]
```

## Design Decisions

### 1. No Triangle Inequality Tests

The D&D 3.5e 1-2-1-2 diagonal distance intentionally violates the triangle inequality. This is RAW-compliant behavior (PHB p.148):

```
Example: A=(0,0), B=(1,1), C=(2,2)
- dist(A,B) = 5 feet (1 diagonal costs 5)
- dist(B,C) = 5 feet (1 diagonal costs 5)
- dist(A,C) = 15 feet (2 diagonals cost 5+10=15)
- But dist(A,B) + dist(B,C) = 10, and 15 > 10!
```

Instead, we test that distance is:
- Non-negative
- Symmetric (dist(A,B) == dist(B,A))
- Reflexive (dist(A,A) == 0)

### 2. Deterministic Randomness

All tests use `RNGManager` with derived seeds, ensuring:
- Reproducibility from master seed
- Failure cases can be re-run with specific seed
- No dependency on hypothesis or external property testing libraries

### 3. Failure Shrinking

The harness logs minimal failing cases with:
- Seed for exact reproduction
- Iteration number
- Full context (positions, parameters, etc.)

## Test Results

```
Property tests: 48 passed in 22.34s
Baseline tests: 2813 passed in 12.52s (no regressions)
```

Thousand-Fold Fireball runs 1000 iterations across all AoE shapes without crashes.

## Performance

| Test Suite | Iterations | Time |
|------------|------------|------|
| Thousand-Fold Fireball | 1000 | ~2.1s |
| Cover Symmetry | 1000 | ~3.2s |
| LOS Reflexivity | 1000 | ~2.8s |
| LOS Symmetry | 1000 | ~2.4s |
| AoE Containment | 1000 | ~0.3s |
| Cone Square Count | 1000 | ~0.9s |
| **Total (all tests)** | **~6000** | **~22s** |

## Files Created

- `aidm/testing/property_testing.py` (501 lines)
- `tests/integration/test_property_based.py` (650 lines)

## Files Modified

- `pyproject.toml` (added test markers)

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| Thousand-Fold Fireball runs 1000 iterations without crash | ✅ |
| All property invariants hold | ✅ |
| Failing cases logged with reproducible seeds | ✅ |
| Tests marked for optional skipping | ✅ |
| All existing tests pass (2767+) | ✅ (2813 passed) |

## Discovery: Distance Non-Metricity

Property testing revealed that D&D 3.5e distance is not a true metric space — the 1-2-1-2 diagonal pattern violates the triangle inequality. This is documented in the test suite as expected RAW behavior, not a bug.
