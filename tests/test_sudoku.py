"""Mini Sudoku rules: puzzle generation, entries, lives, win and loss (spec 002)."""

import random
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import sudoku
from sudoku import (
    Game,
    Outcome,
    Puzzle,
    Status,
    count_solutions,
    enter_number,
    generate_puzzle,
    is_solved_grid,
    start_game,
)
from tasks import LEVELS

# A complete, valid 6×6 grid: every row, column and 2×3 box holds 1–6 once.
SOLUTION = (
    (1, 2, 3, 4, 5, 6),
    (4, 5, 6, 1, 2, 3),
    (2, 3, 1, 5, 6, 4),
    (5, 6, 4, 2, 3, 1),
    (3, 1, 2, 6, 4, 5),
    (6, 4, 5, 3, 1, 2),
)
# Three empty cells: (0, 0) needs 1, (2, 3) needs 5, (5, 5) needs 2.
EMPTY = ((0, 0), (2, 3), (5, 5))


def with_cells(grid, changes):
    """A copy of `grid` with {(row, col): value} changed."""
    return tuple(
        tuple(changes.get((r, c), value) for c, value in enumerate(row))
        for r, row in enumerate(grid)
    )


def known_game(lives=3):
    givens = with_cells(SOLUTION, {cell: 0 for cell in EMPTY})
    puzzle = Puzzle(givens=givens, solution=SOLUTION)
    return Game(level="Easy", puzzle=puzzle, grid=givens, lives=lives)


def empty_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]


# --- Constants ---


def test_constants_match_the_brief():
    assert sudoku.SIZE == 6
    assert (sudoku.BOX_ROWS, sudoku.BOX_COLS) == (2, 3)
    assert sudoku.LIVES == 3


def test_every_level_has_a_number_of_empty_cells():
    assert sudoku.EMPTY_CELLS == {"Easy": 12, "Medium": 16, "Hard": 20, "Pro": 24}
    assert list(sudoku.EMPTY_CELLS) == list(LEVELS)


# --- Checking grids ---


def test_known_solution_is_a_solved_grid():
    assert is_solved_grid(SOLUTION)


def test_grid_with_an_empty_cell_is_not_solved():
    assert not is_solved_grid(with_cells(SOLUTION, {(3, 3): 0}))


def test_duplicate_in_a_row_is_not_solved():
    # Swapping two cells of one column keeps that column valid but breaks two rows.
    swapped = with_cells(SOLUTION, {(0, 0): 4, (1, 0): 1})
    assert not is_solved_grid(swapped)


def test_duplicate_in_a_column_is_not_solved():
    # Swapping two cells of one row keeps that row valid but breaks two columns.
    swapped = with_cells(SOLUTION, {(0, 0): 2, (0, 1): 1})
    assert not is_solved_grid(swapped)


def test_duplicate_in_a_box_is_not_solved():
    # Every row and column is a valid 1–6, but the 2×3 boxes are not.
    rows_shifted_by_one = tuple(
        tuple((r + c) % 6 + 1 for c in range(6)) for r in range(6)
    )
    assert not is_solved_grid(rows_shifted_by_one)


def test_numbers_outside_one_to_six_are_not_solved():
    assert not is_solved_grid(tuple(tuple(v + 1 for v in row) for row in SOLUTION))


def test_count_solutions_of_a_full_valid_grid_is_one():
    assert count_solutions(SOLUTION) == 1


def test_count_solutions_of_the_known_puzzle_is_one():
    assert count_solutions(known_game().grid) == 1


def test_count_solutions_stops_at_the_limit():
    empty_grid = tuple((0,) * 6 for _ in range(6))
    assert count_solutions(empty_grid, limit=2) == 2


def test_count_solutions_of_a_contradiction_is_zero():
    # Row 0 needs a 1 at (0, 0), but column 0 now already has a 1 at (1, 0).
    broken = with_cells(SOLUTION, {(0, 0): 0, (1, 0): 1})
    assert count_solutions(broken) == 0


def test_count_solutions_does_not_change_the_grid():
    grid = known_game().grid
    count_solutions(grid)
    assert empty_cells(grid) == list(EMPTY)


# --- Generating puzzles (Done when: Generation, Variety) ---


@pytest.mark.parametrize("level", LEVELS)
def test_generated_puzzles_follow_the_rules(level):
    for seed in range(50):
        puzzle = generate_puzzle(level, random.Random(seed))
        assert is_solved_grid(puzzle.solution), (level, seed)
        for r in range(6):
            for c in range(6):
                given = puzzle.givens[r][c]
                assert given in (0, puzzle.solution[r][c]), (level, seed, r, c)
        assert len(empty_cells(puzzle.givens)) == sudoku.EMPTY_CELLS[level], (level, seed)
        assert count_solutions(puzzle.givens) == 1, (level, seed)


def test_same_seed_gives_the_same_puzzle():
    assert generate_puzzle("Hard", random.Random(7)) == generate_puzzle("Hard", random.Random(7))


def test_different_seeds_give_different_puzzles():
    puzzles = {generate_puzzle("Easy", random.Random(seed)) for seed in range(20)}
    assert len(puzzles) == 20


