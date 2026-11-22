# 013 – Leaderboard: all-time ranking per operation and level

Source: `docs/product-brief.md` version 1.2 (changed in this branch): new MB06,
new MB R10, new scenarios A11–A13, and adjusted MB R7, MB R9 and scope boundaries.

## Why
Since spec 011 every player has an account and their runs are stored online.
Players now want to compare themselves with others: who is fastest at
Multiplication Pro? An all-time leaderboard per operation and level on the
Tests screen shows the best players and where the signed-in player stands.

## What

### Screen (MB06)
- On the Tests screen, below the Highscores, a section **Leaderboard** with the
  caption "All-time top 15 · <operation> · <level>". It follows the Operation
  and Level buttons above it and changes when the selection changes.
- A table with the columns Rank, Player, Score, Date (the date the score was
  first reached, `YYYY-MM-DD`, UTC). It uses the same table style as the
  Highscores.
- The signed-in player's row is marked "<username> (you)" (and highlighted).
  If they rank below 15, a row "…" follows the top 15, then their own row with
  their real rank. Without a run of this operation and level there is no own row.
- Without any ranked run: "No runs yet for this operation and level." and no table.
- Only usernames are shown, never email addresses.

### Rules (MB R10)
- One all-time leaderboard per test type and level, of all users.
- Each user appears at most once, with their best score (MB R6) of that test
  type and level. If they reached that score more than once, the earliest time counts.
- Runs without an owner (saved before spec 011) are not included.
- Higher scores rank first. Equal scores: the earlier date and time ranks
  first. Equal score and identical time: usernames in alphabetical order,
  ignoring upper and lower case. Every row gets its own rank 1, 2, 3, …
- Top 15. Own row as described above.
- Calculated from the saved runs; nothing new is stored.

### Structure
- `leaderboard.py` (rule module, no Streamlit, no SQL, no clock): `Entry`
  (user id, username, value, achieved at), `Row` (rank, user id, username,
  value, achieved at, is_you), `Board` (top rows, own row or None), and
  `build(entries, *, better=Better.HIGHER, top=15, user_id=None)`.
  `Better.LOWER` ranks smaller values first (for example a fastest time in a
  game later); Tests always uses `Better.HIGHER`. Nothing in it is specific to Tests.
- `db.py`: `leaderboard_entries(test_type, level)` returns one `Entry` per
  owned run of that test type and level: a read-only join of `runs`,
  `run_owners` and `users`. It selects the username, never the email. It uses
  plain SQL with `?` placeholders, so it runs on SQLite and on Postgres
  through the existing translation.
- **No new table:** everything needed is already stored (runs, owners,
  usernames). AGENTS.md says rankings like highscores are calculated from
  saved runs, never stored separately.
- `app.py`: the Leaderboard section in `render_select()`, using the existing
  table style. No rules, no SQL.

### Product brief (this branch)
- Version 1.2 with a change note.
- New MB06 – See the leaderboard; new MB R10 – Leaderboard; new A11–A13.
- MB R7: "Each user only sees their own statistics and highscores" gets the
  exception "except the leaderboard (MB R10), which shows usernames and best scores".
- MB R9: runs without an owner are also left out of the leaderboard.
- Scope boundaries: the leaderboard is in scope (no longer "planned").

## Out of scope
Leaderboards for games, Trainer, Knowledge or Textbook (the rule module is
ready for them). Weekly or daily boards, friends, filters, pagination beyond
the top 15. Hiding a user from the leaderboard. Any change to accounts
(`accounts.py`, `accounts_db.py`), `tests/conftest.py`, the `runs`, `users`
or `run_owners` tables, Trainer, Knowledge or Games.

## Done when
- **A11 – Order and tie-break:** Mia 18 (reached Monday), Adrian 18 (Tuesday),
  Lena 15 show as 1 Mia, 2 Adrian, 3 Lena. Adrian's runs of 12 and 18 appear
  once, with 18.
- **A12 – Own rank:** with 20 players, 15 rows are shown. A signed-in player
  ranked 18 sees "…" and their row with rank 18 below; ranked 4 sees their row
  marked "(you)" and no extra row; without a run sees no own row.
- **A13 – Separate and private:** a Multiplication Medium run does not appear
  on the Multiplication Easy leaderboard; runs without an owner appear on no
  leaderboard; no email address appears on the screen.
- **Lower is better:** the rule module ranks smaller values first with
  `Better.LOWER`, with the same tie-break.
- **Both databases:** all tests pass on SQLite; the Postgres test for
  `leaderboard_entries` passes against a Neon test branch.
- **Unchanged:** all existing tests pass without changes.
