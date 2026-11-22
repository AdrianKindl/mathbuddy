# 012 Profile: statistics, streak and 7 day activity

Source: `docs/product-brief.md`, MB05 and MB R8 (updated in this spec),
scenarios A5, A6, A8 and A9. Builds on spec 011 (online accounts).

> **Spec review 1 (Adrian):** count all completed activities, not only test
> runs. This version adds owners for Trainer, Knowledge and Textbook and saves
> finished games. Points marked *(to confirm)* need a team decision.

## Why
Players want to see that they are getting better. Today the Profile section
only shows "Coming soon". Players who only use the Trainer, Knowledge or
Games must not get an empty profile, so every completed activity counts.
These statistics are also the basis for the leaderboard in 013.

## Activities
An **activity** is one completed:

| Kind | Saved in | Counts for tasks and accuracy | Counts for streak and chart |
|---|---|---|---|
| Test run | `runs` | yes: correct, wrong, skipped | yes |
| Trainer session | `trainer_sessions` | yes: correct, wrong, skipped | yes |
| Tricks practice round | `practice_rounds` | yes: correct, and 10 − correct not correct | yes |
| Textbook practice round | `textbook_rounds` | yes: correct, and 10 − correct not correct | yes |
| Game (Mini Sudoku, Sudoku) | `game_results` (new) | no | yes |

- Aborted test runs, aborted Trainer sessions and practice rounds left early
  are never saved (MB R5, existing rules), so they never count.
- A game counts when it ends: won, or lost after losing all lives. A game
  that is left before it ends does not count *(to confirm: lost games count)*.
- Practice rounds always have 10 tasks and are only saved when all 10 are
  answered, so "not correct" (wrong or skipped) is 10 − correct
  (`knowledge.ROUND_LENGTH`, `textbook.ROUND_LENGTH`). The tables keep their
  columns.

## What

### Statistics rules (`stats.py`, new rule module)
- Pure functions: no Streamlit, no SQL, no clock. They take the player's
  activities and, where needed, `today` (a `date`) and the time zone.
- An `Activity` has: kind, `finished_at` (UTC), correct, not_correct
  (wrong + skipped; 0 for games) and whether it counts for tasks.
- **Tasks completed** = the sum of correct over Tests, Trainer and practice rounds.
- **Accuracy** = correct ÷ (correct + wrong + skipped) over Tests, Trainer and
  practice rounds. Without any such activity there is no accuracy (shown "–").
- **Longest streak** = the longest number of consecutive calendar days with at
  least one activity of any kind. Several activities on one day count as one
  day. Without any activity the streak is 0.
- **7 day activity** = the number of activities of any kind on each of the 7
  days from `today - 6` to `today`, oldest first. Days without activity show 0.
- **Calendar day:** activities are saved in UTC. The day of an activity is its
  `finished_at` converted to `Europe/Lisbon` (decided by the team). The app
  passes the time zone in; `stats.py` does not choose it.
- **Highscores** = `runs.highscores` over the player's test runs: the same
  function the Tests tab uses. Highscores are about Tests only.

### Storage (owners and games)
- **New table `activity_owners`**: kind, activity_id, user_id; one owner per
  (kind, activity_id). When a Trainer session, Tricks round or Textbook round
  is saved, its owner is recorded here, like `run_owners` for test runs (011).
- **New table `game_results`**: id, user_id, game, level, finished_at, outcome
  (won or lost). Saved once when a game ends; saving the same id again changes
  nothing.
- Activities saved before this spec have no owner; they are kept but count for
  nobody (like test runs before 011).
- Each player only sees their own activities. Totals, streak and chart are
  calculated from the saved activities, never stored separately (MB R8).
- The rules of Tests, Trainer, Knowledge, Textbook and Games do not change.
  Only their saving code records the owner (and games are now saved).

### Screen (`app.py`)
The Profile section no longer shows "Coming soon". From top to bottom:
1. Heading "Profile" and the username.
2. Three numbers side by side: "Tasks completed", "Accuracy" (as a percentage,
   "–" without tasks) and "Longest streak" ("3 days", "1 day", "0 days").
3. "Highscores": a table with one row per test type (Addition, Subtraction,
   Multiplication, Division, Random) and one column per level (Easy, Medium,
   Hard, Pro). Empty cells show "–".
4. "Last 7 days": a bar chart. x-axis: the short weekday names (e.g. Mon, Tue),
   today last. Bars: completed activities per day.
- Without any activity the profile shows the hint
  "Complete a test, training, practice round or game to see your statistics here."
  It does not crash and shows 0 tasks, "–" accuracy, 0 days streak, an empty
  highscore table and 7 bars of 0.

## Changes to earlier specs
- `tests/test_app.py`: the test that expects "Coming soon" for Profile now
  only checks Games. No other expected result changes.
- Trainer (002), Knowledge (009), Textbook (010) and Games (002, 002b): their
  saving code records the signed in player as owner; finished games are saved.
  Their existing tests keep passing unchanged.
- `docs/product-brief.md`: MB R8 counts all activities (see below).

## Out of scope
Leaderboard and comparing players (013). Highscores for Trainer, Knowledge or
Games. Current streak (the brief asks for the longest streak). Showing a
history list of activities. Editing the username or email, deleting the
account, password reset, email verification.

## Done when
- **New player:** no activity: 0 tasks, "–" accuracy, 0 days streak, empty
  highscore table, 7 bars of 0 and the hint; no error.
- **A5 – Saving a run:** after a completed Multiplication Easy run with
  12 correct, 3 wrong and 2 skipped, "Tasks completed" is 12 higher and the
  accuracy includes 12 of 17. An aborted run leaves every number unchanged.
- **All kinds count:** a finished Trainer session with 8 correct, 1 wrong and
  1 skipped adds 8 tasks and 8 of 10 to the accuracy; a Tricks round with
  7 correct adds 7 tasks and 7 of 10; a finished game adds one activity but no
  tasks. Each adds 1 to today's bar.
- **Never counted:** an aborted Trainer session, a practice round left early
  and a game left before it ends change nothing.
- **A6 – Highscore:** the profile table uses `runs.highscores` and shows the
  same highscores as the Tests tab, per test type and level.
- **A8 – Streak:** activities on Monday (a test), Tuesday (a Trainer session
  and a game) and Wednesday (a Tricks round), none on Thursday, one on Friday:
  the longest streak is 3 days. Two activities on one day count as one day.
- **A9 – 7 day activity:** two activities today, one yesterday, none on the
  five days before: the chart shows 2 for today, 1 for yesterday and 0 for the
  other five days.
- **Day boundary:** in summer (Lisbon time = UTC+1), an activity finished at
  23:30 Lisbon time counts for that day, not the next one.
- **Own data only:** activities of another player and activities without an
  owner do not change any number on the profile.
- All existing tests pass; the tests for `stats.py` use fixed dates.
