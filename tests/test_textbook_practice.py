"""Textbook practice rules in textbook.py, stage 2 (T R6–T R10, TA8–TA10).

The ranges come from the "Practice catalogue" of docs/textbook-brief new.md, with
the decisions in specs/010-textbook.md (stage 2). They are written out here on
purpose, so a wrong range in textbook.py cannot pass by checking itself.
"""

import math
import random
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from textbook import (
    ROUND_LENGTH,
    AnswerType,
    Outcome,
    SavedRound,
    Status,
    TextbookTask,
    answer_text,
    current_task,
    evaluate,
    generate_task,
    practised,
    skip_task,
    start_round,
    submit_answer,
)

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ["Easy", "Medium", "Hard", "Pro"]
ARTICLES = ["B1", "B2", "B3", "F1", "F2", "F3", "C1", "C2", "C3", "C4", "C5", "C6", "C7",
            "E1", "E2", "E3", "E4"]  # fmt: skip
CASES = [(article_id, level) for article_id in ARTICLES for level in LEVELS]
SEED = 2026

F = Fraction
EXACT_PERCENTS = {F(p) for p in ("10", "12.5", "20", "25", "37.5", "40", "50", "60", "62.5",
                                 "75", "80", "87.5")}  # fmt: skip
F3_SMALL = {F(n, 100) for n in (25, 36, 49, 64, 81)}
F3_ALL = {F(n * n, 100) for n in range(2, 10)} | {F("1.21"), F("1.44"), F("2.25"), F(4)}
UNITS = {3: "K", 6: "M", 9: "B", 12: "T"}


# --- Helpers ---


def vals(task):
    return {name: F(value) for name, value in task.values}


def between(x, low, high):
    return low <= x <= high


def whole(x):
    return F(x).denominator == 1


def places(x, n):
    """x has at most n decimal places."""
    return whole(F(x) * 10**n)


def all_in(values, names, low, high, *, whole_numbers=True):
    return all(between(values[n], low, high) and (whole(values[n]) or not whole_numbers)
               for n in names)  # fmt: skip


def exact_sqrt(x):
    top, bottom = math.isqrt(x.numerator), math.isqrt(x.denominator)
    assert top * top == x.numerator and bottom * bottom == x.denominator, x
    return F(top, bottom)


def digits(x):
    return len(str(int(x)))


def root(n):
    n = int(n)
    return 9 if n % 9 == 0 else n % 9


def computed(task):
    """The answer from the task's template and values, worked out here."""
    env = {**vals(task), "digits": digits, "root": root}
    return F(eval(task.template, {"__builtins__": {}}, env))  # noqa: S307 - our own templates


def rounded(x, decimals):
    """Half away from zero (decision 1)."""
    exact = Decimal(x.numerator) / Decimal(x.denominator)
    sign = -1 if exact < 0 else 1
    return sign * abs(exact).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def multiple_of_ten_near(n):
    return round(n / 10) * 10


# --- Which option of a choice task is right, worked out here ---


def unit_label(coefficient, exponent):
    return f"{int(coefficient):,} {UNITS[exponent]}"


def right_choice(task):
    v = vals(task)
    template = task.template
    if template == "compare":
        first, second = v["a"] / v["b"], v["c"] / v["d"]
        labels = task.choices
        return labels[2] if first == second else (labels[0] if first > second else labels[1])
    if template == "fraction":
        return f"{v['f'].numerator}/{v['f'].denominator}"
    if template in ("square_vs_x", "root_vs_x", "square_vs_root", "order"):
        x = v["x"]
        sizes = {"x²": x * x, "x": x, "√x": exact_sqrt(x)}
        if template == "order":
            return " < ".join(sorted(sizes, key=sizes.get))
        a, b = task.choices
        return a if sizes[a] > sizes[b] else b
    if template == "mul":
        return unit_label(v["a"] * v["b"], int(v["ua"] + v["ub"]))
    if template == "div":
        value = v["a"] * 10 ** int(v["ua"]) / (v["b"] * 10 ** int(v["ub"]))
        for exponent in UNITS:
            coefficient = value / 10**exponent
            if whole(coefficient) and 1 <= coefficient <= 999:
                return unit_label(coefficient, exponent)
        raise AssertionError(f"{task}: no whole result with a unit")
    if template == "check":
        return "Correct" if v["c"] == v["a"] * v["b"] else "Wrong"
    raise AssertionError(f"unknown choice template {template!r}")


