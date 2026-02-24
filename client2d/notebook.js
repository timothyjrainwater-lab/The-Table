/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   notebook.js — Notebook: draw, transcript, bestiary tabs
   WO-UI-2D-NOTEBOOK-001
   ============================================================= */

(function () {
  'use strict';

  const MAX_TRANSCRIPT = 200;

  const drawer = document.getElementById('notebook-drawer');

  // Build notebook shell into drawer
  drawer.innerHTML =
    '<div class="nb-tab-bar">' +
      '<button class="nb-tab-btn active" data-tab="draw">Draw</button>' +
      '<button class="nb-tab-btn" data-tab="transcript">Transcript</button>' +
      '<button class="nb-tab-btn" data-tab="bestiary">Bestiary</button>' +
    '</div>' +
    '<div id="nb-panel-draw" class="nb-panel active">' +
      '<div class="nb-draw-locked">' +
        '<div class="nb-draw-locked-icon">&#9871;</div>' +
        '<div>Ink requires consent \u2014 write gating is v2</div>' +
      '</div>' +
    '</div>' +
    '<div id="nb-panel-transcript" class="nb-panel"></div>' +
    '<div id="nb-panel-bestiary" class="nb-panel"></div>';

  const transcriptPanel = document.getElementById('nb-panel-transcript');
  const bestiaryPanel   = document.getElementById('nb-panel-bestiary');

  // Tab switching
  drawer.querySelectorAll('.nb-tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      drawer.querySelectorAll('.nb-tab-btn').forEach(function (b) { b.classList.remove('active'); });
      drawer.querySelectorAll('.nb-panel').forEach(function (p) { p.classList.remove('active'); });
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
