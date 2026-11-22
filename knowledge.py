"""Knowledge rules: practice tasks, rounds, navigation and the ✓ (K R3–K R7).

No Streamlit, no SQL and no clock. Randomness only comes from the
random.Random passed in. The ranges themselves are data in knowledge_content.py;
this module turns them into tasks.
"""

import random
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from functools import lru_cache

from knowledge_content import category_of, get_trick
from tasks import LEVELS, parse_answer

ROUND_LENGTH = 10


# StrEnum, compared with ==: Streamlit re-imports a changed module, while a Round
# in session_state keeps members of the old class. Values still compare equal.
class Status(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    SKIPPED = "skipped"
    IGNORED = "ignored"


@dataclass(frozen=True)
class PracticeTask:
    trick_id: str
    operation: str  # "+", "−", "×", "÷" or "²"
    a: int
    b: int | None  # None for a square

    @property
    def answer(self) -> int:
        if self.operation == "²":
            return self.a * self.a
        if self.operation == "+":
            return self.a + self.b
        if self.operation == "−":
            return self.a - self.b
        if self.operation == "×":
            return self.a * self.b
        return self.a // self.b

    @property
    def text(self) -> str:
        if self.operation == "²":
            return f"{self.a:,}²"
        return f"{self.a:,} {self.operation} {self.b:,}"


@dataclass(frozen=True)
class Attempt:
    task: PracticeTask
    given: str | None  # None for a skip
    outcome: Outcome


@dataclass(frozen=True)
class Round:
    trick_id: str
    level: str
    tasks: tuple[PracticeTask, ...]
    attempts: tuple[Attempt, ...] = ()

    @property
    def status(self) -> Status:
        return Status.COMPLETED if len(self.attempts) >= len(self.tasks) else Status.RUNNING

    def _count(self, outcome: Outcome) -> int:
        return sum(1 for attempt in self.attempts if attempt.outcome == outcome)

    @property
    def correct(self) -> int:
        return self._count(Outcome.CORRECT)

    @property
    def wrong(self) -> int:
        return self._count(Outcome.WRONG)

    @property
    def skipped(self) -> int:
        return self._count(Outcome.SKIPPED)


@dataclass(frozen=True)
class SavedRound:
    id: str
    trick_id: str
    level: str
    finished_at: datetime
    correct: int


# --- Number pools from the content's ranges ---


@lru_cache(maxsize=None)
def _pool(
    spec: tuple[int, ...],
    mod: int | None = None,
    ends: tuple[int, ...] = (),
    digit_sum: tuple[int, int] | None = None,
    factor: tuple[int, int] | None = None,
) -> tuple[int, ...]:
    """All numbers of a (low, high) or (low, high, step) range that pass the filters."""
    low, high, *step = spec
    numbers = range(low, high + 1, step[0] if step else 1)
    return tuple(
        n
        for n in numbers
        if (mod is None or n % mod in ends)
        and (digit_sum is None or digit_sum[0] <= sum(map(int, str(n))) <= digit_sum[1])
        and (factor is None or any(n % f == 0 for f in range(factor[0], factor[1] + 1)))
    )


@lru_cache(maxsize=None)
def _square_pool(spec: tuple[int, ...], exclude: tuple[int, ...]) -> tuple[int, ...]:
    """Square tasks leave out multiples of 10, unless the range steps to them on purpose."""
    stepped = len(spec) == 3
    return tuple(
        n for n in _pool(spec) if (stepped or n % 10 != 0) and n not in exclude
    )


def _digit(n: int, place: int) -> int:
    return n // 10**place % 10


def _between(rng: random.Random, spec: tuple[int, int]) -> int:
    return rng.randint(spec[0], spec[1])


# --- One rule per kind of trick. Each returns (operation, a, b). ---


def _sum_pair(rng, p):
    return "+", _between(rng, p["a"]), _between(rng, p["b"])


def _compatible(rng, p):
    a = rng.choice(_pool(p["a"]))
    return "+", a, p["whole"] - a + _between(rng, p["extra"])


def _give_take(rng, p):
    while True:  # a lies 1 to `below` under a multiple of `unit`
        a = _between(rng, p["a"])
        if 1 <= -a % p["unit"] <= p["below"]:
            return "+", a, _between(rng, p["b"])


def _nine(rng, p):
    return "+", rng.choice(_pool(p["a"])), _between(rng, p["b"])


def _difference(rng, p):
    firsts = _pool(p["a"])
    seconds = _pool(p["b"], p.get("b_mod"), p.get("b_ends", ()))
    cross = p.get("cross")
    while True:  # the result is at least 1, and a round number lies in between
        a, b = rng.choice(firsts), rng.choice(seconds)
        if a > b and (cross is None or a // cross > b // cross):
            return "−", a, b


def _no_borrow(rng, p):
    digits = p["digits"]
    while True:  # every digit of a is at least the matching digit of b
        a = b = 0
        for place in reversed(range(digits)):
            low = 1 if place == digits - 1 else 0
            lower = rng.randint(low, 9)
            upper = rng.randint(lower, 9)
            a, b = a * 10 + upper, b * 10 + lower
        if a > b:
            return "−", a, b


def _borrow(rng, p):
    digits, places, borrows = p["digits"], p["places"], p["borrows"]
    low, high = 10 ** (digits - 1), 10**digits - 1
    while True:
        a, b = rng.randint(low, high), rng.randint(low, high)
        count = sum(1 for place in places if _digit(a, place) < _digit(b, place))
        if a > b and count in borrows:
            return "−", a, b


def _times(rng, p):
    a = rng.choice(_pool(p["a"], digit_sum=p.get("digit_sum")))
    return "×", a, p["factor"]


def _divide(rng, p):
    divisor = p["divisor"]
    return "÷", divisor * _between(rng, p["result"]), divisor


def _cancel_zeros(rng, p):
    while True:  # the result is whole
        a = _between(rng, p["a"]) * p["a_scale"]
        b = _between(rng, p["b"]) * p["b_scale"]
        if a % b == 0:
            return "÷", a, b


def _simplify(rng, p):
    divisors = _pool(p["divisor"], factor=p["factor"])
    low, high = p.get("dividend", (1, 10**9))
    while True:
        divisor = rng.choice(divisors)
        dividend = divisor * _between(rng, p["result"])
        if low <= dividend <= high:
            return "÷", dividend, divisor


def _square(rng, p):
    return "²", rng.choice(_square_pool(p["n"], p.get("exclude", ()))), None


_GENERATORS = {
    "sum_pair": _sum_pair,
    "compatible": _compatible,
    "give_take": _give_take,
    "nine": _nine,
    "difference": _difference,
    "no_borrow": _no_borrow,
    "borrow": _borrow,
    "times": _times,
    "divide": _divide,
    "cancel_zeros": _cancel_zeros,
    "simplify": _simplify,
    "square": _square,
}


# --- Tasks and rounds (K R4, K R5, K R6) ---


def generate_task(
    trick_id: str, level: str, rng: random.Random, previous: PracticeTask | None = None
) -> PracticeTask:
    """A task inside the trick's range for the level, different from `previous`."""
    try:
        trick = get_trick(trick_id)
    except KeyError:
        raise ValueError(f"Unknown trick: {trick_id!r}") from None
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level!r}")

    make = _GENERATORS[trick.generator]
    params = trick.practice[level]
    while True:
        task = PracticeTask(trick_id, *make(rng, params))
        if task != previous:
            return task


def start_round(trick_id: str, level: str, rng: random.Random) -> Round:
    """A new round of ROUND_LENGTH tasks, never the same task twice in a row."""
    tasks: list[PracticeTask] = []
    for _ in range(ROUND_LENGTH):
        tasks.append(generate_task(trick_id, level, rng, tasks[-1] if tasks else None))
    return Round(trick_id, level, tuple(tasks))


def current_task(practice_round: Round) -> PracticeTask | None:
    if practice_round.status != Status.RUNNING:
        return None
    return practice_round.tasks[len(practice_round.attempts)]


def submit_answer(practice_round: Round, raw: str) -> tuple[Round, Outcome]:
    task = current_task(practice_round)
    if task is None:
        return practice_round, Outcome.IGNORED
    answer = parse_answer(raw)
    if answer is None:
        return practice_round, Outcome.IGNORED
    outcome = Outcome.CORRECT if answer == task.answer else Outcome.WRONG
    return _record(practice_round, Attempt(task, raw.strip(), outcome)), outcome


def skip_task(practice_round: Round) -> tuple[Round, Outcome]:
    task = current_task(practice_round)
    if task is None:
        return practice_round, Outcome.IGNORED
    return _record(practice_round, Attempt(task, None, Outcome.SKIPPED)), Outcome.SKIPPED


def _record(practice_round: Round, attempt: Attempt) -> Round:
    return replace(practice_round, attempts=(*practice_round.attempts, attempt))


# --- Navigation (K R3) ---


def neighbours(trick_id: str) -> tuple[str | None, str | None]:
    """The previous and next trick in the same category, or None at either end."""
    ids = [trick.id for trick in category_of(trick_id).tricks]
    index = ids.index(trick_id)
    previous = ids[index - 1] if index > 0 else None
    following = ids[index + 1] if index < len(ids) - 1 else None
    return previous, following


def position(trick_id: str) -> tuple[int, int]:
    """The trick's place in its category, counted from 1, and the category size."""
    ids = [trick.id for trick in category_of(trick_id).tricks]
    return ids.index(trick_id) + 1, len(ids)


# --- Practised (K R7) ---


def practised(saved_rounds: Iterable[SavedRound]) -> set[str]:
    """The tricks with at least one completed round, at any level and score."""
    return {saved.trick_id for saved in saved_rounds}
