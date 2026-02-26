# ANVIL_WS_AUDIT_001 — WebSocket Contract Validation Report
**Filed:** 2026-02-25
**WO:** WO-ANVIL-WS-AUDIT-001
**Auditor:** Anvil (cold read)
**Type:** READ-ONLY AUDIT — no code changes

---

## 1. Files Read

Server-side:
- `aidm/server/ws_bridge.py` — WebSocket message serialization + routing
- `aidm/schemas/ws_protocol.py` — Protocol dataclass definitions
- `aidm/server/app.py` — WS endpoint, CORS, upgrade handler
- `aidm/core/play_loop.py` — Event emission from execute_turn()
- `aidm/core/combat_controller.py` — Combat event emission

Client-side:
- `client2d/ws.js` — WsBridge class, send/on/dispatch implementation
- `client2d/main.js` — WS event handlers, layout mode
- `client2d/dm-panel.js` — DM overlay handlers
- `client2d/notebook.js` — Notebook handlers (post CLIENT-PATCH-001 deletions)
- `client2d/slip.js` — Dice roll slip handlers
- `client2d/sheet.js` — Character state handlers
- `client2d/orb.js` — Speaker orb handlers
- `client2d/map.js` — Scene/token/fog handlers

---

## 2. Security Check — CRITICAL

### Origin Validation: **NO**
Evidence: `app.py` configures CORSMiddleware with `allow_origins=["*"]`. No Origin header validation at WebSocket upgrade.

### Auth Token Check: **NO**
Evidence: `ws_bridge.py` accepts WebSocket connection without auth pre-check. `SessionControl` join message (line 203) auto-generates a new session if none provided — not auth-gated.

**Verdict: OPEN_SECURITY_POSTURE**

Any webpage the user visits can open a WebSocket to `ws://localhost:8000/ws`. This is CSWSH (Cross-Site WebSocket Hijacking) exposure. The server has no defense. Risk is real on a local machine with active browser sessions.

Recommendation: add `Origin` header validation in the WS upgrade path to restrict connections to `localhost` origins only.

---

## 3. Table A — Client Sends (Outbound)

| Source File | msg_type sent | Server accepts? | Field names match? | Status |
|-------------|--------------|-----------------|-------------------|--------|
| `main.js` | `player_utterance` | YES (partial) | MISSING: `msg_id`, `timestamp` | **FIELD DRIFT** |
| `slip.js` | `roll_confirm` | NO | N/A | **GHOST** |
| `sheet.js` | `ability_check_declare` | NO | N/A | **GHOST** |
| `ws.js` | `session_control` (join) | YES | MATCH | **MATCH** |

---

## 4. Table B — Client Listens (Inbound)

| Source File | Event name | Server emits? | Fields accessed | Status |
|-------------|-----------|---------------|-----------------|--------|
| `main.js` | `speaking_start` | **NO** | (none) | **GHOST** |
| `main.js` | `speaking_stop` | **NO** | (none) | **GHOST** |
| `main.js` | `combat_start` | YES | (none) | **MATCH** |
| `main.js` | `combat_end` | UNCERTAIN | (none) | **NAME DRIFT?** |
| `dm-panel.js` | `speaking_start` | **NO** | `portrait_url` | **GHOST** |
| `dm-panel.js` | `speaking_stop` | **NO** | (none) | **GHOST** |
| `dm-panel.js` | `narration` | YES | `text` | **MATCH** |
| `orb.js` | `speaking_start` | **NO** | `portrait_url`, `text` | **GHOST** |
| `orb.js` | `speaking_stop` | **NO** | (none) | **GHOST** |
| `sheet.js` | `character_state` | YES | `name`, `class`, `level`, `hp`, `hp_max`, `ac`, `abilities.*` | **MATCH** |
| `slip.js` | `pending_roll` | **NO** | `id`, `formula` | **GHOST** |
| `slip.js` | `roll_result` | **NO** | `id`, `result` | **GHOST** |
| `map.js` | `scene_set` | **NO** | `cols`, `rows`, `grid`, `image_url` | **GHOST** |
| `map.js` | `scene_clear` | **NO** | (none) | **GHOST** |
| `map.js` | `token_add` | YES | `id`, `col`, `row`, `name`, `faction`, `hp`, `hp_max` | **MATCH** |
| `map.js` | `token_move` | **NO** | `id`, `col`, `row` | **GHOST** |
| `map.js` | `token_remove` | YES | `id` | **MATCH** |
| `map.js` | `token_update` | YES | `id`, `hp` | **MATCH** |
| `map.js` | `fog_reveal` | **NO** | `cells` | **GHOST** |
| `map.js` | `fog_reset` | **NO** | `rows`, `cols` | **GHOST** |
| `map.js` | `aoe_add` | **NO** | `id`, shape fields | **GHOST** |
| `map.js` | `aoe_clear` | **NO** | `id` | **GHOST** |

---

## 5. Verified Server Emitters

