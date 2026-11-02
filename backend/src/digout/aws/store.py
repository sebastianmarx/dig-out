"""DynamoDB storage (single table, on-demand). Keys:

    GAME#<id>      META          game record (JSON), rev, gsi1pk=LOBBY while open
    GAME#<id>      SUB#<conn>    WebSocket subscription
    CODE#<code>    META          join code -> game id
    CONN#<conn>    META          connected user (+ subscribed game)
    TICKET#<t>     META          one-time WebSocket ticket (60 s)
    RL#<ip-hash>   GATE          failed gate attempts (15 min)

Every item carries `ttl` so DynamoDB cleans up on its own.
"""

import json
import secrets
import time
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from digout.service.models import Game
from digout.service.repo import ConflictError

GAME_TTL = 30 * 24 * 3600
CONN_TTL = 3 * 3600
TICKET_TTL = 60
RATE_WINDOW = 15 * 60


def _ttl(seconds: int) -> int:
    return int(time.time()) + seconds


class DynamoGameRepository:
    def __init__(self, table_name: str) -> None:
        self.table = boto3.resource("dynamodb").Table(table_name)

    def get(self, game_id: str) -> Game | None:
        item = self.table.get_item(Key={"PK": f"GAME#{game_id}", "SK": "META"}, ConsistentRead=True).get("Item")
        if not item:
            return None
        game = Game.model_validate_json(str(item["data"]))
        game.rev = int(item["rev"])
        return game

    def by_code(self, code: str) -> Game | None:
        item = self.table.get_item(Key={"PK": f"CODE#{code.upper()}", "SK": "META"}).get("Item")
        return self.get(str(item["game_id"])) if item else None

    def open_games(self) -> list[Game]:
        result = self.table.query(IndexName="gsi1", KeyConditionExpression=Key("gsi1pk").eq("LOBBY"),
                                  ScanIndexForward=False, Limit=30)
        games = [Game.model_validate_json(str(item["data"])) for item in result.get("Items", [])]
        return [g for g in games if g.status == "lobby"]

    def put(self, game: Game) -> None:
        new_rev = game.rev + 1
        item: dict[str, Any] = {
            "PK": f"GAME#{game.id}",
            "SK": "META",
            "data": game.model_copy(update={"rev": new_rev}).model_dump_json(),
            "rev": new_rev,
            "ttl": _ttl(GAME_TTL),
        }
        if game.status == "lobby":
            item |= {"gsi1pk": "LOBBY", "gsi1sk": f"{game.created_at:017.3f}"}
        condition = "attribute_not_exists(PK)" if game.rev == 0 else "rev = :rev"
        values = {} if game.rev == 0 else {":rev": game.rev}
        try:
            self.table.put_item(Item=item, ConditionExpression=condition,
                                **({"ExpressionAttributeValues": values} if values else {}))
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ConflictError(game.id) from exc
            raise
        if game.rev == 0:
            self.table.put_item(Item={"PK": f"CODE#{game.code}", "SK": "META", "game_id": game.id,
                                      "ttl": _ttl(GAME_TTL)})
        game.rev = new_rev

    def delete(self, game_id: str) -> None:
        game = self.get(game_id)
        self.table.delete_item(Key={"PK": f"GAME#{game_id}", "SK": "META"})
        if game:
            self.table.delete_item(Key={"PK": f"CODE#{game.code}", "SK": "META"})


class ConnectionStore:
    def __init__(self, table_name: str) -> None:
        self.table = boto3.resource("dynamodb").Table(table_name)

    # One-time tickets: the WebSocket URL never carries the JWT.
    def issue_ticket(self, user_id: str, name: str) -> str:
        ticket = secrets.token_urlsafe(32)
        self.table.put_item(Item={"PK": f"TICKET#{ticket}", "SK": "META", "user": user_id, "name": name,
                                  "ttl": _ttl(TICKET_TTL)})
        return ticket

    def consume_ticket(self, ticket: str) -> tuple[str, str] | None:
        old = self.table.delete_item(Key={"PK": f"TICKET#{ticket}", "SK": "META"}, ReturnValues="ALL_OLD")
        item = old.get("Attributes")
        if not item or int(item["ttl"]) < time.time():
            return None
        return str(item["user"]), str(item["name"])

    def add_connection(self, conn_id: str, user_id: str, name: str) -> None:
        self.table.put_item(Item={"PK": f"CONN#{conn_id}", "SK": "META", "user": user_id, "name": name,
                                  "ttl": _ttl(CONN_TTL)})

    def connection(self, conn_id: str) -> dict[str, Any] | None:
        item = self.table.get_item(Key={"PK": f"CONN#{conn_id}", "SK": "META"}).get("Item")
        return dict(item) if item else None

    def subscribe(self, game_id: str, conn_id: str, user_id: str) -> None:
        conn = self.connection(conn_id)
        if conn and conn.get("game") and conn["game"] != game_id:
            self.table.delete_item(Key={"PK": f"GAME#{conn['game']}", "SK": f"SUB#{conn_id}"})
        self.table.put_item(Item={"PK": f"GAME#{game_id}", "SK": f"SUB#{conn_id}", "user": user_id,
                                  "ttl": _ttl(CONN_TTL)})
        self.table.update_item(Key={"PK": f"CONN#{conn_id}", "SK": "META"}, UpdateExpression="SET game = :g",
                               ExpressionAttributeValues={":g": game_id})

    def subscribers(self, game_id: str) -> list[tuple[str, str]]:
        condition = Key("PK").eq(f"GAME#{game_id}") & Key("SK").begins_with("SUB#")
        result = self.table.query(KeyConditionExpression=condition)
        return [(str(i["SK"])[4:], str(i["user"])) for i in result.get("Items", [])]

    def drop_connection(self, conn_id: str) -> None:
        old = self.table.delete_item(Key={"PK": f"CONN#{conn_id}", "SK": "META"}, ReturnValues="ALL_OLD")
        game = old.get("Attributes", {}).get("game")
        if game:
            self.table.delete_item(Key={"PK": f"GAME#{game}", "SK": f"SUB#{conn_id}"})

    def drop_subscription(self, game_id: str, conn_id: str) -> None:
        self.table.delete_item(Key={"PK": f"GAME#{game_id}", "SK": f"SUB#{conn_id}"})

    # Brute-force protection for the platform password.
    def gate_attempt(self, ip_hash: str) -> int:
        result = self.table.update_item(
            Key={"PK": f"RL#{ip_hash}", "SK": "GATE"},
            UpdateExpression="ADD attempts :one SET #ttl = if_not_exists(#ttl, :ttl)",
            ExpressionAttributeNames={"#ttl": "ttl"},
            ExpressionAttributeValues={":one": 1, ":ttl": _ttl(RATE_WINDOW)},
            ReturnValues="UPDATED_NEW",
        )
        return int(result["Attributes"]["attempts"])

    def gate_reset(self, ip_hash: str) -> None:
        self.table.delete_item(Key={"PK": f"RL#{ip_hash}", "SK": "GATE"})


def dumps(message: dict[str, Any]) -> str:
    return json.dumps(message, separators=(",", ":"))
