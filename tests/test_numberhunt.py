"""Number Hunt rules: generation, steps, undo, reset, lives, win and loss (spec 002c)."""

import random
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import numberhunt
from numberhunt import (
    Game,
    Outcome,
    Puzzle,
    Status,
    Step,
    apply_step,
    calculate,
    generate_puzzle,
    is_stuck,
    reset,
    start_game,
    undo,
)
from tasks import LEVELS

# 4 and 6 can become 24 with 4 × 6; a target of 24.
SIMPLE = Puzzle(numbers=(4, 6), target=24, solution=(Step(4, "×", 6, 24),))
# 3, 5 and 7: (3 + 5) × 7 = 56.
THREE = Puzzle(
    numbers=(3, 5, 7), target=56, solution=(Step(3, "+", 5, 8), Step(8, "×", 7, 56))
)


def game_of(puzzle, lives=3):
    return Game(level="Easy", puzzle=puzzle, numbers=puzzle.numbers, lives=lives)


def play(game, step):
    """Apply a Step by finding its numbers in the current pool."""
    first = game.numbers.index(step.a)
    second = next(k for k, n in enumerate(game.numbers) if n == step.b and k != first)
    return apply_step(game, first, step.op, second)


# --- Constants ---


def test_constants_match_the_brief_and_the_spec():
    assert numberhunt.LIVES == 3
    assert numberhunt.OPERATIONS == ("+", "−", "×", "÷")
    assert numberhunt.START_NUMBERS == {
        "Easy": (3, 2, 9),
        "Medium": (4, 2, 12),
        "Hard": (5, 2, 20),
        "Pro": (6, 2, 25),
    }
    assert numberhunt.TARGET_RANGE == {
        "Easy": (10, 99),
        "Medium": (20, 199),
        "Hard": (50, 499),
        "Pro": (100, 999),
    }


# --- Calculating (brief: whole numbers > 0, no × or ÷ by 1) ---


@pytest.mark.parametrize(
    "a, op, b, result",
    [(7, "+", 1, 8), (9, "−", 7, 2), (8, "÷", 2, 4), (7, "×", 8, 56), (12, "÷", 12, 1)],
)
def test_allowed_steps(a, op, b, result):
    assert calculate(a, op, b) == result


@pytest.mark.parametrize(
    "a, op, b",
    [(7, "−", 9), (7, "−", 7), (7, "÷", 2), (7, "×", 1), (1, "×", 7), (7, "÷", 1)],
)
def test_steps_the_brief_does_not_allow(a, op, b):
    assert calculate(a, op, b) is None


def test_unknown_operation_is_rejected():
    with pytest.raises(ValueError):
        calculate(2, "^", 3)


# --- Generating puzzles (Done when: Generation, Variety) ---


@pytest.mark.parametrize("level", LEVELS)
def test_generated_puzzles_follow_the_level_and_are_solvable(level):
    count, low, high = numberhunt.START_NUMBERS[level]
    target_low, target_high = numberhunt.TARGET_RANGE[level]
    for seed in range(50):
        puzzle = generate_puzzle(level, random.Random(seed))
        assert len(puzzle.numbers) == count, (level, seed)
        assert all(low <= n <= high for n in puzzle.numbers), (level, seed)
        assert target_low <= puzzle.target <= target_high, (level, seed)
        assert puzzle.target not in puzzle.numbers, (level, seed)

        game = game_of(puzzle)
        for step in puzzle.solution:
            game, outcome = play(game, step)
            assert outcome == Outcome.CORRECT, (level, seed, step)
        assert game.status == Status.WON, (level, seed)
        assert len(puzzle.solution) == count - 1


def test_same_seed_gives_the_same_puzzle():
    assert generate_puzzle("Pro", random.Random(4)) == generate_puzzle("Pro", random.Random(4))


def test_different_seeds_give_different_puzzles():
    puzzles = {generate_puzzle("Medium", random.Random(seed)) for seed in range(20)}
    assert len(puzzles) == 20


def test_unknown_level_is_rejected():
    with pytest.raises(ValueError):
        generate_puzzle("Impossible", random.Random(1))


def test_new_game_starts_with_the_start_numbers_and_three_lives():
    game = start_game("Hard", random.Random(8))
    assert game.numbers == game.puzzle.numbers
    assert len(game.numbers) == 5
    assert game.steps == ()
    assert game.lives == 3
    assert game.status == Status.RUNNING


def test_game_cannot_be_changed_in_place():
    with pytest.raises(FrozenInstanceError):
        game_of(SIMPLE).lives = 99


# --- Steps ---


def test_valid_step_replaces_both_numbers_with_the_result():
    game, outcome = apply_step(game_of(THREE), 0, "+", 1)
    assert outcome == Outcome.CORRECT
    assert sorted(game.numbers) == [7, 8]
    assert game.steps == (Step(3, "+", 5, 8),)
    assert game.lives == 3
    assert game.status == Status.RUNNING


