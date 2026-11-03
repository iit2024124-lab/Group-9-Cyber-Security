# Stored XSS (Variant 1) – VULNERABLE "DevTalk" Developer Forum

> **Intentionally vulnerable.** Educational use only. Run on `127.0.0.1` (your own laptop). Never deploy it or expose it to a network.

## 1. Project title
**Stored Cross-Site Scripting (Variant 1) – Vulnerable Build** – Flask + SQLite discussion forum.

## 2. Assignment objective
Show how JavaScript submitted through a comment form is **stored in a database** and later **executes in another user's browser** when the discussion page is opened. The matching secured build (`Stored_XSS_Secured`) uses the **same payload** and the **same database schema**, but renders it harmlessly.

## 3. What is Stored XSS?
Cross-Site Scripting (XSS) lets an attacker make a victim's browser run attacker-controlled JavaScript *as if it came from the trusted site*. In **Stored (persistent) XSS** the malicious input is saved on the server (database, file, etc.) and sent to **every user** who later views that content. The attacker does not need to trick the victim into clicking a special link: opening the normal page is enough. (Reflected XSS bounces the payload straight back from the request; DOM-based XSS happens purely in client-side JavaScript.)

## 4. Technologies used
| Layer | Technology |
|---|---|
| Frontend | HTML, CSS (no client-side JavaScript of our own) |
| Backend | Python 3, Flask (Jinja2 templates) |
| Database | SQLite (single file, built into Python) |
| Tests | pytest; optional Playwright (real Chromium) |

## 5. Directory structure
```
Stored_XSS_Vulnerable/
├── app.py                  Flask routes (port 5001)
├── database.py             SQLite schema, seed data, reset/show commands
├── requirements.txt        Flask (only runtime dependency)
├── requirements-dev.txt    pytest (+ optional Playwright)
├── pytest.ini
├── templates/
│   ├── base.html           page layout + coloured build banner
│   ├── index.html          home page: list posts, create a post
│   ├── discussion.html     one post + comments  <-- THE VULNERABLE LINE IS HERE
│   └── not_found.html
├── static/style.css
├── screenshots/            put YOUR screenshots here (see CHECKLIST.md)
├── tests/
│   ├── conftest.py
│   ├── test_vulnerable.py          backend + database tests
│   └── test_browser_playwright.py  optional real-browser test
└── docs/ASSIGNMENT_REPORT.md       theory, comparison, video script, 30 viva Q&A, compliance map
```
`forum_vulnerable.db` is created automatically the first time you run the app.

