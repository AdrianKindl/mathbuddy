"""Mathbuddy: Streamlit screens and navigation only."""

import math
import random
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import db
import numberhunt
import sudoku
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
LIVES = sudoku.LIVES
SUDOKU_VARIANTS = {"Mini Sudoku": sudoku.MINI, "Sudoku": sudoku.CLASSIC}
GAMES = [*SUDOKU_VARIANTS, "Number Hunt"]
COMING_SOON_GAMES = ["Magic Square"]
HUNT_OPERATIONS = {"plus": "+", "minus": "−", "times": "×", "divide": "÷"}
GAME_RULES = {
    "Mini Sudoku": (
        "Fill the grid with the numbers 1–6 so that each number appears once in every "
        "row, every column and every 2×3 box. A wrong number costs one of your 3 lives."
    ),
    "Sudoku": (
        "Fill the grid with the numbers 1–9 so that each number appears once in every "
        "row, every column and every 3×3 box. A wrong number costs one of your 3 lives. "
        "Take your time: there is no timer."
    ),
    "Number Hunt": (
        "Reach the target: tap a number, an operation, then a second number. The two "
        "numbers are replaced by their result. You win when the last number left is the "
        "target. Results must be whole numbers above 0, and × or ÷ by 1 is not allowed. "
        "A step that breaks these rules, Undo and Reset each cost one of your 3 lives."
    ),
}

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


# --- Games ---


def cell_key(row: int, col: int) -> str:
    return f"cell_{row}_{col}"


def clear_game() -> None:
    for key in [key for key in state if str(key).startswith("cell_")]:
        del state[key]  # no old entries in the next grid's fields
    for name in ("game", "hunt", "hunt_message"):
        state.pop(name, None)
    state.game_flash = None
    state.game_hint = False
    state.hunt_pick = {"first": None, "op": None}


def on_game_change() -> None:
    clear_game()  # nothing is saved, so the old game simply ends


def on_new_game() -> None:
    clear_game()
    choice = state.get("game_choice", GAMES[0])
    if choice == "Number Hunt":
        state.hunt = numberhunt.start_game(state.game_level, random.Random())
    else:
        variant = SUDOKU_VARIANTS[choice]
        state.game = sudoku.start_game(state.game_level, random.Random(), variant)


def on_cell(row: int, col: int) -> None:
    key = cell_key(row, col)
    raw = state[key]
    game, outcome = sudoku.enter_number(state.game, row, col, raw)
    state.game = game
    state[key] = ""  # a wrong or invalid entry leaves the field empty again
    state.game_attempt = state.get("game_attempt", 0) + 1
    state.game_flash = (row, col) if outcome == sudoku.Outcome.WRONG else None
    state.game_hint = outcome == sudoku.Outcome.IGNORED and raw.strip() != ""


def hunt_after(game: numberhunt.Game, outcome: numberhunt.Outcome, message: str | None) -> None:
    state.hunt = game
    state.hunt_pick = {"first": None, "op": None}
    state.game_attempt = state.get("game_attempt", 0) + 1
    state.game_flash = "hunt" if outcome == numberhunt.Outcome.WRONG else None
    state.hunt_message = message


def on_hunt_number(position: int) -> None:
    pick = state.hunt_pick
    if pick["first"] is None or pick["op"] is None:
        # Tapping the chosen number again unselects it; another number replaces it.
        pick["first"] = None if pick["first"] == position else position
        return
    if position == pick["first"]:
        return
    game = state.hunt
    a, op, b = game.numbers[pick["first"]], pick["op"], game.numbers[position]
    game, outcome = numberhunt.apply_step(game, pick["first"], op, position)
    message = None
    if outcome == numberhunt.Outcome.WRONG:
        message = f"{a} {op} {b} is not allowed. It cost a life."
    hunt_after(game, outcome, message)


def on_hunt_operation(op: str) -> None:
    if state.hunt_pick["first"] is not None:
        state.hunt_pick["op"] = op


def on_hunt_undo() -> None:
    hunt_after(*numberhunt.undo(state.hunt), None)


def on_hunt_reset() -> None:
    hunt_after(*numberhunt.reset(state.hunt), None)


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


SUDOKU_CSS = """<style>
.st-key-sudoku_grid { gap: 0.35rem; }
.st-key-sudoku_grid [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.35rem;
}
.st-key-sudoku_grid [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
    flex: 1 1 0 !important;
}
.st-key-sudoku_grid [data-testid="stTextInputRootElement"] {
    background: transparent;
    border: 2px solid rgba(128, 128, 128, 0.4);
    border-radius: 0.5rem;
}
.st-key-sudoku_grid input {
    background: transparent;
    text-align: center;
    font-size: 1.15rem;
    font-weight: 600;
    padding: 0;
}
.sudoku-cell {
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.5rem;
    font-size: 1.15rem;
    font-weight: 600;
}
.sudoku-given { background: rgba(128, 128, 128, 0.18); }
.sudoku-correct { background: rgb(22, 163, 74); color: white; }
.sudoku-missed { border: 2px dashed rgb(220, 38, 38); color: rgb(220, 38, 38); }
</style>"""


