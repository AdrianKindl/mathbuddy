"""The trick catalogue in knowledge_content.py (K R1, K R2, KA1–KA3, KA5)."""

import re
from fractions import Fraction
from pathlib import Path

import pytest

from knowledge_content import CATEGORIES, get_trick

ROOT = Path(__file__).resolve().parent.parent
DIFFICULTIES = {"Easy", "Medium", "Hard", "Extreme"}

# The catalogue from docs/knowledge-brief.md, copied on purpose rather than
# imported, so a wrong catalogue cannot pass by checking itself.
CATALOGUE = {
    "Addition": [
        ("A1", "Split one number", "Medium"),
        ("A2", "Split both numbers", "Medium"),
        ("A3", "Compatible numbers", "Medium"),
        ("A4", "Give and take", "Medium"),
        ("A5", "The 9 trick", "Medium–Extreme"),
    ],
    "Subtraction": [
        ("S1", "Split one number", "Medium"),
        ("S2", "Split both numbers", "Medium"),
        ("S3", "Count up to a round number", "Medium"),
        ("S4", "Compensate", "Medium"),
        ("S5", "Add the same to both", "Medium"),
        ("S6", "Avoid borrowing", "Medium"),
        ("S7", "Subtract from 1,000", "Medium"),
        ("S8", "Count up in steps", "Medium"),
    ],
    "Multiplication": [
        ("M1", "Times 5", "Medium"),
        ("M2", "Times 8", "Medium"),
        ("M3", "Times 9", "Medium"),
        ("M4", "Times 11", "Easy–Extreme"),
        ("M5", "Times 12", "Hard"),
        ("M6", "Times 13", "Hard"),
        ("M7", "Times 25", "Medium"),
        ("M8", "Times 99", "Medium"),
    ],
    "Division": [
        ("D1", "Divide by 5", "Medium"),
        ("D2", "Divide by 8", "Medium"),
        ("D3", "Cancel zeros", "Medium"),
        ("D4", "Simplify", "Medium"),
    ],
    "Square numbers": [
        ("Q1", "Between 10 and 25", "Extreme"),
        ("Q2", "Between 25 and 75", "Extreme"),
        ("Q3", "Between 75 and 125", "Extreme"),
        ("Q4", "Ending in 5", "Medium–Hard"),
        ("Q5", "Round to the nearest ten", "Hard"),
    ],
}

# The worked example equation(s) of every trick, from the brief.
EQUATIONS = {
    "A1": ["56 + 38 = 94"],
    "A2": ["123 + 291 = 414"],
    "A3": ["25 + 78 = 103"],
    "A4": ["585 + 242 = 827"],
    "A5": ["29 + 15 = 44", "299 + 146 = 445", "3,999 + 2,450 = 6,449"],
    "S1": ["72 − 51 = 21"],
    "S2": ["467 − 123 = 344"],
    "S3": ["100 − 47 = 53"],
    "S4": ["228 − 97 = 131"],
    "S5": ["94 − 18 = 76"],
    "S6": ["325 − 134 = 191"],
    "S7": ["1,000 − 728 = 272"],
    "S8": ["120 − 57 = 63"],
    "M1": ["8 × 5 = 40"],
    "M2": ["7 × 8 = 56"],
    "M3": ["12 × 9 = 108"],
    "M4": ["3 × 11 = 33", "17 × 11 = 187", "57 × 11 = 627", "243 × 11 = 2,673"],
    "M5": ["384 × 12 = 4,608"],
    "M6": ["437 × 13 = 5,681"],
    "M7": ["13 × 25 = 325"],
    "M8": ["7 × 99 = 693"],
    "D1": ["45 ÷ 5 = 9"],
    "D2": ["32 ÷ 8 = 4"],
    "D3": ["8,000 ÷ 200 = 40"],
    "D4": ["48 ÷ 8 = 6"],
    "Q1": ["19² = 361"],
    "Q2": ["47² = 2,209"],
    "Q3": ["96² = 9,216", "106² = 11,236"],
    "Q4": ["85² = 7,225", "205² = 42,025"],
    "Q5": ["83² = 6,889"],
}

VARIANT_LABELS = {
    "A5": [("9 to 99", "Medium"), ("199 to 999", "Hard"), ("1,999 to 9,999", "Extreme")],
    "M4": [("1 to 9", "Easy"), ("10 to 18", "Medium"), ("19 to 99", "Hard"),
           ("100 to 999", "Extreme")],
    "Q3": [("75 to 99", None), ("101 to 125", None)],
    "Q4": [("15 to 95", None), ("105 to 995", None)],
}  # fmt: skip

TRICKS_WITH_NOTES = ["A3", "A5", "S2", "S3", "S7", "M4", "D2"]
ALL_TRICK_IDS = [trick_id for tricks in CATALOGUE.values() for trick_id, _, _ in tricks]


def all_tricks():
    return [trick for category in CATEGORIES for trick in category.tricks]


# --- An independent checker for the calculation format in specs/009 ---

NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+|\d+")


def value(expression):
    """Evaluate an expression with + − × ÷ ( ) and ², exactly."""
    text = NUMBER.sub(lambda m: f"Fraction({int(m.group().replace(',', ''))})", expression)
    text = text.replace("×", "*").replace("÷", "/").replace("−", "-").replace("²", "**2")
    if not re.fullmatch(r"[\sFraction()\d+\-*/]*", text):
        raise ValueError(f"unexpected characters in {expression!r}")
    return eval(text, {"Fraction": Fraction})  # noqa: S307 - only digits and operators reach here


