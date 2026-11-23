"""Trainer screens in trainer_ui.py and their wiring in app.py, driven through AppTest.

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
    # Some decimal tasks have a whole answer (5.4 + 8.6 = 14), with no point to
    # turn into a comma. Answer those first, so the test does not depend on chance.
    while "." not in right_answer(at):
        submit(at, right_answer(at))
    before = at.session_state["tr_session"]
    submit(at, right_answer(at).replace(".", ","))  # a comma is not evaluated
    assert at.session_state["tr_session"].attempts == before.attempts
    assert [box.value for box in at.warning] == [ANSWER_HINTS[AnswerKind.DECIMAL]]

    submit(at, right_answer(at))
    assert at.session_state["tr_session"].correct == before.correct + 1


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
