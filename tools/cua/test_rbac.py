"""Check scoped redirects, write denial and protected response content offline."""
import unittest
from types import SimpleNamespace
from urllib.parse import urlsplit

from rbac import RBACPolicy


class RBACPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {"result": 1, "denied_markers": ["PRIVATE-FIXTURE-MARKER"]}

    def test_only_expected_login_redirect_is_allowed(self):
        policy = RBACPolicy("anonymous", self.fixture)
        self.assertTrue(policy.allows(urlsplit("/login/?next=/app/patients/")))
        self.assertFalse(policy.allows(urlsplit("/login/?next=/app/patients/2/")))
        self.assertFalse(policy.allows(urlsplit("/portal/results/1/")))
        self.assertFalse(policy.allow_post("/login/", "synthetic"))

    def test_denied_response_with_protected_content_stops_probe(self):
        policy = RBACPolicy("patient", self.fixture)
        request = SimpleNamespace(url="http://127.0.0.1/portal/results/1/", is_navigation_request=lambda: True)
        response = SimpleNamespace(status=404, text=lambda: "PRIVATE-FIXTURE-MARKER")
        with self.assertRaisesRegex(RuntimeError, "protected fixture marker"):
            policy.observe_read(request, response)
        self.assertEqual(policy.observations, {})
