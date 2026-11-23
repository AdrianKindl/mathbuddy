"""Screens and wiring in app.py, driven through Streamlit's AppTest.

AppTest does not run a browser, so these need a manual check in the PR:
the live timer ticking, the end of a run without any click, the green and red
flash, cursor focus, the field clearing after submit, cancelling during the
countdown, and a real Ctrl+C restart.
"""

import re
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.proto.ButtonGroup_pb2 import ButtonGroup as ButtonGroupProto

import accounts_db
import db
from conftest import TEST_USER

APP = Path(__file__).resolve().parent.parent / "app.py"
TEST_TYPES = ["Addition", "Subtraction", "Multiplication", "Division", "Random"]
LEVELS = ["Easy", "Medium", "Hard", "Pro"]
NO_HIGHSCORE = "–"
FINISHED = datetime(2026, 11, 3, 12, 1, 0, tzinfo=timezone.utc)
TESTS_DESCRIPTION = "Solve as many tasks as you can in 60 seconds. Only correct answers count."
SIGNS = {"Addition": "+", "Subtraction": "−", "Multiplication": "×", "Division": "÷"}
ADDITION_RANGES = {"Easy": (1, 19), "Medium": (20, 249), "Hard": (250, 1249), "Pro": (1250, 5000)}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))


@pytest.fixture
def fast_sleep(monkeypatch):
    """Keep the 3-second countdown from slowing down every test."""
    real_sleep = time.sleep
    monkeypatch.setattr(time, "sleep", lambda seconds: real_sleep(min(seconds, 0.01)))


def open_app():
    at = AppTest.from_file(APP, default_timeout=10).run()
    assert not at.exception
    return at


def start_test(at, test_type="Multiplication", level="Easy"):
    at.button_group(key="test_type").set_value(test_type)
    at.button_group(key="level").set_value(level)
    at.button(key="start").click().run()
    assert not at.exception
    return at


def go_to(at, section):
    at.radio(key="nav").set_value(section).run()
    assert not at.exception


def submit(at, text):
    at.text_input(key="answer").input(text)
    at.button(key="submit").click().run()
    assert not at.exception


def out_of_time(at, **totals):
    """Move the running test's start 61 seconds back, without any rerun yet."""
    started = datetime.now(timezone.utc) - timedelta(seconds=61)
    at.session_state["run"] = replace(at.session_state["run"], started_at=started, **totals)


def finish_run(at, **totals):
    out_of_time(at, **totals)
    at.run()
    assert not at.exception


def page_text(at):
    groups = (at.title, at.header, at.subheader, at.markdown, at.text, at.caption, at.success, at.info)
    return "\n".join(str(element.value) for group in groups for element in group)


def metrics(at):
    return {metric.label: metric.value for metric in at.metric}


def highscore_table(at):
    """The full highscore table: on the Profile since spec 015."""
    return at.table[0].value


def your_best(at, test_type="Multiplication", level="Easy"):
    """The Tests tab's best score for one test type and level (spec 015)."""
    at.button_group(key="test_type").set_value(test_type)
    at.button_group(key="level").set_value(level)
    at.run()
    assert not at.exception
    return metrics(at)["Your best"]


def seed_run(run_id, level, correct):
    db.init_db()
    db.save_run(run_id, "Multiplication", level, FINISHED, correct, 0, 0)
    accounts_db.init_db()  # since 011: runs belong to the signed in test user
    accounts_db.assign_run(run_id, TEST_USER.id)


# --- Navigation (MB01) ---


def test_navigation_shows_the_five_sections():
    assert list(open_app().radio(key="nav").options) == [
        "Tests",
        "Trainer",
        "Knowledge",
        "Games",
        "Profile",
    ]


def test_tests_is_the_first_screen_and_is_built():
    at = open_app()
    assert at.radio(key="nav").value == "Tests"
    assert "Coming soon" not in page_text(at)


def test_profile_section_is_built():  # since spec 012; Games is built since 002d
    at = open_app()
    go_to(at, "Profile")
    assert "Coming soon" not in page_text(at)


def test_games_section_is_built():
    at = open_app()
    go_to(at, "Games")
    assert "Coming soon" not in page_text(at)


# --- Tests screen (decision 11) ---


def test_pickers_offer_five_test_types_and_four_levels():
    at = open_app()
    assert list(at.button_group(key="test_type").options) == TEST_TYPES
    assert list(at.button_group(key="level").options) == LEVELS


def test_highscore_table_has_all_20_cells_and_shows_a_dash_when_empty():
    at = open_app()
    go_to(at, "Profile")  # the full table is on the Profile since spec 015
    table = highscore_table(at)
    assert list(table.index) == TEST_TYPES
    assert list(table.columns) == LEVELS
    assert all(table.loc[t, level] == NO_HIGHSCORE for t in TEST_TYPES for level in LEVELS)


# --- Tests screen design (spec 008) ---


def choose(at, key, value):
    """Pick one option of a row of pills or of a segmented control."""
    at.button_group(key=key).set_value(value).run()
    assert not at.exception


