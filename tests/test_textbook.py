"""Textbook rules in textbook.py, stage 1: navigation (T R3)."""

from pathlib import Path

from textbook import neighbours, position

ROOT = Path(__file__).resolve().parent.parent


def test_previous_and_next_stay_within_the_category():
    assert neighbours("B1") == (None, "B2")
    assert neighbours("B3") == ("B2", None)  # not F1 of the next category
    assert neighbours("C4") == ("C3", "C5")
    assert neighbours("C7") == ("C6", None)
    assert neighbours("E1") == (None, "E2")


def test_position_within_the_category():
    assert position("B1") == (1, 3)
    assert position("C2") == (2, 7)
    assert position("E4") == (4, 4)


def test_rule_module_follows_the_design_rules():
    source = (ROOT / "textbook.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", ".now(", "time.time", "random.Random("):
        assert forbidden not in source
