"""The Textbook catalogue in textbook_content.py (T R1, T R2, T R4, TA1–TA4)."""

import math
import re
from fractions import Fraction
from pathlib import Path

import pytest

from knowledge_content import get_trick
from textbook_content import CATEGORIES, get_article

ROOT = Path(__file__).resolve().parent.parent

# From "docs/textbook-brief.md", copied on purpose rather than imported.
CATALOGUE = {
    "Basics": [
        ("B1", "Order of operations", "Medium"),
        ("B2", "Rules for negative numbers", "Medium"),
        ("B3", "Calculating with decimals", "Medium"),
    ],
    "Fractions": [
        ("F1", "Fractions, decimals and percentages", "Medium"),
        ("F2", "Comparing fractions", "Medium"),
        ("F3", "The fraction trap: 0 < x < 1", "Hard"),
    ],
    "Case interview": [
        ("C1", "Successive percentage changes", "Hard"),
        ("C2", "The rule of 72", "Medium"),
        ("C3", "Margin vs markup", "Hard"),
        ("C4", "Percentage change", "Medium"),
        ("C5", "Weighted averages", "Medium"),
        ("C6", "The break-even equation", "Medium"),
        ("C7", "Calculating with large numbers", "Medium"),
    ],
    "Estimating & rounding": [
        ("E1", "Rounding & estimating", "Medium"),
        ("E2", "Compatible numbers", "Medium"),
        ("E3", "Order of magnitude", "Medium"),
        ("E4", "Casting out nines", "Hard"),
    ],
}
ALL_IDS = [article_id for articles in CATALOGUE.values() for article_id, _, _ in articles]

OVERVIEWS = {
    "B1": "Brackets, exponents, multiplication/division, addition/subtraction – the universal order.",
    "B2": "How negative numbers behave in the four operations – and why minus times minus is plus.",
    "B3": "Adding, subtracting, multiplying and dividing decimals – and the decimal-point shift.",
    "F1": "The reference: 1/2 to 1/12 with all conversions.",
    "F2": "Cross-multiply to compare: a/b vs c/d → compare a × d with b × c.",
    "F3": "Squaring makes it smaller, the square root makes it bigger. (1/2)² = 1/4, but √(1/4) = 1/2.",
    "C1": "Chain the multipliers – 20 % up, then 10 % down = 1.20 × 0.90 = 1.08.",
    "C2": "72 ÷ growth rate ≈ doubling time.",
    "C3": "Margin = markup / (1 + markup). Don't mix them up.",
    "C4": "% change = (new − old) / old × 100.",
    "C5": "Average = Σ(weight × value) / Σ(weights).",
    "C6": "Q = fixed costs / (price − variable costs).",
    "C7": "K × K = M, M × K = B, M × M = T.",
    "E1": "Round to the leading digits for fast, approximate results.",
    "E2": "Replace awkward values with nearby, easy ones.",
    "E3": "Check the number of digits to catch big mistakes.",
    "E4": "Check calculations with the single-digit digit sum.",
}  # fmt: skip

CARD_TITLES = {
    "B1": "Why the order matters", "B2": "Rules for all four operations",
    "B3": "The four operations with decimals", "F1": "Learn by heart",
    "F2": "The cross-multiplication trick", "F3": "Reversed intuitions",
    "C1": "Chained multipliers", "C2": "Doubling time in seconds", "C3": "Margin vs markup",
    "C4": "Always divide by the starting value", "C5": "Not all data points are equal",
    "C6": "Where revenue meets costs", "C7": "Calculating with abbreviations",
    "E1": "Leading-digit strategy", "E2": "Easy substitutes",
    "E3": "Thinking in powers of ten", "E4": "The single-digit digit-sum check",
}  # fmt: skip

