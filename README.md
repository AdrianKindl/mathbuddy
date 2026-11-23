# Mathbuddy

A Streamlit web app for training mental arithmetic with short, varied and measurable practice.

**Live app:** https://playmathbuddy.streamlit.app

Group project for *Introduction to Programming* at Nova SBE.

## Objectives

Many people want to get faster and more confident at mental arithmetic, but practice apps either repeat the same tasks or give no sense of progress. Mathbuddy is for anyone who wants to train mental math in short sessions, for example students, or candidates preparing for case interviews.

- **Varied tasks:** every round uses newly generated tasks within fixed rules, so users train skills instead of memorising answers.
- **Measurable progress:** timed tests, highscores, a leaderboard and a profile with statistics show how a user improves over time.
- **Learning, not only testing:** a configurable Trainer explains mistakes, and the Knowledge section teaches tricks and background with matching practice.

The full requirements are in the business requirements document, [docs/product-brief.md](docs/product-brief.md).

## Features

All text in the app is in English. A user must be signed in to use it.

### Tests

- Five test types (Addition, Subtraction, Multiplication, Division, Random) at four levels (Easy, Medium, Hard, Pro).
- A 3-second countdown, then a 60-second timer. Answers given at or after 60 seconds do not count.
- One task at a time. The answer field flashes green or red after each answer, and tasks can be skipped or the test aborted.
- The result shows score, wrong and skipped tasks, accuracy and highscore, and marks a new highscore.
- The Tests screen shows "Your best" for the selected test type and level, plus an all-time leaderboard: the top 15 players, with your own rank shown even if you are not in the top 15.

### Trainer

Practice without the 60-second pressure, in three categories:

- **Operations:** Addition, Subtraction, Multiplication, Division, Percentage, Square or Square root, at four levels.
- **Number types:** Natural numbers, Decimals, Large numbers, Money or Fractions, mixing several operations with a level for each.
- **Special trainings:** Word problems, Mixed tasks, Digit sums, Rule of three, Equations, Chain calculations and Fun with fractions.

There are three modes: a fixed number of tasks, a total time limit, or a time limit per task. After a mistake the Trainer shows the correct answer and how to get there.

### Knowledge

- **Tricks:** mental-math tricks for addition, subtraction, multiplication, division and square numbers. Each has a step-by-step explanation and a practice round that uses exactly that trick, and a ✓ marks tricks you have practised.
- **Textbook:** short articles with worked examples and reference tables (Basics, Fractions, Case interview, Estimating & rounding), with practice tasks.

### Games

Mini Sudoku (6×6), Sudoku (9×9), Number Hunt, Magic Square and Number Chain, chosen from a tile overview.

- Each game has four levels and 3 lives. Wrong entries cost a life.
- The Sudokus have a stopwatch.
- Every game has an End game button, and a Try again button appears after Game over.

### Accounts and Profile

- Sign up with a username, an email address and a password typed twice. Sign in with your username from any device.
- Passwords are stored only as a salted hash.
- The profile shows:
  - tasks completed and accuracy across Tests, Trainer and Knowledge practice;
  - the longest streak of days with at least one activity;
  - your highscores per test type and level;
  - a bar chart of activities over the last 7 days.
- All statistics are calculated from saved activities, never stored separately. Each user sees only their own data, except usernames and scores on the leaderboard.

## Tech stack

