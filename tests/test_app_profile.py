"""Profile section and activity owners in the app (spec 012, MB05, MB R8).

The profile shows the signed in player's tasks completed, accuracy, longest
streak, highscores (same function as the Tests tab) and activities of the
last 7 days. Every completed activity counts: Tests, Trainer, Tricks and
Textbook practice, and finished games.
"""

import io
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

import accounts_db
import activity_db
import db
from conftest import TEST_USER
from stats import Kind

import test_app as tests_tab
import test_knowledge_ui as tricks_ui
import test_textbook_practice_ui as textbook_ui
import test_trainer_ui as trainer_ui

APP = Path(__file__).resolve().parent.parent / "app.py"
LISBON = ZoneInfo("Europe/Lisbon")
TEST_TYPES = ["Addition", "Subtraction", "Multiplication", "Division", "Random"]
LEVELS = ["Easy", "Medium", "Hard", "Pro"]
NO_VALUE = "–"
EMPTY_HINT = "Complete a test, training, practice round or game to see your statistics here."
OTHER_USER = "someone-else"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    for module in (db, accounts_db, activity_db):
        module.init_db()


@pytest.fixture
def fast_sleep(monkeypatch):
    real_sleep = time.sleep
    monkeypatch.setattr(time, "sleep", lambda seconds: real_sleep(min(seconds, 0.01)))


def today():
    return datetime.now(LISBON).date()


def noon_utc(days_ago=0):
    day = today() - timedelta(days=days_ago)
    return datetime(day.year, day.month, day.day, 12, 0, tzinfo=timezone.utc)


def open_app():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    return at


def open_profile():
    at = open_app()
    tests_tab.go_to(at, "Profile")
    return at


def metrics(at):
    return {metric.label: metric.value for metric in at.metric}


def highscore_table(at):
    return at.table[0].value


def chart_bars(at):
    """(label, value) of each bar of the 7 day chart, in the order shown."""
    [chart] = at.get("vega_lite_chart")
    [dataset] = chart.proto.datasets
    frame = pa.ipc.open_stream(io.BytesIO(dataset.data.data)).read_all().to_pandas()
    labels, values = frame.columns[0], frame.columns[-1]
    return list(zip(frame[labels], frame[values]))


def seed_test_run(run_id, correct, wrong=0, skipped=0, days_ago=0, level="Easy", user=TEST_USER.id):
    db.save_run(run_id, "Multiplication", level, noon_utc(days_ago), correct, wrong, skipped)
    accounts_db.assign_run(run_id, user)


def seed_game(game_id, days_ago=0, user=TEST_USER.id, outcome="won"):
    activity_db.save_game(game_id, user, "Mini Sudoku", "Easy", noon_utc(days_ago), outcome)


def my_activities():
    return activity_db.list_activities_for(TEST_USER.id)


def kinds_and_tasks():
    return [(a.kind, a.correct, a.not_correct) for a in my_activities()]


# --- Screen ---


def test_profile_no_longer_shows_coming_soon():
    text = tests_tab.page_text(open_profile())
    assert "Coming soon" not in text
    assert "Profile" in text


def test_profile_shows_the_username():
    assert TEST_USER.username in tests_tab.page_text(open_profile())


def test_new_player_sees_empty_values_and_the_hint_without_an_error():
    at = open_profile()
    assert not at.exception
    assert metrics(at) == {"Tasks completed": "0", "Accuracy": NO_VALUE, "Longest streak": "0 days"}
    assert EMPTY_HINT in tests_tab.page_text(at)
    table = highscore_table(at)
    assert all(table.loc[t, level] == NO_VALUE for t in TEST_TYPES for level in LEVELS)
    assert [value for _, value in chart_bars(at)] == [0] * 7


def test_scenario_a5_tasks_and_accuracy_after_a_run():
    seed_test_run("r1", correct=12, wrong=3, skipped=2)
    at = open_profile()
    assert metrics(at) == {"Tasks completed": "12", "Accuracy": "71%", "Longest streak": "1 day"}
    assert EMPTY_HINT not in tests_tab.page_text(at)


def test_only_games_show_activity_but_no_tasks_or_accuracy():
    seed_game("g1")
    at = open_profile()
    assert metrics(at) == {"Tasks completed": "0", "Accuracy": NO_VALUE, "Longest streak": "1 day"}
    assert chart_bars(at)[-1][1] == 1


def test_streak_counts_days_with_any_activity():
    seed_test_run("r1", correct=5, days_ago=2)
    seed_game("g1", days_ago=1)
    seed_game("g2", days_ago=1)
    seed_test_run("r2", correct=5, days_ago=0)
    assert metrics(open_profile())["Longest streak"] == "3 days"


def test_chart_shows_weekdays_oldest_first_with_today_last():
    labels = [label for label, _ in chart_bars(open_profile())]
    expected = [(today() - timedelta(days=n)).strftime("%a") for n in range(6, -1, -1)]
    assert labels == expected


