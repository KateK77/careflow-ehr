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
        self.verify_browser("anonymous-staff", "Staff directory", 302, "/login/?next=/app/patients/")

    def test_patient_redirect_in_offline_chromium(self):
        self.verify_browser("anonymous-patient", "Patient dashboard", 302, "/portal/login/?next=/portal/")

    def test_patient_own_dashboard(self):
        self.verify_browser("patient-dashboard", "Own dashboard", 200, "/portal/")

    def test_patient_other_result_denied(self):
        self.verify_browser("patient-other-result", "Other patient result", 404, "/portal/results/1/")

    def test_owner_released_result(self):
        self.verify_browser("owner-result", "Own released result", 200, "/portal/results/1/")

    def test_physician_directory(self):
        self.verify_browser("physician-directory", "Permitted staff directory", 200, "/app/patients/")

    def test_physician_demographic_edit_denied(self):
        self.verify_browser("physician-demographic-denial", "Restricted demographic edit", 403,
                            "/app/patients/1/edit/")

    def verify_browser(self, scenario, label, status, destination):
        with tempfile.TemporaryDirectory() as evidence:
            diagnostics = Diagnostics()
            run(Namespace(scenario=f"rbac-{scenario}", mode="offline",
                          evidence_dir=Path(evidence) / "captures",
                          django_python=ROOT / ".venv/Scripts/python.exe"), diagnostics)
            self.assertEqual(diagnostics.checks, {
                label: {"verified": True, "http_status": status, "destination": destination,
                        "redirect": destination if status == 302 else None},
            })
            self.assertEqual(diagnostics.attempts, 0)

    def test_wrong_redirect_stops_probe(self):
        policy = RBACPolicy("anonymous-patient", self.fixture)
        request = SimpleNamespace(url="http://127.0.0.1/portal/", is_navigation_request=lambda: True)
        response = SimpleNamespace(status=302, text=lambda: "", headers={"location": "/login/"})
        with self.assertRaisesRegex(RuntimeError, "Unexpected redirect destination"):
            policy.observe_read(request, response)

    def test_denied_response_with_protected_content_stops_probe(self):
        policy = RBACPolicy("patient-other-result", self.fixture)
        request = SimpleNamespace(url="http://127.0.0.1/portal/results/1/", is_navigation_request=lambda: True)
        response = SimpleNamespace(status=404, text=lambda: "PRIVATE-FIXTURE-MARKER")
        with self.assertRaisesRegex(RuntimeError, "protected fixture marker"):
            policy.observe_read(request, response)
        self.assertEqual(policy.observations, {})
