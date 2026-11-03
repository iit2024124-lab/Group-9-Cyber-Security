# OS Command Injection — In-band Demo

Coursework demo for an intentionally vulnerable web endpoint and its mitigation.

## Run on Windows (PowerShell)

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000/

## Demo flow

1. On `/vulnerable`, submit a normal local host such as `127.0.0.1`.
2. For the authorized local demonstration, submit `127.0.0.1 & whoami` on Windows. The shell treats `&` as a command separator and the `whoami` output is returned in-band.
3. On `/safe`, submit the exact same input. The allow-list rejects it.
4. Explain the root cause: user input is concatenated into a command string executed with `shell=True`.
5. Explain the mitigation: strict allow-list validation and an argument vector with `shell=False`.

The app chooses the appropriate ping count flag for Windows (`-n`) or Linux/macOS (`-c`).

## Safety

This intentionally vulnerable app binds to `127.0.0.1` only. Do not deploy it publicly or test systems you do not own or have explicit permission to test.
