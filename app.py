"""Mathbuddy: Streamlit screens and navigation only."""

import math
import random
import secrets
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import accounts_db
import db
import trainer_ui
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
from accounts import (
    SIGN_IN_FAILED,
    User,
    hash_password,
    normalize_email,
    sign_up_problems,
    verify_password,
)
import knowledge_ui
from ui_components import (
    EXAMPLE_SEED,
    FLASH_COLORS,
    FLASH_MS,
    answer_flash,
    answer_focus,
    answer_form,
    example_box,
    pick,
)

SECTIONS = ["Tests", "Trainer", "Knowledge", "Games", "Profile"]
PASSWORD_HINT = "Use a password you don't use anywhere else."
TESTS_DESCRIPTION = "Solve as many tasks as you can in 60 seconds. Only correct answers count."
EXAMPLE_PROMPT = "Calculate"  # the Trainer's prompt for the basic operations
NO_VALUE = "–"
IGNORED_HINT = "Numbers only, e.g. 4250"
LIVES = sudoku.LIVES
SUDOKU_VARIANTS = {"Mini Sudoku": sudoku.MINI, "Sudoku": sudoku.CLASSIC}
GAMES = list(SUDOKU_VARIANTS)
COMING_SOON_GAMES = ["Number Hunt", "Magic Square"]
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
}

state = st.session_state


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def own_runs():
    """The signed in user's completed runs (spec 011)."""
    return accounts_db.list_runs_for(state.user.id)


# --- Accounts (spec 011) ---


def current_sign_up_problems() -> list[str]:
    username = state.get("signup_username", "").strip()
    email = normalize_email(state.get("signup_email", ""))
    return sign_up_problems(
        username,
        email,
        state.get("signup_password", ""),
        state.get("signup_repeat", ""),
        username_taken=accounts_db.username_taken(username),
        email_taken=accounts_db.email_taken(email),
    )


def on_sign_up_field_change() -> None:
    """Shown sign up errors follow the fields, so only errors that apply stay."""
    if state.get("account_errors") and state.account_errors != [SIGN_IN_FAILED]:
        state.account_errors = current_sign_up_problems()


def on_sign_up() -> None:
    username = state.signup_username.strip()
    email = normalize_email(state.signup_email)
    password = state.signup_password
    problems = current_sign_up_problems()
    if not problems:
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=hash_password(password, secrets.token_bytes(16)),
            created_at=utc_now(),
        )
        try:
            accounts_db.create_user(user)
        except ValueError:  # taken in the meantime by someone else
            problems = current_sign_up_problems()
        else:
            sign_in_as(user)
            return
    state.account_errors = problems


def on_sign_in() -> None:
    user = accounts_db.find_user(state.signin_username.strip())
    if user is None or not verify_password(state.signin_password, user.password_hash):
        state.account_errors = [SIGN_IN_FAILED]
        return
    sign_in_as(user)


def sign_in_as(user: User) -> None:
    for key in ("signin_password", "signup_password", "signup_repeat"):
        state.pop(key, None)
    state.pop("account_errors", None)
    state.user = user


def on_sign_out() -> None:
    on_nav_change()  # leaves a running test unsaved, like switching sections
    state.clear()


def render_sign_in() -> None:
    st.title("Mathbuddy", anchor=False)
    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])
    with sign_in_tab:
        st.text_input("Username", key="signin_username")
        st.text_input("Password", type="password", key="signin_password")
        st.button("Sign in", key="signin_submit", type="primary", on_click=on_sign_in)
    with sign_up_tab:
        changed = on_sign_up_field_change
        st.text_input("Username", key="signup_username", max_chars=20, on_change=changed)
        st.text_input("Email", key="signup_email", on_change=changed)
        st.text_input("Password", type="password", key="signup_password", on_change=changed)
        st.text_input("Repeat password", type="password", key="signup_repeat", on_change=changed)
        st.caption(PASSWORD_HINT)
        st.button("Create account", key="signup_submit", type="primary", on_click=on_sign_up)
    for message in state.get("account_errors", []):
        st.error(message)


