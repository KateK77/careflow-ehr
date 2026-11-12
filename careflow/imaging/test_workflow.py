import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from careflow.clinical.models import Note
from .models import ExamWorkflow, ImagingReview
from .tests import ImagingFixture
from .workflow import acknowledge, current_report, radiology_command


class WorkflowFixture(ImagingFixture):
    def setup_workflow(self):
        self.setup_imaging()
        group = Group.objects.create(name="RadiologyStaff")
        self.rad = get_user_model().objects.create_user("synthetic-radiology", password=self.password)
        self.other_rad = get_user_model().objects.create_user("synthetic-radiology-other")
        self.rad.groups.add(group)
        self.other_rad.groups.add(group)
        self.order = self.imaging("imaging_sign", self.draft_order())

    def command(self, action, actor=None, key=None, **data):
        self.order = radiology_command(actor or self.rad, self.order.pk, self.physician.pk, action,
                                       self.order.version, key or uuid.uuid4(), True, **data)
        self.order.refresh_from_db()
        return self.order

    def perform_exam(self):
        self.command("imaging_assign")
        self.command("imaging_staff_schedule", scheduled_at=timezone.now() + timedelta(days=1))
        self.command("imaging_exam_start")
        self.command("imaging_exam_perform", study_id="SYN-STUDY-1", body_site="Synthetic region")

    def report_final(self):
        self.perform_exam()
        self.command("imaging_report_draft", findings="Synthetic draft findings", impression="Synthetic impression")
        self.command("imaging_exam_complete")
        self.command("imaging_final")
        return current_report(self.order)

    def review(self, report, key=None):
        self.order.refresh_from_db()
        self.order = acknowledge(self.physician, self.order.pk, self.physician.pk,
                                 report.pk, self.order.version, key or uuid.uuid4(), True)
        return self.order


