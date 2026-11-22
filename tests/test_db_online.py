"""Choosing between local SQLite and online Postgres in db.py (spec 011).

These tests need no database server: the Postgres connection is replaced by a
stand-in that records what it receives.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
import streamlit as st
from streamlit import config

import db

URL = "postgresql://user:password@example.neon.tech/neondb?sslmode=require"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DB", str(tmp_path / "test.db"))
    monkeypatch.delenv("MATHBUDDY_DATABASE_URL", raising=False)


class FakeCursor:
    def fetchall(self):
        return []


class FakePostgres:
    """Stands in for a psycopg connection."""

    def __init__(self):
        self.statements = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def execute(self, sql, parameters=None):
        self.statements.append((sql, parameters))
        return FakeCursor()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


@pytest.fixture
def fake_postgres(monkeypatch):
    connections = []

    def fake_connect(url):
        connections.append(url)
        fake = FakePostgres()
        fake_connect.last = fake
        return fake

    monkeypatch.setattr(db, "_connect_postgres", fake_connect)
    monkeypatch.setenv("MATHBUDDY_DATABASE_URL", URL)
    fake_connect.urls = connections
    return fake_connect


# --- Which database ---


def test_without_url_the_local_sqlite_file_is_used():
    assert db.database_url() is None
    with closing(db.connect()) as connection:
        assert isinstance(connection, sqlite3.Connection)


def test_an_empty_url_counts_as_no_url(monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DATABASE_URL", "")
    assert db.database_url() is None


def test_with_url_postgres_is_used(fake_postgres):
    db.connect()
    assert fake_postgres.urls == [URL]


def test_with_url_no_local_file_is_created(fake_postgres, tmp_path):
    db.connect()
    assert not (tmp_path / "test.db").exists()


# --- Same SQL on both databases ---


def test_question_marks_become_postgres_placeholders():
    assert db.to_postgres("SELECT * FROM runs WHERE id = ? AND level = ?") == (
        "SELECT * FROM runs WHERE id = %s AND level = %s"
    )


def test_insert_or_ignore_becomes_on_conflict_do_nothing():
    sql = "INSERT OR IGNORE INTO runs (id, correct) VALUES (?, ?)"
    assert db.to_postgres(sql) == (
        "INSERT INTO runs (id, correct) VALUES (%s, %s) ON CONFLICT DO NOTHING"
    )


def test_multi_line_insert_or_ignore_is_translated():
    sql = "INSERT OR IGNORE INTO runs \n(id, correct) \nVALUES (?, ?)\n"
    assert db.to_postgres(sql).strip().endswith("ON CONFLICT DO NOTHING")
    assert "OR IGNORE" not in db.to_postgres(sql)


def test_percent_signs_are_kept_literal():
    assert db.to_postgres("SELECT '5 %' WHERE x = ?") == "SELECT '5 %%' WHERE x = %s"


def test_other_sql_is_unchanged():
    sql = "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, correct INTEGER NOT NULL)"
    assert db.to_postgres(sql) == sql


def test_storage_modules_send_translated_sql_to_postgres(fake_postgres):
    with closing(db.connect()) as connection, connection:
        connection.execute("INSERT OR IGNORE INTO runs (id) VALUES (?)", ("r1",))
    sql, parameters = fake_postgres.last.statements[-1]
    assert sql == "INSERT INTO runs (id) VALUES (%s) ON CONFLICT DO NOTHING"
    assert parameters == ("r1",)


def test_leaving_the_with_block_commits_and_closing_closes(fake_postgres):
    with closing(db.connect()) as connection, connection:
        connection.execute("SELECT 1")
    assert fake_postgres.last.committed
    assert fake_postgres.last.closed


def test_an_error_rolls_back(fake_postgres):
    with pytest.raises(RuntimeError):
        with closing(db.connect()) as connection, connection:
            connection.execute("SELECT 1")
            raise RuntimeError("boom")
    assert fake_postgres.last.rolled_back
    assert not fake_postgres.last.committed


# --- Safety net: tests never see the real secrets file ---
# Streamlit copies root keys of .streamlit/secrets.toml into the environment
# as soon as it reads the file, which would overwrite the empty
# MATHBUDDY_DATABASE_URL set in conftest.py. So tests must not read that file.

REAL_SECRETS_FILE = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"


def test_tests_never_read_the_real_secrets_file():
    secrets_files = [Path(path).resolve() for path in config.get_option("secrets.files")]
    assert REAL_SECRETS_FILE not in secrets_files


def test_reading_streamlit_secrets_keeps_the_online_database_off(monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DATABASE_URL", "")
    st.secrets.load_if_toml_exists()
    online = db.database_url() is not None  # never show the URL itself in test output
    assert not online
