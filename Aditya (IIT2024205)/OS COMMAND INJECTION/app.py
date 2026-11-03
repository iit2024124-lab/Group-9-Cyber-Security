import re
import platform
import subprocess
from flask import Flask, render_template, request

app = Flask(__name__)

PING_COUNT_FLAG = "-n" if platform.system() == "Windows" else "-c"


def ping_command(host):
    return f"ping {PING_COUNT_FLAG} 1 {host}"


@app.route("/")
def home():
    return render_template("index.html")
@app.route("/vulnerable", methods=["GET", "POST"])
def vulnerable():
    output = None
    command_run = None
    host = ""
    if request.method == "POST":

        
        host = request.form.get("host", "").strip()
        command_run = ping_command(host)
        try:
            result = subprocess.run(
                command_run,
                shell=True,
                capture_output=True,
                text=True,
                timeout=8
            )
            output = result.stdout + result.stderr


        except subprocess.TimeoutExpired:
            output = "Command timed out."
        except Exception as exc:
            output = f"Error: {exc}"

    return render_template(
        "vulnerable.html",
        output=output,
        command_run=command_run,
        host=host
    )

HOST_RE = re.compile(
    r"^(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3}|"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*)$"
)


def valid_host(host):
    if not host or len(host) > 253 or not HOST_RE.fullmatch(host):
        return False
    # Reject malformed IPv4 octets if input looks like an IPv4 address.
    if re.fullmatch(r"[0-9.]+", host):
        parts = host.split(".")
        return len(parts) == 4 and all(
            part.isdigit() and 0 <= int(part) <= 255 for part in parts
        )
    return True


@app.route("/safe", methods=["GET", "POST"])
def safe():
    output = None
    rejected = None
    host = ""

    if request.method == "POST":
        host = request.form.get("host", "").strip()

  
        if not valid_host(host):
            rejected = "Rejected: enter only a valid hostname or IP address."
        else:


            
            try:
                result = subprocess.run(
                    ["ping", PING_COUNT_FLAG, "1", host],
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=8
                )

                
                output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                output = "Ping timed out."
            except Exception as exc:
                output = f"Error: {exc}"

    return render_template(
        "safe.html",
        output=output,
        rejected=rejected,
        host=host
    )


if __name__ == "__main__":
    
    app.run(host="127.0.0.1", port=5000, debug=False)
