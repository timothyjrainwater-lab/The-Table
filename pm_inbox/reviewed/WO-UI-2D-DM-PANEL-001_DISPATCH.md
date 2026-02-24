# WO-UI-2D-DM-PANEL-001 — DM Panel: Two-Mode Voice Overlay

**Gate:** UI-2D-DM-PANEL
**Tests:** 10 (DMP-01 through DMP-10)
**Dispatch:** 2026-02-24
**Depends on:** WO-UI-2D-ORB-001 (ACCEPTED c14eba7)
**Blocks:** nothing (standalone feature)
**Commit message:** `feat: WO-UI-2D-DM-PANEL-001 — Two-mode DM voice overlay — Gate UI-2D-DM-PANEL 10/10`

---

## Target Lock

`#dm-panel` already exists in `index.html` and `style.css` as a skeleton (RELAYOUT-002 builder stubbed it in). It is `display:none`, has `#dm-panel-portrait` and `#dm-panel-text` children, and CSS pre-defines it as a fixed overlay sliding down from top covering ~25vh of the scene surface (not the right rail).

`#orb-transcript` also exists in `index.html` as a stub between speaker panel and dice section. It is `display:none`. This WO wires both.

**Two modes:**

| Mode | When | What shows |
|------|------|-----------|
| **EXPLORATION** | `speaking_start` while `body` does NOT have `.combat-active` | `#dm-panel` slides down from top, shows portrait + narration text |
| **COMBAT** | `speaking_start` while `body` HAS `.combat-active` | `#orb-transcript` strip shows inside right rail, no full panel |

`speaking_stop` hides whichever is active.

The `narration` WS event writes text in the active mode's text area. main.js currently has a stale handler that writes to `#transcript-area` (a no-op because that element doesn't exist). DM-PANEL-001 adds the correct handler by overriding it cleanly — orb.js is already wired to `speaking_start`/`speaking_stop`; dm-panel.js adds its own handlers on the same events (both fire, no conflict).

---

## Binary Decisions (locked)

| # | Decision | Answer |
|---|----------|--------|
| BD-1 | Mode detection | `body.classList.contains('combat-active')` at moment of `speaking_start` |
| BD-2 | Panel animation | CSS `transform: translateY(-100%)` → `translateY(0)` via `transition`. No JS animation. |
| BD-3 | Portrait in dm-panel | Same `portrait_url` from `speaking_start` payload. No-op if absent (empty circle). |
| BD-4 | Text accumulation | EXPLORATION: narration text appends to `#dm-panel-text` (scrolls internally). COMBAT: appends to `#orb-transcript`. Both clear on `speaking_stop`. |
| BD-5 | Overlap with Speaker Panel | `#dm-panel` overlays scene-surface only (right=var(--right-col-width)). Speaker Panel is untouched. |
| BD-6 | `speaking_stop` behavior | Hides active mode element. Clears portrait. Does NOT clear text immediately — text fades with panel. |

---

## Files

**Create:** `client2d/dm-panel.js`
**Modify:** `client2d/index.html` — one `<script src="dm-panel.js">` tag
**Modify:** `client2d/style.css` — slide animation for `#dm-panel`

No other files touched.

---

## Implementation

### style.css additions (append to end)

```css
/* =============================================================
   WO-UI-2D-DM-PANEL-001: DM panel slide animation
   ============================================================= */

/* EXPLORATION mode: panel visible */
#dm-panel.panel-active {
  display: flex !important;
  transform: translateY(0);
}

/* Slide-in transition — defined separately so display:none → flex doesn't fight transition */
#dm-panel {
  transform: translateY(-100%);
  transition: transform 0.3s ease;
}

/* COMBAT mode: orb transcript visible */
#orb-transcript.transcript-active {
  display: block !important;
}
```

### dm-panel.js (full file)

