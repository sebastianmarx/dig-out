"""Game state. Everything is plain data (JSON-serialisable) so it can live in DynamoDB."""

from typing import Any, Literal

from pydantic import BaseModel, Field

PendingKind = Literal[
    "choose_place",      # after a simple move roll
    "extort_response",   # target of an extortion: comply / refuse / react
    "combat",            # current fighter must play weapons or yield
    "discard",           # discard N cards (hand limit, raid, smuggler)
    "choose_card",       # pick a card from options (snitch, informant, phone)
    "beaten",            # reaction window before receiving beatings
]


class GameOptions(BaseModel):
    win_points: int | None = None       # None = by player count (rules.yaml)
    team_mode: bool = False             # not implemented yet
    dig_in: bool = False                # not implemented yet
    turn_seconds: int | None = None     # None = no time limit (default while testing)
    reaction_seconds: int | None = None


class PlayerState(BaseModel):
    id: str
    name: str
    seat: int
    place: str
    hand: list[str] = Field(default_factory=list)       # card instance ids
    tunnel: list[str] = Field(default_factory=list)     # dug tools, in order
    bonus_points: int = 0                               # e.g. ex-miner
    gang: str | None = None                             # gang card instance id
    background: str                                     # background id
    background_revealed: bool = False
    beatings: int = 0
    cigarettes: int = 0
    prepared_weapon: str | None = None
    hand_limit: int = 10
    protected: bool = False                             # phantom: no extortion until own next turn


class TurnState(BaseModel):
    player: str
    number: int = 1
    actions_left: int = 2
    used: list[str] = Field(default_factory=list)       # once-per-turn markers: search, extort, craft, reroll


class Pending(BaseModel):
    id: int
    kind: PendingKind
    player: str                                         # who has to decide
    data: dict[str, Any] = Field(default_factory=dict)


class GameState(BaseModel):
    id: str
    version: int = 0
    options: GameOptions
    phase: Literal["running", "finished"] = "running"
    players: list[PlayerState]
    cards: dict[str, str]                               # instance id -> card def id
    search_deck: list[str]                              # top = last
    search_discard: list[str] = Field(default_factory=list)
    piles: dict[str, list[str]]                         # spoon/pickaxe/shovel/knife, top = last
    gang_piles: dict[str, list[str]]                    # top = last, returned cards go to index 0
    gang_of_card: dict[str, str]                        # gang card instance id -> gang id
    turn: TurnState
    pending: list[Pending] = Field(default_factory=list)  # stack, active = last
    queue: list[dict[str, Any]] = Field(default_factory=list)  # deferred steps, run when nothing is pending
    next_pending_id: int = 1
    rng: int
    win_points: int
    winner: str | None = None

    def player(self, player_id: str) -> PlayerState:
        return next(p for p in self.players if p.id == player_id)

    @property
    def active_pending(self) -> Pending | None:
        return self.pending[-1] if self.pending else None

    def actor(self) -> str:
        """Who has to act now: the pending decider, else the turn player."""
        pending = self.active_pending
        return pending.player if pending else self.turn.player
