"""Mathbuddy: Streamlit screens and navigation only."""

import math
import random
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import db
import trainer_ui
from runs import (
    COUNTDOWN_SECONDS,
    Outcome,
    Run,
    Status,
    abort_run,
    accuracy,
    finish_if_expired,
    finished_at,
    highscores,
    is_new_highscore,
    is_time_up,
    remaining_seconds,
    skip_task,
    start_run,
    submit_answer,
)
from tasks import LEVELS, TEST_TYPES, generate_task

SECTIONS = ["Tests", "Trainer", "Knowledge", "Games", "Profile"]
NO_VALUE = "–"
IGNORED_HINT = "Numbers only, e.g. 4250"
FLASH_COLORS = {"green": "rgb(22, 163, 74)", "red": "rgb(220, 38, 38)"}
FLASH_MS = 700

state = st.session_state


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- Changing screens ---


def begin_run() -> None:
    state.run = start_run(state.chosen_type, state.chosen_level, utc_now())
    state.run_id = str(uuid.uuid4())
    state.rng = random.Random()
    state.current_task = generate_task(state.chosen_type, state.chosen_level, state.rng)
    state.flash = None
    state.attempt = 0
    state.show_hint = False
    state.phase = "running"


def clear_run() -> None:
    for name in ("run", "run_id", "rng", "current_task", "flash", "show_hint"):
        state.pop(name, None)
    state.phase = "select"


def complete_run(run: Run) -> None:
    """Save the run and prepare the result. Safe to repeat for the same run."""
    earlier = [saved for saved in db.list_runs() if saved.id != state.run_id]
    previous = highscores(earlier).get((run.test_type, run.level))
    db.save_run(
        state.run_id,
        run.test_type,
        run.level,
        finished_at(run),
        run.correct,
        run.wrong,
        run.skipped,
    )
    state.result = {
        "run": run,
        "highscore": highscores(db.list_runs())[(run.test_type, run.level)],
        "is_new": is_new_highscore(previous, run.correct),
    }
    clear_run()
    state.phase = "result"


def apply_outcome(run: Run, outcome: Outcome) -> None:
    state.attempt += 1  # the focus script runs again for every attempt
    state.run = run
    if outcome == Outcome.TIME_UP:
        complete_run(run)
        return

    state.show_hint = outcome == Outcome.IGNORED
    state.flash = {Outcome.CORRECT: "green", Outcome.WRONG: "red"}.get(outcome)
    if outcome != Outcome.IGNORED:
        state.current_task = generate_task(
            run.test_type, run.level, state.rng, previous=state.current_task
        )


def leave_run(now: datetime) -> None:
    """End the running test early: discarded, unless its 60 seconds were already up."""
    run = abort_run(state.run, now)
    if run.status == Status.COMPLETED:
        complete_run(run)
    else:
        clear_run()


# --- Callbacks: each one reads the clock first, so the time is as close as
# possible to when the action arrived ---


def on_start() -> None:
    state.chosen_type = state.test_type
    state.chosen_level = state.level
    state.phase = "countdown"


def on_cancel_countdown() -> None:
    clear_run()


def on_submit() -> None:
    now = utc_now()
    apply_outcome(*submit_answer(state.run, state.current_task, state.answer, now))


def on_skip() -> None:
    now = utc_now()
    apply_outcome(*skip_task(state.run, now))


def on_abort() -> None:
    leave_run(utc_now())


def on_back() -> None:
    state.pop("result", None)
    state.phase = "select"


def on_nav_change() -> None:
    now = utc_now()
    if state.phase == "running":
        leave_run(now)
    state.pop("result", None)
    state.phase = "select"
    trainer_ui.leave()


# --- Screens ---


def render_coming_soon(section: str) -> None:
    st.header(section, anchor=False)
    st.info("Coming soon")


def render_select() -> None:
    st.header("Tests", anchor=False)
    st.selectbox(
        "Test type",
        TEST_TYPES,
        index=TEST_TYPES.index(state.get("chosen_type", TEST_TYPES[0])),
        key="test_type",
    )
    st.selectbox(
        "Level",
        LEVELS,
        index=LEVELS.index(state.get("chosen_level", LEVELS[0])),
        key="level",
    )
    st.button("Start", key="start", type="primary", on_click=on_start)

    st.subheader("Highscores", anchor=False)
    best = highscores(db.list_runs())
    st.table(
        pd.DataFrame(
            {
                level: [str(best.get((test_type, level), NO_VALUE)) for test_type in TEST_TYPES]
                for level in LEVELS
            },
            index=list(TEST_TYPES),
        )
    )


