"""Mini Sudoku rules: puzzle generation, entries, lives, win and loss (spec 002).

A grid is a tuple of 6 rows of 6 numbers; 0 marks an empty cell.
"""

import random
import re
from dataclasses import dataclass, replace
from enum import StrEnum

from tasks import LEVELS

SIZE = 6
BOX_ROWS = 2
BOX_COLS = 3
LIVES = 3
DIGITS = frozenset(range(1, SIZE + 1))

# How many of the 36 cells are empty at the start, per level (spec 002).
EMPTY_CELLS = {"Easy": 12, "Medium": 16, "Hard": 20, "Pro": 24}

Grid = tuple[tuple[int, ...], ...]

_DIGIT = re.compile(rf"[1-{SIZE}]")


# StrEnum and compared with ==, for the same reason as in runs.py: Streamlit
# re-imports changed modules, but a Game in session_state keeps the old class.
class Status(StrEnum):
    RUNNING = "running"
    WON = "won"
    LOST = "lost"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    IGNORED = "ignored"


@dataclass(frozen=True)
class Puzzle:
    givens: Grid
    solution: Grid


@dataclass(frozen=True)
class Game:
    level: str
    puzzle: Puzzle
    grid: Grid
    lives: int = LIVES
    status: Status = Status.RUNNING


# --- Checking grids ---


def _units() -> list[list[tuple[int, int]]]:
    """Every row, column and 2×3 box as a list of (row, col) cells."""
    rows = [[(r, c) for c in range(SIZE)] for r in range(SIZE)]
    cols = [[(r, c) for r in range(SIZE)] for c in range(SIZE)]
    boxes = [
        [(r, c) for r in range(top, top + BOX_ROWS) for c in range(left, left + BOX_COLS)]
        for top in range(0, SIZE, BOX_ROWS)
        for left in range(0, SIZE, BOX_COLS)
    ]
    return rows + cols + boxes


_UNITS = _units()


def _box_start(row: int, col: int) -> tuple[int, int]:
    return row - row % BOX_ROWS, col - col % BOX_COLS


def is_solved_grid(grid: Grid) -> bool:
    """True if every row, column and 2×3 box holds each of 1–6 exactly once."""
    return all({grid[r][c] for r, c in unit} == DIGITS for unit in _UNITS)


def _has_conflict(grid: list[list[int]]) -> bool:
    """True if a filled-in number appears twice in a row, column or box."""
    for unit in _UNITS:
        values = [grid[r][c] for r, c in unit if grid[r][c] != 0]
        if len(values) != len(set(values)):
            return True
    return False


def _candidates(grid: list[list[int]], row: int, col: int) -> set[int]:
    top, left = _box_start(row, col)
    used = set(grid[row])
    used.update(grid[r][col] for r in range(SIZE))
    used.update(
        grid[r][c] for r in range(top, top + BOX_ROWS) for c in range(left, left + BOX_COLS)
    )
    return DIGITS - used


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """Count the ways to fill the empty cells, stopping once `limit` is reached."""
    work = [list(row) for row in grid]
    if _has_conflict(work):
        return 0
    return _count(work, limit)


def _count(grid: list[list[int]], limit: int) -> int:
    # Fill the empty cell with the fewest options first: far fewer dead ends.
    best = None
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] == 0:
                options = _candidates(grid, r, c)
                if best is None or len(options) < len(best[2]):
                    best = (r, c, options)
    if best is None:
        return 1  # nothing left to fill: one complete solution

    row, col, options = best
    found = 0
    for value in sorted(options):
        grid[row][col] = value
        found += _count(grid, limit - found)
        grid[row][col] = 0
        if found >= limit:
            break
    return found


# --- Generating puzzles ---


def _fill(grid: list[list[int]], rng: random.Random) -> bool:
    """Fill every empty cell of `grid` in place, trying numbers in random order."""
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] == 0:
                options = sorted(_candidates(grid, r, c))
                rng.shuffle(options)
                for value in options:
                    grid[r][c] = value
                    if _fill(grid, rng):
                        return True
                grid[r][c] = 0
                return False
    return True


def _freeze(grid: list[list[int]]) -> Grid:
    return tuple(tuple(row) for row in grid)


def generate_puzzle(level: str, rng: random.Random) -> Puzzle:
    """A new puzzle with exactly one solution and EMPTY_CELLS[level] empty cells."""
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level!r}")
    target = EMPTY_CELLS[level]

    while True:
        grid = [[0] * SIZE for _ in range(SIZE)]
        _fill(grid, rng)
        solution = _freeze(grid)

        # Empty the cells one by one in random order. Put a number back if
        # removing it would allow a second solution.
        cells = [(r, c) for r in range(SIZE) for c in range(SIZE)]
        rng.shuffle(cells)
        emptied = 0
        for r, c in cells:
            if emptied == target:
                break
            grid[r][c] = 0
            if _count(grid, 2) == 1:
                emptied += 1
            else:
                grid[r][c] = solution[r][c]

        if emptied == target:
            return Puzzle(givens=_freeze(grid), solution=solution)
        # Rare: this solution got stuck before reaching the target. Try another.


# --- Playing ---


def start_game(level: str, rng: random.Random) -> Game:
    puzzle = generate_puzzle(level, rng)
    return Game(level=level, puzzle=puzzle, grid=puzzle.givens)


def parse_entry(raw: str) -> int | None:
    """The digit 1–6 in `raw`, or None if the entry should not be evaluated."""
    text = raw.strip()
    return int(text) if _DIGIT.fullmatch(text) else None


def enter_number(game: Game, row: int, col: int, raw: str) -> tuple[Game, Outcome]:
    """Evaluate an entry: a correct one is locked, a wrong one costs a life."""
    if not (0 <= row < SIZE and 0 <= col < SIZE):
        raise ValueError(f"Cell outside the grid: ({row}, {col})")
    if game.status != Status.RUNNING or game.grid[row][col] != 0:
        return game, Outcome.IGNORED

    value = parse_entry(raw)
    if value is None:
        return game, Outcome.IGNORED

    if value != game.puzzle.solution[row][col]:
        lives = game.lives - 1
        status = Status.LOST if lives <= 0 else Status.RUNNING
        return replace(game, lives=lives, status=status), Outcome.WRONG

    grid = tuple(
        tuple(value if (r, c) == (row, col) else old for c, old in enumerate(cells))
        for r, cells in enumerate(game.grid)
    )
    status = Status.WON if grid == game.puzzle.solution else Status.RUNNING
    return replace(game, grid=grid, status=status), Outcome.CORRECT
