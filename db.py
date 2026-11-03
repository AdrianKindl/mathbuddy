"""SQLite storage of completed runs.

Each call opens and closes its own connection, because Streamlit may run the
script on a different thread each time and SQLite connections stay on one thread.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from runs import SavedRun

_DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "mathbuddy.db"


def db_path() -> Path:
    return Path(os.environ.get("MATHBUDDY_DB") or _DEFAULT_PATH)


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def init_db() -> None:
    with closing(connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                test_type TEXT NOT NULL,
                level TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                correct INTEGER NOT NULL,
                wrong INTEGER NOT NULL,
                skipped INTEGER NOT NULL
            )
            """
        )


def save_run(
    run_id: str,
    test_type: str,
    level: str,
    finished_at: datetime,
    correct: int,
    wrong: int,
    skipped: int,
) -> None:
    """Save a completed run. Saving the same id again changes nothing."""
    with closing(connect()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO runs "
            "(id, test_type, level, finished_at, correct, wrong, skipped) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                test_type,
                level,
                finished_at.astimezone(timezone.utc).isoformat(),
                correct,
                wrong,
                skipped,
            ),
        )


def list_runs() -> list[SavedRun]:
    with closing(connect()) as connection:
        rows = connection.execute(
            "SELECT id, test_type, level, finished_at, correct, wrong, skipped "
            "FROM runs ORDER BY finished_at, id"
        ).fetchall()
    return [
        SavedRun(
            id=row[0],
            test_type=row[1],
            level=row[2],
            finished_at=datetime.fromisoformat(row[3]),
            correct=row[4],
            wrong=row[5],
            skipped=row[6],
        )
        for row in rows
    ]
