"""Trainer task generation and answer checking (spec 002).

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
