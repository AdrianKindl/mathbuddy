"""Number Chain rules: chain generation, answers, score, lives (spec 002e).

A chain is a start number followed by steps such as "+ 8" or "× 3". The user
calculates along in their head and enters the result. Every solved chain adds a
point and makes the next chain one step longer.
"""

import random
from dataclasses import dataclass, replace
from enum import StrEnum

from tasks import LEVELS, parse_answer

LIVES = 3
MAX_EXTRA_STEPS = 10  # a chain grows by at most this many steps


@dataclass(frozen=True)
class LevelSettings:
    steps: int  # steps in the first chain
    operations: tuple[str, ...]
    start: tuple[int, int]  # range of the start number
    add: tuple[int, int]  # range of the number in + and − steps
    multiply: tuple[int, int]  # range of the number in × and ÷ steps
    largest: int  # the running result never goes above this
    seconds: float  # how long each step is shown


LEVEL_SETTINGS = {
    "Easy": LevelSettings(4, ("+", "−"), (2, 10), (2, 9), (2, 2), 50, 3.0),
    "Medium": LevelSettings(5, ("+", "−", "×"), (2, 20), (2, 15), (2, 5), 150, 2.5),
    "Hard": LevelSettings(6, ("+", "−", "×", "÷"), (2, 30), (3, 25), (2, 9), 400, 2.0),
    "Pro": LevelSettings(8, ("+", "−", "×", "÷"), (5, 50), (5, 49), (2, 12), 999, 1.5),
}


class Status(StrEnum):
    RUNNING = "running"
    LOST = "lost"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    IGNORED = "ignored"


@dataclass(frozen=True)
class ChainStep:
    op: str
    value: int

    @property
    def text(self) -> str:
        return f"{self.op} {self.value}"


@dataclass(frozen=True)
class Chain:
    start: int
    steps: tuple[ChainStep, ...]

    @property
    def result(self) -> int:
        value = self.start
        for step in self.steps:
            value = apply(value, step)
        return value


@dataclass(frozen=True)
class Game:
    level: str
    chain: Chain
    score: int = 0
    lives: int = LIVES
    status: Status = Status.RUNNING
    last_result: int | None = None  # the result of the chain just answered


def apply(value: int, step: ChainStep) -> int:
    if step.op == "+":
        return value + step.value
    if step.op == "−":
        return value - step.value
    if step.op == "×":
        return value * step.value
    if step.op == "÷":
        return value // step.value
    raise ValueError(f"Unknown operation: {step.op!r}")


_OPPOSITE = {"+": "−", "−": "+", "×": "÷", "÷": "×"}


def _undo(step: ChainStep) -> ChainStep:
    """The step that takes `step` back."""
    return ChainStep(_OPPOSITE[step.op], step.value)


def _possible_steps(value: int, settings: LevelSettings) -> list[ChainStep]:
    """Every step that keeps the result a whole number from 1 to `largest`."""
    steps = []
    for op in settings.operations:
        low, high = settings.add if op in ("+", "−") else settings.multiply
        for number in range(low, high + 1):
            step = ChainStep(op, number)
            if op == "÷" and value % number != 0:
                continue
            if 1 <= apply(value, step) <= settings.largest:
                steps.append(step)
    return steps


def chain_length(level: str, score: int) -> int:
    """The number of steps after `score` solved chains."""
    return LEVEL_SETTINGS[level].steps + min(score, MAX_EXTRA_STEPS)


def generate_chain(level: str, length: int, rng: random.Random) -> Chain:
    """A start number and `length` steps; every result on the way stays in range."""
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level!r}")
    settings = LEVEL_SETTINGS[level]

    while True:
        value = rng.randint(*settings.start)
        start = value
        steps: list[ChainStep] = []
        while len(steps) < length:
            # No step that repeats or undoes the one before: "+ 8, − 8" is dull.
            possible = [
                step
                for step in _possible_steps(value, settings)
                if not steps or (step != steps[-1] and step != _undo(steps[-1]))
            ]
            if not possible:
                break  # a dead end: start a new chain
            # Pick the operation first, so + and − do not crowd out × and ÷.
            op = rng.choice(sorted({step.op for step in possible}))
            step = rng.choice([step for step in possible if step.op == op])
            steps.append(step)
            value = apply(value, step)
        if len(steps) == length:
            return Chain(start=start, steps=tuple(steps))


def start_game(level: str, rng: random.Random) -> Game:
    return Game(level=level, chain=generate_chain(level, chain_length(level, 0), rng))


def answer(game: Game, raw: str, rng: random.Random) -> tuple[Game, Outcome]:
    """Evaluate the answer to the current chain and prepare the next one."""
    if game.status != Status.RUNNING:
        return game, Outcome.IGNORED
    value = parse_answer(raw)
    if value is None:
        return game, Outcome.IGNORED

    result = game.chain.result
    if value == result:
        score = game.score + 1
        chain = generate_chain(game.level, chain_length(game.level, score), rng)
        return replace(game, score=score, chain=chain, last_result=result), Outcome.CORRECT

    lives = game.lives - 1
    if lives <= 0:
        return replace(game, lives=0, status=Status.LOST, last_result=result), Outcome.WRONG
    chain = generate_chain(game.level, chain_length(game.level, game.score), rng)
    return replace(game, lives=lives, chain=chain, last_result=result), Outcome.WRONG
