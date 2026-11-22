"""Number Hunt rules: puzzle generation, steps, undo, reset, lives, win and loss (spec 002c).

The user combines two of the current numbers with +, −, × or ÷. Each step
replaces the two numbers with their result. The game is won when a single
number is left and it equals the target.
"""

import random
from dataclasses import dataclass, replace
from enum import StrEnum

from tasks import LEVELS

LIVES = 3
OPERATIONS = ("+", "−", "×", "÷")

# Per level: how many start numbers, and their range (inclusive).
START_NUMBERS = {
    "Easy": (3, 2, 9),
    "Medium": (4, 2, 12),
    "Hard": (5, 2, 20),
    "Pro": (6, 2, 25),
}
# Per level: the range of the target (inclusive).
TARGET_RANGE = {
    "Easy": (10, 99),
    "Medium": (20, 199),
    "Hard": (50, 499),
    "Pro": (100, 999),
}


# StrEnum and compared with ==, for the same reason as in runs.py.
class Status(StrEnum):
    RUNNING = "running"
    WON = "won"
    LOST = "lost"


class Outcome(StrEnum):
    CORRECT = "correct"  # a valid step was applied
    WRONG = "wrong"  # an invalid step: costs a life, nothing changes
    UNDONE = "undone"
    RESET = "reset"
    IGNORED = "ignored"


@dataclass(frozen=True)
class Step:
    a: int
    op: str
    b: int
    result: int

    @property
    def text(self) -> str:
        return f"{self.a} {self.op} {self.b} = {self.result}"


@dataclass(frozen=True)
class Puzzle:
    numbers: tuple[int, ...]
    target: int
    solution: tuple[Step, ...]  # one way to reach the target, using every number


@dataclass(frozen=True)
class Game:
    level: str
    puzzle: Puzzle
    numbers: tuple[int, ...]
    steps: tuple[Step, ...] = ()
    history: tuple[tuple[int, ...], ...] = ()  # the numbers before each step
    lives: int = LIVES
    status: Status = Status.RUNNING


def calculate(a: int, op: str, b: int) -> int | None:
    """The result of a op b, or None if the brief does not allow this step.

    Every result must be a whole number greater than zero, and multiplying or
    dividing by 1 is not allowed.
    """
    if op == "+":
        return a + b
    if op == "−":
        return a - b if a > b else None
    if op == "×":
        return a * b if a != 1 and b != 1 else None
    if op == "÷":
        return a // b if b != 1 and a % b == 0 else None
    raise ValueError(f"Unknown operation: {op!r}")


# --- Generating puzzles ---


def _combine_randomly(
    numbers: tuple[int, ...], rng: random.Random
) -> tuple[int, tuple[Step, ...]] | None:
    """Combine all numbers by random valid steps. None if it runs into a dead end."""
    pool = list(numbers)
    steps = []
    while len(pool) > 1:
        options = [
            (i, op, j)
            for i in range(len(pool))
            for j in range(len(pool))
            if i != j
            for op in OPERATIONS
            if calculate(pool[i], op, pool[j]) is not None
        ]
        if not options:
            return None
        i, op, j = rng.choice(options)
        result = calculate(pool[i], op, pool[j])
        steps.append(Step(pool[i], op, pool[j], result))
        pool = [n for k, n in enumerate(pool) if k not in (i, j)] + [result]
    return pool[0], tuple(steps)


def generate_puzzle(level: str, rng: random.Random) -> Puzzle:
    """Random start numbers and a target that is reachable with all of them."""
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level!r}")
    count, low, high = START_NUMBERS[level]
    target_low, target_high = TARGET_RANGE[level]

    while True:
        numbers = tuple(rng.randint(low, high) for _ in range(count))
        combined = _combine_randomly(numbers, rng)
        if combined is None:
            continue
        target, steps = combined
        if target_low <= target <= target_high and target not in numbers:
            return Puzzle(numbers=numbers, target=target, solution=steps)


# --- Playing ---


def start_game(level: str, rng: random.Random) -> Game:
    puzzle = generate_puzzle(level, rng)
    return Game(level=level, puzzle=puzzle, numbers=puzzle.numbers)


def _lose_life(game: Game, **changes) -> Game:
    lives = game.lives - 1
    status = Status.LOST if lives <= 0 else Status.RUNNING
    return replace(game, lives=lives, status=status, **changes)


def apply_step(game: Game, first: int, op: str, second: int) -> tuple[Game, Outcome]:
    """Combine the numbers at positions `first` and `second` of game.numbers."""
    if op not in OPERATIONS:
        raise ValueError(f"Unknown operation: {op!r}")
    if not (0 <= first < len(game.numbers) and 0 <= second < len(game.numbers)):
        raise ValueError(f"No number at position {first} or {second}")
    if game.status != Status.RUNNING or first == second:
        return game, Outcome.IGNORED

    a, b = game.numbers[first], game.numbers[second]
    result = calculate(a, op, b)
    if result is None:
        return _lose_life(game), Outcome.WRONG

    # The result takes the place of the first number; the second one goes.
    numbers = tuple(
        result if k == first else n for k, n in enumerate(game.numbers) if k != second
    )
    won = len(numbers) == 1 and numbers[0] == game.puzzle.target
    return (
        replace(
            game,
            numbers=numbers,
            steps=(*game.steps, Step(a, op, b, result)),
            history=(*game.history, game.numbers),
            status=Status.WON if won else Status.RUNNING,
        ),
        Outcome.CORRECT,
    )


def undo(game: Game) -> tuple[Game, Outcome]:
    """Take back the last step. Costs a life."""
    if game.status != Status.RUNNING or not game.steps:
        return game, Outcome.IGNORED
    return (
        _lose_life(
            game, steps=game.steps[:-1], history=game.history[:-1], numbers=game.history[-1]
        ),
        Outcome.UNDONE,
    )


def reset(game: Game) -> tuple[Game, Outcome]:
    """Go back to the start numbers. Costs a life."""
    if game.status != Status.RUNNING or not game.steps:
        return game, Outcome.IGNORED
    return (
        _lose_life(game, steps=(), history=(), numbers=game.puzzle.numbers),
        Outcome.RESET,
    )


def is_stuck(game: Game) -> bool:
    """One number is left but it is not the target: only Undo or Reset help."""
    return game.status == Status.RUNNING and len(game.numbers) == 1