# --- The practice catalogue: one rule per article and level ---


def b1(level):
    def rule(t):
        v = vals(t)
        names = [n for n in "abcdefg" if n in v]
        if level == "Easy":
            return t.template == "a+b*c" and all_in(v, names, 2, 9)
        if level == "Medium":
            return (t.template in ("a*b-c*d", "a+b*c-d") and all_in(v, names, 2, 12)
                    and t.answer >= 0)  # fmt: skip
        if level == "Hard":
            return (t.template == "(a+b)*c-d/e" and all_in(v, names, 2, 20)
                    and v["d"] % v["e"] == 0 and t.answer >= 0)  # fmt: skip
        return (t.template == "(a-b)*(c+d)-e*f/g" and all_in(v, names, 2, 20)
                and (v["e"] * v["f"]) % v["g"] == 0 and t.answer >= 0)  # fmt: skip
    return rule


def b2(level):
    def rule(t):
        v = vals(t)
        if level == "Easy":
            return (t.template in ("a+b", "a-b") and between(v["a"], 1, 20)
                    and between(v["b"], -20, -1))  # fmt: skip
        if level == "Medium":
            if t.template in ("a+b", "a-b"):
                return between(v["a"], -12, -1) and between(v["b"], -12, -1)
            return t.template == "a*b" and between(v["a"], -12, -1) and between(v["b"], 1, 12)
        if level == "Hard":
            if t.template == "a*b":
                return between(abs(v["a"]), 2, 20) and between(abs(v["b"]), 2, 20)
            return (t.template == "a/b" and between(abs(v["b"]), 2, 20)
                    and whole(v["a"] / v["b"]) and between(abs(v["a"] / v["b"]), 2, 20))  # fmt: skip
        return (t.template == "a*b-c*d" and all_in(v, "abc", -15, -2)
                and between(v["d"], 2, 15))  # fmt: skip
    return rule


def b3(level):
    def rule(t):
        v = vals(t)
        one = lambda x: places(x, 1) and between(x, F("0.1"), F("9.9"))  # noqa: E731
        two = lambda x: places(x, 2) and between(x, F("0.01"), F("9.99"))  # noqa: E731
        if level == "Easy":
            return t.template in ("a+b", "a-b") and one(v["a"]) and one(v["b"]) and t.answer >= 0
        if level == "Medium":
            if t.template in ("a+b", "a-b"):
                return two(v["a"]) and two(v["b"]) and t.answer >= 0
            if t.template == "a*b":
                return two(v["a"]) and v["b"] in (10, 100)
            if t.template == "a/b" and v["b"] == 10:
                return places(v["a"], 1) and between(v["a"], F("0.1"), F("99.9"))
            return t.template == "a/b" and v["b"] == 100 and whole(v["a"]) and between(v["a"], 1, 999)
        if level == "Hard":
            return t.template == "a*b" and one(v["a"]) and one(v["b"])
        return (t.template == "a*b-c" and one(v["a"]) and one(v["b"]) and one(v["c"])
                and t.answer >= 0)  # fmt: skip
    return rule


def f1(level):
    def rule(t):
        v = vals(t)
        if level == "Pro":
            return t.template == "p/100*n" and v["p"] in EXACT_PERCENTS and whole(v["n"]) and v["n"] > 0
        f = v["f"]
        denominators = {"Easy": {2, 4, 5, 10}, "Medium": {8}, "Hard": {3, 6, 12}}[level]
        templates = {"Easy": {"f*100"}, "Medium": {"f*100", "f"},
                     "Hard": {"f*100", "f", "fraction"}}[level]  # fmt: skip
        return 0 < f < 1 and f.denominator in denominators and t.template in templates
    return rule


