# WO-UI-2D-ORB-001 — Speaker Panel Wiring: Portrait, Beats, Orb Pulse

**Type:** Builder WO
**Gate:** UI-2D-ORB
**Tests:** 12 (ORB-01 through ORB-12)
**Depends on:** WO-UI-2D-RELAYOUT-002 (ACCEPTED cbd5d9b — `#speaker-panel`, `#speaker-portrait`, `#speaker-beats`, `#orb` all exist on disk)
**Blocks:** WO-UI-2D-DM-PANEL-001
**Priority:** HIGH — DM presence; can dispatch in parallel with MAP/SLIP/SHEET/NOTEBOOK

---

## 1. Target Lock

RELAYOUT-002 delivered the structural skeleton: `#speaker-panel`, `#speaker-portrait`,
`#speaker-beats`, `#orb` (36px heartbeat). All placeholder — no content, no wiring, no
portrait logic.

This WO wires the Speaker Panel to the existing WS events (`speaking_start`,
`speaking_stop`) and populates the idle state. One new `.js` file. No changes to
`index.html` or `style.css`. No new WS message types.

**Deliver:** `client2d/orb.js` — Speaker Panel behavior:
- Idle: DM crest rendered in `#speaker-portrait` (warm sepia underexposure via CSS filter)
- `speaking_start`: portrait filter clears (crisp), orb inner div gets `.speaking` class, one beat appended to `#speaker-beats`
- `speaking_stop`: portrait returns to idle filter, orb `.speaking` class removed, beats age
- Beat strip: opacity-only aging via CSS `nth-last-child`, DOM cap 8 beats
- Crest: non-interactive (no click handler, no event listener on portrait)
- Posture-responsive: panel compresses on LEAN/DOWN/DICE — JS does not fight posture

**No new WS message types. No changes to `ws.js`. No changes to `index.html` or `style.css`.**

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | What file is created? | `client2d/orb.js` — one new file. Loaded via `<script src="orb.js"></script>` added to `index.html` after `ws.js`, before `main.js`. |
| BD-02 | What renders the DM crest at idle? | `orb.js` sets `#speaker-portrait` background to a CSS-driven placeholder: a dim walnut rect with a centered brass "DM" text node. Not an image file — pure DOM + CSS. ORB-001 does not introduce any image assets. |
| BD-03 | How is idle portrait styled? | CSS filter on `#speaker-portrait` at idle: `brightness(0.5) sepia(0.4) saturate(0.6)`. Applied as `speaker-portrait.style.filter` by orb.js on init. On `speaking_start`: filter clears to `brightness(1) sepia(0) saturate(1)` with CSS transition ~400ms. On `speaking_stop`: filter returns to idle. |
| BD-04 | Where does the CSS transition live? | In `style.css` — one new rule: `#speaker-portrait { transition: filter 0.4s ease; }`. This is the only `style.css` change. Builder adds it at the end of the `#speaker-portrait` block. |
| BD-05 | How does NPC portrait work? | `speaking_start` payload may contain `speaker_id` and/or `portrait_url`. If `portrait_url` is present: set `#speaker-portrait` background-image to that URL (filter still clears). If absent: keep DM crest. On `speaking_stop`: clear background-image, restore DM crest, restore idle filter. |
| BD-06 | How does the beat strip work? | On `speaking_start`: create a `<div class="beat">` with `data.text` (or `data.beats[0]` — see Integration Seams). Append to `#speaker-beats`. If beat count > 8: remove oldest (first child). CSS `nth-last-child` selectors handle opacity aging. No JS timers. No scroll. No animation beyond CSS. |
| BD-07 | How is beat opacity aging done? | Pure CSS. `orb.js` does not touch opacity. Builder adds to `style.css`: `.beat { opacity: 0.15; transition: opacity 0.3s ease; } #speaker-beats .beat:nth-last-child(1) { opacity: 1; } #speaker-beats .beat:nth-last-child(2) { opacity: 0.7; } #speaker-beats .beat:nth-last-child(3) { opacity: 0.45; } #speaker-beats .beat:nth-last-child(4) { opacity: 0.25; }` — beats 5+ remain at 0.15. |
| BD-08 | How does the orb pulse work? | `main.js` already toggles `.speaking` on `#orb` (line 86/90). That class is on `#orb`, but the CSS pulse targets `#orb > div:first-child.speaking`. Builder confirms the existing `main.js` handler applies `.speaking` to the correct element. If it applies to `#orb` and not the inner div: orb.js adds a handler that proxies the class to the inner div. Do not modify `main.js`. |
| BD-09 | Does the crest have a click handler? | No. No event listener on `#speaker-portrait` or `#speaker-panel`. The portrait element is purely visual in v1. Builder must not add a click handler. |
| BD-10 | Does speaking override posture? | No. `orb.js` never modifies `#right-col` width, `#speaker-panel` flex, or any posture class. Panel compresses on LEAN/DOWN/DICE — JS respects that. Beat still appends. Orb still pulses. Portrait filter still clears. But the panel does not expand. |
| BD-11 | What about the stale `transcript-area` reference in main.js? | Leave it. `main.js` has a `ws.on('narration', ...)` handler that writes to `#transcript-area`. That element doesn't exist in the new index.html — the handler silently no-ops (`if (!transcriptArea) return`). Do not remove it. DM-PANEL-001 will repurpose or replace it. |
| BD-12 | What WS message fields does orb.js read? | `speaking_start`: `data.text` (beat text, optional), `data.speaker_id` (optional), `data.portrait_url` (optional). `speaking_stop`: no payload fields needed. If `speaking_start` has no `text` field, append no beat (orb still pulses). |

