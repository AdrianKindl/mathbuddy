"""Magic Square rules: generation, keypad, entries, lives, win and loss (spec 002d)."""

import random
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import magicsquare
from magicsquare import (
    BASE_SQUARES_4,
    LO_SHU,
    Game,
    Outcome,
    Puzzle,
    Status,
    count_completions,
    enter_number,
    generate_puzzle,
    is_magic,
    keypad,
    magic_sum,
    start_game,
)
from tasks import LEVELS

# Lo Shu with three empty cells: (0, 0) needs 2, (1, 1) needs 5, (2, 2) needs 8.
EMPTY = ((0, 0), (1, 1), (2, 2))


def with_cells(grid, changes):
    return tuple(
        tuple(changes.get((r, c), value) for c, value in enumerate(row))
        for r, row in enumerate(grid)
    )


def known_game(lives=3):
    givens = with_cells(LO_SHU, {cell: 0 for cell in EMPTY})
    puzzle = Puzzle(givens=givens, solution=LO_SHU, target=15)
    return Game(level="Easy", puzzle=puzzle, grid=givens, lives=lives)


def empty_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]


# --- Constants and base squares ---


def test_constants_match_the_brief_and_the_spec():
    assert magicsquare.LIVES == 3
    assert magicsquare.LEVEL_SETTINGS == {
        "Easy": (3, 4, 1, 1),
        "Medium": (3, 6, 2, 20),
        "Hard": (4, 7, 1, 1),
        "Pro": (4, 10, 2, 30),
    }
    assert list(magicsquare.LEVEL_SETTINGS) == list(LEVELS)


def test_lo_shu_and_every_4x4_base_square_are_magic():
    assert is_magic(LO_SHU)
    assert len(BASE_SQUARES_4) == 12
    for square in BASE_SQUARES_4:
        assert is_magic(square), square
        assert sorted(v for row in square for v in row) == list(range(1, 17))


@pytest.mark.parametrize(
    "size, smallest, target", [(3, 1, 15), (4, 1, 34), (3, 2, 18), (4, 30, 150)]
)
def test_magic_sum(size, smallest, target):
    assert magic_sum(size, smallest) == target


# --- Checking grids ---


def test_swapping_two_numbers_breaks_the_magic():
    assert not is_magic(with_cells(LO_SHU, {(0, 0): 7, (0, 1): 2}))


def test_rows_and_columns_alone_are_not_enough():
    # Every row and column adds up to 15, but the diagonals do not.
    latin = ((1, 5, 9), (5, 9, 1), (9, 1, 5))
    assert not is_magic(latin)


def test_repeated_numbers_are_not_magic():
    assert not is_magic(((5, 5, 5), (5, 5, 5), (5, 5, 5)))


def test_incomplete_grid_is_not_magic():
    assert not is_magic(with_cells(LO_SHU, {(1, 1): 0}))


def test_known_puzzle_has_one_completion():
    assert count_completions(known_game().grid, [2, 5, 8], 15) == 1


def test_count_completions_stops_at_the_limit():
    # With only the centre given, the 1–9 square can be completed in 8 ways.
    centre_only = ((0, 0, 0), (0, 5, 0), (0, 0, 0))
    assert count_completions(centre_only, [1, 2, 3, 4, 6, 7, 8, 9], 15, limit=2) == 2
    assert count_completions(centre_only, [1, 2, 3, 4, 6, 7, 8, 9], 15, limit=100) == 8


def test_impossible_numbers_have_no_completion():
    assert count_completions(known_game().grid, [1, 5, 9], 15) == 0


# --- Generating puzzles (Done when: Generation, Variety) ---


@pytest.mark.parametrize("level", LEVELS)
def test_generated_puzzles_follow_the_level(level):
    size, empties, low, high = magicsquare.LEVEL_SETTINGS[level]
    for seed in range(50):
        puzzle = generate_puzzle(level, random.Random(seed))
        numbers = sorted(v for row in puzzle.solution for v in row)
        smallest = numbers[0]

        assert len(puzzle.solution) == size, (level, seed)
        assert is_magic(puzzle.solution), (level, seed)
        assert low <= smallest <= high, (level, seed)
        assert numbers == list(range(smallest, smallest + size * size)), (level, seed)
        assert puzzle.target == magic_sum(size, smallest), (level, seed)
        assert sum(puzzle.solution[0]) == puzzle.target, (level, seed)

        for r in range(size):
            for c in range(size):
                assert puzzle.givens[r][c] in (0, puzzle.solution[r][c]), (level, seed)
        assert len(empty_cells(puzzle.givens)) == empties, (level, seed)

        missing = [puzzle.solution[r][c] for r, c in empty_cells(puzzle.givens)]
        assert count_completions(puzzle.givens, missing, puzzle.target) == 1, (level, seed)