def f2(level):
    low, high = {"Easy": (2, 9), "Medium": (5, 12), "Hard": (7, 20), "Pro": (11, 30)}[level]

    def rule(t):
        v = vals(t)
        if t.template != "compare" or not all_in(v, "bd", low, high):
            return False
        if not (0 < v["a"] < v["b"] and 0 < v["c"] < v["d"]):
            return False
        if t.choices != (f"{v['a']}/{v['b']}", f"{v['c']}/{v['d']}", "Equal"):
            return False
        gap = abs(v["a"] / v["b"] - v["c"] / v["d"])
        if gap == 0:
            return level in ("Hard", "Pro") and v["b"] != v["d"]
        return {"Easy": gap >= F("0.1"), "Medium": F("0.02") <= gap <= F("0.1"),
                "Hard": gap < F("0.05"), "Pro": gap < F("0.02")}[level]  # fmt: skip
    return rule


def f3(level):
    template, xs, choices = {
        "Easy": ("square_vs_x", F3_SMALL, {"x²", "x"}),
        "Medium": ("root_vs_x", F3_SMALL, {"√x", "x"}),
        "Hard": ("square_vs_root", F3_ALL, {"x²", "√x"}),
        "Pro": ("order", F3_ALL, None),
    }[level]

    def rule(t):
        ok = t.template == template and vals(t)["x"] in xs
        if choices is not None:
            return ok and set(t.choices) == choices
        return ok and len(t.choices) == 4 and all(set(c.split(" < ")) == {"x²", "x", "√x"}
                                                   for c in t.choices)  # fmt: skip
    return rule


def c1(level):
    count = 2 if level in ("Easy", "Medium") else 3
    allowed = {"Easy": {10, 20}, "Medium": set(range(5, 31, 5)), "Hard": set(range(5, 31, 5)),
               "Pro": set(range(1, 31))}[level]  # fmt: skip

    def rule(t):
        v = vals(t)
        names = [f"p{i}" for i in range(1, count + 1)]
        expected = "*".join(f"(1+{n}/100)" for n in names)
        return (t.template == f"({expected}-1)*100" and set(v) == set(names)
                and all(abs(v[n]) in allowed for n in names))  # fmt: skip
    return rule


DOUBLING_EASY = {2, 3, 4, 6, 8, 9, 12}
DOUBLING_MEDIUM = DOUBLING_EASY | {18, 24, 36}


def c2(level):
    def rule(t):
        v = vals(t)
        if level == "Easy":
            return t.template == "72/r" and v["r"] in DOUBLING_EASY
        if level == "Medium":
            return ((t.template == "72/r" and v["r"] in DOUBLING_MEDIUM)
                    or (t.template == "114/r" and v["r"] in {2, 3, 6}))  # fmt: skip
        if level == "Hard":
            return (t.template == "s*2**k" and between(v["s"], 5, 50) and whole(v["s"])
                    and v["r"] in DOUBLING_EASY and v["k"] in {1, 2, 3}
                    and v["t"] == v["k"] * 72 / v["r"])  # fmt: skip
        return t.template == "72/r*k" and v["r"] in DOUBLING_MEDIUM and v["k"] in {2, 3}
    return rule


def c3(level):
    def rule(t):
        v = vals(t)
        if level == "Easy":
            return (t.template in ("(p-c)/p*100", "(p-c)/c*100") and whole(v["c"]) and whole(v["p"])
                    and 0 < v["c"] < v["p"] and whole(t.answer))  # fmt: skip
        if level == "Medium":
            return ((t.template == "m/(100+m)*100" and v.get("m") in {25, F("33.3"), 50, F("66.7"), 100})
                    or (t.template == "g/(100-g)*100" and v.get("g") in {20, 25, 40, 50}))  # fmt: skip
        if level == "Hard":
            return t.template == "m/(100+m)*100" and v["m"] in set(range(10, 151, 5))
        return t.template == "g/(100-g)*100" and v["g"] in set(range(10, 61, 5))
    return rule


def c4(level):
    def rule(t):
        v = vals(t)
        if level == "Pro":
            return t.template == "a/(100-a)*100" and v["a"] in set(range(5, 51, 5))
        if t.template != "(n-o)/o*100" or not whole(v["n"]) or v["n"] <= 0 or v["n"] == v["o"]:
            return False
        if level == "Easy":
            return v["o"] in {50, 100, 200} and whole(t.answer)
        if level == "Medium":
            return between(v["o"], 10, 999) and whole(t.answer)
        return between(v["o"], 10, 999) and between(v["n"], 10, 999)
    return rule


