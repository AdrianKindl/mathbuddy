# Mathbuddy – Business Requirements

> Train mental arithmetic with short, varied, measurable practice.

**5 sections · 4 difficulty levels · 60-second tests**
Group project · Introduction to Programming · Version 1.1 · 22 November 2026

> **Changes in 1.1 (spec 011, online accounts):** passwords and a shared online database are now in scope (MB05, MB R7, new MB R9, scope boundaries, extended A7, new A10).

---

## The opportunity
Many people want to get faster and more confident at mental arithmetic, but practice apps either repeat the same tasks or give no sense of progress. Mathbuddy offers short timed tests, configurable training, tips and tricks, and logic games. Every round uses new tasks, so users train skills instead of memorising answers, and their profile shows how they are improving.

All text in the app is in English.

## Product overview
The app has five sections, reached through a main navigation:

| Section | Purpose | Release |
|---|---|---|
| **Tests** | 60-second tests: solve as many tasks as possible | R1 |
| **Profile** | Account, statistics, streak, 7-day activity | R1 |
| **Trainer** | Configurable practice by operation, number type and special topic | R2–R3 |
| **Knowledge** | Tips and tricks with practice examples | R3 |
| **Games** | Mini Sudoku, Sudoku, Number Hunt, Magic Square | R4 |

## First release (R1)
Deliver the **Tests** section and the **Profile** section. The other three sections appear in the navigation and show "Coming soon".

Tests offer five test types (Addition, Subtraction, Multiplication, Division, Random) at four levels (Easy, Medium, Hard, Pro). A test lasts 60 seconds. Tasks are generated within fixed rules per operation and level (MB R1). A user can create an account with a unique username and an email address, sign in with their username, and see their statistics.

## The user journey (R1)
The user creates an account or signs in. They open Tests, choose a test type and level, and see a 3-second countdown. The 60-second timer starts and stays visible. They type answers; correct answers flash green, wrong answers flash red, and either way a new task appears. They can skip a task they cannot solve. When time runs out they see their score, accuracy and highscore. Later they open their Profile to see completed tasks, their longest streak and their activity over the last 7 days. They come back on another day and continue where their statistics left off.

---

## Required capabilities

### MB01 – Navigate the app
Show the five sections: Tests, Trainer, Knowledge, Games, Profile. Sections not yet built show "Coming soon".

### MB02 – Start a test
Let the signed-in user choose one of five test types and one of four levels. Show a 3-second countdown, then start a 60-second timer that is visible throughout the test.

### MB03 – Solve tasks
Show one task at a time with an answer field. After submitting, the field briefly flashes green (correct) or red (wrong) and a new task appears. Provide a Skip button. Allow the user to abort a running test.

### MB04 – See the result
When the time is up, show the score (correct answers), the number of wrong and skipped tasks, the accuracy, and the highscore for this test type and level. Indicate when the run sets a new highscore.

### MB05 – Account and profile
Let a user create an account with a username, an email address and a password (typed twice), and sign in with their username and password from any device. A user must be signed in to use the app; without a user only the sign in screen is shown. A signed in user can sign out. The profile shows the username, total tasks completed, accuracy, longest streak, the highscore per test type and level, and a bar chart of completed activities for each of the last 7 days (x-axis: weekdays, bars: completed activities per day).

---

## Business rules

### MB R1 – Task generation
Tasks are generated randomly within these rules. All bounds are inclusive.

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| **Addition** a + b | a, b: 1–19 | a, b: 20–249 | a, b: 250–1,249 | a, b: 1,250–5,000 |
| **Subtraction** a − b | a, b: 1–19 | a, b: 10–99 | a, b: 100–999 | a, b: 1,000–9,999 |
| **Multiplication** a × b | a, b: 2–9 | a: 11–28, b: 2–9 | a, b: 11–19 | a: 20–48, b: 11–17 |
| **Division** a ÷ b = q | b: 2–9, q: 2–9 | b: 2–9, q: 11–29 | b: 29–99, q: 11–29 | b: 101–291, q: 11–28 |

