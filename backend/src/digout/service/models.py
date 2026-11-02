"""Lobby / game records as stored by a repository (in memory now, DynamoDB later)."""

from typing import Literal

from pydantic import BaseModel, Field

from digout.engine import GameOptions, GameState

CHARACTERS = ("char.01", "char.02", "char.03", "char.04", "char.05", "char.06")
MAX_PLAYERS = 6


class Seat(BaseModel):
    user_id: str
    name: str
    character: str | None = None
    ready: bool = False


class Game(BaseModel):
    id: str
    code: str                                   # short join code
    host: str
    created_at: float
    status: Literal["lobby", "running", "finished"] = "lobby"
    options: GameOptions = Field(default_factory=GameOptions)
    seats: list[Seat] = Field(default_factory=list)
    state: GameState | None = None
    deadline: float | None = None               # unix time when the current decision times out
    rev: int = 0                                # storage revision for optimistic locking

    def seat(self, user_id: str) -> Seat | None:
        return next((s for s in self.seats if s.user_id == user_id), None)
