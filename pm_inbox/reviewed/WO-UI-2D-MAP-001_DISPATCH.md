# WO-UI-2D-MAP-001 — Scene Canvas: Grid, Fog, Tokens, AoE

**Gate:** UI-2D-MAP
**Tests:** 12 (MAP-01 through MAP-12)
**Dispatch:** 2026-02-24
**Depends on:** WO-UI-2D-RELAYOUT-002 (ACCEPTED cbd5d9b)
**Blocks:** nothing (parallel wave)
**Commit message:** `feat: WO-UI-2D-MAP-001 — Scene canvas: grid, fog, tokens, AoE — Gate UI-2D-MAP 12/12`

---

## Target Lock

`#scene-surface` exists in `index.html` and `style.css`. Inside it is `#scene-display` (parchment background, faint CSS grid). `index.html` has a comment: `<!-- Live scene canvas added by WO-UI-2D-MAP-001 -->`.

This WO injects a `<canvas id="scene-canvas">` into `#scene-display` and wires `map.js` to the WS bridge. The canvas renders:

1. **Grid** — 40px square grid, faint ink lines, toggleable
2. **Fog of war** — black overlay tiles, revealed by `fog_reveal` events
3. **Tokens** — faction-colored circles with HP bar and name label, placed/moved by WS events
4. **AoE shapes** — semi-transparent overlays (circle, cone, line) from `aoe_add`/`aoe_clear` events
5. **Scene image** — background image (town painting, dungeon map, etc.) from `scene_set` event, crossfades 300–400ms

The canvas fills `#scene-display` 100% width/height. Scene-label (`#scene-label`) remains in place — canvas is positioned absolute behind it.

---

## Binary Decisions (locked)

| # | Decision | Answer |
|---|----------|--------|
| BD-1 | Canvas positioning | `position: absolute; inset: 0; z-index: 0` inside `#scene-display`. `#scene-label` stays at z-index 1. |
| BD-2 | Coordinate system | Grid cell (col, row) origin top-left. 40px per cell. `cellToCanvas(col,row)` → `{x: col*40, y: row*40}`. |
| BD-3 | Scene image crossfade | Two `<img>` elements behind canvas. Active/pending swap with CSS `opacity` transition (350ms). Canvas renders grid/tokens/fog above. |
| BD-4 | Token shapes | Filled circle, radius 18px. Faction color from `token_data.faction` (ally=`#3a6b3a`, enemy=`#8b1a1a`, neutral=`#5c3d22`). Border 2px parchment. HP bar below circle (40px wide, 4px tall). Name label below HP bar. |
| BD-5 | Fog | Black fill per cell. Reveal = clear cell (remove from fog set, redraw). No partial reveal in v1. |
| BD-6 | AoE shapes | Semi-transparent fill: `rgba(139,26,26,0.25)` stroke `rgba(139,26,26,0.7)`. Shapes: `circle` (cx,cy,r), `cone` (points array), `line` (x1,y1,x2,y2,width). |
| BD-7 | Resize | `ResizeObserver` on `#scene-display`. Canvas resizes to match. Re-renders on resize. |
| BD-8 | Combat-active | `combat_start` adds `.combat-active` to `#scene-surface` (already done by main.js). map.js does not duplicate this. |

---

## WS Events Handled

| `msg_type` | Payload fields | Action |
|-----------|---------------|--------|
| `scene_set` | `image_url`, `grid` (bool), `cols`, `rows` | Load image, set grid dims, crossfade in |
| `scene_clear` | — | Clear image, return to parchment background |
| `token_add` | `id`, `col`, `row`, `name`, `faction`, `hp`, `hp_max` | Place token |
| `token_move` | `id`, `col`, `row` | Move token (animate 200ms) |
| `token_remove` | `id` | Remove token |
| `token_update` | `id`, `hp` | Update HP bar |
| `fog_reveal` | `cells`: `[[col,row],...]` | Reveal fog cells |
| `fog_reset` | `cols`, `rows` | Full fog, new dims |
| `aoe_add` | `id`, `shape`, `...coords` | Add AoE overlay |
| `aoe_clear` | `id` | Remove AoE overlay |

---

## Files

**Create:** `client2d/map.js`
**Modify:** `client2d/index.html` — one `<script src="map.js">` tag + canvas element inside `#scene-display`
**Modify:** `client2d/style.css` — canvas positioning + scene image layer

No other files touched.

---

## Implementation

### style.css additions (append to end)

```css
/* =============================================================
   WO-UI-2D-MAP-001: Scene canvas
   ============================================================= */

#scene-display {
  position: relative;  /* already set — ensure it stays */
}

#scene-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  pointer-events: none;  /* tokens clickable via separate overlay in future WO */
}

.scene-img-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
  opacity: 0;
  transition: opacity 0.35s ease;
}

.scene-img-layer.active {
  opacity: 1;
}
```

