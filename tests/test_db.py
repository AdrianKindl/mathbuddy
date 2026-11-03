"""SQLite storage of completed runs."""

import os
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
from runs import SavedRun, highscores

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINISHED = datetime(2026, 11, 3, 12, 1, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test uses its own file, so data/mathbuddy.db is never touched."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("MATHBUDDY_DB", str(path))
    return path


def save(run_id="run-1", test_type="Multiplication", level="Easy", correct=12, wrong=3, skipped=2):
    db.save_run(run_id, test_type, level, FINISHED, correct, wrong, skipped)


# --- Location ---


def test_default_path_is_data_mathbuddy_db(monkeypatch):
    monkeypatch.delenv("MATHBUDDY_DB")
    assert Path(db.db_path()).parts[-2:] == ("data", "mathbuddy.db")


def test_path_can_be_overridden(temp_db):
    assert Path(db.db_path()) == temp_db


def test_missing_folders_are_created(tmp_path, monkeypatch):
    path = tmp_path / "does" / "not" / "exist" / "test.db"
    monkeypatch.setenv("MATHBUDDY_DB", str(path))
    db.init_db()
    assert path.exists()


# --- Schema ---


def test_only_a_runs_table_exists_with_exactly_the_required_columns():
    """Highscores and totals are never stored. No status or user column in 001."""
    db.init_db()
    with closing(db.connect()) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            if not row[0].startswith("sqlite_")
        }
        columns = {row[1] for row in connection.execute("PRAGMA table_info(runs)")}

    assert tables == {"runs"}
    assert columns == {"id", "test_type", "level", "finished_at", "correct", "wrong", "skipped"}


# --- Saving and reading ---


def test_no_runs_at_first():
    db.init_db()
    assert db.list_runs() == []


def test_saved_run_is_read_back_with_all_fields():
    db.init_db()
    save()
    assert db.list_runs() == [
        SavedRun(
            id="run-1",
            test_type="Multiplication",
            level="Easy",
            finished_at=FINISHED,
            correct=12,
            wrong=3,
            skipped=2,
        )
    ]


def test_finished_at_is_read_back_in_utc():
    db.init_db()
    save()
    assert db.list_runs()[0].finished_at.utcoffset() == timedelta(0)


def test_several_runs_are_all_kept():
    db.init_db()
    save("a", correct=1)
    save("b", correct=2)
    assert sorted(run.correct for run in db.list_runs()) == [1, 2]


def test_run_with_no_attempts_is_saved():
    db.init_db()
    save(correct=0, wrong=0, skipped=0)
    assert len(db.list_runs()) == 1


def test_saving_the_same_run_twice_keeps_the_first_one():
    db.init_db()
    save("same", correct=12)
    save("same", correct=99)
    runs = db.list_runs()
    assert len(runs) == 1
    assert runs[0].correct == 12


# --- Restart ---


def test_init_db_twice_keeps_saved_runs():
    db.init_db()
    save()
    db.init_db()
    assert len(db.list_runs()) == 1


def test_highscore_survives_a_restart():
    """A new process on the same file stands in for stopping and restarting the app."""
    db.init_db()
    save("a", correct=15)
    save("b", correct=12)

    script = "import db; db.init_db(); print(len(db.list_runs()))"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "2"
    assert highscores(db.list_runs()) == {("Multiplication", "Easy"): 15}
