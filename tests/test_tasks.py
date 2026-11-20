"""Task generation and answer checking (MB R1-R3, scenarios A1-A3)."""

import random
from collections import Counter
from pathlib import Path

import pytest

import tasks
from tasks import Task, generate_task, is_correct, parse_answer

OPERATIONS = ["Addition", "Subtraction", "Multiplication", "Division"]
TEST_TYPES = [*OPERATIONS, "Random"]
LEVELS = ["Easy", "Medium", "Hard", "Pro"]
ALL_COMBINATIONS = [(t, level) for t in TEST_TYPES for level in LEVELS]
OPERATION_COMBINATIONS = [(op, level) for op in OPERATIONS for level in LEVELS]

# MB R1, copied from the product brief on purpose. It is not imported from
# tasks.py, so a wrong table in tasks.py cannot pass by checking itself.
# Addition, Subtraction, Multiplication: (a range, b range).
# Division: (divisor b range, result q range).
MB_R1 = {
    ("Addition", "Easy"): ((1, 19), (1, 19)),
    ("Addition", "Medium"): ((20, 249), (20, 249)),
    ("Addition", "Hard"): ((250, 1249), (250, 1249)),
    ("Addition", "Pro"): ((1250, 5000), (1250, 5000)),
    ("Subtraction", "Easy"): ((1, 19), (1, 19)),
    ("Subtraction", "Medium"): ((10, 99), (10, 99)),
    ("Subtraction", "Hard"): ((100, 999), (100, 999)),
    ("Subtraction", "Pro"): ((1000, 9999), (1000, 9999)),
    ("Multiplication", "Easy"): ((2, 9), (2, 9)),
    ("Multiplication", "Medium"): ((11, 28), (2, 9)),
    ("Multiplication", "Hard"): ((11, 19), (11, 19)),
    ("Multiplication", "Pro"): ((20, 48), (11, 17)),
    ("Division", "Easy"): ((2, 9), (2, 9)),
    ("Division", "Medium"): ((2, 9), (11, 29)),
    ("Division", "Hard"): ((29, 99), (11, 29)),
    ("Division", "Pro"): ((101, 291), (11, 28)),
}


def generate_round(test_type, level, seed, count=1000):
    """Generate tasks the way a round does: each one knows the previous one."""
    rng = random.Random(seed)
    round_tasks = []
    previous = None
    for _ in range(count):
        previous = generate_task(test_type, level, rng, previous=previous)
        round_tasks.append(previous)
    return round_tasks


def checked_numbers(task):
    """The two numbers MB R1 constrains. For division these are b and q."""
    if task.operation == "Division":
        return task.b, task.a // task.b
    return task.a, task.b


def assert_follows_mb_r1(task, level):
    (first_low, first_high), (second_low, second_high) = MB_R1[(task.operation, level)]
    first, second = checked_numbers(task)
    assert first_low <= first <= first_high, task
    assert second_low <= second <= second_high, task
    if task.operation == "Subtraction":
        assert task.a > task.b, task
    if task.operation == "Division":
        assert task.a % task.b == 0, task


# --- Generation (A1) ---


@pytest.mark.parametrize("test_type, level", ALL_COMBINATIONS)
def test_1000_tasks_follow_mb_r1(test_type, level):
    for task in generate_round(test_type, level, seed=1):
        if test_type != "Random":
            assert task.operation == test_type
        assert task.operation in OPERATIONS
        assert_follows_mb_r1(task, level)


def test_there_are_20_combinations():
    assert len(ALL_COMBINATIONS) == 20
    assert list(tasks.TEST_TYPES) == TEST_TYPES
    assert list(tasks.LEVELS) == LEVELS


def test_pro_division_divisor_result_and_no_remainder():
    for task in generate_round("Division", "Pro", seed=2):
        assert 101 <= task.b <= 291
        assert 11 <= task.a // task.b <= 28
        assert task.a % task.b == 0


def test_easy_subtraction_result_is_at_least_1():
    for task in generate_round("Subtraction", "Easy", seed=3):
        assert task.answer >= 1


@pytest.mark.parametrize("level", ["Medium", "Hard", "Pro"])
def test_no_trivial_factors_from_medium_upwards(level):
    for task in generate_round("Multiplication", level, seed=4):
        assert not {task.a, task.b} & {1, 10}


@pytest.mark.parametrize("level", ["Medium", "Hard", "Pro"])
def test_no_trivial_divisors_from_medium_upwards(level):
    for task in generate_round("Division", level, seed=5):
        assert task.b not in {1, 10, 100}


