# WO-UI-2D-NOTEBOOK-001 — Notebook: Draw, Transcript, Bestiary Tabs

**Gate:** UI-2D-NOTEBOOK
**Tests:** 10 (NB-01 through NB-10)
**Dispatch:** 2026-02-24
**Depends on:** WO-UI-2D-RELAYOUT-002 (ACCEPTED cbd5d9b)
**Blocks:** nothing (parallel wave)
**Commit message:** `feat: WO-UI-2D-NOTEBOOK-001 — Notebook draw transcript bestiary tabs — Gate UI-2D-NOTEBOOK 10/10`

---

## Target Lock

The shelf has `#shelf-notebook` button with `data-posture="posture-down"` and `data-drawer="notebook-drawer"`. This WO creates `#notebook-drawer` — a drawer that overlays the scene surface in DOWN posture, containing three tabs.

**Doctrine (sealed — do not reopen):** Notebook is write-locked by default. A deterministic consent handshake gates any write action. This WO does NOT implement freehand drawing with a canvas — that is a future WO with its own consent flow. The "Draw" tab in this WO is a placeholder div labeled "Drawing surface — consent required." The tab skeleton is required now so DM-PANEL-001 and future WOs have a stable anchor.

**Three tabs:**

| Tab | ID | Content |
|-----|----|---------|
| Draw | `nb-tab-draw` | Placeholder only — "Ink requires consent" label. Future WO adds canvas + consent handshake. |
| Transcript | `nb-tab-transcript` | Scrolling log of `narration` events. Append-only. No edit. |
| Bestiary | `nb-tab-bestiary` | List of `bestiary_entry` events received. Name + brief stat block. |

---

## Binary Decisions (locked)

| # | Decision | Answer |
|---|----------|--------|
| BD-1 | Drawer mechanism | Same pattern as SHEET-001: `#notebook-drawer` `position: fixed`, overlays scene surface. `drawer-open` class toggle on shelf button click. |
| BD-2 | Tab switching | Three `<button class="nb-tab-btn">` elements. Click sets `active` class on content panel, removes from others. Pure CSS + one JS handler. No framework. |
| BD-3 | Transcript source | `narration` WS events. Same events that DM-PANEL-001 routes to `#dm-panel-text`. notebook.js appends a copy to transcript tab — both receive the event independently. |
| BD-4 | Bestiary source | `bestiary_entry` WS event. Fields: `name`, `cr`, `hp`, `ac`, `attacks` (brief string). One card per entry. No images in v1. |
| BD-5 | Write lock display | Draw tab shows: locked icon (⚿), italic text "Ink requires consent — write gating is v2." No button. Not interactive. |
| BD-6 | DOM cap | Transcript: 200 lines max (oldest removed). Bestiary: unlimited (typically small). |

---

## Files

**Create:** `client2d/notebook.js`
**Modify:** `client2d/index.html` — `#notebook-drawer` div + one `<script src="notebook.js">` tag
**Modify:** `client2d/style.css` — notebook drawer + tab styles

No other files touched.

---

## Implementation

### style.css additions (append to end)

```css
/* =============================================================
   WO-UI-2D-NOTEBOOK-001: Notebook drawer
   ============================================================= */

#notebook-drawer {
  display: none;
  position: fixed;
  top: 5px;
  left: 0;
  right: var(--right-col-width);
  bottom: var(--shelf-height);
  background: linear-gradient(160deg, #f0e8d0 0%, #e8d8b0 100%);
  color: var(--ink);
  z-index: 80;
  display: none;
  flex-direction: column;
  box-shadow: inset 0 0 40px rgba(26,18,8,0.08), 4px 0 16px rgba(0,0,0,0.4);
  border-right: 2px solid var(--leather-warm);
}

#notebook-drawer.drawer-open {
  display: flex;
}

.nb-tab-bar {
  display: flex;
  border-bottom: 2px solid var(--leather-warm);
  background: rgba(26,18,8,0.06);
}

.nb-tab-btn {
  flex: 1;
  background: none;
  border: none;
  border-right: 1px solid rgba(26,18,8,0.1);
  padding: 8px 0;
  font-family: inherit;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(26,18,8,0.45);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.nb-tab-btn:last-child { border-right: none; }

.nb-tab-btn.active {
  background: rgba(139,105,20,0.1);
  color: var(--ink);
  font-weight: bold;
}

.nb-tab-btn:hover:not(.active) {
  background: rgba(26,18,8,0.05);
}

.nb-panel {
  display: none;
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.nb-panel.active {
  display: block;
}

/* Draw tab — write-locked placeholder */
.nb-draw-locked {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: rgba(26,18,8,0.35);
  font-style: italic;
  font-size: 14px;
  user-select: none;
}

.nb-draw-locked-icon {
  font-size: 48px;
  opacity: 0.2;
}

/* Transcript tab */
.nb-transcript-line {
  font-size: 12px;
  line-height: 1.7;
  color: var(--ink);
  padding: 2px 0;
  border-bottom: 1px solid rgba(26,18,8,0.06);
}

/* Bestiary tab */
.nb-bestiary-card {
  background: rgba(26,18,8,0.04);
  border: 1px solid rgba(26,18,8,0.12);
  border-radius: 2px;
  padding: 8px 10px;
  margin-bottom: 8px;
  font-size: 12px;
}

.nb-bestiary-name {
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 4px;
}

.nb-bestiary-stat {
  color: rgba(26,18,8,0.55);
  font-size: 11px;
}
```

### index.html changes

Inside `<body>`, after `#sheet-drawer`:

```html
  <!-- Notebook drawer — DOWN posture, overlays scene surface -->
  <div id="notebook-drawer">
    <!-- Populated by WO-UI-2D-NOTEBOOK-001 / notebook.js -->
  </div>
```

Script tag after `sheet.js`:

```html
  <script src="notebook.js"></script>   <!-- NOTEBOOK-001 -->
```

### notebook.js (full file)

```js
/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   notebook.js — Notebook: draw, transcript, bestiary tabs
   WO-UI-2D-NOTEBOOK-001
   ============================================================= */

(function () {
  'use strict';

  const MAX_TRANSCRIPT = 200;

  const drawer     = document.getElementById('notebook-drawer');

  // Build notebook shell into drawer
  drawer.innerHTML =
    '<div class="nb-tab-bar">' +
      '<button class="nb-tab-btn active" data-tab="draw">Draw</button>' +
      '<button class="nb-tab-btn" data-tab="transcript">Transcript</button>' +
      '<button class="nb-tab-btn" data-tab="bestiary">Bestiary</button>' +
    '</div>' +
    '<div id="nb-panel-draw" class="nb-panel active">' +
      '<div class="nb-draw-locked">' +
        '<div class="nb-draw-locked-icon">⚿</div>' +
        '<div>Ink requires consent — write gating is v2</div>' +
      '</div>' +
    '</div>' +
    '<div id="nb-panel-transcript" class="nb-panel"></div>' +
    '<div id="nb-panel-bestiary" class="nb-panel"></div>';

  const transcriptPanel = document.getElementById('nb-panel-transcript');
  const bestiaryPanel   = document.getElementById('nb-panel-bestiary');

  // Tab switching
  drawer.querySelectorAll('.nb-tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      drawer.querySelectorAll('.nb-tab-btn').forEach(function(b){ b.classList.remove('active'); });
      drawer.querySelectorAll('.nb-panel').forEach(function(p){ p.classList.remove('active'); });
      btn.classList.add('active');
      document.getElementById('nb-panel-' + btn.dataset.tab).classList.add('active');
    });
  });

  // Shelf button wiring
  var shelfBtn = document.getElementById('shelf-notebook');
  if (shelfBtn) {
    shelfBtn.addEventListener('click', function () {
      drawer.classList.toggle('drawer-open');
    });
  }

  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[notebook] WsBridge not found'); return; }

    bridge.on('narration', function (d) {
      var text = (d && d.text) ? d.text : '';
      if (!text) return;
      var line = document.createElement('div');
      line.className = 'nb-transcript-line';
      line.textContent = text;
      transcriptPanel.appendChild(line);
      // Cap at MAX_TRANSCRIPT
      while (transcriptPanel.children.length > MAX_TRANSCRIPT) {
        transcriptPanel.removeChild(transcriptPanel.firstChild);
      }
      // Auto-scroll if transcript tab is active
      var tBtn = drawer.querySelector('[data-tab="transcript"]');
      if (tBtn && tBtn.classList.contains('active')) {
        transcriptPanel.scrollTop = transcriptPanel.scrollHeight;
      }
    });

    bridge.on('bestiary_entry', function (d) {
      var card = document.createElement('div');
      card.className = 'nb-bestiary-card';
      card.innerHTML =
        '<div class="nb-bestiary-name">' + (d.name || 'Unknown') + '</div>' +
        '<div class="nb-bestiary-stat">CR ' + (d.cr || '?') +
          ' &nbsp;|&nbsp; HP ' + (d.hp || '?') +
          ' &nbsp;|&nbsp; AC ' + (d.ac || '?') + '</div>' +
        (d.attacks ? '<div class="nb-bestiary-stat">' + d.attacks + '</div>' : '');
      bestiaryPanel.appendChild(card);
    });
  });

})();
```

---

## Integration Seams

**§1 — `narration` handled by three listeners:** dm-panel.js, notebook.js, and main.js (no-op) all receive `narration`. All fire. Non-overlapping DOM targets. Safe.

**§2 — Drawer shell built in JS:** notebook.js writes drawer innerHTML on script load (not on `load` event) — this means the DOM is built before `load` fires. Tab buttons are wired immediately. WS events wired on `load`. No timing issue.

**§3 — SHEET-001 parallel:** Both add `#sheet-drawer` / `#notebook-drawer` to index.html and `sheet.js` / `notebook.js` script tags. If dispatched to separate builders, second builder reads current index.html before writing. Both drawers coexist — same mechanism, different IDs.

**§4 — Notebook write lock:** The `⚿` lock icon and "consent required" copy are non-interactive. No `cursor: pointer`. No click handler on the draw panel. Doctrine preserved — write gating is a future WO.

---

## Gate Tests (file: `tests/test_ui_2d_notebook_gate.py`)

| ID | Check |
|----|-------|
| NB-01 | `notebook.js` exists in `client2d/` |
| NB-02 | `notebook.js` contains `narration` |
| NB-03 | `notebook.js` contains `bestiary_entry` |
| NB-04 | `notebook.js` contains `nb-tab-btn` |
| NB-05 | `notebook.js` contains `nb-draw-locked` |
| NB-06 | `notebook.js` contains `drawer-open` |
| NB-07 | `notebook.js` contains `MAX_TRANSCRIPT` |
| NB-08 | `index.html` contains `notebook-drawer` |
| NB-09 | `index.html` contains `notebook.js` |
| NB-10 | `style.css` contains `nb-tab-btn` |

---

## Preflight

```
pytest tests/test_ui_2d_notebook_gate.py        # 10/10
pytest tests/test_ui_2d_relayout_002_gate.py    # 14/14
pytest tests/test_ui_2d_relayout_gate.py        # 12/12
```