---

## 3. Contract Spec

### 3.1 New file: `client2d/orb.js`

```js
/* orb.js — Speaker Panel wiring: portrait, beats, orb pulse
   WO-UI-2D-ORB-001
   Depends on: ws.js (WsBridge), main.js (orb .speaking class toggle already wired)
*/
(function () {
  'use strict';

  const portrait  = document.getElementById('speaker-portrait');
  const beats     = document.getElementById('speaker-beats');
  const orbInner  = document.querySelector('#orb > div');  // 36px circle

  const IDLE_FILTER   = 'brightness(0.5) sepia(0.4) saturate(0.6)';
  const ACTIVE_FILTER = 'brightness(1) sepia(0) saturate(1)';
  const MAX_BEATS = 8;

  // Idle state: DM crest placeholder
  function setIdle() {
    portrait.style.filter = IDLE_FILTER;
    portrait.style.backgroundImage = '';
    // DM crest text already set by CSS ::after or init render (see §3.3)
  }

  // Speaking state
  function setSpeaking(data) {
    portrait.style.filter = ACTIVE_FILTER;
    if (data.portrait_url) {
      portrait.style.backgroundImage = 'url(' + data.portrait_url + ')';
      portrait.style.backgroundSize  = 'cover';
      portrait.style.backgroundPosition = 'center top';
    }
    if (data.text) {
      const beat = document.createElement('div');
      beat.className = 'beat';
      beat.textContent = data.text;
      beats.appendChild(beat);
      while (beats.children.length > MAX_BEATS) {
        beats.removeChild(beats.firstChild);
      }
    }
    // Orb pulse: main.js already toggles .speaking on #orb.
    // If .speaking lands on #orb instead of orbInner, proxy it:
    orbInner.classList.add('speaking');
  }

  function stopSpeaking() {
    setIdle();
    orbInner.classList.remove('speaking');
  }

  // Wire to WsBridge (ws must exist on window or be passed in)
  // ws is exposed as window.__ws by main.js — orb.js loads after main.js
  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[orb] WsBridge not found'); return; }
    bridge.on('speaking_start', setSpeaking);
    bridge.on('speaking_stop',  stopSpeaking);
    setIdle();
    console.log('[orb] Speaker Panel wired.');
  });

})();
```

