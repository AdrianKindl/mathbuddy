"""One-file installer for the Mathbuddy Trainer (spec 002).

How to use it:

1. Save this file as install_trainer.py in the project root, next to app.py.
2. Run it once in the terminal:

       uv run python install_trainer.py

3. Delete install_trainer.py again. It does not belong in the repository.

What it does, and nothing else:

- It creates the nine Trainer files listed in FILES below. A file that already
  exists is never overwritten.
- It makes the small edits listed in EDITS at the bottom: three in app.py, two
  in tests/test_app.py and one in AGENTS.md. An edit is only made if the exact
  old text is found once. Otherwise the file is left alone and the edit is
  printed, so it can be made by hand.

Running it a second time changes nothing.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEEDED = ("app.py", "tasks.py", "runs.py", "db.py")

FILES = {}

####################################################################################################
# specs/002-trainer.md
####################################################################################################

FILES['specs/002-trainer.md'] = r'''# 002 – Trainer: configurable practice that explains mistakes

## Why
A user should be able to practise exactly what they want (one operation, a
number type, or a special training), at their own level and in the mode they
choose, without the 60-second pressure of a test. After a mistake the Trainer
shows the correct answer and how to get there, so the user learns from it.

## What

### Choosing what to train
The Trainer screen offers three categories:

- **Operations:** one of Addition, Subtraction, Multiplication, Division,
  Percentage, Square, Square root, at one of the four levels.
- **Number types:** one of Natural numbers, Decimals, Large numbers, Money,
  Fractions. The user ticks one or more of its operations and sets a separate
  level for each. Tasks mix the ticked operations with equal probability.
  - Natural numbers: Addition, Subtraction, Multiplication, Division, Percentage, Square, Square root
  - Decimals: Addition, Subtraction, Multiplication, Division
  - Large numbers: Addition, Subtraction, Multiplication, Division, Percentage
  - Money: Addition, Subtraction, Division, Percentage
  - Fractions: Addition, Subtraction, Multiplication, Division
- **Special trainings:** one of Word problems, Mixed tasks, Digit sums, Rule of
  three, Equations, Chain calculations, Fun with fractions, at one of the four levels.

The setup screen shows an example task for the current selection and remembers
the selection for the rest of the browser session.

### Modes
- **Task count:** 5–100 tasks. The time is measured but does not run out. The
  session ends with the last answer or skip.
- **Total time:** 30–900 seconds. An answer or skip at or after the limit does
  not count, and the session ends.
- **Time per task:** 1–60 seconds. The clock restarts with every answer or
  skip. The session ends when one task takes as long as the limit or longer.

A 3-second countdown runs before the session and does not count towards any time.
Settings outside these ranges, or without any operation, are rejected with a
message and no session starts. The limits are enforced by the rules, not only
by the input fields.

### Answering (MB R2, MB R3)
- One task at a time. Correct: +1. Wrong: no point. Skip: counts as wrong for
  the accuracy and is recorded as skipped. In all three cases a new task appears.
- After a wrong answer or a skip, the correct answer and the way to it are
  shown next to the new task. After a correct answer the solution is confirmed.
- The same task never appears twice in a row.
- Input that is empty or not in the accepted format is not evaluated: nothing
  is counted, the task stays, the clock keeps running, and a hint shows the format.
- Accepted formats. All tasks have exact answers, so nothing is ever rounded.
  - Whole number: digits only, e.g. `4250`.
  - Decimal: digits with a point, e.g. `12.5`. `12.50` is the same answer.
  - Money: like a decimal with at most two decimals, with or without `€`.
  - Fraction: `3/4` in lowest terms, or a whole number. A fraction that is not
    simplified (`6/8`) is not evaluated, so the user can simplify it.

### Result and history
- At the end: correct, wrong, skipped, accuracy, time taken, average time per
  task, a review of every task (task, the user's answer, correct answer,
  result, seconds) and the solutions of all missed tasks. If the time ran out,
  the task that was not answered is shown with its solution.
- "Train again" starts a new session with the same settings.
- Only a finished session is saved (category, name, levels, mode, limit, end
  time, duration, correct, wrong, skipped), in its own table
  `trainer_sessions`. The setup screen lists the 10 newest sessions.
- A session the user ends early, or leaves by switching section, is not saved
  and shows no result (as MB R5). One whose time was already up counts as finished.

### Task rules
All bounds are inclusive. Natural numbers use MB R1 for the four basic operations.

**Natural numbers**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Percentage p % of n | p: 10, 25, 50; n: 20–200, step 20 | p: 5, 20, 40, 60, 75; n: 20–400, step 20 | p: 1–99; n: 100–2,000, step 100 | p: 101–250; n: 100–5,000, step 100 |
| Square a² / Square root √(r²) | a, r: 2–9 | 11–19 | 21–39 | 41–99 |

From Hard upwards, a and r are never a multiple of 10.

**Decimals** (one decimal unless stated)

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction | 0.1–9.9 | 10.0–99.9 | 1.00–99.99 (two decimals) | 100.00–999.99 (two decimals) |
| Multiplication a × b | a: 0.1–0.9; b: 2–9 | a: 1.1–9.9; b: 2–9 | a: 1.1–9.9; b: 0.2–0.9 | a, b: 1.1–9.9 |
| Division a ÷ b = q | b: 2–9; q: 0.1–0.9 | b: 2–9; q: 1.1–9.9 | b: 0.2–0.9; q: 2–19 | b: 0.2–0.9; q: 1.1–9.9 |

A factor or result of 1.1–9.9 is never a whole number.

**Large numbers**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction | 1,000–99,000, step 1,000 | 11,000–999,000, step 1,000 | 110,000–9,990,000, step 10,000 | 10,100,000–999,900,000, step 100,000 |
| Multiplication a × b | a: 2,000–9,000; b: 2–9 | a, b: 200–900, step 100 | a: 11,000–19,000; b: 200–900 | a: 11,000–99,000; b: 1,100–1,900 |
| Division | (a × b) ÷ b with the a and b of Multiplication | | | |
| Percentage p % of n | p: 10, 25, 50; n: 10,000–990,000, step 10,000 | p: 5, 20, 40, 60, 75; n as Easy | p: 1–99; n: 100,000–9,900,000, step 100,000 | p: 101–250; n: 1–99 million |

**Money**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction | €0.10–€9.90, step €0.10 | €1.00–€49.95, step €0.05 | €1.00–€99.99 | €100.00–€999.99 |
| Division: amount ÷ people = share | people: 2–5; share: €1.00–€9.50, step €0.50 | people: 2–9; share: €1.10–€19.90, step €0.10 | people: 2–9; share: €1.05–€49.95, step €0.05 | people: 11–19; share: €1.01–€29.99 |
| Percentage p % of n | p: 10, 25, 50; n: €20–€200, step €20 | p: 5, 20, 40, 60, 75; n: €2–€98, step €2 | p: 1–99; n: €1–€99 | p: 1–99; n: €100–€2,000, step €50 |

Every result is exact to the cent.

**Fractions** (always shown in lowest terms)

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction (fractions below 1) | same denominator, 2–12 | denominators d and 2d or 3d, d: 2–6 | two different denominators, 2–9 | two different denominators, 5–15 |
| Multiplication, Division | a fraction (denominator 2–9) and a whole number 2–9 | two fractions below 1, denominators 2–6 | two fractions below 1, denominators 5–12 | numerators and denominators 2–12, also above 1 |

**All number types:** in a subtraction the larger number comes first and the
result is above zero. In a division the divisor and the result are chosen
first, so the result is always exact. From Hard upwards a percentage p is
never a multiple of 10.

**Special trainings**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Word problems | one calculation in a short story, with the MB R1 numbers of the level; all four operations occur | | | |
| Mixed tasks | a + b × c, a × b ± c (2–9) | brackets and division, e.g. (a + b) × c | two products or two brackets (2–12) | larger numbers, e.g. (a + b) × (c − d) |
| Digit sums | 2 digits | 3 digits | 5 digits | 8 digits |
| Rule of three | value for one: 2–9; amounts 2–9 | asked amount 11–20 | value for one: 11–19; asked amount 11–29 | inverse: more workers need less time |
| Equations | x + a = b, x − a = b | ax = b, x ÷ a = b | ax + b = c, ax − b = c | x on both sides, or a(x + b) = c |
| Chain calculations | 3 steps, + − | 4 steps, + − × | 5 steps, + − × ÷ | 7 steps, + − × ÷ |
| Fun with fractions | simplify a fraction, GCD of two numbers, LCM of two numbers, mixed; larger numbers at higher levels | | | |

Every special training has a whole-number answer above zero, except
simplifying a fraction. In a chain every intermediate result is a whole number
from 1 to 9,999.

### Structure
- `trainer_tasks.py`: task generation and answer checking. No Streamlit, no SQL,
  randomness only from the `random.Random` passed in.
- `trainer.py`: settings, modes, time limits, result. No Streamlit, no SQL, the
  current time is passed in as `now`.
- `trainer_db.py`: storage of finished sessions, through `db.connect()`.
- `trainer_ui.py`: the screens. `app.py` only calls `trainer_ui.render()` and
  `trainer_ui.leave()`.

## Changes to 001
- The Trainer no longer shows "Coming soon" (MB01). Two tests in
  `tests/test_app.py` that used the Trainer as an unbuilt section now use Knowledge.

## Out of scope
Trainer sessions in the profile statistics, streak and 7-day chart (MB R8 counts
test runs). Accounts: sessions are saved without a user for now, like runs in
001. Knowledge and Games.

## Done when
- **Offer:** the three categories, seven operations, five number types with
  their operations, seven special trainings, four levels and three modes are
  selectable.
- **Generation:** for every operation of every number type and every special
  training, at every level, 1,000 generated tasks (fixed seed) follow the
  tables above; each answer, recalculated from the task text, is right; and the
  shown answer is accepted when typed.
- **Variety:** two rounds with different seeds differ; no task twice in a row,
  also when several operations are mixed.
- **Answers:** for 25 % of 80, answer 20 → correct; 25 → wrong; Skip →
  skipped; empty input → nothing changes. For 3/4, answer 6/8 is not evaluated.
- **Task count:** a session of 5 tasks ends with the 5th answer or skip, not before.
- **Total time:** with 30 s, an answer at 29.9 s counts; at 30.0 s it does not
  and the session ends.
- **Time per task:** with 10 s, an answer 9.9 s after the task appeared counts;
  at 10.0 s the session ends. Each answer restarts the 10 s.
- **Rejected settings:** 4 or 101 tasks, 29 or 901 s, 0 or 61 s per task, no
  operation ticked, and an operation the number type does not offer are all
  rejected, and no session starts.
- **Result:** 3 correct, 1 wrong, 1 skipped → accuracy 60.0 %; the review lists
  all 5 tasks and the solutions of the 2 missed ones.
- **Saving:** a finished session appears once in the history, also after
  stopping and restarting the app. A session ended early leaves the history unchanged.
'''

####################################################################################################
# trainer_tasks.py
####################################################################################################

FILES['trainer_tasks.py'] = r'''"""Trainer task generation and answer checking (spec 002).

