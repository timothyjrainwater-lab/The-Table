# WO-UI-2D-SLIP-001 — Roll Slip Ritual: PENDING_ROLL → Stamp → Archive

**Gate:** UI-2D-SLIP
**Tests:** 10 (SLIP-01 through SLIP-10)
**Dispatch:** 2026-02-24
**Depends on:** WO-UI-2D-RELAYOUT-002 (ACCEPTED cbd5d9b)
**Blocks:** nothing (parallel wave)
**Commit message:** `feat: WO-UI-2D-SLIP-001 — Roll slip ritual: PENDING_ROLL stamp archive — Gate UI-2D-SLIP 10/10`

---

## Target Lock

`#slip-tray` exists in `index.html` inside `#dice-section`. It already has `#slip-tray-label` ("Roll Slip Tray") as a placeholder. This WO wires the roll slip ritual — the physical dice replacement for the 2D client.

**The ritual:**

1. Backend sends `pending_roll` → a roll slip prints into `#slip-tray` showing formula + "PENDING"
2. Player clicks the slip to "stamp" it → WS message `roll_confirm` sent, slip updates to stamped state
3. Backend sends `roll_result` → slip updates with result value + wax seal visual, then moves to archive zone after 3s

The slip is a diegetic object — like a printed receipt from a slot. Not a modal, not a tooltip, not a popup.

---

## Binary Decisions (locked)

| # | Decision | Answer |
|---|----------|--------|
| BD-1 | Slip DOM target | `#slip-tray`. Slips stack vertically, newest at bottom. `#slip-tray` already scrolls internally (`overflow-y: auto`). |
| BD-2 | Stamp interaction | Click anywhere on the pending slip. No button. No tooltip. Single click = confirm. |
| BD-3 | Wax seal visual | CSS `::after` pseudo-element on the stamped slip: round red circle, `--wax-red` color, "✦" character. |
| BD-4 | Archive | After `roll_result`, slip gets `.archived` class after 3s delay. Archived slips: opacity 0.4, font-size 10px, compact. Not removed from DOM in v1 — slip tray scrolls. DOM cap at 20 slips (oldest removed when exceeded). |
| BD-5 | Formula display | Plain text from `pending_roll.formula` field. E.g. "1d20+5 (Attack)". |
| BD-6 | Multiple concurrent slips | Each slip identified by `id` field from backend. Map of id→element. `roll_result` matches by id. |

---

## Files

**Create:** `client2d/slip.js`
**Modify:** `client2d/index.html` — one `<script src="slip.js">` tag
**Modify:** `client2d/style.css` — slip visual styles

No other files touched.

---

## Implementation

### style.css additions (append to end)

```css
/* =============================================================
   WO-UI-2D-SLIP-001: Roll slip ritual
   ============================================================= */

.roll-slip {
  background: var(--parchment);
  color: var(--ink);
  border: 1px solid rgba(26,18,8,0.2);
  border-radius: 2px;
  padding: 6px 8px;
  font-size: 11px;
  font-family: 'Georgia', serif;
  cursor: pointer;
  user-select: none;
  position: relative;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  transition: opacity 0.4s ease, font-size 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.roll-slip:hover {
  background: var(--parchment-aged);
}

.roll-slip.pending::after {
  content: 'PENDING';
  font-size: 9px;
  letter-spacing: 0.15em;
  color: var(--brass);
  font-style: italic;
}

.roll-slip.stamped::after {
  content: '✦';
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--wax-red);
  color: var(--parchment);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.4);
}

.roll-slip.archived {
  opacity: 0.4;
  font-size: 10px;
  cursor: default;
  pointer-events: none;
}

.slip-formula {
  font-weight: bold;
  font-size: 12px;
}

.slip-result {
  font-size: 14px;
  font-weight: bold;
  color: var(--ink);
  letter-spacing: 0.05em;
}
```

### slip.js (full file)

