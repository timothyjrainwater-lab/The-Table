/* =============================================================
   DnD 3.5 — 2D Illustrated Table Client
   ws.js — WebSocket connection, reconnect logic, message routing
   ============================================================= */

class WsBridge {
  constructor(url = 'ws://localhost:8765/ws') {
    this._url = url;
    this._ws = null;
    this._handlers = {};   // { msg_type: [fn, ...] }
    this._retries = 0;
    this._maxRetries = 10;
    this._retryDelay = 2000; // ms
    this._retryTimer = null;
    this._connected = false;
    this._statusEl = null;
  }

  /** Call once to attach status element and open connection */
  init() {
    this._statusEl = document.getElementById('ws-status');
    this.connect();
  }

  connect() {
    this._setStatus('connecting');
    try {
      this._ws = new WebSocket(this._url);
    } catch (e) {
      console.error('[WS] Failed to create WebSocket:', e);
      this._scheduleReconnect();
      return;
    }

    this._ws.addEventListener('open', () => {
      console.log('[WS] Connected to', this._url);
      this._connected = true;
      this._retries = 0;
      this._setStatus('connected');

      // Join message on connect
      this.send({
        msg_type: 'session_control',
        command: 'join',
        msg_id: this._uuid(),
        timestamp: Date.now() / 1000
      });
    });

    this._ws.addEventListener('message', (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        console.warn('[WS] Non-JSON message received:', event.data);
        return;
      }
      this._route(data);
    });

    this._ws.addEventListener('close', (event) => {
      console.log('[WS] Connection closed:', event.code, event.reason);
      this._connected = false;
      this._setStatus('disconnected');
      this._scheduleReconnect();
    });

    this._ws.addEventListener('error', (event) => {
      console.error('[WS] WebSocket error:', event);
      // close event will fire after error, which triggers reconnect
    });
  }

  /** Send a JSON object */
  send(obj) {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
      console.warn('[WS] Cannot send — not connected:', obj);
      return;
    }
    this._ws.send(JSON.stringify(obj));
  }

  /** Register a handler for a specific msg_type.
   *  Use '*' to receive all messages. */
  on(msgType, handler) {
    if (!this._handlers[msgType]) {
      this._handlers[msgType] = [];
    }
    this._handlers[msgType].push(handler);
  }

  /** Remove a handler for a specific msg_type. */
  off(msgType, handler) {
    if (!this._handlers[msgType]) return;
    this._handlers[msgType] = this._handlers[msgType].filter(h => h !== handler);
  }

  // ---------------------------------------------------------------
  //  Private
  // ---------------------------------------------------------------

  _route(data) {
    const type = data.msg_type;

    // Fire specific handlers
    if (this._handlers[type]) {
      this._handlers[type].forEach(fn => {
        try { fn(data); } catch (e) { console.error('[WS] Handler error for', type, e); }
      });
    }

    // Fire wildcard handlers
    if (this._handlers['*']) {
      this._handlers['*'].forEach(fn => {
        try { fn(data); } catch (e) { console.error('[WS] Wildcard handler error:', e); }
      });
    }
  }

  _scheduleReconnect() {
    if (this._retryTimer) return; // already scheduled
    if (this._retries >= this._maxRetries) {
      console.error('[WS] Max retries reached. Giving up.');
      return;
    }
    this._retries++;
    const delay = this._retryDelay * this._retries; // back-off: 2s, 4s, 6s …
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this._retries}/${this._maxRetries})`);
    this._retryTimer = setTimeout(() => {
      this._retryTimer = null;
      this.connect();
    }, delay);
  }

  _setStatus(state) {
    if (!this._statusEl) return;
    this._statusEl.className = `ws-status-${state}`;
    this._statusEl.title = `WS: ${state}`;
  }

  _uuid() {
    // Simple UUID v4 — no external dependency
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
}

// Expose globally for main.js
window.WsBridge = WsBridge;