Every generator receives a Topic and a `random.Random` and returns a
TrainerTask. Answers are exact `Fraction` values, so whole numbers, decimals,
money and fractions are all compared without rounding errors.
"""

import math
import random
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

import tasks
from tasks import LEVELS

NATURAL = "Natural numbers"
DECIMALS = "Decimals"
LARGE = "Large numbers"
MONEY = "Money"
FRACTIONS = "Fractions"
SPECIAL = "Special trainings"

OPERATIONS = (
    "Addition",
    "Subtraction",
    "Multiplication",
    "Division",
    "Percentage",
    "Square",
    "Square root",
)

# Which operations each number type offers (product brief, R2).
NUMBER_TYPES = {
    NATURAL: OPERATIONS,
    DECIMALS: ("Addition", "Subtraction", "Multiplication", "Division"),
    LARGE: ("Addition", "Subtraction", "Multiplication", "Division", "Percentage"),
    MONEY: ("Addition", "Subtraction", "Division", "Percentage"),
    FRACTIONS: ("Addition", "Subtraction", "Multiplication", "Division"),
}

SPECIAL_TRAININGS = (
    "Word problems",
    "Mixed tasks",
    "Digit sums",
    "Rule of three",
    "Equations",
    "Chain calculations",
    "Fun with fractions",
)

MAX_ANSWER_LENGTH = 20
MAX_DECIMAL_PLACES = 6


class AnswerKind(StrEnum):
    WHOLE = "whole"
    DECIMAL = "decimal"
    MONEY = "money"
    FRACTION = "fraction"


class Check(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    INVALID = "invalid"  # not in the accepted format, so it is not evaluated


@dataclass(frozen=True)
class Topic:
    """One thing to practise: an operation of a number type, or a special training."""

    group: str  # a number type, or SPECIAL
    name: str  # an operation, or a special training
    level: str


@dataclass(frozen=True)
class TrainerTask:
    topic: Topic
    prompt: str  # short instruction, e.g. "Solve for x"
    text: str  # the task itself, e.g. "3x + 5 = 20"
    answer: Fraction
    kind: AnswerKind
    solution: str  # the way to the answer, shown after a wrong answer or a skip


# --- Showing numbers ---


def format_number(value: Fraction | int, places: int | None = None) -> str:
    """Write a whole number or decimal with thousands separators: 1,234.5.

    `places` fixes the number of decimals. Without it, as many as needed are used.
    """
    value = Fraction(value)
    if places is None:
        places = 0
        while (value * 10**places).denominator != 1:
            places += 1
            if places > MAX_DECIMAL_PLACES:
                raise ValueError(f"{value} cannot be written as a short decimal")
    scaled = value * 10**places
    if scaled.denominator != 1:
        raise ValueError(f"{value} has more than {places} decimals")
    whole, part = divmod(abs(scaled.numerator), 10**places)
    text = f"{whole:,}"
    if places:
        text += f".{part:0{places}d}"
    return f"−{text}" if value < 0 else text


def format_money(value: Fraction | int) -> str:
    return "€" + format_number(value, places=2)


def format_fraction(value: Fraction | int) -> str:
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def format_answer(task: TrainerTask) -> str:
    """The correct answer the way it is shown to the user."""
    if task.kind == AnswerKind.MONEY:
        return format_money(task.answer)
    if task.kind == AnswerKind.FRACTION:
        return format_fraction(task.answer)
    return format_number(task.answer)


# --- Checking answers ---

ANSWER_HINTS = {
    AnswerKind.WHOLE: "Whole numbers only, e.g. 4250",
    AnswerKind.DECIMAL: "Use digits and a point for decimals, e.g. 12.5",
    AnswerKind.MONEY: "Enter an amount with a point and at most two decimals, e.g. 12.50",
    AnswerKind.FRACTION: "Enter a fraction in lowest terms, e.g. 3/4, or a whole number",
}

_PATTERNS = {
    AnswerKind.WHOLE: re.compile(r"[+-]?[0-9]+"),
    AnswerKind.DECIMAL: re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?"),
    AnswerKind.MONEY: re.compile(r"[+-]?[0-9]+(?:\.[0-9]{1,2})?"),
    AnswerKind.FRACTION: re.compile(r"[+-]?[0-9]+(?:\s*/\s*[0-9]+)?"),
}


def parse_answer(raw: str, kind: AnswerKind) -> Fraction | None:
    """Return the value typed in `raw`, or None if it should not be evaluated."""
    text = raw.strip()
    if kind == AnswerKind.MONEY:
        text = text.removeprefix("€").removesuffix("€").strip()
    if len(text) > MAX_ANSWER_LENGTH or not _PATTERNS[kind].fullmatch(text):
        return None

    if kind == AnswerKind.FRACTION and "/" in text:
        top, bottom = (int(part) for part in text.split("/"))
        # 6/8 is not accepted: the user is asked to simplify first.
        if bottom == 0 or math.gcd(top, bottom) != 1:
            return None
        return Fraction(top, bottom)
    return Fraction(text)


def check_answer(task: TrainerTask, raw: str) -> Check:
    answer = parse_answer(raw, task.kind)
    if answer is None:
        return Check.INVALID
    return Check.CORRECT if answer == task.answer else Check.WRONG


# --- Helpers for the generators ---


def _task(
    topic: Topic,
    text: str,
    answer: Fraction | int,
    solution: str,
    kind: AnswerKind = AnswerKind.WHOLE,
    prompt: str = "Calculate",
) -> TrainerTask:
    return TrainerTask(topic, prompt, text, Fraction(answer), kind, solution)


def _not_round(low: int, high: int) -> tuple[int, ...]:
    """low to high without multiples of 10, which would make a task trivial."""
    return tuple(number for number in range(low, high + 1) if number % 10)


def _larger_first(draw: Callable[[], Fraction | int]) -> tuple:
    """Two different numbers, larger first, so a subtraction stays above zero."""
    while True:
        first, second = draw(), draw()
        if first != second:
            return max(first, second), min(first, second)


# --- Natural numbers ---

_PERCENT = {  # level: (percentages, base numbers)
    "Easy": ((10, 25, 50), range(20, 201, 20)),
    "Medium": ((5, 20, 40, 60, 75), range(20, 401, 20)),
    "Hard": (_not_round(1, 99), range(100, 2001, 100)),
    "Pro": (_not_round(101, 250), range(100, 5001, 100)),
}

_ROOTS = {  # level: numbers that are squared, or that are the result of a root
    "Easy": tuple(range(2, 10)),
    "Medium": tuple(range(11, 20)),
    "Hard": _not_round(21, 39),
    "Pro": _not_round(41, 99),
}


def _basic(topic: Topic, rng: random.Random) -> TrainerTask:
    """Addition, subtraction, multiplication and division follow MB R1 in tasks.py."""
    task = tasks.generate_task(topic.name, topic.level, rng)
    solution = f"{task.text} = {task.answer:,}"
    if task.operation == "Division":
        solution += f", because {task.answer:,} × {task.b:,} = {task.a:,}"
    return _task(topic, task.text, task.answer, solution)


def _percent_task(topic: Topic, percent: int, base: int, money: bool = False) -> TrainerTask:
    show = format_money if money else format_number
    result = Fraction(percent * base, 100)
    text = f"{percent} % of {show(base)}"
    solution = f"{text} = {show(base)} × {percent} ÷ 100 = {show(result)}"
    kind = AnswerKind.MONEY if money else AnswerKind.WHOLE
    return _task(topic, text, result, solution, kind=kind)


def _percentage(topic: Topic, rng: random.Random) -> TrainerTask:
    percents, bases = _PERCENT[topic.level]
    return _percent_task(topic, rng.choice(percents), rng.choice(bases))


def _square(topic: Topic, rng: random.Random) -> TrainerTask:
    a = rng.choice(_ROOTS[topic.level])
    return _task(topic, f"{a}²", a * a, f"{a}² = {a} × {a} = {a * a:,}")


def _square_root(topic: Topic, rng: random.Random) -> TrainerTask:
    root = rng.choice(_ROOTS[topic.level])
    square = root * root
    solution = f"√{square:,} = {root}, because {root} × {root} = {square:,}"
    return _task(topic, f"√{square:,}", root, solution)


# --- Decimals ---

# Decimals are drawn as whole numbers of tenths or hundredths:
# (low, high, decimal places, whole numbers allowed).
_DECIMAL_SUMS = {
    "Easy": (1, 99, 1, True),  # 0.1 to 9.9
    "Medium": (100, 999, 1, True),  # 10.0 to 99.9
    "Hard": (100, 9_999, 2, True),  # 1.00 to 99.99
    "Pro": (10_000, 99_999, 2, True),  # 100.00 to 999.99
}

_DECIMAL_FACTORS = {  # level: (first factor, second factor)
    "Easy": ((1, 9, 1, True), (2, 9, 0, True)),  # 0.7 × 6
    "Medium": ((11, 99, 1, False), (2, 9, 0, True)),  # 7.4 × 6
    "Hard": ((11, 99, 1, False), (2, 9, 1, True)),  # 7.4 × 0.6
    "Pro": ((11, 99, 1, False), (11, 99, 1, False)),  # 7.4 × 3.6
}

_DECIMAL_DIVISIONS = {  # level: (divisor, result). The result is chosen first.
    "Easy": ((2, 9, 0, True), (1, 9, 1, True)),  # 4.2 ÷ 6 = 0.7
    "Medium": ((2, 9, 0, True), (11, 99, 1, False)),  # 44.4 ÷ 6 = 7.4
    "Hard": ((2, 9, 1, True), (2, 19, 0, True)),  # 4.2 ÷ 0.6 = 7
    "Pro": ((2, 9, 1, True), (11, 99, 1, False)),  # 4.44 ÷ 0.6 = 7.4
}


def _decimal(rng: random.Random, low: int, high: int, places: int, whole: bool) -> Fraction:
    while True:
        value = Fraction(rng.randint(low, high), 10**places)
        if whole or value.denominator != 1:
            return value


def _decimal_task(topic: Topic, a: Fraction, symbol: str, b: Fraction, result: Fraction):
    text = f"{format_number(a)} {symbol} {format_number(b)}"
    solution = f"{text} = {format_number(result)}"
    if symbol == "÷":
        solution += f", because {format_number(result)} × {format_number(b)} = {format_number(a)}"
    return _task(topic, text, result, solution, kind=AnswerKind.DECIMAL)


def _decimal_addition(topic: Topic, rng: random.Random) -> TrainerTask:
    limits = _DECIMAL_SUMS[topic.level]
    a, b = _decimal(rng, *limits), _decimal(rng, *limits)
    return _decimal_task(topic, a, "+", b, a + b)


def _decimal_subtraction(topic: Topic, rng: random.Random) -> TrainerTask:
    limits = _DECIMAL_SUMS[topic.level]
    a, b = _larger_first(lambda: _decimal(rng, *limits))
    return _decimal_task(topic, a, "−", b, a - b)


def _decimal_multiplication(topic: Topic, rng: random.Random) -> TrainerTask:
    first, second = _DECIMAL_FACTORS[topic.level]
    a, b = _decimal(rng, *first), _decimal(rng, *second)
    return _decimal_task(topic, a, "×", b, a * b)


def _decimal_division(topic: Topic, rng: random.Random) -> TrainerTask:
    divisor_limits, result_limits = _DECIMAL_DIVISIONS[topic.level]
    divisor, result = _decimal(rng, *divisor_limits), _decimal(rng, *result_limits)
    return _decimal_task(topic, divisor * result, "÷", divisor, result)


# --- Large numbers ---

# Sums: (lowest multiplier, highest multiplier, unit), e.g. 37 × 1,000 = 37,000.
_LARGE_SUMS = {
    "Easy": (1, 99, 1_000),
    "Medium": (11, 999, 1_000),
    "Hard": (11, 999, 10_000),
    "Pro": (101, 9_999, 100_000),
}

# Products: ((multipliers, unit) of a, (multipliers, unit) of b).
# A division shows (a × b) ÷ b, so its result is a.
_LARGE_FACTORS = {
    "Easy": ((range(2, 10), 1_000), (range(2, 10), 1)),  # 6,000 × 7
    "Medium": ((range(2, 10), 100), (range(2, 10), 100)),  # 600 × 700
    "Hard": ((range(11, 20), 1_000), (range(2, 10), 100)),  # 14,000 × 300
    "Pro": ((_not_round(11, 99), 1_000), (range(11, 20), 100)),  # 23,000 × 1,400
}

# Percentages: (percentages, unit). The base is 1 to 99 times the unit.
_LARGE_PERCENT = {
    "Easy": ((10, 25, 50), 10_000),
    "Medium": ((5, 20, 40, 60, 75), 10_000),
    "Hard": (_not_round(1, 99), 100_000),
    "Pro": (_not_round(101, 250), 1_000_000),
}


def _whole_task(topic: Topic, a: int, symbol: str, b: int, result: int) -> TrainerTask:
    text = f"{a:,} {symbol} {b:,}"
    solution = f"{text} = {result:,}"
    if symbol == "÷":
        solution += f", because {result:,} × {b:,} = {a:,}"
    return _task(topic, text, result, solution)


def _large(rng: random.Random, level: str) -> int:
    low, high, unit = _LARGE_SUMS[level]
    return rng.randint(low, high) * unit


def _large_factors(rng: random.Random, level: str) -> tuple[int, int]:
    (a_multipliers, a_unit), (b_multipliers, b_unit) = _LARGE_FACTORS[level]
    return rng.choice(a_multipliers) * a_unit, rng.choice(b_multipliers) * b_unit


def _large_addition(topic: Topic, rng: random.Random) -> TrainerTask:
    a, b = _large(rng, topic.level), _large(rng, topic.level)
    return _whole_task(topic, a, "+", b, a + b)


def _large_subtraction(topic: Topic, rng: random.Random) -> TrainerTask:
    a, b = _larger_first(lambda: _large(rng, topic.level))
    return _whole_task(topic, a, "−", b, a - b)


def _large_multiplication(topic: Topic, rng: random.Random) -> TrainerTask:
    a, b = _large_factors(rng, topic.level)
    return _whole_task(topic, a, "×", b, a * b)


def _large_division(topic: Topic, rng: random.Random) -> TrainerTask:
    result, divisor = _large_factors(rng, topic.level)
    return _whole_task(topic, result * divisor, "÷", divisor, result)


def _large_percentage(topic: Topic, rng: random.Random) -> TrainerTask:
    percents, unit = _LARGE_PERCENT[topic.level]
    return _percent_task(topic, rng.choice(percents), rng.randint(1, 99) * unit)


# --- Money ---

# All amounts are drawn in cents, so there is never a fraction of a cent.
_MONEY_SUMS = {
    "Easy": range(10, 991, 10),  # €0.10 to €9.90 in steps of 10 cents
    "Medium": range(100, 4_996, 5),  # €1.00 to €49.95 in steps of 5 cents
    "Hard": range(100, 10_000),  # €1.00 to €99.99
    "Pro": range(10_000, 100_000),  # €100.00 to €999.99
}

_MONEY_SHARES = {  # level: (number of people, share of each person in cents)
    "Easy": (range(2, 6), range(100, 951, 50)),
    "Medium": (range(2, 10), range(110, 1_991, 10)),
    "Hard": (range(2, 10), range(105, 4_996, 5)),
    "Pro": (range(11, 20), range(101, 3_000)),
}

_MONEY_PERCENT = {  # level: (percentages, base amounts in whole euros)
    "Easy": ((10, 25, 50), range(20, 201, 20)),
    "Medium": ((5, 20, 40, 60, 75), range(2, 99, 2)),
    "Hard": (_not_round(1, 99), range(1, 100)),
    "Pro": (_not_round(1, 99), range(100, 2_001, 50)),
}


def _euros(cents: int) -> Fraction:
    return Fraction(cents, 100)


def _money_task(topic: Topic, text: str, result: Fraction) -> TrainerTask:
    solution = f"{text} = {format_money(result)}"
    return _task(topic, text, result, solution, kind=AnswerKind.MONEY)


def _money_addition(topic: Topic, rng: random.Random) -> TrainerTask:
    amounts = _MONEY_SUMS[topic.level]
    a, b = _euros(rng.choice(amounts)), _euros(rng.choice(amounts))
    return _money_task(topic, f"{format_money(a)} + {format_money(b)}", a + b)


def _money_subtraction(topic: Topic, rng: random.Random) -> TrainerTask:
    amounts = _MONEY_SUMS[topic.level]
    a, b = _larger_first(lambda: _euros(rng.choice(amounts)))
    return _money_task(topic, f"{format_money(a)} − {format_money(b)}", a - b)


def _money_division(topic: Topic, rng: random.Random) -> TrainerTask:
    people, shares = _MONEY_SHARES[topic.level]
    divisor, share = rng.choice(people), _euros(rng.choice(shares))
    return _money_task(topic, f"{format_money(share * divisor)} ÷ {divisor}", share)


def _money_percentage(topic: Topic, rng: random.Random) -> TrainerTask:
    percents, bases = _MONEY_PERCENT[topic.level]
    return _percent_task(topic, rng.choice(percents), rng.choice(bases), money=True)


# --- Fractions ---


def _proper(rng: random.Random, bottom: int) -> Fraction:
    """A fraction below 1 in lowest terms with this denominator, e.g. 3/4."""
    tops = [top for top in range(1, bottom) if math.gcd(top, bottom) == 1]
    return Fraction(rng.choice(tops), bottom)


def _lowest_terms(rng: random.Random, low: int, high: int) -> Fraction:
    """Any fraction in lowest terms, also above 1, e.g. 7/4."""
    while True:
        top, bottom = rng.randint(low, high), rng.randint(low, high)
        if math.gcd(top, bottom) == 1:
            return Fraction(top, bottom)


def _fractions_to_add(rng: random.Random, level: str) -> tuple[Fraction, Fraction]:
    if level == "Easy":  # same denominator
        bottom = rng.randint(2, 12)
        return _proper(rng, bottom), _proper(rng, bottom)
    if level == "Medium":  # one denominator is a multiple of the other
        bottom = rng.randint(2, 6)
        return _proper(rng, bottom), _proper(rng, bottom * rng.randint(2, 3))
    first, second = rng.sample(range(2, 10) if level == "Hard" else range(5, 16), 2)
    return _proper(rng, first), _proper(rng, second)


def _fractions_to_multiply(rng: random.Random, level: str) -> tuple[Fraction, Fraction]:
    if level == "Easy":  # a fraction and a whole number
        return _proper(rng, rng.randint(2, 9)), Fraction(rng.randint(2, 9))
    if level == "Medium":
        return _proper(rng, rng.randint(2, 6)), _proper(rng, rng.randint(2, 6))
    if level == "Hard":
        return _proper(rng, rng.randint(5, 12)), _proper(rng, rng.randint(5, 12))
    return _lowest_terms(rng, 2, 12), _lowest_terms(rng, 2, 12)


def _unsimplified(top: int, bottom: int) -> list[str]:
    """['6/8', '3/4'], or only ['3/4'] if there is nothing to simplify."""
    steps = [f"{top}/{bottom}"]
    simplified = format_fraction(Fraction(top, bottom))
    if simplified != steps[0]:
        steps.append(simplified)
    return steps


def _fraction_sum(topic: Topic, a: Fraction, b: Fraction, sign: int) -> TrainerTask:
    symbol = "+" if sign > 0 else "−"
    common = math.lcm(a.denominator, b.denominator)
    a_top = a.numerator * common // a.denominator
    b_top = b.numerator * common // b.denominator

    text = f"{format_fraction(a)} {symbol} {format_fraction(b)}"
    steps = [text]
    if a.denominator != b.denominator:
        steps.append(f"{a_top}/{common} {symbol} {b_top}/{common}")
    steps += _unsimplified(a_top + sign * b_top, common)
    return _task(topic, text, a + sign * b, " = ".join(steps), kind=AnswerKind.FRACTION)


def _fraction_addition(topic: Topic, rng: random.Random) -> TrainerTask:
    a, b = _fractions_to_add(rng, topic.level)
    return _fraction_sum(topic, a, b, sign=1)


def _fraction_subtraction(topic: Topic, rng: random.Random) -> TrainerTask:
    while True:
        a, b = _fractions_to_add(rng, topic.level)
        if a != b:
            return _fraction_sum(topic, max(a, b), min(a, b), sign=-1)


def _fraction_multiplication(topic: Topic, rng: random.Random) -> TrainerTask:
    a, b = _fractions_to_multiply(rng, topic.level)
    text = f"{format_fraction(a)} × {format_fraction(b)}"
    steps = [text, *_unsimplified(a.numerator * b.numerator, a.denominator * b.denominator)]
    return _task(topic, text, a * b, " = ".join(steps), kind=AnswerKind.FRACTION)


def _fraction_division(topic: Topic, rng: random.Random) -> TrainerTask:
    a, b = _fractions_to_multiply(rng, topic.level)
    text = f"{format_fraction(a)} ÷ {format_fraction(b)}"
    steps = [
        text,
        f"{format_fraction(a)} × {format_fraction(1 / b)}",  # multiply by the reciprocal
        *_unsimplified(a.numerator * b.denominator, a.denominator * b.numerator),
    ]
    return _task(topic, text, a / b, " = ".join(steps), kind=AnswerKind.FRACTION)


# --- Special training: word problems ---

# The numbers come from the MB R1 rules of the chosen level. Units such as km
# and € are used where a number can be 1, so the sentence never reads "1 apples".
_WORD_PROBLEMS = {
    "Addition": (
        "A market stall sells {a} kg of apples in the morning and {b} kg in the "
        "afternoon. How many kg does it sell in total?",
        "A cyclist rides {a} km on Saturday and {b} km on Sunday. How many km is that altogether?",
        "You have €{a} and earn €{b} more. How many € do you have now?",
    ),
    "Subtraction": (
        "A hike is {a} km long. You have walked {b} km. How many km are left?",
        "You have €{a} and spend €{b}. How many € are left?",
        "A tank holds {a} l of water. {b} l are used. How many l are left?",
    ),
    "Multiplication": (
        "A box holds {b} pencils. How many pencils are in {a} boxes?",
        "One ticket costs €{b}. How many € do {a} tickets cost?",
        "A hall has {a} rows of {b} chairs. How many chairs are there?",
    ),
    "Division": (
        "{a} sweets are shared equally among {b} children. How many sweets does each child get?",
        "{a} bottles are packed into crates of {b}. How many crates are filled?",
        "A {a} km trip is split into {b} equal stages. How many km is each stage?",
    ),
}


def _word_problem(topic: Topic, rng: random.Random) -> TrainerTask:
    task = tasks.generate_task(tasks.RANDOM, topic.level, rng)
    template = rng.choice(_WORD_PROBLEMS[task.operation])
    text = template.format(a=f"{task.a:,}", b=f"{task.b:,}")
    solution = f"{task.text} = {task.answer:,}"
    return _task(topic, text, task.answer, solution, prompt="Read and calculate")


# --- Special training: mixed tasks ---

# Each pattern returns (text, answer, solution), or None if the numbers it drew
# would give a result below 1. The generator then simply draws again.
_Mixed = tuple[str, int, str] | None


def _draw(rng: random.Random, count: int, low: int, high: int) -> list[int]:
    return [rng.randint(low, high) for _ in range(count)]


def _sum_then_product(rng: random.Random) -> _Mixed:
    a, b, c = _draw(rng, 3, 2, 9)
    return f"{a} + {b} × {c}", a + b * c, f"First {b} × {c} = {b * c}, then {a} + {b * c} = {a + b * c}"


def _product_then_sum(rng: random.Random) -> _Mixed:
    a, b, c = _draw(rng, 3, 2, 9)
    return f"{a} × {b} + {c}", a * b + c, f"First {a} × {b} = {a * b}, then {a * b} + {c} = {a * b + c}"


def _product_then_difference(rng: random.Random) -> _Mixed:
    a, b, c = _draw(rng, 3, 2, 9)
    if a * b <= c:
        return None
    return f"{a} × {b} − {c}", a * b - c, f"First {a} × {b} = {a * b}, then {a * b} − {c} = {a * b - c}"


def _bracket_sum_times(rng: random.Random) -> _Mixed:
    (a, b), c = _draw(rng, 2, 2, 19), rng.randint(2, 9)
    total = a + b
    solution = f"Brackets first: {a} + {b} = {total}, then {total} × {c} = {total * c}"
    return f"({a} + {b}) × {c}", total * c, solution


def _bracket_difference_times(rng: random.Random) -> _Mixed:
    (a, b), c = _draw(rng, 2, 2, 19), rng.randint(2, 9)
    if a <= b:
        return None
    rest = a - b
    solution = f"Brackets first: {a} − {b} = {rest}, then {rest} × {c} = {rest * c}"
    return f"({a} − {b}) × {c}", rest * c, solution


def _minus_product(rng: random.Random) -> _Mixed:
    (b, c), result = _draw(rng, 2, 2, 9), rng.randint(1, 19)
    a = b * c + result
    return f"{a} − {b} × {c}", result, f"First {b} × {c} = {b * c}, then {a} − {b * c} = {result}"


def _quotient_then_sum(rng: random.Random) -> _Mixed:
    (b, quotient), c = _draw(rng, 2, 2, 9), rng.randint(2, 19)
    a = b * quotient
    solution = f"First {a} ÷ {b} = {quotient}, then {quotient} + {c} = {quotient + c}"
    return f"{a} ÷ {b} + {c}", quotient + c, solution


def _two_products(rng: random.Random, sign: int, first: tuple[int, int] = (2, 12)) -> _Mixed:
    a = rng.randint(*first)
    b, c, d = _draw(rng, 3, 2, 12 if first == (2, 12) else 9)
    result = a * b + sign * c * d
    if result < 1:
        return None
    symbol = "+" if sign > 0 else "−"
    solution = (
        f"First {a} × {b} = {a * b} and {c} × {d} = {c * d}, "
        f"then {a * b} {symbol} {c * d} = {result}"
    )
    return f"{a} × {b} {symbol} {c} × {d}", result, solution


def _two_bracket_sums(rng: random.Random) -> _Mixed:
    a, b, c, d = _draw(rng, 4, 2, 12)
    left, right = a + b, c + d
    solution = f"Brackets first: {a} + {b} = {left} and {c} + {d} = {right}, then {left} × {right} = {left * right}"
    return f"({a} + {b}) × ({c} + {d})", left * right, solution


def _bracket_sum_times_difference(rng: random.Random) -> _Mixed:
    (a, b), c, d = _draw(rng, 2, 11, 29), rng.randint(11, 19), rng.randint(2, 9)
    left, right = a + b, c - d
    solution = f"Brackets first: {a} + {b} = {left} and {c} − {d} = {right}, then {left} × {right} = {left * right}"
    return f"({a} + {b}) × ({c} − {d})", left * right, solution


def _product_plus_quotient(rng: random.Random) -> _Mixed:
    a, quotient = _draw(rng, 2, 11, 19)
    b, d = _draw(rng, 2, 2, 9)
    c = d * quotient
    solution = (
        f"First {a} × {b} = {a * b} and {c} ÷ {d} = {quotient}, "
        f"then {a * b} + {quotient} = {a * b + quotient}"
    )
    return f"{a} × {b} + {c} ÷ {d}", a * b + quotient, solution


_MIXED_PATTERNS = {
    "Easy": (_sum_then_product, _product_then_sum, _product_then_difference),
    "Medium": (_bracket_sum_times, _bracket_difference_times, _minus_product, _quotient_then_sum),
    "Hard": (
        lambda rng: _two_products(rng, sign=1),
        lambda rng: _two_products(rng, sign=-1),
        _two_bracket_sums,
    ),
    "Pro": (
        _bracket_sum_times_difference,
        lambda rng: _two_products(rng, sign=-1, first=(11, 19)),
        _product_plus_quotient,
    ),
}


def _mixed_task(topic: Topic, rng: random.Random) -> TrainerTask:
    while True:
        drawn = rng.choice(_MIXED_PATTERNS[topic.level])(rng)
        if drawn is not None:
            text, answer, solution = drawn
            return _task(topic, text, answer, solution, prompt="Mind the order of operations")


# --- Special training: digit sums ---

_DIGIT_SUM_NUMBERS = {
    "Easy": (10, 99),
    "Medium": (100, 999),
    "Hard": (10_000, 99_999),
    "Pro": (10_000_000, 99_999_999),
}


def _digit_sum(topic: Topic, rng: random.Random) -> TrainerTask:
    number = rng.randint(*_DIGIT_SUM_NUMBERS[topic.level])
    digits = [int(digit) for digit in str(number)]
    solution = f"{' + '.join(str(digit) for digit in digits)} = {sum(digits)}"
    return _task(topic, f"Digit sum of {number:,}", sum(digits), solution, prompt="Add up all digits")


# --- Special training: rule of three ---

_DIRECT_TEMPLATES = (
    "{x} pens cost €{total}. How many € do {y} pens cost?",
    "{x} machines make {total} parts per hour. How many parts do {y} machines make per hour?",
    "A recipe for {x} people needs {total} g of flour. How many g are needed for {y} people?",
)

_INVERSE_TEMPLATES = (
    "{x} workers need {total} days for a job. How many days do {y} workers need?",
    "{x} pumps fill a pool in {total} hours. How many hours do {y} pumps need?",
)

_RULE_OF_THREE = {  # level: (value for one, known amount x, asked amount y)
    "Easy": ((2, 9), (2, 5), (2, 9)),
    "Medium": ((2, 9), (2, 9), (11, 20)),
    "Hard": ((11, 19), (2, 9), (11, 29)),
}


def _rule_of_three(topic: Topic, rng: random.Random) -> TrainerTask:
    if topic.level == "Pro":
        return _inverse_rule_of_three(topic, rng)

    unit_limits, x_limits, y_limits = _RULE_OF_THREE[topic.level]
    unit = rng.randint(*unit_limits)
    while True:
        x, y = rng.randint(*x_limits), rng.randint(*y_limits)
        if x != y:
            break
    total, answer = unit * x, unit * y
    text = rng.choice(_DIRECT_TEMPLATES).format(x=x, y=y, total=f"{total:,}")
    solution = f"For 1: {total:,} ÷ {x} = {unit}. For {y}: {unit} × {y} = {answer:,}"
    return _task(topic, text, answer, solution, prompt="Read and calculate")


def _inverse_rule_of_three(topic: Topic, rng: random.Random) -> TrainerTask:
    """More workers need less time. x × days stays the same."""
    group, time_unit = rng.randint(1, 4), rng.randint(1, 6)
    m, n = rng.sample(range(2, 6), 2)
    x, y = group * m, group * n
    x_time, y_time = n * time_unit, m * time_unit  # so that x × x_time = y × y_time
    work = x * x_time
    text = rng.choice(_INVERSE_TEMPLATES).format(x=x, y=y, total=x_time)
    solution = f"For 1: {x} × {x_time} = {work}. For {y}: {work} ÷ {y} = {y_time}"
    return _task(topic, text, y_time, solution, prompt="Read and calculate")


# --- Special training: equations ---


def _equation(topic: Topic, rng: random.Random) -> TrainerTask:
    text, x, solution = rng.choice(_EQUATION_PATTERNS[topic.level])(rng)
    return _task(topic, text, x, solution, prompt="Solve for x")


def _x_plus(rng: random.Random) -> tuple[str, int, str]:
    x, a = _draw(rng, 2, 1, 19)
    text = rng.choice((f"x + {a} = {x + a}", f"{a} + x = {x + a}"))
    return text, x, f"x = {x + a} − {a} = {x}"


def _x_minus(rng: random.Random) -> tuple[str, int, str]:
    b, a = _draw(rng, 2, 1, 19)
    x = a + b
    return f"x − {a} = {b}", x, f"x = {b} + {a} = {x}"


def _x_times(rng: random.Random) -> tuple[str, int, str]:
    a, x = rng.randint(2, 9), rng.randint(2, 12)
    return f"{a}x = {a * x}", x, f"x = {a * x} ÷ {a} = {x}"


def _x_divided(rng: random.Random) -> tuple[str, int, str]:
    a, b = rng.randint(2, 9), rng.randint(2, 12)
    return f"x ÷ {a} = {b}", a * b, f"x = {b} × {a} = {a * b}"


def _two_steps(rng: random.Random) -> tuple[str, int, str]:
    a, x, b = rng.randint(2, 9), rng.randint(2, 12), rng.randint(1, 20)
    product = a * x
    if rng.random() < 0.5 or product <= b:
        c = product + b
        return f"{a}x + {b} = {c}", x, f"{a}x = {c} − {b} = {product}, so x = {product} ÷ {a} = {x}"
    c = product - b
    return f"{a}x − {b} = {c}", x, f"{a}x = {c} + {b} = {product}, so x = {product} ÷ {a} = {x}"


def _x_on_both_sides(rng: random.Random) -> tuple[str, int, str]:
    x, c, more, b = rng.randint(2, 12), rng.randint(2, 8), rng.randint(1, 6), rng.randint(1, 20)
    a = c + more
    d = more * x + b
    text = f"{a}x + {b} = {c}x + {d}"
    if more == 1:
        return text, x, f"{a}x − {c}x = x, so x = {d} − {b} = {x}"
    solution = f"{a}x − {c}x = {more}x = {d} − {b} = {d - b}, so x = {d - b} ÷ {more} = {x}"
    return text, x, solution


def _x_in_brackets(rng: random.Random) -> tuple[str, int, str]:
    a, x, b = rng.randint(2, 9), rng.randint(1, 12), rng.randint(1, 9)
    c = a * (x + b)
    solution = f"x + {b} = {c} ÷ {a} = {x + b}, so x = {x + b} − {b} = {x}"
    return f"{a}(x + {b}) = {c}", x, solution


_EQUATION_PATTERNS = {
    "Easy": (_x_plus, _x_minus),
    "Medium": (_x_times, _x_divided),
    "Hard": (_two_steps,),
    "Pro": (_x_on_both_sides, _x_in_brackets),
}


# --- Special training: chain calculations ---

CHAIN_MAXIMUM = 9_999

_CHAINS = {  # level: (steps, symbols, start, numbers to add or subtract, highest factor)
    "Easy": (3, "+−", (5, 20), (2, 9), 0),
    "Medium": (4, "+−×", (5, 20), (2, 19), 5),
    "Hard": (5, "+−×÷", (10, 50), (2, 29), 9),
    "Pro": (7, "+−×÷", (20, 99), (11, 99), 12),
}

_OPPOSITE = {"+": "−", "−": "+", "×": "÷", "÷": "×"}


def _chain_step(
    rng: random.Random,
    value: int,
    symbols: str,
    amounts: tuple[int, int],
    highest_factor: int,
    undo: tuple[str, int] | None,
) -> tuple[str, int]:
    """Choose one step that keeps the value a whole number from 1 to CHAIN_MAXIMUM."""
    low, high = amounts
    for _ in range(20):
        symbol = rng.choice(symbols)
        if symbol == "+":
            numbers = range(low, min(high, CHAIN_MAXIMUM - value) + 1)
        elif symbol == "−":
            numbers = range(low, min(high, value - 1) + 1)
        elif symbol == "×":
            numbers = range(2, min(highest_factor, CHAIN_MAXIMUM // value) + 1)
        else:
            numbers = [n for n in range(2, highest_factor + 1) if value % n == 0 and n < value]
        if numbers:
            step = (symbol, rng.choice(numbers))
            if step != undo:  # "+ 5" straight after "− 5" would be pointless
                return step
    return "+", low  # always possible: the value stays far below the maximum


def _apply(value: int, symbol: str, number: int) -> int:
    if symbol == "+":
        return value + number
    if symbol == "−":
        return value - number
    if symbol == "×":
        return value * number
    return value // number


def _chain(topic: Topic, rng: random.Random) -> TrainerTask:
    steps, symbols, start_limits, amounts, highest_factor = _CHAINS[topic.level]
    value = rng.randint(*start_limits)
    text_parts, solution_parts = [f"{value:,}"], []
    undo = None
    for _ in range(steps):
        symbol, number = _chain_step(rng, value, symbols, amounts, highest_factor, undo)
        result = _apply(value, symbol, number)
        text_parts.append(f"{symbol} {number}")
        solution_parts.append(f"{value:,} {symbol} {number} = {result:,}")
        undo = (_OPPOSITE[symbol], number)
        value = result
    text = f"{text_parts[0]} {' → '.join(text_parts[1:])}"
    solution = " → ".join(solution_parts)
    return _task(topic, text, value, solution, prompt="Calculate step by step, from left to right")


# --- Special training: fun with fractions ---

_SIMPLIFY = {  # level: (denominators of the simplified fraction, common factors)
    "Easy": ((2, 6), (2, 5)),
    "Medium": ((2, 10), (2, 9)),
    "Hard": ((3, 15), (6, 12)),
    "Pro": ((5, 25), (11, 19)),
}

_GCD = {  # level: (greatest common divisors, what is left of each number)
    "Easy": ((2, 6), (1, 5)),
    "Medium": ((2, 12), (2, 7)),
    "Hard": ((6, 20), (2, 9)),
    "Pro": ((11, 30), (3, 12)),
}

_LCM = {"Easy": (2, 10), "Medium": (4, 15), "Hard": (6, 25), "Pro": (12, 40)}


def _simplify(topic: Topic, rng: random.Random) -> TrainerTask:
    bottoms, factors = _SIMPLIFY[topic.level]
    simplified = _proper(rng, rng.randint(*bottoms))
    factor = rng.randint(*factors)
    text = f"{simplified.numerator * factor}/{simplified.denominator * factor}"
    solution = f"Divide top and bottom by {factor}: {text} = {format_fraction(simplified)}"
    return _task(
        topic, text, simplified, solution, kind=AnswerKind.FRACTION, prompt="Simplify the fraction"
    )


def _gcd(topic: Topic, rng: random.Random) -> TrainerTask:
    divisors, rests = _GCD[topic.level]
    divisor = rng.randint(*divisors)
    while True:
        m, n = rng.randint(*rests), rng.randint(*rests)
        if m != n and math.gcd(m, n) == 1:
            break
    a, b = divisor * m, divisor * n
    solution = f"{a} = {divisor} × {m} and {b} = {divisor} × {n}, so the GCD is {divisor}"
    return _task(
        topic, f"GCD of {a} and {b}", divisor, solution, prompt="Find the greatest common divisor"
    )


def _lcm(topic: Topic, rng: random.Random) -> TrainerTask:
    a, b = rng.sample(range(_LCM[topic.level][0], _LCM[topic.level][1] + 1), 2)
    divisor, multiple = math.gcd(a, b), math.lcm(a, b)
    if divisor == 1:
        solution = f"{a} and {b} share no factor, so the LCM is {a} × {b} = {multiple:,}"
    else:
        solution = f"The GCD is {divisor}, so the LCM is {a} × {b} ÷ {divisor} = {multiple:,}"
    return _task(
        topic, f"LCM of {a} and {b}", multiple, solution, prompt="Find the least common multiple"
    )


def _fun_with_fractions(topic: Topic, rng: random.Random) -> TrainerTask:
    return rng.choice((_simplify, _gcd, _lcm))(topic, rng)


# --- Generating a task ---

_GENERATORS: dict[tuple[str, str], Callable[[Topic, random.Random], TrainerTask]] = {
    (NATURAL, "Addition"): _basic,
    (NATURAL, "Subtraction"): _basic,
    (NATURAL, "Multiplication"): _basic,
    (NATURAL, "Division"): _basic,
    (NATURAL, "Percentage"): _percentage,
    (NATURAL, "Square"): _square,
    (NATURAL, "Square root"): _square_root,
    (DECIMALS, "Addition"): _decimal_addition,
    (DECIMALS, "Subtraction"): _decimal_subtraction,
    (DECIMALS, "Multiplication"): _decimal_multiplication,
    (DECIMALS, "Division"): _decimal_division,
    (LARGE, "Addition"): _large_addition,
    (LARGE, "Subtraction"): _large_subtraction,
    (LARGE, "Multiplication"): _large_multiplication,
    (LARGE, "Division"): _large_division,
    (LARGE, "Percentage"): _large_percentage,
    (MONEY, "Addition"): _money_addition,
    (MONEY, "Subtraction"): _money_subtraction,
    (MONEY, "Division"): _money_division,
    (MONEY, "Percentage"): _money_percentage,
    (FRACTIONS, "Addition"): _fraction_addition,
    (FRACTIONS, "Subtraction"): _fraction_subtraction,
    (FRACTIONS, "Multiplication"): _fraction_multiplication,
    (FRACTIONS, "Division"): _fraction_division,
    (SPECIAL, "Word problems"): _word_problem,
    (SPECIAL, "Mixed tasks"): _mixed_task,
    (SPECIAL, "Digit sums"): _digit_sum,
    (SPECIAL, "Rule of three"): _rule_of_three,
    (SPECIAL, "Equations"): _equation,
    (SPECIAL, "Chain calculations"): _chain,
    (SPECIAL, "Fun with fractions"): _fun_with_fractions,
}


def is_valid_topic(topic: Topic) -> bool:
    return (topic.group, topic.name) in _GENERATORS and topic.level in LEVELS


def generate_task(
    topics: Sequence[Topic], rng: random.Random, previous: TrainerTask | None = None
) -> TrainerTask:
    """Return a new task for one of `topics`, different from `previous` (MB R2)."""
    if not topics:
        raise ValueError("At least one topic is needed")
    for topic in topics:
        if not is_valid_topic(topic):
            raise ValueError(f"Unknown topic: {topic!r}")

    while True:
        topic = rng.choice(topics)
        task = _GENERATORS[(topic.group, topic.name)](topic, rng)
        if previous is None or task.text != previous.text:
            return task
'''

####################################################################################################
# trainer.py
####################################################################################################

FILES['trainer.py'] = r'''"""Trainer session rules: settings, modes, time limits and results (spec 002).

