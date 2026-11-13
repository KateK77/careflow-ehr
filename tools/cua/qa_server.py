"""Serve the real Django app on a private loopback port using a fresh SQLite file."""
import json
import os
import secrets
from datetime import timedelta
import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


def main():
    directory = Path(sys.argv[1]).resolve(strict=True)
    database = directory / "computer-use-qa.sqlite3"
    database.touch(exist_ok=False)
    os.environ["CAREFLOW_DB_PATH"] = str(database)
    os.environ["DJANGO_SETTINGS_MODULE"] = "careflow.settings"
    application = StaticFilesHandler(get_wsgi_application())
    call_command("migrate", verbosity=0, interactive=False)
    if sys.argv[2:] == ["registration"]:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        from django.utils import timezone

        from registration import USERNAME

        # Keep the demo slot on the current clinic date throughout the bounded run.
        now = timezone.localtime()
        start = (now + timedelta(minutes=12)).replace(second=0, microsecond=0)
        if start.date() != now.date():
            raise RuntimeError("Run the same-day check-in scenario outside the last twelve clinic minutes.")
        password = secrets.token_urlsafe(24)
        for name, role, first, last, credential in [
            (USERNAME, "FrontDesk", "Synthetic", "Front Desk", password),
            ("cua-physician", "Physician", "Synthetic", "Physician", None),
        ]:
            user = get_user_model().objects.create_user(name, password=credential, first_name=first, last_name=last)
            user.groups.add(Group.objects.get_or_create(name=role)[0])
        (directory / "fixture.json").write_text(json.dumps({
            "password": password, "physician": user.pk, "start": start.strftime("%Y-%m-%dT%H:%M"),
        }), encoding="utf8")
    with make_server("127.0.0.1", 0, application, handler_class=QuietHandler) as server:
        ready = directory / "server-port"
        staging = ready.with_suffix(".tmp")
        staging.write_text(str(server.server_port), encoding="ascii")
        staging.replace(ready)
        server.serve_forever()


if __name__ == "__main__":
    main()
