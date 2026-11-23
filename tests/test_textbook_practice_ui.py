"""Textbook practice screens (stage 2), driven through AppTest (TA10–TA12, T R5).

AppTest does not run a browser, so these need a manual check in the PR: the look
of the choice buttons, the green and red flash, cursor focus and field clearing.
"""

import random
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest
from streamlit.proto.ButtonGroup_pb2 import ButtonGroup as ButtonGroupProto
from streamlit.testing.v1 import AppTest

import activity_db
import knowledge_db
import textbook_db
from knowledge import skip_task as skip_trick
from knowledge import start_round as start_trick_round
from textbook import AnswerType, current_task
from conftest import TEST_USER
from stats import Kind

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
LEVELS = ["Easy", "Medium", "Hard", "Pro"]
CASE_INTERVIEW_IDS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
CATEGORY_OF = {"B": "basics", "F": "fractions", "C": "case_interview", "E": "estimating"}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


def go_to(at, section):
    at.radio(key="nav").set_value(section).run()
    assert not at.exception


def click(at, key):
    at.button(key=key).click().run()
    assert not at.exception
    return at


def set_mode(at, mode):
    at.button_group(key="kn_mode").set_value(mode).run()
    assert not at.exception


def open_app():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    go_to(at, "Knowledge")
    return at


def open_article(article_id, at=None):
    at = at or open_app()
    set_mode(at, "Textbook")
    if "tb_back" in [b.key for b in at.button]:  # back to the overview first
        while "tb_back" in [b.key for b in at.button]:
            click(at, "tb_back")
    click(at, f"tb_category_{CATEGORY_OF[article_id[0]]}")
    return click(at, f"tb_article_{article_id}")


def practising(article_id="C2", level="Easy", at=None):
    at = open_article(article_id, at)
    click(at, "tb_practice")
    at.button_group(key="tb_level").set_value(level)
    return click(at, "tb_start")


def task_now(at):
    return current_task(at.session_state["tb_round"])


def rounded(x, decimals):
    exact = Decimal(x.numerator) / Decimal(x.denominator)
    sign = -1 if exact < 0 else 1
    return sign * abs(exact).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def give(at, raw):
    """Answer the current task: type it, or click the option with that label."""
    task = task_now(at)
    if task.kind == AnswerType.CHOICE:
        button = next(b for b in at.button if (b.key or "").startswith("tb_choice_") and b.label == raw)
        button.click().run()
    else:
        at.text_input(key="tb_answer").input(raw)
        at.button(key="tb_submit").click().run()
    assert not at.exception
    return at


def answer_right(at):
    task = task_now(at)
    if task.kind == AnswerType.CHOICE:
        return give(at, task.correct_choice)
    if task.kind == AnswerType.DECIMAL:
        return give(at, str(rounded(task.answer, task.decimals)))
    return give(at, str(round(task.answer)))


def answer_wrong(at):
    task = task_now(at)
    if task.kind == AnswerType.CHOICE:
        return give(at, next(c for c in task.choices if c != task.correct_choice))
    if task.kind == AnswerType.ESTIMATE:
        return give(at, str(int(abs(task.answer)) * 3 + 100))
    if task.kind == AnswerType.DECIMAL:
        return give(at, str(rounded(task.answer, task.decimals) + 1))
    return give(at, str(int(task.answer) + 1))


def complete_round(at, correct=0, wrong=0, skipped=0):
    for _ in range(correct):
        answer_right(at)
    for _ in range(wrong):
        answer_wrong(at)
    for _ in range(skipped):
        click(at, "tb_skip")
    return at


def page_text(at):
    groups = (
        at.header, at.subheader, at.markdown, at.caption, at.text,
        at.success, at.info, at.warning, at.error,
    )  # fmt: skip
    return "\n".join(str(element.value) for group in groups for element in group)


def metrics(at):
    return {metric.label: metric.value for metric in at.metric}


