"""Test helpers: build a game and arrange the state by hand."""

from digout.engine import GameState, apply, load_game_data, start_game
from digout.engine import actions as A

DATA = load_game_data()


def new_game(players: int = 3, seed: int = 7) -> GameState:
    state = start_game("t", [(f"p{i}", f"P{i}") for i in range(players)], seed=seed, data=DATA)
    state.turn.player = "p0"
    for p in state.players:  # empty hands, hidden backgrounds revealed so no reaction windows interfere
        state.search_discard.extend(p.hand)
        p.hand = []
        p.background_revealed = True
    return state


def give(state: GameState, player_id: str, def_id: str, count: int = 1) -> list[str]:
    """Move card instances of `def_id` from wherever they are into the player's hand."""
    player = state.player(player_id)
    moved: list[str] = []
    for card_id, card_def in state.cards.items():
        if len(moved) == count:
            break
        if card_def != def_id or any(card_id in p.hand or card_id in p.tunnel for p in state.players):
            continue
        for stack in (state.search_deck, state.search_discard, *state.piles.values()):
            if card_id in stack:
                stack.remove(card_id)
                break
        player.hand.append(card_id)
        moved.append(card_id)
    assert len(moved) == count, f"not enough {def_id}"
    return moved


def set_background(state: GameState, player_id: str, background: str, revealed: bool = False) -> None:
    p = state.player(player_id)
    p.background = background
    p.background_revealed = revealed


def join(state: GameState, player_id: str, gang: str) -> None:
    state.player(player_id).gang = state.gang_piles[gang].pop()


def act(state: GameState, player_id: str, action: A.Action) -> GameState:
    new_state, _ = apply(state, player_id, action, DATA)
    return new_state


def all_card_locations(state: GameState) -> list[str]:
    locations = [*state.search_deck, *state.search_discard]
    for pile in state.piles.values():
        locations += pile
    for p in state.players:
        locations += p.hand + p.tunnel + ([p.prepared_weapon] if p.prepared_weapon else [])
    return locations
