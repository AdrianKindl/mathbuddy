"""Test run rules: time limit, scoring, completion, highscore (MB R3-R6)."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import runs
from runs import (
    Outcome,
    SavedRun,
    Status,
    abort_run,
    accuracy,
    finish_if_expired,
    finished_at,
    highscores,
    is_new_highscore,
    is_time_up,
    remaining_seconds,
    skip_task,
    start_run,
    submit_answer,
)
from tasks import Task

T0 = datetime(2026, 11, 3, 12, 0, 0, tzinfo=timezone.utc)
TASK = Task("Multiplication", 7, 8)  # the example from A3; the answer is 56


def at(seconds):
    return T0 + timedelta(seconds=seconds)


def new_run():
    return start_run("Multiplication", "Easy", T0)


def totals(run):
    return run.correct, run.wrong, run.skipped


def saved(run_id, test_type, level, correct, wrong=0, skipped=0):
    return SavedRun(
        id=run_id,
        test_type=test_type,
        level=level,
        finished_at=at(60),
        correct=correct,
        wrong=wrong,
        skipped=skipped,
    )


# --- Starting a run ---


def test_constants_match_the_brief():
    assert runs.TIME_LIMIT_SECONDS == 60
    assert runs.COUNTDOWN_SECONDS == 3


def test_new_run_starts_empty_and_running():
    run = new_run()
    assert (run.test_type, run.level, run.started_at) == ("Multiplication", "Easy", T0)
    assert totals(run) == (0, 0, 0)
    assert run.status is Status.RUNNING


@pytest.mark.parametrize(
    "test_type, level",
    [("Addition", "Impossible"), ("Percentage", "Easy")],
)
def test_invalid_test_type_or_level_raises(test_type, level):
    with pytest.raises(ValueError):
        start_run(test_type, level, T0)


# --- Answers and skip (A3) ---


def test_correct_answer_adds_a_point():
    run, outcome = submit_answer(new_run(), TASK, "56", at(1))
    assert outcome is Outcome.CORRECT
    assert totals(run) == (1, 0, 0)
    assert run.status is Status.RUNNING


def test_wrong_answer_adds_no_point():
    run, outcome = submit_answer(new_run(), TASK, "54", at(1))
    assert outcome is Outcome.WRONG
    assert totals(run) == (0, 1, 0)


def test_skip_is_recorded_as_skipped_only():
    """Decision 1: skip counts as wrong through accuracy, not through `wrong`."""
    run, outcome = skip_task(new_run(), at(1))
    assert outcome is Outcome.SKIPPED
    assert totals(run) == (0, 0, 1)
    assert accuracy(run.correct, run.wrong, run.skipped) == 0


@pytest.mark.parametrize("raw", ["", "   ", "abc", "5.5", "1,250", "1_000"])
def test_empty_or_non_numeric_input_changes_nothing(raw):
    before = new_run()
    run, outcome = submit_answer(before, TASK, raw, at(1))
    assert outcome is Outcome.IGNORED
    assert run == before


def test_negative_answer_is_evaluated_as_wrong():
    run, outcome = submit_answer(new_run(), TASK, "-5", at(1))
    assert outcome is Outcome.WRONG
    assert totals(run) == (0, 1, 0)


def test_actions_return_a_new_run_and_leave_the_old_one_unchanged():
    before = new_run()
    submit_answer(before, TASK, "56", at(1))
    skip_task(before, at(2))
    abort_run(before, at(3))
    assert totals(before) == (0, 0, 0)
    assert before.status is Status.RUNNING
    with pytest.raises(FrozenInstanceError):
        before.correct = 5


# --- Time limit (A4) ---


def test_answer_at_59_9_seconds_counts():
    run, outcome = submit_answer(new_run(), TASK, "56", at(59.9))
    assert outcome is Outcome.CORRECT
    assert run.correct == 1
    assert run.status is Status.RUNNING


def test_answer_one_microsecond_before_the_limit_counts():
    run, outcome = submit_answer(new_run(), TASK, "56", at(59.999999))
    assert outcome is Outcome.CORRECT
    assert run.correct == 1


@pytest.mark.parametrize("seconds", [60, 60.000001, 61, 3600])
@pytest.mark.parametrize("raw", ["56", "54", "", "abc"])
def test_any_input_at_or_after_60_seconds_does_not_count_and_ends_the_run(seconds, raw):
    run, outcome = submit_answer(new_run(), TASK, raw, at(seconds))
    assert outcome is Outcome.TIME_UP
    assert totals(run) == (0, 0, 0)
    assert run.status is Status.COMPLETED


def test_time_is_checked_before_the_answer_is_counted():
    run, _ = submit_answer(new_run(), TASK, "56", at(10))
    run, _ = submit_answer(run, TASK, "54", at(20))
    run, _ = skip_task(run, at(30))
    run, outcome = submit_answer(run, TASK, "56", at(60))
    assert outcome is Outcome.TIME_UP
    assert totals(run) == (1, 1, 1)  # earlier totals are kept
    assert run.status is Status.COMPLETED


@pytest.mark.parametrize("seconds", [60, 61])
def test_skip_at_or_after_60_seconds_does_not_count_and_ends_the_run(seconds):
    run, outcome = skip_task(new_run(), at(seconds))
    assert outcome is Outcome.TIME_UP
    assert totals(run) == (0, 0, 0)
    assert run.status is Status.COMPLETED


def test_skip_at_59_9_seconds_counts():
    run, outcome = skip_task(new_run(), at(59.9))
    assert outcome is Outcome.SKIPPED
    assert run.skipped == 1


def test_countdown_is_not_part_of_the_60_seconds():
    countdown_began = T0
    started = countdown_began + timedelta(seconds=runs.COUNTDOWN_SECONDS)
    run = start_run("Addition", "Easy", started)
    task = Task("Addition", 1, 2)

    # 62.9 s after the countdown began is only 59.9 s into the run.
    counted, outcome = submit_answer(run, task, "3", countdown_began + timedelta(seconds=62.9))
    assert outcome is Outcome.CORRECT
    assert counted.correct == 1

    late, outcome = submit_answer(run, task, "3", countdown_began + timedelta(seconds=63))
    assert outcome is Outcome.TIME_UP
    assert late.correct == 0


@pytest.mark.parametrize(
    "seconds, expected",
    [(0, False), (59.9, False), (60, True), (75, True)],
)
def test_is_time_up(seconds, expected):
    assert is_time_up(new_run(), at(seconds)) is expected


@pytest.mark.parametrize(
    "seconds, expected",
    [(0, 60), (0.5, 59.5), (59.9, 0.1), (60, 0), (75, 0)],
)
def test_remaining_seconds_never_goes_below_zero(seconds, expected):
    assert remaining_seconds(new_run(), at(seconds)) == pytest.approx(expected)


# --- Completion and abort (R5) ---


def test_finish_if_expired_leaves_a_run_within_the_limit_running():
    run = new_run()
    assert finish_if_expired(run, at(59.9)) == run


def test_finish_if_expired_completes_a_run_at_the_limit_and_keeps_totals():
    run, _ = submit_answer(new_run(), TASK, "56", at(1))
    finished = finish_if_expired(run, at(60))
    assert finished.status is Status.COMPLETED
    assert totals(finished) == (1, 0, 0)


def test_aborted_run_is_not_completed_by_expiry():
    aborted = abort_run(new_run(), at(30))
    assert finish_if_expired(aborted, at(61)) == aborted


@pytest.mark.parametrize("seconds", [0, 30, 59.9])
def test_abort_before_the_limit_marks_the_run_aborted(seconds):
    assert abort_run(new_run(), at(seconds)).status is Status.ABORTED


@pytest.mark.parametrize("seconds", [60, 61])
def test_abort_at_or_after_the_limit_counts_as_completed(seconds):
    """The run reached its end before the abort arrived (MB R5)."""
    run, _ = submit_answer(new_run(), TASK, "56", at(1))
    finished = abort_run(run, at(seconds))
    assert finished.status is Status.COMPLETED
    assert finished.correct == 1


@pytest.mark.parametrize(
    "end",
    [lambda run: abort_run(run, at(30)), lambda run: finish_if_expired(run, at(60))],
    ids=["aborted", "completed"],
)
def test_actions_after_the_end_are_ignored(end):
    ended = end(new_run())
    # Use a time that would otherwise count, so only the status can reject them.
    answered, answer_outcome = submit_answer(ended, TASK, "56", at(31))
    skipped, skip_outcome = skip_task(ended, at(31))
    assert (answered, answer_outcome) == (ended, Outcome.IGNORED)
    assert (skipped, skip_outcome) == (ended, Outcome.IGNORED)
    assert abort_run(ended, at(31)) == ended


def test_finished_at_is_exactly_60_seconds_after_the_start():
    """Decision 7: it does not depend on when the app noticed the end."""
    run = new_run()
    noticed_late = finish_if_expired(run, at(95))
    assert finished_at(noticed_late) == at(60)


# --- Accuracy (R3, decision 5) ---


def test_accuracy_12_correct_3_wrong_2_skipped():
    assert accuracy(12, 3, 2) == pytest.approx(12 / 17)


def test_skipped_lowers_accuracy():
    assert accuracy(1, 0, 1) == pytest.approx(0.5)


def test_accuracy_extremes():
    assert accuracy(5, 0, 0) == 1
    assert accuracy(0, 5, 0) == 0


def test_accuracy_without_attempts_is_none():
    assert accuracy(0, 0, 0) is None


# --- Highscore (A6, decision 6) ---


def test_highscore_is_the_best_saved_score():
    saved_runs = [saved("a", "Multiplication", "Easy", 15), saved("b", "Multiplication", "Easy", 12)]
    assert highscores(saved_runs) == {("Multiplication", "Easy"): 15}


def test_higher_score_raises_the_highscore_and_is_flagged():
    saved_runs = [saved("a", "Multiplication", "Easy", 15), saved("b", "Multiplication", "Easy", 12)]
    previous = highscores(saved_runs)[("Multiplication", "Easy")]
    assert is_new_highscore(previous, 18) is True

    saved_runs.append(saved("c", "Multiplication", "Easy", 18))
    assert highscores(saved_runs)[("Multiplication", "Easy")] == 18


def test_medium_run_does_not_change_the_easy_highscore():
    saved_runs = [saved("a", "Multiplication", "Easy", 15), saved("b", "Multiplication", "Medium", 30)]
    assert highscores(saved_runs) == {
        ("Multiplication", "Easy"): 15,
        ("Multiplication", "Medium"): 30,
    }


def test_random_has_its_own_highscore():
    saved_runs = [saved("a", "Random", "Easy", 9), saved("b", "Addition", "Easy", 4)]
    assert highscores(saved_runs) == {("Random", "Easy"): 9, ("Addition", "Easy"): 4}


def test_only_correct_answers_count_towards_the_highscore():
    saved_runs = [saved("a", "Addition", "Easy", 3, wrong=20, skipped=20)]
    assert highscores(saved_runs) == {("Addition", "Easy"): 3}


def test_no_saved_runs_give_no_highscores():
    assert highscores([]) == {}


@pytest.mark.parametrize(
    "previous, score, expected",
    [
        (15, 18, True),
        (15, 12, False),
        (15, 15, False),  # a tie is not new
        (None, 1, True),  # a first run above 0 is new
        (None, 0, False),  # a first run with 0 is not new
        (0, 0, False),
        (0, 1, True),
    ],
)
def test_is_new_highscore(previous, score, expected):
    assert is_new_highscore(previous, score) is expected


def test_module_follows_design_rules():
    source = (Path(__file__).parent.parent / "runs.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", ".now(", "time.time", "random.Random("):
        assert forbidden not in source
