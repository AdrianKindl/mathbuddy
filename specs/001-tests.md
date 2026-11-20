# 001 – Tests: play a 60-second test and keep the highscore

## Why
A user should be able to pick any test type and level, solve as many tasks as
possible in 60 seconds, see the result, and find their highscore still there
after coming back later.

## What
- The Tests screen offers five test types (Addition, Subtraction,
  Multiplication, Division, Random) and four levels (Easy, Medium, Hard, Pro).
- Tasks are generated randomly following MB R1 (number ranges per operation and
  level, subtraction result >= 1, division without remainder, no trivial
  factors/divisors from Medium upwards). Random picks one of the four
  operations per task with equal probability.
- Every round generates new tasks; the same task never appears twice in a row (MB R2).
- After choosing, a 3-second countdown runs, then a 60-second timer starts and
  stays visible.
- The user types an answer and submits it. Correct: +1 point, field flashes
  green, new task. Wrong: no point, field flashes red, new task. Skip: counts as
  wrong and is recorded as skipped. Empty or non-numeric input is not evaluated (MB R3).
- Answers submitted at or after 60 seconds do not count; the run then ends (MB R4).
- At the end, show score, wrong, skipped, accuracy, and the highscore for this
  test type and level; indicate a new highscore (MB R6).
- Only completed runs are saved in SQLite (test type, level, date and time,
  correct, wrong, skipped). An aborted run is not saved (MB R5).
- The Tests screen shows the saved highscore per test type and level, also
  after the app is stopped and restarted. Highscores are calculated from saved
  runs, not stored separately.
- The navigation shows Tests, Trainer, Knowledge, Games, Profile; all except
  Tests show "Coming soon" (MB01).
- Implements MB01 (partly), MB02, MB03, MB04 and MB R1–R6, with A1–A4, A6 and
  the run-saving part of A5.

## Out of scope
Accounts and sign-in (MB05, MB R7): runs are saved without a user for now.
Profile statistics, streak and 7-day chart (MB R8). Trainer, Knowledge, Games.

## Done when
- **Generation:** for each of the 20 test type/level combinations, 1,000
  generated tasks (fixed seed) all follow MB R1. Examples: Pro division divisor
  101–291, result 11–28, no remainder; Easy subtraction result >= 1; no Medium
  multiplication with a factor of 10.
- **Variety:** two rounds with different seeds produce different task
  sequences; within a round no task appears twice in a row.
- **Answers:** for 7 × 8, answer 56 → score 1; answer 54 → wrong 1, score 0;
  Skip → skipped 1, counts as wrong; empty input → nothing changes.
- **Time limit:** with the run started at t = 0, an answer at 59.9 s counts; an
  answer at 60.0 s does not, and the run is over. The countdown is not part of the 60 s.
- **Accuracy:** 12 correct, 3 wrong, 2 skipped → accuracy 12/17.
- **Highscore:** saved Multiplication Easy runs with 15 and 12 points →
  highscore 15; a new run with 18 → 18 and flagged as new; a Multiplication
  Medium run does not change the Easy highscore.
- **Aborted run:** an aborted run leaves the saved runs unchanged.
- **Restart:** after completing a run, stopping the app with Ctrl+C and
  starting it again, the Tests screen still shows that highscore.
  