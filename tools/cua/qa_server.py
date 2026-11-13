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
    from registration import PHASES

    scenario = sys.argv[2] if len(sys.argv) == 3 else None
    if scenario in PHASES:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        from django.utils import timezone

        from registration import USERNAME

        # Keep the demo slot on the current clinic date throughout the bounded run.
        now = timezone.localtime()
        start = (now + timedelta(minutes=12)).replace(second=0, microsecond=0)
        if scenario == "registration" and start.date() != now.date():
            raise RuntimeError("Run the same-day check-in scenario outside the last twelve clinic minutes.")
        password = secrets.token_urlsafe(24)
        for name, role, first, last, credential in [
            (USERNAME, "FrontDesk", "Synthetic", "Front Desk", password),
            ("cua-physician", "Physician", "Synthetic", "Physician", None),
        ]:
            user = get_user_model().objects.create_user(name, password=credential, first_name=first, last_name=last)
            user.groups.add(Group.objects.get_or_create(name=role)[0])
        if scenario in {"appointment-only", "checkin-only"}:
            from datetime import date
            from careflow.patients.models import Patient

            patient = Patient.objects.create(mrn="SYN-CUA-001", first_name="Synthetic", last_name="Journey",
                                             dob=date(1990, 1, 15), sex="unknown")
            if scenario == "checkin-only":
                from careflow.scheduling.models import Appointment

                visit_start = now.replace(second=0, microsecond=0)
                Appointment.objects.create(patient=patient, physician=user, start_at=visit_start,
                                           end_at=visit_start + timedelta(minutes=30),
                                           appointment_type="Outpatient visit")
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