@pytest.mark.parametrize("test_type, level", OPERATION_COMBINATIONS)
def test_range_limits_are_inclusive_and_reachable(test_type, level):
    """Catches off-by-one ranges. 50,000 tasks make missing a limit very unlikely."""
    pairs = [checked_numbers(t) for t in generate_round(test_type, level, 6, 50_000)]
    firsts = [pair[0] for pair in pairs]
    seconds = [pair[1] for pair in pairs]
    (first_low, first_high), (second_low, second_high) = MB_R1[(test_type, level)]

    if test_type == "Subtraction":
        # The larger number comes first, so check the limits across both numbers.
        assert min(seconds) == first_low
        assert max(firsts) == first_high
    else:
        assert (min(firsts), max(firsts)) == (first_low, first_high)
        assert (min(seconds), max(seconds)) == (second_low, second_high)


@pytest.mark.parametrize("level", LEVELS)
def test_random_picks_each_operation_with_equal_probability(level):
    counts = Counter(t.operation for t in generate_round("Random", level, 7, 4000))
    assert set(counts) == set(OPERATIONS)
    for operation in OPERATIONS:
        assert 880 <= counts[operation] <= 1120  # 25% of 4000, +/- 3 percentage points


@pytest.mark.parametrize(
    "test_type, level",
    [("Addition", "Impossible"), ("Percentage", "Easy"), ("addition", "Easy")],
)
def test_invalid_test_type_or_level_raises(test_type, level):
    with pytest.raises(ValueError):
        generate_task(test_type, level, random.Random(0))


# --- Variety (A2) ---


@pytest.mark.parametrize("test_type, level", ALL_COMBINATIONS)
def test_no_task_appears_twice_in_a_row(test_type, level):
    round_tasks = generate_round(test_type, level, seed=8)
    for first, second in zip(round_tasks, round_tasks[1:]):
        assert first != second


def test_previous_task_is_never_returned():
    previous = Task("Multiplication", 7, 8)
    rng = random.Random(9)
    for _ in range(2000):
        assert generate_task("Multiplication", "Easy", rng, previous=previous) != previous


@pytest.mark.parametrize("test_type, level", ALL_COMBINATIONS)
def test_different_seeds_give_different_sequences(test_type, level):
    assert generate_round(test_type, level, seed=10) != generate_round(test_type, level, seed=11)


@pytest.mark.parametrize("test_type, level", ALL_COMBINATIONS)
def test_same_seed_gives_same_sequence(test_type, level):
    assert generate_round(test_type, level, seed=12) == generate_round(test_type, level, seed=12)


def test_generation_does_not_touch_global_randomness():
    state = random.getstate()
    generate_round("Random", "Pro", seed=13, count=100)
    assert random.getstate() == state


def test_module_follows_design_rules():
    source = (Path(__file__).parent.parent / "tasks.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", ".now(", "time.time", "random.Random("):
        assert forbidden not in source


# --- Task (decisions 4 and 10) ---


@pytest.mark.parametrize(
    "task, answer",
    [
        (Task("Addition", 7, 8), 15),
        (Task("Subtraction", 8, 7), 1),
        (Task("Multiplication", 7, 8), 56),
        (Task("Division", 56, 7), 8),
    ],
)
def test_task_answer(task, answer):
    assert task.answer == answer


@pytest.mark.parametrize(
    "task, text",
    [
        (Task("Addition", 1250, 3000), "1,250 + 3,000"),
        (Task("Subtraction", 1000, 999), "1,000 − 999"),
        (Task("Multiplication", 7, 8), "7 × 8"),
        (Task("Division", 5548, 292), "5,548 ÷ 292"),
    ],
)
def test_task_text(task, text):
    assert task.text == text


def test_same_numbers_in_other_order_are_a_different_task():
    assert Task("Multiplication", 7, 8) == Task("Multiplication", 7, 8)
    assert Task("Multiplication", 7, 8) != Task("Multiplication", 8, 7)


def test_same_numbers_with_another_operation_are_a_different_task():
    assert Task("Addition", 7, 8) != Task("Multiplication", 7, 8)


# --- Answer checking (A3, decisions 2 and 3) ---


@pytest.mark.parametrize(
    "raw, expected",
    [("56", 56), (" 56 ", 56), ("0", 0), ("007", 7), ("-5", -5), ("+5", 5)],
)
def test_parse_answer_accepts_whole_numbers(raw, expected):
    assert parse_answer(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "abc",
        "5.5",
        "56.0",
        "1,250",
        "1 250",
        "1_000",
        "5e3",
        "0x10",
        "--5",
        "+",
        "-",
        "٥٦",  # Arabic-Indic digits, which int() would accept
        "５６",  # full-width digits, which int() would accept
        "²",  # superscript two
    ],
)
def test_parse_answer_ignores_everything_else(raw):
    assert parse_answer(raw) is None


def test_is_correct():
    task = Task("Multiplication", 7, 8)
    assert is_correct(task, 56) is True
    assert is_correct(task, 54) is False
    assert is_correct(task, -56) is False
