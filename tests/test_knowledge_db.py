"""Storage of completed practice rounds in knowledge_db.py (K R6, KA8, KA9)."""

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
from knowledge import SavedRound, current_task, practised, skip_task, start_round, submit_answer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINISHED = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    knowledge_db.init_db()


def completed_round(trick_id="M4", level="Easy", correct=7):
    practice_round = start_round(trick_id, level, random.Random(1))
    for number in range(10):
        if number < correct:
            practice_round, _ = submit_answer(
                practice_round, str(current_task(practice_round).answer)
            )
        else:
            practice_round, _ = skip_task(practice_round)
    return practice_round


def unfinished_round(tasks_done=5):
    practice_round = start_round("M4", "Easy", random.Random(1))
    for _ in range(tasks_done):
        practice_round, _ = skip_task(practice_round)
    return practice_round


def test_table_has_exactly_the_required_columns():
    with closing(db.connect()) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_rounds)")}
    assert columns == {"id", "trick_id", "level", "finished_at", "correct"}


def test_runs_table_is_left_alone():
    db.init_db()
    with closing(db.connect()) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        columns = {row[1] for row in connection.execute("PRAGMA table_info(runs)")}
    assert {"runs", "practice_rounds"} <= tables
    assert columns == {"id", "test_type", "level", "finished_at", "correct", "wrong", "skipped"}


def test_nothing_is_saved_at_first():
    assert knowledge_db.list_rounds() == []


def test_completed_round_is_saved_with_all_fields():
    knowledge_db.save_round("round-1", completed_round(correct=7), FINISHED)
    assert knowledge_db.list_rounds() == [
        SavedRound(id="round-1", trick_id="M4", level="Easy", finished_at=FINISHED, correct=7)
    ]


def test_finished_at_is_read_back_in_utc():
    knowledge_db.save_round("round-1", completed_round(), FINISHED)
    assert knowledge_db.list_rounds()[0].finished_at.utcoffset() == timedelta(0)


def test_saving_the_same_round_twice_keeps_one():
    practice_round = completed_round()
    knowledge_db.save_round("same", practice_round, FINISHED)
    knowledge_db.save_round("same", practice_round, FINISHED)
    assert len(knowledge_db.list_rounds()) == 1


@pytest.mark.parametrize("tasks_done", [0, 5, 9])
def test_an_unfinished_round_cannot_be_saved(tasks_done):
    with pytest.raises(ValueError):
        knowledge_db.save_round("early", unfinished_round(tasks_done), FINISHED)
    assert knowledge_db.list_rounds() == []
    assert practised(knowledge_db.list_rounds()) == set()


def test_practised_comes_from_the_saved_rounds():
    knowledge_db.save_round("one", completed_round("M4", correct=0), FINISHED)
    assert practised(knowledge_db.list_rounds()) == {"M4"}


def test_saved_rounds_survive_a_restart():
    """A new process on the same file stands in for stopping and restarting the app."""
    knowledge_db.save_round("one", completed_round("M4"), FINISHED)
    script = (
        "import knowledge_db, knowledge; knowledge_db.init_db(); "
        "print(sorted(knowledge.practised(knowledge_db.list_rounds())))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "['M4']"


def test_storage_module_has_no_streamlit():
    source = (PROJECT_ROOT / "knowledge_db.py").read_text(encoding="utf-8")
    assert "streamlit" not in source
