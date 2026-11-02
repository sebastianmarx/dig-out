"""Rule handlers: turn actions, responses to pending decisions and deferred queue steps.

See docs/rules.md for the rules these implement.
"""

from collections.abc import Callable
from typing import Any

from . import actions as A
from .ctx import Ctx, require
from .models import Pending, PlayerState

# ================================================================ turn actions

def search(ctx: Ctx, p: PlayerState, a: A.Search) -> None:
    ctx.once_per_turn("search")
    ctx.spend(p)
    bonus = 1 if ctx.has_ability(p, "search_bonus") else 0
    ctx.draw(p, ctx.d.place(p.place).search + bonus)


def move_roll(ctx: Ctx, p: PlayerState, a: A.MoveRoll) -> None:
    ctx.spend(p)
    if a.fixed is not None:
        ctx.reveal(p, "fix_roll")
        value = a.fixed
        if ctx.gang_bonus(p):
            ctx.draw(p, 1)
    else:
        value = ctx.roll()
    ctx.emit("rolled", player=p.id, value=value, fixed=a.fixed is not None)
    resolve_roll(ctx, p, value)


def resolve_roll(ctx: Ctx, p: PlayerState, value: int) -> None:
    options = ctx.d.board.dice[value]
    if p.place in options:
        ctx.move(p, next(o for o in options if o != p.place))
    else:
        ctx.push_pending("choose_place", p, options=options, roll=value)


def move_cautious(ctx: Ctx, p: PlayerState, a: A.MoveCautious) -> None:
    require(a.place != p.place, "you are already there")
    ctx.spend(p, ctx.d.rules.cautious_move_cost)
    ctx.move(p, a.place)


def join_gang(ctx: Ctx, p: PlayerState, a: A.JoinGang) -> None:
    gang = ctx.d.gangs.get(a.gang)
    require(gang is not None, "unknown gang")
    assert gang is not None
    require(ctx.s.gang_piles[gang.id], "no membership cards left")
    require(ctx.gang(p) != gang.id, "already a member")
    require(len(set(a.cards)) == len(a.cards) == gang.requires.distinct, f"needs {gang.requires.distinct} accessories")
    allowed = set(gang.requires.from_) if gang.requires.from_ != "any" else None
    fixed: list[str] = []
    wildcards = 0
    for card_id in a.cards:
        require(card_id in p.hand, "card not in hand")
        card = ctx.card(card_id)
        require(card.kind == "accessory", "only accessories")
        if card.accessory == "any":
            wildcards += 1
        else:
            assert card.accessory is not None
            fixed.append(card.accessory)
    require(len(set(fixed)) == len(fixed), "accessories must be different")
    if allowed is not None:
        require(set(fixed) <= allowed, "wrong accessory for this gang")
        require(len(allowed - set(fixed)) >= wildcards, "not enough different accessories")
    ctx.spend(p)
    for card_id in a.cards:
        ctx.take_from_hand(p, card_id)
        ctx.discard(card_id)
    if p.gang:
        ctx.s.gang_piles[ctx.s.gang_of_card[p.gang]].insert(0, p.gang)
    p.gang = ctx.s.gang_piles[gang.id].pop()
    ctx.emit("joined_gang", player=p.id, gang=gang.id)


def play_card(ctx: Ctx, p: PlayerState, a: A.PlayCard) -> None:
    from .effects import CARD_EFFECTS

    require(a.card in p.hand, "card not in hand")
    card = ctx.card(a.card)
    require(card.kind in ("action", "gadget") and card.effect in CARD_EFFECTS, "not a playable card")
    require(not card.reaction, "this card is only played as a reaction")
    ctx.spend(p)
    ctx.emit("card_played", player=p.id, card=card.id)
    if card.kind == "action":
        ctx.take_from_hand(p, a.card)
        ctx.discard(a.card)
    assert card.effect is not None
    CARD_EFFECTS[card.effect](ctx, p, a, card.amount)


def extort(ctx: Ctx, p: PlayerState, a: A.Extort) -> None:
    target = ctx.player(a.target)
    require(target.id != p.id, "cannot extort yourself")
    require(target.place == p.place, "target must be at your place")
    require(not target.protected, "target cannot be extorted right now")
    require(a.weapon in p.hand and ctx.card(a.weapon).kind == "weapon", "you need a weapon")
    ctx.once_per_turn("extort")
    ctx.spend(p)
    ctx.emit("extortion", player=p.id, target=target.id, tool=a.tool, weapon=ctx.def_id(a.weapon))
    ctx.push_pending("extort_response", target, attacker=p.id, tool=a.tool, weapon=a.weapon)


