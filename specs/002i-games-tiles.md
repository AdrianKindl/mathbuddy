# 002i – Games: a tile overview instead of a dropdown

## Why
Since the new design (777), every section looks like an app, but Games still
starts with a plain "Game" dropdown. Knowledge already uses coloured tiles; the
Games section should feel the same.

## What
- Games opens on an overview with one tile per game, two per row: Mini Sudoku,
  Sudoku, Number Hunt, Magic Square, Number Chain.
- Each tile has the game's name, one colour from the design tokens (coral,
  violet, amber, green, blue) and a small symbol in the bottom right corner.
  The symbols are SVGs inside `design.css`, so nothing loads from other sites.
- Tapping a tile opens that game: its name, rules, level and "New game", as
  before. "← All games" goes back to the overview. A game that has not ended
  is not saved, so going back simply ends it (like changing the game before).
- An open game stays open when the player switches to another section and
  back.
- On a laptop the tiles take at most 540 px; on a phone they fill the width.
- Only `app.py`, `design.css` and the tests change. Rules, the database and
  saving finished games (spec 012) stay the same.

## Bug fix found in review (Floria, #24)
Typing a digit into a Sudoku cell without pressing Enter and then clicking
"New game" or "← All games" crashed with a `KeyError`: the button's callback
ended the game and removed the cells before the cell's own callback ran. The
cell callback now does nothing when its cell or the game is already gone. Two
new tests cover both buttons. (The "New game" case already existed on `main`.)
## Changes to reviewed tests (needs the team's OK)
The old "Game" dropdown is gone, so the Games tests in `tests/test_app.py` open
a game by its tile instead:
- the start helpers (`start_game`, `start_sudoku`, `start_hunt`, `start_magic`,
  `start_chain_game`, `start_any_game`) click the game's tile instead of
  choosing it in the dropdown;
- the four "picker offers …" tests check the tiles instead of the dropdown's
  options; `test_games_section_offers_the_four_levels` opens Mini Sudoku first;
- the two "changing the game ends …" tests go back with "← All games" and open
  another tile.

What every test checks stays the same. `tests/test_app_profile.py` uses these
helpers and needs no change.

## Done when
- The overview shows the five tiles in order and no game.
- Every tile opens its game, and "New game" starts that game.
- "← All games" ends a running game and shows the tiles again.
- An open game is still open after visiting another section.
- All other tests pass.
- Manual check: laptop and phone, light and dark mode.
