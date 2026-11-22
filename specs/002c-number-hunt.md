# 002c – Games: play Number Hunt

## Why
Number Hunt is the third game of R4. It trains choosing operations, not only
calculating.

Builds on spec 002b: merge `002-mini-sudoku` and `002b-sudoku` first.

## What
- Number Hunt can be chosen in the Games section. Magic Square stays
  "Coming soon".
- The game shows a target number and a few start numbers. The user combines two
  numbers with +, −, × or ÷: tap a number, an operation, then a second number.
  The two numbers are replaced with their result. The game is won when a single
  number is left and it equals the target: every start number is used once.
- Every result must be a whole number greater than zero, and multiplying or
  dividing by 1 is not allowed (MB R4 Games). A step that breaks these rules is
  a wrong entry: it flashes red, costs one life and changes nothing.
- Valid steps are listed in green and stay (they are locked).
- Undo takes back the last step, Reset goes back to the start numbers. Each
  costs one life (brief). Undo or Reset without any step does nothing and costs
  no life.
- If one number is left and it is not the target, the user is told to use Undo
  or Reset.
- 3 lives; with 0 lives the game is lost and one possible solution is shown.
- Every puzzle is generated anew and is always solvable: it is built by
  combining random start numbers with random valid steps, and those steps are
  kept as the solution.
- Levels (the brief gives no numbers; decided in this spec):

  | Level | Start numbers | Range | Target |
  |---|---|---|---|
  | Easy | 3 | 2–9 | 10–99 |
  | Medium | 4 | 2–12 | 20–199 |
  | Hard | 5 | 2–20 | 50–499 |
  | Pro | 6 | 2–25 | 100–999 |

  The target is never one of the start numbers.
- The rules live in `numberhunt.py` (no Streamlit, no SQL, randomness passed
  in), the screen in `app.py`.

## Out of scope
Saving games or statistics, hints, a timer, showing every possible solution.

## Done when
- **Generation:** for every level, 50 generated puzzles (fixed seeds) have the
  level's count and range of start numbers, a target in the level's range that
  is not a start number, and a stored solution that reaches the target with
  every number when played through the game rules.
- **Variety:** the same seed gives the same puzzle; different seeds give
  different puzzles.
- **Rules:** 7 − 9, 7 − 7, 7 ÷ 2, 7 × 1, 1 × 7 and 7 ÷ 1 are not allowed;
  7 + 1, 9 − 7, 8 ÷ 2 and 7 × 8 are.
- **Steps:** a valid step replaces the two numbers with the result and is
  recorded; an invalid one costs a life and changes nothing else; three invalid
  steps lose the game.
- **Undo and Reset:** each restores the numbers and costs a life; without steps
  they are ignored; the third life lost this way loses the game.
- **Win:** the last number equal to the target wins; a single number that is
  not the target does not, and counts as stuck.
- **Screen:** the user can choose Number Hunt, sees the target, the numbers and
  3 lives; tapping a valid step shows it; an invalid step lowers the lives;
  Undo costs a life; playing the solution shows "You found it!"; three invalid
  steps show "Game over".
- **Manual check in the PR:** red flash, green steps, layout on a phone.
