"""Lobby and game use cases, independent of transport (devserver now, Lambda later).

Views returned here are exactly what a client receives; nothing hidden leaves this layer.
"""

import secrets
import string
import time
from typing import Any

from pydantic import ValidationError

from digout.engine import (
    GameData,
    GameOptions,
    IllegalAction,
    apply,
    default_action,
    events_for,
    legal_actions,
    load_game_data,
    parse_action,
    start_game,
    view_for,
)
from digout.engine.ctx import Event

from .models import CHARACTERS, MAX_PLAYERS, Game, Seat
from .repo import ConflictError, GameRepository

TIMER_CHOICES = (0, 60, 90, 120)   # seconds per turn, 0 = no limit
REACTION_SECONDS = 25


class ServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _code() -> str:
    alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


class GameService:
    def __init__(self, repo: GameRepository, data: GameData | None = None) -> None:
        self.repo = repo
        self.data = data or load_game_data()

    # ------------------------------------------------------------- loading ---
    def game(self, game_id: str) -> Game:
        game = self.repo.get(game_id)
        if game is None:
            raise ServiceError("NOT_FOUND", "Spiel nicht gefunden")
        return game

    def _save(self, game: Game) -> None:
        try:
            self.repo.put(game)
        except ConflictError as exc:
            raise ServiceError("STALE", "Der Spielstand hat sich geändert") from exc

    # --------------------------------------------------------------- lobby ---
    def create_game(self, user_id: str, name: str, options: GameOptions | None = None) -> Game:
        game = Game(id=secrets.token_hex(8), code=_code(), host=user_id, created_at=time.time(),
                    options=options or GameOptions(), seats=[Seat(user_id=user_id, name=name)])
        self._save(game)
        return game

    def open_games(self) -> list[Game]:
        return sorted(self.repo.open_games(), key=lambda g: -g.created_at)

    def join(self, user_id: str, name: str, game_id: str | None = None, code: str | None = None) -> Game:
        game = self.game(game_id) if game_id else self.repo.by_code(code or "")
        if game is None:
            raise ServiceError("NOT_FOUND", "Kein Spiel mit diesem Code")
        if game.seat(user_id):
            return game
        if game.status != "lobby":
            raise ServiceError("STARTED", "Das Spiel läuft bereits")
        if len(game.seats) >= MAX_PLAYERS:
            raise ServiceError("FULL", "Das Spiel ist voll")
        game.seats.append(Seat(user_id=user_id, name=name))
        self._save(game)
        return game

    def leave(self, user_id: str, game_id: str) -> Game | None:
        game = self.game(game_id)
        if game.status != "lobby":
            raise ServiceError("STARTED", "Ein laufendes Spiel kann man nicht verlassen")
        game.seats = [s for s in game.seats if s.user_id != user_id]
        if not game.seats:
            self.repo.delete(game.id)
            return None
        if game.host == user_id:
            game.host = game.seats[0].user_id
        self._save(game)
        return game

    def lobby_op(self, user_id: str, game_id: str, op: str, character: str | None = None,
                 timer: int | None = None) -> Game:
        game = self.game(game_id)
        seat = game.seat(user_id)
        if seat is None or game.status != "lobby":
            raise ServiceError("NOT_SEATED", "Du sitzt nicht in diesem Warteraum")
        match op:
            case "character":
                if character not in CHARACTERS:
                    raise ServiceError("BAD_CHARACTER", "Unbekannte Figur")
                if any(s.character == character and s.user_id != user_id for s in game.seats):
                    raise ServiceError("TAKEN", "Figur ist schon vergeben")
                seat.character = character
            case "timer":
                if user_id != game.host:
                    raise ServiceError("NOT_HOST", "Nur der Gastgeber kann das Zeitlimit ändern")
                if timer not in TIMER_CHOICES:
                    raise ServiceError("BAD_TIMER", "Ungültiges Zeitlimit")
                game.options.turn_seconds = timer or None
                game.options.reaction_seconds = REACTION_SECONDS if timer else None
            case "ready" | "unready":
                if op == "ready" and seat.character is None:
                    raise ServiceError("NO_CHARACTER", "Wähle zuerst eine Figur")
                seat.ready = op == "ready"
            case "start":
                return self._start(game, user_id)
            case _:
                raise ServiceError("BAD_OP", "Unbekannte Aktion")
        self._save(game)
        return game

    def _start(self, game: Game, user_id: str) -> Game:
        if user_id != game.host:
            raise ServiceError("NOT_HOST", "Nur der Gastgeber kann starten")
        if len(game.seats) < 2:
            raise ServiceError("TOO_FEW", "Mindestens 2 Spieler")
        if not all(s.ready for s in game.seats):
            raise ServiceError("NOT_READY", "Noch nicht alle bereit")
        try:
            game.state = start_game(game.id, [(s.user_id, s.name) for s in game.seats], seed=secrets.randbits(63),
                                    options=game.options, data=self.data)
        except IllegalAction as exc:
            raise ServiceError("BAD_OPTIONS", str(exc)) from exc
        game.status = "running"
        self._set_deadline(game)
        self._save(game)
        return game

    # ---------------------------------------------------------------- play ---
    def act(self, user_id: str, game_id: str, version: int, payload: dict[str, Any]) -> tuple[Game, list[Event]]:
        game = self.game(game_id)
        if game.state is None or game.status != "running":
            raise ServiceError("NOT_RUNNING", "Das Spiel läuft nicht")
        if version != game.state.version:
            raise ServiceError("STALE", "Der Spielstand hat sich geändert")
        try:
            action = parse_action(payload)
        except ValidationError as exc:
            raise ServiceError("BAD_ACTION", "Ungültige Aktion") from exc
        try:
            game.state, events = apply(game.state, user_id, action, self.data)
        except IllegalAction as exc:
            raise ServiceError("ILLEGAL", str(exc)) from exc
        self._after_change(game)
        return game, events

    def timeout(self, game_id: str, version: int) -> tuple[Game, list[Event]] | None:
        """Called by a timer: if nothing happened since `version`, play the default action."""
        game = self.repo.get(game_id)
        if game is None or game.state is None or game.status != "running" or game.state.version != version:
            return None
        actor, action = default_action(game.state, self.data)
        game.state, events = apply(game.state, actor, action, self.data)
        events.insert(0, Event("timeout", {"player": actor}))
        self._after_change(game)
        return game, events

    def _after_change(self, game: Game) -> None:
        assert game.state is not None
        if game.state.phase == "finished":
            game.status = "finished"
            game.deadline = None
        else:
            self._set_deadline(game)
        self._save(game)

    def _set_deadline(self, game: Game) -> None:
        assert game.state is not None
        seconds = game.options.reaction_seconds if game.state.pending else game.options.turn_seconds
        game.deadline = time.time() + seconds if seconds else None

    # --------------------------------------------------------------- views ---
    def lobby_view(self, game: Game) -> dict[str, Any]:
        return {
            "id": game.id,
            "code": game.code,
            "host": game.host,
            "status": game.status,
            "options": game.options.model_dump(),
            "seats": [s.model_dump() for s in game.seats],
        }

    def game_view(self, game: Game, user_id: str, events: list[Event] | None = None) -> dict[str, Any]:
        assert game.state is not None
        viewer = user_id if game.seat(user_id) else None
        return {
            "lobby": self.lobby_view(game),
            "view": view_for(game.state, viewer, self.data),
            "legal": [a.model_dump() for a in legal_actions(game.state, viewer, self.data)] if viewer else [],
            "deadline": game.deadline,
            "events": events_for(events or [], viewer),
        }

    def message(self, game: Game, user_id: str, events: list[Event] | None = None) -> dict[str, Any]:
        """The WebSocket message one subscriber receives after a change."""
        if game.status == "lobby":
            return {"t": "lobby", "game": self.lobby_view(game)}
        return {"t": "state", **self.game_view(game, user_id, events)}

    def game_data_view(self) -> dict[str, Any]:
        """Static names/texts the client needs for labels (no secrets)."""
        return self.data.model_dump(by_alias=True)
