# 002d – Games: play Magic Square

## Why
Magic Square is the last game of R4. With it, all four games are playable and
the Games section no longer shows "Coming soon".

Builds on spec 002c: merge `002-mini-sudoku`, `002b-sudoku` and
`002c-number-hunt` first.

## What
- Magic Square can be chosen in the Games section. All four games are now
  built, so the Games section no longer shows "Coming soon" (MB01: only sections
  that are not built show it).
- The game shows a square grid, some numbers given, and the target sum. The
  user fills the empty cells so that every row, every column and both diagonals
  add up to the target sum. The grid holds consecutive whole numbers, each once.
- The user taps an empty cell, then a number on the keypad. The keypad only
  offers the numbers still needed for the puzzle (brief); a number disappears
  from it once placed correctly.
- Every puzzle has exactly one solution with the keypad's numbers, so every
  entry is either right or wrong. Puzzles are generated anew for every game.
- 3 lives. A correct entry turns green and is locked. A wrong entry flashes
  red, costs one life, and the cell stays empty. With 0 lives the game is lost
  and the solution is shown; filling every cell correctly wins.
- Levels (the brief gives no numbers; decided in this spec):

  | Level | Grid | Empty cells | Numbers |
  |---|---|---|---|
  | Easy | 3×3 | 4 | 1–9 |
  | Medium | 3×3 | 6 | 9 in a row, starting at 2–20 |
  | Hard | 4×4 | 7 | 1–16 |
  | Pro | 4×4 | 10 | 16 in a row, starting at 2–30 |

- Puzzles come from the 3×3 Lo Shu square and twelve 4×4 magic squares, each
  changed at random by rotating, mirroring, reordering rows and columns in a
  way that keeps the diagonals, replacing every x by (largest + 1 − x), and
  shifting all numbers. All of these keep the square magic.
- The rules live in `magicsquare.py` (no Streamlit, no SQL, randomness passed
  in), the screen in `app.py`.

## Open decision: two reviewed tests
Two reviewed tests check that Games shows "Coming soon":
`test_other_sections_show_coming_soon[Games]` (spec 001) and the last line of
`test_games_section_lists_all_four_games` (spec 002). That was true while games
were missing. With all four built, MB01 ("Sections not yet built show
'Coming soon'") requires the opposite, so both now fail.

Following AGENTS.md, they are **not** changed here. The team decides. Proposal:
drop "Games" from the first test's list, add a test that Games does not show
"Coming soon", and drop the "Coming soon" line from the second test. Until
then these two tests fail on this branch; all other tests pass.

## Out of scope
Saving games or statistics, hints, a timer, squares larger than 4×4.

## Done when
- **Base squares:** Lo Shu and all twelve 4×4 base squares are magic.
- **Generation:** for every level, 50 generated puzzles (fixed seeds) have the
  level's size and number of empty cells, a magic solution of consecutive
  numbers in the level's range, the right target sum, givens that match the
  solution, and exactly one way to place the keypad's numbers.
- **Variety:** the same seed gives the same puzzle; different seeds give
  different puzzles.
- **Keypad:** it offers exactly the missing numbers, smallest first; a correct
  entry removes its number; a number not on the keypad is ignored.
- **Entries:** correct entries lock; wrong ones cost a life and leave the cell
  empty; given or locked cells ignore entries; three wrong entries lose; the
  last correct entry wins; entries after the end are ignored.
- **Screen:** the user can choose Magic Square, sees the target sum, one button
  per empty cell, the keypad and 3 lives; tapping a cell and the right number
  locks it; a wrong number lowers the lives; three wrong numbers show
  "Game over"; solving shows "You solved it!"; Games shows no "Coming soon".
- **Manual check in the PR:** selected cell, green and red, layout on a phone.
