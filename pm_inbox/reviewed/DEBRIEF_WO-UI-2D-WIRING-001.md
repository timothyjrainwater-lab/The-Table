# DEBRIEF — WO-UI-2D-WIRING-001

**Gate:** UI-2D-WIRING 10/10 ✓
**Filed by:** Anvil (BS Buddy seat, interactive session with Thunder)
**Date:** 2026-02-25

---

## Pass 1 — Context Dump

### Files changed

**`aidm/server/ws_bridge.py`**
- Added `_make_raw_msg(msg_type, data, in_reply_to)` helper (module-level function, ~25 lines). Returns a `ServerMessage` subclass with an overridden `to_dict()` that merges custom payload fields with the standard envelope. This avoids creating new dataclasses for every new message type while satisfying `_send_message`'s `msg.to_dict()` requirement.
- `_turn_result_to_messages()` signature extended with optional `session: Any = None` parameter.
- Generic `state_update` loop replaced with typed routing: `hp_changed` → `token_update`, `entity_defeated` → `token_remove`, `combat_started` → `combat_start`, `combat_ended` → `combat_end`. All other event types keep the existing `StateUpdate` passthrough.
- `character_state` emission added after the events loop. Reads `session.world_state.entities`, finds first entity with `EF.TEAM == "player"`, emits `character_state` with name/class/level/hp/hp_max/ac/abilities.
- Added `_build_token_add_messages(session, in_reply_to)` helper. Iterates `session.world_state.entities`, emits `token_add` for each entity with a valid `EF.POSITION` (`{"x": int, "y": int}`). Entities with no position skipped silently.
- `websocket_endpoint()`: after sending snapshot, calls `_build_token_add_messages` and sends each result.
- Both `process_text_turn` and `process_voice_turn` callers updated to pass `session` to `_turn_result_to_messages`.

**`client2d/main.js`**
- Wildcard stub `handled` array updated to include: `token_add`, `token_update`, `token_remove`, `token_move`, `character_state`. Truly unknown types still log to console.

**`client2d/orb.js`**
- Added `window.ORB_STANCE_CONFIG` object at top of IIFE. Keys: `STANDARD`, `BATTLE`, `DOWN`, `DICE`, `SPEAKING`. Values: empty strings (Thunder to point at assets interactively). Config is globally accessible for runtime patching.

**`tests/test_ui_2d_wiring.py`** (new)
- 10 gate tests, all passing.

---

### Confirmed assumptions

| Assumption | Result |
|---|---|
| `WorldState.entities` — plain dict keyed by entity_id | ✓ Confirmed |
| `EF.POSITION` format | `{"x": int, "y": int}` — mapped to `col`/`row` in bridge |
| `EF.TEAM` values | `"player"` and `"monsters"` |
| Entity name field | Plain `"name"` key — no EF constant |
| `combat_started` event_type string | `"combat_started"` at `combat_controller.py:179` ✓ |
| `TurnResult` carries world_state | **WRONG** — TurnResult has no world_state field. Fixed by passing `session` to `_turn_result_to_messages`. |
| `_send_message` accepts plain dict | **WRONG** — requires `ServerMessage` with `.to_dict()`. Fixed by `_make_raw_msg` inline subclass. |

---

### Open findings

| ID | Severity | Description |
|---|---|---|
| FIND-WIRING-001 | LOW | `combat_ended` event type string not found in engine. `combat_controller.py` emits `combat_started` (line 179) but no matching end event. `play_loop.py` and `combat_controller.py` have no `combat_ended` emission. Wired to `"combat_ended"` string per WO spec — will activate when engine emits it. |
| FIND-WIRING-002 | LOW | `character_state` emits only for first `"player"` team entity. Multi-PC support deferred. |
| FIND-WIRING-003 | INFO | Starlette was not installed in the project venv — `test_ws_bridge.py` was failing collection. Installed `starlette==0.52.1` to enable import. |
| FIND-WIRING-004 | INFO | Dead narration handler in `main.js` (lines 109-120, references `#transcript-area` which doesn't exist) left in place — out of scope for this WO. |

---

## Pass 2 — PM Summary (≤100 words)

Server→client event pipeline wired. `hp_changed` → `token_update`, `entity_defeated` → `token_remove`, `combat_started` → `combat_start`, `combat_ended` → `combat_end`. Character state emitted after each turn for first player entity. Token add emitted on session join for all positioned entities. `main.js` stub updated. `orb.js` stance config object exposed for Thunder-directed polish. Gate UI-2D-WIRING 10/10. One gap: `combat_ended` engine event not found — wired but will be inert until engine emits it.

---

## Pass 3 — Retrospective

**Drift caught:**
- WO spec assumed `TurnResult` carries `world_state`. It does not — `TurnResult` is a pure result DTO. Fix: added `session` param to `_turn_result_to_messages`. Callers already had `session` in scope.
- WO spec assumed `_make_raw_msg` could return a plain dict that `_send_message` would serialize. `_send_message` calls `msg.to_dict()` — requires a `ServerMessage` instance. Fix: inline `_RawMsg` subclass with overridden `to_dict()`.
- `combat_ended` event type not present in engine. WO spec said "check `combat_controller.py`" — checked, not there. Wired the string defensively; filed as FIND-WIRING-001.

**Patterns worth noting:**
- The bridge's `_send_message` → `msg.to_dict()` pattern means any new message type needs either a dataclass or the `_make_raw_msg` helper. The helper is the right lightweight solution for typed messages that don't need `from_dict`.
- `_build_token_add_messages` as a separate method (not inline in `websocket_endpoint`) made it directly testable without async machinery — good pattern for future bridge methods.

**Recommendations for next WO:**
- Add `combat_ended` event emission to the engine (likely in `play_loop.py` when all monsters are defeated). Once emitted, FIND-WIRING-001 resolves automatically.
- Interactive polish session with Thunder: point `ORB_STANCE_CONFIG` paths at actual assets. The config is live at `window.ORB_STANCE_CONFIG` in the browser console.
- Dead narration handler in `main.js` (lines 109-120) should be cleaned up in a dedicated client cleanup WO.