def craft(ctx: Ctx, p: PlayerState, a: A.Craft) -> None:
    require(ctx.d.place(p.place).craft_allowed, "no crafting here")
    require(p.beatings == 0, "too beaten up to craft")
    recipe = next((r for r in ctx.d.rules.recipes if r.id == a.recipe), None)
    require(recipe is not None, "unknown recipe")
    assert recipe is not None
    require(ctx.s.piles[recipe.gives], "nothing left to craft")
    require(len(set(a.cards)) == len(a.cards), "duplicate cards")
    for card_id in a.cards:
        require(card_id in p.hand, "card not in hand")
    allowance = ctx.reveal(p, "craft_discount") if a.use_background else 0
    missing = missing_ingredients(ctx, recipe.needs, a.cards)
    require(missing <= allowance, "ingredients missing")
    ctx.once_per_turn("craft")
    ctx.spend(p)
    for card_id in a.cards:
        ctx.take_from_hand(p, card_id)
        ctx.discard(card_id)
    ctx.take_from_pile(p, recipe.gives, recipe.amount)
    ctx.emit("crafted", player=p.id, recipe=recipe.id)


def missing_ingredients(ctx: Ctx, needs: dict[str, int], cards: list[str]) -> int:
    """Units still missing after assigning the cards; raises if a card contributes nothing."""
    need = dict(needs)
    flexible: list[list[str]] = []
    for card_id in cards:
        card = ctx.card(card_id)
        if card.counts_as_any:
            flexible.append(card.counts_as_any)
            continue
        contributes = card.counts_as or ({card.material: 1} if card.material else {})
        useful = False
        for material, units in contributes.items():
            if need.get(material, 0) > 0:
                need[material] -= min(units, need[material])
                useful = True
        require(useful, f"{card.name} is not needed for this recipe")
    for options in flexible:
        chosen = next((m for m in options if need.get(m, 0) > 0), None)
        require(chosen is not None, "superfluous ingredient")
        assert chosen is not None
        need[chosen] -= 1
    return sum(need.values())


def dig(ctx: Ctx, p: PlayerState, a: A.Dig) -> None:
    require("dig" in ctx.d.place(p.place).actions, "you can only dig in the cell block")
    require(p.beatings < ctx.d.rules.max_beatings, "too beaten up to dig")
    require(len(set(a.tools)) == len(a.tools), "duplicate tools")
    for card_id in a.tools:
        require(card_id in p.hand and ctx.card(card_id).kind == "tool", "only tools can be dug in")
    max_tools, bonus = 1, 0
    if a.use_background:
        effect = ctx.background(p).effect
        require(effect in ("multi_dig", "dig_bonus"), "background does not help digging")
        amount = ctx.reveal(p, effect)
        if effect == "multi_dig":
            max_tools = amount
        else:
            bonus = amount
    require(len(a.tools) <= max_tools, f"you can dig in at most {max_tools} tool(s)")
    ctx.spend(p)
    for card_id in a.tools:
        ctx.take_from_hand(p, card_id)
        p.tunnel.append(card_id)
    p.bonus_points += bonus
    ctx.emit("dug", player=p.id, tools=[ctx.def_id(c) for c in a.tools], bonus=bonus, points=ctx.points(p))


def steal_spoon(ctx: Ctx, p: PlayerState, a: A.StealSpoon) -> None:
    require("steal_spoon" in ctx.d.place(p.place).actions, "no spoons here")
    require(ctx.s.piles["spoon"], "no spoons left")
    ctx.spend(p)
    ctx.take_from_pile(p, "spoon")


def heal(ctx: Ctx, p: PlayerState, a: A.Heal) -> None:
    require("heal" in ctx.d.place(p.place).actions, "you can only heal in the infirmary")
    require(p.beatings > 0, "nothing to heal")
    ctx.spend(p)
    p.beatings -= 1
    ctx.emit("healed", player=p.id, beatings=p.beatings)


