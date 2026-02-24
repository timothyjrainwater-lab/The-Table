/* orb.js — Speaker Panel wiring: portrait, beats, orb pulse
   WO-UI-2D-ORB-001
   Depends on: ws.js (WsBridge), main.js (window.__ws exposed, orb .speaking toggle)
*/
(function () {
  'use strict';

  const portrait  = document.getElementById('speaker-portrait');
  const beats     = document.getElementById('speaker-beats');
  const orbInner  = document.querySelector('#orb > div');  // 36px circle

  const IDLE_FILTER   = 'brightness(0.5) sepia(0.4) saturate(0.6)';
  const ACTIVE_FILTER = 'brightness(1) sepia(0) saturate(1)';
  const MAX_BEATS = 8;

  // Idle state: DM crest placeholder — dim filter, no portrait image
  function setIdle() {
    portrait.style.filter = IDLE_FILTER;
    portrait.style.backgroundImage = '';
    portrait.classList.remove('has-portrait');
  }

  // Speaking state: clear filter, optionally load NPC portrait, append beat
  function setSpeaking(data) {
    portrait.style.filter = ACTIVE_FILTER;
    if (data.portrait_url) {
      portrait.style.backgroundImage = 'url(' + data.portrait_url + ')';
      portrait.style.backgroundSize  = 'cover';
      portrait.style.backgroundPosition = 'center top';
      portrait.classList.add('has-portrait');
    }
    if (data.text) {
      const beat = document.createElement('div');
      beat.className = 'beat';
      beat.textContent = data.text;
      beats.appendChild(beat);
      while (beats.children.length > MAX_BEATS) {
        beats.removeChild(beats.firstChild);
      }
    }
    // Proxy .speaking to inner div — CSS pulse targets #orb > div:first-child.speaking
    orbInner.classList.add('speaking');
  }

  function stopSpeaking() {
    setIdle();
    orbInner.classList.remove('speaking');
  }

  // Wire to WsBridge — window.__ws exposed by main.js; load fires after all scripts
  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[orb] WsBridge not found'); return; }
    bridge.on('speaking_start', setSpeaking);
    bridge.on('speaking_stop',  stopSpeaking);
    setIdle();
    console.log('[orb] Speaker Panel wired.');
  });

})();
