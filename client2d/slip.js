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
