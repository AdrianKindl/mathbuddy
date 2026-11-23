# 777 – Design: one look for every screen, on phone and laptop

## Why
Mathbuddy should feel like a real app that people enjoy opening every day: clear
on a phone held in one hand, roomy on a laptop, and lively when you play. Until
now every screen used the plain Streamlit look. The look must not copy Numbio.

## What
- **Theme** in `.streamlit/config.toml`: violet brand colour, warm accent,
  rounded corners, the fonts Plus Jakarta Sans (text), Outfit (headings,
  numbers) and JetBrains Mono (code). A light and a dark version; the app
  follows the setting of the phone or laptop.
- **Design layer** in `design.py`, `design.css` and `design.js`. `app.py` only
  calls `design.apply()` right after `st.set_page_config`. Nothing in the layer
  changes what a screen shows or does: same texts, keys, widgets and rules.
- **Top bar**: logo and "Mathbuddy" on the left, the signed-in player
  (greeting, name, avatar with the first letter) on the right. Tapping the
  player opens the account panel (the sidebar starts closed).
- **Navigation**: a glass bar with one icon per section on the laptop; on a
  phone (640 px wide or less) a tab bar fixed at the bottom, like a native app.
- **Every screen styled**: pills and segmented controls, input fields, cards,
  metrics (the main result as a coloured hero card), tables, charts, alerts,
  tabs, the account panel, the sign-in screen with floating maths symbols.
- **Tests and Trainer**: the task as a big card, a round 3-2-1 countdown, the
  time left as a ring that turns red in the last 10 seconds, a "+1" and a small
  burst of confetti for a right answer, a shake for a wrong one, a big confetti
  burst for a new highscore.
- **Knowledge and Textbook**: category tiles with a symbol, list rows with a
  chevron, "Previous / Next" stays one row on the phone.
- **Games**: Sudoku, Mini Sudoku, Number Hunt, Magic Square and Number Chain
  boards drawn as cards with big tiles; hearts inside the Lives card; the
  selected tile stays blue ("blue cell" in the game texts).
- **Phone details**: main buttons full width and at least 52 px high, two
  buttons side by side stay side by side, long button labels wrap instead of
  ending in "…", metric rows wrap two per line, no "Press Enter" hint.
- **New screens get the look by themselves** (for example the Profile with its
  metrics, highscore and leaderboard tables and the 7-day chart), as long as they
  use normal Streamlit elements.
- Respects "reduce motion": no animations, no confetti.
- **Flaky test fixed**: `test_decimal_answers_are_typed_with_a_point` (spec
  002) failed about once in ten runs. About every tenth decimal task has a whole
  answer (5.4 + 8.6 = 14), so there was no point to turn into a comma. The test
  now answers such tasks first, then checks exactly the same things as before.

## Out of scope
New features, new texts, changes to rules, the database or the tests of other
specs. A theme switch inside the app (the device setting decides).

## Done when
- `uv run pytest` passes, including `tests/test_design.py`: theme with light
  and dark version, no secrets in the theme file, a style sheet Streamlit does
  not remove, no nested `:has()`, phone + dark + reduced-motion rules, one nav
  icon per section, a script that loads nothing from other sites, the avatar
  letter, the player name shown as text only, the design on the sign-in screen
  and in the app, no extra text on any screen.
- Manual check in the PR (laptop and a browser at 375 px, light and dark):
  sign-in, Tests (select, countdown, running, result, highscore), Trainer
  (setup, running, result), Knowledge and Textbook (tiles, list, article,
  previous/next), all five games, Profile, account panel and sign-out.
