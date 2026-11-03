# SQL Injection - Authentication Bypass

**Name:** Atharva  
**Roll number:** IIT2024192  
**Course:** Cyber Security (IT-30001)  
**Group:** 9

| Name | Roll number | Category | Variant |
|---|---|---|---|
| Atharva | IIT2024192 | SQL injection | Authentication bypass |

## Files
- SQL_Injection_Vulnerable: original login query, runs on port 8001
- SQL_Injection_Secured: parameterized query, runs on port 8002
- Screenshots: login attempts before and after the fix

Both folders contain the Maison website, a README, a short report in docs, and tests. No external Python packages are needed.

## Run
Open a terminal in either project folder and run:
```sh
python app.py
```
Open http://127.0.0.1:8001 for the vulnerable version, or http://127.0.0.1:8002 for the secured version. To run both, use two terminals.

## Test login
The normal credentials are alex / Maison!26. First try alex / alex123; this should fail. Then try username `alex' -- ` with the same password `alex123`.

The vulnerable version logs in as Alex. The secured version rejects the same input. The correct credentials still work in both.

Run tests inside each folder:
```sh
python -m unittest discover -s tests -v
```
