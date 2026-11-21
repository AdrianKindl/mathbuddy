# 010 – Textbook: background articles in the Knowledge tab

Source: `docs/textbook-brief new.md` (Textbook mode feature brief, version 0.1),
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
1. **Brief file name:** the brief is `docs/textbook-brief new.md` (with a
   space and "new"). It is referred to as `docs/textbook-brief.md`; renaming
   it before committing is suggested.
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

## Open questions for stage 2 (from the brief)
- TA9 says 7,341 ÷ 83 is "88.45…"; it is 88.4458…, so "88.44…" (the
  accepted range 80–97 is right either way).
- A decimal separator "," clashes with "no thousands separators": "1,250" would
  be read as 1.25.
- Rounding: half up or half to even (12.25 → 12.3 or 12.2)? More decimals than
  asked ("66.67" for 1 decimal place): wrong, or not evaluated?
- Estimate range ±10 %: are the limits included?
- C3 Medium "33.3 ↔ 50": is the answer for margin 33.3 % 50 % or 49.9 %?
- F3 Hard "x from {0.04 … 0.81}": which values exactly?
- Article names differ between the catalogue, the practice table and the
  scenarios ("The rule of 72" vs "Rule of 72", "Rules for negative numbers"
  vs "Negative numbers"). The catalogue names are used on screen.

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
TA8–TA12, to be detailed when stage 2 starts.