- **Subtraction:** the larger number comes first; the result is always at least 1.
- **Division:** the divisor b and the result q are chosen first, and a = b × q is shown. Every division has a whole-number result and no remainder.
- **Trivial tasks:** from Medium upwards, no factor of 1 or 10 and no divisor of 1, 10 or 100 (already reflected in the table).
- **Random test:** each task uses one of the four operations, chosen with equal probability, at the selected level.

### MB R2 – Variety
Tasks are generated anew for every round. There are no fixed task lists. The same task never appears twice in a row.

### MB R3 – Answer evaluation
Answers are whole numbers. A correct answer adds one point and shows the next task. A wrong answer adds no point and shows a new task (the wrong task is not repeated). A skipped task counts as a wrong answer: it adds no point and lowers the accuracy; it is recorded as skipped. An empty or non-numeric entry is not evaluated and does not count.

Accuracy = correct ÷ (correct + wrong + skipped).

### MB R4 – Time limit
The 3-second countdown does not count towards the test time. An answer submitted within 60 seconds of the start counts; an answer submitted at or after 60 seconds does not. The limit is enforced by the rules, not only by the timer display.

### MB R5 – Completed runs
Only a run that reaches the end of its 60 seconds is completed and saved. An aborted run is not saved and does not affect statistics, highscores or streaks.

### MB R6 – Highscore
The highscore for a test type and level is the highest score among the user's completed runs of that test type and level. A run with a lower score leaves the highscore unchanged.

### MB R7 – Accounts
A username is 3–20 characters (letters A–Z, digits, underscore) and unique regardless of upper or lower case ("Adrian" and "adrian" are the same username). An email address must have a valid format (`name@domain.tld`, no spaces) and may belong to only one account, compared in lower case. A password has at least 8 characters and must be typed the same way twice. A rejected sign-up shows every reason that applies, and only those; when the user corrects a field, the shown reasons are updated. Passwords are never stored, only a salted hash. Signing in works with the username in any upper or lower case; a wrong username and a wrong password give the same message ("Wrong username or password"). Each user only sees their own statistics and highscores.

### MB R9 – Storage
Accounts and completed runs are stored in one shared online database, so that a user can sign in from any device and sees the same data everywhere. The connection details are secret: they are kept outside the code repository and never shown. Without connection details the app uses a local file instead, so it can be developed and tested offline. Automated tests never use the online database. Runs saved before accounts existed have no owner; they are kept but shown to nobody.

### MB R8 – Statistics and streak
- **Tasks completed** = the number of correctly solved tasks across all completed runs.
- **Activity** = one completed run. The 7-day chart covers today and the six days before it; days without activity show 0.
- **Streak** = consecutive calendar days with at least one completed run. Several runs on one day count as one day. The profile shows the longest streak.

---

## What the product must remember
Save each account (username, email address, password hash, creation date). Save each completed run: user (owner), test type, level, date and time, number of correct, wrong and skipped tasks. Highscores, totals, accuracy, streaks and the 7-day chart are calculated from the saved runs, so they always stay consistent with them after reopening the app. Tasks and their rules are generated, not stored.

---

## Acceptance criteria (R1)

### Scenario A1 – Generation rules
For every test type and level, 1,000 generated tasks all follow MB R1. Examples: every Pro division has a divisor of 101–291, a result of 11–28 and no remainder; every subtraction has a result of at least 1; no Medium multiplication contains a factor of 10.

### Scenario A2 – Variety
Two rounds of the same test type and level do not show the same sequence of tasks. Within a round, no task appears twice in a row.

### Scenario A3 – Answers and skip
For the task 7 × 8, the answer 56 adds one point and shows a new task. The answer 54 adds no point, counts as wrong, and shows a new task. Pressing Skip adds no point and counts as wrong. An empty entry changes nothing.

### Scenario A4 – Time limit
After the countdown, an answer submitted at 59.9 seconds counts; an answer submitted at 60.0 seconds or later does not, and the run ends.

### Scenario A5 – Saving a run
A completed Multiplication Easy run with 12 correct, 3 wrong and 2 skipped tasks is saved. After restarting the app, the profile shows 12 more tasks completed and an accuracy that includes 12 of 17. An aborted run leaves all statistics unchanged.

