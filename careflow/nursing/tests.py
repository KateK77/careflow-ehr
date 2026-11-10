from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch
from zoneinfo import ZoneInfo

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
from .models import NursingEvent, RoomingAssessment, VitalObservation
from .services import NursingConflict, save_documentation


class NursingFixture:
    def make_fixture(self):
        self.users = {}
        for role in ["Nurse", "Physician", "Administrator", "FrontDesk"]:
            user = get_user_model().objects.create_user(username="nursing-" + role)
            user.groups.add(Group.objects.get_or_create(name=role)[0])
            self.users[role] = user
        self.nurse = self.users["Nurse"]
        self.physician = self.users["Physician"]
        self.patient = Patient.objects.create(mrn="NURSING-001", first_name="Synthetic", last_name="Nursing",
                                             dob=date(1980, 1, 1), sex="unknown")
        self.other_patient = Patient.objects.create(mrn="NURSING-002", first_name="Fictional", last_name="Other",
                                                   dob=date(1990, 1, 1), sex="unknown")
        now = timezone.now()
        self.appointment = Appointment.objects.create(patient=self.patient, physician=self.physician, start_at=now,
            end_at=now + timedelta(minutes=30), appointment_type="Synthetic nursing", status="arrived")

    def data(self, kind="vitals", **changes):
        base = {"observed_at": timezone.now() - timedelta(minutes=2), "encounter": None, "synthetic_confirmed": True}
        if kind == "assessment":
            values = {"chief_complaint": "Synthetic rooming complaint", "pain_score": 0,
                      "observations": "Synthetic nursing observations", "ready_for_provider": False}
        else:
            values = {"systolic": 120, "diastolic": 80, "heart_rate": 70, "respiratory_rate": 16,
                      "temperature": Decimal("37.20"), "temperature_unit": "C", "oxygen_saturation": Decimal("98.00"),
                      "height": Decimal("170.00"), "height_unit": "cm", "weight": Decimal("70.00"),
                      "weight_unit": "kg", "pain_score": 0, "source": "measured", "source_detail": "Synthetic device"}
        return {**base, **values, **changes}

    def save(self, kind="vitals", record=None, actor=None, **changes):
        return save_documentation(actor or self.nurse, self.patient.pk, self.appointment.pk, kind,
            self.data(kind, **changes), record.version if record else 0, record.pk if record else None)


