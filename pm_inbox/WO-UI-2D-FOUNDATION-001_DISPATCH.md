# WO-UI-2D-FOUNDATION-001 — 2D Illustrated Table Client Foundation

**Type:** Builder WO
**Gate:** UI-2D-FOUNDATION
**Tests:** 10 (2D-01 through 2D-10)
**Depends on:** Nothing (standalone new client)
**Blocks:** All subsequent 2D UI WOs
**Priority:** HIGH — replaces Three.js client track

---

## Context (read before building)

The Three.js client (`client/`) is frozen. Do not touch it. This WO builds a new
`client2d/` directory — a completely separate, self-contained 2D client. Vanilla JS,
no build step, no TypeScript, no npm. Opens directly in a browser as a static file.

The backend (Python engine, WS server) does not change. The WS protocol does not
change. The new client connects to `ws://localhost:8765/ws` and speaks the **exact
same JSON message format with the exact same `msg_type` strings** as the existing
3D client. No adapter. No translation layer. No new protocol dialect.

---

## Vision (read this before writing a single line of code)

**"A candlelit tavern table, seen from above — real objects, real paper, real stamps —
where the crystal ball is the DM."**

This is not a game UI. This is not a retro pixel game. This is a 2D illustrated
tabletop surface. Every pixel is a physical object or the table it sits on. No
floating panels. No tooltips. No HUD chrome. No menus.

**Style:** Ink-sprite hybrid, artifact-first. Materials are illustrated, not
photographed. Walnut = CSS gradient. Parchment = off-white + noise. Leather = warm
dark tone + shadow. No external texture files required for this WO.

**The vibe comes from:** warm vignette, consistent material language, soft drop
shadows on every artifact, amber glow on the crystal ball. Not from animation
complexity or polygon count.

---

## 1. Target Lock

Deliver a working `client2d/` folder containing:

- `client2d/index.html` — entry point, loads the other files
- `client2d/style.css` — all CSS, palette, posture classes, artifact styles
- `client2d/ws.js` — WebSocket connection, reconnect logic, message routing
- `client2d/main.js` — zone layout, posture switching, event wiring

The result must:
- Connect to the backend WS and stay connected (auto-reconnect)
- Render the table as a layered 2D illustrated scene on a walnut/vignette background
- Show five named zones as positioned regions on the table surface
- Support four posture transitions via keyboard hotkeys 1-4 — smooth CSS transition
- Display the crystal orb in DM_ZONE — glows amber idle, pulses brighter on `speaking_start`
- Display a placeholder battle map scroll in VAULT_ZONE
- Display placeholder shelf objects in SHELF_ZONE
- Display a placeholder roll slip tray in DICE_ZONE
- Have the text input bar fixed at bottom — Enter/Send → `player_input` WS message
- Have a diegetic WS status indicator (not a browser-style status bar)

This WO delivers the **skeleton only**. No live data wired to sheet/notebook/map yet.
Subsequent WOs handle each artifact in isolation.

---

## 2. File Structure (mandatory — do not deviate)

```
client2d/
  index.html      ← HTML structure only, loads css + js files
  style.css       ← ALL styles, palette variables, posture classes, artifact styles
  ws.js           ← WebSocket class: connect, reconnect, send, on(msgType, handler)
  main.js         ← Entry point: instantiates WS, wires events, handles posture keys
```

**Hard rule:** No inline styles in HTML. No inline scripts in HTML. All JS in `.js`
files. All CSS in `style.css`. Subsequent WOs will each add one new `.js` file
(e.g., `map.js`, `sheet.js`, `slip.js`) and import it in `index.html`. This keeps
each builder's scope surgical and prevents context-window sprawl.

---

## 3. Visual Design Spec

### Palette (CSS custom properties in `:root`)

```css
:root {
  --walnut-dark:    #2a1f14;   /* table edge / deep shadow */
  --walnut-mid:     #3d2b1a;   /* main table surface */
  --walnut-warm:    #5c3d22;   /* raised areas, rail */
  --felt-deep:      #1a2a1a;   /* vault inset (dark green felt) */
  --parchment:      #f4ead5;   /* map, slip paper */
  --parchment-aged: #e8d5b0;   /* slightly darker parchment */
  --ink:            #1a1208;   /* text, grid lines */
  --leather-warm:   #6b3d2e;   /* notebook, bag */
  --leather-dark:   #3d1f14;   /* tome, darker leather */
  --brass:          #8b6914;   /* corner details, accents */
  --wax-red:        #8b1a1a;   /* wax seal */
  --amber-idle:     rgba(255, 180, 60, 0.3);   /* orb idle glow */
  --amber-speak:    rgba(255, 200, 80, 0.7);   /* orb speaking glow */
  --vignette:       radial-gradient(ellipse at center,
                      transparent 40%, rgba(20,12,5,0.7) 100%);
}
```

