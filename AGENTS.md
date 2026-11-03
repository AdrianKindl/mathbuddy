# Mathbuddy – agent and team rules

## Commands
- Install after cloning: `uv sync`
- Run app: `uv run streamlit run app.py`
- Run tests: `uv run pytest`

## Structure
- `app.py` – Streamlit screens and navigation only (no rules, no SQL)
- `tasks.py` – task generation and answer checking (MB R1–R3). Reused later by the Trainer.
- `runs.py` – test run rules: time limit, scoring, completion, highscore (MB R4–R6)
- `accounts.py` – username and email rules (MB R7)
- `stats.py` – profile statistics: totals, accuracy, streak, 7-day activity (MB R8)
- `db.py` – SQLite storage. Default file `data/mathbuddy.db`, overridable with `MATHBUDDY_DB`.
- `tests/` – one test file per module, e.g. `tests/test_tasks.py`
- `docs/product-brief.md` – the BRD. Source of truth for behaviour.
- `specs/` – numbered task specs, e.g. `specs/001-tests.md`
- Keep all code files in the project root. Do not create a `src/` folder.
- All text shown in the app is in English.

## Design rules
- Rule modules never read the clock or create their own randomness.
  Pass the current time (`now`) and a `random.Random` instance in as arguments,
  so tests can use fixed times and fixed seeds.
- Rule modules contain no Streamlit and no SQL.
- Statistics, highscores and streaks are calculated from saved runs, never stored separately.

## Workflow rules
- Never commit directly to `main`. One branch per spec, named like the spec: `001-tests`.
- Before creating a branch: `git checkout main` and `git pull`.
- Write tests first and wait for review before implementing.
- Never weaken, skip or delete a reviewed test to make it pass. If a test seems
  wrong, stop and explain why with reference to the product brief.
- Only work on the current spec. Do not add features that are out of scope.
- Do not change files that belong to another open spec without asking.
- Never commit database files or secrets.
- Finish every task by running the tests, showing the output and listing the changed files.
- Every pull request is reviewed by another team member before merging.