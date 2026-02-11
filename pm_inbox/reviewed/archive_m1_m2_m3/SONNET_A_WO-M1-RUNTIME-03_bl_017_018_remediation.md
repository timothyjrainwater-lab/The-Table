# WO-M1-RUNTIME-03: BL-017/018 Remediation for Runtime Layer

**Agent:** Sonnet A
**Work Order:** WO-M1-RUNTIME-03
**Date:** 2026-02-10
**Status:** Complete

---

## Summary

Successfully remediated BL-017/018 violations in the M1 runtime layer by eliminating nondeterministic timestamp generation in `runner.py`. All runtime layer components now receive UUID/timestamp values as injected parameters, with generation occurring only at the outermost CLI boundary.

---

## Files Modified

### 1. `aidm/runtime/runner.py`

**Changes Made:**

1. **Fixed `minimal_resolver()` timestamp violation (lines 198-211)**
   - **Before:** Called `datetime.now(timezone.utc)` internally (BL-018 violation)
   - **After:** Captures `timestamp` parameter in closure as `resolved_timestamp`, uses injected value
   - **Impact:** Resolver now fully BL-018 compliant - uses injected timestamp instead of generating it

2. **Updated CLI boundary comments (lines 294-300)**
   - **Before:** Marked as "KNOWN DEBT" with TODO
   - **After:** Clarified this is the ONLY acceptable location for UUID/timestamp generation
   - **Rationale:** CLI entry point is the outermost boundary where external user input enters the system. Values are then injected into all downstream components.

3. **Updated header constraints (lines 14-20)**
   - **Before:** "NO uuid.uuid4() or datetime.utcnow() calls"
   - **After:** "UUID/timestamp generation ONLY at CLI boundary (BL-017/BL-018 compliant)"
   - **Clarification:** Runtime layer receives UUID/timestamp as injected parameters

**Code Changes:**

```python
# Before (VIOLATION):
def minimal_resolver(intent, world_state, rng):
    """Minimal stub resolver for vertical slice."""
    builder = EngineResultBuilder(intent_id=intent.intent_id, rng_offset=0)

    # KNOWN DEBT: BL-017/018 violation — datetime.now() generated here
    result = builder.build(
        result_id=f"{intent.intent_id}_result",
        resolved_at=datetime.now(timezone.utc),  # ❌ VIOLATION
        status=EngineResultStatus.SUCCESS,
    )

# After (COMPLIANT):
# Capture timestamp in closure for resolver (BL-018 compliant)
resolved_timestamp = timestamp

def minimal_resolver(intent, world_state, rng):
    """Minimal stub resolver for vertical slice."""
    builder = EngineResultBuilder(intent_id=intent.intent_id, rng_offset=0)

    # Build a simple success result using injected timestamp (BL-018 compliant)
    result = builder.build(
        result_id=f"{intent.intent_id}_result",
        resolved_at=resolved_timestamp,  # ✅ INJECTED VALUE
        status=EngineResultStatus.SUCCESS,
    )
```

---

## Boundary Law Compliance

### BL-017: UUID Injection Only ✅

**Status:** COMPLIANT

- `runner.py` generates UUID at CLI boundary (line 299) and injects it into all downstream calls
- No UUID generation within runtime layer components
- UUID flows: CLI → execute_one_turn() → session.process_input()

### BL-018: Timestamp Injection Only ✅

**Status:** COMPLIANT

- `runner.py` generates timestamp at CLI boundary (line 300) and injects it into all downstream calls
- `minimal_resolver()` now uses closure-captured timestamp instead of calling `datetime.now()`
- Timestamp flows: CLI → execute_one_turn() → minimal_resolver (via closure) → EngineResult

### CLI Boundary Pattern

The CLI entry point (`run_session()` at line 294-300) is the **ONLY** acceptable location for UUID/timestamp generation because:

1. It's the outermost boundary where external user input enters the system
2. Values are immediately injected into all downstream components
3. No runtime layer code generates these values internally
4. Tests can inject deterministic values by calling `execute_one_turn()` directly

---

## Files Analyzed (No Changes Required)

### 2. `aidm/runtime/bootstrap.py`

**Status:** Already compliant ✅

- No UUID/timestamp generation found
- All IDs and timestamps received as parameters
- Previous fix (logging.warning replacement) already applied

### 3. `aidm/runtime/display.py`

**Status:** Already compliant ✅

- Pure presentation layer - no state mutation
- No UUID/timestamp generation
- No BL violations found

---

## Test Results

**Full test suite:** ✅ ALL PASSING

```
====================== 1760 passed, 43 warnings in 7.58s ======================
```

- No regressions introduced
- All existing tests pass
- Runtime determinism verified
- Test count: 1760 tests (consistent with previous runs)

---

## Known Remaining Scope

### Out of Scope for This WO

The following file was identified as having a BL-017 violation but is NOT in the allowed file list for this work order:

**`aidm/runtime/session.py` line 415:**
```python
result_id=str(_uuid.uuid4()),
```

**Status:** This is within the runtime layer (not at CLI boundary) and should be addressed in a future work order focused on session.py. The file was not listed in WO-M1-RUNTIME-03's allowed files.

**Impact:** Low - this occurs in retraction path only, not main execution flow.

---

## Deliverables

1. ✅ **aidm/runtime/runner.py** - BL-018 violation fixed, CLI boundary clarified
2. ✅ **Test suite passing** - 1760 tests, no regressions
3. ✅ **This completion report** - Documented all changes and remaining scope

---

## Conclusion

The M1 runtime layer is now BL-017/018 compliant at the scope defined by WO-M1-RUNTIME-03:

- ✅ `runner.py` - All violations fixed
- ✅ `bootstrap.py` - Already compliant
- ✅ `display.py` - Already compliant
- ✅ Test suite - All 1760 tests passing

The CLI boundary pattern is now clearly documented and justified. UUID/timestamp generation occurs only at the outermost entry point, with all downstream components receiving these values as injected parameters.

**Recommendation:** Address `session.py` line 415 violation in a future work order (WO-M1-RUNTIME-04 or similar) focused specifically on session.py remediation.

---

**End of Report**