class ImagingWorkflowTests(WorkflowFixture, TestCase):
    def setUp(self):
        self.setup_workflow()

    def test_role_and_assignment_url_boundaries(self):
        route = reverse("imaging_exam", args=[self.order.pk])
        self.client.force_login(self.rad)
        self.assertNotContains(self.client.get(route), self.patient.mrn)
        self.command("imaging_assign")
        self.assertContains(self.client.get(route), self.patient.mrn)
        self.client.force_login(self.other_rad)
        self.assertEqual(self.client.get(route).status_code, 404)
        self.assertEqual(self.client.post(route, {}).status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(route).status_code, 403)
        self.client.force_login(self.rad)
        chart = reverse("patient_chart", args=[self.patient.pk])
        self.assertEqual(self.client.get(chart).status_code, 403)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.rad)
        self.assertEqual(protected.post(route, {}).status_code, 403)

    def test_exam_state_guards_post_encounter_and_note_preservation(self):
        self.finish_encounter()
        before = Note.objects.filter(encounter=self.encounter).values().get()
        with self.assertRaises(PermissionDenied):
            self.command("imaging_exam_start")
        self.perform_exam()
        with self.assertRaises(ValidationError):
            self.imaging("imaging_cancel", self.order, reason="Too late")
        with self.assertRaises(ValidationError):
            self.command("imaging_final")
        self.command("imaging_exam_complete")
        self.assertEqual(self.order.workflow.status, "completed")
        self.assertEqual(Note.objects.filter(encounter=self.encounter).values().get(), before)
        self.encounter.refresh_from_db()
        self.assertEqual(self.encounter.status, "completed")

    def test_preliminary_draft_and_report_role_visibility(self):
        self.perform_exam()
        route = reverse("imaging_report", args=[self.order.pk])
        self.command("imaging_report_draft", findings="HIDDEN_DRAFT", impression="Synthetic impression")
        self.client.force_login(self.physician)
        self.assertNotContains(self.client.get(route), "HIDDEN_DRAFT")
        self.command("imaging_preliminary")
        self.assertContains(self.client.get(route), "HIDDEN_DRAFT")
        self.client.force_login(self.staff["Nurse"])
        self.assertNotContains(self.client.get(route), "HIDDEN_DRAFT")
        self.assertEqual(self.client.post(route, {}).status_code, 403)
        self.command("imaging_report_draft", findings="UPDATED_FINAL", impression="Synthetic final")
        self.command("imaging_exam_complete")
        self.command("imaging_final")
        self.assertContains(self.client.get(route), "UPDATED_FINAL")
        self.assertNotContains(self.client.get(route), "HIDDEN_DRAFT")
        for actor, code in [(self.other, 404), (self.admin, 403), (self.rad, 404)]:
            self.client.force_login(actor)
            self.assertEqual(self.client.get(route).status_code, code)

    def test_acknowledgement_correction_and_withdrawal_preserve_history(self):
        final = self.report_final()
        self.client.force_login(self.physician)
        queue = reverse("imaging_review_worklist")
        self.assertContains(self.client.get(queue), "Synthetic X-ray")
        self.review(final)
        self.assertNotContains(self.client.get(queue), "Synthetic X-ray")
        self.command("imaging_correct", findings="CORRECTED_VALUE", impression="Synthetic revised impression",
                     reason="Synthetic correction reason")
        corrected = current_report(self.order)
        self.assertEqual(corrected.based_on, final)
        with self.assertRaises(ValidationError):
            self.review(final)
        self.assertContains(self.client.get(queue), "Synthetic X-ray")
        self.review(corrected)
        self.command("imaging_withdraw", reason="Synthetic withdrawal", withdrawal_kind="report_error")
        path = reverse("imaging_report", args=[self.order.pk])
        self.assertContains(self.client.get(path), "Report content is unavailable")
        self.assertNotContains(self.client.get(path), "CORRECTED_VALUE")
        self.assertEqual(ImagingReview.objects.count(), 2)
        final.refresh_from_db()
        self.assertEqual(final.findings, "Synthetic draft findings")
        with self.assertRaises(ValidationError):
            final.save()

    def test_context_withdrawal_quarantines_staff_and_clinical_views(self):
        report = self.report_final()
        self.command("imaging_withdraw", reason="Synthetic mismatch", withdrawal_kind="context_error")
        self.client.force_login(self.rad)
        staff = self.client.get(reverse("imaging_exam", args=[self.order.pk]))
        self.assertContains(staff, "Report content is restricted")
        self.assertNotContains(staff, report.findings)
        self.assertNotContains(staff, "SYN-STUDY-1")
        for actor in [self.physician, self.staff["Nurse"]]:
            self.client.force_login(actor)
            response = self.client.get(reverse("imaging_report", args=[self.order.pk]))
            self.assertNotContains(response, report.findings)
        self.assertEqual(self.order.reports.get(pk=report.pk).findings, report.findings)

    def test_replay_stale_version_and_audit_rollback(self):
        key = uuid.uuid4()
        args = (self.rad, self.order.pk, self.physician.pk, "imaging_assign", self.order.version, key, True)
        assigned = radiology_command(*args)
        self.assertEqual(radiology_command(*args).pk, assigned.pk)
        self.assertEqual(ExamWorkflow.objects.count(), 1)
        with self.assertRaises(ValidationError):
            self.command("imaging_staff_schedule", scheduled_at=timezone.now() + timedelta(days=1))
        self.order.refresh_from_db()
        with patch("careflow.imaging.services.ImagingEvent.objects.create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                self.command("imaging_staff_schedule", scheduled_at=timezone.now() + timedelta(days=1))
        self.order.refresh_from_db()
        self.assertFalse(hasattr(self.order, "exam"))


class ImagingConcurrencyTests(WorkflowFixture, TransactionTestCase):
    def test_competing_assignment_has_one_owner_and_one_event(self):
        self.setup_workflow()
        barrier = Barrier(2)

        def compete(actor):
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                radiology_command(actor, self.order.pk, self.physician.pk, "imaging_assign",
                                  self.order.version, uuid.uuid4(), True)
                return True
            except (ValidationError, PermissionDenied):
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(compete, [self.rad, self.other_rad]))
        self.assertEqual(results.count(True), 1)
        self.assertEqual(ExamWorkflow.objects.count(), 1)
        self.assertEqual(self.order.events.filter(audit__action="imaging_assign").count(), 1)