### Scenario A6 – Highscore
With a Multiplication Easy highscore of 15, a new run with 12 points leaves the highscore at 15; a run with 18 points sets it to 18 and is shown as a new highscore. A run of Multiplication Medium does not change the Easy highscore.

### Scenario A7 – Accounts
Creating the username "adrian" succeeds. A second account named "Adrian" is rejected. The email "adrian@" is rejected. An email already used by another account is rejected, also in other upper or lower case. A password of 7 characters is rejected; two different passwords are rejected. A short password typed twice the same way shows only the length error; a long password with a mismatch shows only the mismatch error. A rejected sign-up creates no account. "ADRIAN" can sign in as "adrian"; a wrong password and an unknown username give the same message.

### Scenario A8 – Streak
With completed runs on Monday, Tuesday (two runs) and Wednesday, none on Thursday, and one on Friday, the longest streak is 3 days.

### Scenario A9 – 7-day activity
With two completed runs today, one yesterday and none on the five days before, the chart shows 2 for today, 1 for yesterday and 0 for the other five days. Aborted runs do not appear.

### Scenario A10 – Online accounts
An account created on a phone through the public link can sign in on a laptop and sees the same highscores. After the online app is restarted, accounts and runs are still there. A run completed by user A does not appear in the highscores of user B. Runs without an owner appear for nobody.

---

## Later releases (overview)

### R2 – Trainer: operations and number types
**Operations:** Addition, Subtraction, Multiplication, Division, Percentage, Square, Square root. The user focuses on one operation, chooses one of four levels, and chooses one mode:
- a fixed number of tasks, 5–100 (time is measured but does not run out),
- a total time limit, 30 seconds to 15 minutes,
- a time limit per task, 1–60 seconds (the run ends when a task takes too long).

**Number types:** the user selects several operations within one number type and sets a separate level for each; tasks mix the selected operations.
- Natural numbers: Addition, Subtraction, Multiplication, Division, Percentage, Square, Square root
- Decimals: Addition, Subtraction, Multiplication, Division
- Large numbers: Addition, Subtraction, Multiplication, Division, Percentage
- Money: Addition, Subtraction, Division, Percentage
- Fractions: Addition, Subtraction, Multiplication, Division

Rules for percentages, square roots, decimals, money and fractions (accepted answer formats, rounding, simplified fractions) are defined in the R2 specification.

### R3 – Special trainings and Knowledge
**Special trainings:** Word problems, Mixed tasks (several operations in one task), Digit sums, Rule of three, Equations, Chain calculations, Fun with fractions (simplifying, GCD and LCM).

**Knowledge:** tips and tricks for the four basic operations, percentages and square numbers. Each trick has an explanation and practice tasks that use exactly this trick (for example: multiplying by 5 = multiplying by 10 and halving).

### R4 – Games
All games have the four levels and 3 lives. A wrong entry costs a life; losing all lives ends the game. Correct entries turn green and are locked; wrong entries flash red.
- **Mini Sudoku:** fill a 6×6 grid with 1–6 so that each digit appears once in every row, column and 2×3 box.
- **Sudoku:** fill a 9×9 grid with 1–9 so that each digit appears once in every row, column and 3×3 box. No time pressure.
- **Number Hunt:** combine the given numbers with +, −, ×, ÷ to reach the target number. Each step replaces two numbers with their result; the game is won when the last remaining number equals the target. Every result must be a whole number greater than zero; multiplying or dividing by 1 is not allowed. Undo and Reset each cost a life.
- **Magic Square:** fill the grid so that every row, column and both diagonals add up to the target sum. The keypad only offers the numbers needed for the puzzle.

---

## Scope boundaries
Passwords and a shared online database are in scope since version 1.1 (spec 011); the app runs on a free hosting service and a free online database. A leaderboard between users is planned (spec 013). Email verification, password reset, changing the username or password, deleting accounts, locking an account after failed sign-ins, payments, advertising, sound, offline mobile apps and any paid external service are not required.

Completed runs and accounts must survive restarting the app. Rejected actions (invalid sign-ups, answers after the time limit, aborted runs) leave saved data unchanged. The core experience works with generated content. The online app needs its database; locally the app and all tests also work without an internet connection.
