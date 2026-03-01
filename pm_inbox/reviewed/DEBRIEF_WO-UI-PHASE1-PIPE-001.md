# DEBRIEF: WO-UI-PHASE1-PIPE-001 - Phase 1 Integration: Connect the Pipe

**Lifecycle:** ARCHIVE
**Commit:** 2b9db07
**Filed by:** Chisel
**Session:** 26
**Date:** 2026-03-01
**WO:** WO-UI-PHASE1-PIPE-001
**Status:** FILED - awaiting PM verdict

---

## Pass 1 - Context Dump

### Summary

Three wiring gaps between client2d and the engine were identified and closed.
The pipe now carries player text input from browser to engine and back.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `client2d/ws.js` | MODIFIED | Line 7: default URL `ws://localhost:8765/ws` -> `ws://localhost:8000/ws` |
| `client2d/main.js` | MODIFIED | Line 60: `msg_type: 'player_input'` -> `msg_type: 'player_utterance'`; Line 78: WsBridge URL `8765` -> `8000` |
| `start_server.py` | NEW | Factory + uvicorn launch entry point for Phase 1 |
| `tests/test_ui_phase1_pipe_gate.py` | NEW | PIPE-001..PIPE-008 gate tests |

### Before / After: GAP-01 (Port Fix)

**ws.js line 7 BEFORE:**
```js
constructor(url = 'ws://localhost:8765/ws') {
```
**ws.js line 7 AFTER:**
```js
constructor(url = 'ws://localhost:8000/ws') {
```

**main.js line 78 BEFORE:**
```js
const ws = new WsBridge('ws://localhost:8765/ws');
```
**main.js line 78 AFTER:**
```js
const ws = new WsBridge('ws://localhost:8000/ws');
```

### Before / After: GAP-02 (Message Type Fix)

**main.js line 60 BEFORE:**
```js
ws.send({ msg_type: 'player_input', text: text });
```
**main.js line 60 AFTER:**
```js
ws.send({ msg_type: 'player_utterance', text: text });
```

### GAP-03: start_server.py (New File)

Pattern sourced from `aidm/evaluation/harness.py:203`.
`build_simple_combat_fixture()` returns a `ScenarioFixture`; `fixture.world_state`
is extracted and passed to `SessionOrchestrator`. Factory is a closure capturing
the fixture so each new session_id maps to the same shared 3v3 encounter (Stage 1 intent).

**Key structural points:**
- `create_app(session_orchestrator_factory=factory)` - real factory passed; `_StubSession` closure inside `create_app` is never reached
- `_StubSession` bypass confirmed at `app.py:53` - the stub is defined inside the `if session_orchestrator_factory is None:` guard
- Launch: `python start_server.py` - binds to `127.0.0.1:8000`

### Grep: Port 8765 Before Fix (Acceptance Note 5)

Two hardcodes confirmed before fix:
```
client2d/ws.js:7:   constructor(url = 'ws://localhost:8765/ws') {
client2d/main.js:78: const ws = new WsBridge('ws://localhost:8765/ws');
```

After fix: 0 occurrences of 8765 in client2d/.

### Consumption Chain Verified

| Layer | File | Action |
|-------|------|--------|
| Fix | `client2d/ws.js:7` | Port 8765 -> 8000 |
| Fix | `client2d/main.js:60,78` | msg_type + URL corrected |
| New | `start_server.py` | Factory + uvicorn on 8000 |
| Read | `aidm/server/app.py:53` | `_StubSession` bypassed when factory provided |
| Effect | Text input reaches `process_text_turn()`, resolves via real engine, events return to client |
| Test | PIPE-001..PIPE-008 (8/8 PASS) |

### Gate Results

**File:** `tests/test_ui_phase1_pipe_gate.py`
**Run:** `python -m pytest tests/test_ui_phase1_pipe_gate.py -v`

| Gate | Description | Result |
|------|-------------|--------|
| PIPE-001 | `start_server.py` imports cleanly | PASS |
| PIPE-002 | `build_simple_combat_fixture()` returns WorldState with 6 actors | PASS |
| PIPE-003 | `SessionOrchestrator` constructed from fixture | PASS |
| PIPE-004 | `create_app()` with factory; `_StubSession` not used | PASS |
| PIPE-005 | `player_utterance` routes to `process_text_turn()`, not UNKNOWN_MSG_TYPE | PASS |
| PIPE-006 | Attack intent returns at least one engine event | PASS |
| PIPE-007 | `hp_changed` event present after successful attack (seed=3 confirmed hit) | PASS |
| PIPE-008 | First WS connection = DM; second = PLAYER | PASS |

