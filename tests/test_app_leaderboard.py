"""The leaderboard on the Tests screen (MB06, MB R10, A11–A13), driven through AppTest.

The signed-in user is TEST_USER from tests/conftest.py ("tester"). It only
appears on a leaderboard when it exists in the users table, so tests that need
it create it.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import accounts_db
import db
from accounts import User
from conftest import TEST_USER

APP = Path(__file__).resolve().parent.parent / "app.py"
MONDAY = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
CREATED = datetime(2026, 11, 1, tzinfo=timezone.utc)
COLUMNS = ["Rank", "Player", "Score"]  # MB06: no Date column (review of 013)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    db.init_db()
    accounts_db.init_db()


def add_user(user_id, username):
    accounts_db.create_user(
        User(user_id, username, f"{username.lower()}@example.com", "pbkdf2_sha256$1$00$00", CREATED)
    )


def add_me():
    accounts_db.create_user(TEST_USER)


def add_run(run_id, correct, owner, test_type="Multiplication", level="Easy", when=MONDAY):
    db.save_run(run_id, test_type, level, when, correct, 0, 0)
    if owner:
        accounts_db.assign_run(run_id, owner)


def add_players(count, *, start=100, test_type="Multiplication", level="Easy"):
    """`count` players with different scores: p01 has the most (start − 1)."""
    for n in range(1, count + 1):
        add_user(f"p{n:02d}", f"p{n:02d}")
        add_run(f"p{n:02d}-run", start - n, f"p{n:02d}", test_type, level)


def open_tests(operation="Multiplication", level="Easy"):
    at = AppTest.from_file(APP, default_timeout=10).run()
    at.button_group(key="test_type").set_value(operation)
    at.button_group(key="level").set_value(level)
    at.run()
    assert not at.exception
    return at


def board(at):
    """The leaderboard table as rows of text: the only table on the Tests screen (spec 015)."""
    table = at.table[0].value
    assert list(table.columns) == COLUMNS
    return [[str(cell) for cell in row] for row in table.itertuples(index=False)]


def page_text(at):
    groups = (at.header, at.subheader, at.markdown, at.caption, at.text, at.info, at.warning)
    return "\n".join(str(element.value) for group in groups for element in group)


# --- Place and selection (MB06) ---


def test_leaderboard_follows_the_highscores_and_the_selection():
    add_user("u1", "Adrian")
    add_run("r1", 12, "u1")
    at = open_tests("Multiplication", "Easy")
    subheaders = [s.value for s in at.subheader]
    assert subheaders.index("Leaderboard") > subheaders.index("Highscores")
    assert "All-time top 15 · Multiplication · Easy" in [c.value for c in at.caption]
    assert board(at) == [["1", "Adrian", "12"]]


def test_changing_the_selection_changes_the_leaderboard():
    add_user("u1", "Adrian")
    add_run("easy", 12, "u1", level="Easy")
    add_run("pro", 7, "u1", test_type="Division", level="Pro")
    at = open_tests("Multiplication", "Easy")
    assert board(at)[0][2] == "12"
    at.button_group(key="test_type").set_value("Division")
    at.button_group(key="level").set_value("Pro")
    at.run()
    assert "All-time top 15 · Division · Pro" in [c.value for c in at.caption]
    assert board(at) == [["1", "Adrian", "7"]]


def test_empty_leaderboard_shows_a_message_and_no_table():
    at = open_tests("Addition", "Hard")
    assert "No runs yet for this operation and level." in page_text(at)
    assert len(at.table) == 0  # no leaderboard table, and no highscore table since spec 015


# --- Order, tie-break, one entry per user (A11) ---


def test_order_and_tie_break_by_the_earlier_date():
    add_user("u1", "Mia")
    add_user("u2", "Adrian")
    add_user("u3", "Lena")
    add_run("mia", 18, "u1", when=MONDAY)
    add_run("adrian-low", 12, "u2", when=MONDAY)
    add_run("adrian", 18, "u2", when=MONDAY + timedelta(days=1))
    add_run("lena", 15, "u3", when=MONDAY)
    assert board(open_tests()) == [
        ["1", "Mia", "18"],
        ["2", "Adrian", "18"],
        ["3", "Lena", "15"],
    ]


# --- Top 15 and the own row (A12) ---


def test_only_the_top_15_without_an_own_run():
    add_players(20)
    add_me()
    rows = board(open_tests())
    assert [row[0] for row in rows] == [str(n) for n in range(1, 16)]
    assert not any("(you)" in row[1] for row in rows)


def test_own_row_below_the_top_15():
    add_players(20)  # scores 99 down to 80
    add_me()
    # 82 like p18, but reached an hour later, so p18 ranks 18 and tester 19.
    add_run("mine", 82, TEST_USER.id, when=MONDAY + timedelta(hours=1))
    rows = board(open_tests())
    assert len(rows) == 17
    assert [row[0] for row in rows[:15]] == [str(n) for n in range(1, 16)]
    assert rows[15] == ["…", "", ""]
    assert rows[16] == ["19", "tester (you)", "82"]


def test_own_row_inside_the_top_15_is_marked_and_not_repeated():
    add_players(20)
    add_me()
    add_run("mine", 1000, TEST_USER.id)
    rows = board(open_tests())
    assert len(rows) == 15
    assert rows[0] == ["1", "tester (you)", "1000"]
    assert sum("(you)" in row[1] for row in rows) == 1


def test_own_run_of_another_level_gives_no_own_row():
    add_players(20)
    add_me()
    add_run("mine", 5, TEST_USER.id, level="Medium")
    rows = board(open_tests("Multiplication", "Easy"))
    assert len(rows) == 15
    assert not any("(you)" in row[1] for row in rows)


def test_a_best_score_of_0_does_not_appear_and_gives_no_own_row():
    """MB R10 (review of 013): only highscores of at least 1 count."""
    add_user("u1", "Lena")
    add_user("u2", "Mia")
    add_me()
    add_run("lena", 0, "u1")  # Lena's only run: 0 correct
    add_run("mia", 1, "u2")  # Mia's best score is 1
    add_run("mine", 0, TEST_USER.id)  # the signed-in user's only run: 0 correct
    rows = board(open_tests())
    assert rows == [["1", "Mia", "1"]]
    assert not any("(you)" in row[1] for row in rows)


# --- Separate and private (A13) ---


def test_operation_and_level_are_kept_separate():
    add_user("u1", "Adrian")
    add_user("u2", "Mia")
    add_run("easy", 12, "u1", level="Easy")
    add_run("medium", 30, "u2", level="Medium")
    add_run("addition", 40, "u2", test_type="Addition", level="Easy")
    assert board(open_tests("Multiplication", "Easy")) == [["1", "Adrian", "12"]]


def test_runs_without_an_owner_are_not_shown():
    add_user("u1", "Adrian")
    add_run("owned", 12, "u1")
    add_run("old", 99, None)
    assert board(open_tests()) == [["1", "Adrian", "12"]]


def test_no_email_address_is_shown():
    add_players(3)
    add_me()
    add_run("mine", 50, TEST_USER.id)
    at = open_tests()
    cells = [cell for row in board(at) for cell in row]
    assert not any("@" in cell for cell in cells)
    assert "@" not in page_text(at)


def test_highscores_still_show_only_the_own_runs():
    add_user("u1", "Adrian")
    add_run("theirs", 50, "u1")
    at = open_tests()
    assert {metric.label: metric.value for metric in at.metric}["Your best"] == "–"
