/**
 * WebSocket bridge — connects frontend to backend.
 *
 * Protocol: JSON messages over ws://localhost:8765 (configurable).
 * Handles reconnection and message routing.
 */

export type MessageHandler = (data: Record<string, unknown>) => void;

export class WsBridge {
  private url: string;
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private statusEl: HTMLElement | null;

  constructor(url: string = 'ws://localhost:8765/ws') {
    this.url = url;
    this.statusEl = document.getElementById('ws-status');
  }

  connect(): void {
    this.setStatus('connecting...');
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.setStatus('connected');
      // Send join message
      this.send({
        msg_type: 'session_control',
        msg_id: crypto.randomUUID(),
        timestamp: Date.now() / 1000,
        command: 'join',
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Record<string, unknown>;
        const msgType = data.msg_type as string;
        const handlers = this.handlers.get(msgType) || [];
        for (const h of handlers) h(data);
        // Also fire a wildcard handler
        const wildcardHandlers = this.handlers.get('*') || [];
        for (const h of wildcardHandlers) h(data);
      } catch (e) {
        console.error('WS message parse error:', e);
      }
    };

    this.ws.onclose = () => {
      this.setStatus('disconnected');
      // Reconnect after 3s
      setTimeout(() => this.connect(), 3000);
    };

    this.ws.onerror = () => {
      this.setStatus('error');
    };
  }

  on(msgType: string, handler: MessageHandler): void {
    if (!this.handlers.has(msgType)) {
      this.handlers.set(msgType, []);
    }
    this.handlers.get(msgType)!.push(handler);
  }

  send(data: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private setStatus(status: string): void {
    if (this.statusEl) {
      this.statusEl.textContent = `WS: ${status}`;
    }
  }
}
