"""Knowledge rules in knowledge.py: practice tasks, rounds, navigation, ✓ (K R3–K R7)."""

import random
from datetime import datetime, timezone
from math import gcd
from pathlib import Path

import pytest

import knowledge
from knowledge import (
    ROUND_LENGTH,
    Outcome,
    PracticeTask,
    SavedRound,
    Status,
    current_task,
    generate_task,
    neighbours,
    position,
    practised,
    skip_task,
    start_round,
    submit_answer,
)

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ["Easy", "Medium", "Hard", "Pro"]
SEED = 2026


# --- Helpers for the range rules ---


def between(n, low, high):
    return n is not None and low <= n <= high


def size(n):
    return len(str(n))


def digit(n, place):
    return n // 10**place % 10


def ends_in(n, last_digits):
    return n % 10 in last_digits


def last_two_in(n, low, high):
    return low <= n % 100 <= high


def borrowing_places(a, b, places):
    return [place for place in places if digit(a, place) < digit(b, place)]


def no_borrowing(a, b):
    return size(a) == size(b) and not borrowing_places(a, b, range(size(a)))


def complement_plus(a, b, whole, low, high):
    return between(b - (whole - a), low, high)


def has_factor(n, low, high):
    return any(n % factor == 0 for factor in range(low, high + 1))


def square(low, high, *, ending_5=False, also_not=()):
    def rule(t):
        n = t.a
        if ending_5:
            return between(n, low, high) and n % 10 == 5
        return between(n, low, high) and n % 10 != 0 and n not in also_not

    return rule


def times(factor, low, high, extra=lambda n: True):
    return lambda t: t.b == factor and between(t.a, low, high) and extra(t.a)


def divide(divisor, low, high):
    return lambda t: t.b == divisor and t.a == divisor * t.answer and between(t.answer, low, high)


def digit_sum(n):
    return sum(int(d) for d in str(n))


# --- The "Practice levels" table of docs/knowledge-brief.md, with the decisions
# listed in specs/009-knowledge.md. Each rule gets the task and says whether it
# is inside the range. a is the first number, b the second (None for squares). ---

