"""Per-player views: everything a client may know, nothing more (hidden hands, deck order, backgrounds)."""

from typing import Any

from .ctx import Event
from .data import GameData
from .models import GameState, Pending, PlayerState

PUBLIC_PENDING_KEYS = {
    "choose_place": {"options", "roll"},
    "extort_response": {"attacker", "tool"},
    "combat": {"attacker", "defender", "tool", "owed"},
    "discard": {"count", "reason"},
    "choose_card": {"mode"},
    "beaten": {"amount", "source"},
}


def _points(state: GameState, data: GameData, p: PlayerState) -> int:
    return sum(data.cards[state.cards[c]].points for c in p.tunnel) + p.bonus_points


def _gang(state: GameState, p: PlayerState) -> str | None:
    return state.gang_of_card[p.gang] if p.gang else None


def _pending_view(state: GameState, pending: Pending, viewer: str | None) -> dict[str, Any]:
    if viewer == pending.player:
        data = dict(pending.data)
        if "options" in data and isinstance(data["options"], dict):
            data["options"] = [{"id": c, "card": state.cards[c], "owner": o} for c, o in data["options"].items()]
    else:
        data = {k: v for k, v in pending.data.items() if k in PUBLIC_PENDING_KEYS[pending.kind]}
    if pending.kind == "extort_response":
        data["weapon"] = state.cards[pending.data["weapon"]]  # the weapon is shown openly
    return {"id": pending.id, "kind": pending.kind, "player": pending.player, "data": data}


def view_for(state: GameState, viewer: str | None, data: GameData) -> dict[str, Any]:
    """viewer=None -> spectator view."""
    players = []
    for p in sorted(state.players, key=lambda x: x.seat):
        hidden_count = _gang(state, p) == "shadow" and p.id != viewer
        players.append({
            "id": p.id,
            "name": p.name,
            "seat": p.seat,
            "place": p.place,
            "hand_count": None if hidden_count else len(p.hand),
            "tunnel": [state.cards[c] for c in p.tunnel],
            "points": _points(state, data, p),
            "gang": _gang(state, p),
            "background": p.background if p.background_revealed else None,
            "beatings": p.beatings,
            "cigarettes": p.cigarettes,
            "prepared_weapon": state.cards[p.prepared_weapon] if p.prepared_weapon else None,
            "protected": p.protected,
        })
    me = None
    if viewer is not None:
        own = state.player(viewer)
        me = {
            "id": own.id,
            "hand": [{"id": c, "card": state.cards[c]} for c in own.hand],
            "background": own.background,
            "background_revealed": own.background_revealed,
            "hand_limit": own.hand_limit,
        }
    discard_top = state.cards[state.search_discard[-1]] if state.search_discard else None
    return {
        "id": state.id,
        "version": state.version,
        "phase": state.phase,
        "winner": state.winner,
        "win_points": state.win_points,
        "turn": state.turn.model_dump(),
        "players": players,
        "me": me,
        "piles": {k: len(v) for k, v in state.piles.items()},
        "gang_piles": {k: len(v) for k, v in state.gang_piles.items()},
        "search_deck": len(state.search_deck),
        "search_discard": {"count": len(state.search_discard), "top": discard_top},
        "pending": _pending_view(state, state.pending[-1], viewer) if state.pending else None,
    }


def events_for(events: list[Event], viewer: str | None) -> list[dict[str, Any]]:
    return [e.as_dict() for e in events if e.to is None or (viewer is not None and viewer in e.to)]