### 3.2 `index.html` change — one line only

Add `<script src="orb.js"></script>` after `ws.js`, before `main.js`:

```html
<script src="ws.js"></script>
<script src="orb.js"></script>   <!-- ORB-001 -->
<script src="main.js"></script>
```

### 3.3 `style.css` changes — two additions only

**Addition 1 — portrait transition and crest (append to `#speaker-portrait` block):**

```css
#speaker-portrait {
  /* ... existing rules ... */
  transition: filter 0.4s ease;
  background-size: cover;
  background-position: center top;
  /* DM crest: brass-tinted "DM" label via pseudo-element */
  display: flex;
  align-items: center;
  justify-content: center;
}

#speaker-portrait::after {
  content: 'DM';
  font-size: 1.4rem;
  letter-spacing: 0.2em;
  color: rgba(139, 105, 20, 0.4);  /* --brass at low opacity */
  font-style: italic;
  pointer-events: none;
  user-select: none;
}
```

**Addition 2 — beat strip aging (append to beat styles, new block):**

```css
.beat {
  opacity: 0.15;
  font-size: 11px;
  line-height: 1.5;
  color: var(--parchment-aged);
  padding: 1px 0;
  transition: opacity 0.3s ease;
}

#speaker-beats .beat:nth-last-child(1) { opacity: 1;    }
#speaker-beats .beat:nth-last-child(2) { opacity: 0.70; }
#speaker-beats .beat:nth-last-child(3) { opacity: 0.45; }
#speaker-beats .beat:nth-last-child(4) { opacity: 0.25; }
/* beats 5+ remain at 0.15 */
```

---

## 4. Implementation Plan

1. **Read `client2d/main.js`** — confirm `window.__ws` is exposed (line 138: `window.__ws = ws`). Confirm `.speaking` class target: line 86 applies to `orb` (the `#orb` div, not `orbInner`). orb.js proxies `.speaking` to `orbInner` directly — do not modify main.js.

2. **Create `client2d/orb.js`** — implement per Contract Spec §3.1. No deviation.

3. **Modify `client2d/index.html`** — insert `<script src="orb.js"></script>` between ws.js and main.js. One line, nothing else.

4. **Modify `client2d/style.css`** — two additions per §3.3:
   - Portrait transition + `::after` crest rule
   - `.beat` opacity aging block

5. **Create `tests/test_ui_2d_orb_gate.py`** — 12 gate tests (ORB-01 through ORB-12)

6. **Preflight:**
   - `pytest tests/test_ui_2d_orb_gate.py -v` — 12/12 must pass
   - `pytest tests/test_ui_2d_relayout_002_gate.py -v` — 14/14 must still pass
   - `pytest tests/test_ui_2d_relayout_gate.py -v` — 12/12 must still pass

7. **Visual confirmation:** Open `client2d/index.html` in browser. Confirm: Speaker Panel shows faint "DM" crest text in dimmed portrait area, beat strip empty, orb small amber glow. Include screenshot or description in debrief.

---

## 5. Gate Tests (UI-2D-ORB 12/12)

File: `tests/test_ui_2d_orb_gate.py`

Tests use Python `html.parser` + file content search. No browser required.

| ID | Description |
|----|-------------|
| ORB-01 | `client2d/orb.js` exists |
| ORB-02 | `index.html` contains `<script src="orb.js">` |
| ORB-03 | `orb.js` references `speaking_start` |
| ORB-04 | `orb.js` references `speaking_stop` |
| ORB-05 | `orb.js` references `speaker-portrait` |
| ORB-06 | `orb.js` references `speaker-beats` |
| ORB-07 | `orb.js` contains `IDLE_FILTER` or `brightness(0.5)` (idle filter defined) |
| ORB-08 | `orb.js` contains `MAX_BEATS` or the value `8` (DOM cap present) |
| ORB-09 | `orb.js` does NOT add any click or mousedown event listener (crest non-interactive) |
| ORB-10 | `style.css` contains `.beat` selector |
| ORB-11 | `style.css` contains `nth-last-child` (beat aging present) |
| ORB-12 | `style.css` contains `speaker-portrait` with `transition` (filter transition present) |

