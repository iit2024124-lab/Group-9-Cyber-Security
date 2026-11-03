"""Shared test setup. Every test gets its own temporary database."""
import pytest

import app as app_module

# The exact payload required by the assignment (same string in both projects).
PAYLOAD = "<script>alert('Stored XSS Successfully Executed');</script>"


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_forum.db")


@pytest.fixture
def flask_app(db_path):
    flask_app = app_module.create_app(db_path)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def payload():
    return PAYLOAD
