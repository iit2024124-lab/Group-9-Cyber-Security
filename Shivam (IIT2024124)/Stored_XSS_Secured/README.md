# Stored XSS (Variant 1) – SECURED "DevTalk" Developer Forum

> Secured version of the Stored XSS demo. Same application, same database schema, same payload. Educational use only; run on `127.0.0.1`.

## 1. Project title
**Stored Cross-Site Scripting (Variant 1) – Secured Build** – Flask + SQLite discussion forum with output encoding.

## 2. Assignment objective
Prove that **context-aware output encoding** (Jinja2 auto-escaping) stops the *exact same* Stored XSS payload from executing, **while still storing and displaying the user's original text**. The comment is *not* blocked at submission.

## 3. What is Stored XSS?
XSS makes a victim's browser run attacker-supplied JavaScript with the trusted site's origin. In **Stored XSS** the payload is saved server-side (here, SQLite) and delivered to every later visitor. Reflected XSS bounces from the request; DOM-based XSS happens in client-side JavaScript. This project shows the stored variant being neutralised.

## 4. Technologies used
Python 3 + Flask (Jinja2), SQLite, HTML/CSS, pytest, optional Playwright.

## 5. Directory structure
```
Stored_XSS_Secured/
├── app.py                  Flask routes (port 5002)
├── database.py             SQLite schema, seed data, reset/show commands
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── discussion.html     <-- THE FIX IS HERE: {{ c.comment }} (no |safe)
│   └── not_found.html
├── static/style.css
├── screenshots/            put YOUR screenshots here (see CHECKLIST.md)
├── tests/
│   ├── conftest.py
│   ├── test_secured.py
│   └── test_browser_playwright.py   optional real-browser test
└── docs/ASSIGNMENT_REPORT.md
```
`forum_secured.db` is created automatically on first run. It is a **different file** from the vulnerable build's database.

