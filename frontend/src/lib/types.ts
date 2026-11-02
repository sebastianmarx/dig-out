// Mirrors the server views (backend/src/digout/engine/view.py, service/service.py).

export type Action = { type: string } & Record<string, unknown>;

export interface PlayerPublic {
  id: string;
  name: string;
  seat: number;
  place: string;
  hand_count: number | null;
  tunnel: string[];
  points: number;
  gang: string | null;
  background: string | null;
  beatings: number;
  cigarettes: number;
  prepared_weapon: string | null;
  protected: boolean;
}

export interface HandCard {
  id: string;
  card: string;
}

export interface Me {
  id: string;
  hand: HandCard[];
  background: string;
  background_revealed: boolean;
  hand_limit: number;
}

export interface PendingOption {
  id: string;
  card: string;
  owner: string;
}

export interface Pending {
  id: number;
  kind: "choose_place" | "extort_response" | "combat" | "discard" | "choose_card" | "beaten";
  player: string;
  data: Record<string, unknown> & { options?: unknown; count?: number; reason?: string };
}

export interface View {
  id: string;
  version: number;
  phase: "running" | "finished";
  winner: string | null;
  win_points: number;
  turn: { player: string; number: number; actions_left: number; used: string[] };
  players: PlayerPublic[];
  me: Me | null;
  piles: Record<string, number>;
  gang_piles: Record<string, number>;
  search_deck: number;
  search_discard: { count: number; top: string | null };
  pending: Pending | null;
}

export interface Seat {
  user_id: string;
  name: string;
  character: string | null;
  ready: boolean;
}

export interface LobbyGame {
  id: string;
  code: string;
  host: string;
  status: "lobby" | "running" | "finished";
  options: Record<string, unknown>;
  seats: Seat[];
}

export type GameEvent = { type: string } & Record<string, unknown>;

export interface StateMessage {
  t: "state";
  lobby: LobbyGame;
  view: View;
  legal: Action[];
  deadline: number | null;
  events: GameEvent[];
}

export interface BoardRoom {
  index: number;
  outline: [number, number][]; // floor corners (normalized image coords): left, bottom, right, top
  label: [number, number];
  top: [number, number];
  slots: [number, number][];
}

export interface BoardLayout {
  image: { width: number; height: number };
  unit_height: number;
  rooms: Record<string, BoardRoom>;
}

export interface CardDef {
  id: string;
  name: string;
  kind: string;
  value: number;
  points: number;
  text: string;
  effect: string | null;
}

export interface PlaceDef {
  id: string;
  name: string;
  search: number;
  actions: string[];
  craft_allowed: boolean;
}

export interface GangDef {
  id: string;
  name: string;
  text: string;
  cards: number;
  requires: { from: string[] | "any"; distinct: number };
}

export interface GameData {
  board: { places: PlaceDef[]; dice: Record<string, string[]> };
  cards: Record<string, CardDef>;
  gangs: Record<string, GangDef>;
  backgrounds: Record<string, { id: string; name: string; text: string; timing: string }>;
  rules: {
    recipes: { id: string; gives: string; needs: Record<string, number> }[];
    market: { id: string; gives: string; amount: number; cost: number }[];
  };
}
