# WO-WS-DEADVERB-001 — Unknown Client msg_type: Fail Loud

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** Security / Server
**Priority:** MEDIUM — unknown client verbs silently dropped; contract violations invisible
**WO type:** BUG FIX (fail-loud contract enforcement)
**Seat:** Builder

**Closes:** FINDING-WS-DEAD-VERB-SWALLOW-001 (MEDIUM)
**Context:** ADVERSARIAL_AUDIT_SYNTHESIS_001 — Inverted Default 2 (system defaults to SILENT)
**Three-layer accuracy:** Closes information accuracy failure (player sends verb, receives no feedback).

---

## 0. Section 0 — Doctrine Hard Stops

Server WO. UI doctrine does not apply except WS security invariant (locked 2026-02-25):

> *Unknown `msg_type` from client → `error` response + server log. No silent consumption of unknown inputs. Violations are observable and diagnosable.*

- **No changes to engine, parsers, or client code in this WO.**
- **Scope is `ws_bridge.py` only** — the routing layer.
- The fix is additive: one error response path + one log line. Total change is small.

---

## 1. Target Lock

**Current behavior:** `_route_message()` in `ws_bridge.py` dispatches `player_utterance`, `player_action`, `session_control`. Unknown `msg_type` falls back to the base `ClientMessage` type — silently. No error returned. No log entry. The client action is consumed and disappears.

**Effect:** `roll_confirm`, `ability_check_declare`, and any future client verb not yet registered arrive and vanish. The client has no way to know the server didn't process the action. The player may believe their action resolved when it didn't.

**Fix:** Unknown `msg_type` must:
1. Return an `error` message to the client with the unrecognized type name.
2. Log a WARNING server-side so the gap is visible in server output.

---

## 2. Binary Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Error response format | `ErrorEvent(code="UNKNOWN_MSG_TYPE", message=f"Unrecognized message type: {msg_type!r}")` | Consistent with existing error path in ws_bridge |
| Log level | WARNING | Unknown verb is a contract gap, not a normal condition |
| Close connection? | NO — return error and continue | Dead verb is not a security breach; connection stays alive |
| Rate limit for unknown verbs? | No — out of scope for this WO | WO-UI-WS-SERVER-HARDENING-001 handles rate limiting |

---

## 3. Contract Spec

### 3.1 `_route_message()` change

Locate the routing logic in `ws_bridge.py`. Current structure (approximately):

```python
async def _route_message(self, msg):
    if isinstance(msg, PlayerUtterance):
        ...
    elif isinstance(msg, PlayerAction):
        ...
    elif isinstance(msg, SessionControl):
        ...
    # else: falls through silently
```

New structure:

```python
async def _route_message(self, msg):
    if isinstance(msg, PlayerUtterance):
        ...
    elif isinstance(msg, PlayerAction):
        ...
    elif isinstance(msg, SessionControl):
        ...
    else:
        # Unknown msg_type — fail loud
        msg_type = getattr(msg, "msg_type", type(msg).__name__)
        import logging
        logging.getLogger(__name__).warning(
            "ws_bridge: unrecognized msg_type %r from connection — returning error",
            msg_type
        )
        await self._send_message(ErrorEvent(
            code="UNKNOWN_MSG_TYPE",
            message=f"Unrecognized message type: {msg_type!r}. No action taken."
        ))
```

### 3.2 `parse_client_message()` behavior

`ws_protocol.py` already raises `INVALID_MESSAGE` on parse failure — that path is separate and correct. This WO addresses the case where `parse_client_message()` returns a base `ClientMessage` (or equivalent) for an unregistered but parseable `msg_type`. The fix is in `_route_message()`, not in the parser.

### 3.3 Events emitted

None. `ErrorEvent` is a WS response message, not an engine event.

---

## 4. Implementation Plan

1. **`aidm/server/ws_bridge.py`** — add `else` branch to `_route_message()`. Two lines: WARNING log + `ErrorEvent` send. Nothing else.
2. **`tests/test_ws_deadverb_001.py`** (NEW) — ≥5 tests.

---

## 5. Gate Tests (≥5 required)

```
DV-001: Known msg_type (player_utterance) — routes correctly, no error returned
DV-002: Unknown msg_type ("roll_confirm") — ErrorEvent returned to client with UNKNOWN_MSG_TYPE code
DV-003: Unknown msg_type ("ability_check_declare") — ErrorEvent returned
DV-004: Unknown msg_type — WARNING log entry produced (check logging output)
DV-005: Unknown msg_type — connection NOT closed (subsequent known msg_type still routed)
```

---

## 6. Integration Seams

- `aidm/server/ws_bridge.py` — `_route_message()` method
- `aidm/server/ws_protocol.py` — `ErrorEvent` dataclass — read, do not modify

---

## 7. Assumptions to Validate

- Confirm: `_route_message()` is the single dispatch point for all client messages
- Confirm: `ErrorEvent` is importable from `ws_protocol.py` and has `code` + `message` fields
- Confirm: base `ClientMessage` objects (unknown type) reach `_route_message()` without being filtered earlier

---

## 8. Preflight

Before writing code:
- [ ] Read `aidm/server/ws_bridge.py` — locate `_route_message()`
- [ ] Read `aidm/server/ws_protocol.py` — confirm `ErrorEvent` constructor fields
- [ ] Confirm where `parse_client_message()` returns base `ClientMessage` for unknown type (vs. raises)

---

## 9. Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-WS-DEADVERB-001.md`

**Pass 1:**
- `_route_message()` else branch location (line citation)
- WARNING log confirmed present
- `ErrorEvent` constructor used correctly
- Connection stays open after unknown verb confirmed

**Pass 2 (≤100 words):** What was implemented.

**Pass 3:** Drift caught.

**Radar (mandatory):**
- DV-001 through DV-005: all pass
- No silent drop path remains for unknown msg_type

Missing debrief or missing Radar → REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
