# 002e – Games: play Number Chain

## Why
The four games of R4 are puzzles. Number Chain adds a fast game that trains
pure mental arithmetic: keeping a running result in your head.

**This game is not in the product brief.** It extends R4 with a fifth game and
needs the team's agreement before it is merged.

Builds on spec 002d: merge `002-mini-sudoku`, `002b-sudoku`,
`002c-number-hunt` and `002d-magic-square` first.

## What
- Number Chain can be chosen in the Games section.
- A chain is a start number followed by steps such as "+ 8", "× 3" or "÷ 6".
  The start number and then each step are shown one after the other, each for a
  few seconds; earlier steps disappear. Then the user types the result.
- A correct result adds one point, and the next chain is one step longer (at
  most 10 steps longer than the first). A wrong result costs one of 3 lives,
  shows the right result, and the next chain keeps its length. With 0 lives the
  game is over and the score is shown.
- Empty or non-numeric answers are not evaluated (like MB R3).
- Every result along the way is a whole number from 1 to the level's largest
  number; ÷ only appears when it divides exactly; × and ÷ never use 1.
- No step repeats the step before it or takes it back ("+ 8" is never followed
  by "+ 8" or "− 8"; "× 3" never by "÷ 3").
- Levels (decided in this spec):

  | Level | First chain | Operations | Start | + and − | × and ÷ | Largest | Seconds per step |
  |---|---|---|---|---|---|---|---|
  | Easy | 4 steps | + − | 2–10 | 2–9 | – | 50 | 3.0 |
  | Medium | 5 steps | + − × | 2–20 | 2–15 | 2–5 | 150 | 2.5 |
  | Hard | 6 steps | + − × ÷ | 2–30 | 3–25 | 2–9 | 400 | 2.0 |
  | Pro | 8 steps | + − × ÷ | 5–50 | 5–49 | 2–12 | 999 | 1.5 |

- The rules live in `numberchain.py` (no Streamlit, no SQL, randomness passed
  in), the screen in `app.py`.

## Out of scope
Saving games, scores or highscores. Pausing a chain or showing it again.

## Done when
- **Generation:** for every level and every chain length the game can reach,
  generated chains (fixed seeds) have the right length, start in range, only
  use the level's operations and numbers, stay whole and within 1 to the
  largest number at every step, and never repeat or undo the step before.
- **Variety:** the same seed gives the same chain; different seeds give
  different chains.
- **Answers:** the right result adds a point and makes the next chain one step
  longer; a wrong one costs a life and keeps the length; empty or non-numeric
  answers change nothing; the third wrong answer ends the game; answers after
  the end are ignored; the chain stops growing after 10 extra steps.
- **Screen:** the user can choose Number Chain, start a chain, sees the steps
  and then an answer field with lives and score; a right answer raises the
  score; three wrong answers show "Game over" with the score.
- **Manual check in the PR:** the timing of the steps feels right on every level.
