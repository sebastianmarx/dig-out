"""Mutable rule context for one `apply` call: state + static data + RNG + collected events."""

from dataclasses import dataclass, field
from typing import Any

from .data import Background, CardDef, GameData
from .models import GameState, Pending, PlayerState
from .rng import Rng


class IllegalAction(Exception):
    """The action is not allowed in the current state (state stays unchanged)."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise IllegalAction(message)


@dataclass
class Event:
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    to: list[str] | None = None          # None = visible to everyone

    def as_dict(self) -> dict[str, Any]:
        return {"type": self.type, **self.data}


class Ctx:
    def __init__(self, state: GameState, data: GameData) -> None:
        self.s = state
        self.d = data
        self.events: list[Event] = []
        self._rng = Rng(state.rng)

    def finish(self) -> None:
        self.s.rng = self._rng.state

    # --------------------------------------------------------------- random ---
    def roll(self) -> int:
        return self._rng.randint(1, 6)

    def shuffle(self, items: list[Any]) -> None:
        self._rng.shuffle(items)

    def random_card(self, player: PlayerState) -> str | None:
        return self._rng.choice(player.hand) if player.hand else None

    def sample(self, items: list[str], k: int) -> list[str]:
        pool = list(items)
        self._rng.shuffle(pool)
        return pool[:k]

    # --------------------------------------------------------------- events ---
    def emit(self, event_type: str, to: list[str] | None = None, **data: Any) -> None:
        self.events.append(Event(event_type, data, to))

    # ---------------------------------------------------------------- cards ---
    def card(self, card_id: str) -> CardDef:
        return self.d.cards[self.s.cards[card_id]]

    def def_id(self, card_id: str) -> str:
        return self.s.cards[card_id]

    def take_from_hand(self, player: PlayerState, card_id: str) -> None:
        require(card_id in player.hand, f"card {card_id} is not in your hand")
        player.hand.remove(card_id)

    def discard(self, card_id: str) -> None:
        """Board items go back on top of their pile, everything else onto the search discard."""
        def_id = self.def_id(card_id)
        if def_id in self.s.piles:
            self.s.piles[def_id].append(card_id)
        else:
            self.s.search_discard.append(card_id)

    def draw(self, player: PlayerState, count: int) -> list[str]:
        drawn: list[str] = []
        for _ in range(count):
            if not self.s.search_deck:
                if not self.s.search_discard:
                    break
                self.s.search_deck, self.s.search_discard = self.s.search_discard, []
                self.shuffle(self.s.search_deck)
                self.emit("deck_reshuffled")
            drawn.append(self.s.search_deck.pop())
        player.hand.extend(drawn)
        self.emit("drew", player=player.id, count=len(drawn))
        self.emit("drew_cards", to=[player.id], player=player.id, cards=drawn)
        return drawn

    def take_from_pile(self, player: PlayerState, pile: str, count: int = 1) -> list[str]:
        stack = self.s.piles[pile]
        taken = [stack.pop() for _ in range(min(count, len(stack)))]
        player.hand.extend(taken)
        if taken:
            self.emit("took_from_pile", player=player.id, pile=pile, cards=taken)
        return taken

    def give_card(self, giver: PlayerState, receiver: PlayerState, card_id: str, public: bool = False) -> None:
        self.take_from_hand(giver, card_id)
        receiver.hand.append(card_id)
        if public:
            self.emit("card_passed", source=giver.id, player=receiver.id, card=card_id)
        else:
            self.emit("card_passed", source=giver.id, player=receiver.id)
            self.emit("card_passed_detail", to=[giver.id, receiver.id], source=giver.id, player=receiver.id,
                      card=card_id)

    def tools_in_hand(self, player: PlayerState, tool: str) -> list[str]:
        return [c for c in player.hand if self.def_id(c) == tool]

    # -------------------------------------------------------------- players ---
    def player(self, player_id: str) -> PlayerState:
        require(any(p.id == player_id for p in self.s.players), f"unknown player {player_id}")
        return self.s.player(player_id)

    def others(self, player: PlayerState) -> list[PlayerState]:
        return [p for p in self.s.players if p.id != player.id]

    def at_place(self, player: PlayerState) -> list[PlayerState]:
        return [p for p in self.others(player) if p.place == player.place]

    def gang(self, player: PlayerState) -> str | None:
        return self.s.gang_of_card[player.gang] if player.gang else None

    def has_ability(self, player: PlayerState, ability: str) -> bool:
        gang = self.gang(player)
        return gang is not None and self.d.gangs[gang].ability == ability

    def background(self, player: PlayerState) -> Background:
        return self.d.backgrounds[player.background]

    def can_reveal(self, player: PlayerState, effect: str) -> bool:
        return not player.background_revealed and self.background(player).effect == effect

    def reveal(self, player: PlayerState, effect: str) -> int:
        """Reveal the background and return its strength (gang bonus applied)."""
        require(self.can_reveal(player, effect), "background not available")
        bg = self.background(player)
        player.background_revealed = True
        self.emit("background_revealed", player=player.id, background=bg.id)
        return self.bg_amount(player)

    def gang_bonus(self, player: PlayerState) -> bool:
        return self.gang(player) == self.background(player).gang

    def bg_amount(self, player: PlayerState) -> int:
        bg = self.background(player)
        if self.gang_bonus(player) and bg.gang_amount is not None:
            return bg.gang_amount
        return bg.amount

    def points(self, player: PlayerState) -> int:
        return sum(self.card(c).points for c in player.tunnel) + player.bonus_points

    # ---------------------------------------------------- turn bookkeeping ---
    def spend(self, player: PlayerState, actions: int = 1) -> None:
        require(self.s.turn.actions_left >= actions, "not enough actions left")
        self.s.turn.actions_left -= actions

    def once_per_turn(self, marker: str) -> None:
        require(marker not in self.s.turn.used, f"'{marker}' only once per turn")
        self.s.turn.used.append(marker)

    def move(self, player: PlayerState, place: str) -> None:
        require(place in self.d.place_ids, f"unknown place {place}")
        player.place = place
        self.emit("moved", player=player.id, place=place)

    # ----------------------------------------------------- pending & queue ---
    def push_pending(self, kind: str, player: PlayerState, **data: Any) -> Pending:
        pending = Pending(id=self.s.next_pending_id, kind=kind, player=player.id, data=data)
        self.s.next_pending_id += 1
        self.s.pending.append(pending)
        self.emit("waiting_for", player=player.id, kind=kind)
        return pending

    def pop_pending(self) -> None:
        self.s.pending.pop()

    def enqueue_front(self, *steps: dict[str, Any]) -> None:
        self.s.queue[0:0] = list(steps)

    def enqueue(self, *steps: dict[str, Any]) -> None:
        self.s.queue.extend(steps)

    def check_win(self) -> None:
        if self.s.phase != "running":
            return
        order = sorted(self.s.players, key=lambda p: p.id != self.s.turn.player)
        for player in order:
            if self.points(player) >= self.s.win_points:
                self.s.phase = "finished"
                self.s.winner = player.id
                self.s.pending.clear()
                self.s.queue.clear()
                self.emit("game_won", player=player.id, points=self.points(player))
                return
