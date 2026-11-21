"""Trainer session rules: settings, modes, time limits and results (spec 002).

Like runs.py, this module never reads the clock. The current time is passed in
as `now`, so tests can use fixed times.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from runs import accuracy
from trainer_tasks import (
    NATURAL,
    NUMBER_TYPES,
    SPECIAL,
    Check,
    Topic,
    TrainerTask,
    check_answer,
    format_answer,
    is_valid_topic,
)

OPERATIONS_CATEGORY = "Operations"
NUMBER_TYPES_CATEGORY = "Number types"
SPECIAL_CATEGORY = "Special trainings"
CATEGORIES = (OPERATIONS_CATEGORY, NUMBER_TYPES_CATEGORY, SPECIAL_CATEGORY)

COUNTDOWN_SECONDS = 3


# StrEnum, and always compared with == rather than `is`, for the same reason
# as in runs.py: Streamlit re-imports a module when its source changes.
class Mode(StrEnum):
    TASK_COUNT = "Task count"
    TOTAL_TIME = "Total time"
    TIME_PER_TASK = "Time per task"


# Lowest and highest limit per mode, inclusive: tasks for TASK_COUNT, seconds otherwise.
LIMITS = {
    Mode.TASK_COUNT: (5, 100),
    Mode.TOTAL_TIME: (30, 900),
    Mode.TIME_PER_TASK: (1, 60),
}


class Status(StrEnum):
    RUNNING = "running"
    FINISHED = "finished"
    ABORTED = "aborted"


class EndReason(StrEnum):
    ALL_TASKS_DONE = "all_tasks_done"
    TIME_UP = "time_up"  # the total time ran out
    TOO_SLOW = "too_slow"  # one task took longer than the time per task
    ABORTED = "aborted"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    SKIPPED = "skipped"
    IGNORED = "ignored"
    TIME_UP = "time_up"


class SettingsError(ValueError):
    """The chosen settings are not allowed. The message can be shown to the user."""


@dataclass(frozen=True)
class Settings:
    category: str  # one of CATEGORIES
    name: str  # what was picked in the category, e.g. "Percentage" or "Decimals"
    topics: tuple[Topic, ...]
    mode: Mode
    limit: int  # tasks for TASK_COUNT, seconds otherwise


@dataclass(frozen=True)
class Attempt:
    """One answered or skipped task, kept for the review after the session."""

    text: str
    given: str  # what the user typed, empty for a skip
    answer: str  # the correct answer as it is shown
    solution: str
    outcome: Outcome  # CORRECT, WRONG or SKIPPED
    seconds: float


@dataclass(frozen=True)
class Session:
    settings: Settings
    started_at: datetime
    task_started_at: datetime
    attempts: tuple[Attempt, ...] = ()
    status: Status = Status.RUNNING
    end_reason: EndReason | None = None
    ended_at: datetime | None = None

    # The totals are counted from the attempts and never stored separately.
    @property
    def correct(self) -> int:
        return self._count(Outcome.CORRECT)

    @property
    def wrong(self) -> int:
        return self._count(Outcome.WRONG)

    @property
    def skipped(self) -> int:
        return self._count(Outcome.SKIPPED)

    def _count(self, outcome: Outcome) -> int:
        return sum(1 for attempt in self.attempts if attempt.outcome == outcome)


@dataclass(frozen=True)
class Summary:
    correct: int
    wrong: int
    skipped: int
    accuracy: float | None
    duration_seconds: float
    average_seconds: float | None  # per answered or skipped task


@dataclass(frozen=True)
class SavedSession:
    id: str
    category: str
    name: str
    levels: str
    mode: str
    limit: int
    finished_at: datetime
    duration_seconds: float
    correct: int
    wrong: int
    skipped: int


# --- Settings ---


def make_settings(
    category: str, name: str, topics: Sequence[Topic], mode: str, limit: int
) -> Settings:
    """Check the user's choices. Raises SettingsError and starts nothing if one is not allowed."""
    if category not in CATEGORIES:
        raise SettingsError(f"Unknown category: {category}")
    topics = tuple(topics)
    if not topics:
        raise SettingsError("Select at least one operation.")
    if not all(is_valid_topic(topic) for topic in topics):
        raise SettingsError("Unknown operation, training or level.")
    if len({(topic.group, topic.name) for topic in topics}) != len(topics):
        raise SettingsError("Each operation can only be selected once.")

    # The three categories differ in what may be combined (product brief, R2 and R3).
    one_topic = len(topics) == 1 and topics[0].name == name
    if category == OPERATIONS_CATEGORY and not (one_topic and topics[0].group == NATURAL):
        raise SettingsError("Operations trains exactly one operation.")
    if category == SPECIAL_CATEGORY and not (one_topic and topics[0].group == SPECIAL):
        raise SettingsError("Special trainings trains exactly one training.")
    if category == NUMBER_TYPES_CATEGORY and not (
        name in NUMBER_TYPES and all(topic.group == name for topic in topics)
    ):
        raise SettingsError("All operations must belong to the chosen number type.")

    try:
        mode = Mode(mode)
    except ValueError:
        raise SettingsError(f"Unknown mode: {mode}") from None
    low, high = LIMITS[mode]
    # `type(...) is int` also rejects True and 10.0, which would pass a plain comparison.
    if type(limit) is not int or not low <= limit <= high:
        raise SettingsError(f"{mode}: choose a whole number from {low} to {high}.")

    return Settings(category, name, topics, mode, limit)


