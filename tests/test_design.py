"""The design layer (spec 777): theme, style sheet, script and top bar.

What it looks like needs a manual check in the PR, on a phone (or a browser
at 375 px) and on a laptop: every section, light and dark mode, the bottom
tab bar on the phone, the timer ring, the confetti and the "+1".
"""

import re
import tomllib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import design
from conftest import TEST_USER

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
CONFIG = ROOT / ".streamlit" / "config.toml"
SECTIONS = ["Tests", "Trainer", "Knowledge", "Games", "Profile"]


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


def html_bodies(at: AppTest) -> list[str]:
    return [element.proto.body for element in at.get("html")]


# --- Theme ---


def test_theme_has_a_light_and_a_dark_version_with_the_same_fonts():
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["theme"]
    assert theme["font"].startswith("Inter:https://fonts.googleapis.com/")
    assert theme["headingFont"].startswith("Inter:https://fonts.googleapis.com/")
    for mode in ("light", "dark"):
        for option in ("primaryColor", "backgroundColor", "secondaryBackgroundColor", "textColor"):
            assert re.fullmatch(r"#[0-9A-Fa-f]{6}", theme[mode][option]), (mode, option)


def test_secrets_stay_out_of_the_theme_file():
    text = CONFIG.read_text(encoding="utf-8").lower()
    assert "password" not in text
    assert "postgres" not in text


# --- Style sheet and script ---


def test_style_sheet_has_nothing_that_streamlit_would_remove():
    """Streamlit drops a <style> block that contains "<" followed by a letter or "/"."""
    css = design.stylesheet()
    assert css.strip()
    assert re.findall(r"<[/\w]", css) == []


def test_style_sheet_never_nests_has():
    """A :has() inside a :has() is not valid CSS: the browser would drop the whole rule."""
    css = design.stylesheet()
    for match in re.finditer(r":has\(", css):
        depth, end = 1, match.end()
        while depth:
            depth += {"(": 1, ")": -1}.get(css[end], 0)
            end += 1
        assert ":has(" not in css[match.end() : end], css[match.start() : match.start() + 120]


def test_style_sheet_covers_phones_dark_mode_and_less_motion():
    css = design.stylesheet()
    assert "@media (max-width: 640px)" in css
    assert ':root[data-mb-theme="dark"]' in css
    assert "@media (prefers-color-scheme: dark)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_navigation_has_one_icon_per_section():
    css = design.stylesheet()
    for position in range(1, len(SECTIONS) + 1):
        assert f'[data-testid="stRadioGroup"] > :nth-child({position}) [data-testid="stRadioOption"]' in css


def test_script_loads_nothing_from_other_sites():
    script = design.script()
    assert "http://" not in script
    assert "https://" not in script
    assert "fetch(" not in script
    assert "</script" not in script.lower()


# --- Top bar ---


@pytest.mark.parametrize(
    ("username", "initial"),
    [("mia_design", "M"), ("tester", "T"), ("_bo", "B"), ("7up", "7"), ("__", "?")],
)
def test_avatar_shows_the_first_letter_or_digit(username, initial):
    assert design.initial_of(username) == initial


def test_username_in_the_top_bar_is_shown_as_text_never_as_html():
    bar = design.top_bar("<b>x</b>")
    assert "<b>x</b>" not in bar
    assert "&lt;b&gt;x&lt;/b&gt;" in bar


def test_top_bar_tells_the_timer_ring_how_long_a_test_lasts():
    assert 'data-mb-test-seconds="60"' in design.top_bar("tester")


# --- In the app ---


def test_signed_in_app_has_the_design_and_the_player_in_the_top_bar():
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    bodies = html_bodies(at)
    assert any("Mathbuddy design system" in body for body in bodies)
    assert any('class="mb-topbar"' in body and TEST_USER.username in body for body in bodies)
    assert [str(option) for option in at.radio(key="nav").options] == SECTIONS


@pytest.mark.signed_out
def test_sign_in_screen_has_the_design_but_no_top_bar_and_no_decoration():
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    bodies = html_bodies(at)
    assert any("Mathbuddy design system" in body for body in bodies)
    assert not any('class="mb-topbar"' in body for body in bodies)
    assert not any('class="mb-decor"' in body for body in bodies)  # clean look: nothing floats behind the card
    assert at.title[0].value == "Mathbuddy"


def test_design_adds_no_text_to_the_screens():
    """The design only adds html elements, so every screen keeps its texts."""
    at = AppTest.from_file(str(APP)).run()
    texts = [element.value for element in (*at.title, *at.header, *at.markdown, *at.caption)]
    assert not any("mb-" in str(text) for text in texts)
