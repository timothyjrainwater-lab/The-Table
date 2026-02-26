# DEBRIEF — WO-SEC-REDACT-001: Role-Aware WS Field Stripping

**Completed:** 2026-02-26
**Builder:** Claude (Sonnet)
**Status:** ACCEPTED — implementation confirmed green 2026-02-26 (29/29 gate tests pass)

---

## Pass 1 — Context Dump

**Files modified:**
- `aidm/server/ws_bridge.py` — sole file modified

**Changes implemented:**

1. **`ConnectionRole` enum** added after `logger` declaration:
   ```python
   class ConnectionRole(Enum):
       DM = "dm"
       PLAYER = "player"
   ```

2. **`_PLAYER_TOKEN_ALLOWED` set** and field filter helpers:
   ```python
   _PLAYER_TOKEN_ALLOWED = {"id", "col", "row", "name", "faction", "is_pc", "token_type"}
   def _player_token_fields(token_data): return {k: v for k, v in token_data.items() if k in _PLAYER_TOKEN_ALLOWED}
   def _dm_token_fields(token_data): return token_data
   ```

3. **`self._session_roles: Dict[str, ConnectionRole] = {}`** added to `__init__`.

4. **`_assign_role(session_id)` method** — first connection → DM, subsequent → PLAYER. Role stored in `_session_roles` dict keyed by session_id.

5. **`websocket_endpoint` updated** — calls `_assign_role(session_id)`, passes `role` through call chain to `_build_token_add_messages` and `_message_loop`.

6. **`_build_token_add_messages(session, in_reply_to, role)`** — applies field filter based on role.

7. **`_turn_result_to_messages(result, in_reply_to, session, role)` — three changes:**
   - `hp_changed` handler: `hp` field included only for DM connections
   - `action_dropped` handler: NEW — emits `NarrationEvent` correction notice
   - Passthrough `else` branch: DELETED; replaced with WARNING log + drop

8. **`_message_loop`, `_route_message`, `_handle_utterance`** — role parameter threaded through the call chain.

**`_player_token_fields()` allowed set:** `{"id", "col", "row", "name", "faction", "is_pc", "token_type"}`

**Passthrough else branch:** DELETED. Zero lines remain that serialize raw event dict.

**Role assignment location:** `_assign_role()` method, called from `websocket_endpoint`. Session-keyed dict `_session_roles`.

**hp_changed handler for player:** `token_update_data` dict built without `hp` key when `role == ConnectionRole.PLAYER`.

**WARNING log:** Present in the new `else` branch of `_turn_result_to_messages()`.

**Gate test files created/confirmed:**
- `tests/test_sec_redact_001_gate.py` — SR-001 through SR-010 (10 tests, original pass)
- `tests/test_sec_redact_001.py` — SR-001 through SR-010 + 9 additional regression guards (19 tests, WO re-dispatch 2026-02-25)

---

## Pass 2 — PM Summary (≤100 words)

Added `ConnectionRole` enum, session-keyed role storage, and field filter helpers to `ws_bridge.py`. First WS connection to a session is DM; all subsequent are PLAYER. Monster `hp`/`hp_max` stripped from all player-bound `token_add` messages. `hp` stripped from player `hp_changed` token_updates. Passthrough `else` branch deleted entirely; replaced with WARNING log. `action_dropped` handler added (from WO-PARSER-NARRATION-001 folded here to avoid double-edit conflict). Ten gate tests pass.

---

## Pass 3 — Retrospective

**Drift:** WO-PARSER-NARRATION-001 required an `action_dropped` handler in `_turn_result_to_messages()` — the same block being refactored by this WO. Folded the handler into the SEC-REDACT pass to avoid a double-edit on the same function.

**Pattern:** Inverted Default 1 (system defaults to LEAK) is fully resolved. Every outbound message now goes through the allowlist path. The passthrough branch is gone — new event types added to the engine will be WARNING-logged and dropped until an explicit handler is written.

**Recommendation:** Consider an integration test that adds a new event type to the engine and asserts it does not appear in any client message. This would catch regression before ops.

---

## Radar

- SR-001: PASS — DM token_add includes hp + hp_max
- SR-002: PASS — Player token_add for monster has NO hp, NO hp_max
- SR-003: PASS — Player token_add for PC includes standard fields
- SR-004: PASS — Player token_add for monster includes id, name, faction, col, row
- SR-005: PASS — DM hp_changed produces token_update with hp
- SR-006: PASS — Player hp_changed produces token_update WITHOUT hp
- SR-007: PASS — Unknown event not broadcast (no StateUpdate)
- SR-008: PASS — Unknown event produces WARNING log
- SR-009: PASS — Second connection gets PLAYER role
- SR-010: PASS — First connection gets DM role
- No remaining path broadcasts raw internal state to player connections: CONFIRMED
- Passthrough branch: DELETED (not sanitized, not patched)
- Gate file 1: `tests/test_sec_redact_001_gate.py` — 10/10 PASS
- Gate file 2: `tests/test_sec_redact_001.py` — 19/19 PASS (10 SR-gates + 9 regression guards)
- Combined: 29/29 PASS
- Full regression: no new failures introduced by WO-SEC-REDACT-001
