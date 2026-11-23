"""Sign in, sign up and sign out screens in app.py (spec 011).

These start without a signed in user (see tests/conftest.py).
"""

import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import accounts_db
import db
from accounts import (
    EMAIL_INVALID,
    EMAIL_TAKEN,
    PASSWORD_TOO_SHORT,
    PASSWORDS_DIFFER,
    SIGN_IN_FAILED,
    USERNAME_TAKEN,
)

APP = Path(__file__).resolve().parent.parent / "app.py"
PASSWORD_HINT = "Use a password you don't use anywhere else."
NO_HIGHSCORE = "–"

pytestmark = pytest.mark.signed_out


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


@pytest.fixture
def fast_sleep(monkeypatch):
    real_sleep = time.sleep
    monkeypatch.setattr(time, "sleep", lambda seconds: real_sleep(min(seconds, 0.01)))


def open_app():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    return at


def sign_up(at, username="adrian", email="adrian@example.com", password="secret123", repeat=None):
    at.text_input(key="signup_username").input(username)
    at.text_input(key="signup_email").input(email)
    at.text_input(key="signup_password").input(password)
    at.text_input(key="signup_repeat").input(password if repeat is None else repeat)
    at.button(key="signup_submit").click().run()
    assert not at.exception
    return at


def sign_in(at, username="adrian", password="secret123"):
    at.text_input(key="signin_username").input(username)
    at.text_input(key="signin_password").input(password)
    at.button(key="signin_submit").click().run()
    assert not at.exception
    return at


def sign_out(at):
    at.button(key="sign_out").click().run()
    assert not at.exception
    return at


def is_signed_in(at):
    return len(at.radio) > 0 and at.radio(key="nav") is not None


def errors(at):
    return [element.value for element in at.error]


def sidebar_text(at):
    return " ".join(element.value for element in at.sidebar.markdown)


def finish_a_run(at, correct):
    """Start a Multiplication Easy test and let its 60 seconds run out."""
    at.button_group(key="test_type").set_value("Multiplication")
    at.button_group(key="level").set_value("Easy")
    at.button(key="start").click().run()
    started = datetime.now(timezone.utc) - timedelta(seconds=61)
    at.session_state["run"] = replace(at.session_state["run"], started_at=started, correct=correct)
    at.run()
    assert not at.exception


def multiplication_easy_highscore(at):
    """The Tests tab's "Your best" for Multiplication Easy (spec 015)."""
    at.button_group(key="test_type").set_value("Multiplication")
    at.button_group(key="level").set_value("Easy")
    at.run()
    assert not at.exception
    return str({metric.label: metric.value for metric in at.metric}["Your best"])


# --- Sign in screen ---


def test_without_a_user_only_the_sign_in_screen_is_shown():
    at = open_app()
    assert not is_signed_in(at)
    assert at.title[0].value == "Mathbuddy"
    assert [tab.label for tab in at.tabs] == ["Sign in", "Create account"]


def test_sign_in_screen_shows_the_password_hint():
    at = open_app()
    assert any(PASSWORD_HINT in caption.value for caption in at.caption)


def test_password_fields_hide_what_is_typed():
    at = open_app()
    for key in ("signin_password", "signup_password", "signup_repeat"):
        assert at.text_input(key=key).proto.type == at.text_input(key=key).proto.PASSWORD


# --- Create account (A7) ---


def test_creating_an_account_signs_the_user_in():
    at = sign_up(open_app())
    assert is_signed_in(at)
    assert "Signed in as adrian" in sidebar_text(at)
    assert accounts_db.find_user("adrian") is not None


def test_new_account_stores_a_hash_not_the_password():
    sign_up(open_app())
    stored = accounts_db.find_user("adrian").password_hash
    assert "secret123" not in stored
    assert stored.startswith("pbkdf2_sha256$")


def test_two_accounts_get_different_salts():
    sign_up(open_app(), "adrian", "adrian@example.com", "samepassword")
    sign_up(open_app(), "mia", "mia@example.com", "samepassword")
    assert accounts_db.find_user("adrian").password_hash != accounts_db.find_user("mia").password_hash


def test_username_in_other_case_is_rejected_and_no_account_is_created():
    sign_up(open_app())
    at = sign_up(open_app(), "Adrian", "other@example.com")
    assert USERNAME_TAKEN in errors(at)
    assert not is_signed_in(at)
    assert accounts_db.find_user("adrian").email == "adrian@example.com"


def test_invalid_email_is_rejected():
    at = sign_up(open_app(), email="adrian@")
    assert EMAIL_INVALID in errors(at)
    assert not is_signed_in(at)
    assert accounts_db.find_user("adrian") is None


def test_used_email_is_rejected_in_any_case():
    sign_up(open_app())
    at = sign_up(open_app(), "mia", "ADRIAN@example.com")
    assert EMAIL_TAKEN in errors(at)
    assert accounts_db.find_user("mia") is None


def test_short_password_is_rejected():
    at = sign_up(open_app(), password="1234567")
    assert PASSWORD_TOO_SHORT in errors(at)
    assert accounts_db.find_user("adrian") is None


def test_different_passwords_are_rejected():
    at = sign_up(open_app(), password="secret123", repeat="secret124")
    assert PASSWORDS_DIFFER in errors(at)
    assert accounts_db.find_user("adrian") is None


