"""Textbook rules: navigation (T R3) and practice (T R6–T R10).

No Streamlit, no SQL, no clock. Randomness only comes from the random.Random
passed in. The practice ranges follow the "Practice catalogue" of
"docs/textbook-brief new.md" with the decisions in specs/010-textbook.md.

Every task carries its `template`: the calculation over its `values`. The
answer of a typed task is that calculation, worked out exactly with fractions.
"""

import math
import random
import re
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from fractions import Fraction
from itertools import permutations

from tasks import LEVELS
from textbook_content import category_of, get_article

ROUND_LENGTH = 10
F = Fraction


# --- Navigation (T R3) ---


def _ids_around(article_id: str) -> list[str]:
    return [article.id for article in category_of(article_id).articles]


def neighbours(article_id: str) -> tuple[str | None, str | None]:
    """The previous and next article in the same category, or None at either end."""
    ids = _ids_around(article_id)
    index = ids.index(article_id)
    previous = ids[index - 1] if index > 0 else None
    following = ids[index + 1] if index < len(ids) - 1 else None
    return previous, following


def position(article_id: str) -> tuple[int, int]:
    """The article's place in its category, counted from 1, and the category size."""
    ids = _ids_around(article_id)
    return ids.index(article_id) + 1, len(ids)


# --- Tasks and answer types (T R7) ---


# StrEnum, compared with ==: Streamlit re-imports a changed module, while a Round
# in session_state keeps members of the old class. Values still compare equal.
class AnswerType(StrEnum):
    WHOLE = "whole"
    DECIMAL = "decimal"
    CHOICE = "choice"
    ESTIMATE = "estimate"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    SKIPPED = "skipped"
    IGNORED = "ignored"