def render_account_sidebar() -> None:
    with st.sidebar:
        name = state.user.username.replace("_", "\\_")  # "_" would turn text italic
        st.markdown(f"Signed in as {name}")
        st.button("Sign out", key="sign_out", on_click=on_sign_out)


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
    earlier = [saved for saved in own_runs() if saved.id != state.run_id]
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
    accounts_db.assign_run(state.run_id, state.user.id)
    state.result = {
        "run": run,
        "highscore": highscores(own_runs())[(run.test_type, run.level)],
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
    state.chosen_type = state.get("test_type") or TEST_TYPES[0]
    state.chosen_level = state.get("level") or LEVELS[0]
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
    knowledge_ui.leave()


# --- Games ---


def cell_key(row: int, col: int) -> str:
    return f"cell_{row}_{col}"


def clear_game() -> None:
    for key in [key for key in state if str(key).startswith("cell_")]:
        del state[key]  # no old entries in the next grid's fields
    state.pop("game", None)
    state.game_flash = None
    state.game_hint = False


def on_game_change() -> None:
    clear_game()  # nothing is saved, so the old game simply ends


def on_new_game() -> None:
    clear_game()
    variant = SUDOKU_VARIANTS[state.get("game_choice", GAMES[0])]
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


# --- Screens ---


def render_coming_soon(section: str) -> None:
    st.header(section, anchor=False)
    st.info("Coming soon")


def render_select() -> None:
    st.header("Tests", anchor=False)
    st.caption(TESTS_DESCRIPTION)
    operation = pick(st.pills, "Operation", TEST_TYPES, "test_type")
    level = pick(st.segmented_control, "Level", LEVELS, "level")
    # Display only: its own random generator, so it is not counted, not saved,
    # and not the first task of the test.
    example = generate_task(operation, level, random.Random(EXAMPLE_SEED))
    example_box(EXAMPLE_PROMPT, example.text)
    st.button("Start", key="start", type="primary", on_click=on_start)

    st.subheader("Highscores", anchor=False)
    best = highscores(own_runs())
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


def render_running() -> None:
    render_timer()
    st.header(state.current_task.text, anchor=False)
    answer_form("", on_submit, on_skip)

    if state.show_hint:
        st.warning(IGNORED_HINT)
    st.button("Abort test", key="abort", on_click=on_abort)

    answer_flash("", state.get("flash"), state.attempt)
    answer_focus("", state.attempt)


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


def render_games() -> None:
    st.header("Games", anchor=False)
    choice = st.selectbox("Game", GAMES, key="game_choice", on_change=on_game_change)
    st.subheader(choice, anchor=False)
    st.caption(f"Coming soon: {', '.join(COMING_SOON_GAMES)}")
    st.markdown(GAME_RULES[choice])

    level_column, button_column = st.columns([2, 1], vertical_alignment="bottom")
    game = state.get("game")
    level_column.selectbox(
        "Level",
        LEVELS,
        index=LEVELS.index(game.level if game else LEVELS[0]),
        key="game_level",
    )
    button_column.button(
        "New game", key="new_game", type="primary", on_click=on_new_game, width="stretch"
    )

    if game is not None:
        render_sudoku(game)


def use_online_database() -> None:
    """Copy the online database setting from .streamlit/secrets.toml, if there is one."""
    try:
        db.use_database_url_from(st.secrets)
    except FileNotFoundError:  # no secrets file: stay on the local SQLite file
        pass


def main() -> None:
    st.set_page_config(page_title="Mathbuddy")
    if "phase" not in state:  # once per session, so reruns during a test stay fast
        use_online_database()
        db.init_db()
        accounts_db.init_db()
        state.phase = "select"

    if "user" not in state:
        render_sign_in()
        return
    render_account_sidebar()

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
    elif section == "Knowledge":
        knowledge_ui.render()
    elif section == "Games":
        render_games()
    else:
        render_coming_soon(section)


main()
