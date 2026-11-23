"""Regression tests for spec 016: the task card disappeared during a running test.

Cause: the once-a-second timer refresh (a Streamlit fragment) could arrive while
the page was being redrawn after an answer. The browser then dropped the task
card until the next answer. AppTest does not run a browser or the timer's
refreshes, so it cannot reproduce that race itself. These tests guard what the
fix relies on:

- the timer, the task card and the answer form are drawn by one and the same
  self-refreshing fragment, so an answer and a timer refresh rerun the same
  fragment one after the other instead of overlapping with a full redraw;
- a running test does no database work, so nothing slows down an answer.
"""

import ast
import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import db

APP = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


@pytest.fixture
def fast_sleep(monkeypatch):
    real_sleep = time.sleep
    monkeypatch.setattr(time, "sleep", lambda seconds: real_sleep(min(seconds, 0.01)))


def start_test():
    at = AppTest.from_file(APP, default_timeout=10).run()  # signed in by tests/conftest.py
    at.button_group(key="test_type").set_value("Multiplication")
    at.button_group(key="level").set_value("Easy")
    at.button(key="start").click().run()
    assert not at.exception
    return at


def task_card(at):
    return [header.value for header in at.header]


def test_thirty_answers_keep_the_task_and_timer_and_touch_no_database(fast_sleep, monkeypatch):
    at = start_test()
    connections = []
    real_connect = db.connect
    monkeypatch.setattr(db, "connect", lambda: connections.append(1) or real_connect())

    for number in range(30):
        task = at.session_state["current_task"]
        assert task_card(at) == [task.text], f"answer {number}: the task card is missing"
        assert "Time left" in [metric.label for metric in at.metric]
        answer = task.answer if number % 3 else task.answer + 1  # right and wrong answers
        at.text_input(key="answer").input(str(answer))
        at.button(key="submit").click().run()
        assert not at.exception
    at.button(key="skip").click().run()
    assert not at.exception

    run = at.session_state["run"]
    assert run.correct + run.wrong + run.skipped == 31
    assert task_card(at) == [at.session_state["current_task"].text]
    assert connections == [], "a running test should not query the database"


def _fragment_run_every(function: ast.FunctionDef) -> bool:
    for decorator in function.decorator_list:
        if (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "fragment"
                and any(k.arg == "run_every" for k in decorator.keywords)):  # fmt: skip
            return True
    return False


def _called_names(function: ast.FunctionDef) -> set[str]:
    names = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            target = node.func
            names.add(target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", ""))
    return names


def test_timer_task_card_and_form_are_one_self_refreshing_fragment():
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    running = functions["render_running"]

    assert _fragment_run_every(running), "render_running should refresh itself every second"
    called = _called_names(running)
    assert {"metric", "header", "answer_form"} <= called  # timer, task card, answer form
    fragments = {name for name, node in functions.items() if _fragment_run_every(node)}
    assert not (called & (fragments - {"render_running"})), (
        "no second self-refreshing fragment inside the running screen"
    )
