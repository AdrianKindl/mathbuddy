"""Knowledge screens in knowledge_ui.py and their wiring in app.py, driven through AppTest.

AppTest does not run a browser, so these need a manual check in the PR: the look
of the tiles, rows and example cards, the green and red flash, cursor focus and
the field clearing after submit.
"""

from pathlib import Path

import pytest
from streamlit.proto.ButtonGroup_pb2 import ButtonGroup as ButtonGroupProto
from streamlit.testing.v1 import AppTest

import knowledge_db
from knowledge import current_task

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
LEVELS = ["Easy", "Medium", "Hard", "Pro"]
CATEGORY_IDS = ["addition", "subtraction", "multiplication", "division", "squares"]
ADDITION = [
    ("A1", "Split one number", "Medium"),
    ("A2", "Split both numbers", "Medium"),
    ("A3", "Compatible numbers", "Medium"),
    ("A4", "Give and take", "Medium"),
    ("A5", "The 9 trick", "Medium–Extreme"),
]
MULTIPLICATION_IDS = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]
IGNORED_HINT = "Numbers only, e.g. 4250"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


def go_to(at, section):
    at.radio(key="nav").set_value(section).run()
    assert not at.exception


def open_knowledge():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    go_to(at, "Knowledge")
    return at


def click(at, key):
    at.button(key=key).click().run()
    assert not at.exception
    return at


def open_trick(trick_id, category_id):
    at = open_knowledge()
    click(at, f"kn_category_{category_id}")
    return click(at, f"kn_trick_{trick_id}")


def start_practice(at, level="Easy"):
    at.button_group(key="kn_level").set_value(level)
    return click(at, "kn_start")


def submit(at, text):
    at.text_input(key="kn_answer").input(text)
    return click(at, "kn_submit")


def task_now(at):
    return current_task(at.session_state["kn_round"])


def answer_right(at):
    return submit(at, str(task_now(at).answer))


def page_text(at):
    groups = (
        at.header, at.subheader, at.markdown, at.caption, at.text,
        at.success, at.info, at.warning, at.error,
    )  # fmt: skip
    return "\n".join(str(element.value) for group in groups for element in group)


def metrics(at):
    return {metric.label: metric.value for metric in at.metric}


def labels(at, prefix):
    return [button.label for button in at.button if (button.key or "").startswith(prefix)]


def trick_label(at, trick_id):
    return at.button(key=f"kn_trick_{trick_id}").label


def complete_round(at, correct=0, wrong=0, skipped=0):
    for _ in range(correct):
        answer_right(at)
    for _ in range(wrong):
        submit(at, "0")
    for _ in range(skipped):
        click(at, "kn_skip")
    return at


# --- Knowledge tab and modes ---


def test_knowledge_is_built_and_starts_in_tricks_mode():
    at = open_knowledge()
    assert "Coming soon" not in page_text(at)
    mode = at.button_group(key="kn_mode")
    assert list(mode.options) == ["Tricks", "Textbook"]
    assert mode.value == "Tricks"


def test_textbook_mode_is_coming_soon():
    at = open_knowledge()
    at.button_group(key="kn_mode").set_value("Textbook").run()
    assert "Coming soon" in page_text(at)


# --- Overview and category (KA1, KA2) ---


def test_overview_shows_five_categories_with_their_trick_counts():
    assert labels(open_knowledge(), "kn_category_") == [
        "Addition (5)",
        "Subtraction (8)",
        "Multiplication (8)",
        "Division (4)",
        "Square numbers (5)",
    ]


def test_addition_lists_its_five_tricks_in_order_without_a_tick():
    at = open_knowledge()
    click(at, "kn_category_addition")
    assert "Addition" in [header.value for header in at.header]
    assert "Addition tricks" in page_text(at)
    assert labels(at, "kn_trick_") == [f"{name} · {difficulty}" for _, name, difficulty in ADDITION]


@pytest.mark.parametrize("category_id", CATEGORY_IDS)
def test_every_category_opens(category_id):
    at = open_knowledge()
    click(at, f"kn_category_{category_id}")
    assert labels(at, "kn_trick_")


def test_back_goes_from_trick_to_category_to_overview():
    at = open_trick("A2", "addition")
    click(at, "kn_back")
    assert labels(at, "kn_trick_")
    click(at, "kn_back")
    assert labels(at, "kn_category_")


# --- Trick screen (KA3, KA4) ---


def test_split_one_number_shows_the_example_and_its_three_steps_in_order():
    text = page_text(open_trick("A1", "addition"))
    assert "Split one number" in text
    assert "56 + 38 = 94" in text
    expected = ["Split the smaller number", "38 → 30 & 8", "Add the tens", "56 + 30 = 86",
                "Add the ones", "86 + 8 = 94"]  # fmt: skip
    positions = [text.find(part) for part in expected]
    assert -1 not in positions
    assert positions == sorted(positions)


def test_a_trick_with_variants_shows_every_variant():
    text = page_text(open_trick("M4", "multiplication"))
    for label in ("1 to 9", "10 to 18", "19 to 99", "100 to 999"):
        assert label in text


