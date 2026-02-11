# WO-012 Completion Report: Box-Lens Bridge

**Agent:** Sonnet-F (Claude 4.5 Sonnet)
**Date:** 2026-02-11
**Status:** COMPLETE

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| aidm/core/box_lens_bridge.py | 364 | Integration layer between Box and Lens |
| tests/test_box_lens_bridge.py | 642 | Full test suite (51 tests) |

**Total:** 1006 lines

---

## Test Results

### New Tests: 51 passed
- TestConstruction: 3 tests
- TestEntityClassMapping: 4 tests
- TestEntitySync: 8 tests
- TestCellSync: 5 tests
- TestQueries: 8 tests
- TestValidation: 6 tests
- TestLargeCreatures: 3 tests
- TestRoundTrip: 2 tests
- TestSnapshot: 3 tests
- TestEdgeCases: 5 tests
- TestBoxTierAuthority: 4 tests

### Full Suite Verification
```
2603 passed, 43 warnings in 10.22s
```
**Zero regressions.** All existing tests continue to pass.

---

## Implementation Summary

### BoxLensBridge Class

```python
class BoxLensBridge:
    def __init__(self, grid: BattleGrid, lens: LensIndex)
```

### Sync Functions (Grid → Lens)

1. **sync_entity_to_lens(entity_id, turn)** → bool
   - Reads position and size from grid._entities
   - Stores as BOX-tier facts in Lens
   - Returns False if entity not in grid

2. **sync_all_entities(turn)** → int
   - Syncs all grid entities to Lens
   - Returns count synced

3. **sync_cell_to_lens(pos, turn)** → bool
   - Stores cell_mask, elevation, border_masks as BOX-tier facts
   - Creates cell_x_y entity in Lens
   - Returns False if position out of bounds

4. **sync_grid_to_lens(turn)** → int
   - Syncs all cells in grid
   - Returns count synced

### Query Functions (Lens → Box)

1. **get_entity_size(entity_id)** → Optional[SizeCategory]
   - Queries Lens for size fact
   - Converts string value to enum

2. **get_entity_position(entity_id)** → Optional[Position]
   - Uses Lens spatial index

3. **get_entities_in_area(positions)** → List[str]
   - Uses Lens spatial index
   - Returns deduplicated list

4. **get_cell_properties(pos)** → Optional[PropertyMask]
   - Queries Lens for cell_mask fact

### Validation

**validate_consistency(turn)** → List[str]
- Checks all grid entities exist in Lens
- Checks all Lens entities (non-terrain) exist in grid
- Verifies positions match
- Verifies sizes match
- Returns empty list if consistent

### Entity Class Mapping

| Prefix | Class |
|--------|-------|
| creature_ | creature |
| object_ | object |
| terrain_ | terrain |
| (other) | unknown |

---

## Design Decisions

1. **BOX Tier Authority**: All synced facts use SourceTier.BOX (tier 1) to ensure mechanical facts from the geometric engine override any LLM-generated data from Spark.

2. **Cell Entity IDs**: Cells are stored as entities with IDs following pattern `cell_{x}_{y}` and class "terrain". This allows them to use the same fact storage and query mechanisms.

3. **Top-Left Anchor**: For multi-square creatures (Large+), only the top-left anchor position is stored in Lens, matching BattleGrid's entity tracking.

4. **Terrain Exclusion**: validate_consistency excludes terrain-class entities when checking Lens→Grid consistency, since cell entities only exist in Lens.

5. **Spatial Index Integration**: Positions are stored both as facts (for attribute queries) and in the Lens spatial index (via set_position) for efficient area queries.

---

## Acceptance Criteria Checklist

- [x] All new tests pass (51/51)
- [x] All existing tests pass (2603 total, zero regressions)
- [x] Grid→Lens sync works (entities and cells)
- [x] Lens queries return correct data
- [x] Consistency validation catches issues
- [x] BOX tier authority enforced

---

## Dependencies

- **WO-001** (BattleGrid): Imports from aidm.core.geometry_engine
- **WO-007** (LensIndex): Imports from aidm.core.lens_index

No modifications to existing files were made.

---

## Usage Example

```python
from aidm.core.geometry_engine import BattleGrid
from aidm.core.lens_index import LensIndex
from aidm.core.box_lens_bridge import BoxLensBridge

# Create components
grid = BattleGrid(20, 20)
lens = LensIndex()
bridge = BoxLensBridge(grid, lens)

# Place entities on grid
grid.place_entity("creature_goblin", Position(x=5, y=5), SizeCategory.MEDIUM)

# Sync to Lens
bridge.sync_all_entities(turn=1)

# Query through Lens
pos = bridge.get_entity_position("creature_goblin")
size = bridge.get_entity_size("creature_goblin")

# Validate consistency
errors = bridge.validate_consistency(turn=1)
assert errors == []
```