Like runs.py, this module never reads the clock. The current time is passed in
as `now`, so tests can use fixed times.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from runs import accuracy
from trainer_tasks import (
    NATURAL,
    NUMBER_TYPES,
    SPECIAL,
    Check,
    Topic,
    TrainerTask,
    check_answer,
    format_answer,
    is_valid_topic,
)

OPERATIONS_CATEGORY = "Operations"
NUMBER_TYPES_CATEGORY = "Number types"
SPECIAL_CATEGORY = "Special trainings"
CATEGORIES = (OPERATIONS_CATEGORY, NUMBER_TYPES_CATEGORY, SPECIAL_CATEGORY)

COUNTDOWN_SECONDS = 3


# StrEnum, and always compared with == rather than `is`, for the same reason
# as in runs.py: Streamlit re-imports a module when its source changes.
class Mode(StrEnum):
    TASK_COUNT = "Task count"
    TOTAL_TIME = "Total time"
    TIME_PER_TASK = "Time per task"


# Lowest and highest limit per mode, inclusive: tasks for TASK_COUNT, seconds otherwise.
LIMITS = {
    Mode.TASK_COUNT: (5, 100),
    Mode.TOTAL_TIME: (30, 900),
    Mode.TIME_PER_TASK: (1, 60),
}


class Status(StrEnum):
    RUNNING = "running"
    FINISHED = "finished"
    ABORTED = "aborted"


class EndReason(StrEnum):
    ALL_TASKS_DONE = "all_tasks_done"
    TIME_UP = "time_up"  # the total time ran out
    TOO_SLOW = "too_slow"  # one task took longer than the time per task
    ABORTED = "aborted"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    SKIPPED = "skipped"
    IGNORED = "ignored"
    TIME_UP = "time_up"


class SettingsError(ValueError):
    """The chosen settings are not allowed. The message can be shown to the user."""


@dataclass(frozen=True)
class Settings:
    category: str  # one of CATEGORIES
    name: str  # what was picked in the category, e.g. "Percentage" or "Decimals"
    topics: tuple[Topic, ...]
    mode: Mode
    limit: int  # tasks for TASK_COUNT, seconds otherwise


@dataclass(frozen=True)
class Attempt:
    """One answered or skipped task, kept for the review after the session."""

    text: str
    given: str  # what the user typed, empty for a skip
    answer: str  # the correct answer as it is shown
    solution: str
    outcome: Outcome  # CORRECT, WRONG or SKIPPED
    seconds: float


@dataclass(frozen=True)
class Session:
    settings: Settings
    started_at: datetime
    task_started_at: datetime
    attempts: tuple[Attempt, ...] = ()
    status: Status = Status.RUNNING
    end_reason: EndReason | None = None
    ended_at: datetime | None = None

    # The totals are counted from the attempts and never stored separately.
    @property
    def correct(self) -> int:
        return self._count(Outcome.CORRECT)

    @property
    def wrong(self) -> int:
        return self._count(Outcome.WRONG)

    @property
    def skipped(self) -> int:
        return self._count(Outcome.SKIPPED)

    def _count(self, outcome: Outcome) -> int:
        return sum(1 for attempt in self.attempts if attempt.outcome == outcome)


@dataclass(frozen=True)
class Summary:
    correct: int
    wrong: int
    skipped: int
    accuracy: float | None
    duration_seconds: float
    average_seconds: float | None  # per answered or skipped task


@dataclass(frozen=True)
class SavedSession:
    id: str
    category: str
    name: str
    levels: str
    mode: str
    limit: int
    finished_at: datetime
    duration_seconds: float
    correct: int
    wrong: int
    skipped: int


# --- Settings ---


def make_settings(
    category: str, name: str, topics: Sequence[Topic], mode: str, limit: int
) -> Settings:
    """Check the user's choices. Raises SettingsError and starts nothing if one is not allowed."""
    if category not in CATEGORIES:
        raise SettingsError(f"Unknown category: {category}")
    topics = tuple(topics)
    if not topics:
        raise SettingsError("Select at least one operation.")
    if not all(is_valid_topic(topic) for topic in topics):
        raise SettingsError("Unknown operation, training or level.")
    if len({(topic.group, topic.name) for topic in topics}) != len(topics):
        raise SettingsError("Each operation can only be selected once.")

    # The three categories differ in what may be combined (product brief, R2 and R3).
    one_topic = len(topics) == 1 and topics[0].name == name
    if category == OPERATIONS_CATEGORY and not (one_topic and topics[0].group == NATURAL):
        raise SettingsError("Operations trains exactly one operation.")
    if category == SPECIAL_CATEGORY and not (one_topic and topics[0].group == SPECIAL):
        raise SettingsError("Special trainings trains exactly one training.")
    if category == NUMBER_TYPES_CATEGORY and not (
        name in NUMBER_TYPES and all(topic.group == name for topic in topics)
    ):
        raise SettingsError("All operations must belong to the chosen number type.")

    try:
        mode = Mode(mode)
    except ValueError:
        raise SettingsError(f"Unknown mode: {mode}") from None
    low, high = LIMITS[mode]
    # `type(...) is int` also rejects True and 10.0, which would pass a plain comparison.
    if type(limit) is not int or not low <= limit <= high:
        raise SettingsError(f"{mode}: choose a whole number from {low} to {high}.")

    return Settings(category, name, topics, mode, limit)


def levels_text(settings: Settings) -> str:
    """'Easy' for one topic, 'Addition Easy, Division Hard' for several."""
    if len(settings.topics) == 1:
        return settings.topics[0].level
    return ", ".join(f"{topic.name} {topic.level}" for topic in settings.topics)


# --- Time ---


def start_session(settings: Settings, now: datetime) -> Session:
    """Start a session at `now`, which is after the countdown."""
    return Session(settings, started_at=now, task_started_at=now)


def _deadline(session: Session) -> datetime | None:
    limit = timedelta(seconds=session.settings.limit)
    if session.settings.mode == Mode.TOTAL_TIME:
        return session.started_at + limit
    if session.settings.mode == Mode.TIME_PER_TASK:
        return session.task_started_at + limit
    return None  # a task count never runs out of time


def is_time_up(session: Session, now: datetime) -> bool:
    deadline = _deadline(session)
    return deadline is not None and now >= deadline


def remaining_seconds(session: Session, now: datetime) -> float | None:
    """Seconds left in total or for the current task. None if the mode has no time limit."""
    deadline = _deadline(session)
    if deadline is None:
        return None
    return max(0.0, (deadline - now).total_seconds())