```js
/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   dm-panel.js — Two-mode DM voice overlay
   WO-UI-2D-DM-PANEL-001
   ============================================================= */

(function () {
  'use strict';

  const panel          = document.getElementById('dm-panel');
  const panelPortrait  = document.getElementById('dm-panel-portrait');
  const panelText      = document.getElementById('dm-panel-text');
  const transcript     = document.getElementById('orb-transcript');

  function isCombat() {
    return document.body.classList.contains('combat-active');
  }

  function onSpeakingStart(data) {
    if (isCombat()) {
      transcript.classList.add('transcript-active');
    } else {
      panel.classList.add('panel-active');
      if (data && data.portrait_url) {
        panelPortrait.style.backgroundImage = 'url(' + data.portrait_url + ')';
        panelPortrait.style.backgroundSize  = 'cover';
        panelPortrait.style.backgroundPosition = 'center top';
      }
    }
  }

  function onSpeakingStop() {
    panel.classList.remove('panel-active');
    transcript.classList.remove('transcript-active');
    panelPortrait.style.backgroundImage = '';
  }

  function onNarration(data) {
    const text = (data && data.text) ? data.text : '';
    if (!text) return;
    if (isCombat()) {
      const line = document.createElement('p');
      line.textContent = text;
      transcript.appendChild(line);
      transcript.scrollTop = transcript.scrollHeight;
    } else {
      const line = document.createElement('p');
      line.textContent = text;
      panelText.appendChild(line);
      panelText.scrollTop = panelText.scrollHeight;
    }
  }

  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[dm-panel] WsBridge not found'); return; }
    bridge.on('speaking_start', onSpeakingStart);
    bridge.on('speaking_stop',  onSpeakingStop);
    bridge.on('narration',      onNarration);
  });

})();
```

### index.html change

After `<script src="orb.js">`, add:

```html
  <script src="dm-panel.js"></script>   <!-- DM-PANEL-001 -->
```

Load order: `ws.js` → `orb.js` → `dm-panel.js` → `main.js`

---

## Integration Seams

**§1 — main.js stale narration handler:** main.js writes `narration` to `#transcript-area` which does not exist → silent no-op (`if (!transcriptArea) return`). dm-panel.js adds its own `narration` handler on the same bridge. Both fire; main.js handler no-ops; dm-panel.js handler writes. No conflict.

**§2 — orb.js and dm-panel.js both listen to speaking_start:** Both fire. orb.js handles portrait swap + beat append in Speaker Panel. dm-panel.js handles exploration/combat overlay. Non-overlapping DOM targets. Safe.

**§3 — combat-active class:** Set by main.js on `combat_start` / `combat_end`. dm-panel.js reads it at moment of `speaking_start`. Class must already be set before voice fires — backend protocol guarantees this order. If not, graceful fallback: shows exploration panel during combat (acceptable degradation).

**§4 — Panel CSS transition on display:** `#dm-panel` has `display:none` in HTML. Adding `panel-active` sets `display:flex !important` then `transform:translateY(0)`. The transition on `transform` fires because display change and class add happen in the same microtask — browser renders the flex state, then animates. Standard pattern.

---

## Gate Tests (file: `tests/test_ui_2d_dm_panel_gate.py`)

All static file checks. No browser. No server.

| ID | Check |
|----|-------|
| DMP-01 | `dm-panel.js` exists in `client2d/` |
| DMP-02 | `dm-panel.js` contains `panel-active` |
| DMP-03 | `dm-panel.js` contains `transcript-active` |
| DMP-04 | `dm-panel.js` contains `combat-active` |
| DMP-05 | `dm-panel.js` contains `speaking_start` |
| DMP-06 | `dm-panel.js` contains `speaking_stop` |
| DMP-07 | `dm-panel.js` contains `narration` |
| DMP-08 | `index.html` contains `dm-panel.js` |
| DMP-09 | `index.html` script order: `orb.js` before `dm-panel.js` before `main.js` |
| DMP-10 | `style.css` contains `panel-active` |

---

## Preflight

Before committing, all three suites must be green:

```
pytest tests/test_ui_2d_dm_panel_gate.py        # 10/10
pytest tests/test_ui_2d_orb_gate.py             # 12/12
pytest tests/test_ui_2d_relayout_002_gate.py    # 14/14
```
