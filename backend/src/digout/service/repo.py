"""Game storage behind a small interface: in memory for the devserver, DynamoDB in AWS (digout.aws.store)."""

from typing import Protocol

from .models import Game


class ConflictError(Exception):
    """Someone else changed the game in the meantime (optimistic locking)."""


class GameRepository(Protocol):
    def get(self, game_id: str) -> Game | None: ...
    def by_code(self, code: str) -> Game | None: ...
    def open_games(self) -> list[Game]: ...
    def put(self, game: Game) -> None:
        """Store the game if game.rev still matches the stored revision; increments game.rev."""
    def delete(self, game_id: str) -> None: ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._games: dict[str, Game] = {}

    def get(self, game_id: str) -> Game | None:
        game = self._games.get(game_id)
        return game.model_copy(deep=True) if game else None

    def by_code(self, code: str) -> Game | None:
        game = next((g for g in self._games.values() if g.code == code.upper()), None)
        return game.model_copy(deep=True) if game else None

    def open_games(self) -> list[Game]:
        return [g.model_copy(deep=True) for g in self._games.values() if g.status == "lobby"]

    def put(self, game: Game) -> None:
        stored = self._games.get(game.id)
        if (stored.rev if stored else 0) != game.rev:
            raise ConflictError(game.id)
        game.rev += 1
        self._games[game.id] = game.model_copy(deep=True)

    def delete(self, game_id: str) -> None:
        self._games.pop(game_id, None)
