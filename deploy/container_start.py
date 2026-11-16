"""Start an already-provisioned demo; do not migrate or seed on startup."""
import os
from pathlib import Path
import subprocess
import sys

database = Path(os.environ.get("CAREFLOW_HOSTED_DB", "/missing"))
if not database.is_file():
    raise SystemExit("Provision a NEW persistent demo database before starting the server.")
subprocess.run([sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"], check=True)
subprocess.run([sys.executable, "manage.py", "migrate", "--check"], check=True)
subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], check=True)
# One worker for the limited SQLite demonstration, never a production scale claim.
port = int(os.environ.get("PORT", "8000"))
if not 1024 <= port <= 65535:
    raise SystemExit("PORT is outside the allowed range.")
os.execvp("gunicorn", ["gunicorn", "careflow.wsgi:application", "--bind", f"0.0.0.0:{port}",
                      "--workers", "1", "--threads", "1", "--timeout", "30"])
