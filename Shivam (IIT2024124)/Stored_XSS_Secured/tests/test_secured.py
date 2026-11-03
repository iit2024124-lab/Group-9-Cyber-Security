"""
Automated backend + database tests for the SECURED build.

IMPORTANT LIMITATION: Flask's test client is NOT a browser. It never runs
JavaScript, so it can never show an alert. These tests prove that
  (a) the exact same payload is stored in SQLite unchanged, and
  (b) the server sends it to the browser HTML-ESCAPED (so a real browser shows
      it as text and has no <script> tag to run).
That the alert really does NOT appear must be confirmed in a real browser
(manually, or with tests/test_browser_playwright.py).
"""
import os
import sqlite3

import app as app_module
import database

# What Jinja2 auto-escaping produces for the payload.
ESCAPED_PAYLOAD = "&lt;script&gt;alert(&#39;Stored XSS Successfully Executed&#39;);&lt;/script&gt;"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def post_comment(client, payload, username="mallory", post_id=1):
    return client.post(
        f"/post/{post_id}/comment",
        data={"username": username, "comment": payload},
    )


def test_application_starts_and_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Discussion posts" in response.data
    assert b"SECURED BUILD" in response.data


def test_server_is_configured_for_localhost_only():
    assert app_module.HOST == "127.0.0.1"
    assert app_module.PORT == 5002


def test_secured_build_uses_its_own_database_file():
    assert database.DEFAULT_DB_PATH.endswith("forum_secured.db")


def test_database_schema_has_required_columns(flask_app, db_path):
    conn = sqlite3.connect(db_path)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(comments)")]
    conn.close()
    for required in ("id", "username", "comment", "created_at"):
        assert required in columns


def test_comment_submission_works(client):
    response = post_comment(client, "Nice post!", username="dave")
    assert response.status_code == 302
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
    assert row[1] == "Saved to disk?"
    assert row[2]


def test_comment_remains_after_refresh(client):
    post_comment(client, "I should still be here")
    assert b"I should still be here" in client.get("/post/1").data
    assert b"I should still be here" in client.get("/post/1").data


def test_comment_survives_application_restart(db_path):
    first_run = app_module.create_app(db_path)
    first_run.test_client().post(
        "/post/1/comment", data={"username": "frank", "comment": "Persistent!"}
    )
    second_run = app_module.create_app(db_path)
    assert b"Persistent!" in second_run.test_client().get("/post/1").data


def test_exact_same_payload_is_stored_unchanged_in_sqlite(client, db_path, payload):
    """The fix is at OUTPUT time, so the database still holds the original text."""
    response = post_comment(client, payload)
    assert response.status_code == 302                 # submission is NOT blocked
    conn = sqlite3.connect(db_path)
    stored = conn.execute(
        "SELECT comment FROM comments WHERE username = 'mallory'"
    ).fetchone()[0]
    conn.close()
    assert stored == payload


def test_payload_is_sent_to_browser_as_escaped_text(client, payload):
    """No raw <script> reaches the browser; it receives harmless entities."""
    post_comment(client, payload)
    html = client.get("/post/1").get_data(as_text=True)
    assert ESCAPED_PAYLOAD in html                     # displayed as text
    assert payload not in html                         # raw executable markup absent
    assert "<script>alert(" not in html                # no script tag from user data


def test_page_has_no_script_tags_at_all(client, payload):
    """The templates contain no <script> of their own, so any <script> would be an injection."""
    post_comment(client, payload)
    html = client.get("/post/1").get_data(as_text=True).lower()
    assert "<script" not in html


def test_second_user_sees_harmless_text(flask_app, payload):
    attacker = flask_app.test_client()
    victim = flask_app.test_client()
    post_comment(attacker, payload, username="attacker")
    html = victim.get("/post/1").get_data(as_text=True)
    assert ESCAPED_PAYLOAD in html
    assert payload not in html


def test_payload_stays_harmless_on_every_visit(client, payload):
    post_comment(client, payload)
    for _ in range(3):
        html = client.get("/post/1").get_data(as_text=True)
        assert ESCAPED_PAYLOAD in html
        assert payload not in html


def test_username_is_also_escaped(client):
    post_comment(client, "hi", username="<b>bold</b>")
    html = client.get("/post/1").get_data(as_text=True)
    assert "&lt;b&gt;bold&lt;/b&gt;" in html
    assert "<b>bold</b>" not in html


def test_jinja_autoescape_is_enabled_for_templates(flask_app):
    assert flask_app.jinja_env.autoescape("discussion.html")


def test_no_unsafe_rendering_in_source_code():
    """Guards the mitigation: no |safe filter and no Markup() on user data."""
    for folder, extension in (("templates", ".html"), (".", ".py")):
        directory = os.path.join(PROJECT_DIR, folder)
        for name in os.listdir(directory):
            if not name.endswith(extension):
                continue
            with open(os.path.join(directory, name), encoding="utf-8") as handle:
                source = handle.read()
            # Comments in the files mention these words, so look for real usages.
            assert "| safe }}" not in source and "|safe }}" not in source, name
            assert "Markup(" not in source, name
            assert "render_template_string" not in source, name
            assert "autoescape false" not in source.lower(), name


def test_empty_comment_is_rejected(client):
    assert post_comment(client, "   ", username="gina").status_code == 400


def test_reset_db_removes_payload(db_path, payload):
    flask_app = app_module.create_app(db_path)
    flask_app.test_client().post(
        "/post/1/comment", data={"username": "x", "comment": payload}
    )
    database.reset_db(db_path)
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM comments WHERE comment = ?", (payload,)).fetchone()[0]
    conn.close()
    assert count == 0
