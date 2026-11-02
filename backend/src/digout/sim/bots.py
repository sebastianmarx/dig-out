"""Simple bots on top of legal_actions(): random (fuzzing) and a priority heuristic (balancing, later fill-ins)."""

import random
from collections.abc import Callable

from digout.engine import Action, GameData, GameState, legal_actions

Bot = Callable[[GameState, str, GameData, random.Random], Action]


def random_bot(state: GameState, player_id: str, data: GameData, rnd: random.Random) -> Action:
    actions = legal_actions(state, player_id, data)
    # Ending the turn early is legal at any time; make it rarer so games progress.
    weighted = [a for a in actions if a.type != "end_turn"] or actions
    if rnd.random() < 0.15 or not weighted:
        weighted = actions
    return rnd.choice(weighted)


PRIORITY = {
    # responses
    "take_beating": 1, "shrug": 5, "comply": 2, "refuse": 3, "react": 6, "play_weapon": 6, "yield": 1,
    "skip": 7, "brawl": 7, "choose_place": 1, "reroll": 0, "discard": 1, "pick_card": 1,
    # turn actions
    "dig": 100, "craft": 80, "buy": 70, "heal": 65, "steal_spoon": 60, "join_gang": 40, "play_card": 35,
    "reveal_background": 30, "search": 50, "extort": 45, "sell": 20, "train": 15, "move_roll": 25,
    "move_cautious": 10, "end_turn": 0,
}


def _tool_points(data: GameData, state: GameState, player_id: str) -> int:
    hand = state.player(player_id).hand
    return sum(data.cards[state.cards[c]].points for c in hand)


def heuristic_bot(state: GameState, player_id: str, data: GameData, rnd: random.Random) -> Action:
    actions = legal_actions(state, player_id, data)
    me = state.player(player_id)
    has_tools = _tool_points(data, state, player_id) > 0

    def score(action: Action) -> float:
        base = PRIORITY.get(action.type, 10)
        match action.type:
            case "move_roll" | "move_cautious":
                wants = "cellblock" if has_tools and me.beatings < 2 else (
                    "infirmary" if me.beatings else "recreation" if me.cigarettes >= 6 else "cafeteria")
                if getattr(action, "place", None) == wants:
                    base += 40
            case "choose_place":
                if has_tools and action.place == "cellblock":
                    base += 10
            case "sell":
                # sell junk only when it buys something
                base += 30 if me.cigarettes + len(action.cards) >= 6 else -30
            case "play_weapon":
                base += 1
            case "end_turn":
                base = 1 if state.turn.actions_left == 0 else -1
        return base + rnd.random()

    return max(actions, key=score)