def test_order_matters_for_minus_and_divide():
    game, outcome = apply_step(game_of(THREE), 2, "−", 0)  # 7 − 3
    assert outcome == Outcome.CORRECT
    assert game.steps[-1] == Step(7, "−", 3, 4)
    game, outcome = apply_step(game_of(THREE), 0, "−", 2)  # 3 − 7
    assert outcome == Outcome.WRONG


def test_invalid_step_costs_a_life_and_changes_nothing_else():
    before = game_of(THREE)
    game, outcome = apply_step(before, 2, "÷", 0)  # 7 ÷ 3 is not whole
    assert outcome == Outcome.WRONG
    assert game.lives == 2
    assert game.numbers == before.numbers
    assert game.steps == ()


def test_third_invalid_step_loses_the_game():
    game = game_of(THREE)
    for _ in range(3):
        game, outcome = apply_step(game, 0, "−", 1)  # 3 − 5
        assert outcome == Outcome.WRONG
    assert game.lives == 0
    assert game.status == Status.LOST


def test_choosing_the_same_number_twice_is_ignored():
    before = game_of(THREE)
    game, outcome = apply_step(before, 1, "+", 1)
    assert outcome == Outcome.IGNORED
    assert game == before


@pytest.mark.parametrize("first, second", [(-1, 0), (0, 3), (5, 1)])
def test_positions_outside_the_numbers_are_rejected(first, second):
    with pytest.raises(ValueError):
        apply_step(game_of(THREE), first, "+", second)


def test_steps_after_the_end_are_ignored():
    lost = game_of(THREE, lives=1)
    lost, _ = apply_step(lost, 0, "−", 1)
    assert lost.status == Status.LOST
    game, outcome = apply_step(lost, 0, "+", 1)
    assert outcome == Outcome.IGNORED
    assert game == lost


def test_entering_does_not_change_the_old_game():
    before = game_of(THREE)
    apply_step(before, 0, "+", 1)
    assert before == game_of(THREE)


# --- Winning and getting stuck ---


def test_last_number_equal_to_the_target_wins():
    game, _ = apply_step(game_of(SIMPLE), 0, "×", 1)
    assert game.numbers == (24,)
    assert game.status == Status.WON
    assert not is_stuck(game)


def test_last_number_not_equal_to_the_target_is_stuck_not_won():
    game, outcome = apply_step(game_of(SIMPLE), 0, "+", 1)  # 4 + 6 = 10, not 24
    assert outcome == Outcome.CORRECT
    assert game.status == Status.RUNNING
    assert is_stuck(game)


def test_reaching_the_target_with_numbers_left_is_not_a_win():
    puzzle = Puzzle(numbers=(4, 6, 3), target=24, solution=())
    game, _ = apply_step(game_of(puzzle), 0, "×", 1)  # 24 and 3 are left
    assert game.status == Status.RUNNING
    assert not is_stuck(game)


def test_steps_after_winning_are_ignored():
    won, _ = apply_step(game_of(SIMPLE), 0, "×", 1)
    game, outcome = undo(won)
    assert outcome == Outcome.IGNORED
    assert game == won


# --- Undo and Reset (brief: each costs a life) ---


def test_undo_takes_back_the_last_step_and_costs_a_life():
    game, _ = apply_step(game_of(THREE), 0, "+", 1)
    game, outcome = undo(game)
    assert outcome == Outcome.UNDONE
    assert game.numbers == (3, 5, 7)
    assert game.steps == ()
    assert game.lives == 2


def test_undo_only_takes_back_one_step():
    game, _ = apply_step(game_of(THREE), 0, "+", 1)  # 8, 7
    numbers_after_first_step = game.numbers
    game, _ = apply_step(game, 0, "+", 1)  # 15
    game, _ = undo(game)
    assert game.numbers == numbers_after_first_step
    assert len(game.steps) == 1


def test_reset_goes_back_to_the_start_and_costs_a_life():
    game, _ = apply_step(game_of(THREE), 0, "+", 1)
    game, _ = apply_step(game, 0, "+", 1)
    game, outcome = reset(game)
    assert outcome == Outcome.RESET
    assert game.numbers == (3, 5, 7)
    assert game.steps == ()
    assert game.lives == 2


def test_undo_and_reset_without_steps_are_free():
    before = game_of(THREE)
    for action in (undo, reset):
        game, outcome = action(before)
        assert outcome == Outcome.IGNORED
        assert game == before


def test_losing_the_last_life_by_undo_ends_the_game():
    game, _ = apply_step(game_of(THREE, lives=1), 0, "+", 1)
    game, outcome = undo(game)
    assert outcome == Outcome.UNDONE
    assert game.lives == 0
    assert game.status == Status.LOST


def test_step_text():
    assert Step(8, "×", 7, 56).text == "8 × 7 = 56"


# --- Design rules (AGENTS.md) ---


def test_rule_module_has_no_streamlit_sql_clock_or_own_randomness():
    source = (Path(__file__).resolve().parent.parent / "numberhunt.py").read_text()
    for forbidden in ("streamlit", "sqlite", "SELECT", "datetime.now", "random.Random(", "time.time"):
        assert forbidden not in source, forbidden
