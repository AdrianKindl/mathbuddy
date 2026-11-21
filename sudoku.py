"""Sudoku rules for Mini Sudoku (6×6, spec 002) and Sudoku (9×9, spec 002b):
puzzle generation, entries, lives, win and loss, and the stopwatch (spec 002f).

A grid is a tuple of rows of numbers; 0 marks an empty cell. The size of the
grid (6 or 9) decides which variant's rules apply.
"""

import random
import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from tasks import LEVELS

# Mini Sudoku, the default variant.
SIZE = 6
BOX_ROWS = 2
BOX_COLS = 3
LIVES = 3

# How many of the 36 cells are empty at the start, per level (spec 002).
EMPTY_CELLS = {"Easy": 12, "Medium": 16, "Hard": 20, "Pro": 24}
# How many of the 81 cells are empty at the start, per level (spec 002b).
SUDOKU_EMPTY_CELLS = {"Easy": 36, "Medium": 42, "Hard": 48, "Pro": 52}

Grid = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class Variant:
    name: str
    size: int
    box_rows: int
    box_cols: int
    empty_cells: dict[str, int]

    @property
    def digits(self) -> frozenset[int]:
        return frozenset(range(1, self.size + 1))


MINI = Variant("Mini Sudoku", SIZE, BOX_ROWS, BOX_COLS, EMPTY_CELLS)
CLASSIC = Variant("Sudoku", 9, 3, 3, SUDOKU_EMPTY_CELLS)
VARIANTS = {variant.size: variant for variant in (MINI, CLASSIC)}


def variant_of(grid: Grid) -> Variant:
    """The variant whose rules apply to `grid`, found from its size."""
    if len(grid) not in VARIANTS or any(len(row) != len(grid) for row in grid):
        raise ValueError(f"No Sudoku variant for a grid of {len(grid)} rows")
    return VARIANTS[len(grid)]


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
    started_at: datetime | None = None  # for the stopwatch (spec 002f)
    ended_at: datetime | None = None  # when the game was won or lost


# --- Checking grids ---


def _units(variant: Variant) -> list[list[tuple[int, int]]]:
    """Every row, column and box as a list of (row, col) cells."""
    size = variant.size
    rows = [[(r, c) for c in range(size)] for r in range(size)]
    cols = [[(r, c) for r in range(size)] for c in range(size)]
    boxes = [
        [
            (r, c)
            for r in range(top, top + variant.box_rows)
            for c in range(left, left + variant.box_cols)
        ]
        for top in range(0, size, variant.box_rows)
        for left in range(0, size, variant.box_cols)
    ]
    return rows + cols + boxes


_UNITS = {variant.size: _units(variant) for variant in VARIANTS.values()}


def is_solved_grid(grid: Grid) -> bool:
    """True if every row, column and box holds each number exactly once."""
    variant = variant_of(grid)
    return all(
        {grid[r][c] for r, c in unit} == variant.digits for unit in _UNITS[variant.size]
    )


def _has_conflict(grid: list[list[int]], variant: Variant) -> bool:
    """True if a filled-in number appears twice in a row, column or box."""
    for unit in _UNITS[variant.size]:
        values = [grid[r][c] for r, c in unit if grid[r][c] != 0]
        if len(values) != len(set(values)):
            return True
    return False


def _candidates(grid: list[list[int]], variant: Variant, row: int, col: int) -> set[int]:
    top = row - row % variant.box_rows
    left = col - col % variant.box_cols
    used = set(grid[row])
    used.update(grid[r][col] for r in range(variant.size))
    used.update(
        grid[r][c]
        for r in range(top, top + variant.box_rows)
        for c in range(left, left + variant.box_cols)
    )
    return variant.digits - used


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """Count the ways to fill the empty cells, stopping once `limit` is reached."""
    variant = variant_of(grid)
    work = [list(row) for row in grid]
    if _has_conflict(work, variant):
        return 0
    return _count(work, variant, limit)


def _count(grid: list[list[int]], variant: Variant, limit: int) -> int:
    # Fill the empty cell with the fewest options first: far fewer dead ends.
    best = None
    for r in range(variant.size):
        for c in range(variant.size):
            if grid[r][c] == 0:
                options = _candidates(grid, variant, r, c)
                if best is None or len(options) < len(best[2]):
                    best = (r, c, options)
                    if not options:
                        return 0  # a dead end: no number fits here
    if best is None:
        return 1  # nothing left to fill: one complete solution

    row, col, options = best
    found = 0
    for value in sorted(options):
        grid[row][col] = value
        found += _count(grid, variant, limit - found)
        grid[row][col] = 0
        if found >= limit:
            break
    return found


