"""Public engine API: start_game, apply, legal_actions, view_for, default_action.

Pure functions on plain data: no I/O, no clock. apply() never mutates its input; on an
illegal action it raises IllegalAction and the caller keeps the old state.
"""

from . import actions as A
from .ctx import Ctx, Event, IllegalAction, require
from .data import PILES, GameData, load_game_data
from .models import GameOptions, GameState, PlayerState, TurnState
from .rng import Rng
from .rules import RESPONSE_HANDLERS, TURN_HANDLERS, run_queue


def start_game(game_id: str, players: list[tuple[str, str]], seed: int, options: GameOptions | None = None,
               data: GameData | None = None) -> GameState:
    """players: [(id, name), ...] in seating order."""
    data = data or load_game_data()
    options = options or GameOptions()
    require(2 <= len(players) <= 6, "2 to 6 players")
    require(len({pid for pid, _ in players}) == len(players), "player ids must be unique")
    require(not options.team_mode and not options.dig_in, "team mode and Dig In are not implemented yet")
    rng = Rng(seed)

    cards: dict[str, str] = {}

    def make(def_id: str, count: int) -> list[str]:
        ids = [f"c{len(cards) + i + 1}" for i in range(count)]
        cards.update({i: def_id for i in ids})
        return ids

    search_deck = [cid for card in data.cards.values() if card.id not in PILES for cid in make(card.id, card.count)]
    rng.shuffle(search_deck)
    piles = {pile: make(pile, data.cards[pile].count) for pile in PILES}
    gang_piles: dict[str, list[str]] = {}
    gang_of_card: dict[str, str] = {}
    for gang in data.gangs.values():
        ids = [f"g{len(gang_of_card) + i + 1}" for i in range(gang.cards)]
        gang_piles[gang.id] = ids
        gang_of_card.update({i: gang.id for i in ids})
    backgrounds = list(data.backgrounds)
    rng.shuffle(backgrounds)

    player_states = []
    for seat, (pid, name) in enumerate(players):
        hand = [search_deck.pop() for _ in range(data.rules.start_hand)]
        player_states.append(PlayerState(id=pid, name=name, seat=seat, place=data.board.start_place, hand=hand,
                                         background=backgrounds.pop(), hand_limit=data.rules.hand_limit))
    first = rng.choice([pid for pid, _ in players])
    return GameState(
        id=game_id,
        options=options,
        players=player_states,
        cards=cards,
        search_deck=search_deck,
        piles=piles,
        gang_piles=gang_piles,
        gang_of_card=gang_of_card,
        turn=TurnState(player=first, actions_left=data.rules.actions_per_turn),
        rng=rng.state,
        win_points=options.win_points or data.rules.win_points[len(players)],
    )


def apply(state: GameState, player_id: str, action: A.Action,
          data: GameData | None = None) -> tuple[GameState, list[Event]]:
    data = data or load_game_data()
    require(state.phase == "running", "the game is over")
    s = state.model_copy(deep=True)
    ctx = Ctx(s, data)
    pending = s.active_pending
    if pending:
        require(player_id == pending.player, "waiting for another player")
        require(action.type in A.RESPONSES_BY_PENDING[pending.kind], f"expected a response to '{pending.kind}'")
        RESPONSE_HANDLERS[action.type](ctx, pending, s.player(player_id), action)
    else:
        require(player_id == s.turn.player, "not your turn")
        require(action.type in TURN_HANDLERS, f"'{action.type}' is only a response")
        TURN_HANDLERS[action.type](ctx, s.player(player_id), action)
    run_queue(ctx)
    ctx.check_win()
    ctx.finish()
    s.version += 1
    return s, ctx.events


def default_action(state: GameState, data: GameData | None = None) -> tuple[str, A.Action]:
    """What happens when the deciding player runs out of time (docs/rules.md §11)."""
    data = data or load_game_data()
    actor = state.actor()
    pending = state.active_pending
    if pending is None:
        return actor, A.EndTurn()
    p = state.player(actor)
    match pending.kind:
        case "choose_place":
            return actor, A.ChoosePlace(place=pending.data["options"][0])
        case "extort_response":
            return actor, A.Refuse()
        case "combat":
            return actor, A.Yield()
        case "discard":
            count = min(pending.data["count"], len(p.hand))
            return actor, A.Discard(cards=p.hand[len(p.hand) - count:])
        case "choose_card":
            card = next(iter(pending.data["options"]))
            give = next((c for c in p.hand if c != pending.data.get("phone")), None)
            return actor, A.PickCard(card=card, give=give if pending.data["mode"] == "phone" else None)
        case _:
            return actor, A.TakeBeating()


__all__ = ["IllegalAction", "apply", "default_action", "start_game"]
