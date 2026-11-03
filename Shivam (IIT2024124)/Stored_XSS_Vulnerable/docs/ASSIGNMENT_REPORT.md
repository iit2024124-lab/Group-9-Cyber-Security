# Stored XSS (Variant 1) – Assignment Report

This file is identical in both ZIPs. It covers: implementation walkthrough, security analysis, the comparison table, theory on other mitigations, the video script, 30 viva Q&A, and the requirement-to-evidence compliance map.

> **Note on the official assignment PDF:** the compliance map in section 8 is built from the requirements you wrote in your brief. If the official PDF has extra wording or deliverables (file names, report format, marking scheme), check them against this list.

---

## 1. Implementation walkthrough

| File | Role |
|---|---|
| `app.py` | Flask app factory `create_app(db_path)`. Routes: `GET /` (posts), `POST /post/new`, `GET /post/<id>` (discussion), `POST /post/<id>/comment`. Binds to `127.0.0.1`, port 5001 (vulnerable) / 5002 (secured), `debug=False`. |
| `database.py` | SQLite connection helper, `CREATE TABLE IF NOT EXISTS` schema, sample data, `reset_db()`, and a CLI (`python3 database.py reset|show`). All SQL is parameterised (`?`). |
| `templates/discussion.html` | **The only security-relevant difference.** Vulnerable: `{{ c.comment \| safe }}`. Secured: `{{ c.comment }}`. |
| `templates/base.html`, `index.html`, `not_found.html`, `static/style.css` | Identical UI in both builds (the banner colour/label differs so screenshots are unambiguous). |
| `tests/` | pytest backend tests + optional Playwright browser test. |

**Code path of the attack (vulnerable build)**

1. Form `POST /post/1/comment` → `add_comment()` in `app.py` reads `request.form["comment"]` and `strip()`s surrounding spaces only.
2. `INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)` stores the text unchanged.
3. Redirect (Post/Redirect/Get) → the browser makes a fresh `GET /post/1`.
4. `discussion()` runs `SELECT … FROM comments WHERE post_id = ?` and passes rows to `discussion.html`.
5. The template prints `{{ c.comment | safe }}` → raw `<script>…</script>` in the HTML.
6. Browser's HTML parser creates a `<script>` element and runs it in the page's origin.

**Differences between the two builds (exhaustive):** the `| safe` filter (the fix), port number, database filename, banner text/colour, explanatory comments, and the test files. `database.py` schema and all routes are the same.

**Design choices worth knowing for the viva**

* The flaw is isolated to one output path (comments). Usernames, post titles and bodies use normal escaped output in *both* builds.
* Escaping is **not** done on input in either build: the database always stores what the user typed. The fix belongs at output time because the correct encoding depends on where the data is printed.
* `comments` has the four required columns plus `post_id` (needed to attach a comment to a post).

---

## 2. Security analysis (the nine required questions)

**1. What is Cross-Site Scripting?** A class of injection flaw where an application includes untrusted data in a web page without proper encoding/validation for its context, so the victim's browser executes attacker-supplied script as if the trusted site had sent it.

**2. What is Stored XSS?** The payload is saved by the server (database, log, profile field…) and delivered to every user who views the affected content. It is "persistent", unlike reflected XSS (payload is in the request and echoed back immediately) or DOM-based XSS (the flaw is in client-side code that writes data into a dangerous sink).

**3. Why is it dangerous?** It needs no interaction beyond viewing a normal page; it hits every visitor, including administrators; and the script runs with the site's origin, so it can read page content, send same-origin requests as the user, read non-HttpOnly cookies and `localStorage`, capture keystrokes, rewrite the page (fake login forms), and spread itself (worm-like behaviour, as in the 2005 Samy/MySpace worm).

**4. Vulnerable code path?** See section 1: `add_comment()` → SQLite → `discussion()` → `{{ c.comment | safe }}`.

**5. Why does the payload execute?** `| safe` marks the string as trusted HTML, so Jinja2 skips escaping and writes `<script>alert('…');</script>` verbatim into the response body.

**6. How does the browser interpret it?** The HTML parser tokenises `<script>` as a start tag, creates a script element, collects the text until `</script>`, and executes it synchronously (a *parser-inserted* script). It runs in the origin `http://127.0.0.1:5001`, with access to that origin's DOM, storage and same-origin requests.

