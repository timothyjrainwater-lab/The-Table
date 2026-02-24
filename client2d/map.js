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

  let activeImg  = imgA;
  let pendingImg = imgB;

  let gridCols = 0, gridRows = 0, showGrid = false;
  let fog    = new Set();   // 'col,row' strings
  let tokens = new Map();   // id → {col,row,name,faction,hp,hp_max}
  let aoes   = new Map();   // id → {shape,...}
  let firstRender = true;

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
      var tmp   = activeImg;
      activeImg  = pendingImg;
      pendingImg = tmp;
    };
  }

  function clearSceneImage() {
    activeImg.classList.remove('active');
    pendingImg.classList.remove('active');
    activeImg.src  = '';
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
    // Hide the CSS pseudo-grid once canvas takes over
    if (firstRender) {
      canvas.parentElement.classList.add('scene-canvas-active');
      firstRender = false;
    }
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
        aoe.points.slice(1).forEach(function (p) { ctx.lineTo(p[0] * CELL, p[1] * CELL); });
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