## 6–8. Installation, virtual environment, dependencies (macOS)
```bash
cd Stored_XSS_Secured
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 9–10. Run it and open it
```bash
python3 app.py
```
Open **http://127.0.0.1:5002** (secured build, **port 5002**).

> Run this project **independently** from the vulnerable one (vulnerable = **5001**, secured = **5002**). You can run both at once in two terminals, each with its own virtual environment. Stop with `Ctrl+C`.

## 11. Database
* File **`forum_secured.db`** next to `app.py`, auto-created with sample data. Persists across restarts.
* Schema identical to the vulnerable build (`comments`: `id`, `post_id`, `username`, `comment`, `created_at`; `posts`: `id`, `username`, `title`, `body`, `created_at`).
* Inspect: `sqlite3 forum_secured.db "SELECT id, username, comment FROM comments;"` or `python3 database.py show`
* Reset (stop server first): `python3 database.py reset`

## 12. Exact exploit payload (identical to the vulnerable build)
```html
<script>alert('Stored XSS Successfully Executed');</script>
```

## 13. Step-by-step demonstration
1. `python3 app.py`. **Screenshot 1:** home page at http://127.0.0.1:5002 (the **+** button at the top right opens the *Start a new discussion* side panel; 9 sample topics are pre-loaded) (green SECURED banner).
2. **Browser A (attacker):** open *Welcome to DevTalk*, username `attacker`, paste the payload into **Comment**. **Screenshot 2:** form filled. Click **Submit comment**. It is accepted ("Comment submitted successfully").
3. **Screenshot 3 (database):** the payload is stored *unchanged*:
   ```bash
   sqlite3 forum_secured.db "SELECT id, username, comment FROM comments;"
   ```
4. **Browser B (victim, a different browser or private window):** open http://127.0.0.1:5002 → *Welcome to DevTalk*.
5. The comment appears as **visible text** `<script>alert('Stored XSS Successfully Executed');</script>`. **Screenshot 4.** No alert.
6. **Refresh** the page several times. Still no alert. **Screenshot 5.**
7. *View Page Source*: the comment line is `&lt;script&gt;alert(&#39;Stored XSS Successfully Executed&#39;);&lt;/script&gt;`.
8. Open `templates/discussion.html` and capture the `{{ c.comment }}` line with its comment. **Screenshot 6.**

## 14. Expected output
* Payload accepted (HTTP 302), stored unchanged in SQLite, read back from SQLite.
* Browser shows the payload as ordinary text; **no JavaScript alert**, before or after refresh.
* HTML source contains `&lt;script&gt;…&lt;/script&gt;`, not a `<script>` element.

## 15. Secured code explanation
`templates/discussion.html`:
```jinja
{# SECURE: context-aware output encoding (HTML text context). #}
<div class="comment-text">{{ c.comment }}</div>
```
Flask enables Jinja2 auto-escaping for `.html` templates. `{{ ... }}` therefore replaces `& < > ' "` with `&amp; &lt; &gt; &#39; &#34;`. The browser's HTML parser sees only text characters, so no `<script>` element is created. `app.py` and `database.py` are the same as the vulnerable build apart from the port, labels, and database filename; **the stored data is not modified**.

## 16. Root cause (of the original bug)
Untrusted data was placed in an HTML page without output encoding (`| safe` disabled the escaping).

## 17. Mitigation explanation
**Implemented:** output encoding at the rendering layer, using Jinja2 auto-escaping for the HTML-text context. Not used: `| safe`, `markupsafe.Markup`, `render_template_string` with user data, or `autoescape` off. We deliberately do **not** rely on input validation or JavaScript filtering, and we do not block the comment.

**Limits (be ready to say this in the viva):** auto-escaping protects the *HTML text/quoted attribute contexts only*. It does not make `<script>` blocks, event-handler attributes, `href`/`src` URLs (`javascript:`), or CSS safe; it does not stop DOM XSS in client-side code; and the stored database value still contains the raw payload, so any other consumer that renders it unsafely would be vulnerable. Defence in depth (CSP, HttpOnly cookies, safe DOM sinks, sanitizers for rich HTML) is covered in `docs/ASSIGNMENT_REPORT.md` but **only output encoding is implemented here**.

## 18. Testing
```bash
pip install -r requirements-dev.txt
python3 -m pytest -v
```
* **18 backend tests** (Flask test client) verify: app starts, submission works, row saved in SQLite, persistence after refresh and restart, **exact payload stored unchanged**, response HTML contains the **escaped** payload and **no raw `<script>`**, auto-escaping enabled, no `| safe`/`Markup(` in the source.
* The test client **never executes JavaScript**, so it cannot prove "no alert". Verify in a real browser (section 13) or with the optional Playwright test (asserts the text is visible, no `<script>` element, no dialog):
  ```bash
  python3 -m playwright install chromium
  python3 -m pytest tests/test_browser_playwright.py -v
  ```
  It is skipped automatically if Playwright/Chromium is unavailable.

## 19. Screenshots to capture
See `screenshots/CHECKLIST.md`. None are included; capture your own.

## 20. Viva preparation (quick list – 30 full answers in `docs/ASSIGNMENT_REPORT.md`)
1. What single change fixes the bug, and why there rather than at input?
2. What exactly does Jinja2 do to `<`, `>`, `&`, `'`, `"`?
3. Why is the payload still stored raw in SQLite, and is that acceptable?
4. Why didn't we reject comments containing `<script>`? What goes wrong with blacklists?
5. When is Jinja2 auto-escaping *not* enough? Give three contexts.
6. How would you allow bold/italic comments safely?
7. How would a CSP have helped here, and what are its limits?
8. Would HttpOnly cookies have prevented this attack? Why not alone?
9. How would you fix the same bug if the comment were inserted via JavaScript?
10. What does `{{ x | tojson }}` solve?
11. How do you prove "no execution" given the test client can't run JS?
12. What other consumers of the database could still be at risk?