**7. Why is SQLite storage important?** It makes the attack *persistent*: the payload survives restarts and is served to every later visitor without being in their request. That is what distinguishes Stored from Reflected XSS, and it is why the alert repeats on each refresh until the database is reset.

**8. Why does output encoding prevent execution?** Encoding converts characters with special meaning in HTML (`<`, `>`, `&`, `'`, `"`) into entities (`&lt;`, `&gt;`, `&amp;`, `&#39;`, `&#34;`). The parser then sees *text* characters, not a tag start, so no element is created; the browser displays `<script>…` literally.

**9. Why is the same payload harmless in the secured build?** The stored bytes are identical, but the response contains `&lt;script&gt;alert(&#39;Stored XSS Successfully Executed&#39;);&lt;/script&gt;`. The same bytes are *data* instead of *code* because encoding happens at the output boundary.

### Comparison table

| Feature | Vulnerable Version | Secured Version |
|---|---|---|
| Comment storage | Persistent | Persistent |
| Database | SQLite (`forum_vulnerable.db`) | SQLite (`forum_secured.db`) |
| Rendering | Unsafe HTML rendering (`\| safe`) | Auto-escaped template rendering |
| Payload stored | Yes (unchanged) | Yes (unchanged) |
| Payload in HTML sent to browser | Raw `<script>…</script>` | `&lt;script&gt;…&lt;/script&gt;` |
| JavaScript executes | Yes | No |
| Security status | Vulnerable | Mitigated |

---

## 3. Other XSS mitigations (theory only – NOT implemented in this project)

**Implemented here:** context-aware output encoding through Jinja2 auto-escaping (items 1–2 below, HTML-text context). Items 3–6 are study material.

### 3.1 Context-aware output encoding
* **What:** Encode untrusted data according to the context where it is placed: HTML text, quoted HTML attribute, JavaScript string, URL, CSS.
* **How:** HTML text → entity-encode `& < > " '`. Quoted attribute → same, and always quote the attribute. JS context → serialise data safely (e.g. `{{ data | tojson }}` in Jinja) rather than string-pasting. URL parameter → percent-encode; URLs used in `href`/`src` also need a scheme allow-list (`http`, `https`, `mailto`) to block `javascript:`.
* **Helps:** Turns data into inert text in the context it is used.
* **Limits:** Wrong encoder for the context = still vulnerable (HTML-encoding inside `<script>` or an `onclick` handler does not make it safe). Easy to forget in one place.
* **Example:** `<p>Hello {{ name }}</p>` is safe; `<a href="{{ user_url }}">` is **not** safe unless the URL scheme is validated.

### 3.2 Framework auto-escaping
* **What:** The template engine applies HTML encoding to every `{{ variable }}` by default. Flask enables it for `.html`, `.htm`, `.xml`, `.xhtml`, `.svg` templates.
* **How:** Jinja2/MarkupSafe escape the value unless it is explicitly marked safe.
* **Helps:** Secure by default; this is the mechanism used in the secured build.
* **Limits:** HTML contexts only; it is bypassed by `| safe`, `Markup()`, `{% autoescape false %}`, or building HTML with string concatenation; it does not fix JS/URL/CSS contexts or client-side DOM XSS.
* **Example:** `{{ c.comment }}` (secure) vs `{{ c.comment | safe }}` (vulnerable).

### 3.3 HTML sanitisers (for rich HTML)
* **What:** Libraries (e.g. DOMPurify in the browser, `nh3` in Python) that parse HTML and keep only an allow-list of tags/attributes.
* **How:** Parse into a DOM, remove disallowed elements/attributes (`<script>`, `onerror=`, `javascript:` URLs), serialise the result.
* **Helps:** The right tool when users *must* submit formatting (bold, links, images), where escaping everything would destroy the feature.
* **Limits:** Complex; needs a strict allow-list and prompt library updates; historical bypasses exist (e.g. mutation XSS); sanitising for one context does not make the result safe in another. Prefer plain-text escaping when rich HTML is not required.
* **Example:** `nh3.clean(user_html, tags={"b", "i", "a"}, attributes={"a": {"href"}})`.

