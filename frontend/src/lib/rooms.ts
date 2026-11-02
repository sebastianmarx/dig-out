import type { Action, GameData, View } from "./types";

/** What a room offers, for the room labels and the room sheet. */
export const ROOM_ACTIONS: Record<string, { label: string; icon: string; hint: string }> = {
  dig: { label: "Graben", icon: "⛏️", hint: "Werkzeug in deinen Tunnel → Tunnelpunkte" },
  steal_spoon: { label: "Löffel klauen", icon: "🥄", hint: "Nimm einen Löffel vom Stapel" },
  heal: { label: "Heilen", icon: "🩹", hint: "Entferne 1 Prügel" },
  sell: { label: "Verkaufen", icon: "🚬", hint: "Karten gegen Zigaretten tauschen" },
  buy: { label: "Kaufen", icon: "🛒", hint: "Messer, Spitzhacke oder Schaufel für Zigaretten" },
  train: { label: "Trainieren", icon: "🥊", hint: "Eine Waffe für den nächsten Kampf vorbereiten" },
};

const TOOLS = new Set(["spoon", "pickaxe", "shovel"]);

/** Die faces that can lead into a room (face n offers room n or n+1). */
export function diceFor(data: GameData, place: string): number[] {
  return Object.entries(data.board.dice)
    .filter(([, options]) => options.includes(place))
    .map(([face]) => Number(face))
    .sort((a, b) => a - b);
}

/**
 * Why an action type is not possible right now (null = possible, i.e. it is in the legal list).
 * The server is the authority; these texts only explain the greyed-out buttons.
 */
export function blockedReason(type: string, place: string, view: View, data: GameData, legal: Action[]): string | null {
  if (legal.some((a) => a.type === type)) return null;
  const me = view.me;
  const player = view.players.find((p) => p.id === me?.id);
  if (!me || !player) return "Du spielst nicht mit";
  if (view.phase !== "running") return "Das Spiel ist vorbei";
  if (view.pending) return "Erst die offene Entscheidung treffen";
  if (view.turn.player !== me.id) return "Du bist nicht am Zug";
  if (player.place !== place) return "Nur wenn du in diesem Raum bist";
  if (view.turn.actions_left < 1) return "Keine Aktionen mehr – Zug beenden";
  const hand = me.hand.map((c) => data.cards[c.card]);
  switch (type) {
    case "search":
      return view.turn.used.includes("search") ? "Nur einmal pro Zug" : "Suchstapel leer";
    case "dig":
      if (player.beatings >= 2) return "Zu verprügelt zum Graben (2 Prügel)";
      return hand.some((c) => TOOLS.has(c.id)) ? "Gerade nicht möglich" : "Du brauchst ein Werkzeug (Löffel, Spitzhacke, Schaufel)";
    case "steal_spoon":
      return "Keine Löffel mehr übrig";
    case "heal":
      return "Du hast keine Prügel";
    case "sell":
      return "Du hast keine Karten";
    case "buy": {
      const cheapest = Math.min(...data.rules.market.map((o) => o.cost));
      return player.cigarettes < cheapest ? `Zu wenig Zigaretten (ab ${cheapest})` : "Ausverkauft";
    }
    case "train":
      if (player.prepared_weapon) return "Du hast schon eine vorbereitete Waffe";
      return "Du brauchst eine Waffe (Messer, Klinge)";
    case "craft":
      if (!data.board.places.find((p) => p.id === place)?.craft_allowed) return "Hier kann man nicht herstellen";
      if (player.beatings > 0) return "Mit Prügeln kann man nicht herstellen";
      if (view.turn.used.includes("craft")) return "Nur einmal pro Zug";
      return "Zutaten fehlen: 2 Kettenglieder + Spitze / Behälter / Klinge";
    default:
      return "Gerade nicht möglich";
  }
}

export function gangRequirement(data: GameData, gang: string): string {
  const req = data.gangs[gang].requires;
  if (req.from === "any") return `${req.distinct} verschiedene Accessoires`;
  return `${req.distinct} verschiedene aus ${req.from.map((a) => data.cards[a]?.name ?? a).join(", ")}`;
}