def test_unknown_level_is_rejected():
    with pytest.raises(ValueError):
        generate_puzzle("Impossible", random.Random(1))


# --- Starting a game ---


def test_new_game_starts_with_three_lives_and_the_givens():
    game = start_game("Medium", random.Random(3))
    assert game.level == "Medium"
    assert game.lives == 3
    assert game.status == Status.RUNNING
    assert game.grid == game.puzzle.givens
    assert len(empty_cells(game.grid)) == 16


def test_game_cannot_be_changed_in_place():
    with pytest.raises(FrozenInstanceError):
        known_game().lives = 99


# --- Entries (Done when: Correct entry, Wrong entry, Ignored entries) ---


def test_correct_entry_fills_the_cell_and_keeps_the_lives():
    game, outcome = enter_number(known_game(), 0, 0, "1")
    assert outcome == Outcome.CORRECT
    assert game.grid[0][0] == 1
    assert game.lives == 3
    assert game.status == Status.RUNNING


def test_spaces_around_the_number_are_allowed():
    game, outcome = enter_number(known_game(), 2, 3, " 5 ")
    assert outcome == Outcome.CORRECT
    assert game.grid[2][3] == 5


def test_wrong_entry_costs_a_life_and_leaves_the_cell_empty():
    game, outcome = enter_number(known_game(), 0, 0, "4")
    assert outcome == Outcome.WRONG
    assert game.grid[0][0] == 0
    assert game.lives == 2
    assert game.status == Status.RUNNING


def test_entering_does_not_change_the_old_game():
    before = known_game()
    enter_number(before, 0, 0, "1")
    enter_number(before, 2, 3, "4")
    assert before == known_game()


@pytest.mark.parametrize("raw", ["", "   ", "abc", "0", "7", "-1", "2.5", "12"])
def test_invalid_entries_change_nothing(raw):
    before = known_game()
    game, outcome = enter_number(before, 0, 0, raw)
    assert outcome == Outcome.IGNORED
    assert game == before


def test_entry_in_a_given_cell_changes_nothing():
    before = known_game()
    game, outcome = enter_number(before, 0, 1, "3")  # (0, 1) is a given 2
    assert outcome == Outcome.IGNORED
    assert game == before


def test_locked_correct_cell_cannot_be_changed_or_cost_a_life():
    solved_once, _ = enter_number(known_game(), 0, 0, "1")
    game, outcome = enter_number(solved_once, 0, 0, "4")
    assert outcome == Outcome.IGNORED
    assert game == solved_once


@pytest.mark.parametrize("row, col", [(-1, 0), (0, -1), (6, 0), (0, 6)])
def test_cells_outside_the_grid_are_rejected(row, col):
    with pytest.raises(ValueError):
        enter_number(known_game(), row, col, "1")


# --- Losing (Done when: Three wrong entries) ---


def test_third_wrong_entry_loses_the_game():
    game = known_game()
    for _ in range(3):
        game, outcome = enter_number(game, 0, 0, "6")
        assert outcome == Outcome.WRONG
    assert game.lives == 0
    assert game.status == Status.LOST


def test_entries_after_losing_are_ignored():
    lost = known_game(lives=1)
    lost, _ = enter_number(lost, 0, 0, "6")
    assert lost.status == Status.LOST
    game, outcome = enter_number(lost, 0, 0, "1")
    assert outcome == Outcome.IGNORED
    assert game == lost


# --- Winning (Done when: Win) ---


def fill_all(game):
    for r, c in EMPTY:
        game, outcome = enter_number(game, r, c, str(SOLUTION[r][c]))
        assert outcome == Outcome.CORRECT
    return game


def test_filling_every_cell_correctly_wins():
    game = fill_all(known_game())
    assert game.status == Status.WON
    assert game.grid == SOLUTION
    assert game.lives == 3


def test_winning_with_lives_lost_still_wins():
    game, _ = enter_number(known_game(), 0, 0, "6")
    game, _ = enter_number(game, 0, 0, "5")
    assert game.lives == 1
    game = fill_all(game)
    assert game.status == Status.WON
    assert game.lives == 1


def test_game_is_not_won_before_the_last_cell():
    game, _ = enter_number(known_game(), 0, 0, "1")
    game, _ = enter_number(game, 2, 3, "5")
    assert game.status == Status.RUNNING


def test_entries_after_winning_are_ignored():
    won = fill_all(known_game())
    game, outcome = enter_number(won, 0, 0, "3")
    assert outcome == Outcome.IGNORED
    assert game == won


def test_full_generated_game_can_be_won():
    game = start_game("Pro", random.Random(11))
    for r, c in empty_cells(game.grid):
        game, outcome = enter_number(game, r, c, str(game.puzzle.solution[r][c]))
        assert outcome == Outcome.CORRECT
    assert game.status == Status.WON


# --- Design rules (AGENTS.md) ---


