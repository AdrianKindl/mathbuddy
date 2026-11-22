"""Owners of activities and saved games (spec 012, MB R8).

Test runs get their owner in `run_owners` (spec 011). Trainer sessions and
Tricks and Textbook practice rounds get theirs in `activity_owners`. Games
are saved once when they end, in `game_results`, with their player. Every
completed activity of a player is read back as a `stats.Activity`.
"""

from contextlib import closing
from datetime import datetime, timezone

import accounts_db
import db
import knowledge
import knowledge_db
import textbook
import textbook_db
import trainer_db
from stats import Activity, Kind

GAME_OUTCOMES = ("won", "lost")
OWNED_KINDS = (Kind.TRAINER, Kind.TRICKS, Kind.TEXTBOOK)


def init_db() -> None:
    for module in (db, accounts_db, trainer_db, knowledge_db, textbook_db):
        module.init_db()  # the tables that list_activities_for reads
    with closing(db.connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_owners (
                kind TEXT NOT NULL,
                activity_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                PRIMARY KEY (kind, activity_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS game_results (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                game TEXT NOT NULL,
                level TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                outcome TEXT NOT NULL
            )
            """
        )


def assign_owner(kind: Kind, activity_id: str, user_id: str) -> None:
    """Record the player of a saved Trainer session or practice round. Repeating changes nothing."""
    if kind not in OWNED_KINDS:
        raise ValueError(f"Owners of {kind} are not kept here")
    with closing(db.connect()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO activity_owners (kind, activity_id, user_id) VALUES (?, ?, ?)",
            (kind.value, activity_id, user_id),
        )


def save_game(
    game_id: str, user_id: str, game: str, level: str, finished_at: datetime, outcome: str
) -> None:
    """Save a game that ended. Saving the same id again changes nothing."""
    if outcome not in GAME_OUTCOMES:
        raise ValueError("Only a won or lost game can be saved")
    with closing(db.connect()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO game_results (id, user_id, game, level, finished_at, outcome) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (game_id, user_id, game, level,
             finished_at.astimezone(timezone.utc).isoformat(), outcome),
        )  # fmt: skip


def _moment(text: str) -> datetime:
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _owned(connection, table: str, kind: Kind, columns: str, user_id: str) -> list:
    return connection.execute(
        f"SELECT t.finished_at, {columns} FROM {table} t "
        "JOIN activity_owners o ON o.activity_id = t.id AND o.kind = ? "
        "WHERE o.user_id = ?",
        (kind.value, user_id),
    ).fetchall()


def list_activities_for(user_id: str) -> list[Activity]:
    """Every completed activity of one player, oldest first. Unowned ones belong to nobody."""
    with closing(db.connect()) as connection:
        tests = connection.execute(
            "SELECT runs.finished_at, runs.correct, runs.wrong + runs.skipped FROM runs "
            "JOIN run_owners ON run_owners.run_id = runs.id WHERE run_owners.user_id = ?",
            (user_id,),
        ).fetchall()
        trainer = _owned(connection, "trainer_sessions", Kind.TRAINER, "t.correct, t.wrong + t.skipped", user_id)
        tricks = _owned(connection, "practice_rounds", Kind.TRICKS, "t.correct", user_id)
        textbook_rounds = _owned(connection, "textbook_rounds", Kind.TEXTBOOK, "t.correct", user_id)
        games = connection.execute(
            "SELECT finished_at FROM game_results WHERE user_id = ?", (user_id,)
        ).fetchall()

    activities = [Activity(Kind.TEST, _moment(f), c, n) for f, c, n in tests]
    activities += [Activity(Kind.TRAINER, _moment(f), c, n) for f, c, n in trainer]
    # Practice rounds are only saved with all tasks answered: not correct = length - correct.
    activities += [Activity(Kind.TRICKS, _moment(f), c, knowledge.ROUND_LENGTH - c) for f, c in tricks]
    activities += [
        Activity(Kind.TEXTBOOK, _moment(f), c, textbook.ROUND_LENGTH - c) for f, c in textbook_rounds
    ]
    activities += [Activity(Kind.GAME, _moment(f)) for (f,) in games]
    return sorted(activities, key=lambda activity: activity.finished_at)
