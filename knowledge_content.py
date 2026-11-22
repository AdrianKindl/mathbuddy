"""The Knowledge catalogue: categories, tricks, examples, steps and practice ranges.

Supplied content as data (K R1), taken from docs/knowledge-brief.md with the
decisions in specs/009-knowledge.md. No Streamlit and no SQL. Nothing of this
is stored in the database.

Step calculations use the format of specs/009: equations and comparisons
(`56 + 30 = 86`), splits (`38 → 30 & 8`) and place-value combinations
(`3 | 14 | 20 | 8 → 4,608`), several separated by "; ". Tests check every one.

Practice ranges: `generator` names the rule in knowledge.py that builds a task,
and `practice` gives its numbers per level. A range is (low, high) or
(low, high, step), all bounds inclusive.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Step:
    text: str
    calculation: str


@dataclass(frozen=True)
class Example:
    label: str  # the range the example belongs to, e.g. "9 to 99"
    difficulty: str
    equation: str
    steps: tuple[Step, ...]


@dataclass(frozen=True)
class Trick:
    id: str
    name: str
    difficulty: str
    description: str
    examples: tuple[Example, ...]
    note: str | None
    generator: str
    practice: dict = field(hash=False)


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    subtitle: str
    tricks: tuple[Trick, ...]


def _example(label: str, difficulty: str, equation: str, *steps: tuple[str, str]) -> Example:
    return Example(label, difficulty, equation, tuple(Step(text, calc) for text, calc in steps))


def _trick(id, name, difficulty, description, examples, generator, practice, note=None) -> Trick:
    return Trick(id, name, difficulty, description, tuple(examples), note, generator, practice)


# --- Addition ---

ADDITION = (
    _trick(
        "A1", "Split one number", "Medium",
        "Learn how to add faster by splitting the smaller number into tens and ones.",
        [_example(
            "Two-digit numbers", "Medium", "56 + 38 = 94",
            ("Split the smaller number", "38 → 30 & 8"),
            ("Add the tens", "56 + 30 = 86"),
            ("Add the ones", "86 + 8 = 94"),
        )],
        "sum_pair",
        {
            "Easy": {"a": (11, 49), "b": (11, 49)},
            "Medium": {"a": (20, 99), "b": (20, 99)},
            "Hard": {"a": (100, 999), "b": (20, 99)},
            "Pro": {"a": (100, 999), "b": (100, 999)},
        },
    ),
    _trick(
        "A2", "Split both numbers", "Medium",
        "Learn how to add from left to right by splitting both numbers into place values.",
        [_example(
            "Three-digit numbers", "Medium", "123 + 291 = 414",
            ("Split both numbers into place values", "123 → 100 & 20 & 3; 291 → 200 & 90 & 1"),
            ("Add the matching places", "200 + 100 = 300; 20 + 90 = 110; 3 + 1 = 4"),
            ("Add the results", "300 + 110 + 4 = 414"),
        )],
        "sum_pair",
        {
            "Easy": {"a": (10, 99), "b": (10, 99)},
            "Medium": {"a": (100, 499), "b": (100, 499)},
            "Hard": {"a": (100, 999), "b": (100, 999)},
            "Pro": {"a": (1000, 9999), "b": (1000, 9999)},
        },
    ),
    _trick(
        "A3", "Compatible numbers", "Medium",
        "Learn how to find a part of one number that makes a round number with the other.",
        [_example(
            "Two-digit numbers", "Medium", "25 + 78 = 103",
            ("Find the part that makes a round number", "25 + 75 = 100"),
            ("Take that part away from the other number", "78 − 75 = 3"),
            ("Add the rest", "100 + 3 = 103"),
        )],
        "compatible",
        {
            "Easy": {"a": (25, 75, 25), "whole": 100, "extra": (1, 9)},
            "Medium": {"a": (10, 99), "whole": 100, "extra": (1, 20)},
            "Hard": {"a": (100, 975, 25), "whole": 1000, "extra": (1, 99)},
            "Pro": {"a": (100, 999), "whole": 1000, "extra": (1, 999)},
        },
        note="Works best when the round number is a large multiple of 10.",
    ),
    _trick(
        "A4", "Give and take", "Medium",
        "Learn how to round one number up, add, then take the extra away again.",
        [_example(
            "Three-digit numbers", "Medium", "585 + 242 = 827",
            ("Round one number up to a round number", "585 + 15 = 600"),
            ("Add the other number", "600 + 242 = 842"),
            ("Take away what you added", "842 − 15 = 827"),
        )],
        "give_take",
        {
            "Easy": {"a": (10, 99), "unit": 10, "below": 4, "b": (10, 99)},
            "Medium": {"a": (100, 999), "unit": 100, "below": 25, "b": (100, 999)},
            "Hard": {"a": (100, 999), "unit": 100, "below": 50, "b": (100, 999)},
            "Pro": {"a": (1000, 9999), "unit": 1000, "below": 50, "b": (1000, 9999)},
        },
    ),
    _trick(
        "A5", "The 9 trick", "Medium–Extreme",
        "Learn how to add a number ending in 9 by adding 1, adding, then taking the 1 away.",
        [
            _example(
                "9 to 99", "Medium", "29 + 15 = 44",
                ("Add 1 to the number ending in 9", "29 + 1 = 30"),
                ("Add the other number", "30 + 15 = 45"),
                ("Take the 1 away again", "45 − 1 = 44"),
            ),
            _example(
                "199 to 999", "Hard", "299 + 146 = 445",
                ("Add 1 to make a round hundred", "299 + 1 = 300"),
                ("Add the other number", "300 + 146 = 446"),
                ("Take the 1 away again", "446 − 1 = 445"),
            ),
            _example(
                "1,999 to 9,999", "Extreme", "3,999 + 2,450 = 6,449",
                ("Add 1 to make a round thousand", "3,999 + 1 = 4,000"),
                ("Add the other number", "4,000 + 2,450 = 6,450"),
                ("Take the 1 away again", "6,450 − 1 = 6,449"),
            ),
        ],
        "nine",
        {
            "Easy": {"a": (19, 89, 10), "b": (1, 9)},
            "Medium": {"a": (19, 89, 10), "b": (10, 99)},
            "Hard": {"a": (199, 999, 100), "b": (100, 999)},
            "Pro": {"a": (1999, 9999, 1000), "b": (1000, 9999)},
        },
        note="There are variants depending on how many 9s the number ends with.",
    ),
)

# --- Subtraction ---

SUBTRACTION = (
    _trick(
        "S1", "Split one number", "Medium",
        "Learn how to subtract by splitting the number you subtract into tens and ones.",
        [_example(
            "Two-digit numbers", "Medium", "72 − 51 = 21",
            ("Split the number you subtract", "51 → 50 & 1"),
            ("Subtract the tens", "72 − 50 = 22"),
            ("Subtract the ones", "22 − 1 = 21"),
        )],
        "difference",
        {
            "Easy": {"a": (10, 99), "b": (1, 9)},
            "Medium": {"a": (10, 99), "b": (10, 99)},
            "Hard": {"a": (100, 999), "b": (10, 99)},
            "Pro": {"a": (100, 999), "b": (100, 999)},
        },
    ),
    _trick(
        "S2", "Split both numbers", "Medium",
        "Learn how to subtract place by place.",
        [_example(
            "Three-digit numbers", "Medium", "467 − 123 = 344",
            ("Split both numbers into place values", "467 → 400 & 60 & 7; 123 → 100 & 20 & 3"),
            ("Subtract place by place", "400 − 100 = 300; 60 − 20 = 40; 7 − 3 = 4"),
            ("Add the results", "300 + 40 + 4 = 344"),
        )],
        "no_borrow",
        {"Easy": {"digits": 2}, "Medium": {"digits": 3}, "Hard": {"digits": 4},
         "Pro": {"digits": 5}},
        note="Only works when every digit of the larger number is at least as big as the "
        "matching digit of the smaller one. Otherwise use Avoid borrowing.",
    ),
    _trick(
        "S3", "Count up to a round number", "Medium",
        "Learn how to subtract from a round number by counting up from the smaller number.",
        [_example(
            "From a round number", "Medium", "100 − 47 = 53",
            ("Count up to the next ten", "47 + 3 = 50"),
            ("Count up to the round number", "50 + 50 = 100"),
            ("Add what you counted", "3 + 50 = 53"),
        )],
        "difference",
        {
            "Easy": {"a": (100, 100), "b": (10, 99)},
            "Medium": {"a": (200, 900, 100), "b": (10, 999)},
            "Hard": {"a": (1000, 1000), "b": (100, 999)},
            "Pro": {"a": (2000, 9000, 1000), "b": (100, 9999)},
        },
        note="Best when the first number is a round multiple of 10 (100, 1,000 …).",
    ),
    _trick(
        "S4", "Compensate", "Medium",
        "Learn how to subtract a round number, then add back the difference.",
        [_example(
            "Three-digit minus two-digit", "Medium", "228 − 97 = 131",
            ("Pick a round number above the number you subtract", "97 + 3 = 100"),
            ("Subtract the round number", "228 − 100 = 128"),
            ("Add the difference back", "128 + 3 = 131"),
        )],
        "difference",
        {
            "Easy": {"a": (10, 99), "b": (18, 98), "b_mod": 10, "b_ends": (8, 9)},
            "Medium": {"a": (100, 999), "b": (10, 99), "b_mod": 10, "b_ends": (7, 8, 9)},
            "Hard": {"a": (100, 999), "b": (197, 998), "b_mod": 100, "b_ends": (97, 98, 99)},
            "Pro": {"a": (1000, 9999), "b": (100, 999), "b_mod": 100,
                    "b_ends": (95, 96, 97, 98, 99)},
        },
    ),
    _trick(
        "S5", "Add the same to both", "Medium",
        "Learn how to add the same amount to both numbers so the second becomes round.",
        [_example(
            "Two-digit numbers", "Medium", "94 − 18 = 76",
            ("Make the second number round", "18 + 2 = 20"),
            ("Add the same to the first number", "94 + 2 = 96"),
            ("Subtract", "96 − 20 = 76"),
        )],
        "difference",
        {
            "Easy": {"a": (10, 99), "b": (10, 98), "b_mod": 10, "b_ends": (8, 9)},
            "Medium": {"a": (10, 99), "b": (10, 98), "b_mod": 10, "b_ends": (6, 7, 8, 9)},
            "Hard": {"a": (100, 999), "b": (10, 99), "b_mod": 10, "b_ends": (5, 6, 7, 8, 9)},
            "Pro": {"a": (100, 999), "b": (100, 998), "b_mod": 100,
                    "b_ends": (95, 96, 97, 98, 99)},
        },
    ),
    _trick(
        "S6", "Avoid borrowing", "Medium",
        "Learn how to make the number you subtract smaller where you would need to borrow, "
        "then correct.",
        [_example(
            "Three-digit numbers", "Medium", "325 − 134 = 191",
            ("Split both numbers", "325 → 300 & 20 & 5; 134 → 100 & 30 & 4"),
            ("Find the place that would need borrowing", "20 < 30"),
            ("Lower that place in the number you subtract", "134 − 10 = 124"),
            ("Subtract without borrowing", "325 − 124 = 201"),
            ("Subtract what you removed", "201 − 10 = 191"),
        )],
        "borrow",
        {
            "Easy": {"digits": 2, "places": (0,), "borrows": (1,)},
            "Medium": {"digits": 3, "places": (0, 1), "borrows": (1,)},
            "Hard": {"digits": 3, "places": (0, 1), "borrows": (2,)},
            "Pro": {"digits": 4, "places": (0, 1, 2), "borrows": (1, 2)},
        },
    ),
    _trick(
        "S7", "Subtract from 1,000", "Medium",
        "Learn how to subtract from 1,000 by taking every digit from 9 and the last from 10.",
        [_example(
            "Three-digit numbers", "Medium", "1,000 − 728 = 272",
            ("Take the first digit from 9", "9 − 7 = 2"),
            ("Take the next digit from 9", "9 − 2 = 7"),
            ("Take the last digit from 10", "10 − 8 = 2"),
            ("Put the digits together", "2 | 7 | 2 → 272"),
        )],
        "difference",
        {
            "Easy": {"a": (100, 100), "b": (11, 99)},
            "Medium": {"a": (1000, 1000), "b": (101, 999)},
            "Hard": {"a": (10_000, 10_000), "b": (1001, 9999)},
            "Pro": {"a": (100_000, 100_000), "b": (10_001, 99_999)},
        },
        note="If the number ends in 0, drop the 0 on both sides first, then add it back: "
        "1,000 − 730 → 100 − 73 = 27 → 270.",
    ),
    _trick(
        "S8", "Count up in steps", "Medium",
        "Learn how to count up from the smaller number to the larger one via round numbers.",
        [_example(
            "Three-digit minus two-digit", "Medium", "120 − 57 = 63",
            ("Count up to the next ten", "57 + 3 = 60"),
            ("Count up to the next hundred", "60 + 40 = 100"),
            ("Count up to the first number", "100 + 20 = 120"),
            ("Add the steps", "3 + 40 + 20 = 63"),
        )],
        "difference",
        {
            "Easy": {"a": (10, 99), "b": (10, 99), "cross": 10},
            "Medium": {"a": (101, 199), "b": (10, 99)},
            "Hard": {"a": (100, 999), "b": (100, 999), "cross": 100},
            "Pro": {"a": (1000, 9999), "b": (100, 999)},
        },
    ),
)

# --- Multiplication ---

MULTIPLICATION = (
    _trick(
        "M1", "Times 5", "Medium",
        "Learn how to multiply by 5 by halving, then multiplying by 10.",
        [_example(
            "One-digit numbers", "Medium", "8 × 5 = 40",
            ("Halve the number", "8 ÷ 2 = 4"),
            ("Times 10", "4 × 10 = 40"),
        )],
        "times",
        {
            "Easy": {"factor": 5, "a": (2, 20, 2)},
            "Medium": {"factor": 5, "a": (22, 98, 2)},
            "Hard": {"factor": 5, "a": (11, 99)},
            "Pro": {"factor": 5, "a": (100, 999)},
        },
    ),
    _trick(
        "M2", "Times 8", "Medium",
        "Learn how to multiply by 8 by doubling three times.",
        [_example(
            "One-digit numbers", "Medium", "7 × 8 = 56",
            ("Double once", "7 × 2 = 14"),
            ("Double again", "14 × 2 = 28"),
            ("Double a third time", "28 × 2 = 56"),
        )],
        "times",
        {
            "Easy": {"factor": 8, "a": (2, 12)},
            "Medium": {"factor": 8, "a": (13, 50)},
            "Hard": {"factor": 8, "a": (51, 150)},
            "Pro": {"factor": 8, "a": (151, 999)},
        },
    ),
    _trick(
        "M3", "Times 9", "Medium",
        "Learn how to multiply by 9 by multiplying by 10, then subtracting the number.",
        [_example(
            "Two-digit numbers", "Medium", "12 × 9 = 108",
            ("Times 10", "12 × 10 = 120"),
            ("Subtract the number", "120 − 12 = 108"),
        )],
        "times",
        {
            "Easy": {"factor": 9, "a": (2, 12)},
            "Medium": {"factor": 9, "a": (13, 99)},
            "Hard": {"factor": 9, "a": (100, 999)},
            "Pro": {"factor": 9, "a": (1000, 9999)},
        },
    ),
    _trick(
        "M4", "Times 11", "Easy–Extreme",
        "Learn how to multiply by 11 by writing digit sums between the digits.",
        [
            _example(
                "1 to 9", "Easy", "3 × 11 = 33",
                ("Write the digit twice", "3 | 3 → 33"),
            ),
            _example(
                "10 to 18", "Medium", "17 × 11 = 187",
                ("Add the two digits", "1 + 7 = 8"),
                ("Put the sum between the digits", "1 | 8 | 7 → 187"),
            ),
            _example(
                "19 to 99", "Hard", "57 × 11 = 627",
                ("Add the two digits", "5 + 7 = 12"),
                ("Write the ones of the sum in the middle and carry 1 to the left",
                 "5 | 12 | 7 → 627"),
            ),
            _example(
                "100 to 999", "Extreme", "243 × 11 = 2,673",
                ("Add the neighbouring digits", "2 + 4 = 6; 4 + 3 = 7"),
                ("Keep the outer digits and write the sums between them",
                 "2 | 2+4 | 4+3 | 3 → 2,673"),
            ),
        ],
        "times",
        {
            "Easy": {"factor": 11, "a": (1, 9)},
            "Medium": {"factor": 11, "a": (10, 99), "digit_sum": (1, 9)},
            "Hard": {"factor": 11, "a": (10, 99), "digit_sum": (10, 18)},
            "Pro": {"factor": 11, "a": (100, 999)},
        },
        note="Which variant you use depends on the size of the number. If a sum is 10 or "
        "more, keep its ones digit and carry 1 to the left.",
    ),
    _trick(
        "M5", "Times 12", "Hard",
        "Learn how to multiply by 12 by doubling each digit and adding its right neighbour.",
        [_example(
            "Three-digit numbers", "Hard", "384 × 12 = 4,608",
            ("Put a 0 in front", "384 = 0384"),
            ("Double each digit and add its right neighbour",
             "0 × 2 + 3 = 3; 3 × 2 + 8 = 14; 8 × 2 + 4 = 20; 4 × 2 + 0 = 8"),
            ("Combine the results from the right, carrying", "3 | 14 | 20 | 8 → 4,608"),
        )],
        "times",
        {
            "Easy": {"factor": 12, "a": (2, 12)},
            "Medium": {"factor": 12, "a": (13, 99)},
            "Hard": {"factor": 12, "a": (100, 999)},
            "Pro": {"factor": 12, "a": (1000, 9999)},
        },
    ),
    _trick(
        "M6", "Times 13", "Hard",
        "Learn how to multiply by 13 by tripling each digit and adding its right neighbour.",
        [_example(
            "Three-digit numbers", "Hard", "437 × 13 = 5,681",
            ("Put a 0 in front", "437 = 0437"),
            ("Triple each digit and add its right neighbour",
             "0 × 3 + 4 = 4; 4 × 3 + 3 = 15; 3 × 3 + 7 = 16; 7 × 3 + 0 = 21"),
            ("Combine the results from the right, carrying", "4 | 15 | 16 | 21 → 5,681"),
        )],
        "times",
        {
            "Easy": {"factor": 13, "a": (2, 12)},
            "Medium": {"factor": 13, "a": (13, 99)},
            "Hard": {"factor": 13, "a": (100, 999)},
            "Pro": {"factor": 13, "a": (1000, 9999)},
        },
    ),
    _trick(
        "M7", "Times 25", "Medium",
        "Learn how to multiply by 25 by multiplying by 100, then halving twice.",
        [_example(
            "Two-digit numbers", "Medium", "13 × 25 = 325",
            ("Times 100", "13 × 100 = 1,300"),
            ("Halve", "1,300 ÷ 2 = 650"),
            ("Halve again", "650 ÷ 2 = 325"),
        )],
        "times",
        {
            "Easy": {"factor": 25, "a": (2, 12)},
            "Medium": {"factor": 25, "a": (13, 40)},
            "Hard": {"factor": 25, "a": (41, 199)},
            "Pro": {"factor": 25, "a": (200, 999)},
        },
    ),
    _trick(
        "M8", "Times 99", "Medium",
        "Learn how to multiply by 99 by multiplying by 100, then subtracting the number.",
        [_example(
            "One-digit numbers", "Medium", "7 × 99 = 693",
            ("Times 100", "7 × 100 = 700"),
            ("Subtract the number", "700 − 7 = 693"),
        )],
        "times",
        {
            "Easy": {"factor": 99, "a": (2, 12)},
            "Medium": {"factor": 99, "a": (13, 99)},
            "Hard": {"factor": 99, "a": (100, 999)},
            "Pro": {"factor": 99, "a": (1000, 9999)},
        },
    ),
)

# --- Division ---

DIVISION = (
    _trick(
        "D1", "Divide by 5", "Medium",
        "Learn how to divide by 5 by doubling, then dividing by 10.",
        [_example(
            "Two-digit numbers", "Medium", "45 ÷ 5 = 9",
            ("Double", "45 × 2 = 90"),
            ("Divide by 10", "90 ÷ 10 = 9"),
        )],
        "divide",
        {
            "Easy": {"divisor": 5, "result": (2, 10)},
            "Medium": {"divisor": 5, "result": (11, 100)},
            "Hard": {"divisor": 5, "result": (101, 1000)},
            "Pro": {"divisor": 5, "result": (1001, 10_000)},
        },
    ),
    _trick(
        "D2", "Divide by 8", "Medium",
        "Learn how to divide by 8 by halving three times.",
        [_example(
            "Two-digit numbers", "Medium", "32 ÷ 8 = 4",
            ("Halve", "32 ÷ 2 = 16"),
            ("Halve again", "16 ÷ 2 = 8"),
            ("Halve a third time", "8 ÷ 2 = 4"),
        )],
        "divide",
        {
            "Easy": {"divisor": 8, "result": (2, 10)},
            "Medium": {"divisor": 8, "result": (11, 50)},
            "Hard": {"divisor": 8, "result": (51, 200)},
            "Pro": {"divisor": 8, "result": (201, 1000)},
        },
        note="If you know dividing by 2 and 4, this will not surprise you.",
    ),
    _trick(
        "D3", "Cancel zeros", "Medium",
        "Learn how to remove the same number of trailing zeros from both numbers first.",
        [_example(
            "Round numbers", "Medium", "8,000 ÷ 200 = 40",
            ("Remove the same number of zeros from both numbers",
             "8,000 ÷ 100 = 80; 200 ÷ 100 = 2"),
            ("Divide the smaller numbers", "80 ÷ 2 = 40"),
        )],
        "cancel_zeros",
        {
            "Easy": {"a": (1, 9), "a_scale": 10, "b": (1, 9), "b_scale": 10},
            "Medium": {"a": (1, 9), "a_scale": 100, "b": (1, 9), "b_scale": 10},
            "Hard": {"a": (1, 9), "a_scale": 1000, "b": (1, 9), "b_scale": 100},
            "Pro": {"a": (10, 99), "a_scale": 1000, "b": (10, 99), "b_scale": 100},
        },
    ),
    _trick(
        "D4", "Simplify", "Medium",
        "Learn how to divide both numbers by a common factor first.",
        [_example(
            "Two-digit by one-digit", "Medium", "48 ÷ 8 = 6",
            ("Divide both numbers by a common factor", "48 ÷ 4 = 12; 8 ÷ 4 = 2"),
            ("Divide the simpler numbers", "12 ÷ 2 = 6"),
        )],
        "simplify",
        {
            "Easy": {"divisor": (4, 8, 2), "factor": (2, 2), "result": (2, 9)},
            "Medium": {"divisor": (10, 20), "factor": (2, 5), "result": (2, 12)},
            "Hard": {"divisor": (10, 99), "factor": (2, 9), "result": (2, 20),
                     "dividend": (100, 999)},
            "Pro": {"divisor": (10, 99), "factor": (2, 9), "result": (11, 99),
                    "dividend": (1000, 9999)},
        },
    ),
)

# --- Square numbers ---

SQUARES = (
    _trick(
        "Q1", "Between 10 and 25", "Extreme",
        "Learn how to square the numbers from 11 to 19 in four short steps.",
        [_example(
            "11 to 19", "Extreme", "19² = 361",
            ("Add the ones digit to the number", "19 + 9 = 28"),
            ("Times 10", "28 × 10 = 280"),
            ("Square the ones digit", "9² = 81"),
            ("Add", "280 + 81 = 361"),
        )],
        "square",
        {
            "Easy": {"n": (11, 13)},
            "Medium": {"n": (14, 16)},
            "Hard": {"n": (17, 19)},
            "Pro": {"n": (11, 19)},
        },
        note="These steps work for the numbers 11 to 19.",
    ),
    _trick(
        "Q2", "Between 25 and 75", "Extreme",
        "Learn how to square a number between 25 and 75 using its distance from 50.",
        [_example(
            "26 to 74", "Extreme", "47² = 2,209",
            ("Subtract 25", "47 − 25 = 22"),
            ("Times 100", "22 × 100 = 2,200"),
            ("Find the distance from 50", "50 − 47 = 3"),
            ("Square it", "3² = 9"),
            ("Add", "2,200 + 9 = 2,209"),
        )],
        "square",
        {
            "Easy": {"n": (45, 55)},
            "Medium": {"n": (35, 65)},
            "Hard": {"n": (30, 70)},
            "Pro": {"n": (26, 74)},
        },
    ),
    _trick(
        "Q3", "Between 75 and 125", "Extreme",
        "Learn how to square a number near 100 using its distance from 100.",
        [
            _example(
                "75 to 99", "Extreme", "96² = 9,216",
                ("Find the distance below 100", "100 − 96 = 4"),
                ("Subtract it from the number", "96 − 4 = 92"),
                ("Times 100", "92 × 100 = 9,200"),
                ("Square the distance", "4² = 16"),
                ("Add", "9,200 + 16 = 9,216"),
            ),
            _example(
                "101 to 125", "Extreme", "106² = 11,236",
                ("Find the distance above 100", "106 − 100 = 6"),
                ("Add it to the number", "106 + 6 = 112"),
                ("Times 100", "112 × 100 = 11,200"),
                ("Square the distance", "6² = 36"),
                ("Add", "11,200 + 36 = 11,236"),
            ),
        ],
        "square",
        {
            "Easy": {"n": (95, 105), "exclude": (100,)},
            "Medium": {"n": (90, 110), "exclude": (100,)},
            "Hard": {"n": (80, 120), "exclude": (100,)},
            "Pro": {"n": (76, 125), "exclude": (100,)},
        },
    ),
    _trick(
        "Q4", "Ending in 5", "Medium–Hard",
        "Learn how to square a number ending in 5: multiply the number before the 5 by the "
        "next number, then append 25.",
        [
            _example(
                "15 to 95", "Medium", "85² = 7,225",
                ("Multiply the number before the 5 by the next number", "8 × 9 = 72"),
                ("Append 25", "72 × 100 + 25 = 7,225"),
            ),
            _example(
                "105 to 995", "Hard", "205² = 42,025",
                ("Multiply the number before the 5 by the next number", "20 × 21 = 420"),
                ("Append 25", "420 × 100 + 25 = 42,025"),
            ),
        ],
        "square",
        {
            "Easy": {"n": (15, 45, 10)},
            "Medium": {"n": (55, 95, 10)},
            "Hard": {"n": (105, 495, 10)},
            "Pro": {"n": (505, 995, 10)},
        },
    ),
    _trick(
        "Q5", "Round to the nearest ten", "Hard",
        "Learn how to square a number by rounding it to a ten and correcting.",
        [_example(
            "Two-digit numbers", "Hard", "83² = 6,889",
            ("Round up to a ten", "83 + 7 = 90"),
            ("Round down by the same amount", "83 − 7 = 76"),
            ("Multiply", "90 × 76 = 6,840"),
            ("Square the amount", "7² = 49"),
            ("Add", "6,840 + 49 = 6,889"),
        )],
        "square",
        {
            "Easy": {"n": (11, 29)},
            "Medium": {"n": (31, 59)},
            "Hard": {"n": (61, 99)},
            "Pro": {"n": (101, 199)},
        },
    ),
)

CATEGORIES = (
    Category("addition", "Addition", "Addition tricks", ADDITION),
    Category("subtraction", "Subtraction", "Subtraction tricks", SUBTRACTION),
    Category("multiplication", "Multiplication", "Multiplication tricks", MULTIPLICATION),
    Category("division", "Division", "Division tricks", DIVISION),
    Category("squares", "Square numbers", "Square number tricks", SQUARES),
)

_TRICKS = {trick.id: trick for category in CATEGORIES for trick in category.tricks}
_CATEGORY_OF = {trick.id: category for category in CATEGORIES for trick in category.tricks}


def get_trick(trick_id: str) -> Trick:
    """The trick with this id. Raises KeyError for an unknown id."""
    return _TRICKS[trick_id]


def get_category(category_id: str) -> Category:
    return next(category for category in CATEGORIES if category.id == category_id)


def category_of(trick_id: str) -> Category:
    return _CATEGORY_OF[trick_id]
