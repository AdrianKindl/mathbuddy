"""Reading leaderboard entries through db.py, on SQLite (MB R10, A13).

The same function runs on Postgres in tests/test_postgres_leaderboard.py.
"""

from contextlib import closing
from datetime import datetime, timedelta, timezone

import pytest

import accounts_db
import db
from accounts import User
from leaderboard import Entry

MONDAY = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
CREATED = datetime(2026, 11, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    db.init_db()
    accounts_db.init_db()


def add_user(user_id, username):
    accounts_db.create_user(
        User(user_id, username, f"{username.lower()}@example.com", "pbkdf2_sha256$1$00$00", CREATED)
    )


def add_run(run_id, correct, owner=None, test_type="Multiplication", level="Easy", when=MONDAY):
    db.save_run(run_id, test_type, level, when, correct, 0, 0)
    if owner:
        accounts_db.assign_run(run_id, owner)


def tables():
    with closing(db.connect()) as connection:
        return {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}  # fmt: skip


def test_nothing_at_first():
    assert db.leaderboard_entries("Multiplication", "Easy") == []


def test_every_owned_run_is_one_entry_with_username_score_and_time():
    add_user("u1", "Adrian")
    add_run("r1", 12, "u1", when=MONDAY)
    add_run("r2", 18, "u1", when=MONDAY + timedelta(days=1))
    assert sorted(db.leaderboard_entries("Multiplication", "Easy"), key=lambda e: e.value) == [
        Entry(user_id="u1", username="Adrian", value=12, achieved_at=MONDAY),
        Entry(user_id="u1", username="Adrian", value=18, achieved_at=MONDAY + timedelta(days=1)),
    ]


def test_times_are_read_back_in_utc():
    add_user("u1", "Adrian")
    add_run("r1", 12, "u1")
    assert db.leaderboard_entries("Multiplication", "Easy")[0].achieved_at.utcoffset() == timedelta(0)


def test_only_the_asked_test_type_and_level():
    add_user("u1", "Adrian")
    add_run("easy", 12, "u1", level="Easy")
    add_run("medium", 30, "u1", level="Medium")
    add_run("addition", 40, "u1", test_type="Addition", level="Easy")
    assert [e.value for e in db.leaderboard_entries("Multiplication", "Easy")] == [12]
    assert [e.value for e in db.leaderboard_entries("Multiplication", "Medium")] == [30]
    assert [e.value for e in db.leaderboard_entries("Addition", "Easy")] == [40]


def test_runs_without_an_owner_are_left_out():
    add_user("u1", "Adrian")
    add_run("owned", 12, "u1")
    add_run("old", 99)  # saved before accounts existed
    assert [e.value for e in db.leaderboard_entries("Multiplication", "Easy")] == [12]


def test_runs_of_several_users():
    add_user("u1", "Adrian")
    add_user("u2", "mia")
    add_run("r1", 12, "u1")
    add_run("r2", 15, "u2")
    assert {(e.username, e.value) for e in db.leaderboard_entries("Multiplication", "Easy")} == {
        ("Adrian", 12), ("mia", 15)}  # fmt: skip


def test_no_email_is_read():
    add_user("u1", "Adrian")
    add_run("r1", 12, "u1")
    entries = db.leaderboard_entries("Multiplication", "Easy")
    assert "@" not in repr(entries)


def test_no_new_table_is_needed():
    before = tables()
    add_user("u1", "Adrian")
    add_run("r1", 12, "u1")
    db.leaderboard_entries("Multiplication", "Easy")
    assert tables() == before == {"runs", "users", "run_owners"}
