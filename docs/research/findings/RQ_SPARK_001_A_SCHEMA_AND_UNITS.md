# RQ-SPARK-001-A: Scene Fact Pack Schema + Units/Defaults

**Research Question:** Define the structured JSON schema for scenes emitted by Spark and ingested by Lens, plus the unit policy, archetype defaults, unknown-handling protocol, and detail drift prevention strategy.

**Date:** 2026-02-11
**Status:** COMPLETE
**Codebase Compatibility:** Verified against `aidm/schemas/geometry.py`, `aidm/schemas/position.py`, `aidm/core/fact_acquisition.py`, `aidm/core/lens_index.py`, `aidm/core/box_lens_bridge.py`

---

## Table of Contents

1. [Scene Fact Pack JSON Schema](#1-scene-fact-pack-json-schema)
2. [Unit Policy](#2-unit-policy)
3. [Archetype Default Table](#3-archetype-default-table)
4. [Unknown-Handling Protocol](#4-unknown-handling-protocol)
5. [Detail Drift Prevention Strategy](#5-detail-drift-prevention-strategy)
6. [Recommendations for Implementation](#6-recommendations-for-implementation)
7. [Appendix A: D&D 3.5e Size Category Reference](#appendix-a-dd-35e-size-category-reference)
8. [Appendix B: PropertyFlag Mapping](#appendix-b-propertyflag-mapping)
9. [Appendix C: Full Example Scene Fact Pack](#appendix-c-full-example-scene-fact-pack)

---

## 1. Scene Fact Pack JSON Schema

### 1.1 Design Principles

1. **Spark emits, Lens validates, Box adjudicates.** The schema is an emission contract: Spark produces it, Lens validates against it, and Box consumes the geometric data to populate `BattleGrid`.
2. **All spatial data maps to existing Box primitives.** Positions map to `Position(x, y)`, sizes map to `SizeCategory`, property flags map to `PropertyFlag` bitmask, and cell state maps to `CellState` FSM.
3. **Boolean flags, never prose.** Affordances like "flammable" or "provides_cover" are boolean flags that Lens can deterministically map to `PropertyFlag` bits. No natural language in mechanical fields.
4. **Required vs Optional per object class.** Missing optional fields get archetype defaults (Section 3). Missing required fields cause Lens rejection.
5. **Pydantic-validatable.** Every field has an explicit type, constrained range, and documented semantics.

### 1.2 Top-Level Schema

```json
{
  "$schema": "scene_fact_pack_v1",
  "scene_id": "string (required, unique identifier)",
  "scene_version": "integer (required, monotonic, starts at 1)",
  "provenance": "SPARK_GENERATED",
  "metadata": {
    "tags": ["string"],
    "biome": "string (enum)",
    "indoors": "boolean",
    "lighting": "string (enum: bright | dim | dark | magical_dark)",
    "time_of_day": "string (enum: dawn | morning | midday | afternoon | dusk | evening | night | midnight)",
    "theme": "string (optional, freeform narrative hint)"
  },
  "dimensions": {
    "width_sq": "integer (required, grid squares, 1-100)",
    "height_sq": "integer (required, grid squares, 1-100)"
  },
  "objects": [ "...SceneObject" ],
  "creatures": [ "...SceneCreature" ],
  "terrain_zones": [ "...TerrainZone" ],
  "borders": [ "...BorderOverride" ]
}
```

### 1.3 SceneObject Schema

Each object occupies one or more grid cells and maps to `GridCell` properties in the `BattleGrid`.

```json
{
  "object_id": "string (required, unique within scene)",
  "class": "string (required, archetype key e.g. 'tavern_table', 'wooden_door')",
  "name": "string (optional, display name, default = class prettified)",
  "material": "string (required, enum: wood | stone | iron | steel | glass | cloth | bone | crystal | earth | ice)",

  "dimensions": {
    "length_ft": "number | 'UNKNOWN' (required)",
    "width_ft": "number | 'UNKNOWN' (required)",
    "height_ft": "number | 'UNKNOWN' (required)"
  },
  "weight_lb": "number | 'UNKNOWN' (optional)",

  "position": {
    "x": "integer (required, grid square 0-indexed)",
    "y": "integer (required, grid square 0-indexed)"
  },
  "footprint_sq": {
    "width": "integer (optional, grid squares, default=ceil(length_ft/5))",
    "height": "integer (optional, grid squares, default=ceil(width_ft/5))"
  },
  "elevation_ft": "integer (optional, default=0, feet above floor)",
  "facing": "string (optional, enum: N | E | S | W | NE | NW | SE | SW, default=N)",

  "solidity": "boolean (required, maps to PropertyFlag.SOLID)",
  "opacity": "boolean (required, maps to PropertyFlag.OPAQUE)",
  "permeability": "boolean (optional, default=false, maps to PropertyFlag.PERMEABLE)",

  "mobility": "string (required, enum: fixed | movable | portable)",

  "condition": "string (required, enum: intact | damaged | broken | destroyed)",
  "hardness": "integer (optional, D&D 3.5e material hardness, default by material)",
  "hit_points": "integer (optional, structural HP, default by material+size)",

  "affordances": {
    "flammable": "boolean (default by material)",
    "climbable": "boolean (default=false)",
    "provides_cover": "boolean (derived: true if solidity=true)",
    "blocks_los": "boolean (derived: true if opacity=true AND permeability=false)",
    "difficult_terrain": "boolean (default=false)",
    "fragile": "boolean (default=false)",
    "conductive": "boolean (default by material)",
    "crystalline": "boolean (default by material)",
    "dense": "boolean (default=false)"
  }
}
```

**Required fields:** `object_id`, `class`, `material`, `dimensions` (all three sub-fields), `position`, `solidity`, `opacity`, `mobility`, `condition`

**Optional fields:** `name`, `weight_lb`, `footprint_sq`, `elevation_ft`, `facing`, `permeability`, `hardness`, `hit_points`, all `affordances` sub-fields

**Field validation rules:**

| Field | Type | Range/Constraint |
|-------|------|-----------------|
| `object_id` | string | Non-empty, unique within scene |
| `class` | string | Non-empty, should match archetype registry |
| `material` | string | One of defined material enum values |
| `dimensions.length_ft` | number or "UNKNOWN" | > 0 if numeric |
| `dimensions.width_ft` | number or "UNKNOWN" | > 0 if numeric |
| `dimensions.height_ft` | number or "UNKNOWN" | > 0 if numeric |
| `weight_lb` | number or "UNKNOWN" | >= 0 if numeric |
| `position.x` | integer | 0 <= x < scene.dimensions.width_sq |
| `position.y` | integer | 0 <= y < scene.dimensions.height_sq |
| `elevation_ft` | integer | >= 0 |
| `hardness` | integer | >= 0 |
| `hit_points` | integer | >= 0 |
| `condition` | string | One of: intact, damaged, broken, destroyed |
| `mobility` | string | One of: fixed, movable, portable |

### 1.4 SceneCreature Schema

Creatures map to entity placement in `BattleGrid` via `place_entity(entity_id, Position, SizeCategory)`.

```json
{
  "creature_id": "string (required, unique within scene)",
  "name": "string (required, display name)",
  "size": "string (required, enum: fine | diminutive | tiny | small | medium | large | huge | gargantuan | colossal)",

  "space_ft": "integer (required, occupied space in feet per side)",
  "reach_ft": "integer (required, natural reach in feet)",

  "position": {
    "x": "integer (required, grid square, top-left for Large+)",
    "y": "integer (required, grid square, top-left for Large+)"
  },
  "elevation_ft": "integer (optional, default=0)",

  "stance": "string (optional, enum: standing | prone | kneeling | flying | swimming, default=standing)",

  "geometry_equipment": [
    {
      "item": "string (e.g. 'tower_shield', 'reach_weapon')",
      "effect": "string (enum: extra_cover | extended_reach | blocks_los_directional)"
    }
  ],

  "team": "string (optional, e.g. 'hostile', 'ally', 'neutral')"
}
```

**Required fields:** `creature_id`, `name`, `size`, `space_ft`, `reach_ft`, `position`

**Optional fields:** `elevation_ft`, `stance`, `geometry_equipment`, `team`

**D&D 3.5e size-to-space/reach mapping (PHB p.149, DMG p.29):**

| Size | Space (ft) | Space (sq) | Natural Reach (ft) | Tall Reach (ft) | Long Reach (ft) |
|------|-----------|-----------|-------------------|-----------------|-----------------|
| Fine | 0.5 | 1* | 0 | 0 | 0 |
| Diminutive | 1 | 1* | 0 | 0 | 0 |
| Tiny | 2.5 | 1* | 0 | 0 | 0 |
| Small | 5 | 1 | 5 | 5 | 5 |
| Medium | 5 | 1 | 5 | 5 | 5 |
| Large | 10 | 2 | 10 | 10 | 5 |
| Huge | 15 | 3 | 15 | 15 | 10 |
| Gargantuan | 20 | 4 | 20 | 20 | 15 |
| Colossal | 30** | 5 | 30** | 30** | 20 |

*Fine/Diminutive/Tiny share squares; engine treats as 1 square.
**Colossal space is 30ft (6 squares actual) but engine uses 25 squares (5x5) per `SizeCategory.footprint()`.

**Validation:** Lens cross-checks `space_ft` against `size` using the table above. Mismatches are rejected.

### 1.5 TerrainZone Schema

Terrain zones paint `PropertyFlag` masks onto rectangular regions of the grid.

```json
{
  "zone_id": "string (required, unique within scene)",
  "zone_type": "string (required, enum: difficult | hazardous | water_shallow | water_deep | pit | rubble | ice | lava | magical)",
  "region": {
    "x": "integer (required, top-left grid square)",
    "y": "integer (required, top-left grid square)",
    "width_sq": "integer (required, squares)",
    "height_sq": "integer (required, squares)"
  },
  "elevation_ft": "integer (optional, override for all cells in zone)",
  "flags": {
    "difficult_terrain": "boolean",
    "hazardous": "boolean",
    "solid": "boolean",
    "opaque": "boolean"
  },
  "description": "string (optional, narrative-only, not consumed by Box)"
}
```

### 1.6 BorderOverride Schema

Explicit border overrides for walls, doors, arrow slits, etc. Maps directly to `BattleGrid.set_border(pos, direction, mask)`.

```json
{
  "border_id": "string (required, unique within scene)",
  "position": {
    "x": "integer (required)",
    "y": "integer (required)"
  },
  "direction": "string (required, enum: N | E | S | W)",
  "solid": "boolean (required)",
  "opaque": "boolean (required)",
  "permeable": "boolean (optional, default=false)",
  "object_ref": "string (optional, object_id of door/wall this border represents)"
}
```

**Note:** Border reciprocity is enforced by `BattleGrid`, not by Spark. Setting the North border of cell (5,5) automatically sets the South border of cell (5,4). Spark only needs to declare one side.

### 1.7 Metadata Enums

**Biome values:**
`cavern`, `dungeon`, `forest`, `mountain`, `plains`, `swamp`, `desert`, `coastal`, `urban`, `underground`, `planar`, `aquatic`

**Lighting values:**
`bright` (normal torch/daylight), `dim` (shadowy, 20% miss chance concealment), `dark` (no light, effective blindness), `magical_dark` (darkness spell, OPAQUE+PERMEABLE)

**Time of day values:**
`dawn`, `morning`, `midday`, `afternoon`, `dusk`, `evening`, `night`, `midnight`

### 1.8 Mapping to Box Primitives

| Scene Fact Pack Field | Box Primitive | Conversion |
|----------------------|---------------|------------|
| `object.position` | `Position(x, y)` | Direct mapping |
| `object.solidity` | `PropertyFlag.SOLID` | `cell_mask.set_flag(SOLID)` if true |
| `object.opacity` | `PropertyFlag.OPAQUE` | `cell_mask.set_flag(OPAQUE)` if true |
| `object.permeability` | `PropertyFlag.PERMEABLE` | `cell_mask.set_flag(PERMEABLE)` if true |
| `object.affordances.flammable` | `PropertyFlag.FLAMMABLE` | `cell_mask.set_flag(FLAMMABLE)` if true |
| `object.affordances.fragile` | `PropertyFlag.FRAGILE` | Flag on cell |
| `object.affordances.conductive` | `PropertyFlag.CONDUCTIVE` | Flag on cell |
| `object.affordances.crystalline` | `PropertyFlag.CRYSTALLINE` | Flag on cell |
| `object.affordances.dense` | `PropertyFlag.DENSE` | Flag on cell |
| `object.affordances.difficult_terrain` | `PropertyFlag.DIFFICULT` | Flag on cell |
| `object.affordances.provides_cover` | Derived from SOLID | Used by `cover_resolver.py` |
| `object.affordances.blocks_los` | Derived from OPAQUE+PERMEABLE | Used by `los_resolver.py` |
| `object.condition` | `CellState` enum | Direct mapping to FSM state |
| `object.hardness` | `GridCell.hardness` | Direct |
| `object.hit_points` | `GridCell.hit_points` | Direct |
| `object.dimensions.height_ft` | `GridCell.height` | Used for LOS occlusion |
| `object.elevation_ft` | `GridCell.elevation` | Height above base |
| `creature.size` | `SizeCategory` enum | Direct mapping |
| `creature.position` | `Position(x, y)` | `BattleGrid.place_entity()` |
| `border.direction` | `Direction` enum | `BattleGrid.set_border()` |
| `border.solid/opaque/permeable` | `PropertyMask` on border | Border-level flags |

---

## 2. Unit Policy

### 2.1 Canonical Units

| Measurement | Unit | Rationale |
|------------|------|-----------|
| Linear distance | **feet (ft)** | D&D 3.5e standard (PHB, DMG, MM) |
| Grid position | **squares** (1 square = 5 ft) | `Position(x, y)` uses integer square indices |
| Height / elevation | **feet (ft)** | `GridCell.elevation` and `GridCell.height` in feet |
| Weight | **pounds (lb)** | D&D 3.5e standard |
| Area of Effect radii | **feet (ft)** | `AoEResult` uses feet, rasterized to squares |
| Reach | **feet (ft)** | Consistent with PHB reach tables |
| Dimensions (L/W/H) | **feet (ft)** | Object physical size |

### 2.2 Conversion Constants

```
1 square = 5 feet
1 foot = 0.2 squares (never use fractional squares in grid coords)
Grid coords: integer only (0-indexed)
Elevation: integer feet (no fractional feet)
Object dimensions: may use 0.5-foot increments (e.g., door width = 0.5 ft for thickness)
```

### 2.3 Forbidden Patterns

| Pattern | Violation | Correct |
|---------|-----------|---------|
| `"distance": "3 meters"` | Metric units | `"distance_ft": 10` |
| `"height": "6 feet"` | String with unit | `"height_ft": 6` |
| `"position": {"x": 2.5, "y": 3}` | Fractional grid coord | `"position": {"x": 2, "y": 3}` |
| `"weight": "50 kg"` | Metric weight | `"weight_lb": 110` |
| `"reach": "2 squares"` | Squares for reach | `"reach_ft": 10` |
| `"size": "medium-large"` | Invented category | `"size": "large"` |
| `"elevation": 7.5` | Fractional elevation | `"elevation_ft": 7` or `"elevation_ft": 8` |

### 2.4 Field Naming Convention

All numeric fields that carry units MUST include the unit suffix:

- `*_ft` for feet (e.g., `length_ft`, `height_ft`, `reach_ft`, `elevation_ft`)
- `*_lb` for pounds (e.g., `weight_lb`)
- `*_sq` for grid squares (e.g., `width_sq`, `height_sq` in scene dimensions)

Fields that are pure grid coordinates (`position.x`, `position.y`) are unitless integers representing square indices.

---

## 3. Archetype Default Table

When Spark emits `"UNKNOWN"` for a dimension, or omits an optional field, Lens substitutes the archetype default for the object's `class`. All values below are sourced from D&D 3.5e rulebooks (DMG p.59-62, PHB equipment tables, Stronghold Builder's Guidebook) or reasonable physical approximation where no RAW exists.

### 3.1 Furniture & Tavern Objects

| Class Key | L (ft) | W (ft) | H (ft) | Weight (lb) | Material | Hardness | HP | Solid | Opaque | Mobility | Notes |
|-----------|--------|--------|--------|-------------|----------|----------|----|-------|--------|----------|-------|
| `tavern_table` | 3 | 3 | 2.5 | 60 | wood | 5 | 15 | true | false | movable | Common 4-person table |
| `tavern_table_long` | 8 | 3 | 2.5 | 120 | wood | 5 | 25 | true | false | movable | Long communal table |
| `bar_counter` | 8 | 2 | 3.5 | 200 | wood | 5 | 30 | true | true | fixed | Tavern bar, provides cover |
| `bar_stool` | 1 | 1 | 3 | 10 | wood | 5 | 5 | false | false | portable | Does not block movement |
| `chair_wooden` | 1.5 | 1.5 | 3 | 15 | wood | 5 | 7 | false | false | portable | |
| `bench_wooden` | 5 | 1.5 | 1.5 | 40 | wood | 5 | 12 | false | false | movable | |
| `bed_single` | 6 | 3 | 2 | 80 | wood | 5 | 15 | true | false | movable | Provides prone cover |
| `bed_double` | 6 | 5 | 2 | 120 | wood | 5 | 20 | true | false | fixed | |
| `wardrobe` | 3 | 2 | 6 | 100 | wood | 5 | 20 | true | true | fixed | Blocks LOS |
| `chest_wooden` | 2 | 1.5 | 1.5 | 25 | wood | 5 | 15 | true | true | movable | |
| `bookshelf` | 4 | 1 | 6 | 80 | wood | 5 | 20 | true | true | fixed | |
| `fireplace` | 5 | 2 | 4 | 500 | stone | 8 | 60 | true | true | fixed | HAZARDOUS if lit |

### 3.2 Dungeon Architecture

| Class Key | L (ft) | W (ft) | H (ft) | Weight (lb) | Material | Hardness | HP | Solid | Opaque | Mobility | Notes |
|-----------|--------|--------|--------|-------------|----------|----------|----|-------|--------|----------|-------|
| `wooden_door` | 3 | 0.5 | 7 | 30 | wood | 5 | 10 | true | true | fixed | DMG p.60 simple wooden |
| `wooden_door_strong` | 3 | 1 | 7 | 50 | wood | 5 | 20 | true | true | fixed | DMG p.60 good wooden |
| `iron_door` | 3 | 1 | 7 | 200 | iron | 10 | 60 | true | true | fixed | DMG p.60 |
| `stone_door` | 3 | 2 | 7 | 500 | stone | 8 | 60 | true | true | fixed | DMG p.60 |
| `portcullis` | 5 | 0.5 | 7 | 300 | iron | 10 | 30 | true | false | fixed | PERMEABLE (LOS through gaps) |
| `stone_pillar` | 2 | 2 | 10 | 800 | stone | 8 | 80 | true | true | fixed | Provides cover |
| `stone_pillar_wide` | 3 | 3 | 10 | 1500 | stone | 8 | 120 | true | true | fixed | Large support column |
| `stone_wall_section` | 5 | 1 | 8 | 1200 | stone | 8 | 90 | true | true | fixed | Freestanding wall segment |
| `arrow_slit` | 1 | 1 | 3 | 0 | stone | 8 | 50 | true | false | fixed | PERMEABLE, provides cover |

### 3.3 Miscellaneous Dungeon Objects

| Class Key | L (ft) | W (ft) | H (ft) | Weight (lb) | Material | Hardness | HP | Solid | Opaque | Mobility | Notes |
|-----------|--------|--------|--------|-------------|----------|----------|----|-------|--------|----------|-------|
| `barrel` | 2 | 2 | 3 | 30 | wood | 5 | 12 | true | true | movable | Can be used as cover |
| `crate_small` | 2 | 2 | 2 | 20 | wood | 5 | 10 | true | true | movable | |
| `crate_large` | 3 | 3 | 3 | 40 | wood | 5 | 15 | true | true | movable | |
| `sarcophagus` | 7 | 3 | 3 | 600 | stone | 8 | 40 | true | true | fixed | |
| `altar_stone` | 5 | 3 | 3 | 400 | stone | 8 | 50 | true | true | fixed | |
| `statue_medium` | 2 | 2 | 6 | 300 | stone | 8 | 40 | true | true | fixed | Medium humanoid statue |
| `weapon_rack` | 4 | 1 | 6 | 40 | wood | 5 | 12 | false | false | fixed | Does not block movement |
| `torch_sconce` | 0.5 | 0.5 | 1 | 2 | iron | 10 | 5 | false | false | fixed | Mounted, FLAMMABLE if lit |
| `rubble_pile` | 5 | 5 | 3 | 500 | stone | 8 | 0 | false | false | fixed | DIFFICULT terrain, no HP |
| `ladder_wooden` | 1 | 0.5 | 10 | 20 | wood | 5 | 10 | false | false | movable | CLIMBABLE |
| `rope_bridge` | 10 | 3 | 0 | 30 | cloth | 0 | 8 | false | false | fixed | DIFFICULT, CLIMBABLE |

### 3.4 Material Default Lookup

When Spark specifies a material but not hardness/HP, Lens uses DMG p.59 material defaults:

| Material | Hardness | HP per inch thickness | Flammable | Conductive | Crystalline |
|----------|----------|----------------------|-----------|------------|-------------|
| `wood` | 5 | 10 | true | false | false |
| `stone` | 8 | 15 | false | false | false |
| `iron` | 10 | 30 | false | true | false |
| `steel` | 10 | 30 | false | true | false |
| `glass` | 1 | 1 | false | false | true |
| `cloth` | 0 | 2 | true | false | false |
| `bone` | 6 | 10 | false | false | false |
| `crystal` | 3 | 5 | false | false | true |
| `earth` | 2 | 5 | false | false | false |
| `ice` | 0 | 3 | false | false | true |

**HP Calculation:** `HP = (HP_per_inch * thickness_inches)` where `thickness_inches = width_ft * 12`. For non-wall objects, use the shortest dimension as "effective thickness."

---

## 4. Unknown-Handling Protocol

### 4.1 The UNKNOWN Sentinel

When Spark lacks certainty about a numeric dimension, it MUST emit the string `"UNKNOWN"` instead of guessing.

```json
{
  "object_id": "mysterious_chest_01",
  "class": "chest_wooden",
  "material": "wood",
  "dimensions": {
    "length_ft": "UNKNOWN",
    "width_ft": "UNKNOWN",
    "height_ft": "UNKNOWN"
  },
  "position": {"x": 5, "y": 3},
  "solidity": true,
  "opacity": true,
  "mobility": "movable",
  "condition": "intact"
}
```

### 4.2 Lens UNKNOWN Resolution Pipeline

```
Spark emits "UNKNOWN"
    |
    v
Lens receives field value
    |
    v
Is value "UNKNOWN"?
    |--- No ---> Validate numeric range, accept if valid
    |
    v (Yes)
Lookup archetype by object.class
    |
    v
Archetype found?
    |--- No ---> Reject scene (missing archetype = schema error)
    |
    v (Yes)
Substitute archetype default
    |
    v
Tag fact as ASSUMED_STANDARD in LensFact provenance
    |
    v
Store with SourceTier.DEFAULT
```

### 4.3 Provenance Labels for Dimension Values

Every dimension stored in Lens gets a provenance tag indicating its origin:

| Tag | Meaning | SourceTier | Mutable? |
|-----|---------|-----------|----------|
| `SPARK_GENERATED` | Spark provided an explicit numeric value | `SPARK` | Only by higher-tier source |
| `ASSUMED_STANDARD` | Value came from archetype default table (Spark said UNKNOWN) | `DEFAULT` | Overridable by SPARK or higher |
| `BOX_CANONICAL` | Box set or overrode the value (e.g., after structural damage) | `BOX` | Only by BOX |

### 4.4 Rules for UNKNOWN Emission

**Spark MUST emit UNKNOWN when:**
- The scene description does not specify the dimension
- The object is unfamiliar or non-standard
- Spark would need to fabricate a number with no basis

**Spark MUST NOT emit UNKNOWN for:**
- `position` (x, y) -- position is always required; if Spark cannot place it, omit the object
- `size` (creature size category) -- this is a required D&D 3.5e classification
- `solidity`, `opacity` -- these are boolean and always determinable from context
- `condition` -- always required, default to "intact" if unsure

**Spark MAY emit UNKNOWN for:**
- `dimensions.length_ft`, `dimensions.width_ft`, `dimensions.height_ft`
- `weight_lb`
- `hardness`, `hit_points`
- `elevation_ft`

### 4.5 Prompt Engineering for UNKNOWN Discipline

The system prompt for Spark MUST include these instructions:

```
UNIT RULES:
- All distances in feet. All grid positions in squares (1 square = 5 feet).
- Heights and elevations in feet. Weights in pounds.
- Never use metric units. Never mix units.

UNKNOWN DISCIPLINE:
- If you do not know the exact dimensions of an object, emit "UNKNOWN" as the field value.
- Do NOT guess dimensions. "UNKNOWN" triggers safe archetype defaults.
- A wrong number is worse than "UNKNOWN" because it becomes a cached fact.
- You MUST provide: position, size (creatures), solidity, opacity, condition.
- You MAY emit "UNKNOWN" for: dimensions, weight, hardness, hit_points, elevation.
```

---

## 5. Detail Drift Prevention Strategy

### 5.1 The Problem

If Spark regenerates the same scene (e.g., player re-enters a room), dimensions and positions must not shift. A table that was 3x3 ft in the first generation must remain 3x3 ft in the second. This is "detail drift" -- the tendency of LLMs to produce slightly different outputs on repeated prompts.

### 5.2 Strategy: Lens-Side First-Seen Cache

**Core principle:** Lens caches the first successfully ingested value for every field of every object. On subsequent Spark emissions for the same scene, Lens compares and enforces consistency.

#### 5.2.1 Cache Architecture

```
SceneCache = Dict[scene_id, Dict[object_id, Dict[field_path, CachedValue]]]

CachedValue:
  value: Any           # The first-seen value
  source: str          # SPARK_GENERATED | ASSUMED_STANDARD | BOX_CANONICAL
  turn_cached: int     # When first stored
  frozen: bool         # True for BOX_CANONICAL values (never overridable)
```

#### 5.2.2 Ingestion Protocol (On Scene Re-Emission)

```
For each field in new Spark emission:
    |
    v
Is field in cache for this scene_id + object_id?
    |
    |--- No ---> Accept value, store in cache, proceed
    |
    v (Yes, cached value exists)
    |
Does new value match cached value?
    |
    |--- Yes ---> Accept (no drift)
    |
    v (No, values differ)
    |
Is cached value BOX_CANONICAL?
    |
    |--- Yes ---> REJECT new value, keep cache. Log drift attempt.
    |
    v (Not BOX_CANONICAL)
    |
Is cached value SPARK_GENERATED and new value SPARK_GENERATED?
    |
    |--- Yes ---> REJECT new value, keep first-seen. Log drift.
    |
    v
Is cached value ASSUMED_STANDARD and new value SPARK_GENERATED?
    |
    |--- Yes ---> ACCEPT upgrade. Spark is providing better data.
    |             Update cache, change provenance to SPARK_GENERATED.
    |
    v
REJECT. Log warning.
```

#### 5.2.3 Drift Logging

Every rejected drift attempt is logged:

```json
{
  "event": "DETAIL_DRIFT_REJECTED",
  "scene_id": "tavern_ground_floor",
  "object_id": "main_table_01",
  "field": "dimensions.length_ft",
  "cached_value": 3,
  "cached_source": "SPARK_GENERATED",
  "new_value": 4,
  "new_source": "SPARK_GENERATED",
  "action": "KEPT_CACHED"
}
```

#### 5.2.4 Cache Lifetime

- Scene cache persists for the lifetime of the session
- On session save, cache is serialized with the session state
- Cache is loaded on session restore
- Cache entries are only deleted when:
  - A scene is explicitly destroyed/collapsed (e.g., cave-in)
  - Box issues a `BOX_CANONICAL` override (e.g., wall destroyed in combat)
  - DM explicitly resets a scene (admin action)

### 5.3 Strategy: Seed-Pinned Regeneration

For `json_mode` structured output, Spark requests include a `seed` parameter derived from the scene_id:

```python
seed = hash(scene_id) % (2**31)
```

This increases (but does not guarantee) output stability for the same prompt. The Lens cache is the authoritative drift prevention; seed pinning is a supplementary measure.

### 5.4 Strategy: Scene Diff Protocol

When Spark re-emits a scene, Lens performs a field-by-field diff rather than wholesale replacement:

1. **New objects** (object_id not in cache): Accept and cache
2. **Missing objects** (object_id in cache but not in new emission): Keep cached version (object still exists)
3. **Modified objects** (object_id in both): Apply per-field drift check (5.2.2)
4. **Position changes**: Only accepted if Box has not placed the entity on the grid. Once an entity is on the `BattleGrid`, position is BOX_CANONICAL.

### 5.5 Anti-Pattern: Full Scene Replacement

Lens MUST NOT do full scene replacement on re-emission. This would:
- Lose BOX_CANONICAL overrides (destroyed walls, moved furniture)
- Allow drift on every field
- Break entity tracking (creatures may have moved since scene creation)

---

## 6. Recommendations for Implementation

### 6.1 Implementation Order

1. **Define Pydantic models** for `SceneFactPack`, `SceneObject`, `SceneCreature`, `TerrainZone`, `BorderOverride` in a new `aidm/schemas/scene_fact_pack.py`
2. **Implement archetype registry** as a frozen dict in `aidm/schemas/archetype_defaults.py` containing the default table from Section 3
3. **Implement UNKNOWN resolution** in the Lens ingestion pipeline, mapping `"UNKNOWN"` to archetype lookups
4. **Implement scene cache** in `aidm/core/scene_cache.py` with first-seen semantics
5. **Implement scene-to-grid converter** in `aidm/core/scene_converter.py` that reads a validated `SceneFactPack` and populates a `BattleGrid`
6. **Add Grammar Shield rules** (WO-031) to enforce this schema in `json_mode` Spark output
7. **Write prompt fragment** for Spark system prompt containing unit rules and UNKNOWN discipline

### 6.2 Pydantic Model Sketch

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List
from enum import Enum

class MaterialEnum(str, Enum):
    WOOD = "wood"
    STONE = "stone"
    IRON = "iron"
    STEEL = "steel"
    GLASS = "glass"
    CLOTH = "cloth"
    BONE = "bone"
    CRYSTAL = "crystal"
    EARTH = "earth"
    ICE = "ice"

class MobilityEnum(str, Enum):
    FIXED = "fixed"
    MOVABLE = "movable"
    PORTABLE = "portable"

class ConditionEnum(str, Enum):
    INTACT = "intact"
    DAMAGED = "damaged"
    BROKEN = "broken"
    DESTROYED = "destroyed"

class UnknownableFloat(BaseModel):
    """A float that can be 'UNKNOWN'."""
    # Handled as Union[float, Literal["UNKNOWN"]] at the field level

class Dimensions(BaseModel):
    length_ft: float | Literal["UNKNOWN"]
    width_ft: float | Literal["UNKNOWN"]
    height_ft: float | Literal["UNKNOWN"]

class GridPosition(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)

class Affordances(BaseModel):
    flammable: Optional[bool] = None   # Default by material
    climbable: bool = False
    provides_cover: Optional[bool] = None  # Derived from solidity
    blocks_los: Optional[bool] = None  # Derived from opacity+permeability
    difficult_terrain: bool = False
    fragile: bool = False
    conductive: Optional[bool] = None  # Default by material
    crystalline: Optional[bool] = None  # Default by material
    dense: bool = False

class SceneObject(BaseModel):
    object_id: str = Field(min_length=1)
    class_: str = Field(alias="class", min_length=1)
    name: Optional[str] = None
    material: MaterialEnum
    dimensions: Dimensions
    weight_lb: Optional[float | Literal["UNKNOWN"]] = None
    position: GridPosition
    footprint_sq: Optional[dict] = None
    elevation_ft: int = 0
    facing: Optional[str] = None
    solidity: bool
    opacity: bool
    permeability: bool = False
    mobility: MobilityEnum
    condition: ConditionEnum
    hardness: Optional[int] = Field(default=None, ge=0)
    hit_points: Optional[int] = Field(default=None, ge=0)
    affordances: Affordances = Field(default_factory=Affordances)

class SceneCreature(BaseModel):
    creature_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    size: Literal["fine","diminutive","tiny","small","medium",
                   "large","huge","gargantuan","colossal"]
    space_ft: int = Field(gt=0)
    reach_ft: int = Field(ge=0)
    position: GridPosition
    elevation_ft: int = 0
    stance: str = "standing"
    geometry_equipment: list = Field(default_factory=list)
    team: Optional[str] = None

class SceneMetadata(BaseModel):
    tags: List[str] = Field(default_factory=list)
    biome: str
    indoors: bool
    lighting: Literal["bright", "dim", "dark", "magical_dark"]
    time_of_day: Literal["dawn","morning","midday","afternoon",
                          "dusk","evening","night","midnight"]
    theme: Optional[str] = None

class SceneFactPack(BaseModel):
    schema_version: str = "scene_fact_pack_v1"
    scene_id: str = Field(min_length=1)
    scene_version: int = Field(ge=1)
    provenance: Literal["SPARK_GENERATED"] = "SPARK_GENERATED"
    metadata: SceneMetadata
    dimensions: dict  # {"width_sq": int, "height_sq": int}
    objects: List[SceneObject] = Field(default_factory=list)
    creatures: List[SceneCreature] = Field(default_factory=list)
    terrain_zones: list = Field(default_factory=list)
    borders: list = Field(default_factory=list)
```

### 6.3 Prompt Fragment for Spark

```
You are generating a Scene Fact Pack for a D&D 3.5e tactical grid.

OUTPUT FORMAT: JSON conforming to scene_fact_pack_v1 schema.

UNITS (MANDATORY):
- All distances: feet (suffix _ft)
- Grid positions: integer squares (1 square = 5 feet)
- Weights: pounds (suffix _lb)
- NO metric units. NO mixing units.

UNKNOWN DISCIPLINE (MANDATORY):
- If you don't know an object's exact dimensions, emit "UNKNOWN" for that field.
- "UNKNOWN" triggers safe archetype defaults. A wrong number is WORSE than "UNKNOWN".
- NEVER guess: emit "UNKNOWN" and let the system handle it.
- You MUST always provide: position, solidity, opacity, condition, material.
- You MUST always provide for creatures: size, space_ft, reach_ft.

BOOLEAN FLAGS ONLY:
- affordances must be boolean (true/false), never prose descriptions.
- "provides_cover" = solid objects that block attacks.
- "blocks_los" = opaque objects that block line of sight.

SIZE CATEGORIES (D&D 3.5e only):
fine, diminutive, tiny, small, medium, large, huge, gargantuan, colossal

CONDITION FSM:
intact -> damaged -> broken -> destroyed (one-way only)

OBJECT IDS: Must be unique within the scene. Use descriptive snake_case.
```

### 6.4 Integration with Existing Systems

- **FactAcquisitionManager** (`fact_acquisition.py`): Scene Fact Pack is a bulk emission that supplements the existing JIT per-entity acquisition. When Spark generates a scene, all objects are registered in Lens as batch. If Box later needs a specific attribute, JIT acquisition is still available as fallback.
- **BoxLensBridge** (`box_lens_bridge.py`): After scene ingestion, the scene converter calls `BattleGrid` methods to place cells, borders, and entities. The bridge then syncs to Lens with `BOX` tier for positions and `SPARK`/`DEFAULT` tier for dimensions.
- **SceneCard** (`bundles.py`): The existing `SceneCard` is a DM prep artifact (narrative description, NPCs, exits). `SceneFactPack` is the mechanical companion -- the structured spatial data that SceneCard lacks. They are linked by `scene_id`.
- **GuardedNarrationService**: Scene generation goes through Grammar Shield (WO-031) for schema enforcement. Failed validation triggers retry (max 2), then template fallback.

---

## Appendix A: D&D 3.5e Size Category Reference

Source: PHB p.132, p.149; DMG p.29; MM Introduction

| Size | Space (ft) | Grid (sq) | Nat. Reach Tall (ft) | Nat. Reach Long (ft) | AC/Attack Mod | Grapple Mod | Hide Mod |
|------|-----------|-----------|---------------------|---------------------|--------------|------------|---------|
| Fine | 0.5 | 1* | 0 | 0 | +8 | -16 | +16 |
| Diminutive | 1 | 1* | 0 | 0 | +4 | -12 | +12 |
| Tiny | 2.5 | 1* | 0 | 0 | +2 | -8 | +8 |
| Small | 5 | 1 | 5 | 5 | +1 | -4 | +4 |
| Medium | 5 | 1 | 5 | 5 | +0 | +0 | +0 |
| Large | 10 | 2 | 10 | 5 | -1 | +4 | -4 |
| Huge | 15 | 3 | 15 | 10 | -2 | +8 | -8 |
| Gargantuan | 20 | 4 | 20 | 15 | -4 | +12 | -12 |
| Colossal | 30 | 5** | 30 | 20 | -8 | +16 | -16 |

*Fine/Diminutive/Tiny: occupy 1 square but can share space.
**Colossal: 30ft actual, engine rounds to 5x5 (25 squares) per `SizeCategory.footprint()`.

## Appendix B: PropertyFlag Mapping

Mapping from Scene Fact Pack boolean fields to `PropertyFlag` bits (defined in `aidm/schemas/geometry.py`):

| Scene Field | PropertyFlag | Bit | On Cell | On Border |
|------------|-------------|-----|---------|-----------|
| `solidity` | `SOLID` | 0 | Yes | Yes |
| `opacity` | `OPAQUE` | 1 | Yes | Yes |
| `permeability` | `PERMEABLE` | 2 | Yes | Yes |
| `affordances.difficult_terrain` | `DIFFICULT` | 3 | Yes | No |
| `terrain_zones[].flags.hazardous` | `HAZARDOUS` | 4 | Yes | No |
| `affordances.flammable` | `FLAMMABLE` | 5 | Yes | No |
| `affordances.fragile` | `FRAGILE` | 6 | Yes | No |
| `affordances.conductive` | `CONDUCTIVE` | 7 | Yes | No |
| `affordances.crystalline` | `CRYSTALLINE` | 8 | Yes | No |
| `affordances.dense` | `DENSE` | 9 | Yes | No |

Derived flags (not directly set by Spark):
- `blocks_los` = `OPAQUE AND NOT PERMEABLE` (computed by `PropertyMask.blocks_los()`)
- `blocks_loe` = `SOLID AND NOT PERMEABLE` (computed by `PropertyMask.blocks_loe()`)
- `provides_cover` = `SOLID` (cover resolver checks SOLID flag)

## Appendix C: Full Example Scene Fact Pack

```json
{
  "$schema": "scene_fact_pack_v1",
  "scene_id": "rusty_dragon_ground_floor",
  "scene_version": 1,
  "provenance": "SPARK_GENERATED",
  "metadata": {
    "tags": ["tavern", "social", "urban"],
    "biome": "urban",
    "indoors": true,
    "lighting": "bright",
    "time_of_day": "evening",
    "theme": "A lively tavern with a crackling fireplace and the smell of roasting meat"
  },
  "dimensions": {
    "width_sq": 12,
    "height_sq": 10
  },
  "objects": [
    {
      "object_id": "bar_counter_01",
      "class": "bar_counter",
      "name": "Main Bar",
      "material": "wood",
      "dimensions": {
        "length_ft": 10,
        "width_ft": 2,
        "height_ft": 3.5
      },
      "weight_lb": "UNKNOWN",
      "position": {"x": 1, "y": 1},
      "footprint_sq": {"width": 2, "height": 1},
      "elevation_ft": 0,
      "facing": "S",
      "solidity": true,
      "opacity": true,
      "permeability": false,
      "mobility": "fixed",
      "condition": "intact",
      "hardness": 5,
      "hit_points": 30,
      "affordances": {
        "flammable": true,
        "climbable": false,
        "provides_cover": true,
        "blocks_los": true,
        "difficult_terrain": false,
        "fragile": false,
        "conductive": false,
        "crystalline": false,
        "dense": false
      }
    },
    {
      "object_id": "table_01",
      "class": "tavern_table",
      "material": "wood",
      "dimensions": {
        "length_ft": 3,
        "width_ft": 3,
        "height_ft": 2.5
      },
      "position": {"x": 4, "y": 3},
      "solidity": true,
      "opacity": false,
      "mobility": "movable",
      "condition": "intact",
      "affordances": {
        "flammable": true,
        "provides_cover": true,
        "blocks_los": false
      }
    },
    {
      "object_id": "fireplace_01",
      "class": "fireplace",
      "material": "stone",
      "dimensions": {
        "length_ft": 5,
        "width_ft": 2,
        "height_ft": 4
      },
      "position": {"x": 10, "y": 4},
      "solidity": true,
      "opacity": true,
      "mobility": "fixed",
      "condition": "intact",
      "affordances": {
        "flammable": false,
        "provides_cover": true,
        "blocks_los": true,
        "dense": true
      }
    },
    {
      "object_id": "stool_01",
      "class": "bar_stool",
      "material": "wood",
      "dimensions": {
        "length_ft": "UNKNOWN",
        "width_ft": "UNKNOWN",
        "height_ft": "UNKNOWN"
      },
      "position": {"x": 1, "y": 2},
      "solidity": false,
      "opacity": false,
      "mobility": "portable",
      "condition": "intact"
    }
  ],
  "creatures": [
    {
      "creature_id": "barkeep_ameiko",
      "name": "Ameiko Kaijitsu",
      "size": "medium",
      "space_ft": 5,
      "reach_ft": 5,
      "position": {"x": 2, "y": 0},
      "elevation_ft": 0,
      "stance": "standing",
      "team": "neutral"
    },
    {
      "creature_id": "bouncer_orik",
      "name": "Orik Vancaskerkin",
      "size": "medium",
      "space_ft": 5,
      "reach_ft": 5,
      "position": {"x": 0, "y": 8},
      "elevation_ft": 0,
      "stance": "standing",
      "geometry_equipment": [
        {
          "item": "tower_shield",
          "effect": "extra_cover"
        }
      ],
      "team": "neutral"
    }
  ],
  "terrain_zones": [
    {
      "zone_id": "hearth_zone",
      "zone_type": "hazardous",
      "region": {"x": 10, "y": 4, "width_sq": 1, "height_sq": 1},
      "flags": {
        "hazardous": true,
        "difficult_terrain": false,
        "solid": false,
        "opaque": false
      },
      "description": "The roaring fireplace radiates intense heat"
    }
  ],
  "borders": [
    {
      "border_id": "front_door",
      "position": {"x": 5, "y": 9},
      "direction": "S",
      "solid": true,
      "opaque": true,
      "permeable": false,
      "object_ref": "wooden_door"
    },
    {
      "border_id": "kitchen_door",
      "position": {"x": 11, "y": 2},
      "direction": "E",
      "solid": true,
      "opaque": true,
      "permeable": false
    }
  ]
}
```

---

*End of RQ-SPARK-001-A findings.*