class NursingTests(NursingFixture, TestCase):
    def setUp(self):
        self.make_fixture()
        self.client.force_login(self.nurse)

    def url(self, name, kind=None, record=None, patient=None, appointment=None):
        args = [(patient or self.patient).pk]
        if name != "nursing_flowsheet":
            args.append((appointment or self.appointment).pk)
        if kind:
            args.append(kind)
        if record:
            args.append(record.pk)
        return reverse(name, args=args)

    def payload(self, kind="vitals", **changes):
        data = self.data(kind, **changes)
        data["observed_at"] = timezone.localtime(data["observed_at"]).strftime("%Y-%m-%dT%H:%M")
        return {key: "" if value is None else value.pk if isinstance(value, Encounter) else value for key, value in data.items()}

    def test_worklist_filters_and_saved_progress_only(self):
        url = reverse("nursing_workspace")
        self.assertContains(self.client.get(url), self.patient.mrn)
        self.assertContains(self.client.get(url), "Not documented")
        self.assertContains(self.client.get(url), "0 observations")
        self.save("assessment", ready_for_provider=True)
        self.save()
        response = self.client.get(url, {"q": self.patient.mrn, "status": "arrived"})
        self.assertContains(response, "Ready for provider")
        self.assertContains(response, "1 observation")
        self.assertNotContains(self.client.get(url, {"q": "not-a-patient"}), self.patient.mrn)
        self.assertNotContains(self.client.get(url, {"status": "scheduled"}), self.patient.mrn)

    def test_worklist_local_day_overlap_and_invalid_filters(self):
        today = timezone.localdate()
        midnight = timezone.make_aware(datetime.combine(today, time.min))
        Appointment.objects.filter(pk=self.appointment.pk).update(start_at=midnight - timedelta(minutes=15), end_at=midnight + timedelta(minutes=15))
        for day in [today, today - timedelta(days=1)]:
            self.assertContains(self.client.get(reverse("nursing_workspace"), {"date": day.isoformat()}), self.patient.mrn)
        for data in [{"date": "9999-12-31"}, {"date": "invalid"}, {"status": "invented"}, {"q": "x" * 121}]:
            response = self.client.get(reverse("nursing_workspace"), data)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, self.patient.mrn)

    def test_assessment_create_edit_provenance_and_no_implicit_encounter(self):
        before = Appointment.objects.values().get(pk=self.appointment.pk)
        record = self.save("assessment")
        self.assertFalse(Encounter.objects.exists())
        other_nurse = get_user_model().objects.create_user(username="second-nurse")
        other_nurse.groups.add(Group.objects.get(name="Nurse"))
        updated = self.save("assessment", record, actor=other_nurse, chief_complaint="Corrected synthetic complaint", ready_for_provider=True)
        self.assertEqual(updated.recorded_by, self.nurse)
        self.assertEqual(updated.updated_by, other_nurse)
        self.assertEqual(updated.version, 2)
        self.assertEqual(Appointment.objects.values().get(pk=self.appointment.pk), before)
        event = NursingEvent.objects.filter(assessment=record).first()
        self.assertEqual(event.before["chief_complaint"], "Synthetic rooming complaint")
        self.assertEqual(event.after["chief_complaint"], "Corrected synthetic complaint")

    def test_assessment_duplicate_service_and_database(self):
        self.save("assessment")
        with self.assertRaises(NursingConflict):
            self.save("assessment")
        with self.assertRaises(IntegrityError), transaction.atomic():
            RoomingAssessment.objects.create(patient=self.patient, appointment=self.appointment,
                recorded_by=self.nurse, updated_by=self.nurse, chief_complaint="Synthetic duplicate")
        self.assertEqual(RoomingAssessment.objects.count(), 1)

    def test_assessment_http_create_edit_and_pain_zero(self):
        response = self.client.post(self.url("nursing_create", "assessment"), self.payload("assessment", version=0))
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(response.url), "0 /10")
        record = RoomingAssessment.objects.get()
        response = self.client.post(self.url("nursing_edit", "assessment", record), self.payload("assessment", version=1, ready_for_provider=True))
        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertTrue(record.ready_for_provider)

    def test_vitals_persist_decimal_units_and_corrected_history(self):
        record = self.save()
        self.assertEqual(record.temperature, Decimal("37.20"))
        self.assertEqual(record.recorded_by, self.nurse)
        updated = self.save(record=record, temperature=Decimal("98.60"), temperature_unit="F", source="patient_reported")
        event = NursingEvent.objects.filter(observation=record).first()
        self.assertEqual(event.before["temperature"], "37.20")
        self.assertEqual(event.after["temperature"], "98.60")
        self.assertEqual(event.after["temperature_unit"], "F")
        self.assertEqual(updated.version, 2)

    def test_partial_panel_and_at_least_one_measurement(self):
        fields = {name: None for name in ["systolic", "diastolic", "heart_rate", "respiratory_rate", "temperature", "oxygen_saturation", "height", "weight", "pain_score"]}
        fields.update(temperature_unit="", height_unit="", weight_unit="")
        with self.assertRaises(ValidationError):
            self.save(**fields)
        fields["heart_rate"] = 70
        record = self.save(**fields)
        self.assertEqual(record.heart_rate, 70)
        self.assertIsNone(record.systolic)

    def test_ranges_and_bp_pairing(self):
        for changes in [{"systolic": 351}, {"diastolic": None}, {"systolic": 80, "diastolic": 100},
                        {"heart_rate": 0}, {"respiratory_rate": 101}, {"oxygen_saturation": Decimal("100.01")},
                        {"pain_score": 11}, {"temperature": Decimal("46"), "temperature_unit": "C"},
                        {"temperature": Decimal("76"), "temperature_unit": "F"},
                        {"height": Decimal("4"), "height_unit": "m"}, {"height": Decimal("19"), "height_unit": "cm"},
                        {"weight": Decimal("701"), "weight_unit": "kg"}, {"weight": Decimal("0.1"), "weight_unit": "lb"}]:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                self.save(**changes)
        self.assertFalse(VitalObservation.objects.exists())

    def test_unit_pairing_and_nonfinite_malformed_values(self):
        for changes in [{"temperature_unit": ""}, {"weight_unit": "stone"}, {"height": None},
                        {"temperature": Decimal("NaN")}, {"weight": Decimal("Infinity")},
                        {"oxygen_saturation": "not numeric"}, {"temperature": Decimal("37.123")}]:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                self.save(**changes)
        response = self.client.post(self.url("nursing_create", "vitals"), self.payload(version=0, heart_rate="70.5"))
        self.assertEqual(response.status_code, 400)

    def test_observation_time_validation_and_local_input(self):
        for instant in [timezone.now() + timedelta(days=1), timezone.make_aware(datetime(1979, 1, 1)), datetime(2020, 1, 1)]:
            with self.assertRaises(ValidationError):
                self.save(observed_at=instant)
        response = self.client.post(self.url("nursing_create", "vitals"), self.payload(version=0))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(VitalObservation.objects.count(), 1)

    def test_local_dst_input_is_rejected_when_ambiguous_or_nonexistent(self):
        with timezone.override(ZoneInfo("America/Chicago")):
            for value in ["2026-03-08T02:30", "2026-11-01T01:30"]:
                response = self.client.post(self.url("nursing_create", "vitals"), {**self.payload(version=0), "observed_at": value})
                self.assertEqual(response.status_code, 400)
        self.assertFalse(VitalObservation.objects.exists())

    def test_synthetic_confirmation_and_invalid_form_preserve_input(self):
        response = self.client.post(self.url("nursing_create", "assessment"), self.payload("assessment", version=0,
            chief_complaint="Keep this synthetic input", synthetic_confirmed=""))
        self.assertContains(response, "Keep this synthetic input", status_code=400)
        self.assertFalse(RoomingAssessment.objects.exists())
        with self.assertRaises(ValidationError):
            self.save(synthetic_confirmed=False)

    def test_role_read_write_policies(self):
        record = self.save()
        for role in ["Physician", "Administrator", "FrontDesk"]:
            self.client.force_login(self.users[role])
            response = self.client.get(self.url("nursing_record", "vitals", record))
            if role == "FrontDesk":
                self.assertEqual(response.status_code, 403)
                self.assertNotIn("Synthetic device", response.content.decode())
            else:
                self.assertContains(response, "37.20 °C")
                self.assertNotContains(response, "Correct documentation")
            self.assertEqual(self.client.get(self.url("nursing_create", "assessment")).status_code, 403)
            self.assertEqual(self.client.post(self.url("nursing_edit", "vitals", record), self.payload(version=1)).status_code, 403)
            with self.assertRaises(PermissionDenied):
                self.save(actor=self.users[role])

    def test_nurse_scope_and_explicit_multi_role_write_extension(self):
        admin = self.users["Administrator"]
        admin.groups.add(Group.objects.get(name="Nurse"))
        self.assertEqual(self.save(actor=admin).recorded_by, admin)
        self.client.force_login(self.nurse)
        self.assertEqual(self.client.get(reverse("nursing_workspace")).status_code, 200)
        self.assertEqual(self.client.post(reverse("encounter_start", args=[self.appointment.pk]), {"version": 1}).status_code, 403)

    def test_physician_isolation_and_longitudinal_flowsheet_scope(self):
        record = self.save()
        other = get_user_model().objects.create_user(username="unassigned-physician")
        other.groups.add(Group.objects.get(name="Physician"))
        self.client.force_login(other)
        self.assertEqual(self.client.get(self.url("nursing_record", "vitals", record)).status_code, 404)
        self.assertNotContains(self.client.get(reverse("nursing_workspace")), self.patient.mrn)
        self.assertEqual(self.client.get(self.url("nursing_flowsheet")).status_code, 404)

    def test_patient_appointment_and_record_isolation(self):
        record = self.save()
        other_appt = Appointment.objects.create(patient=self.other_patient, physician=self.physician,
            start_at=timezone.now() + timedelta(hours=1), end_at=timezone.now() + timedelta(hours=2),
            appointment_type="Other synthetic", status="arrived")
        self.assertEqual(self.client.get(self.url("nursing_record", "vitals", record, self.other_patient, other_appt)).status_code, 404)
        self.assertEqual(self.client.post(self.url("nursing_create", "vitals", patient=self.other_patient), self.payload(version=0)).status_code, 404)
        self.assertEqual(self.client.get(self.url("nursing_flowsheet"), {"appointment": other_appt.pk}).status_code, 404)
        for value in ["not-an-id", "²", str(2**64), "9" * 5000]:
            self.assertEqual(self.client.get(self.url("nursing_flowsheet"), {"appointment": value}).status_code, 404)

    def test_encounter_association_is_validated_and_fixed_after_creation(self):
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        record = self.save(encounter=encounter)
        self.assertEqual(record.encounter, encounter)
        self.assertContains(self.client.get(self.url("nursing_record", "vitals", record)),
                            f'Linked encounter #{encounter.pk}')
        with self.assertRaises(ValidationError):
            self.save(record=record, encounter=None)
        other_appt = Appointment.objects.create(patient=self.other_patient, physician=self.physician,
            start_at=timezone.now(), end_at=timezone.now() + timedelta(minutes=30), appointment_type="Synthetic other", status="arrived")
        other_encounter = start_encounter(self.physician, other_appt.pk, 1)
        with self.assertRaises(ValidationError):
            self.save(encounter=other_encounter)
        self.assertEqual(self.client.post(self.url("nursing_create", "vitals"), self.payload(version=0, encounter=other_encounter)).status_code, 400)

    def test_forged_patient_nurse_and_appointment_fields_are_ignored(self):
        self.client.post(self.url("nursing_create", "vitals"), self.payload(version=0,
            patient=self.other_patient.pk, appointment=999, recorded_by=self.physician.pk))
        record = VitalObservation.objects.get()
        self.assertEqual(record.patient, self.patient)
        self.assertEqual(record.appointment, self.appointment)
        self.assertEqual(record.recorded_by, self.nurse)

    def test_stale_edit_preserves_current_value_and_submitted_text(self):
        record = self.save("assessment")
        self.save("assessment", record, chief_complaint="Current synthetic value")
        response = self.client.post(self.url("nursing_edit", "assessment", record), self.payload("assessment", version=1,
            chief_complaint="Stale synthetic draft"))
        self.assertContains(response, "Stale synthetic draft", status_code=409)
        record.refresh_from_db()
        self.assertEqual(record.chief_complaint, "Current synthetic value")
        self.assertEqual(record.version, 2)

    def test_appointment_state_restrictions(self):
        for status in ["scheduled", "cancelled", "no_show"]:
            Appointment.objects.filter(pk=self.appointment.pk).update(status=status)
            with self.assertRaises(NursingConflict):
                self.save()
            self.assertEqual(self.client.post(self.url("nursing_create", "vitals"), self.payload(version=0)).status_code, 403)

    def test_completed_encounter_blocks_writes_and_preserves_signed_note(self):
        record = self.save()
        encounter = start_encounter(self.physician, self.appointment.pk, 1)
        note = save_note(self.physician, encounter.pk, {"subjective": "Synthetic", "objective": "Synthetic",
            "assessment": "Synthetic", "plan": "Synthetic", "synthetic_confirmed": True}, 0)
        sign_note(self.physician, note.pk, 1, True)
        before = Note.objects.values().get(pk=note.pk)
        self.save(record=record, temperature=Decimal("37.10"))
        self.assertEqual(Note.objects.values().get(pk=note.pk), before)
        complete_encounter(self.physician, encounter.pk, 1)
        record.refresh_from_db()
        with self.assertRaises(NursingConflict):
            self.save(record=record)
        self.assertEqual(self.client.get(self.url("nursing_record", "vitals", record)).status_code, 200)
        self.assertEqual(Note.objects.values().get(pk=note.pk), before)

    def test_atomic_audit_rollback_and_retryable_database_lock(self):
        with patch("careflow.nursing.services._event", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.save()
        self.assertFalse(VitalObservation.objects.exists())
        with patch("careflow.nursing.services._lock_providers", side_effect=OperationalError("database is locked")):
            with self.assertRaises(NursingConflict):
                self.save()
        self.assertFalse(NursingEvent.objects.exists())

    def test_flowsheet_values_units_chronology_and_pagination(self):
        first = self.save(observed_at=timezone.now() - timedelta(hours=1))
        second = self.save(temperature=Decimal("98.60"), temperature_unit="F")
        response = self.client.get(self.url("nursing_flowsheet"))
        self.assertContains(response, "37.20 °C")
        self.assertContains(response, "98.60 °F")
        self.assertLess(response.content.index(f"/vitals/{first.pk}/".encode()), response.content.index(f"/vitals/{second.pk}/".encode()))
        self.assertContains(response, "120 mmHg")
        self.assertContains(response, "0 /10")
        self.assertContains(response, "flowsheet-scroll")
        for _ in range(11):
            self.save()
        self.assertContains(self.client.get(self.url("nursing_flowsheet")), "Older observations")

    def test_empty_flowsheet_and_chart_latest_measurements_timeline(self):
        self.assertContains(self.client.get(self.url("nursing_flowsheet")), "No vital observations")
        self.save("assessment", ready_for_provider=True)
        self.save()
        self.client.force_login(self.physician)
        response = self.client.get(reverse("patient_chart", args=[self.patient.pk]))
        self.assertContains(response, "nursing_vitals_create")
        self.assertContains(response, "nursing_assessment_create")
        self.assertContains(response, "37.20 °C")
        self.assertContains(response, "Ready for provider")
        self.assertContains(response, "DEMO — NOT FOR CLINICAL USE")

    def test_escaping_csrf_anonymous_and_invalid_kind(self):
        record = self.save("assessment", observations="<script>synthetic</script>")
        response = self.client.get(self.url("nursing_record", "assessment", record))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>synthetic")
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.nurse)
        self.assertEqual(secure.post(self.url("nursing_create", "vitals"), self.payload(version=0)).status_code, 403)
        self.assertEqual(self.client.get(self.url("nursing_create", "invented")).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("nursing_workspace")).status_code, 302)


