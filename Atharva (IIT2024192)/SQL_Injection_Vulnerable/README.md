# Maison - Vulnerable version

SQL injection authentication bypass.

Name: Atharva  
Roll number: IIT2024192

## Run
Python 3.10 or newer is needed. There are no extra packages to install.
```sh
python app.py
```
Open http://127.0.0.1:8001. On Windows, Start Demo.bat runs the same command. Stop with Ctrl+C.

## Accounts
| Username | Password |
|---|---|
| alex | Maison!26 |
| taylor | CozyHome!26 |

## Try the bypass
1. Enter alex with password alex123. Login fails.
2. Change the username to `alex' -- ` and keep alex123 as the password.
3. The login opens Alex account details without the correct password.

The vulnerable build runs on 8001 and the secured build on 8002. Both use the same page and customer records. See docs/ASSIGNMENT_REPORT.md for the query, explanation, and one-line fix.

## Tests
```sh
python -m unittest discover -s tests -v
```
Eight tests execute actual SQLite queries. The database is in memory, so there is no database file to reset. Screenshots are in ../Screenshots.