### index.html changes

Inside `#scene-display`, before the closing comment, add canvas and two image layers:

```html
      <!-- WO-UI-2D-MAP-001: scene image layers (crossfade swap) -->
      <img id="scene-img-a" class="scene-img-layer" src="" alt="">
      <img id="scene-img-b" class="scene-img-layer" src="" alt="">
      <!-- WO-UI-2D-MAP-001: live scene canvas -->
      <canvas id="scene-canvas"></canvas>
```

Script tag after `dm-panel.js`:

```html
  <script src="map.js"></script>   <!-- MAP-001 -->
```

### map.js structure (full file)

```js
/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   map.js — Scene canvas: grid, fog, tokens, AoE
   WO-UI-2D-MAP-001
   ============================================================= */

(function () {
  'use strict';

  const CELL = 40;
  const FACTION_COLOR = { ally: '#3a6b3a', enemy: '#8b1a1a', neutral: '#5c3d22' };

  const canvas  = document.getElementById('scene-canvas');
  const ctx     = canvas.getContext('2d');
  const imgA    = document.getElementById('scene-img-a');
  const imgB    = document.getElementById('scene-img-b');

  let activeImg = imgA;
  let pendingImg = imgB;

  let gridCols = 0, gridRows = 0, showGrid = false;
  let fog   = new Set();   // 'col,row' strings
  let tokens = new Map();  // id → {col,row,name,faction,hp,hp_max}
  let aoes   = new Map();  // id → {shape,...}

  // ---------------------------------------------------------------
  //  Resize
  // ---------------------------------------------------------------
  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width  = rect.width;
    canvas.height = rect.height;
    render();
  }

  new ResizeObserver(resize).observe(canvas.parentElement);

  // ---------------------------------------------------------------
  //  Scene image crossfade
  // ---------------------------------------------------------------
  function setSceneImage(url) {
    pendingImg.src = url;
    pendingImg.onload = function () {
      pendingImg.classList.add('active');
      activeImg.classList.remove('active');
      var tmp = activeImg;
      activeImg  = pendingImg;
      pendingImg = tmp;
    };
  }

  function clearSceneImage() {
    activeImg.classList.remove('active');
    pendingImg.classList.remove('active');
    activeImg.src = '';
    pendingImg.src = '';
  }

  // ---------------------------------------------------------------
  //  Render
  // ---------------------------------------------------------------
  function render() {
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    if (showGrid) renderGrid(W, H);
    renderFog(W, H);
    renderAoes();
    renderTokens();
  }

  function renderGrid(W, H) {
    ctx.strokeStyle = 'rgba(26,18,8,0.15)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= W; x += CELL) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y <= H; y += CELL) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
  }

  function renderFog(W, H) {
    ctx.fillStyle = 'rgba(0,0,0,0.85)';
    fog.forEach(function (key) {
      const [col, row] = key.split(',').map(Number);
      ctx.fillRect(col * CELL, row * CELL, CELL, CELL);
    });
  }

  function renderAoes() {
    aoes.forEach(function (aoe) {
      ctx.fillStyle   = 'rgba(139,26,26,0.25)';
      ctx.strokeStyle = 'rgba(139,26,26,0.7)';
      ctx.lineWidth   = 2;
      if (aoe.shape === 'circle') {
        ctx.beginPath();
        ctx.arc(aoe.cx * CELL, aoe.cy * CELL, aoe.r * CELL, 0, Math.PI * 2);
        ctx.fill(); ctx.stroke();
      } else if (aoe.shape === 'cone' && aoe.points) {
        ctx.beginPath();
        ctx.moveTo(aoe.points[0][0] * CELL, aoe.points[0][1] * CELL);
        aoe.points.slice(1).forEach(function(p){ ctx.lineTo(p[0]*CELL, p[1]*CELL); });
        ctx.closePath(); ctx.fill(); ctx.stroke();
      } else if (aoe.shape === 'line') {
        ctx.lineWidth = (aoe.width || 1) * CELL;
        ctx.beginPath();
        ctx.moveTo(aoe.x1 * CELL, aoe.y1 * CELL);
        ctx.lineTo(aoe.x2 * CELL, aoe.y2 * CELL);
        ctx.stroke();
      }
    });
  }

  function renderTokens() {
    tokens.forEach(function (t) {
      const cx = t.col * CELL + CELL / 2;
      const cy = t.row * CELL + CELL / 2;
      const r  = 18;
      const color = FACTION_COLOR[t.faction] || FACTION_COLOR.neutral;

      // Circle
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#f4ead5';
      ctx.lineWidth = 2;
      ctx.stroke();

      // HP bar
      const barW = 40, barH = 4;
      const barX = cx - barW / 2, barY = cy + r + 4;
      const hpFrac = (t.hp_max > 0) ? Math.max(0, t.hp / t.hp_max) : 0;
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.fillRect(barX, barY, barW, barH);
      ctx.fillStyle = hpFrac > 0.5 ? '#3a6b3a' : hpFrac > 0.25 ? '#8b6914' : '#8b1a1a';
      ctx.fillRect(barX, barY, barW * hpFrac, barH);

      // Name
      ctx.fillStyle = '#f4ead5';
      ctx.font = '9px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.fillText(t.name || '', cx, barY + barH + 9);
    });
  }

  // ---------------------------------------------------------------
  //  WS event handlers
  // ---------------------------------------------------------------
  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[map] WsBridge not found'); return; }

    bridge.on('scene_set', function (d) {
      gridCols = d.cols || 0;
      gridRows = d.rows || 0;
      showGrid = !!d.grid;
      if (d.image_url) setSceneImage(d.image_url);
      render();
    });

    bridge.on('scene_clear', function () {
      clearSceneImage();
      showGrid = false;
      fog.clear(); tokens.clear(); aoes.clear();
      render();
    });

    bridge.on('token_add', function (d) {
      tokens.set(d.id, { col: d.col, row: d.row, name: d.name,
                         faction: d.faction, hp: d.hp, hp_max: d.hp_max });
      render();
    });

    bridge.on('token_move', function (d) {
      var t = tokens.get(d.id);
      if (t) { t.col = d.col; t.row = d.row; render(); }
    });

    bridge.on('token_remove', function (d) {
      tokens.delete(d.id); render();
    });

    bridge.on('token_update', function (d) {
      var t = tokens.get(d.id);
      if (t) { t.hp = d.hp; render(); }
    });

    bridge.on('fog_reveal', function (d) {
      (d.cells || []).forEach(function (c) { fog.delete(c[0] + ',' + c[1]); });
      render();
    });

    bridge.on('fog_reset', function (d) {
      fog.clear();
      for (var r = 0; r < (d.rows || 0); r++) {
        for (var c = 0; c < (d.cols || 0); c++) {
          fog.add(c + ',' + r);
        }
      }
      render();
    });

    bridge.on('aoe_add',   function (d) { aoes.set(d.id, d); render(); });
    bridge.on('aoe_clear', function (d) { aoes.delete(d.id); render(); });

    resize();
  });

})();
```

