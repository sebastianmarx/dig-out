"""Property tests: random legal play never breaks the invariants."""

import json
import random

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from digout.engine import apply, legal_actions, start_game, view_for

from .helpers import DATA, all_card_locations


@settings(max_examples=12, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(seed=st.integers(min_value=0, max_value=2**32), players=st.integers(min_value=2, max_value=6))
def test_random_play_keeps_invariants(seed, players):
    rnd = random.Random(seed)
    state = start_game("p", [(f"p{i}", f"P{i}") for i in range(players)], seed=seed, data=DATA)
    expected_cards = sorted(state.cards)
    gang_cards = sorted(state.gang_of_card)
    for _ in range(250):
        if state.phase != "running":
            break
        actor = state.actor()
        actions = legal_actions(state, actor, DATA)
        assert actions, "the deciding player must always have a legal action"
        state, _ = apply(state, actor, rnd.choice(actions), DATA)

        locations = all_card_locations(state)
        assert sorted(locations) == expected_cards, "cards were lost or duplicated"
        in_play = [p.gang for p in state.players if p.gang]
        assert sorted(in_play + [g for pile in state.gang_piles.values() for g in pile]) == gang_cards
        for p in state.players:
            assert 0 <= p.beatings <= DATA.rules.max_beatings
            assert p.cigarettes >= 0
        for viewer in state.players:
            text = json.dumps(view_for(state, viewer.id, DATA))
            for other in state.players:
                if other.id != viewer.id:
                    pending = state.pending[-1] if state.pending else None
                    shown = set(pending.data.get("options", {})) if pending and pending.player == viewer.id else set()
                    leaked = [c for c in other.hand if f'"{c}"' in text and c not in shown]
                    assert not leaked, f"{viewer.id} sees cards of {other.id}"
