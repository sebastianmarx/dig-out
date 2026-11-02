"""AWS adapters against moto (local DynamoDB/SSM mocks): storage, locking, gate, handlers."""

import json
import os

import boto3
import pytest
from moto import mock_aws

from digout.aws import handlers
from digout.aws.security import hash_password, sign_gate_cookie, verify_gate_cookie, verify_password
from digout.service.repo import ConflictError

TABLE = "digout-test"


def test_password_hash_roundtrip():
    encoded = hash_password("geheim-123")
    assert verify_password("geheim-123", encoded)
    assert not verify_password("falsch", encoded)
    assert not verify_password("geheim-123", "kaputt")


def test_gate_cookie_signature_and_expiry():
    value = sign_gate_cookie("key", now=1000)
    assert verify_gate_cookie("key", value, now=2000)
    assert not verify_gate_cookie("other", value, now=2000)
    assert not verify_gate_cookie("key", value, now=1000 + 31 * 24 * 3600)


@pytest.fixture
def aws(monkeypatch):
    with mock_aws():
        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-central-1")
        dynamo = boto3.client("dynamodb")
        dynamo.create_table(
            TableName=TABLE,
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": n, "AttributeType": "S"} for n in ("PK", "SK", "gsi1pk", "gsi1sk")
            ],
            KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
            GlobalSecondaryIndexes=[{
                "IndexName": "gsi1",
                "KeySchema": [
                    {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                    {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }],
        )
        ssm = boto3.client("ssm")
        ssm.put_parameter(Name="/digout/test/gate-hash", Value=hash_password("plattform"), Type="SecureString")
        ssm.put_parameter(Name="/digout/test/gate-key", Value="hmac-key", Type="SecureString")
        for name, value in {
            "TABLE_NAME": TABLE,
            "ORIGIN_VERIFY": "origin-secret",
            "GATE_HASH_PARAM": "/digout/test/gate-hash",
            "GATE_KEY_PARAM": "/digout/test/gate-key",
            "WS_MANAGEMENT_ENDPOINT": "https://example.execute-api.eu-central-1.amazonaws.com/prod",
            "SCHEDULE_GROUP": "digout",
            "TIMEOUT_FUNCTION_ARN": "arn:aws:lambda:eu-central-1:123456789012:function:t",
            "SCHEDULER_ROLE_ARN": "arn:aws:iam::123456789012:role/s",
        }.items():
            monkeypatch.setenv(name, value)
        for fn in (handlers.service, handlers.store, handlers.realtime, handlers.secret):
            fn.cache_clear()
        sent: list[tuple[str, dict]] = []
        monkeypatch.setattr("digout.aws.realtime.Realtime.send",
                            lambda self, conn, msg: sent.append((conn, msg)) or True)
        yield sent


def http(route, user=None, body=None, path=None, origin="origin-secret", headers=None):
    event = {
        "routeKey": route,
        "headers": {"x-origin-verify": origin, **(headers or {})},
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": path or {},
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": user, "username": (user or "").title()}}}},
    }
    response = handlers.http(event, None)
    return response["statusCode"], json.loads(response["body"]), response


def test_repository_detects_concurrent_writes(aws):
    svc = handlers.service()
    game = svc.create_game("anna", "Anna")
    first, second = svc.repo.get(game.id), svc.repo.get(game.id)
    first.seats[0].ready = True
    svc.repo.put(first)
    with pytest.raises(ConflictError):
        svc.repo.put(second)
    assert svc.repo.by_code(game.code).id == game.id
    assert [g.id for g in svc.repo.open_games()] == [game.id]


def test_http_requires_cloudfront_origin_header(aws):
    status, body, _ = http("GET /api/games", user="anna", origin="wrong")
    assert status == 403


def test_gate_sets_cookie_and_rate_limits(aws):
    status, _, response = http("POST /api/gate", body={"password": "plattform"}, headers={"x-forwarded-for": "1.2.3.4"})
    assert status == 200 and response["cookies"][0].startswith("__Host-gate=")
    for _ in range(5):
        http("POST /api/gate", body={"password": "nope"}, headers={"x-forwarded-for": "5.6.7.8"})
    status, body, _ = http("POST /api/gate", body={"password": "plattform"}, headers={"x-forwarded-for": "5.6.7.8"})
    assert status == 429


def test_full_flow_through_lambda_handlers(aws):
    sent = aws
    _, game, _ = http("POST /api/games", user="anna", body={})
    http("POST /api/games/join", user="ben", body={"code": game["code"]})
    tickets = {u: http("POST /api/ws-ticket", user=u)[1]["ticket"] for u in ("anna", "ben")}
    for i, user in enumerate(("anna", "ben")):
        assert handlers.ws_connect({"queryStringParameters": {"ticket": tickets[user]},
                                    "requestContext": {"connectionId": f"c{i}"}}, None)["statusCode"] == 200
    # tickets are single use
    assert handlers.ws_connect({"queryStringParameters": {"ticket": tickets["anna"]},
                                "requestContext": {"connectionId": "x"}}, None)["statusCode"] == 401

    def ws(conn, msg):
        handlers.ws_default({"requestContext": {"connectionId": conn}, "body": json.dumps(msg)}, None)

    for conn, char in (("c0", "char.01"), ("c1", "char.02")):
        ws(conn, {"t": "sub", "gameId": game["id"]})
        ws(conn, {"t": "lobby", "gameId": game["id"], "op": "character", "character": char})
        ws(conn, {"t": "lobby", "gameId": game["id"], "op": "ready"})
    ws("c0", {"t": "lobby", "gameId": game["id"], "op": "start"})
    states = {conn: msg for conn, msg in sent if msg["t"] == "state"}
    assert states["c0"]["view"]["me"]["id"] == "anna" and states["c1"]["view"]["me"]["id"] == "ben"
    assert states["c0"]["deadline"] is None  # no time limit by default

    actor = states["c0"]["view"]["turn"]["player"]
    conn = "c0" if actor == "anna" else "c1"
    ws(conn, {"t": "act", "gameId": game["id"], "v": states[conn]["view"]["version"], "a": {"type": "end_turn"}})
    assert sent[-1][1]["view"]["turn"]["player"] != actor


def test_pre_signup_checks_platform_password(aws):
    event = {"userName": "Anna", "request": {"validationData": {"platformPassword": "plattform"}}, "response": {}}
    assert handlers.pre_signup(event, None)["response"]["autoConfirmUser"] is True
    with pytest.raises(ValueError):
        handlers.pre_signup({"userName": "Anna", "request": {"validationData": {}}, "response": {}}, None)


def test_environment_is_clean():
    assert "TABLE_NAME" not in os.environ or os.environ["TABLE_NAME"] != TABLE