---

## Integration Seams

**§1 — `#scene-display` position:** CSS already has `position: relative` (via `#scene-display` block). Canvas is `position: absolute; inset: 0`. No conflict.

**§2 — `#scene-label` z-index:** Already at `z-index: 1` in style.css. Canvas at `z-index: 2`. Canvas renders above label. If label should remain visible, swap canvas to z-index: 0 and render grid behind. **Decision: canvas above label; label only visible when canvas is empty.** Label disappears once scene renders — acceptable, it's a placeholder.

**§3 — CSS grid on `#scene-display`:** `::before` pseudo-element renders faint CSS grid at 40px. Once canvas renders its own grid, the CSS pseudo-grid will show through (double grid). **Solution:** map.js adds `scene-canvas-active` class to `#scene-display` on first render; style.css hides `::before` when that class is present. Add one CSS rule in the style.css additions block.

**§4 — main.js handles `combat_start`/`combat_end` on `#scene-surface`:** map.js does not touch these. No conflict.

---

## Gate Tests (file: `tests/test_ui_2d_map_gate.py`)

| ID | Check |
|----|-------|
| MAP-01 | `map.js` exists in `client2d/` |
| MAP-02 | `map.js` contains `scene-canvas` |
| MAP-03 | `map.js` contains `scene_set` |
| MAP-04 | `map.js` contains `token_add` |
| MAP-05 | `map.js` contains `fog_reveal` |
| MAP-06 | `map.js` contains `aoe_add` |
| MAP-07 | `map.js` contains `ResizeObserver` |
| MAP-08 | `map.js` contains `FACTION_COLOR` |
| MAP-09 | `index.html` contains `scene-canvas` |
| MAP-10 | `index.html` contains `map.js` |
| MAP-11 | `index.html` contains `scene-img-a` |
| MAP-12 | `style.css` contains `scene-canvas` |

---

## Preflight

```
pytest tests/test_ui_2d_map_gate.py             # 12/12
pytest tests/test_ui_2d_relayout_002_gate.py    # 14/14
pytest tests/test_ui_2d_relayout_gate.py        # 12/12
```
