"""Storage of completed Textbook practice rounds in textbook_db.py (T R9, T R10, TA11, TA12)."""

import os
import random
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import knowledge_db
import textbook_db
from textbook import SavedRound, practised, skip_task, start_round

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINISHED = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    textbook_db.init_db()


def round_with(tasks_done, article_id="C2", level="Easy"):
    practice_round = start_round(article_id, level, random.Random(1))
    for _ in range(tasks_done):
        practice_round, _ = skip_task(practice_round)
    return practice_round


def tables_and_columns():
    with closing(db.connect()) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        columns = {
            table: {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            for table in tables
        }
    return tables, columns


def test_new_table_has_exactly_the_required_columns():
    _, columns = tables_and_columns()
    assert columns["textbook_rounds"] == {"id", "article_id", "level", "finished_at", "correct"}


def test_existing_tables_are_left_alone():
    db.init_db()
    knowledge_db.init_db()
    tables, columns = tables_and_columns()
    assert {"runs", "practice_rounds", "textbook_rounds"} <= tables
    assert columns["runs"] == {"id", "test_type", "level", "finished_at", "correct", "wrong",
                               "skipped"}  # fmt: skip
    assert columns["practice_rounds"] == {"id", "trick_id", "level", "finished_at", "correct"}


def test_nothing_is_saved_at_first():
    assert textbook_db.list_rounds() == []


def test_completed_round_is_saved_with_all_fields():
    textbook_db.save_round("round-1", round_with(10, "C2", "Hard"), FINISHED)
    assert textbook_db.list_rounds() == [
        SavedRound(id="round-1", article_id="C2", level="Hard", finished_at=FINISHED, correct=0)
    ]
    assert textbook_db.list_rounds()[0].finished_at.utcoffset() == timedelta(0)


def test_saving_the_same_round_twice_keeps_one():
    practice_round = round_with(10)
    textbook_db.save_round("same", practice_round, FINISHED)
    textbook_db.save_round("same", practice_round, FINISHED)
    assert len(textbook_db.list_rounds()) == 1


@pytest.mark.parametrize("tasks_done", [0, 5, 9])
def test_an_unfinished_round_cannot_be_saved(tasks_done):
    with pytest.raises(ValueError):
        textbook_db.save_round("early", round_with(tasks_done), FINISHED)
    assert textbook_db.list_rounds() == []


def test_textbook_rounds_do_not_show_up_as_tricks_and_the_other_way_round():
    knowledge_db.init_db()
    textbook_db.save_round("textbook", round_with(10, "C2"), FINISHED)
    assert knowledge_db.list_rounds() == []
    assert practised(textbook_db.list_rounds()) == {"C2"}


def test_saved_rounds_survive_a_restart():
    """A new process on the same file stands in for stopping and restarting the app."""
    textbook_db.save_round("one", round_with(10, "C2"), FINISHED)
    script = (
        "import textbook_db, textbook; textbook_db.init_db(); "
        "print(sorted(textbook.practised(textbook_db.list_rounds())))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "['C2']"


def test_storage_module_has_no_streamlit():
    source = (PROJECT_ROOT / "textbook_db.py").read_text(encoding="utf-8")
    assert "streamlit" not in source