def example_task(at):
    """The text of the example task box on the Tests screen."""
    assert any("Example task" in caption.value for caption in at.caption)
    bold = [md.value for md in at.markdown if md.value.startswith("**") and md.value.endswith("**")]
    assert len(bold) == 1
    return bold[0].strip("*")


def numbers_in(text):
    return [int(part.replace(",", "")) for part in text.split() if part.replace(",", "").isdigit()]


def test_tests_screen_shows_the_description():
    assert TESTS_DESCRIPTION in [caption.value for caption in open_app().caption]


def test_operation_buttons_offer_five_operations_with_addition_first():
    picker = open_app().button_group(key="test_type")
    assert picker.proto.label == "Operation"
    assert list(picker.options) == TEST_TYPES
    assert picker.value == "Addition"


def test_level_buttons_offer_four_levels_with_easy_first():
    picker = open_app().button_group(key="level")
    assert picker.proto.label == "Level"
    assert list(picker.options) == LEVELS
    assert picker.value == "Easy"


def test_tests_uses_the_same_controls_as_the_trainer():
    at = open_app()
    operation_style = at.button_group(key="test_type").proto.style
    level_style = at.button_group(key="level").proto.style
    go_to(at, "Trainer")
    assert operation_style == at.button_group(key="tr_operation").proto.style
    assert level_style == at.button_group(key="tr_level").proto.style
    assert operation_style == ButtonGroupProto.Style.PILLS
    assert level_style == ButtonGroupProto.Style.SEGMENTED_CONTROL


def test_tests_screen_has_no_dropdown_and_no_mode():
    at = open_app()
    assert len(at.selectbox) == 0
    assert len(at.number_input) == 0


@pytest.mark.parametrize("operation", list(SIGNS))
def test_example_task_follows_the_selected_operation(operation):
    at = open_app()
    choose(at, "test_type", operation)
    assert SIGNS[operation] in example_task(at)


def test_example_task_for_random_uses_one_of_the_four_operations():
    at = open_app()
    choose(at, "test_type", "Random")
    assert any(sign in example_task(at) for sign in SIGNS.values())


@pytest.mark.parametrize("level", LEVELS)
def test_example_task_follows_the_selected_level(level):
    at = open_app()
    choose(at, "level", level)
    low, high = ADDITION_RANGES[level]
    numbers = numbers_in(example_task(at))
    assert len(numbers) == 2
    assert all(low <= number <= high for number in numbers)


def test_example_task_stays_the_same_until_the_selection_changes():
    at = open_app()
    first = example_task(at)
    at.run()
    assert example_task(at) == first
    choose(at, "test_type", "Multiplication")
    assert example_task(at) != first


def test_choosing_and_viewing_examples_saves_nothing():
    at = open_app()
    for operation in TEST_TYPES:
        choose(at, "test_type", operation)
    for level in LEVELS:
        choose(at, "level", level)
    assert db.list_runs() == []
    assert "run" not in at.session_state


def test_start_uses_the_selected_operation_and_level(fast_sleep):
    at = start_test(open_app(), "Division", "Pro")
    run = at.session_state["run"]
    assert (run.test_type, run.level) == ("Division", "Pro")
    assert at.session_state["current_task"].operation == "Division"


def test_selection_is_remembered_after_aborting(fast_sleep):
    at = start_test(open_app(), "Division", "Pro")
    at.button(key="abort").click().run()
    assert not at.exception
    assert at.button_group(key="test_type").value == "Division"
    assert at.button_group(key="level").value == "Pro"


# --- Running test (MB02, MB03) ---


def test_starting_shows_a_task_and_the_timer(fast_sleep):
    at = start_test(open_app())
    assert at.session_state["current_task"].text in page_text(at)
    assert "Time left" in metrics(at)


def test_countdown_runs_before_the_60_seconds_start():
    at = open_app()
    clicked = datetime.now(timezone.utc)
    start_test(at)
    assert at.session_state["run"].started_at - clicked >= timedelta(seconds=2.9)


def test_correct_answer_adds_a_point_and_shows_a_new_task(fast_sleep):
    at = start_test(open_app())
    task = at.session_state["current_task"]
    submit(at, str(task.answer))
    assert at.session_state["run"].correct == 1
    assert at.session_state["current_task"] != task


def test_wrong_answer_is_counted_and_shows_a_new_task(fast_sleep):
    at = start_test(open_app())
    task = at.session_state["current_task"]
    submit(at, str(task.answer + 1))
    assert at.session_state["run"].wrong == 1
    assert at.session_state["run"].correct == 0
    assert at.session_state["current_task"] != task


@pytest.mark.parametrize("text", ["", "abc", "5.5"])
def test_empty_or_non_numeric_input_keeps_the_same_task(fast_sleep, text):
    at = start_test(open_app())
    task = at.session_state["current_task"]
    run = at.session_state["run"]
    submit(at, text)
    assert at.session_state["run"] == run
    assert at.session_state["current_task"] == task


