/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   main.js — Entry point: instantiates WS, wires events, handles posture keys
   ============================================================= */

(function () {
  'use strict';

  // ---------------------------------------------------------------
  //  Posture management
  // ---------------------------------------------------------------
  const POSTURE_MAP = {
    '1': 'posture-standard',
    '2': 'posture-lean',
    '3': 'posture-down',
    '4': 'posture-dice',
  };

  const ALL_POSTURE_CLASSES = Object.values(POSTURE_MAP);

  function setPosture(key) {
    const cls = POSTURE_MAP[key];
    if (!cls) return;
    ALL_POSTURE_CLASSES.forEach(c => document.body.classList.remove(c));
    document.body.classList.add(cls);
    console.log('[Posture]', cls);
  }

  // Keyboard handler for posture switching (1-4)
  document.addEventListener('keydown', function (e) {
    // Suppress posture hotkeys when text input is focused
    if (document.activeElement === document.getElementById('player-input')) return;

    if (e.key === '1' || e.key === '2' || e.key === '3' || e.key === '4') {
      setPosture(e.key);
    }
  });

  // ---------------------------------------------------------------
  //  Text input bar
  // ---------------------------------------------------------------
  const playerInput = document.getElementById('player-input');
  const sendBtn = document.getElementById('send-btn');

  function submitInput() {
    const text = playerInput.value.trim();
    if (!text) return;
    ws.send({ msg_type: 'player_input', text: text });
    playerInput.value = '';
  }

  playerInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      submitInput();
    }
  });

  sendBtn.addEventListener('click', function () {
    submitInput();
  });

  // ---------------------------------------------------------------
  //  WebSocket — instantiate and connect
  // ---------------------------------------------------------------
  const ws = new WsBridge('ws://localhost:8765/ws');

  // ---------------------------------------------------------------
  //  Orb: speaking_start / speaking_stop
  // ---------------------------------------------------------------
  const orb = document.getElementById('orb');

  ws.on('speaking_start', function () {
    orb.classList.add('speaking');
  });

  ws.on('speaking_stop', function () {
    orb.classList.remove('speaking');
  });

  // ---------------------------------------------------------------
  //  Combat state: vault zone highlight
  // ---------------------------------------------------------------
  const vaultZone = document.getElementById('vault-zone');

  ws.on('combat_start', function () {
    vaultZone.classList.add('combat-active');
  });

  ws.on('combat_end', function () {
    vaultZone.classList.remove('combat-active');
  });

  // ---------------------------------------------------------------
  //  Narration: append to transcript area
  // ---------------------------------------------------------------
  const transcriptArea = document.getElementById('transcript-area');

  ws.on('narration', function (data) {
    if (!transcriptArea) return;
    if (transcriptArea.style.display === 'none' || !transcriptArea.style.display) {
      transcriptArea.style.display = 'block';
    }
    const p = document.createElement('p');
    p.textContent = data.text || '';
    transcriptArea.appendChild(p);
    transcriptArea.scrollTop = transcriptArea.scrollHeight;
  });

  // ---------------------------------------------------------------
  //  Stub: log all other message types
  // ---------------------------------------------------------------
  ws.on('*', function (data) {
    const handled = ['speaking_start', 'speaking_stop', 'combat_start', 'combat_end', 'narration'];
    if (!handled.includes(data.msg_type)) {
      console.log('[WS stub]', data.msg_type, data);
    }
  });

  // ---------------------------------------------------------------
  //  Boot
  // ---------------------------------------------------------------
  ws.init();

  // Expose for debugging
  window.__ws = ws;

  console.log('[main] 2D Illustrated Table client ready.');
})();