### 3.4 Content Security Policy (CSP)
* **What:** An HTTP response header telling the browser which script sources are allowed.
* **How:** E.g. `Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'`. Without `'unsafe-inline'`, inline `<script>` blocks and inline event handlers are refused, so our payload would be blocked even if injected. Nonces/hashes allow specific trusted inline scripts.
* **Helps:** Strong defence in depth; limits damage when an encoding bug slips through.
* **Limits:** Not a substitute for encoding. Misconfiguration (`'unsafe-inline'`, wildcard hosts, allow-listed hosts with JSONP/script gadgets) weakens it; it does not stop HTML injection used for defacement or phishing text; needs testing against legitimate inline scripts.
* **Example in Flask:** `response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"`.

### 3.5 HttpOnly cookies
* **What:** A `Set-Cookie` attribute that hides the cookie from `document.cookie`.
* **How:** The browser still sends it with requests, but JavaScript cannot read it.
* **Helps:** Stops an XSS payload from *stealing* the session cookie directly.
* **Limits:** **It does not prevent XSS.** The injected script still runs and can act *as the logged-in user* (send authenticated requests, read page data, change the DOM, log keystrokes). It protects one asset (the cookie), not the page. Also does not protect `localStorage` tokens.
* **Example:** `resp.set_cookie("session_id", value, httponly=True, secure=True, samesite="Lax")`. (This demo app has no login or cookies, so it is theory only.)

### 3.6 Safe DOM sinks
* **What:** In client-side JavaScript, choose APIs that treat data as text, not HTML/code.
* **How:** Prefer `element.textContent = data`, `document.createElement` + `setAttribute` (for safe attributes), and `createTextNode`. Avoid dangerous sinks: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `setTimeout("string")`, and assigning untrusted URLs to `location`/`href`/`src`. Trusted Types (a browser feature) can enforce this by blocking raw strings at dangerous sinks; check current browser support before relying on it.
* **Helps:** Prevents **DOM-based XSS**, which server-side escaping cannot catch.
* **Limits:** Developer discipline; third-party libraries may use unsafe sinks; does not help server-rendered HTML.
* **Example:** `div.textContent = comment;` (safe) vs `div.innerHTML = comment;` (unsafe).

### 3.7 What each defence stops (summary)

| Defence | Stops script execution from injected markup? | Role |
|---|---|---|
| Output encoding / auto-escaping | **Yes, in the matching context** (implemented here) | Primary fix |
| HTML sanitiser | Yes, if configured well, for rich HTML | Primary fix when HTML is required |
| CSP | Often (blocks inline/untrusted scripts) | Defence in depth |
| HttpOnly cookies | **No** | Limits cookie theft only |
| Safe DOM sinks | Yes for client-side (DOM) XSS | Primary fix for client code |

---

## 4. Testing report (what was actually run)

Environment: Linux sandbox, Python 3.13, Flask 3.1.3, pytest 9.1.1, Playwright 1.63.0 with Chromium (headless). Not run on macOS.

| Check | Vulnerable | Secured |
|---|---|---|
| `python3 -m pytest -v` (backend/DB tests) | 14 passed | 18 passed |
| Playwright real-Chromium test | 1 passed (alert fired twice: first visit and after reload, in a second browser context) | 1 passed (payload visible as text, no `<script>` element, no dialog, also after reload) |
| **Total** | **15 passed, 0 failed** | **19 passed, 0 failed** |
| Live server on `127.0.0.1:5001` / `:5002`, payload submitted with `curl` | Response held raw `<script>alert('Stored XSS Successfully Executed');</script>` | Response held `&lt;script&gt;alert(&#39;…&#39;);&lt;/script&gt;`, no raw script |
| SQLite row after submission | Payload stored unchanged | Payload stored unchanged (identical bytes) |
| Persistence after stopping and restarting the server | Payload still served | Escaped payload still served |
| `python3 database.py reset` | Works; payload removed | Works; payload removed |
| Separate database files | `forum_vulnerable.db` | `forum_secured.db` |

**Not verified in this sandbox (do these on your Mac):**
* `python3 -m venv .venv` + `pip install -r requirements.txt` from a fresh venv: the sandbox cannot reach PyPI, so tests ran with already-installed system packages. The requirement is only `Flask>=3.0`.
* Manual run in Chrome/Safari on macOS, and the screenshots. None were generated or included.

**Why browser verification is separate:** Flask's test client sends HTTP requests and returns text. It has no HTML engine or JavaScript engine, so it can only show *what the server sent*. Whether script executes is decided by the browser, hence the manual steps and the Playwright test.

---