def test_skip_is_recorded_and_shows_a_new_task(fast_sleep):
    at = start_test(open_app())
    task = at.session_state["current_task"]
    at.button(key="skip").click().run()
    assert not at.exception
    assert at.session_state["run"].skipped == 1
    assert at.session_state["run"].wrong == 0
    assert at.session_state["current_task"] != task


# --- Aborted runs (MB R5, decision 8) ---


def test_aborted_run_saves_nothing_and_returns_to_the_tests_screen(fast_sleep):
    at = start_test(open_app())
    submit(at, str(at.session_state["current_task"].answer))
    at.button(key="abort").click().run()
    assert not at.exception

    assert db.list_runs() == []
    assert your_best(at) == NO_HIGHSCORE


def test_leaving_the_section_during_a_run_saves_nothing(fast_sleep):
    at = start_test(open_app())
    go_to(at, "Profile")
    assert at.radio(key="nav").value == "Profile"  # left the run; Profile is built since 012
    go_to(at, "Tests")

    assert db.list_runs() == []
    assert at.button_group(key="test_type").options  # back on the choice screen, not in the run


# --- Completed runs (MB04, MB R4, MB R5, A5) ---


def test_completed_run_is_saved_and_the_result_is_shown(fast_sleep):
    at = start_test(open_app())
    started = at.session_state["run"]
    finish_run(at, correct=12, wrong=3, skipped=2)

    saved = db.list_runs()
    assert len(saved) == 1
    assert (saved[0].test_type, saved[0].level) == ("Multiplication", "Easy")
    assert (saved[0].correct, saved[0].wrong, saved[0].skipped) == (12, 3, 2)
    assert saved[0].finished_at.utcoffset() == timedelta(0)
    assert saved[0].finished_at != started.started_at

    shown = metrics(at)
    assert shown["Score"] == "12"
    assert shown["Wrong"] == "3"
    assert shown["Skipped"] == "2"
    assert shown["Accuracy"] == "70.6%"
    assert shown["Highscore"] == "12"


def test_run_is_saved_only_once(fast_sleep):
    at = start_test(open_app())
    finish_run(at, correct=5)
    at.run()
    at.run()
    assert not at.exception
    assert len(db.list_runs()) == 1


def test_answer_after_the_limit_does_not_count_and_ends_the_run(fast_sleep):
    at = start_test(open_app())
    task = at.session_state["current_task"]
    out_of_time(at, correct=4)
    submit(at, str(task.answer))

    saved = db.list_runs()
    assert len(saved) == 1
    assert saved[0].correct == 4
    assert metrics(at)["Score"] == "4"


def test_abort_after_the_limit_saves_the_run(fast_sleep):
    at = start_test(open_app())
    out_of_time(at, correct=4)
    at.button(key="abort").click().run()
    assert not at.exception
    assert [run.correct for run in db.list_runs()] == [4]


def test_run_without_attempts_is_saved_and_shows_a_dash_for_accuracy(fast_sleep):
    at = start_test(open_app())
    finish_run(at)
    assert len(db.list_runs()) == 1
    assert metrics(at)["Accuracy"] == "–"
    assert "new highscore" not in page_text(at).lower()


# --- Highscore (MB R6, A6, decision 6) ---


def test_first_run_above_zero_is_a_new_highscore(fast_sleep):
    at = start_test(open_app())
    finish_run(at, correct=1)
    assert "new highscore" in page_text(at).lower()


def test_lower_score_leaves_the_highscore_unchanged(fast_sleep):
    seed_run("seed", "Easy", 15)
    at = start_test(open_app())
    finish_run(at, correct=12)
    assert metrics(at)["Highscore"] == "15"
    assert "new highscore" not in page_text(at).lower()


def test_tie_is_not_a_new_highscore(fast_sleep):
    seed_run("seed", "Easy", 15)
    at = start_test(open_app())
    finish_run(at, correct=15)
    assert metrics(at)["Highscore"] == "15"
    assert "new highscore" not in page_text(at).lower()


def test_higher_score_is_shown_as_a_new_highscore(fast_sleep):
    seed_run("seed", "Easy", 15)
    at = start_test(open_app())
    finish_run(at, correct=18)
    assert metrics(at)["Highscore"] == "18"
    assert "new highscore" in page_text(at).lower()


def test_medium_run_does_not_change_the_easy_highscore_on_screen(fast_sleep):
    seed_run("seed", "Easy", 15)
    at = start_test(open_app(), level="Medium")
    finish_run(at, correct=30)
    at.button(key="back").click().run()
    assert not at.exception

    assert your_best(at, level="Easy") == "15"
    assert your_best(at, level="Medium") == "30"


def test_highscore_is_still_shown_after_a_restart(fast_sleep):
    at = start_test(open_app())
    finish_run(at, correct=9)

    reopened = open_app()  # a new session on the same database file
    assert your_best(reopened) == "9"


# --- Structure (AGENTS.md) ---


def test_app_contains_no_sql():
    source = APP.read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "SELECT " not in source


# --- Games: Mini Sudoku (spec 002) ---

GAMES = ["Mini Sudoku", "Sudoku", "Number Hunt", "Magic Square"]
EMPTY_CELLS = {"Easy": 12, "Medium": 16, "Hard": 20, "Pro": 24}


