"""Number Chain rules: chain generation, answers, score, lives (spec 002e)."""

import random
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import numberchain
from numberchain import (
    Chain,
    ChainStep,
    Game,
    Outcome,
    Status,
    answer,
    apply,
    chain_length,
    generate_chain,
    start_game,
)
from tasks import LEVELS

# 7 + 8 = 15, × 3 = 45, − 9 = 36, ÷ 6 = 6
KNOWN = Chain(
    start=7,
    steps=(ChainStep("+", 8), ChainStep("×", 3), ChainStep("−", 9), ChainStep("÷", 6)),
)
OPPOSITE = {"+": "−", "−": "+", "×": "÷", "÷": "×"}


def known_game(**changes):
    return Game(level="Easy", chain=KNOWN, **changes)


# --- Constants ---


def test_constants_match_the_spec():
    assert numberchain.LIVES == 3
    assert numberchain.MAX_EXTRA_STEPS == 10
    assert list(numberchain.LEVEL_SETTINGS) == list(LEVELS)
    steps = {level: s.steps for level, s in numberchain.LEVEL_SETTINGS.items()}
    assert steps == {"Easy": 4, "Medium": 5, "Hard": 6, "Pro": 8}
    seconds = {level: s.seconds for level, s in numberchain.LEVEL_SETTINGS.items()}
    assert seconds == {"Easy": 3.0, "Medium": 2.5, "Hard": 2.0, "Pro": 1.5}
    assert numberchain.LEVEL_SETTINGS["Easy"].operations == ("+", "−")
    assert numberchain.LEVEL_SETTINGS["Medium"].operations == ("+", "−", "×")


# --- Calculating ---


def test_known_chain_result():
    assert KNOWN.result == 6


@pytest.mark.parametrize(
    "value, op, number, result", [(7, "+", 8, 15), (15, "×", 3, 45), (45, "−", 9, 36), (36, "÷", 6, 6)]
)
def test_apply(value, op, number, result):
    assert apply(value, ChainStep(op, number)) == result


def test_step_text():
    assert ChainStep("×", 3).text == "× 3"


def test_unknown_operation_is_rejected():
    with pytest.raises(ValueError):
        apply(3, ChainStep("^", 2))


# --- Generating chains (Done when: Generation, Variety) ---


@pytest.mark.parametrize("level", LEVELS)
def test_generated_chains_follow_the_level(level):
    settings = numberchain.LEVEL_SETTINGS[level]
    lengths = [chain_length(level, score) for score in (0, 5, 10)]
    for length in lengths:
        for seed in range(40):
            chain = generate_chain(level, length, random.Random(seed))
            assert len(chain.steps) == length, (level, seed)
            low, high = settings.start
            assert low <= chain.start <= high, (level, seed)

            value = chain.start
            previous = None
            for step in chain.steps:
                assert step.op in settings.operations, (level, seed, step)
                low, high = settings.add if step.op in ("+", "−") else settings.multiply
                assert low <= step.value <= high, (level, seed, step)
                assert step.value != 1
                if step.op == "÷":
                    assert value % step.value == 0, (level, seed, value, step)
                value = apply(value, step)
                assert 1 <= value <= settings.largest, (level, seed, value)
                if previous is not None:
                    assert step != previous, (level, seed)
                    assert step != ChainStep(OPPOSITE[previous.op], previous.value), (level, seed)
                previous = step
            assert value == chain.result


def test_harder_levels_use_multiply_and_divide():
    ops = {
        step.op
        for seed in range(30)
        for step in generate_chain("Hard", 6, random.Random(seed)).steps
    }
    assert ops == {"+", "−", "×", "÷"}


def test_same_seed_gives_the_same_chain():
    assert generate_chain("Pro", 8, random.Random(5)) == generate_chain("Pro", 8, random.Random(5))


def test_different_seeds_give_different_chains():
    chains = {generate_chain("Medium", 5, random.Random(seed)) for seed in range(20)}
    assert len(chains) == 20


def test_unknown_level_is_rejected():
    with pytest.raises(ValueError):
        generate_chain("Impossible", 4, random.Random(1))


# --- Chain length ---


def test_chain_grows_by_one_step_per_point_up_to_ten_more():
    assert chain_length("Easy", 0) == 4
    assert chain_length("Easy", 1) == 5
    assert chain_length("Easy", 10) == 14
    assert chain_length("Easy", 25) == 14
    assert chain_length("Pro", 0) == 8


# --- Starting and answering ---


def test_new_game_starts_with_three_lives_and_no_points():
    game = start_game("Hard", random.Random(2))
    assert game.lives == 3
    assert game.score == 0
    assert game.status == Status.RUNNING
    assert len(game.chain.steps) == 6


def test_game_cannot_be_changed_in_place():
    with pytest.raises(FrozenInstanceError):
        known_game().score = 99


def test_right_result_adds_a_point_and_makes_the_next_chain_longer():
    game, outcome = answer(known_game(), "6", random.Random(1))
    assert outcome == Outcome.CORRECT
    assert game.score == 1
    assert game.lives == 3
    assert game.last_result == 6
    assert len(game.chain.steps) == chain_length("Easy", 1) == 5


def test_wrong_result_costs_a_life_and_keeps_the_length():
    game, outcome = answer(known_game(), "7", random.Random(1))
    assert outcome == Outcome.WRONG
    assert game.score == 0
    assert game.lives == 2
    assert game.last_result == 6  # the right result, to show the user
    assert len(game.chain.steps) == 4
    assert game.status == Status.RUNNING


@pytest.mark.parametrize("raw", ["", "  ", "abc", "6.0"])
def test_empty_or_non_numeric_answers_change_nothing(raw):
    before = known_game()
    game, outcome = answer(before, raw, random.Random(1))
    assert outcome == Outcome.IGNORED
    assert game == before


def test_spaces_around_the_answer_are_allowed():
    _, outcome = answer(known_game(), " 6 ", random.Random(1))
    assert outcome == Outcome.CORRECT


def test_third_wrong_answer_ends_the_game():
    game = known_game(lives=1)
    game, outcome = answer(game, "99", random.Random(1))
    assert outcome == Outcome.WRONG
    assert game.lives == 0
    assert game.status == Status.LOST
    assert game.last_result == 6


def test_answers_after_the_end_are_ignored():
    lost, _ = answer(known_game(lives=1), "99", random.Random(1))
    game, outcome = answer(lost, str(lost.chain.result), random.Random(1))
    assert outcome == Outcome.IGNORED
    assert game == lost


def test_answering_does_not_change_the_old_game():
    before = known_game()
    answer(before, "6", random.Random(1))
    assert before == known_game()


def test_a_long_run_keeps_working():
    rng = random.Random(4)
    game = start_game("Pro", rng)
    for _ in range(15):
        game, outcome = answer(game, str(game.chain.result), rng)
        assert outcome == Outcome.CORRECT
    assert game.score == 15
    assert len(game.chain.steps) == 8 + 10


# --- Design rules (AGENTS.md) ---


def test_rule_module_has_no_streamlit_sql_clock_or_own_randomness():
    source = (Path(__file__).resolve().parent.parent / "numberchain.py").read_text()
    for forbidden in ("streamlit", "sqlite", "SELECT", "datetime.now", "random.Random(", "time.time"):
        assert forbidden not in source, forbidden
