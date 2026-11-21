# 002g – Games: end a game early

## Why
The Trainer has an "End training" button. The games had no way to stop a game
except starting a new one or switching sections. Number Chain has no natural
end at all while the player keeps answering correctly.

Builds on spec 002f: merge `002c-number-hunt` … `002f-sudoku-timer` first.

## What
- While a game is running, every game (Mini Sudoku, Sudoku, Number Hunt, Magic
  Square, Number Chain) shows an "End game" button below the game, like
  "End training" in the Trainer.
- "End game" ends the game at once and goes back to the level choice and
  "New game". Nothing is saved (games are never saved), and no message or
  solution is shown, as in the Trainer.
- After a game is won or lost, there is no "End game" button: the game is
  already over and "New game" starts the next one.
- Only `app.py` changes. The rule modules are not touched.

## Out of scope
Asking "Are you sure?", showing the solution after ending, saving anything.

## Done when
- **Every game:** for each of the five games, a running game shows "End game";
  clicking it removes the game and its board, and "New game" is still there.
- **Finished games:** after "Game over" or a solved puzzle, no "End game" is
  shown.
- **Start again:** after ending a game, "New game" starts a fresh one.
- **No other change:** all other tests still pass unchanged.
