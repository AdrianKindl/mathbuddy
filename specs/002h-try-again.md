# 002h – Games: try again after Game over

## Why
After losing, players want another go at the same puzzle instead of a new one.

Builds on spec 002g: merge #4–#7 and #11 first.

## What
- After "Game over", every game shows a "Try again" button.
- Mini Sudoku, Sudoku, Number Hunt and Magic Square: the same puzzle starts
  again from the beginning, with 3 lives (and, for the Sudokus, a fresh stopwatch).
- Number Chain has no fixed puzzle: a new game starts at the same level, score 0.
- Running or solved games show no "Try again". "New game" still starts a new puzzle.
- Only `app.py` changes; the rule modules are not touched. Nothing is saved.

## Done when
- For each game, after Game over, "Try again" restores the same puzzle
  (Number Chain: same level, score 0) with 3 lives.
- Running and solved games show no "Try again".
- All other tests pass unchanged.