---

## 6. Delivery Footer

**Files to create:**

```
client2d/orb.js                  ← CREATE (Speaker Panel wiring)
tests/test_ui_2d_orb_gate.py    ← CREATE (12 gate tests, ORB-01 through ORB-12)
```

**Files to modify:**

```
client2d/index.html    ← MODIFY (one line: add <script src="orb.js"> between ws.js and main.js)
client2d/style.css     ← MODIFY (two additions: portrait transition/crest, beat aging block)
```

**Do not modify `ws.js`. Do not modify `main.js`. Do not touch `client/`.**

**Commit requirement:**

```
feat: WO-UI-2D-ORB-001 — Speaker Panel wiring: portrait, beats, orb pulse — Gate UI-2D-ORB 12/12
```

**Preflight:**

```
pytest tests/test_ui_2d_orb_gate.py -v
pytest tests/test_ui_2d_relayout_002_gate.py -v
pytest tests/test_ui_2d_relayout_gate.py -v
```

All three green before commit.

---

## 7. Integration Seams

- `window.__ws`: `main.js` exposes the WsBridge instance as `window.__ws` (line 138). `orb.js` reads this on `window.addEventListener('load', ...)`. Load order in index.html must be: `ws.js` → `orb.js` → `main.js`. The `window.__ws` assignment happens inside main.js's IIFE — it will be set before `load` fires.
- `orb` vs `orbInner` for `.speaking` class: `main.js` line 83 selects `#orb` and lines 86/90 toggle `.speaking` on it. The CSS pulse targets `#orb > div:first-child.speaking`. orb.js independently also toggles `.speaking` on `orbInner` (`#orb > div`). This is redundant but safe — `.speaking` ends up on the inner div either way. Builder confirms by reading main.js before writing orb.js.
- `speaking_start` payload shape: current backend may not send `text` or `portrait_url`. Builder confirms by reading ws.js message log or backend. If fields are absent, orb.js no-ops gracefully (portrait stays DM crest, no beat appended). No failures.
- `#speaker-portrait::after` crest: if `orb.js` sets `background-image` (NPC portrait), the `::after` pseudo-element will overlay it. Fix: add `#speaker-portrait.has-portrait::after { display: none; }` to style.css, and `orb.js` adds/removes class `has-portrait` when setting/clearing background-image. Builder implements this refinement.

---

## 8. Assumptions to Validate

- `window.__ws` is accessible after `load` event — builder confirms by tracing main.js init sequence
- `speaking_start` event name matches backend exactly — builder confirms against ws.js handler registration in main.js
- `#orb > div` selector matches the inner circle div — builder confirms against index.html structure (it does: `<div id="orb"><div>...</div></div>`)

---

## 9. Open Findings (log on completion)

| ID | Severity | Description |
|----|----------|-------------|
| FINDING-ORB-NPC-PORTRAIT-001 | LOW | NPC portrait swap requires `portrait_url` in `speaking_start` payload — backend may not send this yet. Graceful no-op in v1; wiring exists when backend adds the field. |
| FINDING-ORB-BEAT-TEXT-001 | LOW | Beat text requires `text` field in `speaking_start` payload. If backend sends narration via separate `narration` event instead, ORB beats will be empty in v1. DM-PANEL-001 will address beat sourcing. |
| FINDING-2D-STATUS-DOT-001 | LOW | WS status dot position may conflict with speaker panel. Address here or as standalone style fix if collision is confirmed in visual check. |

---

## 10. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
