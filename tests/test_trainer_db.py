"""SQLite storage of finished trainer sessions."""

import os
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

import db
import trainer_db
from trainer import (
    Mode,
    SavedSession,
    abort_session,
    finish_if_expired,
    make_settings,
    skip_task,
    start_session,
    submit_answer,
)
from trainer_tasks import AnswerKind, Topic, TrainerTask

PROJECT_ROOT = Path(__file__).resolve().parent.parent
START = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
TOPIC = Topic("Natural numbers", "Percentage", "Easy")
TASK = TrainerTask(TOPIC, "Calculate", "25 % of 80", Fraction(20), AnswerKind.WHOLE, "25 % of 80 = 20")


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test uses its own file, so data/mathbuddy.db is never touched."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("MATHBUDDY_DB", str(path))
    trainer_db.init_db()
    return path


def at(seconds):
    return START + timedelta(seconds=seconds)


def running_session(mode=Mode.TASK_COUNT, limit=5, start=START):
    settings = make_settings("Operations", "Percentage", [TOPIC], mode, limit)
    return start_session(settings, start)


def finished_session(start=START):
    """Five tasks, one every 2 seconds: 3 correct, 1 wrong, 1 skipped."""
    session = running_session(start=start)
    for position, raw in enumerate(["20", "20", "20", "9"], start=1):
        session, _ = submit_answer(session, TASK, raw, start + timedelta(seconds=2 * position))
    session, _ = skip_task(session, TASK, start + timedelta(seconds=10))
    return session


# --- Schema ---


def test_trainer_sessions_live_in_their_own_table_with_exactly_these_columns():
    with closing(db.connect()) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(trainer_sessions)")}
    assert columns == {
        "id",
        "category",
        "name",
        "levels",
        "mode",
        "limit_value",
        "finished_at",
        "duration_seconds",
        "correct",
        "wrong",
        "skipped",
    }


def test_the_runs_table_of_the_tests_is_left_alone():
    db.init_db()
    trainer_db.save_session("session-1", finished_session())
    assert db.list_runs() == []


# --- Saving and reading ---


def test_no_sessions_at_first():
    assert trainer_db.list_sessions() == []


def test_finished_session_is_read_back_with_all_fields():
    trainer_db.save_session("session-1", finished_session())
    assert trainer_db.list_sessions() == [
        SavedSession(
            id="session-1",
            category="Operations",
            name="Percentage",
            levels="Easy",
            mode="Task count",
            limit=5,
            finished_at=at(10),
            duration_seconds=10,
            correct=3,
            wrong=1,
            skipped=1,
        )
    ]


def test_finished_at_is_read_back_in_utc():
    trainer_db.save_session("session-1", finished_session())
    assert trainer_db.list_sessions()[0].finished_at.utcoffset() == timedelta(0)


def test_session_that_ran_out_of_time_is_saved_at_its_limit():
    session = finish_if_expired(running_session(Mode.TOTAL_TIME, 30), at(45))
    trainer_db.save_session("timed", session)
    saved = trainer_db.list_sessions()[0]
    assert (saved.mode, saved.limit, saved.duration_seconds) == ("Total time", 30, 30)
    assert saved.finished_at == at(30)


def test_levels_of_a_mixed_number_type_session_are_saved_as_text():
    topics = [Topic("Decimals", "Addition", "Easy"), Topic("Decimals", "Division", "Hard")]
    settings = make_settings("Number types", "Decimals", topics, Mode.TIME_PER_TASK, 5)
    trainer_db.save_session("mixed", finish_if_expired(start_session(settings, START), at(6)))
    saved = trainer_db.list_sessions()[0]
    assert (saved.category, saved.name) == ("Number types", "Decimals")
    assert saved.levels == "Addition Easy, Division Hard"


def test_saving_the_same_session_twice_keeps_the_first_one():
    trainer_db.save_session("same", finished_session())
    trainer_db.save_session("same", finish_if_expired(running_session(Mode.TOTAL_TIME, 30), at(31)))
    saved = trainer_db.list_sessions()
    assert len(saved) == 1
    assert saved[0].correct == 3


# --- Rejected: only finished sessions are saved ---


def test_running_session_is_not_saved():
    with pytest.raises(ValueError):
        trainer_db.save_session("running", running_session())
    assert trainer_db.list_sessions() == []


def test_aborted_session_is_not_saved():
    session, _ = submit_answer(running_session(), TASK, "20", at(2))
    with pytest.raises(ValueError):
        trainer_db.save_session("aborted", abort_session(session, at(3)))
    assert trainer_db.list_sessions() == []


def test_text_is_stored_as_data_and_never_run_as_sql():
    trainer_db.save_session("x'); DROP TABLE trainer_sessions; --", finished_session())
    assert [saved.id for saved in trainer_db.list_sessions()] == [
        "x'); DROP TABLE trainer_sessions; --"
    ]


# --- Order and history length ---


def test_sessions_are_listed_newest_first():
    for name, day in (("old", 0), ("new", 2), ("middle", 1)):
        trainer_db.save_session(name, finished_session(start=START + timedelta(days=day)))
    assert [saved.id for saved in trainer_db.list_sessions()] == ["new", "middle", "old"]


def test_limit_keeps_only_the_newest_sessions():
    for day in range(5):
        trainer_db.save_session(f"day-{day}", finished_session(start=START + timedelta(days=day)))
    assert [saved.id for saved in trainer_db.list_sessions(limit=2)] == ["day-4", "day-3"]
    assert len(trainer_db.list_sessions()) == 5


# --- Restart ---


def test_init_db_twice_keeps_saved_sessions():
    trainer_db.save_session("session-1", finished_session())
    trainer_db.init_db()
    assert len(trainer_db.list_sessions()) == 1


def test_sessions_survive_a_restart():
    """A new process on the same file stands in for stopping and restarting the app."""
    trainer_db.save_session("session-1", finished_session())

    script = "import trainer_db; trainer_db.init_db(); print(len(trainer_db.list_sessions()))"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "1"
