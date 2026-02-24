# WO-UI-2D-SHEET-001 — Character Sheet: Live WS Data, Clickable Abilities

**Gate:** UI-2D-SHEET
**Tests:** 10 (SHEET-01 through SHEET-10)
**Dispatch:** 2026-02-24
**Depends on:** WO-UI-2D-RELAYOUT-002 (ACCEPTED cbd5d9b)
**Blocks:** nothing (parallel wave)
**Commit message:** `feat: WO-UI-2D-SHEET-001 — Character sheet live WS data clickable abilities — Gate UI-2D-SHEET 10/10`

---

## Target Lock

The shelf has `#shelf-sheet` button with `data-posture="posture-down"` and `data-drawer="sheet-drawer"`. Clicking it triggers posture-down (handled by main.js) — the scene surface minimizes, the right rail narrows, and the player is looking down at the table.

This WO creates the sheet drawer. A `<div id="sheet-drawer">` slides up from `#scene-surface` when `data-drawer="sheet-drawer"` is activated. The drawer overlays the scene surface in DOWN posture.

The sheet displays live character data from a `character_state` WS event. Clickable ability scores send `ability_check_declare` to the server — the DECLARE step in the interaction grammar (DECLARE → POINT → CONFIRM → RECORD).

No tooltips. No hover cards. Ability scores are plain numbers, clicking them is the action.

---

## Binary Decisions (locked)

| # | Decision | Answer |
|---|----------|--------|
| BD-1 | Drawer mechanism | `#sheet-drawer` is `position: fixed`, overlays `#scene-surface` region (excludes right-col). `data-drawer` wiring in main.js handles show/hide toggle — sheet.js hooks into the same mechanism. |
| BD-2 | Drawer trigger | main.js already reads `data-drawer` on shelf buttons. sheet.js adds a `MutationObserver` on `#sheet-drawer` to detect when it becomes visible, then refreshes display. |
| BD-3 | Data source | `character_state` WS event. Fields: `name`, `class`, `level`, `hp`, `hp_max`, `ac`, `abilities` (obj: str/dex/con/int/wis/cha as scores), `saves` (obj), `skills` (arr of {name, bonus}). |
| BD-4 | Ability click | Click an ability score div → `ws.send({ msg_type: 'ability_check_declare', ability: 'str' })`. No confirmation in this WO — CONFIRM step is engine-side. |
| BD-5 | Sheet style | Parchment background, ink text, brass headers. Not a modal — diegetic object, like a sheet on the table. |
| BD-6 | Offline state | If no `character_state` received yet, show placeholder "—" values. Never show an error. |
| BD-7 | Drawer close | Clicking `#shelf-sheet` again (or pressing `1` for STANDARD posture) hides the drawer. main.js handles posture; sheet.js only needs to render when visible. |

---

## Files

**Create:** `client2d/sheet.js`
**Modify:** `client2d/index.html` — `#sheet-drawer` div + one `<script src="sheet.js">` tag
**Modify:** `client2d/style.css` — sheet drawer + character sheet styles

No other files touched.

---

## Implementation

### style.css additions (append to end)

```css
/* =============================================================
   WO-UI-2D-SHEET-001: Character sheet drawer
   ============================================================= */

#sheet-drawer {
  display: none;
  position: fixed;
  top: 5px;    /* below top border */
  left: 0;
  right: var(--right-col-width);
  bottom: var(--shelf-height);
  background: linear-gradient(160deg, var(--parchment) 0%, var(--parchment-aged) 100%);
  color: var(--ink);
  overflow-y: auto;
  z-index: 80;
  padding: 20px 24px;
  box-shadow: inset 0 0 40px rgba(26,18,8,0.1), 4px 0 16px rgba(0,0,0,0.4);
  border-right: 2px solid var(--brass);
}

#sheet-drawer.drawer-open {
  display: block;
}

.sheet-header {
  border-bottom: 2px solid var(--brass);
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.sheet-name {
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 0.05em;
  color: var(--ink);
}

.sheet-class {
  font-size: 12px;
  color: rgba(26,18,8,0.55);
  font-style: italic;
  margin-top: 2px;
}

.sheet-vitals {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  font-size: 13px;
}

.sheet-vital {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sheet-vital-label {
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(26,18,8,0.4);
}

.sheet-vital-value {
  font-size: 18px;
  font-weight: bold;
}

.sheet-section-title {
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--brass);
  border-bottom: 1px solid rgba(139,105,20,0.3);
  padding-bottom: 3px;
  margin: 12px 0 8px;
}

.sheet-abilities {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.ability-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(26,18,8,0.05);
  border: 1px solid rgba(26,18,8,0.1);
  border-radius: 3px;
  padding: 6px 4px;
  cursor: pointer;
  transition: background 0.15s ease, box-shadow 0.15s ease;
  user-select: none;
}

.ability-block:hover {
  background: rgba(139,105,20,0.12);
  box-shadow: 0 0 0 1px var(--brass);
}

.ability-block:active {
  background: rgba(139,105,20,0.2);
}

.ability-label {
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(26,18,8,0.45);
}

.ability-score {
  font-size: 20px;
  font-weight: bold;
  color: var(--ink);
  line-height: 1;
  margin: 3px 0;
}

.ability-mod {
  font-size: 11px;
  color: rgba(26,18,8,0.55);
}
```

### index.html changes

Inside `<body>`, after `#dm-panel` div and before `#layout`:

```html
  <!-- Character sheet drawer — DOWN posture, overlays scene surface -->
  <div id="sheet-drawer">
    <!-- Populated by WO-UI-2D-SHEET-001 / sheet.js -->
  </div>
```