def c5(level):
    def rule(t):
        v = vals(t)
        weights = [v[n] for n in ("w1", "w2", "w3") if n in v]
        values = [v[n] for n in ("v1", "v2", "v3") if n in v]
        sizes = [v[n] for n in ("s1", "s2", "s3") if n in v]
        if level == "Pro":
            if len(sizes) not in (2, 3) or len(values) != len(sizes) or weights:
                return False
            top = "+".join(f"s{i}*v{i}" for i in range(1, len(sizes) + 1))
            bottom = "+".join(f"s{i}" for i in range(1, len(sizes) + 1))
            return (t.template == f"({top})/({bottom})"
                    and all(s % 100 == 0 and between(s, 100, 900) for s in sizes)
                    and all(between(x, 5, 50) and whole(x) for x in values))  # fmt: skip
        count = 3 if level == "Hard" else 2
        top = "+".join(f"w{i}*v{i}" for i in range(1, count + 1))
        value_ok = ((lambda x: x % 10 == 0 and between(x, 10, 90)) if level == "Easy"
                    else (lambda x: whole(x) and between(x, 5, 50)))  # fmt: skip
        return (t.template == f"({top})/100" and len(weights) == count == len(values)
                and sum(weights) == 100 and all(w % 10 == 0 and w >= 10 for w in weights)
                and all(value_ok(x) for x in values))  # fmt: skip
    return rule


def c6(level):
    def rule(t):
        v = vals(t)
        if level == "Easy":
            return (t.template == "F/m" and v["F"] % 1000 == 0 and between(v["F"], 1000, 10_000)
                    and between(v["m"], 5, 50) and v["F"] % v["m"] == 0)  # fmt: skip
        fixed_max = 100_000 if level == "Medium" else 1_000_000
        common = (v["F"] % 1000 == 0 and between(v["F"], 1000, fixed_max)
                  and whole(v["p"]) and whole(v["v"]) and 0 < v["v"] < v["p"] <= 200)  # fmt: skip
        if level in ("Medium", "Hard"):
            return t.template == "F/(p-v)" and common and v["F"] % (v["p"] - v["v"]) == 0
        new_price = v["p"] * (100 + v["x"]) / 100
        return (t.template == "F/(p*(100+x)/100-v)" and common
                and v["x"] in {-20, -10, -5, 5, 10, 20} and whole(new_price)
                and new_price > v["v"] and v["F"] % (new_price - v["v"]) == 0)  # fmt: skip
    return rule


def c7(level):
    def rule(t):
        v = vals(t)
        if len(t.choices) != 4 or {c.split()[-1] for c in t.choices} != {"K", "M", "B", "T"}:
            return False
        if level == "Pro":
            return t.template == "div" and v["ua"] in UNITS and v["ub"] in UNITS
        if t.template != "mul" or v["ua"] + v["ub"] > 12:
            return False
        if level == "Easy":
            return all_in(v, "ab", 1, 9) and (v["ua"], v["ub"]) in {(3, 3), (6, 3)}
        if level == "Medium":
            return between(v["a"], 10, 99) and between(v["b"], 1, 9)
        return between(v["a"], 100, 999) and between(v["b"], 10, 99)
    return rule


def e1(level):
    def rule(t):
        v = vals(t)
        if level == "Easy":
            return t.template == "a+b" and all_in(v, "ab", 100, 999)
        if level == "Medium":
            return all_in(v, "ab", 1000, 9999) and (
                t.template == "a+b" or (t.template == "a-b" and v["a"] - v["b"] >= 1000))
        if level == "Hard":
            return t.template == "a*b" and all_in(v, "ab", 10, 99)
        return (t.template in ("a*b", "a*b+c") and between(v["a"], 100, 999)
                and between(v["b"], 10, 99) and ("c" not in v or between(v["c"], 100, 999)))  # fmt: skip
    return rule


