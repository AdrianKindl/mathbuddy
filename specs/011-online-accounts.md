# 011 Online accounts: play from any device with username and password

## Why
Mathbuddy should run online, so that players can sign in from their own phones
and laptops and later compete on a shared leaderboard. Today every player runs
the app locally and all runs are saved without a user in a local SQLite file.
This spec puts the app online, moves storage to a shared online database and
adds accounts. The profile statistics (MB R8) follow in 012, the leaderboard in 013.

The team agreed to extend the scope of the product brief here: passwords and an
external database service are used, although the brief does not require them.

## What

### Storage (`db.py`)
- If the setting `MATHBUDDY_DATABASE_URL` is present, `db.connect()` connects
  to that Postgres database. Otherwise it uses the local SQLite file exactly as
  before (`MATHBUDDY_DB` or `data/mathbuddy.db`).
- The app copies `MATHBUDDY_DATABASE_URL` from the Streamlit secrets into the
  environment at start. `db.py` itself does not import Streamlit.
- The SQL the storage modules already use (`?` placeholders and
  `INSERT OR IGNORE`) works on both databases. `trainer_db.py`,
  `knowledge_db.py` and `textbook_db.py` are not changed.
- The `runs` table is not changed.

### Accounts (`accounts.py` rules, `accounts_db.py` storage)
- Username: 3 to 20 characters, only the letters A to Z (upper or lower case),
  digits and underscore (MB R7). Unique regardless of upper or lower case:
  "Adrian" and "adrian" are the same username.
- Email: valid format (`name@domain.tld`, no spaces), unique, compared in lower case.
- Password: at least 8 characters, typed twice when creating the account.
- Passwords are never stored. Only a salted hash is stored
  (`hashlib.pbkdf2_hmac` with SHA 256). The salt is passed in as an argument;
  the app creates it with `secrets.token_bytes`, so tests can use a fixed salt.
- Sign in with username (any upper or lower case) and password. A wrong
  username or a wrong password gives the same message: "Wrong username or password".
- New table `users`: id, username, username_key (lower case, unique),
  email (lower case, unique), password_hash, created_at.
- New table `run_owners`: run_id, user_id. A completed run is saved as before
  and its owner is recorded here. Runs saved before this spec have no owner;
  they are kept but shown to nobody.

### Screens (`app.py`)
- Without a signed in user the app shows only the sign in screen:
  heading "Mathbuddy" and two tabs, "Sign in" (username, password) and
  "Create account" (username, email, password, repeat password).
  It shows the hint "Use a password you don't use anywhere else."
- A rejected sign up shows every reason and creates no account.
- Creating an account signs the new user in.
- After signing in, the navigation works as before. The sidebar shows
  "Signed in as <username>" and a "Sign out" button. Signing out returns to
  the sign in screen.
- The Tests screen and the result show only the signed in user's highscores.

### Online
- The app runs on Streamlit Community Cloud from the GitHub repo.
- The database runs on Neon (Free plan, Postgres, region Frankfurt).
- The connection string is stored only in `.streamlit/secrets.toml` locally
  and in the Streamlit Cloud secrets settings. It is never committed.
  `.streamlit/secrets.toml` is listed in `.gitignore`.
- New dependency: `psycopg[binary]`.

### Tests
- `tests/conftest.py` signs a test user in for every test that opens the app
  with `AppTest.from_file`, so the existing screen tests keep working unchanged.
  Tests marked `@pytest.mark.signed_out` start without a user.
- In `tests/test_app.py` only the helper `seed_run` changes: the seeded run
  also gets the test user as owner. No expected result changes.
- `tests/test_postgres.py` runs the storage tests against a real Postgres
  database. It is skipped unless `MATHBUDDY_TEST_DATABASE_URL` is set. That URL
  must point to a separate Neon branch (for example `test`), never to `production`,
  because the tests delete all tables.

## Out of scope
Profile statistics, streak and 7 day chart (012). Leaderboard (013).
Owners for trainer sessions, Knowledge and Textbook rounds (later spec, with
the owners of those modules). Password reset, email verification, changing
username or password, deleting accounts, locking after failed sign ins.
Any change to the rules of Tests, Trainer, Knowledge, Textbook or Games.

## Done when
- **Accounts (A7):** "adrian" can be created; "Adrian" is then rejected;
  "adrian@" is rejected; an email used by another account is rejected
  (also in other upper or lower case); a password of 7 characters is
  rejected; two different passwords are rejected. A rejected sign up creates no account.
- **Password:** the stored hash does not contain the password; the same
  password with the same salt gives the same hash; a different salt gives a
  different hash; the right password signs in, a wrong one does not;
  "ADRIAN" can sign in as "adrian".
- **Own data only:** a run completed by user A does not appear in the
  highscores of user B. Runs without an owner appear for nobody.
- **Sign in screen:** without a user, the navigation is not shown; after
  signing in it is; after signing out it is gone again.
- **Both databases:** all existing tests pass on SQLite. `tests/test_postgres.py`
  passes against a Neon test branch.
- **Online:** an account created on a phone through the public link can sign
  in on a laptop and sees the same highscores. After a reboot of the app on
  Streamlit Cloud, accounts and runs are still there.
- **No secrets:** `git status` never shows `.streamlit/secrets.toml` or a `.db` file.