EXAMPLE_TITLES = {
    "B1": ["Calculate 3 + 4 × 2"], "B2": ["Practical calculations"],
    "B3": ["Multi-step calculation"], "F1": [], "F2": ["Compare 3/7 and 5/11"],
    "F3": ["The ordering rule"], "C1": ["Three years of growth"], "C2": ["Market growth"],
    "C3": ["Applied example"], "C4": ["Revenue change"], "C5": ["Blended margin"],
    "C6": ["Launching a new product"], "C7": ["Market size estimate"],
    "E1": ["Estimate 487 + 623"], "E2": ["Estimate 7,341 ÷ 83", "Estimate 49 × 51"],
    "E3": ["Checking a product"], "E4": ["Check 47 × 83 = 3,901"],
}  # fmt: skip

WITH_NOTE = {"B1", "B3", "F1", "F3", "C1", "C2", "C4", "C5", "C6", "E1", "E3", "E4"}
TABLE_TITLES = {"B2": "Sign rules", "F1": "Common conversions", "C3": "Margin to markup",
                "C7": "Rules for large numbers"}  # fmt: skip
RELATED = {"E2": ("A3", "S3")}

F1_ROWS = [
    ("1/2", "0.5", "50 %"), ("1/3", "0.333…", "33.3 %"), ("2/3", "0.666…", "66.7 %"),
    ("1/4", "0.25", "25 %"), ("3/4", "0.75", "75 %"), ("1/5", "0.2", "20 %"),
    ("2/5", "0.4", "40 %"), ("3/5", "0.6", "60 %"), ("4/5", "0.8", "80 %"),
    ("1/6", "0.1666…", "16.7 %"), ("5/6", "0.8333…", "83.3 %"), ("1/8", "0.125", "12.5 %"),
    ("3/8", "0.375", "37.5 %"), ("5/8", "0.625", "62.5 %"), ("7/8", "0.875", "87.5 %"),
    ("1/10", "0.1", "10 %"), ("1/12", "0.0833…", "8.3 %"),
]  # fmt: skip


def all_articles():
    return [article for category in CATEGORIES for article in category.articles]


def article_text(article):
    """Every text of an article, as one string."""
    parts = [article.name, article.overview, article.card_title, *article.body, article.note or ""]
    for example in article.examples:
        parts += [example.title, *example.lines]
    if article.table:
        parts += [article.table.title, article.table.subtitle, *article.table.columns]
        parts += [cell for row in article.table.rows for cell in row]
    return "\n".join(parts)


# --- An independent checker for the check format in specs/010 ---

NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
PERCENT = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*%")


def _sqrt(x):
    if isinstance(x, Fraction):
        top, bottom = math.isqrt(x.numerator), math.isqrt(x.denominator)
        if top * top == x.numerator and bottom * bottom == x.denominator:
            return Fraction(top, bottom)
    return math.sqrt(x)


def value(expression):
    text = PERCENT.sub(r"(\1/100)", expression)
    text = NUMBER.sub(lambda m: f"F('{m.group().replace(',', '')}')", text)
    text = (text.replace("×", "*").replace("÷", "/").replace("−", "-")
            .replace("²", "**2").replace("√", "sqrt"))  # fmt: skip
    leftover = set(re.findall(r"[A-Za-z]+", text)) - {"F", "sqrt"}
    if leftover or not re.fullmatch(r"[\sA-Za-z'().\d+\-*/]*", text):
        raise ValueError(f"unexpected text in {expression!r}")
    return eval(text, {"F": Fraction, "sqrt": _sqrt})  # noqa: S307 - digits and operators only


def tolerance(right_side):
    """Half a unit of the last shown digit of the right side, for ≈."""
    last = list(PERCENT.finditer(right_side)) or list(NUMBER.finditer(right_side))
    number = last[-1].group(1) if last[-1].re is PERCENT else last[-1].group()
    decimals = len(number.split(".")[1]) if "." in number else 0
    unit = Fraction(1, 10**decimals) / (100 if last[-1].re is PERCENT else 1)
    return unit / 2


def holds(left, relation, right, right_text):
    if relation == "≈":
        return abs(left - right) <= tolerance(right_text) + 1e-12
    if relation == "=":
        if isinstance(left, float) or isinstance(right, float):
            return abs(left - right) < 1e-9
        return left == right
    return left < right if relation == "<" else left > right


