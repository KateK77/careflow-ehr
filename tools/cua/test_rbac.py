"""Check scoped redirects, write denial and protected response content offline."""
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

from diagnostics import Diagnostics
from rbac import RBACPolicy
from smoke import ROOT, run


class RBACPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {"result": 1, "denied_markers": ["PRIVATE-FIXTURE-MARKER"]}

    def test_only_expected_login_redirect_is_allowed(self):
        policy = RBACPolicy("anonymous-staff", self.fixture)
        self.assertTrue(policy.allows(urlsplit("/login/?next=/app/patients/")))
        self.assertFalse(policy.allows(urlsplit("/login/?next=/app/patients/2/")))
        self.assertFalse(policy.allows(urlsplit("/portal/results/1/")))
        self.assertFalse(policy.allow_post("/login/", "synthetic"))

    def test_staff_redirect_in_offline_chromium(self):
        self.verify_browser("staff", "Staff directory", "/login/?next=/app/patients/")

    def test_patient_redirect_in_offline_chromium(self):
        self.verify_browser("patient", "Patient dashboard", "/portal/login/?next=/portal/")

    def verify_browser(self, portal, label, redirect):
        with tempfile.TemporaryDirectory() as evidence:
            diagnostics = Diagnostics()
            run(Namespace(scenario=f"rbac-anonymous-{portal}", mode="offline",
                          evidence_dir=Path(evidence) / "captures",
                          django_python=ROOT / ".venv/Scripts/python.exe"), diagnostics)
            self.assertEqual(diagnostics.checks, {
                label: {"verified": True, "http_status": 302, "redirect": redirect},
            })
            self.assertEqual(diagnostics.attempts, 0)

    def test_wrong_redirect_stops_probe(self):
        policy = RBACPolicy("anonymous-patient", self.fixture)
        request = SimpleNamespace(url="http://127.0.0.1/portal/", is_navigation_request=lambda: True)
        response = SimpleNamespace(status=302, text=lambda: "", headers={"location": "/login/"})
        with self.assertRaisesRegex(RuntimeError, "Unexpected redirect destination"):
            policy.observe_read(request, response)

    def test_denied_response_with_protected_content_stops_probe(self):
        policy = RBACPolicy("patient", self.fixture)
        request = SimpleNamespace(url="http://127.0.0.1/portal/results/1/", is_navigation_request=lambda: True)
        response = SimpleNamespace(status=404, text=lambda: "PRIVATE-FIXTURE-MARKER")
        with self.assertRaisesRegex(RuntimeError, "protected fixture marker"):
            policy.observe_read(request, response)
        self.assertEqual(policy.observations, {})
