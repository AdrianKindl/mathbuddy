"""Owners of activities and saved games in activity_db.py (spec 012).

Every completed activity of a player is read back as a stats.Activity:
test runs (owner in run_owners, spec 011), Trainer sessions, Tricks and
Textbook practice rounds (owner in activity_owners) and finished games
(game_results).
"""

from contextlib import closing
from datetime import datetime, timedelta, timezone

import pytest

import accounts_db
import activity_db
import db
import knowledge_db
import textbook_db
import trainer_db
from stats import Activity, Kind
from test_knowledge_db import completed_round as completed_tricks_round
from test_textbook_db import round_with as textbook_round_with
from test_trainer_db import START as TRAINER_START, finished_session

FINISHED = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
ANNA, BEN = "user-anna", "user-ben"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    for module in (db, accounts_db, trainer_db, knowledge_db, textbook_db, activity_db):
        module.init_db()


def columns(table):
    with closing(db.connect()) as connection:
        return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def save_test_run(run_id, user_id, correct=12, wrong=3, skipped=2, finished=FINISHED):
    db.save_run(run_id, "Multiplication", "Easy", finished, correct, wrong, skipped)
    accounts_db.assign_run(run_id, user_id)


def save_trainer_session(session_id, user_id):
    trainer_db.save_session(session_id, finished_session())  # 3 correct, 1 wrong, 1 skipped
    activity_db.assign_owner(Kind.TRAINER, session_id, user_id)


def save_tricks_round(round_id, user_id, correct=7):
    knowledge_db.save_round(round_id, completed_tricks_round(correct=correct), FINISHED)
    activity_db.assign_owner(Kind.TRICKS, round_id, user_id)


def save_textbook_round(round_id, user_id):
    textbook_db.save_round(round_id, textbook_round_with(10), FINISHED)  # 10 skipped
    activity_db.assign_owner(Kind.TEXTBOOK, round_id, user_id)


# --- Schema ---


def test_activity_owners_table_has_exactly_the_required_columns():
    assert columns("activity_owners") == {"kind", "activity_id", "user_id"}


def test_game_results_table_has_exactly_the_required_columns():
    assert columns("game_results") == {"id", "user_id", "game", "level", "finished_at", "outcome"}


def test_existing_tables_keep_their_columns():
    assert columns("practice_rounds") == {"id", "trick_id", "level", "finished_at", "correct"}
    assert columns("textbook_rounds") == {"id", "article_id", "level", "finished_at", "correct"}
    assert "user_id" not in columns("trainer_sessions")
    assert "user_id" not in columns("runs")


def test_init_db_can_run_twice():
    activity_db.init_db()
    activity_db.init_db()


# --- Nothing yet ---


def test_a_new_player_has_no_activities():
    assert activity_db.list_activities_for(ANNA) == []


# --- Every kind is read back as an Activity ---


def test_test_run_is_read_back_with_correct_and_not_correct():
    save_test_run("r1", ANNA)
    assert activity_db.list_activities_for(ANNA) == [Activity(Kind.TEST, FINISHED, 12, 5)]


def test_trainer_session_is_read_back_with_correct_and_not_correct():
    save_trainer_session("s1", ANNA)
    [activity] = activity_db.list_activities_for(ANNA)
    assert (activity.kind, activity.correct, activity.not_correct) == (Kind.TRAINER, 3, 2)
    assert activity.finished_at == TRAINER_START + timedelta(seconds=10)


def test_tricks_round_counts_10_minus_correct_as_not_correct():
    save_tricks_round("k1", ANNA, correct=7)
    assert activity_db.list_activities_for(ANNA) == [Activity(Kind.TRICKS, FINISHED, 7, 3)]


def test_textbook_round_counts_10_minus_correct_as_not_correct():
    save_textbook_round("t1", ANNA)
    assert activity_db.list_activities_for(ANNA) == [Activity(Kind.TEXTBOOK, FINISHED, 0, 10)]


def test_won_game_is_an_activity_without_tasks():
    activity_db.save_game("g1", ANNA, "Mini Sudoku", "Easy", FINISHED, "won")
    assert activity_db.list_activities_for(ANNA) == [Activity(Kind.GAME, FINISHED, 0, 0)]


def test_lost_game_is_an_activity_too():
    activity_db.save_game("g1", ANNA, "Sudoku", "Hard", FINISHED, "lost")
    assert [a.kind for a in activity_db.list_activities_for(ANNA)] == [Kind.GAME]


def test_game_result_is_saved_with_all_fields():
    activity_db.save_game("g1", ANNA, "Sudoku", "Pro", FINISHED, "won")
    with closing(db.connect()) as connection:
        row = connection.execute(
            "SELECT id, user_id, game, level, finished_at, outcome FROM game_results"
        ).fetchone()
    assert row[:4] == ("g1", ANNA, "Sudoku", "Pro")
    assert datetime.fromisoformat(row[4]) == FINISHED
    assert row[5] == "won"


@pytest.mark.parametrize("outcome", ["running", "aborted", "", "WON"])
def test_only_won_or_lost_games_can_be_saved(outcome):
    with pytest.raises(ValueError):
        activity_db.save_game("g1", ANNA, "Sudoku", "Easy", FINISHED, outcome)
    assert activity_db.list_activities_for(ANNA) == []


def test_saving_the_same_game_twice_keeps_one():
    activity_db.save_game("g1", ANNA, "Sudoku", "Easy", FINISHED, "won")
    activity_db.save_game("g1", ANNA, "Sudoku", "Easy", FINISHED + timedelta(hours=1), "lost")
    assert len(activity_db.list_activities_for(ANNA)) == 1


def test_assigning_the_same_owner_twice_keeps_one_activity():
    save_tricks_round("k1", ANNA)
    activity_db.assign_owner(Kind.TRICKS, "k1", ANNA)
    assert len(activity_db.list_activities_for(ANNA)) == 1


def test_all_kinds_together_oldest_first():
    save_test_run("r1", ANNA, finished=FINISHED + timedelta(hours=2))
    save_tricks_round("k1", ANNA)
    activity_db.save_game("g1", ANNA, "Mini Sudoku", "Easy", FINISHED + timedelta(hours=1), "won")
    kinds = [a.kind for a in activity_db.list_activities_for(ANNA)]
    assert kinds == [Kind.TRICKS, Kind.GAME, Kind.TEST]


# --- Own data only ---


def test_activities_of_another_player_are_not_listed():
    save_test_run("r1", BEN)
    save_trainer_session("s1", BEN)
    save_tricks_round("k1", BEN)
    save_textbook_round("t1", BEN)
    activity_db.save_game("g1", BEN, "Sudoku", "Easy", FINISHED, "won")
    assert activity_db.list_activities_for(ANNA) == []
    assert len(activity_db.list_activities_for(BEN)) == 5


def test_activities_without_owner_count_for_nobody():
    db.save_run("old-run", "Addition", "Easy", FINISHED, 9, 0, 0)
    trainer_db.save_session("old-session", finished_session())
    knowledge_db.save_round("old-tricks", completed_tricks_round(), FINISHED)
    textbook_db.save_round("old-textbook", textbook_round_with(10), FINISHED)
    assert activity_db.list_activities_for(ANNA) == []


def test_same_id_in_two_kinds_belongs_to_each_kind_separately():
    save_tricks_round("same-id", ANNA)
    save_textbook_round("same-id", BEN)
    assert [a.kind for a in activity_db.list_activities_for(ANNA)] == [Kind.TRICKS]
    assert [a.kind for a in activity_db.list_activities_for(BEN)] == [Kind.TEXTBOOK]
