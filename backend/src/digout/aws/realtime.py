"""Push messages to WebSocket connections and schedule decision timeouts (EventBridge Scheduler)."""

import datetime
import json
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

from digout.engine.ctx import Event
from digout.service.models import Game
from digout.service.service import GameService

from .store import ConnectionStore, dumps


class Realtime:
    def __init__(self, store: ConnectionStore) -> None:
        self.store = store
        self.api = boto3.client("apigatewaymanagementapi", endpoint_url=os.environ["WS_MANAGEMENT_ENDPOINT"])
        self.scheduler = boto3.client("scheduler")

    def send(self, conn_id: str, message: dict[str, Any]) -> bool:
        try:
            self.api.post_to_connection(ConnectionId=conn_id, Data=dumps(message).encode())
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "GoneException":
                self.store.drop_connection(conn_id)
                return False
            raise

    def broadcast(self, service: GameService, game: Game, events: list[Event] | None = None) -> None:
        for conn_id, user_id in self.store.subscribers(game.id):
            self.send(conn_id, service.message(game, user_id, events))
        self.schedule_timeout(game)

    def broadcast_closed(self, game_id: str) -> None:
        for conn_id, _ in self.store.subscribers(game_id):
            self.send(conn_id, {"t": "closed", "gameId": game_id})
            self.store.drop_subscription(game_id, conn_id)

    def schedule_timeout(self, game: Game) -> None:
        """One-off schedule per decision; a stale one finds a newer version and does nothing."""
        if game.status != "running" or game.deadline is None or game.state is None:
            return
        at = datetime.datetime.fromtimestamp(game.deadline, datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S")
        try:
            self.scheduler.create_schedule(
                Name=f"digout-{game.id}-{game.state.version}",
                GroupName=os.environ["SCHEDULE_GROUP"],
                ScheduleExpression=f"at({at})",
                ScheduleExpressionTimezone="UTC",
                FlexibleTimeWindow={"Mode": "OFF"},
                ActionAfterCompletion="DELETE",
                Target={
                    "Arn": os.environ["TIMEOUT_FUNCTION_ARN"],
                    "RoleArn": os.environ["SCHEDULER_ROLE_ARN"],
                    "Input": json.dumps({"gameId": game.id, "version": game.state.version}),
                },
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConflictException":
                raise
