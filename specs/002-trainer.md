# 002 – Trainer: configurable practice that explains mistakes

## Why
A user should be able to practise exactly what they want (one operation, a
number type, or a special training), at their own level and in the mode they
choose, without the 60-second pressure of a test. After a mistake the Trainer
shows the correct answer and how to get there, so the user learns from it.

## What

### Choosing what to train
The Trainer screen offers three categories:

- **Operations:** one of Addition, Subtraction, Multiplication, Division,
  Percentage, Square, Square root, at one of the four levels.
- **Number types:** one of Natural numbers, Decimals, Large numbers, Money,
  Fractions. The user ticks one or more of its operations and sets a separate
  level for each. Tasks mix the ticked operations with equal probability.
  - Natural numbers: Addition, Subtraction, Multiplication, Division, Percentage, Square, Square root
  - Decimals: Addition, Subtraction, Multiplication, Division
  - Large numbers: Addition, Subtraction, Multiplication, Division, Percentage
  - Money: Addition, Subtraction, Division, Percentage
  - Fractions: Addition, Subtraction, Multiplication, Division
- **Special trainings:** one of Word problems, Mixed tasks, Digit sums, Rule of
  three, Equations, Chain calculations, Fun with fractions, at one of the four levels.

The setup screen shows an example task for the current selection and remembers
the selection for the rest of the browser session.

### Modes
- **Task count:** 5–100 tasks. The time is measured but does not run out. The
  session ends with the last answer or skip.
- **Total time:** 30–900 seconds. An answer or skip at or after the limit does
  not count, and the session ends.
- **Time per task:** 1–60 seconds. The clock restarts with every answer or
  skip. The session ends when one task takes as long as the limit or longer.

A 3-second countdown runs before the session and does not count towards any time.
Settings outside these ranges, or without any operation, are rejected with a
message and no session starts. The limits are enforced by the rules, not only
by the input fields.

### Answering (MB R2, MB R3)
- One task at a time. Correct: +1. Wrong: no point. Skip: counts as wrong for
  the accuracy and is recorded as skipped. In all three cases a new task appears.
- After a wrong answer or a skip, the correct answer and the way to it are
  shown next to the new task. After a correct answer the solution is confirmed.
- The same task never appears twice in a row.
- Input that is empty or not in the accepted format is not evaluated: nothing
  is counted, the task stays, the clock keeps running, and a hint shows the format.
- Accepted formats. All tasks have exact answers, so nothing is ever rounded.
  - Whole number: digits only, e.g. `4250`.
  - Decimal: digits with a point, e.g. `12.5`. `12.50` is the same answer.
  - Money: like a decimal with at most two decimals, with or without `€`.
  - Fraction: `3/4` in lowest terms, or a whole number. A fraction that is not
    simplified (`6/8`) is not evaluated, so the user can simplify it.

### Result and history
- At the end: correct, wrong, skipped, accuracy, time taken, average time per
  task, a review of every task (task, the user's answer, correct answer,
  result, seconds) and the solutions of all missed tasks. If the time ran out,
  the task that was not answered is shown with its solution.
- "Train again" starts a new session with the same settings.
- Only a finished session is saved (category, name, levels, mode, limit, end
  time, duration, correct, wrong, skipped), in its own table
  `trainer_sessions`. The setup screen lists the 10 newest sessions.
- A session the user ends early, or leaves by switching section, is not saved
  and shows no result (as MB R5). One whose time was already up counts as finished.

### Task rules
All bounds are inclusive. Natural numbers use MB R1 for the four basic operations.

**Natural numbers**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Percentage p % of n | p: 10, 25, 50; n: 20–200, step 20 | p: 5, 20, 40, 60, 75; n: 20–400, step 20 | p: 1–99; n: 100–2,000, step 100 | p: 101–250; n: 100–5,000, step 100 |
| Square a² / Square root √(r²) | a, r: 2–9 | 11–19 | 21–39 | 41–99 |

From Hard upwards, a and r are never a multiple of 10.

**Decimals** (one decimal unless stated)

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction | 0.1–9.9 | 10.0–99.9 | 1.00–99.99 (two decimals) | 100.00–999.99 (two decimals) |
| Multiplication a × b | a: 0.1–0.9; b: 2–9 | a: 1.1–9.9; b: 2–9 | a: 1.1–9.9; b: 0.2–0.9 | a, b: 1.1–9.9 |
| Division a ÷ b = q | b: 2–9; q: 0.1–0.9 | b: 2–9; q: 1.1–9.9 | b: 0.2–0.9; q: 2–19 | b: 0.2–0.9; q: 1.1–9.9 |

A factor or result of 1.1–9.9 is never a whole number.

**Large numbers**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction | 1,000–99,000, step 1,000 | 11,000–999,000, step 1,000 | 110,000–9,990,000, step 10,000 | 10,100,000–999,900,000, step 100,000 |
| Multiplication a × b | a: 2,000–9,000; b: 2–9 | a, b: 200–900, step 100 | a: 11,000–19,000; b: 200–900 | a: 11,000–99,000; b: 1,100–1,900 |
| Division | (a × b) ÷ b with the a and b of Multiplication | | | |
| Percentage p % of n | p: 10, 25, 50; n: 10,000–990,000, step 10,000 | p: 5, 20, 40, 60, 75; n as Easy | p: 1–99; n: 100,000–9,900,000, step 100,000 | p: 101–250; n: 1–99 million |

