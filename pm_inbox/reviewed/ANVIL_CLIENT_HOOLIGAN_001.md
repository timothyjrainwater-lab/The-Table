# Client Hooligan Run — ANVIL-CLIENT-HOOLIGAN-001
**Filed by:** Anvil (BS Buddy seat — Cinder Voss methodology)
**Date:** 2026-02-25 14:16 CST-CN (updated 2026-02-25 after full pass)
**Session:** Interactive with Thunder — live eyes-on `http://localhost:8080`
**Method:** Adversarial probing. No happy path. Top-rope finisher first.

---

## Verdict: FINDINGS — Seven confirmed violations across full client pass

---

## Section 1 — Run Summary

Live browser session. Server: `uvicorn aidm.server.app:app` (stub session factory).
Client: `python -m http.server 8080` serving `client2d/`.

Full pass completed across all client files:
`notebook.js`, `main.js`, `dm-panel.js`, `slip.js`, `sheet.js`, `map.js`, `ws.js`,
`orb.js`, `style.css`, `index.html`.

Evidence is in the source. No speculation. Seven confirmed violations. Three are
structural (client can never connect to backend in current state).

---

## Section 2 — Confirmed Violations

### VIOLATION-001 — GT NB-004 AUTOWRITE BAN
**Severity:** CRITICAL
**File:** `client2d/notebook.js` lines 55–71

```javascript
bridge.on('narration', function (d) {
  var text = (d && d.text) ? d.text : '';
  if (!text) return;
  var line = document.createElement('div');
  line.className = 'nb-transcript-line';
  line.textContent = text;
  transcriptPanel.appendChild(line);   // AUTOWRITE. NO CONSENT.
  ...
});
```

**Violation:** Every `narration` WS event appends directly to the notebook transcript.
No `ConsentRequested` fired. No `ConsentGranted` checked. No consent handshake of any kind.

The write-lock icon (⚿) exists only on the Draw tab. Transcript is wide open.

**The proof:** Sit at the table. Say nothing. Do nothing. Watch the notebook fill itself
from DM narration. Full session log written without consent. GT NB-004 absolute ban violated.

**GT NB-004 text:** "No autowrite. No silent 'helpful logging.'"

**Fix:** Remove lines 55–71 from `notebook.js` immediately. Do not wait for the notebook
rebuild WO. The `narration` listener must be dead code until the consent handshake is
implemented. When the full notebook is rebuilt, Transcript writes must flow through:
`ConsentRequested` → `ConsentGranted` → `NotebookWriteApplied`.

---

### VIOLATION-002 — GT HL-004 TWO-BOOK DOCTRINE
**Severity:** HIGH
**File:** `client2d/notebook.js` lines 73–83

```javascript
bridge.on('bestiary_entry', function (d) {
  var card = document.createElement('div');
  card.className = 'nb-bestiary-card';
  card.innerHTML = ...
  bestiaryPanel.appendChild(card);   // BESTIARY IN NOTEBOOK. WRONG ARTIFACT.
});
```

**Violation:** Bestiary/Beast Journal entries written into the Notebook artifact.
GT HL-004 is explicit: Beast Journal lives in the Rulebook/Beast Book, NOT in the Notebook.
Notebook is player-authored content only. Beast entries are reference canon.

**Fix:** Remove lines 73–83 from `notebook.js` immediately. Beast Journal implementation
belongs in WO-UI-RULEBOOK-001. The "Bestiary" tab in the notebook is wrong by design.

---

### VIOLATION-003 — WRONG MESSAGE TYPE: CLIENT SENDS player_input, PROTOCOL EXPECTS player_utterance
**Severity:** HIGH
**File:** `client2d/main.js` line 24

```javascript
function submitInput() {
  const text = playerInput.value.trim();
  if (!text) return;
  ws.send({ msg_type: 'player_input', text: text });   // WRONG TYPE
  playerInput.value = '';
}
```

**Violation:** Client sends `msg_type: 'player_input'`. The WS protocol defines
`player_utterance` as the canonical message type for player text input. The server's
play loop routes on `player_utterance`. Player text input is silently dropped on the
server side. The text bar has never worked.

