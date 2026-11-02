"""Self-play simulation for fuzzing and balancing.

    uv run python -m digout.sim.run_sim --games 200 --players 4 --bot heuristic
"""

import argparse
import random
import statistics
import time
from collections import Counter
from dataclasses import dataclass, field

from digout.engine import GameData, apply, load_game_data, start_game

from .bots import Bot, heuristic_bot, random_bot

BOTS: dict[str, Bot] = {"random": random_bot, "heuristic": heuristic_bot}


@dataclass
class GameResult:
    winner: str | None
    winner_seat: int | None
    turns: int
    steps: int
    action_counts: Counter[str] = field(default_factory=Counter)
    backgrounds_revealed: Counter[str] = field(default_factory=Counter)
    winner_background: str | None = None
    winner_gang: str | None = None


def play_game(seed: int, players: int, bot: Bot, data: GameData, max_turns: int = 400) -> GameResult:
    rnd = random.Random(seed)
    state = start_game(f"sim-{seed}", [(f"p{i}", f"Bot {i}") for i in range(players)], seed=seed, data=data)
    counts: Counter[str] = Counter()
    steps = 0
    while state.phase == "running" and state.turn.number <= max_turns:
        actor = state.actor()
        action = bot(state, actor, data, rnd)
        state, _ = apply(state, actor, action, data)
        counts[action.type] += 1
        steps += 1
    winner = state.player(state.winner) if state.winner else None
    return GameResult(
        winner=state.winner,
        winner_seat=winner.seat if winner else None,
        turns=state.turn.number,
        steps=steps,
        action_counts=counts,
        backgrounds_revealed=Counter(p.background for p in state.players if p.background_revealed),
        winner_background=winner.background if winner else None,
        winner_gang=state.gang_of_card[winner.gang] if winner and winner.gang else None,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--players", type=int, default=4)
    parser.add_argument("--bot", choices=sorted(BOTS), default="heuristic")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    data = load_game_data()
    started = time.perf_counter()
    results = [play_game(args.seed + i, args.players, BOTS[args.bot], data) for i in range(args.games)]
    elapsed = time.perf_counter() - started

    finished = [r for r in results if r.winner]
    rounds = [r.turns / args.players for r in finished]
    print(f"{args.games} games, {args.players} players, bot={args.bot}, {elapsed:.1f}s "
          f"({elapsed / args.games:.2f}s/game)")
    print(f"finished: {len(finished)}/{args.games}")
    if rounds:
        print(f"rounds per game: median {statistics.median(rounds):.1f}, min {min(rounds):.1f}, max {max(rounds):.1f}")
    print("wins by seat:", dict(sorted(Counter(r.winner_seat for r in finished).items())))
    print("winner gang:", dict(Counter(r.winner_gang for r in finished).most_common()))
    print("winner background:", dict(Counter(r.winner_background for r in finished).most_common(6)))
    total = sum((r.action_counts for r in results), Counter())
    print("actions:", dict(total.most_common()))


if __name__ == "__main__":
    main()