def sudoku_layout_css(variant: sudoku.Variant) -> str:
    """Width of the grid and the extra space between its boxes."""
    box_columns = ", ".join(
        f'.st-key-sudoku_grid [data-testid="stColumn"]:nth-child({col + 1})'
        for col in range(variant.box_cols, variant.size, variant.box_cols)
    )
    box_rows = ", ".join(
        f".st-key-sudoku_row_{row}" for row in range(variant.box_rows, variant.size, variant.box_rows)
    )
    width = {6: "24rem", 9: "32rem"}[variant.size]
    small = "" if variant.size == 6 else """
    @media (max-width: 640px) {
        .st-key-sudoku_grid [data-testid="stHorizontalBlock"],
        .st-key-sudoku_grid { gap: 0.2rem; }
        .st-key-sudoku_grid input, .sudoku-cell { font-size: 1rem; }
        .sudoku-cell,
        .st-key-sudoku_grid input,
        .st-key-sudoku_grid [data-testid="stTextInputRootElement"] {
            height: 2.1rem;
            min-height: 2.1rem;
        }
    }"""
    return f"""<style>
    .st-key-sudoku_grid {{ max-width: {width}; }}
    {box_columns} {{ margin-left: 0.6rem; }}
    {box_rows} {{ margin-top: 0.6rem; }}{small}
    </style>"""


def render_game_flash() -> None:
    cell = state.get("game_flash")
    if cell is None:
        return
    name = f"game-flash-{state.game_attempt}"
    red = FLASH_COLORS["red"]
    st.html(
        f"""<style>
        @keyframes {name} {{
            0%, 60% {{
                background-color: {red};
                border-color: {red};
                box-shadow: 0 0 0 3px {red}, 0 0 14px 4px {red};
            }}
        }}
        .st-key-{cell_key(*cell)} [data-testid="stTextInputRootElement"] {{
            animation: {name} {FLASH_MS}ms ease-out;
        }}
        </style>"""
    )


def render_cell(column, game: sudoku.Game, row: int, col: int) -> None:
    given = game.puzzle.givens[row][col]
    value = game.grid[row][col]
    if given:
        kind, text = "given", given
    elif value:
        kind, text = "correct", value
    elif game.status != sudoku.Status.RUNNING:
        kind, text = "missed", game.puzzle.solution[row][col]
    else:
        column.text_input(
            f"Row {row + 1}, column {col + 1}",
            key=cell_key(row, col),
            max_chars=1,
            autocomplete="off",
            label_visibility="collapsed",
            on_change=on_cell,
            args=(row, col),
        )
        return
    column.html(f'<div class="sudoku-cell sudoku-{kind}">{text}</div>')


def render_lives(lives: int) -> None:
    st.metric("Lives", lives)
    st.caption("❤️" * lives + "🤍" * (LIVES - lives))


def render_sudoku(game: sudoku.Game) -> None:
    variant = sudoku.variant_of(game.grid)
    render_lives(game.lives)

    if game.status == sudoku.Status.WON:
        st.success("You solved it!")
    elif game.status == sudoku.Status.LOST:
        st.markdown(
            "### :red[Game over]\nNo lives left. The missing numbers are shown in red."
        )
    elif state.get("game_hint"):
        st.warning(f"Numbers 1–{variant.size} only")

    st.html(SUDOKU_CSS + sudoku_layout_css(variant))
    with st.container(key="sudoku_grid"):
        for row in range(variant.size):
            with st.container(key=f"sudoku_row_{row}"):
                columns = st.columns(variant.size, gap=None)
                for col in range(variant.size):
                    render_cell(columns[col], game, row, col)
    render_game_flash()


HUNT_CSS = """<style>
.hunt-target {
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1.1;
}
.hunt-steps { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.hunt-step {
    background: rgb(22, 163, 74);
    color: white;
    border-radius: 0.5rem;
    padding: 0.25rem 0.6rem;
    font-weight: 600;
}
.st-key-hunt_header [data-testid="stHorizontalBlock"],
.st-key-hunt_numbers [data-testid="stHorizontalBlock"],
.st-key-hunt_operations [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.4rem;
}
.st-key-hunt_header [data-testid="stColumn"],
.st-key-hunt_numbers [data-testid="stColumn"],
.st-key-hunt_operations [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
    flex: 1 1 0 !important;
}
.st-key-hunt_numbers button, .st-key-hunt_operations button {
    padding-left: 0;
    padding-right: 0;
    min-height: 3rem;
}
.st-key-hunt_numbers button p, .st-key-hunt_operations button p {
    font-size: 1.35rem;
    font-weight: 700;
}
/* The chosen number and operation are blue: red means a wrong step. */
.st-key-hunt_numbers button[kind="primary"],
.st-key-hunt_operations button[kind="primary"] {
    background: rgb(37, 99, 235);
    border-color: rgb(37, 99, 235);
    color: white;
}
.st-key-hunt_numbers { border-radius: 0.6rem; }
</style>"""