def e2(level):
    def rule(t):
        v = vals(t)
        if level == "Easy":
            return t.template == "a/b" and between(v["a"], 100, 999) and between(v["b"], 2, 9)
        if level == "Medium":
            if not (t.template == "a/b" and between(v["a"], 1000, 9999) and between(v["b"], 10, 99)):
                return False
            easy = multiple_of_ten_near(v["b"])
            close = abs(v["b"] - easy) <= 3 and easy > 0
            quotient = round(v["a"] / easy)
            return close and abs(v["a"] - easy * quotient) <= v["a"] / 20
        if level == "Hard":
            return t.template == "a/b" and between(v["a"], 1000, 9999) and between(v["b"], 10, 99)
        if t.template == "a/b":
            return between(v["a"], 10_000, 99_999) and between(v["b"], 10, 99)
        return t.template == "a*b" and (all_in(v, "ab", 45, 55) or all_in(v, "ab", 95, 99))
    return rule


def e3(level):
    def rule(t):
        v = vals(t)
        if level == "Easy":
            return t.template == "digits(a*b)" and between(v["a"], 10, 99) and between(v["b"], 2, 9)
        if level == "Medium":
            return t.template == "digits(a*b)" and all_in(v, "ab", 10, 99)
        if level == "Hard":
            return (t.template == "digits(a*b)" and between(v["a"], 100, 999)
                    and between(v["b"], 10, 999))  # fmt: skip
        if t.template == "digits(a*b*c)":
            return all_in(v, "abc", 10, 99)
        return (t.template == "digits(a*b)" and between(v["a"], 1000, 9999)
                and between(v["b"], 100, 9999))  # fmt: skip
    return rule


def e4(level):
    def rule(t):
        v = vals(t)
        if level in ("Easy", "Medium"):
            low, high = (10, 999) if level == "Easy" else (1000, 99_999)
            return t.template == "root(n)" and between(v["n"], low, high)
        a_low, a_high = (10, 99) if level == "Hard" else (100, 999)
        if not (t.template == "check" and between(v["a"], a_low, a_high)
                and between(v["b"], 10, 99) and t.choices == ("Correct", "Wrong")):  # fmt: skip
            return False
        error = v["c"] - v["a"] * v["b"]
        return error == 0 or (v["c"] > 0 and between(abs(error), 1, 99) and error % 9 != 0)
    return rule


RULES = {"B1": b1, "B2": b2, "B3": b3, "F1": f1, "F2": f2, "F3": f3, "C1": c1, "C2": c2,
         "C3": c3, "C4": c4, "C5": c5, "C6": c6, "C7": c7, "E1": e1, "E2": e2, "E3": e3,
         "E4": e4}  # fmt: skip

PERCENT_1 = (AnswerType.DECIMAL, 1, True)


def expected_type(task, level):
    """(answer type, decimal places, percent) the catalogue gives this task."""
    article = task.article_id
    if article in ("B1", "B2", "C2", "C6", "E3"):
        return AnswerType.WHOLE, None, False
    if article == "B3":
        return AnswerType.DECIMAL, 2, False
    if article == "F1":
        return {"f*100": PERCENT_1, "f": (AnswerType.DECIMAL, 3, False),
                "fraction": (AnswerType.CHOICE, None, False),
                "p/100*n": (AnswerType.WHOLE, None, False)}[task.template]  # fmt: skip
    if article in ("F2", "F3", "C7"):
        return AnswerType.CHOICE, None, False
    if article in ("C1", "C3", "C4", "C5"):
        return PERCENT_1
    if article in ("E1", "E2"):
        return AnswerType.ESTIMATE, None, False
    if article == "E4":
        if level in ("Easy", "Medium"):
            return AnswerType.WHOLE, None, False
        return AnswerType.CHOICE, None, False
    raise AssertionError(article)


def tasks_for(article_id, level, seed=SEED, count=1000):
    rng = random.Random(seed)
    found = []
    previous = None
    for _ in range(count):
        previous = generate_task(article_id, level, rng, previous=previous)
        found.append(previous)
    return found


# --- Generation (T R6, TA8) ---


def test_there_is_a_rule_for_every_article():
    assert set(RULES) == set(ARTICLES)


