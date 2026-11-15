from django.templatetags.static import static
from django.test import SimpleTestCase
from django.urls import reverse


class ScaffoldTests(SimpleTestCase):
    def test_home_renders_prototype_notice(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "CareFlow EHR")
        self.assertContains(response, "Use only synthetic patient data.")

    def test_home_links_to_both_sign_in_routes_and_stylesheets(self):
        response = self.client.get(reverse("home"))
        for route, label in (("login", "Staff Sign In"), ("portal_login", "Patient Sign In")):
            url = reverse(route)
            self.assertContains(response, f'href="{url}"')
            self.assertContains(response, label)
            self.assertEqual(self.client.get(url).status_code, 200)
        for stylesheet in ("core/v2.css",):
            self.assertContains(response, f'href="{static(stylesheet)}"')
        self.assertContains(response, "DEMO — NOT FOR CLINICAL USE")

    def test_health_returns_process_status(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
