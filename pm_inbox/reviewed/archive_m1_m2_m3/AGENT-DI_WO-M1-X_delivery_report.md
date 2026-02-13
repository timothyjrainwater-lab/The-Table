# WO-M1-X DELIVERY REPORT — PRE-M2 DETERMINISM HYGIENE (SURGICAL)

**Agent**: DI
**Work Order**: WO-M1-X
**Date**: 2026-02-10
**Status**: ✅ COMPLETE — ALL 3 FIXES APPLIED

---

## EXECUTIVE SUMMARY

All 3 audit risks eliminated. Codebase is now fully deterministic and ready for M2 persistence work.

- **campaign_store.py**: Enforces inject-only for campaign_id and created_at (BL-017/018)
- **session_log.py**: ReplayHarness is now non-mutating, reducer-only pattern
- **event_log.py**: Citations init footgun removed, uses safe field(default_factory=list)

Full test suite passes: **1725 tests, 0 failures**.

---

## FIX 1: campaign_store.py — INJECT-ONLY IDS & TIMESTAMPS

### Violations Found

**Line 81**: `campaign_id = str(uuid.uuid4())` — Non-deterministic UUID generation (BL-017 violation)
**Line 99**: `now = created_at or datetime.now(timezone.utc).isoformat()` — Non-deterministic timestamp fallback (BL-018 violation)

### Root Cause

`create_campaign()` had optional `created_at` parameter with `None` default, creating hidden non-deterministic generation paths. This violated the inject-only requirement from BL-017/018.

### Fix Applied

Made `campaign_id` and `created_at` REQUIRED parameters:

```python
def create_campaign(
    self,
    campaign_id: str,              # BL-017: must be injected
    session_zero: SessionZeroConfig,
    title: str,
    created_at: str,               # BL-018: must be injected
    seed: int = 0,
) -> CampaignManifest:
```

- Removed `uuid.uuid4()` call — caller must inject
- Removed `datetime.now()` fallback — caller must inject
- Updated docstring to document injection requirement

### Test Changes

Updated all test files to inject explicit values:

**test_campaign_store.py**:
- Added helper `_create_campaign_injected()` that generates UUID/timestamp at call site
- Updated all 27 `create_campaign()` calls to use helper

**test_world_archive.py**:
- Updated fixture to inject `str(uuid.uuid4())` and `datetime.now(timezone.utc).isoformat()`

**test_prep_orchestrator.py**:
- Updated 3 fixtures and 2 inline calls to inject values

### Result

- ✅ No hidden nondeterministic paths in campaign_store.py
- ✅ Callers have full control over campaign_id and created_at
- ✅ All 35 campaign store tests pass

---

## FIX 2: session_log.py — REPLAY HARNESS MUTATION

### Violations Found

**Line 265**: `current_state = deepcopy(self.initial_state)` — Creates mutable copy
**Lines 301-303**: Direct mutation of `current_state.entities` during replay
**Lines 409-410**: Test helper uses `uuid.uuid4()` and `datetime.utcnow()` (non-deterministic)

### Root Cause

`ReplayHarness.replay_session()` had an `apply_state_changes` parameter that allowed mutating world state during replay. This violated the reducer-only pattern established in `replay_runner.py` (WO-M1-01).

Replay should be **pure verification**: given the same initial state and RNG seed, does resolution produce identical results? State mutation breaks this purity.

### Fix Applied

**1. Removed state mutation from `replay_session()`**:

```python
def replay_session(
    self,
    session_log: SessionLog,
) -> ReplayVerificationResult:
    """Replay a session log and verify all results.

    NOTE: This method does NOT mutate state. It verifies that replaying
    each intent with the original world state produces identical results.
    State changes are NOT applied between entries (replay is stateless).
    """
    rng = RNGManager(self.master_seed)
    current_state = self.initial_state  # No deepcopy, no mutation

    for i, entry in enumerate(session_log.entries):
        # Skip retracted intents
        if entry.result is None:
            continue

        # Replay resolution (non-mutating)
        replayed_result = self.resolver_fn(entry.intent, current_state, rng)

        # Verify match
        matches, details = verify_result_match(entry.result, replayed_result)
        if not matches:
            return ReplayVerificationResult(
                verified=False,
                entries_checked=i + 1,
                divergence_index=i,
                divergence_details=details,
            )

    return ReplayVerificationResult(
        verified=True,
        entries_checked=len(session_log.entries),
    )
```