# Review of PR #14: only the password errors that actually apply are shown.


def test_short_password_typed_twice_shows_only_the_length_error():
    at = sign_up(open_app(), password="short12", repeat="short12")
    assert errors(at) == [PASSWORD_TOO_SHORT]


def test_long_passwords_that_differ_show_only_the_mismatch_error():
    at = sign_up(open_app(), password="longpassword1", repeat="longpassword2")
    assert errors(at) == [PASSWORDS_DIFFER]


def change_field(at, key, value):
    """Type into a field and leave it (Enter), without clicking Create account."""
    at.text_input(key=key).input(value)
    return at.run()


def test_errors_follow_a_corrected_repeat_without_a_new_click():
    at = sign_up(open_app(), password="short12", repeat="short13")
    assert errors(at) == [PASSWORD_TOO_SHORT, PASSWORDS_DIFFER]
    at = change_field(at, "signup_repeat", "short12")
    assert errors(at) == [PASSWORD_TOO_SHORT]


def test_errors_follow_a_corrected_length_without_a_new_click():
    at = sign_up(open_app(), password="short12", repeat="short13")
    at = change_field(at, "signup_password", "longpassword1")
    at = change_field(at, "signup_repeat", "longpassword2")
    assert errors(at) == [PASSWORDS_DIFFER]


def test_errors_disappear_when_everything_is_corrected_but_no_account_yet():
    at = sign_up(open_app(), password="short12", repeat="short13")
    at = change_field(at, "signup_password", "longpassword1")
    at = change_field(at, "signup_repeat", "longpassword1")
    assert errors(at) == []
    assert not is_signed_in(at)
    assert accounts_db.find_user("adrian") is None


def test_spaces_around_username_and_email_are_ignored():
    at = sign_up(open_app(), " adrian ", " Adrian@Example.com ")
    assert is_signed_in(at)
    assert accounts_db.find_user("adrian").email == "adrian@example.com"


# --- Sign in and sign out ---


def test_sign_out_returns_to_the_sign_in_screen():
    at = sign_out(sign_up(open_app()))
    assert not is_signed_in(at)
    assert "user" not in at.session_state


def test_sign_in_with_the_right_password():
    sign_up(open_app())
    at = sign_in(open_app())
    assert is_signed_in(at)
    assert "Signed in as adrian" in sidebar_text(at)


def test_sign_in_works_in_any_upper_or_lower_case():
    sign_up(open_app(), username="Adrian")
    at = sign_in(open_app(), username="ADRIAN")
    assert is_signed_in(at)
    assert "Signed in as Adrian" in sidebar_text(at)


def test_wrong_password_is_refused():
    sign_up(open_app())
    at = sign_in(open_app(), password="wrongpass")
    assert errors(at) == [SIGN_IN_FAILED]
    assert not is_signed_in(at)


def test_unknown_username_gives_the_same_message():
    at = sign_in(open_app(), username="nobody")
    assert errors(at) == [SIGN_IN_FAILED]
    assert not is_signed_in(at)


# --- Own data only ---


def test_completed_run_belongs_to_the_signed_in_user(fast_sleep):
    at = sign_up(open_app())
    finish_a_run(at, correct=12)
    user = accounts_db.find_user("adrian")
    assert [run.correct for run in accounts_db.list_runs_for(user.id)] == [12]


def test_highscores_of_another_user_are_not_shown(fast_sleep):
    at = sign_up(open_app())
    finish_a_run(at, correct=12)
    sign_out(at)

    at = sign_up(open_app(), "mia", "mia@example.com")
    assert multiplication_easy_highscore(at) == NO_HIGHSCORE


def test_own_highscore_is_shown_after_signing_in_again(fast_sleep):
    at = sign_up(open_app())
    finish_a_run(at, correct=12)
    sign_out(at)

    at = sign_in(open_app())
    assert multiplication_easy_highscore(at) == "12"


def test_runs_without_owner_are_not_shown():
    db.init_db()
    db.save_run("old", "Multiplication", "Easy", datetime(2026, 11, 3, tzinfo=timezone.utc), 40, 0, 0)
    at = sign_up(open_app())
    assert multiplication_easy_highscore(at) == NO_HIGHSCORE


# --- Online database setting ---


def test_secret_is_copied_when_no_setting_exists(monkeypatch):
    monkeypatch.delenv("MATHBUDDY_DATABASE_URL", raising=False)
    db.use_database_url_from({"MATHBUDDY_DATABASE_URL": "postgresql://from-secrets"})
    assert db.database_url() == "postgresql://from-secrets"


def test_existing_setting_wins_over_the_secret(monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DATABASE_URL", "postgresql://from-environment")
    db.use_database_url_from({"MATHBUDDY_DATABASE_URL": "postgresql://from-secrets"})
    assert db.database_url() == "postgresql://from-environment"


def test_tests_stay_on_sqlite_even_with_a_secret(monkeypatch):
    """conftest sets the setting to empty, so a real secrets.toml is never used in tests."""
    db.use_database_url_from({"MATHBUDDY_DATABASE_URL": "postgresql://from-secrets"})
    assert db.database_url() is None


def test_missing_secret_changes_nothing(monkeypatch):
    monkeypatch.delenv("MATHBUDDY_DATABASE_URL", raising=False)
    db.use_database_url_from({})
    assert db.database_url() is None