## 5. Demonstration guide (short form)

Terminal 1: `cd Stored_XSS_Vulnerable && source .venv/bin/activate && python3 app.py` (port 5001).
Terminal 2: `cd Stored_XSS_Secured && source .venv/bin/activate && python3 app.py` (port 5002).
Payload (same for both): `<script>alert('Stored XSS Successfully Executed');</script>`

1. Attacker window → `http://127.0.0.1:5001/post/1` → username `attacker` → paste payload → Submit.
2. Victim window (private/different browser) → `http://127.0.0.1:5001/post/1` → alert fires; refresh → fires again.
3. `sqlite3 forum_vulnerable.db "SELECT id, username, comment FROM comments;"`.
4. Repeat steps 1–3 on port 5002 / `forum_secured.db`: text shown, no alert.
5. Between runs: `python3 database.py reset` (server stopped).

---

## 6. Video demonstration script (2–3 minutes)

Replace the bracketed items. Have both terminals, two browser windows (one private), and `discussion.html` open in an editor beforehand. Speaking at a normal pace, the spoken text below is roughly 2 min 30 s.

| Time | On screen | Say |
|---|---|---|
| 0:00–0:15 | Title / face | "Hello, I am [Name], roll number [Roll No], IIIT Allahabad. My assigned vulnerability is **Cross-Site Scripting, Stored XSS, Variant 1**. I built a Flask and SQLite discussion forum in a vulnerable and a secured version." |
| 0:15–0:35 | Editor: `templates/discussion.html` (vulnerable) | "Here is the vulnerable code. Comments are rendered with `{{ c.comment \| safe }}`. The `safe` filter turns off Jinja2 auto-escaping, so user input is treated as trusted HTML." |
| 0:35–1:05 | Terminal: `python3 app.py`; Browser A at `127.0.0.1:5001/post/1`; paste payload, submit | "I start the vulnerable app on port 5001. As the attacker I post this comment: `<script>alert('Stored XSS Successfully Executed');</script>`. The server saves it into SQLite exactly as typed." |
| 1:05–1:25 | Terminal: `sqlite3 forum_vulnerable.db "SELECT id, username, comment FROM comments;"` | "Here is the row in the database: the raw script tag is stored." |
| 1:25–1:45 | Browser B (private window) opens the post; alert appears; refresh; alert again | "Now a different user opens the page. They typed nothing, yet the alert runs, and it runs again on refresh because the payload is stored. That is Stored XSS: attacker script executing in the victim's browser in the site's origin." |
| 1:45–2:00 | Editor, point at line | "Root cause: untrusted data reaches the HTML output without encoding." |
| 2:00–2:25 | Secured app on 5002; same payload; DB query; page shows text; refresh | "In the secured build I removed `safe`, so Jinja2 auto-escaping encodes `<` and `>`. Same payload, same database row, but the browser shows it as plain text. No alert, even after refresh." |
| 2:25–2:50 | Editor: `{{ c.comment }}` line; optional View Source showing `&lt;script&gt;` | "This is context-aware output encoding at the rendering layer. I did not block the input." |
| 2:50–3:00 | Face / slide | "Other defences I studied but did not implement: Content Security Policy, HTML sanitisers for rich text, safe DOM sinks, and HttpOnly cookies, which limit cookie theft but do not stop XSS. Thank you." |

Commands to type on camera:
```bash
cd Stored_XSS_Vulnerable && source .venv/bin/activate && python3 app.py
sqlite3 forum_vulnerable.db "SELECT id, username, comment FROM comments;"
cd ../Stored_XSS_Secured && source .venv/bin/activate && python3 app.py
sqlite3 forum_secured.db "SELECT id, username, comment FROM comments;"
```
Tip: if the alert is suppressed by the browser, close the tab and open a new one. Reset between takes with `python3 database.py reset`.

---

## 7. Viva preparation – 30 questions

