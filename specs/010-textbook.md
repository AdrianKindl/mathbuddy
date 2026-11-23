# 010 – Textbook: background articles in the Knowledge tab

Source: `docs/textbook-brief.md` (Textbook mode feature brief, version 0.1),
rules T R1–T R10 and scenarios TA1–TA12. Builds on spec 009 (Knowledge, Tricks mode).

This feature is built in **two stages**:
- **Stage 1 – content (this branch, now):** the Tricks / Textbook toggle, the
  Textbook overview, category screens and article screens (T R1–T R5, TA1–TA7).
- **Stage 2 – practice (later):** practice rounds for articles, answer types,
  saving and the ✓ (T R6–T R10, TA8–TA12).

## Why
Tricks teach single techniques. Many users also need the background: why the
order of operations is what it is, how fractions, decimals and percentages
relate, how to estimate, and the calculations that come up in case interviews.
Short articles with worked examples and reference tables give that background,
and link to the matching tricks.

## What

### Stage 1 – Screens
- **Toggle:** the existing Tricks | Textbook control at the top of the
  Knowledge tab. Textbook no longer shows "Coming soon".
- **Textbook overview:** one tile per category with its article count:
  Basics (3), Fractions (3), Case interview (7), Estimating & rounding (4) (TA1).
- **Category screen:** Back, the category name, and one row per article in
  catalogue order with its difficulty label (Medium or Hard) (TA2). Same
  design as the Tricks category screen. No ✓ yet (stage 2).
- **Article screen**, from top to bottom (TA3, TA4):
  1. Back and the article title.
  2. "Overview" and the one-line summary.
  3. Main card: card title, tags (category and difficulty), body text. A body
     with several items is shown as a list.
  4. The note, if any.
  5. Examples: one card per example with a title and its lines.
  6. The reference table, if any: title, subtitle, table.
  7. Related tricks, if any: one button per trick. It switches to Tricks mode
     and opens that trick (TA6). Back on that trick goes to its Tricks category.
  8. Previous / next within the category with "2 / 7", disabled on the first /
     last article (T R3, TA5), and a **Practice** button that is shown but
     disabled until stage 2.

### Stage 1 – Rules
- **T R1 – Content is fixed:** categories, articles, examples, tables and
  related tricks are data in `textbook_content.py`, with the exact English
  texts of the brief. Nothing of it is stored.
- **T R2 – Content is correct:** every article lists the calculations behind
  its numbers as machine-checkable `checks` (format below); tests verify each
  one and that its numbers appear in the article. Reference tables are checked
  row by row (F1 conversions, B2 sign rules, C3 margin → markup, C7 units).
- **T R3 – Navigation:** previous / next stays within the category.
- **T R4 – Related tricks:** every link names an existing trick id from spec 009.
- **T R5 – Tricks unchanged:** switching modes changes nothing in Tricks mode:
  not its screen, not its ✓ markers (TA7). Tricks practice rounds are untouched.

### Stage 1 – Check format
Like spec 009, extended: numbers may have thousands commas and decimals; a
number followed by `%` means hundredths; operators `+ − × ÷ /`, brackets,
`²` and `√(…)`; relations `=`, `<`, `>` and `≈`. `≈` accepts a difference of
at most half a unit in the last shown digit of the right side
(e.g. `40 / 60 ≈ 66.7 %`, `√(0.5) ≈ 0.707`).

### Stage 1 – Structure
- `textbook_content.py`: the catalogue as data. No Streamlit, no SQL.
- `textbook.py`: rules (stage 1: navigation; stage 2: practice). No Streamlit,
  no SQL, no clock, randomness only from the `random.Random` passed in.
- `textbook_ui.py`: the Textbook screens, called from `knowledge_ui.py` when
  the toggle is on Textbook. Session keys start with `tb_`.
- The pieces both modes share (category tiles, list rows, previous / next bar,
  Back) move into `ui_components.py` and are used by Tricks and Textbook.
  Tricks looks and behaves exactly as before.
- Text with `$` (e.g. "4 $") is escaped when shown, so Streamlit does not read
  it as maths; the data keeps the brief's text.

### Stage 2 – Practice (not built now)
- Practice screen as in Tricks: level, 10 tasks, no time limit, Submit and
  Skip, green / red feedback, the correct answer after a wrong answer or skip,
  "Task 4 / 10", result "x / 10", **Practise again**, **Back to article**.
- **T R6–T R8:** tasks from each article's template and ranges ("Practice
  catalogue"), never the same task twice in a row; answer types whole number,
  decimal (with stated precision, "." or ",", optional "%"), choice (2–4
  buttons) and estimate (±10 %); input of the wrong type shows a hint.
