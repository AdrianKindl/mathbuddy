"""Mathbuddy: Streamlit screens and navigation only."""

import math
import random
import secrets
import time
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import accounts_db
import activity_db
import db
import magicsquare
import numberchain
import numberhunt
import sudoku
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
from leaderboard import MIN_SCORE, TOP, Row, build
from stats import accuracy as overall_accuracy
from stats import last_7_days, longest_streak, tasks_completed
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
LEADERBOARD_COLUMNS = ["Rank", "Player", "Score"]  # MB06: no date shown
LEADERBOARD_EMPTY = "No runs yet for this operation and level."
OWN_ROW_STYLE = "background-color: rgba(255, 75, 75, 0.15); font-weight: 600"
APP_TIME_ZONE = ZoneInfo("Europe/Lisbon")  # calendar days for streak and chart (spec 012)
PROFILE_EMPTY = "Complete a test, training, practice round or game to see your statistics here."
IGNORED_HINT = "Numbers only, e.g. 4250"
LIVES = sudoku.LIVES
SUDOKU_VARIANTS = {"Mini Sudoku": sudoku.MINI, "Sudoku": sudoku.CLASSIC}
GAMES = [*SUDOKU_VARIANTS, "Number Hunt", "Magic Square", "Number Chain"]
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
    "Magic Square": (
        "Fill the grid so that every row, every column and both diagonals add up to the "
        "target sum. Tap an empty cell, then a number: the keypad only offers the numbers "
        "you still need. A wrong number costs one of your 3 lives."
    ),
    "Number Chain": (
        "A start number appears, then one step after another, e.g. + 8, × 3, − 9. "
        "Calculate along in your head and type the result. Every right result is a point "
        "and makes the next chain one step longer. A wrong result costs one of your 3 lives."
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
    for name in (
        "game", "hunt", "hunt_message", "magic", "magic_pick", "magic_message",
        "chain", "chain_rng", "chain_phase", "chain_feedback", "chain_hint", "game_id",
    ):
        state.pop(name, None)
    state.game_flash = None
    state.game_hint = False
    state.hunt_pick = {"first": None, "op": None}


def on_end_game() -> None:
    """Like "End training" in the Trainer: the game ends and is not saved (spec 002g, 012)."""
    clear_game()


def on_try_again() -> None:
    """After Game over: the same puzzle again with 3 lives (spec 002h)."""
    hunt = state.get("hunt")
    magic = state.get("magic")
    chain = state.get("chain")
    game = state.get("game")
    clear_game()
    if hunt is not None:
        state.hunt = numberhunt.Game(
            level=hunt.level, puzzle=hunt.puzzle, numbers=hunt.puzzle.numbers
        )
    elif magic is not None:
        state.magic = magicsquare.Game(
            level=magic.level, puzzle=magic.puzzle, grid=magic.puzzle.givens
        )
    elif chain is not None:  # a chain has no fixed puzzle: start over at the same level
        state.chain_rng = random.Random()
        state.chain = numberchain.start_game(chain.level, state.chain_rng)
        state.chain_phase = "ready"
    elif game is not None:
        state.game = sudoku.Game(
            level=game.level, puzzle=game.puzzle, grid=game.puzzle.givens, started_at=utc_now()
        )
    state.game_id = str(uuid.uuid4())  # a new game, saved on its own when it ends


def current_game():
    """The game that is shown, whichever kind it is, or None."""
    for key in ("hunt", "magic", "chain", "game"):
        if key in state:
            return state[key]
    return None


def on_game_change() -> None:
    clear_game()  # a game that has not ended is not saved, so it simply ends


def save_game_if_over() -> None:
    """A game that ended (won or lost) counts as an activity; saved once (spec 012)."""
    game = current_game()
    if game is None or game.status == "running" or "game_id" not in state:
        return
    choice = state.get("game_choice", GAMES[0])
    activity_db.save_game(state.game_id, state.user.id, choice, game.level, utc_now(), str(game.status))


def on_new_game() -> None:
    clear_game()
    choice = state.get("game_choice", GAMES[0])
    if choice == "Number Hunt":
        state.hunt = numberhunt.start_game(state.game_level, random.Random())
    elif choice == "Magic Square":
        state.magic = magicsquare.start_game(state.game_level, random.Random())
    elif choice == "Number Chain":
        state.chain_rng = random.Random()
        state.chain = numberchain.start_game(state.game_level, state.chain_rng)
        state.chain_phase = "ready"
    else:
        variant = SUDOKU_VARIANTS[choice]
        state.game = sudoku.start_game(state.game_level, random.Random(), variant, utc_now())
    state.game_id = str(uuid.uuid4())


def on_cell(row: int, col: int) -> None:
    key = cell_key(row, col)
    raw = state[key]
    game, outcome = sudoku.enter_number(state.game, row, col, raw, utc_now())
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


def on_magic_cell(row: int, col: int) -> None:
    # Tapping the selected cell again unselects it.
    state.magic_pick = None if state.get("magic_pick") == (row, col) else (row, col)
    state.magic_message = None


def on_magic_key(value: int) -> None:
    cell = state.get("magic_pick")
    if cell is None:
        state.magic_message = "Tap an empty cell first."
        return
    game, outcome = magicsquare.enter_number(state.magic, *cell, value)
    state.magic = game
    state.magic_pick = None
    state.magic_message = None
    state.game_attempt = state.get("game_attempt", 0) + 1
    state.game_flash = cell if outcome == magicsquare.Outcome.WRONG else None


def on_chain_start() -> None:
    state.chain_phase = "showing"
    state.chain_feedback = None


def on_chain_submit() -> None:
    game, outcome = numberchain.answer(state.chain, state.chain_answer, state.chain_rng)
    state.chain_hint = outcome == numberchain.Outcome.IGNORED
    if outcome == numberchain.Outcome.IGNORED:
        return
    state.chain = game
    state.chain_feedback = outcome
    state.chain_phase = "ready"


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

    render_highscores()
    # Only the Tests tab has a leaderboard, and only here are the selected
    # operation and level known (spec 014). The Profile shows the highscores alone.
    render_leaderboard(operation, level)


def render_highscores() -> None:
    """The signed in player's highscores (MB R6), on the Tests tab and the Profile."""
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


def leaderboard_cells(row: Row) -> list[str]:
    player = f"{row.username} (you)" if row.is_you else row.username
    return [str(row.rank), player, str(row.value)]


def render_leaderboard(operation: str, level: str) -> None:
    """MB06: the all-time leaderboard for the selected operation and level."""
    st.subheader("Leaderboard", anchor=False)
    st.caption(f"All-time top {TOP} · {operation} · {level}")
    board = build(
        db.leaderboard_entries(operation, level), user_id=state.user.id, at_least=MIN_SCORE
    )
    if not board.top:
        st.caption(LEADERBOARD_EMPTY)
        return

    rows = [leaderboard_cells(row) for row in board.top]
    marked = [row.is_you for row in board.top]
    if board.own is not None:  # the signed-in user ranks below the top 15
        rows += [["…", "", ""], leaderboard_cells(board.own)]
        marked += [False, True]
    frame = pd.DataFrame(rows, columns=LEADERBOARD_COLUMNS)
    styled = frame.style.apply(
        lambda line: [OWN_ROW_STYLE if marked[line.name] else ""] * len(line), axis=1
    ).hide(axis="index")
    st.table(styled)


def days_text(days: int) -> str:
    return f"{days} day" if days == 1 else f"{days} days"


def render_profile() -> None:
    """MB05: the signed in player's statistics, calculated from saved activities (MB R8)."""
    st.header("Profile", anchor=False)
    st.markdown(state.user.username.replace("_", "\\_"))  # "_" would turn text italic
    activities = activity_db.list_activities_for(state.user.id)
    share = overall_accuracy(activities)
    tasks_column, accuracy_column, streak_column = st.columns(3)
    tasks_column.metric("Tasks completed", str(tasks_completed(activities)))
    accuracy_column.metric("Accuracy", NO_VALUE if share is None else f"{round(100 * share)}%")
    streak_column.metric("Longest streak", days_text(longest_streak(activities, APP_TIME_ZONE)))
    if not activities:
        st.info(PROFILE_EMPTY)

    render_highscores()

    st.subheader("Last 7 days", anchor=False)
    today = datetime.now(APP_TIME_ZONE).date()
    days = last_7_days(activities, today, APP_TIME_ZONE)
    chart = pd.DataFrame(
        {"Activities": [count for _, count in days]},
        index=[day.strftime("%a") for day, _ in days],
    )
    st.bar_chart(chart, x_label="Day", y_label="Activities", sort=False)


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
.st-key-sudoku_header [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.st-key-sudoku_header [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
    flex: 1 1 0 !important;
}
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


@st.fragment(run_every="1s")
def render_sudoku_clock() -> None:
    """Only this part refreshes every second, so typing into the grid is not disturbed."""
    game = state.get("game")
    if game is None:
        return
    seconds = sudoku.elapsed_seconds(game, utc_now())
    st.metric("Time", NO_VALUE if seconds is None else sudoku.clock_text(seconds))


def render_sudoku(game: sudoku.Game) -> None:
    variant = sudoku.variant_of(game.grid)
    with st.container(key="sudoku_header"):
        lives_column, time_column = st.columns(2)
        with lives_column:
            render_lives(game.lives)
        with time_column:
            if game.status == sudoku.Status.RUNNING:
                render_sudoku_clock()
            else:  # the stopwatch has stopped: no need to refresh it
                seconds = sudoku.elapsed_seconds(game, utc_now())
                st.metric("Time", NO_VALUE if seconds is None else sudoku.clock_text(seconds))

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


MAGIC_CSS = """<style>
.st-key-magic_header [data-testid="stHorizontalBlock"],
.st-key-magic_grid [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.4rem;
}
.st-key-magic_header [data-testid="stColumn"],
.st-key-magic_grid [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
    flex: 1 1 0 !important;
}
.st-key-magic_grid { gap: 0.4rem; }
.st-key-magic_grid button, .st-key-magic_grid .sudoku-cell { height: 3.2rem; min-height: 3.2rem; }
.st-key-magic_grid button p, .st-key-magic_grid .sudoku-cell,
.st-key-magic_keypad button p {
    font-size: 1.3rem;
    font-weight: 700;
}
.st-key-magic_keypad [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.4rem;
}
.st-key-magic_keypad [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
    flex: 0 0 3.4rem !important;
}
.st-key-magic_keypad button { min-height: 3rem; padding: 0; }
/* The selected cell is blue: red means a wrong entry. */
.st-key-magic_grid button[kind="primary"] {
    background: rgb(37, 99, 235);
    border-color: rgb(37, 99, 235);
    color: white;
}
</style>"""


def render_magic_flash() -> None:
    cell = state.get("game_flash")
    if not isinstance(cell, tuple):
        return
    name = f"magic-flash-{state.game_attempt}"
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
        .st-key-magic_cell_{cell[0]}_{cell[1]} button {{
            animation: {name} {FLASH_MS}ms ease-out;
        }}
        </style>"""
    )


def render_magic(game: magicsquare.Game) -> None:
    size = len(game.grid)
    running = game.status == magicsquare.Status.RUNNING
    st.html(SUDOKU_CSS + MAGIC_CSS + f"<style>.st-key-magic_grid {{ max-width: {size * 4.6}rem; }}</style>")

    with st.container(key="magic_header"):
        target_column, lives_column = st.columns(2)
        with target_column:
            st.metric("Target sum", game.puzzle.target)
        with lives_column:
            render_lives(game.lives)

    if game.status == magicsquare.Status.WON:
        st.success("You solved it!")
    elif game.status == magicsquare.Status.LOST:
        st.markdown(
            "### :red[Game over]\nNo lives left. The missing numbers are shown in red."
        )
    elif state.get("magic_message"):
        st.warning(state.magic_message)
    elif state.get("magic_pick") is None:
        st.caption("Tap an empty cell.")
    else:
        st.caption("Now tap the number for the blue cell.")

    pick = state.get("magic_pick")
    with st.container(key="magic_grid"):
        for row in range(size):
            columns = st.columns(size)
            for col in range(size):
                given = game.puzzle.givens[row][col]
                value = game.grid[row][col]
                if given or value:
                    kind = "given" if given else "correct"
                    columns[col].html(f'<div class="sudoku-cell sudoku-{kind}">{value}</div>')
                elif not running:
                    missed = game.puzzle.solution[row][col]
                    columns[col].html(f'<div class="sudoku-cell sudoku-missed">{missed}</div>')
                else:
                    columns[col].button(
                        "?",
                        key=f"magic_cell_{row}_{col}",
                        type="primary" if pick == (row, col) else "secondary",
                        on_click=on_magic_cell,
                        args=(row, col),
                        width="stretch",
                    )

    if running:
        numbers = magicsquare.keypad(game)
        with st.container(key="magic_keypad"):
            columns = st.columns(len(numbers))
            for column, number in zip(columns, numbers):
                column.button(
                    str(number),
                    key=f"magic_key_{number}",
                    on_click=on_magic_key,
                    args=(number,),
                    width="stretch",
                )
    render_magic_flash()


CHAIN_CSS = """<style>
.chain-big {
    font-size: 4rem;
    font-weight: 800;
    text-align: center;
    padding: 1.5rem 0;
}
.st-key-chain_header [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.st-key-chain_header [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
    flex: 1 1 0 !important;
}
</style>"""


def render_chain_showing(game: numberchain.Game) -> None:
    """Show the start number and each step for a few seconds, then ask for the result."""
    seconds = numberchain.LEVEL_SETTINGS[game.level].seconds
    chain = game.chain
    big = st.empty()
    progress = st.empty()
    # While this script sleeps, the elements of the previous screen would stay
    # visible below. Empty placeholders overwrite them.
    for _ in range(8):
        st.empty()

    shown = [(f"Start: {chain.start}", "Remember this number.")]
    total = len(chain.steps)
    shown += [(step.text, f"Step {k} of {total}") for k, step in enumerate(chain.steps, 1)]
    for text, caption in shown:
        big.html(f'<div class="chain-big">{text}</div>')
        progress.caption(caption)
        time.sleep(seconds)
    state.chain_phase = "answer"
    st.rerun()


def render_chain(game: numberchain.Game) -> None:
    st.html(CHAIN_CSS)
    phase = state.get("chain_phase", "ready")
    if phase == "showing":
        render_chain_showing(game)
        return

    with st.container(key="chain_header"):
        lives_column, score_column, length_column = st.columns(3)
        with lives_column:
            render_lives(game.lives)
        score_column.metric("Score", game.score)
        length_column.metric("Steps", len(game.chain.steps))

    feedback = state.get("chain_feedback")
    if game.status == numberchain.Status.LOST:
        st.markdown(
            f"### :red[Game over]\nThe result was {game.last_result}. "
            f"You solved {game.score} chain{'' if game.score == 1 else 's'}."
        )
        return
    if feedback == numberchain.Outcome.CORRECT:
        st.success(f"Right! The result was {game.last_result}.")
    elif feedback == numberchain.Outcome.WRONG:
        st.warning(f"Not quite: the result was {game.last_result}. That cost a life.")

    if phase == "answer":
        with st.form("chain_form", clear_on_submit=True, border=False):
            st.text_input("Your result", key="chain_answer", autocomplete="off")
            st.form_submit_button(
                "Submit", key="chain_submit", type="primary", on_click=on_chain_submit
            )
        if state.get("chain_hint"):
            st.warning("Numbers only, e.g. 42")
    else:
        label = "Start chain" if game.score == 0 and feedback is None else "Next chain"
        st.button(label, key="chain_start", type="primary", on_click=on_chain_start)
        st.caption(
            f"{len(game.chain.steps)} steps, "
            f"{numberchain.LEVEL_SETTINGS[game.level].seconds:g} seconds each."
        )


def render_games() -> None:
    st.header("Games", anchor=False)
    choice = st.selectbox("Game", GAMES, key="game_choice", on_change=on_game_change)
    st.subheader(choice, anchor=False)
    st.caption(f"Games: {', '.join(GAMES)}")
    st.markdown(GAME_RULES[choice])

    level_column, button_column = st.columns([2, 1], vertical_alignment="bottom")
    game = state.get("game") or state.get("hunt") or state.get("magic") or state.get("chain")
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
    elif "magic" in state:
        render_magic(state.magic)
    elif "chain" in state:
        render_chain(state.chain)
    elif "game" in state:
        render_sudoku(state.game)

    # Every game's Status has RUNNING = "running"; compared by value, as in runs.py.
    save_game_if_over()
    game = current_game()
    if game is not None and game.status == "running":
        st.button("End game", key="end_game", on_click=on_end_game)
    elif game is not None and game.status == "lost":
        st.button("Try again", key="try_again", type="primary", on_click=on_try_again)

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
        activity_db.init_db()
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
    elif section == "Profile":
        render_profile()
    else:
        render_coming_soon(section)


main()
