"""Spec 014: you only see your own history.

"Recent sessions" in the Trainer and the ✓ marks in Knowledge (Tricks) and
Textbook come only from your own finished sessions and rounds.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import accounts_db
import activity_db
import db
import knowledge_db
import textbook_db
import trainer_db
from conftest import TEST_USER
from knowledge import practised
from stats import Kind
from test_knowledge_db import completed_round as completed_tricks_round
from test_textbook_db import round_with as textbook_round_with
from test_trainer_db import finished_session
from textbook import practised as practised_articles

APP = Path(__file__).resolve().parent.parent / "app.py"
ANNA, BEN = "user-anna", "user-ben"
FINISHED = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    for module in (db, accounts_db, trainer_db, knowledge_db, textbook_db, activity_db):
        module.init_db()


def save_for(session_id, user_id):
    trainer_db.save_session(session_id, finished_session())
    activity_db.assign_owner(Kind.TRAINER, session_id, user_id)


# --- Storage ---


def test_each_player_gets_only_their_own_sessions():
    save_for("anna-1", ANNA)
    save_for("ben-1", BEN)
    save_for("anna-2", ANNA)

    assert sorted(s.id for s in trainer_db.list_sessions_for(ANNA)) == ["anna-1", "anna-2"]
    assert [s.id for s in trainer_db.list_sessions_for(BEN)] == ["ben-1"]


def test_a_new_player_has_no_sessions():
    save_for("anna-1", ANNA)
    assert trainer_db.list_sessions_for(BEN) == []


def test_sessions_without_an_owner_belong_to_nobody():
    trainer_db.save_session("old", finished_session())  # saved before spec 012
    assert trainer_db.list_sessions_for(ANNA) == []


def test_the_limit_counts_only_your_own_sessions():
    for number in range(3):
        save_for(f"anna-{number}", ANNA)
    for number in range(5):
        save_for(f"ben-{number}", BEN)

    assert len(trainer_db.list_sessions_for(ANNA, limit=10)) == 3
    assert len(trainer_db.list_sessions_for(BEN, limit=2)) == 2


def test_own_sessions_look_the_same_as_in_the_full_list():
    save_for("anna-1", ANNA)
    assert trainer_db.list_sessions_for(ANNA) == trainer_db.list_sessions()


# --- Screen ---


def open_trainer():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    at.radio(key="nav").set_value("Trainer").run()
    assert not at.exception
    return at


def test_sessions_of_other_players_are_not_shown():
    save_for("someone-else", BEN)
    at = open_trainer()

    assert len(at.dataframe) == 0
    assert any(
        caption.value.startswith("No finished sessions yet") for caption in at.caption
    )


def test_your_own_sessions_are_shown():
    save_for("mine", TEST_USER.id)
    save_for("someone-else", BEN)
    at = open_trainer()

    history = at.dataframe[0].value
    assert len(history) == 1
    assert list(history["Correct"]) == [3]


# --- ✓ marks in Knowledge (Tricks) and Textbook ---


def save_trick_round(round_id, user_id, trick_id="M4"):
    knowledge_db.save_round(round_id, completed_tricks_round(trick_id=trick_id), FINISHED)
    activity_db.assign_owner(Kind.TRICKS, round_id, user_id)


def save_article_round(round_id, user_id, article_id="C2"):
    textbook_db.save_round(round_id, textbook_round_with(10, article_id=article_id), FINISHED)
    activity_db.assign_owner(Kind.TEXTBOOK, round_id, user_id)


def test_each_player_gets_only_their_own_trick_rounds():
    save_trick_round("anna-m4", ANNA, "M4")
    save_trick_round("ben-m5", BEN, "M5")

    assert practised(knowledge_db.list_rounds_for(ANNA)) == {"M4"}
    assert practised(knowledge_db.list_rounds_for(BEN)) == {"M5"}


def test_trick_rounds_without_an_owner_belong_to_nobody():
    knowledge_db.save_round("old", completed_tricks_round(), FINISHED)
    assert knowledge_db.list_rounds_for(ANNA) == []


def test_each_player_gets_only_their_own_textbook_rounds():
    save_article_round("anna-c2", ANNA, "C2")
    save_article_round("ben-c5", BEN, "C5")

    assert practised_articles(textbook_db.list_rounds_for(ANNA)) == {"C2"}
    assert practised_articles(textbook_db.list_rounds_for(BEN)) == {"C5"}


def test_textbook_rounds_without_an_owner_belong_to_nobody():
    textbook_db.save_round("old", textbook_round_with(10), FINISHED)
    assert textbook_db.list_rounds_for(ANNA) == []


def test_own_rounds_look_the_same_as_in_the_full_lists():
    save_trick_round("anna-m4", ANNA)
    save_article_round("anna-c2", ANNA)
    assert knowledge_db.list_rounds_for(ANNA) == knowledge_db.list_rounds()
    assert textbook_db.list_rounds_for(ANNA) == textbook_db.list_rounds()


def ticked(at, prefix):
    return {
        button.key.removeprefix(prefix)
        for button in at.button
        if (button.key or "").startswith(prefix) and button.label.endswith("✓")
    }


def open_knowledge_category(mode, category_key):
    at = AppTest.from_file(APP, default_timeout=10).run()
    at.radio(key="nav").set_value("Knowledge").run()
    if mode == "Textbook":
        at.button_group(key="kn_mode").set_value("Textbook").run()
    at.button(key=category_key).click().run()
    assert not at.exception
    return at


def test_tricks_practised_by_other_players_get_no_tick():
    save_trick_round("ben-m4", BEN, "M4")
    save_trick_round("mine-m5", TEST_USER.id, "M5")
    at = open_knowledge_category("Tricks", "kn_category_multiplication")
    assert ticked(at, "kn_trick_") == {"M5"}


def test_articles_practised_by_other_players_get_no_tick():
    save_article_round("ben-c2", BEN, "C2")
    save_article_round("mine-c5", TEST_USER.id, "C5")
    at = open_knowledge_category("Textbook", "tb_category_case_interview")
    assert ticked(at, "tb_article_") == {"C5"}
