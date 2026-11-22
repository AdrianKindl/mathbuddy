"""Storage against a real Postgres database (spec 011).

Skipped unless MATHBUDDY_TEST_DATABASE_URL is set. Point it to a separate
Neon branch (for example `test`), never to `production`: every test starts by
deleting all Mathbuddy tables.
"""

import os
from contextlib import closing
from datetime import datetime, timezone

import pytest

import accounts_db
import db
from accounts import User
from runs import SavedRun

TEST_URL = os.environ.get("MATHBUDDY_TEST_DATABASE_URL")
TABLES = ["runs", "users", "run_owners", "trainer_sessions", "practice_rounds", "textbook_rounds"]
FINISHED = datetime(2026, 11, 22, 12, 1, 0, tzinfo=timezone.utc)

pytestmark = pytest.mark.skipif(not TEST_URL, reason="MATHBUDDY_TEST_DATABASE_URL is not set")


@pytest.fixture(autouse=True)
def empty_postgres(monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DATABASE_URL", TEST_URL)
    with closing(db.connect()) as connection, connection:
        for table in TABLES:
            connection.execute(f"DROP TABLE IF EXISTS {table}")
    db.init_db()
    accounts_db.init_db()


def test_run_is_saved_and_read_back():
    db.save_run("r1", "Multiplication", "Easy", FINISHED, 12, 3, 2)
    assert db.list_runs() == [
        SavedRun("r1", "Multiplication", "Easy", FINISHED, 12, 3, 2)
    ]


def test_saving_the_same_run_twice_keeps_the_first_one():
    db.save_run("same", "Multiplication", "Easy", FINISHED, 12, 0, 0)
    db.save_run("same", "Multiplication", "Easy", FINISHED, 99, 0, 0)
    assert [run.correct for run in db.list_runs()] == [12]


def test_accounts_and_owners_work():
    accounts_db.create_user(
        User("u1", "Adrian", "adrian@example.com", "pbkdf2_sha256$1$00$00", FINISHED)
    )
    assert accounts_db.find_user("ADRIAN").id == "u1"
    assert accounts_db.email_taken("Adrian@Example.com")
    with pytest.raises(ValueError):
        accounts_db.create_user(User("u2", "adrian", "x@example.com", "h", FINISHED))

    db.save_run("r1", "Multiplication", "Easy", FINISHED, 12, 0, 0)
    accounts_db.assign_run("r1", "u1")
    accounts_db.assign_run("r1", "u2")
    assert [run.id for run in accounts_db.list_runs_for("u1")] == ["r1"]
    assert accounts_db.list_runs_for("u2") == []


def test_tables_of_the_other_modules_can_be_created():
    import knowledge_db
    import textbook_db
    import trainer_db

    trainer_db.init_db()
    knowledge_db.init_db()
    textbook_db.init_db()
    assert trainer_db.list_sessions() == []
    assert knowledge_db.list_rounds() == []
    assert textbook_db.list_rounds() == []
