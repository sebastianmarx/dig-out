"""Lambda entry points. One deployment package, one handler per function:

    digout.aws.handlers.http          HTTP API (/api/*, behind CloudFront)
    digout.aws.handlers.ws_connect    WebSocket $connect (one-time ticket)
    digout.aws.handlers.ws_disconnect WebSocket $disconnect
    digout.aws.handlers.ws_default    WebSocket messages (sub / lobby / act / ping)
    digout.aws.handlers.timeout       EventBridge Scheduler: decision timed out
    digout.aws.handlers.pre_signup    Cognito pre sign-up: platform password check, auto-confirm
"""

import hashlib
import hmac
import json
import os
import re
from functools import cache
from typing import Any

import boto3

from digout.engine import GameOptions
from digout.service.service import GameService, ServiceError

from .realtime import Realtime
from .security import gate_set_cookie, sign_gate_cookie, verify_password
from .store import ConnectionStore, DynamoGameRepository

NAME_RE = re.compile(r"^[\w äöüÄÖÜß.-]{1,20}$")
MAX_GATE_ATTEMPTS = 5
MAX_MESSAGE_BYTES = 8192


@cache
def service() -> GameService:
    return GameService(DynamoGameRepository(os.environ["TABLE_NAME"]))


@cache
def store() -> ConnectionStore:
    return ConnectionStore(os.environ["TABLE_NAME"])


@cache
def realtime() -> Realtime:
    return Realtime(store())


@cache
def secret(name: str) -> str:
    response = boto3.client("ssm").get_parameter(Name=name, WithDecryption=True)
    return str(response["Parameter"]["Value"])


def _json(status: int, body: Any, cookies: list[str] | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(body),
    }
    if cookies:
        response["cookies"] = cookies
    return response


def _error(exc: ServiceError) -> dict[str, Any]:
    status = {"UNAUTHORIZED": 401, "NOT_FOUND": 404, "RATE_LIMITED": 429}.get(exc.code, 400)
    return _json(status, {"code": exc.code, "message": exc.message})


# ====================================================================== HTTP

def http(event: dict[str, Any], context: Any) -> dict[str, Any]:
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if not hmac.compare_digest(headers.get("x-origin-verify", ""), os.environ["ORIGIN_VERIFY"]):
        return _json(403, {"code": "FORBIDDEN", "message": "Nur über die Website erreichbar"})
    route = event["routeKey"]
    body = json.loads(event.get("body") or "{}") if event.get("body") else {}
    try:
        if route == "POST /api/gate":
            return gate(headers, body)
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        user, name = str(claims["sub"]), str(claims.get("username", claims["sub"]))
        svc = service()
        match route:
            case "GET /api/game-data":
                return _json(200, svc.game_data_view())
            case "GET /api/games":
                return _json(200, [svc.lobby_view(g) for g in svc.open_games()])
            case "POST /api/games":
                game = svc.create_game(user, name, GameOptions.model_validate(body.get("options", {})))
                return _json(200, svc.lobby_view(game))
            case "POST /api/games/join":
                game = svc.join(user, name, game_id=body.get("gameId"), code=body.get("code"))
                realtime().broadcast(svc, game)
                return _json(200, svc.lobby_view(game))
            case "POST /api/games/{game_id}/leave":
                game_id = event["pathParameters"]["game_id"]
                left = svc.leave(user, game_id)
                if left:
                    realtime().broadcast(svc, left)
                else:
                    realtime().broadcast_closed(game_id)
                return _json(200, {"ok": True})
            case "POST /api/ws-ticket":
                return _json(200, {"ticket": store().issue_ticket(user, name)})
        return _json(404, {"code": "NOT_FOUND", "message": "Unbekannter Pfad"})
    except ServiceError as exc:
        return _error(exc)


def gate(headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    """Platform password -> signed cookie that CloudFront checks on every request."""
    ip = headers.get("x-forwarded-for", "").split(",")[0].strip() or "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:32]
    if store().gate_attempt(ip_hash) > MAX_GATE_ATTEMPTS:
        raise ServiceError("RATE_LIMITED", "Zu viele Versuche – bitte 15 Minuten warten")
    if not verify_password(str(body.get("password", "")), secret(os.environ["GATE_HASH_PARAM"])):
        raise ServiceError("UNAUTHORIZED", "Falsches Passwort")
    store().gate_reset(ip_hash)
    return _json(200, {"ok": True}, cookies=[gate_set_cookie(sign_gate_cookie(secret(os.environ["GATE_KEY_PARAM"])))])


# ================================================================= WebSocket

def ws_connect(event: dict[str, Any], context: Any) -> dict[str, Any]:
    ticket = (event.get("queryStringParameters") or {}).get("ticket", "")
    identity = store().consume_ticket(ticket) if ticket else None
    if identity is None:
        return {"statusCode": 401}
    store().add_connection(event["requestContext"]["connectionId"], *identity)
    return {"statusCode": 200}


def ws_disconnect(event: dict[str, Any], context: Any) -> dict[str, Any]:
    store().drop_connection(event["requestContext"]["connectionId"])
    return {"statusCode": 200}


def ws_default(event: dict[str, Any], context: Any) -> dict[str, Any]:
    conn_id = event["requestContext"]["connectionId"]
    raw = event.get("body") or ""
    conn = store().connection(conn_id)
    if conn is None:
        return {"statusCode": 401}
    rt = realtime()
    if len(raw) > MAX_MESSAGE_BYTES:
        rt.send(conn_id, {"t": "error", "code": "TOO_LARGE", "message": "Nachricht zu groß"})
        return {"statusCode": 200}
    msg = json.loads(raw)
    user = str(conn["user"])
    game_id = str(msg.get("gameId", ""))
    svc = service()
    try:
        match msg.get("t"):
            case "ping":
                rt.send(conn_id, {"t": "pong"})
            case "sub":
                game = svc.game(game_id)
                store().subscribe(game.id, conn_id, user)
                rt.send(conn_id, svc.message(game, user))
            case "lobby":
                timer = msg.get("timer")
                game = svc.lobby_op(user, game_id, str(msg.get("op")), msg.get("character"),
                                    int(timer) if timer is not None else None)
                rt.broadcast(svc, game)
            case "act":
                game, events = svc.act(user, game_id, int(msg.get("v", -1)), msg.get("a") or {})
                rt.broadcast(svc, game, events)
            case _:
                raise ServiceError("BAD_MESSAGE", "Unbekannte Nachricht")
    except ServiceError as exc:
        rt.send(conn_id, {"t": "error", "code": exc.code, "message": exc.message})
        if exc.code == "STALE":
            rt.send(conn_id, svc.message(svc.game(game_id), user))
    return {"statusCode": 200}


# ============================================================ other triggers

def timeout(event: dict[str, Any], context: Any) -> None:
    result = service().timeout(str(event["gameId"]), int(event["version"]))
    if result:
        realtime().broadcast(service(), *result)


def pre_signup(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Only people who know the platform password may create an account (the Cognito API is public)."""
    request = event.get("request", {})
    password = (request.get("validationData") or {}).get("platformPassword", "")
    if not verify_password(str(password), secret(os.environ["GATE_HASH_PARAM"])):
        raise ValueError("Plattform-Passwort falsch")
    if not NAME_RE.match(event.get("userName", "")):
        raise ValueError("Name: 1–20 Zeichen, Buchstaben, Ziffern, Leerzeichen, . und -")
    event["response"]["autoConfirmUser"] = True
    return event
