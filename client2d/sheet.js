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
        // WO-UI-PHASE1-POLISH-001 GAP-12: ability_check_declare not yet handled server-side.
        // Disabled to prevent unknown-msg-type error noise during integration testing.
        // Re-enable when ws_bridge._route_message() implements the handler.
        // block.addEventListener('click', function () {
        //   var bridge = window.__ws;
        //   if (bridge) bridge.send({ msg_type: 'ability_check_declare', ability: key });
        // });
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
