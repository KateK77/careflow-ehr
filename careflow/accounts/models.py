from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


STAFF_ROLES = (
    "Physician", "Nurse", "FrontDesk", "Lab Staff", "Pharmacist",
    "BillingStaff", "RadiologyStaff", "HospitalOperations",
)


class Enrollment(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=10, choices=[("patient", "Patient"), ("staff", "Staff")])
    requested_role = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=10, default="pending")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.PROTECT, related_name="enrollment_reviews")
    review_reason = models.CharField(max_length=500, blank=True)
    granted_role = models.CharField(max_length=30, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(kind__in=["patient", "staff"]), name="account_kind_known"),
            models.CheckConstraint(condition=models.Q(status__in=["pending", "approved", "rejected"]), name="account_status_known"),
        ]


class AccountEvent(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=30)
    occurred_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=500, blank=True)
    role = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["occurred_at", "pk"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Account events cannot be edited.")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Account events cannot be deleted.")


class RequestBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
