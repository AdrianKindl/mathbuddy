# 015 Tests tab: only the best score for the selected test

Source: `docs/product-brief.md` MB05, MB06 and MB R6 (MB06 changed in this spec).
Agreed by the team in the group chat.

## Why
Since 012 the full highscore table (5 test types × 4 levels) is shown twice:
on the Tests tab and on the Profile. Together with the leaderboard (013) the
Tests tab is crowded. Before starting a test, a player only cares about the
record for the test type and level they have selected.

## What

### Tests tab (`app.py`)
- The full highscore table and its heading "Highscores" are no longer shown
  on the Tests tab.
- Instead, below the Start button, one number: **"Your best"** with the
  signed-in player's highscore (MB R6) for the selected test type and level,
  or "–" without a completed run of that test type and level.
- It follows the Operation and Level buttons and changes when the selection
  changes, like the leaderboard.
- It uses the same rule as before: `runs.highscores` over the player's own
  runs. Nothing new is stored.
- The leaderboard (MB06) follows directly below "Your best", unchanged.

### Profile (`app.py`)
- Unchanged: the full highscore table stays on the Profile (MB05).

### Product brief
- MB06: the leaderboard is shown below the player's best score for the
  selected test type and level; the full highscore table is on the Profile.
- Change note for version 1.3.

## Changes to earlier specs
The Tests tab no longer has a table of highscores, so tests that read that
table now read "Your best" for the selected test type and level instead.
What each test checks stays the same:
- `tests/test_app.py`: the 20-cell table test now opens the Profile; the
  tests for aborted runs, a Medium run not changing Easy and a restart read
  "Your best" after selecting the test type and level.
- `tests/test_app_accounts.py`: `multiplication_easy_highscore` selects
  Multiplication and Easy and reads "Your best".
- `tests/test_app_leaderboard.py`: the leaderboard is now the first and only
  table on the Tests tab; "own runs only" reads "Your best".
- `tests/test_app_regression.py`: the Tests tab shows "Your best" and the
  leaderboard (one table), not the heading "Highscores".
- `tests/test_app_profile.py`: the Profile table and the Tests tab's
  "Your best" show the same highscore (both from `runs.highscores`).

## Out of scope
Any change to the Profile, the leaderboard, the result screen after a test
(MB04 still shows the highscore and "new highscore"), or how highscores are
calculated.

## Done when
- The Tests tab shows no highscore table and no "Highscores" heading.
- With nothing played, "Your best" shows "–".
- With Multiplication Easy runs of 15 and 9 and a Multiplication Medium run
  of 7: selecting Multiplication Easy shows 15, Multiplication Medium shows 7,
  Addition Easy shows "–".
- A run of another player or a run without an owner never changes "Your best".
- The Profile still shows the full table with the same values.
- All tests pass.