def elapsed_seconds(session: Session, now: datetime) -> float:
    end = session.ended_at or now
    return max(0.0, (end - session.started_at).total_seconds())


def _expire(session: Session) -> Session:
    """End the session at its deadline, however late the app noticed it."""
    too_slow = session.settings.mode == Mode.TIME_PER_TASK
    return replace(
        session,
        status=Status.FINISHED,
        end_reason=EndReason.TOO_SLOW if too_slow else EndReason.TIME_UP,
        ended_at=_deadline(session),
    )


# --- Answers ---


def _record(
    session: Session, task: TrainerTask, given: str, outcome: Outcome, now: datetime
) -> Session:
    attempt = Attempt(
        text=task.text,
        given=given,
        answer=format_answer(task),
        solution=task.solution,
        outcome=outcome,
        seconds=(now - session.task_started_at).total_seconds(),
    )
    session = replace(session, attempts=(*session.attempts, attempt), task_started_at=now)

    all_done = (
        session.settings.mode == Mode.TASK_COUNT
        and len(session.attempts) >= session.settings.limit
    )
    if all_done:
        session = replace(
            session, status=Status.FINISHED, end_reason=EndReason.ALL_TASKS_DONE, ended_at=now
        )
    return session


def submit_answer(
    session: Session, task: TrainerTask, raw: str, now: datetime
) -> tuple[Session, Outcome]:
    if session.status != Status.RUNNING:
        return session, Outcome.IGNORED
    if is_time_up(session, now):
        return _expire(session), Outcome.TIME_UP

    check = check_answer(task, raw)
    if check == Check.INVALID:  # MB R3: not evaluated, and the clock keeps running
        return session, Outcome.IGNORED
    outcome = Outcome.CORRECT if check == Check.CORRECT else Outcome.WRONG
    return _record(session, task, raw.strip(), outcome, now), outcome


def skip_task(session: Session, task: TrainerTask, now: datetime) -> tuple[Session, Outcome]:
    if session.status != Status.RUNNING:
        return session, Outcome.IGNORED
    if is_time_up(session, now):
        return _expire(session), Outcome.TIME_UP
    return _record(session, task, "", Outcome.SKIPPED, now), Outcome.SKIPPED


def abort_session(session: Session, now: datetime) -> Session:
    """Abort a running session. One whose time was already up counts as finished."""
    if session.status != Status.RUNNING:
        return session
    if is_time_up(session, now):
        return _expire(session)
    return replace(session, status=Status.ABORTED, end_reason=EndReason.ABORTED, ended_at=now)


def finish_if_expired(session: Session, now: datetime) -> Session:
    if session.status == Status.RUNNING and is_time_up(session, now):
        return _expire(session)
    return session


# --- Result ---


def summarize(session: Session) -> Summary:
    seconds = [attempt.seconds for attempt in session.attempts]
    return Summary(
        correct=session.correct,
        wrong=session.wrong,
        skipped=session.skipped,
        accuracy=accuracy(session.correct, session.wrong, session.skipped),
        duration_seconds=elapsed_seconds(session, session.ended_at or session.started_at),
        average_seconds=sum(seconds) / len(seconds) if seconds else None,
    )


def format_duration(seconds: float) -> str:
    """75.4 -> '1:15'."""
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}:{rest:02d}"


def limit_text(mode: str, limit: int) -> str:
    """The mode and its limit in a few words, e.g. '10 tasks'."""
    if mode == Mode.TASK_COUNT:
        return f"{limit} tasks"
    if mode == Mode.TOTAL_TIME:
        return f"{format_duration(limit)} min in total"
    return f"{limit} s per task"
'''

####################################################################################################
# trainer_db.py
####################################################################################################

FILES['trainer_db.py'] = r'''"""SQLite storage of finished trainer sessions.

Uses the same database file and connection handling as db.py, but its own
table, so the storage of test runs stays untouched.
"""

from contextlib import closing
from datetime import datetime, timezone

import db
from trainer import SavedSession, Session, Status, levels_text, summarize


