"""Regression tests for spec 018: Submit, Skip or Abort arriving after the test has ended.

Cause: when the 60 seconds run out, the running fragment hands over to a full
app rerun, which saves the run, clears it from the session (`run`,
`current_task`, ...) and shows the result. If the player pressed Enter (or Skip
or Abort) at that same moment, the click was already on its way. Streamlit still
calls the old button's callback on the next rerun, the callback reads
`state.run`, which is gone, and the app shows a red AttributeError above the
result. A late action must be ignored: no error, nothing changed, the run saved
only once.
"""

import time
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import db

APP = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


@pytest.fixture(autouse=True)
def fast_sleep(monkeypatch):
    real_sleep = time.sleep
    monkeypatch.setattr(time, "sleep", lambda seconds: real_sleep(min(seconds, 0.01)))


def saved_runs():
    return [(run.test_type, run.level, run.correct, run.wrong, run.skipped)
            for run in db.list_runs()]  # fmt: skip


@pytest.mark.parametrize("action", ["submit", "skip", "abort"])
def test_an_action_that_arrives_after_time_is_up_is_ignored(action):
    at = AppTest.from_file(APP, default_timeout=10).run()  # signed in by tests/conftest.py
    at.button_group(key="test_type").set_value("Addition")
    at.button_group(key="level").set_value("Easy")
    at.button(key="start").click().run()
    for _ in range(3):  # a few right answers, so the saved run has a score
        at.text_input(key="answer").input(str(at.session_state["current_task"].answer))
        at.button(key="submit").click().run()
    assert not at.exception

    # The player's click, still on its way while the time runs out.
    late = at.button(key=action)
    at.text_input(key="answer").input("7" if action == "submit" else "")

    # The 60 seconds are up: the full rerun saves the run and shows the result.
    run = at.session_state["run"]
    at.session_state["run"] = replace(run, started_at=run.started_at - timedelta(seconds=61))
    at.run()
    assert not at.exception
    assert at.session_state["phase"] == "result"
    assert "run" not in at.session_state and "current_task" not in at.session_state
    result = at.session_state["result"]
    saved = saved_runs()
    assert saved == [("Addition", "Easy", 3, 0, 0)]

    # Now the late click arrives.
    at.session_state["answer"] = ""  # the browser still sends the old answer field as well
    late.click().run()

    assert not at.exception, [error.message for error in at.exception]
    assert at.session_state["phase"] == "result"
    assert at.session_state["result"] == result
    assert "run" not in at.session_state
    assert saved_runs() == saved, "the run must stay as it was and be saved only once"
    assert at.header[0].value == "Time's up: Addition, Easy"
