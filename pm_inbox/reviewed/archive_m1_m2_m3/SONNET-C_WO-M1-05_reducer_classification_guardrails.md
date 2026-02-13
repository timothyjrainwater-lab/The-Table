# WO-M1-05: Reducer Classification Guardrails

Agent: Sonnet-C
Work Order: WO-M1-05
Date: 2026-02-10
Status: Complete

## Summary

Added explicit documentation and test guardrails to enforce the INFORMATIONAL_EVENTS classification policy in the replay reducer.

## Changes Made

### 1. Documentation Added to `replay_runner.py`

Added comprehensive CLASSIFICATION POLICY comment block above `INFORMATIONAL_EVENTS` set:

```python
# CLASSIFICATION POLICY (WO-M1-05):
# An event is informational if:
# 1. It records a narrative moment with no state change (e.g., "attack_roll")
# 2. State mutation has already occurred via a separate mutating event
#    (e.g., "bull_rush_success" is informational because the position change
#    was already recorded by a "move" event)
#
# FUTURE MIGRATION RULE:
# If an informational event begins to directly mutate state (e.g., a maneuver
# result event starts setting entity fields without emitting a mutating event),
# it MUST be migrated to MUTATING_EVENTS and given an explicit reducer handler.
#
# WHY MANEUVER RESULTS ARE INFORMATIONAL:
# Events like "bull_rush_success", "disarm_success", etc. are currently
# informational because:
# - Position changes are recorded by "move" events
# - Condition changes are recorded by "condition_applied" events
# - HP changes are recorded by "hp_changed" events
# - The maneuver result event itself is a narrative marker that doesn't
#   directly mutate state—it reports that a sequence of state-mutating
#   events has completed successfully.
```

**Why This Matters:**
- Documents the rationale for why 70+ events (including all maneuver results) are classified as informational
- Provides clear migration rule for future developers
- Explains the event-sourcing pattern: state mutation happens via dedicated mutating events, success/failure events are narrative markers

### 2. Guardrail Test Added to `test_replay_ac09_ac10.py`

Created `test_wom105_informational_events_do_not_mutate_state()`:

**What It Does:**
- Iterates through all 70 events in `INFORMATIONAL_EVENTS`
- Creates a test event for each type with plausible payload
- Passes each through `reduce_event()`
- Verifies state hash remains unchanged
- **FAILS** if any informational event mutates state

**Test Output Format:**
```
WO-M1-05 GUARDRAIL FAILED: 3 informational events mutated state:
['bull_rush_success', 'disarm_success', 'trip_success']

POLICY VIOLATION: Events in INFORMATIONAL_EVENTS must NOT mutate state.
If an event needs to mutate state, it must be migrated to MUTATING_EVENTS
and given an explicit reducer handler.
See CLASSIFICATION POLICY comment in replay_runner.py for migration rules.
```

**Why This Test Exists:**
- Prevents accidental state mutation from informational events
- Catches bugs where a reducer handler is added for an informational event but the event is not migrated to `MUTATING_EVENTS`
- Enforces the classification policy automatically

## Test Results

All tests pass:
- **AC-09/AC-10 tests**: 6/6 passed (including new WO-M1-05 guardrail test)
- **Full test suite**: 1712/1712 passed

## Files Modified

1. **aidm/core/replay_runner.py** (lines 74-122)
   - Added CLASSIFICATION POLICY comment block
   - No behavior change, documentation only

2. **tests/test_replay_ac09_ac10.py** (lines 90-177)
   - Added `test_wom105_informational_events_do_not_mutate_state()`
   - New guardrail test enforcing classification policy

## Verification

```bash
# Verify AC-09/AC-10 compliance + new guardrail
pytest tests/test_replay_ac09_ac10.py -v
# 6 passed

# Verify no regressions
pytest --tb=short -q
# 1712 passed, 43 warnings
```

## Policy Summary

**An event is INFORMATIONAL if:**
1. It records a narrative moment (e.g., "attack_roll", "save_rolled")
2. State mutation already occurred via a separate mutating event (e.g., "bull_rush_success" follows "move")

**An event is MUTATING if:**
- It directly changes entity fields, combat state, or world state
- All 20 mutating events in `MUTATING_EVENTS` have explicit reducer handlers (AC-09 compliance)

**Future Migration Rule:**
- If an informational event begins directly mutating state → migrate to `MUTATING_EVENTS` and add reducer handler
- The guardrail test will fail if this policy is violated

## Notes

- No behavior change, only documentation + guardrails
- All existing tests remain green
- Maneuver result events (bull_rush_success, disarm_success, etc.) correctly remain informational because state mutations are handled by move/condition_applied/hp_changed events
- Dynamic intent events (intent_*) remain exempt from AC-09 coverage (they are generated at runtime)