The following message types are confirmed emitted by the server:

| msg_type | Emitter location | Trigger |
|---------|-----------------|---------|
| `token_add` | `ws_bridge.py:295` | Session join (initial entity spawn) |
| `token_update` | `ws_bridge.py:549` | `hp_changed` engine event |
| `token_remove` | `ws_bridge.py:555` | `entity_defeated` engine event |
| `combat_start` | `ws_bridge.py:560` | `combat_started` event (combat_controller.py:179) |
| `character_state` | `ws_bridge.py:587` | After each turn, PC stats |
| `narration` | `ws_protocol.py` NarrationEvent | Narrative text output |
| `error` | `ws_protocol.py` ErrorEvent | Error conditions |
| `session_state` | `ws_protocol.py` SessionStateMsg | Session join response |

**Referenced but never emitted:**
`combat_end`, `speaking_start`, `speaking_stop`, `pending_roll`, `roll_result`, `scene_set`, `scene_clear`, `token_move`, `fog_reveal`, `fog_reset`, `aoe_add`, `aoe_clear`, `bestiary_entry`

---

## 6. Mismatches — Structured Findings

| Finding ID | Event | File(s) | Expected | Actual | Severity |
|-----------|-------|---------|----------|--------|----------|
| WS-F01 | `speaking_start` | main.js, dm-panel.js, orb.js | Server emits speaking event | Never emitted | **CRITICAL** |
| WS-F02 | `speaking_stop` | main.js, dm-panel.js, orb.js | Server emits speaking stop | Never emitted | **CRITICAL** |
| WS-F03 | `scene_set` | map.js | Server emits scene background | Never emitted | **CRITICAL** — map rendering disabled |
| WS-F04 | `pending_roll` | slip.js | Server emits roll request | Never emitted | **HIGH** — dice UI non-functional |
| WS-F05 | `roll_result` | slip.js | Server emits roll outcome | Never emitted | **HIGH** |
| WS-F06 | `roll_confirm` | slip.js | Server accepts roll confirmation | UNKNOWN_MSG_TYPE | **HIGH** |
| WS-F07 | `ability_check_declare` | sheet.js | Server accepts ability check | UNKNOWN_MSG_TYPE | **HIGH** |
| WS-F08 | `token_move` | map.js | Server emits movement | Never emitted | **HIGH** — movement visualization dead |
| WS-F09 | `combat_end` | main.js | Server emits combat end | Possibly `combat_ended` — ws_bridge.py checks for it but no emitter found | **MEDIUM** — NAME DRIFT suspected |
| WS-F10 | `scene_clear` | map.js | Server emits scene clear | Never emitted | **MEDIUM** |
| WS-F11 | `fog_reveal` | map.js | Server emits fog reveal | Never emitted | **MEDIUM** |
| WS-F12 | `fog_reset` | map.js | Server emits fog reset | Never emitted | **MEDIUM** |
| WS-F13 | `aoe_add`/`aoe_clear` | map.js | Server emits AoE visualization | Never emitted | **MEDIUM** |
| WS-F14 | `player_utterance` | main.js | Server requires `msg_id`, `timestamp` | Client sends without these | **MEDIUM** — FIELD DRIFT |

**Security findings:**

| Finding ID | Type | Description | Severity |
|-----------|------|-------------|----------|
| WS-SEC-001 | CSWSH | No Origin header validation on WS upgrade | **CRITICAL** |
| WS-SEC-002 | AUTH | No authentication token required on WS connection | **HIGH** |

---

## 7. Protocol Coverage

**Total client-expected message types:** 22
**Server-confirmed emitters:** 8
**Coverage:** ~36%

**Disabled UI systems:**
- NPC speaker portraits and orb pulse (WS-F01/F02)
- Scene background rendering (WS-F03)
- Dice roll visualization (WS-F04/F05/F06)
- Token movement display (WS-F08)
- Fog of war (WS-F11/F12)
- AoE visualization (WS-F13)

**Working UI systems:**
- Narration text (dm-panel.js)
- Character sheet stats (sheet.js)
- Combat layout switching (main.js)
- Token spawn/death/HP (map.js)

---

## 8. Verdict

**MISMATCHES FOUND — Protocol severely incomplete**

The client was built speculatively against a planned-but-not-implemented server contract. ~64% of the client's event handlers are dead code because the server never emits the corresponding messages. The most critical systems for visual gameplay (map, movement, speaking) are entirely disconnected.

**Immediate priority for Slate:** Triage findings into WOs:
1. **WS-SEC-001** — CSWSH Origin validation (security, standalone WO or app.py patch)
2. **WS-F01/F02** — speaking_start/speaking_stop server emitters (NPC persona system)
3. **WS-F03/F08** — scene_set/token_move (map rendering completeness)
4. **WS-F04/F05/F06** — roll flow (slip tray completeness)
5. **WS-F09** — combat_end/combat_ended name drift check

---

*Filed by Anvil cold-read agent. No code changes made.*
