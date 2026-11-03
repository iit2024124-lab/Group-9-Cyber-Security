# CSRF – GET-based forged action (Web Server Security Assignment)


## Project structure

```
csrf-assignment/
├── vulnerable/   server.js + views/{login,profile}.html   -> http://localhost:3000
├── attacker/     attacker.html + server.js                -> http://127.0.0.1:4000
├── secured/      server.js + views/{login,profile}.html   -> http://localhost:3001
├── package.json
└── README.md
```











No `npm install` needed: only built-in Node.js modules are used (Node 16+).

## How to run

Open three terminals in the project folder:

```bash
node vulnerable/server.js    # Version 1, port 3000
node secured/server.js       # Version 2, port 3001
node attacker/server.js      # attacker site, port 4000
```

Demo users: `alice / alice123`, `bob / bob123`.

## Demonstration steps

**Exploit (vulnerable app)**
1. Open `http://localhost:3000`, log in as alice. Theme is **light**.
2. In the *same browser*, open a new tab: `http://127.0.0.1:4000` (the attacker's "prize" page).
   Using `127.0.0.1` instead of `localhost` makes it a genuinely different site.
3. Click **Claim prize** → browser navigates to `http://localhost:3000/profile/theme?value=dark`,
   sends alice's session cookie, and the server changes the theme to **dark**.
4. Show the server console line `>>> theme of "alice" changed to "dark"`.

**Mitigation (secured app)**
1. Open `http://localhost:3001`, log in as alice. Theme is **light**.
2. On the attacker page click **Claim prize (secured target)** (same forged GET).
3. Result: `405 Method Not Allowed`, theme unchanged, console shows `BLOCKED`. Take a screenshot.
4. Show that the real profile page still works: its buttons send `POST /profile/theme`.

## (a) Vulnerable implementation
`vulnerable/server.js`, block `GET /profile/theme` – it changes `users[user].theme` on a GET request.

## (b) Working exploit
```html
<a href="http://localhost:3000/profile/theme?value=dark">Claim prize</a>
```
(in `attacker/attacker.html`). A top-level link navigation is used because browsers restrict
cookies on cross-site sub-requests such as `<img>`; Chrome's default `SameSite=Lax` still sends
cookies on top-level GET navigations, which is why this attack works.

## (c) Root cause
The server authenticates the request only by the session cookie, which the browser attaches
automatically, and it performs a state change on a GET request. Nothing proves the user
*intended* the action (no token, no POST, no origin check).

## (d) Mitigation implemented: avoid state-changing GET requests
`secured/server.js`:
- `GET /profile/theme` now returns **405 Method Not Allowed** and changes nothing.
- The theme is changed only by `POST /profile/theme`, sent by forms on the site's own profile page.
- Extra (defence in depth): the session cookie is set with `SameSite=Lax`, so it is also not
  sent on cross-site POSTs.

## (e) Other mitigations (theory)
- **Anti-CSRF (synchronizer) tokens:** the server puts an unpredictable per-session (or per-request)
  token in each form and checks it on every state-changing request. A malicious site can make the
  browser send the cookie but cannot read or guess the token (same-origin policy), so the forged
  request is rejected.
- **SameSite cookies:** `SameSite=Strict` (or `Lax`) tells the browser not to attach the session
  cookie to requests started by other sites, so forged requests arrive unauthenticated. `Strict`
  blocks even top-level link clicks; `Lax` blocks cross-site POST/sub-requests but allows top-level GET,
  which is why GET must never change state.
- **Re-authentication for sensitive actions:** asking for the password / OTP before critical actions
  (change email, transfer money) means an attacker's forged request cannot supply the secret.
- **Avoiding state-changing GET requests** (implemented here): GET must be safe/idempotent, because
  links, images and prefetchers can trigger GETs without user intent.

Note: moving to POST alone does not stop an auto-submitting form (the *POST-based* CSRF variant);
that needs tokens and/or SameSite, as described above.

## Viva quick answers
- *Why does the attack work?* Browser auto-attaches cookies; server trusts the cookie alone.
- *Why not `<img src=...>`?* Cross-site sub-requests don't get Lax cookies; top-level navigation does.
- *Why is the secured version safe from the link?* The only handler for GET is a 405; the change
  needs a POST, which a cross-site link click cannot produce.
- *Is POST enough?* No – an attacker can auto-submit a form; add tokens / SameSite.
