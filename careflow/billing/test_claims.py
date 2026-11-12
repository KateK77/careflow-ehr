import uuid
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .claims import change_appeal, change_claim, create_claim, position, record_payment
from .models import MockClaim, SimulatedPayment
from .services import create_coverage
from .tests import BillingFixture


class ClaimFixture(BillingFixture):
    def setup_claims(self):
        self.setup_billing()
        self.statement = self.released()
        self.policy = create_coverage(self.biller, self.patient.pk, self.coverage_data(), 0, uuid.uuid4())

    def claim(self, key=None):
        return create_claim(self.biller, self.statement.pk, self.policy.pk, key or uuid.uuid4(), True)

    def advance(self, claim, action, key=None, **kwargs):
        return change_claim(self.biller, claim.pk, claim.version, key or uuid.uuid4(), "billing_claim_" + action,
                            True, **kwargs)

    def denial(self):
        claim = self.advance(self.claim(), "submit")
        claim = self.advance(claim, "queue")
        return self.advance(claim, "decide", outcome="denied", payer_cents=0, denial="demo_scope")

    def appeal(self, claim, action, appeal=None, **kwargs):
        claim.refresh_from_db()
        return change_appeal(self.biller, claim.pk, claim.version, appeal.pk if appeal else None,
                             appeal.version if appeal else 0, uuid.uuid4(), "billing_appeal_" + action, True, **kwargs)

    def payment(self, reference, *, key=None, version=None, **kwargs):
        current = position(type(self.statement).objects.get(pk=self.statement.pk))
        return record_payment(self.biller, self.statement.pk, version or current["version"], key or uuid.uuid4(),
                              True, reference, **kwargs)