def sell(ctx: Ctx, p: PlayerState, a: A.Sell) -> None:
    require("sell" in ctx.d.place(p.place).actions, "you can only sell in the recreation area")
    require(len(set(a.cards)) == len(a.cards), "duplicate cards")
    for card_id in a.cards:
        require(card_id in p.hand, "card not in hand")
    ctx.spend(p)
    total = 0
    for card_id in a.cards:
        total += ctx.card(card_id).value
        ctx.take_from_hand(p, card_id)
        ctx.discard(card_id)
    p.cigarettes += total
    ctx.emit("sold", player=p.id, cards=[ctx.def_id(c) for c in a.cards], cigarettes=total)


def buy_cost(ctx: Ctx, p: PlayerState, offer_id: str) -> int:
    cost = ctx.d.offer(offer_id).cost
    return max(1, cost - 1) if ctx.has_ability(p, "buy_discount") else cost


def buy(ctx: Ctx, p: PlayerState, a: A.Buy) -> None:
    require("buy" in ctx.d.place(p.place).actions, "you can only buy in the recreation area")
    offer = next((o for o in ctx.d.rules.market if o.id == a.offer), None)
    require(offer is not None, "unknown offer")
    assert offer is not None
    cost = buy_cost(ctx, p, offer.id)
    require(p.cigarettes >= cost, "not enough cigarettes")
    require(len(ctx.s.piles[offer.gives]) >= offer.amount, "sold out")
    ctx.spend(p)
    p.cigarettes -= cost
    ctx.take_from_pile(p, offer.gives, offer.amount)
    ctx.emit("bought", player=p.id, offer=offer.id, cost=cost)


def train(ctx: Ctx, p: PlayerState, a: A.Train) -> None:
    require("train" in ctx.d.place(p.place).actions, "you can only train in the yard")
    require(a.weapon in p.hand and ctx.card(a.weapon).kind == "weapon", "you need a weapon")
    require(p.prepared_weapon is None, "you already have a prepared weapon")
    ctx.spend(p)
    ctx.take_from_hand(p, a.weapon)
    p.prepared_weapon = a.weapon
    ctx.emit("trained", player=p.id, weapon=ctx.def_id(a.weapon))


def reveal_background(ctx: Ctx, p: PlayerState, a: A.RevealBackground) -> None:
    from .effects import BACKGROUND_EFFECTS

    bg = ctx.background(p)
    require(not p.background_revealed, "background already revealed")
    require(bg.timing == "own_turn", "this background is revealed at another moment")
    require(bg.place is None or bg.place == p.place, "wrong place for this background")
    amount = ctx.reveal(p, bg.effect)
    BACKGROUND_EFFECTS[bg.effect](ctx, p, a, amount)


def end_turn(ctx: Ctx, p: PlayerState, a: A.EndTurn) -> None:
    ctx.enqueue({"op": "hand_limit", "player": p.id}, {"op": "next_turn"})


TURN_HANDLERS: dict[str, Callable[[Ctx, PlayerState, Any], None]] = {
    "search": search,
    "move_roll": move_roll,
    "move_cautious": move_cautious,
    "join_gang": join_gang,
    "play_card": play_card,
    "extort": extort,
    "craft": craft,
    "dig": dig,
    "steal_spoon": steal_spoon,
    "heal": heal,
    "sell": sell,
    "buy": buy,
    "train": train,
    "reveal_background": reveal_background,
    "end_turn": end_turn,
}


# ================================================================== responses

def choose_place(ctx: Ctx, pending: Pending, p: PlayerState, a: A.ChoosePlace) -> None:
    require(a.place in pending.data["options"], "not one of the rolled places")
    ctx.pop_pending()
    ctx.move(p, a.place)


def reroll(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Reroll) -> None:
    require(ctx.has_ability(p, "reroll"), "only the triad may reroll")
    ctx.once_per_turn("reroll")
    ctx.pop_pending()
    value = ctx.roll()
    ctx.emit("rolled", player=p.id, value=value, reroll=True)
    resolve_roll(ctx, p, value)


def comply(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Comply) -> None:
    tools = ctx.tools_in_hand(p, pending.data["tool"])
    require(tools, "you do not have that tool")
    ctx.pop_pending()
    ctx.give_card(p, ctx.player(pending.data["attacker"]), tools[0], public=True)
    ctx.emit("extortion_complied", player=p.id, attacker=pending.data["attacker"])


