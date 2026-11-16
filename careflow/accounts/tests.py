import secrets
from datetime import date
from unittest.mock import patch
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import OperationalError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from careflow.patients.models import Patient
from careflow.portal.models import PatientPortalAccount
from . import services
from .models import Enrollment, RequestBucket, STAFF_ROLES


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccountTests(TestCase):
    def setUp(self):
        self.password = secrets.token_urlsafe(24)
        self.data = {"username": "synthetic.visitor", "password1": self.password,
                     "password2": self.password, "synthetic_only": True}
        self.admin = get_user_model().objects.create_user("operator", password=self.password)
        self.admin.groups.add(Group.objects.get_or_create(name="Administrator")[0])

    def create(self, kind="patient", **changes):
        data = dict(self.data, **changes)
        if kind == "staff":
            data.setdefault("requested_role", "Physician")
        return services.register(kind, data)

    def decision(self, item, **changes):
        return dict({"version": item.version, "decision": "approve", "role": "Nurse",
                     "reason": "Synthetic demo operator approval."}, **changes)

    def test_patient_signup_activates_and_creates_one_fictional_chart(self):
        response = self.client.post(reverse("account_signup", args=["patient"]), self.data)
        self.assertRedirects(response, reverse("account_complete", args=["patient"]))
        item = Enrollment.objects.get()
        self.assertTrue(item.user.is_active)
        self.assertEqual(item.status, "approved")
        self.assertEqual(PatientPortalAccount.objects.count(), 1)
        patient = PatientPortalAccount.objects.get().patient
        self.assertTrue(patient.mrn.startswith("PORTAL-"))
        self.assertEqual(patient.dob, date(2000, 1, 1))
        self.assertEqual(patient.email, "")
        self.assertEqual(list(item.events.values_list("action", flat=True)), ["registration"])
        self.assertTrue(patient.auditevent_set.filter(action="patient_create", actor=item.user).exists())

    def test_password_is_hashed_and_username_login_works(self):
        item = self.create()
        self.assertNotEqual(item.user.password, self.password)
        self.assertTrue(item.user.check_password(self.password))
        self.assertEqual(authenticate(username=self.data["username"], password=self.password), item.user)
        self.assertIsNone(authenticate(username=self.data["username"], password="wrong"))

    def test_signup_does_not_send_or_store_email(self):
        with patch("django.core.mail.send_mail") as send:
            item = self.create(email="ignored@example.invalid")
        send.assert_not_called()
        self.assertEqual(item.user.email, "")
        self.assertFalse(any(f.name in ("email", "verified_at") for f in Enrollment._meta.fields))

    def test_username_password_confirmation_are_required(self):
        for field in ("username", "password1", "password2"):
            response = self.client.post("/accounts/register/patient/", dict(self.data, **{field: ""}))
            self.assertIn(field, response.context["form"].errors)
        self.assertFalse(Enrollment.objects.exists())

    def test_mismatched_passwords_do_not_create_account(self):
        response = self.client.post("/accounts/register/patient/", dict(self.data, password2="different"))
        self.assertIn("password2", response.context["form"].errors)
        with self.assertRaises(ValidationError):
            self.create(password2="different")
        self.assertFalse(Enrollment.objects.exists())

    def test_password_policy_is_enforced(self):
        for password in ("short", "123456789012", "password12345"):
            response = self.client.post("/accounts/register/patient/", dict(self.data, password1=password, password2=password))
            self.assertIn("password1", response.context["form"].errors)
        self.assertFalse(Enrollment.objects.exists())

    def test_synthetic_confirmation_is_unchecked_and_required(self):
        response = self.client.get("/accounts/register/patient/")
        self.assertFalse(response.context["form"]["synthetic_only"].value())
        response = self.client.post("/accounts/register/patient/", dict(self.data, synthetic_only=False))
        self.assertIn("synthetic_only", response.context["form"].errors)
        with self.assertRaises(ValidationError):
            self.create(synthetic_only=False)
        self.assertFalse(Enrollment.objects.exists())

    def test_username_format_and_length_are_validated(self):
        for username in ("ab", "a" * 41, "UpperCase", "name@example.invalid", "a b", "<script>"):
            response = self.client.post("/accounts/register/patient/", dict(self.data, username=username))
            self.assertIn("username", response.context["form"].errors)
        self.assertFalse(Enrollment.objects.exists())

    def test_duplicate_username_does_not_create_another_chart(self):
        item = self.create()
        response = self.client.post("/accounts/register/patient/", self.data)
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertTrue(item.user.check_password(self.password))

    def test_legacy_mixed_case_username_cannot_be_claimed(self):
        get_user_model().objects.create_user("Existing.User", password=self.password)
        response = self.client.post("/accounts/register/patient/", dict(self.data, username="existing.user"))
        self.assertIn("username", response.context["form"].errors)
        self.assertFalse(Enrollment.objects.exists())

    def test_supplied_ids_names_and_privileges_cannot_claim_existing_chart(self):
        patient = Patient.objects.create(mrn="SYN-EXISTING", first_name="Other", last_name="Synthetic", dob=date(1990, 1, 1), sex="unknown")
        item = self.create(patient_id=patient.pk, mrn=patient.mrn, is_superuser=True, is_staff=True,
                           requested_role="Administrator", first_name="Untrusted")
        self.assertNotEqual(PatientPortalAccount.objects.get(user=item.user).patient_id, patient.pk)
        self.assertFalse(item.user.is_staff or item.user.is_superuser or item.user.groups.exists())
        self.assertEqual(item.user.first_name, "Synthetic")

    def test_two_patient_registrations_have_distinct_portal_contexts(self):
        first = self.create()
        second = self.create(username="second.visitor")
        self.assertNotEqual(PatientPortalAccount.objects.get(user=first.user).patient_id,
                            PatientPortalAccount.objects.get(user=second.user).patient_id)
        self.client.force_login(first.user)
        self.assertEqual(self.client.get("/portal/").status_code, 200)
        other = PatientPortalAccount.objects.get(user=second.user).patient_id
        self.assertEqual(self.client.get(f"/app/patients/{other}/").status_code, 403)

    def test_patient_cannot_use_staff_login(self):
        self.create()
        response = self.client.post("/login/", {"username": self.data["username"], "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_patient_login_works_and_staff_routes_deny_access(self):
        item = self.create()
        response = self.client.post("/portal/login/", {"username": item.user.username, "password": self.password})
        self.assertRedirects(response, "/portal/")
        for path in ("/app/dashboard/", "/app/patients/new/", "/app/accounts/applications/"):
            self.assertEqual(self.client.get(path).status_code, 403)

    def test_staff_pending_cannot_sign_in_and_has_no_patient_or_role(self):
        item = self.create("staff")
        self.assertFalse(item.user.is_active or item.user.groups.exists())
        self.assertFalse(Patient.objects.exists())
        self.assertIsNone(authenticate(username=item.user.username, password=self.password))
        self.assertEqual(item.status, "pending")

    def test_admin_approval_grants_exact_role_and_audit(self):
        item = self.create("staff")
        services.review(self.admin, item.pk, self.decision(item))
        item.refresh_from_db()
        item.user.refresh_from_db()
        self.assertTrue(item.user.is_active)
        self.assertEqual(list(item.user.groups.values_list("name", flat=True)), ["Nurse"])
        self.assertEqual(item.reviewed_by, self.admin)
        self.assertEqual(item.version, 2)
        self.assertEqual(item.events.last().action, "staff_approved")
        self.assertIsNotNone(authenticate(username=item.user.username, password=self.password))

    def test_admin_http_review_and_worklist(self):
        item = self.create("staff")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get("/app/accounts/applications/"), item.user.username)
        self.assertRedirects(self.client.post(reverse("account_application", args=[item.pk]), self.decision(item)),
                             reverse("account_applications"))

    def test_rejection_preserves_application_but_no_access(self):
        item = self.create("staff")
        services.review(self.admin, item.pk, self.decision(item, decision="reject", role=""))
        item.refresh_from_db()
        self.assertEqual(item.status, "rejected")
        self.assertIsNone(authenticate(username=item.user.username, password=self.password))
        self.assertEqual(item.events.last().action, "staff_rejected")

    def test_approval_stale_version_and_replay_are_rejected(self):
        item = self.create("staff")
        with self.assertRaises(ValidationError):
            services.review(self.admin, item.pk, self.decision(item, version=99))
        services.review(self.admin, item.pk, self.decision(item))
        with self.assertRaises(ValidationError):
            services.review(self.admin, item.pk, self.decision(item))
        self.assertEqual(item.events.filter(action="staff_approved").count(), 1)

    def test_registration_cannot_request_administrator(self):
        response = self.client.post("/accounts/register/staff/", dict(self.data, requested_role="Administrator"))
        self.assertIn("requested_role", response.context["form"].errors)
        with self.assertRaises(ValidationError):
            self.create("staff", requested_role="Administrator")
        self.assertFalse(Enrollment.objects.exists())

    def test_approval_cannot_grant_administrator_or_missing_reason(self):
        item = self.create("staff")
        for changes in ({"role": "Administrator"}, {"reason": ""}, {"decision": "unknown"}):
            with self.assertRaises(ValidationError):
                services.review(self.admin, item.pk, self.decision(item, **changes))
        item.refresh_from_db()
        self.assertEqual(item.status, "pending")

    def test_all_non_admin_roles_cannot_review_applications(self):
        item = self.create("staff")
        for index, role in enumerate(STAFF_ROLES):
            actor = get_user_model().objects.create_user(f"role-{index}", password=self.password)
            actor.groups.add(Group.objects.get_or_create(name=role)[0])
            with self.assertRaises(PermissionDenied):
                services.review(actor, item.pk, self.decision(item))
            self.client.force_login(actor)
            self.assertEqual(self.client.get(reverse("account_application", args=[item.pk])).status_code, 403)
            self.assertEqual(self.client.post(reverse("account_application", args=[item.pk]), self.decision(item)).status_code, 403)

    def test_conflicting_staff_state_rolls_back_approval(self):
        item = self.create("staff")
        item.user.groups.add(Group.objects.get_or_create(name="Nurse")[0])
        with self.assertRaises(ValidationError):
            services.review(self.admin, item.pk, self.decision(item))
        item.refresh_from_db()
        self.assertEqual(item.status, "pending")
        self.assertEqual(item.version, 1)

    def test_staff_cannot_sign_in_to_patient_portal(self):
        item = self.create("staff")
        services.review(self.admin, item.pk, self.decision(item))
        response = self.client.post("/portal/login/", {"username": item.user.username, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_csrf_required_for_signup_and_review(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/accounts/register/patient/", self.data).status_code, 403)
        item = self.create("staff")
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse("account_application", args=[item.pk]), self.decision(item)).status_code, 403)

    def test_failed_chart_write_rolls_back_registration(self):
        with patch("careflow.accounts.services.Patient.objects.create", side_effect=OperationalError("private database detail")):
            response = self.client.post("/accounts/register/patient/", self.data)
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "private database detail", status_code=503)
        self.assertFalse(Enrollment.objects.exists())
        self.assertFalse(get_user_model().objects.filter(username=self.data["username"]).exists())

    @override_settings(CAREFLOW_AUTH_IP_LIMIT=2)
    def test_ip_limit_does_not_trust_forwarded_headers(self):
        for username in ("one", "two"):
            self.client.post("/accounts/register/patient/", dict(self.data, username=username))
        response = self.client.post("/accounts/register/patient/", dict(self.data, username="three"), HTTP_X_FORWARDED_FOR="192.0.2.4")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "900")

    @override_settings(CAREFLOW_AUTH_IDENTITY_LIMIT=1)
    def test_identity_limit_applies_across_addresses(self):
        self.client.post("/login/", {"username": "missing", "password": "wrong"}, REMOTE_ADDR="192.0.2.1")
        response = self.client.post("/login/", {"username": "MISSING", "password": "wrong"}, REMOTE_ADDR="192.0.2.2")
        self.assertEqual(response.status_code, 429)
        self.assertFalse(any("missing" in key for key in RequestBucket.objects.values_list("key", flat=True)))

    def test_sensitive_pages_not_cached(self):
        for path in ("/login/", "/portal/login/", "/accounts/register/patient/"):
            response = self.client.get(path)
            self.assertIn("no-store", response["Cache-Control"])
            self.assertEqual(response["Referrer-Policy"], "same-origin")

    def test_legacy_authentication_unchanged(self):
        user = get_user_model().objects.create_user("legacy@example.invalid", password=self.password)
        self.assertEqual(authenticate(username=user.username, password=self.password), user)
        self.assertEqual(authenticate(username=self.admin.username, password=self.password), self.admin)

    def test_account_events_reject_model_edit_and_delete(self):
        item = self.create()
        event = item.events.get()
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()

    def test_registration_links_have_no_email_or_code_fields(self):
        for path in ("/", "/login/", "/portal/login/"):
            self.assertContains(self.client.get(path), "/accounts/register/")
        for kind in ("patient", "staff"):
            response = self.client.get(f"/accounts/register/{kind}/")
            self.assertNotContains(response, 'type="email"')
            self.assertNotContains(response, 'name="code"')
            self.assertNotContains(response, 'value="Administrator"')
            self.assertContains(response, "No email required")
        for path in ("/accounts/verify/", "/accounts/recover/confirm/", "/accounts/register/administrator/"):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_gets_never_create_accounts_and_put_is_rejected(self):
        self.client.get("/accounts/register/patient/", self.data)
        self.client.get("/accounts/complete/patient/")
        self.assertFalse(Enrollment.objects.exists())
        self.assertEqual(self.client.put("/accounts/register/patient/", self.data).status_code, 405)


    def test_pending_staff_correct_password_explains_approval_without_login(self):
        item = self.create("staff")
        response = self.client.post("/login/", {"username": item.user.username, "password": self.password})
        self.assertContains(response, "Your staff application is awaiting Administrator approval")
        self.assertNotIn("_auth_user_id", self.client.session)
        item.user.refresh_from_db()
        self.assertFalse(item.user.is_active)
        self.assertFalse(item.user.groups.exists())

    def test_pending_status_not_disclosed_for_wrong_password_or_unknown_user(self):
        item = self.create("staff")
        for username in (item.user.username, "nonexistent"):
            response = self.client.post("/login/", {"username": username, "password": "wrong-password"})
            self.assertNotContains(response, "Your staff application is awaiting Administrator approval")
            self.assertNotIn("_auth_user_id", self.client.session)

    def test_rejected_and_unrelated_inactive_accounts_keep_generic_failure(self):
        item = self.create("staff")
        services.review(self.admin, item.pk, self.decision(item, decision="reject", role=""))
        inactive = get_user_model().objects.create_user("inactive-legacy", password=self.password, is_active=False)
        for user in (item.user, inactive):
            response = self.client.post("/login/", {"username": user.username, "password": self.password})
            self.assertNotContains(response, "Your staff application is awaiting Administrator approval")
            self.assertNotIn("_auth_user_id", self.client.session)

    def test_pending_status_is_not_exposed_through_patient_login(self):
        item = self.create("staff")
        response = self.client.post("/portal/login/", {"username": item.user.username, "password": self.password})
        self.assertNotContains(response, "Your staff application is awaiting Administrator approval")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_login_works_after_approval_with_same_registration_password(self):
        item = self.create("staff")
        services.review(self.admin, item.pk, self.decision(item))
        response = self.client.post("/login/", {"username": item.user.username, "password": self.password})
        self.assertRedirects(response, "/app/dashboard/")
        self.assertEqual(int(self.client.session["_auth_user_id"]), item.user_id)
        self.assertEqual(self.client.get("/app/accounts/applications/").status_code, 403)

    def test_staff_completion_and_signup_explain_operator_review(self):
        response = self.client.get("/accounts/complete/staff/")
        self.assertContains(response, "Staff applications")
        self.assertContains(response, "requested role")
        form_response = self.client.get("/accounts/register/staff/")
        self.assertNotContains(form_response, 'value="Administrator"')