def test_rule_module_has_no_streamlit_sql_clock_or_own_randomness():
    source = (Path(__file__).resolve().parent.parent / "sudoku.py").read_text()
    for forbidden in ("streamlit", "sqlite", "SELECT", "datetime.now", "random.Random(", "time.time"):
        assert forbidden not in source, forbidden


# --- Sudoku 9×9 (spec 002b) ---

# A complete, valid 9×9 grid built from the classic shifting pattern.
SOLUTION_9 = tuple(
    tuple((r * 3 + r // 3 + c) % 9 + 1 for c in range(9)) for r in range(9)
)
EMPTY_9 = ((0, 0), (4, 4), (8, 8))


def known_game_9(lives=3):
    givens = with_cells(SOLUTION_9, {cell: 0 for cell in EMPTY_9})
    return Game(level="Easy", puzzle=Puzzle(givens=givens, solution=SOLUTION_9), grid=givens, lives=lives)


def test_classic_variant_matches_the_brief():
    assert sudoku.CLASSIC.size == 9
    assert (sudoku.CLASSIC.box_rows, sudoku.CLASSIC.box_cols) == (3, 3)
    assert sudoku.CLASSIC.empty_cells == {"Easy": 36, "Medium": 42, "Hard": 48, "Pro": 52}
    assert list(sudoku.CLASSIC.empty_cells) == list(LEVELS)


def test_mini_is_still_the_default_variant():
    assert sudoku.MINI.size == 6
    assert len(generate_puzzle("Easy", random.Random(1)).givens) == 6


def test_known_9x9_solution_is_a_solved_grid():
    assert is_solved_grid(SOLUTION_9)
    assert count_solutions(SOLUTION_9) == 1


def test_9x9_duplicate_in_a_box_is_not_solved():
    # Every row and column is a valid 1–9, but the 3×3 boxes are not.
    rows_shifted_by_one = tuple(tuple((r + c) % 9 + 1 for c in range(9)) for r in range(9))
    assert not is_solved_grid(rows_shifted_by_one)


@pytest.mark.parametrize("size", [4, 5, 7, 8])
def test_grids_of_other_sizes_are_rejected(size):
    with pytest.raises(ValueError):
        is_solved_grid(tuple((0,) * size for _ in range(size)))


def test_ragged_grids_are_rejected():
    with pytest.raises(ValueError):
        count_solutions(SOLUTION[:5] + ((1, 2, 3),))


@pytest.mark.parametrize("level", LEVELS)
def test_generated_9x9_puzzles_follow_the_rules(level):
    for seed in range(10):
        puzzle = generate_puzzle(level, random.Random(seed), sudoku.CLASSIC)
        assert len(puzzle.solution) == 9
        assert is_solved_grid(puzzle.solution), (level, seed)
        for r in range(9):
            for c in range(9):
                assert puzzle.givens[r][c] in (0, puzzle.solution[r][c]), (level, seed, r, c)
        assert len(empty_cells(puzzle.givens)) == sudoku.CLASSIC.empty_cells[level], (level, seed)
        assert count_solutions(puzzle.givens) == 1, (level, seed)


def test_new_9x9_game_starts_with_three_lives():
    game = start_game("Pro", random.Random(5), sudoku.CLASSIC)
    assert game.lives == 3
    assert game.status == Status.RUNNING
    assert len(game.grid) == 9
    assert len(empty_cells(game.grid)) == 52


def test_9x9_accepts_nine_as_an_entry():
    game, outcome = enter_number(known_game_9(), 0, 0, "1")
    assert outcome == Outcome.CORRECT
    game, outcome = enter_number(game, 8, 8, str(SOLUTION_9[8][8]))
    assert outcome == Outcome.CORRECT


@pytest.mark.parametrize("raw", ["7", "8", "9"])
def test_7_8_and_9_are_evaluated_on_9x9(raw):
    # (0, 0) needs a 1, so 7, 8 and 9 are wrong entries there, not ignored ones.
    game, outcome = enter_number(known_game_9(), 0, 0, raw)
    assert outcome == Outcome.WRONG
    assert game.lives == 2


@pytest.mark.parametrize("raw", ["0", "10", "", "x"])
def test_invalid_9x9_entries_change_nothing(raw):
    before = known_game_9()
    game, outcome = enter_number(before, 0, 0, raw)
    assert outcome == Outcome.IGNORED
    assert game == before


@pytest.mark.parametrize("row, col", [(9, 0), (0, 9)])
def test_cells_outside_the_9x9_grid_are_rejected(row, col):
    with pytest.raises(ValueError):
        enter_number(known_game_9(), row, col, "1")


def test_three_wrong_9x9_entries_lose_the_game():
    game = known_game_9()
    for _ in range(3):
        game, _ = enter_number(game, 4, 4, "9" if SOLUTION_9[4][4] != 9 else "1")
    assert game.status == Status.LOST


def test_full_generated_9x9_game_can_be_won():
    game = start_game("Hard", random.Random(2), sudoku.CLASSIC)
    for r, c in empty_cells(game.grid):
        game, outcome = enter_number(game, r, c, str(game.puzzle.solution[r][c]))
        assert outcome == Outcome.CORRECT
    assert game.status == Status.WON
    assert game.lives == 3
