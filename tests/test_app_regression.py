"""Regression test for spec 014: the Tests tab crashed after merging 012 and 013.

The merge put the leaderboard call (013) inside render_highscores() (012), where
the selected operation and level do not exist, so opening Tests raised
"NameError: name 'operation' is not defined". The Profile, which also shows the
highscores, crashed the same way.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import accounts_db
import db
from accounts import User

APP = Path(__file__).resolve().parent.parent / "app.py"
FINISHED = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    db.init_db()
    accounts_db.init_db()


def subheaders(at):
    return [subheader.value for subheader in at.subheader]


@pytest.mark.parametrize("operation, level", [("Division", "Pro"), ("Addition", "Easy")])
def test_tests_tab_renders_highscores_and_the_leaderboard_for_the_selection(operation, level):
    accounts_db.create_user(
        User("u1", "Adrian", "adrian@example.com", "pbkdf2_sha256$1$00$00", FINISHED)
    )
    db.save_run("r1", operation, level, FINISHED, 7, 0, 0)
    accounts_db.assign_run("r1", "u1")

    at = AppTest.from_file(APP, default_timeout=10).run()  # signed in by tests/conftest.py
    assert not at.exception
    at.button_group(key="test_type").set_value(operation)
    at.button_group(key="level").set_value(level)
    at.run()

    assert not at.exception
    assert "Highscores" in subheaders(at)
    assert "Leaderboard" in subheaders(at)
    assert f"All-time top 15 · {operation} · {level}" in [c.value for c in at.caption]
    assert len(at.table) == 2  # the highscores and the leaderboard
    assert list(at.table[1].value.iloc[0]) == ["1", "Adrian", "7"]


def test_profile_shows_its_highscores_without_the_leaderboard():
    at = AppTest.from_file(APP, default_timeout=10).run()
    at.radio(key="nav").set_value("Profile").run()

    assert not at.exception
    assert "Highscores" in subheaders(at)
    assert "Leaderboard" not in subheaders(at)
    assert len(at.table) == 1  # only the highscore table
