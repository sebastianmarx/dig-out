"""Effects of action cards, the phone and own-turn backgrounds (game-data `effect` ids)."""

from collections.abc import Callable
from typing import Any

from . import actions as A
from .ctx import Ctx, require
from .models import PlayerState

SHADOW_PEEK = 3  # spying on a shadow gang member only shows this many random cards


def _target(ctx: Ctx, p: PlayerState, target_id: str | None, same_place: bool = False) -> PlayerState:
    require(target_id is not None, "choose a target player")
    assert target_id is not None
    target = ctx.player(target_id)
    require(target.id != p.id, "choose another player")
    require(not same_place or target.place == p.place, "target must be at your place")
    return target


def _visible_hand(ctx: Ctx, target: PlayerState) -> list[str]:
    """What a spy gets to see of a hand (shadow gang: only a few random cards)."""
    if ctx.has_ability(target, "hidden_hand"):
        return ctx.sample(target.hand, SHADOW_PEEK)
    return list(target.hand)


def _show_hand(ctx: Ctx, viewer: PlayerState, target: PlayerState, cards: list[str]) -> None:
    ctx.emit("hand_seen", player=viewer.id, target=target.id)
    ctx.emit("hand_revealed", to=[viewer.id], player=viewer.id, target=target.id,
             cards={c: ctx.def_id(c) for c in cards})


# =============================================================== card effects

def extra_actions(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    ctx.s.turn.actions_left += amount


def move_anywhere(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    require(a.place is not None and a.place != p.place, "choose another place")
    assert a.place is not None
    ctx.move(p, a.place)


def draw(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    ctx.draw(p, amount)


def raid(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    victims = [o for o in ctx.at_place(p) if o.hand]
    for victim in reversed(victims):  # stack: the first victim decides first
        ctx.push_pending("discard", victim, count=1, reason="raid")


def buy_pickaxe(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    require(p.cigarettes >= amount, "not enough cigarettes")
    require(ctx.s.piles["pickaxe"], "no pickaxes left")
    p.cigarettes -= amount
    ctx.take_from_pile(p, "pickaxe")


def heal(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    require(p.beatings > 0, "nothing to heal")
    p.beatings = max(0, p.beatings - amount)
    ctx.emit("healed", player=p.id, beatings=p.beatings)


def snitch(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    target = _target(ctx, p, a.target)
    seen = _visible_hand(ctx, target)
    _show_hand(ctx, p, target, seen)
    options = {c: target.id for c in seen if ctx.card(c).kind not in ("weapon", "tool")}
    if options:
        ctx.push_pending("choose_card", p, mode="snitch", options=options)


def cave_in(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    target = _target(ctx, p, a.target)
    spoons = [c for c in target.tunnel if ctx.def_id(c) == "spoon"]
    require(spoons, "that tunnel has no spoon")
    target.tunnel.remove(spoons[-1])
    ctx.discard(spoons[-1])
    ctx.emit("tunnel_collapsed", player=p.id, target=target.id, points=ctx.points(target))


def phone_swap(ctx: Ctx, p: PlayerState, a: A.PlayCard, amount: int) -> None:
    target = _target(ctx, p, a.target)
    require(target.hand, "that player has no cards")
    require(any(c != a.card for c in p.hand), "you have nothing to swap")
    seen = _visible_hand(ctx, target)
    _show_hand(ctx, p, target, seen)
    ctx.push_pending("choose_card", p, mode="phone", phone=a.card, options={c: target.id for c in seen})


CARD_EFFECTS: dict[str, Callable[[Ctx, PlayerState, Any, int], None]] = {
    "extra_actions": extra_actions,
    "move_anywhere": move_anywhere,
    "draw": draw,
    "raid": raid,
    "buy_pickaxe": buy_pickaxe,
    "heal": heal,
    "snitch": snitch,
    "cave_in": cave_in,
    "phone_swap": phone_swap,
}


# ========================================================= background effects

def pickpocket(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    if ctx.gang_bonus(p):
        victims = ctx.at_place(p)
        steals = [(v, 1) for v in victims]
    else:
        steals = [(_target(ctx, p, a.target, same_place=True), amount)]
    for victim, count in steals:
        for _ in range(count):
            card = ctx.random_card(victim)
            if card:
                ctx.give_card(victim, p, card)


def hoard(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    ctx.draw(p, ctx.background(p).amount)
    if ctx.gang_bonus(p):
        p.hand_limit = amount


def gain_cigarettes(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    p.cigarettes += amount
    ctx.emit("cigarettes_gained", player=p.id, amount=amount)


def smuggle_shovel(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    require(ctx.s.piles["shovel"], "no shovels left")
    require(len(set(a.cards)) == len(a.cards) == amount, f"discard exactly {amount} card(s)")
    for card_id in a.cards:
        ctx.take_from_hand(p, card_id)
        ctx.discard(card_id)
    ctx.take_from_pile(p, "shovel")


def give_beating(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    target = _target(ctx, p, a.target, same_place=True)
    ctx.enqueue_front({"op": "beating", "player": target.id, "amount": amount, "source": p.id})


def collect(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    for other in ctx.others(p):
        paid = min(other.cigarettes, amount)
        other.cigarettes -= paid
        p.cigarettes += paid
        if paid:
            ctx.emit("cigarettes_paid", player=other.id, to_player=p.id, amount=paid)


def take_knives(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    ctx.take_from_pile(p, "knife", amount)


def free_move(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    require(a.place is not None and a.place != p.place, "choose another place")
    assert a.place is not None
    ctx.move(p, a.place)
    if ctx.gang_bonus(p):
        ctx.s.turn.actions_left += 1


def steal_tunnel_tool(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    tool = "pickaxe" if ctx.gang_bonus(p) else "spoon"
    target = _target(ctx, p, a.target)
    found = [c for c in target.tunnel if ctx.def_id(c) == tool]
    require(found, f"that tunnel has no {tool}")
    target.tunnel.remove(found[-1])
    p.tunnel.append(found[-1])
    ctx.emit("tunnel_tool_stolen", player=p.id, target=target.id, tool=tool, points=ctx.points(p))


def see_all_hands(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    options: dict[str, str] = {}
    for other in ctx.others(p):
        seen = _visible_hand(ctx, other)
        _show_hand(ctx, p, other, seen)
        options.update({c: other.id for c in seen})
    if ctx.gang_bonus(p) and options:
        ctx.push_pending("choose_card", p, mode="informant", options=options)


def untouchable(ctx: Ctx, p: PlayerState, a: A.RevealBackground, amount: int) -> None:
    p.protected = True
    if ctx.gang_bonus(p):
        ctx.s.turn.actions_left += 1


BACKGROUND_EFFECTS: dict[str, Callable[[Ctx, PlayerState, Any, int], None]] = {
    "pickpocket": pickpocket,
    "hoard": hoard,
    "gain_cigarettes": gain_cigarettes,
    "smuggle_shovel": smuggle_shovel,
    "give_beating": give_beating,
    "collect": collect,
    "take_knives": take_knives,
    "free_move": free_move,
    "steal_tunnel_tool": steal_tunnel_tool,
    "see_all_hands": see_all_hands,
    "untouchable": untouchable,
}