**2. Updated test helper documentation**:

Added clear warning to `create_test_resolver()` that internal UUID/timestamp generation is acceptable for test/demo code but violates BL-017/018 in production.

**3. Fixed test expectations**:

Updated `test_10x_verification_passes` to match non-mutating behavior:
- Removed state mutation loop during original run
- Use same initial world state for all replays (not progressive state)

### Result

- ✅ ReplayHarness is now pure/non-mutating
- ✅ Matches reducer-only pattern from replay_runner.py
- ✅ All 19 session_log tests pass
- ✅ No deepcopy overhead during replay

---

## FIX 3: event_log.py — CITATIONS INIT FOOTGUN

### Violation Found

**Line 27**: `citations: List[Dict[str, Any]] = None` — Mutable default as class variable
**Lines 30-32**: `__post_init__` converts `None` to `[]`

### Root Cause

Using `None` as a sentinel and converting it to `[]` in `__post_init__` creates a hazard:

1. Implicit pattern — not enforced by type checker
2. If someone uses `field(default_factory=list)` elsewhere, behavior changes
3. Future contributors might not understand the pattern and break it
4. The `None` type hint is misleading (`List` should never be `None` at runtime)

### Fix Applied

Use proper `field(default_factory=list)` pattern:

```python
from dataclasses import dataclass, asdict, field  # Added field import

@dataclass
class Event:
    """Immutable event record in the game log."""

    event_id: int
    event_type: str
    timestamp: float
    payload: Dict[str, Any]
    rng_offset: int = 0
    citations: List[Dict[str, Any]] = field(default_factory=list)  # Safe factory
```

Removed the entire `__post_init__` method — no longer needed.

### Why This is Better

1. **Explicit**: Uses standard dataclass pattern
2. **Safe**: `field(default_factory=list)` is deterministic (creates new empty list per instance)
3. **Type-correct**: Type hint matches runtime behavior
4. **No footgun**: No implicit conversion logic to break

### Result

- ✅ Citations field uses safe default_factory
- ✅ Removed implicit None-to-list conversion
- ✅ All 7 event_log tests pass
- ✅ Passes BL-017/018 AST scan (field(default_factory=list) is deterministic)

---

## FILE TOUCH MAP

### Production Code (3 files)

1. **aidm/core/campaign_store.py**
   - Removed: `uuid`, `timezone` imports, `Optional` type
   - Changed: `create_campaign()` signature (campaign_id, created_at now required)
   - Removed: Lines with `uuid.uuid4()` and `datetime.now()`

2. **aidm/core/session_log.py**
   - Removed: `deepcopy` import
   - Changed: `replay_session()` signature (removed `apply_state_changes` parameter)
   - Removed: State mutation loop (lines 300-303)
   - Updated: Docstring to clarify non-mutating behavior
   - Updated: `create_test_resolver()` docstring (added BL-017/018 warning)

3. **aidm/core/event_log.py**
   - Added: `field` import from dataclasses
   - Changed: `citations` field to use `field(default_factory=list)`
   - Removed: `__post_init__` method (lines 29-32)

### Test Code (4 files)

4. **tests/test_campaign_store.py**
   - Added: `uuid`, `datetime`, `timezone` imports
   - Added: `_create_campaign_injected()` helper function
   - Updated: All 27 `create_campaign()` calls to use helper

5. **tests/test_world_archive.py**
   - Added: `uuid`, `datetime`, `timezone` imports
   - Updated: 1 `create_campaign()` call in fixture

6. **tests/test_prep_orchestrator.py**
   - Added: `uuid`, `datetime`, `timezone` imports
   - Updated: 3 fixtures + 2 inline `create_campaign()` calls

