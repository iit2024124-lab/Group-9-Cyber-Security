"""
OPTIONAL real-browser test (Playwright + Chromium) for the SECURED build.

This is the only test that proves JavaScript really does NOT run. It is skipped
automatically if Playwright or its browser is not installed, so the normal test
suite and the application itself never depend on it.

Setup (once):
    pip install -r requirements-dev.txt
    python3 -m playwright install chromium
Run:
    python3 -m pytest tests/test_browser_playwright.py -v
"""
import threading

import pytest

sync_api = pytest.importorskip("playwright.sync_api")
from werkzeug.serving import make_server  # noqa: E402

import app as app_module  # noqa: E402

PAYLOAD = "<script>alert('Stored XSS Successfully Executed');</script>"


@pytest.fixture
def live_url(tmp_path):
    """Start the real Flask app on a free localhost port with a throw-away database."""
    flask_app = app_module.create_app(str(tmp_path / "browser_test.db"))
    server = make_server("127.0.0.1", 0, flask_app)   # port 0 = pick any free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def browser():
    with sync_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception as error:  # browser binary not installed
            pytest.skip(f"Chromium is not available for Playwright: {error}")
        yield browser
        browser.close()


def test_payload_is_shown_as_text_and_does_not_execute(live_url, browser):
    # Browser context 1 = the attacker. Browser context 2 = the victim (separate session).
    attacker = browser.new_context().new_page()
    attacker.goto(f"{live_url}/post/1")
    attacker.fill("input[name=username]", "attacker")
    attacker.fill("textarea[name=comment]", PAYLOAD)
    attacker.click("button:has-text('Submit comment')")

    victim_page = browser.new_context().new_page()
    alerts = []

    def on_dialog(dialog):
        alerts.append(dialog.message)
        dialog.accept()

    victim_page.on("dialog", on_dialog)
    victim_page.goto(f"{live_url}/post/1")

    # 1) The payload is visible as plain text on the page.
    shown = victim_page.inner_text("#comments")
    assert PAYLOAD in shown
    # 2) No <script> element was created from the comment.
    assert victim_page.locator("#comments script").count() == 0
    # 3) No alert dialog appeared, including after a refresh.
    victim_page.reload()
    assert PAYLOAD in victim_page.inner_text("#comments")
    assert alerts == []
