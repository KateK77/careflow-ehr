from datetime import timedelta

from urllib.parse import urlsplit

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.utils import timezone

from .models import PatientAppointmentRequest
from .tests import PortalFixture


class PortalCommunicationBrowserTests(PortalFixture, StaticLiveServerTestCase):
    def test_patient_and_staff_message_and_request_workflow(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_portal()
        for user in [self.admin, self.physician]:
            user.set_password(self.password)
            user.save(update_fields=["password"])
        slot = timezone.localtime(timezone.now() + timedelta(days=3)).strftime("%Y-%m-%dT10:00")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            patient = browser.new_page(viewport={"width": 390, "height": 800})
            patient.set_default_timeout(7000)
            staff = browser.new_page()
            staff.set_default_timeout(7000)

            def login(page, actor, route):
                page.goto(self.live_server_url + reverse(route))
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(self.password)
                label = "Sign in" if route == "portal_login" else "Sign in to workspace"
                page.get_by_role("button", name=label, exact=True).click()

            login(patient, self.portal_a, "portal_login")
            patient.get_by_role("link", name="Messages", exact=True).click()
            patient.get_by_role("link", name="New message").click()
            patient.get_by_label("Clinician").select_option(str(self.physician.pk))
            patient.get_by_label("Subject").fill("Synthetic portal question")
            patient.locator("textarea[name=body]").fill("Synthetic patient text")
            patient.get_by_role("button", name="Send message").click()
            expect(patient.get_by_text("Synthetic patient text")).to_be_visible()
            thread_path = urlsplit(patient.url).path

            login(staff, self.physician, "login")
            staff.get_by_role("link", name="Patient messages").click()
            staff.get_by_role("link", name="Synthetic portal question").click()
            staff.get_by_role("button", name="Mark as read").click()
            staff.locator("textarea[name=body]").fill("Synthetic physician reply")
            staff.get_by_role("button", name="Send reply").click()
            expect(staff.get_by_text("Synthetic physician reply")).to_be_visible()
            patient.get_by_role("link", name="Dashboard", exact=True).click()
            expect(patient.get_by_role("link", name="Unread conversations (1)")).to_be_visible()
            patient.get_by_role("link", name="Unread conversations (1)").click()
            patient.get_by_role("link", name="Synthetic portal question").click()
            expect(patient.get_by_text("Synthetic physician reply")).to_be_visible()
            patient.get_by_role("button", name="Mark as read").click()

            patient.get_by_role("link", name="Appointment requests").click()
            patient.get_by_role("link", name="Request an appointment").click()
            patient.get_by_label("Clinician").select_option(str(self.physician.pk))
            patient.get_by_label("Proposed clinic-local start").fill(slot)
            patient.get_by_label("Duration in minutes").fill("20")
            patient.get_by_label("Synthetic reason").fill("Synthetic portal booking")
            patient.get_by_role("button", name="Submit request").click()
            expect(patient.get_by_text("Pending", exact=True)).to_be_visible()
            request_path = urlsplit(patient.url).path

            scheduling = browser.new_page()
            login(scheduling, self.admin, "login")
            scheduling.get_by_role("link", name="Portal appointment requests").click()
            scheduling.get_by_role("link", name="New appointment").click()
            scheduling.get_by_label("Response to patient").fill("Synthetic slot confirmed")
            scheduling.get_by_label("Confirm this decision").check()
            scheduling.get_by_role("button", name="Submit decision").click()
            expect(scheduling.get_by_text("Synthetic slot confirmed")).to_be_visible()
            patient.reload()
            expect(patient.get_by_text("Synthetic slot confirmed")).to_be_visible()
            expect(patient.get_by_text("Current appointment status")).to_be_visible()
            patient.get_by_role("button", name="Sign out").click()
            login(patient, self.portal_b, "portal_login")
            for path in (thread_path, request_path):
                response = patient.goto(self.live_server_url + path)
                self.assertEqual(response.status, 404)
            browser.close()
        self.assertEqual(PatientAppointmentRequest.objects.get().status, "approved")
