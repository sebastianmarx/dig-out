import { api, type Identity } from "./api";
import { getConfig } from "./config";

type Listener = (message: Record<string, unknown>) => void;

// WebSocket with automatic reconnect; re-subscribes to the current game after reconnecting.
export class GameSocket {
  private ws: WebSocket | null = null;
  private retry = 0;
  private gameId: string | null = null;
  private closedByUs = false;
  private queue: string[] = [];

  constructor(
    private identity: Identity,
    private onMessage: Listener,
    private onStatus: (connected: boolean) => void,
  ) {
    this.connect();
  }

  private async url(): Promise<string> {
    const config = getConfig();
    if (config.mode === "aws") {
      const { ticket } = await api.wsTicket(this.identity); // one-time ticket, the JWT never goes into a URL
      return `${config.wsUrl}?ticket=${encodeURIComponent(ticket)}`;
    }
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    const params = new URLSearchParams({ user: this.identity.id, name: this.identity.name });
    return `${scheme}://${location.host}/ws?${params}`;
  }

  private connect(): void {
    void this.url().then(
      (url) => this.open(url),
      () => this.retryLater(),
    );
  }

  private retryLater(): void {
    if (this.closedByUs) return;
    const delay = Math.min(10_000, 500 * 2 ** this.retry++);
    setTimeout(() => this.connect(), delay);
  }

  private open(url: string): void {
    const ws = new WebSocket(url);
    this.ws = ws;
    ws.onopen = () => {
      this.retry = 0;
      this.onStatus(true);
      if (this.gameId) ws.send(JSON.stringify({ t: "sub", gameId: this.gameId }));
      for (const raw of this.queue.splice(0)) ws.send(raw);
    };
    ws.onmessage = (event) => this.onMessage(JSON.parse(event.data as string));
    ws.onclose = () => {
      this.onStatus(false);
      this.retryLater();
    };
  }

  subscribe(gameId: string): void {
    this.gameId = gameId;
    this.send({ t: "sub", gameId });
  }

  send(message: Record<string, unknown>): void {
    const raw = JSON.stringify(message);
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(raw);
    else this.queue.push(raw);
  }

  close(): void {
    this.closedByUs = true;
    this.ws?.close();
  }
}