def article_labels(at):
    return {b.key.removeprefix("tb_article_"): b.label for b in at.button
            if (b.key or "").startswith("tb_article_")}  # fmt: skip


def trick_labels(at):
    return {b.key.removeprefix("kn_trick_"): b.label for b in at.button
            if (b.key or "").startswith("kn_trick_")}  # fmt: skip


def save_completed_trick_round(trick_id):
    knowledge_db.init_db()
    practice_round = start_trick_round(trick_id, "Easy", random.Random(1))
    for _ in range(10):
        practice_round, _ = skip_trick(practice_round)
    knowledge_db.save_round(f"{trick_id}-done", practice_round,
                            datetime(2026, 11, 21, 12, tzinfo=timezone.utc))  # fmt: skip
    activity_db.init_db()
    activity_db.assign_owner(Kind.TRICKS, f"{trick_id}-done", TEST_USER.id)  # spec 014


def case_interview_ticks(at):
    labels = article_labels(at)
    return {article_id: labels[article_id].endswith("✓") for article_id in CASE_INTERVIEW_IDS}


# --- Starting (T R6) ---


def test_practice_uses_the_same_level_buttons_as_tricks():
    at = open_article("C2")
    click(at, "tb_practice")
    level = at.button_group(key="tb_level")
    assert list(level.options) == LEVELS
    assert level.proto.style == ButtonGroupProto.Style.SEGMENTED_CONTROL


def test_starting_shows_task_1_of_10_for_the_article_and_level():
    at = practising("C2", "Hard")
    practice_round = at.session_state["tb_round"]
    assert (practice_round.article_id, practice_round.level) == ("C2", "Hard")
    assert len(practice_round.tasks) == 10
    assert "Task 1 / 10" in page_text(at)
    assert task_now(at).prompt in page_text(at)


def test_back_from_the_level_choice_returns_to_the_article():
    at = open_article("C2")
    click(at, "tb_practice")
    click(at, "tb_back")
    assert "The rule of 72" in page_text(at)


# --- Answer types on screen (T R7, T R8) ---


def test_correct_typed_answer_moves_on():
    at = practising("C2")
    answer_right(at)
    assert at.session_state["tb_round"].correct == 1
    assert "Task 2 / 10" in page_text(at)


def test_wrong_typed_answer_shows_the_correct_answer():
    at = practising("C2")
    task = task_now(at)
    answer_wrong(at)
    assert at.session_state["tb_round"].wrong == 1
    assert f"The answer is {int(task.answer):,}" in page_text(at)


def test_skip_shows_the_correct_answer():
    at = practising("C2")
    task = task_now(at)
    click(at, "tb_skip")
    assert at.session_state["tb_round"].skipped == 1
    assert f"The answer is {int(task.answer):,}" in page_text(at)


def test_input_of_the_wrong_form_shows_a_hint_and_keeps_the_task():
    at = practising("C2")
    task = task_now(at)
    give(at, "abc")
    assert at.warning, "a hint is shown"
    assert task_now(at) == task
    assert "Task 1 / 10" in page_text(at)


def test_choice_tasks_show_one_button_per_option_and_a_click_answers():
    at = practising("F2", "Easy")
    task = task_now(at)
    labels = [b.label for b in at.button if (b.key or "").startswith("tb_choice_")]
    assert labels == list(task.choices)
    assert "tb_answer" not in [box.key for box in at.text_input]
    answer_right(at)
    assert at.session_state["tb_round"].correct == 1
    assert "Task 2 / 10" in page_text(at)


