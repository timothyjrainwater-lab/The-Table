# Completion Report: WO-007 — Lens Object Property Indexing

**Assigned To:** Sonnet-A (Claude 4.5 Sonnet)
**Completed:** 2026-02-11
**Status:** COMPLETE

---

## Executive Summary

Successfully implemented the Lens Object Property Indexing system — the data membrane between Spark (LLM) and Box (deterministic engine). Created 2 files totaling 1,245 lines of code. All 42 new tests pass, and all 2,388 existing tests continue to pass (zero regressions).

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `aidm/core/lens_index.py` | 598 | SourceTier, LensFact, EntityProfile, LensIndex |
| `tests/test_lens_index.py` | 647 | 42 comprehensive tests |
| **Total** | **1,245** | |

---

## Test Results

### New Tests: 42/42 PASSED (100%)

```
tests/test_lens_index.py ... 42 passed in 0.16s
```

Test breakdown by category:
- SourceTier tests: 4 (existence, ordering, values)
- LensFact tests: 4 (creation, immutability, serialization)
- EntityProfile tests: 3 (creation, storage, serialization)
- LensIndex entity tests: 7 (register, get, remove, list)
- LensIndex fact tests: 6 (set, get, tracking)
- Authority resolution tests: 6 (BOX overrides, SPARK cannot override, same tier, CANONICAL immutable)
- Spatial index tests: 7 (position, entities_at, radius search)
- Snapshot tests: 3 (independence, mutation isolation)
- Serialization tests: 2 (round-trip, empty index)

### Full Suite: 2,388/2,388 PASSED (zero regressions)

```
2388 passed, 43 warnings in 10.53s
```

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All new tests pass | ✅ | 42/42 tests pass |
| All existing tests pass | ✅ | 2388 tests pass |
| Authority resolution correct | ✅ | 6 tests verify BOX > SPARK, same-tier, CANONICAL immutable |
| Spatial queries work | ✅ | 7 tests verify position, entities_at, radius search |
| Serialization works | ✅ | to_dict/from_dict round-trip preserves all data |
| Snapshot produces independent copy | ✅ | 3 tests verify mutation isolation |

---

## Implementation Summary

### SourceTier (Authority Hierarchy)

```python
class SourceTier(IntEnum):
    BOX = 1       # Highest — mechanical facts
    CANONICAL = 2 # Rulebook constants
    PLAYER = 3    # Player input
    SPARK = 4     # LLM generated
    DEFAULT = 5   # Lowest — system defaults
```

Lower number = higher authority. BOX always overrides SPARK.

### LensFact (Immutable Fact with Provenance)

```python
@dataclass(frozen=True)
class LensFact:
    entity_id: str
    attribute: str
    value: Any
    source_tier: SourceTier
    timestamp: int  # Turn number
    provenance_id: Optional[str] = None
```

Frozen dataclass ensures facts are never modified in place.

### EntityProfile (Fact Collection)

```python
@dataclass
class EntityProfile:
    entity_id: str
    entity_class: str  # 'creature', 'object', 'terrain'
    facts: Dict[str, LensFact]
    created_at: int
    updated_at: int
```

### LensIndex (Main Indexing System)

```python
class LensIndex:
    # Entity management
    def register_entity(entity_id, entity_class, turn) -> EntityProfile
    def get_entity(entity_id) -> Optional[EntityProfile]
    def remove_entity(entity_id) -> bool
    def list_entities(entity_class=None) -> List[str]

    # Fact storage with authority resolution
    def set_fact(entity_id, attribute, value, source_tier, turn) -> Optional[LensFact]
    def get_fact(entity_id, attribute) -> Optional[LensFact]
    def get_facts(entity_id) -> Dict[str, LensFact]

    # Spatial index
    def set_position(entity_id, pos, turn) -> None
    def get_position(entity_id) -> Optional[Position]
    def get_entities_at(pos) -> List[str]
    def get_entities_in_radius(center, radius) -> List[str]

    # Snapshot and serialization
    def snapshot() -> LensIndex
    def to_dict() -> dict
    def from_dict(data) -> LensIndex
```

---

## Authority Resolution Rules

Per RQ-LENS-001 Finding 1, implemented as:

1. **No existing fact** → Accept new fact
2. **Existing has lower tier number (higher authority)** → Reject new fact
3. **Same tier** → Accept if newer timestamp
4. **Existing has higher tier number (lower authority)** → Accept new fact
5. **CANONICAL facts** → Immutable after first set (even BOX cannot override)

### Truth Table

| Existing Tier | New Tier | Outcome |
|--------------|----------|---------|
| SPARK (4) | BOX (1) | ✅ Accept |
| BOX (1) | SPARK (4) | ❌ Reject |
| SPARK (4) | SPARK (4), newer | ✅ Accept |
| SPARK (4) | SPARK (4), older | ❌ Reject |
| CANONICAL (2) | BOX (1) | ❌ Reject (immutable) |

---

## Spatial Index Design

Internal data structures for O(1) position queries:

```python
_position_index: Dict[str, Position]           # entity_id → position
_grid_index: Dict[Tuple[int,int], Set[str]]    # (x,y) → entity_ids
```

When position changes:
1. Remove entity from old grid cell
2. Add entity to new grid cell
3. Update position index
4. Store position as BOX-tier fact

`get_entities_in_radius` uses bounding box + distance filter with Position.distance_to() (1-2-1-2 diagonal movement).

---

## Design Decisions

### 1. SourceTier as IntEnum

Using IntEnum allows direct comparison operators (`<`, `>`) for authority resolution. Lower value = higher authority makes the logic intuitive.

### 2. LensFact is Frozen

Facts are immutable (frozen dataclass). When a fact is updated, a new LensFact is created and replaces the old one. This prevents accidental mutation and ensures provenance integrity.

### 3. Position Stored as BOX-tier Fact

`set_position()` also stores the position as a BOX-tier fact with attribute "position". This ensures positions are tracked in the fact system with proper authority.

### 4. CANONICAL Immutability Check Before Tier Comparison

CANONICAL facts are checked for immutability before the tier comparison, ensuring even higher-authority sources cannot override rulebook constants.

### 5. Spatial Index Rebuilds from Serialization

`from_dict()` rebuilds the grid index from stored positions, ensuring spatial queries work correctly after deserialization.

---

## Issues and Concerns

### None

Implementation proceeded smoothly. All requirements were clear and unambiguous.

---

## Deliverables Summary

| Deliverable | Status |
|-------------|--------|
| `aidm/core/lens_index.py` | ✅ Created (598 lines) |
| `tests/test_lens_index.py` | ✅ Created (647 lines, 42 tests) |
| All new tests pass | ✅ 42/42 |
| All existing tests pass | ✅ 2388/2388 |
| Completion report | ✅ This document |

---

## Ready for Integration

The Lens Index is complete and provides:
- Authority-aware fact storage (BOX > CANONICAL > PLAYER > SPARK > DEFAULT)
- Fast spatial queries (O(1) position lookup, efficient radius search)
- Full serialization for persistence
- Snapshot for rollback support

This forms the data membrane between Spark (LLM) and Box (deterministic engine), ensuring mechanical facts always have authority over generated content.
