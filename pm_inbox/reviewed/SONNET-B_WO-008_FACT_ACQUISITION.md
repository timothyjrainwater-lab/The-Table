# Completion Report: WO-008 JIT Fact Acquisition Protocol

**Work Order:** WO-008 — JIT Fact Acquisition Protocol
**Agent:** Sonnet-B (Claude 4.5 Sonnet)
**Date Completed:** 2026-02-11
**Status:** COMPLETE

---

## Executive Summary

Successfully implemented the Just-In-Time Fact Acquisition protocol for the Lens-Spark membrane. When Box queries data that Lens doesn't have, Lens requests it from Spark, validates the response, stores with provenance, and serves to Box.

---

## Deliverables

### 1. `aidm/core/fact_acquisition.py` (480 lines)

**Schema Components:**

| Component | Description |
|-----------|-------------|
| `FactRequest` | Frozen dataclass for requesting facts from Spark |
| `FactResponse` | Frozen dataclass for Spark's response |
| `ValidationResult` | Frozen dataclass with valid/errors/warnings |
| `AcquisitionResult` | Frozen dataclass with success/acquired/defaulted/errors |

**Constants (per RQ-LENS-001 Finding 5):**

| Constant | Value |
|----------|-------|
| `CREATURE_REQUIRED` | ["size", "position", "hit_points", "armor_class"] |
| `OBJECT_REQUIRED` | ["size", "position", "material", "hardness"] |
| `TERRAIN_REQUIRED` | ["position", "elevation", "movement_cost"] |
| `ALLOWED_DEFAULTS` | material="wood", hardness=5, movement_cost=1, elevation=0 |
| `FORBIDDEN_DEFAULTS` | size, position, hit_points, armor_class |

**FactAcquisitionManager Methods:**

| Method | Description |
|--------|-------------|
| `create_request()` | Generate FactRequest with unique UUID |
| `validate_response()` | Validate response against request |
| `apply_response()` | Store validated facts in Lens with SPARK tier |
| `apply_defaults()` | Apply ALLOWED_DEFAULTS for missing attrs |
| `acquire_facts()` | Full acquisition cycle with fallback |
| `get_or_acquire()` | Query with automatic acquisition if missing |
| `get_required_attributes()` | Get required attrs for entity class |
| `get_missing_attributes()` | Get unfilled required attrs |

### 2. `tests/test_fact_acquisition.py` (58 tests, 640 lines)

**Test Coverage by Category:**

| Category | Tests | Description |
|----------|-------|-------------|
| FactRequest schema | 5 | Creation, defaults, immutability, serialization |
| FactResponse schema | 5 | Creation, errors, immutability, serialization |
| ValidationResult schema | 2 | Valid/invalid result creation |
| AcquisitionResult schema | 2 | Success/failure result creation |
| Request generation | 3 | Valid request, unique ID, attributes populated |
| Response validation | 8 | ID match, missing attrs, type validation, extras |
| Apply response | 4 | Storage, SPARK tier, provenance, invalid rejected |
| Default application | 5 | Allowed applied, forbidden not, existing preserved |
| Full acquisition cycle | 5 | Success, partial, failure, exception, object |
| get_or_acquire | 4 | Existing returned, missing acquired, failure, default |
| Timeout handling | 2 | Fallback triggered, error logged |
| Edge cases | 5 | Unknown class, empty attrs, extra data, wrong types |
| Utility methods | 5 | Required attrs, missing attrs |
| Constants | 3 | Validation of module constants |
| **Total** | **58** | |

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All new tests pass | ✅ | 58 tests passed in 0.16s |
| All existing tests pass | ✅ | 2505 total tests, 0 failures |
| Validation catches all error cases | ✅ | Tests for ID mismatch, missing attrs, wrong types |
| Defaults applied correctly | ✅ | ALLOWED_DEFAULTS only, never FORBIDDEN |
| Facts stored with SPARK tier | ✅ | `test_source_tier_is_spark` |
| Timeout triggers fallback | ✅ | `test_timeout_triggers_default_fallback` |

---

## Design Decisions

### 1. Deterministic UUID Generation
The `FactAcquisitionManager` accepts an optional `uuid_generator` callback, allowing tests to inject deterministic UUIDs. Production code uses Python's `uuid.uuid4()`.

### 2. Frozen Dataclasses
All schema types (`FactRequest`, `FactResponse`, `ValidationResult`, `AcquisitionResult`) are frozen (immutable) for:
- Deterministic event logging
- Thread safety
- Prevention of accidental mutation

### 3. Validation Rules
Response validation is strict:
- Request ID must match exactly
- FORBIDDEN_DEFAULTS must be provided by Spark
- Type validation for all known attributes
- Unknown attributes are accepted with warnings (extensibility)

### 4. Graceful Degradation
On Spark timeout/failure:
1. Apply ALLOWED_DEFAULTS for missing attributes
2. Return `AcquisitionResult` with `success=False`
3. Log the failure with request details

### 5. Authority Preservation
Facts acquired from Spark are stored with `SourceTier.SPARK`, ensuring BOX (higher authority) can always override them later.

---

## Integration Points

**Depends on (from WO-007):**
- `LensIndex` — Main storage for acquired facts
- `SourceTier` — SPARK and DEFAULT tiers for provenance
- `LensFact` — Fact storage format

**Does NOT modify:**
- Any existing files (per WO constraints)

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `aidm/core/fact_acquisition.py` | 480 | JIT fact acquisition protocol |
| `tests/test_fact_acquisition.py` | 640 | Comprehensive test suite |

---

## Test Results

```
tests/test_fact_acquisition.py: 58 passed in 0.16s
Full suite: 2505 passed, 43 warnings in 10.13s
```

---

## Validation Rule Summary

| Attribute | Type Check | Value Check |
|-----------|------------|-------------|
| size | string | must be valid SizeCategory |
| position | dict | must have integer x, y keys |
| hit_points | int | must be positive (> 0) |
| armor_class | int | any integer |
| hardness | int | must be non-negative (>= 0) |
| elevation | int | any integer |
| movement_cost | int | must be >= 1 |
| material | string | any string |

---

## Known Limitations

1. **No async support**: Spark callback is synchronous; async would require protocol changes
2. **No retry logic**: Single attempt per acquisition (could add exponential backoff)
3. **No caching**: Each `get_or_acquire` call checks Lens first but doesn't cache failed acquisitions

---

## Future Work

- WO-009+ could add retry logic with exponential backoff
- Batch acquisition for multiple entities in single Spark call
- Async Spark callback support

---

**Status:** COMPLETE — Awaiting PM review

**Submitted:** 2026-02-11
**Agent:** Sonnet-B
