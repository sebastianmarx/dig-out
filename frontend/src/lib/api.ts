import { accessToken, signOut, tokenIdentity } from "./auth";
import { getConfig } from "./config";
import type { GameData, LobbyGame } from "./types";

// Development identity (replaced by Cognito later). Stored per browser.
export interface Identity {
  id: string;
  name: string;
}

const KEY = "digout.identity";

export function loadIdentity(): Identity | null {
  if (getConfig().mode === "aws") return tokenIdentity();
  // Dev only: ?as=Name logs this tab in as that player (session storage, so tabs can differ).
  if (import.meta.env.DEV) {
    const as = new URLSearchParams(location.search).get("as");
    if (as) sessionStorage.setItem(KEY, JSON.stringify({ id: as.toLowerCase(), name: as }));
    const session = sessionStorage.getItem(KEY);
    if (session) return JSON.parse(session) as Identity;
  }
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Identity) : null;
  } catch {
    return null;
  }
}

export function saveIdentity(name: string): Identity {
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 12) || "spieler";
  const identity = { id: `${slug}-${Math.random().toString(36).slice(2, 7)}`, name };
  try {
    localStorage.setItem(KEY, JSON.stringify(identity));
  } catch {
    // private mode: identity lives for this tab only
  }
  return identity;
}

export function clearIdentity(): void {
  signOut();
  try {
    localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export async function authHeaders(identity: Identity): Promise<Record<string, string>> {
  if (getConfig().mode === "aws") {
    const token = await accessToken();
    if (!token) throw new ApiError("UNAUTHORIZED", "Bitte neu anmelden");
    return { Authorization: `Bearer ${token}` };
  }
  return { "X-Dev-User": identity.id, "X-Dev-Name": identity.name };
}

async function request<T>(identity: Identity, path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders(identity)) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const json = await response.json();
  if (!response.ok) throw new ApiError(json.code ?? "ERROR", json.message ?? "Fehler");
  return json as T;
}

export const api = {
  openGames: (id: Identity) => request<LobbyGame[]>(id, "/api/games"),
  createGame: (id: Identity) => request<LobbyGame>(id, "/api/games", {}),
  joinByCode: (id: Identity, code: string) => request<LobbyGame>(id, "/api/games/join", { code }),
  joinById: (id: Identity, gameId: string) => request<LobbyGame>(id, "/api/games/join", { gameId }),
  leave: (id: Identity, gameId: string) => request<{ ok: boolean }>(id, `/api/games/${gameId}/leave`, {}),
  gameData: async (id: Identity): Promise<GameData> => request<GameData>(id, "/api/game-data"),
  wsTicket: (id: Identity) => request<{ ticket: string }>(id, "/api/ws-ticket", {}),
};