def levels_text(settings: Settings) -> str:
    """'Easy' for one topic, 'Addition Easy, Division Hard' for several."""
    if len(settings.topics) == 1:
        return settings.topics[0].level
    return ", ".join(f"{topic.name} {topic.level}" for topic in settings.topics)


# --- Time ---


def start_session(settings: Settings, now: datetime) -> Session:
    """Start a session at `now`, which is after the countdown."""
    return Session(settings, started_at=now, task_started_at=now)


def _deadline(session: Session) -> datetime | None:
    limit = timedelta(seconds=session.settings.limit)
    if session.settings.mode == Mode.TOTAL_TIME:
        return session.started_at + limit
    if session.settings.mode == Mode.TIME_PER_TASK:
        return session.task_started_at + limit
    return None  # a task count never runs out of time


def is_time_up(session: Session, now: datetime) -> bool:
    deadline = _deadline(session)
    return deadline is not None and now >= deadline


def remaining_seconds(session: Session, now: datetime) -> float | None:
    """Seconds left in total or for the current task. None if the mode has no time limit."""
    deadline = _deadline(session)
    if deadline is None:
        return None
    return max(0.0, (deadline - now).total_seconds())


def elapsed_seconds(session: Session, now: datetime) -> float:
    end = session.ended_at or now
    return max(0.0, (end - session.started_at).total_seconds())


def _expire(session: Session) -> Session:
    """End the session at its deadline, however late the app noticed it."""
    too_slow = session.settings.mode == Mode.TIME_PER_TASK
    return replace(
        session,
        status=Status.FINISHED,
        end_reason=EndReason.TOO_SLOW if too_slow else EndReason.TIME_UP,
        ended_at=_deadline(session),
    )


# --- Answers ---


def _record(
    session: Session, task: TrainerTask, given: str, outcome: Outcome, now: datetime
) -> Session:
    attempt = Attempt(
        text=task.text,
        given=given,
        answer=format_answer(task),
        solution=task.solution,
        outcome=outcome,
        seconds=(now - session.task_started_at).total_seconds(),
    )
    session = replace(session, attempts=(*session.attempts, attempt), task_started_at=now)

    all_done = (
        session.settings.mode == Mode.TASK_COUNT
        and len(session.attempts) >= session.settings.limit
    )
    if all_done:
        session = replace(
            session, status=Status.FINISHED, end_reason=EndReason.ALL_TASKS_DONE, ended_at=now
        )
    return session


def submit_answer(
    session: Session, task: TrainerTask, raw: str, now: datetime
) -> tuple[Session, Outcome]:
    if session.status != Status.RUNNING:
        return session, Outcome.IGNORED
    if is_time_up(session, now):
        return _expire(session), Outcome.TIME_UP

    check = check_answer(task, raw)
    if check == Check.INVALID:  # MB R3: not evaluated, and the clock keeps running
        return session, Outcome.IGNORED
    outcome = Outcome.CORRECT if check == Check.CORRECT else Outcome.WRONG
    return _record(session, task, raw.strip(), outcome, now), outcome


def skip_task(session: Session, task: TrainerTask, now: datetime) -> tuple[Session, Outcome]:
    if session.status != Status.RUNNING:
        return session, Outcome.IGNORED
    if is_time_up(session, now):
        return _expire(session), Outcome.TIME_UP
    return _record(session, task, "", Outcome.SKIPPED, now), Outcome.SKIPPED


def abort_session(session: Session, now: datetime) -> Session:
    """Abort a running session. One whose time was already up counts as finished."""
    if session.status != Status.RUNNING:
        return session
    if is_time_up(session, now):
        return _expire(session)
    return replace(session, status=Status.ABORTED, end_reason=EndReason.ABORTED, ended_at=now)


def finish_if_expired(session: Session, now: datetime) -> Session:
    if session.status == Status.RUNNING and is_time_up(session, now):
        return _expire(session)
    return session


# --- Result ---


def summarize(session: Session) -> Summary:
    seconds = [attempt.seconds for attempt in session.attempts]
    return Summary(
        correct=session.correct,
        wrong=session.wrong,
        skipped=session.skipped,
        accuracy=accuracy(session.correct, session.wrong, session.skipped),
        duration_seconds=elapsed_seconds(session, session.ended_at or session.started_at),
        average_seconds=sum(seconds) / len(seconds) if seconds else None,
    )


def format_duration(seconds: float) -> str:
    """75.4 -> '1:15'."""
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}:{rest:02d}"


def limit_text(mode: str, limit: int) -> str:
    """The mode and its limit in a few words, e.g. '10 tasks'."""
    if mode == Mode.TASK_COUNT:
        return f"{limit} tasks"
    if mode == Mode.TOTAL_TIME:
        return f"{format_duration(limit)} min in total"
    return f"{limit} s per task"
