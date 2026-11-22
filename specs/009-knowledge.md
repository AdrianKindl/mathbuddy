# 009 – Knowledge: learn mental-math tricks and practise them

Source: `docs/knowledge-brief.md` (Knowledge feature brief, version 0.1), rules
K R1–K R7 and scenarios KA1–KA9. This spec builds the **Tricks** mode only.

## Why
A user who wants to get faster should not only be tested, but also learn how.
The Knowledge tab explains well-known mental-math tricks step by step, then lets
the user practise exactly that trick with tasks where the trick always works.
A ✓ shows which tricks the user has already practised.

## What

### Screens
- **Mode toggle** at the top: Tricks | Textbook. Tricks is selected at first.
  Textbook shows "Coming soon".
- **Overview:** one tile (button) per category with its trick count:
  Addition (5), Subtraction (8), Multiplication (8), Division (4),
  Square numbers (5) (KA1).
- **Category screen:** Back button, the category name, a subtitle
  ("Addition tricks"), and one row per trick in catalogue order: name,
  difficulty label and a ✓ once the trick has been practised (K R7, KA2).
  Clicking a row opens the trick.
- **Trick screen:** Back button and title; the description; one example card
  per variant (range label, operation and difficulty tags, worked equation);
  the note, if any; numbered steps, each with a short text and a calculation;
  previous / next within the category with a position indicator ("2 / 5"),
  disabled on the first / last trick (K R3, KA4); and a Practice button.
  A trick with variants shows the steps of each variant under its example.
- **Practice:** level buttons Easy, Medium, Hard, Pro (the same control as
  Tests and Trainer), then Start. 10 tasks, one at a time, no time limit, with
  "Task 4 / 10", the answer field with Submit and Skip, and the same green / red
  flash and cursor focus as Tests. After a wrong answer or skip the correct
  answer is shown with the next task. An empty or non-numeric entry shows the
  hint "Numbers only, e.g. 4250" and changes nothing. "Back to trick" leaves
  the round early.
- **Result:** correct answers out of 10 ("7 / 10"), and the buttons
  **Practise again** (same trick and level) and **Back to trick**.

### Rules (from the brief)
- **K R1 – Content is fixed:** categories, tricks, examples, steps and practice
  ranges are data in `knowledge_content.py`. Nothing of it is stored.
- **K R2 – Examples are correct:** every example equation and every step
  calculation is arithmetically correct, and the steps of each example end
  with that example's result (checked by tests, KA5).
- **K R3 – Navigation:** previous / next stays within the category.
- **K R4 – Practice tasks:** a round has exactly 10 tasks for one trick and one
  level, each inside that trick's range for that level ("Practice levels"
  table, with the decisions below). Tasks are generated anew for every round;
  the same task never appears twice in a row. No time limit.
- **K R5 – Answers:** whole numbers, evaluated as in Tests (MB R3), using
  `tasks.parse_answer`: correct +1; wrong and skipped add nothing; empty or
  non-numeric input is not evaluated.
- **K R6 – Completed rounds:** a round is completed after its 10th answer or
  skip. Only completed rounds are saved; leaving early (Back to trick, or
  another tab) saves nothing.
- **K R7 – Practised:** a trick shows a ✓ when at least one round of it was
  completed, at any level and score. Calculated from the saved rounds.

### Calculation format (for K R2)
Each step calculation is one or more parts separated by "; ". A part is one of:
- an equation or comparison, e.g. `56 + 30 = 86`, `20 < 30`, `19² = 361`;
- a split, `38 → 30 & 8` (the parts add up to the number);
- a place-value combination, `3 | 14 | 20 | 8 → 4,608` (the parts, each times
  its place value, add up to the result; parts may be sums such as `2+4`).

### Storage
Each completed round is saved in a new table `practice_rounds` (id, trick_id,
level, finished_at, correct) in the same database file, through
`db.connect()`. The `runs` table and the Tests and Trainer storage are unchanged.

### Structure
- `knowledge_content.py`: the catalogue as data (texts, examples, steps,
  practice ranges). No Streamlit, no SQL.
- `knowledge.py`: rules: task generation (randomness from the
  `random.Random` passed in), the round, scoring, navigation, the ✓.
  No Streamlit, no SQL, no clock.
