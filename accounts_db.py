"""Storage of accounts and run owners (spec 011).

Uses the same database and connection handling as db.py, but its own tables,
so the runs table of spec 001 stays untouched. Works on SQLite and Postgres.
"""

from contextlib import closing
from datetime import datetime, timezone

import db
from accounts import User, normalize_email, username_key
from runs import SavedRun


def init_db() -> None:
    with closing(db.connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                username_key TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS run_owners (
                run_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL
            )
            """
        )


def username_taken(username: str) -> bool:
    with closing(db.connect()) as connection:
        row = connection.execute(
            "SELECT 1 FROM users WHERE username_key = ?", (username_key(username),)
        ).fetchall()
    return bool(row)


def email_taken(email: str) -> bool:
    with closing(db.connect()) as connection:
        row = connection.execute(
            "SELECT 1 FROM users WHERE email = ?", (normalize_email(email),)
        ).fetchall()
    return bool(row)


def create_user(user: User) -> None:
    """Save a new account. A taken username or email is refused with ValueError."""
    if username_taken(user.username):
        raise ValueError("Username is already taken")
    if email_taken(user.email):
        raise ValueError("Email already belongs to an account")
    with closing(db.connect()) as connection, connection:
        connection.execute(
            "INSERT INTO users (id, username, username_key, email, password_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                user.id,
                user.username,
                username_key(user.username),
                normalize_email(user.email),
                user.password_hash,
                user.created_at.astimezone(timezone.utc).isoformat(),
            ),
        )


def find_user(username: str) -> User | None:
    with closing(db.connect()) as connection:
        rows = connection.execute(
            "SELECT id, username, email, password_hash, created_at "
            "FROM users WHERE username_key = ?",
            (username_key(username),),
        ).fetchall()
    if not rows:
        return None
    row = rows[0]
    return User(
        id=row[0],
        username=row[1],
        email=row[2],
        password_hash=row[3],
        created_at=datetime.fromisoformat(row[4]),
    )


def assign_run(run_id: str, user_id: str) -> None:
    """Record the owner of a saved run. The first owner is kept."""
    with closing(db.connect()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO run_owners (run_id, user_id) VALUES (?, ?)",
            (run_id, user_id),
        )


def list_runs_for(user_id: str) -> list[SavedRun]:
    """The completed runs of one user. Runs without an owner belong to nobody."""
    with closing(db.connect()) as connection:
        rows = connection.execute(
            "SELECT runs.id, runs.test_type, runs.level, runs.finished_at, "
            "runs.correct, runs.wrong, runs.skipped "
            "FROM runs JOIN run_owners ON run_owners.run_id = runs.id "
            "WHERE run_owners.user_id = ? "
            "ORDER BY runs.finished_at, runs.id",
            (user_id,),
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
