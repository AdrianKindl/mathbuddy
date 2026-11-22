# 012 Profile: statistics, streak and 7 day activity

Source: `docs/product-brief.md`, MB05 and MB R8, scenarios A5, A6, A8 and A9.
Builds on spec 011 (online accounts): every completed test run has an owner.

> **Draft**, to be reviewed by the team before the tests are written.

## Why
Players want to see that they are getting better. Today the Profile section
only shows "Coming soon". After 011 every run belongs to a player, so the app
can show each player their own statistics. These statistics are also the
basis for the leaderboard in 013.

## What

### Statistics rules (`stats.py`, new rule module)
- Pure functions: no Streamlit, no SQL, no clock. They take the player's
  saved runs (`list[SavedRun]`) and, where needed, `today` (a `date`).
- **Tasks completed** = the sum of `correct` over all completed runs (MB R8).
- **Accuracy** = correct ÷ (correct + wrong + skipped) over all completed runs.
  Uses `runs.accuracy`. Without any runs there is no accuracy.
- **Longest streak** = the longest number of consecutive calendar days with at
  least one completed run. Several runs on one day count as one day (MB R8).
  Without any runs the streak is 0.
- **7 day activity** = the number of completed runs on each of the 7 days
  from `today - 6` to `today`, oldest first. Days without runs count 0 (MB R8).
- **Highscores** = the existing `runs.highscores`, unchanged.
- **Calendar day:** runs are saved in UTC. The day of a run is its
  `finished_at` converted to the app time zone `Europe/Lisbon` (decided by
  the team). The app passes the time zone in; `stats.py` does not choose it.

### Screen (`app.py`)
The Profile section no longer shows "Coming soon". From top to bottom:
1. Heading "Profile" and the username.
2. Three numbers side by side: "Tasks completed", "Accuracy" (as a percentage,
   "–" without runs) and "Longest streak" ("3 days", "1 day", "0 days").
3. "Highscores": a table with one row per test type (Addition, Subtraction,
   Multiplication, Division, Random) and one column per level (Easy, Medium,
   Hard, Pro). Empty cells show "–".
4. "Last 7 days": a bar chart. x-axis: the short weekday names (e.g. Mon, Tue),
   today last. Bars: completed runs per day.
- Without any completed run the profile shows the hint
  "Complete a test to see your statistics here." and the empty highscore table.

### Storage
- No new tables. All numbers are calculated from the saved runs of the signed
  in player (`accounts_db.list_runs_for`), never stored separately.
- Only completed test runs count. Aborted runs are never saved (MB R5), runs
  without an owner and runs of other players never appear.

## Changes to earlier specs
- `tests/test_app.py`: the test that expects "Coming soon" for Profile now
  only checks Games. The expectation changes because this spec builds the
  Profile section; no other expected result changes.

## Out of scope
Leaderboard and comparing players (013). Trainer, Knowledge, Textbook and
Games activity in the statistics (they have no owner yet, see 011).
Current streak (the brief asks for the longest streak). Editing the username
or email, deleting the account, password reset, email verification.

## Done when
- **A5 – Saving a run:** after a completed Multiplication Easy run with
  12 correct, 3 wrong and 2 skipped, "Tasks completed" is 12 higher and the
  accuracy includes 12 of 17. An aborted run leaves every number unchanged.
- **A6 – Highscore:** the profile table shows the same highscores as the
  Tests screen, per test type and level.
- **A8 – Streak:** runs on Monday, Tuesday (two runs) and Wednesday, none on
  Thursday, one on Friday: the longest streak is 3 days.
- **A9 – 7 day activity:** two runs today, one yesterday, none on the five
  days before: the chart shows 2 for today, 1 for yesterday and 0 for the
  other five days.
- **Day boundary:** in summer (Lisbon time = UTC+1), a run finished at
  23:30 Lisbon time counts for that day, not the next one, although it is
  00:30 of the next day in UTC.
- **Own data only:** runs of another player and runs without an owner do not
  change any number on the profile.
- **No runs:** a new player sees 0 tasks, "–" accuracy, 0 days streak, an
  empty highscore table, 7 bars of 0 and the hint.
- All existing tests pass; the tests for `stats.py` use fixed dates.