**Total: 8/8 PASS. 0 regressions in non-ws-server, non-immersion suite.**

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | Show `app.py` before/after - `_StubSession` bypassed when factory provided | CONFIRMED | `app.py:43-55`: stub is inside `if session_orchestrator_factory is None:` guard. When real factory passed, guard is not entered. PIPE-004 proves factory produces `SessionOrchestrator`, not `_StubSession`. |
| 2 | Show PIPE-005 routing trace - `player_utterance` reaches `process_text_turn()` | CONFIRMED | PIPE-005 PASS. Spy on `process_text_turn` confirms call count == 1. No `UNKNOWN_MSG_TYPE` error code in responses. |
| 3 | PIPE-006 must prove real engine fired - show actual event | CONFIRMED | PIPE-006 PASS. `process_text_turn("attack Goblin Warrior", "pc_fighter")` returns `events=('turn_start', 'attack_roll', 'turn_end')` at seed=42. Not stub output. |
| 4 | `start_server.py` must be runnable - include exact launch invocation | CONFIRMED | Launch: `python start_server.py`. PIPE-001 import test passes. Binds to `127.0.0.1:8000` via uvicorn. |
| 5 | Grep for 8765 - show all occurrences before fix; confirm only ws.js hardcode exists | CONFIRMED | Two occurrences pre-fix (ws.js:7 default, main.js:78 call). 0 occurrences post-fix. Both in client2d/ only - no other files affected. |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Read app.py:85, ws.js:1, main.js:60 before any edits. Confirmed all 3 gaps live. |
| Consume-site verified end-to-end | ML-002 | PASS | Write (client fix + start_server) -> Read (app.py factory param) -> Effect (process_text_turn fires) -> Test (PIPE-005,006,007). |
| No ghost targets | ML-003 | PASS | Rule 15c: all 3 gaps confirmed present before fixing. |
| Dispatch parity checked | ML-004 | N/A | No resolver function modified. Client-side fix + server entry point. No parallel resolver paths. |
| Coverage map updated | ML-005 | PASS (see below) | UI integration row added. |
| Commit before debrief | ML-006 | PASS | Commit 2b9db07 precedes this debrief. |
| PM Acceptance Notes addressed | ML-007 | PASS | All 5 confirmed above. |

---

## Pass 2 - PM Summary

Three one-line wiring gaps closed. Port `8765->8000` in ws.js and main.js. Message type
`player_input->player_utterance` in main.js. New `start_server.py` passes a real
`SessionOrchestrator` factory to `create_app()`, bypassing the `_StubSession` stub.
The 3v3 combat fixture from `build_simple_combat_fixture()` is live. All 8 gate tests
pass. The pipe is open: browser text input now reaches the engine and returns events.

---

## Pass 3 - Retrospective

### Findings During Execution

**FINDING-UI-PIPE-TARGET-AMBIGUITY-001 (LOW, OPEN)**
`"attack goblin"` is ambiguous in the 3v3 fixture (3 goblins: Goblin Warrior, Goblin Archer,
Goblin Skirmisher). The intent bridge returns `FC-AMBIG` with zero events rather than picking
the nearest/first. This is correct engine behavior (not a bug), but it means a player typing
bare "attack goblin" in the browser will get a clarification request, not an attack.
Client-side disambiguation UI is Stage 3+ scope. Logged for Stage 3 WO.

**FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001 (LOW, OPEN)**
`start_server.py` builds one fixture at import time and all sessions share the same
`WorldState` object. For Stage 1 (single player dev testing), this is correct. For Stage 2+
(multiple concurrent sessions), each factory call must produce a fresh fixture. The factory
closure will need to call `build_simple_combat_fixture()` inside `factory()`, not outside it.
Documented for Stage 2 WO.

**Observation: harness.py:203 pattern**
`harness.py` wraps `SessionOrchestrator` in an evaluation loop - it does not call
`uvicorn.run()`. The pattern is clean to copy for `start_server.py` because both layers
need the same `__init__` args. No hidden coupling discovered.

**Observation: asyncio deprecation warning in PIPE-005**
`asyncio.get_event_loop().run_until_complete()` triggers a deprecation warning in Python 3.10+
("There is no current event loop"). Non-fatal for this gate but a future test hygiene WO
should migrate ws_bridge tests to `asyncio.run()` or `pytest-asyncio`. Logged as LOW.

**FINDING-UI-PIPE-ASYNCIO-DEPRECATION-001 (LOW, OPEN)**
PIPE-005 uses `asyncio.get_event_loop().run_until_complete()` to drive the async bridge
call in a synchronous test. Deprecated in Python 3.10+. Future test hygiene: migrate to
`pytest-asyncio` and `async def test_*`. Does not affect gate result.

### Kernel Touches

None. This WO is pure plumbing (port, message type, entry point). No engine resolver
paths modified. No lifecycle, constraint, or topology kernel interactions.

### Out-of-Scope Items (not fixed)

- Enemy turn loop (GAP-04 + GAP-05) - Stage 2 WO
- Narration display, orb animations, grid, faction colors (GAP-06 through GAP-09, GAP-11) - Stage 3 WO
- Ability scores, dice tray, ability click (GAP-10, GAP-12) - Stage 4 WO

### Coverage Map Update

Row added to `docs/ENGINE_COVERAGE_MAP.md` (UI integration section):

| Mechanic | Status | WO | Notes |
|----------|--------|----|-------|
| Phase 1 Pipe (port + msg_type + factory) | IMPLEMENTED | WO-UI-PHASE1-PIPE-001 | Commit 2b9db07 |

### Radar

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-UI-PIPE-TARGET-AMBIGUITY-001 | LOW | OPEN | "attack goblin" ambiguous in 3-goblin fixture; client needs disambiguation UI (Stage 3+) |
| FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001 | LOW | OPEN | Shared WorldState across sessions - intentional for Stage 1; must fix before Stage 2 multi-session |
| FINDING-UI-PIPE-ASYNCIO-DEPRECATION-001 | LOW | OPEN | PIPE-005 uses deprecated `get_event_loop()` pattern; future test hygiene WO |
