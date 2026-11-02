"""Deterministic RNG (splitmix64) whose whole state is one int stored in the game state.

Same seed + same actions => same game (replays, reproducible bug reports).
"""

from collections.abc import MutableSequence, Sequence
from typing import TypeVar

T = TypeVar("T")
MASK = (1 << 64) - 1


class Rng:
    def __init__(self, state: int) -> None:
        self.state = state & MASK

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def randint(self, low: int, high: int) -> int:
        """Uniform integer in [low, high] (rejection sampling, no modulo bias)."""
        span = high - low + 1
        limit = (1 << 64) - ((1 << 64) % span)
        while True:
            value = self.next_u64()
            if value < limit:
                return low + value % span

    def choice(self, items: Sequence[T]) -> T:
        return items[self.randint(0, len(items) - 1)]

    def shuffle(self, items: MutableSequence[T]) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.randint(0, i)
            items[i], items[j] = items[j], items[i]