| Purpose | Tool |
|---|---|
| Language | Python 3.12 |
| Web app | [Streamlit](https://streamlit.io) |
| Database (local) | SQLite, built into Python |
| Database (online) | PostgreSQL on [Neon](https://neon.tech), via `psycopg` |
| Tables and charts | pandas, Streamlit charts |
| Tests | pytest, Streamlit `AppTest` |
| Packages and environment | [uv](https://docs.astral.sh/uv/) |
| Hosting | Streamlit Community Cloud |

## Installation

Prerequisites:

- [Python 3.12](https://www.python.org/downloads/) or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [git](https://git-scm.com/downloads)

```bash
git clone https://github.com/AdrianKindl/mathbuddy.git
cd mathbuddy
uv sync
```

`uv sync` creates a virtual environment in `.venv` and installs the exact versions from `uv.lock`.

## Running the app

```bash
uv run streamlit run app.py
```

Streamlit opens the app in your browser (by default at http://localhost:8501). Create an account on the sign-in screen to start.

- **Without any configuration** the app stores accounts and activities in a local SQLite file, `data/mathbuddy.db`, and works fully offline. The folder is created automatically. You can choose another file with the environment variable `MATHBUDDY_DB`.
- **The online database** (used by the live app) is configured only through `MATHBUDDY_DATABASE_URL` in Streamlit secrets: `.streamlit/secrets.toml` locally, or the app's secrets settings on Streamlit Community Cloud. The secrets file and all database files are listed in `.gitignore` and are never committed.

## Running the tests

```bash
uv run pytest
```

The suite has about 2,700 tests. They cover the rule modules, the database layer and the screens through Streamlit's `AppTest`. Tests always use a temporary SQLite file and an empty secrets file, so they never touch the online database.

The PostgreSQL tests in `tests/test_postgres.py` are skipped unless `MATHBUDDY_TEST_DATABASE_URL` points to a separate test database. Never point it at the production database.

## Project structure

All code files live in the project root. Rule modules contain no Streamlit, no SQL and no clock: the current time and random numbers are passed in, so tests can use fixed values.

| File | Purpose |
|---|---|
| `app.py` | Streamlit screens and navigation (Tests, result, Profile, Games, sign-in). |
| `tasks.py` | Task generation and answer checking for Tests (MB R1–R3). |
| `runs.py` | Test run rules: time limit, scoring, completion, highscore (MB R4–R6). |
| `leaderboard.py` | Leaderboard ranking per test type and level (MB R10). |
| `stats.py` | Profile statistics: totals, accuracy, streak, 7-day activity (MB R8). |
| `accounts.py` | Username, email and password rules, password hashing (MB R7). |
| `db.py` | Storage of test runs; SQLite locally, PostgreSQL when `MATHBUDDY_DATABASE_URL` is set. |
| `accounts_db.py` | Storage of accounts and run ownership. |
| `activity_db.py` | Storage of completed activities (Trainer, practice, games) for the profile. |
| `trainer.py`, `trainer_tasks.py` | Trainer session rules and task generation. |
| `trainer_ui.py`, `trainer_db.py` | Trainer screens and storage. |
| `knowledge.py`, `knowledge_content.py` | Tricks: rules and content. |
| `knowledge_ui.py`, `knowledge_db.py` | Tricks screens and practised-trick storage. |
| `textbook.py`, `textbook_content.py` | Textbook: rules and article content. |
| `textbook_ui.py`, `textbook_db.py` | Textbook screens and storage. |
| `practice_ui.py` | Shared practice-round screen for Tricks and Textbook. |
| `sudoku.py`, `numberhunt.py`, `magicsquare.py`, `numberchain.py` | Game rules: Mini Sudoku and Sudoku, Number Hunt, Magic Square, Number Chain. |
| `ui_components.py` | Shared screen parts: answer form, focus and flash. |
| `design.py`, `design.css`, `design.js` | Visual design (stylesheet, top bar, cursors). |
| `install_trainer.py` | One-time installer used while adding the Trainer (spec 002); not needed to run the app. |
| `tests/` | One test file per module, plus screen tests (`test_app*.py`). |
| `docs/` | Product and feature briefs. |
| `specs/` | Numbered task specifications, one per feature or fix. |
| `.streamlit/config.toml` | Theme (colours and fonts). |

## Documentation

- [docs/product-brief.md](docs/product-brief.md): business requirements (BRD), the source of truth for behaviour.
- [docs/knowledge-brief.md](docs/knowledge-brief.md): Knowledge section, Tricks mode.
- [docs/textbook-brief.md](docs/textbook-brief.md): Knowledge section, Textbook mode.
- [specs/](specs/): one numbered spec per feature or fix, for example `001-tests.md` or `013-leaderboard.md`.
- [AGENTS.md](AGENTS.md): commands, structure, design rules and workflow rules for the team and for AI coding assistants.

## Development process

1. **Spec first.** Every feature or fix starts with a numbered spec in `specs/` that refers to the product brief.
2. **Tests first.** Tests are written before the implementation and reviewed by the team. Reviewed tests are never weakened to make code pass.
3. **One branch per spec,** named like the spec (for example `013-leaderboard`), created from the latest `main`. Nobody commits directly to `main`.
4. **Pull requests** are reviewed by another team member before merging.
5. **Deployment:** Streamlit Community Cloud deploys the live app from `main`.

All team members used an AI coding assistant (Claude Code) as part of the course workflow. Its rules are in [AGENTS.md](AGENTS.md). Each member specified, reviewed and tested the work in their area, and all changes went through the same spec, test and pull-request reviews. Some commits are attributed to the assistant in the git history.

## Team and contributions

| Name | GitHub | Main areas |
|---|---|---|
| Adrian Kindl | [AdrianKindl](https://github.com/AdrianKindl) | BRD (product brief), project setup and team rules, Tests (task rules, runs, Tests screen), Knowledge (Tricks, Textbook), leaderboard, deployment; fixes for the task flicker and late submits, custom cursor |
| Floria Bade | [Floria187](https://github.com/Floria187) | Online accounts and PostgreSQL storage, profile and statistics, "Your best" on the Tests tab |
| Celina Dzaak | [Celina695](https://github.com/Celina695) | Games: Mini Sudoku, Sudoku, Number Hunt, Magic Square and Number Chain (built with Claude Code), End game and Try again buttons, tile overview |
| Adrian Resch | [ReschAdr](https://github.com/ReschAdr) | Trainer, app design (new look, phone tab bar), showing only your own history |

## Known limitations

- **Timer updates come from the server.** The 60-second timer refreshes once per second from the server, so on a slow connection it can occasionally stutter. The time limit itself is enforced by the rules, not by the display.
- **Usernames are public on the leaderboard.** Every user's username and best score per test type and level are visible to all signed-in users. Email addresses are never shown.
- **Account features are basic.** There is no email verification, password reset, changing of username or password, or account deletion.
- **The live app needs its online database.** If the database is unreachable, the live app cannot sign users in. The local version works offline.
- **Fixed time zone.** Streaks and the 7-day chart use calendar days in Europe/Lisbon.
