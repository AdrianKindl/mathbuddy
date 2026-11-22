"""Magic Square rules: puzzle generation, entries, lives, win and loss (spec 002d).

Every row, every column and both diagonals add up to the same target sum. The
grid holds consecutive whole numbers, each once. A grid is a tuple of rows;
0 marks an empty cell.
"""

import random
from dataclasses import dataclass, replace
from enum import StrEnum

from tasks import LEVELS

LIVES = 3

# Per level: grid size, empty cells, and the range for the smallest number.
LEVEL_SETTINGS = {
    "Easy": (3, 4, 1, 1),
    "Medium": (3, 6, 2, 20),
    "Hard": (4, 7, 1, 1),
    "Pro": (4, 10, 2, 30),
}

Grid = tuple[tuple[int, ...], ...]

# The only 3×3 magic square with 1–9, up to rotation and reflection.
LO_SHU: Grid = ((2, 7, 6), (9, 5, 1), (4, 3, 8))

# Some 4×4 magic squares with 1–16. Each one gives 32 more through _transform.
BASE_SQUARES_4: tuple[Grid, ...] = (
    ((15, 10, 5, 4), (3, 6, 9, 16), (2, 7, 12, 13), (14, 11, 8, 1)),
    ((12, 2, 15, 5), (14, 8, 9, 3), (1, 13, 4, 16), (7, 11, 6, 10)),
    ((10, 6, 11, 7), (8, 15, 2, 9), (3, 12, 5, 14), (13, 1, 16, 4)),
    ((7, 3, 10, 14), (2, 12, 5, 15), (16, 6, 11, 1), (9, 13, 8, 4)),
    ((5, 7, 12, 10), (9, 11, 6, 8), (16, 14, 3, 1), (4, 2, 13, 15)),
    ((12, 2, 15, 5), (3, 7, 14, 10), (13, 9, 4, 8), (6, 16, 1, 11)),
    ((9, 4, 7, 14), (2, 16, 11, 5), (15, 1, 6, 12), (8, 13, 10, 3)),
    ((9, 5, 8, 12), (4, 16, 13, 1), (14, 2, 3, 15), (7, 11, 10, 6)),
    ((4, 14, 1, 15), (11, 5, 10, 8), (13, 3, 16, 2), (6, 12, 7, 9)),
    ((7, 13, 10, 4), (12, 2, 5, 15), (6, 16, 11, 1), (9, 3, 8, 14)),
    ((4, 15, 9, 6), (5, 10, 16, 3), (14, 1, 7, 12), (11, 8, 2, 13)),
    ((4, 10, 5, 15), (13, 7, 12, 2), (11, 1, 14, 8), (6, 16, 3, 9)),
)

# Reordering rows and columns by the same one of these keeps a 4×4 square magic:
# rows and columns keep their sums, and both diagonals stay diagonals.
_SAME_ORDER_4 = (
    (0, 1, 2, 3),
    (3, 2, 1, 0),
    (1, 0, 3, 2),
    (2, 3, 0, 1),
    (0, 2, 1, 3),
    (3, 1, 2, 0),
    (1, 3, 0, 2),
    (2, 0, 3, 1),
)


# StrEnum and compared with ==, for the same reason as in runs.py.
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
    target: int


@dataclass(frozen=True)
class Game:
    level: str
    puzzle: Puzzle
    grid: Grid
    lives: int = LIVES
    status: Status = Status.RUNNING


# --- Checking grids ---


def lines(size: int) -> list[list[tuple[int, int]]]:
    """Every row, every column and both diagonals as lists of (row, col) cells."""
    rows = [[(r, c) for c in range(size)] for r in range(size)]
    cols = [[(r, c) for r in range(size)] for c in range(size)]
    diagonals = [[(i, i) for i in range(size)], [(i, size - 1 - i) for i in range(size)]]
    return rows + cols + diagonals