def open_game(at, choice):
    """Open a game from its tile on the Games overview (spec 002i)."""
    at.button(key="game_tile_" + choice.lower().replace(" ", "_")).click().run()
    assert not at.exception


def game_tiles(at):
    """The game tiles on the Games overview, in order (spec 002i)."""
    return [button.label for button in at.button if (button.key or "").startswith("game_tile_")]


def start_game(level="Easy"):
    at = open_app()
    go_to(at, "Games")
    open_game(at, "Mini Sudoku")
    at.selectbox(key="game_level").set_value(level)
    at.button(key="new_game").click().run()
    assert not at.exception
    return at


def cell_keys(at):
    return {box.key for box in at.text_input if box.key.startswith("cell_")}


def first_empty_cell(at):
    game = at.session_state["game"]
    for r, row in enumerate(game.grid):
        for c, value in enumerate(row):
            if value == 0:
                return r, c, game.puzzle.solution[r][c]
    raise AssertionError("no empty cell")


def enter(at, row, col, text):
    at.text_input(key=f"cell_{row}_{col}").input(text).run()
    assert not at.exception


def wrong_digit(right):
    return str(right % 6 + 1)


def test_games_section_lists_all_four_games():
    at = open_app()
    go_to(at, "Games")
    text = page_text(at)
    for game in GAMES:
        assert game in text


def test_games_section_offers_the_four_levels():
    at = open_app()
    go_to(at, "Games")
    open_game(at, "Mini Sudoku")
    assert list(at.selectbox(key="game_level").options) == LEVELS


@pytest.mark.parametrize("level", LEVELS)
def test_new_game_shows_one_input_per_empty_cell_and_three_lives(level):
    at = start_game(level)
    assert len(cell_keys(at)) == EMPTY_CELLS[level]
    assert metrics(at)["Lives"] == "3"


def test_correct_entry_locks_the_cell_and_keeps_the_lives():
    at = start_game()
    row, col, right = first_empty_cell(at)
    enter(at, row, col, str(right))
    assert f"cell_{row}_{col}" not in cell_keys(at)
    assert len(cell_keys(at)) == EMPTY_CELLS["Easy"] - 1
    assert metrics(at)["Lives"] == "3"


def test_wrong_entry_lowers_the_lives_on_screen():
    at = start_game()
    row, col, right = first_empty_cell(at)
    enter(at, row, col, wrong_digit(right))
    assert metrics(at)["Lives"] == "2"
    assert f"cell_{row}_{col}" in cell_keys(at)


def test_non_numeric_entry_costs_no_life():
    at = start_game()
    row, col, _ = first_empty_cell(at)
    enter(at, row, col, "x")
    assert metrics(at)["Lives"] == "3"


def test_three_wrong_entries_show_game_over():
    at = start_game()
    row, col, right = first_empty_cell(at)
    for _ in range(3):
        enter(at, row, col, wrong_digit(right))
    assert "Game over" in page_text(at)
    assert not cell_keys(at)


def test_solving_every_cell_shows_you_solved_it():
    at = start_game()
    for _ in range(EMPTY_CELLS["Easy"]):
        row, col, right = first_empty_cell(at)
        enter(at, row, col, str(right))
    assert "You solved it!" in page_text(at)
    assert metrics(at)["Lives"] == "3"


def test_a_new_game_starts_fresh_after_game_over():
    at = start_game()
    row, col, right = first_empty_cell(at)
    for _ in range(3):
        enter(at, row, col, wrong_digit(right))
    at.button(key="new_game").click().run()
    assert metrics(at)["Lives"] == "3"
    assert len(cell_keys(at)) == EMPTY_CELLS["Easy"]


# --- Games: Sudoku 9×9 (spec 002b) ---

SUDOKU_EMPTY_CELLS = {"Easy": 36, "Medium": 42, "Hard": 48, "Pro": 52}


def start_sudoku(level="Easy"):
    at = open_app()
    go_to(at, "Games")
    open_game(at, "Sudoku")
    at.selectbox(key="game_level").set_value(level)
    at.button(key="new_game").click().run()
    assert not at.exception
    return at


def test_games_picker_offers_both_sudokus():
    at = open_app()
    go_to(at, "Games")
    assert game_tiles(at)[:2] == ["Mini Sudoku", "Sudoku"]


@pytest.mark.parametrize("level", LEVELS)
def test_new_sudoku_shows_one_input_per_empty_cell_and_three_lives(level):
    at = start_sudoku(level)
    assert len(at.session_state["game"].grid) == 9
    assert len(cell_keys(at)) == SUDOKU_EMPTY_CELLS[level]
    assert metrics(at)["Lives"] == "3"


def test_sudoku_correct_entry_locks_the_cell():
    at = start_sudoku()
    row, col, right = first_empty_cell(at)
    enter(at, row, col, str(right))
    assert f"cell_{row}_{col}" not in cell_keys(at)
    assert metrics(at)["Lives"] == "3"