@pytest.mark.parametrize("article_id, level", CASES)
def test_1000_tasks_follow_the_template_ranges_and_answer_type(article_id, level):
    rule = RULES[article_id](level)
    for task in tasks_for(article_id, level):
        assert task.article_id == article_id
        assert rule(task), f"{article_id} {level}: {task.template} {task.values} is outside the range"
        kind, decimals, percent = expected_type(task, level)
        assert (task.kind, task.decimals, task.percent) == (kind, decimals, percent), task
        assert task.prompt.strip()
        if kind == AnswerType.CHOICE:
            assert 2 <= len(task.choices) <= 4
            assert len(set(task.choices)) == len(task.choices)
            assert task.correct_choice in task.choices
            assert task.correct_choice == right_choice(task)
            continue
        assert task.answer == computed(task), task
        if kind == AnswerType.WHOLE:
            assert whole(task.answer), task
        if kind == AnswerType.DECIMAL:
            assert f"({decimals} decimal place" in task.prompt, task.prompt
        if kind == AnswerType.ESTIMATE:
            assert task.prompt.startswith("Estimate"), task.prompt


@pytest.mark.parametrize("article_id, level", [("B3", level) for level in LEVELS])
def test_decimal_results_of_b3_are_exact_with_two_places(article_id, level):
    assert all(places(task.answer, 2) for task in tasks_for(article_id, level))


@pytest.mark.parametrize("article_id, level", [("F2", "Hard"), ("F2", "Pro"), ("E4", "Hard"),
                                                ("E4", "Pro"), ("F3", "Hard"), ("F3", "Pro")])  # fmt: skip
def test_both_kinds_of_answer_occur(article_id, level):
    answers = {task.correct_choice for task in tasks_for(article_id, level)}
    assert len(answers) >= 2, answers
    if article_id == "F2":
        assert "Equal" in answers


def test_hard_large_numbers_include_billion_times_thousand():
    assert any((vals(t)["ua"], vals(t)["ub"]) in {(9, 3), (3, 9)} for t in tasks_for("C7", "Hard"))


@pytest.mark.parametrize("article_id, level", CASES)
def test_no_task_appears_twice_in_a_row(article_id, level):
    found = tasks_for(article_id, level, count=300)
    assert all(first != second for first, second in zip(found, found[1:]))


@pytest.mark.parametrize("article_id, level", CASES)
def test_rounds_differ_between_seeds_and_repeat_with_the_same_seed(article_id, level):
    assert tasks_for(article_id, level, 1, 10) != tasks_for(article_id, level, 2, 10)
    assert tasks_for(article_id, level, 3, 10) == tasks_for(article_id, level, 3, 10)


def test_generation_does_not_touch_global_randomness():
    state = random.getstate()
    tasks_for("C6", "Pro", count=50)
    assert random.getstate() == state


@pytest.mark.parametrize("article_id, level", [("C2X", "Easy"), ("C2", "Extreme")])
def test_unknown_article_or_level_raises(article_id, level):
    with pytest.raises(ValueError):
        generate_task(article_id, level, random.Random(0))


# --- Answer types (T R7, T R8, TA9) ---


def task_of(kind, answer=None, **fields):
    return TextbookTask(article_id="C4", template="", values=(), prompt="", kind=kind,
                        answer=answer, **fields)  # fmt: skip


DECIMAL_66 = task_of(AnswerType.DECIMAL, F(200, 3), decimals=1, percent=True)
ESTIMATE_7341 = task_of(AnswerType.ESTIMATE, F(7341, 83))
WHOLE_MINUS_12 = task_of(AnswerType.WHOLE, F(-12))
CHOICE = TextbookTask(article_id="F2", template="compare", values=(), prompt="",
                      kind=AnswerType.CHOICE, choices=("3/7", "5/11", "Equal"),
                      correct_choice="5/11")  # fmt: skip


@pytest.mark.parametrize("raw", ["66.7", "66,7", "66.7%", "66.7 %", " 66.70 "])
def test_decimal_with_one_place_accepts_the_rounded_result(raw):
    assert evaluate(DECIMAL_66, raw) == Outcome.CORRECT


@pytest.mark.parametrize("raw", ["66.6", "66.67", "67", "-66.7"])
def test_decimal_with_another_value_is_wrong(raw):
    assert evaluate(DECIMAL_66, raw) == Outcome.WRONG


@pytest.mark.parametrize("raw", ["abc", "", "   ", "66.7.1", "66,7,1", "%", "6 6.7"])
def test_decimal_input_of_the_wrong_form_is_not_evaluated(raw):
    assert evaluate(DECIMAL_66, raw) == Outcome.IGNORED


