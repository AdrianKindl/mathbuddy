"""Storage of accounts and run owners (spec 011)."""

from datetime import datetime, timezone

import pytest

import accounts_db
import db
from accounts import User
from runs import highscores

CREATED = datetime(2026, 11, 22, 10, 0, 0, tzinfo=timezone.utc)
FINISHED = datetime(2026, 11, 22, 12, 1, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test uses its own file, so data/mathbuddy.db is never touched."""
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    monkeypatch.delenv("MATHBUDDY_DATABASE_URL", raising=False)
    db.init_db()
    accounts_db.init_db()


def user(user_id="u1", username="adrian", email="adrian@example.com"):
    return User(
        id=user_id,
        username=username,
        email=email,
        password_hash="pbkdf2_sha256$1$00$00",
        created_at=CREATED,
    )


def save_run(run_id, correct, owner=None, level="Easy"):
    db.save_run(run_id, "Multiplication", level, FINISHED, correct, 0, 0)
    if owner is not None:
        accounts_db.assign_run(run_id, owner)


# --- Users ---


def test_no_user_at_first():
    assert accounts_db.find_user("adrian") is None
    assert not accounts_db.username_taken("adrian")
    assert not accounts_db.email_taken("adrian@example.com")


def test_created_user_is_read_back_with_all_fields():
    accounts_db.create_user(user())
    assert accounts_db.find_user("adrian") == user()


def test_created_at_is_read_back_in_utc():
    accounts_db.create_user(user())
    assert accounts_db.find_user("adrian").created_at == CREATED


def test_user_is_found_in_any_upper_or_lower_case():
    accounts_db.create_user(user())
    assert accounts_db.find_user("ADRIAN") == user()
    assert accounts_db.find_user("Adrian") == user()


def test_username_keeps_its_original_spelling():
    accounts_db.create_user(user(username="Adrian"))
    assert accounts_db.find_user("adrian").username == "Adrian"


def test_username_is_taken_in_any_upper_or_lower_case():
    accounts_db.create_user(user())
    assert accounts_db.username_taken("Adrian")


def test_email_is_taken_in_any_upper_or_lower_case():
    accounts_db.create_user(user())
    assert accounts_db.email_taken("ADRIAN@example.com")


def test_email_is_stored_in_lower_case():
    accounts_db.create_user(user(email="Adrian@Example.com"))
    assert accounts_db.find_user("adrian").email == "adrian@example.com"


def test_second_account_with_the_same_username_is_refused():
    accounts_db.create_user(user())
    with pytest.raises(ValueError):
        accounts_db.create_user(user("u2", "Adrian", "other@example.com"))
    assert accounts_db.find_user("adrian").id == "u1"


def test_second_account_with_the_same_email_is_refused():
    accounts_db.create_user(user())
    with pytest.raises(ValueError):
        accounts_db.create_user(user("u2", "mia", "ADRIAN@example.com"))
    assert accounts_db.find_user("mia") is None


def test_several_users_are_all_kept():
    accounts_db.create_user(user())
    accounts_db.create_user(user("u2", "mia", "mia@example.com"))
    assert accounts_db.find_user("adrian").id == "u1"
    assert accounts_db.find_user("mia").id == "u2"


# --- Run owners ---


def test_runs_table_is_unchanged():
    """Owners live in their own table, so the runs table of spec 001 stays as it is."""
    save_run("r1", 12, owner="u1")
    assert [run.id for run in db.list_runs()] == ["r1"]


def test_user_sees_only_their_own_runs():
    save_run("a", 15, owner="u1")
    save_run("b", 18, owner="u2")
    assert [run.id for run in accounts_db.list_runs_for("u1")] == ["a"]
    assert [run.id for run in accounts_db.list_runs_for("u2")] == ["b"]


def test_runs_without_owner_are_shown_to_nobody():
    save_run("old", 40)
    save_run("mine", 10, owner="u1")
    assert [run.id for run in accounts_db.list_runs_for("u1")] == ["mine"]


def test_highscore_of_another_user_does_not_count():
    save_run("a", 15, owner="u1")
    save_run("b", 30, owner="u2")
    assert highscores(accounts_db.list_runs_for("u1")) == {("Multiplication", "Easy"): 15}


def test_user_without_runs_has_no_highscores():
    save_run("a", 15, owner="u1")
    assert accounts_db.list_runs_for("u2") == []


def test_assigning_the_same_run_twice_keeps_the_first_owner():
    save_run("a", 15, owner="u1")
    accounts_db.assign_run("a", "u2")
    assert [run.id for run in accounts_db.list_runs_for("u1")] == ["a"]
    assert accounts_db.list_runs_for("u2") == []


def test_owned_runs_are_read_back_with_all_fields():
    save_run("a", 15, owner="u1")
    assert accounts_db.list_runs_for("u1") == db.list_runs()


def test_init_db_twice_keeps_users_and_owners():
    accounts_db.create_user(user())
    save_run("a", 15, owner="u1")
    accounts_db.init_db()
    assert accounts_db.find_user("adrian") == user()
    assert len(accounts_db.list_runs_for("u1")) == 1
