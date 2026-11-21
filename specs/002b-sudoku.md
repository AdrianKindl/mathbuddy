# 002b – Games: play Sudoku (9×9)

## Why
Sudoku is the second game of R4. It follows the same rules as Mini Sudoku
(spec 002) on a bigger grid, so it reuses `sudoku.py`.

Builds on spec 002: merge `002-mini-sudoku` first.

## What
- The Games section lets the user choose between Mini Sudoku and Sudoku.
  Number Hunt and Magic Square stay "Coming soon". Choosing another game ends
  the current game; nothing is saved.
- Sudoku shows a 9×9 grid. The user fills the empty cells with 1–9 so that each
  digit appears once in every row, every column and every 3×3 box. No time
  pressure (no timer).
- Every puzzle has exactly one solution and is generated anew for every game.
- The level sets how many of the 81 cells are empty: Easy 36, Medium 42,
  Hard 48, Pro 52. The brief gives no numbers; decided in this spec. All four
  are reachable with a unique solution (greedy removal reaches at least 54).
- Everything else works exactly as in Mini Sudoku: 3 lives, a correct entry
  turns green and is locked, a wrong entry flashes red and costs one life,
  empty or invalid entries (anything but 1–9) are ignored, "Game over" with the
  solution, "You solved it!".
- `sudoku.py` keeps its Mini Sudoku defaults, so spec 002 and its tests are
  unchanged. The variant (6×6 or 9×9) is found from the size of the grid.

## Out of scope
Saving games or statistics, hints, pencil marks, a timer.

## Done when
- **Generation:** for every level, 10 generated 9×9 puzzles (fixed seeds) have
  a complete, valid solution, givens that match it, the level's number of empty
  cells and exactly one solution.
- **Rules:** a known valid 9×9 grid is solved; a grid with a duplicate in a 3×3
  box is not; grids of other sizes are rejected.
- **Entries:** 7, 8 and 9 are valid entries; 0 and 10 are ignored; correct and
  wrong entries behave as in Mini Sudoku; a full 9×9 game can be won.
- **Screen:** the user can choose Sudoku, start a game at every level and sees
  one input per empty cell and 3 lives; a correct 9 locks its cell; three wrong
  entries show "Game over"; changing the game ends the current one.
- **Spec 002 unchanged:** all Mini Sudoku tests still pass without changes.
- **Manual check in the PR:** the grid lines between the 3×3 boxes and how the
  9×9 grid fits on a phone.