def check(calculation):
    for part in calculation.split("; "):
        sides = re.split(r"\s(=|<|>|≈)\s", part)
        texts = sides[0::2]
        values = [value(side) for side in texts]
        for i, relation in enumerate(sides[1::2]):
            assert holds(values[i], relation, values[i + 1], texts[i + 1]), part


def numbers_of(text):
    return {m.group().replace(",", "") for m in NUMBER.finditer(text)}


def test_checker_rejects_wrong_calculations():
    for wrong in ["3 + 4 × 2 = 14", "40 / 60 ≈ 66.6 %", "(−4) × (−3) = −12", "√(0.5) ≈ 0.71 + 0.1"]:
        with pytest.raises(AssertionError):
            check(wrong)


def test_checker_accepts_the_formats_of_the_brief():
    check("8 ÷ 2 × 4 = 16")
    check("5 + (−3) = 5 − 3 = 2")
    check("1.10 × 1.20 × 1.05 = 1.386")
    check("0.60 × 30 % + 0.40 × 20 % = 26 %")
    check("40 / 60 ≈ 66.7 %")
    check("√(1/4) = 1/2; √(0.5) ≈ 0.707")
    check("33 < 35")


# --- Catalogue (TA1, TA2) ---


def test_four_categories_with_their_article_counts():
    assert [(c.name, len(c.articles)) for c in CATEGORIES] == [
        ("Basics", 3),
        ("Fractions", 3),
        ("Case interview", 7),
        ("Estimating & rounding", 4),
    ]


@pytest.mark.parametrize("category_name", list(CATALOGUE))
def test_articles_are_in_catalogue_order_with_names_and_labels(category_name):
    category = next(c for c in CATEGORIES if c.name == category_name)
    assert [(a.id, a.name, a.difficulty) for a in category.articles] == CATALOGUE[category_name]


def test_ids_are_unique_and_can_be_looked_up():
    assert len(set(ALL_IDS)) == len(ALL_IDS) == 17
    assert len({c.id for c in CATEGORIES}) == 4
    for article_id in ALL_IDS:
        assert get_article(article_id).id == article_id


@pytest.mark.parametrize("article_id", ALL_IDS)
def test_overview_card_and_example_titles_match_the_brief(article_id):
    article = get_article(article_id)
    assert article.overview == OVERVIEWS[article_id]
    assert article.card_title == CARD_TITLES[article_id]
    assert article.body and all(item.strip() for item in article.body)
    assert [example.title for example in article.examples] == EXAMPLE_TITLES[article_id]
    assert all(example.lines for example in article.examples)


@pytest.mark.parametrize("article_id", ALL_IDS)
def test_notes_tables_and_related_tricks_are_where_the_brief_has_them(article_id):
    article = get_article(article_id)
    assert bool(article.note) == (article_id in WITH_NOTE)
    assert (article.table.title if article.table else None) == TABLE_TITLES.get(article_id)
    if article.table:
        assert article.table.subtitle.strip()
    assert article.related == RELATED.get(article_id, ())


# --- B1 and F1, word for word (TA3, TA4) ---


def test_order_of_operations_matches_the_brief():
    article = get_article("B1")
    assert article.body == (
        "Without a shared order, the same expression could give different results. "
        "3 + 4 × 2 is 11, not 14, because multiplication comes before addition. "
        "The agreed order is: (1) brackets, from the inside out; (2) exponents, i.e. powers "
        "and roots; (3) multiplication and division, equal rank, left to right; (4) addition "
        "and subtraction, equal rank, left to right. A common mistake is to think "
        "multiplication always comes before division, or addition before subtraction. Each "
        "pair has equal rank and is worked from left to right.",
    )
    assert article.note == (
        "Multiplication and division have equal rank – work left to right. The same holds "
        "for addition and subtraction. So 8 ÷ 2 × 4 = 16 (not 1): 8 ÷ 2 = 4, then 4 × 4 = 16. "
        "Likewise 10 − 3 + 2 = 9 (not 5)."
    )
    assert article.examples[0].lines == (
        "Step 1: no brackets or exponents.",
        "Step 2: multiplication first: 4 × 2 = 8.",
        "Step 3: addition: 3 + 8 = 11.",
        "The result is 11, not 14.",
    )
    assert "3 + 4 × 2 = 11" in article.checks