## 6–8. Installation, virtual environment, dependencies (macOS)
Requires Python 3.9+ (`python3 --version`). From inside the project folder:
```bash
cd Stored_XSS_Vulnerable
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 9–10. Run it and open it
```bash
python3 app.py
```
Open **http://127.0.0.1:5001** (vulnerable build, **port 5001**).

> The two projects are **independent**. Run them in **separate terminals** if you want both at once: vulnerable on **5001**, secured on **5002**. Each has its own virtual environment and its own database file. (Port 5000 is avoided because macOS AirPlay Receiver often uses it.)

Stop the server with `Ctrl+C`.

## 11. Database
* File: **`forum_vulnerable.db`**, in the project folder (next to `app.py`). Created and filled with sample data automatically if missing.
* Table `comments`: `id`, `post_id`, `username`, `comment`, `created_at` (`post_id` links a comment to its post; the other four are the required columns). Table `posts`: `id`, `username`, `title`, `body`, `created_at`.
* Data **persists** across restarts.
* Look inside:
  ```bash
  sqlite3 forum_vulnerable.db "SELECT id, username, comment FROM comments;"
  # or, without the sqlite3 tool:
  python3 database.py show
  ```
* **Reset** for a fresh demonstration (stop the server first):
  ```bash
  python3 database.py reset
  ```

## 12. Exact exploit payload
```html
<script>alert('Stored XSS Successfully Executed');</script>
```
Copy it exactly. The secured build uses the identical string.

## 13. Step-by-step demonstration (two users)
1. Start the app (`python3 app.py`). **Screenshot 1:** home page at http://127.0.0.1:5001 (the **+** button at the top right opens the *Start a new discussion* side panel; 9 sample topics are pre-loaded).
2. **Browser A – the attacker** (e.g. normal Chrome window). Click **Open discussion** on *Welcome to DevTalk*.
3. Username `attacker`; paste the payload into **Comment**. **Screenshot 2:** form filled in. Click **Submit comment**.
4. You will see "Comment submitted successfully." **Screenshot 3.** (Browser A may also show the alert, since the attacker's own page runs it too. Click OK.)
5. Show the payload in the database (**Screenshot 4**):
   ```bash
   sqlite3 forum_vulnerable.db "SELECT id, username, comment FROM comments;"
   ```
6. **Browser B – the victim** (a *different* browser or a private/incognito window, so it is a separate session). Go to http://127.0.0.1:5001 (there is no login; type nothing) and click **Open discussion** on *Welcome to DevTalk*.
7. A dialog **"127.0.0.1:5001 says: Stored XSS Successfully Executed"** appears. **Screenshot 5.** The victim never submitted anything, so this is *stored*, not reflected.
8. Click OK, then **refresh** the page: the alert appears again every time, because the payload is still in SQLite.
9. Right-click → *View Page Source* and find the raw `<script>` line inside `comment-text`. **Screenshot 6 (code):** open `templates/discussion.html` and capture the `| safe` line.

If the alert does not appear: Chrome may have suppressed dialogs ("Prevent this page from creating additional dialogs") – close the tab and open a new one.

## 14. Expected output
* Attacker submission succeeds (HTTP 302 redirect, then the page loads).
* SQLite row contains the **unchanged** payload text.
* Victim's browser runs the script: alert text `Stored XSS Successfully Executed`.
* Alert repeats on every page load until you run `python3 database.py reset`.

## 15. Vulnerable code explanation
`templates/discussion.html`:
```jinja
{# INTENTIONALLY VULNERABLE: Stored XSS demonstration.
   User-controlled content is rendered without appropriate output encoding. #}
<div class="comment-text">{{ c.comment | safe }}</div>
```
`app.py` stores the comment exactly as typed (parameterised `INSERT`, so no SQL injection), reads it back with `SELECT`, and passes it to the template. The `| safe` filter tells Jinja2 "this string is trusted HTML – do not escape it".

Everything else (post titles, bodies, usernames) goes through normal `{{ ... }}` and **is** escaped, so the flaw is isolated to one rendering path.

## 16. Root cause
**Untrusted data (a comment written by another user) is output into an HTML page without output encoding.** The `| safe` filter disables Jinja2's auto-escaping, so the browser's HTML parser sees real `<script>` tags.

## 17. Mitigation (implemented in the other project)
Remove `| safe` so Jinja2 auto-escaping converts `< > & ' "` to `&lt; &gt; &amp; &#39; &#34;`. See `Stored_XSS_Secured/README.md`. Other defences (CSP, HttpOnly cookies, sanitizers, safe DOM sinks) are explained in `docs/ASSIGNMENT_REPORT.md`.

## 18. Testing
```bash
pip install -r requirements-dev.txt      # pytest (+ Playwright, optional)
python3 -m pytest -v                     # backend + database tests
```
* The **14 backend tests** use Flask's test client. It is **not a browser and never runs JavaScript**, so these tests prove the payload is *stored unchanged* and *sent unescaped*; they cannot prove an alert appears.
* **Real browser verification** is required: do the manual steps in section 13, or run the optional Playwright test:
  ```bash
  python3 -m playwright install chromium    # one-time download
  python3 -m pytest tests/test_browser_playwright.py -v
  ```
  If Playwright/Chromium is missing, that test is skipped automatically; the app never needs it.

## 19. Screenshots to capture
See `screenshots/CHECKLIST.md`. No screenshots are included; you must capture your own from your own run.

## 20. Viva preparation (quick list – 30 full answers in `docs/ASSIGNMENT_REPORT.md`)
1. Which exact line makes this app vulnerable, and why?
2. Why is this *stored* and not reflected XSS?
3. Why doesn't the Post/Redirect/Get redirect matter for the attack?
4. Why is storing the payload in SQLite essential to the demo?
5. Parameterised SQL is used. Why doesn't that stop XSS?
6. What origin does the injected script run in, and what can it access?
7. Would the payload work if the comment were inserted with `innerHTML`? (Hint: no for `<script>`; what would work instead?)
8. Why are usernames and post bodies *not* vulnerable here?
9. What would an attacker do beyond `alert()`?
10. Why is `debug=False` and `host=127.0.0.1` used?
11. Why can't the Flask test client verify execution?
12. What is the minimal change that fixes the bug, and where is it applied?

## Safety notes
Local only (`127.0.0.1`). No authentication or CSRF protection by design (out of scope for this assignment) – another reason never to deploy it.
