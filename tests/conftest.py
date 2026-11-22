"""Shared test setup.

Two safety nets for every test:
- Tests never touch the online database, even when `.streamlit/secrets.toml`
  holds the real connection string: MATHBUDDY_DATABASE_URL is set to empty,
  and the app only copies the secret when the variable is not set at all.
- Since spec 011 the app shows a sign in screen first. Every test that opens
  the app with `AppTest.from_file` starts with TEST_USER signed in, so the
  screen tests written before 011 keep working unchanged. Tests marked
  `@pytest.mark.signed_out` start without a user.
"""

from datetime import datetime, timezone

import pytest
from streamlit.testing.v1 import AppTest

from accounts import User

TEST_USER = User(
    id="test-user",
    username="tester",
    email="tester@example.com",
    password_hash="not-a-real-hash",
    created_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
)


def pytest_configure(config):
    config.addinivalue_line("markers", "signed_out: open the app without a signed in user")


@pytest.fixture(autouse=True)
def never_use_the_online_database(monkeypatch):
    monkeypatch.setenv("MATHBUDDY_DATABASE_URL", "")


@pytest.fixture(autouse=True)
def signed_in_by_default(request, monkeypatch):
    if request.node.get_closest_marker("signed_out"):
        return

    original = AppTest.from_file

    def from_file(*args, **kwargs):
        at = original(*args, **kwargs)
        at.session_state["user"] = TEST_USER
        return at

    monkeypatch.setattr(AppTest, "from_file", from_file)