def refuse(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Refuse) -> None:
    attacker = ctx.player(pending.data["attacker"])
    ctx.pop_pending()
    weapon = pending.data["weapon"]
    ctx.take_from_hand(attacker, weapon)
    ctx.discard(weapon)
    ctx.emit("combat_started", attacker=attacker.id, defender=p.id)
    ctx.push_pending("combat", p, attacker=attacker.id, defender=p.id, tool=pending.data["tool"], owed=1,
                     last_weapon={attacker.id: ctx.def_id(weapon)}, skip_used=False)


def react(ctx: Ctx, pending: Pending, p: PlayerState, a: A.React) -> None:
    attacker = ctx.player(pending.data["attacker"])
    if a.card is not None:
        require(a.card in p.hand and ctx.card(a.card).effect == "cancel_extortion", "not a reaction card")
        ctx.pop_pending()
        ctx.take_from_hand(p, a.card)
        ctx.discard(a.card)
        ctx.emit("extortion_cancelled", player=p.id, by="distraction")
        return
    ctx.reveal(p, "bribe_guard")
    ctx.pop_pending()
    ctx.emit("extortion_cancelled", player=p.id, by="briber")
    if ctx.gang_bonus(p):
        stolen = ctx.random_card(attacker)
        if stolen:
            ctx.give_card(attacker, p, stolen)
    ctx.enqueue_front({"op": "beating", "player": attacker.id, "amount": 1, "source": p.id})


def _opponent(pending: Pending, player_id: str) -> str:
    data = pending.data
    return str(data["defender"] if player_id == data["attacker"] else data["attacker"])


def _hand_over(pending: Pending, next_player: str, owed: int) -> None:
    pending.player = next_player
    pending.data["owed"] = owed


def play_weapon(ctx: Ctx, pending: Pending, p: PlayerState, a: A.PlayWeapon) -> None:
    if a.card == "prepared":
        require(p.prepared_weapon is not None, "no prepared weapon")
        assert p.prepared_weapon is not None
        weapon, p.prepared_weapon = p.prepared_weapon, None
    else:
        require(a.card in p.hand and ctx.card(a.card).kind == "weapon", "not a weapon in your hand")
        weapon = a.card
        ctx.take_from_hand(p, weapon)
    ctx.discard(weapon)
    pending.data["last_weapon"][p.id] = ctx.def_id(weapon)
    owed = pending.data["owed"] - 1
    ctx.emit("weapon_played", player=p.id, weapon=ctx.def_id(weapon), owed=owed)
    if owed > 0:
        pending.data["owed"] = owed
    else:
        _hand_over(pending, _opponent(pending, p.id), 1)


def skip(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Skip) -> None:
    require(p.id == pending.data["defender"] and ctx.has_ability(p, "defender_skip"), "you cannot skip")
    require(not pending.data["skip_used"], "already skipped in this combat")
    pending.data["skip_used"] = True
    ctx.emit("combat_skipped", player=p.id)
    _hand_over(pending, _opponent(pending, p.id), 1)


def brawl(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Brawl) -> None:
    amount = ctx.reveal(p, "brawl")
    pending.data["last_weapon"][p.id] = None
    ctx.emit("brawl", player=p.id, owed=amount)
    _hand_over(pending, _opponent(pending, p.id), amount)


def yield_(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Yield) -> None:
    winner = _opponent(pending, p.id)
    data = pending.data
    ctx.pop_pending()
    last = data["last_weapon"].get(winner)
    beatings = 1 + (ctx.d.cards[last].extra_beatings if last else 0)
    ctx.emit("combat_won", player=winner, loser=p.id)
    ctx.enqueue_front(
        {"op": "beating", "player": p.id, "amount": beatings, "source": winner},
        {"op": "combat_reward", "winner": winner, "loser": p.id, "tool": data["tool"],
         "defender": data["defender"]},
    )


def discard(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Discard) -> None:
    count = pending.data["count"]
    require(len(a.cards) == min(count, len(p.hand)) and len(set(a.cards)) == len(a.cards),
            f"discard exactly {count} card(s)")
    ctx.pop_pending()
    for card_id in a.cards:
        ctx.take_from_hand(p, card_id)
        ctx.discard(card_id)
    ctx.emit("discarded", player=p.id, cards=[ctx.def_id(c) for c in a.cards], reason=pending.data["reason"])


