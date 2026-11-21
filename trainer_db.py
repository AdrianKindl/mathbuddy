"""SQLite storage of finished trainer sessions.

Uses the same database file and connection handling as db.py, but its own
table, so the storage of test runs stays untouched.
"""

from contextlib import closing
from datetime import datetime, timezone

import db
from trainer import SavedSession, Session, Status, levels_text, summarize


def init_db() -> None:
    with closing(db.connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trainer_sessions (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                levels TEXT NOT NULL,
                mode TEXT NOT NULL,
                limit_value INTEGER NOT NULL,
                finished_at TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                correct INTEGER NOT NULL,
                wrong INTEGER NOT NULL,
                skipped INTEGER NOT NULL
            )
            """
        )


def save_session(session_id: str, session: Session) -> None:
    """Save a finished session. Saving the same id again changes nothing.

    A running or aborted session is refused, so it can never reach the history.
    """
    if session.status != Status.FINISHED or session.ended_at is None:
        raise ValueError("Only a finished session can be saved")

    summary = summarize(session)
    settings = session.settings
    with closing(db.connect()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO trainer_sessions "
            "(id, category, name, levels, mode, limit_value, finished_at, "
            "duration_seconds, correct, wrong, skipped) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                settings.category,
                settings.name,
                levels_text(settings),
                str(settings.mode),
                settings.limit,
                session.ended_at.astimezone(timezone.utc).isoformat(),
                summary.duration_seconds,
                summary.correct,
                summary.wrong,
                summary.skipped,
            ),
        )


def list_sessions(limit: int | None = None) -> list[SavedSession]:
    """Finished sessions, newest first. `limit` keeps only the newest ones."""
    query = (
        "SELECT id, category, name, levels, mode, limit_value, finished_at, "
        "duration_seconds, correct, wrong, skipped "
        "FROM trainer_sessions ORDER BY finished_at DESC, id"
    )
    parameters: tuple[int, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        parameters = (limit,)

    with closing(db.connect()) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [
        SavedSession(
            id=row[0],
            category=row[1],
            name=row[2],
            levels=row[3],
            mode=row[4],
            limit=row[5],
            finished_at=datetime.fromisoformat(row[6]),
            duration_seconds=row[7],
            correct=row[8],
            wrong=row[9],
            skipped=row[10],
        )
        for row in rows
    ]
