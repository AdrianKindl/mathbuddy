"""Task generation and answer checking (MB R1-R3)."""

import random
import re
from dataclasses import dataclass

OPERATIONS = ("Addition", "Subtraction", "Multiplication", "Division")
RANDOM = "Random"
TEST_TYPES = (*OPERATIONS, RANDOM)
LEVELS = ("Easy", "Medium", "Hard", "Pro")

# MB R1, all bounds inclusive.
# Addition, Subtraction, Multiplication: (a range, b range).
# Division: (divisor b range, result q range).
_RANGES = {
    "Addition": {
        "Easy": ((1, 19), (1, 19)),
        "Medium": ((20, 249), (20, 249)),
        "Hard": ((250, 1249), (250, 1249)),
        "Pro": ((1250, 5000), (1250, 5000)),
    },
    "Subtraction": {
        "Easy": ((1, 19), (1, 19)),
        "Medium": ((10, 99), (10, 99)),
        "Hard": ((100, 999), (100, 999)),
        "Pro": ((1000, 9999), (1000, 9999)),
    },
    "Multiplication": {
        "Easy": ((2, 9), (2, 9)),
        "Medium": ((11, 28), (2, 9)),
        "Hard": ((11, 19), (11, 19)),
        "Pro": ((20, 48), (11, 17)),
    },
    "Division": {
        "Easy": ((2, 9), (2, 9)),
        "Medium": ((2, 9), (11, 29)),
        "Hard": ((29, 99), (11, 29)),
        "Pro": ((101, 291), (11, 28)),
    },
}

_SYMBOLS = {"Addition": "+", "Subtraction": "−", "Multiplication": "×", "Division": "÷"}
_WHOLE_NUMBER = re.compile(r"[+-]?[0-9]+")


@dataclass(frozen=True)
class Task:
    operation: str
    a: int
    b: int

    @property
    def answer(self) -> int:
        if self.operation == "Addition":
            return self.a + self.b
        if self.operation == "Subtraction":
            return self.a - self.b
        if self.operation == "Multiplication":
            return self.a * self.b
        return self.a // self.b

    @property
    def text(self) -> str:
        return f"{self.a:,} {_SYMBOLS[self.operation]} {self.b:,}"


def generate_task(
    test_type: str, level: str, rng: random.Random, previous: Task | None = None
) -> Task:
    """Return a new task that follows MB R1 and differs from `previous` (MB R2)."""
    if test_type not in TEST_TYPES or level not in LEVELS:
        raise ValueError(f"Unknown test type or level: {test_type!r}, {level!r}")

    while True:
        operation = rng.choice(OPERATIONS) if test_type == RANDOM else test_type
        task = _draw_task(operation, level, rng)
        if task != previous:
            return task


def _draw_task(operation: str, level: str, rng: random.Random) -> Task:
    (first_low, first_high), (second_low, second_high) = _RANGES[operation][level]

    if operation == "Subtraction":
        # Two different numbers, larger first, so the result is at least 1.
        a, b = sorted(rng.sample(range(first_low, first_high + 1), 2), reverse=True)
        return Task(operation, a, b)

    first = rng.randint(first_low, first_high)
    second = rng.randint(second_low, second_high)
    if operation == "Division":
        # first is the divisor and second the result, so there is never a remainder.
        return Task(operation, first * second, first)
    return Task(operation, first, second)


def parse_answer(raw: str) -> int | None:
    """Return the whole number in `raw`, or None if it should not be evaluated."""
    text = raw.strip()
    if not _WHOLE_NUMBER.fullmatch(text):
        return None
    try:
        return int(text)
    except ValueError:  # Python refuses to convert absurdly long digit strings
        return None


def is_correct(task: Task, answer: int) -> bool:
    return answer == task.answer