- **T R9–T R10:** only completed rounds are saved, in a new table (article id,
  level, date and time, correct); the ✓ next to practised articles is
  calculated from them. Tricks rounds stay in their own table.
- Its open questions are listed below and must be settled in the stage 2 spec update.

## Decisions on unclear points (stage 1, to confirm)
1. **Brief file name:** the brief was supplied with a space and "new" in
   its file name and has since been renamed to `docs/textbook-brief.md`
   (spec 019).
2. **F1 has no example card**, only the table. Examples are optional for it.
3. **Table subtitles** are not given for F1 and C3. Written: F1 "Fraction ·
   Decimal · Percent", C3 "Margin and the matching markup". B2 uses "Signs of
   products and quotients", C7 "Row × column", from the brief's brackets.
4. **Rounded table values:** C3's "33.3 % → 50 %" is exact only for 1/3
   (33.3 % gives 49.9 %). Rounded table values are checked to within 0.1
   percentage points.
5. **Related-trick button label:** "Compatible numbers (Addition)", as in the
   brief. After following it, Back goes to the Tricks category, not to the article.
6. **Practice button in stage 1:** shown, disabled.
7. **Body lists:** B2 and B3 bodies are lists of items as in the brief; the
   other bodies are one paragraph.

## Stage 2 – Structure
- `textbook.py` gets the practice rules: `TextbookTask` (article, template,
  values, prompt, answer type, exact answer, decimals, percent, choices),
  `generate_task`, `evaluate`, `answer_text`, the round (`start_round`,
  `current_task`, `submit_answer`, `skip_task`) and `practised`. A task's
  `template` is the calculation over its `values`, so tests can recompute
  every answer independently.
- `textbook_db.py`: completed rounds in a new table `textbook_rounds`
  (id, article_id, level, finished_at, correct), through `db.connect()`.
- `textbook_ui.py`: the practice screens, built from the Tricks practice
  components (level buttons, answer form, flash, focus). Choice tasks show one
  button per option; choosing one submits it. Tricks practice is unchanged.

## Stage 2 – Decisions on unclear points in the brief (to confirm)
**Answers (T R7, T R8)**
1. **Rounding** is half away from zero: 10.25 % with 1 decimal place is 10.3 %.
2. **Decimal answers** are compared by value with the rounded result: "66.70"
   is right, "66.67" is wrong (not ignored). "8" is accepted for 8.0.
3. **Comma:** in a decimal answer "," is always the decimal separator, so
   "1,250" means 1.25. In a whole-number or estimate answer a comma is not
   accepted, and the input is not evaluated.
4. **Minus sign:** "-" and "−" are both accepted. "%" is accepted after any
   decimal answer and ignored.
5. **Estimates** are whole numbers; the ±10 % limits are included. After a
   wrong estimate the exact result and the accepted whole numbers are shown,
   e.g. "88.45 (accepted: 80 to 97)".
6. **TA9** says 7,341 ÷ 83 is "88.45…"; it is 88.4458…. Shown rounded to two
   decimals it is 88.45; the accepted range 80–97 is right either way.

**Practice catalogue: ranges that do not work as written, and the fix used**
7. **B3 Medium ÷ 100:** a two-decimal number divided by 100 has four decimals,
   which a two-decimal answer cannot express. ÷ 10 uses numbers with one
   decimal (0.1–99.9), ÷ 100 uses whole numbers (1–999). "Two decimal places"
   numbers are 0.01–9.99.
8. **F1 Pro:** the rounded table percentages (33.3 %, 66.7 %, 16.7 %, 83.3 %,
   8.3 %) never give a whole result (33.3 % of 300 = 99.9). Only the exact
   ones are used: 10, 12.5, 20, 25, 37.5, 40, 50, 60, 62.5, 75, 80, 87.5 %.
9. **C3 Medium:** margin 33.3 % → markup gives 49.9 %, not the table's 50 %.
   That direction is left out; markup 33.3 % → margin (25.0 %) is kept.
10. **C6 Pro:** a price cut can make the price equal to or lower than the
    variable cost, so there is no break-even. The new price must be whole and
    above the variable cost.
11. **E1 Medium:** the difference of two 4-digit numbers can be tiny or 0
    (±10 % of 14 is 13–15; of 0 only 0). The larger number comes first and the
    difference is at least 1,000.
12. **F3 Easy and Medium:** every x is between 0 and 1, so the right answer is
    always "x" (Easy) or always "√x" (Medium). Built as written; worth a
    content decision.
