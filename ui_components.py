"""Screen pieces shared by Tests (app.py), the Trainer (trainer_ui.py) and
Knowledge (knowledge_ui.py).

Streamlit only: no rules and no SQL. All screens use these, so they look and
behave the same.
"""

from collections.abc import Callable

import streamlit as st

EXAMPLE_SEED = 7  # a fixed seed, so an example does not change on every rerun
FLASH_COLORS = {"green": "rgb(22, 163, 74)", "red": "rgb(220, 38, 38)"}
FLASH_MS = 700


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


# --- The answer field: one form with Submit and Skip, the green / red flash and
# the cursor focus. `prefix` keeps each screen's keys apart: "" gives the keys
# "answer", "submit" and "skip", "tr_" gives "tr_answer", "tr_submit", … ---


def answer_form(
    prefix: str,
    on_submit: Callable[[], None],
    on_skip: Callable[[], None],
    placeholder: str | None = None,
) -> None:
    with st.form(f"{prefix}answer_form", clear_on_submit=True, border=False):
        st.text_input(
            "Answer", key=f"{prefix}answer", autocomplete="off", placeholder=placeholder
        )
        submit_column, skip_column = st.columns(2)
        # Submit comes first, because Enter triggers the first button in a form.
        submit_column.form_submit_button(
            "Submit", key=f"{prefix}submit", type="primary", on_click=on_submit, width="stretch"
        )
        skip_column.form_submit_button(
            "Skip", key=f"{prefix}skip", on_click=on_skip, width="stretch"
        )


def answer_flash(prefix: str, color: str | None, attempt: int) -> None:
    """Flash the answer field "green" or "red". None shows no flash."""
    if color is None:
        return
    # A new animation name per attempt makes the same colour replay. The colour
    # holds for most of the flash, then fades back to the field's normal look.
    name = f"{prefix}flash-{attempt}"
    flash_color = FLASH_COLORS[color]
    st.html(
        f"""<style>
        @keyframes {name} {{
            0%, 60% {{
                background-color: {flash_color};
                border-color: {flash_color};
                box-shadow: 0 0 0 3px {flash_color}, 0 0 18px 6px {flash_color};
            }}
        }}
        .st-key-{prefix}answer [data-testid="stTextInputRootElement"] {{
            animation: {name} {FLASH_MS}ms ease-out;
        }}
        </style>"""
    )


def answer_focus(prefix: str, attempt: int) -> None:
    """Put the cursor back in the answer field. Clicking a button would move it away.

    `attempt` must change with every answer, so the script runs again.
    """
    st.html(
        f"""<script data-attempt="{attempt}">
        requestAnimationFrame(() => {{
            document.querySelector(".st-key-{prefix}answer input")?.focus();
        }});
        </script>""",
        unsafe_allow_javascript=True,
    )