RULES = {
    "A1": {
        "Easy": lambda t: between(t.a, 11, 49) and between(t.b, 11, 49),
        "Medium": lambda t: between(t.a, 20, 99) and between(t.b, 20, 99),
        "Hard": lambda t: between(t.a, 100, 999) and between(t.b, 20, 99),
        "Pro": lambda t: between(t.a, 100, 999) and between(t.b, 100, 999),
    },
    "A2": {
        "Easy": lambda t: between(t.a, 10, 99) and between(t.b, 10, 99),
        "Medium": lambda t: between(t.a, 100, 499) and between(t.b, 100, 499),
        "Hard": lambda t: between(t.a, 100, 999) and between(t.b, 100, 999),
        "Pro": lambda t: between(t.a, 1000, 9999) and between(t.b, 1000, 9999),
    },
    "A3": {
        "Easy": lambda t: t.a in (25, 50, 75) and complement_plus(t.a, t.b, 100, 1, 9),
        "Medium": lambda t: between(t.a, 10, 99) and complement_plus(t.a, t.b, 100, 1, 20),
        "Hard": lambda t: between(t.a, 100, 999) and t.a % 25 == 0
        and complement_plus(t.a, t.b, 1000, 1, 99),
        "Pro": lambda t: between(t.a, 100, 999) and complement_plus(t.a, t.b, 1000, 1, 999),
    },
    "A4": {
        "Easy": lambda t: between(t.a, 10, 99) and ends_in(t.a, {6, 7, 8, 9})
        and between(t.b, 10, 99),
        "Medium": lambda t: between(t.a, 100, 999) and last_two_in(t.a, 75, 99)
        and between(t.b, 100, 999),
        "Hard": lambda t: between(t.a, 100, 999) and last_two_in(t.a, 50, 99)
        and between(t.b, 100, 999),
        "Pro": lambda t: between(t.a, 1000, 9999) and 950 <= t.a % 1000 <= 999
        and between(t.b, 1000, 9999),
    },
    "A5": {
        "Easy": lambda t: t.a in range(19, 90, 10) and between(t.b, 1, 9),
        "Medium": lambda t: t.a in range(19, 90, 10) and between(t.b, 10, 99),
        "Hard": lambda t: t.a in range(199, 1000, 100) and between(t.b, 100, 999),
        "Pro": lambda t: t.a in range(1999, 10000, 1000) and between(t.b, 1000, 9999),
    },
    "S1": {
        "Easy": lambda t: between(t.a, 10, 99) and between(t.b, 1, 9),
        "Medium": lambda t: between(t.a, 10, 99) and between(t.b, 10, 99),
        "Hard": lambda t: between(t.a, 100, 999) and between(t.b, 10, 99),
        "Pro": lambda t: between(t.a, 100, 999) and between(t.b, 100, 999),
    },
    "S2": {
        level: (lambda digits: lambda t: size(t.a) == digits and no_borrowing(t.a, t.b))(digits)
        for level, digits in zip(LEVELS, (2, 3, 4, 5))
    },
    "S3": {
        "Easy": lambda t: t.a == 100 and between(t.b, 10, 99),
        "Medium": lambda t: t.a in range(200, 1000, 100) and between(t.b, 10, 999),
        "Hard": lambda t: t.a == 1000 and between(t.b, 100, 999),
        "Pro": lambda t: t.a in range(2000, 10000, 1000) and between(t.b, 100, 9999),
    },
    "S4": {
        "Easy": lambda t: between(t.a, 10, 99) and between(t.b, 18, 98)
        and ends_in(t.b, {8, 9}),
        "Medium": lambda t: between(t.a, 100, 999) and between(t.b, 10, 99)
        and ends_in(t.b, {7, 8, 9}),
        "Hard": lambda t: between(t.a, 100, 999) and between(t.b, 197, 998)
        and last_two_in(t.b, 97, 99),
        "Pro": lambda t: between(t.a, 1000, 9999) and between(t.b, 100, 999)
        and last_two_in(t.b, 95, 99),
    },
    "S5": {
        "Easy": lambda t: between(t.a, 10, 99) and between(t.b, 10, 98)
        and ends_in(t.b, {8, 9}),
        "Medium": lambda t: between(t.a, 10, 99) and between(t.b, 10, 98)
        and ends_in(t.b, {6, 7, 8, 9}),
        "Hard": lambda t: between(t.a, 100, 999) and between(t.b, 10, 99)
        and ends_in(t.b, {5, 6, 7, 8, 9}),
        "Pro": lambda t: between(t.a, 100, 999) and between(t.b, 100, 998)
        and last_two_in(t.b, 95, 99),
    },
    "S6": {
        "Easy": lambda t: size(t.a) == size(t.b) == 2 and borrowing_places(t.a, t.b, [0]) == [0],
        "Medium": lambda t: size(t.a) == size(t.b) == 3
        and len(borrowing_places(t.a, t.b, [0, 1])) == 1,
        "Hard": lambda t: size(t.a) == size(t.b) == 3
        and borrowing_places(t.a, t.b, [0, 1]) == [0, 1],
        "Pro": lambda t: size(t.a) == size(t.b) == 4
        and len(borrowing_places(t.a, t.b, [0, 1, 2])) in (1, 2),
    },
    "S7": {
        "Easy": lambda t: t.a == 100 and between(t.b, 11, 99),
        "Medium": lambda t: t.a == 1000 and between(t.b, 101, 999),
        "Hard": lambda t: t.a == 10_000 and between(t.b, 1001, 9999),
        "Pro": lambda t: t.a == 100_000 and between(t.b, 10_001, 99_999),
    },
    "S8": {
        "Easy": lambda t: size(t.a) == size(t.b) == 2 and t.a // 10 > t.b // 10,
        "Medium": lambda t: between(t.a, 101, 199) and between(t.b, 10, 99),
        "Hard": lambda t: size(t.a) == size(t.b) == 3 and t.a // 100 > t.b // 100,
        "Pro": lambda t: between(t.a, 1000, 9999) and between(t.b, 100, 999),
    },
    "M1": {
        "Easy": times(5, 2, 20, lambda n: n % 2 == 0),
        "Medium": times(5, 22, 98, lambda n: n % 2 == 0),
        "Hard": times(5, 11, 99),
        "Pro": times(5, 100, 999),
    },
    "M2": {"Easy": times(8, 2, 12), "Medium": times(8, 13, 50),
           "Hard": times(8, 51, 150), "Pro": times(8, 151, 999)},
    "M3": {"Easy": times(9, 2, 12), "Medium": times(9, 13, 99),
           "Hard": times(9, 100, 999), "Pro": times(9, 1000, 9999)},
    "M4": {
        "Easy": times(11, 1, 9),
        "Medium": times(11, 10, 99, lambda n: digit_sum(n) <= 9),
        "Hard": times(11, 10, 99, lambda n: digit_sum(n) >= 10),
        "Pro": times(11, 100, 999),
    },
    "M5": {"Easy": times(12, 2, 12), "Medium": times(12, 13, 99),
           "Hard": times(12, 100, 999), "Pro": times(12, 1000, 9999)},
    "M6": {"Easy": times(13, 2, 12), "Medium": times(13, 13, 99),
           "Hard": times(13, 100, 999), "Pro": times(13, 1000, 9999)},
    "M7": {"Easy": times(25, 2, 12), "Medium": times(25, 13, 40),
           "Hard": times(25, 41, 199), "Pro": times(25, 200, 999)},
    "M8": {"Easy": times(99, 2, 12), "Medium": times(99, 13, 99),
           "Hard": times(99, 100, 999), "Pro": times(99, 1000, 9999)},
    "D1": {"Easy": divide(5, 2, 10), "Medium": divide(5, 11, 100),
           "Hard": divide(5, 101, 1000), "Pro": divide(5, 1001, 10_000)},
    "D2": {"Easy": divide(8, 2, 10), "Medium": divide(8, 11, 50),
           "Hard": divide(8, 51, 200), "Pro": divide(8, 201, 1000)},
    "D3": {
        "Easy": lambda t: t.a % 10 == 0 and between(t.a // 10, 1, 9)
        and t.b % 10 == 0 and between(t.b // 10, 1, 9),
        "Medium": lambda t: t.a % 100 == 0 and between(t.a // 100, 1, 9)
        and t.b % 10 == 0 and between(t.b // 10, 1, 9),
        "Hard": lambda t: t.a % 1000 == 0 and between(t.a // 1000, 1, 9)
        and t.b % 100 == 0 and between(t.b // 100, 1, 9),
        "Pro": lambda t: t.a % 1000 == 0 and between(t.a // 1000, 10, 99)
        and t.b % 100 == 0 and between(t.b // 100, 10, 99),
    },
    "D4": {
        "Easy": lambda t: t.b in (4, 6, 8) and t.a % 2 == 0 and between(t.answer, 2, 9),
        "Medium": lambda t: between(t.b, 10, 20) and has_factor(t.b, 2, 5)
        and between(t.answer, 2, 12),
        "Hard": lambda t: between(t.a, 100, 999) and between(t.b, 10, 99)
        and has_factor(t.b, 2, 9) and between(t.answer, 2, 20),
        "Pro": lambda t: between(t.a, 1000, 9999) and between(t.b, 10, 99)
        and has_factor(t.b, 2, 9) and between(t.answer, 11, 99),
    },
    # Decision 1 in specs/009: the method only works for 11–19.
    "Q1": {"Easy": square(11, 13), "Medium": square(14, 16),
           "Hard": square(17, 19), "Pro": square(11, 19)},
    "Q2": {"Easy": square(45, 55), "Medium": square(35, 65),
           "Hard": square(30, 70), "Pro": square(26, 74)},
    "Q3": {"Easy": square(95, 105, also_not={100}), "Medium": square(90, 110, also_not={100}),
           "Hard": square(80, 120, also_not={100}), "Pro": square(76, 125, also_not={100})},
    "Q4": {"Easy": square(15, 45, ending_5=True), "Medium": square(55, 95, ending_5=True),
           "Hard": square(105, 495, ending_5=True), "Pro": square(505, 995, ending_5=True)},
    "Q5": {"Easy": square(11, 29), "Medium": square(31, 59),
           "Hard": square(61, 99), "Pro": square(101, 199)},
}  # fmt: skip

OPERATIONS = {"A": "+", "S": "−", "M": "×", "D": "÷", "Q": "²"}
TRICK_IDS = list(RULES)
ALL_CASES = [(trick_id, level) for trick_id in TRICK_IDS for level in LEVELS]


def tasks_for(trick_id, level, seed=SEED, count=1000):
    rng = random.Random(seed)
    found = []
    previous = None
    for _ in range(count):
        previous = generate_task(trick_id, level, rng, previous=previous)
        found.append(previous)
    return found


def expected_answer(task):
    return {
        "+": lambda: task.a + task.b,
        "−": lambda: task.a - task.b,
        "×": lambda: task.a * task.b,
        "÷": lambda: task.a / task.b,
        "²": lambda: task.a**2,
    }[task.operation]()


# --- Generation (K R4, KA6) ---


def test_there_is_a_rule_for_every_trick():
    assert len(TRICK_IDS) == 30


@pytest.mark.parametrize("trick_id, level", ALL_CASES)
def test_1000_tasks_lie_in_the_range_and_have_whole_answers(trick_id, level):
    rule = RULES[trick_id][level]
    for task in tasks_for(trick_id, level):
        assert task.trick_id == trick_id
        assert task.operation == OPERATIONS[trick_id[0]]
        assert rule(task), f"{trick_id} {level}: {task.text} is outside the range"
        assert isinstance(task.answer, int)
        assert task.answer == expected_answer(task)
        assert task.answer >= 1


@pytest.mark.parametrize("trick_id, level", ALL_CASES)
def test_no_task_appears_twice_in_a_row(trick_id, level):
    found = tasks_for(trick_id, level, count=300)
    assert all(first != second for first, second in zip(found, found[1:]))


@pytest.mark.parametrize("trick_id, level", ALL_CASES)
def test_rounds_differ_between_seeds_and_repeat_with_the_same_seed(trick_id, level):
    assert tasks_for(trick_id, level, 1, 10) != tasks_for(trick_id, level, 2, 10)
    assert tasks_for(trick_id, level, 3, 10) == tasks_for(trick_id, level, 3, 10)


def test_generation_does_not_touch_global_randomness():
    state = random.getstate()
    tasks_for("M4", "Pro", count=50)
    assert random.getstate() == state


@pytest.mark.parametrize(
    "task, text",
    [
        (PracticeTask("A1", "+", 56, 38), "56 + 38"),
        (PracticeTask("S7", "−", 1000, 728), "1,000 − 728"),
        (PracticeTask("M4", "×", 243, 11), "243 × 11"),
        (PracticeTask("D3", "÷", 8000, 200), "8,000 ÷ 200"),
        (PracticeTask("Q4", "²", 205, None), "205²"),
    ],
)
def test_task_text(task, text):
    assert task.text == text


@pytest.mark.parametrize("trick_id, level", [("Q1", "Easy"), ("A1", "Easy")])
def test_unknown_trick_or_level_raises(trick_id, level):
    with pytest.raises(ValueError):
        generate_task(trick_id + "X", level, random.Random(0))
    with pytest.raises(ValueError):
        generate_task(trick_id, "Extreme", random.Random(0))


# --- A round (K R4–K R6, KA7) ---


def new_round(trick_id="M4", level="Easy", seed=SEED):
    return start_round(trick_id, level, random.Random(seed))


def answer_right(practice_round):
    return submit_answer(practice_round, str(current_task(practice_round).answer))


def test_a_round_has_exactly_10_tasks_for_one_trick_and_level():
    practice_round = new_round("A1", "Hard")
    assert ROUND_LENGTH == 10
    assert len(practice_round.tasks) == 10
    assert {(t.trick_id, RULES["A1"]["Hard"](t)) for t in practice_round.tasks} == {("A1", True)}
    assert all(a != b for a, b in zip(practice_round.tasks, practice_round.tasks[1:]))
    assert practice_round.status == Status.RUNNING
    assert current_task(practice_round) == practice_round.tasks[0]


def test_correct_answer_adds_a_point_and_moves_on():
    practice_round, outcome = answer_right(new_round())
    assert outcome == Outcome.CORRECT
    assert (practice_round.correct, practice_round.wrong, practice_round.skipped) == (1, 0, 0)
    assert current_task(practice_round) == practice_round.tasks[1]


def test_wrong_answer_adds_nothing_and_keeps_the_correct_answer():
    start = new_round()
    task = current_task(start)
    practice_round, outcome = submit_answer(start, str(task.answer + 1))
    assert outcome == Outcome.WRONG
    assert (practice_round.correct, practice_round.wrong) == (0, 1)
    assert practice_round.attempts[-1].task == task
    assert practice_round.attempts[-1].given == str(task.answer + 1)
    assert current_task(practice_round) == practice_round.tasks[1]


def test_skip_adds_nothing_and_is_recorded_as_skipped():
    start = new_round()
    practice_round, outcome = skip_task(start)
    assert outcome == Outcome.SKIPPED
    assert (practice_round.correct, practice_round.wrong, practice_round.skipped) == (0, 0, 1)
    assert practice_round.attempts[-1].task == current_task(start)


@pytest.mark.parametrize("raw", ["", "   ", "abc", "5.5", "1,250"])
def test_empty_or_non_numeric_input_changes_nothing(raw):
    start = new_round()
    practice_round, outcome = submit_answer(start, raw)
    assert outcome == Outcome.IGNORED
    assert practice_round == start


def test_7_correct_2_wrong_1_skipped_gives_7_of_10_and_completes():
    practice_round = new_round("M4", "Hard")
    for _ in range(7):
        practice_round, _ = answer_right(practice_round)
    for _ in range(2):
        practice_round, _ = submit_answer(practice_round, "0")
    assert practice_round.status == Status.RUNNING  # 9 of 10 done
    practice_round, _ = skip_task(practice_round)

    assert (practice_round.correct, practice_round.wrong, practice_round.skipped) == (7, 2, 1)
    assert practice_round.status == Status.COMPLETED
    assert current_task(practice_round) is None


def test_actions_after_the_tenth_task_are_ignored():
    practice_round = new_round()
    for _ in range(10):
        practice_round, _ = skip_task(practice_round)
    for action in (lambda r: submit_answer(r, "5"), skip_task):
        after, outcome = action(practice_round)
        assert (after, outcome) == (practice_round, Outcome.IGNORED)


def test_every_round_generates_new_tasks():
    assert new_round(seed=1).tasks != new_round(seed=2).tasks


# --- Navigation (K R3, KA4) ---


def test_previous_and_next_stay_within_the_category():
    assert neighbours("A1") == (None, "A2")
    assert neighbours("A3") == ("A2", "A4")
    assert neighbours("A5") == ("A4", None)  # not S1 of the next category
    assert neighbours("S1") == (None, "S2")
    assert neighbours("Q5") == ("Q4", None)


def test_position_within_the_category():
    assert position("A2") == (2, 5)
    assert position("S8") == (8, 8)
    assert position("D1") == (1, 4)


# --- Practised (K R7) ---


def saved(trick_id, level="Easy", correct=0, run_id=None):
    return SavedRound(
        id=run_id or f"{trick_id}-{level}-{correct}",
        trick_id=trick_id,
        level=level,
        finished_at=datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc),
        correct=correct,
    )


def test_no_rounds_means_nothing_practised():
    assert practised([]) == set()


def test_one_round_at_any_level_and_score_counts_as_practised():
    assert practised([saved("M4", "Pro", correct=0)]) == {"M4"}
    assert practised([saved("M4"), saved("M4", "Hard", 10), saved("A1")]) == {"M4", "A1"}


def test_rule_module_follows_the_design_rules():
    source = (ROOT / "knowledge.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", ".now(", "time.time", "random.Random("):
        assert forbidden not in source
