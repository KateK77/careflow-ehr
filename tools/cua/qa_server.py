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
    if len(sys.argv) == 3 and sys.argv[2].startswith("rbac-"):
        from django.conf import settings
        from django.test import Client
        from careflow.portal.tests import PortalFixture
        from rbac import LAUNCHER, launcher_html

        actor = sys.argv[2].removeprefix("rbac-")
        fixture = PortalFixture()
        fixture.setup_portal()
        fixture.release()
        users = {"owner": fixture.portal_a, "patient": fixture.portal_b, "physician": fixture.physician}
        cookie = None
        if actor != "anonymous":
            client = Client()
            client.force_login(users[actor])
            cookie = {"name": settings.SESSION_COOKIE_NAME,
                      "value": client.cookies[settings.SESSION_COOKIE_NAME].value}
        (directory / "fixture.json").write_text(json.dumps({
            "cookie": cookie, "result": fixture.original.pk,
            "denied_markers": ["LAB-01", "LAB-02", "Synthetic Lab", "Synthetic Other", "SYN-A", "demo-U"],
        }), encoding="utf8")
        django_application = application

        def application(environ, start_response):
            if environ["PATH_INFO"] == LAUNCHER and environ["REQUEST_METHOD"] == "GET":
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"),
                                          ("Cache-Control", "no-store")])
                return [launcher_html(actor, fixture.original.pk).encode("utf8")]
            return django_application(environ, start_response)

    with make_server("127.0.0.1", 0, application, handler_class=QuietHandler) as server:
        ready = directory / "server-port"
        staging = ready.with_suffix(".tmp")
        staging.write_text(str(server.server_port), encoding="ascii")
        staging.replace(ready)
        server.serve_forever()


if __name__ == "__main__":
    main()
