"""Local development server: REST lobby + WebSocket game, in-memory storage, fake auth.

    uv run uvicorn digout.devserver:app --reload --port 8100

Identity comes from the X-Dev-User / X-Dev-Name headers (REST) or ?user=&name= (WebSocket).
In AWS this is replaced by Cognito + API Gateway; the GameService stays the same.
"""

import asyncio
import json
import re
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from digout.engine import GameOptions
from digout.engine.ctx import Event

from .service.models import Game
from .service.repo import InMemoryRepository
from .service.service import GameService, ServiceError

MAX_MESSAGE_BYTES = 8192
NAME_RE = re.compile(r"^[\w äöüÄÖÜß.-]{1,20}$")

service = GameService(InMemoryRepository())


class Hub:
    """Tracks WebSocket subscriptions per game and pushes personalised views."""

    def __init__(self) -> None:
        self.subscribers: dict[str, dict[WebSocket, str]] = defaultdict(dict)
        self.timers: dict[str, asyncio.TimerHandle] = {}

    def subscribe(self, game_id: str, ws: WebSocket, user_id: str) -> None:
        for subs in self.subscribers.values():
            subs.pop(ws, None)
        self.subscribers[game_id][ws] = user_id

    def drop(self, ws: WebSocket) -> None:
        for subs in self.subscribers.values():
            subs.pop(ws, None)

    async def send(self, ws: WebSocket, message: dict[str, Any]) -> None:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:  # connection gone
            self.drop(ws)

    def message_for(self, game: Game, user_id: str, events: list[Event] | None = None) -> dict[str, Any]:
        return service.message(game, user_id, events)

    async def broadcast(self, game: Game, events: list[Event] | None = None) -> None:
        for ws, user_id in list(self.subscribers.get(game.id, {}).items()):
            await self.send(ws, self.message_for(game, user_id, events))
        self.schedule_timeout(game)

    async def broadcast_closed(self, game_id: str) -> None:
        for ws in list(self.subscribers.pop(game_id, {})):
            await self.send(ws, {"t": "closed", "gameId": game_id})

    def schedule_timeout(self, game: Game) -> None:
        if handle := self.timers.pop(game.id, None):
            handle.cancel()
        if game.status != "running" or game.deadline is None or game.state is None:
            return
        version = game.state.version
        delay = max(0.0, game.deadline - time.time())
        loop = asyncio.get_running_loop()
        self.timers[game.id] = loop.call_later(delay, lambda: asyncio.ensure_future(self.on_timeout(game.id, version)))

    async def on_timeout(self, game_id: str, version: int) -> None:
        result = service.timeout(game_id, version)
        if result:
            await self.broadcast(*result)


hub = Hub()


# ------------------------------------------------------------------- REST ---

def identity(request: Request) -> tuple[str, str]:
    user = request.headers.get("x-dev-user", "")
    name = request.headers.get("x-dev-name", user)
    if not user or not NAME_RE.match(name):
        raise ServiceError("UNAUTHORIZED", "Bitte anmelden")
    return user, name


def error_response(exc: ServiceError) -> JSONResponse:
    status = {"UNAUTHORIZED": 401, "NOT_FOUND": 404}.get(exc.code, 400)
    return JSONResponse({"code": exc.code, "message": exc.message}, status_code=status)


Handler = Callable[[Request, str, str], Awaitable[JSONResponse]]


def endpoint(handler: Handler) -> Callable[[Request], Awaitable[JSONResponse]]:
    """Resolve the dev identity and turn ServiceErrors into JSON error responses."""

    async def wrapped(request: Request) -> JSONResponse:
        try:
            return await handler(request, *identity(request))
        except ServiceError as exc:
            return error_response(exc)

    return wrapped


@endpoint
async def list_games(request: Request, user: str, name: str) -> JSONResponse:
    return JSONResponse([service.lobby_view(g) for g in service.open_games()])


@endpoint
async def create_game(request: Request, user: str, name: str) -> JSONResponse:
    body = await request.json() if await request.body() else {}
    options = GameOptions.model_validate(body.get("options", {}))
    game = service.create_game(user, name, options)
    return JSONResponse(service.lobby_view(game))


@endpoint
async def join_game(request: Request, user: str, name: str) -> JSONResponse:
    body = await request.json()
    game = service.join(user, name, game_id=body.get("gameId"), code=body.get("code"))
    await hub.broadcast(game)
    return JSONResponse(service.lobby_view(game))


@endpoint
async def leave_game(request: Request, user: str, name: str) -> JSONResponse:
    game_id = request.path_params["game_id"]
    game = service.leave(user, game_id)
    if game:
        await hub.broadcast(game)
    else:
        await hub.broadcast_closed(game_id)
    return JSONResponse({"ok": True})


async def game_data(request: Request) -> JSONResponse:
    return JSONResponse(service.game_data_view())


# -------------------------------------------------------------- WebSocket ---

async def ws_endpoint(ws: WebSocket) -> None:
    user = ws.query_params.get("user", "")
    name = ws.query_params.get("name", user)
    if not user or not NAME_RE.match(name):
        await ws.close(code=4401)
        return
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            if len(raw) > MAX_MESSAGE_BYTES:
                await hub.send(ws, {"t": "error", "code": "TOO_LARGE", "message": "Nachricht zu groß"})
                continue
            await handle_message(ws, user, json.loads(raw))
    except WebSocketDisconnect:
        hub.drop(ws)


async def handle_message(ws: WebSocket, user: str, msg: dict[str, Any]) -> None:
    kind = msg.get("t")
    game_id = str(msg.get("gameId", ""))
    try:
        match kind:
            case "ping":
                await hub.send(ws, {"t": "pong"})
            case "sub":
                game = service.game(game_id)
                hub.subscribe(game.id, ws, user)
                await hub.send(ws, hub.message_for(game, user))
            case "lobby":
                timer = msg.get("timer")
                game = service.lobby_op(user, game_id, str(msg.get("op")), msg.get("character"),
                                        int(timer) if timer is not None else None)
                await hub.broadcast(game)
            case "act":
                game, events = service.act(user, game_id, int(msg.get("v", -1)), msg.get("a") or {})
                await hub.broadcast(game, events)
            case _:
                raise ServiceError("BAD_MESSAGE", "Unbekannte Nachricht")
    except ServiceError as exc:
        await hub.send(ws, {"t": "error", "code": exc.code, "message": exc.message})
        if exc.code == "STALE":
            await hub.send(ws, hub.message_for(service.game(game_id), user))


app = Starlette(routes=[
    Route("/api/game-data", game_data),
    Route("/api/games", list_games, methods=["GET"]),
    Route("/api/games", create_game, methods=["POST"]),
    Route("/api/games/join", join_game, methods=["POST"]),
    Route("/api/games/{game_id}/leave", leave_game, methods=["POST"]),
    WebSocketRoute("/ws", ws_endpoint),
])