def test_wrong_estimate_shows_the_exact_result_and_the_accepted_range():
    at = practising("E2", "Hard")
    task = task_now(at)
    answer_wrong(at)
    low = int(-(-task.answer * 9 // 10))  # smallest whole number within -10 %
    high = int(task.answer * 11 // 10)
    assert f"accepted: {low:,} to {high:,}" in page_text(at)


def test_correct_decimal_answer_is_accepted():
    at = practising("C1", "Medium")
    answer_right(at)
    assert at.session_state["tb_round"].correct == 1


# --- Result, saving and the tick (T R9, T R10, TA10–TA12) ---


def test_6_correct_3_wrong_1_skipped_shows_6_of_10_and_is_saved():
    at = complete_round(practising("C5", "Hard"), correct=6, wrong=3, skipped=1)
    assert metrics(at)["Correct"] == "6 / 10"
    saved = textbook_db.list_rounds()
    assert [(r.article_id, r.level, r.correct) for r in saved] == [("C5", "Hard", 6)]
    assert at.button(key="tb_again")
    assert at.button(key="tb_to_article")


def test_completed_rule_of_72_round_shows_a_tick_only_next_to_it():
    save_completed_trick_round("M4")
    at = complete_round(practising("C2"), correct=4, skipped=6)
    click(at, "tb_to_article")
    assert "The rule of 72" in page_text(at)
    click(at, "tb_back")
    assert case_interview_ticks(at) == {a: a == "C2" for a in CASE_INTERVIEW_IDS}

    set_mode(at, "Tricks")  # Tricks ✓ markers are unchanged (T R5)
    if "kn_category_multiplication" in [b.key for b in at.button]:
        click(at, "kn_category_multiplication")
    assert {t: label.endswith("✓") for t, label in trick_labels(at).items()} == {
        f"M{n}": n == 4 for n in range(1, 9)
    }


def test_tick_is_still_there_after_a_restart():
    complete_round(practising("C2"), skipped=10)
    at = open_app()  # a new session on the same database file
    set_mode(at, "Textbook")
    click(at, "tb_category_case_interview")
    assert case_interview_ticks(at) == {a: a == "C2" for a in CASE_INTERVIEW_IDS}


def test_leaving_a_round_after_5_tasks_saves_nothing():
    at = complete_round(practising("C2"), correct=5)
    click(at, "tb_leave")
    assert textbook_db.list_rounds() == []
    assert "The rule of 72" in page_text(at)  # back on the article
    click(at, "tb_back")
    assert not any(case_interview_ticks(at).values())


def test_switching_tab_during_a_round_saves_nothing():
    at = complete_round(practising("C2"), correct=5)
    go_to(at, "Tests")
    go_to(at, "Knowledge")
    assert textbook_db.list_rounds() == []
    assert "tb_round" not in at.session_state


def test_practise_again_starts_a_new_round_with_the_same_article_and_level():
    at = complete_round(practising("C2", "Medium"), skipped=10)
    click(at, "tb_again")
    practice_round = at.session_state["tb_round"]
    assert (practice_round.article_id, practice_round.level) == ("C2", "Medium")
    assert practice_round.attempts == ()
    assert "Task 1 / 10" in page_text(at)


def test_back_to_article_from_the_result():
    at = complete_round(practising("B1"), skipped=10)
    click(at, "tb_to_article")
    assert "Why the order matters" in page_text(at)


# --- Tricks practice unchanged ---


def test_tricks_practice_still_saves_only_tricks_rounds():
    at = open_app()
    click(at, "kn_category_multiplication")
    click(at, "kn_trick_M4")
    click(at, "kn_practice")
    at.button_group(key="kn_level").set_value("Easy")
    click(at, "kn_start")
    for _ in range(10):
        click(at, "kn_skip")
    assert metrics(at)["Correct"] == "0 / 10"
    assert [r.trick_id for r in knowledge_db.list_rounds()] == ["M4"]
    textbook_db.init_db()
    assert textbook_db.list_rounds() == []


def test_a_textbook_round_adds_no_tricks_round():
    complete_round(practising("C2"), skipped=10)
    knowledge_db.init_db()
    assert knowledge_db.list_rounds() == []
    assert [r.article_id for r in textbook_db.list_rounds()] == ["C2"]