- `knowledge_db.py`: storage of completed rounds through `db.connect()`.
- `knowledge_ui.py`: the screens. `app.py` only calls `knowledge_ui.render()`
  and `knowledge_ui.leave()`.
- The answer field, Submit / Skip, the flash and the focus script move into
  `ui_components.py` and are used by Tests, Trainer and Knowledge. Tests and
  Trainer look and behave exactly as before.

### Decisions on unclear points in the brief (confirmed)
1. **Q1 practice range:** the brief's method (add the ones digit, times 10,
   add the ones digit squared) only works for 11–19; for 21–25 it gives a
   wrong result (23²: 26 × 10 + 9 = 269, not 529). Q1 therefore practises
   Easy 11–13, Medium 14–16, Hard 17–19, Pro 11–19, and its example card and
   note say it works for 11 to 19. The trick keeps its name from the brief.
2. **Square ranges and multiples of 10:** "Square tasks exclude multiples of 10"
   is applied to every square trick, so Q3 excludes 80, 90, 110 and 120 as
   well as 100.
3. **Q4 ranges** mean the numbers ending in 5 inside the range (Easy: 15, 25,
   35, 45).
4. **D3 Easy** also requires a whole result (70 ÷ 20 would be 3.5). In D3, a
   and b are 1–9 except at Pro, where they are 10–99.
5. **D4:** Easy "both even, divisor 4–9" means a divisor of 4, 6 or 8.
   Medium "common factor 2–5" excludes the divisors 11, 13, 17 and 19. Hard and
   Pro need a divisor with a factor from 2 to 9.
6. **No result of 1 or less in subtraction:** S4 and S5 can never use 99 (or
   999) as the subtrahend, because no number of the same size is larger; those
   values are left out.
7. **"Within 25 below a hundred"** (A4) means 1 to 25 below a multiple of 100,
   so the last two digits are 75–99 (Hard: 50–99; Pro: last three digits 950–999).
8. **A3 complement:** "its complement to 100 + 1–9" means the second number is
   (100 − first) plus 1 to 9.
9. **Crossing** (S8) means the larger number is in a higher ten (hundred,
   thousand) than the smaller one.
10. **Borrowing places** (S2, S6) compare the digits place by place: a place
    borrows when the larger number's digit is smaller than the other's.
11. **Steps for tricks the brief gives only as a chain** (for example
    "7 × 8: 14 → 28 → 56") are written as numbered steps with equations
    ("Double: 7 × 2 = 14", …). Their texts need a content review.
12. **Example labels** for tricks without variants are not given in the brief;
    a short label is written for each (for example "Two-digit numbers").
13. **Saving** follows the Trainer's pattern: a `knowledge_db.py` module using
    `db.connect()`, so `db.py` itself and its tests stay unchanged.

## Changes to earlier specs
Knowledge no longer shows "Coming soon" (MB01). In `tests/test_app.py`, two
tests that used Knowledge as an unbuilt section now use Profile.

## Out of scope
Textbook mode, recommendations, a random trick, favourites, feedback buttons,
worked solutions for practice tasks (only the correct answer is shown),
practice results in the Profile statistics, accounts (rounds are saved without
a user, like runs). Any change to Tests, Trainer, Games, `tasks.py`, `runs.py`,
`db.py` or the `runs` table.

## Done when
- **KA1:** the overview shows the five categories with 5, 8, 8, 4, 5 tricks.
- **KA2:** Addition lists its five tricks in order with their labels, no ✓.
- **KA3:** "Split one number" shows 56 + 38 = 94 and the three steps
  38 → 30 & 8; 56 + 30 = 86; 86 + 8 = 94.
- **KA4:** previous is disabled on a category's first trick, next on its last.
- **KA5:** every example and step calculation of every trick is correct, and
  each example's steps end with its result.
- **KA6:** for every trick and level, 1,000 tasks (fixed seed) are in the
  trick's range and have whole-number answers of at least 1.
- **KA7:** a round has exactly 10 tasks; 7 correct, 2 wrong, 1 skipped shows 7 / 10.
- **KA8:** after one completed round of Times 11 it shows a ✓ in
  Multiplication, also after a restart; other tricks have none.
- **KA9:** leaving a round after 5 tasks saves nothing and shows no ✓.
- **Unchanged:** all existing tests pass; only the two Knowledge-as-unbuilt
  tests in `tests/test_app.py` change, as described above.
