# Group 9 – Web Server Security Assignment

**Indian Institute of Information Technology Allahabad**
Department of Information Technology
**Cyber Security (IT-30001) | Autumn Semester 2026**
Instructor: Dr. Soumyadev Maity

**Assignment:** Exploitation and Mitigation of Four Vulnerability Categories
(SQL injection, OS command injection, Cross-Site Scripting, Cross-Site Request Forgery)

> **Educational use only.** Every application in this repository is intentionally vulnerable and binds to `127.0.0.1`. Run them only on your own machine. Never deploy them publicly or test systems you do not own.

---

## 1. Video demonstration

Group video (screen recording with voice-over, each member narrates their own variant):

**[Google Drive folder – Group 9 demo video](https://drive.google.com/drive/u/1/folders/1UqiPTHgZ4gHbqMFIInNPc-ukGVCcjbTj)**

---

## 2. Ownership declaration (Table 3)

| S. No. | Member name | Roll number | Category | Variant implemented |
|:---:|---|---|---|---|
| 1 | Atharva | IIT2024192 | SQL injection | Authentication bypass |
| 2 | Aditya | IIT2024205 | OS command injection | In-band (command output returned) |
| 3 | Shivam | IIT2024124 | Cross-Site Scripting (XSS) | Stored XSS |
| 4 | Anurag | IIT2024156 | Cross-Site Scripting (XSS) | Reflected XSS |
| 5 | Arun | IIT2024157 | Cross-Site Request Forgery (CSRF) | GET-based forged action |

**Note on group size:** our group has five members. As the assignment allows for groups of more than four, two members implement the same category (XSS) with **mandatorily different variants** (Stored vs Reflected). All four categories are covered, and no two members implement the same variant.

---

## 3. Repository structure

```
Group-9-Cyber-Security/
├── README.md                          <- this file
├── Atharva (IIT2024192)/              SQL injection – authentication bypass
│   ├── SQL_Injection_Vulnerable/      port 8001
│   ├── SQL_Injection_Secured/         port 8002
│   └── Screenshots/
├── Aditya (IIT2024205)/               OS command injection – in-band
│   ├── OS COMMAND INJECTION/          /vulnerable and /safe routes, port 5000
│   └── Screenshot/
├── Shivam (IIT2024124)/               Stored XSS
│   ├── Stored_XSS_Vulnerable/         port 5001
│   ├── Stored_XSS_Secured/            port 5002
│   └── Screenshots/
├── anurag(IIT2024156)/                Reflected XSS
│   ├── app.py                         /search/vulnerable and /search/safe, port 5000
│   └── screenshots/
└── Arun(IIT2024157)/                  CSRF – GET-based
    ├── vulnerable/                    port 3000
    ├── secured/                       port 3001
    ├── attacker/                      attacker site, port 4000
    └── screenshots/
```

---

## 4. Summary of all variants (Table 2 items a–e)

### 4.1 SQL injection – Authentication bypass (Atharva, IIT2024192)

| Item | Details |
|---|---|
| **(a) Vulnerable code** | `authenticate()` in `SQL_Injection_Vulnerable/app.py` builds the query with an f-string: `SELECT ... WHERE username = '{username}' AND password = '{password}'` |
| **(b) Exploit** | Username `alex' -- ` (note the trailing space) with any password, e.g. `alex123` |
| **(c) Root cause** | User input is concatenated directly into the SQL string, so the quote closes the string and `-- ` comments out the password check. |
| **(d) Mitigation implemented** | **Parameterised query**: `WHERE username = ? AND password = ?` with values bound separately. The same payload is rejected. |
| **(e) Other mitigations (theory)** | **Allow-list input validation** restricts usernames to the expected characters and length (an extra layer, not a replacement). **Least-privilege DB accounts** limit damage if injection occurs. **Safe errors** return generic messages and keep DB diagnostics in protected logs so attackers cannot learn the schema. |

### 4.2 OS command injection – In-band (Aditya, IIT2024205)

| Item | Details |
|---|---|
| **(a) Vulnerable code** | `/vulnerable` route in `app.py`: `subprocess.run(f"ping -n 1 {host}", shell=True, ...)` |
| **(b) Exploit** | Windows: `127.0.0.1 & whoami`. Linux/macOS: `127.0.0.1; whoami`. The output of `whoami` is returned in the page. |
| **(c) Root cause** | User input is concatenated into a command string that is run through the shell, so shell metacharacters (`&`, `;`, `\|`) start a second command. |
| **(d) Mitigation implemented** | `/safe` route: **allow-list validation** (strict hostname/IPv4 regex) **plus an argument vector** with `shell=False`: `["ping", "-n", "1", host]`. The same payload is rejected. |
| **(e) Other mitigations (theory)** | **Avoid the shell** altogether (use a library/API call such as a native ping or DNS lookup instead of spawning a process). **Parameterised execution with an argument vector** passes each argument as a separate item so no shell parses the input. **Allow-list validation** accepts only known-good input shapes. **Least privilege** runs the web process under an account with minimal OS permissions, so a successful injection can do little. |

### 4.3 Stored XSS (Shivam, IIT2024124)

| Item | Details |
|---|---|
| **(a) Vulnerable code** | `templates/discussion.html` in `Stored_XSS_Vulnerable`: `{{ c.comment \| safe }}` |
| **(b) Exploit** | Post this as a comment: `<script>alert('Stored XSS Successfully Executed');</script>` |
| **(c) Root cause** | The comment is stored unchanged and rendered with the `\| safe` filter, so Jinja2 skips escaping and the browser executes the script for every visitor. |
| **(d) Mitigation implemented** | **Context-aware output encoding via Jinja2 auto-escaping**: `{{ c.comment }}`. The payload is still stored but displayed as harmless text. |
| **(e) Other mitigations (theory)** | **Framework auto-escaping** makes encoding the default. **HTML sanitiser** (DOMPurify, nh3) allow-lists safe tags when rich HTML is needed. **Content Security Policy** blocks inline scripts even if injection occurs. **HttpOnly cookies** stop scripts from reading session cookies (limits damage, does not prevent XSS). **Safe DOM sinks** (`textContent` instead of `innerHTML`) prevent DOM-based XSS. |

### 4.4 Reflected XSS (Anurag, IIT2024156)

| Item | Details |
|---|---|
| **(a) Vulnerable code** | `/search/vulnerable` in `app.py`: `query_display = query` (the `?q=` parameter is placed into the HTML unencoded). |
| **(b) Exploit** | `/search/vulnerable?q=<script>alert('XSS')</script>` |
| **(c) Root cause** | Input from the request is reflected into the response without output encoding, so the browser parses it as markup and runs it. |
| **(d) Mitigation implemented** | `/search/safe`: **output encoding** with `html.escape(query)`. The same URL now shows the payload as plain text. |
| **(e) Other mitigations (theory)** | **Framework auto-escaping** (Jinja2 `{{ var }}`), **HTML sanitiser** (DOMPurify/Bleach) for rich content, **CSP** to block inline script execution, **HttpOnly cookies** to protect session cookies, and **safe DOM sinks** (`textContent`). |

### 4.5 CSRF – GET-based forged action (Arun, IIT2024157)

| Item | Details |
|---|---|
| **(a) Vulnerable code** | `vulnerable/server.js`, handler for `GET /profile/theme`, which changes the user's theme on a GET request. |
| **(b) Exploit** | The attacker page (`attacker/attacker.html`) contains `<a href="http://localhost:3000/profile/theme?value=dark">Claim prize</a>`. A logged-in victim who clicks it has their theme changed. |
| **(c) Root cause** | The server trusts the session cookie alone (the browser attaches it automatically) and performs a state change on a GET, with no proof the user intended the action. |
| **(d) Mitigation implemented** | **Avoid state-changing GET requests**: `GET /profile/theme` returns **405 Method Not Allowed**; the change is only accepted via `POST`. The session cookie also carries `SameSite=Lax`. |
| **(e) Other mitigations (theory)** | **Anti-CSRF (synchronizer) tokens**: unpredictable per-session token checked on every state-changing request; attackers cannot read it because of the same-origin policy. **SameSite cookies**: the browser withholds the cookie on cross-site requests. **Re-authentication** for sensitive actions: a password/OTP the attacker cannot supply. |

---

## 5. How to run each project

Each project is independent. Prerequisites: **Python 3.9+** (for the Flask apps) and **Node.js 16+** (for the CSRF demo).

> Anurag's and Aditya's apps both use port 5000, so run them one at a time.

### SQL injection (Atharva)
```bash
cd "Atharva (IIT2024192)/SQL_Injection_Vulnerable"
python app.py            # http://127.0.0.1:8001

cd "../SQL_Injection_Secured"
python app.py            # http://127.0.0.1:8002
```
Exploit: username `alex' -- ` with password `alex123`. Valid login: `alex` / `Maison!26`.
Tests: `python -m unittest discover -s tests -v`

### OS command injection (Aditya)
```bash
cd "Aditya (IIT2024205)/OS COMMAND INJECTION"
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000  (/vulnerable and /safe)
```

### Stored XSS (Shivam)
```bash
cd "Shivam (IIT2024124)/Stored_XSS_Vulnerable"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py           # http://127.0.0.1:5001

cd "../Stored_XSS_Secured"       # use its own virtual environment
pip install -r requirements.txt
python3 app.py           # http://127.0.0.1:5002
```
Tests: `pip install -r requirements-dev.txt && pytest`

### Reflected XSS (Anurag)
```bash
cd "anurag(IIT2024156)"
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000  (vulnerable and mitigated pages)
```
(`run.sh` / `run.bat` are also provided.)

### CSRF (Arun)
No `npm install` needed (built-in Node modules only). Open three terminals:
```bash
cd "Arun(IIT2024157)"
node vulnerable/server.js    # http://localhost:3000
node secured/server.js       # http://localhost:3001
node attacker/server.js      # http://127.0.0.1:4000
```
Demo users: `alice / alice123`, `bob / bob123`. Log in as alice, then open the attacker page in the same browser and click **Claim prize**. Use `127.0.0.1` for the attacker so it is a genuinely different site from `localhost`.

---

## 6. Evidence

Screenshots of the working exploit and the blocked attempt (same payload) are in each member's screenshots folder:

- `Atharva (IIT2024192)/Screenshots/`
- `Aditya (IIT2024205)/Screenshot/`
- `Shivam (IIT2024124)/Screenshots/`
- `anurag(IIT2024156)/screenshots/`
- `Arun(IIT2024157)/screenshots/`

---

## 7. Viva readiness

Each member can demonstrate their own variant live and explain: the vulnerable code path, the exact payload, the root cause, the one mitigation they implemented, and the theory of the alternative mitigations listed above.

## 8. Academic integrity

All code and exploits in this repository are the group's own work. Testing was done only against our own applications running on `127.0.0.1`.
