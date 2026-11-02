"""Player intents. Clients send these as JSON ({"type": ..., ...}); the engine validates them."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _Action(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ----------------------------------------------------------- turn actions ---

class Search(_Action):
    type: Literal["search"] = "search"


class MoveRoll(_Action):
    type: Literal["move_roll"] = "move_roll"
    fixed: int | None = Field(default=None, ge=1, le=6)   # reveal the gambler background and pick the face


class MoveCautious(_Action):
    type: Literal["move_cautious"] = "move_cautious"
    place: str


class JoinGang(_Action):
    type: Literal["join_gang"] = "join_gang"
    gang: str
    cards: list[str]


class PlayCard(_Action):
    type: Literal["play_card"] = "play_card"
    card: str
    target: str | None = None
    place: str | None = None


class Extort(_Action):
    type: Literal["extort"] = "extort"
    target: str
    tool: Literal["spoon", "pickaxe", "shovel"]
    weapon: str


class Craft(_Action):
    type: Literal["craft"] = "craft"
    recipe: str
    cards: list[str]
    use_background: bool = False


class Dig(_Action):
    type: Literal["dig"] = "dig"
    tools: list[str] = Field(min_length=1, max_length=3)
    use_background: bool = False


class StealSpoon(_Action):
    type: Literal["steal_spoon"] = "steal_spoon"


class Heal(_Action):
    type: Literal["heal"] = "heal"


class Sell(_Action):
    type: Literal["sell"] = "sell"
    cards: list[str] = Field(min_length=1)


class Buy(_Action):
    type: Literal["buy"] = "buy"
    offer: str


class Train(_Action):
    type: Literal["train"] = "train"
    weapon: str


class RevealBackground(_Action):
    type: Literal["reveal_background"] = "reveal_background"
    target: str | None = None
    place: str | None = None
    cards: list[str] = Field(default_factory=list)


class EndTurn(_Action):
    type: Literal["end_turn"] = "end_turn"


# ------------------------------------------------------ pending responses ---

class ChoosePlace(_Action):
    type: Literal["choose_place"] = "choose_place"
    place: str


class Reroll(_Action):
    type: Literal["reroll"] = "reroll"


class Comply(_Action):
    type: Literal["comply"] = "comply"


class Refuse(_Action):
    type: Literal["refuse"] = "refuse"


class React(_Action):
    """Cancel an extortion: with a 'distraction' card, or (card=None) by revealing the briber background."""
    type: Literal["react"] = "react"
    card: str | None = None


class PlayWeapon(_Action):
    type: Literal["play_weapon"] = "play_weapon"
    card: str                                    # weapon instance id, or "prepared"


class Yield(_Action):
    type: Literal["yield"] = "yield"


class Skip(_Action):
    type: Literal["skip"] = "skip"


class Brawl(_Action):
    type: Literal["brawl"] = "brawl"


class Discard(_Action):
    type: Literal["discard"] = "discard"
    cards: list[str]


class PickCard(_Action):
    type: Literal["pick_card"] = "pick_card"
    card: str
    give: str | None = None                      # phone: own card handed over in exchange


class TakeBeating(_Action):
    type: Literal["take_beating"] = "take_beating"


class Shrug(_Action):
    """Reveal 'tough' and ignore the beatings."""
    type: Literal["shrug"] = "shrug"


Action = Annotated[
    Search | MoveRoll | MoveCautious | JoinGang | PlayCard | Extort | Craft | Dig | StealSpoon | Heal | Sell | Buy
    | Train | RevealBackground | EndTurn | ChoosePlace | Reroll | Comply | Refuse | React | PlayWeapon | Yield
    | Skip | Brawl | Discard | PickCard | TakeBeating | Shrug,
    Field(discriminator="type"),
]
ACTION_ADAPTER: TypeAdapter[Action] = TypeAdapter(Action)

RESPONSES_BY_PENDING: dict[str, set[str]] = {
    "choose_place": {"choose_place", "reroll"},
    "extort_response": {"comply", "refuse", "react"},
    "combat": {"play_weapon", "yield", "skip", "brawl"},
    "discard": {"discard"},
    "choose_card": {"pick_card"},
    "beaten": {"take_beating", "shrug"},
}


def parse_action(payload: dict) -> Action:  # type: ignore[type-arg]
    return ACTION_ADAPTER.validate_python(payload)
