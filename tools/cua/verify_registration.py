"""Verify the registration batch against the temporary QA database only."""
import sqlite3
from contextlib import closing

from registration import MRN, USERNAME


def verify(directory):
    database = directory / "computer-use-qa.sqlite3"
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        patients = db.execute("SELECT id, mrn, first_name, last_name FROM patients_patient").fetchall()
        visits = db.execute(
            """SELECT a.patient_id, a.status, a.version, u.username, p.username
               FROM scheduling_appointment a JOIN auth_user u ON a.checked_in_by_id=u.id
               JOIN auth_user p ON a.physician_id=p.id"""
        ).fetchall()
        events = db.execute(
            """SELECT e.action, u.username FROM patients_auditevent e JOIN auth_user u ON e.actor_id=u.id
               WHERE e.patient_id=1 AND e.action IN ('patient_create','appointment_create','appointment_arrive')
               ORDER BY e.id"""
        ).fetchall()
    return {
        "one_synthetic_patient": patients == [(1, MRN, "Synthetic", "Journey")],
        "appointment_arrived": visits == [(1, "arrived", 2, USERNAME, "cua-physician")],
        "ordered_audit_events": events == [(action, USERNAME) for action in
                                           ("patient_create", "appointment_create", "appointment_arrive")],
    }
