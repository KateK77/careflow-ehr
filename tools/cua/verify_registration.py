"""Verify the registration batch against the temporary QA database only."""
import sqlite3
from contextlib import closing

from registration import MRN, USERNAME


def verify(directory, scenario="registration"):
    database = directory / "computer-use-qa.sqlite3"
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        patients = db.execute("SELECT id, mrn, first_name, last_name, dob, sex FROM patients_patient").fetchall()
        visits = db.execute(
            """SELECT a.patient_id, a.status, a.version, u.username, p.username, a.checked_in_at IS NOT NULL
               FROM scheduling_appointment a LEFT JOIN auth_user u ON a.checked_in_by_id=u.id
               JOIN auth_user p ON a.physician_id=p.id"""
        ).fetchall()
        events = db.execute(
            """SELECT e.action, u.username FROM patients_auditevent e JOIN auth_user u ON e.actor_id=u.id
               WHERE e.patient_id=1 AND e.action IN ('patient_create','appointment_create','appointment_arrive')
               ORDER BY e.id"""
        ).fetchall()
    actions = {
        "registration": ("patient_create", "appointment_create", "appointment_arrive"),
        "registration-only": ("patient_create",),
        "appointment-only": ("appointment_create",),
        "checkin-only": ("appointment_arrive",),
    }[scenario]
    checks = {
        "one_synthetic_patient": patients == [(1, MRN, "Synthetic", "Journey", "1990-01-15", "unknown")],
        "ordered_audit_events": events == [(action, USERNAME) for action in actions],
    }
    if scenario == "registration-only":
        checks["no_appointment_created"] = not visits
    elif scenario == "appointment-only":
        checks["appointment_scheduled"] = visits == [(1, "scheduled", 1, None, "cua-physician", 0)]
    else:
        checks["appointment_arrived"] = visits == [(1, "arrived", 2, USERNAME, "cua-physician", 1)]
    return checks
