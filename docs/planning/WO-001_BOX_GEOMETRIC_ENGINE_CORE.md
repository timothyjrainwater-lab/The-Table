# Work Order: Box Geometric Engine Core

**Work Order ID:** WO-001
**Execution Plan Step:** 1.1
**Assigned To:** TBD (coding agent)
**Priority:** 1 (first work order in execution plan)
**Status:** READY FOR DISPATCH
**Created:** 2026-02-11
**Issued By:** Opus (PM)

---

## Strategic Context

The Box geometric engine is the foundation for all spatial reasoning in the AIDM system. Cover resolution, LOS/LOE checks, AoE rasterization, and ranged attack resolution all depend on this data layer existing first. Currently, the codebase has zero geometric engine code — terrain exists as a flat dict of cells with string keys, and the only ray-casting is a basic 2D Bresenham in `targeting_resolver.py`.

This work order implements the **data structures only** — the uniform grid, property masks, border metadata, and spatial indexing. Algorithms (cover, LOS/LOE, AoE) come in subsequent work orders (WO-002 through WO-004) and build on top of these structures.

**Research basis:** RQ-BOX-001 Findings 1, 2, 6, 7, 10, 11

---

## What Already Exists (DO NOT RECREATE)

| Component | Location | Status |
|-----------|----------|--------|
| `Position` (canonical 2D grid type) | `aidm/schemas/position.py` | Complete — frozen dataclass, integer x/y, `distance_to()`, `is_adjacent_to()` |
| `TerrainCell` schema | `aidm/schemas/terrain.py` | Complete — elevation, movement_cost, terrain_tags, cover_type, hazards |
| `TerrainTag` enum | `aidm/schemas/terrain.py` | Complete — DIFFICULT_TERRAIN, SLIPPERY, WALL_SMOOTH, etc. |
| `CoverType` constants | `aidm/schemas/terrain.py` | Complete — STANDARD, IMPROVED, TOTAL, SOFT |
| `terrain_resolver.py` | `aidm/core/terrain_resolver.py` | Complete — terrain cell lookup, cover checking, hazard resolution |
| `bresenham_line()` | `aidm/core/targeting_resolver.py` | Complete — 2D Bresenham for LOS/LOE |
| `PropertyMask` concept | RQ-BOX-001 Finding 2 | Research only — not yet in code |

**The Position type, TerrainCell schema, and terrain_resolver are locked. This work order adds new modules alongside them, not replacing them.**

---

## Objective

Implement the geometric engine data layer: a uniform grid with per-cell and per-border property masks, spatial entity tracking, and the data structures that cover/LOS/LOE algorithms will query.

---

## Scope

### Deliverable 1: GridCell and PropertyMask Schema

**File:** `aidm/schemas/geometry.py` (new file)

Implement:

1. **PropertyMask** — Uint32 bitmask for cell and border properties:
   - Bit 0: `SOLID` — physically solid, blocks movement
   - Bit 1: `OPAQUE` — blocks visual light (LOS)
   - Bit 2: `PERMEABLE` — allows LOE despite solidity (e.g., grate, arrow slit)
   - Bit 3: `DIFFICULT` — difficult terrain
   - Bit 4: `HAZARDOUS` — environmental hazard present
   - Bit 5: `FLAMMABLE` — catches fire from energy damage
   - Bit 6: `FRAGILE` — takes double damage from impact
   - Bit 7: `CONDUCTIVE` — electricity arcs to adjacent
   - Bit 8: `CRYSTALLINE` — vulnerable to sonic
   - Bit 9: `DENSE` — provides total cover even if damaged
   - Bits 10-31: Reserved

   Must support:
   - `has_flag(flag) -> bool` via bitwise AND
   - `set_flag(flag)` / `clear_flag(flag)` via bitwise OR/AND-NOT
   - `blocks_los() -> bool` — shortcut for `has_flag(OPAQUE) and not has_flag(PERMEABLE)`
   - `blocks_loe() -> bool` — shortcut for `has_flag(SOLID) and not has_flag(PERMEABLE)`
   - `to_int() -> int` / `from_int(val) -> PropertyMask`
   - Frozen/immutable for snapshot safety; mutations return new instance

2. **BorderMask** — Per-edge property mask for the 4 borders of each cell (N, E, S, W):
   - Same bit layout as PropertyMask
   - Represents walls, doors, arrow slits, windows
   - Example: Arrow slit = `SOLID | PERMEABLE` (blocks movement, allows LOE)
   - Example: Glass wall = `SOLID | OPAQUE` inverted — actually `SOLID` only (blocks movement, allows LOS but blocks LOE)