def test_sudoku_accepts_a_nine():
    at = start_sudoku()
    game = at.session_state["game"]
    row, col = next(
        (r, c) for r in range(9) for c in range(9)
        if game.grid[r][c] == 0 and game.puzzle.solution[r][c] == 9
    )
    enter(at, row, col, "9")
    assert f"cell_{row}_{col}" not in cell_keys(at)
    assert metrics(at)["Lives"] == "3"


def test_sudoku_three_wrong_entries_show_game_over():
    at = start_sudoku()
    row, col, right = first_empty_cell(at)
    for _ in range(3):
        enter(at, row, col, str(right % 9 + 1))
    assert "Game over" in page_text(at)
    assert not cell_keys(at)


def test_changing_the_game_ends_the_current_one():
    at = start_sudoku()
    at.button(key="games_back").click().run()
    open_game(at, "Mini Sudoku")
    assert "game" not in at.session_state
    assert not cell_keys(at)


# --- Games: Number Hunt (spec 002c) ---


def start_hunt(level="Easy"):
    at = open_app()
    go_to(at, "Games")
    open_game(at, "Number Hunt")
    at.selectbox(key="game_level").set_value(level)
    at.button(key="new_game").click().run()
    assert not at.exception
    return at


HUNT_OP_KEYS = {"+": "plus", "−": "minus", "×": "times", "÷": "divide"}


def hunt_step(at, first, op, second):
    """Tap number, operation, number, by their positions in the current numbers."""
    at.button(key=f"hunt_num_{first}").click().run()
    at.button(key=f"hunt_op_{HUNT_OP_KEYS[op]}").click().run()
    at.button(key=f"hunt_num_{second}").click().run()
    assert not at.exception


def play_hunt_step(at, step):
    numbers = at.session_state["hunt"].numbers
    first = numbers.index(step.a)
    second = next(k for k, n in enumerate(numbers) if n == step.b and k != first)
    hunt_step(at, first, step.op, second)


def invalid_hunt_step(at):
    """Positions of a step that is never allowed: the smaller number minus the larger."""
    numbers = at.session_state["hunt"].numbers
    small = min(range(len(numbers)), key=lambda k: numbers[k])
    large = next(k for k in range(len(numbers)) if k != small and numbers[k] >= numbers[small])
    return small, "−", large


def test_games_picker_offers_number_hunt():
    at = open_app()
    go_to(at, "Games")
    assert "Number Hunt" in game_tiles(at)


@pytest.mark.parametrize("level, count", [("Easy", 3), ("Medium", 4), ("Hard", 5), ("Pro", 6)])
def test_new_hunt_shows_target_numbers_and_three_lives(level, count):
    at = start_hunt(level)
    game = at.session_state["hunt"]
    assert metrics(at)["Target"] == str(game.puzzle.target)
    assert metrics(at)["Lives"] == "3"
    labels = [at.button(key=f"hunt_num_{k}").label for k in range(count)]
    assert labels == [str(n) for n in game.puzzle.numbers]


def test_valid_hunt_step_is_shown_and_keeps_the_lives():
    at = start_hunt()
    step = at.session_state["hunt"].puzzle.solution[0]
    play_hunt_step(at, step)
    game = at.session_state["hunt"]
    assert game.steps == (step,)
    assert len(game.numbers) == 2
    assert metrics(at)["Lives"] == "3"


def test_invalid_hunt_step_lowers_the_lives():
    at = start_hunt()
    hunt_step(at, *invalid_hunt_step(at))
    assert metrics(at)["Lives"] == "2"
    assert at.session_state["hunt"].steps == ()


def test_hunt_undo_costs_a_life():
    at = start_hunt()
    play_hunt_step(at, at.session_state["hunt"].puzzle.solution[0])
    at.button(key="hunt_undo").click().run()
    assert not at.exception
    assert metrics(at)["Lives"] == "2"
    assert at.session_state["hunt"].steps == ()


def test_playing_the_solution_shows_you_found_it():
    at = start_hunt("Medium")
    for step in at.session_state["hunt"].puzzle.solution:
        play_hunt_step(at, step)
    assert "You found it!" in page_text(at)
    assert metrics(at)["Lives"] == "3"


def test_three_invalid_hunt_steps_show_game_over():
    at = start_hunt()
    for _ in range(3):
        hunt_step(at, *invalid_hunt_step(at))
    assert "Game over" in page_text(at)


def test_changing_the_game_ends_the_hunt():
    at = start_hunt()
    at.button(key="games_back").click().run()
    open_game(at, "Sudoku")
    assert "hunt" not in at.session_state


# --- Games: Magic Square (spec 002d) ---

MAGIC_EMPTY_CELLS = {"Easy": 4, "Medium": 6, "Hard": 7, "Pro": 10}


def start_magic(level="Easy"):
    at = open_app()
    go_to(at, "Games")
    open_game(at, "Magic Square")
    at.selectbox(key="game_level").set_value(level)
    at.button(key="new_game").click().run()
    assert not at.exception
    return at


def magic_cell_keys(at):
    return {b.key for b in at.button if b.key and b.key.startswith("magic_cell_")}


