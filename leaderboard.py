"""Leaderboard rules (MB R10, spec 013).

A rule module: no Streamlit, no SQL, no clock. Nothing here is specific to
Tests. It ranks any list of entries (a user, a value, when it was reached), so
game leaderboards can reuse it later, also with "lower is better" for times.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

TOP = 15


class Better(StrEnum):
    HIGHER = "higher"  # scores: more is better (Tests)
    LOWER = "lower"  # for example a fastest time


@dataclass(frozen=True)
class Entry:
    """One result of one user, for example one completed run."""

    user_id: str
    username: str
    value: int | float
    achieved_at: datetime


@dataclass(frozen=True)
class Row:
    rank: int
    user_id: str
    username: str
    value: int | float
    achieved_at: datetime
    is_you: bool


@dataclass(frozen=True)
class Board:
    top: tuple[Row, ...]  # the best `top` users
    own: Row | None  # the signed-in user, only when ranked below the top


def _order(entry: Entry, better: Better) -> tuple:
    """Best value first; equal values: the earlier time; then the username, any case."""
    value = -entry.value if better == Better.HIGHER else entry.value
    return value, entry.achieved_at, entry.username.lower()


def build(
    entries: Iterable[Entry],
    *,
    better: Better = Better.HIGHER,
    top: int = TOP,
    user_id: str | None = None,
) -> Board:
    """Rank users by their best entry, each user once (MB R10)."""
    best: dict[str, Entry] = {}
    for entry in entries:
        current = best.get(entry.user_id)
        if current is None or _order(entry, better) < _order(current, better):
            best[entry.user_id] = entry

    ranked = sorted(best.values(), key=lambda entry: _order(entry, better))
    rows = [
        Row(rank, entry.user_id, entry.username, entry.value, entry.achieved_at,
            is_you=user_id is not None and entry.user_id == user_id)
        for rank, entry in enumerate(ranked, start=1)
    ]  # fmt: skip
    own = next((row for row in rows[top:] if row.is_you), None)
    return Board(top=tuple(rows[:top]), own=own)