### Table surface

```css
body {
  background-color: var(--walnut-mid);
  background-image: linear-gradient(
    160deg,
    var(--walnut-dark) 0%,
    var(--walnut-warm) 50%,
    var(--walnut-dark) 100%
  );
}

/* Vignette overlay — fixed, pointer-events: none */
#vignette {
  position: fixed; inset: 0;
  background: var(--vignette);
  pointer-events: none;
  z-index: 100;
}
```

### Artifacts: drop shadow on every object

Every zone/artifact div gets:
```css
box-shadow: 0 4px 16px rgba(0,0,0,0.6), 0 1px 4px rgba(0,0,0,0.4);
```

This is what makes objects feel "placed on the table."

---

## 4. Zone Layout

Five named zones. CSS Grid layout on `#table`. Zone sizing shifts per posture class.

```
┌─────────────────────────────────────────────┐
│  #dm-zone                                   │
│  Crystal orb. Centered. Dark walnut bg.     │
├─────────────────────────────────────────────┤
│  #vault-zone                                │
│  Battle map canvas. Dark felt inset.        │
├──────────────────┬──────────────────────────┤
│  #work-zone      │  #dice-zone              │
│  Handout area    │  Roll slip tray          │
├──────────────────┴──────────────────────────┤
│  #shelf-zone                                │
│  Sheet | Notebook | Tome | Dice bag         │
└─────────────────────────────────────────────┘
│  #text-input-bar (fixed, always visible)    │
└─────────────────────────────────────────────┘
```

### Posture classes (on `<body>`)

| Posture | Key | Class | Effect |
|---------|-----|-------|--------|
| STANDARD | 1 | `posture-standard` | Balanced — all zones visible |
| LEAN_FORWARD | 2 | `posture-lean` | Vault zone expands (flat top-down, no perspective) |
| DOWN | 3 | `posture-down` | Shelf zone expands, vault shrinks |
| DICE_TRAY | 4 | `posture-dice` | Dice zone expands |

All zone size changes via CSS class only. No JS layout calculation. Transition:
`transition: all 0.35s ease-in-out` on all zone elements.

LEAN_FORWARD is **flat** — the map simply gets larger. No perspective transform.
No CSS `perspective`. No `transform: rotateX()`. Flat and reliable for v1.

---

## 5. Crystal Orb

```html
<div id="dm-zone">
  <div id="orb">
    <div id="orb-portrait"></div>  <!-- NPC portrait placeholder: empty for now -->
  </div>
</div>
```

```css
#orb {
  width: 120px; height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%,
    #c8a040, #3a2800);
  box-shadow:
    0 0 24px 8px var(--amber-idle),
    0 4px 16px rgba(0,0,0,0.8);
  transition: box-shadow 0.4s ease;
}

#orb.speaking {
  box-shadow:
    0 0 48px 16px var(--amber-speak),
    0 4px 16px rgba(0,0,0,0.8);
  animation: orb-pulse 1.2s ease-in-out infinite;
}

@keyframes orb-pulse {
  0%, 100% { box-shadow: 0 0 48px 16px var(--amber-speak), 0 4px 16px rgba(0,0,0,0.8); }
  50%       { box-shadow: 0 0 64px 24px var(--amber-speak), 0 4px 16px rgba(0,0,0,0.8); }
}
```

WS wiring in `main.js`:
```js
ws.on('speaking_start', () => document.getElementById('orb').classList.add('speaking'));
ws.on('speaking_stop',  () => document.getElementById('orb').classList.remove('speaking'));
```

---

## 6. Roll Slip Tray (placeholder)

```html
<div id="dice-zone">
  <div id="slip-tray">
    <div id="slip-tray-label">Roll Slip Tray</div>
    <!-- Pending slips injected here by future WO-UI-2D-SLIP-001 -->
  </div>
</div>
```

Styled as a shallow parchment-colored tray with aged paper texture (CSS gradient).
This is a placeholder — the full ritual (PENDING_ROLL → slip prints → wax stamp →
result) is implemented in `WO-UI-2D-SLIP-001`. This WO only establishes the tray
as a positioned zone element.

---

## 7. WS Module (`ws.js`)

```js
class WsBridge {
  constructor(url = 'ws://localhost:8765/ws') { ... }
  connect() { ... }          // auto-reconnect, max 10 retries, 2s delay
  send(obj) { ... }          // JSON.stringify + ws.send
  on(msgType, handler) { ... } // register handler for msg_type
  // onmessage routes by msg_type, fires wildcard '*' handlers too
}
```