def magic_keypad(at):
    return [int(b.label) for b in at.button if b.key and b.key.startswith("magic_key_")]


def first_empty_magic_cell(at):
    game = at.session_state["magic"]
    for r, row in enumerate(game.grid):
        for c, value in enumerate(row):
            if value == 0:
                return r, c, game.puzzle.solution[r][c]
    raise AssertionError("no empty cell")


def magic_enter(at, row, col, value):
    at.button(key=f"magic_cell_{row}_{col}").click().run()
    at.button(key=f"magic_key_{value}").click().run()
    assert not at.exception


def wrong_magic_number(at, right):
    return next(n for n in magic_keypad(at) if n != right)


def test_games_picker_offers_all_four_games():
    at = open_app()
    go_to(at, "Games")
    options = game_tiles(at)
    assert options[: len(GAMES)] == GAMES  # the four R4 games, in the brief's order


@pytest.mark.parametrize("level", LEVELS)
def test_new_magic_square_shows_target_cells_keypad_and_lives(level):
    at = start_magic(level)
    game = at.session_state["magic"]
    assert metrics(at)["Target sum"] == str(game.puzzle.target)
    assert metrics(at)["Lives"] == "3"
    assert len(magic_cell_keys(at)) == MAGIC_EMPTY_CELLS[level]
    expected = sorted(
        game.puzzle.solution[r][c]
        for r in range(len(game.grid))
        for c in range(len(game.grid))
        if game.grid[r][c] == 0
    )
    assert magic_keypad(at) == expected


def test_magic_correct_number_locks_the_cell_and_leaves_the_keypad():
    at = start_magic()
    row, col, right = first_empty_magic_cell(at)
    magic_enter(at, row, col, right)
    assert f"magic_cell_{row}_{col}" not in magic_cell_keys(at)
    assert right not in magic_keypad(at)
    assert metrics(at)["Lives"] == "3"


def test_magic_wrong_number_lowers_the_lives():
    at = start_magic()
    row, col, right = first_empty_magic_cell(at)
    magic_enter(at, row, col, wrong_magic_number(at, right))
    assert metrics(at)["Lives"] == "2"
    assert f"magic_cell_{row}_{col}" in magic_cell_keys(at)


def test_magic_keypad_without_a_cell_asks_for_a_cell():
    at = start_magic()
    number = magic_keypad(at)[0]
    at.button(key=f"magic_key_{number}").click().run()
    assert not at.exception
    assert metrics(at)["Lives"] == "3"
    assert any("Tap an empty cell first" in w.value for w in at.warning)


def test_magic_three_wrong_numbers_show_game_over():
    at = start_magic()
    row, col, right = first_empty_magic_cell(at)
    for _ in range(3):
        magic_enter(at, row, col, wrong_magic_number(at, right))
    assert "Game over" in page_text(at)
    assert not magic_cell_keys(at)


def test_magic_solving_shows_you_solved_it():
    at = start_magic("Hard")
    for _ in range(MAGIC_EMPTY_CELLS["Hard"]):
        row, col, right = first_empty_magic_cell(at)
        magic_enter(at, row, col, right)
    assert "You solved it!" in page_text(at)
    assert metrics(at)["Lives"] == "3"


# --- Games: Number Chain (spec 002e) ---


def start_chain_game(level="Easy"):
    at = open_app()
    go_to(at, "Games")
    open_game(at, "Number Chain")
    at.selectbox(key="game_level").set_value(level)
    at.button(key="new_game").click().run()
    assert not at.exception
    return at


def show_chain(at):
    """Start the chain; with fast_sleep the steps run by in a moment."""
    at.button(key="chain_start").click().run()
    assert not at.exception


def answer_chain(at, text):
    at.text_input(key="chain_answer").input(text)
    at.button(key="chain_submit").click().run()
    assert not at.exception


def test_games_picker_offers_number_chain():
    at = open_app()
    go_to(at, "Games")
    assert "Number Chain" in game_tiles(at)


def test_new_chain_game_shows_lives_score_and_a_start_button():
    at = start_chain_game()
    assert metrics(at)["Lives"] == "3"
    assert metrics(at)["Score"] == "0"
    assert metrics(at)["Steps"] == "4"
    assert at.button(key="chain_start").label == "Start chain"


def test_chain_steps_are_followed_by_an_answer_field(fast_sleep):
    at = start_chain_game()
    show_chain(at)
    assert at.text_input(key="chain_answer") is not None
    assert at.session_state["chain_phase"] == "answer"


def test_right_chain_result_raises_the_score(fast_sleep):
    at = start_chain_game()
    result = at.session_state["chain"].chain.result
    show_chain(at)
    answer_chain(at, str(result))
    assert metrics(at)["Score"] == "1"
    assert metrics(at)["Steps"] == "5"
    assert "Right!" in page_text(at)
    assert at.button(key="chain_start").label == "Next chain"


def test_wrong_chain_result_costs_a_life_and_shows_the_result(fast_sleep):
    at = start_chain_game()
    result = at.session_state["chain"].chain.result
    show_chain(at)
    answer_chain(at, str(result + 1))
    assert metrics(at)["Lives"] == "2"
    assert any(str(result) in w.value for w in at.warning)


