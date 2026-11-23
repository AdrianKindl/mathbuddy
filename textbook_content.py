"""The Textbook catalogue: categories, articles, examples, tables, related tricks.

Supplied content as data (T R1), with the texts of "docs/textbook-brief.md"
and the decisions in specs/010-textbook.md. No Streamlit and no SQL. Nothing of
this is stored in the database.

`checks` lists the calculations behind an article's numbers in the format of
specs/010 (equations, comparisons and ≈ for rounded values). Tests verify each
one and that its numbers appear in the article (T R2).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Table:
    title: str
    subtitle: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Example:
    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Article:
    id: str
    name: str
    difficulty: str
    overview: str
    card_title: str
    body: tuple[str, ...]  # one paragraph, or the items of a list
    note: str | None
    examples: tuple[Example, ...]
    table: Table | None
    related: tuple[str, ...]  # trick ids from knowledge_content.py
    checks: tuple[str, ...]


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    articles: tuple[Article, ...]


def _article(
    id, name, difficulty, overview, card_title, body, *,
    note=None, examples=(), table=None, related=(), checks=(),
) -> Article:  # fmt: skip
    return Article(
        id, name, difficulty, overview, card_title, tuple(body), note,
        tuple(Example(title, tuple(lines)) for title, lines in examples),
        table, tuple(related), tuple(checks),
    )  # fmt: skip


# --- Basics ---

BASICS = (
    _article(
        "B1", "Order of operations", "Medium",
        "Brackets, exponents, multiplication/division, addition/subtraction – the universal order.",
        "Why the order matters",
        ["Without a shared order, the same expression could give different results. "
         "3 + 4 × 2 is 11, not 14, because multiplication comes before addition. "
         "The agreed order is: (1) brackets, from the inside out; (2) exponents, i.e. powers "
         "and roots; (3) multiplication and division, equal rank, left to right; (4) addition "
         "and subtraction, equal rank, left to right. A common mistake is to think "
         "multiplication always comes before division, or addition before subtraction. Each "
         "pair has equal rank and is worked from left to right."],
        note="Multiplication and division have equal rank – work left to right. The same holds "
        "for addition and subtraction. So 8 ÷ 2 × 4 = 16 (not 1): 8 ÷ 2 = 4, then 4 × 4 = 16. "
        "Likewise 10 − 3 + 2 = 9 (not 5).",
        examples=[("Calculate 3 + 4 × 2", [
            "Step 1: no brackets or exponents.",
            "Step 2: multiplication first: 4 × 2 = 8.",
            "Step 3: addition: 3 + 8 = 11.",
            "The result is 11, not 14.",
        ])],
        checks=["3 + 4 × 2 = 11", "4 × 2 = 8", "3 + 8 = 11", "8 ÷ 2 × 4 = 16", "8 ÷ 2 = 4",
                "4 × 4 = 16", "10 − 3 + 2 = 9"],
    ),
    _article(
        "B2", "Rules for negative numbers", "Medium",
        "How negative numbers behave in the four operations – and why minus times minus is plus.",
        "Rules for all four operations",
        [
            "Addition: adding a negative number is the same as subtracting its positive value. "
            "5 + (−3) = 5 − 3 = 2.",
            "Subtraction: subtracting a negative number is the same as adding. "
            "5 − (−3) = 5 + 3 = 8. Think of it as taking away a debt.",
            "Multiplication and division: equal signs give a positive result, different signs "
            "a negative one. (−4) × (−3) = +12 and (−4) × 3 = −12.",
            "Why minus times minus is plus: if 3 people each owe you 4 $, that is 12 $ of debt "
            "to you: (−4) × 3 = −12. If those 3 debts are removed, you gain 12 $: "
            "(−4) × (−3) = +12.",
        ],
        examples=[("Practical calculations", [
            "(−7) + (−5) = −12 (two debts add up).",
            "(−8) − (−3) = −8 + 3 = −5.",
            "(−6) × 4 = −24 (different signs → negative).",
            "(−20) ÷ (−5) = 4 (equal signs → positive).",
        ])],
        table=Table(
            "Sign rules", "Signs of products and quotients", ("Signs", "Result"),
            (("(+) × (+)", "+"), ("(+) × (−)", "−"), ("(−) × (+)", "−"), ("(−) × (−)", "+")),
        ),
        checks=["5 + (−3) = 5 − 3 = 2", "5 − (−3) = 5 + 3 = 8", "(−4) × (−3) = 12",
                "(−4) × 3 = −12", "(−7) + (−5) = −12", "(−8) − (−3) = −8 + 3 = −5",
                "(−6) × 4 = −24", "(−20) ÷ (−5) = 4"],
    ),
    _article(
        "B3", "Calculating with decimals", "Medium",
        "Adding, subtracting, multiplying and dividing decimals – and the decimal-point shift.",
        "The four operations with decimals",
        [
            "Addition and subtraction: line up the decimal points, then add or subtract as "
            "usual. Fill in trailing zeros if needed: 3.5 + 2.75 becomes 3.50 + 2.75 = 6.25.",
            "Multiplication: ignore the decimal points, multiply the whole numbers, count the "
            "decimal places in both factors and set the point. 1.2 × 0.3: 12 × 3 = 36, "
            "2 decimal places → 0.36.",
            "Powers of ten: dividing moves the point left (45.6 ÷ 10 = 4.56); multiplying "
            "moves it right (0.037 × 100 = 3.7).",
        ],
        note="Every decimal is a fraction (0.75 = 75/100 = 3/4) and every percentage is a "
        "decimal (12.5 % = 0.125). Switching between decimals, fractions and percentages is a "
        "core mental-math skill: if one form makes a calculation hard, switch to another.",
        examples=[("Multi-step calculation", [
            "Calculate 2.5 × 3.2 − 1.4.",
            "Step 1: 25 × 32 = 800, 2 decimal places → 8.00.",
            "Step 2: 8.00 − 1.4 = 6.6.",
        ])],
        checks=["3.5 + 2.75 = 3.50 + 2.75 = 6.25", "12 × 3 = 36", "1.2 × 0.3 = 0.36",
                "45.6 ÷ 10 = 4.56", "0.037 × 100 = 3.7", "0.75 = 75/100 = 3/4",
                "12.5 % = 0.125", "25 × 32 = 800", "2.5 × 3.2 = 8.00", "8.00 − 1.4 = 6.6"],
    ),
)

# --- Fractions ---

FRACTIONS = (
    _article(
        "F1", "Fractions, decimals and percentages", "Medium",
        "The reference: 1/2 to 1/12 with all conversions.",
        "Learn by heart",
        ["Knowing the common conversions between fractions, decimals and percentages saves a "
         "lot of time. These are the ones used most in mental math. Memorise the ones you meet "
         "most often and derive the rest."],
        note="Thirds (0.333…, 0.666…), sixths (0.1666…, 0.8333…) and twelfths (0.0833…) are "
        "repeating decimals. Round to the precision your task needs.",
        table=Table(
            "Common conversions", "Fraction · Decimal · Percent",
            ("Fraction", "Decimal", "Percent"),
            (
                ("1/2", "0.5", "50 %"), ("1/3", "0.333…", "33.3 %"),
                ("2/3", "0.666…", "66.7 %"), ("1/4", "0.25", "25 %"),
                ("3/4", "0.75", "75 %"), ("1/5", "0.2", "20 %"), ("2/5", "0.4", "40 %"),
                ("3/5", "0.6", "60 %"), ("4/5", "0.8", "80 %"),
                ("1/6", "0.1666…", "16.7 %"), ("5/6", "0.8333…", "83.3 %"),
                ("1/8", "0.125", "12.5 %"), ("3/8", "0.375", "37.5 %"),
                ("5/8", "0.625", "62.5 %"), ("7/8", "0.875", "87.5 %"),
                ("1/10", "0.1", "10 %"), ("1/12", "0.0833…", "8.3 %"),
            ),
        ),
    ),
    _article(
        "F2", "Comparing fractions", "Medium",
        "Cross-multiply to compare: a/b vs c/d → compare a × d with b × c.",
        "The cross-multiplication trick",
        ["To compare a/b and c/d without a common denominator, cross-multiply: work out "
         "a × d and b × c. If a × d > b × c, then a/b > c/d. This works because you are "
         "effectively comparing both fractions over the common denominator b × d."],
        examples=[("Compare 3/7 and 5/11", [
            "3 × 11 = 33 and 5 × 7 = 35.",
            "Since 33 < 35, 3/7 < 5/11.",
        ])],
        checks=["3 × 11 = 33", "5 × 7 = 35", "33 < 35", "3/7 < 5/11"],
    ),
    _article(
        "F3", "The fraction trap: 0 < x < 1", "Hard",
        "Squaring makes it smaller, the square root makes it bigger. (1/2)² = 1/4, but "
        "√(1/4) = 1/2.",
        "Reversed intuitions",
        ["For numbers between 0 and 1, our intuition about operations is reversed. Squaring "
         "makes them smaller, not bigger: (1/2)² = 1/4. Taking the square root makes them "
         "bigger, not smaller: √(1/4) = 1/2. Multiplying by a proper fraction also makes the "
         'result smaller, because you take "a part of a part".'],
        note="This is one of the most common traps in standardised tests and mental-math "
        "challenges. Whenever you see an exponent or a root, first check: is the number "
        "between 0 and 1?",
        examples=[("The ordering rule", [
            "Let x = 0.5.",
            "Then x² = 0.25 (smaller than x) and √x ≈ 0.707 (bigger than x).",
            "For every number with 0 < x < 1: x² < x < √x.",
        ])],
        checks=["(1/2)² = 1/4", "√(1/4) = 1/2", "0.5² = 0.25", "√(0.5) ≈ 0.707",
                "0.25 < 0.5 < 0.707"],
    ),
)

# --- Case interview ---

CASE_INTERVIEW = (
    _article(
        "C1", "Successive percentage changes", "Hard",
        "Chain the multipliers – 20 % up, then 10 % down = 1.20 × 0.90 = 1.08.",
        "Chained multipliers",
        ["For successive percentage changes, multiply the individual multipliers. A 20 % "
         "increase followed by a 10 % decrease gives 1.20 × 0.90 = 1.08, a net increase of "
         "8 %. Never add or subtract percentages that refer to different bases."],
        note="For small rates (under 10 %) you can add them as an approximation: "
        "3 % + 4 % + 2 % ≈ 9 % in total. The error is small because the cross terms "
        "(such as 0.03 × 0.04) are negligible.",
        examples=[("Three years of growth", [
            "Revenue grows by 10 %, then 20 %, then 5 %.",
            "Total multiplier: 1.10 × 1.20 × 1.05 = 1.386, a total increase of 38.6 % over "
            "three years.",
        ])],
        checks=["1.20 × 0.90 = 1.08", "3 % + 4 % + 2 % = 9 %", "1.10 × 1.20 × 1.05 = 1.386"],
    ),
    _article(
        "C2", "The rule of 72", "Medium",
        "72 ÷ growth rate ≈ doubling time.",
        "Doubling time in seconds",
        ["To estimate how long an investment or metric takes to double at a constant growth "
         "rate, divide 72 by the rate (as a whole number). At 8 % growth, doubling takes about "
         "72 ÷ 8 = 9 years. This works because ln(2) ≈ 0.693, and 72 is a handy approximation "
         "of 69.3 with many divisors."],
        note="For tripling time use 114 instead of 72. At 6 % growth: 114 ÷ 6 = 19 years to "
        "triple.",
        examples=[("Market growth", [
            "A market grows by 6 % per year.",
            "Doubling time: 72 ÷ 6 = 12 years.",
            "If the market is worth 10 bn $ today, it will be worth about 20 bn $ in 12 years.",
        ])],
        checks=["72 ÷ 8 = 9", "114 ÷ 6 = 19", "72 ÷ 6 = 12", "10 × 2 = 20"],
    ),
    _article(
        "C3", "Margin vs markup", "Hard",
        "Margin = markup / (1 + markup). Don't mix them up.",
        "Margin vs markup",
        ["Margin and markup both express profit, but on different bases. Margin = profit / "
         "revenue (profit as a share of the selling price). Markup = profit / cost (profit as "
         "a share of the cost). Conversion: margin = markup / (1 + markup), or equivalently "
         "markup = margin / (1 − margin)."],
        examples=[("Applied example", [
            "A product costs 60 $ and sells for 100 $.",
            "Profit = 40 $.",
            "Margin = 40 / 100 = 40 %.",
            "Markup = 40 / 60 = 66.7 %.",
            "Both describe the same 40 $ profit, measured against different bases.",
        ])],
        table=Table(
            "Margin to markup", "Margin and the matching markup", ("Margin", "Markup"),
            (("20 %", "25 %"), ("25 %", "33.3 %"), ("33.3 %", "50 %"), ("40 %", "66.7 %"),
             ("50 %", "100 %")),
        ),
        checks=["100 − 60 = 40", "40 / 100 = 40 %", "40 / 60 ≈ 66.7 %"],
    ),
    _article(
        "C4", "Percentage change", "Medium",
        "% change = (new − old) / old × 100.",
        "Always divide by the starting value",
        ["Percentage change = (new value − old value) / old value × 100. The denominator is "
         "always the original value. A positive result is an increase, a negative one a "
         "decrease. This is the formula used most often in case interviews."],
        note="Always use the OLD value as the base. If revenue falls from 100 m $ to 80 m $, "
        "the drop is 20 % (not 25 %). If it then rises back to 100 m $, that is a 25 % "
        "increase from 80 m $.",
        examples=[("Revenue change", [
            "Revenue rose from 80 m $ to 92 m $.",
            "Change = (92 − 80) / 80 × 100 = 12 / 80 × 100 = 15 % increase.",
        ])],
        checks=["(80 − 100) / 100 × 100 = −20", "(100 − 80) / 80 × 100 = 25",
                "(92 − 80) / 80 × 100 = 12 / 80 × 100 = 15"],
    ),
    _article(
        "C5", "Weighted averages", "Medium",
        "Average = Σ(weight × value) / Σ(weights).",
        "Not all data points are equal",
        ["A weighted average takes the relative importance (weight) of each value into "
         "account. Multiply each value by its weight, add up the products and divide by the "
         "total weight. This is essential for blended rates, portfolio returns and "
         "segment-weighted metrics."],
        note="In case interviews, always check whether segments have different weights before "
        "averaging. A simple average of segment margins can be very misleading when segment "
        "sizes differ a lot.",
        examples=[("Blended margin", [
            "Product A: 60 % of revenue at 30 % margin.",
            "Product B: 40 % of revenue at 20 % margin.",
            "Blended margin = 0.60 × 30 % + 0.40 × 20 % = 18 % + 8 % = 26 %.",
        ])],
        checks=["0.60 × 30 % + 0.40 × 20 % = 18 % + 8 % = 26 %"],
    ),
    _article(
        "C6", "The break-even equation", "Medium",
        "Q = fixed costs / (price − variable costs).",
        "Where revenue meets costs",
        ["The break-even point is where total revenue exactly equals total cost. Break-even "
         "quantity Q = fixed costs / (price per unit − variable cost per unit). The "
         "denominator (price − variable cost) is the contribution margin per unit: how much "
         "each unit sold contributes to covering fixed costs."],
        note="Interviewers often ask what happens when prices or costs change. A 10 % price "
        "increase on a 50 $ product raises the contribution margin by 5 $ (from 20 $ to 25 $) "
        "and lowers break-even by 20 % (from 25,000 to 20,000 units).",
        examples=[("Launching a new product", [
            "Fixed costs: 500,000 $.",
            "Price per unit: 50 $.",
            "Variable cost: 30 $.",
            "Contribution margin: 20 $.",
            "Break-even: 500,000 ÷ 20 = 25,000 units.",
        ])],
        checks=["50 − 30 = 20", "500,000 ÷ 20 = 25,000", "50 × 10 % = 5", "20 + 5 = 25",
                "500,000 ÷ 25 = 20,000", "(25,000 − 20,000) / 25,000 = 20 %"],
    ),
    _article(
        "C7", "Calculating with large numbers", "Medium",
        "K × K = M, M × K = B, M × M = T.",
        "Calculating with abbreviations",
        ["When working with large numbers, use abbreviations: K = thousand, M = million, "
         "B = billion, T = trillion. Multiplication rules: K × K = M, M × K = B, M × M = T, "
         "B × K = T. Focus on the coefficients and track the order of magnitude separately."],
        examples=[("Market size estimate", [
            "300 M people × 50 K $ average income = 300 × 50 × (M × K) = 15,000 B = 15 T $ GDP.",
            "Coefficients: 300 × 50 = 15,000.",
            "Magnitudes: M × K = B.",
            "So 15,000 B = 15 T $.",
        ])],
        table=Table(
            "Rules for large numbers", "Row × column", ("×", "K", "M", "B"),
            (("K", "M", "B", "T"), ("M", "B", "T", "—"), ("B", "T", "—", "—")),
        ),
        checks=["300 × 50 = 15,000"],
    ),
)

# --- Estimating & rounding ---

ESTIMATING = (
    _article(
        "E1", "Rounding & estimating", "Medium",
        "Round to the leading digits for fast, approximate results.",
        "Leading-digit strategy",
        ["Front-end estimation focuses on the leading (leftmost) digits of each number to get "
         "a quick approximate result. Round each number to its highest place value, do the "
         "operation and adjust if needed. It is the fastest way to a rough reference value."],
        note="For a single calculation, round to the nearest value. In chains of calculations, "
        "balance the rounding: round some numbers up and others down so the errors partly "
        "cancel out.",
        examples=[("Estimate 487 + 623", [
            "Round to hundreds: 500 + 600 = 1,100.",
            "The exact result is 1,110 – the estimate is very close.",
            "For more accuracy, adjust: the remainders are −13 + 23 = 10, so the refined "
            "estimate is 1,110.",
        ])],
        checks=["500 + 600 = 1,100", "487 + 623 = 1,110", "487 − 500 = −13", "623 − 600 = 23",
                "−13 + 23 = 10", "1,100 + 10 = 1,110"],
    ),
    _article(
        "E2", "Compatible numbers", "Medium",
        "Replace awkward values with nearby, easy ones.",
        "Easy substitutes",
        ["Compatible numbers are pairs that are easy to calculate in your head. Replace "
         "awkward numbers with nearby easy ones. When dividing, choose numbers that divide "
         "evenly. When multiplying, choose numbers ending in 0 or 5. The key is to pick "
         "substitutes close enough to the original to give a useful estimate."],
        examples=[
            ("Estimate 7,341 ÷ 83", [
                "Replace with 7,200 ÷ 80 = 90.",
                "The exact result is about 88.4 – the compatible-number estimate is excellent.",
            ]),
            ("Estimate 49 × 51", [
                "Both are close to 50: 50 × 50 = 2,500.",
                "The exact result is 2,499.",
            ]),
        ],
        related=["A3", "S3"],
        checks=["7,200 ÷ 80 = 90", "7,341 ÷ 83 ≈ 88.4", "50 × 50 = 2,500", "49 × 51 = 2,499"],
    ),
    _article(
        "E3", "Order of magnitude", "Medium",
        "Check the number of digits to catch big mistakes.",
        "Thinking in powers of ten",
        ['An order-of-magnitude check asks: "How many digits should the result have?" '
         "Multiplying a 3-digit number by a 2-digit number should give 4 or 5 digits. This kind "
         "of plausibility check catches errors where you are off by a factor of 10 or more."],
        note="In multiplication, the product of an m-digit and an n-digit number has either "
        "(m + n − 1) or (m + n) digits. In addition, the sum has as many digits as the larger "
        "number, or one more.",
        examples=[("Checking a product", [
            "You calculate 34 × 78 and get 26,520.",
            "Check: 2-digit × 2-digit should give a 3- or 4-digit result.",
            "26,520 has 5 digits – something is wrong.",
            "The correct result is 2,652.",
        ])],
        checks=["34 × 78 = 2,652", "26,520 = 2,652 × 10"],
    ),
    _article(
        "E4", "Casting out nines", "Hard",
        "Check calculations with the single-digit digit sum.",
        "The single-digit digit-sum check",
        ["Casting out nines is an old method for checking calculations. Add the digits of a "
         "number until you get a single digit (the digital root). For every correct "
         "multiplication, the digital root of the product equals the digital root of the "
         "product of the two digital roots. If they don't match, the calculation is wrong."],
        note="Casting out nines cannot detect errors that are multiples of 9 (such as swapped "
        "digits). It catches about 89 % of random single-digit errors – good, but not perfect.",
        examples=[("Check 47 × 83 = 3,901", [
            "Digital root of 47: 4 + 7 = 11 → 1 + 1 = 2.",
            "Digital root of 83: 8 + 3 = 11 → 1 + 1 = 2.",
            "Product of the roots: 2 × 2 = 4.",
            "Digital root of 3,901: 3 + 9 + 0 + 1 = 13 → 1 + 3 = 4.",
            "Both give 4, so the result is probably correct.",
        ])],
        checks=["4 + 7 = 11", "1 + 1 = 2", "8 + 3 = 11", "2 × 2 = 4", "3 + 9 + 0 + 1 = 13",
                "1 + 3 = 4", "47 × 83 = 3,901"],
    ),
)

CATEGORIES = (
    Category("basics", "Basics", BASICS),
    Category("fractions", "Fractions", FRACTIONS),
    Category("case_interview", "Case interview", CASE_INTERVIEW),
    Category("estimating", "Estimating & rounding", ESTIMATING),
)

_ARTICLES = {article.id: article for category in CATEGORIES for article in category.articles}
_CATEGORY_OF = {
    article.id: category for category in CATEGORIES for article in category.articles
}


def get_article(article_id: str) -> Article:
    """The article with this id. Raises KeyError for an unknown id."""
    return _ARTICLES[article_id]


def get_category(category_id: str) -> Category:
    return next(category for category in CATEGORIES if category.id == category_id)


def category_of(article_id: str) -> Category:
    return _CATEGORY_OF[article_id]