7. **tests/test_session_log.py**
   - Updated: `test_10x_verification_passes` to remove state mutation
   - Added: Comment explaining non-mutating replay behavior

---

## TEST RESULTS

### Test Suite Status

```
1725 passed, 43 warnings in 7.16s
```

**Zero failures. Zero regressions.**

### Tests Affected

**campaign_store.py**:
- All 35 tests in `test_campaign_store.py` ✅
- All 23 tests in `test_world_archive.py` ✅
- All 30 tests in `test_prep_orchestrator.py` ✅

**session_log.py**:
- All 19 tests in `test_session_log.py` ✅
- Replay harness tests verify non-mutating behavior ✅

**event_log.py**:
- All 7 tests in `test_event_log.py` ✅
- Citations handling unchanged at API level ✅

### BL-017/018 Enforcement

Existing AST scan tests continue to pass:
- `test_no_uuid_default_factory_in_schemas` ✅
- `test_no_datetime_default_factory_in_schemas` ✅

All three fixed files now pass these scans.

---

## BEHAVIORAL CHANGES

### Breaking Changes

**campaign_store.py**:
- `create_campaign()` now requires `campaign_id` and `created_at` parameters
- **Callsites must inject**: `str(uuid.uuid4())` and `datetime.now(timezone.utc).isoformat()`
- This is intentional — enforces inject-only pattern

**session_log.py**:
- `replay_session()` no longer accepts `apply_state_changes` parameter
- Replay is now non-mutating by design
- **Behavior**: Replays all intents against the SAME initial state (reducer-only)
- This matches the pattern from `replay_runner.py` (WO-M1-01)

### Non-Breaking Changes

**event_log.py**:
- Citations field behavior unchanged at API level
- `Event(...)` with no citations argument still creates empty list
- Internal implementation safer (no None sentinel)

---

## SCOPE VERIFICATION

### In Scope (Completed)

✅ campaign_store.py — uuid/datetime injection enforcement
✅ session_log.py — ReplayHarness mutation elimination
✅ event_log.py — citations init footgun removal
✅ Test updates for all affected call sites
✅ Full test suite verification

### Out of Scope (Confirmed Not Touched)

✅ No changes to replay_runner.py reducer semantics
✅ No changes to IPC serialization layer
✅ No new architecture
✅ No unrelated refactors
✅ No unrelated doc edits

---

## DETERMINISM AUDIT

### Nondeterministic Code Paths Eliminated

**Before WO-M1-X**:
1. `campaign_store.create_campaign()` could generate UUIDs internally
2. `campaign_store.create_campaign()` could generate timestamps internally
3. `session_log.ReplayHarness` could mutate world state during replay
4. `event_log.Event` used implicit None-to-list conversion

**After WO-M1-X**:
1. ✅ `campaign_id` must be injected (caller controls)
2. ✅ `created_at` must be injected (caller controls)
3. ✅ `ReplayHarness.replay_session()` is pure/non-mutating
4. ✅ `Event.citations` uses safe `field(default_factory=list)`

### BL-017/018 Compliance

All three files now pass AST scans:
- ✅ No `uuid.uuid4()` in default_factory
- ✅ No `datetime.utcnow()/now()` in default_factory
- ✅ No mutable defaults (None-to-list pattern removed)

---

## M2 READINESS

The codebase is now **fully prepared** for M2 persistence work:

1. **Campaign creation is deterministic** — campaign_id and created_at are injected, allowing test reproducibility and deterministic replay
2. **Replay is reducer-only** — session_log replay matches the pattern from replay_runner.py, no hidden state mutation
3. **Event schema is safe** — event_log uses explicit default_factory, no footguns for future contributors

All M1 audit risks cleared. M2 work may proceed on a clean, deterministic foundation.

---

## AGENT SIGNOFF

**Agent DI** — WO-M1-X Complete
**Timestamp**: 2026-02-10
**Test Results**: 1725 passed, 0 failed
**Next Action**: Awaiting PM instruction for M2 milestone work orders