**XSS fundamentals**
1. **What is XSS?** Injection of attacker-controlled script into a page viewed by others, executing with the site's origin because the app failed to encode/validate untrusted data for its output context.
2. **Stored vs Reflected vs DOM-based?** Stored: payload saved server-side and served to later visitors. Reflected: payload in the request (URL/form) echoed immediately in the response. DOM-based: client-side JS reads attacker-controlled data (URL fragment, etc.) and writes it into a dangerous sink; the server may never see it.
3. **Why is this one Stored?** The victim's request contains no payload; the script comes from the database. It persists across restarts and repeats on each load.
4. **What can an attacker do besides `alert()`?** Read DOM content and non-HttpOnly cookies, send authenticated requests as the user, log keystrokes, show fake login forms, redirect, deface, self-propagate.
5. **Which origin does the script run in?** `http://127.0.0.1:5001`, the page's origin. Same-origin policy therefore *allows* the script to access that origin's data; SOP does not protect against XSS because the browser believes the code is the site's own.

**Browser behaviour**
6. **How does the browser decide to run the script?** The HTML parser sees a `<script>` start tag, builds a script element, and executes it when the closing tag is parsed.
7. **Would `<script>` work if inserted with `innerHTML`?** No: script elements inserted via `innerHTML` do not execute. But `<img src=x onerror=…>` would, which is why blacklisting `<script>` fails.
8. **Why does the secured page show the text instead?** The parser receives `&lt;script&gt;`, an entity that decodes to the *character* `<` in a text node, never a tag-open token.

**Database / flow**
9. **Why use SQLite here?** Built into Python, a single file, persistent, easy to inspect. Persistence is what makes the XSS "stored".
10. **Parameterised queries are used; why is XSS still possible?** They prevent SQL injection (data interpreted as SQL). XSS is a different sink: data interpreted as HTML in the output. Each sink needs its own defence.
11. **Where is the database and how do I reset it?** `forum_vulnerable.db` / `forum_secured.db` next to `app.py`; `python3 database.py reset`.
12. **What is Post/Redirect/Get and does it affect the attack?** After `POST` the server redirects to a `GET`. It prevents duplicate form submissions; the script runs on the later GET built from the database, which confirms it is not reflected.
13. **Why are the two databases separate?** So testing one build can't change the other; also each build's file name is set in `database.py`.

**Vulnerable code**
14. **Which line is vulnerable?** `{{ c.comment | safe }}` in `templates/discussion.html`.
15. **What does `| safe` do internally?** Wraps the string as `markupsafe.Markup`, a type Jinja2 treats as already-escaped HTML, so it is not escaped again.
16. **Why not fix it in `add_comment()`?** You *can* sanitise at input, but encoding depends on the output context, and input filters/blacklists are fragile. The robust fix is at the output boundary; input validation is an additional layer.

**Secured code**
17. **What exactly changed?** Removed `| safe`; `{{ c.comment }}` is auto-escaped.
18. **What characters does Jinja2 escape?** `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`, `'`→`&#39;`, `"`→`&#34;`.
19. **How do I know auto-escaping is on?** Flask enables it for `.html` templates; the test `test_jinja_autoescape_is_enabled_for_templates` checks it, and the response HTML shows entities.
20. **Why keep the raw payload in the database?** Storing original data and encoding on output preserves information and supports multiple output contexts. The downside: any other consumer must also encode.

**Context-aware encoding and limits**
21. **What does "context-aware" mean?** The encoding must match the context: HTML text, attribute, JS, URL, CSS each need different rules.
22. **Name three situations where Jinja2 auto-escaping alone is insufficient.** (a) Inside `<script>` blocks: use `| tojson`. (b) `href`/`src` with user URLs: validate scheme (`javascript:`). (c) Unquoted attributes or inline event handlers like `onclick="…"`; also CSS contexts and client-side DOM sinks.
23. **What are the limitations of your implemented mitigation?** Only HTML-text/quoted-attribute contexts; breaks if someone later adds `| safe`; no protection against DOM XSS or against other consumers of the raw data; no rich-text support; no defence in depth (CSP etc.).

**Other mitigations**
24. **How does CSP help, and can it replace escaping?** It blocks inline/untrusted scripts so many payloads would be refused even if injected. It cannot replace escaping: misconfiguration or allow-listed gadgets weaken it, and it doesn't stop HTML-injection defacement.
25. **Do HttpOnly cookies stop XSS?** No. They stop JavaScript *reading* that cookie. The script can still perform actions as the user and read page data.
26. **When would you use a sanitiser instead of escaping?** When users legitimately submit HTML (rich text). Use an allow-list sanitiser (DOMPurify, `nh3`); escape everything otherwise.
27. **What are safe vs unsafe DOM sinks?** Safe: `textContent`, `createTextNode`, `setAttribute` on safe attributes. Unsafe: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, string `setTimeout`, untrusted `location`/`href`.

