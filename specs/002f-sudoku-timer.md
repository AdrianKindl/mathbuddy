# 002f – Games: a stopwatch for Mini Sudoku and Sudoku

## Why
Players want to see how fast they solve a Sudoku and try to beat their time.

The brief says Sudoku has "no time pressure". So this is a **stopwatch** that
only counts up: there is no time limit, and time never costs a life or ends a
game. Specs 002 and 002b listed "a timer" as out of scope; this spec adds the
stopwatch on purpose and needs the team's agreement.

Builds on spec 002e: merge `002-mini-sudoku` … `002e-number-chain` first.

## What
- Mini Sudoku and Sudoku show a "Time" next to the lives, as m:ss (h:mm:ss
  from one hour on). It starts when the game starts and refreshes every second.
- It stops when the game is won or lost and keeps showing the final time.
- Only the clock refreshes every second, so typing into the grid is not
  disturbed.
- The rules (`sudoku.py`) never read the clock: the app passes the current time
  in when a game starts and with every entry (AGENTS.md design rules).
- Games created without a start time (as in the tests of spec 002 and 002b)
  have no stopwatch; everything else works exactly as before.

## Out of scope
A countdown or time limit, best times, saving times. A stopwatch for Number
Hunt, Magic Square or Number Chain.

## Done when
- **Elapsed time:** with a start at 12:00:00, the elapsed time at 12:01:05 is
  65 seconds; it is frozen at the moment of the winning or losing entry, however
  late it is read; a game without a start time has none.
- **No effect on the game:** entries, lives, win and loss behave as before; all
  tests of spec 002 and 002b still pass unchanged.
- **Display:** 0 → "0:00", 65 → "1:05", 3725 → "1:02:05".
- **Screen:** a new Mini Sudoku and a new Sudoku show "Time" next to the lives;
  after solving, "You solved it!" and the time are shown.
- **Manual check in the PR:** the clock ticks and typing is not disturbed.
