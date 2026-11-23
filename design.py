"""Mathbuddy's look: one design for every screen (spec 777).

Streamlit only: no rules and no SQL. app.py calls `apply()` first in every
run. The colours and fonts come from `.streamlit/config.toml`, `design.css`
styles the elements Streamlit draws, and `design.js` adds the small moments
(confetti, the timer ring, the pop of a new task).

A new screen, like Profile, gets the same look by itself as long as it uses
normal Streamlit elements: st.header, st.caption, st.metric in st.columns,
st.table, st.bar_chart, st.container(border=True), buttons, pills and so on.
Nothing in here changes what a screen shows or does.
"""

from html import escape
from pathlib import Path

import streamlit as st

from runs import TIME_LIMIT_SECONDS

HERE = Path(__file__).resolve().parent
CSS_FILE = HERE / "design.css"
JS_FILE = HERE / "design.js"

# Floating maths symbols behind the sign-in card. Decoration only.
DECOR_SYMBOLS = ("+", "×", "÷", "−", "√", "%", "=", "π", "²", "∑", "½", "∞")


def stylesheet() -> str:
    return CSS_FILE.read_text(encoding="utf-8")


def script() -> str:
    return JS_FILE.read_text(encoding="utf-8")


def initial_of(username: str) -> str:
    """The letter in the avatar circle: the first letter or digit, upper case."""
    for character in username:
        if character.isalnum():
            return character.upper()
    return "?"


def top_bar(username: str) -> str:
    """Logo on the left, the signed-in player on the right (opens the account panel)."""
    name = escape(username)
    initial = escape(initial_of(username))
    return f"""
<div class="mb-topbar" data-mb-topbar data-mb-initial="{initial}"
     data-mb-test-seconds="{TIME_LIMIT_SECONDS}">
  <div class="mb-brand">
    <span class="mb-logo" aria-hidden="true"></span>
    <span class="mb-wordmark">Math<b>buddy</b></span>
  </div>
  <button class="mb-account" type="button" data-mb-account aria-label="Account: {name}">
    <span class="mb-account-text">
      <span class="mb-greet" data-mb-greet>Hi</span>
      <span class="mb-name">{name}</span>
    </span>
    <span class="mb-avatar" aria-hidden="true">{initial}</span>
  </button>
</div>"""


def decor() -> str:
    spans = "".join(f"<span>{symbol}</span>" for symbol in DECOR_SYMBOLS)
    return f'<div class="mb-decor" aria-hidden="true">{spans}</div>'


def apply() -> None:
    """Draw the design layer. Call it once per run, right after st.set_page_config."""
    st.html(f"<style>{stylesheet()}</style>")
    user = st.session_state.get("user")
    chrome = top_bar(user.username) if user is not None else decor()
    st.html(f"{chrome}<script>{script()}</script>", unsafe_allow_javascript=True)
