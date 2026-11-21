"""Trainer session rules: settings, modes, time limits and results (spec 002)."""

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