def test_previous_is_disabled_on_the_first_trick_and_next_works():
    at = open_trick("A1", "addition")
    assert at.button(key="kn_prev").disabled
    assert not at.button(key="kn_next").disabled
    assert "1 / 5" in page_text(at)
    click(at, "kn_next")
    assert "Split both numbers" in page_text(at)
    assert "2 / 5" in page_text(at)


def test_next_is_disabled_on_the_last_trick():
    at = open_trick("A5", "addition")
    assert at.button(key="kn_next").disabled
    assert not at.button(key="kn_prev").disabled
    assert "5 / 5" in page_text(at)


# --- Practice (K R4, K R5) ---


def test_practice_uses_the_same_level_buttons_as_tests():
    at = open_trick("M4", "multiplication")
    click(at, "kn_practice")
    level = at.button_group(key="kn_level")
    assert list(level.options) == LEVELS
    assert level.proto.style == ButtonGroupProto.Style.SEGMENTED_CONTROL


def test_starting_shows_task_1_of_10():
    at = open_trick("M4", "multiplication")
    click(at, "kn_practice")
    start_practice(at, "Hard")
    practice_round = at.session_state["kn_round"]
    assert (practice_round.trick_id, practice_round.level) == ("M4", "Hard")
    assert "Task 1 / 10" in page_text(at)
    assert task_now(at).text in page_text(at)


def practising(trick_id="M4", category_id="multiplication", level="Easy"):
    at = open_trick(trick_id, category_id)
    click(at, "kn_practice")
    return start_practice(at, level)


def test_correct_answer_moves_to_the_next_task():
    at = practising()
    answer_right(at)
    assert at.session_state["kn_round"].correct == 1
    assert "Task 2 / 10" in page_text(at)


def test_wrong_answer_shows_the_correct_answer():
    at = practising("M4", "multiplication", "Pro")
    task = task_now(at)
    submit(at, "0")
    assert at.session_state["kn_round"].wrong == 1
    assert f"The answer is {task.answer:,}" in page_text(at)
    assert "Task 2 / 10" in page_text(at)


def test_skip_shows_the_correct_answer():
    at = practising()
    task = task_now(at)
    click(at, "kn_skip")
    assert at.session_state["kn_round"].skipped == 1
    assert f"The answer is {task.answer:,}" in page_text(at)


@pytest.mark.parametrize("text", ["", "abc"])
def test_empty_or_non_numeric_input_shows_the_hint_and_keeps_the_task(text):
    at = practising()
    task = task_now(at)
    submit(at, text)
    assert IGNORED_HINT in page_text(at)
    assert task_now(at) == task
    assert "Task 1 / 10" in page_text(at)


# --- Result, saving and the tick (K R6, K R7, KA7–KA9) ---


def test_7_correct_2_wrong_1_skipped_shows_7_of_10_and_is_saved():
    at = complete_round(practising("M4", "multiplication", "Hard"), correct=7, wrong=2, skipped=1)
    assert metrics(at)["Correct"] == "7 / 10"
    saved = knowledge_db.list_rounds()
    assert [(r.trick_id, r.level, r.correct) for r in saved] == [("M4", "Hard", 7)]
    assert at.button(key="kn_again")
    assert at.button(key="kn_to_trick")


def test_completed_times_11_round_shows_a_tick_only_next_to_times_11():
    at = complete_round(practising("M4", "multiplication"), correct=3, skipped=7)
    click(at, "kn_to_trick")
    assert "Times 11" in page_text(at)
    click(at, "kn_back")
    for trick_id in MULTIPLICATION_IDS:
        assert trick_label(at, trick_id).endswith("✓") == (trick_id == "M4"), trick_id


def test_tick_is_still_there_after_a_restart():
    complete_round(practising("M4", "multiplication"), skipped=10)
    at = open_knowledge()  # a new session on the same database file
    click(at, "kn_category_multiplication")
    assert trick_label(at, "M4").endswith("✓")
    assert not trick_label(at, "M5").endswith("✓")


def test_leaving_a_round_after_5_tasks_saves_nothing_and_shows_no_tick():
    at = complete_round(practising("M4", "multiplication"), correct=5)
    click(at, "kn_leave")
    assert knowledge_db.list_rounds() == []
    assert "Times 11" in page_text(at)  # back on the trick screen
    click(at, "kn_back")
    assert not trick_label(at, "M4").endswith("✓")


def test_switching_tab_during_a_round_saves_nothing():
    at = complete_round(practising(), correct=5)
    go_to(at, "Tests")
    go_to(at, "Knowledge")
    assert knowledge_db.list_rounds() == []
    assert "kn_round" not in at.session_state


def test_practise_again_starts_a_new_round_with_the_same_trick_and_level():
    at = complete_round(practising("M4", "multiplication", "Medium"), skipped=10)
    click(at, "kn_again")
    practice_round = at.session_state["kn_round"]
    assert (practice_round.trick_id, practice_round.level) == ("M4", "Medium")
    assert practice_round.attempts == ()
    assert "Task 1 / 10" in page_text(at)


def test_back_to_trick_from_the_result():
    at = complete_round(practising("A1", "addition"), skipped=10)
    click(at, "kn_to_trick")
    assert "56 + 38 = 94" in page_text(at)


# --- Structure (AGENTS.md) ---


def test_knowledge_screens_contain_no_sql():
    source = (ROOT / "knowledge_ui.py").read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "SELECT " not in source