def test_same_seed_gives_the_same_puzzle():
    assert generate_puzzle("Pro", random.Random(3)) == generate_puzzle("Pro", random.Random(3))


@pytest.mark.parametrize("level", LEVELS)
def test_different_seeds_give_different_puzzles(level):
    puzzles = {generate_puzzle(level, random.Random(seed)) for seed in range(20)}
    assert len(puzzles) >= 15


def test_unknown_level_is_rejected():
    with pytest.raises(ValueError):
        generate_puzzle("Impossible", random.Random(1))


def test_new_game_starts_with_three_lives_and_the_givens():
    game = start_game("Hard", random.Random(6))
    assert game.grid == game.puzzle.givens
    assert game.lives == 3
    assert game.status == Status.RUNNING
    assert len(empty_cells(game.grid)) == 7


def test_game_cannot_be_changed_in_place():
    with pytest.raises(FrozenInstanceError):
        known_game().lives = 99


# --- Keypad (brief: only the numbers needed) ---


def test_keypad_offers_exactly_the_missing_numbers_smallest_first():
    assert keypad(known_game()) == (2, 5, 8)


def test_correct_entry_removes_its_number_from_the_keypad():
    game, _ = enter_number(known_game(), 1, 1, 5)
    assert keypad(game) == (2, 8)


def test_number_not_on_the_keypad_is_ignored():
    before = known_game()
    for value in (0, 1, 9, 10, -2):
        game, outcome = enter_number(before, 0, 0, value)
        assert outcome == Outcome.IGNORED
        assert game == before


def test_keypad_of_a_generated_game_matches_its_empty_cells():
    game = start_game("Pro", random.Random(9))
    expected = sorted(game.puzzle.solution[r][c] for r, c in empty_cells(game.grid))
    assert list(keypad(game)) == expected


# --- Entries ---


def test_correct_entry_fills_the_cell_and_keeps_the_lives():
    game, outcome = enter_number(known_game(), 0, 0, 2)
    assert outcome == Outcome.CORRECT
    assert game.grid[0][0] == 2
    assert game.lives == 3
    assert game.status == Status.RUNNING


def test_wrong_entry_costs_a_life_and_leaves_the_cell_empty():
    game, outcome = enter_number(known_game(), 0, 0, 8)  # 8 is needed, but not here
    assert outcome == Outcome.WRONG
    assert game.grid[0][0] == 0
    assert game.lives == 2
    assert keypad(game) == (2, 5, 8)


def test_entry_in_a_given_cell_changes_nothing():
    before = known_game()
    game, outcome = enter_number(before, 0, 1, 2)
    assert outcome == Outcome.IGNORED
    assert game == before


def test_locked_cell_cannot_be_changed():
    locked, _ = enter_number(known_game(), 0, 0, 2)
    game, outcome = enter_number(locked, 0, 0, 5)
    assert outcome == Outcome.IGNORED
    assert game == locked


@pytest.mark.parametrize("row, col", [(-1, 0), (0, 3), (3, 0)])
def test_cells_outside_the_grid_are_rejected(row, col):
    with pytest.raises(ValueError):
        enter_number(known_game(), row, col, 2)


def test_third_wrong_entry_loses_the_game():
    game = known_game()
    for _ in range(3):
        game, outcome = enter_number(game, 1, 1, 2)
        assert outcome == Outcome.WRONG
    assert game.lives == 0
    assert game.status == Status.LOST


def test_last_correct_entry_wins():
    game = known_game()
    for (r, c) in EMPTY:
        game, outcome = enter_number(game, r, c, LO_SHU[r][c])
        assert outcome == Outcome.CORRECT
    assert game.status == Status.WON
    assert keypad(game) == ()


def test_entries_after_the_end_are_ignored():
    lost = known_game(lives=1)
    lost, _ = enter_number(lost, 1, 1, 2)
    game, outcome = enter_number(lost, 1, 1, 5)
    assert outcome == Outcome.IGNORED
    assert game == lost


def test_full_generated_game_can_be_won():
    game = start_game("Pro", random.Random(12))
    for r, c in empty_cells(game.grid):
        game, outcome = enter_number(game, r, c, game.puzzle.solution[r][c])
        assert outcome == Outcome.CORRECT
    assert game.status == Status.WON


# --- Design rules (AGENTS.md) ---


def test_rule_module_has_no_streamlit_sql_clock_or_own_randomness():
    source = (Path(__file__).resolve().parent.parent / "magicsquare.py").read_text()
    for forbidden in ("streamlit", "sqlite", "SELECT", "datetime.now", "random.Random(", "time.time"):
        assert forbidden not in source, forbidden