```js
/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   slip.js — Roll slip ritual: PENDING_ROLL → stamp → archive
   WO-UI-2D-SLIP-001
   ============================================================= */

(function () {
  'use strict';

  const MAX_SLIPS = 20;
  const tray  = document.getElementById('slip-tray');
  const slips = new Map();  // id → element

  function makeSlip(id, formula) {
    const el = document.createElement('div');
    el.className = 'roll-slip pending';
    el.dataset.slipId = id;

    const fEl = document.createElement('div');
    fEl.className = 'slip-formula';
    fEl.textContent = formula || 'Roll';
    el.appendChild(fEl);

    el.addEventListener('click', function () {
      if (el.classList.contains('pending')) {
        el.classList.remove('pending');
        el.classList.add('stamped');
        var bridge = window.__ws;
        if (bridge) bridge.send({ msg_type: 'roll_confirm', id: id });
      }
    });

    return el;
  }

  function pruneSlips() {
    while (tray.children.length > MAX_SLIPS + 1) {
      // +1 for #slip-tray-label
      var oldest = tray.querySelector('.roll-slip');
      if (oldest) tray.removeChild(oldest);
    }
  }

  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[slip] WsBridge not found'); return; }

    bridge.on('pending_roll', function (d) {
      var id      = d.id || ('slip-' + Date.now());
      var formula = d.formula || 'Roll';
      var el = makeSlip(id, formula);
      slips.set(id, el);
      tray.appendChild(el);
      tray.scrollTop = tray.scrollHeight;
      pruneSlips();
    });

    bridge.on('roll_result', function (d) {
      var el = slips.get(d.id);
      if (!el) return;
      el.classList.remove('pending');
      el.classList.add('stamped');

      var rEl = document.createElement('div');
      rEl.className = 'slip-result';
      rEl.textContent = String(d.result !== undefined ? d.result : '?');
      el.appendChild(rEl);

      setTimeout(function () {
        el.classList.add('archived');
      }, 3000);
    });
  });

})();
```

### index.html change

After `<script src="map.js">` (or after `dm-panel.js` if map.js hasn't landed yet — both are parallel wave):

```html
  <script src="slip.js"></script>   <!-- SLIP-001 -->
```

Load order: `ws.js` → `orb.js` → `dm-panel.js` → `map.js` → `slip.js` → `main.js`

---

## Integration Seams

**§1 — `#slip-tray-label` preserved:** slip.js appends `.roll-slip` elements to `#slip-tray`. The label div is already in the tray as first child. `pruneSlips()` uses `querySelector('.roll-slip')` to find oldest slip — never removes the label.

**§2 — `roll_confirm` WS send:** slip.js calls `bridge.send(...)`. `WsBridge.send()` must exist. Check `ws.js` for the send method signature before committing. If send is not implemented, add a TODO comment and gate will still pass (send is not gate-tested).

**§3 — Parallel with MAP-001:** Both add script tags to index.html. Builder must ensure both tags are present and in the correct order. If dispatched to separate builders, the second builder must read index.html current state before writing.

---

## Gate Tests (file: `tests/test_ui_2d_slip_gate.py`)

| ID | Check |
|----|-------|
| SLIP-01 | `slip.js` exists in `client2d/` |
| SLIP-02 | `slip.js` contains `pending_roll` |
| SLIP-03 | `slip.js` contains `roll_result` |
| SLIP-04 | `slip.js` contains `roll_confirm` |
| SLIP-05 | `slip.js` contains `roll-slip` |
| SLIP-06 | `slip.js` contains `archived` |
| SLIP-07 | `slip.js` contains `MAX_SLIPS` |
| SLIP-08 | `index.html` contains `slip.js` |
| SLIP-09 | `style.css` contains `roll-slip` |
| SLIP-10 | `style.css` contains `wax-red` |

---

## Preflight

```
pytest tests/test_ui_2d_slip_gate.py            # 10/10
pytest tests/test_ui_2d_relayout_002_gate.py    # 14/14
pytest tests/test_ui_2d_relayout_gate.py        # 12/12
```
