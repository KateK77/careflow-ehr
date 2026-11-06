from django.test import SimpleTestCase
from django.urls import reverse


class ScaffoldTests(SimpleTestCase):
    def test_home_renders_prototype_notice(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "CareFlow EHR")
        self.assertContains(response, "Use only synthetic patient data.")

    def test_health_returns_process_status(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