def test_decimal_accepts_8_for_8_point_0():
    eight = task_of(AnswerType.DECIMAL, F(8), decimals=1, percent=False)
    for raw in ("8", "8.0", "8,0"):
        assert evaluate(eight, raw) == Outcome.CORRECT


def test_decimal_can_be_negative_with_either_minus_sign():
    falling = task_of(AnswerType.DECIMAL, F(-4, 3), decimals=1, percent=True)
    assert evaluate(falling, "-1.3") == Outcome.CORRECT
    assert evaluate(falling, "−1.3") == Outcome.CORRECT
    assert evaluate(falling, "1.3") == Outcome.WRONG


def test_decimal_rounds_half_away_from_zero():
    assert evaluate(task_of(AnswerType.DECIMAL, F("10.25"), decimals=1, percent=True),
                    "10.3") == Outcome.CORRECT  # fmt: skip
    assert evaluate(task_of(AnswerType.DECIMAL, F("10.25"), decimals=1, percent=True),
                    "10.2") == Outcome.WRONG  # fmt: skip
    assert evaluate(task_of(AnswerType.DECIMAL, F("-10.25"), decimals=1, percent=True),
                    "-10.3") == Outcome.CORRECT  # fmt: skip


def test_decimal_comma_is_always_a_decimal_separator():
    small = task_of(AnswerType.DECIMAL, F("1.25"), decimals=2, percent=False)
    assert evaluate(small, "1,250") == Outcome.CORRECT


@pytest.mark.parametrize("raw, outcome", [("80", Outcome.CORRECT), ("97", Outcome.CORRECT),
                                          ("88", Outcome.CORRECT), ("79", Outcome.WRONG),
                                          ("98", Outcome.WRONG)])  # fmt: skip
def test_estimate_of_7341_by_83_accepts_80_to_97(raw, outcome):
    assert evaluate(ESTIMATE_7341, raw) == outcome


@pytest.mark.parametrize("raw", ["88.4", "88,4", "abc", "", "1,000", "90%"])
def test_estimate_must_be_a_whole_number(raw):
    assert evaluate(ESTIMATE_7341, raw) == Outcome.IGNORED


def test_estimate_limits_are_included():
    hundred = task_of(AnswerType.ESTIMATE, F(100))
    assert evaluate(hundred, "90") == Outcome.CORRECT
    assert evaluate(hundred, "110") == Outcome.CORRECT
    assert evaluate(hundred, "89") == Outcome.WRONG
    assert evaluate(hundred, "111") == Outcome.WRONG


@pytest.mark.parametrize("raw", ["-12", "−12", " -12 "])
def test_whole_number_reads_a_leading_minus(raw):
    assert evaluate(WHOLE_MINUS_12, raw) == Outcome.CORRECT


def test_whole_number_with_another_value_is_wrong():
    assert evaluate(WHOLE_MINUS_12, "12") == Outcome.WRONG


@pytest.mark.parametrize("raw", ["-12.0", "1,250", "abc", "", "--12", "12%"])
def test_whole_number_input_of_the_wrong_form_is_not_evaluated(raw):
    assert evaluate(WHOLE_MINUS_12, raw) == Outcome.IGNORED


def test_choice_is_right_only_for_the_correct_option():
    assert evaluate(CHOICE, "5/11") == Outcome.CORRECT
    assert evaluate(CHOICE, "3/7") == Outcome.WRONG
    assert evaluate(CHOICE, "Equal") == Outcome.WRONG
    assert evaluate(CHOICE, "7/3") == Outcome.IGNORED


def test_answer_text_shows_what_counts_as_right():
    assert answer_text(DECIMAL_66) == "66.7 %"
    assert answer_text(task_of(AnswerType.DECIMAL, F("0.125"), decimals=3, percent=False)) == "0.125"
    assert answer_text(WHOLE_MINUS_12) == "−12"
    assert answer_text(task_of(AnswerType.WHOLE, F(25000))) == "25,000"
    assert answer_text(CHOICE) == "5/11"
    assert answer_text(ESTIMATE_7341) == "88.45 (accepted: 80 to 97)"


# --- A round (T R6, T R8, T R9, TA10) ---


def typed_right(task):
    if task.kind == AnswerType.CHOICE:
        return task.correct_choice
    if task.kind == AnswerType.DECIMAL:
        return str(rounded(task.answer, task.decimals))
    return str(round(task.answer))