def test_non_numeric_chain_answer_changes_nothing(fast_sleep):
    at = start_chain_game()
    show_chain(at)
    answer_chain(at, "abc")
    assert metrics(at)["Lives"] == "3"
    assert at.session_state["chain_phase"] == "answer"


def test_three_wrong_chain_results_show_game_over(fast_sleep):
    at = start_chain_game()
    for _ in range(3):
        result = at.session_state["chain"].chain.result
        show_chain(at)
        answer_chain(at, str(result + 1))
    assert "Game over" in page_text(at)
    assert "You solved 0 chains" in page_text(at)


# --- Games: Sudoku stopwatch (spec 002f) ---

CLOCK = re.compile(r"\d+:\d\d(:\d\d)?")


def test_new_mini_sudoku_shows_a_running_clock():
    at = start_game()
    assert CLOCK.fullmatch(metrics(at)["Time"])
    assert at.session_state["game"].started_at is not None


def test_new_sudoku_shows_a_running_clock():
    at = start_sudoku()
    assert CLOCK.fullmatch(metrics(at)["Time"])


def test_solved_sudoku_shows_the_final_time():
    at = start_game()
    for _ in range(EMPTY_CELLS["Easy"]):
        row, col, right = first_empty_cell(at)
        enter(at, row, col, str(right))
    assert "You solved it!" in page_text(at)
    assert at.session_state["game"].ended_at is not None
    assert CLOCK.fullmatch(metrics(at)["Time"])


# --- Games: End game (spec 002g) ---

GAME_STATE_KEYS = {
    "Mini Sudoku": "game",
    "Sudoku": "game",
    "Number Hunt": "hunt",
    "Magic Square": "magic",
    "Number Chain": "chain",
}


def start_any_game(choice):
    at = open_app()
    go_to(at, "Games")
    open_game(at, choice)
    at.button(key="new_game").click().run()
    assert not at.exception
    return at


def has_end_button(at):
    return any(button.key == "end_game" for button in at.button)


@pytest.mark.parametrize("choice", list(GAME_STATE_KEYS))
def test_running_game_can_be_ended(choice):
    at = start_any_game(choice)
    assert GAME_STATE_KEYS[choice] in at.session_state
    assert has_end_button(at)
    assert at.button(key="end_game").label == "End game"

    at.button(key="end_game").click().run()
    assert not at.exception
    assert GAME_STATE_KEYS[choice] not in at.session_state
    assert not cell_keys(at)
    assert not magic_cell_keys(at)
    assert not has_end_button(at)
    assert any(button.key == "new_game" for button in at.button)


def test_new_game_after_ending_starts_fresh():
    at = start_any_game("Mini Sudoku")
    row, col, right = first_empty_cell(at)
    enter(at, row, col, str(right % 6 + 1))  # lose a life first
    at.button(key="end_game").click().run()
    at.button(key="new_game").click().run()
    assert not at.exception
    assert metrics(at)["Lives"] == "3"
    assert len(cell_keys(at)) == EMPTY_CELLS["Easy"]
    assert has_end_button(at)


def test_lost_game_has_no_end_button():
    at = start_game()
    row, col, right = first_empty_cell(at)
    for _ in range(3):
        enter(at, row, col, wrong_digit(right))
    assert "Game over" in page_text(at)
    assert not has_end_button(at)


def test_solved_game_has_no_end_button():
    at = start_game()
    for _ in range(EMPTY_CELLS["Easy"]):
        row, col, right = first_empty_cell(at)
        enter(at, row, col, str(right))
    assert "You solved it!" in page_text(at)
    assert not has_end_button(at)


def test_number_chain_can_be_ended_while_answering(fast_sleep):
    at = start_chain_game()
    show_chain(at)
    assert at.session_state["chain_phase"] == "answer"
    at.button(key="end_game").click().run()
    assert not at.exception
    assert "chain" not in at.session_state



# --- Games: Try again (spec 002h) ---


def has_try_again_button(at):
    return any(button.key == "try_again" for button in at.button)


def lose_sudoku(at, size=6):
    row, col, right = first_empty_cell(at)
    for _ in range(3):
        enter(at, row, col, str(right % size + 1))


def test_try_again_replays_the_same_sudoku_with_three_lives():
    at = start_game()
    puzzle = at.session_state["game"].puzzle
    lose_sudoku(at)
    assert "Game over" in page_text(at)
    assert has_try_again_button(at)

    at.button(key="try_again").click().run()
    assert not at.exception
    game = at.session_state["game"]
    assert game.puzzle == puzzle
    assert game.grid == puzzle.givens
    assert game.lives == 3
    assert game.status == "running"
    assert metrics(at)["Lives"] == "3"
    assert len(cell_keys(at)) == EMPTY_CELLS["Easy"]
    assert not has_try_again_button(at)


