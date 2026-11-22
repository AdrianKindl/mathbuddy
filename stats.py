"""Profile statistics rules (MB R8, spec 012).

A rule module: no Streamlit, no SQL, no clock. The caller passes in the
player's activities, `today` and the time zone that decides calendar days.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, tzinfo
from enum import StrEnum


class Kind(StrEnum):
    TEST = "test"
    TRAINER = "trainer"
    TRICKS = "tricks"
    TEXTBOOK = "textbook"
    GAME = "game"


@dataclass(frozen=True)
class Activity:
    """One completed activity of a player. Games have no tasks."""

    kind: Kind
    finished_at: datetime  # UTC
    correct: int = 0
    not_correct: int = 0  # wrong + skipped

    @property
    def counts_for_tasks(self) -> bool:
        return self.kind != Kind.GAME


def local_day(moment: datetime, zone: tzinfo) -> date:
    """The calendar day of `moment` in the app time zone."""
    return moment.astimezone(zone).date()


def tasks_completed(activities: Iterable[Activity]) -> int:
    """Correctly solved tasks of Tests, Trainer and practice rounds (MB R8)."""
    return sum(a.correct for a in activities if a.counts_for_tasks)


def accuracy(activities: Iterable[Activity]) -> float | None:
    """correct / (correct + wrong + skipped); None without any task (MB R8)."""
    with_tasks = [a for a in activities if a.counts_for_tasks]
    correct = sum(a.correct for a in with_tasks)
    total = correct + sum(a.not_correct for a in with_tasks)
    return correct / total if total else None


def longest_streak(activities: Iterable[Activity], zone: tzinfo) -> int:
    """Most consecutive calendar days with at least one activity (MB R8)."""
    days = sorted({local_day(a.finished_at, zone) for a in activities})
    longest = current = 0
    previous = None
    for day in days:
        current = current + 1 if previous == day - timedelta(days=1) else 1
        longest = max(longest, current)
        previous = day
    return longest


def last_7_days(activities: Iterable[Activity], today: date, zone: tzinfo) -> list[tuple[date, int]]:
    """Activities per day from today - 6 to today, oldest first; 0 without activity."""
    days = [today - timedelta(days=n) for n in range(6, -1, -1)]
    counts = dict.fromkeys(days, 0)
    for activity in activities:
        day = local_day(activity.finished_at, zone)
        if day in counts:
            counts[day] += 1
    return [(day, counts[day]) for day in days]
