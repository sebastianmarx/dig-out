"""Static game data loaded from game-data/*.yaml. The models double as the data schema."""

import os
from functools import cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

CardKind = Literal["material", "weapon", "accessory", "tool", "action", "valuable", "gadget"]
Timing = Literal["own_turn", "on_dig", "on_craft", "on_roll", "on_extorted", "on_beaten", "in_combat"]
TOOLS = ("spoon", "pickaxe", "shovel")
PILES = (*TOOLS, "knife")  # open stacks on the board


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Place(Strict):
    id: str
    name: str
    search: int
    actions: list[str]
    craft_allowed: bool


class Board(Strict):
    places: list[Place]
    start_place: str
    dice: dict[int, list[str]]


class CardDef(Strict):
    id: str
    name: str
    kind: CardKind
    count: int
    value: int
    rare: bool = False
    material: str | None = None
    accessory: str | None = None          # "any" = wildcard (fake ID)
    counts_as: dict[str, int] = Field(default_factory=dict)
    counts_as_any: list[str] = Field(default_factory=list)
    points: int = 0
    effect: str | None = None
    amount: int = 0
    reaction: bool = False
    extra_beatings: int = 0
    text: str = ""


class Cards(Strict):
    search_deck: list[CardDef]
    board_piles: list[CardDef]


class GangRequirement(Strict):
    from_: list[str] | Literal["any"] = Field(alias="from")
    distinct: int


class Gang(Strict):
    id: str
    name: str
    cards: int
    requires: GangRequirement
    ability: str
    text: str


class Background(Strict):
    id: str
    name: str
    gang: str
    timing: Timing
    effect: str
    amount: int = 0
    gang_amount: int | None = None
    place: str | None = None
    text: str


class Recipe(Strict):
    id: str
    needs: dict[str, int]
    gives: str
    amount: int


class MarketOffer(Strict):
    id: str
    gives: str
    amount: int
    cost: int


class Rules(Strict):
    actions_per_turn: int
    cautious_move_cost: int
    start_hand: int
    hand_limit: int
    max_beatings: int
    prepared_weapon_max: int
    win_points: dict[int, int]
    recipes: list[Recipe]
    market: list[MarketOffer]


class GameData(Strict):
    board: Board
    cards: dict[str, CardDef]
    gangs: dict[str, Gang]
    backgrounds: dict[str, Background]
    rules: Rules

    @property
    def place_ids(self) -> list[str]:
        return [p.id for p in self.board.places]

    def place(self, place_id: str) -> Place:
        return next(p for p in self.board.places if p.id == place_id)

    def recipe(self, recipe_id: str) -> Recipe:
        return next(r for r in self.rules.recipes if r.id == recipe_id)

    def offer(self, offer_id: str) -> MarketOffer:
        return next(o for o in self.rules.market if o.id == offer_id)


def data_dir() -> Path:
    env = os.environ.get("DIGOUT_GAME_DATA")
    return Path(env) if env else Path(__file__).resolve().parents[4] / "game-data"


def _read(name: str) -> dict:  # type: ignore[type-arg]
    with open(data_dir() / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)  # type: ignore[no-any-return]


@cache
def load_game_data() -> GameData:
    cards = Cards.model_validate(_read("cards.yaml"))
    all_cards = {c.id: c for c in [*cards.search_deck, *cards.board_piles]}
    data = GameData(
        board=Board.model_validate(_read("board.yaml")),
        cards=all_cards,
        gangs={g["id"]: Gang.model_validate(g) for g in _read("gangs.yaml")["gangs"]},
        backgrounds={b["id"]: Background.model_validate(b) for b in _read("backgrounds.yaml")["backgrounds"]},
        rules=Rules.model_validate(_read("rules.yaml")),
    )
    _check(data)
    return data


def _check(data: GameData) -> None:
    """Cross-references the YAML files cannot express."""
    places = set(data.place_ids)
    assert data.board.start_place in places
    for face, options in data.board.dice.items():
        assert 1 <= face <= 6 and len(options) == 2 and set(options) <= places, face
    for recipe in data.rules.recipes:
        assert recipe.gives in data.cards
    for offer in data.rules.market:
        assert offer.gives in data.cards
    for bg in data.backgrounds.values():
        assert bg.gang in data.gangs and (bg.place is None or bg.place in places), bg.id
    for tool in TOOLS:
        assert data.cards[tool].kind == "tool"
