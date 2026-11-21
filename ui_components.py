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
        # Once the key exists, its value counts. A default as well would make
        # Streamlit warn when a callback sets the choice through session_state.
        default=None if key in st.session_state else options[0],
        required=True,
        key=key,
        persist_state="session",
        **options_for_widget,
    )
    return choice or options[0]


# --- Knowledge pieces, shared by Tricks and Textbook. A row or tile is
# (label, key, args): `args` is passed to the click handler. ---


def back_button(key: str, on_click: Callable, args: tuple = ()) -> None:
    st.button("← Back", key=key, on_click=on_click, args=args)


def tile_grid(tiles: list[tuple[str, str, tuple]], on_click: Callable, per_row: int = 3) -> None:
    """Tiles in rows of `per_row`. One row of columns at a time keeps their order."""
    for start in range(0, len(tiles), per_row):
        columns = st.columns(per_row)
        for column, (label, key, args) in zip(columns, tiles[start : start + per_row]):
            column.button(label, key=key, on_click=on_click, args=args, width="stretch")


def list_rows(rows: list[tuple[str, str, tuple]], on_click: Callable) -> None:
    for label, key, args in rows:
        st.button(label, key=key, on_click=on_click, args=args, width="stretch")


def card_header(title: str, category: str, difficulty: str) -> None:
    """A card's title with its category and difficulty tags."""
    st.markdown(f"**{title}**  \n:blue-badge[{category}] :orange-badge[{difficulty}]")


def previous_next_bar(
    prefix: str,
    previous_id: str | None,
    next_id: str | None,
    number: int,
    total: int,
    on_open: Callable,
) -> None:
    """Previous / next buttons, disabled at either end, with "2 / 5" between them."""
    left, middle, right = st.columns(3, vertical_alignment="center")
    left.button(
        "← Previous",
        key=f"{prefix}prev",
        disabled=previous_id is None,
        on_click=on_open,
        args=(previous_id,),
        width="stretch",
    )
    middle.markdown(f"<div style='text-align: center'>{number} / {total}</div>",
                    unsafe_allow_html=True)  # fmt: skip
    right.button(
        "Next →",
        key=f"{prefix}next",
        disabled=next_id is None,
        on_click=on_open,
        args=(next_id,),
        width="stretch",
    )


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
