"""Profile statistics rules in stats.py (spec 012, MB R8).

Pure functions: fixed dates, no database, no clock. Activities are saved in
UTC; calendar days are counted in the app time zone (Europe/Lisbon).
"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from stats import (
    Activity,
    Kind,
    accuracy,
    last_7_days,
    local_day,
    longest_streak,
    tasks_completed,
)

LISBON = ZoneInfo("Europe/Lisbon")
TODAY = date(2026, 11, 20)  # a Friday, winter: Lisbon time = UTC


def at(day, hour=12, minute=0):
    """A UTC moment on the given day."""
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc)


def a_test_run(day=TODAY, correct=0, not_correct=0):
    return Activity(Kind.TEST, at(day), correct, not_correct)


def game(day=TODAY):
    return Activity(Kind.GAME, at(day))


# --- Kinds of activity ---


def test_there_are_five_kinds_of_activity():
    assert [kind.value for kind in Kind] == ["test", "trainer", "tricks", "textbook", "game"]


@pytest.mark.parametrize("kind", [Kind.TEST, Kind.TRAINER, Kind.TRICKS, Kind.TEXTBOOK])
def test_tests_training_and_practice_count_for_tasks(kind):
    assert Activity(kind, at(TODAY), 3, 1).counts_for_tasks


def test_games_do_not_count_for_tasks():
    assert not game().counts_for_tasks


def test_a_game_has_no_tasks():
    assert (game().correct, game().not_correct) == (0, 0)


# --- Tasks completed (MB R8) ---


def test_no_activity_means_no_tasks_completed():
    assert tasks_completed([]) == 0


def test_tasks_completed_adds_the_correct_answers_of_every_kind_except_games():
    activities = [
        Activity(Kind.TEST, at(TODAY), 12, 5),
        Activity(Kind.TRAINER, at(TODAY), 8, 2),
        Activity(Kind.TRICKS, at(TODAY), 7, 3),
        Activity(Kind.TEXTBOOK, at(TODAY), 6, 4),
        game(),
    ]
    assert tasks_completed(activities) == 12 + 8 + 7 + 6


# --- Accuracy (MB R8) ---


def test_no_tasks_means_no_accuracy():
    assert accuracy([]) is None


def test_only_games_means_no_accuracy():
    assert accuracy([game(), game()]) is None


def test_accuracy_of_scenario_a5_is_12_of_17():
    assert accuracy([a_test_run(correct=12, not_correct=3 + 2)]) == pytest.approx(12 / 17)


def test_accuracy_counts_all_tasks_of_tests_training_and_practice():
    activities = [
        Activity(Kind.TEST, at(TODAY), 12, 5),
        Activity(Kind.TRAINER, at(TODAY), 8, 2),
        Activity(Kind.TRICKS, at(TODAY), 7, 3),
        game(),
    ]
    assert accuracy(activities) == pytest.approx((12 + 8 + 7) / (17 + 10 + 10))


def test_activities_without_any_task_give_no_accuracy():
    assert accuracy([a_test_run(correct=0, not_correct=0)]) is None


# --- Calendar days in Lisbon ---


def test_in_winter_the_lisbon_day_is_the_utc_day():
    assert local_day(datetime(2026, 1, 10, 23, 30, tzinfo=timezone.utc), LISBON) == date(2026, 1, 10)


def test_in_summer_2330_in_lisbon_is_still_the_same_day():
    # 23:30 Lisbon summer time is 22:30 UTC
    assert local_day(datetime(2026, 7, 10, 22, 30, tzinfo=timezone.utc), LISBON) == date(2026, 7, 10)


def test_in_summer_0030_in_lisbon_is_the_next_day_although_utc_is_still_before_midnight():
    # 00:30 Lisbon summer time is 23:30 UTC of the day before
    assert local_day(datetime(2026, 7, 10, 23, 30, tzinfo=timezone.utc), LISBON) == date(2026, 7, 11)


# --- Longest streak (MB R8, scenario A8) ---


def test_no_activity_means_a_streak_of_0():
    assert longest_streak([], LISBON) == 0


def test_one_activity_is_a_streak_of_1():
    assert longest_streak([a_test_run()], LISBON) == 1


def test_scenario_a8_longest_streak_is_3_days():
    monday = date(2026, 11, 16)
    tuesday, wednesday, friday = (monday + timedelta(days=n) for n in (1, 2, 4))
    activities = [
        a_test_run(monday),
        Activity(Kind.TRAINER, at(tuesday, 9), 5, 0),
        game(tuesday),
        Activity(Kind.TRICKS, at(wednesday), 7, 3),
        a_test_run(friday),
    ]
    assert longest_streak(activities, LISBON) == 3


def test_several_activities_on_one_day_count_as_one_day():
    assert longest_streak([a_test_run(), game(), a_test_run(), game()], LISBON) == 1


def test_games_alone_make_a_streak():
    days = [TODAY - timedelta(days=n) for n in range(4)]
    assert longest_streak([game(day) for day in days], LISBON) == 4


def test_the_longest_streak_wins_even_if_it_is_not_the_latest():
    days = [date(2026, 11, d) for d in (1, 2, 3, 4, 10, 11)]
    assert longest_streak([a_test_run(day) for day in days], LISBON) == 4


def test_order_of_the_activities_does_not_matter():
    days = [date(2026, 11, d) for d in (3, 1, 2)]
    assert longest_streak([a_test_run(day) for day in days], LISBON) == 3


def test_streak_uses_lisbon_days():
    # Summer: 23:30 UTC on 10 July is 00:30 on 11 July in Lisbon,
    # so together with an activity at noon on 12 July it is a 2-day streak.
    late = Activity(Kind.TEST, datetime(2026, 7, 10, 23, 30, tzinfo=timezone.utc), 1, 0)
    next_day = Activity(Kind.TEST, datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc), 1, 0)
    assert longest_streak([late, next_day], LISBON) == 2


# --- 7 day activity (MB R8, scenario A9) ---


def test_seven_days_end_today_oldest_first():
    days = [day for day, _ in last_7_days([], TODAY, LISBON)]
    assert days == [TODAY - timedelta(days=n) for n in range(6, -1, -1)]


def test_no_activity_shows_seven_zeros():
    assert [count for _, count in last_7_days([], TODAY, LISBON)] == [0] * 7


def test_scenario_a9_two_today_one_yesterday_zero_before():
    yesterday = TODAY - timedelta(days=1)
    activities = [a_test_run(TODAY), game(TODAY), Activity(Kind.TRAINER, at(yesterday), 4, 1)]
    counts = [count for _, count in last_7_days(activities, TODAY, LISBON)]
    assert counts == [0, 0, 0, 0, 0, 1, 2]


def test_every_kind_counts_as_one_activity_in_the_chart():
    activities = [Activity(kind, at(TODAY), 1, 0) for kind in Kind]
    assert last_7_days(activities, TODAY, LISBON)[-1] == (TODAY, 5)


def test_activities_older_than_seven_days_or_in_the_future_are_left_out():
    activities = [a_test_run(TODAY - timedelta(days=7)), a_test_run(TODAY + timedelta(days=1))]
    assert [count for _, count in last_7_days(activities, TODAY, LISBON)] == [0] * 7


def test_chart_uses_lisbon_days():
    today = date(2026, 7, 11)
    late = Activity(Kind.TEST, datetime(2026, 7, 10, 23, 30, tzinfo=timezone.utc), 1, 0)
    assert last_7_days([late], today, LISBON)[-1] == (today, 1)