**Money**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction | €0.10–€9.90, step €0.10 | €1.00–€49.95, step €0.05 | €1.00–€99.99 | €100.00–€999.99 |
| Division: amount ÷ people = share | people: 2–5; share: €1.00–€9.50, step €0.50 | people: 2–9; share: €1.10–€19.90, step €0.10 | people: 2–9; share: €1.05–€49.95, step €0.05 | people: 11–19; share: €1.01–€29.99 |
| Percentage p % of n | p: 10, 25, 50; n: €20–€200, step €20 | p: 5, 20, 40, 60, 75; n: €2–€98, step €2 | p: 1–99; n: €1–€99 | p: 1–99; n: €100–€2,000, step €50 |

Every result is exact to the cent.

**Fractions** (always shown in lowest terms)

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Addition, Subtraction (fractions below 1) | same denominator, 2–12 | denominators d and 2d or 3d, d: 2–6 | two different denominators, 2–9 | two different denominators, 5–15 |
| Multiplication, Division | a fraction (denominator 2–9) and a whole number 2–9 | two fractions below 1, denominators 2–6 | two fractions below 1, denominators 5–12 | numerators and denominators 2–12, also above 1 |

**All number types:** in a subtraction the larger number comes first and the
result is above zero. In a division the divisor and the result are chosen
first, so the result is always exact. From Hard upwards a percentage p is
never a multiple of 10.

**Special trainings**

| | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| Word problems | one calculation in a short story, with the MB R1 numbers of the level; all four operations occur | | | |
| Mixed tasks | a + b × c, a × b ± c (2–9) | brackets and division, e.g. (a + b) × c | two products or two brackets (2–12) | larger numbers, e.g. (a + b) × (c − d) |
| Digit sums | 2 digits | 3 digits | 5 digits | 8 digits |
| Rule of three | value for one: 2–9; amounts 2–9 | asked amount 11–20 | value for one: 11–19; asked amount 11–29 | inverse: more workers need less time |
| Equations | x + a = b, x − a = b | ax = b, x ÷ a = b | ax + b = c, ax − b = c | x on both sides, or a(x + b) = c |
| Chain calculations | 3 steps, + − | 4 steps, + − × | 5 steps, + − × ÷ | 7 steps, + − × ÷ |
| Fun with fractions | simplify a fraction, GCD of two numbers, LCM of two numbers, mixed; larger numbers at higher levels | | | |

Every special training has a whole-number answer above zero, except
simplifying a fraction. In a chain every intermediate result is a whole number
from 1 to 9,999.

### Structure
- `trainer_tasks.py`: task generation and answer checking. No Streamlit, no SQL,
  randomness only from the `random.Random` passed in.
- `trainer.py`: settings, modes, time limits, result. No Streamlit, no SQL, the
  current time is passed in as `now`.
- `trainer_db.py`: storage of finished sessions, through `db.connect()`.
- `trainer_ui.py`: the screens. `app.py` only calls `trainer_ui.render()` and
  `trainer_ui.leave()`.

## Changes to 001
- The Trainer no longer shows "Coming soon" (MB01). Two tests in
  `tests/test_app.py` that used the Trainer as an unbuilt section now use Knowledge.

## Out of scope
Trainer sessions in the profile statistics, streak and 7-day chart (MB R8 counts
test runs). Accounts: sessions are saved without a user for now, like runs in
001. Knowledge and Games.

## Done when
- **Offer:** the three categories, seven operations, five number types with
  their operations, seven special trainings, four levels and three modes are
  selectable.
- **Generation:** for every operation of every number type and every special
  training, at every level, 1,000 generated tasks (fixed seed) follow the
  tables above; each answer, recalculated from the task text, is right; and the
  shown answer is accepted when typed.
- **Variety:** two rounds with different seeds differ; no task twice in a row,
  also when several operations are mixed.
- **Answers:** for 25 % of 80, answer 20 → correct; 25 → wrong; Skip →
  skipped; empty input → nothing changes. For 3/4, answer 6/8 is not evaluated.
- **Task count:** a session of 5 tasks ends with the 5th answer or skip, not before.
- **Total time:** with 30 s, an answer at 29.9 s counts; at 30.0 s it does not
  and the session ends.
- **Time per task:** with 10 s, an answer 9.9 s after the task appeared counts;
  at 10.0 s the session ends. Each answer restarts the 10 s.
- **Rejected settings:** 4 or 101 tasks, 29 or 901 s, 0 or 61 s per task, no
  operation ticked, and an operation the number type does not offer are all
  rejected, and no session starts.
- **Result:** 3 correct, 1 wrong, 1 skipped → accuracy 60.0 %; the review lists
  all 5 tasks and the solutions of the 2 missed ones.
- **Saving:** a finished session appears once in the history, also after
  stopping and restarting the app. A session ended early leaves the history unchanged.
