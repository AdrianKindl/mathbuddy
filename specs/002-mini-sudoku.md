# 002 – Games: play Mini Sudoku

## Why
The Games section is the last section that only shows "Coming soon". Mini
Sudoku is the smallest of the four games in R4, so it comes first. Its rules
(grid, lives, locked cells) are written so the 9×9 Sudoku can reuse them later.

## What
- The Games section shows Mini Sudoku. Sudoku, Number Hunt and Magic Square are
  listed as "Coming soon".
- The user chooses one of the four levels (Easy, Medium, Hard, Pro) and starts
  a new game.
- The game shows a 6×6 grid. Some cells are given, the others are empty. The
  user fills the empty cells with 1–6 so that each digit appears once in every
  row, every column and every 2×3 box.
- Every puzzle has exactly one solution, so every entry is either right or
  wrong. Puzzles are generated anew for every game; there are no fixed puzzle
  lists.
- The level sets how many cells are empty: Easy 12, Medium 16, Hard 20, Pro 24
  (out of 36). The brief gives no numbers; decided in this spec. All four
  are reachable with a unique solution.
- The user starts with 3 lives, shown on screen throughout the game.
- A correct entry turns green and is locked. A wrong entry flashes red, costs
  one life, and the cell stays empty.
- An empty entry, a non-numeric entry, or a number outside 1–6 is not
  evaluated and costs no life. The brief only says "wrong entry"; this spec
  treats these like the Tests section treats non-numeric input (MB R3).
- Entering into a given or already locked cell does nothing.
- With 0 lives the game is lost: "Game over" is shown together with the
  solution. When every cell is filled correctly the game is won: "You solved
  it!" is shown. After either, no more entries count, and the user can start a
  new game.
- The rules live in `sudoku.py` (no Streamlit, no SQL, randomness passed in as
  `random.Random`), the screen in `app.py`.

## Out of scope
Saving games, game statistics or highscores (the brief does not ask to remember
games). Sudoku 9×9, Number Hunt, Magic Square. A timer. Hints. Pencil marks.

## Done when
- **Generation:** for every level, 50 generated puzzles (fixed seeds) have a
  complete, valid solution; the given cells match the solution; the number of
  empty cells matches the level; each puzzle has exactly one solution.
- **Variety:** the same seed gives the same puzzle; different seeds give
  different puzzles.
- **Correct entry:** the cell is filled and locked; lives stay at 3.
- **Wrong entry:** the cell stays empty; lives go from 3 to 2.
- **Three wrong entries:** the game is lost; later entries are ignored.
- **Ignored entries:** "", "abc", "0", "7" and "2.5" change nothing and cost no
  life. Entries into given or locked cells change nothing.
- **Win:** filling all empty cells correctly wins the game, also after losing
  one or two lives; later entries are ignored.
- **Screen:** the Games section lists all four games, offers the four levels,
  shows one input per empty cell and the lives; a wrong entry lowers the lives
  on screen, three wrong entries show "Game over", solving shows
  "You solved it!".
- **Manual check in the PR:** green and red colouring, the grid lines between
  the 2×3 boxes, and how the grid looks on a phone.
