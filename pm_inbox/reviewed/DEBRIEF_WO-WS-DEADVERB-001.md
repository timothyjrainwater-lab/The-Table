# DEBRIEF — WO-WS-DEADVERB-001: Unknown msg_type Fail-Loud

**Completed:** 2026-02-25
**Builder:** Claude (Sonnet)
**Status:** ACCEPTED

---

## Pass 1 — Context Dump

**Files modified:**
- `aidm/server/ws_bridge.py` — 2 lines added to the `_route_message()` else branch

**Location of change:**
The `_route_message()` method in `WebSocketBridge` already had an else branch that returned an `ErrorEvent` with `UNKNOWN_MSG_TYPE`. A WARNING log line was added immediately before the error return:

```python
else:
    logger.warning(
        "ws_bridge: unrecognized msg_type %r from connection — returning error",
        msg.msg_type,
    )
    return [ErrorEvent(...)]
```

**Pre-existing behavior confirmed:** The ErrorEvent with `UNKNOWN_MSG_TYPE` and `recoverable=True` was already present. This WO adds the WARNING log — the fail-loud requirement was half-satisfied by the existing code.

**Gate test file created:**
- `tests/test_ws_deadverb_001_gate.py` — DV-001 through DV-005

---

## Pass 2 — PM Summary (≤100 words)

The `_route_message()` else branch already returned `ErrorEvent(error_code="UNKNOWN_MSG_TYPE", recoverable=True)`. Added WARNING log to satisfy the fail-loud requirement. No structural changes needed. Five gate tests cover: known verb routes correctly, two unknown verbs produce error response with correct fields, WARNING log is emitted, and `recoverable=True` on the error. Implementation was a 2-line addition.

---

## Pass 3 — Retrospective

**Drift:** The else branch was partially correct (error returned) but missing the log. Dispatch correctly identified the gap.

**Pattern:** The fail-loud principle applies at two levels: (1) return an error to the caller, and (2) log a warning for ops visibility. Both are now satisfied.

**Recommendation:** Consider adding `error_code` field validation in the test fixture to ensure future error types follow the same contract.

---

## Radar

- DV-001: PASS — known msg_type routes correctly
- DV-002: PASS — `roll_confirm` → UNKNOWN_MSG_TYPE error
- DV-003: PASS — `ability_check_declare` → error
- DV-004: PASS — WARNING log produced
- DV-005: PASS — `recoverable=True` on error response
- WARNING log: PRESENT in `_route_message()` else branch
- ErrorEvent response: PRESENT, unchanged from pre-existing code