def test_try_again_replays_the_same_9x9_sudoku():
    at = start_sudoku()
    puzzle = at.session_state["game"].puzzle
    lose_sudoku(at, size=9)
    at.button(key="try_again").click().run()
    assert not at.exception
    assert at.session_state["game"].puzzle == puzzle
    assert len(at.session_state["game"].grid) == 9


def test_try_again_replays_the_same_number_hunt():
    at = start_hunt()
    puzzle = at.session_state["hunt"].puzzle
    for _ in range(3):
        hunt_step(at, *invalid_hunt_step(at))
    assert "Game over" in page_text(at)
    at.button(key="try_again").click().run()
    assert not at.exception
    game = at.session_state["hunt"]
    assert game.puzzle == puzzle
    assert game.numbers == puzzle.numbers
    assert game.steps == ()
    assert game.lives == 3


def test_try_again_replays_the_same_magic_square():
    at = start_magic()
    puzzle = at.session_state["magic"].puzzle
    row, col, right = first_empty_magic_cell(at)
    for _ in range(3):
        magic_enter(at, row, col, wrong_magic_number(at, right))
    assert "Game over" in page_text(at)
    at.button(key="try_again").click().run()
    assert not at.exception
    game = at.session_state["magic"]
    assert game.puzzle == puzzle
    assert game.grid == puzzle.givens
    assert game.lives == 3


def test_try_again_starts_number_chain_over_at_the_same_level(fast_sleep):
    at = start_chain_game("Medium")
    for _ in range(3):
        result = at.session_state["chain"].chain.result
        show_chain(at)
        answer_chain(at, str(result + 1))
    assert "Game over" in page_text(at)
    at.button(key="try_again").click().run()
    assert not at.exception
    game = at.session_state["chain"]
    assert game.level == "Medium"
    assert game.score == 0
    assert game.lives == 3
    assert at.session_state["chain_phase"] == "ready"


def test_running_and_solved_games_have_no_try_again_button():
    at = start_game()
    assert not has_try_again_button(at)
    for _ in range(EMPTY_CELLS["Easy"]):
        row, col, right = first_empty_cell(at)
        enter(at, row, col, str(right))
    assert "You solved it!" in page_text(at)
    assert not has_try_again_button(at)

# --- Tests tab shows only the best score for the selection (spec 015) ---


def test_tests_tab_has_no_highscore_table_and_no_highscores_heading():
    at = open_app()
    assert "Highscores" not in [subheader.value for subheader in at.subheader]
    assert not any(list(table.value.columns) == LEVELS for table in at.table)


def test_your_best_shows_a_dash_when_nothing_was_played():
    assert metrics(open_app())["Your best"] == NO_HIGHSCORE


def test_your_best_follows_the_selected_test_type_and_level():
    seed_run("e1", "Easy", 15)
    seed_run("e2", "Easy", 9)
    seed_run("m1", "Medium", 7)
    at = open_app()
    assert your_best(at, "Multiplication", "Easy") == "15"
    assert your_best(at, "Multiplication", "Medium") == "7"
    assert your_best(at, "Addition", "Easy") == NO_HIGHSCORE


def test_your_best_ignores_runs_of_others_and_without_owner():
    db.init_db()
    db.save_run("no-owner", "Multiplication", "Easy", FINISHED, 40, 0, 0)
    accounts_db.init_db()
    db.save_run("theirs", "Multiplication", "Easy", FINISHED, 50, 0, 0)
    accounts_db.assign_run("theirs", "someone-else")
    assert your_best(open_app()) == NO_HIGHSCORE


# --- Games: tile overview (spec 002i) ---

ALL_GAMES = ["Mini Sudoku", "Sudoku", "Number Hunt", "Magic Square", "Number Chain"]


def test_games_starts_with_one_tile_per_game_and_no_game_open():
    at = open_app()
    go_to(at, "Games")
    assert game_tiles(at) == ALL_GAMES
    assert not any(button.key == "new_game" for button in at.button)
    assert not any(button.key == "games_back" for button in at.button)


@pytest.mark.parametrize("choice", ALL_GAMES)
def test_a_tile_opens_its_game(choice):
    at = open_app()
    go_to(at, "Games")
    open_game(at, choice)
    assert choice in [str(sub.value) for sub in at.subheader]
    assert not game_tiles(at)
    assert at.button(key="games_back").label == "← All games"
    at.button(key="new_game").click().run()
    assert not at.exception
    assert current_game_name(at) == choice


def current_game_name(at):
    keys = {"hunt": "Number Hunt", "magic": "Magic Square", "chain": "Number Chain"}
    for key, name in keys.items():
        if key in at.session_state:
            return name
    return "Sudoku" if len(at.session_state["game"].grid) == 9 else "Mini Sudoku"


def test_back_returns_to_the_tiles_and_ends_the_running_game():
    at = start_hunt()
    at.button(key="games_back").click().run()
    assert not at.exception
    assert "hunt" not in at.session_state
    assert game_tiles(at) == ALL_GAMES


def test_an_open_game_stays_open_when_coming_back_to_games():
    at = start_magic()
    go_to(at, "Tests")
    go_to(at, "Games")
    assert "magic" in at.session_state
    assert not game_tiles(at)