def test_scenario_a9_chart_two_today_one_yesterday():
    seed_test_run("r1", correct=5)
    seed_game("g1")
    seed_test_run("r2", correct=5, days_ago=1)
    seed_test_run("old", correct=5, days_ago=9)
    assert [value for _, value in chart_bars(open_profile())] == [0, 0, 0, 0, 0, 1, 2]


def test_highscore_table_is_the_same_as_on_the_tests_tab():
    seed_test_run("r1", correct=15, level="Easy")
    seed_test_run("r2", correct=9, level="Easy")
    seed_test_run("r3", correct=7, level="Medium")
    at = open_app()
    on_tests_tab = highscore_table(at)
    tests_tab.go_to(at, "Profile")
    on_profile = highscore_table(at)
    assert on_profile.equals(on_tests_tab)
    assert on_profile.loc["Multiplication", "Easy"] == 15


def test_activities_of_other_players_and_without_owner_change_nothing():
    seed_test_run("theirs", correct=20, user=OTHER_USER)
    seed_game("their-game", user=OTHER_USER)
    db.save_run("no-owner", "Addition", "Easy", noon_utc(), 30, 0, 0)
    at = open_profile()
    assert metrics(at) == {"Tasks completed": "0", "Accuracy": NO_VALUE, "Longest streak": "0 days"}
    assert [value for _, value in chart_bars(at)] == [0] * 7


# --- Every completed activity gets the signed in player as owner ---


def test_completed_test_run_counts(fast_sleep):
    at = tests_tab.start_test(open_app())
    tests_tab.finish_run(at, correct=4, wrong=1, skipped=0)
    assert kinds_and_tasks() == [(Kind.TEST, 4, 1)]


def test_aborted_test_run_never_counts(fast_sleep):
    at = tests_tab.start_test(open_app())
    tests_tab.go_to(at, "Profile")
    assert my_activities() == []


def test_finished_trainer_session_counts():
    at = trainer_ui.start_with(trainer_ui.open_trainer(), "Task count", 5)
    for _ in range(5):
        trainer_ui.submit(at, trainer_ui.right_answer(at))
    assert trainer_ui.phase(at) == "result"
    assert kinds_and_tasks() == [(Kind.TRAINER, 5, 0)]


def test_aborted_trainer_session_never_counts():
    at = trainer_ui.start_with(trainer_ui.open_trainer(), "Task count", 5)
    trainer_ui.submit(at, trainer_ui.right_answer(at))
    at.button(key="tr_abort").click().run()
    assert my_activities() == []


def test_completed_tricks_round_counts():
    tricks_ui.complete_round(tricks_ui.practising(), correct=7, skipped=3)
    assert kinds_and_tasks() == [(Kind.TRICKS, 7, 3)]


def test_tricks_round_left_early_never_counts():
    at = tricks_ui.complete_round(tricks_ui.practising(), correct=4)
    tests_tab.go_to(at, "Profile")
    assert my_activities() == []


def test_completed_textbook_round_counts():
    textbook_ui.complete_round(textbook_ui.practising(), skipped=10)
    assert kinds_and_tasks() == [(Kind.TEXTBOOK, 0, 10)]


def solve_game(at):
    while at.session_state["game"].status == "running":
        row, col, right = tests_tab.first_empty_cell(at)
        tests_tab.enter(at, row, col, str(right))
    return at


def lose_game(at):
    row, col, right = tests_tab.first_empty_cell(at)
    for digit in [d for d in range(1, 7) if d != right][:3]:
        tests_tab.enter(at, row, col, str(digit))
    return at


def test_won_game_counts_as_an_activity():
    at = solve_game(tests_tab.start_game())
    assert at.session_state["game"].status == "won"
    assert [a.kind for a in my_activities()] == [Kind.GAME]


def test_lost_game_counts_as_an_activity():
    at = lose_game(tests_tab.start_game())
    assert at.session_state["game"].status == "lost"
    assert [a.kind for a in my_activities()] == [Kind.GAME]


def test_game_left_before_it_ends_never_counts():
    at = tests_tab.start_game()
    row, col, right = tests_tab.first_empty_cell(at)
    tests_tab.enter(at, row, col, str(right))
    tests_tab.go_to(at, "Profile")
    assert my_activities() == []


def test_a_finished_game_is_saved_only_once():
    at = solve_game(tests_tab.start_game())
    at.run()
    tests_tab.go_to(at, "Profile")
    tests_tab.go_to(at, "Games")
    assert len(my_activities()) == 1


def test_all_kinds_together_on_the_profile():
    seed_test_run("r1", correct=12, wrong=3, skipped=2)
    tricks_ui.complete_round(tricks_ui.practising(), correct=7, skipped=3)
    solve_game(tests_tab.start_game())
    at = open_profile()
    assert metrics(at) == {
        "Tasks completed": str(12 + 7),
        "Accuracy": f"{round(100 * (12 + 7) / (17 + 10))}%",
        "Longest streak": "1 day",
    }
    assert chart_bars(at)[-1][1] == 3
