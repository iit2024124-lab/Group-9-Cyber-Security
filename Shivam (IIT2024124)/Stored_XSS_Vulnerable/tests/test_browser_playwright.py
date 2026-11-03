"""
OPTIONAL real-browser test (Playwright + Chromium) for the VULNERABLE build.

This is the only test that proves JavaScript really runs. It is skipped
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
EXPECTED_ALERT_TEXT = "Stored XSS Successfully Executed"


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


def test_stored_xss_alert_fires_for_a_second_user(live_url, browser):
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
    assert alerts == [EXPECTED_ALERT_TEXT]            # script ran on first visit

    victim_page.reload()                              # still stored -> runs again
    assert alerts == [EXPECTED_ALERT_TEXT] * 2