Script tag after `slip.js`:

```html
  <script src="sheet.js"></script>   <!-- SHEET-001 -->
```

### sheet.js (full file)

```js
/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   sheet.js — Character sheet: live WS data, clickable abilities
   WO-UI-2D-SHEET-001
   ============================================================= */

(function () {
  'use strict';

  const ABILITY_KEYS   = ['str', 'dex', 'con', 'int', 'wis', 'cha'];
  const ABILITY_LABELS = { str: 'STR', dex: 'DEX', con: 'CON',
                           int: 'INT', wis: 'WIS', cha: 'CHA' };

  const drawer = document.getElementById('sheet-drawer');
  let   state  = null;   // last character_state received

  function mod(score) {
    var m = Math.floor((score - 10) / 2);
    return (m >= 0 ? '+' : '') + m;
  }

  function render() {
    if (!state) return;
    drawer.innerHTML = '';

    // Header
    var hdr = document.createElement('div');
    hdr.className = 'sheet-header';
    hdr.innerHTML =
      '<div class="sheet-name">' + (state.name || 'Adventurer') + '</div>' +
      '<div class="sheet-class">' + (state.class || '') + ' ' + (state.level ? 'Level ' + state.level : '') + '</div>';
    drawer.appendChild(hdr);

    // Vitals
    var vitals = document.createElement('div');
    vitals.className = 'sheet-vitals';
    [
      { label: 'HP', value: (state.hp !== undefined ? state.hp + ' / ' + state.hp_max : '—') },
      { label: 'AC', value: state.ac !== undefined ? state.ac : '—' },
    ].forEach(function (v) {
      var vEl = document.createElement('div');
      vEl.className = 'sheet-vital';
      vEl.innerHTML = '<div class="sheet-vital-label">' + v.label + '</div>' +
                      '<div class="sheet-vital-value">' + v.value + '</div>';
      vitals.appendChild(vEl);
    });
    drawer.appendChild(vitals);

    // Abilities
    var abTitle = document.createElement('div');
    abTitle.className = 'sheet-section-title';
    abTitle.textContent = 'Ability Scores';
    drawer.appendChild(abTitle);

    var abGrid = document.createElement('div');
    abGrid.className = 'sheet-abilities';

    ABILITY_KEYS.forEach(function (key) {
      var score = (state.abilities && state.abilities[key] !== undefined)
        ? state.abilities[key] : null;
      var block = document.createElement('div');
      block.className = 'ability-block';
      block.innerHTML =
        '<div class="ability-label">' + ABILITY_LABELS[key] + '</div>' +
        '<div class="ability-score">' + (score !== null ? score : '—') + '</div>' +
        '<div class="ability-mod">' + (score !== null ? mod(score) : '') + '</div>';
      if (score !== null) {
        block.addEventListener('click', function () {
          var bridge = window.__ws;
          if (bridge) bridge.send({ msg_type: 'ability_check_declare', ability: key });
        });
      }
      abGrid.appendChild(block);
    });
    drawer.appendChild(abGrid);
  }

  // Watch for drawer becoming visible — re-render on open
  new MutationObserver(function () {
    if (drawer.classList.contains('drawer-open') && state) render();
  }).observe(drawer, { attributes: true, attributeFilter: ['class'] });

  // Shelf button wiring — toggle drawer-open
  var shelfBtn = document.getElementById('shelf-sheet');
  if (shelfBtn) {
    shelfBtn.addEventListener('click', function () {
      drawer.classList.toggle('drawer-open');
    });
  }

  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[sheet] WsBridge not found'); return; }

    bridge.on('character_state', function (d) {
      state = d;
      if (drawer.classList.contains('drawer-open')) render();
    });
  });

})();
```

---

## Integration Seams

**§1 — main.js shelf button / posture wiring:** main.js reads `data-posture` on shelf buttons and calls `setPosture()` when clicked. sheet.js adds its own click listener on `#shelf-sheet` to toggle `drawer-open`. Both listeners fire. Posture changes; drawer opens. No conflict.

**§2 — `right-col-width` in sheet drawer `right` property:** Sheet drawer uses `right: var(--right-col-width)`. In LEAN/DOWN/DICE postures, right-col width changes (CSS posture classes). Sheet drawer CSS uses the CSS variable directly — auto-adapts. No JS needed.

**§3 — DOWN posture:** Player pressing `3` triggers `posture-down` class on body. Sheet drawer is not directly tied to posture class — it's controlled by shelf button click. Player can open sheet in any posture. DOWN posture is the canonical sheet-reading posture but is not enforced.

---

## Gate Tests (file: `tests/test_ui_2d_sheet_gate.py`)

| ID | Check |
|----|-------|
| SHEET-01 | `sheet.js` exists in `client2d/` |
| SHEET-02 | `sheet.js` contains `character_state` |
| SHEET-03 | `sheet.js` contains `ability_check_declare` |
| SHEET-04 | `sheet.js` contains `ability-block` |
| SHEET-05 | `sheet.js` contains `sheet-drawer` |
| SHEET-06 | `sheet.js` contains `drawer-open` |
| SHEET-07 | `sheet.js` contains `MutationObserver` |
| SHEET-08 | `index.html` contains `sheet-drawer` |
| SHEET-09 | `index.html` contains `sheet.js` |
| SHEET-10 | `style.css` contains `ability-block` |

---

## Preflight

```
pytest tests/test_ui_2d_sheet_gate.py           # 10/10
pytest tests/test_ui_2d_relayout_002_gate.py    # 14/14
pytest tests/test_ui_2d_relayout_gate.py        # 12/12
```
