import type { Action, GameData, GameEvent, PendingOption, StateMessage } from "./types";

const TOOL_NAMES: Record<string, string> = { spoon: "Löffel", pickaxe: "Spitzhacke", shovel: "Schaufel" };

export const PENDING_TITLES: Record<string, string> = {
  choose_place: "Wohin gehst du?",
  extort_response: "Du wirst erpresst!",
  combat: "Kampf!",
  discard: "Karten abwerfen",
  choose_card: "Karte wählen",
  beaten: "Du bekommst Prügel",
};

export class Labels {
  constructor(
    private data: GameData,
    private game: StateMessage,
  ) {}

  place = (id: unknown): string => this.data.board.places.find((p) => p.id === id)?.name ?? String(id);
  card = (def: unknown): string => this.data.cards[String(def)]?.name ?? String(def);
  gang = (id: unknown): string => this.data.gangs[String(id)]?.name ?? String(id);
  background = (id: unknown): string => this.data.backgrounds[String(id)]?.name ?? String(id);
  tool = (id: unknown): string => TOOL_NAMES[String(id)] ?? String(id);
  player = (id: unknown): string =>
    id === this.game.view.me?.id ? "Du" : (this.game.view.players.find((p) => p.id === id)?.name ?? String(id));

  /** Card definition of an instance id the viewer may know (own hand or offered options). */
  cardOf = (instance: unknown): string => {
    const own = this.game.view.me?.hand.find((c) => c.id === instance);
    if (own) return own.card;
    const options = this.game.view.pending?.data.options as PendingOption[] | undefined;
    return options?.find((o) => o.id === instance)?.card ?? "?";
  };

  action = (a: Action): string => {
    const target = a.target ? ` → ${this.player(a.target)}` : "";
    switch (a.type) {
      case "search":
        return "Suchen";
      case "move_roll":
        return a.fixed ? `Glücksspieler: ${a.fixed} würfeln` : "Würfeln & gehen";
      case "move_cautious":
        return `Vorsichtig → ${this.place(a.place)}`;
      case "join_gang":
        return `${this.gang(a.gang)} beitreten`;
      case "play_card":
        return `${this.card(this.cardOf(a.card))}${target}${a.place ? ` → ${this.place(a.place)}` : ""}`;
      case "extort":
        return `Erpressen: ${this.player(a.target)} (${this.tool(a.tool)})`;
      case "craft": {
        const recipe = this.data.rules.recipes.find((r) => r.id === a.recipe);
        return `Herstellen: ${this.card(recipe?.gives)}${a.use_background ? " (Mechaniker)" : ""}`;
      }
      case "dig":
        return `Graben: ${(a.tools as string[]).map((t) => this.card(this.cardOf(t))).join(", ")}${
          a.use_background ? " (Hintergrund)" : ""
        }`;
      case "steal_spoon":
        return "Löffel klauen";
      case "heal":
        return "Heilen";
      case "sell":
        return `Verkaufen (${(a.cards as string[]).length} Karten)`;
      case "buy": {
        const offer = this.data.rules.market.find((o) => o.id === a.offer);
        return `Kaufen: ${offer?.amount === 2 ? "2× " : ""}${this.card(offer?.gives)} (${offer?.cost} Zig.)`;
      }
      case "train":
        return "Waffe trainieren";
      case "reveal_background":
        return `Hintergrund aufdecken${target}${a.place ? ` → ${this.place(a.place)}` : ""}`;
      case "end_turn":
        return "Zug beenden";
      case "choose_place":
        return `→ ${this.place(a.place)}`;
      case "reroll":
        return "Neu würfeln (Triade)";
      case "comply":
        return "Nachgeben";
      case "refuse":
        return "Weigern – Kampf!";
      case "react":
        return a.card ? "Ablenkung spielen" : "Bestecher aufdecken";
      case "play_weapon":
        return a.card === "prepared" ? "Vorbereitete Waffe" : `${this.card(this.cardOf(a.card))} spielen`;
      case "yield":
        return "Aufgeben";
      case "skip":
        return "Aussetzen (Biker)";
      case "brawl":
        return "Raufbold aufdecken";
      case "discard":
        return "Abwerfen";
      case "pick_card":
        return `${this.card(this.cardOf(a.card))} nehmen`;
      case "take_beating":
        return "Einstecken";
      case "shrug":
        return "Zäh wie Leder aufdecken";
      default:
        return a.type;
    }
  };