def check_part(part):
    """Assert one part of a calculation. Returns its final value."""
    if " & " in part:
        whole, pieces = part.split(" → ")
        assert sum(value(p) for p in pieces.split(" & ")) == value(whole), part
        return value(pieces.split(" & ")[-1])
    if " | " in part:
        pieces, result = part.split(" → ")
        places = pieces.split(" | ")
        total = sum(value(p) * 10 ** (len(places) - 1 - i) for i, p in enumerate(places))
        assert total == value(result), part
        return value(result)
    sides = re.split(r"\s(=|<|>)\s", part)
    values = [value(side) for side in sides[0::2]]
    for left, relation, right in zip(values, sides[1::2], values[1:]):
        assert {"=": left == right, "<": left < right, ">": left > right}[relation], part
    return values[-1]


def check_calculation(calculation):
    results = [check_part(part) for part in calculation.split("; ")]
    return results[-1]


def test_checker_rejects_wrong_calculations():
    for wrong in ["56 + 30 = 87", "38 → 30 & 9", "3 | 14 | 20 | 8 → 4,609", "20 > 30"]:
        with pytest.raises(AssertionError):
            check_calculation(wrong)


def test_checker_accepts_the_brief_notation():
    assert check_calculation("38 → 30 & 8") == 8
    assert check_calculation("2 | 2+4 | 4+3 | 3 → 2,673") == 2673
    assert check_calculation("200 + 100 = 300; 20 + 90 = 110; 3 + 1 = 4") == 4
    assert check_calculation("384 = 0384") == 384


# --- Catalogue (KA1, KA2) ---


def test_five_categories_with_their_trick_counts():
    assert [(c.name, len(c.tricks)) for c in CATEGORIES] == [
        ("Addition", 5),
        ("Subtraction", 8),
        ("Multiplication", 8),
        ("Division", 4),
        ("Square numbers", 5),
    ]


@pytest.mark.parametrize("category_name", list(CATALOGUE))
def test_tricks_are_in_catalogue_order_with_names_and_labels(category_name):
    category = next(c for c in CATEGORIES if c.name == category_name)
    assert [(t.id, t.name, t.difficulty) for t in category.tricks] == CATALOGUE[category_name]


def test_addition_subtitle():
    assert CATEGORIES[0].subtitle == "Addition tricks"


def test_every_category_has_an_id_and_a_subtitle():
    assert all(category.id and category.subtitle for category in CATEGORIES)
    assert len({category.id for category in CATEGORIES}) == len(CATEGORIES)


def test_trick_ids_are_unique_and_can_be_looked_up():
    assert len(set(ALL_TRICK_IDS)) == len(ALL_TRICK_IDS) == 30
    for trick_id in ALL_TRICK_IDS:
        assert get_trick(trick_id).id == trick_id


def test_difficulty_labels_are_single_or_a_range():
    for trick in all_tricks():
        assert set(trick.difficulty.split("–")) <= DIFFICULTIES, trick.id


# --- Trick screens (KA3) ---


def test_split_one_number_matches_the_brief():
    trick = get_trick("A1")
    assert [example.equation for example in trick.examples] == ["56 + 38 = 94"]
    steps = trick.examples[0].steps
    assert [(step.text, step.calculation) for step in steps] == [
        ("Split the smaller number", "38 → 30 & 8"),
        ("Add the tens", "56 + 30 = 86"),
        ("Add the ones", "86 + 8 = 94"),
    ]


@pytest.mark.parametrize("trick_id", ALL_TRICK_IDS)
def test_every_trick_has_text_examples_and_steps(trick_id):
    trick = get_trick(trick_id)
    assert trick.description.strip()
    assert trick.examples
    for example in trick.examples:
        assert example.label.strip()
        assert example.steps
        assert all(step.text.strip() and step.calculation.strip() for step in example.steps)


@pytest.mark.parametrize("trick_id", ALL_TRICK_IDS)
def test_example_equations_match_the_brief(trick_id):
    assert [example.equation for example in get_trick(trick_id).examples] == EQUATIONS[trick_id]


@pytest.mark.parametrize("trick_id", list(VARIANT_LABELS))
def test_variant_tricks_have_one_card_per_variant(trick_id):
    examples = get_trick(trick_id).examples
    expected = VARIANT_LABELS[trick_id]
    assert [example.label for example in examples] == [label for label, _ in expected]
    for example, (_, difficulty) in zip(examples, expected):
        if difficulty is not None:
            assert example.difficulty == difficulty


@pytest.mark.parametrize("trick_id", TRICKS_WITH_NOTES)
def test_tricks_with_a_note_in_the_brief_have_one(trick_id):
    assert get_trick(trick_id).note


# --- Correctness (K R2, KA5) ---


@pytest.mark.parametrize("trick_id", ALL_TRICK_IDS)
def test_every_example_and_step_calculation_is_correct(trick_id):
    for example in get_trick(trick_id).examples:
        result = check_calculation(example.equation)
        for step in example.steps:
            check_calculation(step.calculation)
        assert check_calculation(example.steps[-1].calculation) == result, (
            f"{trick_id}: the steps of {example.equation} do not end with its result"
        )


def test_content_module_has_no_streamlit_and_no_sql():
    source = (ROOT / "knowledge_content.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", "SELECT "):
        assert forbidden not in source
