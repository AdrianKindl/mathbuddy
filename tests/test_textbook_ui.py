"""Textbook screens in textbook_ui.py (stage 1), driven through AppTest (TA1–TA7).

AppTest does not run a browser, so these need a manual check in the PR: the look
of the tiles, cards, tags and tables, and text with "$" showing correctly.
"""

import random
from datetime import datetime, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import knowledge_db
from knowledge import skip_task, start_round

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
CASE_INTERVIEW = [
    ("C1", "Successive percentage changes", "Hard"),
    ("C2", "The rule of 72", "Medium"),
    ("C3", "Margin vs markup", "Hard"),
    ("C4", "Percentage change", "Medium"),
    ("C5", "Weighted averages", "Medium"),
    ("C6", "The break-even equation", "Medium"),
    ("C7", "Calculating with large numbers", "Medium"),
]
MULTIPLICATION_IDS = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]


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
    return at


def open_textbook():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    go_to(at, "Knowledge")
    return set_mode(at, "Textbook")


def open_article(article_id, category_id):
    at = open_textbook()
    click(at, f"tb_category_{category_id}")
    return click(at, f"tb_article_{article_id}")


def page_text(at):
    groups = (
        at.header, at.subheader, at.markdown, at.caption, at.text,
        at.success, at.info, at.warning, at.error,
    )  # fmt: skip
    return "\n".join(str(element.value) for group in groups for element in group)


def labels(at, prefix):
    return [button.label for button in at.button if (button.key or "").startswith(prefix)]


def save_completed_trick_round(trick_id):
    knowledge_db.init_db()
    practice_round = start_round(trick_id, "Easy", random.Random(1))
    for _ in range(10):
        practice_round, _ = skip_task(practice_round)
    knowledge_db.save_round(
        f"{trick_id}-done", practice_round, datetime(2026, 11, 21, 12, tzinfo=timezone.utc)
    )


# --- Toggle and overview (TA1) ---


def test_textbook_shows_its_overview_instead_of_coming_soon():
    at = open_textbook()
    assert "Coming soon" not in page_text(at)
    assert labels(at, "tb_category_") == [
        "Basics (3)",
        "Fractions (3)",
        "Case interview (7)",
        "Estimating & rounding (4)",
    ]


def test_tricks_is_still_the_first_mode():
    at = AppTest.from_file(APP, default_timeout=10).run()
    go_to(at, "Knowledge")
    assert at.button_group(key="kn_mode").value == "Tricks"
    assert labels(at, "kn_category_")


# --- Category screen (TA2) ---


def test_case_interview_lists_its_seven_articles_in_order():
    at = open_textbook()
    click(at, "tb_category_case_interview")
    assert "Case interview" in [header.value for header in at.header]
    assert labels(at, "tb_article_") == [f"{name} · {label}" for _, name, label in CASE_INTERVIEW]


@pytest.mark.parametrize("category_id", ["basics", "fractions", "case_interview", "estimating"])
def test_every_category_opens_and_back_returns_to_the_overview(category_id):
    at = open_textbook()
    click(at, f"tb_category_{category_id}")
    assert labels(at, "tb_article_")
    click(at, "tb_back")
    assert labels(at, "tb_category_")


# --- Article screen (TA3, TA4) ---


def test_order_of_operations_shows_overview_card_note_and_example():
    text = page_text(open_article("B1", "basics"))
    for part in (
        "Order of operations",
        "Overview",
        "Brackets, exponents, multiplication/division, addition/subtraction – the universal order.",
        "Why the order matters",
        "Multiplication and division have equal rank – work left to right.",
        "Calculate 3 + 4 × 2",
        "Step 2: multiplication first: 4 × 2 = 8.",
        "The result is 11, not 14.",
    ):
        assert part in text, part


def test_conversions_article_shows_all_17_table_rows():
    at = open_article("F1", "fractions")
    assert "Common conversions" in page_text(at)
    table = at.table[0].value
    assert list(table.columns) == ["Fraction", "Decimal", "Percent"]
    assert len(table) == 17
    assert list(table.iloc[0]) == ["1/2", "0.5", "50 %"]
    assert list(table.iloc[-1]) == ["1/12", "0.0833…", "8.3 %"]


def test_back_from_an_article_returns_to_its_category():
    at = open_article("C3", "case_interview")
    click(at, "tb_back")
    assert labels(at, "tb_article_")[0].startswith("Successive percentage changes")


# --- Navigation (TA5) ---


def test_previous_is_disabled_on_the_first_article_and_next_works():
    at = open_article("C1", "case_interview")
    assert at.button(key="tb_prev").disabled
    assert not at.button(key="tb_next").disabled
    assert "1 / 7" in page_text(at)
    click(at, "tb_next")
    assert "The rule of 72" in page_text(at)
    assert "2 / 7" in page_text(at)


def test_next_is_disabled_on_the_last_article():
    at = open_article("C7", "case_interview")
    assert at.button(key="tb_next").disabled
    assert not at.button(key="tb_prev").disabled
    assert "7 / 7" in page_text(at)


def test_practice_button_is_enabled_since_stage_2():
    """Stage 2 of spec 010 builds practice, so the button is no longer disabled."""
    at = open_article("B1", "basics")
    assert not at.button(key="tb_practice").disabled


# --- Related tricks (TA6) ---


def test_related_trick_opens_compatible_numbers_in_addition():
    at = open_article("E2", "estimating")
    assert labels(at, "tb_trick_") == [
        "Compatible numbers (Addition)",
        "Count up to a round number (Subtraction)",
    ]
    click(at, "tb_trick_A3")
    assert at.button_group(key="kn_mode").value == "Tricks"
    text = page_text(at)
    assert "Compatible numbers" in text
    assert "25 + 78 = 103" in text  # the trick screen, with its example
    click(at, "kn_back")
    assert labels(at, "kn_trick_")[0].startswith("Split one number")  # Addition


def test_articles_without_related_tricks_show_no_links():
    assert labels(open_article("B1", "basics"), "tb_trick_") == []


# --- Tricks mode unchanged (T R5, TA7) ---


def test_switching_to_textbook_and_back_keeps_the_tricks_screen_and_ticks():
    save_completed_trick_round("M4")
    at = AppTest.from_file(APP, default_timeout=10).run()
    go_to(at, "Knowledge")
    click(at, "kn_category_multiplication")
    before = labels(at, "kn_trick_")
    assert [label.endswith("✓") for label in before] == [t == "M4" for t in MULTIPLICATION_IDS]

    set_mode(at, "Textbook")
    click(at, "tb_category_basics")
    click(at, "tb_article_B2")
    set_mode(at, "Tricks")

    assert labels(at, "kn_trick_") == before  # same screen, same ✓ markers
    assert [saved.trick_id for saved in knowledge_db.list_rounds()] == ["M4"]


def test_switching_back_to_textbook_keeps_the_open_article():
    at = open_article("C5", "case_interview")
    set_mode(at, "Tricks")
    set_mode(at, "Textbook")
    assert "Weighted averages" in page_text(at)


# --- Structure (AGENTS.md) ---


def test_textbook_screens_contain_no_sql():
    source = (ROOT / "textbook_ui.py").read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "SELECT " not in source
