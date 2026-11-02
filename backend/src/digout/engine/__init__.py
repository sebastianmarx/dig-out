"""Dig Out game engine – pure rules, no I/O. See docs/rules.md."""

from .actions import Action, parse_action
from .ctx import Event, IllegalAction
from .data import GameData, load_game_data
from .engine import apply, default_action, start_game
from .legal import legal_actions
from .models import GameOptions, GameState
from .view import events_for, view_for

__all__ = [
    "Action",
    "Event",
    "GameData",
    "GameOptions",
    "GameState",
    "IllegalAction",
    "apply",
    "default_action",
    "events_for",
    "legal_actions",
    "load_game_data",
    "parse_action",
    "start_game",
    "view_for",
]
