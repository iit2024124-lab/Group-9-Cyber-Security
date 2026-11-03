# SQL Injection: Authentication Bypass

Name: Atharva  
Roll number: IIT2024192

## Application
Maison is a small home essentials account page. The login checks a users table in SQLite and returns the customer's name and email if a record matches. The database uses sample accounts and is created in memory for each request.

## Vulnerable query
In app.py, authenticate() uses this line:
```python
row = db.execute(f"SELECT id, username, name, email FROM users WHERE username = '{username}' AND password = '{password}'").fetchone()
```
The username and password are inserted directly into the SQL string. This lets input change the query itself.

## Login attempts
| Username | Password | Vulnerable | Secured |
|---|---|---|---|
| alex | alex123 | Rejected | Rejected |
| alex' -- | alex123 | Logged in as Alex | Rejected |
| alex | Maison!26 | Logged in as Alex | Logged in as Alex |

The attack username is `alex' -- `, with a space after the hyphens.

The resulting query in the vulnerable version is:
```sql
SELECT id, username, name, email FROM users WHERE username = 'alex' -- ' AND password = 'alex123'
```
The quote closes the username string. The `-- ` comments out the rest of the line, so the password condition is ignored. Only the username is checked. This is why the account opens even though alex123 is not Alex's password.

## Fix
Replace that line with:
```python
row = db.execute("SELECT id, username, name, email FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
```
The values are now passed separately from the SQL statement. SQLite treats the entire attack string as a username instead of interpreting its quote and comment as SQL. There is no matching username, so login fails. This is the only security-related difference between the two builds. The ports also differ so they can run together.

## Other precautions
- **Allow-list validation:** Restrict usernames to the characters and length the application needs. This is an extra check, not a replacement for bound parameters.
- **Least privilege:** Give the application only the database permissions it needs. This reduces damage but does not stop a bypass that only uses SELECT. SQLite uses file permissions rather than database user grants.
- **Safe errors:** Return a generic error to the user and keep database diagnostics in protected logs. Hiding errors alone does not fix an injectable query.

## Verification
Each version has eight tests for valid accounts, incorrect credentials, empty input, a malformed quote, the main payload, and an OR 1=1 payload. All 16 tests passed. Browser runs also confirmed that the same payload succeeds in the vulnerable version and fails in the secured version. Screenshots are in ../../Screenshots.

To demonstrate: show the failed normal login, run the payload on 8001, explain the query, then run the same payload on 8002. Finally show a normal successful login and the one-line fix.

## Limitations
This example displays account details after login but has no persistent sessions. Passwords are sample plaintext values to keep the query example small. A real site also needs salted password hashes and proper session management. Run these examples locally only.

## References
- https://docs.python.org/3/library/sqlite3.html
- https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