def test_fractions_decimals_and_percentages_matches_the_brief():
    article = get_article("F1")
    assert article.body == (
        "Knowing the common conversions between fractions, decimals and percentages saves a "
        "lot of time. These are the ones used most in mental math. Memorise the ones you meet "
        "most often and derive the rest.",
    )
    assert article.note == (
        "Thirds (0.333…, 0.666…), sixths (0.1666…, 0.8333…) and twelfths (0.0833…) are "
        "repeating decimals. Round to the precision your task needs."
    )
    assert article.table.columns == ("Fraction", "Decimal", "Percent")
    assert [tuple(row) for row in article.table.rows] == F1_ROWS


# --- Correctness (T R2) ---


@pytest.mark.parametrize("row", F1_ROWS, ids=[row[0] for row in F1_ROWS])
def test_every_conversion_row_is_correct(row):
    fraction, decimal, percent = row
    exact = Fraction(fraction)
    shown_percent = Fraction(percent.removesuffix(" %"))
    if decimal.endswith("…"):  # a repeating decimal: its digits are the start of the value
        digits = decimal.removesuffix("…")
        start = Fraction(digits)
        assert start <= exact < start + Fraction(1, 10 ** len(digits.split(".")[1]))
        assert abs(exact * 100 - shown_percent) <= Fraction(1, 20)  # rounded to 0.1
    else:
        assert Fraction(decimal) == exact
        assert shown_percent == exact * 100


def test_sign_rules_table_is_correct():
    rows = get_article("B2").table.rows
    assert len(rows) == 4
    for signs, result in rows:
        first, second = re.findall(r"\(([+−])\)", signs)
        assert (result == "+") == (first == second), signs


def test_margin_to_markup_table_is_correct():
    rows = get_article("C3").table.rows
    assert [margin for margin, _ in rows] == ["20 %", "25 %", "33.3 %", "40 %", "50 %"]
    for margin_text, markup_text in rows:
        margin = Fraction(margin_text.removesuffix(" %")) / 100
        markup = Fraction(markup_text.removesuffix(" %")) / 100
        assert abs(margin / (1 - margin) - markup) <= Fraction(1, 1000)  # 0.1 point


def test_large_number_table_is_correct():
    table = get_article("C7").table
    powers = {"K": 3, "M": 6, "B": 9, "T": 12}
    names = {power: name for name, power in powers.items()}
    assert table.columns == ("×", "K", "M", "B")
    assert [row[0] for row in table.rows] == ["K", "M", "B"]
    for row in table.rows:
        for column, cell in zip(table.columns[1:], row[1:]):
            assert cell == names.get(powers[row[0]] + powers[column], "—"), (row[0], column)


@pytest.mark.parametrize("article_id", ALL_IDS)
def test_every_check_is_correct_and_belongs_to_the_article(article_id):
    article = get_article(article_id)
    if article_id != "F1":  # F1's numbers are all in its table, checked above
        assert article.checks, f"{article_id} has no checks"
    text_numbers = numbers_of(article_text(article))
    for calculation in article.checks:
        check(calculation)
        missing = numbers_of(calculation) - text_numbers
        assert not missing, f"{article_id}: {calculation} uses numbers not in the article {missing}"


# --- Related tricks (T R4) ---


def test_every_related_trick_exists():
    for article in all_articles():
        for trick_id in article.related:
            assert get_trick(trick_id)


def test_compatible_numbers_links_the_two_tricks_of_the_brief():
    related = [get_trick(trick_id) for trick_id in get_article("E2").related]
    assert [trick.name for trick in related] == ["Compatible numbers", "Count up to a round number"]


def test_content_module_has_no_streamlit_and_no_sql():
    source = (ROOT / "textbook_content.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", "SELECT "):
        assert forbidden not in source
