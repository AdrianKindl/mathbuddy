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
    assert "HICCUP_MAX = 8" in script
    assert "bubble.remove()" in script
    assert "event.preventDefault()" in script  # the answer field keeps the cursor


def test_one_delegated_listener_on_the_document_bound_only_once():
    """Spec 021: the click must work however late the logo appears (slow Cloud
    load) and however often design.js runs or Streamlit redraws the logo."""
    script = design.script()
    assert 'const BRAND = "[data-mb-topbar] .mb-brand";' in script
    assert "target.closest(BRAND)" in script  # delegation: found from the clicked element
    guard = script.index("if (!doc.__mbHiccupBound) {")
    assert "doc.__mbHiccupBound = true;" in script[guard:guard + 80]
    bound = script[guard:]
    assert re.search(r'doc\.addEventListener\("click", \(event\) => \{\s*const brand = brandFor\(event\);', bound)
    assert re.search(r'doc\.addEventListener\("mousedown",', bound)
    # Only these two listeners mention the logo, and only inside the guard.
    calls = r"(?<!function )brandFor\(event\)"
    assert len(re.findall(calls, script)) == 2
    assert re.findall(calls, script[:guard]) == []
    # Capture phase, so nothing on the way can stop the click first.
    assert bound.count("}, true);") >= 2


def test_the_top_bar_sits_above_streamlits_toolbar_where_the_toolbar_is_shown():
    """Spec 021: wider than 1100 px Streamlit's toolbar (z-index 999990) covers
    the whole header, so the logo and account button got no clicks."""
    css = design.stylesheet()
    hidden = re.search(r"@media \(max-width: 1100px\) \{\s*\[data-testid=\"stToolbar\"\] \{\s*display: none;", css)
    assert hidden, "the toolbar is hidden up to 1100 px"
    lifted = re.search(
        r"@media not all and \(max-width: 1100px\) \{\s*\.mb-topbar \{([^}]*)\}", css
    )
    assert lifted, "exactly where the toolbar is shown, the top bar is lifted"
    assert "position: relative;" in lifted.group(1)
    z_index = int(re.search(r"z-index: (\d+);", lifted.group(1)).group(1))
    assert z_index > 999990  # Streamlit's header and toolbar
    assert z_index < 1000001  # the confetti and the floating equations stay on top


def test_the_logo_click_does_not_depend_on_resize():
    script = design.script()
    resize_listeners = re.findall(r'addEventListener\("resize", (\w+)\)', script)
    assert resize_listeners == ["resize"]  # only the confetti canvas follows the window size
    assert "hiccup" not in script[script.index("function resize()"):script.index("function launch(")]


def test_the_stylesheet_animates_the_logo_and_never_blocks_clicks():
    css = design.stylesheet()
    assert ".mb-logo[data-mb-hiccup]" in css
    block = re.search(r"\.mb-hiccup \{(.*?)\}", css, re.S).group(1)
    assert "pointer-events: none;" in block
    assert "position: fixed;" in block
    calm = css[css.index("20. Easter egg"):]
    assert re.search(r"prefers-reduced-motion: reduce\)\s*\{\s*\.mb-hiccup \{[^}]*mb-hiccup-fade", calm)
