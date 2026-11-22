"""Leaderboard entries against a real Postgres database (spec 013).

Skipped unless MATHBUDDY_TEST_DATABASE_URL is set, like tests/test_postgres.py.
Point it to a separate Neon branch (for example `test`), never to `production`:
every test starts by deleting all Mathbuddy tables.
"""

import os
from contextlib import closing
from datetime import datetime, timedelta, timezone

import pytest

import accounts_db
import db
from accounts import User
from leaderboard import Entry, build

TEST_URL = os.environ.get("MATHBUDDY_TEST_DATABASE_URL")
TABLES = ["runs", "users", "run_owners", "trainer_sessions", "practice_rounds", "textbook_rounds"]
MONDAY = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)

pytestmark = pytest.mark.skipif(not TEST_URL, reason="MATHBUDDY_TEST_DATABASE_URL is not set")


@pytest.fixture(autouse=True)
def empty_postgres(monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DATABASE_URL", TEST_URL)
    with closing(db.connect()) as connection, connection:
        for table in TABLES:
            connection.execute(f"DROP TABLE IF EXISTS {table}")
    db.init_db()
    accounts_db.init_db()


def test_leaderboard_entries_work_on_postgres():
    for user_id, name in (("u1", "Adrian"), ("u2", "mia")):
        accounts_db.create_user(
            User(user_id, name, f"{name.lower()}@example.com", "pbkdf2_sha256$1$00$00", MONDAY)
        )
    db.save_run("r1", "Multiplication", "Easy", MONDAY + timedelta(days=1), 18, 0, 0)
    db.save_run("r2", "Multiplication", "Easy", MONDAY, 18, 0, 0)
    db.save_run("r3", "Multiplication", "Medium", MONDAY, 40, 0, 0)
    db.save_run("old", "Multiplication", "Easy", MONDAY, 99, 0, 0)  # no owner
    accounts_db.assign_run("r1", "u1")
    accounts_db.assign_run("r2", "u2")
    accounts_db.assign_run("r3", "u1")

    entries = db.leaderboard_entries("Multiplication", "Easy")
    assert sorted(entries, key=lambda e: e.user_id) == [
        Entry("u1", "Adrian", 18, MONDAY + timedelta(days=1)),
        Entry("u2", "mia", 18, MONDAY),
    ]
    assert [row.username for row in build(entries).top] == ["mia", "Adrian"]
