import uuid
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from careflow.patients.models import AuditEvent, Patient
from careflow.portal.models import PatientPortalAccount
from .forms import username_validator
from .models import AccountEvent, Enrollment, STAFF_ROLES


def is_account_admin(user):
    return bool(user.is_authenticated and user.is_active
                and user.groups.filter(name="Administrator").exists()
                and not PatientPortalAccount.objects.filter(user=user).exists())


@transaction.atomic
def register(kind, data):
    if kind not in ("patient", "staff") or not data.get("synthetic_only"):
        raise ValidationError("Confirm the synthetic demonstration scope.")
    if kind == "staff" and data.get("requested_role") not in STAFF_ROLES:
        raise ValidationError("Choose a permitted staff role.")
    username = data["username"]
    username_validator(username)
    if data["password1"] != data.get("password2"):
        raise ValidationError("The passwords do not match.")
    users = get_user_model()
    if users.objects.filter(username__iexact=username).exists():
        raise ValidationError("This username is unavailable. Choose another.")
    user = users(username=username, first_name="Synthetic", last_name="Visitor", is_active=kind == "patient")
    validate_password(data["password1"], user)
    user.set_password(data["password1"])
    user.save()
    enrollment = Enrollment.objects.create(user=user, kind=kind,
        requested_role=data.get("requested_role", "") if kind == "staff" else "",
        status="approved" if kind == "patient" else "pending")
    AccountEvent.objects.create(enrollment=enrollment, actor=user, action="registration")
    if kind == "patient":
        # A new fictional chart prevents supplied IDs from claiming existing records.
        patient = Patient.objects.create(mrn="PORTAL-" + uuid.uuid4().hex[:20].upper(),
            first_name="Synthetic", last_name="Visitor", dob=date(2000, 1, 1), sex="unknown")
        PatientPortalAccount.objects.create(user=user, patient=patient)
        AuditEvent.objects.create(actor=user, patient=patient, action="patient_create",
                                  changed_fields=["synthetic_portal_registration"])
    return enrollment


@transaction.atomic
def review(actor, enrollment_id, data):
    if not is_account_admin(actor):
        raise PermissionDenied
    status = "approved" if data["decision"] == "approve" else "rejected"
    role = data["role"] if status == "approved" else ""
    if data["decision"] not in ("approve", "reject") or (status == "approved" and role not in STAFF_ROLES):
        raise ValidationError("Choose a permitted decision and staff role.")
    if not data["reason"].strip() or len(data["reason"]) > 500:
        raise ValidationError("Provide a review reason of at most 500 characters.")
    updated = Enrollment.objects.filter(pk=enrollment_id, kind="staff", status="pending",
        version=data["version"]).exclude(user=actor).update(status=status, granted_role=role,
        reviewed_by=actor, reviewed_at=timezone.now(), review_reason=data["reason"].strip(), version=F("version") + 1)
    if updated != 1:
        raise ValidationError("The application changed or is not eligible. Reload before reviewing.")
    enrollment = Enrollment.objects.select_related("user").get(pk=enrollment_id)
    user = enrollment.user
    if user.is_active or user.is_staff or user.is_superuser or user.groups.exists() or PatientPortalAccount.objects.filter(user=user).exists():
        raise ValidationError("The account has conflicting access. Review it separately.")
    if status == "approved":
        user.groups.add(Group.objects.get_or_create(name=role)[0])
        user.is_active = True
        user.save(update_fields=["is_active"])
    AccountEvent.objects.create(enrollment=enrollment, actor=actor, action="staff_" + status,
                                role=role, reason=data["reason"].strip())