13. **C7:** M × B, B × M and B × B have no unit and are never used. Results keep
    the coefficient and take the unit from the table ("1,500 M", "98,901 T"),
    and the four options are that coefficient with K, M, B and T, so exactly
    one is right.

**Ranges the brief leaves open, and the values used**
14. B2 Hard: a × b with |a|, |b| 2–20, or a ÷ b with |b| and |a ÷ b| 2–20,
    any signs. B3 Easy and Pro: results are at least 0.
15. F1 Easy uses fractions in lowest terms with denominator 2, 4, 5 or 10;
    Hard thirds, sixths and twelfths in lowest terms. F2: all fractions are
    proper; in Hard and Pro about one task in five is "Equal", shown as two
    different fractions. F3 Hard and Pro: x is 0.04, 0.09, …, 0.81, 1.21, 1.44,
    2.25 or 4.
16. C2 Hard: 1–3 doubling periods with an Easy rate, start 5–50 bn. C3 Easy:
    the asked margin or markup is a whole percent. C4 Easy and Medium: the new
    value is whole and the change a whole percent. C5 Easy values 10–90 in
    tens; Pro sizes 100–900 in hundreds. C6 Medium and Hard: price up to 200,
    fixed costs in thousands.
17. E2 Easy divides by 2–9. E2 Medium: the divisor is at most 3 from a
    multiple of 10, and the dividend within 5 % of a multiple of that round
    number. E2 Pro "near 50 or 100": both factors 45–55, or both 95–99.
    E3 Easy multiplies by 2–9; Pro "three factors" are 2-digit. E4 Hard and
    Pro: about half the tasks are correct; wrong results differ by 1–99, never
    a multiple of 9.
18. **Names:** the catalogue names are used on screen ("The rule of 72").

**Screens**
19. Practice keys and texts follow Tricks: level buttons, Start, "Task 4 / 10",
    Submit and Skip, "Back to article" to leave early, result "x / 10" with
    **Practise again** and **Back to article**. Input of the wrong type shows a
    hint naming the expected format.

## Changes to earlier specs
Textbook no longer shows "Coming soon" (spec 009). In `tests/test_knowledge_ui.py`
the test `test_textbook_mode_is_coming_soon` becomes a check that Textbook shows
its overview.

## Out of scope
Stage 1: everything in stage 2. Both stages: favourites, feedback buttons, a
"For you" section, worked solutions per practice task, articles not in the
brief, practice results in Profile statistics, accounts. Any change to Tricks,
Tests, Trainer, Games, `tasks.py`, `runs.py`, `db.py` or existing tables.

## Done when (stage 1)
- **TA1:** the overview shows four categories with 3, 3, 7 and 4 articles.
- **TA2:** Case interview lists its seven articles in order with their labels.
- **TA3:** "Order of operations" shows the overview, the main card, the note
  and the example "Calculate 3 + 4 × 2" with result 11.
- **TA4:** "Fractions, decimals and percentages" shows the table with all 17
  rows from 1/2 to 1/12.
- **TA5:** previous is disabled on a category's first article, next on its last.
- **TA6:** the related trick in "Compatible numbers" opens the trick
  "Compatible numbers" in Addition.
- **TA7:** switching to Textbook and back keeps the Tricks screen and all ✓ markers.
- **Content:** article names, labels, overviews, card titles, example titles,
  notes, tables and related tricks match the brief; B1 and F1 match word for
  word; every check and every table row is correct.
- **Unchanged:** all other existing tests pass.

## Done when (stage 2)
- **TA8:** for every article and level, 1,000 tasks (fixed seed) follow the
  template and ranges above; whole-number answers are whole, decimal answers
  state their precision, estimates start with "Estimate", choices have 2–4
  different options with exactly one correct.
- **TA9:** decimal 66.666… with 1 decimal place: "66.7", "66,7", "66.7%" right,
  "66.6" wrong, "abc" not evaluated. Estimate of 7,341 ÷ 83: 80 and 97 right,
  79 and 98 wrong. Whole number: "-12" is −12.
- **TA10:** a round has 10 tasks; 6 correct, 3 wrong, 1 skipped shows 6 / 10.
- **TA11:** after one completed round of "The rule of 72" it shows a ✓ in Case
  interview, also after a restart; no other article has one; Tricks ✓ markers
  are unchanged.
- **TA12:** leaving a round after 5 tasks saves nothing.
- **Unchanged:** Tricks practice and all other existing tests; in
  `tests/test_textbook_ui.py` only the stage 1 Practice-button test changes
  (the button is now enabled).
