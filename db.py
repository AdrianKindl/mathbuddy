"""Storage of completed runs, and the database connection for every storage module.

Each call opens and closes its own connection, because Streamlit may run the
script on a different thread each time and SQLite connections stay on one thread.

Locally the data lives in a SQLite file. When MATHBUDDY_DATABASE_URL is set,
the same SQL runs on an online Postgres database instead (spec 011).
"""

import os
import re
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from leaderboard import Entry
from runs import SavedRun

_DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "mathbuddy.db"
DATABASE_URL_SETTING = "MATHBUDDY_DATABASE_URL"

_INSERT_OR_IGNORE = re.compile(r"^\s*INSERT\s+OR\s+IGNORE\s+INTO\s+", re.IGNORECASE)


def db_path() -> Path:
    return Path(os.environ.get("MATHBUDDY_DB") or _DEFAULT_PATH)


def database_url() -> str | None:
    """The online database, or None for the local SQLite file."""
    return os.environ.get(DATABASE_URL_SETTING) or None


def use_database_url_from(secrets: Mapping) -> None:
    """Take the online database from the app's secrets, unless the setting already exists.

    An existing setting always wins, even an empty one. Note: when Streamlit
    reads a secrets file it copies its keys into the environment itself, so in
    the running app the setting from secrets.toml is already there. To run the
    app locally without the online database, start it with an empty secrets
    file: `uv run streamlit run app.py --secrets.files no-secrets.toml`.
    The tests do the same in tests/conftest.py.
    """
    if DATABASE_URL_SETTING in os.environ:
        return
    url = secrets.get(DATABASE_URL_SETTING)
    if url:
        os.environ[DATABASE_URL_SETTING] = url


def to_postgres(sql: str) -> str:
    """Translate the SQLite SQL used by the storage modules into Postgres SQL."""
    translated = sql.replace("%", "%%").replace("?", "%s")
    if _INSERT_OR_IGNORE.match(translated):
        translated = _INSERT_OR_IGNORE.sub("INSERT INTO ", translated, count=1)
        translated = translated.rstrip() + " ON CONFLICT DO NOTHING"
    return translated


class _PostgresConnection:
    """Gives a Postgres connection the same small interface as sqlite3.

    `with connection:` commits on success and rolls back on an error,
    `closing(connection)` closes it, and `execute` accepts SQLite SQL.
    """

    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql: str, parameters=()):
        return self._connection.execute(to_postgres(sql), tuple(parameters))

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        if error_type is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        return False

    def close(self) -> None:
        self._connection.close()


def _connect_postgres(url: str):
    import psycopg  # only needed online

    return psycopg.connect(url)


def connect():
    url = database_url()
    if url:
        return _PostgresConnection(_connect_postgres(url))
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


def leaderboard_entries(test_type: str, level: str) -> list[Entry]:
    """One entry per owned run of this test type and level (MB R10, spec 013).

    Read-only: runs, their owners (run_owners) and the usernames (users) are
    already stored, so nothing new is saved. Runs without an owner are left out
    by the join. Only the username is read, never the email address.
    """
    with closing(connect()) as connection:
        rows = connection.execute(
            "SELECT run_owners.user_id, users.username, runs.correct, runs.finished_at "
            "FROM runs "
            "JOIN run_owners ON run_owners.run_id = runs.id "
            "JOIN users ON users.id = run_owners.user_id "
            "WHERE runs.test_type = ? AND runs.level = ? "
            "ORDER BY runs.finished_at, runs.id",
            (test_type, level),
        ).fetchall()
    return [
        Entry(user_id=row[0], username=row[1], value=row[2],
              achieved_at=datetime.fromisoformat(row[3]))
        for row in rows
    ]  # fmt: skip