On connect: send `{msg_type: 'session_control', command: 'join', msg_id: uuid, timestamp: Date.now()/1000}`

WS status indicator: a small div `#ws-status` styled as a candle-flame icon or
amber dot — positioned at table edge (not a browser chrome bar).
Classes: `ws-status-connecting`, `ws-status-connected`, `ws-status-disconnected`.

---

## 8. Text Input Bar

```html
<div id="text-input-bar">
  <input type="text" id="player-input" placeholder="speak your action...">
  <button id="send-btn">⏎</button>
</div>
```

- Enter key or button click → `ws.send({msg_type: 'player_input', text: value})` → clear input
- Suppress posture hotkeys (1-4) when input is focused
- Styled: dark walnut bar, parchment-colored input field, brass-toned button

---

## 9. WS Message Handling

Wire these in `main.js` for this WO. Everything else is a `console.log` stub.

| `msg_type` | Action |
|-----------|--------|
| `speaking_start` | `orb.classList.add('speaking')` |
| `speaking_stop` | `orb.classList.remove('speaking')` |
| `combat_start` | Add class `combat-active` to `#vault-zone` (future map WO uses this) |
| `combat_end` | Remove class `combat-active` from `#vault-zone` |
| `narration` | Append `data.text` to `#transcript-area` if element exists |
| All others | `console.log('[WS stub]', data.msg_type, data)` |

---

## 10. Gate Tests (UI-2D-FOUNDATION 10/10)

File: `tests/test_ui_2d_foundation_gate.py`

Tests use Python `html.parser` + string search. No browser required.

| ID | Description |
|----|-------------|
| 2D-01 | `client2d/index.html` exists and parses as valid HTML |
| 2D-02 | `client2d/style.css`, `client2d/ws.js`, `client2d/main.js` all exist |
| 2D-03 | No Three.js references anywhere in `client2d/` (`THREE`, `WebGLRenderer`, `PerspectiveCamera`) |
| 2D-04 | No npm/node references (`require(`, `node_modules`, `import from`) in `client2d/` |
| 2D-05 | `style.css` contains all palette variables: `--walnut-mid`, `--parchment`, `--amber-idle`, `--amber-speak`, `--wax-red` |
| 2D-06 | `index.html` contains all five zone IDs: `dm-zone`, `vault-zone`, `work-zone`, `dice-zone`, `shelf-zone` |
| 2D-07 | `style.css` contains all four posture classes: `posture-standard`, `posture-lean`, `posture-down`, `posture-dice` |
| 2D-08 | `main.js` contains keydown handler and keys `'1'` `'2'` `'3'` `'4'` |
| 2D-09 | `main.js` contains `speaking_start` and `speaking_stop` handlers wiring orb class |
| 2D-10 | `ws.js` contains `ws://localhost:8765/ws` and `player_input` send on text submit |

---

## 11. Delivery Footer

**Files to create:**
```
client2d/index.html
client2d/style.css
client2d/ws.js
client2d/main.js
tests/test_ui_2d_foundation_gate.py
```

**Files to NOT touch:**
- `client/` — frozen
- All Python engine files
- All existing gate tests

**Commit requirement:**
```
feat: WO-UI-2D-FOUNDATION-001 — 2D illustrated table client skeleton — Gate UI-2D-FOUNDATION 10/10
```

**Preflight:**
```
pytest tests/test_ui_2d_foundation_gate.py -v
```
10/10 must pass.

**Visual confirmation required (mandatory):** Builder opens `client2d/index.html`
in a browser. Confirms: walnut background visible, vignette overlay present, orb
visible in DM zone with amber glow, five zones laid out, keys 1-4 shift posture
with smooth transition, text input bar at bottom. Include screenshot or written
description in debrief.

---

## 12. What Comes Next (not this WO — do not build these)

| WO | Scope | File added |
|----|-------|-----------|
| WO-UI-2D-MAP-001 | Battle map canvas: grid, fog, token sprites, AoE | `map.js` |
| WO-UI-2D-SLIP-001 | Roll slip ritual: PENDING_ROLL → slip → wax stamp → result | `slip.js` |
| WO-UI-2D-SHEET-001 | Character sheet panel: live WS data, clickable abilities | `sheet.js` |
| WO-UI-2D-NOTEBOOK-001 | Notebook: draw strokes, transcript tab, bestiary tab | `notebook.js` |
| WO-UI-2D-ORB-001 | Orb portrait wiring: NPC portrait swap on WS events | `orb.js` |

Each WO adds one file. Each builder reads one file. No sprawl.

---

## 13. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