def magic_sum(size: int, smallest: int) -> int:
    """The target sum of a size×size square of the numbers smallest, smallest + 1, …"""
    count = size * size
    return (count * smallest + count * (count - 1) // 2) // size


def is_magic(grid: Grid) -> bool:
    """True if the grid is full of different numbers and every line has the same sum."""
    values = [value for row in grid for value in row]
    if any(len(row) != len(grid) for row in grid) or 0 in values:
        return False
    if len(set(values)) != len(values):
        return False
    sums = {sum(grid[r][c] for r, c in line) for line in lines(len(grid))}
    return len(sums) == 1


def _fits(grid: list[list[int]], target: int, all_lines) -> bool:
    """No line is over the target, and every full line hits it exactly."""
    for line in all_lines:
        values = [grid[r][c] for r, c in line]
        total = sum(values)
        if 0 in values:
            if total >= target:  # the missing numbers are all above 0
                return False
        elif total != target:
            return False
    return True


def count_completions(grid: Grid, numbers, target: int, limit: int = 2) -> int:
    """Count the ways to place `numbers` into the empty cells, up to `limit`."""
    size = len(grid)
    work = [list(row) for row in grid]
    empty = [(r, c) for r in range(size) for c in range(size) if work[r][c] == 0]
    all_lines = lines(size)
    if len(empty) != len(numbers):
        return 0

    found = 0

    def place(k: int, left: frozenset[int]) -> None:
        nonlocal found
        if found >= limit:
            return
        if k == len(empty):
            found += 1
            return
        r, c = empty[k]
        for value in sorted(left):
            work[r][c] = value
            if _fits(work, target, all_lines):
                place(k + 1, left - {value})
            work[r][c] = 0

    if _fits(work, target, all_lines):
        place(0, frozenset(numbers))
    return found


# --- Generating puzzles ---


def _transform(square: Grid, rng: random.Random) -> Grid:
    """A random rotation, reflection, reordering or complement that keeps it magic."""
    size = len(square)
    grid = [list(row) for row in square]
    if rng.random() < 0.5:
        grid = [list(col) for col in zip(*grid)]  # transpose
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]  # rotate a quarter turn
    if size == 4:
        order = rng.choice(_SAME_ORDER_4)
        grid = [[grid[order[r]][order[c]] for c in range(size)] for r in range(size)]
    if rng.random() < 0.5:
        largest = size * size + 1
        grid = [[largest - value for value in row] for row in grid]  # complement
    return tuple(tuple(row) for row in grid)


def generate_puzzle(level: str, rng: random.Random) -> Puzzle:
    """A new magic square with the level's empty cells and exactly one solution."""
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level!r}")
    size, empty_cells, low, high = LEVEL_SETTINGS[level]
    smallest = rng.randint(low, high)
    target = magic_sum(size, smallest)

    while True:
        base = LO_SHU if size == 3 else rng.choice(BASE_SQUARES_4)
        solution = tuple(
            tuple(value + smallest - 1 for value in row) for row in _transform(base, rng)
        )

        # Empty cells one by one in random order. Put a number back if the
        # missing numbers could then be placed in more than one way.
        grid = [list(row) for row in solution]
        cells = [(r, c) for r in range(size) for c in range(size)]
        rng.shuffle(cells)
        emptied = 0
        for r, c in cells:
            if emptied == empty_cells:
                break
            grid[r][c] = 0
            missing = [solution[i][j] for i in range(size) for j in range(size) if grid[i][j] == 0]
            frozen = tuple(tuple(row) for row in grid)
            if count_completions(frozen, missing, target) == 1:
                emptied += 1
            else:
                grid[r][c] = solution[r][c]

        if emptied == empty_cells:
            givens = tuple(tuple(row) for row in grid)
            return Puzzle(givens=givens, solution=solution, target=target)


# --- Playing ---


def start_game(level: str, rng: random.Random) -> Game:
    puzzle = generate_puzzle(level, rng)
    return Game(level=level, puzzle=puzzle, grid=puzzle.givens)


def keypad(game: Game) -> tuple[int, ...]:
    """The numbers still needed, smallest first: the only ones the keypad offers."""
    size = len(game.grid)
    return tuple(
        sorted(
            game.puzzle.solution[r][c]
            for r in range(size)
            for c in range(size)
            if game.grid[r][c] == 0
        )
    )


def enter_number(game: Game, row: int, col: int, value: int) -> tuple[Game, Outcome]:
    """Evaluate a keypad entry: a correct one is locked, a wrong one costs a life."""
    size = len(game.grid)
    if not (0 <= row < size and 0 <= col < size):
        raise ValueError(f"Cell outside the grid: ({row}, {col})")
    if game.status != Status.RUNNING or game.grid[row][col] != 0:
        return game, Outcome.IGNORED
    if value not in keypad(game):
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