3. **GridCell** — Single cell in the uniform grid:
   - `position: Position` — grid coordinates
   - `cell_mask: PropertyMask` — properties of the cell volume
   - `border_masks: Dict[Direction, PropertyMask]` — N/E/S/W border properties
   - `elevation: int` — height in feet above base level
   - `height: int` — height of contents in feet (for LOS occlusion)
   - `material_mask: int` — material property bits (from Finding 11)
   - `hardness: int` — damage reduction for destructible objects
   - `hit_points: int` — structural integrity (0 = destroyed)
   - `state: CellState` — FSM state (INTACT, DAMAGED, BROKEN, DESTROYED)
   - `occupant_ids: List[str]` — entity IDs occupying this cell

4. **Direction** — Enum for cell borders: `N, E, S, W`

5. **CellState** — Enum for destructibility FSM: `INTACT, DAMAGED, BROKEN, DESTROYED`

6. **SizeCategory** — Enum matching 3.5e: `FINE, DIMINUTIVE, TINY, SMALL, MEDIUM, LARGE, HUGE, GARGANTUAN, COLOSSAL` with `footprint() -> int` method returning squares occupied (1 for Medium and smaller, 4 for Large, 9 for Huge, 16 for Gargantuan, 25+ for Colossal)

### Deliverable 2: BattleGrid Data Structure

**File:** `aidm/core/geometry_engine.py` (new file)

Implement:

1. **BattleGrid** — The uniform grid data structure:
   - Constructor: `BattleGrid(width: int, height: int)` — creates empty grid
   - Internal storage: flat array of GridCell indexed by `y * width + x` for cache-friendly access
   - `get_cell(pos: Position) -> GridCell` — O(1) direct access
   - `set_cell(pos: Position, cell: GridCell) -> None`
   - `get_border(pos: Position, direction: Direction) -> PropertyMask` — border between pos and neighbor
   - `set_border(pos: Position, direction: Direction, mask: PropertyMask) -> None` — must also update the reciprocal border (pos.N == neighbor.S)
   - `in_bounds(pos: Position) -> bool`
   - `get_neighbors(pos: Position) -> List[Position]` — 8-directional, bounds-checked
   - `get_occupants(pos: Position) -> List[str]` — entity IDs at position
   - `snapshot() -> BattleGrid` — deep copy for snapshot phase of resolve loop

2. **Entity spatial tracking:**
   - `place_entity(entity_id: str, pos: Position, size: SizeCategory) -> None`
   - `remove_entity(entity_id: str) -> None`
   - `move_entity(entity_id: str, new_pos: Position) -> None`
   - `get_entity_position(entity_id: str) -> Optional[Position]`
   - `get_entities_in_area(positions: List[Position]) -> List[str]`
   - Internal dict: `entity_id -> (Position, SizeCategory)` for reverse lookup
   - Large creatures occupy multiple cells; `place_entity` must update all occupied cells

3. **Factory / conversion:**
   - `from_terrain_map(terrain_map: Dict, entities: Dict) -> BattleGrid` — converts existing `world_state.active_combat["terrain_map"]` format to BattleGrid. This is the bridge between old and new systems.
   - Maps TerrainCell properties to PropertyMask bits:
     - `cover_type == 'total'` → SOLID + OPAQUE
     - `terrain_tags contains 'WALL_SMOOTH' or 'WALL_ROUGH'` → SOLID + OPAQUE on cell
     - `terrain_tags contains 'DIFFICULT_TERRAIN'` → DIFFICULT
     - `terrain_tags contains 'DEEP_WATER'` → DIFFICULT + HAZARDOUS
     - Elevation preserved directly

### Deliverable 3: Tests

**File:** `tests/test_geometry_engine.py` (new file)

Required test coverage:

1. **PropertyMask tests:**
   - Bit flag set/get/clear round-trip
   - `blocks_los()` / `blocks_loe()` for all barrier types from RQ-BOX-001 Finding 4 table:
     - Stone wall: SOLID+OPAQUE → blocks both
     - Glass wall: SOLID only → blocks LOE, not LOS
     - Magical darkness: OPAQUE+PERMEABLE → blocks LOS, not LOE
     - Iron grate: SOLID+PERMEABLE → blocks neither (both have escape via PERMEABLE)
   - Immutability (mutations return new instance)
   - `to_int()` / `from_int()` round-trip