**Testing**
28. **Why can't your pytest tests prove the alert fires/doesn't fire?** The Flask test client has no browser engine or JS engine; it only checks the HTML text. Use a real browser or Playwright for execution.
29. **How did you prove the fix works with the identical payload?** Same string submitted in both builds; DB rows identical; response HTML differs (raw vs `&lt;…&gt;`); Playwright/manual browser shows alert only in vulnerable build.

**Challenge follow-ups**
30. **"If I change the secured template to `<div onclick="show('{{ c.comment }}')">`, is it still safe?"** No. HTML-escaping does not protect JavaScript string context: the attribute value is HTML-decoded *before* the JS runs, so a payload like `');alert(1);//` can break out. Use `data-` attributes read via `dataset`, or `| tojson` in a proper JS context, plus CSP.

---

## 8. Assignment compliance checklist (against your brief)

| # | Requirement (brief section) | Where it is satisfied |
|---|---|---|
| 1 | Two separate ZIPs, independently runnable (§1) | `Stored_XSS_Vulnerable.zip`, `Stored_XSS_Secured.zip`; separate ports 5001/5002, separate DB files, no shared code |
| 2 | Forum: home page, create post, comments, persistent, usernames, clean UI (§2) | `app.py`, `templates/index.html`, `discussion.html`, `static/style.css` |
| 3 | Flask + SQLite + HTML/CSS/JS stack, runs on macOS (§3) | `requirements.txt` (Flask only), README §6–10. No custom client-side JS is needed |
| 4 | Vulnerable: stored via SQLite, retrieved, rendered unsafely, clearly commented (§4A–B) | `templates/discussion.html` (`\| safe` + INTENTIONALLY VULNERABLE comment); `app.py` header and `add_comment()` comments |
| 5 | Exact payload `<script>alert('Stored XSS Successfully Executed');</script>`, executes on open/refresh (§4C) | Payload in READMEs §12, `tests/conftest.py`, `tests/test_vulnerable.py`; browser proof in `tests/test_browser_playwright.py` |
| 6 | Two-user demonstration instructions (§4C) | Vulnerable README §13; this report §5 |
| 7 | Secured: output encoding, auto-escape, no `\| safe`, no `Markup()`, payload stored but not executed, not blocked (§5) | Secured `templates/discussion.html` `{{ c.comment }}`; `test_no_unsafe_rendering_in_source_code`, `test_exact_same_payload_is_stored_unchanged_in_sqlite` |
| 8 | Same payload on secured build; displayed as text; no alert after refresh (§5B) | Secured README §13–14; `test_payload_is_sent_to_browser_as_escaped_text`; Playwright test |
| 9 | SQLite schema (id, username, comment, created_at), auto-init, sample data, location explained, reset, separate DBs (§6) | `database.py` (`SCHEMA`, `init_db`, `seed_sample_data`, `reset_db`); READMEs §11. `post_id` column added to link comments to posts |
| 10 | Security comparison: nine explanations + table (§7) | This report §2 |
| 11 | Other mitigations theory incl. HttpOnly caveat (§8) | This report §3 |
| 12 | Project structure (§9) | READMEs §5 |
| 13 | Automated tests for both; explanation that the test client doesn't run JS; optional Playwright (§10) | `tests/test_vulnerable.py` (14), `tests/test_secured.py` (18), `tests/test_browser_playwright.py` in each; READMEs §18; report §4. Playwright is only in `requirements-dev.txt` |
| 14 | README with all 20 sections, macOS commands (§11) | `README.md` in each project |
| 15 | Screenshot folders and checklists, no fabricated screenshots (§12) | `screenshots/CHECKLIST.md` in each; **no screenshots exist: you must capture them** |
| 16 | 2–3 minute video script with commands (§13) | This report §6 (you must record the video) |
| 17 | ≥25 viva questions with answers incl. challenge follow-ups (§14) | This report §7 (30 questions) |
| 18 | Code quality: complete, commented, localhost only, no unrelated vulnerabilities, `debug=False` (§15) | `app.py` (`HOST = "127.0.0.1"`, `debug=False`), parameterised SQL. Demo has no authentication/CSRF protection by design; do not deploy |
| 19 | Final validation actually executed (§16) | Testing report in section 4 above, with the items that could not be verified |