**Fix:** Change `player_input` → `player_utterance`. One character change. Unblock the
entire text input path.

---

### VIOLATION-004 — WRONG PORT: CLIENT DIALS 8765, SERVER RUNS ON 8000
**Severity:** HIGH (structural — client cannot connect)
**File:** `client2d/main.js` line 42

```javascript
const ws = new WsBridge('ws://localhost:8765/ws');   // WRONG PORT
```

**Violation:** Server starts on port 8000 (`uvicorn aidm.server.app:app --port 8000`).
Client dials `ws://localhost:8765/ws`. The WebSocket connection fails on every load.
WS status dot shows connecting → disconnected on every session. The client has never
had a live backend connection during this WO.

**Fix:** Change port to 8000. `new WsBridge('ws://localhost:8000/ws')`.

---

### VIOLATION-005 — DEAD NARRATION HANDLER: #transcript-area DOES NOT EXIST
**Severity:** MEDIUM
**File:** `client2d/main.js` lines 84–95

```javascript
const transcriptArea = document.getElementById('transcript-area');   // NULL

ws.on('narration', function (data) {
  if (!transcriptArea) return;   // always returns — element never existed
  ...
});
```

**Violation:** `main.js` registers a `narration` handler referencing `#transcript-area`.
That element does not exist in `index.html`. The handler silently no-ops on every
narration event. This is dead code from FIND-WIRING-004 (prior session). Three separate
`narration` handlers are now registered simultaneously (`main.js`, `notebook.js`,
`dm-panel.js`) — only `dm-panel.js` is wired to a real element.

**Fix:** Remove the dead handler from `main.js` lines 84–95. One narration handler
(`dm-panel.js`) is the correct owner.

---

### VIOLATION-006 — COMBAT DETECTION BROKEN: dm-panel.js CHECKS WRONG CLASS
**Severity:** HIGH
**File:** `client2d/dm-panel.js` line 17

```javascript
function isCombat() {
  return document.body.classList.contains('combat-active');   // NEVER TRUE
}
```

**Violation:** `dm-panel.js` branches on `combat-active`. The engine fires
`combat_start` / `combat_end` events. `main.js` responds by toggling `mode-combat`
/ `mode-explore` on `document.body`. The class `combat-active` is set NOWHERE in
the entire codebase. `isCombat()` always returns `false`. The combat branch of
dm-panel (orb-transcript mode) is permanently dead. Combat narration goes to
`panelText` instead of `orb-transcript` in every combat encounter.

**Fix:** Change `combat-active` → `mode-combat`. One string. Unlocks the combat
narration path.

---

### VIOLATION-007 — SLIP CLICK BYPASSES TOWER RITUAL
**Severity:** MEDIUM (doctrine violation — UI Memo dice tower doctrine)
**File:** `client2d/slip.js` lines 24–31

```javascript
el.addEventListener('click', function () {
  if (el.classList.contains('pending')) {
    el.classList.remove('pending');
    el.classList.add('stamped');
    var bridge = window.__ws;
    if (bridge) bridge.send({ msg_type: 'roll_confirm', id: id });   // CLICK = CONFIRM
  }
});
```

**Violation:** Clicking a roll slip sends `roll_confirm` to the server. This means
clicking a card on a tray performs the authoritative roll confirmation. The UI Memo
dice tower doctrine is explicit:

> Authoritative roll requires: PENDING_ROLL(spec) → player selects correct dice →
> drops into tower → runtime validates → Box result → UI animates forced outcome.

Slip click is a "roll button" by another name. It bypasses the tower drop entirely.
The slip should be read-only — a receipt, not a trigger. Confirmation must come
from the tower drop path, not a click event.

**Fix:** Remove the click handler from `makeSlip()`. Slip tray is archive/receipt
only. The roll confirmation event must come from the dice tower interaction path
(not yet implemented — this WO surfaces that the slip is pre-empting the ritual).

---

## Section 3 — Attack Surface Notes (Structural — No Fix Needed, Slate Awareness)

These are not doctrine violations but surface findings Slate should track:

**A — window.__ws GLOBAL EXPOSURE**
`main.js` line 119: `window.__ws = ws;`
The WsBridge is exposed on window. Any injected script or DevTools console command
can call `window.__ws.send({...})` to inject arbitrary messages to the server.
Intended for debugging per code comment. Acceptable for dev. Flag for production
hardening.

**B — DEAD DATA-POSTURE ATTRIBUTES ON SHELF BUTTONS**
`index.html` lines 107–113: shelf buttons carry `data-posture="posture-down"` /
`data-posture="posture-dice"`. Posture system was removed in WO-UI-POSTURE-AUDIT-001.
These attributes are dead. No JS reads them. Cosmetic noise — no behavior impact,
but stale doctrine residue.

**C — UNIMPLEMENTED DRAWERS REFERENCED IN HTML**
`index.html` lines 110–113: `#shelf-tome` references `data-drawer="tome-drawer"` and
`#shelf-dice-bag` references `data-drawer="dice-drawer"`. Neither `tome-drawer` nor
`dice-drawer` elements exist in `index.html`. Tome (Rulebook) and Dice Bag drawers
are not built. Buttons are dead on click. Not a violation — these are unbuilt WOs
(WO-UI-RULEBOOK-001, WO-UI-DICETOOLS-001). Tracking note only.

**D — NO WS SEND RATE LIMITING**
`ws.js`: `send()` has no rate limiting. PROBE-001 (40x rapid fire) is a valid
attack path against the play loop. Unconfirmed until live engine session.

---

## Section 4 — Probe List (Requires Live Engine — Not Yet Executed)

These require a real session or DevTools WS access. Unconfirmed. Slate to assign.

| ID | Probe | Target Law | Method |
|---|---|---|---|
| PROBE-001 | Spam send 40x in 2 seconds | Play loop stability | Rapid-fire `player_utterance` via WS |
| PROBE-002 | "I kill the DM" — does Spark narrate success or leak hidden state? | HL-001, HL-005 | Text input, observe narration |
| PROBE-003 | Drag token off-map (-9999, -9999) | Map bounds validation | DevTools WS inject bad `TOKEN_MOVE_INTENT` |
| PROBE-004 | Inject `{"msg_type":"combat_started"}` manually | Layout slide robustness | DevTools WS console, no real session |
| PROBE-005 | Fire `combat_ended` before `combat_started` | Event ordering safety | DevTools WS, reverse order |
| PROBE-006 | Hold voice 90 seconds of silence | STT hang / play loop stall | Mic input, observe loop |
| PROBE-007 | F5 mid-session | Session/world state persistence | Browser refresh during active session |
| PROBE-008 | Same utterance twice rapid-fire | WorkingSet determinism | Same input, compare output events |

---

## Section 5 — Recommended Slate Actions

1. **STOP-AND-FIX (three violations kill all live testing):**
   - VIOLATION-004: fix port 8765 → 8000 (client is deaf right now)
   - VIOLATION-003: fix msg_type `player_input` → `player_utterance` (text bar broken)
   - VIOLATION-006: fix `combat-active` → `mode-combat` in dm-panel.js (combat path dead)

2. **Immediate patch WO** — Remove from `notebook.js`:
   - Lines 55–71 (narration autowrite — GT NB-004 CRITICAL)
   - Lines 73–83 (bestiary in notebook — GT HL-004 HIGH)
   Two cuts. No design. Do it now.

3. **Slip tray doctrine patch** — Remove click handler from `slip.js` `makeSlip()`.
   Slip is archive/receipt only. Tower path owns authoritative roll confirmation.

4. **Gate tests** — After patch, add regression tests confirming:
   - No `narration` event handler writes to notebook without `ConsentGranted`
   - No `bestiary_entry` handler exists in `notebook.js`
   - Client WS URL is port 8000
   - `isCombat()` checks `mode-combat`

5. **Probe execution WO** — Assign PROBE-001 through PROBE-008 to a builder with a real
   session fixture. VIOLATION-003 and VIOLATION-004 must be fixed first or probes cannot run.

---

*Cinder Voss methodology. The lock was cosmetic. The cage was already open.*
*And when I looked closer: three of the walls were just painted on.*
*Seven Wisdoms. Zero Regrets.*