2. **GridCell tests:**
   - Border reciprocity (setting N border on cell also sets S border on neighbor)
   - Direction enum completeness
   - CellState FSM transitions (INTACT→DAMAGED→BROKEN→DESTROYED)
   - Occupant tracking (add/remove)

3. **BattleGrid tests:**
   - Construction with dimensions
   - O(1) cell access by position
   - Bounds checking
   - Entity placement (single cell for Medium, multi-cell for Large+)
   - Entity removal cleans all occupied cells
   - Entity movement updates old and new cells
   - `get_neighbors()` at corners/edges returns correct subset
   - `get_entities_in_area()` returns correct entity set
   - `snapshot()` produces independent deep copy (mutation isolation)

4. **Conversion tests:**
   - `from_terrain_map()` correctly maps existing terrain format to BattleGrid
   - WALL_SMOOTH terrain tag → SOLID+OPAQUE on cell mask
   - DIFFICULT_TERRAIN → DIFFICULT flag
   - Elevation preserved
   - Entity positions populated from entities dict

5. **SizeCategory tests:**
   - Footprint values match 3.5e PHB (Medium=1, Large=4, Huge=9, etc.)
   - Large creature placement occupies correct 2x2 cells

---

## Design Constraints

1. **Deterministic** — No floating point. All integer arithmetic. Same inputs → same outputs.
2. **Pure functions where possible** — BattleGrid is mutable (it's the state container), but query methods must not mutate.
3. **Schema-first** — All data types are dataclasses with `to_dict()` / `from_dict()` for serialization.
4. **Position type** — Use `aidm.schemas.position.Position` exclusively. Do not create alternate coordinate types.
5. **No rendering** — This is a data layer. No visualization, no display logic.
6. **Backward compatible** — The `from_terrain_map()` factory bridges old format. Existing terrain_resolver.py continues to work unchanged. The geometric engine is additive.
7. **Python pure** — No C extensions, no numpy in this work order. Performance optimization is a later decision point.

---

## Integration Points

- **Position type**: Import from `aidm.schemas.position`
- **TerrainCell/TerrainTag**: Import from `aidm.schemas.terrain` for conversion
- **terrain_resolver.py**: Not modified. BattleGrid reads from the same terrain_map data.
- **targeting_resolver.py**: Future WO-002/003 will make this query BattleGrid instead of raw terrain dicts. Not in this WO scope.
- **aoo.py**: Future WO will generalize `get_threatened_squares()` using BattleGrid. Not in this WO scope.

---

## Acceptance Criteria

1. All new tests pass
2. All existing 2003 tests continue to pass (zero regressions)
3. PropertyMask correctly resolves all 4 barrier types from RQ-BOX-001 Finding 4 table
4. BattleGrid supports grids up to 100x100 (10,000 cells)
5. `from_terrain_map()` successfully converts existing test terrain data
6. Border reciprocity is enforced (cannot have inconsistent adjacent borders)
7. Large creature multi-cell placement works correctly
8. `snapshot()` produces a fully independent copy

---

## Out of Scope (Explicitly)

- Cover resolution algorithms (WO-002)
- LOS/LOE ray-casting algorithms (WO-003)
- AoE rasterization (WO-004)
- Ranged attack mechanics (WO-005)
- Height-aware 3D voxel traversal (WO-003)
- Intra-tile positioning for Tiny creatures (deferred)
- Hierarchical bitmasks for multi-level dungeons (deferred — not needed for target scale)
- Action Grid / Dijkstra pathing (deferred)

---

## Research References

| Finding | Topic | Relevance to This WO |
|---------|-------|---------------------|
| RQ-BOX-001 F1 | Data-Oriented Design, SoA layout | Informs BattleGrid internal storage |
| RQ-BOX-001 F2 | Discrete Metadata, PropertyMask Uint32 | Direct implementation target |
| RQ-BOX-001 F6 | Deterministic FSMs for environmental change | CellState enum and transitions |
| RQ-BOX-001 F7 | Spatial Querying and Indexing | BattleGrid as uniform grid with O(1) access |
| RQ-BOX-001 F10 | Border metadata, 1-square-foot rule | BorderMask per-edge properties |
| RQ-BOX-001 F11 | Material bitmasks | material_mask field on GridCell |
