"""Spec 020: the logo's "equation hiccup" easter egg lives in the design files
and every equation it shows is correct."""

import math
import re

import design

OPERATIONS = {
    "+": lambda a, b: a + b,
    "−": lambda a, b: a - b,
    "×": lambda a, b: a * b,
    "÷": lambda a, b: a / b,
}


def hiccups() -> list[str]:
    block = re.search(r"const HICCUPS = \[(.*?)\];", design.script(), re.S)
    assert block, "design.js should list the equations in HICCUPS"
    return re.findall(r'"([^"]+)"', block.group(1))


def is_correct(equation: str) -> bool:
    if match := re.fullmatch(r"(\d+) ([+−×÷]) (\d+) = (\d+)", equation):
        a, operation, b, result = match.groups()
        return OPERATIONS[operation](int(a), int(b)) == int(result)
    if match := re.fullmatch(r"(\d+)² = (\d+)", equation):
        return int(match.group(1)) ** 2 == int(match.group(2))
    if match := re.fullmatch(r"√(\d+) = (\d+)", equation):
        return math.isqrt(int(match.group(1))) ** 2 == int(match.group(1)) and (
            math.isqrt(int(match.group(1))) == int(match.group(2))
        )
    raise AssertionError(f"unknown equation format: {equation!r}")


def test_there_are_20_to_30_different_equations():
    equations = hiccups()
    assert 20 <= len(equations) <= 30
    assert len(set(equations)) == len(equations)


def test_every_equation_is_correct():
    wrong = [equation for equation in hiccups() if not is_correct(equation)]
    assert wrong == []


def test_the_checker_notices_a_wrong_equation():
    assert not is_correct("7 × 8 = 54")
    assert not is_correct("15² = 215")
    assert not is_correct("√80 = 9")


def test_the_script_hiccups_on_a_logo_click_and_cleans_up():
    script = design.script()
    assert '.closest("[data-mb-topbar] .mb-brand")' in script
    assert "HICCUP_MAX = 8" in script
    assert "bubble.remove()" in script
    assert "event.preventDefault()" in script  # the answer field keeps the cursor


def test_the_stylesheet_animates_the_logo_and_never_blocks_clicks():
    css = design.stylesheet()
    assert ".mb-logo[data-mb-hiccup]" in css
    block = re.search(r"\.mb-hiccup \{(.*?)\}", css, re.S).group(1)
    assert "pointer-events: none;" in block
    assert "position: fixed;" in block
    calm = css[css.index("20. Easter egg"):]
    assert re.search(r"prefers-reduced-motion: reduce\)\s*\{\s*\.mb-hiccup \{[^}]*mb-hiccup-fade", calm)
