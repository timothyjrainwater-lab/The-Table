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