class ClaimTests(ClaimFixture, TestCase):
    def setUp(self):
        self.setup_claims()

    def test_claim_state_coverage_isolation_and_replay(self):
        foreign = create_coverage(self.biller, self.foreign.pk,
                                  {**self.coverage_data(), "policy": "SYN-FOREIGN"}, 0, uuid.uuid4())
        with self.assertRaises(ValidationError):
            create_claim(self.biller, self.statement.pk, foreign.pk, uuid.uuid4(), True)
        key = uuid.uuid4()
        draft = self.claim(key)
        self.assertEqual(self.claim(key).pk, draft.pk)
        with self.assertRaises(ValidationError):
            self.claim()
        with self.assertRaises(ValidationError):
            self.advance(draft, "decide", outcome="approved", payer_cents=3765)
        submitted = self.advance(draft, "submit")
        with self.assertRaises(ValidationError):
            self.advance(draft, "queue")
        pending = self.advance(submitted, "queue")
        with self.assertRaises(ValidationError):
            self.advance(pending, "decide", outcome="approved", payer_cents=3000)
        approved = self.advance(pending, "decide", outcome="approved", payer_cents=3765)
        self.assertEqual(approved.status, "approved")
        self.assertEqual(approved.coverage, self.policy)
        self.assertEqual(approved.decisions.count(), 1)

    def test_denial_draft_revision_submit_overturn_and_immutable_history(self):
        claim = self.denial()
        denial = claim.decisions.get()
        line = self.statement.lines.get()
        draft = self.appeal(claim, "save", explanation="Synthetic draft", line_id=line.pk)
        draft = self.appeal(claim, "save", draft, explanation="Synthetic revised draft", line_id=line.pk)
        submitted = self.appeal(claim, "submit", draft)
        self.assertEqual(MockClaim.objects.get(pk=claim.pk).status, "denied")
        self.appeal(claim, "overturn", submitted, resolution="Synthetic review", outcome="partial", payer_cents=2000)
        claim.refresh_from_db()
        self.assertEqual(claim.status, "partial")
        self.assertEqual(claim.decisions.count(), 2)
        denial.refresh_from_db()
        self.assertEqual(denial.get_denial_display(), "Synthetic plan scope")
        self.assertEqual(self.statement.total_cents, 3765)
        with self.assertRaises(ValidationError):
            denial.save()

    def test_appeal_uphold_and_invalid_reference(self):
        claim = self.denial()
        with self.assertRaises(ValidationError):
            self.appeal(claim, "save", explanation="Synthetic evidence", line_id=99999)
        appeal = self.appeal(claim, "save", explanation="Synthetic evidence")
        appeal = self.appeal(claim, "submit", appeal)
        appeal = self.appeal(claim, "uphold", appeal, resolution="Synthetic policy limit")
        self.assertEqual(appeal.status, "upheld")
        self.assertEqual(claim.decisions.count(), 2)
        self.assertEqual(claim.decisions.first().denial, "demo_scope")

    def test_patient_and_payer_ledger_partial_full_reversal_and_stale_writes(self):
        claim = self.advance(self.advance(self.claim(), "submit"), "queue")
        self.advance(claim, "decide", outcome="partial", payer_cents=2000)
        starting = position(type(self.statement).objects.get(pk=self.statement.pk))
        key = uuid.uuid4()
        first = self.payment("SYN-P1", key=key, version=starting["version"], source="patient", cents=765)
        self.assertEqual(self.payment("SYN-P1", key=key, version=starting["version"], source="patient", cents=765), first)
        with self.assertRaises(ValidationError):
            self.payment("SYN-P2", version=starting["version"], source="patient", cents=1000)
        with self.assertRaises(ValidationError):
            self.payment("SYN-P2", source="patient", cents=1001)
        self.payment("SYN-P2", source="patient", cents=1000)
        payer = self.payment("SYN-PAYER", source="payer", cents=2000)
        summary = position(type(self.statement).objects.get(pk=self.statement.pk))
        self.assertEqual((summary["status"], summary["patient_due"], summary["payer_due"]), ("Paid", 0, 0))
        reversal = self.payment("SYN-REVERSE", reversal_id=payer.pk, reason="Synthetic duplicate review")
        self.assertEqual(reversal.reversal_of, payer)
        with self.assertRaises(ValidationError):
            self.payment("SYN-SECOND-REV", reversal_id=payer.pk, reason="Repeated reversal")
        self.assertEqual(position(type(self.statement).objects.get(pk=self.statement.pk))["payer_due"], 2000)
        with self.assertRaises(ValidationError):
            payer.save()

    def test_payments_and_appeal_cannot_conflict_or_bypass_roles(self):
        claim = self.denial()
        self.payment("SYN-PRE-APPEAL", source="patient", cents=3000)
        appeal = self.appeal(claim, "save", explanation="Synthetic reconsideration")
        with self.assertRaises(ValidationError):
            self.payment("SYN-PENDING", source="patient", cents=1)
        appeal = self.appeal(claim, "submit", appeal)
        with self.assertRaises(ValidationError):
            self.appeal(claim, "overturn", appeal, resolution="Invalid allocation", outcome="partial", payer_cents=1000)
        self.assertEqual(claim.decisions.count(), 1)
        with self.assertRaises(PermissionDenied):
            record_payment(self.admin, self.statement.pk, "0:0", uuid.uuid4(), True, "SYN-FORBIDDEN", source="patient", cents=1)

    def test_atomic_payment_and_decision_rollback(self):
        claim = self.advance(self.advance(self.claim(), "submit"), "queue")
        with patch("careflow.billing.services.BillingEvent.objects.create", side_effect=RuntimeError("audit failure")):
            with self.assertRaises(RuntimeError):
                self.advance(claim, "decide", outcome="approved", payer_cents=3765)
        claim.refresh_from_db()
        self.assertEqual(claim.status, "pending")
        self.assertFalse(claim.decisions.exists())
        self.advance(claim, "decide", outcome="approved", payer_cents=3765)
        with patch("careflow.billing.services.BillingEvent.objects.create", side_effect=RuntimeError("audit failure")):
            with self.assertRaises(RuntimeError):
                self.payment("SYN-ROLLBACK", source="payer", cents=1)
        self.assertFalse(SimulatedPayment.objects.exists())

    def test_staff_and_patient_route_isolation_csrf_and_minimum_history(self):
        self.payment("SYN-INTERNAL-REF", source="patient", cents=100)
        patient_route = reverse("portal_payments", args=[self.statement.pk])
        staff_route = reverse("billing_payments", args=[self.statement.pk])
        self.client.force_login(self.portal_b)
        self.assertEqual(self.client.get(patient_route).status_code, 404)
        self.client.force_login(self.portal_a)
        response = self.client.get(patient_route)
        self.assertContains(response, "$36.65")
        self.assertNotContains(response, "SYN-INTERNAL-REF")
        self.assertEqual(self.client.get(staff_route).status_code, 403)
        self.assertEqual(self.client.post(staff_route, {}).status_code, 403)
        self.client.force_login(self.staff["FrontDesk"])
        self.assertEqual(self.client.get(reverse("billing_claims")).status_code, 403)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.biller)
        self.assertEqual(protected.post(staff_route, {}).status_code, 403)
        self.client.force_login(self.biller)
        workspace = self.client.get(reverse("billing_claims"))
        self.assertContains(workspace, "<span>BillingStaff</span>", html=True)
