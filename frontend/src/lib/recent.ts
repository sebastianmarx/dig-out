// Games this browser opened recently, so players can get back into a running game from the lobby.

const KEY = "digout.recent";
const MAX = 8;

export interface RecentGame {
  id: string;
  label: string;
  at: number;
}

export function recentGames(): RecentGame[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]") as RecentGame[];
  } catch {
    return [];
  }
}

function save(games: RecentGame[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(games.slice(0, MAX)));
  } catch {
    // storage unavailable: nothing to remember
  }
}

export function rememberGame(id: string, label: string): void {
  save([{ id, label, at: Date.now() }, ...recentGames().filter((g) => g.id !== id)]);
}

export function forgetGame(id: string): void {
  save(recentGames().filter((g) => g.id !== id));
}