def typed_wrong(task):
    if task.kind == AnswerType.CHOICE:
        return next(choice for choice in task.choices if choice != task.correct_choice)
    if task.kind == AnswerType.ESTIMATE:
        return str(int(abs(task.answer)) * 3 + 100)
    if task.kind == AnswerType.DECIMAL:
        return str(rounded(task.answer, task.decimals) + 1)
    return str(int(task.answer) + 1)


def new_round(article_id="C2", level="Easy", seed=SEED):
    return start_round(article_id, level, random.Random(seed))


@pytest.mark.parametrize("article_id", ARTICLES)
def test_a_round_has_exactly_10_tasks_for_one_article_and_level(article_id):
    practice_round = new_round(article_id, "Medium")
    assert ROUND_LENGTH == 10
    assert len(practice_round.tasks) == 10
    assert all(task.article_id == article_id for task in practice_round.tasks)
    assert all(RULES[article_id]("Medium")(task) for task in practice_round.tasks)
    assert all(a != b for a, b in zip(practice_round.tasks, practice_round.tasks[1:]))
    assert practice_round.status == Status.RUNNING
    assert current_task(practice_round) == practice_round.tasks[0]


@pytest.mark.parametrize("article_id", ARTICLES)
def test_right_and_wrong_answers_are_counted_for_every_article(article_id):
    practice_round = new_round(article_id, "Hard")
    practice_round, first = submit_answer(practice_round, typed_right(current_task(practice_round)))
    practice_round, second = submit_answer(practice_round, typed_wrong(current_task(practice_round)))
    assert (first, second) == (Outcome.CORRECT, Outcome.WRONG)
    assert (practice_round.correct, practice_round.wrong) == (1, 1)


def test_input_of_the_wrong_form_changes_nothing():
    start = new_round("C2")
    practice_round, outcome = submit_answer(start, "abc")
    assert outcome == Outcome.IGNORED
    assert practice_round == start


def test_wrong_answer_and_skip_keep_the_task_for_the_correct_answer():
    start = new_round("C2")
    task = current_task(start)
    practice_round, _ = submit_answer(start, typed_wrong(task))
    assert practice_round.attempts[-1].task == task
    practice_round, outcome = skip_task(practice_round)
    assert outcome == Outcome.SKIPPED
    assert practice_round.attempts[-1].given is None


def test_6_correct_3_wrong_1_skipped_gives_6_of_10_and_completes():
    practice_round = new_round("C5", "Hard")
    for _ in range(6):
        practice_round, _ = submit_answer(practice_round, typed_right(current_task(practice_round)))
    for _ in range(3):
        practice_round, _ = submit_answer(practice_round, typed_wrong(current_task(practice_round)))
    assert practice_round.status == Status.RUNNING  # 9 of 10 done
    practice_round, _ = skip_task(practice_round)

    assert (practice_round.correct, practice_round.wrong, practice_round.skipped) == (6, 3, 1)
    assert practice_round.status == Status.COMPLETED
    assert current_task(practice_round) is None


def test_actions_after_the_tenth_task_are_ignored():
    practice_round = new_round()
    for _ in range(10):
        practice_round, _ = skip_task(practice_round)
    for action in (lambda r: submit_answer(r, "5"), skip_task):
        assert action(practice_round) == (practice_round, Outcome.IGNORED)


def test_every_round_generates_new_tasks():
    assert new_round("E2", seed=1).tasks != new_round("E2", seed=2).tasks


# --- Practised (T R10) ---


def saved(article_id, level="Easy", correct=0):
    return SavedRound(id=f"{article_id}-{level}-{correct}", article_id=article_id, level=level,
                      finished_at=datetime(2026, 11, 21, 12, tzinfo=timezone.utc),
                      correct=correct)  # fmt: skip


def test_practised_comes_from_saved_rounds_at_any_level_and_score():
    assert practised([]) == set()
    assert practised([saved("C2", "Pro", 0), saved("C2", "Easy", 10), saved("E4")]) == {"C2", "E4"}


def test_rule_module_follows_the_design_rules():
    source = (ROOT / "textbook.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", ".now(", "time.time", "random.Random("):
        assert forbidden not in source