  event = (e: GameEvent): string | null => {
    const who = this.player(e.player);
    switch (e.type) {
      case "turn_started":
        return `— ${who} ${who === "Du" ? "bist" : "ist"} am Zug —`;
      case "moved":
        return `${who} → ${this.place(e.place)}`;
      case "rolled":
        return `${who} würfelt ${e.value}${e.fixed ? " (festgelegt)" : ""}`;
      case "drew":
        return `${who} zieht ${e.count} Karte(n)`;
      case "drew_cards":
        return `Gezogen: ${(e.cards as string[]).map((c) => this.card(this.cardOf(c))).join(", ")}`;
      case "took_from_pile":
        return `${who} nimmt ${(e.cards as string[]).length}× ${this.card(e.pile)}`;
      case "joined_gang":
        return `${who} tritt ${this.gang(e.gang)} bei`;
      case "card_played":
        return `${who} spielt ${this.card(e.card)}`;
      case "extortion":
        return `${who} erpresst ${this.player(e.target)} mit ${this.card(e.weapon)} um ${this.tool(e.tool)}`;
      case "extortion_complied":
        return `${who} gibt nach`;
      case "extortion_cancelled":
        return `Erpressung abgebrochen (${e.by === "briber" ? "Bestecher" : "Ablenkung"})`;
      case "combat_started":
        return `Kampf: ${this.player(e.attacker)} gegen ${this.player(e.defender)}`;
      case "weapon_played":
        return `${who} schlägt mit ${this.card(e.weapon)} zu`;
      case "combat_won":
        return `${who} gewinnt den Kampf`;
      case "combat_skipped":
        return `${who} weicht aus`;
      case "brawl":
        return `${who} prügelt wie ein Raufbold!`;
      case "beaten":
        return `${who} bekommt ${e.amount} Prügel`;
      case "beating_ignored":
        return `${who} steckt die Prügel weg`;
      case "card_passed":
        return `${this.player(e.source)} gibt ${who} eine Karte`;
      case "crafted":
        return `${who} stellt etwas her`;
      case "dug":
        return `${who} gräbt (${e.points} Punkte)`;
      case "healed":
        return `${who} wird verarztet`;
      case "sold":
        return `${who} verkauft für ${e.cigarettes} Zigaretten`;
      case "bought":
        return `${who} kauft (${e.cost} Zig.)`;
      case "trained":
        return `${who} trainiert im Hof`;
      case "background_revealed":
        return `${who} deckt auf: ${this.background(e.background)}`;
      case "discarded":
        return `${who} wirft ${(e.cards as string[]).length} Karte(n) ab`;
      case "hand_seen":
        return `${who} schaut in die Karten von ${this.player(e.target)}`;
      case "tunnel_collapsed":
        return `Tunnel von ${this.player(e.target)} stürzt ein!`;
      case "tunnel_tool_stolen":
        return `${who} stiehlt aus dem Tunnel von ${this.player(e.target)}`;
      case "cigarettes_gained":
        return `${who} erhält ${e.amount} Zigaretten`;
      case "cigarettes_paid":
        return `${who} zahlt ${e.amount} Zigaretten`;
      case "timeout":
        return `Zeit abgelaufen für ${who}`;
      case "deck_reshuffled":
        return "Suchstapel neu gemischt";
      case "game_won":
        return `${who} ist ausgebrochen!`;
      default:
        return null;
    }
  };
}
