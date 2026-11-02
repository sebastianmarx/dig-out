import { create } from "zustand";

import { api, type Identity, loadIdentity, saveIdentity } from "./api";
import { forgetGame, rememberGame } from "./recent";
import { GameSocket } from "./socket";
import type { Action, BoardLayout, GameData, GameEvent, LobbyGame, StateMessage } from "./types";

interface LogEntry {
  id: number;
  event: GameEvent;
}

interface Store {
  identity: Identity | null;
  data: GameData | null;
  layout: BoardLayout | null;
  connected: boolean;
  gameId: string | null;
  lobby: LobbyGame | null;
  game: StateMessage | null;
  closed: boolean;
  log: LogEntry[];
  lastEvents: GameEvent[];
  error: string | null;
  busy: boolean;
  login: (name: string) => void;
  setIdentity: (identity: Identity | null) => void;
  open: (gameId: string) => void;
  leaveView: () => void;
  lobbyOp: (op: string, extra?: { character?: string; timer?: number }) => void;
  act: (action: Action) => void;
  clearError: () => void;
}

let socket: GameSocket | null = null;
let logId = 0;

function ensureSocket(identity: Identity): GameSocket {
  socket ??= new GameSocket(identity, onMessage, (connected) => useStore.setState({ connected }));
  return socket;
}

function onMessage(message: Record<string, unknown>): void {
  switch (message.t) {
    case "lobby": {
      const lobby = message.game as LobbyGame;
      rememberGame(lobby.id, `${lobby.seats.map((s) => s.name).join(", ")} · Warteraum`);
      useStore.setState({ lobby, game: null, closed: false });
      break;
    }
    case "state": {
      const state = message as unknown as StateMessage;
      const entries = state.events.map((event) => ({ id: ++logId, event }));
      rememberGame(
        state.lobby.id,
        `${state.lobby.seats.map((s) => s.name).join(", ")} · ${state.view.phase === "finished" ? "beendet" : "läuft"}`,
      );
      useStore.setState((s) => ({
        game: state,
        lobby: state.lobby,
        busy: false,
        lastEvents: state.events,
        log: [...s.log, ...entries].slice(-80),
      }));
      break;
    }
    case "closed":
      forgetGame(String(message.gameId));
      useStore.setState({ closed: true, lobby: null, game: null });
      break;
    case "error":
      useStore.setState({ error: String(message.message ?? "Fehler"), busy: false });
      break;
  }
}

export const useStore = create<Store>((set, get) => ({
  identity: loadIdentity(),
  data: null,
  layout: null,
  connected: false,
  gameId: null,
  lobby: null,
  game: null,
  closed: false,
  log: [],
  lastEvents: [],
  error: null,
  busy: false,
  login: (name) => set({ identity: saveIdentity(name) }),
  setIdentity: (identity) => set({ identity }),
  open: (gameId) => {
    const identity = get().identity;
    if (!identity) return;
    if (!get().data) void api.gameData(identity).then((data) => set({ data }));
    if (!get().layout)
      void fetch("/assets/board/board.layout.json")
        .then((r) => r.json())
        .then((layout: BoardLayout) => set({ layout }));
    set({ gameId, lobby: null, game: null, closed: false, log: [] });
    ensureSocket(identity).subscribe(gameId);
  },
  leaveView: () => set({ gameId: null, lobby: null, game: null }),
  lobbyOp: (op, extra) => {
    const { gameId } = get();
    if (gameId) socket?.send({ t: "lobby", gameId, op, ...extra });
  },
  act: (action) => {
    const { gameId, game } = get();
    if (!gameId || !game) return;
    set({ busy: true });
    socket?.send({ t: "act", gameId, v: game.view.version, a: action });
  },
  clearError: () => set({ error: null }),
}));
