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


