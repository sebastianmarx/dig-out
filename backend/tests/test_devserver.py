"""End-to-end through the devserver: lobby via REST, game via WebSocket."""

from starlette.testclient import TestClient

from digout.devserver import app


def headers(user: str) -> dict[str, str]:
    return {"X-Dev-User": user, "X-Dev-Name": user.title()}


def test_lobby_to_running_game_over_websocket():
    client = TestClient(app)
    game = client.post("/api/games", headers=headers("anna"), json={}).json()
    assert client.post("/api/games/join", headers=headers("ben"), json={"code": game["code"]}).status_code == 200

    with client.websocket_connect("/ws?user=anna&name=Anna") as anna, \
            client.websocket_connect("/ws?user=ben&name=Ben") as ben:
        for ws in (anna, ben):
            ws.send_json({"t": "sub", "gameId": game["id"]})
            assert ws.receive_json()["t"] == "lobby"
        for ws, char in ((anna, "char.01"), (ben, "char.02")):
            ws.send_json({"t": "lobby", "gameId": game["id"], "op": "character", "character": char})
            anna.receive_json(), ben.receive_json()
            ws.send_json({"t": "lobby", "gameId": game["id"], "op": "ready"})
            anna.receive_json(), ben.receive_json()
        anna.send_json({"t": "lobby", "gameId": game["id"], "op": "start"})
        msg_a, msg_b = anna.receive_json(), ben.receive_json()
        assert msg_a["t"] == "state" and msg_a["view"]["me"]["id"] == "anna"
        # each player only sees their own hand
        assert msg_b["view"]["me"]["id"] == "ben" and len(msg_b["view"]["me"]["hand"]) == 3

        current = msg_a["view"]["turn"]["player"]
        ws = anna if current == "anna" else ben
        state = msg_a if current == "anna" else msg_b
        assert {"type": "end_turn"} in state["legal"]
        ws.send_json({"t": "act", "gameId": game["id"], "v": state["view"]["version"], "a": {"type": "end_turn"}})
        after = anna.receive_json()
        ben.receive_json()
        assert after["view"]["turn"]["player"] != current
        # stale version is rejected and answered with the fresh state
        ws.send_json({"t": "act", "gameId": game["id"], "v": 0, "a": {"type": "end_turn"}})
        assert ws.receive_json()["code"] == "STALE"
        assert ws.receive_json()["t"] == "state"


def test_requires_identity():
    assert TestClient(app).get("/api/games").status_code == 401
