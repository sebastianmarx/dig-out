import pytest

from digout.engine import IllegalAction, apply, start_game, view_for
from digout.engine import actions as A

from .helpers import DATA, act, give, join, new_game, set_background


def test_game_data_matches_the_board_game():
    assert sum(c.count for c in DATA.cards.values() if c.id not in ("spoon", "pickaxe", "shovel", "knife")) == 77
    assert len(DATA.backgrounds) == 18 and len(DATA.gangs) == 6


def test_start_deals_three_cards_and_a_background():
    state = start_game("g", [("a", "A"), ("b", "B")], seed=1, data=DATA)
    assert all(len(p.hand) == 3 and p.place == "cellblock" for p in state.players)
    assert len({p.background for p in state.players}) == 2
    assert state.win_points == 12


def test_same_seed_and_actions_give_the_same_game():
    def play(seed):
        state = start_game("g", [("a", "A"), ("b", "B")], seed=seed, data=DATA)
        for _ in range(3):
            state = act(state, state.turn.player, A.MoveRoll())
            if state.pending:
                state = act(state, state.actor(), A.ChoosePlace(place=state.pending[-1].data["options"][0]))
            state = act(state, state.turn.player, A.EndTurn())
        return state.model_dump()

    assert play(5) == play(5)
    assert play(5) != play(6)


def test_search_draws_by_place_and_only_once_per_turn():
    state = new_game()
    state.player("p0").place = "showers"
    state = act(state, "p0", A.Search())
    assert len(state.player("p0").hand) == 3
    with pytest.raises(IllegalAction):
        act(state, "p0", A.Search())


def test_crew_searches_one_more_card():
    state = new_game()
    join(state, "p0", "crew")
    state = act(state, "p0", A.Search())
    assert len(state.player("p0").hand) == 2  # cell block 1 + crew 1


def test_two_actions_per_turn():
    state = new_game()
    state = act(state, "p0", A.MoveCautious(place="yard"))
    with pytest.raises(IllegalAction):
        act(state, "p0", A.Search())


def test_end_turn_passes_to_next_seat_and_resets_actions():
    state = act(new_game(), "p0", A.EndTurn())
    assert state.turn.player == "p1" and state.turn.actions_left == 2


def test_dig_scores_points_and_wins():
    state = new_game()
    state.win_points = 3
    shovel = give(state, "p0", "shovel")[0]
    state = act(state, "p0", A.Dig(tools=[shovel]))
    assert state.phase == "finished" and state.winner == "p0"


def test_dig_only_in_cell_block_and_not_with_two_beatings():
    state = new_game()
    spoon = give(state, "p0", "spoon")[0]
    state.player("p0").beatings = 2
    with pytest.raises(IllegalAction):
        act(state, "p0", A.Dig(tools=[spoon]))
    state.player("p0").beatings = 0
    state.player("p0").place = "yard"
    with pytest.raises(IllegalAction):
        act(state, "p0", A.Dig(tools=[spoon]))


def test_craft_pickaxe_and_reject_superfluous_or_wrong_place():
    state = new_game()
    state.player("p0").place = "cafeteria"
    cards = give(state, "p0", "link", 2) + give(state, "p0", "pike")
    extra = give(state, "p0", "cap")
    with pytest.raises(IllegalAction):
        act(state, "p0", A.Craft(recipe="pickaxe", cards=cards + extra))
    crafted = act(state, "p0", A.Craft(recipe="pickaxe", cards=cards))
    assert [crafted.cards[c] for c in crafted.player("p0").hand] == ["cap", "pickaxe"]
    state.player("p0").place = "cellblock"
    with pytest.raises(IllegalAction):
        act(state, "p0", A.Craft(recipe="pickaxe", cards=cards))


def test_steel_wire_counts_as_two_links_and_handle_as_pike():
    state = new_game()
    state.player("p0").place = "yard"
    cards = give(state, "p0", "steel_wire") + give(state, "p0", "universal_handle")
    state = act(state, "p0", A.Craft(recipe="pickaxe", cards=cards))
    assert [state.cards[c] for c in state.player("p0").hand] == ["pickaxe"]


def test_mechanic_ignores_one_ingredient():
    state = new_game()
    state.player("p0").place = "yard"
    set_background(state, "p0", "mechanic")
    cards = give(state, "p0", "link", 2)
    with pytest.raises(IllegalAction):
        act(state, "p0", A.Craft(recipe="shovel", cards=cards))
    state = act(state, "p0", A.Craft(recipe="shovel", cards=cards, use_background=True))
    assert state.player("p0").background_revealed


def test_join_gang_needs_different_allowed_accessories_fake_id_is_wildcard():
    state = new_game()
    caps = give(state, "p0", "cap", 2)
    with pytest.raises(IllegalAction):
        act(state, "p0", A.JoinGang(gang="crew", cards=caps))
    fake = give(state, "p0", "fake_id")
    state = act(state, "p0", A.JoinGang(gang="crew", cards=[caps[0], fake[0]]))
    assert state.gang_of_card[state.player("p0").gang] == "crew"


def test_extortion_comply_hands_over_the_tool():
    state = new_game()
    knife = give(state, "p0", "knife")[0]
    give(state, "p1", "pickaxe")
    state = act(state, "p0", A.Extort(target="p1", tool="pickaxe", weapon=knife))
    assert state.actor() == "p1"
    state = act(state, "p1", A.Comply())
    assert [state.cards[c] for c in state.player("p0").hand] == ["knife", "pickaxe"]