class Status(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass(frozen=True)
class TextbookTask:
    article_id: str
    template: str
    values: tuple[tuple[str, int | Fraction], ...]
    prompt: str
    kind: AnswerType
    answer: Fraction | None = None  # the exact result; None for a choice
    decimals: int | None = None  # for a decimal answer
    percent: bool = False  # a decimal answer that is a percentage
    choices: tuple[str, ...] = ()
    correct_choice: str | None = None


_WHOLE = re.compile(r"[-−]?\d+")
_DECIMAL = re.compile(r"[-−]?\d+(?:[.,]\d+)?\s*%?")


def _parse_whole(raw: str) -> int | None:
    text = raw.strip()
    if not _WHOLE.fullmatch(text):
        return None
    return int(text.replace("−", "-"))


def _parse_decimal(raw: str) -> Fraction | None:
    text = raw.strip()
    if not _DECIMAL.fullmatch(text):
        return None
    number = text.removesuffix("%").strip().replace(",", ".").replace("−", "-")
    return F(number)


def round_half_away(value: Fraction, decimals: int) -> Fraction:
    """Round to `decimals` places; a half goes away from zero (decision 1)."""
    scaled = abs(value) * 10**decimals
    rounded = math.floor(scaled + F(1, 2))
    return (1 if value >= 0 else -1) * F(rounded, 10**decimals)


def accepted_range(task: TextbookTask) -> tuple[int, int]:
    """The whole numbers within ±10 % of an estimate's exact result, limits included."""
    exact = task.answer
    return math.ceil(exact * F(9, 10)), math.floor(exact * F(11, 10))


def evaluate(task: TextbookTask, raw: str) -> Outcome:
    """Check one answer. Input that does not fit the answer type is IGNORED (T R8)."""
    if task.kind == AnswerType.CHOICE:
        if raw not in task.choices:
            return Outcome.IGNORED
        return Outcome.CORRECT if raw == task.correct_choice else Outcome.WRONG

    if task.kind == AnswerType.DECIMAL:
        given = _parse_decimal(raw)
        if given is None:
            return Outcome.IGNORED
        right = given == round_half_away(task.answer, task.decimals)
        return Outcome.CORRECT if right else Outcome.WRONG

    given = _parse_whole(raw)
    if given is None:
        return Outcome.IGNORED
    if task.kind == AnswerType.ESTIMATE:
        low, high = accepted_range(task)
        return Outcome.CORRECT if low <= given <= high else Outcome.WRONG
    return Outcome.CORRECT if given == task.answer else Outcome.WRONG


def _minus(text: str) -> str:
    return text.replace("-", "−")


def _short(value: Fraction, decimals: int) -> str:
    """At most `decimals` places, without trailing zeros, with thousands commas."""
    rounded = round_half_away(value, decimals)
    text = f"{float(rounded):,.{decimals}f}" if decimals else f"{int(rounded):,}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return _minus(text)


def answer_text(task: TextbookTask) -> str:
    """The correct answer as shown after a wrong answer or skip (T R8)."""
    if task.kind == AnswerType.CHOICE:
        return task.correct_choice
    if task.kind == AnswerType.DECIMAL:
        rounded = round_half_away(task.answer, task.decimals)
        text = _minus(f"{float(rounded):,.{task.decimals}f}")
        return f"{text} %" if task.percent else text
    if task.kind == AnswerType.ESTIMATE:
        low, high = accepted_range(task)
        return f"{_short(task.answer, 2)} (accepted: {low:,} to {high:,})"
    return _minus(f"{int(task.answer):,}")


# --- Building tasks ---


def _digits(x) -> int:
    return len(str(int(x)))


def _root(n) -> int:
    n = int(n)
    return 9 if n % 9 == 0 else n % 9


def _computed(template: str, values: dict) -> Fraction:
    env = {name: F(value) for name, value in values.items()}
    env.update(digits=_digits, root=_root)
    return F(eval(template, {"__builtins__": {}}, env))  # noqa: S307 - our own templates


def _task(article_id, template, values, prompt, kind, *, decimals=None, percent=False,
          choices=(), correct=None) -> TextbookTask:  # fmt: skip
    answer = None if kind == AnswerType.CHOICE else _computed(template, values)
    return TextbookTask(
        article_id, template, tuple(values.items()), prompt, kind, answer,
        decimals, percent, tuple(choices), correct,
    )  # fmt: skip


def _places_note(decimals: int) -> str:
    return f" ({decimals} decimal place{'s' if decimals > 1 else ''})"


def _dec(value: Fraction) -> str:
    """A terminating decimal as text, e.g. 2.5 or 0.04."""
    if value.denominator == 1:
        return f"{int(value):,}"
    places = 0
    while (value * 10**places).denominator != 1:
        places += 1
    return f"{float(value):.{places}f}"


def _signed(n: int) -> str:
    return f"(−{-n})" if n < 0 else str(n)


def _num(n) -> str:
    return _dec(F(n))


def _sign_word(p: int) -> str:
    return f"rises by {p} %" if p > 0 else f"falls by {-p} %"


# --- One builder per article. Each takes the level and the random generator. ---


def _b1(level, rng):
    r = rng.randint
    while True:
        if level == "Easy":
            v = {"a": r(2, 9), "b": r(2, 9), "c": r(2, 9)}
            template, text = "a+b*c", "{a} + {b} × {c}"
        elif level == "Medium":
            v = {n: r(2, 12) for n in "abcd"}
            template, text = rng.choice([("a*b-c*d", "{a} × {b} − {c} × {d}"),
                                         ("a+b*c-d", "{a} + {b} × {c} − {d}")])  # fmt: skip
        elif level == "Hard":
            e = r(2, 20)
            d = rng.choice([m for m in range(e, 21, e)])
            v = {"a": r(2, 20), "b": r(2, 20), "c": r(2, 20), "d": d, "e": e}
            template, text = "(a+b)*c-d/e", "({a} + {b}) × {c} − {d} ÷ {e}"
        else:
            v = {n: r(2, 20) for n in "abcdefg"}
            if (v["e"] * v["f"]) % v["g"]:
                continue
            template, text = "(a-b)*(c+d)-e*f/g", "({a} − {b}) × ({c} + {d}) − {e} × {f} ÷ {g}"
        if _computed(template, v) >= 0:
            return _task("B1", template, v, "Calculate " + text.format(**v), AnswerType.WHOLE)


def _b2(level, rng):
    r = rng.randint
    if level == "Easy":
        a, b = r(1, 20), -r(1, 20)
        template, op = rng.choice([("a+b", "+"), ("a-b", "−")])
        return _task("B2", template, {"a": a, "b": b}, f"Calculate {a} {op} {_signed(b)}",
                     AnswerType.WHOLE)  # fmt: skip
    if level == "Medium":
        if rng.random() < 2 / 3:
            a, b = -r(1, 12), -r(1, 12)
            template, op = rng.choice([("a+b", "+"), ("a-b", "−")])
        else:
            a, b = -r(1, 12), r(1, 12)
            template, op = "a*b", "×"
        return _task("B2", template, {"a": a, "b": b},
                     f"Calculate {_signed(a)} {op} {_signed(b)}", AnswerType.WHOLE)  # fmt: skip
    if level == "Hard":
        sign = lambda: rng.choice([1, -1])  # noqa: E731
        if rng.random() < 0.5:
            a, b = sign() * r(2, 20), sign() * r(2, 20)
            template, op = "a*b", "×"
        else:
            b, q = sign() * r(2, 20), sign() * r(2, 20)
            a, template, op = b * q, "a/b", "÷"
        return _task("B2", template, {"a": a, "b": b},
                     f"Calculate {_signed(a)} {op} {_signed(b)}", AnswerType.WHOLE)  # fmt: skip
    v = {"a": -r(2, 15), "b": -r(2, 15), "c": -r(2, 15), "d": r(2, 15)}
    prompt = (f"Calculate {_signed(v['a'])} × {_signed(v['b'])} − "
              f"{_signed(v['c'])} × {v['d']}")  # fmt: skip
    return _task("B2", "a*b-c*d", v, prompt, AnswerType.WHOLE)


def _b3(level, rng):
    one = lambda: F(rng.randint(1, 99), 10)  # noqa: E731
    two = lambda: F(rng.randint(1, 999), 100)  # noqa: E731
    note = _places_note(2)

    def sum_or_difference(make):
        a, b = make(), make()
        if rng.random() < 0.5:
            return "a+b", {"a": a, "b": b}, f"{_dec(a)} + {_dec(b)}"
        a, b = max(a, b), min(a, b)
        return "a-b", {"a": a, "b": b}, f"{_dec(a)} − {_dec(b)}"

    while True:
        if level == "Easy":
            template, v, text = sum_or_difference(one)
        elif level == "Medium":
            kind = rng.choice(["sum", "times", "by10", "by100"])
            if kind == "sum":
                template, v, text = sum_or_difference(two)
            elif kind == "times":
                v = {"a": two(), "b": rng.choice([10, 100])}
                template, text = "a*b", f"{_dec(v['a'])} × {v['b']}"
            elif kind == "by10":
                v = {"a": F(rng.randint(1, 999), 10), "b": 10}
                template, text = "a/b", f"{_dec(v['a'])} ÷ 10"
            else:
                v = {"a": rng.randint(1, 999), "b": 100}
                template, text = "a/b", f"{v['a']} ÷ 100"
        elif level == "Hard":
            v = {"a": one(), "b": one()}
            template, text = "a*b", f"{_dec(v['a'])} × {_dec(v['b'])}"
        else:
            v = {"a": one(), "b": one(), "c": one()}
            template, text = "a*b-c", f"{_dec(v['a'])} × {_dec(v['b'])} − {_dec(v['c'])}"
        if _computed(template, v) >= 0:
            return _task("B3", template, v, f"Calculate {text}{note}", AnswerType.DECIMAL,
                         decimals=2)  # fmt: skip


EXACT_PERCENTS = [F(p) for p in ("10", "12.5", "20", "25", "37.5", "40", "50", "60", "62.5",
                                 "75", "80", "87.5")]  # fmt: skip


def _fractions(denominators) -> list[Fraction]:
    return [F(n, d) for d in denominators for n in range(1, d) if math.gcd(n, d) == 1]


def _repeating(value: Fraction) -> str:
    """A decimal with its first four places, and "…" when it goes on."""
    if (value * 10**4).denominator == 1:
        return _dec(value)
    return f"{math.floor(value * 10**4) / 10**4:.4f}…"


def _f1(level, rng):
    if level == "Pro":
        p = rng.choice(EXACT_PERCENTS)
        step = (p / 100).denominator
        n = step * rng.randint(max(1, -(-10 // step)), 1000 // step)
        return _task("F1", "p/100*n", {"p": p, "n": n}, f"What is {_dec(p)} % of {n:,}?",
                     AnswerType.WHOLE)  # fmt: skip
    pool = _fractions({"Easy": (2, 4, 5, 10), "Medium": (8,), "Hard": (3, 6, 12)}[level])
    f = rng.choice(pool)
    shapes = {"Easy": ["percent"], "Medium": ["percent", "decimal"],
              "Hard": ["percent", "decimal", "fraction"]}[level]  # fmt: skip
    shape = rng.choice(shapes)
    name = f"{f.numerator}/{f.denominator}"
    if shape == "percent":
        return _task("F1", "f*100", {"f": f}, f"Write {name} as a percent{_places_note(1)}",
                     AnswerType.DECIMAL, decimals=1, percent=True)  # fmt: skip
    if shape == "decimal":
        return _task("F1", "f", {"f": f}, f"Write {name} as a decimal{_places_note(3)}",
                     AnswerType.DECIMAL, decimals=3)  # fmt: skip
    others = rng.sample([g for g in pool if g != f], 3)
    choices = [f"{g.numerator}/{g.denominator}" for g in [f, *others]]
    rng.shuffle(choices)
    return _task("F1", "fraction", {"f": f}, f"Which fraction is {_repeating(f)}?",
                 AnswerType.CHOICE, choices=choices, correct=name)  # fmt: skip


def _f2(level, rng):
    low, high = {"Easy": (2, 9), "Medium": (5, 12), "Hard": (7, 20), "Pro": (11, 30)}[level]
    r = rng.randint
    if level in ("Hard", "Pro") and rng.random() < 0.2:
        while True:  # two different names for the same value
            q = r(2, 10)
            p = r(1, q - 1)
            multiples = [m for m in range(1, 31) if low <= q * m <= high]
            if math.gcd(p, q) == 1 and len(multiples) >= 2:
                m1, m2 = rng.sample(multiples, 2)
                a, b, c, d = p * m1, q * m1, p * m2, q * m2
                break
    else:
        while True:
            b, d = r(low, high), r(low, high)
            a, c = r(1, b - 1), r(1, d - 1)
            gap = abs(F(a, b) - F(c, d))
            if gap and {"Easy": gap >= F("0.1"), "Medium": F("0.02") <= gap <= F("0.1"),
                        "Hard": gap < F("0.05"), "Pro": gap < F("0.02")}[level]:  # fmt: skip
                break
    first, second = f"{a}/{b}", f"{c}/{d}"
    x, y = F(a, b), F(c, d)
    correct = "Equal" if x == y else (first if x > y else second)
    return _task("F2", "compare", {"a": a, "b": b, "c": c, "d": d},
                 f"Which is larger: {first} or {second}?", AnswerType.CHOICE,
                 choices=(first, second, "Equal"), correct=correct)  # fmt: skip


F3_SMALL = [F(n, 100) for n in (25, 36, 49, 64, 81)]
F3_ALL = [F(n * n, 100) for n in range(2, 10)] + [F("1.21"), F("1.44"), F("2.25"), F(4)]


def _sqrt(x: Fraction) -> Fraction:
    return F(math.isqrt(x.numerator), math.isqrt(x.denominator))


def _f3(level, rng):
    x = rng.choice(F3_SMALL if level in ("Easy", "Medium") else F3_ALL)
    sizes = {"x²": x * x, "x": x, "√x": _sqrt(x)}
    shown = f"x = {_dec(x)}."
    if level == "Pro":
        right = " < ".join(sorted(sizes, key=sizes.get))
        orders = [" < ".join(order) for order in permutations(["x²", "x", "√x"])]
        choices = [right, *rng.sample([o for o in orders if o != right], 3)]
        rng.shuffle(choices)
        return _task("F3", "order", {"x": x},
                     f"{shown} Order x², x and √x from smallest to largest.",
                     AnswerType.CHOICE, choices=choices, correct=right)  # fmt: skip
    template, pair = {"Easy": ("square_vs_x", ["x²", "x"]), "Medium": ("root_vs_x", ["√x", "x"]),
                      "Hard": ("square_vs_root", ["x²", "√x"])}[level]  # fmt: skip
    rng.shuffle(pair)
    right = max(pair, key=sizes.get)
    return _task("F3", template, {"x": x}, f"{shown} Which is larger, {pair[0]} or {pair[1]}?",
                 AnswerType.CHOICE, choices=pair, correct=right)  # fmt: skip


def _c1(level, rng):
    count = 2 if level in ("Easy", "Medium") else 3
    sizes = {"Easy": [10, 20], "Medium": list(range(5, 31, 5)), "Hard": list(range(5, 31, 5)),
             "Pro": list(range(1, 31))}[level]  # fmt: skip
    changes = [rng.choice(sizes) * rng.choice([1, -1]) for _ in range(count)]
    v = {f"p{i}": p for i, p in enumerate(changes, start=1)}
    chain = "*".join(f"(1+p{i}/100)" for i in range(1, count + 1))
    words = ", then ".join(_sign_word(p) for p in changes)
    prompt = (f"A value {words}. What is the total change in percent?"
              f"{_places_note(1)}")  # fmt: skip
    return _task("C1", f"({chain}-1)*100", v, prompt, AnswerType.DECIMAL, decimals=1,
                 percent=True)  # fmt: skip


DOUBLING_EASY = [2, 3, 4, 6, 8, 9, 12]
DOUBLING_MEDIUM = DOUBLING_EASY + [18, 24, 36]


def _c2(level, rng):
    if level == "Easy" or (level == "Medium" and rng.random() < 0.7):
        r = rng.choice(DOUBLING_EASY if level == "Easy" else DOUBLING_MEDIUM)
        prompt = (f"With the rule of 72, how many years does it take to double at {r} % "
                  "growth per year?")  # fmt: skip
        return _task("C2", "72/r", {"r": r}, prompt, AnswerType.WHOLE)
    if level == "Medium":
        r = rng.choice([2, 3, 6])
        prompt = (f"Using 114 instead of 72, how many years does it take to triple at {r} % "
                  "growth per year?")  # fmt: skip
        return _task("C2", "114/r", {"r": r}, prompt, AnswerType.WHOLE)
    if level == "Hard":
        s, r, k = rng.randint(5, 50), rng.choice(DOUBLING_EASY), rng.randint(1, 3)
        t = k * 72 // r
        prompt = (f"A market worth {s} bn grows by {r} % per year. With the rule of 72, what "
                  f"is it worth in bn after {t} years?")  # fmt: skip
        return _task("C2", "s*2**k", {"s": s, "r": r, "k": k, "t": t}, prompt, AnswerType.WHOLE)
    r, k = rng.choice(DOUBLING_MEDIUM), rng.choice([2, 3])
    prompt = (f"At {r} % growth per year, how many years until the value is {2**k} times as "
              "large? Use the rule of 72.")  # fmt: skip
    return _task("C2", "72/r*k", {"r": r, "k": k}, prompt, AnswerType.WHOLE)


def _c3(level, rng):
    note = _places_note(1)
    if level == "Easy":
        if rng.random() < 0.5:  # markup: cost in twenties, markup in fives
            c, m = 20 * rng.randint(1, 10), 5 * rng.randint(1, 40)
            p, template, asked = c * (100 + m) // 100, "(p-c)/c*100", "markup"
        else:  # margin: price in twenties, margin in fives
            p, g = 20 * rng.randint(1, 20), 5 * rng.randint(1, 16)
            c, template, asked = p - p * g // 100, "(p-c)/p*100", "margin"
        prompt = (f"A product costs {c} dollars and sells for {p} dollars. What is the "
                  f"{asked} in percent?{note}")  # fmt: skip
        return _task("C3", template, {"c": c, "p": p}, prompt, AnswerType.DECIMAL,
                     decimals=1, percent=True)  # fmt: skip
    if level == "Medium" and rng.random() < 0.5:
        g = rng.choice([20, 25, 40, 50])
        to_markup = True
    elif level == "Medium":
        m = rng.choice([F(25), F("33.3"), F(50), F("66.7"), F(100)])
        to_markup = False
    elif level == "Hard":
        m, to_markup = F(5 * rng.randint(2, 30)), False
    else:
        g, to_markup = 5 * rng.randint(2, 12), True
    if to_markup:
        return _task("C3", "g/(100-g)*100", {"g": g},
                     f"A margin of {_num(g)} % equals what markup in percent?{note}",
                     AnswerType.DECIMAL, decimals=1, percent=True)  # fmt: skip
    return _task("C3", "m/(100+m)*100", {"m": m},
                 f"A markup of {_num(m)} % equals what margin in percent?{note}",
                 AnswerType.DECIMAL, decimals=1, percent=True)  # fmt: skip


def _c4(level, rng):
    note = _places_note(1)
    if level == "Pro":
        a = 5 * rng.randint(1, 10)
        return _task("C4", "a/(100-a)*100", {"a": a},
                     f"After a fall of {a} %, what rise in percent brings the value back?{note}",
                     AnswerType.DECIMAL, decimals=1, percent=True)  # fmt: skip
    while True:
        if level == "Hard":
            o, n = rng.randint(10, 999), rng.randint(10, 999)
        else:
            o = rng.choice([50, 100, 200]) if level == "Easy" else rng.randint(10, 999)
            q = rng.randint(-50, 100)
            if q == 0 or (o * (100 + q)) % 100:
                continue
            n = o * (100 + q) // 100
        if n != o and n > 0:
            return _task("C4", "(n-o)/o*100", {"o": o, "n": n},
                         f"A value changes from {o} to {n}. What is the change in percent?{note}",
                         AnswerType.DECIMAL, decimals=1, percent=True)  # fmt: skip


def _c5(level, rng):
    names = "ABC"
    if level == "Pro":
        count = rng.choice([2, 3])
        v = {}
        for i in range(1, count + 1):
            v[f"s{i}"] = 100 * rng.randint(1, 9)
        for i in range(1, count + 1):
            v[f"v{i}"] = rng.randint(5, 50)
        top = "+".join(f"s{i}*v{i}" for i in range(1, count + 1))
        bottom = "+".join(f"s{i}" for i in range(1, count + 1))
        parts = " ".join(f"Segment {names[i - 1]}: {v[f's{i}']} m revenue at {v[f'v{i}']} % "
                         "margin." for i in range(1, count + 1))  # fmt: skip
        return _task("C5", f"({top})/({bottom})", v,
                     f"{parts} What is the blended margin in percent?{_places_note(1)}",
                     AnswerType.DECIMAL, decimals=1, percent=True)  # fmt: skip
    if level == "Hard":
        w1 = 10 * rng.randint(1, 8)
        w2 = 10 * rng.randint(1, (90 - w1) // 10)
        weights = [w1, w2, 100 - w1 - w2]
    else:
        w1 = 10 * rng.randint(1, 9)
        weights = [w1, 100 - w1]
    if level == "Easy":
        values = [10 * rng.randint(1, 9) for _ in weights]
    else:
        values = [rng.randint(5, 50) for _ in weights]
    v = {f"w{i}": w for i, w in enumerate(weights, start=1)}
    v.update({f"v{i}": x for i, x in enumerate(values, start=1)})
    top = "+".join(f"w{i}*v{i}" for i in range(1, len(weights) + 1))
    parts = " ".join(f"Segment {names[i]}: {w} % of revenue at {x} % margin."
                     for i, (w, x) in enumerate(zip(weights, values)))  # fmt: skip
    return _task("C5", f"({top})/100", v,
                 f"{parts} What is the blended margin in percent?{_places_note(1)}",
                 AnswerType.DECIMAL, decimals=1, percent=True)  # fmt: skip


def _fixed_costs(rng, margin: int, highest: int) -> int | None:
    """Fixed costs in whole thousands up to `highest` that `margin` divides, or None."""
    step = margin // math.gcd(margin, 1000)
    count = (highest // 1000) // step
    return 1000 * step * rng.randint(1, count) if count else None


def _c6(level, rng):
    question = "How many units are needed to break even?"
    if level == "Easy":
        while True:
            m = rng.randint(5, 50)
            fixed = _fixed_costs(rng, m, 10_000)
            if fixed:
                prompt = (f"Fixed costs are {fixed:,} dollars and the contribution margin is "
                          f"{m} dollars per unit. {question}")  # fmt: skip
                return _task("C6", "F/m", {"F": fixed, "m": m}, prompt, AnswerType.WHOLE)
    highest = 100_000 if level == "Medium" else 1_000_000
    while True:
        if level == "Pro":
            p, x = 20 * rng.randint(1, 10), rng.choice([-20, -10, -5, 5, 10, 20])
            new_price = p * (100 + x) // 100
            v = rng.randint(1, min(p, new_price) - 1) if min(p, new_price) > 1 else None
            margin = new_price - v if v else 0
        else:
            p = rng.randint(10, 200)
            v = rng.randint(1, p - 1)
            margin = p - v
        fixed = _fixed_costs(rng, margin, highest) if margin > 0 else None
        if not fixed:
            continue
        prompt = (f"Fixed costs are {fixed:,} dollars, the price is {p} dollars and the "
                  f"variable cost {v} dollars per unit.")  # fmt: skip
        if level == "Pro":
            change = f"rises by {x} %" if x > 0 else f"falls by {-x} %"
            prompt += f" The price {change}. {question}"
            return _task("C6", "F/(p*(100+x)/100-v)", {"F": fixed, "p": p, "v": v, "x": x},
                         prompt, AnswerType.WHOLE)  # fmt: skip
        return _task("C6", "F/(p-v)", {"F": fixed, "p": p, "v": v}, f"{prompt} {question}",
                     AnswerType.WHOLE)  # fmt: skip


UNITS = {3: "K", 6: "M", 9: "B", 12: "T"}
UNIT_PAIRS = [(3, 3), (3, 6), (6, 3), (3, 9), (9, 3), (6, 6)]  # results up to T


def _unit_choices(rng, coefficient: int, exponent: int) -> tuple[list[str], str]:
    choices = [f"{coefficient:,} {unit}" for unit in UNITS.values()]
    rng.shuffle(choices)
    return choices, f"{coefficient:,} {UNITS[exponent]}"


def _c7(level, rng):
    r = rng.randint
    if level == "Pro":
        c, uc = r(1, 999), rng.choice([3, 6, 9])
        b, ub = r(2, 999), rng.choice([u for u in (3, 6, 9) if uc + u <= 12])
        a, ua = c * b, uc + ub
        choices, right = _unit_choices(rng, c, uc)
        return _task("C7", "div", {"a": a, "ua": ua, "b": b, "ub": ub},
                     f"{a:,} {UNITS[ua]} ÷ {b:,} {UNITS[ub]} = ?", AnswerType.CHOICE,
                     choices=choices, correct=right)  # fmt: skip
    if level == "Easy":
        a, b, (ua, ub) = r(1, 9), r(1, 9), rng.choice([(3, 3), (6, 3)])
    elif level == "Medium":
        a, b, (ua, ub) = r(10, 99), r(1, 9), rng.choice(UNIT_PAIRS)
    else:
        a, b, (ua, ub) = r(100, 999), r(10, 99), rng.choice(UNIT_PAIRS)
    choices, right = _unit_choices(rng, a * b, ua + ub)
    return _task("C7", "mul", {"a": a, "ua": ua, "b": b, "ub": ub},
                 f"{a} {UNITS[ua]} × {b} {UNITS[ub]} = ?", AnswerType.CHOICE,
                 choices=choices, correct=right)  # fmt: skip


def _e1(level, rng):
    r = rng.randint
    if level == "Easy":
        v, template, text = {"a": r(100, 999), "b": r(100, 999)}, "a+b", "{a:,} + {b:,}"
    elif level == "Medium" and rng.random() < 0.5:
        v, template, text = {"a": r(1000, 9999), "b": r(1000, 9999)}, "a+b", "{a:,} + {b:,}"
    elif level == "Medium":
        b = r(1000, 8999)
        v, template, text = {"a": r(b + 1000, 9999), "b": b}, "a-b", "{a:,} − {b:,}"
    elif level == "Hard":
        v, template, text = {"a": r(10, 99), "b": r(10, 99)}, "a*b", "{a} × {b}"
    elif rng.random() < 0.5:
        v, template, text = {"a": r(100, 999), "b": r(10, 99)}, "a*b", "{a} × {b}"
    else:
        v = {"a": r(100, 999), "b": r(10, 99), "c": r(100, 999)}
        template, text = "a*b+c", "{a} × {b} + {c}"
    return _task("E1", template, v, "Estimate " + text.format(**v), AnswerType.ESTIMATE)


def _e2(level, rng):
    r = rng.randint
    if level == "Easy":
        v = {"a": r(100, 999), "b": r(2, 9)}
    elif level == "Medium":
        while True:  # near an easy pair: a round divisor and a round multiple of it
            easy = 10 * r(2, 9)
            b = easy + r(-3, 3)
            q = r(-(-1000 // easy), 9999 // easy)
            a = round(easy * q * (1 + rng.uniform(-0.04, 0.04)))
            if 1000 <= a <= 9999 and abs(a - easy * round(a / easy)) <= a / 20:
                v = {"a": a, "b": b}
                break
    elif level == "Hard":
        v = {"a": r(1000, 9999), "b": r(10, 99)}
    elif rng.random() < 0.5:
        v = {"a": r(10_000, 99_999), "b": r(10, 99)}
    else:
        low, high = rng.choice([(45, 55), (95, 99)])
        v = {"a": r(low, high), "b": r(low, high)}
        return _task("E2", "a*b", v, f"Estimate {v['a']} × {v['b']}", AnswerType.ESTIMATE)
    return _task("E2", "a/b", v, f"Estimate {v['a']:,} ÷ {v['b']}", AnswerType.ESTIMATE)


def _e3(level, rng):
    r = rng.randint
    if level == "Pro" and rng.random() < 0.5:
        v = {"a": r(10, 99), "b": r(10, 99), "c": r(10, 99)}
        return _task("E3", "digits(a*b*c)", v,
                     f"How many digits does {v['a']} × {v['b']} × {v['c']} have?",
                     AnswerType.WHOLE)  # fmt: skip
    a_range, b_range = {"Easy": ((10, 99), (2, 9)), "Medium": ((10, 99), (10, 99)),
                        "Hard": ((100, 999), (10, 999)),
                        "Pro": ((1000, 9999), (100, 9999))}[level]  # fmt: skip
    v = {"a": r(*a_range), "b": r(*b_range)}
    return _task("E3", "digits(a*b)", v, f"How many digits does {v['a']:,} × {v['b']:,} have?",
                 AnswerType.WHOLE)  # fmt: skip


def _e4(level, rng):
    r = rng.randint
    if level in ("Easy", "Medium"):
        n = r(10, 999) if level == "Easy" else r(1000, 99_999)
        return _task("E4", "root(n)", {"n": n}, f"What is the digital root of {n:,}?",
                     AnswerType.WHOLE)  # fmt: skip
    a = r(10, 99) if level == "Hard" else r(100, 999)
    b = r(10, 99)
    c = a * b
    if rng.random() < 0.5:
        while True:  # a wrong result that casting out nines can catch
            error = r(1, 99) * rng.choice([1, -1])
            if error % 9 and c + error > 0:
                c += error
                break
    right = "Correct" if c == a * b else "Wrong"
    return _task("E4", "check", {"a": a, "b": b, "c": c}, f"Is {a} × {b} = {c:,} correct?",
                 AnswerType.CHOICE, choices=("Correct", "Wrong"), correct=right)  # fmt: skip


_BUILDERS = {"B1": _b1, "B2": _b2, "B3": _b3, "F1": _f1, "F2": _f2, "F3": _f3, "C1": _c1,
             "C2": _c2, "C3": _c3, "C4": _c4, "C5": _c5, "C6": _c6, "C7": _c7, "E1": _e1,
             "E2": _e2, "E3": _e3, "E4": _e4}  # fmt: skip


def generate_task(
    article_id: str, level: str, rng: random.Random, previous: TextbookTask | None = None
) -> TextbookTask:
    """A task for the article and level, different from `previous` (T R6)."""
    try:
        get_article(article_id)
    except KeyError:
        raise ValueError(f"Unknown article: {article_id!r}") from None
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level!r}")
    while True:
        task = _BUILDERS[article_id](level, rng)
        if task != previous:
            return task


# --- Rounds (T R6, T R8, T R9) ---


@dataclass(frozen=True)
class Attempt:
    task: TextbookTask
    given: str | None  # None for a skip
    outcome: Outcome


@dataclass(frozen=True)
class Round:
    article_id: str
    level: str
    tasks: tuple[TextbookTask, ...]
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
    article_id: str
    level: str
    finished_at: datetime
    correct: int


def start_round(article_id: str, level: str, rng: random.Random) -> Round:
    """A new round of ROUND_LENGTH tasks, never the same task twice in a row."""
    tasks: list[TextbookTask] = []
    for _ in range(ROUND_LENGTH):
        tasks.append(generate_task(article_id, level, rng, tasks[-1] if tasks else None))
    return Round(article_id, level, tuple(tasks))


def current_task(practice_round: Round) -> TextbookTask | None:
    if practice_round.status != Status.RUNNING:
        return None
    return practice_round.tasks[len(practice_round.attempts)]


def submit_answer(practice_round: Round, raw: str) -> tuple[Round, Outcome]:
    """A typed answer, or the label of the chosen option."""
    task = current_task(practice_round)
    if task is None:
        return practice_round, Outcome.IGNORED
    outcome = evaluate(task, raw)
    if outcome == Outcome.IGNORED:
        return practice_round, outcome
    return _record(practice_round, Attempt(task, raw.strip(), outcome)), outcome


def skip_task(practice_round: Round) -> tuple[Round, Outcome]:
    task = current_task(practice_round)
    if task is None:
        return practice_round, Outcome.IGNORED
    return _record(practice_round, Attempt(task, None, Outcome.SKIPPED)), Outcome.SKIPPED


def _record(practice_round: Round, attempt: Attempt) -> Round:
    return replace(practice_round, attempts=(*practice_round.attempts, attempt))


# --- Practised (T R10) ---


def practised(saved_rounds: Iterable[SavedRound]) -> set[str]:
    """The articles with at least one completed round, at any level and score."""
    return {saved.article_id for saved in saved_rounds}
