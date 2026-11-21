"""Screen pieces shared by the Tests screen (app.py) and the Trainer (trainer_ui.py).

Streamlit only: no rules and no SQL. Both screens use these, so they look and
behave the same.
"""

import streamlit as st

EXAMPLE_SEED = 7  # a fixed seed, so an example does not change on every rerun


def pick(widget, label: str, options, key: str, **options_for_widget) -> str:
    """One choice out of a few, as a row of buttons (st.pills or st.segmented_control).

    It cannot be empty and is remembered for the session, also while the
    widget is not on screen.
    """
    options = list(options)
    choice = widget(
        label,
        options,
        default=options[0],
        required=True,
        key=key,
        persist_state="session",
        **options_for_widget,
    )
    return choice or options[0]


def example_box(prompt: str, text: str) -> None:
    """A bordered box with one example task. Display only."""
    with st.container(border=True):
        st.caption(f"Example task · {prompt}")
        st.markdown(f"**{text}**")