# --- Generating puzzles ---


def _fill(grid: list[list[int]], variant: Variant, rng: random.Random) -> bool:
    """Fill every empty cell of `grid` in place, trying numbers in random order."""
    for r in range(variant.size):
        for c in range(variant.size):
            if grid[r][c] == 0:
                options = sorted(_candidates(grid, variant, r, c))
                rng.shuffle(options)
                for value in options:
                    grid[r][c] = value
                    if _fill(grid, variant, rng):
                        return True
                grid[r][c] = 0
                return False
    return True


def _freeze(grid: list[list[int]]) -> Grid:
    return tuple(tuple(row) for row in grid)


def generate_puzzle(level: str, rng: random.Random, variant: Variant = MINI) -> Puzzle:
    """A new puzzle with exactly one solution and the level's number of empty cells."""
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level!r}")
    target = variant.empty_cells[level]
    size = variant.size

    while True:
        grid = [[0] * size for _ in range(size)]
        _fill(grid, variant, rng)
        solution = _freeze(grid)

        # Empty the cells one by one in random order. Put a number back if
        # removing it would allow a second solution.
        cells = [(r, c) for r in range(size) for c in range(size)]
        rng.shuffle(cells)
        emptied = 0
        for r, c in cells:
            if emptied == target:
                break
            grid[r][c] = 0
            if _count(grid, variant, 2) == 1:
                emptied += 1
            else:
                grid[r][c] = solution[r][c]

        if emptied == target:
            return Puzzle(givens=_freeze(grid), solution=solution)
        # Rare: this solution got stuck before reaching the target. Try another.


# --- Playing ---


def start_game(
    level: str, rng: random.Random, variant: Variant = MINI, now: datetime | None = None
) -> Game:
    """A new game; `now` starts its stopwatch."""
    puzzle = generate_puzzle(level, rng, variant)
    return Game(level=level, puzzle=puzzle, grid=puzzle.givens, started_at=now)


def parse_entry(raw: str, size: int = SIZE) -> int | None:
    """The number 1–size in `raw`, or None if the entry should not be evaluated."""
    text = raw.strip()
    if not re.fullmatch(r"[1-9]", text) or int(text) > size:
        return None
    return int(text)


def enter_number(
    game: Game, row: int, col: int, raw: str, now: datetime | None = None
) -> tuple[Game, Outcome]:
    """Evaluate an entry: a correct one is locked, a wrong one costs a life.

    `now` stops the stopwatch if this entry wins or loses the game.
    """
    size = variant_of(game.grid).size
    if not (0 <= row < size and 0 <= col < size):
        raise ValueError(f"Cell outside the grid: ({row}, {col})")
    if game.status != Status.RUNNING or game.grid[row][col] != 0:
        return game, Outcome.IGNORED

    value = parse_entry(raw, size)
    if value is None:
        return game, Outcome.IGNORED

    if value != game.puzzle.solution[row][col]:
        lives = game.lives - 1
        status = Status.LOST if lives <= 0 else Status.RUNNING
        ended_at = now if status == Status.LOST else None
        return replace(game, lives=lives, status=status, ended_at=ended_at), Outcome.WRONG

    grid = tuple(
        tuple(value if (r, c) == (row, col) else old for c, old in enumerate(cells))
        for r, cells in enumerate(game.grid)
    )
    status = Status.WON if grid == game.puzzle.solution else Status.RUNNING
    ended_at = now if status == Status.WON else None
    return replace(game, grid=grid, status=status, ended_at=ended_at), Outcome.CORRECT


# --- Stopwatch (spec 002f): it only counts, it never ends a game ---


def elapsed_seconds(game: Game, now: datetime) -> float | None:
    """Seconds since the start; frozen once the game is won or lost."""
    if game.started_at is None:
        return None
    end = game.ended_at or now
    return max(0.0, (end - game.started_at).total_seconds())


def clock_text(seconds: float) -> str:
    """Whole seconds as m:ss, or h:mm:ss from one hour on."""
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
