"""SQLite storage of completed Knowledge practice rounds.

Uses the same database file and connection handling as db.py, but its own
table, so the storage of test runs stays untouched.
"""

from contextlib import closing
from datetime import datetime, timezone

import db
from knowledge import Round, SavedRound, Status
from stats import Kind


def init_db() -> None:
    with closing(db.connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS practice_rounds (
                id TEXT PRIMARY KEY,
                trick_id TEXT NOT NULL,
                level TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                correct INTEGER NOT NULL
            )
            """
        )


def save_round(round_id: str, practice_round: Round, finished_at: datetime) -> None:
    """Save a completed round. Saving the same id again changes nothing.

    A round that is not completed is refused, so leaving early can never save (K R6).
    """
    if practice_round.status != Status.COMPLETED:
        raise ValueError("Only a completed round can be saved")

    with closing(db.connect()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO practice_rounds (id, trick_id, level, finished_at, correct) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                round_id,
                practice_round.trick_id,
                practice_round.level,
                finished_at.astimezone(timezone.utc).isoformat(),
                practice_round.correct,
            ),
        )


COLUMNS = "t.id, t.trick_id, t.level, t.finished_at, t.correct"


def list_rounds() -> list[SavedRound]:
    """Completed rounds of all players, oldest first."""
    return _read(f"SELECT {COLUMNS} FROM practice_rounds t", ())


def list_rounds_for(user_id: str) -> list[SavedRound]:
    """Completed rounds of one player, oldest first (spec 014).

    The owner is in `activity_owners` (spec 012); rounds without an owner
    belong to nobody.
    """
    return _read(
        f"SELECT {COLUMNS} FROM practice_rounds t "
        "JOIN activity_owners o ON o.activity_id = t.id AND o.kind = ? "
        "WHERE o.user_id = ?",
        (Kind.TRICKS.value, user_id),
    )


def _read(query: str, parameters: tuple) -> list[SavedRound]:
    with closing(db.connect()) as connection:
        rows = connection.execute(query + " ORDER BY t.finished_at, t.id", parameters).fetchall()
    return [
        SavedRound(
            id=row[0],
            trick_id=row[1],
            level=row[2],
            finished_at=datetime.fromisoformat(row[3]),
            correct=row[4],
        )
        for row in rows
    ]
