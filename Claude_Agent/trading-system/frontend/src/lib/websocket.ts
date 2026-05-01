export type WSEventType =
  | 'price_update'
  | 'signal'
  | 'order_filled'
  | 'portfolio_update';

export interface WSPriceUpdate {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  timestamp: string;
}

export interface WSSignal {
  id: string;
  symbol: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD' | 'BLOCK' | 'REDUCE';
  strategy: string;
  strength: number;
  price: number;
  timestamp: string;
}

export interface WSOrderFilled {
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  fill_price: number;
  timestamp: string;
}

export interface WSPortfolioUpdate {
  total_value: number;
  cash: number;
  day_pnl: number;
  day_pnl_pct: number;
  total_pnl: number;
}

type EventCallback<T = unknown> = (data: T) => void;

class WebSocketManager {
  private socket: WebSocket | null = null;
  private clientId: string | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 5000;
  private isIntentionalClose = false;
  private listeners: Map<string, Set<EventCallback>> = new Map();

  connect(clientId: string): void {
    this.clientId = clientId;
    this.isIntentionalClose = false;
    this._openSocket();
  }

  private _openSocket(): void {
    if (!this.clientId) return;

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const url = `${wsUrl}/ws/${this.clientId}`;

    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        console.log('[WS] Connected to', url);
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.socket.onmessage = (event: MessageEvent) => {
        try {
          const message = JSON.parse(event.data as string) as {
            type: WSEventType;
            data: unknown;
          };
          const callbacks = this.listeners.get(message.type);
          if (callbacks) {
            callbacks.forEach((cb) => cb(message.data));
          }
        } catch (err) {
          console.error('[WS] Failed to parse message', err);
        }
      };

      this.socket.onerror = (err) => {
        console.error('[WS] Error', err);
      };

      this.socket.onclose = (event) => {
        console.warn('[WS] Closed', event.code, event.reason);
        if (!this.isIntentionalClose) {
          this._scheduleReconnect();
        }
      };
    } catch (err) {
      console.error('[WS] Failed to open socket', err);
      this._scheduleReconnect();
    }
  }

  private _scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    console.log(`[WS] Reconnecting in ${this.reconnectDelay}ms…`);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this._openSocket();
    }, this.reconnectDelay);
  }

  subscribe<T = unknown>(event: WSEventType, callback: EventCallback<T>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback as EventCallback);
  }

  unsubscribe<T = unknown>(event: WSEventType, callback: EventCallback<T>): void {
    this.listeners.get(event)?.delete(callback as EventCallback);
  }

  send(data: unknown): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    this.isIntentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }

  get isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
const wsManager = new WebSocketManager();
export default wsManager;
