"""Enumerates legal actions: drives UI buttons, bots and fuzz tests.

Actions with free card choices (sell, craft, join gang, discard) are represented by a few
sensible concrete choices; `apply` itself validates any choice a client sends.
Every candidate is checked by a dry run, so everything returned is guaranteed to be legal.
"""

from collections.abc import Iterator

from . import actions as A
from .ctx import Ctx, IllegalAction
from .data import TOOLS, GameData
from .models import GameState, PlayerState


def _accessory_sets(ctx: Ctx, p: PlayerState, allowed: set[str] | None, distinct: int) -> list[str] | None:
    picked: list[str] = []
    types: set[str] = set()
    for card_id in p.hand:
        card = ctx.card(card_id)
        if card.kind != "accessory" or card.accessory == "any":
            continue
        assert card.accessory is not None
        if card.accessory not in types and (allowed is None or card.accessory in allowed):
            types.add(card.accessory)
            picked.append(card_id)
    picked += [c for c in p.hand if ctx.card(c).accessory == "any"]
    return picked[:distinct] if len(picked) >= distinct else None


def _craft_sets(ctx: Ctx, p: PlayerState, needs: dict[str, int]) -> Iterator[list[str]]:
    chosen: list[str] = []
    for material, count in needs.items():
        for card_id in p.hand:
            card = ctx.card(card_id)
            if count <= 0:
                break
            if card_id in chosen:
                continue
            gives = card.counts_as.get(material, 0) or (1 if card.material == material else 0)
            if gives or material in card.counts_as_any:
                chosen.append(card_id)
                count -= gives or 1
    yield chosen
    if len(chosen) > 1:
        yield chosen[:-1]  # one short: valid with the mechanic background


def _turn_candidates(ctx: Ctx, p: PlayerState) -> Iterator[A.Action]:
    yield A.EndTurn()
    others = ctx.others(p)
    here = ctx.at_place(p)
    places = [pl for pl in ctx.d.place_ids if pl != p.place]
    yield A.Search()
    yield A.MoveRoll()
    if ctx.can_reveal(p, "fix_roll"):
        yield from (A.MoveRoll(fixed=f) for f in range(1, 7))
    yield from (A.MoveCautious(place=pl) for pl in places)
    for gang in ctx.d.gangs.values():
        allowed = set(gang.requires.from_) if gang.requires.from_ != "any" else None
        cards = _accessory_sets(ctx, p, allowed, gang.requires.distinct)
        if cards:
            yield A.JoinGang(gang=gang.id, cards=cards)
    for card_id in dict.fromkeys(p.hand):
        effect = ctx.card(card_id).effect
        if effect in ("snitch", "cave_in", "phone_swap"):
            yield from (A.PlayCard(card=card_id, target=o.id) for o in others)
        elif effect == "move_anywhere":
            yield from (A.PlayCard(card=card_id, place=pl) for pl in places)
        elif effect:
            yield A.PlayCard(card=card_id)
    weapons = [c for c in p.hand if ctx.card(c).kind == "weapon"]
    if weapons:
        for target in here:
            yield from (A.Extort(target=target.id, tool=t, weapon=weapons[0]) for t in TOOLS)
        yield A.Train(weapon=weapons[0])
    for recipe in ctx.d.rules.recipes:
        for cards in _craft_sets(ctx, p, recipe.needs):
            yield A.Craft(recipe=recipe.id, cards=cards)
            yield A.Craft(recipe=recipe.id, cards=cards, use_background=True)
    tools = [c for c in p.hand if ctx.card(c).kind == "tool"]
    best_first = sorted(tools, key=lambda c: -ctx.card(c).points)
    for tool in best_first:
        yield A.Dig(tools=[tool])
        yield A.Dig(tools=[tool], use_background=True)
    if len(best_first) > 1:
        yield A.Dig(tools=best_first[:3], use_background=True)
        yield A.Dig(tools=best_first[:2], use_background=True)
    yield A.StealSpoon()
    yield A.Heal()
    if p.hand:
        yield A.Sell(cards=list(p.hand))
        yield from (A.Sell(cards=[c]) for c in p.hand)
    yield from (A.Buy(offer=o.id) for o in ctx.d.rules.market)
    if not p.background_revealed:
        yield A.RevealBackground()
        yield from (A.RevealBackground(target=o.id) for o in others)
        yield from (A.RevealBackground(place=pl) for pl in places)
        amount = ctx.bg_amount(p)
        if ctx.background(p).effect == "smuggle_shovel" and 0 < amount <= len(p.hand):
            yield A.RevealBackground(cards=p.hand[:amount])


def _response_candidates(ctx: Ctx, p: PlayerState) -> Iterator[A.Action]:
    pending = ctx.s.pending[-1]
    data = pending.data
    match pending.kind:
        case "choose_place":
            yield from (A.ChoosePlace(place=o) for o in data["options"])
            yield A.Reroll()
        case "extort_response":
            yield A.Refuse()
            yield A.Comply()
            yield A.React()
            yield from (A.React(card=c) for c in p.hand if ctx.card(c).effect == "cancel_extortion")
        case "combat":
            yield A.Yield()
            yield from (A.PlayWeapon(card=c) for c in p.hand if ctx.card(c).kind == "weapon")
            yield A.PlayWeapon(card="prepared")
            yield A.Skip()
            yield A.Brawl()
        case "discard":
            count = min(data["count"], len(p.hand))
            yield A.Discard(cards=p.hand[-count:] if count else [])
            yield A.Discard(cards=p.hand[:count])
        case "choose_card":
            give = next((c for c in p.hand if c != data.get("phone")), None)
            yield from (A.PickCard(card=c, give=give if data["mode"] == "phone" else None) for c in data["options"])
        case "beaten":
            yield A.TakeBeating()
            yield A.Shrug()


def legal_actions(state: GameState, player_id: str, data: GameData) -> list[A.Action]:
    from .engine import apply

    if state.phase != "running" or state.actor() != player_id:
        return []
    ctx = Ctx(state, data)
    p = state.player(player_id)
    candidates = _response_candidates(ctx, p) if state.pending else _turn_candidates(ctx, p)
    legal: list[A.Action] = []
    seen: set[str] = set()
    for action in candidates:
        key = action.model_dump_json()
        if key in seen:
            continue
        seen.add(key)
        try:
            apply(state, player_id, action, data)
        except IllegalAction:
            continue
        legal.append(action)
    return legal