class NursingConcurrencyTests(NursingFixture, TransactionTestCase):
    def setUp(self):
        self.make_fixture()

    def parallel(self, actions):
        barrier = Barrier(len(actions))

        def run(action):
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=self.nurse.pk)
                barrier.wait(timeout=10)
                try:
                    action(actor)
                    return "saved"
                except NursingConflict:
                    return "conflict"
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=len(actions)) as executor:
            return list(executor.map(run, actions))

    def test_parallel_assessment_creation_has_one_winner(self):
        data = self.data("assessment")
        results = self.parallel([lambda actor: save_documentation(actor, self.patient.pk, self.appointment.pk,
                                "assessment", data, 0)] * 2)
        self.assertCountEqual(results, ["saved", "conflict"])
        self.assertEqual(RoomingAssessment.objects.count(), 1)
        self.assertEqual(NursingEvent.objects.count(), 1)

    def test_parallel_vital_corrections_preserve_one_version(self):
        record = self.save()
        results = self.parallel([
            lambda actor: save_documentation(actor, self.patient.pk, self.appointment.pk, "vitals", self.data(heart_rate=71), 1, record.pk),
            lambda actor: save_documentation(actor, self.patient.pk, self.appointment.pk, "vitals", self.data(heart_rate=72), 1, record.pk),
        ])
        self.assertCountEqual(results, ["saved", "conflict"])
        record.refresh_from_db()
        self.assertEqual(record.version, 2)
        self.assertEqual(NursingEvent.objects.count(), 2)