def test_combat_defender_starts_loser_is_beaten_and_robbed():
    state = new_game()
    knives = give(state, "p0", "knife", 2)
    give(state, "p1", "knife")
    give(state, "p1", "shovel")
    state = act(state, "p0", A.Extort(target="p1", tool="shovel", weapon=knives[0]))
    state = act(state, "p1", A.Refuse())
    assert state.pending[-1].kind == "combat" and state.actor() == "p1"
    state = act(state, "p1", A.PlayWeapon(card=state.player("p1").hand[0]))
    assert state.actor() == "p0"
    state = act(state, "p0", A.PlayWeapon(card=knives[1]))
    state = act(state, "p1", A.Yield())
    assert state.player("p1").beatings == 1
    assert "shovel" in [state.cards[c] for c in state.player("p0").hand]


def test_shiv_win_gives_two_beatings():
    state = new_game()
    shiv = give(state, "p0", "shiv")[0]
    state = act(state, "p0", A.Extort(target="p1", tool="spoon", weapon=shiv))
    state = act(state, "p1", A.Refuse())
    state = act(state, "p1", A.Yield())
    assert state.player("p1").beatings == 2


def test_distraction_cancels_extortion():
    state = new_game()
    knife = give(state, "p0", "knife")[0]
    card = give(state, "p1", "distraction")[0]
    state = act(state, "p0", A.Extort(target="p1", tool="spoon", weapon=knife))
    state = act(state, "p1", A.React(card=card))
    assert not state.pending and state.player("p1").hand == []


def test_hidden_background_always_gets_a_beating_window():
    state = new_game()
    set_background(state, "p1", "hoarder")  # not 'tough' – the window opens anyway
    knife = give(state, "p0", "knife")[0]
    state = act(state, "p0", A.Extort(target="p1", tool="spoon", weapon=knife))
    state = act(state, "p1", A.Refuse())
    state = act(state, "p1", A.Yield())
    assert state.pending[-1].kind == "beaten"
    with pytest.raises(IllegalAction):
        act(state, "p1", A.Shrug())
    state = act(state, "p1", A.TakeBeating())
    assert state.player("p1").beatings == 1


def test_tough_ignores_beatings():
    state = new_game()
    set_background(state, "p1", "tough")
    knife = give(state, "p0", "knife")[0]
    state = act(state, "p0", A.Extort(target="p1", tool="spoon", weapon=knife))
    state = act(state, "p1", A.Refuse())
    state = act(state, "p1", A.Yield())
    state = act(state, "p1", A.Shrug())
    assert state.player("p1").beatings == 0


def test_phantom_cannot_be_extorted_until_its_next_turn():
    state = new_game()
    state.turn.player = "p1"
    set_background(state, "p1", "phantom")
    state = act(state, "p1", A.RevealBackground())
    state = act(state, "p1", A.EndTurn())
    knife = give(state, "p2", "knife")[0]
    with pytest.raises(IllegalAction):
        act(state, "p2", A.Extort(target="p1", tool="spoon", weapon=knife))


def test_hand_limit_forces_discard_before_the_turn_passes():
    state = new_game()
    give(state, "p0", "link", 12)
    state = act(state, "p0", A.EndTurn())
    assert state.pending[-1].kind == "discard" and state.pending[-1].data["count"] == 2
    state = act(state, "p0", A.Discard(cards=state.player("p0").hand[:2]))
    assert state.turn.player == "p1" and len(state.player("p0").hand) == 10


def test_buy_with_cartel_discount():
    state = new_game()
    state.player("p0").place = "recreation"
    state.player("p0").cigarettes = 5
    join(state, "p0", "cartel")
    state = act(state, "p0", A.Buy(offer="pickaxe"))
    assert state.player("p0").cigarettes == 0


def test_cave_in_removes_last_spoon():
    state = new_game()
    spoon = give(state, "p1", "spoon")[0]
    state.player("p1").hand.remove(spoon)
    state.player("p1").tunnel.append(spoon)
    card = give(state, "p0", "cave_in")[0]
    state = act(state, "p0", A.PlayCard(card=card, target="p1"))
    assert state.player("p1").tunnel == []


def test_simple_move_forces_the_other_place():
    state = new_game()
    rolled = None
    for seed in range(1, 50):  # find a seed whose roll includes the cell block
        state.rng = seed
        try_state = act(state, "p0", A.MoveRoll())
        if not try_state.pending:
            rolled = try_state
            break
    assert rolled is not None and rolled.player("p0").place in ("cafeteria", "yard")


def test_views_hide_other_hands_and_private_pending_data():
    state = new_game()
    secret = give(state, "p1", "gold_tooth")[0]
    view = view_for(state, "p0", DATA)
    assert secret not in str(view) and view["players"][1]["hand_count"] == 1
    join(state, "p1", "shadow")
    assert view_for(state, "p0", DATA)["players"][1]["hand_count"] is None
    assert view_for(state, "p1", DATA)["me"]["hand"] == [{"id": secret, "card": "gold_tooth"}]


def test_wrong_player_and_wrong_response_are_rejected():
    state = new_game()
    with pytest.raises(IllegalAction):
        apply(state, "p1", A.Search(), DATA)
    with pytest.raises(IllegalAction):
        apply(state, "p0", A.Comply(), DATA)