def render_hunt_flash() -> None:
    if state.get("game_flash") != "hunt":
        return
    name = f"hunt-flash-{state.game_attempt}"
    red = FLASH_COLORS["red"]
    st.html(
        f"""<style>
        @keyframes {name} {{
            0%, 60% {{ box-shadow: 0 0 0 3px {red}, 0 0 18px 6px {red}; }}
        }}
        .st-key-hunt_numbers {{ animation: {name} {FLASH_MS}ms ease-out; }}
        </style>"""
    )


def render_hunt(game: numberhunt.Game) -> None:
    st.html(HUNT_CSS)
    with st.container(key="hunt_header"):
        target_column, lives_column = st.columns(2)
        with target_column:
            st.metric("Target", game.puzzle.target)
        with lives_column:
            render_lives(game.lives)

    running = game.status == numberhunt.Status.RUNNING
    if game.status == numberhunt.Status.WON:
        st.success("You found it!")
    elif game.status == numberhunt.Status.LOST:
        st.markdown("### :red[Game over]\nNo lives left. One way to reach the target:")
        st.markdown("  \n".join(step.text for step in game.puzzle.solution))
    elif state.get("hunt_message"):
        st.warning(state.hunt_message)
    elif numberhunt.is_stuck(game):
        st.info("That is not the target. Use Undo or Reset to try another way.")

    pick = state.hunt_pick
    if running and not numberhunt.is_stuck(game):
        if pick["first"] is None:
            prompt = "Tap a number."
        elif pick["op"] is None:
            prompt = f"{game.numbers[pick['first']]} … choose an operation."
        else:
            prompt = f"{game.numbers[pick['first']]} {pick['op']} … tap the second number."
        st.caption(prompt)

    with st.container(key="hunt_numbers"):
        columns = st.columns(max(len(game.numbers), 3))
        for position, number in enumerate(game.numbers):
            columns[position].button(
                str(number),
                key=f"hunt_num_{position}",
                type="primary" if pick["first"] == position else "secondary",
                on_click=on_hunt_number,
                args=(position,),
                disabled=not running,
                width="stretch",
            )
    with st.container(key="hunt_operations"):
        columns = st.columns(len(HUNT_OPERATIONS))
        for column, (name, op) in zip(columns, HUNT_OPERATIONS.items()):
            column.button(
                op,
                key=f"hunt_op_{name}",
                type="primary" if pick["op"] == op else "secondary",
                on_click=on_hunt_operation,
                args=(op,),
                disabled=not running or pick["first"] is None,
                width="stretch",
            )

    if game.steps:
        chips = "".join(f'<span class="hunt-step">{step.text}</span>' for step in game.steps)
        st.html(f'<div class="hunt-steps">{chips}</div>')

    undo_column, reset_column = st.columns(2)
    undo_column.button(
        "Undo (costs a life)",
        key="hunt_undo",
        on_click=on_hunt_undo,
        disabled=not running or not game.steps,
        width="stretch",
    )
    reset_column.button(
        "Reset (costs a life)",
        key="hunt_reset",
        on_click=on_hunt_reset,
        disabled=not running or not game.steps,
        width="stretch",
    )
    render_hunt_flash()


def render_games() -> None:
    st.header("Games", anchor=False)
    choice = st.selectbox("Game", GAMES, key="game_choice", on_change=on_game_change)
    st.subheader(choice, anchor=False)
    st.caption(f"Games: {', '.join(GAMES)} · Coming soon: {', '.join(COMING_SOON_GAMES)}")
    st.markdown(GAME_RULES[choice])

    level_column, button_column = st.columns([2, 1], vertical_alignment="bottom")
    game = state.get("game") or state.get("hunt")
    level_column.selectbox(
        "Level",
        LEVELS,
        index=LEVELS.index(game.level if game else LEVELS[0]),
        key="game_level",
    )
    button_column.button(
        "New game", key="new_game", type="primary", on_click=on_new_game, width="stretch"
    )

    if "hunt_pick" not in state:
        state.hunt_pick = {"first": None, "op": None}
    # Decided by the state key, not isinstance: Streamlit re-imports changed modules.
    if "hunt" in state:
        render_hunt(state.hunt)
    elif "game" in state:
        render_sudoku(state.game)


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
    elif section == "Games":
        render_games()
    else:
        render_coming_soon(section)


main()
