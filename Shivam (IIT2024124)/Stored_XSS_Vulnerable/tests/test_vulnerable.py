"""
Automated backend + database tests for the VULNERABLE build.

IMPORTANT LIMITATION: Flask's test client is NOT a browser. It never runs
JavaScript. These tests prove that
  (a) the payload is stored in SQLite unchanged, and
  (b) the server sends it back to the browser UNESCAPED (so a real browser would run it).
Whether the alert really pops up must be checked in a real browser
(manually, or with tests/test_browser_playwright.py).
"""
import os
import sqlite3

import app as app_module
import database

ESCAPED_PAYLOAD = "&lt;script&gt;alert(&#39;Stored XSS Successfully Executed&#39;);&lt;/script&gt;"


def post_comment(client, payload, username="mallory", post_id=1):
    return client.post(
        f"/post/{post_id}/comment",
        data={"username": username, "comment": payload},
    )


def test_application_starts_and_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Discussion posts" in response.data
    assert b"VULNERABLE BUILD" in response.data


def test_server_is_configured_for_localhost_only():
    assert app_module.HOST == "127.0.0.1"
    assert app_module.PORT == 5001


def test_database_schema_has_required_columns(flask_app, db_path):
    conn = sqlite3.connect(db_path)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(comments)")]
    conn.close()
    for required in ("id", "username", "comment", "created_at"):
        assert required in columns


def test_comment_submission_works(client, payload):
    response = post_comment(client, "Nice post!", username="dave")
    assert response.status_code == 302            # redirected back to the discussion
    page = client.get("/post/1")
    assert b"Nice post!" in page.data
    assert b"dave" in page.data


def test_comment_is_saved_in_sqlite(client, db_path):
    post_comment(client, "Saved to disk?", username="erin")
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT username, comment, created_at FROM comments WHERE username = 'erin'"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "erin"
    assert row[1] == "Saved to disk?"
    assert row[2]                                  # created_at was filled in


def test_comment_remains_after_refresh(client):
    post_comment(client, "I should still be here")
    first_visit = client.get("/post/1")
    second_visit = client.get("/post/1")           # "refresh"
    assert b"I should still be here" in first_visit.data
    assert b"I should still be here" in second_visit.data


def test_comment_survives_application_restart(db_path):
    first_run = app_module.create_app(db_path)
    first_run.test_client().post(
        "/post/1/comment", data={"username": "frank", "comment": "Persistent!"}
    )
    second_run = app_module.create_app(db_path)    # simulates stopping and restarting
    assert b"Persistent!" in second_run.test_client().get("/post/1").data


def test_exact_payload_is_stored_unchanged_in_sqlite(client, db_path, payload):
    post_comment(client, payload)
    conn = sqlite3.connect(db_path)
    stored = conn.execute(
        "SELECT comment FROM comments WHERE username = 'mallory'"
    ).fetchone()[0]
    conn.close()
    assert stored == payload                       # byte-for-byte identical


def test_payload_is_sent_to_browser_unescaped(client, payload):
    """This is the vulnerability: raw <script> reaches the browser as HTML."""
    post_comment(client, payload)
    html = client.get("/post/1").get_data(as_text=True)
    assert payload in html                         # raw, executable markup
    assert ESCAPED_PAYLOAD not in html             # NOT converted to harmless text


def test_stored_not_reflected_second_user_gets_payload(flask_app, payload):
    """Attacker and victim are two separate clients (two browser sessions)."""
    attacker = flask_app.test_client()
    victim = flask_app.test_client()
    post_comment(attacker, payload, username="attacker")
    # The victim sends no payload at all, yet receives it, because it is STORED.
    html = victim.get("/post/1").get_data(as_text=True)
    assert payload in html


def test_payload_keeps_being_served_on_every_visit(client, payload):
    post_comment(client, payload)
    for _ in range(3):
        assert payload in client.get("/post/1").get_data(as_text=True)


def test_unsafe_safe_filter_is_present_in_template():
    """Documents the root cause: the template marks the comment as trusted HTML."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates", "discussion.html",
    )
    with open(template_path, encoding="utf-8") as handle:
        source = handle.read()
    assert "c.comment | safe" in source
    assert "INTENTIONALLY VULNERABLE" in source


def test_empty_comment_is_rejected(client):
    response = post_comment(client, "   ", username="gina")
    assert response.status_code == 400


def test_reset_db_restores_sample_data(db_path, payload):
    flask_app = app_module.create_app(db_path)
    flask_app.test_client().post(
        "/post/1/comment", data={"username": "x", "comment": payload}
    )
    database.reset_db(db_path)
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM comments WHERE comment = ?", (payload,)).fetchone()[0]
    conn.close()
    assert count == 0
