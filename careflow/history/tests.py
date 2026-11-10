from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError, close_old_connections, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from careflow.clinical.models import Encounter, Note
from careflow.clinical.services import complete_encounter, save_note, sign_note, start_encounter
from careflow.patients.models import Patient
from careflow.scheduling.models import Appointment
from .access import can_maintain
from .models import Allergy, AllergyState, EncounterDiagnosis, HistoryEvent, MedicalHistory, MedicationStatement, Problem
from .services import HistoryConflict, review_allergy_state, save_record


class HistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {}
        for role in ["Physician", "Nurse", "Administrator", "FrontDesk"]:
            user = get_user_model().objects.create_user(username="history-" + role)
            user.groups.add(Group.objects.get_or_create(name=role)[0])
            cls.users[role] = user
        cls.physician = cls.users["Physician"]
        cls.other = get_user_model().objects.create_user(username="history-other")
        cls.other.groups.add(Group.objects.get(name="Physician"))
        cls.patient = Patient.objects.create(mrn="HISTORY-01", first_name="Synthetic", last_name="History",
                                             dob=date(1980, 1, 1), sex="unknown")
        cls.foreign_patient = Patient.objects.create(mrn="HISTORY-02", first_name="Fictional", last_name="Isolated",
                                                     dob=date(1990, 2, 2), sex="female")

    def setUp(self):
        now = timezone.now()
        self.appointment = Appointment.objects.create(patient=self.patient, physician=self.physician,
            start_at=now, end_at=now + timedelta(minutes=30), status="arrived", appointment_type="Synthetic history")
        self.client.force_login(self.physician)

    def data(self, kind, **changes):
        common = {"label": "Synthetic " + kind, "comments": "Fictional only", "source": "patient_reported",
                  "source_detail": "Synthetic interview", "synthetic_confirmed": True}
        extra = {
            "medical": {"category": "medical", "start_date": None, "end_date": None},
            "problems": {"status": "active", "onset_date": None, "resolution_date": None, "code": "MOCK-1"},
            "allergies": {"reaction": "Synthetic reaction", "severity": "mild", "status": "active",
                          "verification": "unconfirmed", "onset_date": None},
            "medications": {"dose": "Synthetic dose description", "route": "Synthetic route",
                            "frequency": "Synthetic frequency", "status": "active", "start_date": None, "end_date": None},
            "diagnoses": {"rank": "secondary", "code": "MOCK-DX", "problem": None},
        }
        return {**common, **extra[kind], **changes}

    def save(self, kind, record=None, encounter=None, **changes):
        return save_record(self.physician, self.patient.pk, kind, self.data(kind, **changes),
                           record.version if record else 0, record.pk if record else None,
                           encounter.pk if encounter else None)

    def payload(self, kind, **changes):
        return {k: "" if v is None else v for k, v in self.data(kind, **changes).items()}

    def url(self, action, kind, record=None, patient=None):
        args = [(patient or self.patient).pk, kind]
        if record:
            args.append(record.pk)
        return reverse("history_" + action, args=args)

    def test_history_all_categories_create_edit_and_review(self):
        for category in ["medical", "surgical", "family", "social"]:
            record = self.save("medical", category=category)
            self.assertEqual(record.patient, self.patient)
            self.assertEqual(record.author, self.physician)
            reviewed = save_record(self.physician, self.patient.pk, "medical", {"synthetic_confirmed": True},
                                   1, record.pk, review=True)
            self.assertEqual(reviewed.reviewed_by, self.physician)
            self.assertIsNotNone(reviewed.reviewed_at)
            edited = self.save("medical", reviewed, category=category, comments="Corrected synthetic comment")
            self.assertIsNone(edited.reviewed_at)
            self.assertEqual(edited.author, self.physician)
            events = HistoryEvent.objects.filter(kind="medical", record_id=record.pk)
            self.assertEqual(events.count(), 3)
            self.assertEqual(events.first().before["comments"], "Fictional only")
            self.assertEqual(events.first().after["comments"], "Corrected synthetic comment")

    def test_longitudinal_form_creation_persistence_and_detail(self):
        for kind in ["medical", "problems", "allergies", "medications"]:
            response = self.client.post(self.url("create", kind), self.payload(kind, version=0))
            self.assertEqual(response.status_code, 302, response.content.decode())
            detail = self.client.get(response.url)
            self.assertContains(detail, "Synthetic " + kind)
            self.assertContains(detail, "Original author")
            self.assertContains(detail, "Record history")
            self.assertContains(self.client.get(self.url("list", kind)), "Synthetic " + kind)

    def test_medical_invalid_dates_and_category(self):
        for changes in [{"category": "invalid"}, {"start_date": timezone.localdate() + timedelta(days=1)},
                        {"start_date": date(2020, 1, 1), "end_date": date(2019, 1, 1)}]:
            with self.assertRaises(ValidationError):
                self.save("medical", **changes)
        self.assertFalse(MedicalHistory.objects.exists())

    def test_problem_resolved_inactive_history_and_validation(self):
        record = self.save("problems", onset_date=date(2020, 1, 1))
        record = self.save("problems", record, status="resolved", onset_date=date(2020, 1, 1), resolution_date=date(2021, 1, 1))
        self.assertEqual(Problem.objects.count(), 1)
        self.assertContains(self.client.get(self.url("list", "problems")), "Resolved")
        record = self.save("problems", record, status="inactive")
        self.assertEqual(record.status, "inactive")
        self.assertTrue(HistoryEvent.objects.filter(kind="problems", before__status="resolved").exists())
        for changes in [{"status": "resolved"}, {"status": "active", "resolution_date": date(2020, 1, 1)},
                        {"status": "resolved", "onset_date": date(2022, 1, 1), "resolution_date": date(2020, 1, 1)}]:
            with self.assertRaises(ValidationError):
                self.save("problems", **changes)

    def test_medication_sources_states_dates_and_review(self):
        record = self.save("medications")
        self.assertEqual(record.source, "patient_reported")
        record = self.save("medications", record, status="stopped", end_date=timezone.localdate(), source="documented")
        self.assertEqual(record.status, "stopped")
        self.assertEqual(record.source, "documented")
        record = self.save("medications", record, status="historical")
        self.assertEqual(record.status, "historical")
        reviewed = save_record(self.physician, self.patient.pk, "medications", {"synthetic_confirmed": True},
                              record.version, record.pk, review=True)
        self.assertIsNotNone(reviewed.reviewed_at)
        for changes in [{"status": "stopped"}, {"status": "active", "end_date": date(2020, 1, 1)},
                        {"start_date": date(2021, 1, 1), "end_date": date(2020, 1, 1), "status": "historical"}]:
            with self.assertRaises(ValidationError):
                self.save("medications", **changes)

    def test_allergy_unknown_not_reviewed_and_no_known_are_distinct(self):
        response = self.client.get(self.url("list", "allergies"))
        self.assertContains(response, "Allergy assessment: Not reviewed")
        self.assertFalse(AllergyState.objects.exists())
        state = review_allergy_state(self.physician, self.patient.pk, "unknown", 0, True)
        self.assertContains(self.client.get(self.url("list", "allergies")), "Allergy assessment: Unknown")
        state = review_allergy_state(self.physician, self.patient.pk, "no_known", state.version, True)
        self.assertContains(self.client.get(self.url("list", "allergies")), "Allergy assessment: No known allergies")
        state = review_allergy_state(self.physician, self.patient.pk, "not_reviewed", state.version, True)
        self.assertIsNone(state.reviewed_at)

    def test_allergy_creation_atomically_supersedes_no_known(self):
        state = review_allergy_state(self.physician, self.patient.pk, "no_known", 0, True)
        self.save("allergies")
        state.refresh_from_db()
        self.assertEqual(state.status, "documented")
        self.assertIsNone(state.reviewed_at)
        for status in ["no_known", "unknown", "not_reviewed"]:
            with self.assertRaises(ValidationError):
                review_allergy_state(self.physician, self.patient.pk, status, state.version, True)
        with self.assertRaises(HistoryConflict):
            review_allergy_state(self.physician, self.patient.pk, "documented", 1, True)
        self.assertContains(self.client.get(reverse("patient_chart", args=[self.patient.pk])), "Allergy assessment: Documented allergies")

    def test_last_allergy_inactivation_does_not_infer_no_known(self):
        allergy = self.save("allergies")
        allergy = self.save("allergies", allergy, status="inactive")
        self.assertEqual(AllergyState.objects.get(patient=self.patient).status, "not_reviewed")
        self.assertEqual(Allergy.objects.count(), 1)
        self.assertContains(self.client.get(self.url("list", "allergies")), "Inactive")
        self.save("allergies", allergy, status="active")
        self.assertEqual(AllergyState.objects.get(patient=self.patient).status, "documented")

    def test_allergy_verification_and_assessment_validation(self):
        with self.assertRaises(ValidationError):
            review_allergy_state(self.physician, self.patient.pk, "documented", 0, True)
        for verification in ["refuted", "entered_in_error"]:
            with self.assertRaises(ValidationError):
                self.save("allergies", verification=verification)
        allergy = self.save("allergies", status="inactive", verification="refuted")
        self.assertEqual(allergy.verification, "refuted")
        self.assertEqual(AllergyState.objects.get(patient=self.patient).status, "not_reviewed")

    def test_allergy_summary_review_endpoint_and_stale_post(self):
        url = reverse("allergy_state_review", args=[self.patient.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {"version": 0, "status": "unknown"}).status_code, 400)
        self.assertEqual(self.client.post(url, {"version": 0, "status": "unknown", "synthetic_confirmed": True}).status_code, 302)
        self.assertEqual(self.client.post(url, {"version": 0, "status": "no_known", "synthetic_confirmed": True}).status_code, 409)

    def test_read_only_roles_and_frontdesk_get_post(self):
        record = self.save("medical")
        for role in ["Nurse", "Administrator", "FrontDesk"]:
            self.client.force_login(self.users[role])
            response = self.client.get(self.url("detail", "medical", record))
            if role == "FrontDesk":
                self.assertEqual(response.status_code, 403)
                self.assertNotIn(record.label, response.content.decode())
            else:
                self.assertContains(response, record.label)
                self.assertNotContains(response, "Edit record")
            self.assertEqual(self.client.get(self.url("create", "medical")).status_code, 403)
            self.assertEqual(self.client.post(self.url("edit", "medical", record), self.payload("medical", version=1)).status_code, 403)
            self.assertEqual(self.client.post(self.url("review", "medical", record), {"version": 1, "synthetic_confirmed": True}).status_code, 403)

    def test_cross_patient_isolation_and_forged_context(self):
        record = self.save("medical")
        self.assertEqual(self.client.get(self.url("detail", "medical", record, self.foreign_patient)).status_code, 404)
        response = self.client.post(self.url("create", "medical"), self.payload("medical", version=0,
            patient=self.foreign_patient.pk, author=self.other.pk))
        self.assertEqual(response.status_code, 302)
        newest = MedicalHistory.objects.first()
        self.assertEqual(newest.patient, self.patient)
        self.assertEqual(newest.author, self.physician)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url("list", "medical")).status_code, 404)

    def test_historical_assignment_read_only_and_completed_encounter(self):
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        note = save_note(self.physician, encounter.pk, {"subjective": "Synthetic", "objective": "Synthetic",
            "assessment": "Synthetic", "plan": "Synthetic", "synthetic_confirmed": True}, 0)
        sign_note(self.physician, note.pk, 1, True)
        complete_encounter(self.physician, encounter.pk, 1)
        self.assertFalse(can_maintain(self.physician, self.patient.pk))
        self.assertEqual(self.client.get(self.url("list", "medical")).status_code, 200)
        self.assertEqual(self.client.post(self.url("create", "medical"), self.payload("medical", version=0)).status_code, 403)

    def test_stale_edits_reviews_and_original_author_preserved(self):
        record = self.save("medical")
        self.save("medical", record, label="Revised synthetic history")
        with self.assertRaises(HistoryConflict):
            self.save("medical", record, label="Stale overwrite")
        with self.assertRaises(HistoryConflict):
            save_record(self.physician, self.patient.pk, "medical", {"synthetic_confirmed": True}, 1, record.pk, review=True)
        response = self.client.post(self.url("edit", "medical", record), self.payload("medical", version=1, label="Stale form text"))
        self.assertContains(response, "Stale form text", status_code=409)
        record.refresh_from_db()
        self.assertEqual(record.label, "Revised synthetic history")
        self.assertEqual(record.author, self.physician)

    def test_invalid_form_keeps_input_and_requires_synthetic_assertion(self):
        response = self.client.post(self.url("create", "medical"), self.payload("medical", version=0,
            synthetic_confirmed="", label="Keep this synthetic draft"))
        self.assertContains(response, "Keep this synthetic draft", status_code=400)
        self.assertFalse(MedicalHistory.objects.exists())
        with self.assertRaises(ValidationError):
            self.save("medical", comments="x" * 4001)

    def test_atomic_audit_rollback_includes_allergy_summary(self):
        with patch("careflow.history.services._event", side_effect=RuntimeError("unavailable")):
            with self.assertRaises(RuntimeError):
                self.save("allergies")
        self.assertFalse(Allergy.objects.exists())
        self.assertFalse(AllergyState.objects.exists())
        self.assertFalse(HistoryEvent.objects.exists())

    def test_busy_database_is_retryable_before_and_after_lock_acquisition(self):
        for target in ["careflow.history.services.can_maintain", "careflow.history.services._lock_patient"]:
            with patch(target, side_effect=OperationalError("database is locked")):
                with self.assertRaises(HistoryConflict):
                    self.save("medical")
                with self.assertRaises(HistoryConflict):
                    review_allergy_state(self.physician, self.patient.pk, "unknown", 0, True)
        self.assertFalse(MedicalHistory.objects.exists())
        self.assertFalse(AllergyState.objects.exists())

    def test_diagnoses_primary_secondary_link_and_persistence(self):
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        problem = self.save("problems")
        primary = self.save("diagnoses", encounter=encounter, rank="primary", problem=problem)
        secondary = self.save("diagnoses", encounter=encounter)
        self.assertEqual(primary.patient, self.patient)
        self.assertEqual(primary.problem, problem)
        self.assertEqual(secondary.rank, "secondary")
        self.assertEqual(Problem.objects.count(), 1)
        self.assertContains(self.client.get(reverse("diagnosis_list", args=[self.patient.pk, encounter.pk])), "Primary")
        with self.assertRaises(ValidationError):
            self.save("diagnoses", encounter=encounter, rank="primary")
        with self.assertRaises(IntegrityError), transaction.atomic():
            EncounterDiagnosis.objects.create(patient=self.patient, encounter=encounter, label="Synthetic direct",
                source="documented", author=self.physician, updated_by=self.physician, rank="primary")

    def test_diagnosis_cross_patient_problem_and_encounter_rejected(self):
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        foreign = Problem.objects.create(patient=self.foreign_patient, label="Foreign synthetic", status="active",
            source="documented", author=self.other, updated_by=self.other)
        with self.assertRaises(ValidationError):
            self.save("diagnoses", encounter=encounter, problem=foreign)
        response = self.client.post(reverse("diagnosis_create", args=[self.patient.pk, encounter.pk]),
                                    self.payload("diagnoses", version=0, problem=foreign.pk))
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(foreign.label, response.content.decode())
        self.assertEqual(self.client.get(reverse("diagnosis_list", args=[self.foreign_patient.pk, encounter.pk])).status_code, 404)

    def test_completed_diagnoses_and_signed_soap_unchanged(self):
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        diagnosis = self.save("diagnoses", encounter=encounter)
        note = save_note(self.physician, encounter.pk, {"subjective": "Synthetic S", "objective": "Synthetic O",
            "assessment": "Synthetic A", "plan": "Synthetic P", "synthetic_confirmed": True}, 0)
        sign_note(self.physician, note.pk, 1, True)
        original = Note.objects.values().get(pk=note.pk)
        self.save("problems", label="New synthetic problem after signing")
        complete_encounter(self.physician, encounter.pk, 1)
        with self.assertRaises(HistoryConflict):
            self.save("diagnoses", diagnosis, encounter, label="Attempted change")
        self.assertEqual(self.client.post(reverse("diagnosis_edit", args=[self.patient.pk, encounter.pk, diagnosis.pk]),
                                         self.payload("diagnoses", version=1)).status_code, 403)
        self.assertEqual(Note.objects.values().get(pk=note.pk), original)
        self.assertEqual(EncounterDiagnosis.objects.get(pk=diagnosis.pk).label, diagnosis.label)

    def test_diagnosis_authorization_for_other_staff(self):
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        for role in ["Administrator", "Nurse", "FrontDesk"]:
            self.client.force_login(self.users[role])
            self.assertEqual(self.client.post(reverse("diagnosis_create", args=[self.patient.pk, encounter.pk]),
                                             self.payload("diagnoses", version=0)).status_code, 403)
        with self.assertRaises(PermissionDenied):
            save_record(self.other, self.patient.pk, "diagnoses", self.data("diagnoses"), 0, encounter_id=encounter.pk)

    def test_encounter_with_missing_checkin_recorder_remains_readable(self):
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        self.assertContains(self.client.get(reverse("encounter_detail", args=[self.patient.pk, encounter.pk])),
                            "Recorder not recorded")

    def test_chart_timeline_and_history_escaping(self):
        record = self.save("medical", label="<script>synthetic</script>")
        response = self.client.get(self.url("detail", "medical", record))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>synthetic")
        chart = self.client.get(reverse("patient_chart", args=[self.patient.pk]))
        self.assertContains(chart, "Medical history recorded")
        self.assertContains(chart, "DEMO — NOT FOR CLINICAL USE")

    def test_csrf_anonymous_and_unknown_modules(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.physician)
        self.assertEqual(secure.post(self.url("create", "medical"), self.payload("medical", version=0)).status_code, 403)
        self.assertEqual(self.client.get(self.url("list", "not-a-module")).status_code, 404)
        self.assertEqual(self.client.get(self.url("list", "diagnoses")).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url("list", "medical")).status_code, 302)


class HistoryConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_user(username="parallel-history")
        self.actor.groups.add(Group.objects.get_or_create(name="Physician")[0])
        self.patient = Patient.objects.create(mrn="PARALLEL-HISTORY", first_name="Synthetic", last_name="Parallel",
                                             dob=date(1980, 1, 1), sex="unknown")
        now = timezone.now()
        self.appointment = Appointment.objects.create(patient=self.patient, physician=self.actor,
            start_at=now, end_at=now + timedelta(minutes=30), status="arrived", appointment_type="Synthetic")

    def parallel(self, actions):
        barrier = Barrier(len(actions))

        def run(action):
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=self.actor.pk)
                barrier.wait(timeout=10)
                try:
                    action(actor)
                    return "saved"
                except (HistoryConflict, ValidationError):
                    return "conflict"
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=len(actions)) as executor:
            return list(executor.map(run, actions))

    def test_parallel_edits_do_not_overwrite_newer_version(self):
        data = {"label": "Synthetic", "comments": "", "source": "documented", "source_detail": "",
                "status": "active", "onset_date": None, "resolution_date": None, "code": "", "synthetic_confirmed": True}
        record = save_record(self.actor, self.patient.pk, "problems", data, 0)
        results = self.parallel([
            lambda actor: save_record(actor, self.patient.pk, "problems", {**data, "label": "Synthetic A"}, 1, record.pk),
            lambda actor: save_record(actor, self.patient.pk, "problems", {**data, "label": "Synthetic B"}, 1, record.pk),
        ])
        self.assertCountEqual(results, ["saved", "conflict"])
        record.refresh_from_db()
        self.assertEqual(record.version, 2)
        self.assertEqual(HistoryEvent.objects.filter(kind="problems").count(), 2)

    def test_allergy_creation_racing_no_known_has_consistent_result(self):
        data = {"label": "Synthetic allergen", "comments": "", "source": "documented", "source_detail": "",
                "reaction": "Synthetic", "severity": "unknown", "status": "active", "verification": "unconfirmed",
                "onset_date": None, "synthetic_confirmed": True}
        self.parallel([
            lambda actor: save_record(actor, self.patient.pk, "allergies", data, 0),
            lambda actor: review_allergy_state(actor, self.patient.pk, "no_known", 0, True),
        ])
        state = AllergyState.objects.get(patient=self.patient)
        active = Allergy.objects.filter(patient=self.patient, status="active").exists()
        self.assertEqual(state.status, "documented" if active else "no_known")

    def test_diagnosis_edit_racing_completion_preserves_completed_snapshot(self):
        encounter = start_encounter(self.actor, self.appointment.pk, 1)
        note = save_note(self.actor, encounter.pk, {"subjective": "Synthetic", "objective": "Synthetic",
            "assessment": "Synthetic", "plan": "Synthetic", "synthetic_confirmed": True}, 0)
        sign_note(self.actor, note.pk, 1, True)
        data = {"label": "Synthetic diagnosis", "comments": "", "source": "documented", "source_detail": "",
                "rank": "primary", "code": "", "problem": None, "synthetic_confirmed": True}
        diagnosis = save_record(self.actor, self.patient.pk, "diagnoses", data, 0, encounter_id=encounter.pk)
        self.parallel([
            lambda actor: save_record(actor, self.patient.pk, "diagnoses", {**data, "label": "Revised synthetic"},
                                      1, diagnosis.pk, encounter.pk),
            lambda actor: complete_encounter(actor, encounter.pk, 1),
        ])
        encounter.refresh_from_db()
        # Busy SQLite writes may require the completion action to be retried by the caller.
        if encounter.status == "in_progress":
            complete_encounter(self.actor, encounter.pk, 1)
            encounter.refresh_from_db()
        latest = HistoryEvent.objects.filter(kind="diagnoses").first()
        self.assertLessEqual(latest.audit.occurred_at, encounter.completed_at)
        with self.assertRaises(HistoryConflict):
            save_record(self.actor, self.patient.pk, "diagnoses", data, 1, diagnosis.pk, encounter.pk)
