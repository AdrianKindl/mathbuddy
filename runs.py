"""Test run rules: time limit, scoring, completion and highscore (MB R3-R6)."""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from tasks import LEVELS, TEST_TYPES, Task, is_correct, parse_answer

TIME_LIMIT_SECONDS = 60
COUNTDOWN_SECONDS = 3

_TIME_LIMIT = timedelta(seconds=TIME_LIMIT_SECONDS)


# StrEnum, and always compared with == rather than `is`. Streamlit re-imports a
# module when its source changes, but a Run in session_state keeps the old class.
# Members of the old and new class are only equal when they compare by value.
class Status(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    SKIPPED = "skipped"
    IGNORED = "ignored"
    TIME_UP = "time_up"


@dataclass(frozen=True)
class Run:
    test_type: str
    level: str
    started_at: datetime
    correct: int = 0
    wrong: int = 0
    skipped: int = 0
    status: Status = Status.RUNNING


@dataclass(frozen=True)
class SavedRun:
    id: str
    test_type: str
    level: str
    finished_at: datetime
    correct: int
    wrong: int
    skipped: int


def start_run(test_type: str, level: str, now: datetime) -> Run:
    """Start a run at `now`, which is after the countdown (MB R4)."""
    if test_type not in TEST_TYPES or level not in LEVELS:
        raise ValueError(f"Unknown test type or level: {test_type!r}, {level!r}")
    return Run(test_type, level, started_at=now)


def is_time_up(run: Run, now: datetime) -> bool:
    return now - run.started_at >= _TIME_LIMIT


def remaining_seconds(run: Run, now: datetime) -> float:
    return max(0.0, (run.started_at + _TIME_LIMIT - now).total_seconds())


def submit_answer(run: Run, task: Task, raw: str, now: datetime) -> tuple[Run, Outcome]:
    if run.status != Status.RUNNING:
        return run, Outcome.IGNORED
    if is_time_up(run, now):
        return replace(run, status=Status.COMPLETED), Outcome.TIME_UP

    answer = parse_answer(raw)
    if answer is None:
        return run, Outcome.IGNORED
    if is_correct(task, answer):
        return replace(run, correct=run.correct + 1), Outcome.CORRECT
    return replace(run, wrong=run.wrong + 1), Outcome.WRONG


def skip_task(run: Run, now: datetime) -> tuple[Run, Outcome]:
    if run.status != Status.RUNNING:
        return run, Outcome.IGNORED
    if is_time_up(run, now):
        return replace(run, status=Status.COMPLETED), Outcome.TIME_UP
    return replace(run, skipped=run.skipped + 1), Outcome.SKIPPED


def abort_run(run: Run, now: datetime) -> Run:
    """Abort a running run. One that already reached its end counts as completed."""
    if run.status != Status.RUNNING:
        return run
    status = Status.COMPLETED if is_time_up(run, now) else Status.ABORTED
    return replace(run, status=status)


def finish_if_expired(run: Run, now: datetime) -> Run:
    if run.status == Status.RUNNING and is_time_up(run, now):
        return replace(run, status=Status.COMPLETED)
    return run


def finished_at(run: Run) -> datetime:
    """The end of the run's 60 seconds, however late the app noticed it."""
    return run.started_at + _TIME_LIMIT


def accuracy(correct: int, wrong: int, skipped: int) -> float | None:
    """correct / (correct + wrong + skipped), or None without any attempts."""
    attempts = correct + wrong + skipped
    if attempts == 0:
        return None
    return correct / attempts


def highscores(saved_runs: Iterable[SavedRun]) -> dict[tuple[str, str], int]:
    """The best score per (test type, level), calculated from saved runs (MB R6)."""
    best: dict[tuple[str, str], int] = {}
    for run in saved_runs:
        key = (run.test_type, run.level)
        best[key] = max(best.get(key, run.correct), run.correct)
    return best


def is_new_highscore(previous: int | None, score: int) -> bool:
    """A tie is not new, and neither is a first run that scores 0."""
    return score > (previous or 0)
