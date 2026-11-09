from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, time, timedelta
from threading import Barrier
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import OperationalError, close_old_connections
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from careflow.patients.models import AuditEvent, Patient
from .forms import AppointmentForm
from .models import Appointment, AppointmentEvent
from .services import AppointmentConflict, save_appointment, transition_appointment


class SchedulingFixture:
    def make_fixture(self):
        self.staff = {}
        for role in ("Administrator", "FrontDesk", "Physician", "Nurse"):
            user = get_user_model().objects.create_user(role.lower())
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            self.staff[role] = user
        self.doctor = self.staff["Physician"]
        self.other_doctor = get_user_model().objects.create_user("other-physician")
        self.other_doctor.groups.add(Group.objects.get(name="Physician"))
        self.actor = self.staff["FrontDesk"]
        self.patient = Patient.objects.create(
            mrn="SCHEDULE-001", first_name="Schedule", last_name="Synthetic",
            dob="1990-01-01", sex="unknown",
        )
        self.start = timezone.localtime().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=2)

    def data(self, **changes):
        values = {
            "patient": self.patient, "physician": self.doctor, "start_at": self.start,
            "duration": 30, "appointment_type": "Synthetic follow-up", "reason": "", "version": 1,
        }
        values.update(changes)
        return values

    def existing_today(self, **changes):
        start = timezone.localtime().replace(hour=9, minute=0, second=0, microsecond=0)
        values = {
            "patient": self.patient, "physician": self.doctor,
            "start_at": start.astimezone(UTC), "end_at": (start + timedelta(minutes=30)).astimezone(UTC),
            "appointment_type": "Synthetic visit",
        }
        values.update(changes)
        return Appointment.objects.create(**values)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SchedulingTests(SchedulingFixture, TestCase):
    def setUp(self):
        self.make_fixture()
        self.client.force_login(self.actor)

    def payload(self, **changes):
        values = {
            "patient": str(self.patient.pk), "physician": str(self.doctor.pk),
            "start_at": self.start.strftime("%Y-%m-%dT%H:%M"), "duration": "30",
            "appointment_type": "Synthetic follow-up", "reason": "", "version": "1",
        }
        values.update(changes)
        return values

    def book_in_browser(self, data=None, appointment=None):
        payload = data or self.payload()
        url = reverse("appointment_edit", args=[appointment.pk]) if appointment else reverse("appointment_create")
        review = self.client.post(url, {**payload, "action": "review"})
        self.assertEqual(review.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 1 if appointment else 0)
        return self.client.post(url, {
            **payload, "action": "confirm", "review_token": review.context["review_token"],
        })

    def test_review_then_create_persists_and_is_audited(self):
        response = self.book_in_browser()
        appointment = Appointment.objects.get()
        self.assertRedirects(response, reverse("appointment_detail", args=[appointment.pk]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "scheduled")
        self.assertEqual(appointment.duration, 30)
        self.assertEqual(appointment.start_at.utcoffset(), timedelta(0))
        event = AppointmentEvent.objects.get()
        self.assertEqual(event.audit.actor, self.actor)
        self.assertEqual(event.audit.patient, self.patient)
        self.assertEqual(event.audit.action, "appointment_create")

    def test_confirm_without_review_is_rejected(self):
        response = self.client.post(reverse("appointment_create"), {**self.payload(), "action": "confirm"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_confirmation_cannot_be_tampered_with_or_reused_by_another_user(self):
        payload = self.payload()
        review = self.client.post(reverse("appointment_create"), {**payload, "action": "review"})
        token = review.context["review_token"]
        response = self.client.post(reverse("appointment_create"), {
            **payload, "duration": "60", "action": "confirm", "review_token": token,
        })
        self.assertEqual(response.status_code, 400)
        self.client.force_login(self.staff["Administrator"])
        response = self.client.post(reverse("appointment_create"), {
            **payload, "action": "confirm", "review_token": token,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_review_can_return_to_editing_without_saving(self):
        response = self.client.post(reverse("appointment_create"), {**self.payload(), "action": "edit"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_invalid_date_duration_and_physician_are_rejected(self):
        for changes in (
            {"start_at": "invalid"}, {"start_at": "2000-01-01T09:00"},
            {"duration": "0"}, {"duration": "8"}, {"duration": "245"},
            {"physician": str(self.staff["Nurse"].pk)}, {"patient": "999999"},
            {"appointment_type": ""}, {"version": "0"},
        ):
            with self.subTest(changes=changes):
                response = self.client.post(reverse("appointment_create"), {
                    **self.payload(**changes), "action": "review",
                })
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.context["form"].errors)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_overlapping_intervals_including_containment_are_rejected(self):
        save_appointment(self.actor, self.data())
        for offset, duration in ((0, 30), (15, 30), (-15, 30), (-15, 60), (5, 5)):
            with self.subTest(offset=offset, duration=duration):
                with self.assertRaises(AppointmentConflict):
                    save_appointment(self.actor, self.data(
                        start_at=self.start + timedelta(minutes=offset), duration=duration,
                    ))
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(AppointmentEvent.objects.count(), 1)

    def test_adjacent_intervals_and_different_physicians_are_allowed(self):
        save_appointment(self.actor, self.data())
        save_appointment(self.actor, self.data(start_at=self.start + timedelta(minutes=30)))
        save_appointment(self.actor, self.data(physician=self.other_doctor))
        self.assertEqual(Appointment.objects.count(), 3)

    def test_conflict_response_is_409_and_original_booking_is_preserved(self):
        first = save_appointment(self.actor, self.data())
        payload = self.payload()
        review = self.client.post(reverse("appointment_create"), {**payload, "action": "review"})
        response = self.client.post(reverse("appointment_create"), {
            **payload, "action": "confirm", "review_token": review.context["review_token"],
        })
        self.assertContains(response, "unavailable", status_code=409)
        self.assertEqual(Appointment.objects.get().pk, first.pk)

    def test_reschedule_updates_time_and_creates_event(self):
        appointment = save_appointment(self.actor, self.data())
        later = self.start + timedelta(hours=2)
        response = self.book_in_browser(
            self.payload(start_at=later.strftime("%Y-%m-%dT%H:%M")), appointment,
        )
        self.assertEqual(response.status_code, 302)
        appointment.refresh_from_db()
        self.assertEqual(appointment.start_at, later)
        self.assertEqual(appointment.version, 2)
        event = appointment.events.get(audit__action="appointment_reschedule")
        self.assertEqual(event.details["before"]["start"], self.start.astimezone(UTC).isoformat())
        self.assertEqual(event.audit.changed_fields, ["start_at", "end_at"])
        save_appointment(self.actor, self.data())
        self.assertEqual(Appointment.objects.count(), 2)

    def test_reschedule_can_change_physician(self):
        appointment = save_appointment(self.actor, self.data())
        updated = save_appointment(self.actor, self.data(physician=self.other_doctor), appointment.pk)
        self.assertEqual(updated.physician, self.other_doctor)

    def test_reschedule_cannot_change_patient(self):
        appointment = save_appointment(self.actor, self.data())
        other = Patient.objects.create(
            mrn="SCHEDULE-002", first_name="Other", last_name="Synthetic",
            dob="1990-01-01", sex="unknown",
        )
        with self.assertRaises(ValidationError):
            save_appointment(self.actor, self.data(patient=other), appointment.pk)
        appointment.refresh_from_db()
        self.assertEqual(appointment.patient, self.patient)

    def test_stale_reschedule_and_transition_are_rejected(self):
        appointment = save_appointment(self.actor, self.data())
        save_appointment(self.actor, self.data(start_at=self.start + timedelta(hours=1)), appointment.pk)
        with self.assertRaises(AppointmentConflict):
            save_appointment(self.actor, self.data(), appointment.pk)
        response = self.client.post(reverse("appointment_transition", args=[appointment.pk]), {
            "version": 1, "action": "cancel", "reason": "Synthetic change",
        })
        self.assertEqual(response.status_code, 409)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "scheduled")
        self.assertEqual(appointment.version, 2)

    def test_cancellation_requires_reason_and_releases_slot(self):
        appointment = save_appointment(self.actor, self.data())
        url = reverse("appointment_transition", args=[appointment.pk])
        self.assertEqual(self.client.post(url, {"version": 1, "action": "cancel"}).status_code, 400)
        response = self.client.post(url, {"version": 1, "action": "cancel", "reason": "Synthetic cancellation"})
        self.assertEqual(response.status_code, 302)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "cancelled")
        self.assertEqual(appointment.events.get(audit__action="appointment_cancel").reason, "Synthetic cancellation")
        save_appointment(self.actor, self.data())
        self.assertEqual(Appointment.objects.count(), 2)

    def test_checkin_records_actor_time_and_rejects_repeat(self):
        appointment = self.existing_today()
        url = reverse("appointment_transition", args=[appointment.pk])
        self.assertEqual(self.client.post(url, {"version": 1, "action": "arrive"}).status_code, 302)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "arrived")
        self.assertEqual(appointment.checked_in_by, self.actor)
        self.assertIsNotNone(appointment.checked_in_at)
        self.assertTrue(appointment.events.filter(audit__action="appointment_arrive").exists())
        response = self.client.post(url, {"version": 2, "action": "arrive"})
        self.assertEqual(response.status_code, 409)
        appointment.refresh_from_db()
        self.assertEqual(appointment.version, 2)

    def test_checkin_rejects_different_local_day(self):
        appointment = save_appointment(self.actor, self.data())
        with self.assertRaises(ValidationError):
            transition_appointment(self.actor, appointment.pk, "arrive", 1)

    def test_arrived_can_be_cancelled_but_not_rescheduled(self):
        appointment = self.existing_today()
        transition_appointment(self.actor, appointment.pk, "arrive", 1)
        with self.assertRaises(AppointmentConflict):
            save_appointment(self.actor, self.data(version=2), appointment.pk)
        cancelled = transition_appointment(self.actor, appointment.pk, "cancel", 2, "Synthetic reason")
        self.assertEqual(cancelled.status, "cancelled")
        self.assertIsNotNone(cancelled.checked_in_at)

    def test_no_show_requires_start_and_reason(self):
        future = save_appointment(self.actor, self.data())
        with self.assertRaises(ValidationError):
            transition_appointment(self.actor, future.pk, "no_show", 1, "Synthetic reason")
        past = self.existing_today(
            start_at=timezone.now() - timedelta(hours=1), end_at=timezone.now() - timedelta(minutes=30),
        )
        with self.assertRaises(ValidationError):
            transition_appointment(self.actor, past.pk, "no_show", 1)
        result = transition_appointment(self.actor, past.pk, "no_show", 1, "Did not arrive (demo)")
        self.assertEqual(result.status, "no_show")

    def test_terminal_and_unknown_transitions_are_rejected(self):
        appointment = save_appointment(self.actor, self.data())
        result = transition_appointment(self.actor, appointment.pk, "cancel", 1, "Synthetic reason")
        for action in ("cancel", "arrive", "no_show", "completed", "unknown"):
            with self.subTest(action=action), self.assertRaises(AppointmentConflict):
                transition_appointment(self.actor, result.pk, action, result.version, "Synthetic reason")

    def test_permissions_on_direct_get_and_post_requests(self):
        appointment = save_appointment(self.actor, self.data())
        for role in ("Physician", "Nurse"):
            self.client.force_login(self.staff[role])
            for url in (reverse("appointment_create"), reverse("appointment_edit", args=[appointment.pk])):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, self.payload()).status_code, 403)
            self.assertEqual(self.client.post(reverse("appointment_transition", args=[appointment.pk]), {
                "version": 1, "action": "cancel", "reason": "Not permitted",
            }).status_code, 403)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "scheduled")
        self.assertTrue(AuditEvent.objects.filter(action="access_denied").exists())

    def test_administrator_can_manage_and_services_also_enforce_roles(self):
        result = save_appointment(self.staff["Administrator"], self.data())
        self.assertEqual(result.status, "scheduled")
        for role in ("Physician", "Nurse"):
            with self.assertRaises(PermissionDenied):
                save_appointment(self.staff[role], self.data())
            with self.assertRaises(PermissionDenied):
                transition_appointment(self.staff[role], result.pk, "cancel", 1, "Not permitted")

    def test_anonymous_and_no_role_users_are_denied(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("schedule")).status_code, 302)
        self.assertEqual(self.client.post(reverse("appointment_create"), self.payload()).status_code, 302)
        outsider = get_user_model().objects.create_user("outsider")
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(reverse("schedule")).status_code, 403)

    def test_physician_own_scope_and_nurse_clinic_scope(self):
        own = save_appointment(self.actor, self.data())
        other = save_appointment(self.actor, self.data(physician=self.other_doctor))
        params = {"date": self.start.date().isoformat(), "view": "day"}
        self.client.force_login(self.doctor)
        response = self.client.get(reverse("schedule"), params)
        self.assertEqual([item.pk for item in response.context["appointments"]], [own.pk])
        self.assertEqual(self.client.get(reverse("appointment_detail", args=[other.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("schedule"), {
            **params, "physician": self.other_doctor.pk,
        }).status_code, 400)
        response = self.client.get(reverse("patient_detail", args=[self.patient.pk]))
        self.assertEqual([item.pk for item in response.context["appointments"]], [own.pk])
        self.client.force_login(self.staff["Nurse"])
        self.assertEqual(len(self.client.get(reverse("schedule"), params).context["appointments"]), 2)
        self.assertEqual(self.client.get(reverse("appointment_detail", args=[other.pk])).status_code, 200)

    def test_daily_and_weekly_calendar_and_search_filters(self):
        appointment = save_appointment(self.actor, self.data())
        params = {"date": self.start.date().isoformat(), "view": "day", "physician": self.doctor.pk}
        for mode in ("day", "week"):
            response = self.client.get(reverse("schedule"), {**params, "view": mode, "q": self.patient.mrn})
            self.assertContains(response, "DEMO — NOT FOR CLINICAL USE")
            self.assertContains(response, "Synthetic follow-up")
            self.assertEqual(response.context["appointments"][0].pk, appointment.pk)
            self.assertEqual(len(response.context["columns"]), 1 if mode == "day" else 7)
        self.assertEqual(len(self.client.get(reverse("schedule"), {
            **params, "q": "unmatched",
        }).context["appointments"]), 0)

    def test_checkin_worklist_searches_selected_date(self):
        appointment = self.existing_today()
        response = self.client.get(reverse("checkin_worklist"), {
            "date": timezone.localdate().isoformat(), "q": self.patient.mrn,
        })
        self.assertEqual(response.context["appointments"][0].pk, appointment.pk)
        self.assertContains(response, "Arrivals worklist")
        full_name = f"{self.patient.first_name} {self.patient.last_name}"
        self.assertEqual(len(self.client.get(reverse("checkin_worklist"), {"q": full_name}).context["appointments"]), 1)

    def test_cross_midnight_appointment_visible_on_both_days(self):
        start = self.start.replace(hour=23, minute=45)
        appointment = save_appointment(self.actor, self.data(start_at=start, duration=30))
        for day in (start.date(), start.date() + timedelta(days=1)):
            response = self.client.get(reverse("schedule"), {"date": day.isoformat(), "view": "day"})
            self.assertEqual(response.context["appointments"][0].pk, appointment.pk)
            self.assertTrue(any(cell["appointments"] for row in response.context["rows"] for cell in row["cells"]))

    def test_invalid_filters_do_not_crash(self):
        for values in ({"date": "bad"}, {"date": "9999-12-31"}, {"view": "unknown"}, {"physician": "99999"}):
            self.assertEqual(self.client.get(reverse("schedule"), values).status_code, 400)

    def test_patient_search_selector_and_patient_context(self):
        response = self.client.get(reverse("appointment_create"), {"q": self.patient.mrn})
        self.assertEqual(list(response.context["form"].fields["patient"].queryset), [self.patient])
        appointment = save_appointment(self.actor, self.data())
        response = self.client.get(reverse("patient_detail", args=[self.patient.pk]))
        self.assertContains(response, reverse("appointment_detail", args=[appointment.pk]))

    def test_audit_failure_rolls_back_creation_and_transition(self):
        with patch("careflow.scheduling.services.AppointmentEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                save_appointment(self.actor, self.data())
        self.assertEqual(Appointment.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.filter(action="appointment_create").count(), 0)
        appointment = self.existing_today()
        with patch("careflow.scheduling.services.AppointmentEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                transition_appointment(self.actor, appointment.pk, "arrive", 1)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "scheduled")
        self.assertIsNone(appointment.checked_in_at)

    def test_database_busy_is_a_retryable_conflict(self):
        with patch("careflow.scheduling.services._lock_providers", side_effect=OperationalError("database is locked")):
            with self.assertRaises(AppointmentConflict):
                save_appointment(self.actor, self.data())
        self.assertEqual(Appointment.objects.count(), 0)

    def test_get_and_missing_csrf_cannot_change_status(self):
        appointment = self.existing_today()
        url = reverse("appointment_transition", args=[appointment.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.actor)
        self.assertEqual(secure.post(url, {"version": 1, "action": "arrive"}).status_code, 403)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "scheduled")

    def test_daylight_saving_validation_and_elapsed_duration(self):
        zone = ZoneInfo("America/Chicago")
        year = timezone.localdate().year + 2
        march = datetime(year, 3, 8)
        spring = (march + timedelta(days=(6 - march.weekday()) % 7)).date()
        november = datetime(year, 11, 1)
        fall = (november + timedelta(days=(6 - november.weekday()) % 7)).date()
        with timezone.override(zone):
            for day, clock in ((spring, "02:30"), (fall, "01:30")):
                form = AppointmentForm(self.actor, self.payload(start_at=f"{day.isoformat()}T{clock}"))
                self.assertFalse(form.is_valid())
                self.assertIn("start_at", form.errors)
            for day, hour, expected_end_hour in ((spring, 1, 4), (fall, 0, 1)):
                start = datetime.combine(day, time(hour, 30), tzinfo=zone)
                appointment = save_appointment(self.actor, self.data(start_at=start, duration=120))
                appointment.refresh_from_db()
                self.assertEqual(appointment.duration, 120)
                self.assertEqual(timezone.localtime(appointment.end_at).hour, expected_end_hour)
                response = self.client.get(reverse("schedule"), {"date": day.isoformat(), "view": "day"})
                self.assertEqual(response.context["appointments"][0].pk, appointment.pk)


class ConcurrentBookingTests(SchedulingFixture, TransactionTestCase):
    def setUp(self):
        self.make_fixture()

    def test_two_concurrent_overlapping_bookings_have_only_one_winner(self):
        barrier = Barrier(2)

        def attempt():
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=self.actor.pk)
                barrier.wait(timeout=10)
                try:
                    save_appointment(actor, self.data())
                    return "saved"
                except AppointmentConflict:
                    return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(results, ["saved", "conflict"])
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(AppointmentEvent.objects.count(), 1)