def pick_card(ctx: Ctx, pending: Pending, p: PlayerState, a: A.PickCard) -> None:
    options: dict[str, str] = pending.data["options"]  # card id -> owner id
    require(a.card in options, "not one of the offered cards")
    owner = ctx.player(options[a.card])
    if pending.data["mode"] == "phone":
        require(a.give is not None and a.give in p.hand and a.give != pending.data["phone"],
                "choose one of your cards to give")
        assert a.give is not None
        ctx.pop_pending()
        ctx.give_card(p, owner, a.give)
    else:
        ctx.pop_pending()
    ctx.give_card(owner, p, a.card)


def take_beating(ctx: Ctx, pending: Pending, p: PlayerState, a: A.TakeBeating) -> None:
    ctx.pop_pending()
    apply_beatings(ctx, p, pending.data["amount"])


def shrug(ctx: Ctx, pending: Pending, p: PlayerState, a: A.Shrug) -> None:
    ctx.reveal(p, "ignore_beating")
    ctx.pop_pending()
    if ctx.gang_bonus(p) and p.beatings > 0:
        p.beatings -= 1
    ctx.emit("beating_ignored", player=p.id, beatings=p.beatings)


RESPONSE_HANDLERS: dict[str, Callable[[Ctx, Pending, PlayerState, Any], None]] = {
    "choose_place": choose_place,
    "reroll": reroll,
    "comply": comply,
    "refuse": refuse,
    "react": react,
    "play_weapon": play_weapon,
    "skip": skip,
    "brawl": brawl,
    "yield": yield_,
    "discard": discard,
    "pick_card": pick_card,
    "take_beating": take_beating,
    "shrug": shrug,
}


# ================================================================ queue steps

def apply_beatings(ctx: Ctx, p: PlayerState, amount: int) -> None:
    p.beatings = min(ctx.d.rules.max_beatings, p.beatings + amount)
    ctx.emit("beaten", player=p.id, amount=amount, beatings=p.beatings)


def step_beating(ctx: Ctx, step: dict[str, Any]) -> None:
    p = ctx.player(step["player"])
    if not p.background_revealed:
        # Always a window while the background is hidden, so it reveals nothing about the card.
        ctx.push_pending("beaten", p, amount=step["amount"], source=step["source"])
    else:
        apply_beatings(ctx, p, step["amount"])


def step_combat_reward(ctx: Ctx, step: dict[str, Any]) -> None:
    winner, loser = ctx.player(step["winner"]), ctx.player(step["loser"])
    tools = ctx.tools_in_hand(loser, step["tool"]) if loser.id == step["defender"] else []
    if tools:
        ctx.give_card(loser, winner, tools[0], public=True)
    else:
        card = ctx.random_card(loser)
        if card:
            ctx.give_card(loser, winner, card)
    if ctx.has_ability(winner, "winner_cigarettes") and loser.beatings:
        winner.cigarettes += loser.beatings
        ctx.emit("cigarettes_gained", player=winner.id, amount=loser.beatings)


def step_hand_limit(ctx: Ctx, step: dict[str, Any]) -> None:
    p = ctx.player(step["player"])
    excess = len(p.hand) - p.hand_limit
    if excess > 0:
        ctx.push_pending("discard", p, count=excess, reason="hand_limit")


def step_next_turn(ctx: Ctx, step: dict[str, Any]) -> None:
    players = sorted(ctx.s.players, key=lambda p: p.seat)
    index = next(i for i, p in enumerate(players) if p.id == ctx.s.turn.player)
    nxt = players[(index + 1) % len(players)]
    nxt.protected = False  # phantom protection lasts until the owner's next turn
    ctx.s.turn.player = nxt.id
    ctx.s.turn.number += 1
    ctx.s.turn.actions_left = ctx.d.rules.actions_per_turn
    ctx.s.turn.used = []
    ctx.emit("turn_started", player=nxt.id, number=ctx.s.turn.number)


STEP_HANDLERS: dict[str, Callable[[Ctx, dict[str, Any]], None]] = {
    "beating": step_beating,
    "combat_reward": step_combat_reward,
    "hand_limit": step_hand_limit,
    "next_turn": step_next_turn,
}


def run_queue(ctx: Ctx) -> None:
    while ctx.s.phase == "running" and not ctx.s.pending and ctx.s.queue:
        step = ctx.s.queue.pop(0)
        STEP_HANDLERS[step["op"]](ctx, step)
        ctx.check_win()

