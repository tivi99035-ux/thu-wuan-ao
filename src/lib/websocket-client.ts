/**
 * WebSocket Client for Real-time Updates
 * Handles connection management and message processing
 */

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;

interface WebSocketMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private sessionId: string | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private connectionHandlers: ConnectionHandler[] = [];
  private disconnectionHandlers: ConnectionHandler[] = [];
  private isConnecting: boolean = false;

  constructor(url?: string) {
    this.url = url || this._getWebSocketUrl();
  }

  private _getWebSocketUrl(): string {
    if (typeof window === 'undefined') return '';
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
  }

  async connect(sessionId?: string): Promise<void> {
    if (this.isConnecting || this.isConnected()) {
      return;
    }

    this.isConnecting = true;
    this.sessionId = sessionId || this.sessionId;

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.sessionId ? `${this.url}?session_id=${this.sessionId}` : this.url;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('🔗 WebSocket kết nối thành công');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.connectionHandlers.forEach(handler => handler());
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data: WebSocketMessage = JSON.parse(event.data);
            this._handleMessage(data);
          } catch (error) {
            console.error('Lỗi phân tích tin nhắn WebSocket:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('🔌 WebSocket đã ngắt kết nối');
          this.isConnecting = false;
          this.ws = null;
          this.disconnectionHandlers.forEach(handler => handler());
          this._attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('🚨 Lỗi WebSocket:', error);
          this.isConnecting = false;
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  send(message: any): boolean {
    if (!this.isConnected()) {
      console.warn('WebSocket chưa kết nối');
      return false;
    }

    try {
      this.ws!.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Lỗi gửi tin nhắn WebSocket:', error);
      return false;
    }
  }

  // Event handlers
  on(eventType: string, handler: MessageHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  off(eventType: string, handler?: MessageHandler): void {
    if (!this.handlers.has(eventType)) return;

    if (handler) {
      const handlers = this.handlers.get(eventType)!;
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    } else {
      this.handlers.delete(eventType);
    }
  }

  onConnection(handler: ConnectionHandler): void {
    this.connectionHandlers.push(handler);
  }

  onDisconnection(handler: ConnectionHandler): void {
    this.disconnectionHandlers.push(handler);
  }

  // Job-specific methods
  subscribeToJob(jobId: string): void {
    this.send({
      type: 'subscribe_job',
      job_id: jobId,
      timestamp: new Date().toISOString()
    });
  }

  unsubscribeFromJob(jobId: string): void {
    this.send({
      type: 'unsubscribe_job',
      job_id: jobId,
      timestamp: new Date().toISOString()
    });
  }

  requestSystemStatus(): void {
    this.send({
      type: 'get_system_status',
      timestamp: new Date().toISOString()
    });
  }

  ping(): void {
    this.send({
      type: 'ping',
      timestamp: new Date().toISOString()
    });
  }

  private _handleMessage(data: WebSocketMessage): void {
    const { type } = data;

    // Handle specific message types
    switch (type) {
      case 'connection':
        if (data.session_id) {
          this.sessionId = data.session_id;
          console.log(`📱 Session ID nhận được: ${this.sessionId}`);
        }
        break;

      case 'job_update':
        console.log(`📊 Cập nhật công việc ${data.job_id}: ${data.status} (${data.progress}%)`);
        break;

      case 'system_status':
        console.log('🖥️ Trạng thái hệ thống đã cập nhật');
        break;

      case 'error':
        console.error('❌ Lỗi từ server:', data.message);
        break;

      case 'pong':
        console.log('🏓 Pong nhận được từ server');
        break;

      default:
        console.log(`📨 Tin nhắn không xác định: ${type}`);
    }

    // Call registered handlers
    const handlers = this.handlers.get(type) || [];
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error(`Lỗi trong handler cho ${type}:`, error);
      }
    });
  }

  private _attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('🔴 Đã hết số lần thử kết nối lại');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff

    console.log(`🔄 Thử kết nối lại (${this.reconnectAttempts}/${this.maxReconnectAttempts}) sau ${delay}ms...`);

    setTimeout(() => {
      this.connect(this.sessionId || undefined);
    }, delay);
  }

  // Utility methods
  getSessionId(): string | null {
    return this.sessionId;
  }

  getConnectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }
}

// Global WebSocket client instance
export const wsClient = new WebSocketClient();

// Auto-connect when module loads (browser only)
if (typeof window !== 'undefined') {
  // Generate session ID from localStorage or create new one
  let sessionId = localStorage.getItem('seed-vc-session-id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('seed-vc-session-id', sessionId);
  }

  // Connect with stored session ID
  wsClient.connect(sessionId || undefined).catch(console.error);

  // Setup periodic ping
  setInterval(() => {
    if (wsClient.isConnected()) {
      wsClient.ping();
    }
  }, 30000); // Ping every 30 seconds

  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    wsClient.disconnect();
  });
}

export default WebSocketClient;