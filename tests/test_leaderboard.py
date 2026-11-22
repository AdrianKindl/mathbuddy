"""Leaderboard rules in leaderboard.py (MB R10, A11, A12)."""

from dataclasses import fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from leaderboard import TOP, Better, Board, Entry, Row, build

ROOT = Path(__file__).resolve().parent.parent
MONDAY = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
TUESDAY = MONDAY + timedelta(days=1)
WEDNESDAY = MONDAY + timedelta(days=2)


def entry(user_id, value, when=MONDAY, username=None):
    return Entry(user_id=user_id, username=username or user_id, value=value, achieved_at=when)


def ranking(board):
    return [(row.rank, row.username, row.value) for row in board.top]


def players(count, *, start=100):
    """`count` players with different scores: p01 has the most."""
    return [entry(f"p{n:02d}", start - n) for n in range(1, count + 1)]


# --- Order and tie-break (A11) ---


def test_higher_scores_rank_first():
    board = build([entry("lena", 15), entry("mia", 18), entry("adrian", 12)])
    assert ranking(board) == [(1, "mia", 18), (2, "lena", 15), (3, "adrian", 12)]


def test_equal_scores_rank_the_earlier_one_first():
    board = build([entry("adrian", 18, TUESDAY), entry("mia", 18, MONDAY), entry("lena", 15)])
    assert ranking(board) == [(1, "mia", 18), (2, "adrian", 18), (3, "lena", 15)]


def test_equal_score_and_time_rank_by_username_ignoring_case():
    board = build([entry("u1", 18, username="mia"), entry("u2", 18, username="Adrian"),
                   entry("u3", 18, username="lena")])  # fmt: skip
    assert [row.username for row in board.top] == ["Adrian", "lena", "mia"]


def test_every_row_gets_its_own_rank():
    board = build([entry("a", 10), entry("b", 10, TUESDAY), entry("c", 10, WEDNESDAY)])
    assert [row.rank for row in board.top] == [1, 2, 3]


# --- One entry per user (A11) ---


def test_each_user_appears_once_with_their_best_score():
    board = build([entry("adrian", 12, MONDAY), entry("adrian", 18, TUESDAY), entry("mia", 15)])
    assert ranking(board) == [(1, "adrian", 18), (2, "mia", 15)]
    assert board.top[0].achieved_at == TUESDAY


def test_the_earliest_time_counts_when_the_best_score_was_reached_twice():
    board = build([entry("adrian", 18, WEDNESDAY), entry("adrian", 18, MONDAY),
                   entry("mia", 18, TUESDAY)])  # fmt: skip
    assert ranking(board) == [(1, "adrian", 18), (2, "mia", 18)]
    assert board.top[0].achieved_at == MONDAY


def test_users_are_told_apart_by_id_not_by_name():
    board = build([entry("u1", 10, username="sam"), entry("u2", 9, username="sam")])
    assert [row.user_id for row in board.top] == ["u1", "u2"]


# --- Top 15 and the own row (A12) ---


def test_only_the_top_15_are_shown():
    board = build(players(20))
    assert TOP == 15
    assert [row.rank for row in board.top] == list(range(1, 16))
    assert board.top[-1].user_id == "p15"


def test_own_row_below_the_top_15_shows_the_real_rank():
    board = build(players(20), user_id="p18")
    assert len(board.top) == 15
    assert not any(row.is_you for row in board.top)
    assert board.own == Row(rank=18, user_id="p18", username="p18", value=82,
                            achieved_at=MONDAY, is_you=True)  # fmt: skip


def test_own_row_inside_the_top_15_is_highlighted_and_not_repeated():
    board = build(players(20), user_id="p04")
    assert [row.user_id for row in board.top if row.is_you] == ["p04"]
    assert board.top[3].rank == 4
    assert board.own is None


def test_no_own_row_without_a_run():
    board = build(players(20), user_id="newcomer")
    assert board.own is None
    assert not any(row.is_you for row in board.top)


def test_no_own_row_without_a_signed_in_user():
    board = build(players(20))
    assert board.own is None
    assert not any(row.is_you for row in board.top)


def test_own_row_on_rank_15_is_inside_and_on_rank_16_outside():
    assert build(players(20), user_id="p15").own is None
    assert build(players(20), user_id="p16").own.rank == 16


def test_an_empty_leaderboard():
    assert build([], user_id="p01") == Board(top=(), own=None)


def test_the_size_of_the_top_can_be_changed():
    board = build(players(8), top=5, user_id="p07")
    assert [row.rank for row in board.top] == [1, 2, 3, 4, 5]
    assert board.own.rank == 7


# --- Ready for "lower is better" (later game leaderboards) ---


def test_lower_is_better_ranks_smaller_values_first():
    board = build([entry("mia", 95.5), entry("lena", 61.2), entry("adrian", 70.0)],
                  better=Better.LOWER)  # fmt: skip
    assert ranking(board) == [(1, "lena", 61.2), (2, "adrian", 70.0), (3, "mia", 95.5)]


def test_lower_is_better_keeps_each_users_smallest_value_and_the_same_tie_break():
    board = build([entry("adrian", 70, MONDAY), entry("adrian", 61, TUESDAY),
                   entry("mia", 61, MONDAY)], better=Better.LOWER)  # fmt: skip
    assert ranking(board) == [(1, "mia", 61), (2, "adrian", 61)]


def test_higher_is_better_is_the_default():
    entries = [entry("a", 1), entry("b", 2)]
    assert build(entries) == build(entries, better=Better.HIGHER)


# --- Privacy and design rules ---


def test_entries_and_rows_carry_no_email():
    for record in (Entry, Row):
        assert not any("mail" in field.name for field in fields(record))


def test_rule_module_follows_the_design_rules():
    source = (ROOT / "leaderboard.py").read_text(encoding="utf-8")
    for forbidden in ("streamlit", "sqlite3", "SELECT ", ".now(", "time.time", "random."):
        assert forbidden not in source


@pytest.mark.parametrize("better", list(Better))
def test_build_does_not_change_its_input(better):
    entries = [entry("b", 2), entry("a", 1)]
    copy = list(entries)
    build(entries, better=better)
    assert entries == copy