def render_countdown() -> None:
    number = st.empty()
    st.button("Cancel", key="cancel", on_click=on_cancel_countdown)
    # While this script sleeps, the elements of the previous screen would stay
    # visible below. Empty placeholders overwrite them.
    for _ in range(12):
        st.empty()

    for remaining in range(COUNTDOWN_SECONDS, 0, -1):
        number.header(str(remaining), anchor=False)
        time.sleep(1)

    begin_run()
    st.rerun()


@st.fragment(run_every="1s")
def render_timer() -> None:
    """Only this part refreshes every second, so typing is not disturbed."""
    run = state.get("run")
    if run is None:
        return
    now = utc_now()
    if is_time_up(run, now):
        st.rerun(scope="app")
    st.metric("Time left", math.ceil(remaining_seconds(run, now)))


def render_flash() -> None:
    color = state.get("flash")
    if color is None:
        return
    # A new animation name per attempt makes the same colour replay. The colour
    # holds for most of the flash, then fades back to the field's normal look.
    name = f"flash-{state.attempt}"
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
        .st-key-answer [data-testid="stTextInputRootElement"] {{
            animation: {name} {FLASH_MS}ms ease-out;
        }}
        </style>"""
    )


def render_focus_script() -> None:
    """Put the cursor back in the answer field. Clicking a button would move it away."""
    st.html(
        f"""<script data-attempt="{state.attempt}">
        requestAnimationFrame(() => {{
            document.querySelector(".st-key-answer input")?.focus();
        }});
        </script>""",
        unsafe_allow_javascript=True,
    )


def render_running() -> None:
    render_timer()
    st.header(state.current_task.text, anchor=False)

    with st.form("answer_form", clear_on_submit=True, border=False):
        st.text_input("Answer", key="answer", autocomplete="off")
        submit_column, skip_column = st.columns(2)
        # Submit comes first, because Enter triggers the first button in a form.
        submit_column.form_submit_button(
            "Submit", key="submit", type="primary", on_click=on_submit, width="stretch"
        )
        skip_column.form_submit_button("Skip", key="skip", on_click=on_skip, width="stretch")

    if state.show_hint:
        st.warning(IGNORED_HINT)
    st.button("Abort test", key="abort", on_click=on_abort)

    render_flash()
    render_focus_script()


def render_result() -> None:
    result = state.result
    run = result["run"]
    run_accuracy = accuracy(run.correct, run.wrong, run.skipped)

    st.header(f"Time's up: {run.test_type}, {run.level}", anchor=False)
    if result["is_new"]:
        st.success("New highscore!")

    columns = st.columns(5)
    columns[0].metric("Score", run.correct)
    columns[1].metric("Wrong", run.wrong)
    columns[2].metric("Skipped", run.skipped)
    columns[3].metric("Accuracy", NO_VALUE if run_accuracy is None else f"{run_accuracy:.1%}")
    columns[4].metric("Highscore", result["highscore"])

    st.button("Back to Tests", key="back", type="primary", on_click=on_back)


def render_tests() -> None:
    if state.phase == "running":
        run = finish_if_expired(state.run, utc_now())
        if run.status == Status.COMPLETED:
            complete_run(run)

    if state.phase == "countdown":
        render_countdown()
    elif state.phase == "running":
        render_running()
    elif state.phase == "result":
        render_result()
    else:
        render_select()


def main() -> None:
    st.set_page_config(page_title="Mathbuddy")
    if "phase" not in state:  # once per session, so reruns during a test stay fast
        db.init_db()
        state.phase = "select"

    section = st.radio(
        "Section",
        SECTIONS,
        key="nav",
        horizontal=True,
        label_visibility="collapsed",
        on_change=on_nav_change,
    )
    if section == "Tests":
        render_tests()
    elif section == "Trainer":
        trainer_ui.render()
    else:
        render_coming_soon(section)


main()
