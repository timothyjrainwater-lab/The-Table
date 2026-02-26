# WO-ANVIL-WS-AUDIT-001 — WebSocket Contract Validation Audit

**Issued:** 2026-02-25
**Lifecycle:** ACCEPTED — debrief filed 2026-02-25 (ANVIL_WS_AUDIT_001.md)
**Track:** QA / Architecture
**Priority:** HIGH — all client WOs after patch are building on unverified assumptions
**WO type:** AUDIT (read, compare, report — no code changes)
**Seat:** Anvil (BS Buddy)

---

## 1. Target Lock

The client was built against a WS contract that has never been validated against
a live engine session. The port mismatch (8765 vs 8000) is proof: nobody has ever
run client and engine together and watched a message flow.

Every event name the client listens for, every message type the client sends, every
field name in every payload — all of it is unverified assumption. Some of those
assumptions are already confirmed wrong (`player_input` vs `player_utterance`).
The question is how many more are quietly broken.

**Anvil's task:** Read the actual protocol definition and the actual engine emitters.
Map every WS event against what the client expects. Flag every mismatch.

This audit gates all future client WOs. No point building handlers against event
names that don't exist.

---

## 2. Files To Read

### Server-side (source of truth)

| File | What to look for |
|---|---|
| `aidm/server/ws_bridge.py` | All `await ws.send_json(...)` or equivalent calls — these are what the client actually receives. Exact `msg_type` values. Exact field names. |
| `aidm/server/app.py` | WS endpoint handler, message routing — what `msg_type` values does the server accept from the client? |
| Any `ws_protocol.py` or `protocol.py` if it exists | Canonical event name definitions |
| `aidm/core/play_loop.py` | What events does `execute_turn()` emit? What are the exact event type strings? |

### Client-side (what it expects)

| File | What to look for |
|---|---|
| `client2d/main.js` | Every `ws.on('...')` handler — event names it listens for |
| `client2d/dm-panel.js` | Every `ws.on('...')` handler |
| `client2d/notebook.js` | Every `ws.on('...')` handler (after patch deletes the violations) |
| `client2d/slip.js` | Every `ws.on('...')` handler, every `ws.send(...)` call |
| `client2d/sheet.js` | Every `ws.send(...)` call — msg_type values |
| `client2d/orb.js` | Every `ws.on('...')` handler |
| `client2d/map.js` | Every `ws.on('...')` handler |
| `client2d/ws.js` | The WsBridge implementation — how does `send()` serialize? How does `on()` dispatch? |

---

## 3. What To Produce

### Table A — Client Sends (outbound)

For every `ws.send(...)` in the client:

| Source | msg_type sent | Server accepts? | Field names match? | Status |
|---|---|---|---|---|
| `main.js` | `player_utterance` | ? | ? | ? |
| `sheet.js` | `ability_check_declare` | ? | ? | ? |
| `slip.js` | `roll_confirm` | ? | ? | ? |
| ... | | | | |

### Table B — Client Listens (inbound)

For every `ws.on('...')` in the client:

| Source | Event name listened for | Server actually emits? | Exact field names used | Status |
|---|---|---|---|---|
| `main.js` | `combat_start` | ? | — | ? |
| `dm-panel.js` | `narration` | ? | `d.text` | ? |
| `orb.js` | `speaking_start` | ? | — | ? |
| ... | | | | |

**Status values:**
- **MATCH** — name and fields confirmed correct
- **NAME DRIFT** — server emits different event name (e.g. `combat_started` vs `combat_start`)
- **FIELD DRIFT** — name correct but field names differ
- **GHOST** — client listens for event server never emits
- **UNHANDLED** — server emits event client never handles

---

## 4. Specific Hypotheses To Test

### Priority 0 — Security (check before anything else)

**CSWSH (Cross-Site WebSocket Hijacking) — HIGHEST PRIORITY.**
Read `aidm/server/app.py` WS upgrade handler and `ws_bridge.py`.

Answer these two questions:
1. Does the server validate the `Origin` header on WS upgrade and reject unknown origins?
2. Does the server require an auth token (query param, header, or first-message handshake)?

If the answer to either is NO, report immediately as CRITICAL — any webpage the user
visits can open a WebSocket to the local engine. This is not a theoretical risk.

### Priority 1 — Contract drift hypotheses

These are the high-probability mismatches based on the canary analysis:

| Hypothesis | Check |
|---|---|
| Server emits `combat_started` but client listens for `combat_start` | Read `ws_bridge.py` emit vs `main.js` `ws.on` |
| Server emits `speaking_begin` but client listens for `speaking_start` | Same |
| `roll_result` message is never emitted by engine — slip tray handshake is one-sided | Read play_loop for PENDING_ROLL → result flow |
| `bestiary_entry` event never emitted by engine | Confirm or deny |
| `character_state` field names in payload differ from what `sheet.js` reads | Compare emit payload vs client field access |
| `token_add` / `token_update` / `token_remove` event names match exactly | Confirm |

---

## 5. What Anvil Does NOT Do

- No code changes. Read, compare, report only.
- No fixes. Every mismatch becomes a finding for Slate to triage.
- No new WOs. Slate drafts from findings.
- Do not spend time on files not listed in Section 2.

---

## 6. Delivery

File report to: `pm_inbox/reviewed/ANVIL_WS_AUDIT_001.md`

**Required sections:**

1. **Files read** — confirm every file in Section 2 was read
2. **Table A** — complete outbound message map
3. **Table B** — complete inbound event map
4. **Mismatches** — every NAME DRIFT, FIELD DRIFT, GHOST, UNHANDLED entry listed
   as a structured finding: event name / file / expected / actual / severity
5. **Verdict** — CLEAN / MISMATCHES FOUND / PROTOCOL UNDEFINED

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Contract audit complete. Results filed."
```
