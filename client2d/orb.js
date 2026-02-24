/* orb.js — Speaker Panel wiring: portrait, beats, orb pulse
   WO-UI-2D-ORB-001
   Depends on: ws.js (WsBridge), main.js (window.__ws exposed, .speaking class toggle already wired)
   Load order: ws.js → orb.js → main.js
*/
(function () {
  'use strict';

  const portrait  = document.getElementById('speaker-portrait');
  const beats     = document.getElementById('speaker-beats');
  const orbInner  = document.querySelector('#orb > div');  // 36px circle

  const IDLE_FILTER   = 'brightness(0.5) sepia(0.4) saturate(0.6)';
  const ACTIVE_FILTER = 'brightness(1) sepia(0) saturate(1)';
  const MAX_BEATS = 8;

  // Idle state: DM crest placeholder
  function setIdle() {
    portrait.style.filter = IDLE_FILTER;
    portrait.style.backgroundImage = '';
    portrait.classList.remove('has-portrait');
  }

  // Speaking state
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
    // Orb pulse: main.js toggles .speaking on #orb (the container).
    // CSS pulse targets #orb > div:first-child.speaking — proxy to inner div.
    orbInner.classList.add('speaking');
  }

  function stopSpeaking() {
    setIdle();
    orbInner.classList.remove('speaking');
  }

  // Wire to WsBridge — window.__ws is exposed by main.js after load fires
  window.addEventListener('load', function () {
    var bridge = window.__ws;
    if (!bridge) { console.warn('[orb] WsBridge not found'); return; }
    bridge.on('speaking_start', setSpeaking);
    bridge.on('speaking_stop',  stopSpeaking);
    setIdle();
    console.log('[orb] Speaker Panel wired.');
  });

})();