def init_db() -> None:
    with closing(db.connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trainer_sessions (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                levels TEXT NOT NULL,
                mode TEXT NOT NULL,
                limit_value INTEGER NOT NULL,
                finished_at TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                correct INTEGER NOT NULL,
                wrong INTEGER NOT NULL,
                skipped INTEGER NOT NULL
            )
            """
        )


def save_session(session_id: str, session: Session) -> None:
    """Save a finished session. Saving the same id again changes nothing.

    A running or aborted session is refused, so it can never reach the history.
    """
    if session.status != Status.FINISHED or session.ended_at is None:
        raise ValueError("Only a finished session can be saved")

    summary = summarize(session)
    settings = session.settings
    with closing(db.connect()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO trainer_sessions "
            "(id, category, name, levels, mode, limit_value, finished_at, "
            "duration_seconds, correct, wrong, skipped) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                settings.category,
                settings.name,
                levels_text(settings),
                str(settings.mode),
                settings.limit,
                session.ended_at.astimezone(timezone.utc).isoformat(),
                summary.duration_seconds,
                summary.correct,
                summary.wrong,
                summary.skipped,
            ),
        )


def list_sessions(limit: int | None = None) -> list[SavedSession]:
    """Finished sessions, newest first. `limit` keeps only the newest ones."""
    query = (
        "SELECT id, category, name, levels, mode, limit_value, finished_at, "
        "duration_seconds, correct, wrong, skipped "
        "FROM trainer_sessions ORDER BY finished_at DESC, id"
    )
    parameters: tuple[int, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        parameters = (limit,)

    with closing(db.connect()) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [
        SavedSession(
            id=row[0],
            category=row[1],
            name=row[2],
            levels=row[3],
            mode=row[4],
            limit=row[5],
            finished_at=datetime.fromisoformat(row[6]),
            duration_seconds=row[7],
            correct=row[8],
            wrong=row[9],
            skipped=row[10],
        )
        for row in rows
    ]
'''

####################################################################################################
# trainer_ui.py
####################################################################################################

FILES['trainer_ui.py'] = r'''"""Trainer: Streamlit screens only. The rules live in trainer.py and trainer_tasks.py.

app.py calls `render()` to show the Trainer and `leave()` when the user
switches to another section. Everything this file keeps in st.session_state
starts with "tr_", so it cannot clash with the Tests screen in app.py.
"""

import math
import random
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import trainer_db
from tasks import LEVELS
from trainer import (
    CATEGORIES,
    COUNTDOWN_SECONDS,
    LIMITS,
    NUMBER_TYPES_CATEGORY,
    OPERATIONS_CATEGORY,
    EndReason,
    Mode,
    Outcome,
    Session,
    SettingsError,
    Status,
    abort_session,
    elapsed_seconds,
    finish_if_expired,
    format_duration,
    is_time_up,
    levels_text,
    limit_text,
    make_settings,
    remaining_seconds,
    skip_task,
    start_session,
    submit_answer,
    summarize,
)
from trainer_tasks import (
    ANSWER_HINTS,
    DECIMALS,
    FRACTIONS,
    LARGE,
    MONEY,
    NATURAL,
    NUMBER_TYPES,
    OPERATIONS,
    SPECIAL,
    SPECIAL_TRAININGS,
    AnswerKind,
    Topic,
    generate_task,
)

NO_VALUE = "–"
FLASH_COLORS = {Outcome.CORRECT: "rgb(22, 163, 74)", Outcome.WRONG: "rgb(220, 38, 38)"}
FLASH_MS = 700
LONG_TASK_LENGTH = 40  # longer tasks, such as word problems, use a smaller heading
HISTORY_LENGTH = 10
EXAMPLE_SEED = 7  # a fixed seed, so the example does not change on every rerun

NUMBER_TYPE_NOTES = {
    NATURAL: "Whole numbers. Type answers as whole numbers.",
    DECIMALS: "Numbers with one or two decimals. Type answers with a point, e.g. 12.5.",
    LARGE: "Thousands and millions. Type answers without separators, e.g. 4250000.",
    MONEY: "Amounts in euros and cents. Type answers like 12.50.",
    FRACTIONS: "Type answers as a fraction in lowest terms, e.g. 3/4, or as a whole number.",
}

SPECIAL_NOTES = {
    "Word problems": "Short everyday stories that hide one calculation.",
    "Mixed tasks": "Several operations in one task. Brackets first, then × and ÷, then + and −.",
    "Digit sums": "Add up all the digits of a number.",
    "Rule of three": "Work out the value for one, then for the amount that is asked.",
    "Equations": "Find the number that x stands for.",
    "Chain calculations": "Carry one result through a chain of steps.",
    "Fun with fractions": "Simplify fractions and find the GCD and the LCM.",
}

MODE_NOTES = {
    Mode.TASK_COUNT: "A fixed number of tasks. The time is measured but does not run out.",
    Mode.TOTAL_TIME: "Solve as many tasks as you can before the time runs out.",
    Mode.TIME_PER_TASK: "Every task has its own time limit. "
    "The session ends when one task takes too long.",
}

LIMIT_INPUTS = {  # mode: (label, key, value at the start, step of the + and − buttons)
    Mode.TASK_COUNT: ("Number of tasks", "tr_limit_tasks", 10, 5),
    Mode.TOTAL_TIME: ("Total time in seconds", "tr_limit_total", 120, 30),
    Mode.TIME_PER_TASK: ("Seconds per task", "tr_limit_per_task", 10, 1),
}

PLACEHOLDERS = {
    AnswerKind.WHOLE: "Whole number",
    AnswerKind.DECIMAL: "Decimal, e.g. 12.5",
    AnswerKind.MONEY: "Amount, e.g. 12.50",
    AnswerKind.FRACTION: "Fraction, e.g. 3/4",
}

END_MESSAGES = {
    EndReason.ALL_TASKS_DONE: "All tasks done.",
    EndReason.TIME_UP: "Time's up.",
    EndReason.TOO_SLOW: "The last task took too long, so the session ended.",
}

RESULT_WORDS = {Outcome.CORRECT: "Correct", Outcome.WRONG: "Wrong", Outcome.SKIPPED: "Skipped"}

state = st.session_state


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _percent(value: float | None) -> str:
    return NO_VALUE if value is None else f"{value:.1%}"


# --- Changing screens ---


def _begin() -> None:
    settings = state.tr_settings
    state.tr_session = start_session(settings, _utc_now())
    state.tr_session_id = str(uuid.uuid4())
    state.tr_rng = random.Random()
    state.tr_task = generate_task(settings.topics, state.tr_rng)
    state.tr_feedback = None
    state.tr_flash = None
    state.tr_show_hint = False
    state.tr_attempt = 0
    state.tr_phase = "running"


def _clear_session() -> None:
    for name in (
        "tr_session",
        "tr_session_id",
        "tr_rng",
        "tr_task",
        "tr_feedback",
        "tr_flash",
        "tr_show_hint",
    ):
        state.pop(name, None)
    state.tr_phase = "setup"


def _finish(session: Session) -> None:
    """Save the session and prepare the result. Safe to repeat for the same session."""
    trainer_db.save_session(state.tr_session_id, session)
    # When the time ran out, the task on screen was never answered.
    unanswered = None if session.end_reason == EndReason.ALL_TASKS_DONE else state.tr_task
    state.tr_result = {"session": session, "unanswered": unanswered}
    _clear_session()
    state.tr_phase = "result"


def _apply(session: Session, outcome: Outcome) -> None:
    state.tr_attempt += 1  # the flash and the focus script run again for every attempt
    state.tr_session = session
    if session.status == Status.FINISHED:
        _finish(session)
        return

    state.tr_show_hint = outcome == Outcome.IGNORED
    state.tr_flash = outcome if outcome in FLASH_COLORS else None
    if outcome != Outcome.IGNORED:
        state.tr_feedback = session.attempts[-1]
        state.tr_task = generate_task(
            session.settings.topics, state.tr_rng, previous=state.tr_task
        )


def _end_early(now: datetime) -> None:
    """End the running session: discarded, unless its time was already up."""
    session = abort_session(state.tr_session, now)
    if session.status == Status.FINISHED:
        _finish(session)
    else:
        _clear_session()


def leave() -> None:
    """For app.py: the user switched to another section."""
    if "tr_phase" not in state:
        return
    if state.tr_phase == "running":
        _end_early(_utc_now())
    state.pop("tr_result", None)
    state.tr_phase = "setup"


# --- Callbacks: each one reads the clock first, so the time is as close as
# possible to when the action arrived ---


def _on_submit() -> None:
    now = _utc_now()
    _apply(*submit_answer(state.tr_session, state.tr_task, state.tr_answer, now))


def _on_skip() -> None:
    now = _utc_now()
    _apply(*skip_task(state.tr_session, state.tr_task, now))


def _on_abort() -> None:
    _end_early(_utc_now())


def _on_cancel_countdown() -> None:
    _clear_session()


def _on_train_again() -> None:
    state.tr_settings = state.tr_result["session"].settings
    state.pop("tr_result", None)
    state.tr_phase = "countdown"


def _on_change_settings() -> None:
    state.pop("tr_result", None)
    state.tr_phase = "setup"


# --- Setup screen ---


def _pick(widget, label: str, options, key: str, **options_for_widget) -> str:
    """One choice out of a few. It cannot be empty and is remembered for the session."""
    options = list(options)
    choice = widget(
        label,
        options,
        default=options[0],
        required=True,
        key=key,
        persist_state="session",
        **options_for_widget,
    )
    return choice or options[0]


def _pick_operation() -> tuple[str, list[Topic]]:
    operation = _pick(st.pills, "Operation", OPERATIONS, "tr_operation")
    level = _pick(st.segmented_control, "Level", LEVELS, "tr_level")
    return operation, [Topic(NATURAL, operation, level)]


def _pick_number_type() -> tuple[str, list[Topic]]:
    number_type = _pick(st.pills, "Number type", NUMBER_TYPES, "tr_number_type")
    st.caption(NUMBER_TYPE_NOTES[number_type])
    st.markdown("Operations and their levels")

    topics = []
    for position, operation in enumerate(NUMBER_TYPES[number_type]):
        use_column, level_column = st.columns([1, 2], vertical_alignment="center")
        use = use_column.checkbox(
            operation,
            value=position == 0,
            key=f"tr_use_{number_type}_{operation}",
            persist_state="session",
        )
        level = _pick(
            level_column.segmented_control,
            f"Level for {operation}",
            LEVELS,
            f"tr_level_{number_type}_{operation}",
            label_visibility="collapsed",
            disabled=not use,
        )
        if use:
            topics.append(Topic(number_type, operation, level))
    return number_type, topics


def _pick_special() -> tuple[str, list[Topic]]:
    training = _pick(st.pills, "Training", SPECIAL_TRAININGS, "tr_special")
    st.caption(SPECIAL_NOTES[training])
    level = _pick(st.segmented_control, "Level", LEVELS, "tr_special_level")
    return training, [Topic(SPECIAL, training, level)]


def _pick_mode() -> tuple[str, int]:
    mode = _pick(st.segmented_control, "Mode", [mode.value for mode in Mode], "tr_mode")
    st.caption(MODE_NOTES[mode])
    label, key, value, step = LIMIT_INPUTS[mode]
    low, high = LIMITS[mode]
    limit = st.number_input(
        f"{label} ({low} to {high})",
        min_value=low,
        max_value=high,
        value=value,
        step=step,
        key=key,
        persist_state="session",
    )
    return mode, limit


def _render_example(topics: list[Topic]) -> None:
    if not topics:
        return
    example = generate_task(topics, random.Random(EXAMPLE_SEED))
    with st.container(border=True):
        st.caption(f"Example task · {example.prompt}")
        st.markdown(f"**{example.text}**")


def _render_history() -> None:
    st.subheader("Recent sessions", anchor=False)
    sessions = trainer_db.list_sessions(limit=HISTORY_LENGTH)
    if not sessions:
        st.caption("No finished sessions yet. Sessions you end early are not saved.")
        return
    rows = [
        {
            "Date": saved.finished_at.strftime("%Y-%m-%d"),
            "Training": saved.name,
            "Level": saved.levels,
            "Mode": limit_text(saved.mode, saved.limit),
            "Correct": saved.correct,
            "Wrong": saved.wrong,
            "Skipped": saved.skipped,
            "Time": format_duration(saved.duration_seconds),
        }
        for saved in sessions
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True)


def render_setup() -> None:
    st.header("Trainer", anchor=False)
    st.caption("Practise at your own pace. After a mistake you see how to solve the task.")

    category = _pick(
        st.segmented_control, "Training", CATEGORIES, "tr_category", label_visibility="collapsed"
    )
    if category == OPERATIONS_CATEGORY:
        name, topics = _pick_operation()
    elif category == NUMBER_TYPES_CATEGORY:
        name, topics = _pick_number_type()
    else:
        name, topics = _pick_special()
    _render_example(topics)

    mode, limit = _pick_mode()

    if st.button("Start training", key="tr_start", type="primary"):
        try:
            state.tr_settings = make_settings(category, name, topics, mode, limit)
        except SettingsError as error:  # nothing starts, and the reason is shown
            st.error(str(error))
        else:
            state.tr_phase = "countdown"
            st.rerun()

    _render_history()


# --- Countdown ---


def render_countdown() -> None:
    number = st.empty()
    st.button("Cancel", key="tr_cancel", on_click=_on_cancel_countdown)
    # While this script sleeps, the elements of the previous screen would stay
    # visible below. Empty placeholders overwrite them.
    for _ in range(40):
        st.empty()

    for remaining in range(COUNTDOWN_SECONDS, 0, -1):
        number.header(str(remaining), anchor=False)
        time.sleep(1)

    _begin()
    st.rerun()


# --- Running session ---


@st.fragment(run_every="1s")
def _render_status() -> None:
    """Only this part refreshes every second, so typing is not disturbed."""
    session = state.get("tr_session")
    if session is None:
        return
    now = _utc_now()
    if is_time_up(session, now):
        st.rerun(scope="app")

    settings = session.settings
    task_number = len(session.attempts) + 1
    remaining = remaining_seconds(session, now)
    if settings.mode == Mode.TASK_COUNT:
        shown = {
            "Task": f"{task_number} of {settings.limit}",
            "Time": format_duration(elapsed_seconds(session, now)),
        }
        progress = len(session.attempts) / settings.limit
    elif settings.mode == Mode.TOTAL_TIME:
        shown = {"Time left": format_duration(math.ceil(remaining)), "Task": task_number}
        progress = remaining / settings.limit
    else:
        shown = {"Time left for this task": math.ceil(remaining), "Task": task_number}
        progress = remaining / settings.limit
    shown["Correct"] = session.correct
    shown["Wrong or skipped"] = session.wrong + session.skipped

    for column, (label, value) in zip(st.columns(len(shown)), shown.items()):
        column.metric(label, value)
    st.progress(min(1.0, max(0.0, progress)))


def _render_feedback() -> None:
    """Show how the previous task went. This is where the Trainer teaches."""
    attempt = state.get("tr_feedback")
    if attempt is None:
        return
    if attempt.outcome == Outcome.CORRECT:
        st.success(f"Correct! {attempt.solution}")
    elif attempt.outcome == Outcome.WRONG:
        st.error(
            f"Not quite. You answered **{attempt.given}**, the answer is **{attempt.answer}**."
            f"\n\n{attempt.solution}"
        )
    else:
        st.warning(f"Skipped. The answer is **{attempt.answer}**.\n\n{attempt.solution}")


def _render_flash() -> None:
    color = FLASH_COLORS.get(state.get("tr_flash"))
    if color is None:
        return
    # A new animation name per attempt makes the same colour replay.
    name = f"tr-flash-{state.tr_attempt}"
    st.html(
        f"""<style>
        @keyframes {name} {{
            0%, 60% {{
                background-color: {color};
                border-color: {color};
                box-shadow: 0 0 0 3px {color}, 0 0 18px 6px {color};
            }}
        }}
        .st-key-tr_answer [data-testid="stTextInputRootElement"] {{
            animation: {name} {FLASH_MS}ms ease-out;
        }}
        </style>"""
    )


def _render_focus_script() -> None:
    """Put the cursor back in the answer field. Clicking a button would move it away."""
    st.html(
        f"""<script data-attempt="{state.tr_attempt}">
        requestAnimationFrame(() => {{
            document.querySelector(".st-key-tr_answer input")?.focus();
        }});
        </script>""",
        unsafe_allow_javascript=True,
    )


def render_running() -> None:
    task = state.tr_task
    # The status gets a container of its own. Without it, Streamlit sometimes
    # drops the element that follows a self-refreshing fragment, when the
    # refresh and a submitted answer arrive at the same moment.
    with st.container():
        _render_status()

    st.caption(task.prompt)
    if len(task.text) <= LONG_TASK_LENGTH:
        st.header(task.text, anchor=False)
    else:
        st.subheader(task.text, anchor=False)

    with st.form("tr_answer_form", clear_on_submit=True, border=False):
        st.text_input(
            "Answer", key="tr_answer", autocomplete="off", placeholder=PLACEHOLDERS[task.kind]
        )
        submit_column, skip_column = st.columns(2)
        # Submit comes first, because Enter triggers the first button in a form.
        submit_column.form_submit_button(
            "Submit", key="tr_submit", type="primary", on_click=_on_submit, width="stretch"
        )
        skip_column.form_submit_button(
            "Skip", key="tr_skip", on_click=_on_skip, width="stretch"
        )

    if state.tr_show_hint:
        st.warning(ANSWER_HINTS[task.kind])
    _render_feedback()
    st.button("End training", key="tr_abort", on_click=_on_abort)

    _render_flash()
    _render_focus_script()


# --- Result ---


def _render_review(session: Session) -> None:
    st.subheader("Review", anchor=False)
    if not session.attempts:
        st.caption("No task was answered.")
        return
    rows = [
        {
            "Task": attempt.text,
            "Your answer": attempt.given or NO_VALUE,
            "Correct answer": attempt.answer,
            "Result": RESULT_WORDS[attempt.outcome],
            "Seconds": round(attempt.seconds, 1),
        }
        for attempt in session.attempts
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    missed = [attempt for attempt in session.attempts if attempt.outcome != Outcome.CORRECT]
    if missed:
        st.subheader("How to solve the ones you missed", anchor=False)
        for attempt in missed:
            st.markdown(f"**{attempt.text}**  \n{attempt.solution}")


def render_result() -> None:
    session = state.tr_result["session"]
    unanswered = state.tr_result["unanswered"]
    settings = session.settings
    summary = summarize(session)

    st.header(f"Training finished: {settings.name}", anchor=False)
    st.caption(
        f"{settings.category} · {levels_text(settings)} · "
        f"{limit_text(settings.mode, settings.limit)}"
    )
    st.info(END_MESSAGES[session.end_reason])
    if unanswered is not None:
        st.markdown(f"**Not answered in time:** {unanswered.text}  \n{unanswered.solution}")

    average = summary.average_seconds
    shown = {
        "Correct": summary.correct,
        "Wrong": summary.wrong,
        "Skipped": summary.skipped,
        "Accuracy": _percent(summary.accuracy),
        "Time": format_duration(summary.duration_seconds),
        "Per task": NO_VALUE if average is None else f"{average:.1f} s",
    }
    for column, (label, value) in zip(st.columns(len(shown)), shown.items()):
        column.metric(label, value)

    again_column, change_column = st.columns(2)
    again_column.button(
        "Train again", key="tr_again", type="primary", on_click=_on_train_again, width="stretch"
    )
    change_column.button(
        "Change settings", key="tr_change", on_click=_on_change_settings, width="stretch"
    )

    _render_review(session)


# --- Entry point ---


def render() -> None:
    if "tr_phase" not in state:  # once per browser session
        trainer_db.init_db()
        state.tr_phase = "setup"

    if state.tr_phase == "running":
        session = finish_if_expired(state.tr_session, _utc_now())
        if session.status == Status.FINISHED:
            _finish(session)

    if state.tr_phase == "countdown":
        render_countdown()
    elif state.tr_phase == "running":
        render_running()
    elif state.tr_phase == "result":
        render_result()
    else:
        render_setup()
'''

####################################################################################################
# tests/test_trainer_tasks.py
####################################################################################################

FILES['tests/test_trainer_tasks.py'] = r'''"""Trainer task generation and answer checking (spec 002).

The expected numbers are written out here on purpose and not imported from
trainer_tasks.py, so a wrong table there cannot pass by checking itself. Every
answer is also recalculated from the text of the task, the way a user reads it.
"""

import math
import random
import re
from fractions import Fraction
from pathlib import Path

import pytest

from trainer_tasks import (
    ANSWER_HINTS,
    NUMBER_TYPES,
    SPECIAL,
    SPECIAL_TRAININGS,
    AnswerKind,
    Check,
    Topic,
    TrainerTask,
    check_answer,
    format_answer,
    generate_task,
    is_valid_topic,
    parse_answer,
)

LEVELS = ["Easy", "Medium", "Hard", "Pro"]
ROUND = 1000

# Product brief, R2 and R3.
OFFERED = {
    "Natural numbers": [
        "Addition",
        "Subtraction",
        "Multiplication",
        "Division",
        "Percentage",
        "Square",
        "Square root",
    ],
    "Decimals": ["Addition", "Subtraction", "Multiplication", "Division"],
    "Large numbers": ["Addition", "Subtraction", "Multiplication", "Division", "Percentage"],
    "Money": ["Addition", "Subtraction", "Division", "Percentage"],
    "Fractions": ["Addition", "Subtraction", "Multiplication", "Division"],
    "Special trainings": [
        "Word problems",
        "Mixed tasks",
        "Digit sums",
        "Rule of three",
        "Equations",
        "Chain calculations",
        "Fun with fractions",
    ],
}
ALL_TOPICS = [(group, name, level) for group, names in OFFERED.items() for name in names for level in LEVELS]
SYMBOLS = {"Addition": "+", "Subtraction": "−", "Multiplication": "×", "Division": "÷"}
ARITHMETIC = [
    (group, name, level)
    for group, name, level in ALL_TOPICS
    if name in SYMBOLS and group != "Special trainings"
]


def generate_round(group, name, level, seed=1, count=ROUND):
    """Generate tasks the way a session does: each one knows the previous one."""
    rng = random.Random(seed)
    topic = Topic(group, name, level)
    round_tasks, previous = [], None
    for _ in range(count):
        previous = generate_task([topic], rng, previous=previous)
        round_tasks.append(previous)
    return round_tasks


def number(text):
    """'€1,234.50' -> Fraction(2469, 2), '3/4' -> Fraction(3, 4)."""
    return Fraction(text.replace(",", "").replace("€", ""))


def numbers_in(text):
    return [int(found.replace(",", "")) for found in re.findall(r"\d[\d,]*", text)]


def typed(task):
    """The correct answer the way a user types it: no thousands separators, no €."""
    return format_answer(task).replace(",", "").replace("€", "")


def calculate(expression, x=None):
    """Work out a task text such as '(14 + 5) × 3' with Python as an independent check."""
    python = expression.replace(",", "").replace("×", "*").replace("÷", "/").replace("−", "-")
    python = re.sub(r"(\d)(x|\()", r"\1*\2", python)  # 3x -> 3*x, 3(x + 1) -> 3*(x + 1)
    assert re.fullmatch(r"[0-9x+\-*/() ]+", python), expression
    return eval(python, {"__builtins__": {}}, {"x": x})  # noqa: S307 - text is generated, and checked above


def make_task(answer, kind, text="task"):
    topic = Topic("Natural numbers", "Addition", "Easy")
    return TrainerTask(topic, "Calculate", text, Fraction(answer), kind, f"{text} = {answer}")


# --- What the Trainer offers (product brief, R2 and R3) ---


def test_number_types_offer_the_operations_of_the_brief():
    offered = {group: list(names) for group, names in NUMBER_TYPES.items()}
    offered[SPECIAL] = list(SPECIAL_TRAININGS)
    assert offered == OFFERED


@pytest.mark.parametrize("group, name, level", ALL_TOPICS)
def test_every_offered_topic_is_valid(group, name, level):
    assert is_valid_topic(Topic(group, name, level))


@pytest.mark.parametrize(
    "group, name, level",
    [
        ("Money", "Multiplication", "Easy"),  # not offered for money
        ("Fractions", "Percentage", "Easy"),
        ("Natural numbers", "Addition", "Extreme"),
        ("Natural numbers", "Equations", "Easy"),  # a special training, not an operation
        ("Imaginary numbers", "Addition", "Easy"),
    ],
)
def test_other_topics_are_rejected(group, name, level):
    topic = Topic(group, name, level)
    assert not is_valid_topic(topic)
    with pytest.raises(ValueError):
        generate_task([topic], random.Random(1))


def test_generating_without_a_topic_is_rejected():
    with pytest.raises(ValueError):
        generate_task([], random.Random(1))


# --- Every task, whatever the topic ---


@pytest.mark.parametrize("group, name, level", ALL_TOPICS)
def test_generated_tasks_are_well_formed(group, name, level):
    for task in generate_round(group, name, level):
        assert task.topic == Topic(group, name, level)
        assert task.text and task.prompt
        assert task.answer > 0, task
        # The answer that is shown must be accepted when the user types it.
        assert check_answer(task, typed(task)) is Check.CORRECT, task
        assert format_answer(task) in task.solution, task
        if task.kind is AnswerKind.WHOLE:
            assert task.answer.denominator == 1, task
        if task.kind is AnswerKind.MONEY:  # never a fraction of a cent
            assert (task.answer * 100).denominator == 1, task
        if task.kind is AnswerKind.DECIMAL:
            assert (task.answer * 10_000).denominator == 1, task


@pytest.mark.parametrize("group, name, level", ALL_TOPICS)
def test_no_task_appears_twice_in_a_row(group, name, level):
    round_tasks = generate_round(group, name, level)
    for earlier, later in zip(round_tasks, round_tasks[1:]):
        assert earlier.text != later.text


@pytest.mark.parametrize("group, name, level", ALL_TOPICS)
def test_two_rounds_do_not_show_the_same_sequence(group, name, level):
    first = [task.text for task in generate_round(group, name, level, seed=1, count=30)]
    second = [task.text for task in generate_round(group, name, level, seed=2, count=30)]
    assert first != second


def test_the_same_seed_gives_the_same_round():
    """All randomness comes from the passed-in generator, so tests can fix it."""
    first = generate_round("Special trainings", "Chain calculations", "Pro", seed=5, count=50)
    second = generate_round("Special trainings", "Chain calculations", "Pro", seed=5, count=50)
    assert first == second


def test_selected_topics_are_mixed_and_none_twice_in_a_row():
    topics = [
        Topic("Decimals", "Addition", "Easy"),
        Topic("Decimals", "Division", "Hard"),
        Topic("Decimals", "Multiplication", "Pro"),
    ]
    rng = random.Random(3)
    drawn, previous = [], None
    for _ in range(300):
        previous = generate_task(topics, rng, previous=previous)
        drawn.append(previous)

    assert {task.topic for task in drawn} == set(topics)
    assert all(a.text != b.text for a, b in zip(drawn, drawn[1:]))


# --- Arithmetic of all number types: recalculated from the text ---


@pytest.mark.parametrize("group, name, level", ARITHMETIC)
def test_arithmetic_answer_matches_the_text(group, name, level):
    for task in generate_round(group, name, level):
        left, symbol, right = task.text.split(" ")
        a, b = number(left), number(right)
        assert symbol == SYMBOLS[name], task
        expected = {"+": a + b, "−": a - b, "×": a * b, "÷": a / b}[symbol]
        assert task.answer == expected, task


# --- Natural numbers: percentage, square, square root ---

PERCENT_RULES = {  # level: (allowed percentages, lowest base, highest base, step of the base)
    "Easy": ({10, 25, 50}, 20, 200, 20),
    "Medium": ({5, 20, 40, 60, 75}, 20, 400, 20),
    "Hard": ({p for p in range(1, 100) if p % 10}, 100, 2000, 100),
    "Pro": ({p for p in range(101, 251) if p % 10}, 100, 5000, 100),
}
ROOT_RULES = {"Easy": (2, 9), "Medium": (11, 19), "Hard": (21, 39), "Pro": (41, 99)}


@pytest.mark.parametrize("level", LEVELS)
def test_percentage_follows_the_table(level):
    percents, low, high, step = PERCENT_RULES[level]
    for task in generate_round("Natural numbers", "Percentage", level):
        percent, base = numbers_in(task.text)
        assert task.text == f"{percent} % of {base:,}"
        assert percent in percents, task
        assert low <= base <= high and base % step == 0, task
        assert task.answer == Fraction(percent * base, 100), task


@pytest.mark.parametrize("level", LEVELS)
def test_square_follows_the_table(level):
    low, high = ROOT_RULES[level]
    for task in generate_round("Natural numbers", "Square", level):
        (a,) = numbers_in(task.text.removesuffix("²"))
        assert task.text == f"{a}²"
        assert low <= a <= high, task
        assert task.answer == a * a, task
        if level in ("Hard", "Pro"):
            assert a % 10 != 0, task


@pytest.mark.parametrize("level", LEVELS)
def test_square_root_follows_the_table_and_is_always_whole(level):
    low, high = ROOT_RULES[level]
    for task in generate_round("Natural numbers", "Square root", level):
        (square,) = numbers_in(task.text)
        assert task.text == f"√{square:,}"
        assert low <= task.answer <= high, task
        assert task.answer * task.answer == square, task


def test_basic_operations_reuse_the_rules_of_the_tests():
    """Spot checks of MB R1, which tasks.py implements and test_tasks.py covers in full."""
    for task in generate_round("Natural numbers", "Division", "Pro"):
        dividend, divisor = numbers_in(task.text)
        assert 101 <= divisor <= 291 and 11 <= task.answer <= 28 and dividend % divisor == 0
    for task in generate_round("Natural numbers", "Multiplication", "Medium"):
        a, b = numbers_in(task.text)
        assert 11 <= a <= 28 and 2 <= b <= 9


# --- Decimals ---

DECIMAL_SUM_RULES = {  # level: (lowest, highest, most decimal places)
    "Easy": ("0.1", "9.9", 1),
    "Medium": ("10", "99.9", 1),
    "Hard": ("1", "99.99", 2),
    "Pro": ("100", "999.99", 2),
}


def decimal_places(value):
    places = 0
    while (value * 10**places).denominator != 1:
        places += 1
    return places


@pytest.mark.parametrize("name", ["Addition", "Subtraction"])
@pytest.mark.parametrize("level", LEVELS)
def test_decimal_sums_follow_the_table(name, level):
    low, high, places = DECIMAL_SUM_RULES[level]
    for task in generate_round("Decimals", name, level):
        left, _, right = task.text.split(" ")
        for operand in (number(left), number(right)):
            assert Fraction(low) <= operand <= Fraction(high), task
            assert decimal_places(operand) <= places, task


def test_decimal_factors_follow_the_table():
    for task in generate_round("Decimals", "Multiplication", "Easy"):
        left, _, right = task.text.split(" ")
        assert Fraction("0.1") <= number(left) <= Fraction("0.9"), task
        assert right in "23456789", task
    for task in generate_round("Decimals", "Multiplication", "Pro"):
        left, _, right = task.text.split(" ")
        for operand in (number(left), number(right)):
            assert Fraction("1.1") <= operand <= Fraction("9.9"), task
            assert operand.denominator != 1, task  # never a whole number


def test_decimal_division_results_follow_the_table():
    for task in generate_round("Decimals", "Division", "Easy"):
        _, _, divisor = task.text.split(" ")
        assert divisor in "23456789", task
        assert Fraction("0.1") <= task.answer <= Fraction("0.9"), task
    for task in generate_round("Decimals", "Division", "Hard"):
        _, _, divisor = task.text.split(" ")
        assert Fraction("0.2") <= number(divisor) <= Fraction("0.9"), task
        assert task.answer.denominator == 1 and 2 <= task.answer <= 19, task


def test_decimal_answers_are_typed_with_a_point():
    task = generate_round("Decimals", "Addition", "Hard", count=1)[0]
    assert task.kind is AnswerKind.DECIMAL


# --- Large numbers ---

LARGE_SUM_RULES = {  # level: (lowest, highest, every number is a multiple of)
    "Easy": (1_000, 99_000, 1_000),
    "Medium": (11_000, 999_000, 1_000),
    "Hard": (110_000, 9_990_000, 10_000),
    "Pro": (10_100_000, 999_900_000, 100_000),
}


@pytest.mark.parametrize("name", ["Addition", "Subtraction"])
@pytest.mark.parametrize("level", LEVELS)
def test_large_sums_follow_the_table(name, level):
    low, high, unit = LARGE_SUM_RULES[level]
    for task in generate_round("Large numbers", name, level):
        for operand in numbers_in(task.text):
            assert low <= operand <= high and operand % unit == 0, task


@pytest.mark.parametrize("name", OFFERED["Large numbers"])
@pytest.mark.parametrize("level", LEVELS)
def test_large_numbers_are_round_and_reach_the_thousands(name, level):
    for task in generate_round("Large numbers", name, level):
        assert task.kind is AnswerKind.WHOLE
        # 300 × 600 has small factors, but its result is large.
        assert max(*numbers_in(task.text), task.answer) >= 1_000, task
        assert max(numbers_in(task.text)) % 100 == 0, task


def test_large_percentage_follows_the_table():
    for task in generate_round("Large numbers", "Percentage", "Easy"):
        percent, base = numbers_in(task.text)
        assert percent in {10, 25, 50}, task
        assert 10_000 <= base <= 990_000 and base % 10_000 == 0, task
        assert task.answer == Fraction(percent * base, 100), task


# --- Money ---

MONEY_SUM_RULES = {  # level: (lowest, highest, step), all in cents
    "Easy": (10, 990, 10),
    "Medium": (100, 4995, 5),
    "Hard": (100, 9999, 1),
    "Pro": (10_000, 99_999, 1),
}
AMOUNT = r"€\d{1,3}(,\d{3})*\.\d\d"


@pytest.mark.parametrize("name", ["Addition", "Subtraction"])
@pytest.mark.parametrize("level", LEVELS)
def test_money_sums_follow_the_table(name, level):
    low, high, step = MONEY_SUM_RULES[level]
    for task in generate_round("Money", name, level):
        left, _, right = task.text.split(" ")
        for amount in (left, right):
            assert re.fullmatch(AMOUNT, amount), task  # always two decimals
            cents = number(amount) * 100
            assert low <= cents <= high and cents % step == 0, task


@pytest.mark.parametrize("level", LEVELS)
def test_money_is_divided_by_a_whole_number_of_people(level):
    people_low, people_high = (2, 5) if level == "Easy" else (11, 19) if level == "Pro" else (2, 9)
    for task in generate_round("Money", "Division", level):
        amount, _, people = task.text.split(" ")
        assert re.fullmatch(AMOUNT, amount), task
        assert people_low <= int(people) <= people_high, task


@pytest.mark.parametrize("level", LEVELS)
def test_money_percentage_is_exact_to_the_cent(level):
    for task in generate_round("Money", "Percentage", level):
        percent, amount = re.fullmatch(rf"(\d+) % of ({AMOUNT})", task.text).group(1, 2)
        assert task.answer == number(amount) * int(percent) / 100, task
        assert task.kind is AnswerKind.MONEY


def test_money_answer_is_shown_in_euros_with_two_decimals():
    assert format_answer(make_task("1390.01", AnswerKind.MONEY)) == "€1,390.01"
    assert format_answer(make_task("6", AnswerKind.MONEY)) == "€6.00"


# --- Fractions ---


def shown_fractions(task):
    return [found for found in task.text.split(" ") if "/" in found]


@pytest.mark.parametrize("name", OFFERED["Fractions"])
@pytest.mark.parametrize("level", LEVELS)
def test_shown_fractions_are_in_lowest_terms(name, level):
    for task in generate_round("Fractions", name, level):
        assert shown_fractions(task), task
        for shown in shown_fractions(task):
            top, bottom = (int(part) for part in shown.split("/"))
            assert math.gcd(top, bottom) == 1 and bottom > 1, task
        assert task.kind is AnswerKind.FRACTION


@pytest.mark.parametrize("name", ["Addition", "Subtraction"])
def test_easy_fraction_sums_share_one_denominator(name):
    for task in generate_round("Fractions", name, "Easy"):
        bottoms = {shown.split("/")[1] for shown in shown_fractions(task)}
        assert len(bottoms) == 1, task


@pytest.mark.parametrize("name", ["Addition", "Subtraction"])
def test_medium_fraction_sums_have_one_denominator_that_is_a_multiple_of_the_other(name):
    for task in generate_round("Fractions", name, "Medium"):
        first, second = sorted(int(shown.split("/")[1]) for shown in shown_fractions(task))
        assert second % first == 0 and second != first, task


@pytest.mark.parametrize("name", ["Multiplication", "Division"])
def test_easy_fraction_products_use_one_fraction_and_one_whole_number(name):
    for task in generate_round("Fractions", name, "Easy"):
        left, _, right = task.text.split(" ")
        assert "/" in left and right in "23456789", task


@pytest.mark.parametrize("level", ["Easy", "Medium", "Hard"])
def test_fractions_below_pro_are_smaller_than_one(level):
    for task in generate_round("Fractions", "Addition", level):
        assert all(number(shown) < 1 for shown in shown_fractions(task)), task


def test_fraction_answer_is_shown_in_lowest_terms_or_as_a_whole_number():
    assert format_answer(make_task(Fraction(10, 12), AnswerKind.FRACTION)) == "5/6"
    assert format_answer(make_task(Fraction(4, 2), AnswerKind.FRACTION)) == "2"


# --- Special trainings ---


@pytest.mark.parametrize("level", LEVELS)
def test_word_problem_hides_one_calculation_with_the_numbers_of_the_text(level):
    operations = set()
    for task in generate_round("Special trainings", "Word problems", level):
        calculation, result = task.solution.split(" = ")
        assert calculate(calculation) == task.answer == number(result), task
        assert sorted(numbers_in(calculation)) == sorted(numbers_in(task.text)), task
        assert task.text.endswith("?"), task
        operations.add(calculation.split(" ")[1])
    assert operations == {"+", "−", "×", "÷"}


@pytest.mark.parametrize("level", LEVELS)
def test_mixed_task_follows_the_order_of_operations(level):
    for task in generate_round("Special trainings", "Mixed tasks", level):
        assert calculate(task.text) == task.answer, task
        assert len(re.findall(r"[+−×÷]", task.text)) >= 2, task  # several operations


def test_mixed_tasks_use_brackets_from_medium_upwards():
    assert not any("(" in t.text for t in generate_round("Special trainings", "Mixed tasks", "Easy"))
    for level in ("Medium", "Hard", "Pro"):
        assert any("(" in t.text for t in generate_round("Special trainings", "Mixed tasks", level))


@pytest.mark.parametrize("level, digits", [("Easy", 2), ("Medium", 3), ("Hard", 5), ("Pro", 8)])
def test_digit_sum(level, digits):
    for task in generate_round("Special trainings", "Digit sums", level):
        (shown,) = numbers_in(task.text)
        assert len(str(shown)) == digits, task
        assert task.answer == sum(int(digit) for digit in str(shown)), task


@pytest.mark.parametrize("level", ["Easy", "Medium", "Hard"])
def test_rule_of_three_grows_with_the_amount(level):
    for task in generate_round("Special trainings", "Rule of three", level):
        known, total, asked = numbers_in(task.text)
        assert known != asked, task
        assert total % known == 0, task  # the value for one is a whole number
        assert task.answer == total // known * asked, task


def test_pro_rule_of_three_is_inverse_more_workers_need_less_time():
    for task in generate_round("Special trainings", "Rule of three", "Pro"):
        known, time_needed, asked = numbers_in(task.text)
        assert known != asked, task
        assert task.answer * asked == known * time_needed, task  # the work stays the same


@pytest.mark.parametrize("level", LEVELS)
def test_equation_is_solved_by_the_answer(level):
    for task in generate_round("Special trainings", "Equations", level):
        left, right = task.text.split(" = ")
        x = int(task.answer)
        assert "x" in task.text, task
        assert calculate(left, x) == calculate(right, x), task


def test_pro_equations_have_x_on_both_sides_or_in_brackets():
    for task in generate_round("Special trainings", "Equations", "Pro"):
        assert task.text.count("x") == 2 or "(x" in task.text, task


CHAIN_RULES = {  # level: (steps, allowed symbols)
    "Easy": (3, "+−"),
    "Medium": (4, "+−×"),
    "Hard": (5, "+−×÷"),
    "Pro": (7, "+−×÷"),
}


@pytest.mark.parametrize("level", LEVELS)
def test_chain_is_calculated_step_by_step_and_stays_a_whole_number(level):
    steps, symbols = CHAIN_RULES[level]
    used = set()
    for task in generate_round("Special trainings", "Chain calculations", level):
        start, *rest = task.text.replace("→ ", "").split(" ")
        value = number(start)
        pairs = list(zip(rest[::2], rest[1::2]))
        assert len(pairs) == steps, task
        for symbol, amount in pairs:
            assert symbol in symbols, task
            value = {"+": value + int(amount), "−": value - int(amount),
                     "×": value * int(amount), "÷": value / int(amount)}[symbol]  # fmt: skip
            assert value.denominator == 1 and 1 <= value <= 9_999, task
            used.add(symbol)
        assert task.answer == value, task
    assert used == set(symbols)


@pytest.mark.parametrize("level", LEVELS)
def test_fun_with_fractions_simplifies_and_finds_gcd_and_lcm(level):
    kinds = set()
    for task in generate_round("Special trainings", "Fun with fractions", level):
        a, b = numbers_in(task.text)
        if task.text.startswith("GCD"):
            assert task.answer == math.gcd(a, b) and a != b, task
            kinds.add("GCD")
        elif task.text.startswith("LCM"):
            assert task.answer == math.lcm(a, b) and a != b, task
            kinds.add("LCM")
        else:
            assert task.text == f"{a}/{b}" and task.kind is AnswerKind.FRACTION, task
            assert task.answer == Fraction(a, b), task
            assert math.gcd(a, b) > 1, task  # there is something to simplify
            kinds.add("simplify")
    assert kinds == {"GCD", "LCM", "simplify"}


# --- Reading the user's answer (MB R3: empty or unreadable input is not evaluated) ---


@pytest.mark.parametrize(
    "raw, expected",
    [("56", 56), (" 56 ", 56), ("0", 0), ("007", 7), ("-5", -5), ("+5", 5)],
)
def test_whole_answers_are_accepted(raw, expected):
    assert parse_answer(raw, AnswerKind.WHOLE) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "abc", "5.5", "56.0", "1,250", "1 250", "5e3", "0x10", "--5", "+", "3/4",
     "€5", "٥٦", "５６", "²", "9" * 21],  # fmt: skip
)
def test_other_input_for_a_whole_answer_is_not_evaluated(raw):
    assert parse_answer(raw, AnswerKind.WHOLE) is None


@pytest.mark.parametrize(
    "raw, expected",
    [("12.5", "12.5"), ("12.50", "12.5"), ("12", "12"), ("0.35", "0.35"), (" 7.0 ", "7")],
)
def test_decimal_answers_are_accepted(raw, expected):
    assert parse_answer(raw, AnswerKind.DECIMAL) == Fraction(expected)


@pytest.mark.parametrize("raw", ["", "12,5", ".5", "5.", "1.2.3", "1,234.5", "abc", "3/4", "1e2"])
def test_other_input_for_a_decimal_answer_is_not_evaluated(raw):
    assert parse_answer(raw, AnswerKind.DECIMAL) is None


@pytest.mark.parametrize("raw", ["12.50", "12.5", "€12.50", "12.50€", "€ 12.50", " 12.50 € "])
def test_money_answers_are_accepted_with_or_without_the_euro_sign(raw):
    assert parse_answer(raw, AnswerKind.MONEY) == Fraction("12.5")


@pytest.mark.parametrize("raw", ["", "12.505", "12,50", "$12.50", "EUR 12.50", "€", "12.5.0"])
def test_other_input_for_a_money_answer_is_not_evaluated(raw):
    assert parse_answer(raw, AnswerKind.MONEY) is None


@pytest.mark.parametrize(
    "raw, expected",
    [("3/4", Fraction(3, 4)), (" 3 / 4 ", Fraction(3, 4)), ("7/4", Fraction(7, 4)),
     ("2", Fraction(2)), ("2/1", Fraction(2))],  # fmt: skip
)
def test_fraction_answers_are_accepted(raw, expected):
    assert parse_answer(raw, AnswerKind.FRACTION) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "6/8", "4/2", "0/5", "3/0", "3/", "/4", "3//4", "0.75", "1 3/4", "three quarters"],
)
def test_other_input_for_a_fraction_answer_is_not_evaluated(raw):
    """6/8 is the right value for 3/4, but the user is asked to simplify first."""
    assert parse_answer(raw, AnswerKind.FRACTION) is None


def test_checking_a_whole_answer():
    task = make_task(20, AnswerKind.WHOLE, "25 % of 80")
    assert check_answer(task, "20") is Check.CORRECT
    assert check_answer(task, "25") is Check.WRONG
    assert check_answer(task, "") is Check.INVALID
    assert check_answer(task, "twenty") is Check.INVALID
    assert check_answer(task, "20.0") is Check.INVALID


def test_checking_a_decimal_answer():
    task = make_task("2.5", AnswerKind.DECIMAL)
    assert check_answer(task, "2.5") is Check.CORRECT
    assert check_answer(task, "2.50") is Check.CORRECT
    assert check_answer(task, "2.6") is Check.WRONG
    assert check_answer(task, "2,5") is Check.INVALID


def test_checking_a_money_answer():
    task = make_task("12.5", AnswerKind.MONEY)
    assert check_answer(task, "€12.50") is Check.CORRECT
    assert check_answer(task, "12.5") is Check.CORRECT
    assert check_answer(task, "12.49") is Check.WRONG
    assert check_answer(task, "12.499") is Check.INVALID


def test_checking_a_fraction_answer():
    task = make_task(Fraction(3, 4), AnswerKind.FRACTION)
    assert check_answer(task, "3/4") is Check.CORRECT
    assert check_answer(task, "2/3") is Check.WRONG
    assert check_answer(task, "6/8") is Check.INVALID


def test_every_answer_format_has_a_hint_for_the_user():
    assert set(ANSWER_HINTS) == set(AnswerKind)
    assert all(ANSWER_HINTS.values())


@pytest.mark.parametrize(
    "answer, kind, shown",
    [
        (4250, AnswerKind.WHOLE, "4,250"),
        ("0.35", AnswerKind.DECIMAL, "0.35"),
        ("1999.98", AnswerKind.DECIMAL, "1,999.98"),
        (20, AnswerKind.DECIMAL, "20"),
    ],
)
def test_answer_is_shown_with_thousands_separators(answer, kind, shown):
    assert format_answer(make_task(answer, kind)) == shown


# --- Structure (AGENTS.md) ---


def test_module_follows_design_rules():
    source = (Path(__file__).parent.parent / "trainer_tasks.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", ".now(", "time.time", "random.Random("):
        assert forbidden not in source
'''

####################################################################################################
# tests/test_trainer.py
####################################################################################################

FILES['tests/test_trainer.py'] = r'''"""Trainer session rules: settings, modes, time limits and results (spec 002)."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

from trainer import (
    CATEGORIES,
    LIMITS,
    EndReason,
    Mode,
    Outcome,
    Settings,
    SettingsError,
    Status,
    abort_session,
    elapsed_seconds,
    finish_if_expired,
    format_duration,
    is_time_up,
    levels_text,
    limit_text,
    make_settings,
    remaining_seconds,
    skip_task,
    start_session,
    submit_answer,
    summarize,
)
from trainer_tasks import AnswerKind, Topic, TrainerTask

START = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
PERCENTAGE = Topic("Natural numbers", "Percentage", "Easy")
TASK = TrainerTask(
    PERCENTAGE, "Calculate", "25 % of 80", Fraction(20), AnswerKind.WHOLE, "25 % of 80 = 20"
)
FRACTION_TASK = TrainerTask(
    Topic("Fractions", "Addition", "Easy"),
    "Calculate",
    "1/4 + 2/4",
    Fraction(3, 4),
    AnswerKind.FRACTION,
    "1/4 + 2/4 = 3/4",
)


def at(seconds):
    return START + timedelta(seconds=seconds)


def settings(mode=Mode.TASK_COUNT, limit=5):
    return make_settings("Operations", "Percentage", [PERCENTAGE], mode, limit)


def new_session(mode=Mode.TASK_COUNT, limit=5):
    return start_session(settings(mode, limit), START)


def totals(session):
    return session.correct, session.wrong, session.skipped


def answer_all(session, answers, step=2):
    """Submit one answer every `step` seconds."""
    for position, raw in enumerate(answers, start=1):
        session, _ = submit_answer(session, TASK, raw, at(position * step))
    return session


# --- Settings: what the user may choose (product brief, R2) ---


def test_three_categories_and_three_modes():
    assert list(CATEGORIES) == ["Operations", "Number types", "Special trainings"]
    assert [mode.value for mode in Mode] == ["Task count", "Total time", "Time per task"]


def test_limits_of_the_brief():
    assert LIMITS == {
        Mode.TASK_COUNT: (5, 100),  # 5 to 100 tasks
        Mode.TOTAL_TIME: (30, 900),  # 30 seconds to 15 minutes
        Mode.TIME_PER_TASK: (1, 60),  # 1 to 60 seconds
    }


@pytest.mark.parametrize(
    "mode, limit",
    [
        (Mode.TASK_COUNT, 5),
        (Mode.TASK_COUNT, 100),
        (Mode.TOTAL_TIME, 30),
        (Mode.TOTAL_TIME, 900),
        (Mode.TIME_PER_TASK, 1),
        (Mode.TIME_PER_TASK, 60),
    ],
)
def test_limits_on_the_boundary_are_accepted(mode, limit):
    made = settings(mode, limit)
    assert (made.mode, made.limit) == (mode, limit)


@pytest.mark.parametrize(
    "mode, limit",
    [
        (Mode.TASK_COUNT, 4),
        (Mode.TASK_COUNT, 101),
        (Mode.TOTAL_TIME, 29),
        (Mode.TOTAL_TIME, 901),
        (Mode.TIME_PER_TASK, 0),
        (Mode.TIME_PER_TASK, 61),
        (Mode.TASK_COUNT, -10),
        (Mode.TASK_COUNT, 10.0),  # not a whole number type
        (Mode.TASK_COUNT, "10"),
        (Mode.TASK_COUNT, None),
        (Mode.TASK_COUNT, True),
    ],
)
def test_limits_outside_the_range_are_rejected(mode, limit):
    with pytest.raises(SettingsError):
        settings(mode, limit)


def test_mode_can_be_given_as_text_and_unknown_modes_are_rejected():
    assert settings("Total time", 60).mode is Mode.TOTAL_TIME
    with pytest.raises(SettingsError):
        settings("Endless", 60)


def test_operations_trains_exactly_one_operation_of_natural_numbers():
    made = make_settings("Operations", "Square", [Topic("Natural numbers", "Square", "Pro")], "Task count", 10)
    assert made == Settings(
        "Operations", "Square", (Topic("Natural numbers", "Square", "Pro"),), Mode.TASK_COUNT, 10
    )


@pytest.mark.parametrize(
    "name, topics",
    [
        ("Percentage", []),  # nothing selected
        ("Percentage", [PERCENTAGE, Topic("Natural numbers", "Square", "Easy")]),  # two operations
        ("Addition", [Topic("Decimals", "Addition", "Easy")]),  # not natural numbers
        ("Square", [PERCENTAGE]),  # the name does not match the topic
        ("Equations", [Topic("Special trainings", "Equations", "Easy")]),
        ("Percentage", [Topic("Natural numbers", "Percentage", "Extreme")]),  # unknown level
        ("Cube", [Topic("Natural numbers", "Cube", "Easy")]),  # unknown operation
    ],
)
def test_other_operation_settings_are_rejected(name, topics):
    with pytest.raises(SettingsError):
        make_settings("Operations", name, topics, "Task count", 10)


def test_number_type_mixes_several_operations_each_with_its_own_level():
    topics = [Topic("Decimals", "Addition", "Easy"), Topic("Decimals", "Division", "Hard")]
    made = make_settings("Number types", "Decimals", topics, "Total time", 120)
    assert made.topics == tuple(topics)
    assert levels_text(made) == "Addition Easy, Division Hard"


@pytest.mark.parametrize(
    "name, topics",
    [
        ("Decimals", []),  # no operation ticked
        ("Decimals", [Topic("Money", "Addition", "Easy")]),  # another number type
        ("Decimals", [Topic("Decimals", "Addition", "Easy"), Topic("Money", "Addition", "Easy")]),
        ("Decimals", [Topic("Decimals", "Addition", "Easy"), Topic("Decimals", "Addition", "Pro")]),
        ("Money", [Topic("Money", "Multiplication", "Easy")]),  # money has no multiplication
        ("Vectors", [Topic("Vectors", "Addition", "Easy")]),
    ],
)
def test_other_number_type_settings_are_rejected(name, topics):
    with pytest.raises(SettingsError):
        make_settings("Number types", name, topics, "Task count", 10)


def test_special_training_trains_exactly_one_training():
    topic = Topic("Special trainings", "Equations", "Hard")
    made = make_settings("Special trainings", "Equations", [topic], "Time per task", 20)
    assert made.topics == (topic,)
    assert levels_text(made) == "Hard"
    with pytest.raises(SettingsError):
        make_settings("Special trainings", "Equations", [topic, PERCENTAGE], "Task count", 10)
    with pytest.raises(SettingsError):
        make_settings("Special trainings", "Percentage", [PERCENTAGE], "Task count", 10)


def test_unknown_category_is_rejected():
    with pytest.raises(SettingsError):
        make_settings("Games", "Percentage", [PERCENTAGE], "Task count", 10)


def test_rejected_settings_explain_why_in_words_for_the_user():
    with pytest.raises(SettingsError, match="5 to 100"):
        settings(Mode.TASK_COUNT, 101)
    with pytest.raises(SettingsError, match="at least one"):
        make_settings("Number types", "Decimals", [], "Task count", 10)


# --- Answers (MB R3) ---


def test_new_session_starts_empty_and_running():
    session = new_session()
    assert session.status is Status.RUNNING
    assert totals(session) == (0, 0, 0)
    assert session.attempts == ()
    assert session.started_at == session.task_started_at == START


def test_correct_answer_adds_a_point():
    session, outcome = submit_answer(new_session(), TASK, "20", at(3))
    assert outcome is Outcome.CORRECT
    assert totals(session) == (1, 0, 0)


def test_wrong_answer_adds_no_point():
    session, outcome = submit_answer(new_session(), TASK, "25", at(3))
    assert outcome is Outcome.WRONG
    assert totals(session) == (0, 1, 0)


def test_skip_is_recorded_as_skipped_only():
    session, outcome = skip_task(new_session(), TASK, at(3))
    assert outcome is Outcome.SKIPPED
    assert totals(session) == (0, 0, 1)
    assert summarize(session).accuracy == 0


@pytest.mark.parametrize("raw", ["", "   ", "abc", "20.0", "1,000"])
def test_empty_or_unreadable_input_changes_nothing(raw):
    before = new_session()
    after, outcome = submit_answer(before, TASK, raw, at(3))
    assert outcome is Outcome.IGNORED
    assert after == before


def test_unsimplified_fraction_is_not_evaluated():
    before = new_session()
    after, outcome = submit_answer(before, FRACTION_TASK, "6/8", at(3))
    assert outcome is Outcome.IGNORED
    assert after == before
    assert submit_answer(before, FRACTION_TASK, "3/4", at(3))[1] is Outcome.CORRECT


def test_every_attempt_is_kept_for_the_review():
    session, _ = submit_answer(new_session(), TASK, " 25 ", at(4))
    session, _ = skip_task(session, TASK, at(5.5))
    wrong, skipped = session.attempts

    assert (wrong.text, wrong.given, wrong.answer) == ("25 % of 80", "25", "20")
    assert wrong.solution == "25 % of 80 = 20"
    assert wrong.outcome is Outcome.WRONG
    assert wrong.seconds == 4
    assert (skipped.given, skipped.outcome, skipped.seconds) == ("", Outcome.SKIPPED, 1.5)


def test_totals_are_counted_from_the_attempts():
    session = answer_all(new_session(limit=10), ["20", "20", "7", "20"])
    session, _ = skip_task(session, TASK, at(60))
    assert totals(session) == (3, 1, 1)
    assert len(session.attempts) == 5


# --- Mode: task count ---


def test_task_count_ends_after_the_last_task_and_not_before():
    session = answer_all(new_session(limit=5), ["20", "1", "20", "20"])
    assert session.status is Status.RUNNING

    session, outcome = submit_answer(session, TASK, "20", at(30))
    assert outcome is Outcome.CORRECT  # the last answer still counts
    assert session.status is Status.FINISHED
    assert session.end_reason is EndReason.ALL_TASKS_DONE
    assert session.ended_at == at(30)
    assert totals(session) == (4, 1, 0)


def test_skipped_tasks_count_towards_the_task_count():
    session = new_session(limit=5)
    for second in range(1, 6):
        session, _ = skip_task(session, TASK, at(second))
    assert session.status is Status.FINISHED
    assert totals(session) == (0, 0, 5)


def test_ignored_input_does_not_count_towards_the_task_count():
    session = answer_all(new_session(limit=5), ["20", "", "abc", "20", "20", "20"])
    assert session.status is Status.RUNNING
    assert len(session.attempts) == 4


def test_task_count_has_no_time_limit():
    session = new_session()
    a_day_later = at(24 * 60 * 60)
    assert is_time_up(session, a_day_later) is False
    assert remaining_seconds(session, a_day_later) is None
    assert finish_if_expired(session, a_day_later) == session
    assert submit_answer(session, TASK, "20", a_day_later)[1] is Outcome.CORRECT


def test_time_is_measured_in_task_count_mode():
    session = answer_all(new_session(limit=5), ["20"] * 5, step=3)
    assert elapsed_seconds(session, at(999)) == 15  # stops at the last answer
    assert summarize(session).duration_seconds == 15


# --- Mode: total time ---


def test_answer_just_before_the_total_time_counts():
    session, outcome = submit_answer(new_session(Mode.TOTAL_TIME, 30), TASK, "20", at(29.9))
    assert outcome is Outcome.CORRECT
    assert session.status is Status.RUNNING


@pytest.mark.parametrize("seconds", [30.0, 30.1, 500])
def test_answer_at_or_after_the_total_time_does_not_count_and_ends_the_session(seconds):
    session, outcome = submit_answer(new_session(Mode.TOTAL_TIME, 30), TASK, "20", at(seconds))
    assert outcome is Outcome.TIME_UP
    assert session.status is Status.FINISHED
    assert session.end_reason is EndReason.TIME_UP
    assert totals(session) == (0, 0, 0)
    assert session.ended_at == at(30)  # the limit, however late the answer came


def test_skip_at_the_total_time_does_not_count():
    session, outcome = skip_task(new_session(Mode.TOTAL_TIME, 30), TASK, at(30))
    assert outcome is Outcome.TIME_UP
    assert totals(session) == (0, 0, 0)


def test_total_time_does_not_restart_with_each_task():
    session = answer_all(new_session(Mode.TOTAL_TIME, 30), ["20"] * 10, step=2.5)
    assert remaining_seconds(session, at(25)) == 5
    assert is_time_up(session, at(29.9)) is False
    assert is_time_up(session, at(30)) is True


def test_total_time_session_finishes_without_any_answer():
    session = finish_if_expired(new_session(Mode.TOTAL_TIME, 30), at(31))
    assert session.status is Status.FINISHED
    assert summarize(session).accuracy is None
    assert summarize(session).duration_seconds == 30


# --- Mode: time per task ---


def test_answer_just_before_the_time_per_task_counts():
    session, outcome = submit_answer(new_session(Mode.TIME_PER_TASK, 10), TASK, "20", at(9.9))
    assert outcome is Outcome.CORRECT
    assert session.status is Status.RUNNING


def test_answer_at_the_time_per_task_ends_the_session():
    session, outcome = submit_answer(new_session(Mode.TIME_PER_TASK, 10), TASK, "20", at(10))
    assert outcome is Outcome.TIME_UP
    assert session.status is Status.FINISHED
    assert session.end_reason is EndReason.TOO_SLOW
    assert totals(session) == (0, 0, 0)


def test_time_per_task_restarts_with_every_answer_or_skip():
    session = new_session(Mode.TIME_PER_TASK, 10)
    session, _ = submit_answer(session, TASK, "20", at(9))
    session, _ = skip_task(session, TASK, at(18))
    session, outcome = submit_answer(session, TASK, "1", at(27))
    assert outcome is Outcome.WRONG
    assert session.status is Status.RUNNING
    assert remaining_seconds(session, at(30)) == 7

    session, outcome = submit_answer(session, TASK, "20", at(37))
    assert outcome is Outcome.TIME_UP
    assert session.ended_at == at(37)  # 10 seconds after the task appeared
    assert totals(session) == (1, 1, 1)


def test_ignored_input_does_not_restart_the_time_per_task():
    session, _ = submit_answer(new_session(Mode.TIME_PER_TASK, 10), TASK, "abc", at(9))
    assert remaining_seconds(session, at(9)) == 1
    assert is_time_up(session, at(10)) is True


# --- Aborting and finished sessions ---


def test_aborted_session_is_not_finished():
    session = answer_all(new_session(), ["20", "20"])
    aborted = abort_session(session, at(10))
    assert aborted.status is Status.ABORTED
    assert aborted.end_reason is EndReason.ABORTED


def test_abort_after_the_time_limit_counts_as_finished():
    session = abort_session(new_session(Mode.TOTAL_TIME, 30), at(31))
    assert session.status is Status.FINISHED
    assert session.end_reason is EndReason.TIME_UP


@pytest.mark.parametrize("ended", ["finished", "aborted"])
def test_nothing_changes_after_the_session_has_ended(ended):
    session = answer_all(new_session(limit=5), ["20"] * 5)
    if ended == "aborted":
        session = abort_session(answer_all(new_session(), ["20"]), at(9))

    assert submit_answer(session, TASK, "20", at(60)) == (session, Outcome.IGNORED)
    assert skip_task(session, TASK, at(60)) == (session, Outcome.IGNORED)
    assert abort_session(session, at(60)) == session
    assert finish_if_expired(session, at(60)) == session


def test_sessions_are_not_changed_in_place():
    before = new_session()
    submit_answer(before, TASK, "20", at(1))
    skip_task(before, TASK, at(1))
    abort_session(before, at(1))
    assert before == new_session()


# --- Result ---


def test_summary_of_a_finished_session():
    session = answer_all(new_session(limit=5), ["20", "20", "20", "9"], step=2)
    session, _ = skip_task(session, TASK, at(12))
    summary = summarize(session)

    assert (summary.correct, summary.wrong, summary.skipped) == (3, 1, 1)
    assert summary.accuracy == 3 / 5  # MB R3: a skip lowers the accuracy
    assert summary.duration_seconds == 12
    assert summary.average_seconds == 12 / 5


def test_summary_without_attempts_has_no_accuracy_and_no_average():
    summary = summarize(finish_if_expired(new_session(Mode.TIME_PER_TASK, 5), at(6)))
    assert summary.accuracy is None
    assert summary.average_seconds is None
    assert summary.duration_seconds == 5


@pytest.mark.parametrize(
    "seconds, text", [(0, "0:00"), (9.9, "0:09"), (75.4, "1:15"), (900, "15:00")]
)
def test_format_duration(seconds, text):
    assert format_duration(seconds) == text


def test_limit_text_names_the_mode_in_a_few_words():
    assert limit_text(Mode.TASK_COUNT, 10) == "10 tasks"
    assert limit_text(Mode.TOTAL_TIME, 90) == "1:30 min in total"
    assert limit_text("Time per task", 8) == "8 s per task"  # also from text, as saved


def test_levels_text_for_one_topic_is_just_the_level():
    assert levels_text(settings()) == "Easy"


def test_elapsed_time_never_goes_below_zero():
    assert elapsed_seconds(new_session(), at(-5)) == 0
    assert remaining_seconds(replace(new_session(Mode.TOTAL_TIME, 30)), at(99)) == 0


# --- Structure (AGENTS.md) ---


def test_module_follows_design_rules():
    source = (Path(__file__).parent.parent / "trainer.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", ".now(", "time.time", "random.Random("):
        assert forbidden not in source
'''

####################################################################################################
# tests/test_trainer_db.py
####################################################################################################

FILES['tests/test_trainer_db.py'] = r'''"""SQLite storage of finished trainer sessions."""

import os
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

import db
import trainer_db
from trainer import (
    Mode,
    SavedSession,
    abort_session,
    finish_if_expired,
    make_settings,
    skip_task,
    start_session,
    submit_answer,
)
from trainer_tasks import AnswerKind, Topic, TrainerTask

PROJECT_ROOT = Path(__file__).resolve().parent.parent
START = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
TOPIC = Topic("Natural numbers", "Percentage", "Easy")
TASK = TrainerTask(TOPIC, "Calculate", "25 % of 80", Fraction(20), AnswerKind.WHOLE, "25 % of 80 = 20")


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test uses its own file, so data/mathbuddy.db is never touched."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("MATHBUDDY_DB", str(path))
    trainer_db.init_db()
    return path


def at(seconds):
    return START + timedelta(seconds=seconds)


def running_session(mode=Mode.TASK_COUNT, limit=5, start=START):
    settings = make_settings("Operations", "Percentage", [TOPIC], mode, limit)
    return start_session(settings, start)


def finished_session(start=START):
    """Five tasks, one every 2 seconds: 3 correct, 1 wrong, 1 skipped."""
    session = running_session(start=start)
    for position, raw in enumerate(["20", "20", "20", "9"], start=1):
        session, _ = submit_answer(session, TASK, raw, start + timedelta(seconds=2 * position))
    session, _ = skip_task(session, TASK, start + timedelta(seconds=10))
    return session


# --- Schema ---


def test_trainer_sessions_live_in_their_own_table_with_exactly_these_columns():
    with closing(db.connect()) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(trainer_sessions)")}
    assert columns == {
        "id",
        "category",
        "name",
        "levels",
        "mode",
        "limit_value",
        "finished_at",
        "duration_seconds",
        "correct",
        "wrong",
        "skipped",
    }


def test_the_runs_table_of_the_tests_is_left_alone():
    db.init_db()
    trainer_db.save_session("session-1", finished_session())
    assert db.list_runs() == []


# --- Saving and reading ---


def test_no_sessions_at_first():
    assert trainer_db.list_sessions() == []


def test_finished_session_is_read_back_with_all_fields():
    trainer_db.save_session("session-1", finished_session())
    assert trainer_db.list_sessions() == [
        SavedSession(
            id="session-1",
            category="Operations",
            name="Percentage",
            levels="Easy",
            mode="Task count",
            limit=5,
            finished_at=at(10),
            duration_seconds=10,
            correct=3,
            wrong=1,
            skipped=1,
        )
    ]


def test_finished_at_is_read_back_in_utc():
    trainer_db.save_session("session-1", finished_session())
    assert trainer_db.list_sessions()[0].finished_at.utcoffset() == timedelta(0)


def test_session_that_ran_out_of_time_is_saved_at_its_limit():
    session = finish_if_expired(running_session(Mode.TOTAL_TIME, 30), at(45))
    trainer_db.save_session("timed", session)
    saved = trainer_db.list_sessions()[0]
    assert (saved.mode, saved.limit, saved.duration_seconds) == ("Total time", 30, 30)
    assert saved.finished_at == at(30)


def test_levels_of_a_mixed_number_type_session_are_saved_as_text():
    topics = [Topic("Decimals", "Addition", "Easy"), Topic("Decimals", "Division", "Hard")]
    settings = make_settings("Number types", "Decimals", topics, Mode.TIME_PER_TASK, 5)
    trainer_db.save_session("mixed", finish_if_expired(start_session(settings, START), at(6)))
    saved = trainer_db.list_sessions()[0]
    assert (saved.category, saved.name) == ("Number types", "Decimals")
    assert saved.levels == "Addition Easy, Division Hard"


def test_saving_the_same_session_twice_keeps_the_first_one():
    trainer_db.save_session("same", finished_session())
    trainer_db.save_session("same", finish_if_expired(running_session(Mode.TOTAL_TIME, 30), at(31)))
    saved = trainer_db.list_sessions()
    assert len(saved) == 1
    assert saved[0].correct == 3


# --- Rejected: only finished sessions are saved ---


def test_running_session_is_not_saved():
    with pytest.raises(ValueError):
        trainer_db.save_session("running", running_session())
    assert trainer_db.list_sessions() == []


def test_aborted_session_is_not_saved():
    session, _ = submit_answer(running_session(), TASK, "20", at(2))
    with pytest.raises(ValueError):
        trainer_db.save_session("aborted", abort_session(session, at(3)))
    assert trainer_db.list_sessions() == []


def test_text_is_stored_as_data_and_never_run_as_sql():
    trainer_db.save_session("x'); DROP TABLE trainer_sessions; --", finished_session())
    assert [saved.id for saved in trainer_db.list_sessions()] == [
        "x'); DROP TABLE trainer_sessions; --"
    ]


# --- Order and history length ---


def test_sessions_are_listed_newest_first():
    for name, day in (("old", 0), ("new", 2), ("middle", 1)):
        trainer_db.save_session(name, finished_session(start=START + timedelta(days=day)))
    assert [saved.id for saved in trainer_db.list_sessions()] == ["new", "middle", "old"]


def test_limit_keeps_only_the_newest_sessions():
    for day in range(5):
        trainer_db.save_session(f"day-{day}", finished_session(start=START + timedelta(days=day)))
    assert [saved.id for saved in trainer_db.list_sessions(limit=2)] == ["day-4", "day-3"]
    assert len(trainer_db.list_sessions()) == 5


# --- Restart ---


def test_init_db_twice_keeps_saved_sessions():
    trainer_db.save_session("session-1", finished_session())
    trainer_db.init_db()
    assert len(trainer_db.list_sessions()) == 1


def test_sessions_survive_a_restart():
    """A new process on the same file stands in for stopping and restarting the app."""
    trainer_db.save_session("session-1", finished_session())

    script = "import trainer_db; trainer_db.init_db(); print(len(trainer_db.list_sessions()))"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "1"
'''

####################################################################################################
# tests/test_trainer_ui.py
####################################################################################################

FILES['tests/test_trainer_ui.py'] = r'''"""Trainer screens in trainer_ui.py and their wiring in app.py, driven through AppTest.

AppTest does not run a browser, so these need a manual check in the PR:
the status line ticking every second, the end of a timed session without any
click, the green and red flash, cursor focus, the field clearing after submit,
and cancelling during the countdown.
"""

import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import db
import trainer_db
from trainer_tasks import ANSWER_HINTS, AnswerKind, Topic, format_answer

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
LEVELS = ["Easy", "Medium", "Hard", "Pro"]


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


@pytest.fixture
def fast_sleep(monkeypatch):
    """Keep the 3-second countdown from slowing down every test."""
    real_sleep = time.sleep
    monkeypatch.setattr(time, "sleep", lambda seconds: real_sleep(min(seconds, 0.01)))


def go_to(at, section):
    at.radio(key="nav").set_value(section).run()
    assert not at.exception


def open_trainer():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    go_to(at, "Trainer")
    return at


def choose(at, key, value):
    """Pick one option of a row of pills or of a segmented control."""
    at.button_group(key=key).set_value(value).run()
    assert not at.exception


def start(at):
    at.button(key="tr_start").click().run()
    assert not at.exception
    return at


def start_with(at, mode, limit):
    keys = {
        "Task count": "tr_limit_tasks",
        "Total time": "tr_limit_total",
        "Time per task": "tr_limit_per_task",
    }
    choose(at, "tr_mode", mode)
    at.number_input(key=keys[mode]).set_value(limit).run()
    return start(at)


def submit(at, text):
    at.text_input(key="tr_answer").input(text)
    at.button(key="tr_submit").click().run()
    assert not at.exception


def skip(at):
    at.button(key="tr_skip").click().run()
    assert not at.exception


def right_answer(at):
    """The correct answer the way a user types it: no thousands separators, no €."""
    return format_answer(at.session_state["tr_task"]).replace(",", "").replace("€", "")


def move_clock(at, seconds):
    """Pretend the session and its current task started `seconds` earlier. No rerun yet."""
    session = at.session_state["tr_session"]
    earlier = timedelta(seconds=seconds)
    at.session_state["tr_session"] = replace(
        session,
        started_at=session.started_at - earlier,
        task_started_at=session.task_started_at - earlier,
    )


def page_text(at):
    groups = (
        at.header, at.subheader, at.markdown, at.caption,
        at.success, at.info, at.warning, at.error,
    )  # fmt: skip
    return "\n".join(str(element.value) for group in groups for element in group)


def metrics(at):
    return {metric.label: metric.value for metric in at.metric}


def phase(at):
    return at.session_state["tr_phase"]


# --- Navigation (MB01) ---


def test_trainer_is_built_and_no_longer_coming_soon():
    at = open_trainer()
    assert "Coming soon" not in page_text(at)
    assert "Trainer" in [header.value for header in at.header]


# --- Setup screen ---


def test_three_categories_with_operations_first():
    at = open_trainer()
    category = at.button_group(key="tr_category")
    assert list(category.options) == ["Operations", "Number types", "Special trainings"]
    assert category.value == "Operations"


def test_operations_offers_seven_operations_and_four_levels():
    at = open_trainer()
    assert list(at.button_group(key="tr_operation").options) == [
        "Addition",
        "Subtraction",
        "Multiplication",
        "Division",
        "Percentage",
        "Square",
        "Square root",
    ]
    assert list(at.button_group(key="tr_level").options) == LEVELS


def test_number_types_offers_five_types_and_the_operations_of_the_chosen_one():
    at = open_trainer()
    choose(at, "tr_category", "Number types")
    assert list(at.button_group(key="tr_number_type").options) == [
        "Natural numbers",
        "Decimals",
        "Large numbers",
        "Money",
        "Fractions",
    ]

    choose(at, "tr_number_type", "Money")
    assert [box.label for box in at.checkbox] == ["Addition", "Subtraction", "Division", "Percentage"]
    assert [box.value for box in at.checkbox] == [True, False, False, False]
    assert list(at.button_group(key="tr_level_Money_Division").options) == LEVELS


def test_special_trainings_offers_seven_trainings_with_a_description():
    at = open_trainer()
    choose(at, "tr_category", "Special trainings")
    assert list(at.button_group(key="tr_special").options) == [
        "Word problems",
        "Mixed tasks",
        "Digit sums",
        "Rule of three",
        "Equations",
        "Chain calculations",
        "Fun with fractions",
    ]
    choose(at, "tr_special", "Equations")
    assert "Find the number that x stands for." in page_text(at)


def test_three_modes_with_the_limits_of_the_brief():
    at = open_trainer()
    assert list(at.button_group(key="tr_mode").options) == [
        "Task count",
        "Total time",
        "Time per task",
    ]
    expected = {
        "Task count": ("tr_limit_tasks", 5, 100),
        "Total time": ("tr_limit_total", 30, 900),
        "Time per task": ("tr_limit_per_task", 1, 60),
    }
    for mode, (key, low, high) in expected.items():
        choose(at, "tr_mode", mode)
        limit = at.number_input(key=key)
        assert (limit.min, limit.max) == (low, high)
        assert low <= limit.value <= high


def test_setup_shows_an_example_task_for_the_selection():
    at = open_trainer()
    choose(at, "tr_operation", "Square root")
    assert "Example task" in page_text(at)
    assert "√" in page_text(at)


def test_history_is_empty_at_first():
    assert "No finished sessions yet" in page_text(open_trainer())


# --- Starting a session ---


def test_starting_shows_a_task_and_the_status(fast_sleep):
    at = start(open_trainer())
    assert phase(at) == "running"
    assert at.session_state["tr_task"].text in page_text(at)
    assert metrics(at)["Task"] == "1 of 10"
    assert {"Time", "Correct", "Wrong or skipped"} <= set(metrics(at))


def test_countdown_runs_before_the_session_starts():
    at = open_trainer()
    clicked = datetime.now(timezone.utc)
    start(at)
    assert at.session_state["tr_session"].started_at - clicked >= timedelta(seconds=2.9)


def test_operations_session_uses_the_chosen_operation_and_level(fast_sleep):
    at = open_trainer()
    choose(at, "tr_operation", "Percentage")
    choose(at, "tr_level", "Hard")
    start(at)

    settings = at.session_state["tr_session"].settings
    assert (settings.category, settings.name) == ("Operations", "Percentage")
    assert settings.topics == (Topic("Natural numbers", "Percentage", "Hard"),)
    assert "% of" in at.session_state["tr_task"].text


def test_number_type_session_mixes_the_ticked_operations_with_their_own_levels(fast_sleep):
    at = open_trainer()
    choose(at, "tr_category", "Number types")
    choose(at, "tr_number_type", "Decimals")
    at.checkbox(key="tr_use_Decimals_Division").check().run()
    choose(at, "tr_level_Decimals_Division", "Hard")
    start(at)

    settings = at.session_state["tr_session"].settings
    assert (settings.category, settings.name) == ("Number types", "Decimals")
    assert settings.topics == (
        Topic("Decimals", "Addition", "Easy"),
        Topic("Decimals", "Division", "Hard"),
    )


def test_number_type_without_any_operation_is_rejected_and_nothing_starts(fast_sleep):
    at = open_trainer()
    choose(at, "tr_category", "Number types")
    at.checkbox(key="tr_use_Natural numbers_Addition").uncheck().run()
    start(at)

    assert phase(at) == "setup"
    assert "tr_session" not in at.session_state
    assert "Select at least one operation." in [error.value for error in at.error]


def test_special_training_session(fast_sleep):
    at = open_trainer()
    choose(at, "tr_category", "Special trainings")
    choose(at, "tr_special", "Equations")
    choose(at, "tr_special_level", "Medium")
    start(at)

    settings = at.session_state["tr_session"].settings
    assert settings.topics == (Topic("Special trainings", "Equations", "Medium"),)
    assert "Solve for x" in page_text(at)


def test_mode_and_limit_are_taken_from_the_setup_screen(fast_sleep):
    at = start_with(open_trainer(), "Time per task", 7)
    settings = at.session_state["tr_session"].settings
    assert (settings.mode, settings.limit) == ("Time per task", 7)
    assert "Time left for this task" in metrics(at)


# --- Answers (MB R3) ---


def test_correct_answer_adds_a_point_and_shows_a_new_task(fast_sleep):
    at = start(open_trainer())
    task = at.session_state["tr_task"]
    submit(at, right_answer(at))

    assert at.session_state["tr_session"].correct == 1
    assert at.session_state["tr_task"] != task
    assert metrics(at)["Correct"] == "1"
    assert [box.value for box in at.success] == [f"Correct! {task.solution}"]


def test_wrong_answer_shows_the_correct_answer_and_the_solution(fast_sleep):
    at = start(open_trainer())
    task = at.session_state["tr_task"]
    submit(at, "99999")

    assert at.session_state["tr_session"].wrong == 1
    assert at.session_state["tr_session"].correct == 0
    assert at.session_state["tr_task"] != task  # the wrong task is not repeated
    (shown,) = [box.value for box in at.error]
    assert "99999" in shown
    assert format_answer(task) in shown
    assert task.solution in shown


def test_skip_is_recorded_and_shows_the_answer(fast_sleep):
    at = start(open_trainer())
    task = at.session_state["tr_task"]
    skip(at)

    session = at.session_state["tr_session"]
    assert (session.skipped, session.wrong) == (1, 0)
    assert at.session_state["tr_task"] != task
    assert metrics(at)["Wrong or skipped"] == "1"
    assert task.solution in "\n".join(box.value for box in at.warning)


@pytest.mark.parametrize("text", ["", "abc", "5.5", "1,000"])
def test_empty_or_unreadable_input_keeps_the_same_task_and_shows_a_hint(fast_sleep, text):
    at = start(open_trainer())
    task = at.session_state["tr_task"]
    session = at.session_state["tr_session"]
    submit(at, text)

    assert at.session_state["tr_session"] == session
    assert at.session_state["tr_task"] == task
    assert [box.value for box in at.warning] == [ANSWER_HINTS[AnswerKind.WHOLE]]


def test_hint_disappears_with_the_next_valid_answer(fast_sleep):
    at = start(open_trainer())
    submit(at, "abc")
    submit(at, right_answer(at))
    assert not at.warning


def test_decimal_answers_are_typed_with_a_point(fast_sleep):
    at = open_trainer()
    choose(at, "tr_category", "Number types")
    choose(at, "tr_number_type", "Decimals")
    start(at)
    submit(at, right_answer(at).replace(".", ","))  # a comma is not evaluated
    assert at.session_state["tr_session"].attempts == ()
    assert [box.value for box in at.warning] == [ANSWER_HINTS[AnswerKind.DECIMAL]]

    submit(at, right_answer(at))
    assert at.session_state["tr_session"].correct == 1


def test_money_answers_are_accepted_with_the_euro_sign(fast_sleep):
    at = open_trainer()
    choose(at, "tr_category", "Number types")
    choose(at, "tr_number_type", "Money")
    start(at)
    submit(at, "€" + right_answer(at))
    assert at.session_state["tr_session"].correct == 1


def test_fraction_that_is_not_simplified_is_not_evaluated(fast_sleep):
    at = open_trainer()
    choose(at, "tr_category", "Number types")
    choose(at, "tr_number_type", "Fractions")
    start(at)
    answer = at.session_state["tr_task"].answer
    submit(at, f"{answer.numerator * 2}/{answer.denominator * 2}")  # right value, not simplified

    assert at.session_state["tr_session"].attempts == ()
    assert [box.value for box in at.warning] == [ANSWER_HINTS[AnswerKind.FRACTION]]

    submit(at, right_answer(at))
    assert at.session_state["tr_session"].correct == 1


# --- Mode: task count ---


def test_task_count_session_ends_after_the_last_task_and_shows_the_result(fast_sleep):
    at = start_with(open_trainer(), "Task count", 5)
    submit(at, right_answer(at))
    submit(at, right_answer(at))
    submit(at, "99999")
    skip(at)
    assert phase(at) == "running"
    assert metrics(at)["Task"] == "5 of 5"
    submit(at, right_answer(at))

    assert phase(at) == "result"
    shown = metrics(at)
    assert (shown["Correct"], shown["Wrong"], shown["Skipped"]) == ("3", "1", "1")
    assert shown["Accuracy"] == "60.0%"
    assert "All tasks done." in page_text(at)
    assert "Not answered in time" not in page_text(at)


def test_result_reviews_every_task_and_explains_the_missed_ones(fast_sleep):
    at = start_with(open_trainer(), "Task count", 5)
    missed = at.session_state["tr_task"]
    submit(at, "99999")
    for _ in range(4):
        submit(at, right_answer(at))

    review = at.dataframe[0].value
    assert list(review.columns) == ["Task", "Your answer", "Correct answer", "Result", "Seconds"]
    assert list(review["Result"]) == ["Wrong", "Correct", "Correct", "Correct", "Correct"]
    assert review.loc[0, "Task"] == missed.text
    assert review.loc[0, "Your answer"] == "99999"
    assert review.loc[0, "Correct answer"] == format_answer(missed)
    assert "How to solve the ones you missed" in page_text(at)
    assert missed.solution in page_text(at)


def test_result_without_mistakes_has_no_missed_section(fast_sleep):
    at = start_with(open_trainer(), "Task count", 5)
    for _ in range(5):
        submit(at, right_answer(at))
    assert metrics(at)["Accuracy"] == "100.0%"
    assert "How to solve the ones you missed" not in page_text(at)


# --- Mode: total time ---


def test_total_time_session_ends_when_the_time_is_up(fast_sleep):
    at = start_with(open_trainer(), "Total time", 30)
    submit(at, right_answer(at))
    unanswered = at.session_state["tr_task"]
    move_clock(at, 31)
    at.run()
    assert not at.exception

    assert phase(at) == "result"
    assert "Time's up." in page_text(at)
    assert metrics(at)["Correct"] == "1"
    assert metrics(at)["Time"] == "0:30"
    assert "Not answered in time" in page_text(at)
    assert unanswered.solution in page_text(at)


def test_answer_after_the_total_time_does_not_count(fast_sleep):
    at = start_with(open_trainer(), "Total time", 30)
    answer = right_answer(at)
    move_clock(at, 31)
    submit(at, answer)

    assert phase(at) == "result"
    assert metrics(at)["Correct"] == "0"
    assert [saved.correct for saved in trainer_db.list_sessions()] == [0]


def test_total_time_keeps_running_while_there_is_time_left(fast_sleep):
    at = start_with(open_trainer(), "Total time", 30)
    move_clock(at, 20)
    submit(at, right_answer(at))
    assert phase(at) == "running"
    assert metrics(at)["Time left"] in ("0:10", "0:09")


# --- Mode: time per task ---


def test_session_ends_when_one_task_takes_too_long(fast_sleep):
    at = start_with(open_trainer(), "Time per task", 5)
    submit(at, right_answer(at))
    move_clock(at, 6)
    at.run()
    assert not at.exception

    assert phase(at) == "result"
    assert "took too long" in page_text(at)
    assert metrics(at)["Correct"] == "1"


def test_every_answer_restarts_the_time_per_task(fast_sleep):
    at = start_with(open_trainer(), "Time per task", 5)
    for _ in range(3):
        move_clock(at, 4)  # 12 seconds in total, but never 5 on one task
        submit(at, right_answer(at))
    assert phase(at) == "running"
    assert at.session_state["tr_session"].correct == 3


def test_late_answer_in_time_per_task_does_not_count(fast_sleep):
    at = start_with(open_trainer(), "Time per task", 5)
    answer = right_answer(at)
    move_clock(at, 5)
    submit(at, answer)
    assert phase(at) == "result"
    assert metrics(at)["Correct"] == "0"


# --- Ending early ---


def test_ended_session_saves_nothing_and_returns_to_the_setup(fast_sleep):
    at = start(open_trainer())
    submit(at, right_answer(at))
    at.button(key="tr_abort").click().run()
    assert not at.exception

    assert phase(at) == "setup"
    assert trainer_db.list_sessions() == []
    assert "No finished sessions yet" in page_text(at)


def test_ending_after_the_time_is_up_still_saves_the_session(fast_sleep):
    at = start_with(open_trainer(), "Total time", 30)
    submit(at, right_answer(at))
    move_clock(at, 31)
    at.button(key="tr_abort").click().run()
    assert not at.exception

    assert phase(at) == "result"
    assert [saved.correct for saved in trainer_db.list_sessions()] == [1]


def test_leaving_the_section_during_a_session_saves_nothing(fast_sleep):
    at = start(open_trainer())
    submit(at, right_answer(at))
    go_to(at, "Tests")
    go_to(at, "Trainer")

    assert phase(at) == "setup"
    assert trainer_db.list_sessions() == []


def test_training_and_tests_do_not_disturb_each_other(fast_sleep):
    at = start_with(open_trainer(), "Task count", 5)
    for _ in range(5):
        skip(at)
    go_to(at, "Tests")
    at.button(key="start").click().run()
    assert not at.exception

    assert at.session_state["phase"] == "running"
    assert at.session_state["current_task"].text in page_text(at)
    assert db.list_runs() == []  # a trainer session is not a test run
    assert len(trainer_db.list_sessions()) == 1


# --- Saving and history ---


def test_finished_session_is_saved_once_with_its_settings(fast_sleep):
    at = open_trainer()
    choose(at, "tr_operation", "Square")
    choose(at, "tr_level", "Medium")
    start_with(at, "Task count", 5)
    for _ in range(5):
        submit(at, right_answer(at))
    at.run()
    at.run()
    assert not at.exception

    (saved,) = trainer_db.list_sessions()
    assert (saved.category, saved.name, saved.levels) == ("Operations", "Square", "Medium")
    assert (saved.mode, saved.limit) == ("Task count", 5)
    assert (saved.correct, saved.wrong, saved.skipped) == (5, 0, 0)
    assert saved.finished_at.utcoffset() == timedelta(0)


def test_change_settings_returns_to_the_setup_with_the_choices_kept_and_the_history(fast_sleep):
    at = open_trainer()
    choose(at, "tr_operation", "Square")
    start_with(at, "Task count", 5)
    for _ in range(5):
        skip(at)
    at.button(key="tr_change").click().run()
    assert not at.exception

    assert phase(at) == "setup"
    assert at.button_group(key="tr_operation").value == "Square"
    assert at.number_input(key="tr_limit_tasks").value == 5
    history = at.dataframe[0].value
    assert list(history["Training"]) == ["Square"]
    assert list(history["Mode"]) == ["5 tasks"]
    assert list(history["Skipped"]) == [5]


def test_train_again_starts_a_new_session_with_the_same_settings(fast_sleep):
    at = start_with(open_trainer(), "Task count", 5)
    first = at.session_state["tr_session"].settings
    for _ in range(5):
        skip(at)
    at.button(key="tr_again").click().run()
    assert not at.exception

    assert phase(at) == "running"
    assert at.session_state["tr_session"].settings == first
    assert at.session_state["tr_session"].attempts == ()
    assert metrics(at)["Task"] == "1 of 5"


def test_history_is_still_shown_after_a_restart(fast_sleep):
    at = start_with(open_trainer(), "Task count", 5)
    for _ in range(5):
        submit(at, right_answer(at))

    reopened = open_trainer()  # a new session on the same database file
    history = reopened.dataframe[0].value
    assert list(history["Training"]) == ["Addition"]
    assert list(history["Correct"]) == [5]


def test_history_shows_the_newest_ten_sessions(fast_sleep):
    at = start_with(open_trainer(), "Task count", 5)
    for _ in range(11):
        for _ in range(5):
            skip(at)
        at.button(key="tr_again").click().run()
    at.button(key="tr_abort").click().run()
    assert not at.exception

    assert len(trainer_db.list_sessions()) == 11
    assert len(at.dataframe[0].value) == 10


# --- Structure (AGENTS.md) ---


def test_trainer_screens_contain_no_sql():
    source = (ROOT / "trainer_ui.py").read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "SELECT " not in source
'''


# (file, what the edit is for, exact old text, new text)
EDITS = [
    (
        "app.py",
        "import the Trainer screens",
        "import db\nfrom runs import (",
        "import db\nimport trainer_ui\nfrom runs import (",
    ),
    (
        "app.py",
        "end a running training when the user switches section",
        '    state.pop("result", None)\n    state.phase = "select"\n\n\n# --- Screens ---',
        '    state.pop("result", None)\n    state.phase = "select"\n    trainer_ui.leave()'
        "\n\n\n# --- Screens ---",
    ),
    (
        "app.py",
        "show the Trainer instead of 'Coming soon'",
        '    if section == "Tests":\n        render_tests()\n    else:\n',
        '    if section == "Tests":\n        render_tests()\n'
        '    elif section == "Trainer":\n        trainer_ui.render()\n    else:\n',
    ),
    (
        "tests/test_app.py",
        "the Trainer is no longer a 'Coming soon' section",
        '@pytest.mark.parametrize("section", ["Trainer", "Knowledge", "Games", "Profile"])',
        '@pytest.mark.parametrize("section", ["Knowledge", "Games", "Profile"])',
    ),
    (
        "tests/test_app.py",
        "leave a running test through Knowledge instead of the Trainer",
        '    go_to(at, "Trainer")\n    assert "Coming soon" in page_text(at)\n    go_to(at, "Tests")',
        '    go_to(at, "Knowledge")\n    assert "Coming soon" in page_text(at)\n    go_to(at, "Tests")',
    ),
    (
        "AGENTS.md",
        "list the Trainer files in the project structure",
        "- `tests/` \u2013 one test file per module",
        "- `trainer_tasks.py` \u2013 Trainer task generation and answer checking for all number "
        "types and special trainings (spec 002)\n"
        "- `trainer.py` \u2013 Trainer session rules: settings, modes, time limits, result\n"
        "- `trainer_db.py` \u2013 SQLite storage of finished Trainer sessions, in its own table "
        "`trainer_sessions`\n"
        "- `trainer_ui.py` \u2013 Trainer screens (Streamlit only). `app.py` calls its `render()` "
        "and `leave()`\n"
        "- `tests/` \u2013 one test file per module",
    ),
]


def create_files() -> None:
    print("Trainer files:")
    for relative, content in FILES.items():
        path = ROOT / relative
        wanted = content.encode("utf-8")
        if path.exists():
            same = path.is_file() and path.read_bytes() == wanted
            note = "already installed" if same else "exists with other content, NOT overwritten"
            print(f"  kept     {relative} ({note})")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(wanted)
        print(f"  created  {relative}")


def make_edits() -> list[tuple[str, str, str, str]]:
    """Make each edit whose old text is found exactly once. Return the ones left to do."""
    print("Edits:")
    left = []
    for relative, purpose, old, new in EDITS:
        path = ROOT / relative
        text = path.read_bytes().decode("utf-8") if path.is_file() else ""
        if new in text:
            status = "already done"
        elif text.count(old) == 1:
            path.write_bytes(text.replace(old, new).encode("utf-8"))
            status = "done"
        else:
            status = "NOT DONE"
            left.append((relative, purpose, old, new))
        print(f"  {status:13}{relative}: {purpose}")
    return left


def main() -> None:
    missing = [name for name in NEEDED if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(
            f"Stopped. Nothing was changed. Not found next to this file: {', '.join(missing)}.\n"
            "Save install_trainer.py in the project root (next to app.py), on a branch that "
            "contains the Tests code, for example 001-tests."
        )

    create_files()
    left = make_edits()

    if left:
        print("\nThese edits could not be made, because the file looks different than expected.")
        print("Make them by hand:")
        for relative, purpose, old, new in left:
            print(f"\n--- {relative}: {purpose}\nReplace:\n{old}\nWith:\n{new}")

    print("\nNext steps:")
    print("  1. uv run pytest")
    print("  2. uv run streamlit run app.py   (then open the Trainer tab)")
    print("  3. Delete install_trainer.py")


if __name__ == "__main__":
    main()