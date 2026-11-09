import os
import re
import secrets
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from careflow.patients.models import Patient
from .models import Appointment


@override_settings(DEBUG=True)
class SchedulingBrowserTests(StaticLiveServerTestCase):
    """Optional browser workflow using an isolated test database."""

    def test_review_reschedule_cancel_and_checkin(self):
        from playwright.sync_api import expect, sync_playwright

        password = secrets.token_urlsafe(24)
        with patch.dict("os.environ", {
            "CAREFLOW_ALLOW_DEMO_SEED": "1", "CAREFLOW_DEMO_PASSWORD": password,
        }):
            call_command("seed_synthetic", stdout=StringIO())
        physician = get_user_model().objects.get(username="physician.demo")
        frontdesk = get_user_model().objects.get(username="frontdesk.demo")
        patient = Patient.objects.get(mrn="DEMO-0001")
        arriving_patient = Patient.objects.get(mrn="DEMO-0002")
        today = timezone.localtime().replace(hour=9, minute=0, second=0, microsecond=0)
        arrival = Appointment.objects.create(
            patient=arriving_patient, physician=physician, start_at=today,
            end_at=today + timedelta(minutes=30), appointment_type="Synthetic arrival",
        )
        future = today + timedelta(days=2)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(self.live_server_url + "/login/")
            page.get_by_label("Username").fill("frontdesk.demo")
            page.get_by_label("Password").fill(password)
            page.get_by_role("button", name="Sign in to workspace").click()
            page.wait_for_url("**/app/dashboard/")
            page.get_by_role("link", name="Schedule", exact=True).click()
            page.get_by_role("link", name="New appointment", exact=True).click()
            page.get_by_label("Find a patient by name or MRN").fill(patient.mrn)
            page.get_by_role("button", name="Find patient", exact=True).click()
            page.locator("#id_patient").select_option(str(patient.pk))
            page.locator("#id_physician").select_option(str(physician.pk))
            page.locator("#id_start_at").fill(future.strftime("%Y-%m-%dT%H:%M"))
            page.locator("#id_appointment_type").fill("Browser appointment")
            page.get_by_role("button", name="Review appointment").click()
            expect(page.get_by_role("heading", name="Review appointment")).to_be_visible()
            page.get_by_role("button", name="Confirm appointment").click()
            page.wait_for_url(re.compile(r"/app/appointments/\d+/$"))
            booking_pk = int(page.url.rstrip("/").split("/")[-1])
            page.get_by_role("link", name="Reschedule / edit").click()
            page.locator("#id_start_at").fill((future + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"))
            page.get_by_role("button", name="Review appointment").click()
            page.get_by_role("button", name="Confirm appointment").click()
            page.wait_for_url(re.compile(r"/app/appointments/\d+/$"))
            page.goto(self.live_server_url + f"/app/schedule/?date={future.date()}&view=week&physician={physician.pk}")
            expect(page.locator(f".calendar-booking[href='/app/appointments/{booking_pk}/']")).to_have_count(1)
            self.assertIn("Browser appointment", page.inner_text("main"))
            output = os.environ.get("CAREFLOW_BROWSER_SCREENSHOT_DIR")
            if output:
                os.makedirs(output, exist_ok=True)
                page.screenshot(path=os.path.join(output, "scheduling-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), page.evaluate("window.innerWidth"))
            if output:
                page.screenshot(path=os.path.join(output, "scheduling-mobile.png"), full_page=True)
            page.goto(self.live_server_url + f"/app/appointments/{booking_pk}/")
            page.get_by_label("Cancellation reason").fill("Synthetic browser cancellation")
            page.get_by_role("button", name="Cancel appointment", exact=True).click()
            expect(page.locator("main .tag").first).to_have_text("Cancelled")
            page.goto(self.live_server_url + f"/app/check-in/?date={today.date()}&q={arriving_patient.mrn}")
            page.get_by_role("link", name="View appointment", exact=True).click()
            page.get_by_role("button", name="Mark Arrived").click()
            expect(page.locator("main .tag").first).to_have_text("Arrived")
            self.assertEqual(errors, [])
            browser.close()

        booking = Appointment.objects.get(pk=booking_pk)
        self.assertEqual(booking.status, "cancelled")
        self.assertEqual(booking.version, 3)
        self.assertEqual(Appointment.objects.count(), 2)
        arrival.refresh_from_db()
        self.assertEqual(arrival.checked_in_by, frontdesk)
        self.assertIsNotNone(arrival.checked_in_at)
