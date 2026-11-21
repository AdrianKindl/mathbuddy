"""Trainer task generation and answer checking (spec 002).

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
