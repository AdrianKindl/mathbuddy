"""SQLite storage of completed Knowledge practice rounds.

Uses the same database file and connection handling as db.py, but its own
table, so the storage of test runs stays untouched.
"""

from contextlib import closing
from datetime import datetime, timezone

import db
from knowledge import Round, SavedRound, Status


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


def list_rounds() -> list[SavedRound]:
    with closing(db.connect()) as connection:
        rows = connection.execute(
            "SELECT id, trick_id, level, finished_at, correct "
            "FROM practice_rounds ORDER BY finished_at, id"
        ).fetchall()
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
